"""Oriented reduction with exact signs, validated against the oracle."""
from sympy import S
from sympy.physics.wigner import wigner_6j

from yutsis.oracle import prism
from yutsis.oriented import reduce_prism_exact


def s6(*a):
    try:
        return float(wigner_6j(*a))
    except ValueError:
        return 0.0


PHASE, FACTORS = reduce_prism_exact()


def check(ltri, k, j):
    jm = dict(zip(("l1", "l2", "l3"), ltri))
    jm.update(zip(("k1", "k2", "k3"), k))
    jm.update(zip(("j1", "j2", "j3"), j))
    pred = (PHASE.evaluate(jm)
            * s6(*[jm[x] for x in FACTORS[0]])
            * s6(*[jm[x] for x in FACTORS[1]]))
    assert abs(prism(*ltri, *k, *j).value() - pred) < 1e-9


def test_oriented_prism_all_integer():
    check((1, 1, 1), (1, 1, 1), (1, 1, 1))


def test_oriented_prism_half_integer():
    h = S(1) / 2
    check((h, h, 0), (h, h, 0), (h, 0, h))


def test_oriented_prism_mixed():
    h = S(1) / 2
    check((S(3) / 2, h, 1), (h, h, 1), (h, 1, h))
