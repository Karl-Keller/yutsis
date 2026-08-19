"""Is there an answer at ANY n if we stop searching altogether?

Not best-first with a queue -- a pure greedy ROLLOUT: take a free move
if one exists, else one cycle-shortening flip, never backtrack. It
cannot wall on the open list because it has none; the only question is
whether it terminates and what it costs. Reuses the shipped move
generators, not reimplementations.
"""
import time

from yutsis import benchmarks as B
from yutsis.moves import (
    cut_bridge,
    excise_bubble,
    excise_loop,
    reduce_triangle,
    targeted_interchanges,
)
from yutsis.search import SUM_PENALTY, is_goal, successors


def free_moves(g):
    out = [excise_bubble(g, p) for p in g.bubbles()]
    out += [excise_loop(g, v) for v in g.excisable_loops()]
    out += [cut_bridge(g, lab) for lab in g.cuttable_bridges()]
    out += [reduce_triangle(g, t) for t in g.triangles()]
    return [c for c in out if c is not None]

def rollout(g, max_steps=100_000):
    cost = moves = flips = 0
    while not is_goal(g):
        moves += 1
        if moves > max_steps:
            return None
        cand = free_moves(g)
        if cand:
            ng, _f, d6, ds, _d = cand[0]
        else:
            ch = targeted_interchanges(g) or []
            if not ch:
                ch = [c for c in successors(g, blind=True) if c is not None]
            if not ch:
                return None
            ng, _f, d6, ds, _d = ch[0]
            flips += 1
        cost += d6 + SUM_PENALTY * ds
        g = ng
    return {"cost": cost, "moves": moves, "flips": flips}

print(f"{'n':>5} {'3n/2':>7} | {'cost':>8} {'moves':>7} "
      f"{'flips':>6} {'sec':>8}", flush=True)
for n in (20, 30, 36, 40, 50, 60, 80, 100, 150, 200, 300):
    g = B.random_cubic(n, seed=7 * n)
    t0 = time.perf_counter()
    r = rollout(g)
    t = time.perf_counter() - t0
    if r is None:
        print(f"{n:>5} {3*n//2:>6}j |  DID NOT TERMINATE  {t:>8.1f}", flush=True)
        continue
    print(f"{n:>5} {3*n//2:>6}j | {r['cost']:>8} {r['moves']:>7} "
          f"{r['flips']:>6} {t:>8.2f}", flush=True)
