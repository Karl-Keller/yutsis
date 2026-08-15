"""Petersen (15j class): girth 5, the former wall. Fast structural test
for CI; the full exact-vs-oracle verification (a ~1M-term brute-force
sum) lives in scripts/verify_petersen.py."""
import time

from yutsis import solve
from yutsis.benchmarks import petersen


def test_petersen_solves_fast_with_targeted_flips():
    t0 = time.time()
    r = solve(petersen())
    assert not r.get("timeout")
    assert r["sums"] == 3 and r["sixj"] == 7
    assert time.time() - t0 < 5.0
