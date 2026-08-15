from yutsis import solve
from yutsis.benchmarks import cube, k33, prism, tetrahedron


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


def test_triangle_factor_uses_opposite_edge_pairing():
    # Reducing the prism's left triangle must pair inside edges with the
    # legs OPPOSITE them -- the structure proved by the prism phase
    # theorem. Column pairs for {top; bottom} are (top_i, bottom_i).
    r = solve(prism())
    fac = r["factors"][0]
    args = fac[len("sixj("):-1].split(",")
    pairs = {frozenset((args[i], args[i + 3])) for i in range(3)}
    theorem_pairs = {frozenset(("l1", "j3")), frozenset(("l3", "j2")),
                     frozenset(("l2", "j1"))}
    assert pairs == theorem_pairs, fac
