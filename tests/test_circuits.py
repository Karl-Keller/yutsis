"""Coupling-tree recoupling: matrix elements vs the state-level CG
oracle, and compiled gate sequences vs direct transforms."""
import random
from sympy import S
from yutsis.circuits import (matrix_element, overlap_oracle, calibrate,
                             random_valid_labeling, compile_recoupling,
                             gate_matrix)

from helpers import gram, identity, matmul, max_abs_diff

T3K = (("j1", "j2"), "j3")
T3B = ("j1", ("j2", "j3"))


def test_three_leaf_matrix_elements_match_state_oracle():
    rng = random.Random(7)
    done = 0
    while done < 4:
        jm = random_valid_labeling(T3K, T3B, rng)
        if jm is None:
            continue
        done += 1
        assert abs(matrix_element(T3K, T3B, jm)
                   - overlap_oracle(T3K, T3B, jm)) < 1e-8


def test_compiled_gates_compose_to_direct_transform():
    h = S(1) / 2
    leaf_j = {"j1": h, "j2": h, "j3": h, "j4": h}
    T1 = ((("j1", "j2"), "j3"), "j4")
    T2 = ("j1", ("j2", ("j3", "j4")))
    path, gates = compile_recoupling(T1, T2, leaf_j, S(1))
    assert len(path) == 3  # two elementary flips

    prod = gates[0]
    for g in gates[1:]:
        prod = matmul(g, prod)
    direct = gate_matrix(T1, T2, leaf_j, S(1))
    assert max_abs_diff(prod, direct) < 1e-12
    assert max_abs_diff(gram(direct), identity(len(direct))) < 1e-12
