"""End-to-end fully signed formulas: solve_exact vs ground truth."""
import itertools

from sympy import S
from sympy.physics.wigner import wigner_9j
import yutsis.oriented as O
from yutsis.oracle import ClosedDiagram


def oriented_k33():
    edges = {}
    verts = {"1": ("a", "b", "c"), "2": ("d", "e", "f"), "3": ("g", "h", "i"),
             "4": ("a", "d", "g"), "5": ("b", "e", "h"), "6": ("c", "f", "i")}
    lab = iter("abcdefghi")
    for u in "123":
        for v in "456":
            edges[next(lab)] = (u, v)
    return O.OGraph(edges, verts)


def dumbbell():
    edges = {"p": ("U", "V"), "q": ("U", "V"), "a": ("W", "U"),
             "b": ("V", "Z"), "c": ("W", "Z"), "d": ("W", "Z")}
    verts = {"U": ("p", "q", "a"), "V": ("p", "q", "b"),
             "W": ("a", "c", "d"), "Z": ("b", "c", "d")}
    return O.OGraph(edges, verts)


def test_k33_fully_signed_equals_9j():
    expr = O.solve_exact(oriented_k33())
    h = S(1) / 2
    js = (h, h, 1, h, h, 1, 1, 1, 2)
    jm = dict(zip("abcdefghi", js))
    assert abs(O.evaluate_expr(expr, jm) - float(wigner_9j(*js))) < 1e-8


def test_bubble_path_fully_signed_vs_oracle():
    og = dumbbell()
    expr = O.solve_exact(dumbbell())
    js = dict(p=S(3) / 2, q=1, a=S(1) / 2, b=S(1) / 2, c=1, d=S(1) / 2)
    cd = ClosedDiagram({lab: (t, h, js[lab])
                        for lab, (t, h) in og.edges.items()}, og.verts)
    assert abs(O.evaluate_expr(expr, js) - cd.value()) < 1e-8


def test_evaluator_enforces_the_triad_conditions():
    """Regression for a silent evaluator bug, found while adding the k=1
    exact layer and NOT specific to it.

    Every emitted identity -- 3j orthogonality for the bubble, Racah for
    the triangle -- is derived assuming the source vertex's triad exists,
    and the final theta is folded into theta_sign as a +-1 phase that
    presumes the SAME. Where a triad fails, the diagram is zero but the
    emitted factors are not, so the formula reported +-1 on vanishing
    diagrams: 186 of 729 labelings wrong on this very fixture before the
    fix, with no k=1 move involved.

    Swept over the full grid, formula and oracle now agree everywhere."""
    og = dumbbell()
    expr = O.solve_exact(og)
    vals = [S(1)/2, S(1), S(3)/2]
    bad = nonzero = 0
    for combo in itertools.product(vals, repeat=6):
        js = dict(zip("pqabcd", combo))
        cd = ClosedDiagram({lab: (t, h, js[lab])
                            for lab, (t, h) in og.edges.items()}, og.verts)
        want = cd.value()
        got = O.evaluate_expr(expr, js)
        nonzero += abs(want) > 1e-12
        bad += abs(got - want) > 1e-8
    assert bad == 0
    assert nonzero > 0


def test_flip_phase_is_textbook():
    assert O.FLIP_PHI == {"p": 1, "q": 1, "e": 1, "x": 1}
