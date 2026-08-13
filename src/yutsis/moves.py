"""Rewrite moves. Each returns (new_graph, factor_string, d_sixj, d_sums)
or None when the pattern guard fails.

v0 tracks factors structurally; the Danos-consistent phase/weight engine
(milestone 2) will derive signs from node orders and arrows, validated
against yutsis.oracle in CI.
"""
from __future__ import annotations
import itertools
from .graph import Graph

fresh = itertools.count(1)


def excise_bubble(g: Graph, pair):
    u, v = pair
    par = [lab for a, b, lab in g.edges if (a, b) == pair]
    ext, keep = [], []
    for a, b, lab in g.edges:
        if (a, b) == pair:
            continue
        if u in (a, b) or v in (a, b):
            other = a if b in (u, v) else b
            ext.append((other, lab))
        else:
            keep.append((a, b, lab))
    if len(ext) != 2:
        return None
    (x, la), (y, _) = ext
    keep.append((x, y, la))
    fac = f"delta({par[0]},{par[1]})/(2*{par[0]}+1)"
    return Graph(keep), fac, 0, 0


def reduce_triangle(g: Graph, tri):
    """Contract a triangle, emitting its cap-tetrahedron 6j.

    Argument order encodes the OPPOSITE-EDGE pairing proved by the prism
    phase theorem (yutsis.phase, Finding 4): column i pairs the inside
    edge NOT touching triangle vertex i with the leg AT vertex i. The
    overall sign still requires oriented, slot-ordered graph states
    (milestone 2 continuation); emitted as sixj(...) up to phase."""
    a, b, c = tri
    inside_at, leg_at, keep = {}, {}, []
    for u, v, lab in g.edges:
        pin = (u in tri) + (v in tri)
        if pin == 2:
            other = ({a, b, c} - {u, v}).pop()
            if other in inside_at:
                return None  # doubled inside edge: not a clean triangle
            inside_at[other] = lab
        elif pin == 1:
            w = u if u in tri else v
            if w in leg_at:
                return None
            leg_at[w] = lab
            keep.append((u, v, lab))
        else:
            keep.append((u, v, lab))
    if len(inside_at) != 3 or len(leg_at) != 3:
        return None
    w = f"T{next(fresh)}"
    merged = [(w if u in tri else u, w if v in tri else v, lab)
              for u, v, lab in keep]
    top = [inside_at[x] for x in (a, b, c)]
    bot = [leg_at[x] for x in (a, b, c)]
    fac = "sixj(" + ",".join(top + bot) + ")"
    return Graph(merged), fac, 1, 0


def interchanges(g: Graph):
    """All edge-flip moves: for internal edge e=(u,v), swap one neighbor of
    u with one neighbor of v across e. The graphical (ab)c -> a(bc)
    recoupling identity: emits one 6j, relabels e with a summed x."""
    out = []
    for u, v, lab in g.edges:
        un = [(w, l) for w, l, _ in g.adj[u] if w != v]
        vn = [(w, l) for w, l, _ in g.adj[v] if w != u]
        if len(un) != 2 or len(vn) != 2:
            continue
        for (P, pl) in un:
            for (Q, ql) in vn:
                x = f"x{next(fresh)}"
                edges, done = [], set()
                for a, b, l2 in g.edges:
                    if "e" not in done and {a, b} == {u, v} and l2 == lab:
                        edges.append((u, v, x)); done.add("e")
                    elif "p" not in done and {a, b} == {u, P} and l2 == pl:
                        edges.append((v, P, pl)); done.add("p")
                    elif "q" not in done and {a, b} == {v, Q} and l2 == ql:
                        edges.append((u, Q, ql)); done.add("q")
                    else:
                        edges.append((a, b, l2))
                ng = Graph(edges)
                if ng.check_cubic():
                    fac = f"sum_{x}(2*{x}+1)*sixj({pl},{ql},{lab},...,{x})"
                    out.append((ng, fac, 1, 1))
    return out
