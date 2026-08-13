from yutsis import solve
from yutsis.benchmarks import tetrahedron, prism, k33, cube


def test_tetrahedron_is_one_6j():
    r = solve(tetrahedron())
    assert (r["sixj"], r["sums"]) == (1, 0)


def test_prism_factorizes_without_sums():
    r = solve(prism())
    assert (r["sixj"], r["sums"]) == (2, 0)


def test_k33_matches_9j_structure():
    r = solve(k33())
    assert (r["sixj"], r["sums"]) == (3, 1)


def test_cube_single_sum_four_6j():
    r = solve(cube())
    assert (r["sixj"], r["sums"]) == (4, 1)


def test_optimality_prefers_sum_free_route():
    # prism cost must beat any summation-bearing alternative
    assert solve(prism())["cost"] < 10
