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

    def girth_cycle(self):
        """One shortest cycle as an ordered vertex tuple (None if acyclic).
        For each edge, BFS the shortest alternative path between its
        endpoints; the minimum closes the girth cycle."""
        from collections import deque
        best = None
        for u0, v0, lab0 in self.edges:
            if u0 == v0:
                continue
            par = {u0: None}
            dq = deque([u0])
            found = False
            while dq and not found:
                w = dq.popleft()
                for nb, lab, ei in self.adj[w]:
                    if w == u0 and nb == v0 and lab == lab0:
                        continue  # skip the removed edge itself
                    if nb not in par:
                        par[nb] = w
                        if nb == v0:
                            found = True
                            break
                        dq.append(nb)
            if v0 in par:
                path = [v0]
                while path[-1] != u0:
                    path.append(par[path[-1]])
                if best is None or len(path) < len(best):
                    best = path
        return tuple(best) if best else None

    def canonical(self):
        """Canonical certificate via nauty (individualization-refinement:
        1-WL equitable refinement plus symmetry breaking plus
        automorphism pruning -- exactly what Finding 1 showed plain 1-WL
        lacks on regular graphs). Multigraph handled by subdividing each
        edge with a distinctly colored edge-vertex. Pure-Python brute
        force retained as fallback for environments without pynauty."""
        if self._canon is None:
            try:
                import pynauty
                vs = sorted(self.adj)
                idx = {v: i for i, v in enumerate(vs)}
                n0 = len(vs)
                adj = {i: [] for i in range(n0 + len(self.edges))}
                for k, (u, v, lab) in enumerate(self.edges):
                    ev = n0 + k
                    adj[ev] = [idx[u], idx[v]]
                g = pynauty.Graph(n0 + len(self.edges),
                                  adjacency_dict=adj,
                                  vertex_coloring=[set(range(n0)),
                                                   set(range(n0, n0 + len(self.edges)))])
                self._canon = pynauty.certificate(g)
            except ImportError:
                import itertools
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
