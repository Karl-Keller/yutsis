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

## Finding 2 — dedup collapse (CLOSED in v0.8.1)

Exact nauty certificates on the subdivided multigraph solve the
collapse outright, and nauty's pathological cases live far from our
sizes (swap to Traces or sparse nauty if n grows past a few dozen).

The residual was intellectual hygiene: states are merged by ANONYMOUS
topology, discarding j-labels, on the argument that future reduction
cost depends only on topology. The argument was correct but folklore in
a docstring.

**Closed.** It is now Lemma 3 of docs/BOUNDS.md, with its proof (every
move's guard is a topological pattern and every move's price is a
constant of its type, so `C*` is an isomorphism invariant) and its
boundary stated explicitly: it FAILS for cost models that price by
numerical magnitude, by label sharing, or by summation range — so a cost
model change is also a canonicalization change. `Graph.canonical()`
references it, and `tests/test_bounds.py` machine-checks the content by
relabelling corpus graphs and asserting both the certificate and `C*`
are unchanged.

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

   **Entry condition now satisfied (v0.8.0).** The k=1 sector is closed:
   loop excision, bridge cut and the dumbbell terminal dissolve the
   degenerate states rather than scoring around them, and
   `Graph.true_girth()` is the one function that sees 1-cycles. So the
   decomposition bound can be re-derived and re-certified against the
   completed move set.

   Note what the sector did to that bound in passing: it went from 0
   admissibility violations to **8**, because each new free move lowers
   `C*` below `(n_i-2)/2` per piece. Re-derivation must start from the
   move set as it now stands, and must be re-certified in the same
   commit as any further free move.

## Finding 4 — the k=1 sector (CLOSED in v0.8.0)

Self-loops and bridges were never edge cases: they are the `k = 1` case
of the separation calculus, where a single line crossing a cut must
carry `j = 0`. All three pieces exist, each derived and oracle-verified
before implementation (docs/K1_SECTOR.md):

- **loop excision** (v0.7.0 structural, v0.7.1 exact) — 0 mismatches
  over 2880 comparisons
- **bridge cut** (v0.8.0) — 0 over 4608; it splits the diagram, so
  states are multi-component and the goal is a property of every
  component
- **the dumbbell terminal** (v0.8.0) — 0 over 162; the bare circle is
  deliberately not a state

Three bugs surfaced on the way, two of them pre-existing and unrelated
to k=1:

- `is_goal` was `n <= 2`, accepting two tadpoles joined by a bridge and
  emitting a formula with every `j = 0` constraint dropped — silent
  incorrectness on valid input;
- `interchanges` was unguarded against self-loop legs, where the fitted
  flip phase has never been validated;
- `evaluate_expr` never enforced the 3j triad conditions, returning
  `+-1` on vanishing diagrams (186 of 729 labelings wrong on an existing
  fixture).

**The standing rule this established:** any new FREE move must be added
to `bounds.sum_bound`'s move-availability test in the same commit that
adds the move. Loop excision and bridge cut each falsified Lemma 1's
hypothesis at exactly the states they were added to handle.

## Finding 5 — the heuristic does almost nothing (new, v0.8.1)

Measured by `scripts/headroom.py`. A* must expand at least as many nodes
as the optimal plan has moves, so `expanded - moves` is the entire prize
available to a better admissible bound, and the comparison against
`h = 0` says how much of it the shipped bound already collects.

| n | moves | exp(h) | exp(h=0) | headroom | saved |
|---|---|---|---|---|---|
| 16 | 9 | 20 | 25 | 11 | 20% |
| 20 | 14 | 99 | 102 | 85 | 3% |
| 22 | 16 | 222 | 228 | 206 | 3% |
| 26 | 21 | 983 | 1004 | 962 | 2% |
| 30 | 25 | 2010 | 2040 | 1985 | 2% |

Two facts, and they point the same way:

1. **The wall is at n ~ 28**, not at benchmark scale. Everything through
   n = 18 is instant; n = 26 takes 1.3 s; one n = 28 instance blew a 25 s
   budget.
2. **Turning the heuristic off costs ~2%.** At n = 30 the search expands
   2010 nodes to find a 25-move plan, so 99% of the work is waste and
   the shipped bound removes a fiftieth of it. The `saved` column decays
   from 20% to 2% as n grows: the bound is becoming *less* useful with
   scale, exactly backwards.

**Why local bounds cannot fix this, tested not assumed.** The girth
strengthening `S >= true_girth - 3` — provable, and cheap now that
`true_girth()` exists — was implemented and measured: **0-3% expansion
cut**, indistinguishable from the shipped bound.

The reason is arithmetic. At n = 30 the optimal cost is 135, of which
summations are ~110 (`S ~ 11` at `SUM_PENALTY = 10`). Any *local*
bound — "at least one flip", "at least girth - 3" — returns at most 20.
A heuristic that estimates 20 out of 135 cannot prune.

**This is the sharpest argument yet FOR the carving/branchwidth bound**,
and it also says what such a bound must achieve to be worth building:
**an estimate of the total remaining summations that scales with n.**
Width invariants grow with the graph; girth does not. That is the whole
difference, and it is why the edge-separator redirect matters rather
than being a technicality.

Closure criterion: a bound whose `saved` column does not decay with n.

## Standing lesson from v0.6.1

The girth-5 wall was retired by nauty in v0.5.0 and nobody noticed for
two versions, because the benchmark that justified the workaround was
never re-run. **Re-run the benchmark that justified a workaround after
changing anything upstream of it.**
