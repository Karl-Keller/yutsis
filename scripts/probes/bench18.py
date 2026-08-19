"""Price the n<=18 table, and split the gain into its two causes.

Four arms:
  base      shipped rung-one bound, no table          (v0.11.0 baseline)
  ship16    n<=16 table seeded to 16  -- reproduces the SHIPPED table
  new16     n<=18 enumeration, cutoff 16 -- same levels, better populated
  new18     n<=18 enumeration, cutoff 18 -- plus the two extra levels

ship16 -> new16 isolates the SEEDING effect; new16 -> new18 isolates the
EXTRA LEVELS. Costs must agree across all four: entries are exact, so a
disagreement means the table is wrong, not merely weak.

`coverage` is the share of heuristic calls with n <= cutoff -- the
ceiling the histogram measures. `hit` is the share that actually found
an entry. coverage - hit is table incompleteness inside its own range.
"""
import multiprocessing as mp
import os
import pickle
import sys
import time
from pathlib import Path

import yutsis.search as S
from yutsis import benchmarks as B
from yutsis.patterns import heuristic_with

SP = os.environ.get("YUTSIS_TABLES",
                    str(Path(__file__).resolve().parent / "tables"))
CASES = [20, 22, 24, 26, 30]
ARMS = [("base", None, 0),
        ("ship16", f"{SP}/pdb16_shipped.pkl", 16),
        ("new16", f"{SP}/pdb18.pkl", 16),
        ("new18", f"{SP}/pdb18.pkl", 18)]

def worker(n, path, cut, q):
    g = B.random_cubic(n, seed=7 * n)
    st = {"calls": 0, "hits": 0, "cov": 0}
    if path:
        tab = pickle.load(open(path, "rb"))
        h0 = heuristic_with(tab, max_n=cut)
        def h(gr):
            st["calls"] += 1
            if gr.n <= cut:
                st["cov"] += 1
                if gr.canonical() in tab:
                    st["hits"] += 1
            return h0(gr)
        S.heuristic = h
    t0 = time.perf_counter()
    r = S.solve(g, max_expanded=400_000)
    c = max(1, st["calls"])
    q.put({"sec": time.perf_counter() - t0, "exp": r["expanded"],
           "cost": r["cost"], "timeout": r["timeout"],
           "hit": 100.0 * st["hits"] / c, "cov": 100.0 * st["cov"] / c})

def run(n, path, cut, budget=1800.0):
    q = mp.Queue()
    p = mp.Process(target=worker, args=(n, path, cut, q))
    p.start()
    p.join(budget)
    if p.is_alive():
        p.terminate()
        p.join()
        return None
    return q.get() if not q.empty() else None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        want = set(sys.argv[1].split(","))
        ARMS = [a for a in ARMS if a[0] in want]
    hdr = (f"{'n':>3} {'arm':>7} {'expanded':>9} {'d_nodes':>8} {'sec':>8} "
           f"{'d_sec':>7} {'cover':>6} {'hit':>6} {'cost':>6}")
    print(hdr)
    print("-" * len(hdr), flush=True)
    for n in CASES:
        ref = None
        for name, path, cut in ARMS:
            r = run(n, path, cut)
            if r is None or r.get("timeout"):
                print(f"{n:>3} {name:>7}   WALL/timeout", flush=True)
                continue
            if name == "base":
                ref = r
            dn = 100.0 * (r["exp"] - ref["exp"]) / max(1, ref["exp"]) if ref else 0
            dsec = 100.0 * (r["sec"] - ref["sec"]) / max(1e-9, ref["sec"]) if ref else 0
            flag = "" if (ref and r["cost"] == ref["cost"]) else "  <-- COST MISMATCH"
            print(f"{n:>3} {name:>7} {r['exp']:>9} {dn:>7.0f}% {r['sec']:>8.2f} "
                  f"{dsec:>6.0f}% {r['cov']:>5.0f}% {r['hit']:>5.0f}% "
                  f"{r['cost']:>6}{flag}", flush=True)
        print(flush=True)
