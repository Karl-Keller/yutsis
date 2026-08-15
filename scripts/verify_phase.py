"""Full prism-phase verification sweep (slow: includes j = 2 labels).

Regenerates random triad-valid prism labelings, evaluates each closed
diagram by brute-force magnetic summation, and checks the phase engine's
theorem value-exactly. Run before releases; CI runs the fast subset in
tests/test_phase.py.
"""
import random

from sympy import S
from sympy.physics.wigner import wigner_6j

from yutsis.oracle import prism
from yutsis.phase import prism_theorem

PL, AL, PR, AR = prism_theorem()
print("theorem:", PL, "x", PR, "x 6j", AL, "x 6j", AR)


def tri_ok(a, b, c):
    return abs(a - b) <= c <= a + b and int(2 * (a + b + c)) % 2 == 0


def valid(ltri, k, j):
    l1, l2, l3 = ltri
    k1, k2, k3 = k
    j1, j2, j3 = j
    return all([tri_ok(l1, l3, j1), tri_ok(l2, l1, j2), tri_ok(l3, l2, j3),
                tri_ok(k3, k1, j1), tri_ok(k1, k2, j2), tri_ok(k2, k3, j3)])


def s6(*a):
    try:
        return float(wigner_6j(*a))
    except ValueError:
        return 0.0


rng = random.Random(3)
half = [S(m) / 2 for m in range(0, 5)]
ok = 0
while ok < 12:
    ltri = tuple(rng.choice(half) for _ in range(3))
    k = tuple(rng.choice(half) for _ in range(3))
    j = tuple(rng.choice(half) for _ in range(3))
    if not valid(ltri, k, j):
        continue
    jm = dict(zip(("l1", "l2", "l3"), ltri))
    jm.update(zip(("k1", "k2", "k3"), k))
    jm.update(zip(("j1", "j2", "j3"), j))
    pred = (PL.evaluate(jm) * PR.evaluate(jm)
            * s6(*[jm[a] for a in AL]) * s6(*[jm[a] for a in AR]))
    if abs(pred) < 1e-12:
        continue
    v = prism(*ltri, *k, *j).value()
    assert abs(v - pred) < 1e-9, (ltri, k, j, v, pred)
    ok += 1
    print(f"  OK  l={ltri} k={k} j={j}  value={v:+.6f}")
print(f"{ok}/12 value-exact")
