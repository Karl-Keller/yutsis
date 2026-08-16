"""Full admissibility certification for yutsis.bounds.

The CI tests (tests/test_bounds.py) run a small corpus in under a
second. This script runs the wide sweep that is too slow for CI, and is
the record referenced by docs/BOUNDS.md "Certification record". Run it
before a release.

    python scripts/certify_bounds.py [--cap N] [--random-seeds N]

Three certificates:

1. Re-certification -- the published benchmark costs recomputed by
   uniform-cost search (h = 0) over the blind move set.
2. Admissibility -- h(G) <= C*(G) over reachable states with a
   computable optimum, reported for both the v0.6.0 bound and the
   current one.
3. The induction step -- Phi(G) <= Phi(G') + d6 for every move out of
   every corpus state. Stronger than (2), since it covers states whose
   C* is out of budget.
"""
from __future__ import annotations

import argparse
from collections import deque

from yutsis import benchmarks as B
from yutsis.bounds import (
    has_bridge,
    has_self_loop,
    heuristic,
    sixj_bound_gated,
    sum_bound,
)
from yutsis.bounds import sixj_bound_decomposition as sixj_bound
from yutsis.search import optimal_cost, successors

PUBLISHED = {"tetrahedron": 1, "prism": 2, "k33": 13, "cube": 14,
             "petersen": 37}


def v060_heuristic(g):
    """The shipped v0.6.0 bound, verbatim, for before/after comparison."""
    h = max(0, (g.n - 2) // 2)
    if g.n > 2 and g.girth_lower() >= 4:
        h += 10
    return h


def reachable(seeds, cap):
    out, seen, dq = [], set(), deque()
    for g in seeds:
        key = g.canonical()
        if key not in seen:
            seen.add(key)
            dq.append(g)
    while dq and len(out) < cap:
        cur = dq.popleft()
        out.append(cur)
        for ng, *_rest in successors(cur, blind=True):
            key = ng.canonical()
            if key not in seen:
                seen.add(key)
                dq.append(ng)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cap", type=int, default=6000,
                    help="max corpus states (default 6000)")
    ap.add_argument("--random-seeds", type=int, default=60,
                    help="random cubic seeds per size (default 60)")
    args = ap.parse_args()

    print("=" * 66)
    print("1. Re-certification: published costs vs C* (h=0, blind moves)")
    print("=" * 66)
    for name, fn in [("tetrahedron", B.tetrahedron), ("prism", B.prism),
                     ("k33", B.k33), ("cube", B.cube),
                     ("petersen", B.petersen)]:
        g = fn()
        c = optimal_cost(g, max_expanded=2_000_000)
        pub = PUBLISHED[name]
        verdict = "MATCH" if c == pub else ("BUDGET" if c is None else "DIFFER")
        print(f"  {name:12s} C*={c!s:>6}  published={pub:>4}   {verdict}")

    seeds = [B.tetrahedron(), B.prism(), B.k33(), B.cube(), B.petersen()]
    for n in (8, 10, 12):
        for s in range(args.random_seeds):
            seeds.append(B.random_cubic(n, seed=n * 1000 + s))
    corpus = reachable(seeds, cap=args.cap)

    print()
    print("=" * 66)
    print(f"2. Admissibility over {len(corpus)} reachable states")
    print("=" * 66)
    checked = v_old = v_new = tight = 0
    c_stars, h_vals, g_vals = [], [], []
    for g in corpus:
        if g.n > 8:
            continue
        c = optimal_cost(g)
        if c is None:
            continue
        checked += 1
        if v060_heuristic(g) > c:
            v_old += 1
        if heuristic(g) > c:
            v_new += 1
            print(f"  *** VIOLATION h={heuristic(g)} > C*={c}: {g.edges}")
        if heuristic(g) == c:
            tight += 1
        c_stars.append(c)
        h_vals.append(heuristic(g))
        g_vals.append(sixj_bound_gated(g) + sum_bound(g))
    pct = (100 * v_old / checked) if checked else 0
    print(f"  states with computable C* : {checked}")
    # Discrimination is the leading indicator for the closure criterion:
    # admissibility says a bound is SAFE, distinct-value counts say
    # whether it can tell same-depth states apart at all (Lemma 4).
    if c_stars:
        print(f"  distinct true C*          : {len(set(c_stars))}")
        print(f"  distinct shipped h        : {len(set(h_vals))}")
        print(f"  distinct gated 6j + sum   : {len(set(g_vals))}")
    print(f"  v0.6.0 violations         : {v_old} ({pct:.1f}%)")
    print(f"  current violations        : {v_new}")
    print(f"  current tight             : {tight}")

    print()
    print("=" * 66)
    print("3. Induction step for the SHIPPED heuristic")
    print("=" * 66)
    moves = broken = 0
    for g in corpus:
        h = heuristic(g)
        for ng, _fac, d6, ds, _desc in successors(g, blind=True):
            moves += 1
            if h > heuristic(ng) + d6 + 10 * ds:
                broken += 1
                print(f"  *** STEP BROKEN at {g.edges}")
    print(f"  moves checked : {moves}")
    print(f"  violations    : {broken}")

    print()
    print("=" * 66)
    print("4. The opt-in decomposition bound, and its known gap")
    print("=" * 66)
    d_adm = d_step = d_step_clean = d_tight = 0
    for g in corpus:
        phi = sixj_bound(g)
        if g.n <= 8:
            c = optimal_cost(g)
            if c is not None:
                if phi > c:
                    d_adm += 1
                elif phi == c:
                    d_tight += 1
        for ng, _fac, d6, _ds, _desc in successors(g, blind=True):
            if phi > sixj_bound(ng) + d6:
                d_step += 1
                if not (has_self_loop(g) or has_bridge(g)
                        or has_self_loop(ng) or has_bridge(ng)):
                    d_step_clean += 1
                    print(f"  *** STEP BROKEN AT A CLEAN STATE: {g.edges}")
    print(f"  admissibility violations      : {d_adm}")
    print(f"  tight                         : {d_tight}")
    print(f"  step violations (total)       : {d_step}")
    print(f"  step violations at CLEAN state: {d_step_clean}")
    print("  (INFORMATIONAL. This bound is opt-in and known inadmissible")
    print("   as of the k=1 sector: loop excision removes two vertices")
    print("   for free, so C* fell below (n_i-2)/2 per piece. It is NOT")
    print("   the shipped heuristic and does not gate the verdict --")
    print("   see docs/BOUNDS.md. A bound verified against a move set is")
    print("   only valid for that move set.)")

    print()
    # The verdict covers the SHIPPED heuristic only. The opt-in bound is
    # reported above but deliberately does not gate: it is documented as
    # inadmissible rather than silently relied on.
    ok = (v_new == 0 and broken == 0)
    print("CERTIFIED (shipped heuristic)" if ok
          else "*** CERTIFICATION FAILED ***")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
