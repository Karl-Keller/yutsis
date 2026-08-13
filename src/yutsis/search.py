"""A* (and greedy best-first) over the rewrite space."""
from __future__ import annotations
import heapq
import itertools
from .graph import Graph
from .moves import excise_bubble, reduce_triangle, interchanges, targeted_interchanges

SUM_PENALTY = 10  # one surviving summation ~ ten 6j lookups at evaluation


def heuristic(g: Graph):
    """Admissible lower bound: each 6j-emitting triangle removes two
    vertices and the goal (theta) has two, so >= (n-2)/2 more 6j's; if
    girth >= 4 the only applicable move is an interchange, forcing >= 1
    summation."""
    h = max(0, (g.n - 2) // 2)
    if g.n > 2 and g.girth_lower() >= 4:
        h += SUM_PENALTY
    return h


def is_goal(g: Graph):
    return g.n <= 2  # theta: pure normalization


def solve(g: Graph, max_expanded=200_000, greedy=False):
    """greedy=True: weighted best-first (w=5) for a fast feasible upper
    bound with no optimality guarantee -- the current escape hatch for
    girth >= 5 inputs (see README findings; Petersen defeats both modes
    under blind flips)."""
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
        children = []
        for pair in cur.bubbles():
            children.append(excise_bubble(cur, pair))
        for tri in cur.triangles():
            children.append(reduce_triangle(cur, tri))
        if not cur.triangles() and not cur.bubbles():
            children.extend(targeted_interchanges(cur) or interchanges(cur))
        for ch in children:
            if ch is None:
                continue
            ng, fac, d6, ds, desc = ch
            nc = cost + d6 + SUM_PENALTY * ds
            key = ng.canonical()
            if key in best and best[key] <= nc:
                continue
            best[key] = nc
            heapq.heappush(open_heap,
                           (nc + w * heuristic(ng), nc, next(tie),
                            ng, facs + [fac], descs + [desc]))
    return None
