"""Exact, sign-carrying rewrite moves on oriented states.

Each move takes an OGraph and returns the rewritten OGraph plus a
PhaseExpr computed constructively, so no formula is trusted on
inspection. Every phase here was either derived analytically and
oracle-checked, or determined by constrained fit against the oracle and
recorded as such.

Two exact symmetry rules of the oracle's algebra generate the
bookkeeping: permuting one vertex's slot order costs (-1)^(triad) when
the permutation is odd, and reversing one edge costs (-1)^(2j).

Split out of yutsis.oriented in v0.8.2 (behavior-preserving); that name
survives as a re-export shim.
"""
from __future__ import annotations

from .benchmarks import oriented_prism
from .phase import PhaseExpr, tetra_to_6j
from .state import OGraph


def theta_sign(og: OGraph):
    """Sign of a two-vertex, three-edge closed state. Canonical +1 form:
    identical slot orders, all edges tail at the first vertex. Each
    reversed edge costs (-1)^(2j); an odd slot permutation costs
    (-1)^(triad sum)."""
    assert og.n == 2 and len(og.edges) == 3
    v1, v2 = sorted(og.verts)
    s1, s2 = og.verts[v1], og.verts[v2]
    phase = PhaseExpr()
    perm = tuple(s2.index(x) for x in s1)
    inv = sum(1 for i in range(3) for k in range(i + 1, 3) if perm[i] > perm[k])
    if inv % 2:
        phase.add_triad(list(s1))
    for lab, (t, h) in og.edges.items():
        if t != v1:
            phase.add_2j(lab)
    return phase


def reduce_triangle_exact(og: OGraph, tri):
    """Returns (new_OGraph, PhaseExpr, sixj_args) with the sign exact."""
    a, b, c = tri
    inside, legs = {}, {}
    for lab, (t, h) in og.edges.items():
        pin = (t in tri) + (h in tri)
        if pin == 2:
            other = ({a, b, c} - {t, h}).pop()
            if other in inside:
                return None
            inside[other] = lab
        elif pin == 1:
            w = t if t in tri else h
            if w in legs:
                return None
            legs[w] = lab
    if len(inside) != 3 or len(legs) != 3:
        return None
    leg_order = (legs[a], legs[b], legs[c])

    # -- cap tetrahedron: triangle verts as-is + G at the legs' far ends
    cap_edges, theta_corr = {}, PhaseExpr()
    for lab, (t, h) in og.edges.items():
        if lab in inside.values():
            cap_edges[lab] = (t, h)
        elif lab in leg_order:
            if t in tri:                # tail at triangle -> G is head
                cap_edges[lab] = (t, "G")
            else:                        # head at triangle -> G is tail
                cap_edges[lab] = ("G", h)
                theta_corr.add_2j(lab)   # dual-pairing flip cost
    cap_verts = {v: og.verts[v] for v in tri}
    cap_verts["G"] = leg_order
    cap_phase, sixj_args = tetra_to_6j(cap_edges, cap_verts)
    phase = cap_phase * theta_corr

    # -- residual: W inherits each leg's triangle-side endpoint role
    new_edges = {}
    for lab, (t, h) in og.edges.items():
        if lab in inside.values():
            continue
        if lab in leg_order:
            new_edges[lab] = ("W_" + str(a), h) if t in tri else (t, "W_" + str(a))
        else:
            new_edges[lab] = (t, h)
    new_verts = {v: s for v, s in og.verts.items() if v not in tri}
    new_verts["W_" + str(a)] = leg_order
    return OGraph(new_edges, new_verts), phase, sixj_args


# ----------------------------------------------------------------------------
# Exact bubble excision
# ----------------------------------------------------------------------------
def excise_bubble_exact(og: OGraph, pair):
    """Canonical bubble (U slots (p,q,a), V slots (p,q,b), p,q: U->V,
    a: head at U, b: tail at V) excises with factor
        (-1)^(2p+2q) * delta(a,b) / (2a+1),
    derived from 3j orthogonality with the on-support metric identity
    (-1)^(j_a - m_a) squared = +1. General case: normalize the local
    patch by slot permutations ((-1)^triad) and orientation flips
    ((-1)^(2j)), MATERIALIZING external flips in the residual. Returns
    (new_OGraph, PhaseExpr, delta_pair, weight_label)."""
    u, v = pair
    par = [lab for lab, (t, h) in og.edges.items() if {t, h} == {u, v}]
    if len(par) != 2:
        return None
    ext_u = [lab for lab, (t, h) in og.edges.items()
             if lab not in par and u in (t, h)]
    ext_v = [lab for lab, (t, h) in og.edges.items()
             if lab not in par and v in (t, h)]
    if len(ext_u) != 1 or len(ext_v) != 1:
        return None
    a, b = ext_u[0], ext_v[0]
    phase = PhaseExpr()
    for p, q in ((par[0], par[1]), (par[1], par[0])):
        ph = PhaseExpr()
        okperm = True
        for vid, want in ((u, (p, q, a)), (v, (p, q, b))):
            have = og.verts[vid]
            if set(have) != set(want):
                okperm = False
                break
            perm = tuple(have.index(x) for x in want)
            inv = sum(1 for i in range(3) for k2 in range(i + 1, 3)
                      if perm[i] > perm[k2])
            if inv % 2:
                ph.add_triad(list(have))
        if not okperm:
            continue
        flips = set()
        for lab, tail_at in ((p, u), (q, u)):
            t, h = og.edges[lab]
            if t != tail_at:
                ph.add_2j(lab)
        # a canonical: head at U; b canonical: tail at V
        if og.edges[a][1] != u:
            ph.add_2j(a); flips.add(a)
        if og.edges[b][0] != v:
            ph.add_2j(b); flips.add(b)
        ph.add_2j(p); ph.add_2j(q)          # the derived (-1)^(2p+2q)
        # residual: merged edge keeps label a, far ends post-normalization
        ta, ha = og.edges[a]
        far_a = ta if ha == u else ha       # far endpoint of a
        tb, hb = og.edges[b]
        far_b = tb if hb == v else hb
        new_edges = {lab: th for lab, th in og.edges.items()
                     if lab not in par and lab not in (a, b)}
        new_edges[a] = (far_a, far_b)       # canonical: far_a -> U, V -> far_b
        new_verts = {}
        for vid, slots in og.verts.items():
            if vid in (u, v):
                continue
            new_verts[vid] = tuple(a if s == b else s for s in slots)
        return OGraph(new_edges, new_verts), ph, (a, b), a
    return None


# ----------------------------------------------------------------------------
# Exact loop excision (the k=1 sector)
# ----------------------------------------------------------------------------
def excise_loop_exact(og: OGraph, v):
    """Canonical tadpole (v slots (k,k,c) with the loop's tail first and
    c: v->w; w slots (c,a,b) with a,b both tailed at w) excises with
    factor

        sqrt(2k+1) / sqrt(2a+1) * delta(c,0) * delta(a,b)

    and phase EXACTLY +1 -- measured against the oracle on every
    labeling of the canonical family, no residual sign to fit
    (docs/K1_SECTOR.md). The two lemmas behind it:

        K1a  sum_m (-1)^(k-m) 3j(k k c; m -m mc)
                                  = sqrt(2k+1) d(c,0) d(mc,0)
        K1b  3j(a b 0; ma mb 0)
                                  = d(a,b) d(ma,-mb) (-1)^(a-ma)/sqrt(2a+1)

    General case: normalize the local patch by slot permutations
    ((-1)^triad) and orientation flips ((-1)^(2j)), exactly as
    excise_bubble_exact does. The loop needs no special orientation
    handling: the oracle fixes its tail/head by slot order, so any
    reordering that preserves the relative order of the two k slots
    preserves the orientation too.

    Returns (new_OGraph, PhaseExpr, zero_label, delta_pair, sqrt_num,
    sqrt_den)."""
    loops = [lab for lab, (t, h) in og.edges.items() if t == h == v]
    if len(loops) != 1:
        return None
    k = loops[0]
    slots = og.verts[v]
    if list(slots).count(k) != 2:
        return None
    others = [s for s in slots if s != k]
    if len(others) != 1:
        return None
    c = others[0]
    tc, hc = og.edges[c]
    w = hc if tc == v else tc
    if w == v:
        return None
    if any(t == h == w for t, h in og.edges.values()):
        return None                      # dumbbell: irreducible terminal
    wslots = og.verts[w]
    if c not in wslots:
        return None
    ab = [s for s in wslots if s != c]
    if len(ab) != 2:
        return None
    a, b = ab

    phase = PhaseExpr()

    # 1. v -> canonical (k, k, c): move c into slot 3, preserving the
    #    order of the two k slots (which carries the loop orientation).
    ci = list(slots).index(c)
    if ci == 1:                          # (k, c, k): one transposition
        phase.add_triad(list(slots))

    # 2. w -> canonical (c, a, b).
    want = (c, a, b)
    perm = tuple(wslots.index(x) for x in want)
    inv = sum(1 for i in range(3) for j in range(i + 1, 3)
              if perm[i] > perm[j])
    if inv % 2:
        phase.add_triad(list(wslots))

    # 3. orientations: c tailed at v, a and b tailed at w.
    if og.edges[c][0] != v:
        phase.add_2j(c)
    for lab in (a, b):
        if og.edges[lab][0] != w:
            phase.add_2j(lab)

    # 4. residual: a and b merge, keeping label a, running from a's far
    #    end to b's far end (the excise_bubble_exact convention).
    ta, ha = og.edges[a]
    far_a = ta if ha == w else ha
    tb, hb = og.edges[b]
    far_b = tb if hb == w else hb
    new_edges = {lab: th for lab, th in og.edges.items()
                 if lab not in (k, c, a, b)}
    new_edges[a] = (far_a, far_b)
    new_verts = {vid: tuple(a if s == b else s for s in sl)
                 for vid, sl in og.verts.items() if vid not in (v, w)}
    return OGraph(new_edges, new_verts), phase, c, (a, b), k, a


def cut_bridge_exact(og: OGraph, lab):
    """Canonical bridge (e: u->w, u slots (a,b,e) with a,b tailed at u,
    w slots (c,d,e) with c,d tailed at w) cuts with factor

        delta(e,0) * delta(a,b) * delta(c,d)
                                  / (sqrt(2a+1) * sqrt(2c+1))

    and phase EXACTLY +1 -- measured against the oracle, no residual
    sign to fit (docs/K1_SECTOR.md). It is the cap rule K1b applied at
    both ends, and it SPLITS the state into two independent closed
    diagrams.

    Returns (new_OGraph, PhaseExpr, zero_label, (delta_u, delta_w),
    (sqrt_den_u, sqrt_den_w))."""
    if lab not in og.edges:
        return None
    u, w = og.edges[lab]
    if u == w:
        return None
    su, sw = og.verts.get(u), og.verts.get(w)
    if su is None or sw is None or lab not in su or lab not in sw:
        return None
    ab = [s for s in su if s != lab]
    cd = [s for s in sw if s != lab]
    if len(ab) != 2 or len(cd) != 2 or len(set(ab)) != 2 or len(set(cd)) != 2:
        return None          # tadpole endpoint: the dumbbell, not this
    a, b = ab
    c, d = cd

    phase = PhaseExpr()
    for vid, slots, want in ((u, su, (a, b, lab)), (w, sw, (c, d, lab))):
        perm = tuple(slots.index(x) for x in want)
        inv = sum(1 for i in range(3) for j in range(i + 1, 3)
                  if perm[i] > perm[j])
        if inv % 2:
            phase.add_triad(list(slots))
    if og.edges[lab][0] != u:
        phase.add_2j(lab)
    for end, labels in ((u, (a, b)), (w, (c, d))):
        for x in labels:
            if og.edges[x][0] != end:
                phase.add_2j(x)

    new_edges = {k: v for k, v in og.edges.items()
                 if k not in (lab, a, b, c, d)}
    for end, keep_lab, other in ((u, a, b), (w, c, d)):
        tk, hk = og.edges[keep_lab]
        far_keep = tk if hk == end else hk
        to, ho = og.edges[other]
        far_other = to if ho == end else ho
        new_edges[keep_lab] = (far_keep, far_other)
    new_verts = {}
    for vid, slots in og.verts.items():
        if vid in (u, w):
            continue
        new_verts[vid] = tuple(a if s == b else (c if s == d else s)
                               for s in slots)
    return (OGraph(new_edges, new_verts), phase, lab, ((a, b), (c, d)),
            (a, c))


def dumbbell_factor(og: OGraph):
    """Value of an irreducible dumbbell component: two tadpoles joined
    by a bridge.

        sqrt(2k+1) * sqrt(2f+1) * delta(c,0)

    with phase +1 in canonical slot order (v = (k,k,c), w = (c,f,f), c
    tailed at v). Capping it would leave a bare circle with no vertices,
    so it terminates instead -- the empty diagram is deliberately not a
    state.

    Returns (PhaseExpr, zero_label, (sqrt_num_k, sqrt_num_f))."""
    loops = [lab for lab, (t, h) in og.edges.items() if t == h]
    if og.n != 2 or len(og.edges) != 3 or len(loops) != 2:
        return None
    bridge = [lab for lab in og.edges if lab not in loops]
    if len(bridge) != 1:
        return None
    c = bridge[0]
    u, w = og.edges[c]
    phase = PhaseExpr()
    # each tadpole: move c out of the way, preserving the loop's two
    # slots in order (that order carries its orientation)
    for vid, target_index in ((u, 2), (w, 0)):
        slots = og.verts[vid]
        ci = list(slots).index(c)
        # one transposition iff c must cross exactly one loop slot
        if (target_index, ci) in ((2, 1), (0, 1)):
            phase.add_triad(list(slots))
    if og.edges[c][0] != u:
        phase.add_2j(c)
    k = [lab for lab in loops if lab in og.verts[u]][0]
    f = [lab for lab in loops if lab in og.verts[w]][0]
    return phase, c, (k, f)


# ----------------------------------------------------------------------------
# Exact interchange (edge flip) -- phase role-coefficients set by the
# constrained fit against wigner_9j (see scripts/fit_flip_phase.py)
# ----------------------------------------------------------------------------
# Fitted against wigner_9j over 22 K3,3 labelings (incl. half-integers),
# 8 survivors out of 8192 forming one triad-equivalence class; canonical
# representative is the textbook recoupling phase (-1)^(p+q+e+x).
FLIP_PHI = {"p": 1, "q": 1, "e": 1, "x": 1}


def interchange_exact(og: OGraph, e, P_pl, Q_ql):
    """Flip edge e=(u,v): neighbor P (edge p) of u swaps with neighbor Q
    (edge q) of v. Canonical input: u slots (p,e,r), v slots (e,q,s),
    orientations p: P->u, e: u->v, q: v->Q, r: u->R, s: v->S. Output:
    u slots (q,x,r), v slots (x,p,s), x: u->v, q: u->Q, p: P->v; factor
    sum_x (2x+1) (-1)^Phi {p e r; q x s}. Non-canonical inputs are
    normalized first (phases tracked, flips materialized)."""
    P, pl = P_pl
    Q, ql = Q_ql
    (t_e, h_e) = og.edges[e]
    u, v = t_e, h_e
    ph = PhaseExpr()
    work = {lab: th for lab, th in og.edges.items()}
    # orient e canonically u->v is by definition of (u,v); allow caller
    # to pass the flip with e reversed by normalizing:
    others_u = [lab for lab, (t, h) in work.items() if lab != e and u in (t, h)]
    others_v = [lab for lab, (t, h) in work.items() if lab != e and v in (t, h)]
    if pl not in others_u or ql not in others_v:
        # caller's u/v assignment is reversed relative to e's orientation
        u, v = v, u
        ph.add_2j(e)
        work[e] = (u, v)
        others_u = [lab for lab, (t, h) in work.items() if lab != e and u in (t, h)]
        others_v = [lab for lab, (t, h) in work.items() if lab != e and v in (t, h)]
        if pl not in others_u or ql not in others_v:
            return None
    r = [lab for lab in others_u if lab != pl][0]
    s = [lab for lab in others_v if lab != ql][0]
    # normalize orientations, materializing
    for lab, tail_should_be, at in ((pl, None, u), (ql, v, None),
                                    (r, u, None), (s, v, None)):
        t, h = work[lab]
        if lab == pl:
            if h != u:                      # canonical p: P->u
                ph.add_2j(lab); work[lab] = (h, t)
        else:
            if t != (v if lab == ql else u if lab == r else v):
                pass
            want_tail = v if lab == ql else (u if lab == r else v)
            if lab == s:
                want_tail = v
            if work[lab][0] != want_tail:
                ph.add_2j(lab); work[lab] = (work[lab][1], work[lab][0])
    # normalize slot orders
    for vid, want in ((u, (pl, e, r)), (v, (e, ql, s))):
        have = og.verts[vid]
        perm = tuple(have.index(x) for x in want)
        inv = sum(1 for i in range(3) for k2 in range(i + 1, 3)
                  if perm[i] > perm[k2])
        if inv % 2:
            ph.add_triad(list(have))
    # canonical rewrite
    x = "x_" + str(e)
    new_edges = {lab: th for lab, th in work.items() if lab not in (e, pl, ql)}
    Pfar = work[pl][0]
    Qfar = work[ql][1]
    new_edges[x] = (u, v)
    new_edges[ql] = (u, Qfar)
    new_edges[pl] = (Pfar, v)
    new_verts = {vid: slots for vid, slots in og.verts.items()
                 if vid not in (u, v)}
    new_verts[u] = (ql, x, r)
    new_verts[v] = (x, pl, s)
    assert FLIP_PHI is not None, "flip phase not fitted yet"
    roles = {"p": pl, "q": ql, "r": r, "s": s, "e": e, "x": x}
    for role, lab in roles.items():
        c = FLIP_PHI.get(role, 0)
        for _ in range(c):
            ph.c[lab] = ph.c.get(lab, 0) + 1
    ph.add_const(FLIP_PHI.get("const", 0))
    ph._norm()
    sixj = (pl, e, r, ql, x, s)             # opposite pairs (p,q),(e,x),(r,s)
    roles = dict(roles); roles["x"] = x
    return OGraph(new_edges, new_verts), ph, x, sixj, roles


def reduce_prism_exact():
    """Full oriented reduction of the prism: two exact triangle
    reductions plus the final theta sign. Returns (PhaseExpr, factors)."""
    og = oriented_prism()
    total, factors = PhaseExpr(), []
    for _ in range(2):
        tri = og.triangles()[0]
        og, ph, args = reduce_triangle_exact(og, tri)
        total, factors = total * ph, factors + [args]
    total = total * theta_sign(og)
    return total, factors
