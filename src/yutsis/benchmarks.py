"""Reference graphs with known reduction structure.

Both structural (Graph) and oriented (OGraph) builders live here, so a
fixture is defined once and imported by tests and scripts alike.
"""
import random

from .graph import Graph
from .state import OGraph


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
    """Q3, girth 4 -- a 12j-class graph."""
    e, i = [], 1
    for u in range(8):
        for v in range(8):
            if u < v and bin(u ^ v).count("1") == 1:
                e.append((u + 1, v + 1, f"j{i}")); i += 1
    return Graph(e)


def petersen():
    """Girth 5: the current open wall for the v0 move set."""
    e = []
    for u in range(5):
        e.append((u, (u + 1) % 5, f"o{u}"))
        e.append((u, u + 5, f"s{u}"))
        e.append((u + 5, (u + 2) % 5 + 5, f"i{u}"))
    return Graph(e)


def random_cubic(n, seed=0):
    rng = random.Random(seed)
    while True:
        stubs = [v for v in range(n) for _ in range(3)]
        rng.shuffle(stubs)
        edges = [(stubs[i], stubs[i + 1]) for i in range(0, len(stubs), 2)]
        if any(u == v for u, v in edges):
            continue
        if len({tuple(sorted(e)) for e in edges}) != len(edges):
            continue
        adj = {v: set() for v in range(n)}
        for u, v in edges:
            adj[u].add(v); adj[v].add(u)
        seen, stack = {0}, [0]
        while stack:
            for w in adj[stack.pop()]:
                if w not in seen:
                    seen.add(w); stack.append(w)
        if len(seen) == n:
            return Graph([(u, v, f"j{i}") for i, (u, v) in enumerate(edges)])


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


def oriented_k33():
    """K3,3 as an oriented state: the 9j symbol. Rows 1-3, columns 4-6,
    edge labels a..i laid out as the 9j matrix."""
    edges = {}
    verts = {"1": ("a", "b", "c"), "2": ("d", "e", "f"), "3": ("g", "h", "i"),
             "4": ("a", "d", "g"), "5": ("b", "e", "h"), "6": ("c", "f", "i")}
    lab = iter("abcdefghi")
    for u in "123":
        for v in "456":
            edges[next(lab)] = (u, v)
    return OGraph(edges, verts)


def oriented_dumbbell():
    """Two bubbles joined by a path: the fixture that exercises the
    bubble path (delta, 1/(2j+1), sign) end to end.

    Not to be confused with the k=1 DUMBBELL TERMINAL (two tadpoles
    joined by a bridge, yutsis.exact_moves.dumbbell_factor) -- this one
    is a four-vertex diagram with no self-loop. The name predates the
    k=1 sector; it is kept because tests and the DEVLOG refer to it."""
    edges = {"p": ("U", "V"), "q": ("U", "V"), "a": ("W", "U"),
             "b": ("V", "Z"), "c": ("W", "Z"), "d": ("W", "Z")}
    verts = {"U": ("p", "q", "a"), "V": ("p", "q", "b"),
             "W": ("a", "c", "d"), "Z": ("b", "c", "d")}
    return OGraph(edges, verts)


def oriented_petersen():
    """The Petersen graph as an oriented state: a 15j symbol. Outer
    cycle O0..O4, inner pentagram I0..I4, spokes between them."""
    edges, verts = {}, {}
    for u in range(5):
        edges[f"o{u}"] = (f"O{u}", f"O{(u+1)%5}")
        edges[f"s{u}"] = (f"O{u}", f"I{u}")
        edges[f"i{u}"] = (f"I{u}", f"I{(u+2)%5}")
    for u in range(5):
        verts[f"O{u}"] = (f"o{(u-1)%5}", f"o{u}", f"s{u}")
        verts[f"I{u}"] = (f"s{u}", f"i{u}", f"i{(u-2)%5}")
    return OGraph(edges, verts)

