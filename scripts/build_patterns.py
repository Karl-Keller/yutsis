"""Build the endgame pattern database (yutsis.patterns).

    python scripts/build_patterns.py --max-n 16 --out patterns16.pkl

Entries are exact optimal costs, so a heuristic reading them is
admissible by construction. See docs/BOUNDS.md, Lemma 6, for why a
table is the shape that survives -- and `yutsis.patterns` for the
measured payoff and its decay.

Rough sizes and build times, seeded as below, on one core:

    n <= 12        910 entries      ~3 s
    n <= 14      5,860 entries     ~37 s
    n <= 16     47,284 entries     ~9 min      14.7 MB
    n <= 18    470,975 entries    ~2h 12m     166.8 MB

Growth is ~10x in entries and ~14x in time per level, so n <= 20 is a
day's work as written and wants the level-wise parallelism first (see
docs/NEXT_STEPS.md). Raise --cap and --budget together: a walk stopped
early raises TruncatedEnumeration, because a partial state set yields
entries ABOVE the true optimum and breaks admissibility silently.
"""
from __future__ import annotations

import argparse
import time

from yutsis import benchmarks as B
from yutsis.patterns import build_table, enumerate_states, save
from yutsis.search import optimal_cost


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-n", type=int, default=14)
    ap.add_argument("--out", default="patterns.pkl")
    ap.add_argument("--budget", type=float, default=900.0)
    ap.add_argument("--cap", type=int, default=200_000,
                    help="max states; n <= 18 needs 500_000")
    ap.add_argument("--verify", type=int, default=40,
                    help="entries to re-check against optimal_cost")
    args = ap.parse_args()

    seeds = [B.petersen(), B.cube(), B.k33(), B.prism(), B.tetrahedron()]
    for n in range(10, args.max_n + 1, 2):
        seeds += [B.random_cubic(n, seed=n * 77 + s) for s in range(10)]

    t0 = time.time()
    states = enumerate_states(args.max_n, seeds, cap=args.cap,
                              budget=args.budget)
    t1 = time.time()
    table = build_table(states)
    t2 = time.time()
    print(f"enumerated {len(states)} states in {t1 - t0:.0f}s")
    print(f"built {len(table)} entries in {t2 - t1:.0f}s")

    # Independent check: the level-wise build must agree with a plain
    # uniform-cost search. Cheap entries only, so this stays quick.
    checked = bad = 0
    for cert, g in states.items():
        if checked >= args.verify:
            break
        if g.n > 8:
            continue
        c = optimal_cost(g)
        if c is None:
            continue
        checked += 1
        if table.get(cert) != c:
            bad += 1
            print(f"  MISMATCH: table={table.get(cert)} optimal_cost={c}")
    print(f"verified {checked} entries against optimal_cost: {bad} mismatches")

    save(table, args.out)
    print(f"wrote {args.out}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
