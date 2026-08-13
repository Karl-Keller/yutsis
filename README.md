# yutsis

Optimal-form reduction of angular-momentum recoupling graphs (Yutsis
diagrams) by A* search over the classical rewrite rules — with a
brute-force magnetic-sum oracle as numerical ground truth.

General recoupling coefficients (3nj symbols) reduce to summation formulae
over products of 6j symbols. Finding the *cheapest* such formula — fewest
summation variables, fewest factors — is a search problem over graph
rewrites: bubble excision, triangle reduction, and edge interchange on
cubic multigraphs. This package treats it as one, with an admissible
heuristic and provable optimality at small sizes, and every structural
claim validated numerically against direct magnetic summation.

## Install

    pip install -e ".[dev]"
    pytest -q          # ground-truth + solver suites
    python -m yutsis   # benchmark reductions

## Example

```python
from yutsis import solve
from yutsis.benchmarks import k33

r = solve(k33())          # the 9j symbol as a closed graph
print(r["sixj"], r["sums"])   # -> 3, 1  (sum_x (2x+1) x three 6j's)
```

## Verified (v0)

- Oracle conventions are phase-exact: the tetrahedron diagram reproduces
  `wigner_6j` including sign on integer and half-integer cases; the K3,3
  diagram equals `wigner_9j` at ratio +1.0000
- Solver reproduces known forms: tetrahedron -> one 6j; prism -> {6j}{6j}
  with no summation; K3,3 -> the 9j single-sum identity (verified to
  1e-10); cube Q3 -> one sum, four 6j
- The prism phase theorem (v0.2.0, `yutsis.phase`): the separation of the
  prism on its rungs is derived analytically in the oracle's conventions,
  and the phase engine reduces both cap tetrahedra to signed 6j's
  symbolically. Result, value-exact against the oracle on 12 random
  labelings including half-integers:
  `prism = (-1)^(j1+j2+j3+2l1+2k2+2k3) x {l1 l3 j1; j3 j2 l2} x {k1 k3 j1; j3 j2 k2}`
  The derivation also exposed that v0's naive 6j argument pairing
  (inside-edges, legs) is structurally wrong -- the true pairing is
  opposite edges of the cap tetrahedron; earlier magnitude agreement was
  a label-symmetry coincidence. Milestone 2 continues: emit engine-derived
  factors from moves.py

## Findings

1. 1-WL hashing collapses all cubic graphs (regular-graph blindness) —
   exact canonicalization is required, and learned heuristics will need
   expressivity beyond plain message passing for the same reason
2. Fresh summation labels defeat naive dedup above n = 8 — nauty-style
   canonical labeling is the scaling milestone
3. Girth-5 inputs (Petersen) defeat both A* and weighted greedy under
   blind edge flips: cycle-targeted moves are required, and the known
   counter-example to girth-first greediness (Van Dyck & Fack) says their
   ordering should ultimately be learned, not hard-coded

## Roadmap

1. Phase engine (STARTED, first theorem proved): extend tetra_to_6j-style
   symbolic reduction to the triangle and interchange moves so moves.py
   emits exact signed factors, validated against the oracle in CI
2. Cycle-targeted interchanges; nauty canonicalization; general n-line
   separator cuts
3. Numeric backends: sympy (exact), wigxjpf (fast float)
4. Learned guidance: GNN value function, MCTS for large diagrams
5. Applications: SU(2)-symmetric tensor-network contraction planning;
   quantum Schur / Clebsch-Gordan cascade circuit compilation, where
   formula size is gate count

## Lineage

See [docs/HISTORY.md](docs/HISTORY.md) — from Slagle's SAINT and the
Yutsis-Levinson-Vanagas calculus through Danos and Williams at NBS, the
GYutsis heuristics of Van Dyck & Fack, to this reframing with modern
optimal search.

MIT license.
