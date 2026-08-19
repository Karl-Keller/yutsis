"""Weighted A* over the SAME primitives as yutsis.search, plus the one
thing solve() cannot report: the frontier's minimum f.

With an admissible h, min-f over the open list is a valid LOWER BOUND on
C* even when the search is cut off. That is what makes a suboptimality
claim possible at sizes where the optimum is not computable.

Reuses successors/is_goal/SUM_PENALTY rather than reimplementing them
(the v0.9.0 lesson), and is oracle-checked against solve() below.
"""
import heapq
import itertools

from yutsis.search import SUM_PENALTY, is_goal, successors


def search(g, h, w=1, cap=200_000, blind=False):
    tie = itertools.count()
    open_heap = [(w * h(g), 0, next(tie), g)]
    best = {g.canonical(): 0}
    expanded = 0
    while open_heap:
        f, cost, _t, cur = heapq.heappop(open_heap)
        if is_goal(cur):
            return {"cost": cost, "expanded": expanded, "lb": cost,
                    "timeout": False}
        expanded += 1
        if expanded > cap:
            lb = min([f] + [e[0] for e in open_heap]) if w == 1 else None
            return {"cost": None, "expanded": expanded, "lb": lb,
                    "timeout": True}
        for ng, _fa, d6, ds, _d in successors(cur, blind=blind):
            nc = cost + d6 + SUM_PENALTY * ds
            k = ng.canonical()
            if k in best and best[k] <= nc:
                continue
            best[k] = nc
            heapq.heappush(open_heap, (nc + w * h(ng), nc, next(tie), ng))
    return None
