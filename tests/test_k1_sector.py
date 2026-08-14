"""The k=1 sector: loop excision, and the terminal it does not yet reach.

A closed diagram is a rotational scalar, so a single line crossing a
separation must carry j = 0. Two lemmas, both oracle-verified
(docs/K1_SECTOR.md):

    K1a  sum_m (-1)^(k-m) 3j(k k c; m -m mc) = sqrt(2k+1) d(c,0) d(mc,0)
    K1b  3j(a b 0; ma mb 0) = d(a,b) d(ma,-mb) (-1)^(a-ma)/sqrt(2a+1)

Loop excision fuses them. Bridge cut needs the multi-component state
model and is the next PR.
"""
import itertools
import math

import pytest
from sympy import S

import yutsis.oriented as O
from yutsis.graph import Graph
from yutsis.moves import excise_loop, interchanges
from yutsis.oracle import ClosedDiagram
from yutsis.search import is_goal, optimal_cost, solve, successors

THETA_WITH_HANDLE = Graph([(1, 2, "a"), (1, 2, "b"), (1, 3, "c"),
                           (2, 3, "d"), (3, 4, "e"),
                           (4, 5, "f"), (4, 6, "g"),
                           (5, 6, "h"), (5, 6, "i")])
"""Two bubbles whose external legs each land on a common vertex. A
legitimate closed cubic diagram carrying no self-loop at the start.
Excising a bubble merges its externals into a tadpole -- which is what
made this the reproduction case for the k=1 defect."""

DUMBBELL_OF_TADPOLES = Graph([(3, 3, "c"), (3, 4, "e"), (4, 4, "f")])
"""Two tadpoles joined by a bridge. Two vertices and three edges, like a
theta -- which is why the old `n <= 2` goal test accepted it."""


def test_theta_with_handle_is_a_legitimate_closed_diagram():
    assert THETA_WITH_HANDLE.check_cubic()
    assert not any(u == v for u, v, _ in THETA_WITH_HANDLE.edges)


# --- what loop excision fixed ----------------------------------------

def test_goal_test_accepts_only_a_true_theta():
    """Regression for the silent-wrong-answer bug: the dumbbell has two
    vertices and three edges but is NOT the goal."""
    d = DUMBBELL_OF_TADPOLES
    assert d.n == 2 and len(d.edges) == 3
    assert not is_goal(d)
    assert not d.is_theta()
    assert is_goal(Graph([(1, 2, "x"), (1, 2, "y"), (1, 2, "z")]))


def test_handle_reduces_and_the_formula_carries_the_k1_constraints():
    """Previously this terminated on the dumbbell at cost 0 with two
    deltas and every j=0 constraint dropped. Now it reduces to a true
    theta and the formula states the k=1 physics explicitly."""
    r = solve(THETA_WITH_HANDLE)
    assert r is not None and not r["timeout"]
    assert [m[0] for m in r["moves"]] == ["bubble", "loop"]
    factors = " ".join(r["factors"])
    assert "loopw(" in factors        # the sqrt(2k+1) tadpole weight
    assert "delta(e,0)" in factors    # the j = 0 forcing (K1a)
    assert "sqrt(" in factors         # the 1/sqrt(2a+1) cap (K1b)
    assert r["sixj"] == 0 and r["sums"] == 0   # k=1 moves are FREE


def test_loop_excision_removes_two_vertices_for_free():
    g = Graph([(0, 0, "L"), (0, 1, "c"), (1, 2, "a"), (1, 3, "b"),
               (2, 3, "d"), (2, 4, "e"), (3, 5, "f"),
               (4, 5, "g"), (4, 5, "h")])
    assert g.excisable_loops() == ["0"]
    ng, fac, d6, ds, desc = excise_loop(g, "0")
    assert ng.n == g.n - 2 and ng.check_cubic()
    assert (d6, ds) == (0, 0)
    assert desc == ("loop", "0")


# --- the flip guard the k=1 sector forced -----------------------------

def test_flips_are_guarded_against_self_loop_legs():
    """The flip phase was fitted on a generic patch (distinct u,v,P,Q).
    A self-loop makes P == u, which that fit never covered. Unguarded,
    the dumbbell 'reduced' at cost 11 through unvalidated algebra."""
    assert interchanges(DUMBBELL_OF_TADPOLES) == []
    for ng, *_rest in interchanges(THETA_WITH_HANDLE):
        assert ng.check_cubic()


# --- one honest girth -------------------------------------------------

def test_true_girth_sees_one_cycles():
    g = Graph([(0, 0, "L"), (0, 1, "a"), (1, 2, "b"), (1, 3, "c"),
               (2, 3, "d"), (2, 4, "e"), (3, 5, "f"),
               (4, 5, "g"), (4, 5, "h")])
    assert g.true_girth() == 1                       # the tadpole
    assert Graph([(1, 2, "x"), (1, 2, "y"),
                  (1, 2, "z")]).true_girth() == 2    # parallel pair


def test_the_other_two_girth_functions_stay_as_they_are_by_design():
    """girth_lower() is the move-availability predicate Lemma 1 rests on
    and girth_cycle() skips loop edges; neither is a girth. They are left
    alone deliberately -- true_girth() is the one to reach for."""
    g = Graph([(0, 0, "L"), (0, 1, "a"), (1, 2, "b"), (1, 3, "c"),
               (2, 3, "d"), (2, 4, "e"), (3, 5, "f"),
               (4, 5, "g"), (4, 5, "h")])
    assert g.true_girth() == 1
    assert g.girth_lower() != 1        # reports by bubble/triangle only
    assert len(g.girth_cycle()) != 1   # skips the self-loop edge


# --- what is NOT fixed yet -------------------------------------------

def test_dumbbell_is_an_honest_dead_end_not_a_false_goal():
    """The loop-to-loop case is an irreducible k=1 terminal: capping it
    leaves a bare circle with no vertices, which needs the empty-diagram
    state model arriving with bridge cut. Until then it is a dead end --
    a loud failure rather than a silent wrong answer."""
    d = DUMBBELL_OF_TADPOLES
    assert d.self_loops() == ["3", "4"]
    assert d.excisable_loops() == []      # guarded, not mishandled
    assert successors(d, blind=True) == []
    assert solve(d) is None
    assert optimal_cost(d) is None


# --- the exact layer --------------------------------------------------

HANDLE_EDGES = {"a": ("1", "2"), "b": ("1", "2"), "c": ("1", "3"),
                "d": ("2", "3"), "e": ("3", "4"), "f": ("4", "5"),
                "g": ("4", "6"), "h": ("5", "6"), "i": ("5", "6")}
HANDLE_VERTS = {"1": ("a", "b", "c"), "2": ("a", "b", "d"),
                "3": ("c", "d", "e"), "4": ("e", "f", "g"),
                "5": ("f", "h", "i"), "6": ("g", "h", "i")}


def _oracle(og, js):
    return ClosedDiagram({lab: (t, h, js[lab])
                          for lab, (t, h) in og.edges.items()},
                         og.verts).value()


def test_exact_loop_excision_canonical_phase_is_plus_one():
    """Measured, not assumed: the canonical tadpole
    (v slots (k,k,c), c: v->w, a and b tailed at w) excises with factor
    exactly sqrt(2k+1)/sqrt(2a+1) and NO residual sign."""
    og = O.OGraph({"k": ("v", "v"), "c": ("v", "w"), "a": ("w", "x"),
                   "b": ("w", "y"), "p": ("x", "y"), "q": ("x", "y")},
                  {"v": ("k", "k", "c"), "w": ("c", "a", "b"),
                   "x": ("a", "p", "q"), "y": ("b", "p", "q")})
    new_og, phase, zero, (da, db), snum, sden = O.excise_loop_exact(og, "v")
    assert (zero, snum, sden) == ("c", "k", "a")
    assert {da, db} == {"a", "b"}
    js = {"k": S(1), "c": S(0), "a": S(1), "b": S(1),
          "p": S(1), "q": S(1)}
    assert phase.evaluate(js) == 1


@pytest.mark.parametrize("wslots", [("c", "a", "b"), ("a", "c", "b"),
                                    ("a", "b", "c")])
@pytest.mark.parametrize("flip", ["c", "a", "b", None])
def test_exact_loop_excision_matches_oracle_in_every_configuration(
        wslots, flip):
    """The normalization must reproduce the oracle for any slot order and
    any orientation, not just the canonical patch. (The full 576-config
    x 5-labeling sweep runs 0 mismatches; this is the CI slice.)"""
    ends = {"c": ("v", "w"), "a": ("w", "x"), "b": ("w", "y")}
    if flip:
        ends[flip] = ends[flip][::-1]
    og = O.OGraph({"k": ("v", "v"), **ends,
                   "p": ("x", "y"), "q": ("x", "y")},
                  {"v": ("k", "k", "c"), "w": wslots,
                   "x": ("a", "p", "q"), "y": ("b", "p", "q")})
    new_og, phase, _z, _d, snum, sden = O.excise_loop_exact(og, "v")
    for k, a, p, q in [(S(1), S(1), S(1), S(1)),
                       (S(1)/2, S(1), S(1)/2, S(1)/2),
                       (S(3)/2, S(1)/2, S(1), S(1)/2)]:
        js = {"k": k, "c": S(0), "a": a, "b": a, "p": p, "q": q}
        before, after = _oracle(og, js), _oracle(new_og, js)
        factor = math.sqrt(float(2 * k + 1)) / math.sqrt(float(2 * a + 1))
        assert abs(before - phase.evaluate(js) * factor * after) < 1e-9


def test_handle_fully_signed_vs_oracle():
    """End-to-end: the k=1 path emits a formula that matches brute-force
    magnetic summation across the labeling grid."""
    og = O.OGraph(HANDLE_EDGES, HANDLE_VERTS)
    expr = O.solve_exact(og)
    assert expr is not None
    assert expr["zeros"] == ["e"]          # the j = 0 forcing
    assert expr["sqrt_num"] and expr["sqrt_den"]
    nonzero = 0
    for a, c, f, h in itertools.product([S(1)/2, S(1), S(3)/2], repeat=4):
        js = dict(a=a, b=a, c=c, d=c, e=S(0), f=f, g=f, h=h, i=h)
        got, want = O.evaluate_expr(expr, js), _oracle(og, js)
        assert abs(got - want) < 1e-9, js
        nonzero += abs(want) > 1e-12
    assert nonzero > 0, "grid degenerate -- all labelings vanished"


def test_exact_formula_vanishes_off_j_zero():
    og = O.OGraph(HANDLE_EDGES, HANDLE_VERTS)
    expr = O.solve_exact(og)
    js = dict(a=S(1)/2, b=S(1)/2, c=S(1), d=S(1), e=S(1),
              f=S(1), g=S(1), h=S(1)/2, i=S(1)/2)
    assert O.evaluate_expr(expr, js) == 0.0
    assert abs(_oracle(og, js)) < 1e-12
