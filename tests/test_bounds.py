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
from yutsis.bounds import (
    flip_free_reducible,
    has_bridge,
    has_self_loop,
    heuristic,
    sixj_bound_decomposition,
    sum_bound,
    three_edge_pieces,
)
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


TADPOLE_STATE = Graph([(0, 3, "x_j13"), (0, 8, "j8"), (0, 9, "j1"),
                       (1, 5, "j6"), (1, 7, "j9"), (1, 8, "j11"),
                       (2, 2, "j5"), (2, 8, "x_j12"),
                       (3, 5, "j14"), (3, 7, "j10"),
                       (5, 9, "j4"), (7, 9, "j0")])
"""n=8 reachable state carrying a self-loop at vertex 2, with no bubble
and no triangle. Its true girth is 1, but girth_lower() reports 4, so it
receives the SUM_PENALTY bonus -- correctly, because every successor is
a flip. Pins the degenerate-state clause of Lemma 1 (docs/BOUNDS.md)."""


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


# --- Lemma 1: the summation bound rests on move availability ---------

def test_girth_lower_is_a_move_availability_predicate():
    """The proof of Lemma 1 uses only this equivalence, never a cycle
    length. Pinned so the bound's justification cannot drift."""
    for g in CORPUS:
        assert (g.girth_lower() >= 4) == (not g.bubbles()
                                          and not g.triangles())


def test_girth_lower_is_not_a_girth_bound_on_self_loop_states():
    """Trap documented in docs/BOUNDS.md: a tadpole is a 1-cycle, but
    girth_lower() reports 4. Sound for Lemma 1, WRONG for any future
    bound that wants an actual girth.

    The girth FUNCTIONS are compared against each other in
    test_k1_sector.py; this pins the specific state Lemma 1 relies on."""
    assert has_self_loop(TADPOLE_STATE)          # true girth is 1
    assert TADPOLE_STATE.girth_lower() == 4      # ...yet reports 4
    assert TADPOLE_STATE.true_girth() == 1


def test_reducibility_catches_what_move_availability_missed():
    """THE COUPLING, and then its successor.

    Before the k=1 sector this state had only flips as successors, so
    Lemma 1 charged it SUM_PENALTY. Loop excision made a free move
    available and the move-AVAILABILITY test then said no summation was
    owed -- admissible, but wrong in fact: the state's true optimum is
    13 = 3 sixj + one summation.

    The reducibility test asks the right question. A free move applies,
    but no sequence of free and triangle moves reaches a terminal, so a
    flip is unavoidable and the bound fires. This is exactly the case a
    pattern match on the current state cannot see."""
    g = TADPOLE_STATE
    assert g.check_cubic()
    assert has_self_loop(g)
    assert g.excisable_loops()            # a free move DOES apply...
    assert not flip_free_reducible(g)     # ...but it cannot finish alone
    assert sum_bound(g) == 10
    assert sum_bound(g) <= optimal_cost(g) == 13


def test_reducibility_bound_never_below_the_move_availability_test():
    """Proof, pinned: if no vertex-removing move applies and g is not
    terminal then _flip_free_children is empty, the recursion returns
    False, and the bound fires. So it can never be smaller than the test
    it replaced -- and it is frequently larger."""
    fired_old = fired_new = 0
    for g in CORPUS:
        old_fires = not (g.is_terminal() or g.bubbles() or g.triangles()
                         or g.excisable_loops() or g.cuttable_bridges())
        new_fires = sum_bound(g) > 0
        assert not (old_fires and not new_fires), "new bound is smaller"
        fired_old += old_fires
        fired_new += new_fires
    assert fired_new > fired_old


# --- the opt-in decomposition bound, and its documented gap ----------

def test_decomposition_gets_the_counterexamples_right():
    """It is the derived answer, and it is exact on both."""
    assert sixj_bound_decomposition(BUBBLE_COUNTEREXAMPLE) == 0
    assert sixj_bound_decomposition(TWO_DIAMOND_COUNTEREXAMPLE) == 2
    assert len(three_edge_pieces(TWO_DIAMOND_COUNTEREXAMPLE)) == 2


def test_decomposition_is_admissible_on_the_small_ci_corpus():
    """Scope matters: over the WIDER corpus in scripts/certify_bounds.py
    this bound has 8 admissibility violations as of the k=1 sector. It
    still holds here, and pinning that keeps the boundary honest rather
    than implying the bound is safe."""
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


# --- Lemma 3: the merge lemma ----------------------------------------

def test_merge_lemma_cost_is_label_independent():
    """Lemma 3 (docs/BOUNDS.md). States are deduped by an ANONYMOUS
    certificate, which is sound only because C* depends on the topology
    and not the labels. Relabelling must change neither.

    This is the state-space collapse the whole search rests on, so it is
    checked rather than asserted."""
    import random

    rng = random.Random(20260814)
    for g in [B.tetrahedron(), B.prism(), B.k33(), B.cube(),
              B.random_cubic(8, seed=3), TWO_DIAMOND_COUNTEREXAMPLE]:
        labels = [lab for _u, _v, lab in g.edges]
        shuffled = labels[:]
        rng.shuffle(shuffled)
        mapping = dict(zip(labels, shuffled))
        relabelled = Graph([(u, v, mapping[lab]) for u, v, lab in g.edges])
        assert relabelled.canonical() == g.canonical()
        assert optimal_cost(relabelled) == optimal_cost(g)


def test_merge_lemma_holds_under_vertex_renaming():
    """The certificate is an isomorphism invariant, so renaming vertices
    must not change it either."""
    g = B.prism()
    renamed = Graph([(f"v{u}", f"v{v}", lab) for u, v, lab in g.edges])
    assert renamed.canonical() == g.canonical()
    assert optimal_cost(renamed) == optimal_cost(g)


# --- Lemma 5: the gated decomposition bound --------------------------

def test_gated_bound_is_admissible_on_the_corpus():
    """It is the sharpest admissible 6j term found: 0 violations where
    the ungated version has 8, all of which sit at states carrying both
    a self-loop and a bridge."""
    from yutsis.bounds import sixj_bound_gated
    checked = 0
    for g in CORPUS:
        if g.n > 8:
            continue
        c_star = optimal_cost(g)
        if c_star is None:
            continue
        checked += 1
        assert sixj_bound_gated(g) + sum_bound(g) <= c_star
    assert checked >= 20


def test_gated_bound_discriminates_more_than_the_shipped_one():
    """Lemma 4 named discrimination as the gap; this bound closes it and
    still buys no expansions (Lemma 5), because the variation it
    resolves is in the 6j count, below the SUM_PENALTY granularity that
    reorders the queue."""
    from yutsis.bounds import sixj_bound_gated
    shipped = {heuristic(g) for g in CORPUS}
    gated = {sixj_bound_gated(g) + sum_bound(g) for g in CORPUS}
    assert len(gated) > len(shipped)


def test_gated_bound_is_not_wired_into_the_heuristic():
    """Deliberate, on the v0.6.1 reasoning: a certified-but-unproven
    bound that cannot change a decision is not worth the risk."""
    from yutsis.bounds import sixj_bound_gated
    disagreeing = [g for g in CORPUS
                   if sixj_bound_gated(g) + sum_bound(g) != heuristic(g)]
    assert disagreeing, "gated bound should differ somewhere"
    for g in disagreeing:
        assert heuristic(g) == sum_bound(g)


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
