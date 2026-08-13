# yutsis — a modern reduction engine for angular-momentum recoupling

Optimal-form reduction of Yutsis graphs (closed angular-momentum diagrams)
by A* over the classical rewrite rules, with a brute-force magnetic-sum
oracle as numerical ground truth. Lineage: the algebraic-optimization
problem attacked as an AI search problem in the early 1980s (Williams /
Danos, NBS), automated heuristically by GYutsis (Van Dyck & Fack 2003),
reframed here with modern optimal search and a road to learned heuristics
and quantum-circuit compilation.

## Files
- yutsis.py     graph layer, rewrite moves, A* (+greedy) solver
- oracle.py     ClosedDiagram: direct m-summation over wigner_3j
- test_oracle.py  CI suite (all passing)
- stress.py     scaling experiments

## Verified results (v0)
- Oracle conventions phase-exact: tetrahedron == wigner_6j on integer and
  half-integer cases; theta = (-1)^(j1+j2+j3) with the documented
  odd-permutation node order (the node-sign convention, caught as designed)
- K3,3 closed diagram == wigner_9j EXACTLY (ratio +1.0000, three cases)
- Solver benchmarks reproduce known forms: tetra -> one 6j; prism ->
  {6j}{6j} (magnitude exact; j-dependent sign pinned by oracle = milestone-2
  phase work); K3,3 -> sum_x(2x+1) x three 6j (verified to 1e-10);
  cube Q3 -> one sum, four 6j

## Findings (the honest part)
1. 1-WL hashing collapses all cubic graphs (regular-graph failure mode) —
   exact canonicalization required; GNN heuristics will need expressivity
   beyond plain message passing for the same reason
2. Fresh summation labels defeat naive dedup at n > 8 — nauty-style
   canonical labeling is required for scale
3. Girth-5 graphs (Petersen) defeat both A* and weighted greedy under
   blind edge flips: ~60-wide branching with no triangle payoff for two
   plies. Motivates cycle-targeted moves (the GYutsis girth strategy) as
   the milestone-3 move set

## Roadmap
1. Phase engine: Danos-consistent signs/arrows derived, validated against
   the oracle in CI (prism sign is the first target)
2. Cycle-targeted interchange moves; nauty canonicalization; general
   n-line separator cuts
3. Backends: sympy exact, wigxjpf fast float
4. Learned guidance: GNN value function (>1-WL expressivity), MCTS
5. Applications: SU(2) tensor-network contraction planning; quantum Schur /
   CG-cascade circuit compilation (formula size = gate count)

## Run
    python3 yutsis.py       # benchmarks
    python3 test_oracle.py  # ground-truth suite
