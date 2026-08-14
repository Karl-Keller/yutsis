"""Admissible lower bounds on reduction cost.

Full derivation, proof status and boundaries: docs/BOUNDS.md.

Every complete reduction uses exactly (n-2)/2 vertex-removing moves,
split into B bubble excisions (free) and T triangle contractions (one 6j
each), plus S flips (one 6j and one summation each):

    #6j  = (n-2)/2 - B + S
    cost = (n-2)/2 - B + (1 + SUM_PENALTY) * S

So a lower bound on cost needs an UPPER bound on B. The v0.6.0
heuristic used (n-2)/2 as its 6j term, which silently assumes B = 0 --
false in general, and inadmissible on 58 of 80 reachable states with a
computable optimum. That is the defect this module fixes.

What ships as the default `heuristic` is the PROVEN part only: the
summation term. The 6j term is 0, which is trivially a valid lower
bound. This costs nothing measurable -- with SUM_PENALTY = 10 the
summation term dominates, and on every benchmark plus random cubic
graphs to n = 14 the decomposition bound below produces byte-identical
costs AND expanded-node counts. A term that cannot change the search
order is not worth an unproven admissibility claim.

`sixj_bound_decomposition` implements the stronger, derived 6j bound and
is kept (it is the foundation of the carving/branchwidth work in
Finding 3), but it is OPT-IN and its certification status is stated
honestly below.

This module is pure graph combinatorics: it knows nothing about phases,
6j conventions or angular momentum. The search layer imports it; the
physics layer never does.
"""
from __future__ import annotations

import itertools
from collections import deque

from .graph import Graph

SUM_PENALTY = 10  # one surviving summation ~ ten 6j lookups at evaluation


# ---------------------------------------------------------------------
# The proven bound (default)
# ---------------------------------------------------------------------

def sum_bound(g: Graph) -> int:
    """Lower bound on summation cost. PROVEN.

    With no bubble and no triangle present, no vertex-removing move
    applies, so at least one interchange -- hence at least one surviving
    summation -- is unavoidable.

    Weak: it returns SUM_PENALTY whether the true answer is one flip or
    five, so it bounds Petersen at S >= 1 against a certified S = 3.
    Tightening it via edge-separator width is Finding 3."""
    if g.n > 2 and g.girth_lower() >= 4:
        return SUM_PENALTY
    return 0


def heuristic(g: Graph) -> int:
    """Admissible h for the A* search. PROVEN admissible.

    h = 0 (6j term) + sum_bound. Both terms are lower bounds on
    disjoint parts of the cost, so their sum is admissible.

    The 6j term is deliberately 0 rather than the decomposition bound
    below: see the module docstring and docs/BOUNDS.md. Restoring it is
    a one-line change if a size is ever found where it matters."""
    return sum_bound(g)


# ---------------------------------------------------------------------
# The 2-cut decomposition (opt-in; certified, not proven)
# ---------------------------------------------------------------------

def has_self_loop(g: Graph) -> bool:
    """A tadpole (forces j = 0). Created by excise_bubble when a bubble's
    two external stubs land on the same vertex."""
    return any(u == v for u, v, _ in g.edges)


def _reachable(edges, start, skip):
    """Vertices reachable from `start` with edge indices in `skip` cut."""
    adj: dict[str, list[str]] = {}
    for i, (u, v, _lab) in enumerate(edges):
        if i in skip:
            continue
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)
    seen, dq = {start}, deque([start])
    while dq:
        for w in adj.get(dq.popleft(), []):
            if w not in seen:
                seen.add(w)
                dq.append(w)
    return seen


def has_bridge(g: Graph) -> bool:
    """A 1-line cut. Outside the decomposition argument."""
    edges = list(g.edges)
    n = len(g.adj)
    return any(len(_reachable(edges, e[0], {i})) != n
               for i, e in enumerate(edges))


def split_on_2cut(g: Graph):
    """Split on one 2-edge-cut, or None if none applies.

    Each side keeps its internal edges plus ONE new edge joining its two
    dangling stubs -- exactly the rewiring excise_bubble performs, which
    is why the decomposition tracks the bubble discount.

    Cuts whose two edges land on a common vertex on either side are
    skipped: joining those stubs would create a self-loop."""
    edges = list(g.edges)
    verts = set(g.adj)
    for i, j in itertools.combinations(range(len(edges)), 2):
        side = _reachable(edges, edges[i][0], {i, j})
        if not side or len(side) == len(verts):
            continue  # removing the pair left the graph connected
        if not all((e[0] in side) != (e[1] in side)
                   for e in (edges[i], edges[j])):
            continue  # both edges must straddle the partition
        stub_a, stub_b = [], []
        for a, b, _lab in (edges[i], edges[j]):
            stub_a.append(a if a in side else b)
            stub_b.append(b if a in side else a)
        if stub_a[0] == stub_a[1] or stub_b[0] == stub_b[1]:
            continue  # would create a self-loop
        keep_a = [(a, b, lab) for k, (a, b, lab) in enumerate(edges)
                  if k not in (i, j) and a in side and b in side]
        keep_b = [(a, b, lab) for k, (a, b, lab) in enumerate(edges)
                  if k not in (i, j) and a not in side and b not in side]
        keep_a.append((stub_a[0], stub_a[1], "cut_a"))
        keep_b.append((stub_b[0], stub_b[1], "cut_b"))
        ga, gb = Graph(keep_a), Graph(keep_b)
        if ga.check_cubic() and gb.check_cubic():
            return ga, gb
    return None


def three_edge_pieces(g: Graph):
    """Decompose into 3-edge-connected pieces by repeated 2-cut splits."""
    split = split_on_2cut(g)
    if split is None:
        return [g]
    return three_edge_pieces(split[0]) + three_edge_pieces(split[1])


def sixj_bound_decomposition(g: Graph) -> int:
    """Lower bound on 6j count: sum of (n_i - 2)/2 over 3-edge-connected
    pieces, degenerate pieces scoring 0.

    Bubbles are creatures of 2-edge-cuts -- a bubble is precisely the
    minimal 2-line cut, and 2-line cuts are the free case of the k-line
    calculus (a k-line separation costs max(0, k-3) summations). So the
    bubble discount is derived from the cut structure rather than bolted
    on.

    CERTIFICATION STATUS -- read before using this in a search whose
    optimality you intend to claim:

      * Admissible on every tested state: 0 violations of h <= C* over
        80 reachable states with a computable optimum, tight on 54.
      * NOT proven. The potential-function proof (docs/BOUNDS.md) needs
        Phi(G) <= Phi(G') + d6 for every move, and that FAILS on 310 of
        42,611 moves -- all of them at states carrying a self-loop or a
        bridge, where a move can relocate the degeneracy between pieces
        and collapse Phi by more than the 6j it emits.

    Because it never changed a single search decision in measurement
    (see module docstring), `heuristic` does not use it. It is retained
    as the foundation for the carving/branchwidth bound of Finding 3,
    where the degenerate cases must be handled properly rather than
    scored 0."""
    return sum(0 if has_self_loop(p) or has_bridge(p)
               else max(0, (p.n - 2) // 2)
               for p in three_edge_pieces(g))
