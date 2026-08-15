"""Evidence for Lemma 4 (docs/BOUNDS.md): width invariants do not work,
and what the search actually lacks is discrimination.

Three measurements, each reproducible:

  --carving      exact carving width vs true S, refuting S >= cw - 3
  --leverage     expansions with h=0, shipped h, and shipped + (n-2)/2,
                 showing a large scaling term buys nothing
  --discriminate spread of true C* vs spread of each candidate bound
                 over all same-depth states, which is the real gap

Exact carving width is a subset DP, O(3^n), so --carving is limited to
about n <= 14.
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
from collections import Counter, deque
from functools import lru_cache

import yutsis.bounds as bd
from yutsis import benchmarks as B
from yutsis.bounds import sixj_bound_decomposition, sum_bound
from yutsis.search import optimal_cost, solve, successors


def carving_width(g):
    """Minimum over carvings of the widest induced edge cut.

    g(S) = 0 for a single vertex, else min over splits A + B = S of
    max(g(A), g(B), cut(A), cut(B)); the carving width is then the best
    top-level split. Validated against cw(C4)=2, cw(K1,3)=3, cw(K4)=4,
    cw(theta)=3, and cw >= max degree in general."""
    vs = sorted(g.adj)
    n = len(vs)
    idx = {v: i for i, v in enumerate(vs)}
    pairs = [(idx[u], idx[v]) for u, v, _lab in g.edges if u != v]
    cuts = [sum(1 for a, b in pairs if ((m >> a) & 1) != ((m >> b) & 1))
            for m in range(1 << n)]

    @lru_cache(maxsize=None)
    def gsub(mask):
        if bin(mask).count("1") == 1:
            return 0
        best = float("inf")
        sub = (mask - 1) & mask
        while sub:
            other = mask ^ sub
            if sub < other:
                best = min(best, max(gsub(sub), gsub(other),
                                     cuts[sub], cuts[other]))
            sub = (sub - 1) & mask
        return best

    full = (1 << n) - 1
    return min(max(gsub(a), gsub(full ^ a), cuts[a])
               for a in range(1, 1 << (n - 1)))


def flips_in_optimum(g):
    r = solve(g, max_expanded=300_000)
    return None if r is None or r.get("timeout") else \
        sum(1 for m in r["moves"] if m[0] == "flip")


def report_carving():
    print("exact carving width vs true S")
    print(f"{'graph':14} {'n':>3} {'cw':>4} {'cw-3':>5} {'S':>4}  verdict")
    print("-" * 48)
    cases = [("tetrahedron", B.tetrahedron()), ("prism", B.prism()),
             ("K3,3", B.k33()), ("cube Q3", B.cube()),
             ("petersen", B.petersen())]
    cases += [(f"random n={n}", B.random_cubic(n, seed=7 * n))
              for n in (8, 10, 12, 14)]
    for name, g in cases:
        cw, s = carving_width(g), flips_in_optimum(g)
        pred = max(0, cw - 3)
        verdict = "ok" if pred <= s else "REFUTES S >= cw-3"
        print(f"{name:14} {g.n:>3} {cw:>4} {pred:>5} {s:>4}  {verdict}")


def _worker(g, mode, q):
    if mode == "zero":
        bd.sum_bound = lambda _g: 0
    elif mode == "sixj":
        base = sum_bound
        bd.sum_bound = lambda gg: base(gg) + max(0, (gg.n - 2) // 2)
    r = solve(g, max_expanded=300_000)
    q.put(r)


def _run(g, mode, budget=90.0):
    q = mp.Queue()
    p = mp.Process(target=_worker, args=(g, mode, q))
    p.start()
    p.join(budget)
    if p.is_alive():
        p.terminate()
        p.join()
        return None
    return q.get()


def report_leverage():
    print("expansions: a large SCALING term buys nothing")
    print(f"{'case':12} {'n':>3} {'h=0':>7} {'shipped':>8} {'+(n-2)/2':>9}")
    print("-" * 44)
    for n in (14, 18, 20, 22, 24, 26):
        g = B.random_cubic(n, seed=7 * n)
        r0, rs, rj = (_run(g, m) for m in ("zero", "ship", "sixj"))
        if None in (r0, rs, rj):
            print(f"{'random n=%d' % n:12} {n:>3}  WALL")
            continue
        print(f"{'random n=%d' % n:12} {n:>3} {r0['expanded']:>7} "
              f"{rs['expanded']:>8} {rj['expanded']:>9}")


def report_discrimination(depth=8):
    seeds = [B.random_cubic(12, seed=84), B.random_cubic(12, seed=7),
             B.cube(), B.random_cubic(10, seed=70)]
    seen, dq, states = set(), deque(seeds), []
    while dq and len(seen) < 4000:
        g = dq.popleft()
        key = g.canonical()
        if key in seen:
            continue
        seen.add(key)
        if g.n == depth:
            states.append(g)
        for ng, *_rest in successors(g, blind=True):
            if ng.canonical() not in seen:
                dq.append(ng)
    rows = []
    for g in states:
        c = optimal_cost(g)
        if c is not None:
            rows.append((c, sum_bound(g), sixj_bound_decomposition(g)
                         + sum_bound(g)))
    print(f"discrimination over {len(rows)} states at n = {depth}")
    print(f"{'quantity':22} {'distinct':>9} {'viol':>5}  distribution")
    print("-" * 66)
    for name, vals, viol in (
            ("true C*", [r[0] for r in rows], None),
            ("shipped h", [r[1] for r in rows],
             sum(1 for r in rows if r[1] > r[0])),
            ("decomposition + sum", [r[2] for r in rows],
             sum(1 for r in rows if r[2] > r[0]))):
        v = "-" if viol is None else str(viol)
        print(f"{name:22} {len(set(vals)):>9} {v:>5}  "
              f"{dict(sorted(Counter(vals).items()))}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--carving", action="store_true")
    ap.add_argument("--leverage", action="store_true")
    ap.add_argument("--discriminate", action="store_true")
    args = ap.parse_args()
    todo = [args.carving, args.leverage, args.discriminate]
    if not any(todo):
        todo = [True, True, True]
        args.carving = args.leverage = args.discriminate = True
    for flag, fn in ((args.carving, report_carving),
                     (args.leverage, report_leverage),
                     (args.discriminate, report_discrimination)):
        if flag:
            fn()
            print()


if __name__ == "__main__":
    main()
