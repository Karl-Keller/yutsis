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

    def self_loops(self):
        """Vertices carrying a tadpole (an edge with both ends at them).

        The k=1 sector: closing two legs of a vertex forces its third
        edge to j = 0 (docs/K1_SECTOR.md)."""
        return sorted({u for u, v, _ in self.edges if u == v})

    def loop_partner(self, v):
        """The far endpoint of a loop vertex's one non-loop edge, with
        that edge's label; None if v carries no self-loop."""
        others = [(w, lab) for w, lab, _ in self.adj[v] if w != v]
        loops = [lab for w, lab, _ in self.adj[v] if w == v]
        if not loops or len(others) != 1:
            return None
        return others[0]

    def excisable_loops(self):
        """Loop vertices whose partner is a distinct, loop-free vertex --
        the guard for loop excision.

        A loop vertex whose partner also carries a loop is the DUMBBELL,
        an irreducible k=1 terminal: capping it leaves a bare circle with
        no vertices, which needs the empty-diagram state model that
        arrives with bridge cut. Excluded here rather than mishandled."""
        loops = set(self.self_loops())
        out = []
        for v in sorted(loops):
            partner = self.loop_partner(v)
            if partner is None:
                continue
            w, _lab = partner
            if w != v and w not in loops:
                out.append(v)
        return out

    def girth_lower(self):
        """NOT a lower bound on girth -- see true_girth(). This is the
        move-availability predicate Lemma 1 rests on: it reports whether
        a bubble (2) or triangle (3) pattern is present, or neither (4).
        It is blind to self-loops by construction, which is correct for
        its one job and wrong for anything else."""
        if self.bubbles():
            return 2
        if self.triangles():
            return 3
        return 4

    def true_girth(self):
        """The actual length of a shortest cycle, self-loops included.

        The one honest girth. girth_lower() reports by bubble/triangle
        presence and never computes a cycle; girth_cycle() skips
        self-loop edges outright. Both therefore return 4 and 2
        respectively on a tadpole whose true girth is 1."""
        if self.self_loops():
            return 1
        if self.bubbles():
            return 2
        cyc = self.girth_cycle()
        return len(cyc) if cyc else float("inf")

    def components(self):
        """Vertex sets of the connected components.

        Bridge cut splits a closed diagram into two independent closed
        diagrams, so states stopped being connected in v0.8.0."""
        from collections import deque
        seen, out = set(), []
        for start in sorted(self.adj):
            if start in seen:
                continue
            comp, dq = {start}, deque([start])
            seen.add(start)
            while dq:
                for w, _lab, _i in self.adj[dq.popleft()]:
                    if w not in seen:
                        seen.add(w)
                        comp.add(w)
                        dq.append(w)
            out.append(frozenset(comp))
        return out

    def component_graphs(self):
        """Each component as a Graph in its own right."""
        return [Graph([(u, v, lab) for u, v, lab in self.edges if u in comp])
                for comp in self.components()]

    def bridges(self):
        """Labels of edges whose removal disconnects (1-line cuts).

        A bridge forces j = 0: a closed diagram is a rotational scalar,
        so a single line crossing a separation carries no angular
        momentum (docs/K1_SECTOR.md)."""
        from collections import deque
        base = len(self.components())
        out = []
        for i, (u, _v, lab) in enumerate(self.edges):
            adj = {}
            for k, (a, b, _l) in enumerate(self.edges):
                if k == i:
                    continue
                adj.setdefault(a, []).append(b)
                adj.setdefault(b, []).append(a)
            seen, dq = {u}, deque([u])
            while dq:
                for w in adj.get(dq.popleft(), []):
                    if w not in seen:
                        seen.add(w)
                        dq.append(w)
            comp_of_u = next(c for c in self.components() if u in c)
            if len(seen) != len(comp_of_u):
                out.append(lab)
        return out

    def cuttable_bridges(self):
        """Bridges whose endpoints are not tadpole vertices.

        Capping a tadpole endpoint would merge a self-loop's two ends
        into a bare circle with no vertices -- the empty diagram, which
        is deliberately NOT a state. That configuration is the dumbbell,
        handled as a terminal instead (see is_dumbbell)."""
        loops = set(self.self_loops())
        out = []
        for lab in self.bridges():
            u, v = next((a, b) for a, b, l in self.edges if l == lab)
            if u == v or u in loops or v in loops:
                continue
            out.append(lab)
        return out

    def is_dumbbell(self):
        """Two tadpoles joined by a bridge: an irreducible k=1 terminal.

        Value sqrt(2k+1)*sqrt(2f+1)*delta(c,0). Two vertices and three
        edges like a theta, which is why the pre-v0.7.0 goal test
        (`n <= 2`) accepted it and dropped the j=0 constraint."""
        if self.n != 2 or len(self.edges) != 3:
            return False
        return len(self.self_loops()) == 2

    def is_terminal(self):
        """Every component is irreducible: a theta or a dumbbell."""
        return all(c.is_theta() or c.is_dumbbell()
                   for c in self.component_graphs())

    def is_theta(self):
        """Two vertices joined by three parallel edges: the true goal.

        Excludes the dumbbell -- two tadpoles joined by a bridge -- which
        also has two vertices and three edges, and which the old n <= 2
        goal test silently accepted, emitting a formula with every j = 0
        constraint dropped."""
        if self.n != 2 or len(self.edges) != 3 or self.self_loops():
            return False
        u, v = sorted(self.adj)
        return all({a, b} == {u, v} for a, b, _ in self.edges)

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
