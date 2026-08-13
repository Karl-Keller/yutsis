"""End-to-end fully signed formulas: solve_exact vs ground truth."""
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


def test_flip_phase_is_textbook():
    assert O.FLIP_PHI == {"p": 1, "q": 1, "e": 1, "x": 1}
