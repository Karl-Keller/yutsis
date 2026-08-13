# yutsis — a modern reduction engine for angular-momentum recoupling

Optimal-form reduction of Yutsis graphs (closed angular-momentum diagrams)
by A* search over the classical rewrite rules. Seed of a public solver for
the algebraic-optimization problem first attacked as an AI search problem
in the early 1980s (Williams / Danos lineage, NBS), heuristically automated
by GYutsis (Van Dyck & Fack, 2003), and here reframed with modern optimal
search — with a road to learned heuristics and quantum-circuit compilation.

## What works (v0, verified)
- Cubic multigraph state space with exact canonical certificates
  (1-WL provably fails on regular graphs — see the bug story in comments)
- Moves: bubble excision (delta), triangle reduction (one 6j),
  edge interchange (one 6j + one summation) — the (ab)c -> a(bc) flip
- A* with admissible bound: h = (n-2)/2 + SUM_PENALTY * [girth >= 4]
- Benchmarks reproduce known results:
  tetrahedron -> one 6j; prism -> {6j}{6j}, no sums;
  K3,3 -> sum_x (2x+1) x three 6j (the 9j identity, verified numerically
  against sympy to 1e-10 on integer and half-integer cases);
  cube Q3 -> one sum, four 6j (12j class)

## Roadmap
1. Phase engine: Danos-consistent vertex signs, arrows, and (-1) phases,
   validated by a brute-force magnetic-sum oracle (closed diagrams evaluated
   by direct m-summation over sympy wigner_3j) in CI
2. Scale: individualized-refinement canonicalization (nauty), separator
   enumeration for general n-line cuts, cost model per numeric backend
3. Backends: sympy (exact), wigxjpf/fastwigxj (fast float)
4. Learned guidance: GNN value function (expressivity beyond 1-WL required
   — the closed-set bug is the existence proof), MCTS for large diagrams
5. Applications: SU(2) tensor-network contraction planning; quantum Schur
   transform / CG-cascade circuit compilation where formula size = gate count

## Run
    python3 yutsis.py
