"""A* (and greedy best-first) over the rewrite space."""
from __future__ import annotations
import heapq
import itertools
from .bounds import SUM_PENALTY, heuristic
from .graph import Graph
from .moves import excise_bubble, reduce_triangle, interchanges, targeted_interchanges

__all__ = ["SUM_PENALTY", "heuristic", "is_goal", "successors", "solve",
           "optimal_cost"]


def is_goal(g: Graph):
    return g.n <= 2  # theta: pure normalization


def successors(g: Graph, blind=False):
    """Children of a state. By default flips are cycle-targeted (the
    girth strategy); blind=True generates the full ~4|E| flip set, which
    is what an optimality claim over the UNRESTRICTED move class needs."""
    children = [excise_bubble(g, pair) for pair in g.bubbles()]
    children += [reduce_triangle(g, tri) for tri in g.triangles()]
    if blind:
        children += interchanges(g)
    elif not g.triangles() and not g.bubbles():
        children += targeted_interchanges(g) or interchanges(g)
    return [c for c in children if c is not None]


def optimal_cost(g: Graph, max_expanded=400_000):
    """True minimum cost C*, by uniform-cost search (h = 0) over the
    BLIND move set. Returns None if the budget is exhausted.

    h = 0 is trivially admissible and the move set is unrestricted, so
    this answer depends on no heuristic and no move-ordering claim. It
    is the ground truth against which heuristics are certified -- what
    the magnetic-sum oracle is to formulas, one layer up."""
    tie = itertools.count()
    heap = [(0, next(tie), g)]
    best = {g.canonical(): 0}
    expanded = 0
    while heap:
        cost, _, cur = heapq.heappop(heap)
        if is_goal(cur):
            return cost
        expanded += 1
        if expanded > max_expanded:
            return None
        for ng, _fac, d6, ds, _desc in successors(cur, blind=True):
            nc = cost + d6 + SUM_PENALTY * ds
            key = ng.canonical()
            if key in best and best[key] <= nc:
                continue
            best[key] = nc
            heapq.heappush(heap, (nc, next(tie), ng))
    return None


def solve(g: Graph, max_expanded=200_000, greedy=False, blind=False):
    """greedy=True: weighted best-first (w=5) for a fast feasible upper
    bound with no optimality guarantee.

    blind=True: search the unrestricted move set, so that an optimal
    result is optimal over ALL flips rather than only the cycle-targeted
    ones (Finding 3)."""
    tie = itertools.count()
    w = 5 if greedy else 1
    open_heap = [(w * heuristic(g), 0, next(tie), g, [], [])]
    best = {g.canonical(): 0}
    expanded = 0
    while open_heap:
        f, cost, _, cur, facs, descs = heapq.heappop(open_heap)
        if is_goal(cur):
            return {"factors": facs, "moves": descs,
                    "sixj": sum(1 for fa in facs if "sixj" in fa),
                    "sums": sum(1 for fa in facs if fa.startswith("sum_")),
                    "cost": cost, "expanded": expanded, "timeout": False}
        expanded += 1
        if expanded > max_expanded:
            return {"factors": None, "sixj": -1, "sums": -1, "cost": -1,
                    "expanded": expanded, "timeout": True}
        for ng, fac, d6, ds, desc in successors(cur, blind=blind):
            nc = cost + d6 + SUM_PENALTY * ds
            key = ng.canonical()
            if key in best and best[key] <= nc:
                continue
            best[key] = nc
            heapq.heappush(open_heap,
                           (nc + w * heuristic(ng), nc, next(tie),
                            ng, facs + [fac], descs + [desc]))
    return None
