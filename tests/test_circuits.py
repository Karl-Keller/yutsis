"""Coupling-tree recoupling: matrix elements vs the state-level CG
oracle, and compiled gate sequences vs direct transforms."""
import random
from sympy import S
from yutsis.circuits import (matrix_element, overlap_oracle, calibrate,
                             random_valid_labeling, compile_recoupling,
                             gate_matrix)

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

    def matmul(A, B):
        return [[sum(A[i][k] * B[k][j] for k in range(len(B)))
                 for j in range(len(B[0]))] for i in range(len(A))]

    prod = gates[0]
    for g in gates[1:]:
        prod = matmul(g, prod)
    direct = gate_matrix(T1, T2, leaf_j, S(1))
    err = max(abs(prod[i][j] - direct[i][j])
              for i in range(len(prod)) for j in range(len(prod[0])))
    assert err < 1e-12
    n = len(direct)
    utu = [[sum(direct[k][i] * direct[k][j] for k in range(n))
            for j in range(n)] for i in range(n)]
    uerr = max(abs(utu[i][j] - (1.0 if i == j else 0.0))
               for i in range(n) for j in range(n))
    assert uerr < 1e-12
