"""yutsis.py — a modern reduction engine for angular-momentum recoupling graphs.

v0: structural layer. States are cubic multigraphs (Yutsis graphs); moves are
the classical reduction rules; A* with an admissible lower bound finds the
cheapest summation formula (cost = SUM_PENALTY * #summations + #sixj).

Phase/weight bookkeeping (Danos-consistent conventions) is deliberately
stubbed in v0 and tracked as symbolic factor tags; milestone 2 adds the exact
phase engine validated against a brute-force magnetic-sum oracle.
"""
from __future__ import annotations
import heapq
import itertools
from collections import Counter, defaultdict

SUM_PENALTY = 10  # one surviving summation costs as much as ten 6j lookups


# ----------------------------------------------------------------------------
# Graph layer
# ----------------------------------------------------------------------------
class Graph:
    """Cubic multigraph. Edges are (u, v, label) with u, v vertex ids."""

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

    # -- pattern finders ----------------------------------------------------
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

    def squares(self):
        sqs = set()
        for a in sorted(self.adj):
            for b, _, _ in self.adj[a]:
                for c, _, _ in self.adj[b]:
                    if c in (a, b):
                        continue
                    for d, _, _ in self.adj[c]:
                        if d in (a, b, c):
                            continue
                        if any(v == a for v, _, _ in self.adj[d]):
                            key = tuple(sorted((a, b, c, d)))
                            sqs.add((key, (a, b, c, d)))
        return [cyc for _, cyc in sorted(sqs)]

    def girth_lower(self):
        if self.bubbles():
            return 2
        if self.triangles():
            return 3
        if self.squares():
            return 4
        return 5

    # -- canonical certificate ---------------------------------------------
    # 1-WL fails on regular graphs (all cubic graphs collapse), so for v0
    # sizes (n <= 9) we brute-force the canonical form over all vertex
    # permutations of the anonymous multigraph. Roadmap: nauty/individualized
    # refinement for larger n.
    def wl_hash(self):
        if self._canon is None:
            import itertools as it
            vs = sorted(self.adj)
            pairs = [(u, v) for u, v, _ in self.edges]
            best = None
            for perm in it.permutations(range(len(vs))):
                m = dict(zip(vs, perm))
                cand = tuple(sorted((min(m[u], m[v]), max(m[u], m[v]))
                                    for u, v in pairs))
                if best is None or cand < best:
                    best = cand
            self._canon = (len(vs), best)
        return self._canon

# ----------------------------------------------------------------------------
# Rewrite layer — each move returns (new_graph, factor_string, d_sixj, d_sums)
# ----------------------------------------------------------------------------
_fresh = itertools.count(1)


def excise_bubble(g: Graph, pair):
    u, v = pair
    par = [lab for a, b, lab in g.edges if (a, b) == pair]
    ext = []
    keep = []
    for a, b, lab in g.edges:
        if (a, b) == pair:
            continue
        if u in (a, b) or v in (a, b):
            other = a if b in (u, v) else b
            ext.append((other, lab))
        else:
            keep.append((a, b, lab))
    if len(ext) != 2:  # theta graph guard: bubble excision needs external legs
        return None
    (x, la), (y, _) = ext
    keep.append((x, y, la))
    fac = f"delta({par[0]},{par[1]})/(2*{par[0]}+1)"
    return Graph(keep), fac, 0, 0


def reduce_triangle(g: Graph, tri):
    a, b, c = tri
    inside, legs, keep = [], [], []
    for u, v, lab in g.edges:
        pin = (u in tri) + (v in tri)
        if pin == 2:
            inside.append(lab)
        elif pin == 1:
            legs.append(lab)
            keep.append((u, v, lab))
        else:
            keep.append((u, v, lab))
    if len(inside) != 3 or len(legs) != 3:
        return None
    w = f"T{next(_fresh)}"
    merged = []
    for u, v, lab in keep:
        u2 = w if u in tri else u
        v2 = w if v in tri else v
        merged.append((u2, v2, lab))
    fac = "sixj(" + ",".join(inside + legs) + ")"
    return Graph(merged), fac, 1, 0


def interchanges(g: Graph):
    """All edge-flip moves. For an internal edge e=(u,v): pick one other
    neighbor P of u and one other neighbor Q of v, and swap them across e.
    This is the graphical (ab)c -> a(bc) recoupling identity: it emits one
    6j and relabels e with a new summed intermediate x."""
    out = []
    for u, v, lab in g.edges:
        un = [(w, l) for w, l, _ in g.adj[u] if w != v]
        vn = [(w, l) for w, l, _ in g.adj[v] if w != u]
        if len(un) != 2 or len(vn) != 2:
            continue
        for (P, pl) in un:
            for (Q, ql) in vn:
                x = f"x{next(_fresh)}"
                edges = []
                done_p = done_q = done_e = False
                for a, b, l2 in g.edges:
                    if not done_e and {a, b} == {u, v} and l2 == lab:
                        edges.append((u, v, x)); done_e = True
                    elif not done_p and {a, b} == {u, P} and l2 == pl:
                        edges.append((v, P, pl)); done_p = True
                    elif not done_q and {a, b} == {v, Q} and l2 == ql:
                        edges.append((u, Q, ql)); done_q = True
                    else:
                        edges.append((a, b, l2))
                ng = Graph(edges)
                if ng.check_cubic():
                    fac = f"sum_{x}(2*{x}+1)*sixj({pl},{ql},{lab},...,{x})"
                    out.append((ng, fac, 1, 1))
    return out


# ----------------------------------------------------------------------------
# Search layer
# ----------------------------------------------------------------------------
def heuristic(g: Graph):
    """Admissible lower bound. Each 6j-emitting triangle removes 2 vertices;
    the goal (theta) has 2 vertices, so >= (n-2)/2 more 6j's are needed.
    If girth >= 4 nothing but an interchange applies first: >= 1 summation."""
    h = max(0, (g.n - 2) // 2)
    if g.n > 2 and g.girth_lower() >= 4:
        h += SUM_PENALTY
    return h


def is_goal(g: Graph):
    return g.n <= 2  # theta graph: pure normalization, value 1


def solve(g: Graph, verbose=False):
    start = (heuristic(g), 0, next(_fresh), g, [])
    open_heap = [start]
    best_g = {g.wl_hash(): 0}
    expanded = 0
    while open_heap:
        f, cost, _, cur, facs = heapq.heappop(open_heap)
        if is_goal(cur):
            return {
                "factors": facs,
                "sixj": sum(1 for fa in facs if fa.startswith("sixj") or "sixj" in fa),
                "sums": sum(1 for fa in facs if fa.startswith("sum_")),
                "cost": cost,
                "expanded": expanded,
            }
        expanded += 1
        children = []
        for pair in cur.bubbles():
            children.append(excise_bubble(cur, pair))
        for tri in cur.triangles():
            children.append(reduce_triangle(cur, tri))
        if not cur.triangles() and not cur.bubbles():
            children.extend(interchanges(cur))
        for ch in children:
            if ch is None:
                continue
            ng, fac, d6, ds = ch
            nc = cost + d6 + SUM_PENALTY * ds
            key = ng.wl_hash()
            if key in best_g and best_g[key] <= nc:
                continue
            best_g[key] = nc
            heapq.heappush(
                open_heap,
                (nc + heuristic(ng), nc, next(_fresh), ng, facs + [fac]),
            )
    return None


# ----------------------------------------------------------------------------
# Test graphs
# ----------------------------------------------------------------------------
def tetrahedron():
    return Graph([(1, 2, "a"), (1, 3, "b"), (1, 4, "c"),
                  (2, 3, "f"), (3, 4, "d"), (2, 4, "e")])


def prism():
    return Graph([(1, 2, "l1"), (2, 3, "l2"), (3, 1, "l3"),
                  (4, 5, "k1"), (5, 6, "k2"), (6, 4, "k3"),
                  (1, 4, "j1"), (2, 5, "j2"), (3, 6, "j3")])


def k33():
    """Twisted prism = K3,3 = the 9j symbol."""
    e, labs = [], iter("abcdefghi")
    for u in (1, 2, 3):
        for v in (4, 5, 6):
            e.append((u, v, next(labs)))
    return Graph(e)


def cube():
    """Q3, girth 4 — a 12j-class graph."""
    e = []
    labs = iter([f"j{i}" for i in range(1, 13)])
    verts = list(range(8))
    for u in verts:
        for v in verts:
            if u < v and bin(u ^ v).count("1") == 1:
                e.append((u + 1, v + 1, next(labs)))
    return Graph(e)


if __name__ == "__main__":
    for name, g in [("tetrahedron (6j)", tetrahedron()),
                    ("prism (separable)", prism()),
                    ("K3,3 (9j core)", k33()),
                    ("cube Q3 (12j class)", cube())]:
        assert g.check_cubic(), name
        r = solve(g)
        print(f"{name:22s} n={g.n}  ->  {r['sixj']} sixj, {r['sums']} sums, "
              f"cost={r['cost']}, expanded={r['expanded']}")
        for fa in r["factors"]:
            print("     ", fa)
        print()
