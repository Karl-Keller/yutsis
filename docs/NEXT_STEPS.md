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

## Finding 3 — girth-5 wall (prong 1 CLOSED in v0.6.1)

**Petersen is certified: the minimum is three summations, not two.**

Uniform-cost search (`h = 0`) over the *blind* move set gives
`C*(Petersen) = 37`. Since `cost = (n-2)/2 - B + 11*S` (Lemma 0,
docs/BOUNDS.md), any two-summation reduction would cost at most `26`.
It costs `37`, so `S = 2` is impossible and the shipped `7` 6j / `3`
sums formula is optimal — over the FULL move set, not merely the
cycle-targeted class. Confirmed three ways: uniform-cost (37), blind-move
A* (37, 7 sixj, 3 sums, 18 expansions), shipped targeted A* (37, 11
expansions).

The premise of the wall was stale. "Petersen defeats both A* and
weighted greedy under blind flips" was measured in v0.4.0, *before*
nauty canonicalization landed in v0.5.0. Because the search dedups on
anonymous topology, nauty collapsed the blind state space: blind-move
A* now solves Petersen in 18 expansions and 0.0 s. The move restriction
was never load-bearing for this benchmark, and nobody re-measured after
the thing that fixed it. **Re-run the benchmark that justified a
workaround after changing anything upstream of it.**

What remains:

1. ~~Certify or refute Petersen~~ — done, see above.
2. Build the RIGHT admissible bound. The summation term is still the
   v0.6.0 girth test: it returns `S >= 1` whether the truth is one flip
   or five, so it bounds Petersen at `S >= 1` against a certified
   `S = 3`. The motivation is now scaling rather than Petersen — larger
   graphs where blind-move A* does *not* collapse. Note the redirect:
   for cubic graphs the natural invariants are **edge**-separator ones
   (carving width, branchwidth), not vertex treewidth, because the
   `(k-3)` calculus lives natively on edge cuts. Empirically, a plain
   treewidth bound is also *weaker* than the girth test here: prism and
   K3,3 both have treewidth 3 but `S = 0` and `S = 1` respectively, so
   treewidth alone cannot separate them.
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

1. Edge-separator (carving/branchwidth) summation bound. Petersen no
   longer motivates it — that is certified — so the target is now
   scaling: sizes where blind-move A* does not collapse. Must be a
   LOWER bound on the width invariant; upper-bound estimators
   (min-fill, min-degree), which the tensor-network literature reaches
   for first, are unsafe here.

   Entry conditions are in "The k=1 sector" below — that work comes
   first, and may dissolve this bound's degenerate-state problem
   outright.

## The k=1 sector (do this before the width bound)

Self-loops and bridges are not edge cases to be scored around. They are
the **k = 1 sector of the separation calculus**, and the principled fix
is physics, not special-casing.

The k-line anchor already covers `k = 2` (free, δ) and `k = 3` (free, 6j
factorization). The engine has never needed `k = 1`, but it is equally
exact: a closed diagram is a rotational scalar, so any single line
crossing a separation must carry `j = 0`. A **bridge** therefore forces
`δ(j,0)` and factorizes the diagram into two independent closed pieces;
a **self-loop** is the same statement one step tighter — closing two
legs of a vertex forces its third edge to zero, emitting a
`sqrt(2j+1)`-type weight and a phase.

So the likely resolution of "handle degenerate states properly" is **two
new moves — loop excision and bridge cut** — derived and oracle-validated
like every move before them, phases included, which remove these states
from the frontier rather than teaching the bound to score them. If they
land properly the decomposition module needs no degenerate carve-out at
all: the proof that failed on 310 moves may have no failing states left
to fail on.

### Opening move: the theta-with-handle completeness test

The engine is incomplete here *today*, on physically legitimate input.
Verified on the closed diagram

    (1,2)x2  (1,3) (2,3)  (3,4)  (4,5) (4,6)  (5,6)x2

— two bubbles whose external legs each land on a common vertex, no
self-loop and no bridge-free obstruction at the start:

- **`solve()` silently returns a wrong formula.** Excising both bubbles
  merges each pair of externals into a self-loop, landing on the
  dumbbell `(3,3) (3,4) (4,4)` — two tadpoles joined by a bridge. Since
  `is_goal` is just `n <= 2`, this is accepted as the goal: cost 0, two
  δ factors, and **every k=1 constraint dropped**. The `j = 0` forcing
  and the loop weights are never emitted.
- **`solve_exact()` crashes**: `ValueError: tuple.index(x): x not in
  tuple`, from `theta_sign`, whose guard `assert og.n == 2 and
  len(og.edges) == 3` passes on this non-theta (two loops plus a
  bridge is also 2 vertices and 3 edges).

Note what was *not* found, so the branch does not chase it: there is no
dead end. A sweep of 786 reachable states found **0** states with `n > 2`
and no applicable move — flips always fire, and `solve()` never returns
`None`. The bug is at the goal test and the exact evaluator, not the
frontier.

First regression tests: the theta-with-handle family reduces correctly
and value-exactly against the oracle, and `is_goal` accepts only a true
theta (2 vertices, 3 parallel edges, no self-loop).

### Coupling: these must ship in ONE PR

The moment loop/bridge excision land as **free** moves, the currently
shipped summation bound becomes inadmissible at exactly these states.
Its proof (docs/BOUNDS.md, Lemma 1) is "no bubble or triangle ⇒ every
move is a flip ⇒ `S >= 1`", and the new free moves falsify the middle
step. So the k=1 moves, the girth fix, and a re-run of the admissibility
corpus must land together, or main briefly carries a repeat of the
v0.6.0 mistake.

### One true girth, not three opinions

`girth_lower()` lies on tadpoles (returns 2/3/4 by bubble/triangle
presence, never a cycle length), and the blindness goes one layer
deeper: **`girth_cycle()` explicitly skips self-loop edges too**
(`graph.py`, `if u0 == v0: continue`) — verified, it returns a 2-cycle
on a graph whose true girth is 1.

Fix once, centrally: a single `true_girth()` — 1 if any self-loop, 2 if
any parallel pair, else the BFS cycle — used by the heuristic, the
stress display, and targeted-move selection alike, rather than three
functions with three opinions about what a cycle is.
2. Merge lemma (an afternoon)
3. Learned heuristic beyond 1-WL (a real ML project; the natural
   follow-on paper)

## Standing lesson from v0.6.1

The girth-5 wall was retired by nauty in v0.5.0 and nobody noticed for
two versions, because the benchmark that justified the workaround was
never re-run. **Re-run the benchmark that justified a workaround after
changing anything upstream of it.**
