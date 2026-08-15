"""The prism phase theorem, verified value-exact against the oracle.

Cases kept small (j <= 1) so the brute-force m-sums stay CI-fast; the
full 12-case sweep including j = 2 labels lives in scripts/verify_phase.py.
"""
from sympy import S
from sympy.physics.wigner import wigner_6j

from yutsis.oracle import prism
from yutsis.phase import prism_theorem

PL, AL, PR, AR = prism_theorem()


def s6(*a):
    try:
        return float(wigner_6j(*a))
    except ValueError:
        return 0.0


def check(ltri, k, j):
    jm = dict(zip(("l1", "l2", "l3"), ltri))
    jm.update(zip(("k1", "k2", "k3"), k))
    jm.update(zip(("j1", "j2", "j3"), j))
    pred = (PL.evaluate(jm) * PR.evaluate(jm)
            * s6(*[jm[a] for a in AL]) * s6(*[jm[a] for a in AR]))
    v = prism(*ltri, *k, *j).value()
    assert abs(v - pred) < 1e-9, (ltri, k, j, v, pred)


def test_all_integer_case():
    check((1, 1, 1), (1, 1, 1), (1, 1, 1))


def test_half_integer_case():
    h = S(1) / 2
    check((h, h, 0), (h, h, 0), (h, 0, h))


def test_mixed_half_integer_case():
    h = S(1) / 2
    check((S(3) / 2, h, 1), (h, h, 1), (h, 1, h))


def test_theorem_structure_is_opposite_edge_pairing():
    # l1 pairs with j3, l3 with j2, j1 with l2 -- not the naive pairing
    assert AL == ("l1", "l3", "j1", "j3", "j2", "l2")
    assert AR == ("k1", "k3", "j1", "j3", "j2", "k2")
