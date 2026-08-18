"""The endgame pattern database: entries must be EXACT.

Admissibility here rests on exactness, not on an inequality -- if a
table entry were ever below the true optimum the A* guarantee would go
with it, and if it were above, results would silently change. So the
tests check the level-wise build against an independent uniform-cost
search, and check that a search driven by the table returns identical
costs.

Small tables only: n <= 8 builds in well under a second, and the
correctness argument does not depend on size. Larger tables are a
release-time concern (scripts/build_patterns.py).
"""
import pytest

from yutsis import benchmarks as B
from yutsis.patterns import (
    TruncatedEnumeration,
    build_table,
    enumerate_states,
    heuristic_with,
)
from yutsis.search import optimal_cost, solve

SEEDS = [B.tetrahedron(), B.prism(), B.k33(), B.cube(),
         B.random_cubic(8, seed=3)]
STATES = enumerate_states(8, SEEDS, budget=60.0)
TABLE = build_table(STATES)


def test_table_is_non_trivial():
    assert len(TABLE) > 20
    assert all(isinstance(v, int) for v in TABLE.values())


def test_every_entry_equals_an_independent_uniform_cost_search():
    """The level-wise Dijkstra build must agree with plain h=0 search --
    the ground truth the whole corpus machinery rests on."""
    checked = 0
    for cert, g in STATES.items():
        c = optimal_cost(g)
        if c is None:
            continue
        checked += 1
        assert TABLE[cert] == c, f"table {TABLE[cert]} != C* {c}"
    assert checked >= 20


@pytest.mark.parametrize("name,fn,cost", [
    ("tetrahedron", B.tetrahedron, 1),
    ("prism", B.prism, 2),
    ("k33", B.k33, 13),
    ("cube", B.cube, 14),
])
def test_published_costs_appear_in_the_table(name, fn, cost):
    assert TABLE[fn().canonical()] == cost


def test_table_backed_heuristic_preserves_costs():
    """Exact where it hits, rung one elsewhere: both are lower bounds,
    so the search order changes and the answer does not."""
    import yutsis.bounds as bd
    h = heuristic_with(TABLE, max_n=8)
    original = bd.sum_bound
    try:
        baseline = {n: solve(B.random_cubic(n, seed=n))["cost"]
                    for n in (8, 10, 12)}
        bd.sum_bound = h
        for n, want in baseline.items():
            assert solve(B.random_cubic(n, seed=n))["cost"] == want
    finally:
        bd.sum_bound = original


def test_heuristic_falls_back_above_the_cut():
    """A state larger than the table's reach must not raise, and must
    still produce an admissible value."""
    import yutsis.bounds as bd
    h = heuristic_with(TABLE, max_n=8)
    g = B.random_cubic(12, seed=5)
    assert h(g) == bd.sum_bound(g)


# ---------------------------------------------------------------------
# Enumeration: the closure is a correctness input, not a quality knob
# ---------------------------------------------------------------------

def _enumerate_dedup_on_pop(max_n, seeds, budget=60.0):
    """The pre-v0.11.3 walk: filter candidates against POPPED states.

    Kept here as the oracle for the in-queue de-duplication. It queues
    a state once per predecessor that reaches it, which is what made the
    n <= 18 queue 4,000,000 entries deep, but it closes over the same
    set -- and that is the claim under test."""
    import time
    from collections import deque

    from yutsis.search import successors
    seen, out, dq = set(), {}, deque(seeds)
    t0 = time.time()
    while dq and time.time() - t0 < budget:
        g = dq.popleft()
        if g.n > max_n:
            continue
        cert = g.canonical()
        if cert in seen:
            continue
        seen.add(cert)
        out[cert] = g
        for ng, *_rest in successors(g, blind=True):
            if ng.n <= max_n and ng.canonical() not in seen:
                dq.append(ng)
    return out


def test_in_queue_dedup_closes_over_the_same_states():
    """Behaviour is FIXED: de-duplicating earlier changes the queue, not
    the closure."""
    for max_n in (6, 8):
        want = _enumerate_dedup_on_pop(max_n, SEEDS)
        got = enumerate_states(max_n, SEEDS, budget=60.0)
        assert set(got) == set(want), f"closure differs at n<={max_n}"


def test_truncated_enumeration_raises_rather_than_returning_partial():
    """A cut-off state set yields table entries ABOVE the true optimum,
    which breaks admissibility silently. It must not pass quietly."""
    with pytest.raises(TruncatedEnumeration):
        enumerate_states(12, SEEDS, cap=5)


def test_truncation_is_still_available_when_asked_for_explicitly():
    partial = enumerate_states(12, SEEDS, cap=5, strict=False)
    assert 0 < len(partial) <= 5


def test_a_closed_enumeration_does_not_raise():
    assert len(enumerate_states(8, SEEDS, budget=120.0)) > 20
