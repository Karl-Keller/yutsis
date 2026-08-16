"""Where does the 99% waste live, relative to C*?

A* with a CONSISTENT h expands every state with f < C* -- mandatory
work, removable only by a stronger admissible bound -- and some subset
of the f = C* plateau, whose size depends purely on tie-breaking.

certify_bounds reports 0 step violations for the shipped heuristic, so
h is consistent and no node is ever re-expanded: the split is exhaustive.

    plateau-dominated  -> no admissible bound was ever going to help;
                          the lever is queue discipline (Lemma 5 generalizes)
    mandatory-dominated -> only a stronger bound helps; brief the
                          flip-count candidates
"""
import heapq
import itertools

from yutsis import benchmarks as B
from yutsis.bounds import SUM_PENALTY, heuristic
from yutsis.search import is_goal, successors


def profile(g, cap=300_000):
    """Replicates search.solve, recording f at each expansion."""
    tie = itertools.count()
    heap = [(heuristic(g), 0, next(tie), g)]
    best = {g.canonical(): 0}
    fs, cstar, expanded = [], None, 0
    while heap:
        f, cost, _t, cur = heapq.heappop(heap)
        if is_goal(cur):
            cstar = cost
            break
        expanded += 1
        if expanded > cap:
            return None
        fs.append(f)
        for ng, _fac, d6, ds, _d in successors(cur):
            nc = cost + d6 + SUM_PENALTY * ds
            k = ng.canonical()
            if k in best and best[k] <= nc:
                continue
            best[k] = nc
            heapq.heappush(heap, (nc + heuristic(ng), nc, next(tie), ng))
    below = sum(1 for f in fs if f < cstar)
    equal = sum(1 for f in fs if f == cstar)
    above = sum(1 for f in fs if f > cstar)
    return cstar, len(fs), below, equal, above


print(f"{'case':12} {'n':>3} {'C*':>5} {'expanded':>9} {'f<C*':>7} "
      f"{'f=C*':>7} {'f>C*':>6} {'plateau share':>14}")
print("-" * 72)
for n in (16, 18, 20, 22, 24, 26, 30):
    g = B.random_cubic(n, seed=7 * n)
    r = profile(g)
    if r is None:
        print(f"random n={n}: WALL")
        continue
    cstar, tot, below, equal, above = r
    share = 100.0 * equal / max(1, tot)
    print(f"{'random n=%d' % n:12} {n:>3} {cstar:>5} {tot:>9} {below:>7} "
          f"{equal:>7} {above:>6} {share:>13.0f}%")
