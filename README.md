# yutsis

![CI](https://github.com/Karl-Keller/yutsis/actions/workflows/ci.yml/badge.svg)

Optimal-form reduction of angular-momentum recoupling graphs (Yutsis
diagrams) by A* search over the classical rewrite rules — with exact,
machine-derived phases, and every formula verified against brute-force
magnetic summation.

General recoupling coefficients (3nj symbols) reduce to summation
formulae over products of 6j symbols. Finding the *cheapest* such
formula — fewest summation variables, fewest factors — is a search
problem over graph rewrites on cubic multigraphs. This package treats
it as one: nauty-canonicalized states, cycle-targeted moves, admissible
heuristics, a symbolic phase engine, and two independent numerical
oracles (diagram-level brute-force m-summation; state-level overlaps of
explicitly constructed Clebsch-Gordan coupled states). No formula is
trusted on inspection.

## Install

    pip install -e ".[dev,perf]"   # perf pulls pynauty for fast canonicalization
    pytest -q                      # 23 tests: oracles, theorems, compiler
    python -m yutsis               # benchmark reductions

## Showcase: the Petersen graph (a 15j symbol)

The Petersen graph — girth 5, no local bubble or triangle anywhere — is
the classic hard case for recoupling reduction. The solver reduces it
in 11 node expansions (~0.01 s) to a fully signed formula: **three
nested summations, seven 6j symbols**, and a thirteen-term phase.

```python
from sympy import S
import yutsis.oriented as O

og = ...  # oriented Petersen (see scripts/verify_petersen.py)
expr = O.solve_exact(og)          # 7 sixj, 3 sums, exact phase
value = O.evaluate_expr(expr, j_assignment)
```

Verification: on a nonzero labeling (pentagon spins 1/2, spokes 1,
pentagram (1/2, 1/2, 1/2, 3/2, 3/2)), the formula evaluates to
**+0.004629630**, matching brute-force evaluation of the closed
diagram — a direct sum over **995,328** magnetic quantum number
assignments — to 1e-9. Run it yourself:

    python scripts/verify_petersen.py

## Verified results (v0.6.0)

- **Oracle conventions phase-exact**: the Racah-oriented tetrahedron
  reproduces `wigner_6j` including sign on integer and half-integer
  cases; the K3,3 diagram equals `wigner_9j` at ratio +1.0000
- **Benchmarks**: tetrahedron -> one 6j; prism -> {6j}{6j} sum-free;
  K3,3 -> the 9j single-sum identity (1e-10); cube Q3 -> one sum, four
  6j; Petersen -> three sums, seven 6j (verified as above)
- **The prism phase theorem** (`yutsis.phase`): derived analytically,
  reduced symbolically by the phase engine, verified value-exact on 12
  random labelings including half-integers:
  `prism = (-1)^(j1+j2+j3+2l1+2k2+2k3) x {l1 l3 j1; j3 j2 l2} x {k1 k3 j1; j3 j2 k2}`
  The derivation also exposed (and fixed) a structurally wrong 6j
  argument pairing in the naive factor emission
- **The flip phase, recovered by machine**: the interchange move's
  phase was determined by constrained fit against `wigner_9j` over 22
  labelings — 8 survivors out of 8192 candidate laws, one
  triad-equivalence class, canonical representative `(-1)^(p+q+e+x)`:
  the textbook recoupling phase
- **Fully signed end-to-end** (`solve_exact`): every move emits exact
  algebra; whole formulas validated against the oracle, including the
  bubble path (delta, 1/(2j+1), sign)
- **Recoupling gate compiler** (`yutsis.circuits`): any two binary
  coupling trees glue into a closed graph, reduce to a calibrated
  physical matrix element (validated 20/20 against explicit CG-state
  overlaps), and compile via associahedron BFS into elementary
  6j-weighted unitary blocks — composition equal to the direct
  transform, and unitary, to ~1e-16. The Schur-transform gate family,
  machine-verified

## Findings (the honest part)

1. 1-WL hashing collapses all cubic graphs (regular-graph blindness);
   canonicalization now runs through nauty's individualization-
   refinement — 1-WL plus symmetry breaking plus automorphism pruning —
   and learned heuristics will need expressivity beyond plain message
   passing for the same reason
2. Fresh summation labels defeat naive dedup above n = 8; exact nauty
   certificates on the subdivided multigraph resolve it
3. Girth-5 inputs defeated both A* and weighted greedy under blind edge
   flips; cycle-targeted interchanges (the girth strategy) cut
   branching from ~4|E| to ~4L and retired the wall — while the known
   counter-example to girth-first greediness (Van Dyck & Fack) says
   move ordering should ultimately be learned

## Roadmap

1. Cost-aware associahedron search: solver summation costs steering
   coupling-path selection; qudit generalization; Qiskit emission
2. General n-line separator cuts; wigxjpf fast-float backend
3. Learned guidance: GNN value function (> 1-WL expressivity), MCTS
4. Applications: SU(2)-symmetric tensor-network contraction planning;
   quantum Schur / Clebsch-Gordan cascade circuit optimization, where
   formula size is gate count

## Lineage

See [docs/HISTORY.md](docs/HISTORY.md) and [docs/DEVLOG.md](docs/DEVLOG.md)
— from Slagle's SAINT and the Yutsis–Levinson–Vanagas calculus through
Danos and Williams at NBS, the GYutsis heuristics of Van Dyck & Fack,
to this reframing with modern optimal search and machine-verified
phases.

MIT license. To cite, see [CITATION.cff](CITATION.cff).
