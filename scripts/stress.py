"""Scaling experiments for the yutsis solver.

Runs the benchmark suite plus random cubic graphs of growing size, in
optimal (A*) and, where noted, greedy mode, with a wall-clock budget per
case. Timeouts are findings, not failures.

(Historical note: this docstring used to say girth >= 5 inputs defeat
both modes under blind edge flips. That was measured in v0.4.0, before
nauty canonicalization; blind-move A* now solves Petersen in 18
expansions, and its three-summation optimum is certified -- v0.6.1.)

Usage:
    python scripts/stress.py [--budget SECONDS] [--max-n N]
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import time

from yutsis import solve
from yutsis.benchmarks import (
    cube,
    k33,
    petersen,
    prism,
    random_cubic,
    tetrahedron,
)


def _worker(graph, greedy, cap, q):
    t0 = time.time()
    r = solve(graph, max_expanded=cap, greedy=greedy)
    r["sec"] = time.time() - t0
    q.put(r)


def run_case(graph, greedy=False, cap=200_000, budget=30.0):
    """Run solve() in a subprocess so a hard wall-clock budget is honest
    even when a single expansion layer stalls."""
    q = mp.Queue()
    p = mp.Process(target=_worker, args=(graph, greedy, cap, q))
    p.start()
    p.join(budget)
    if p.is_alive():
        p.terminate()
        p.join()
        return {"sixj": -1, "sums": -1, "cost": -1, "expanded": -1,
                "sec": budget, "timeout": True}
    return q.get()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--budget", type=float, default=30.0,
                    help="wall-clock seconds per case (default 30)")
    ap.add_argument("--max-n", type=int, default=14,
                    help="largest random cubic size (default 14)")
    args = ap.parse_args()

    cases = [
        ("tetrahedron", tetrahedron(), False),
        ("prism", prism(), False),
        ("K3,3 (9j)", k33(), False),
        ("cube Q3 (12j)", cube(), False),
        ("petersen A*", petersen(), False),
        ("petersen greedy", petersen(), True),
    ]
    for n in range(8, args.max_n + 1, 2):
        cases.append((f"random cubic n={n}", random_cubic(n, seed=7 * n), False))

    hdr = (f"{'case':20s} {'n':>3s} {'g>=':>5s} {'mode':>7s} "
           f"{'sixj':>5s} {'sums':>5s} {'cost':>5s} {'expand':>8s} {'sec':>7s}")
    print(hdr)
    print("-" * len(hdr))
    for name, g, greedy in cases:
        r = run_case(g, greedy=greedy, budget=args.budget)
        mode = "greedy" if greedy else "A*"
        if r.get("timeout"):
            print(f"{name:20s} {g.n:>3d} {g.girth_lower():>5d} {mode:>7s} "
                  f"{'--':>5s} {'--':>5s} {'--':>5s} {'--':>8s} "
                  f"{r['sec']:>7.1f}  WALL (see Findings #3)")
        else:
            print(f"{name:20s} {g.n:>3d} {g.girth_lower():>5d} {mode:>7s} "
                  f"{r['sixj']:>5d} {r['sums']:>5d} {r['cost']:>5d} "
                  f"{r['expanded']:>8d} {r['sec']:>7.2f}")


if __name__ == "__main__":
    main()
