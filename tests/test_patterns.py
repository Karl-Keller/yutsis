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
from yutsis.patterns import build_table, enumerate_states, heuristic_with
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
