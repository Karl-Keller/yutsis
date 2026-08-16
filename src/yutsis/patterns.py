"""Endgame pattern database: exact C* for small topologies.

Lemma 6 (docs/BOUNDS.md) rules out any heuristic whose evaluation cost
scales with the move set -- rung two of the flip-count ladder was
admissible, cut 12-35% of nodes, and ran 10x-23x SLOWER, because it ran
a search inside the bound. A table is the shape that survives that
objection: one dictionary lookup per node, no search at all.

Entries are EXACT optimal costs, so `h` is admissible by construction
and perfectly discriminating wherever the table hits.

BUILD, level by level. Within a level, flips connect states at cost
1 + SUM_PENALTY; vertex-removing moves exit to the level below, whose
C* is already known. Each level is therefore a Dijkstra seeded by exit
costs and relaxed backwards along flip edges -- far cheaper than an
independent uniform-cost search per state. Measured: 47,284 entries for
n <= 16 in about nine minutes, verified against `search.optimal_cost`.

MEASURED PAYOFF with the n <= 16 table, against the shipped rung-one
heuristic:

    n      nodes    wall clock   hit rate
    20      -64%        -71%        94%
    22      -74%        -71%        54%
    24      -45%        -40%        48%
    26      -37%        -34%        24%
    30      -27%        -21%        14%

The first candidate since Finding 5 to cut BOTH nodes and seconds. It
still DECAYS with n, tracking the hit rate, so the closure criterion --
a `saved` column that stops decaying -- is NOT met.

NOT wired into the default heuristic: the table is a build artifact
costing minutes to generate and megabytes to store, and the engine must
work without it. Enable it explicitly.
"""
from __future__ import annotations

import heapq
import pickle
import time
from collections import defaultdict, deque
from pathlib import Path

from .bounds import SUM_PENALTY, sum_bound
from .graph import Graph
from .search import is_goal, successors


def enumerate_states(max_n: int, seeds, cap: int = 200_000,
                     budget: float = 900.0) -> dict:
    """Reachable topologies with `n <= max_n`, keyed by certificate.

    Closure under the BLIND move set, so the table covers states any
    search can reach, not just those the shipped move ordering visits."""
    seen: set = set()
    out: dict = {}
    dq = deque(seeds)
    t0 = time.time()
    while dq and len(seen) < cap and time.time() - t0 < budget:
        g = dq.popleft()
        if g.n > max_n:
            continue
        cert = g.canonical()
        if cert in seen:
            continue
        seen.add(cert)
        out[cert] = g
        for ng, *_rest in successors(g, blind=True):
            if ng.n <= max_n and ng.canonical() not in seen:
                dq.append(ng)
    return out


def build_table(states: dict) -> dict:
    """cert -> exact C*, computed level by level in increasing n."""
    by_n = defaultdict(list)
    for cert, g in states.items():
        by_n[g.n].append((cert, g))
    table: dict = {}
    for n in sorted(by_n):
        exit_cost, flip_fwd = {}, {}
        for cert, g in by_n[n]:
            if is_goal(g):
                exit_cost[cert], flip_fwd[cert] = 0, []
                continue
            best, flips = float("inf"), []
            for ng, _f, d6, ds, _d in successors(g, blind=True):
                k = ng.canonical()
                if ng.n < n:
                    if k in table:
                        best = min(best, d6 + table[k])
                else:
                    flips.append((k, d6 + SUM_PENALTY * ds))
            exit_cost[cert], flip_fwd[cert] = best, flips
        rev = defaultdict(list)
        for cert, edges in flip_fwd.items():
            for k, w in edges:
                rev[k].append((cert, w))
        dist = dict(exit_cost)
        heap = [(d, c) for c, d in dist.items() if d < float("inf")]
        heapq.heapify(heap)
        done: set = set()
        while heap:
            d, c = heapq.heappop(heap)
            if c in done or d > dist.get(c, float("inf")):
                continue
            done.add(c)
            for pred, w in rev.get(c, ()):
                nd = d + w
                if nd < dist.get(pred, float("inf")):
                    dist[pred] = nd
                    heapq.heappush(heap, (nd, pred))
        for cert, _g in by_n[n]:
            if dist.get(cert, float("inf")) < float("inf"):
                table[cert] = dist[cert]
    return table


def save(table: dict, path) -> None:
    Path(path).write_bytes(pickle.dumps(table, protocol=4))


def load(path) -> dict:
    return pickle.loads(Path(path).read_bytes())


def heuristic_with(table: dict, max_n: int = 16):
    """An admissible heuristic backed by `table`.

    Exact where the table hits -- so `f = g + C*` and the node is
    expanded only when it genuinely lies on an optimal path -- and the
    shipped rung-one bound everywhere else. Both parts are lower bounds,
    so the result is admissible; costs are unchanged, only the search
    order is."""
    def h(g: Graph) -> int:
        if g.n <= max_n:
            hit = table.get(g.canonical())
            if hit is not None:
                return hit
        return sum_bound(g)
    return h
