"""Admissibility tests for yutsis.bounds.

This corpus is to heuristics what the magnetic-sum oracle is to
formulas: ground truth, one layer up. C* comes from uniform-cost search
(h = 0) over the BLIND move set, so it depends on no heuristic and no
move-ordering claim.

Derivation and proof status: docs/BOUNDS.md.
"""
from collections import deque

import pytest

from yutsis import benchmarks as B
from yutsis.bounds import (has_bridge, has_self_loop, heuristic,
                           sixj_bound_decomposition, sum_bound,
                           three_edge_pieces)
from yutsis.graph import Graph
from yutsis.search import optimal_cost, successors

# --- the two counterexamples that void the v0.6.0 guarantee -----------
# Neither is producible by random_cubic (it rejects parallel edges),
# which is why no test ever surfaced them.

BUBBLE_COUNTEREXAMPLE = Graph([(1, 2, "a"), (1, 2, "b"),
                               (3, 4, "c"), (3, 4, "d"),
                               (1, 3, "e"), (2, 4, "f")])
"""n=4 multigraph. Excising bubble (1,2) joins the external stubs into
(3,4,e), landing on theta: C* = 0. The v0.6.0 bound claimed 1."""

TWO_DIAMOND_COUNTEREXAMPLE = Graph([(0, 1, "j0"), (0, 2, "j1"), (0, 3, "j2"),
                                    (1, 2, "j3"), (1, 3, "j4"),
                                    (2, 4, "j5"), (3, 5, "j6"),
                                    (4, 6, "j7"), (4, 7, "j8"),
                                    (5, 6, "j9"), (5, 7, "j10"),
                                    (6, 7, "j11")])
"""n=8 SIMPLE graph: two K4-minus-an-edge blocks joined by a 2-cut.
Contracting a diamond's triangle births a parallel pair; excising it
drops n by 4 for one 6j. C* = 2; the v0.6.0 bound claimed 3. Being
simple and bubble-free, it shows that restricting attention to
bubble-free states does NOT rescue the old bound."""


def v060_heuristic(g):
    """The shipped v0.6.0 heuristic, kept verbatim so its defect stays
    pinned and cannot be quietly reintroduced."""
    h = max(0, (g.n - 2) // 2)
    if g.n > 2 and g.girth_lower() >= 4:
        h += 10
    return h


def reachable(seeds, cap):
    """BFS the real move graph. Multigraph, self-loop and bridge states
    are included on purpose: that is where the old bound broke."""
    out, seen, dq = [], set(), deque()
    for g in seeds:
        key = g.canonical()
        if key not in seen:
            seen.add(key)
            dq.append(g)
    while dq and len(out) < cap:
        cur = dq.popleft()
        out.append(cur)
        for ng, *_rest in successors(cur, blind=True):
            key = ng.canonical()
            if key not in seen:
                seen.add(key)
                dq.append(ng)
    return out


CORPUS = reachable([BUBBLE_COUNTEREXAMPLE, TWO_DIAMOND_COUNTEREXAMPLE,
                    B.tetrahedron(), B.prism(), B.k33(),
                    B.random_cubic(8, seed=1), B.random_cubic(8, seed=2)],
                   cap=150)


# --- the counterexamples, pinned -------------------------------------

@pytest.mark.parametrize("g,c_star,old", [
    (BUBBLE_COUNTEREXAMPLE, 0, 1),
    (TWO_DIAMOND_COUNTEREXAMPLE, 2, 3),
])
def test_counterexamples_are_real_and_now_admissible(g, c_star, old):
    assert g.check_cubic()
    assert optimal_cost(g) == c_star          # ground truth
    assert v060_heuristic(g) == old           # the shipped bound...
    assert old > c_star                       # ...was inadmissible
    assert heuristic(g) <= c_star             # the new one is not


def test_two_diamond_is_simple_and_bubble_free():
    """Scoping admissibility to bubble-free simple states would NOT have
    been a valid rescue -- this state is both, and still broke."""
    g = TWO_DIAMOND_COUNTEREXAMPLE
    assert g.bubbles() == []
    assert not has_self_loop(g)
    assert len(set((u, v) for u, v, _ in g.edges)) == len(g.edges)


# --- admissibility of the shipped heuristic --------------------------

def test_admissible_over_reachable_corpus():
    checked = 0
    for g in CORPUS:
        if g.n > 8:
            continue
        c_star = optimal_cost(g)
        if c_star is None:
            continue
        checked += 1
        assert heuristic(g) <= c_star, f"inadmissible on {g.edges}"
    assert checked >= 20


def test_step_inequality_holds_for_shipped_heuristic():
    """The induction step. The shipped 6j term is 0, so this reduces to
    checking the summation term never over-charges -- but it is asserted
    over the real move graph rather than argued."""
    moves = 0
    for g in CORPUS:
        h = heuristic(g)
        for ng, _fac, d6, ds, _desc in successors(g, blind=True):
            moves += 1
            assert h <= heuristic(ng) + d6 + 10 * ds, \
                f"step broken at {g.edges}"
    assert moves > 500


def test_old_heuristic_was_broadly_inadmissible():
    """Pins the scale of the defect: this was not an exotic corner."""
    viol = 0
    for g in CORPUS:
        if g.n > 8:
            continue
        c_star = optimal_cost(g)
        if c_star is not None and v060_heuristic(g) > c_star:
            viol += 1
    assert viol > 0


# --- the opt-in decomposition bound, and its documented gap ----------

def test_decomposition_gets_the_counterexamples_right():
    """It is the derived answer, and it is exact on both."""
    assert sixj_bound_decomposition(BUBBLE_COUNTEREXAMPLE) == 0
    assert sixj_bound_decomposition(TWO_DIAMOND_COUNTEREXAMPLE) == 2
    assert len(three_edge_pieces(TWO_DIAMOND_COUNTEREXAMPLE)) == 2


def test_decomposition_is_admissible_where_measured():
    for g in CORPUS:
        if g.n > 8:
            continue
        c_star = optimal_cost(g)
        if c_star is not None:
            assert sixj_bound_decomposition(g) <= c_star


def test_decomposition_step_gap_is_real_and_confined_to_degenerate_states():
    """Pins WHY the decomposition is not the shipped default: its
    potential-function proof fails, and fails only where a move can
    relocate a self-loop or bridge between pieces.

    If this test ever finds a violation at a clean state, the
    documented boundary in docs/BOUNDS.md is wrong."""
    for g in CORPUS:
        phi = sixj_bound_decomposition(g)
        for ng, _fac, d6, _ds, _desc in successors(g, blind=True):
            if phi > sixj_bound_decomposition(ng) + d6:
                assert (has_self_loop(g) or has_bridge(g)
                        or has_self_loop(ng) or has_bridge(ng)), \
                    f"step broken at a CLEAN state: {g.edges}"


def test_shipped_heuristic_never_exceeds_decomposition_variant():
    """Dominance, stated against the corrected baseline: the shipped
    bound is the conservative one of the two everywhere."""
    for g in CORPUS:
        assert heuristic(g) <= sixj_bound_decomposition(g) + sum_bound(g)


# --- benchmarks -------------------------------------------------------

@pytest.mark.parametrize("name,fn", [
    ("tetrahedron", B.tetrahedron), ("prism", B.prism),
    ("k33", B.k33), ("cube", B.cube), ("petersen", B.petersen),
])
def test_benchmark_roots_are_three_edge_connected(name, fn):
    assert len(three_edge_pieces(fn())) == 1


@pytest.mark.parametrize("name,fn,cost", [
    ("tetrahedron", B.tetrahedron, 1),
    ("prism", B.prism, 2),
    ("k33", B.k33, 13),
])
def test_published_costs_recertified(name, fn, cost):
    """v0.6.0's guarantee was void, but its results were correct: the
    published costs equal C* computed with h = 0 over blind moves.
    (cube and petersen are re-certified in scripts/certify_bounds.py.)"""
    assert optimal_cost(fn()) == cost


def test_petersen_minimum_is_three_summations():
    """Finding 3, prong 1, CLOSED. C* = 37 over the UNRESTRICTED move
    set. By Lemma 0, cost = (n-2)/2 - B + 11*S = 4 - B + 11*S, so any
    S = 2 reduction would cost at most 26. It costs 37, so S = 2 is
    impossible and the shipped 7-6j / 3-sum formula is optimal."""
    g = B.petersen()
    assert optimal_cost(g, max_expanded=2_000_000) == 37
    assert 4 + 11 * 2 < 37
