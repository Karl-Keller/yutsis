# Next steps

Status assessment of the three original Findings and the concrete work
that closes each. Honest framing: all three are retired at benchmark
scale, not resolved in principle; each carries a residual that is a
research problem wearing an engineering costume. For submission venues
this document transposes into "Limitations and open problems."

## Finding 1 — 1-WL blindness (two-thirds closed)

The canonicalization half is done in principle, not just in practice:
nauty's individualization-refinement is the cure prescribed by the
failure mode (1-WL plus symmetry breaking plus automorphism pruning).

The open promissory note is the finding's second clause: learned
heuristics need expressivity beyond plain message passing. Standard
GNNs are provably bounded by 1-WL, so a naive learned value function
would be structurally blind to exactly the twisted-vs-untwisted
distinction our cost model turns on. K3,3 vs the prism — our own
failure case — is a ready-made benchmark for the fix.

Closure criterion: train a value function with an architecture that
exceeds 1-WL (subgraph GNNs, higher-order WL variants, or
identity-aware/random-feature GNNs — individualization as a learning
trick), show it separates the K3,3/prism family, and demonstrate it
beats the hand-built heuristic on a held-out graph distribution.

## Finding 2 — dedup collapse (nearly closed; one unwritten lemma)

Exact nauty certificates on the subdivided multigraph solve the
collapse outright, and nauty's pathological cases live far from our
sizes (swap to Traces or sparse nauty if n grows past a few dozen).

The residual is intellectual hygiene: states are merged by ANONYMOUS
topology, discarding j-labels, on the argument that future reduction
cost depends only on topology. The argument is correct but currently
folklore in a docstring. It deserves a stated one-paragraph lemma with
its boundary explicit: it holds for the current cost model, and would
FAIL for cost models pricing formulas by numerical magnitude or by
shared-label sparsity.

Closure criterion: write the merge lemma into the docs, with the
boundary conditions, and reference it from Graph.canonical().

## Finding 3 — girth-5 wall (open, and the deepest)

Cycle-targeted moves retired the wall at a price: A* is optimal only
within the restricted move class, and the Van Dyck-Fack counter-example
is standing evidence that girth-guided orderings can miss global
optima. Concretely: we do not know whether Petersen's minimum is three
summations or two.

Three prongs, ascending in ambition:

1. Certify or refute Petersen: run blind-move A* to completion with
   better pruning, or locate the minimal 15j form in the literature.
2. Build the RIGHT admissible bound: the minimum number of surviving
   summation variables in evaluating a spin network is governed by
   treewidth-family invariants — the same mathematics that governs
   tensor-network contraction complexity. A treewidth-derived h would
   be dramatically tighter than the girth test, would likely make
   blind-move A* tractable again (restoring provable optimality and
   mooting the move restriction), and would formally marry this
   project to the tensor-network literature. Highest value per effort
   of anything on this page: it certifies Petersen, restores
   optimality, and builds the tensor-network bridge in one stroke.
3. The synthesis: a learned ORDERING over the full move set with an
   exact-search fallback — completeness never sacrificed, only
   expedited.

## Broader roadmap (unchanged in direction)

- Cost-aware associahedron search: solver summation costs steering
  coupling-path selection in yutsis.circuits; qudit generalization;
  Qiskit emission
- General n-line separator cuts; wigxjpf fast-float backend
- Applications: SU(2)-symmetric tensor-network contraction planning;
  Schur / Clebsch-Gordan cascade circuit optimization (formula size is
  gate count)

## Suggested order of attack

1. Treewidth-derived admissible bound (closes the most, builds the
   bridge, likely certifies Petersen)
2. Merge lemma (an afternoon)
3. Learned heuristic beyond 1-WL (a real ML project; the natural
   follow-on paper)
