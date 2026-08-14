"""The k=1 sector: known incompleteness, pinned as executable findings.

A closed diagram is a rotational scalar, so a single line crossing a
separation must carry j = 0. The engine has moves for k = 2 (bubble, a
delta) and k = 3 (triangle, a 6j factorization) but none for k = 1, and
so it mishandles bridges and self-loops rather than dissolving them.

These tests are xfail(strict=True): they FAIL the suite if they ever
start passing, which is exactly the signal wanted when loop excision and
bridge cut land. See docs/NEXT_STEPS.md, "The k=1 sector".
"""
import pytest

import yutsis.oriented as O
from yutsis.graph import Graph
from yutsis.search import is_goal, solve

THETA_WITH_HANDLE = Graph([(1, 2, "a"), (1, 2, "b"), (1, 3, "c"),
                           (2, 3, "d"), (3, 4, "e"),
                           (4, 5, "f"), (4, 6, "g"),
                           (5, 6, "h"), (5, 6, "i")])
"""Two bubbles whose external legs each land on a common vertex. A
physically legitimate closed cubic diagram, carrying no self-loop at the
start. Excising both bubbles merges each pair of externals into a
self-loop, landing on the dumbbell (3,3) (3,4) (4,4)."""

DUMBBELL_OF_TADPOLES = Graph([(3, 3, "c"), (3, 4, "e"), (4, 4, "f")])
"""Two tadpoles joined by a bridge. Two vertices and three edges, like a
theta -- which is why both the goal test and theta_sign accept it."""


def test_theta_with_handle_is_a_legitimate_closed_diagram():
    assert THETA_WITH_HANDLE.check_cubic()
    assert not any(u == v for u, v, _ in THETA_WITH_HANDLE.edges)


def test_reduction_reaches_the_dumbbell_of_tadpoles():
    """Not a bug in itself -- the setup for the two below."""
    r = solve(THETA_WITH_HANDLE)
    assert r is not None and not r["timeout"]
    assert [m[0] for m in r["moves"]] == ["bubble", "bubble"]


@pytest.mark.xfail(strict=True,
                   reason="k=1 sector missing: is_goal is n<=2, so two "
                          "tadpoles joined by a bridge are accepted as "
                          "the goal. Fix with loop excision + bridge cut.")
def test_goal_test_accepts_only_a_true_theta():
    g = DUMBBELL_OF_TADPOLES
    assert g.n == 2 and len(g.edges) == 3   # looks like a theta...
    assert not is_goal(g)                   # ...but must not be the goal


@pytest.mark.xfail(strict=True,
                   reason="k=1 sector missing: solve() terminates on the "
                          "dumbbell and emits no delta(j,0) and no loop "
                          "weight, so the formula silently drops the "
                          "j=0 constraints.")
def test_formula_carries_the_k1_constraints():
    r = solve(THETA_WITH_HANDLE)
    factors = " ".join(r["factors"])
    assert "0" in factors and r["cost"] > 0


@pytest.mark.xfail(strict=True,
                   reason="k=1 sector missing: theta_sign's guard "
                          "(n==2 and 3 edges) passes on two loops plus a "
                          "bridge, then raises ValueError.")
def test_exact_path_handles_the_handle():
    edges = {"a": ("1", "2"), "b": ("1", "2"), "c": ("1", "3"),
             "d": ("2", "3"), "e": ("3", "4"), "f": ("4", "5"),
             "g": ("4", "6"), "h": ("5", "6"), "i": ("5", "6")}
    verts = {"1": ("a", "b", "c"), "2": ("a", "b", "d"),
             "3": ("c", "d", "e"), "4": ("e", "f", "g"),
             "5": ("f", "h", "i"), "6": ("g", "h", "i")}
    O.solve_exact(O.OGraph(edges, verts))


@pytest.mark.xfail(strict=True,
                   reason="both girth functions are blind to 1-cycles: "
                          "girth_lower() reports by bubble/triangle "
                          "presence, girth_cycle() skips self-loop edges. "
                          "Fix with one central true_girth().")
def test_girth_functions_see_one_cycles():
    g = Graph([(0, 0, "L"), (0, 1, "a"), (1, 2, "b"), (1, 3, "c"),
               (2, 3, "d"), (2, 4, "e"), (3, 5, "f"),
               (4, 5, "g"), (4, 5, "h")])
    assert any(u == v for u, v, _ in g.edges)   # true girth is 1
    assert g.girth_lower() == 1
    assert len(g.girth_cycle()) == 1


def test_no_dead_ends_was_verified():
    """Records what was NOT found, so the branch does not chase it: a
    sweep of 786 reachable states found no state with n > 2 and no
    applicable move. The defect is at the goal test, not the frontier."""
    from yutsis.search import successors
    assert successors(THETA_WITH_HANDLE, blind=True)
    assert successors(DUMBBELL_OF_TADPOLES, blind=True) is not None
