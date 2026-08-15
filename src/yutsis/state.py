"""Oriented, slot-ordered diagram states.

An OGraph carries what the search Graph discards: each edge's
orientation (tail -> head) and each vertex's ordered 3j slots. The
search layer never sees this module; the exact algebra in
yutsis.exact_moves is written entirely in terms of it.

Split out of yutsis.oriented in v0.8.2 (behavior-preserving); that name
survives as a re-export shim.
"""
from __future__ import annotations


class OGraph:
    """Oriented cubic multigraph. edges: {label: (tail, head)};
    verts: {vid: (label, label, label)} ordered 3j slots."""

    def __init__(self, edges, verts):
        self.edges = dict(edges)
        self.verts = {v: tuple(s) for v, s in verts.items()}

    @property
    def n(self):
        return len(self.verts)

    def triangles(self):
        out = []
        vs = sorted(self.verts)
        import itertools
        for a, b, c in itertools.combinations(vs, 3):
            def joined(u, v):
                return any(set(e) == {u, v} for e in self.edges.values())
            if joined(a, b) and joined(b, c) and joined(c, a):
                out.append((a, b, c))
        return out


def og_components(og: OGraph):
    """Split an OGraph into its connected components.

    States stopped being connected when bridge cut arrived."""
    adj = {}
    for lab, (t, h) in og.edges.items():
        adj.setdefault(t, set()).add(h)
        adj.setdefault(h, set()).add(t)
    seen, out = set(), []
    for start in sorted(og.verts):
        if start in seen:
            continue
        comp, stack = {start}, [start]
        seen.add(start)
        while stack:
            for w in adj.get(stack.pop(), ()):
                if w not in seen:
                    seen.add(w)
                    comp.add(w)
                    stack.append(w)
        edges = {lab: (t, h) for lab, (t, h) in og.edges.items()
                 if t in comp}
        out.append(OGraph(edges, {v: og.verts[v] for v in comp}))
    return out
