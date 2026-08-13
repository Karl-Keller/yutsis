"""oriented.py -- milestone 2, second half: oriented, slot-ordered states
with EXACT sign tracking for triangle reduction.

An OGraph carries what the search Graph discards: each edge's orientation
(tail -> head) and each vertex's ordered 3j slots. reduce_triangle_exact
then computes its emitted factor's sign constructively:

  1. Cap the triangle: its three vertices (actual slot orders and
     orientations) plus a new vertex G holding the legs at their far
     ends, slots (leg_a, leg_b, leg_c). tetra_to_6j reduces this closed
     cap to (-1)^phase x 6j.
  2. Cap-theta correction: the dual pairing contributes (-1)^(2j) for
     every leg whose triangle-side end is a HEAD (derivation: the
     same-order, uniformly oriented theta is +1; each reversal costs
     (-1)^(2j)).
  3. The residual graph replaces the triangle by W with slots
     (leg_a, leg_b, leg_c), each leg keeping the endpoint role the
     triangle had.

The final two-vertex state is a theta whose sign theta_sign computes by
the same two rules. End-to-end validation: reducing the oriented prism
must reproduce the prism phase theorem's value against the oracle.
"""
from __future__ import annotations
from .phase import PhaseExpr, tetra_to_6j


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


def reduce_triangle_exact(og: OGraph, tri):
    """Returns (new_OGraph, PhaseExpr, sixj_args) with the sign exact."""
    a, b, c = tri
    inside, legs = {}, {}
    for lab, (t, h) in og.edges.items():
        pin = (t in tri) + (h in tri)
        if pin == 2:
            other = ({a, b, c} - {t, h}).pop()
            if other in inside:
                return None
            inside[other] = lab
        elif pin == 1:
            w = t if t in tri else h
            if w in legs:
                return None
            legs[w] = lab
    if len(inside) != 3 or len(legs) != 3:
        return None
    leg_order = (legs[a], legs[b], legs[c])

    # -- cap tetrahedron: triangle verts as-is + G at the legs' far ends
    cap_edges, theta_corr = {}, PhaseExpr()
    for lab, (t, h) in og.edges.items():
        if lab in inside.values():
            cap_edges[lab] = (t, h)
        elif lab in leg_order:
            if t in tri:                # tail at triangle -> G is head
                cap_edges[lab] = (t, "G")
            else:                        # head at triangle -> G is tail
                cap_edges[lab] = ("G", h)
                theta_corr.add_2j(lab)   # dual-pairing flip cost
    cap_verts = {v: og.verts[v] for v in tri}
    cap_verts["G"] = leg_order
    cap_phase, sixj_args = tetra_to_6j(cap_edges, cap_verts)
    phase = cap_phase * theta_corr

    # -- residual: W inherits each leg's triangle-side endpoint role
    new_edges = {}
    for lab, (t, h) in og.edges.items():
        if lab in inside.values():
            continue
        if lab in leg_order:
            new_edges[lab] = ("W" + a, h) if t in tri else (t, "W" + a)
        else:
            new_edges[lab] = (t, h)
    new_verts = {v: s for v, s in og.verts.items() if v not in tri}
    new_verts["W" + a] = leg_order
    return OGraph(new_edges, new_verts), phase, sixj_args


def theta_sign(og: OGraph):
    """Sign of a two-vertex, three-edge closed state. Canonical +1 form:
    identical slot orders, all edges tail at the first vertex. Each
    reversed edge costs (-1)^(2j); an odd slot permutation costs
    (-1)^(triad sum)."""
    assert og.n == 2 and len(og.edges) == 3
    v1, v2 = sorted(og.verts)
    s1, s2 = og.verts[v1], og.verts[v2]
    phase = PhaseExpr()
    perm = tuple(s2.index(x) for x in s1)
    inv = sum(1 for i in range(3) for k in range(i + 1, 3) if perm[i] > perm[k])
    if inv % 2:
        phase.add_triad(list(s1))
    for lab, (t, h) in og.edges.items():
        if t != v1:
            phase.add_2j(lab)
    return phase


def oriented_prism():
    """The oracle's prism, with its exact orientations and slot orders."""
    edges = {
        "l1": ("A", "B"), "l2": ("B", "C"), "l3": ("C", "A"),
        "k1": ("D", "E"), "k2": ("E", "F"), "k3": ("F", "D"),
        "j1": ("A", "D"), "j2": ("B", "E"), "j3": ("C", "F"),
    }
    verts = {
        "A": ("l1", "l3", "j1"), "B": ("l2", "l1", "j2"),
        "C": ("l3", "l2", "j3"), "D": ("k3", "k1", "j1"),
        "E": ("k1", "k2", "j2"), "F": ("k2", "k3", "j3"),
    }
    return OGraph(edges, verts)


def reduce_prism_exact():
    """Full oriented reduction of the prism: two exact triangle
    reductions plus the final theta sign. Returns (PhaseExpr, factors)."""
    og = oriented_prism()
    total, factors = PhaseExpr(), []
    for _ in range(2):
        tri = og.triangles()[0]
        og, ph, args = reduce_triangle_exact(og, tri)
        total, factors = total * ph, factors + [args]
    total = total * theta_sign(og)
    return total, factors
