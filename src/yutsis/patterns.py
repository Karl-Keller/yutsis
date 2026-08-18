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
from array import array
from collections import defaultdict, deque
from pathlib import Path

from .bounds import SUM_PENALTY, sum_bound
from .graph import Graph
from .search import is_goal, successors

_INF = float("inf")


class TruncatedEnumeration(RuntimeError):
    """The state set was cut off by `cap` or `budget` before closing.

    This is not a quality issue, it is a CORRECTNESS one. `build_table`
    takes each state's exit cost as a minimum over its enumerated
    successors; if a successor is missing, that minimum can only come
    out too HIGH, and a table entry above the true optimum destroys the
    A* guarantee. A partial table is not a weaker table, it is a wrong
    one, so truncation raises by default rather than returning quietly."""


def enumerate_states(max_n: int, seeds, cap: int = 200_000,
                     budget: float = 900.0, strict: bool = True) -> dict:
    """Reachable topologies with `n <= max_n`, keyed by certificate.

    Closure under the BLIND move set, so the table covers states any
    search can reach, not just those the shipped move ordering visits.

    Candidates are de-duplicated on the way IN, against every state
    already discovered, rather than on the way out against those already
    popped. Both produce the same closure; the difference is that a
    state with 111 blind successors would otherwise be queued once per
    predecessor that finds it. Measured at n <= 18: a 4,000,000-entry
    queue for 470,975 distinct states, some 32 GB of duplicate Graph
    objects.

    `strict` raises TruncatedEnumeration if the queue is still non-empty
    when cap or budget stops the walk. See that class for why the
    default is to raise."""
    out: dict = {}
    dq: deque = deque()
    queued: set = set()
    for g in seeds:
        if g.n <= max_n:
            cert = g.canonical()
            if cert not in queued:
                queued.add(cert)
                dq.append(g)
    t0 = time.time()
    while dq and len(out) < cap and time.time() - t0 < budget:
        g = dq.popleft()
        out[g.canonical()] = g
        for ng, *_rest in successors(g, blind=True):
            if ng.n <= max_n:
                cert = ng.canonical()
                if cert not in queued:
                    queued.add(cert)
                    dq.append(ng)
    if dq and strict:
        raise TruncatedEnumeration(
            f"{len(out)} states enumerated, {len(dq)} still queued: the "
            f"closure is incomplete and a table built from it would not "
            f"be exact. Raise cap/budget, or pass strict=False if a "
            f"partial state set is genuinely what you want.")
    return out


def build_table(states: dict) -> dict:
    """cert -> exact C*, computed level by level in increasing n.

    Within a level the flip graph is held as interned integer ids in a
    CSR adjacency, not as certificates. The certificates are 360 bytes
    apiece and a level at n = 18 has some 38,000,000 flip edges, each
    of which the obvious dict-of-lists formulation materialises TWICE --
    once forward, once reversed. Measured before the change: 31.4 GB
    for a partial n <= 18 build, against 0.4 GB of interned edges for
    the whole of it. Nothing computed here differs; only the shape of
    what is held in memory."""
    by_n = defaultdict(list)
    for cert, g in states.items():
        by_n[g.n].append((cert, g))
    table: dict = {}
    for n in sorted(by_n):
        level = by_n[n]
        idx = {cert: i for i, (cert, _g) in enumerate(level)}
        m = len(level)
        exit_cost = [_INF] * m
        e_dst = array("i")
        e_src = array("i")
        e_w = array("i")
        for i, (_cert, g) in enumerate(level):
            if is_goal(g):
                exit_cost[i] = 0
                continue
            best = _INF
            for ng, _fac, d6, ds, _d in successors(g, blind=True):
                if ng.n < n:
                    known = table.get(ng.canonical())
                    if known is not None and d6 + known < best:
                        best = d6 + known
                else:
                    j = idx.get(ng.canonical())
                    if j is not None:
                        e_dst.append(j)
                        e_src.append(i)
                        e_w.append(d6 + SUM_PENALTY * ds)
            exit_cost[i] = best
        # CSR over the flip edge's destination, so the Dijkstra below
        # can relax a popped node's predecessors without a reverse dict.
        cnt = array("i", bytes(4 * (m + 1)))
        for j in e_dst:
            cnt[j + 1] += 1
        for k in range(m):
            cnt[k + 1] += cnt[k]
        off = array("i", cnt)
        p_src = array("i", bytes(4 * len(e_dst)))
        p_w = array("i", bytes(4 * len(e_dst)))
        for e in range(len(e_dst)):
            slot = off[e_dst[e]]
            p_src[slot] = e_src[e]
            p_w[slot] = e_w[e]
            off[e_dst[e]] = slot + 1
        del e_dst, e_src, e_w, off
        dist = list(exit_cost)
        heap = [(d, i) for i, d in enumerate(dist) if d < _INF]
        heapq.heapify(heap)
        done = bytearray(m)
        while heap:
            d, c = heapq.heappop(heap)
            if done[c] or d > dist[c]:
                continue
            done[c] = 1
            for e in range(cnt[c], cnt[c + 1]):
                pred = p_src[e]
                nd = d + p_w[e]
                if nd < dist[pred]:
                    dist[pred] = nd
                    heapq.heappush(heap, (nd, pred))
        for i, (cert, _g) in enumerate(level):
            if dist[i] < _INF:
                table[cert] = dist[i]
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
