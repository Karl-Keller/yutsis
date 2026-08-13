"""oracle.py — brute-force ground truth for closed angular-momentum diagrams.

A ClosedDiagram fixes every convention explicitly:
  - each edge e has a j value and an orientation (tail -> head)
  - each vertex is an ORDERED triple of edge ids (the 3j argument order)
Value = sum over all m assignments of
  prod_edges (-1)^(j_e - m_e)  *  prod_vertices 3j(j_a j_b j_c; s_a m_a, s_b m_b, s_c m_c)
where an edge contributes +m at its tail vertex and -m at its head vertex.

This convention makes the theta graph evaluate to exactly 1 (triangle
allowed) and the standard tetrahedron orientation reproduce the Racah
sum formula for the 6j symbol exactly, phase included.
"""
from __future__ import annotations
import itertools
from functools import lru_cache
from sympy import S, N
from sympy.physics.wigner import wigner_3j


@lru_cache(maxsize=None)
def w3j(j1, j2, j3, m1, m2, m3):
    try:
        return float(wigner_3j(j1, j2, j3, m1, m2, m3))
    except ValueError:
        return 0.0


class ClosedDiagram:
    def __init__(self, edges, vertices):
        """edges: {eid: (tail_vertex, head_vertex, j)}
        vertices: {vid: (eid_a, eid_b, eid_c)}  -- ordered 3j slots."""
        self.edges = edges
        self.vertices = vertices
        for vid, tri in vertices.items():
            assert len(tri) == 3, vid
        for eid, (t, h, j) in edges.items():
            uses = sum(tri.count(eid) for tri in vertices.values())
            assert uses == 2, f"edge {eid} used {uses} times"

    def value(self):
        eids = list(self.edges)
        ranges = []
        for eid in eids:
            j = self.edges[eid][2]
            ranges.append([S(k) - j for k in range(int(2 * j) + 1)])
        total = 0.0
        for ms in itertools.product(*ranges):
            m = dict(zip(eids, ms))
            phase = 1
            for eid in eids:
                j = self.edges[eid][2]
                p = j - m[eid]
                phase *= (-1) ** int(p) if p == int(p) else complex(-1) ** p
            term = phase
            for vid, tri in self.vertices.items():
                js, mms = [], []
                for eid in tri:
                    t, h, j = self.edges[eid]
                    js.append(j)
                    mms.append(m[eid] if t == vid else -m[eid])
                term *= w3j(js[0], js[1], js[2], mms[0], mms[1], mms[2])
                if term == 0:
                    break
            total += term
        return total


# ----------------------------------------------------------------------------
# Reference diagrams with explicit standard orientations
# ----------------------------------------------------------------------------
def theta(j1, j2, j3):
    """Two vertices, three parallel edges. Should equal 1 iff triangle holds."""
    edges = {"e1": ("A", "B", j1), "e2": ("A", "B", j2), "e3": ("A", "B", j3)}
    verts = {"A": ("e1", "e2", "e3"), "B": ("e3", "e2", "e1")}
    return ClosedDiagram(edges, verts)


def tetrahedron(j1, j2, j3, j4, j5, j6):
    """Racah's sum formula for {j1 j2 j3; j4 j5 j6} encoded as a diagram.
    Orientation/order chosen to match the standard identity:
      sum (-1)^sum(j-m) 3j(j1 j2 j3;-m1-m2-m3) 3j(j1 j5 j6;m1 -m5 m6)
                        3j(j4 j2 j6;m4 m2 -m6) 3j(j4 j5 j3;-m4 m5 m3)
    Vertices V1..V4; edge tails give +m, heads give -m."""
    edges = {
        "e1": ("V2", "V1", j1),  # +m1 at V2, -m1 at V1
        "e2": ("V3", "V1", j2),
        "e3": ("V4", "V1", j3),
        "e4": ("V3", "V4", j4),  # +m4 at V3, -m4 at V4
        "e5": ("V4", "V2", j5),  # +m5 at V4, -m5 at V2
        "e6": ("V2", "V3", j6),  # +m6 at V2, -m6 at V3
    }
    verts = {
        "V1": ("e1", "e2", "e3"),
        "V2": ("e1", "e5", "e6"),
        "V3": ("e4", "e2", "e6"),
        "V4": ("e4", "e5", "e3"),
    }
    return ClosedDiagram(edges, verts)


def prism(l1, l2, l3, k1, k2, k3, j1, j2, j3):
    """Triangular prism: left triangle l's, right triangle k's, rungs j's.
    Orientation chosen 'naively'; the oracle tells us the resulting phase."""
    edges = {
        "l1": ("A", "B", l1), "l2": ("B", "C", l2), "l3": ("C", "A", l3),
        "k1": ("D", "E", k1), "k2": ("E", "F", k2), "k3": ("F", "D", k3),
        "j1": ("A", "D", j1), "j2": ("B", "E", j2), "j3": ("C", "F", j3),
    }
    verts = {
        "A": ("l1", "l3", "j1"), "B": ("l2", "l1", "j2"), "C": ("l3", "l2", "j3"),
        "D": ("k3", "k1", "j1"), "E": ("k1", "k2", "j2"), "F": ("k2", "k3", "j3"),
    }
    return ClosedDiagram(edges, verts)


def k33(a, b, c, d, e, f, g, h, i):
    """Complete bipartite K3,3 with rows (L1 L2 L3), cols (R1 R2 R3);
    edge j-values laid out as the 9j matrix:
        L1: a b c / L2: d e f / L3: g h i  (column = R index)."""
    labels = {("L1","R1"):a, ("L1","R2"):b, ("L1","R3"):c,
              ("L2","R1"):d, ("L2","R2"):e, ("L2","R3"):f,
              ("L3","R1"):g, ("L3","R2"):h, ("L3","R3"):i}
    edges = {}
    for (u, v), j in labels.items():
        edges[u + v] = (u, v, j)
    verts = {
        "L1": ("L1R1", "L1R2", "L1R3"),
        "L2": ("L2R1", "L2R2", "L2R3"),
        "L3": ("L3R1", "L3R2", "L3R3"),
        "R1": ("L1R1", "L2R1", "L3R1"),
        "R2": ("L1R2", "L2R2", "L3R2"),
        "R3": ("L1R3", "L2R3", "L3R3"),
    }
    return ClosedDiagram(edges, verts)
