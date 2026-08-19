"""Oracle the wrapper before using it: w=1 must reproduce solve()."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wastar import search

from yutsis import benchmarks as B
from yutsis.bounds import sum_bound
from yutsis.search import solve

bad = 0
for n in (8, 10, 12, 16, 20, 22, 24, 26, 30):
    g = B.random_cubic(n, seed=7 * n)
    a = solve(g, max_expanded=200_000)
    b = search(g, sum_bound, w=1, cap=200_000)
    same = (a["cost"] == b["cost"]) and (a["expanded"] == b["expanded"])
    bad += not same
    print(f"n={n:>3}: solve cost={a['cost']:>4} exp={a['expanded']:>6} | "
          f"wrapper cost={b['cost']:>4} exp={b['expanded']:>6} | "
          f"{'OK' if same else 'MISMATCH'}")
for name, g in (("petersen", B.petersen()), ("cube", B.cube()), ("k33", B.k33())):
    a = solve(g)
    b = search(g, sum_bound, w=1)
    ok = a["cost"] == b["cost"] == {"petersen": 37, "cube": 14, "k33": 13}[name]
    bad += not ok
    print(f"{name}: {b['cost']} {'OK' if ok else 'MISMATCH'}")
print("MISMATCHES:", bad)
sys.exit(1 if bad else 0)
