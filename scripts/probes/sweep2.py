"""The closure criterion, aggregated two ways because they disagree.

sweep.py reported a RATIO OF MEANS, which weights the hardest instance
in each size almost exclusively -- it read -8% at n = 34 while the two
instances measured serially read -41% and -15%. Both aggregates are
legitimate and they answer different questions:

    ratio of means   total corpus work saved (throughput)
    mean of ratios   the typical instance

so both are reported, with the per-seed spread, and raw rows dumped.
n = 38/40 are dropped: under a 300k cap only the easy instances of a
size finish, and a mean over survivors is a selection effect.
"""
import json
import multiprocessing as mp
import os
import pickle
import time
from pathlib import Path
from statistics import mean, median

import yutsis.bounds as bd
import yutsis.search as S
from yutsis import benchmarks as B
from yutsis.patterns import heuristic_with

SP = os.environ.get("YUTSIS_TABLES",
                    str(Path(__file__).resolve().parent / "tables"))
TAB = {}
def init():
    TAB["ship16"] = pickle.load(open(f"{SP}/pdb16_shipped.pkl", "rb"))
    TAB["new18"] = pickle.load(open(f"{SP}/pdb18.pkl", "rb"))

def task(job):
    n, seed, arm = job
    g = B.random_cubic(n, seed=seed)
    st = {"c": 0, "h": 0}
    if arm == "base":
        S.heuristic = bd.sum_bound
    else:
        cut = 16 if arm == "ship16" else 18
        tab = TAB[arm]
        h0 = heuristic_with(tab, max_n=cut)
        def h(gr):
            st["c"] += 1
            if gr.n <= cut and gr.canonical() in tab:
                st["h"] += 1
            return h0(gr)
        S.heuristic = h
    t0 = time.perf_counter()
    r = S.solve(g, max_expanded=300_000)
    return dict(n=n, seed=seed, arm=arm, exp=r["expanded"],
                sec=time.perf_counter() - t0, cost=r["cost"],
                to=r["timeout"], hit=100.0 * st["h"] / max(1, st["c"]))

if __name__ == "__main__":
    SIZES = list(range(20, 37, 2))
    NSEED = 5
    jobs = [(n, 7 * n + k, arm) for n in SIZES for k in range(NSEED)
            for arm in ("base", "ship16", "new18")]
    print(f"{len(jobs)} runs", flush=True)
    with mp.Pool(6, initializer=init) as pool:
        res = pool.map(task, jobs, chunksize=1)
    idx = {(r["n"], r["seed"], r["arm"]): r for r in res}
    json.dump(res, open(f"{SP}/sweep2_raw.json", "w"))
    hdr = (f"{'n':>3} {'inst':>5} | {'d16 rom':>8} {'d16 mor':>8} | "
           f"{'d18 rom':>8} {'d18 mor':>8} {'d18 med':>8} "
           f"{'spread':>13} | {'hit18':>6} {'cost':>5}")
    print(hdr)
    print("-" * len(hdr), flush=True)
    for n in SIZES:
        rows = []
        for k in range(NSEED):
            t = [idx.get((n, 7 * n + k, a)) for a in ("base", "ship16", "new18")]
            if all(t) and not any(x["to"] for x in t):
                rows.append(t)
        if not rows:
            print(f"{n:>3}   all WALL", flush=True)
            continue
        ok = all(b["cost"] == s["cost"] == w["cost"] for b, s, w in rows)
        def rom(i):
            """Ratio of means: total corpus work, hardest instance dominates."""
            return 100 * (mean(r[i]["exp"] for r in rows)
                          / mean(r[0]["exp"] for r in rows) - 1)
        rr18 = [100 * (r[2]["exp"] / r[0]["exp"] - 1) for r in rows]
        rr16 = [100 * (r[1]["exp"] / r[0]["exp"] - 1) for r in rows]
        print(f"{n:>3} {len(rows):>5} | {rom(1):>7.0f}% {mean(rr16):>7.0f}% | "
              f"{rom(2):>7.0f}% {mean(rr18):>7.0f}% {median(rr18):>7.0f}% "
              f"{min(rr18):>5.0f}..{max(rr18):>4.0f}% | "
              f"{mean(r[2]['hit'] for r in rows):>5.0f}% "
              f"{'OK' if ok else 'BAD':>5}", flush=True)
