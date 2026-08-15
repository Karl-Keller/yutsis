"""Plan replay and numeric evaluation.

The structural A* in yutsis.search chooses the moves; this module
replays that plan with the exact operations of yutsis.exact_moves and
emits a fully signed expression, then evaluates it at a j assignment.

Split out of yutsis.oriented in v0.8.2 (behavior-preserving); that name
survives as a re-export shim.
"""
from __future__ import annotations

from .exact_moves import (cut_bridge_exact, dumbbell_factor,
                          excise_bubble_exact, excise_loop_exact,
                          interchange_exact, reduce_triangle_exact,
                          theta_sign)
from .phase import PhaseExpr
from .state import OGraph, og_components


# ----------------------------------------------------------------------------
# Plan replay: structural A* chooses the moves; exact ops emit the algebra
# ----------------------------------------------------------------------------
def replay(og: OGraph, moves):
    """Apply a structural solver plan with exact operations. Returns an
    expression dict: phase (PhaseExpr), deltas, weights (labels w for
    1/(2w+1)), sums (x labels), sixjs (arg tuples), and -- from the k=1
    sector -- zeros (labels forced to j=0) and sqrt_num / sqrt_den
    (labels contributing sqrt(2j+1) and 1/sqrt(2j+1))."""
    total = PhaseExpr()
    deltas, weights, sums, sixjs, flip_roles = [], [], [], [], []
    zeros, sqrt_num, sqrt_den = [], [], []
    # Every emitted identity (3j orthogonality for the bubble, the Racah
    # sum for the triangle, K1a/K1b for the loop) is derived ASSUMING the
    # source vertex's triad exists; where it does not, both sides vanish
    # but the emitted factor does not. Record the input triads so the
    # evaluator can enforce them.
    input_triads = [tuple(slots) for slots in og.verts.values()]
    for mv in moves:
        if mv[0] == "bubble":
            og, ph, d, wlab = excise_bubble_exact(og, mv[1])
            deltas.append(d); weights.append(wlab)
        elif mv[0] == "loop":
            og, ph, zlab, d, snum, sden = excise_loop_exact(og, mv[1])
            zeros.append(zlab); deltas.append(d)
            sqrt_num.append(snum); sqrt_den.append(sden)
        elif mv[0] == "bridge":
            og, ph, zlab, (du, dw), (sdu, sdw) = cut_bridge_exact(og, mv[1])
            zeros.append(zlab); deltas.extend((du, dw))
            sqrt_den.extend((sdu, sdw))
        elif mv[0] == "tri":
            og, ph, args = reduce_triangle_exact(og, mv[1])
            sixjs.append(args)
        else:
            _, (u, v, e), Ppl, Qql = mv
            og, ph, x, args, roles = interchange_exact(og, e, Ppl, Qql)
            sums.append(x); sixjs.append(args); flip_roles.append(roles)
        total = total * ph
    # Finalize every component: bridge cut splits the state, so the end
    # of a reduction is a SET of irreducible diagrams -- thetas and
    # dumbbells -- not a single theta.
    thetas = []
    for comp in og_components(og):
        dumb = dumbbell_factor(comp)
        if dumb is not None:
            ph, zlab, (kk, ff) = dumb
            total = total * ph
            zeros.append(zlab)
            sqrt_num.extend((kk, ff))
            continue
        total = total * theta_sign(comp)
        # A theta is folded in as a +-1 PHASE, correct only where it
        # exists. Record its labels so the evaluator can enforce the 3j
        # conditions; without this the formula returns +-1 on diagrams
        # that genuinely vanish.
        thetas.append(tuple(sorted(comp.edges)))
    theta_labels = thetas
    return {"phase": total, "deltas": deltas, "weights": weights,
            "sums": sums, "sixjs": sixjs, "flip_roles": flip_roles,
            "zeros": zeros, "sqrt_num": sqrt_num, "sqrt_den": sqrt_den,
            "theta": theta_labels, "triads": input_triads}


# ----------------------------------------------------------------------------
# solve_exact: structural A* plans, exact ops emit, evaluator checks
# ----------------------------------------------------------------------------
def solve_exact(og: OGraph, greedy=False):
    """End-to-end: run the structural solver on og's topology, replay the
    plan with exact operations. Returns the fully signed expression."""
    from .graph import Graph
    from .search import solve as _solve
    g = Graph([(t, h, lab) for lab, (t, h) in og.edges.items()])
    r = _solve(g, greedy=greedy)
    if r is None or r.get("timeout"):
        return None
    return replay(og, r["moves"])


def evaluate_expr(expr, jmap, xmax=None):
    """Numeric value of a signed expression at a j assignment."""
    import math

    from sympy import S
    from sympy.physics.wigner import wigner_6j

    def s6(*a):
        try:
            return float(wigner_6j(*a))
        except ValueError:
            return 0.0

    for a, b in expr["deltas"]:
        if jmap[a] != jmap[b]:
            return 0.0
    # k=1 sector: a line crossing a 1-cut must carry j = 0, so the whole
    # diagram vanishes off that support.
    for zlab in expr.get("zeros", ()):
        if jmap[zlab] != 0:
            return 0.0
    def triad_ok(j1, j2, j3):
        """The 3j existence conditions: integral triad sum and the
        triangle inequality. A 3nj symbol is zero off these, but the
        emitted factors alone do not say so."""
        a, b, c = float(j1), float(j2), float(j3)
        if abs((a + b + c) - round(a + b + c)) > 1e-9:
            return False
        return abs(a - b) - 1e-9 <= c <= a + b + 1e-9

    # Input triads: the reduction identities presume them.
    for tri in expr.get("triads", ()):
        if not triad_ok(*(jmap[lab] for lab in tri)):
            return 0.0
    weight = 1.0
    for wlab in expr["weights"]:
        weight /= float(2 * jmap[wlab] + 1)
    for slab in expr.get("sqrt_num", ()):
        weight *= math.sqrt(float(2 * jmap[slab] + 1))
    for slab in expr.get("sqrt_den", ()):
        weight /= math.sqrt(float(2 * jmap[slab] + 1))
    if xmax is None:
        xmax = sum(jmap.values())

    def rec(i, jm2, acc):
        if i == len(expr["sums"]):
            # The final theta is folded into theta_sign as a +-1 phase,
            # which presumes it EXISTS. Checked here rather than at the
            # top because its labels may be summation variables.
            for theta in expr.get("theta") or ():
                if not triad_ok(*(jm2[lab] for lab in theta)):
                    return 0.0
            t = acc
            for args in expr["sixjs"]:
                t *= s6(*[jm2[a] for a in args])
                if t == 0.0:
                    return 0.0
            try:
                return expr["phase"].evaluate(jm2) * t
            except AssertionError:
                return 0.0
        tot, x = 0.0, S(0)
        while x <= xmax:
            jm3 = dict(jm2)
            jm3[expr["sums"][i]] = x
            tot += rec(i + 1, jm3, acc * float(2 * x + 1))
            x += S(1) / 2
        return tot

    return weight * rec(0, dict(jmap), 1.0)
