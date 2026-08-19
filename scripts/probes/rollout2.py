"""Does the rollout cycle, or is it genuinely stuck?

Same descent, plus the one thing a queueless walk lacks: memory. Refuse
to re-enter a visited topology, and among the remaining flips prefer the
one that most shortens the shortest cycle -- the girth strategy's actual
intent, rather than 'first candidate wins'.
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

def girth(g):
    try:
        return g.girth()
    except Exception:
        return 99

def rollout(g, max_steps=20_000):
    cost = moves = flips = 0
    seen = {g.canonical()}
    while not is_goal(g):
        moves += 1
        if moves > max_steps:
            return None
        cand = free_moves(g)
        if cand:
            ng, _f, d6, ds, _d = cand[0]
        else:
            ch = list(targeted_interchanges(g) or [])
            ch += [c for c in successors(g, blind=True) if c is not None]
            fresh = [c for c in ch if c[0].canonical() not in seen]
            if not fresh:
                return None
            fresh.sort(key=lambda c: girth(c[0]))
            ng, _f, d6, ds, _d = fresh[0]
            flips += 1
        seen.add(ng.canonical())
        cost += d6 + SUM_PENALTY * ds
        g = ng
    return {"cost": cost, "moves": moves, "flips": flips}

print(f"{'n':>5} {'3n/2':>7} | {'cost':>8} {'moves':>7} "
      f"{'flips':>6} {'sec':>8}", flush=True)
for n in (30, 36, 40, 50, 60, 80, 100, 150, 200):
    g = B.random_cubic(n, seed=7 * n)
    t0 = time.perf_counter()
    r = rollout(g)
    t = time.perf_counter() - t0
    if r is None:
        print(f"{n:>5} {3*n//2:>6}j |  STUCK/CYCLED       {t:>8.1f}", flush=True)
        continue
    print(f"{n:>5} {3*n//2:>6}j | {r['cost']:>8} {r['moves']:>7} "
          f"{r['flips']:>6} {t:>8.2f}", flush=True)
