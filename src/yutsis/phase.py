"""phase.py -- the phase engine, v1: exact signs for closed tetrahedra.

Two exact symmetry rules of the oracle's diagram algebra generate all the
phase bookkeeping needed to reduce any closed tetrahedron to a signed
Wigner 6j:

  1. Permuting the slot order of one vertex's 3j multiplies the diagram
     by (-1)^(sum of that vertex's triad) if the permutation is odd, +1
     if even.
  2. Reversing one edge's orientation multiplies the diagram by
     (-1)^(2 j_e).

A phase is represented symbolically as PhaseExpr: an exponent that is an
integer linear combination of edge j's (coefficients mod 4, since
(-1)^(4j) = +1 for any j). Reduction proceeds by brute-force matching of
the target tetrahedron onto the Racah template used by yutsis.oracle
(vertex bijections x slot rotations/swaps x orientation flips),
accumulating the symbolic phase along the way. The result is a theorem:
   diagram = (-1)^(PhaseExpr) x wigner_6j(args)
valid for ALL j assignments, and testable against the oracle numerically.
"""
from __future__ import annotations
import itertools
from fractions import Fraction


class PhaseExpr:
    """(-1) raised to an integer combination of j labels, coeffs mod 4."""

    def __init__(self, coeffs=None, const=0):
        self.c = dict(coeffs or {})
        self.k0 = const % 2
        self._norm()

    def _norm(self):
        self.c = {k: v % 4 for k, v in self.c.items() if v % 4}

    def add_triad(self, labels):
        for lab in labels:
            self.c[lab] = self.c.get(lab, 0) + 1
        self._norm()

    def add_2j(self, lab):
        self.c[lab] = self.c.get(lab, 0) + 2
        self._norm()

    def add_const(self, k=1):
        self.k0 = (self.k0 + k) % 2

    def __mul__(self, other):
        out = PhaseExpr(self.c, self.k0 + getattr(other, "k0", 0))
        for k, v in other.c.items():
            out.c[k] = out.c.get(k, 0) + v
        out._norm()
        return out

    def evaluate(self, jmap):
        e = sum(Fraction(c) * Fraction(jmap[k]) for k, c in self.c.items())
        assert e.denominator == 1, f"non-integer phase exponent {e}"
        return -1 if (e.numerator + self.k0) % 2 else 1

    def __repr__(self):
        if not self.c:
            return "-1" if self.k0 else "+1"
        terms = "+".join(f"{v}*{k}" if v > 1 else k
                         for k, v in sorted(self.c.items()))
        if self.k0:
            terms = "1+" + terms
        return f"(-1)^({terms})"


# The Racah template: yutsis.oracle.tetrahedron's structure. A closed
# diagram isomorphic to this, with these orientations and slot orders,
# equals wigner_6j(j1..j6) exactly (validated in tests/test_oracle.py).
TEMPLATE_EDGES = {  # eid: (tail, head)
    "e1": ("V2", "V1"), "e2": ("V3", "V1"), "e3": ("V4", "V1"),
    "e4": ("V3", "V4"), "e5": ("V4", "V2"), "e6": ("V2", "V3"),
}
TEMPLATE_VERTS = {
    "V1": ("e1", "e2", "e3"), "V2": ("e1", "e5", "e6"),
    "V3": ("e4", "e2", "e6"), "V4": ("e4", "e5", "e3"),
}
TEMPLATE_6J_ORDER = ("e1", "e2", "e3", "e4", "e5", "e6")

_PERMS3 = list(itertools.permutations(range(3)))


def _parity(p):
    inv = sum(1 for i in range(3) for k in range(i + 1, 3) if p[i] > p[k])
    return inv % 2


def tetra_to_6j(edges, verts):
    """Reduce a closed tetrahedron (oracle-style edges {eid:(tail,head)},
    verts {vid:(eid,eid,eid)}) to (PhaseExpr, sixj_arg_eids).

    Searches vertex bijections onto the template; for each, edge mapping
    is forced by shared-vertex-pair structure; then per-vertex slot
    permutations and per-edge flips are read off and their phases
    accumulated. Returns the first exact match (all are equivalent by the
    6j's tetrahedral symmetry -- the phase expression differs but agrees
    on every valid j assignment)."""
    vids = list(verts)
    assert len(vids) == 4 and len(edges) == 6
    # target: map vertex-pair -> eid
    pair2e = {}
    for eid, (t, h) in edges.items():
        pair2e[frozenset((t, h))] = eid
    tpair2e = {}
    for eid, (t, h) in TEMPLATE_EDGES.items():
        tpair2e[frozenset((t, h))] = eid

    for bij in itertools.permutations(vids):
        vmap = dict(zip(("V1", "V2", "V3", "V4"), bij))  # template -> target
        emap = {}
        ok = True
        for teid, (tt, th) in TEMPLATE_EDGES.items():
            key = frozenset((vmap[tt], vmap[th]))
            if key not in pair2e:
                ok = False
                break
            emap[teid] = pair2e[key]
        if not ok or len(set(emap.values())) != 6:
            continue
        phase = PhaseExpr()
        # orientation flips: template edge direction vs target direction
        for teid, (tt, th) in TEMPLATE_EDGES.items():
            eid = emap[teid]
            t_tail, t_head = vmap[tt], vmap[th]
            tail, head = edges[eid]
            if (tail, head) == (t_tail, t_head):
                pass
            elif (tail, head) == (t_head, t_tail):
                phase.add_2j(_lab(eid))
            else:
                ok = False
                break
        if not ok:
            continue
        # slot permutations: template vertex order mapped into target eids,
        # compared against the target vertex's actual slot order
        for tvid, tslots in TEMPLATE_VERTS.items():
            want = tuple(emap[te] for te in tslots)
            have = verts[vmap[tvid]]
            if set(want) != set(have):
                ok = False
                break
            perm = tuple(have.index(w) for w in want)
            if _parity(perm):
                phase.add_triad([_lab(e) for e in have])
        if not ok:
            continue
        return phase, tuple(_lab(emap[te]) for te in TEMPLATE_6J_ORDER)
    raise ValueError("not a tetrahedron matching the template topology")


def _lab(eid):
    return eid


# ----------------------------------------------------------------------------
# The prism phase theorem
# ----------------------------------------------------------------------------
def prism_theorem():
    """Derivation encoded: separating the oracle prism on its rungs
    (j1,j2,j3) yields prism = Tet_L x Tet_R exactly (the middle theta is
    +1 in these conventions; the two on-support metric insertions cancel
    since the rung triad sum is an integer). Each cap is the closed
    tetrahedron below; the phase engine reduces both to signed 6j's.

    Returns (phase_L, args_L, phase_R, args_R): the exact statement
      prism(l,k,j) = phase_L*phase_R x 6j(args_L) x 6j(args_R)."""
    # Left cap: prism vertices A,B,C + new vertex G, rungs oriented into G
    edges_L = {
        "l1": ("A", "B"), "l2": ("B", "C"), "l3": ("C", "A"),
        "j1": ("A", "G"), "j2": ("B", "G"), "j3": ("C", "G"),
    }
    verts_L = {
        "A": ("l1", "l3", "j1"), "B": ("l2", "l1", "j2"),
        "C": ("l3", "l2", "j3"), "G": ("j1", "j2", "j3"),
    }
    # Right cap: prism vertices D,E,F + new vertex G', rungs oriented out
    edges_R = {
        "k1": ("D", "E"), "k2": ("E", "F"), "k3": ("F", "D"),
        "j1": ("G", "D"), "j2": ("G", "E"), "j3": ("G", "F"),
    }
    verts_R = {
        "D": ("k3", "k1", "j1"), "E": ("k1", "k2", "j2"),
        "F": ("k2", "k3", "j3"), "G": ("j1", "j2", "j3"),
    }
    pl, al = tetra_to_6j(edges_L, verts_L)
    pr, ar = tetra_to_6j(edges_R, verts_R)
    return pl, al, pr, ar
