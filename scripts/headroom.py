"""How much search does the heuristic actually save?

A* must expand at least as many nodes as the optimal plan has moves. The
gap between `expanded` and `moves` is the entire prize available to a
better admissible bound, and comparing against `h = 0` says how much of
that prize the current bound already collects.

This is the measurement that motivates the carving/branchwidth work
(docs/NEXT_STEPS.md, Finding 5) and it is the one to re-run before
claiming any heuristic improvement.

    python scripts/headroom.py [--max-n N] [--budget SECONDS]

Columns:
    moves      length of the optimal plan -- the floor on expansions
    exp(h)     expansions with the shipped heuristic
    exp(h=0)   expansions with no heuristic at all
    headroom   exp(h) - moves, the nodes a PERFECT bound would remove
    saved      how much of the search h removes vs h = 0
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import time

import yutsis.bounds as bd
from yutsis import benchmarks as B
from yutsis.search import solve


def _worker(graph, use_h, cap, q):
    if not use_h:
        bd.sum_bound = lambda g: 0          # noqa: ARG005 - deliberate stub
    t0 = time.time()
    r = solve(graph, max_expanded=cap)
    r["sec"] = time.time() - t0
    q.put(r)


def run_case(graph, use_h=True, cap=200_000, budget=30.0):
    q = mp.Queue()
    p = mp.Process(target=_worker, args=(graph, use_h, cap, q))
    p.start()
    p.join(budget)
    if p.is_alive():
        p.terminate()
        p.join()
        return None
    return q.get()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--budget", type=float, default=30.0)
    ap.add_argument("--max-n", type=int, default=30)
    args = ap.parse_args()

    cases = [("tetrahedron", B.tetrahedron()), ("prism", B.prism()),
             ("K3,3", B.k33()), ("cube", B.cube()),
             ("petersen", B.petersen())]
    for n in range(8, args.max_n + 1, 2):
        cases.append((f"random n={n}", B.random_cubic(n, seed=7 * n)))

    hdr = (f"{'case':>14} {'n':>3} {'moves':>6} {'exp(h)':>8} "
           f"{'exp(h=0)':>9} {'headroom':>9} {'saved':>6} {'sec':>7}")
    print(hdr)
    print("-" * len(hdr))
    for name, g in cases:
        rh = run_case(g, True, budget=args.budget)
        if rh is None or rh.get("timeout"):
            print(f"{name:>14} {g.n:>3} {'--':>6} {'WALL':>8} "
                  f"{'--':>9} {'--':>9} {'--':>6} {args.budget:>7.1f}")
            continue
        r0 = run_case(g, False, budget=args.budget)
        moves = len(rh["moves"])
        e_h = rh["expanded"]
        if r0 is None or r0.get("timeout"):
            e_0, saved = "--", "--"
        else:
            e_0 = r0["expanded"]
            saved = f"{100.0 * (e_0 - e_h) / max(1, e_0):.0f}%"
        print(f"{name:>14} {g.n:>3} {moves:>6} {e_h:>8} {str(e_0):>9} "
              f"{e_h - moves:>9} {str(saved):>6} {rh['sec']:>7.2f}")


if __name__ == "__main__":
    main()
