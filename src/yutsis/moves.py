"""Rewrite moves. Each returns (new_graph, factor_string, d_sixj, d_sums)
or None when the pattern guard fails.

v0 tracks factors structurally; the Danos-consistent phase/weight engine
(milestone 2) will derive signs from node orders and arrows, validated
against yutsis.oracle in CI.
"""
from __future__ import annotations

import itertools

from .graph import Graph

fresh = itertools.count(1)


def excise_bubble(g: Graph, pair):
    u, v = pair
    par = [lab for a, b, lab in g.edges if (a, b) == pair]
    ext, keep = [], []
    for a, b, lab in g.edges:
        if (a, b) == pair:
            continue
        if u in (a, b) or v in (a, b):
            other = a if b in (u, v) else b
            ext.append((other, lab))
        else:
            keep.append((a, b, lab))
    if len(ext) != 2:
        return None
    (x, la), (y, _) = ext
    keep.append((x, y, la))
    fac = f"delta({par[0]},{par[1]})/(2*{par[0]}+1)"
    return Graph(keep), fac, 0, 0, ("bubble", pair)


def excise_loop(g: Graph, v):
    """The k=1 move: excise a tadpole and cap its partner.

    Derivation (docs/K1_SECTOR.md), both halves oracle-verified:

      K1a  sum_m (-1)^(k-m) 3j(k k c; m -m mc) = sqrt(2k+1) d(c,0) d(mc,0)
           -- closing two legs of v forces its third edge c to j = 0.
      K1b  3j(a b 0; ma mb 0) = d(a,b) d(ma,-mb) (-1)^(a-ma)/sqrt(2a+1)
           -- a vertex with a j=0 leg is removed and its other two edges
           merge.

    The two are fused into one move because K1a alone would leave c
    dangling: the graph must stay closed and cubic between moves. Net
    effect: v and its partner w both go, w's other two edges merge, and
    n drops by 2 for NO 6j and NO summation -- a free move, which is
    why yutsis.bounds.sum_bound must test for it (see the coupling note
    in docs/K1_SECTOR.md).

    Guard: w must be distinct from v and carry no loop of its own; the
    loop-to-loop case is the irreducible dumbbell terminal."""
    if v not in g.excisable_loops():
        return None
    loop_labels = [lab for a, b, lab in g.edges if a == b == v]
    if len(loop_labels) != 1:
        return None
    k = loop_labels[0]
    w, c = g.loop_partner(v)
    rest = [(a, b, lab) for a, b, lab in g.edges
            if lab != k and lab != c and v not in (a, b)]
    at_w = [(a, b, lab) for a, b, lab in rest if w in (a, b)]
    if len(at_w) != 2:
        return None
    keep = [e for e in rest if e not in at_w]
    ends = []
    for a, b, lab in at_w:
        ends.append((b if a == w else a, lab))
    (x, la), (y, _lb) = ends
    keep.append((x, y, la))          # w's two edges merge, keeping la
    fac = f"loopw({k})*delta({c},0)*delta({la},{_lb})/sqrt(2*{la}+1)"
    return Graph(keep), fac, 0, 0, ("loop", v)


def cut_bridge(g: Graph, lab):
    """The k=1 move for a 1-line cut: force j = 0 and cap both ends.

    A closed diagram is a rotational scalar, so the single line crossing
    the separation carries no angular momentum. Applying the cap rule
    K1b at each endpoint removes both and splits the diagram into two
    INDEPENDENT closed diagrams:

        delta(e,0) * delta(a,b) * delta(c,d)
                                 / (sqrt(2a+1) * sqrt(2c+1))

    Derivation and oracle verification: docs/K1_SECTOR.md. Canonical
    orientations give phase exactly +1.

    Free move (no 6j, no summation), n drops by 2 and the component
    count rises by 1 -- so `yutsis.bounds.sum_bound` must test for it,
    the same coupling loop excision introduced.

    Guard: neither endpoint may be a tadpole vertex, since capping one
    would merge a self-loop into a bare circle (the empty diagram, which
    is not a state). That case is the dumbbell terminal."""
    if lab not in g.cuttable_bridges():
        return None
    u, w = next((a, b) for a, b, x in g.edges if x == lab)
    at_u = [(a, b, x) for a, b, x in g.edges if x != lab and u in (a, b)]
    at_w = [(a, b, x) for a, b, x in g.edges if x != lab and w in (a, b)]
    if len(at_u) != 2 or len(at_w) != 2:
        return None
    keep = [(a, b, x) for a, b, x in g.edges
            if x != lab and u not in (a, b) and w not in (a, b)]
    merged = []
    for end, pair in ((u, at_u), (w, at_w)):
        ends = [(b if a == end else a, x) for a, b, x in pair]
        (p, lp), (q, _lq) = ends
        merged.append((p, q, lp))
        keep.append((p, q, lp))
    (_pa, _qa, la), (_pc, _qc, lc) = merged
    fac = (f"delta({lab},0)*cap({la})*cap({lc})"
           f"/(sqrt(2*{la}+1)*sqrt(2*{lc}+1))")
    return Graph(keep), fac, 0, 0, ("bridge", lab)


def reduce_triangle(g: Graph, tri):
    """Contract a triangle, emitting its cap-tetrahedron 6j.

    Argument order encodes the OPPOSITE-EDGE pairing proved by the prism
    phase theorem (yutsis.phase, Finding 4): column i pairs the inside
    edge NOT touching triangle vertex i with the leg AT vertex i. The
    overall sign still requires oriented, slot-ordered graph states
    (milestone 2 continuation); emitted as sixj(...) up to phase."""
    a, b, c = tri
    inside_at, leg_at, keep = {}, {}, []
    for u, v, lab in g.edges:
        pin = (u in tri) + (v in tri)
        if pin == 2:
            other = ({a, b, c} - {u, v}).pop()
            if other in inside_at:
                return None  # doubled inside edge: not a clean triangle
            inside_at[other] = lab
        elif pin == 1:
            w = u if u in tri else v
            if w in leg_at:
                return None
            leg_at[w] = lab
            keep.append((u, v, lab))
        else:
            keep.append((u, v, lab))
    if len(inside_at) != 3 or len(leg_at) != 3:
        return None
    w = "W_" + str(a)
    merged = [(w if u in tri else u, w if v in tri else v, lab)
              for u, v, lab in keep]
    top = [inside_at[x] for x in (a, b, c)]
    bot = [leg_at[x] for x in (a, b, c)]
    fac = "sixj(" + ",".join(top + bot) + ")"
    return Graph(merged), fac, 1, 0, ("tri", tuple(tri))


def interchanges(g: Graph):
    """All edge-flip moves: for internal edge e=(u,v), swap one neighbor of
    u with one neighbor of v across e. The graphical (ab)c -> a(bc)
    recoupling identity: emits one 6j, relabels e with a summed x."""
    out = []
    for u, v, lab in g.edges:
        if u == v:
            continue  # k=1 guard: see below
        un = [(w, lb) for w, lb, _ in g.adj[u] if w != v]
        vn = [(w, lb) for w, lb, _ in g.adj[v] if w != u]
        if len(un) != 2 or len(vn) != 2:
            continue
        # k=1 guard. The flip phase was determined by constrained fit
        # against wigner_9j on a GENERIC patch (v0.4.0): e = (u,v) with
        # P a neighbour of u and Q a neighbour of v, all distinct. A
        # self-loop at u makes P == u, which is not that patch, and the
        # fitted phase has never been validated there. Before the k=1
        # sector such states were unreachable in practice; now they are
        # not, so the guard is explicit. Without it the dumbbell -- an
        # irreducible terminal -- "reduces" at cost 11 through
        # unvalidated algebra.
        if any(w in (u, v) for w, _l in un + vn):
            continue
        for (P, pl) in un:
            for (Q, ql) in vn:
                x = "x_" + str(lab)
                edges, done = [], set()
                for a, b, l2 in g.edges:
                    if "e" not in done and {a, b} == {u, v} and l2 == lab:
                        edges.append((u, v, x))
                        done.add("e")
                    elif "p" not in done and {a, b} == {u, P} and l2 == pl:
                        edges.append((v, P, pl))
                        done.add("p")
                    elif "q" not in done and {a, b} == {v, Q} and l2 == ql:
                        edges.append((u, Q, ql))
                        done.add("q")
                    else:
                        edges.append((a, b, l2))
                ng = Graph(edges)
                if ng.check_cubic():
                    fac = f"sum_{x}(2*{x}+1)*sixj({pl},{ql},{lab},...,{x})"
                    out.append((ng, fac, 1, 1, ("flip", (u, v, lab), (P, pl), (Q, ql))))
    return out


def targeted_interchanges(g: Graph):
    """Cycle-shortening flips only (the GYutsis girth strategy): pick one
    shortest cycle v1..vL; for each adjacent edge pair (p, e) along it,
    flip e with P = the cycle vertex behind u -- the cycle contracts by
    one. Branching drops from ~4|E| to ~4L. A* remains optimal over this
    restricted move class (Finding 3 / milestone 3; blind flips are
    retained in interchanges() for exhaustive small-n work)."""
    cyc = g.girth_cycle()
    if not cyc or len(cyc) < 4:
        return []
    L = len(cyc)
    out, seen = [], set()
    def elab(u, v):
        for a, b, lab in g.edges:
            if {a, b} == {u, v}:
                return lab
        return None
    for d in (1, -1):
        order = cyc if d == 1 else tuple(reversed(cyc))
        for i in range(L):
            P, u, v = order[i - 1], order[i], order[(i + 1) % L]
            e, pl = elab(u, v), elab(P, u)
            if e is None or pl is None:
                continue
            if P in (u, v) or u == v:
                continue  # k=1 guard, as in interchanges()
            for Q, ql, _ in g.adj[v]:
                if ql == e or Q in (u, v):
                    continue  # k=1 guard
                key = (e, pl, ql, u)
                if key in seen:
                    continue
                seen.add(key)
                x = "x_" + str(e)
                edges, done = [], set()
                for a, b, l2 in g.edges:
                    if "e" not in done and {a, b} == {u, v} and l2 == e:
                        edges.append((u, v, x))
                        done.add("e")
                    elif "p" not in done and {a, b} == {u, P} and l2 == pl:
                        edges.append((v, P, pl))
                        done.add("p")
                    elif "q" not in done and {a, b} == {v, Q} and l2 == ql:
                        edges.append((u, Q, ql))
                        done.add("q")
                    else:
                        edges.append((a, b, l2))
                ng = Graph(edges)
                if ng.check_cubic():
                    fac = f"sum_{x}(2*{x}+1)*sixj({pl},{ql},{e},...,{x})"
                    out.append((ng, fac, 1, 1, ("flip", (u, v, e), (P, pl), (Q, ql))))
    return out
