"""Cubic multigraph state representation for Yutsis diagrams."""
from __future__ import annotations
import itertools
from collections import Counter, defaultdict


class Graph:
    """Cubic multigraph. Edges are (u, v, label); vertex ids are strings."""

    def __init__(self, edges):
        norm = [(str(u), str(v), lab) for u, v, lab in edges]
        self.edges = tuple(sorted((min(u, v), max(u, v), lab) for u, v, lab in norm))
        self.adj = defaultdict(list)
        self._canon = None
        for i, (u, v, lab) in enumerate(self.edges):
            self.adj[u].append((v, lab, i))
            self.adj[v].append((u, lab, i))

    @property
    def n(self):
        return len(self.adj)

    def check_cubic(self):
        return all(len(nb) == 3 for nb in self.adj.values())

    def bubbles(self):
        """Vertex pairs joined by exactly two parallel edges."""
        cnt = Counter((u, v) for u, v, _ in self.edges)
        return [pair for pair, c in cnt.items() if c == 2]

    def triangles(self):
        tris = []
        vs = sorted(self.adj)
        for a, b, c in itertools.combinations(vs, 3):
            nb_a = {v for v, _, _ in self.adj[a]}
            nb_b = {v for v, _, _ in self.adj[b]}
            if b in nb_a and c in nb_a and c in nb_b:
                tris.append((a, b, c))
        return tris

    def girth_lower(self):
        if self.bubbles():
            return 2
        if self.triangles():
            return 3
        return 4

    def canonical(self):
        """Exact canonical certificate.

        1-WL color refinement provably collapses on regular graphs (all
        cubic graphs look identical to it), so for n <= 8 we brute-force
        the canonical form over vertex permutations of the anonymous
        multigraph. Above that we fall back to the exact labeled edge
        tuple: sound (never merges distinct states) but blind to
        isomorphism. Roadmap: nauty-style individualized refinement.
        """
        if self._canon is None:
            if self.n > 8:
                self._canon = ("exact", self.edges)
            else:
                vs = sorted(self.adj)
                pairs = [(u, v) for u, v, _ in self.edges]
                best = None
                for perm in itertools.permutations(range(len(vs))):
                    m = dict(zip(vs, perm))
                    cand = tuple(sorted((min(m[u], m[v]), max(m[u], m[v]))
                                        for u, v in pairs))
                    if best is None or cand < best:
                        best = cand
                self._canon = (len(vs), best)
        return self._canon
