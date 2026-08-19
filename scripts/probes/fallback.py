"""What does a suboptimal search actually give up at scale?

Above n ~ 36 the optimum is not computable, so "excess" cannot be
measured directly. But with an admissible h, the minimum f on A*'s
frontier is a LOWER BOUND on C* even when A* is cut off, and a weighted
run that finishes gives an UPPER bound. The gap between them is a
CERTIFIED bracket on what the fast answer gives up -- no optimum needed.

Arms: w=1 (optimal / lower bound), w=2 and w=5 over the n<=18 table,
and w=5 over the shipped bound, which is the existing greedy mode.
"""
import os
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wastar import search

from yutsis import benchmarks as B
from yutsis.bounds import sum_bound
from yutsis.patterns import heuristic_with

SP = os.environ.get("YUTSIS_TABLES",
                    str(Path(__file__).resolve().parent / "tables"))
tab = pickle.load(open(f"{SP}/pdb18.pkl", "rb"))
H = heuristic_with(tab, max_n=18)
CAP = 120_000

print(f"{'n':>4} {'3n/2':>6} | {'C* or LB':>9} {'exp':>7} {'sec':>7} | "
      f"{'w2 cost':>8} {'sec':>7} | {'w5 cost':>8} {'sec':>7} | "
      f"{'bracket':>9} | {'old greedy':>10}", flush=True)
for n in (30, 34, 36, 40, 44, 50, 60):
    g = B.random_cubic(n, seed=7 * n)
    t0 = time.perf_counter()
    r1 = search(g, H, w=1, cap=CAP)
    t1 = time.perf_counter() - t0
    lb = r1["lb"]
    exact = not r1["timeout"]
    rows = []
    for w in (2, 5):
        t0 = time.perf_counter()
        r = search(g, H, w=w, cap=CAP)
        rows.append((r, time.perf_counter() - t0))
    t0 = time.perf_counter()
    rg = search(g, sum_bound, w=5, cap=CAP)
    tg = time.perf_counter() - t0
    best = min([r["cost"] for r, _ in rows if r["cost"] is not None] or [None],
               default=None)
    if lb is None or best is None:
        br = "--"
    elif exact:
        br = f"{100*(best-lb)/max(1,lb):+.0f}% exact"
    else:
        br = f"<={100*(best-lb)/max(1,lb):.0f}%"
    c2 = rows[0][0]["cost"]
    c5 = rows[1][0]["cost"]
    print(f"{n:>4} {3*n//2:>5}j | {str(lb):>9} {r1['expanded']:>7} {t1:>7.1f} | "
          f"{str(c2):>8} {rows[0][1]:>7.1f} | {str(c5):>8} {rows[1][1]:>7.1f} | "
          f"{br:>9} | {str(rg['cost']) + (' WALL' if rg['timeout'] else ''):>10}",
          flush=True)
