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
2. Build the RIGHT admissible bound. The summation term became the
   REDUCIBILITY test in v0.10.0 -- stronger than the v0.6.0 girth test
   it replaced -- but it still resolves only `S >= 1`, whether the truth
   is one flip or five, so it bounds Petersen at `S >= 1` against a
   certified `S = 3`. The motivation is scaling rather than Petersen:
   larger graphs where blind-move A* does *not* collapse. The
   edge-separator redirect recorded here was itself refuted in v0.9.0;
   see Lemma 4. Empirically, a plain
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

1. **Climb the flip-count ladder.** Rung one shipped in v0.10.0.

   The diagnostic that chose this family: over n = 16..30 the plateau
   share (`f = C*`) is **0%** -- all search waste is mandatory given
   `h`, so no tie-breaking or learned ordering can remove a node, and
   only a stronger admissible bound can (`scripts/plateau_probe.py`).

   **Rung one, shipped**: `S >= 1` iff not `flip_free_reducible(G)`,
   i.e. G cannot reach a terminal using only free and triangle moves.
   Admissible by definition, subsumes the old move-availability test by
   construction, fires on 223 of 910 corpus states against 35. `saved`
   went 20/3/3/2/2% to 36/14/9/8/7% at n = 16..26 -- roughly triple,
   and still decaying, so the criterion is NOT met.

   **Rung two, REFUTED (v0.10.1)**: `S >= 2` iff no reduction uses
   exactly one flip -- correctly stated, that quantifies over every
   state reachable without a flip, not just `g`'s flip children. Both
   the correct form and a cheap sound restriction are admissible and cut
   real nodes (12-35% and 4-19%), and both LOSE in wall clock, by
   10x-23x and 1.3x-6x. Evaluating the bound costs more than the search
   it saves. See Lemma 6 -- an admissible bound can be strictly better
   as a bound and strictly worse as an algorithm, and only wall clock
   shows it.

   If the ladder buys a constant factor and never an asymptotic one,
   that is Lemma 6 and gets written up as one.

   **Pattern database, SHIPPED opt-in (v0.11.0)**, and the brief's cut
   was too low. The hit-rate ceiling is set by the distribution of
   expansions over n: a table to `n <= 12` caps at 2-3% at n = 26-30,
   below rung one. The waste is at n = 16, 18, 20 -- the MIDDLE of the
   reduction, not the endgame -- so the cut moved to 16, where the
   table covers 43% of expansions at n = 26 and 30% at n = 30.

   47,284 entries for `n <= 16` in ~9 minutes, built level-wise
   (Dijkstra per level: flips within, exits to the level below), every
   sampled entry verified against uniform-cost search. Payoff, the
   first candidate to win on BOTH metrics:

       n        20     22     24     26     30
       nodes   -64%   -74%   -45%   -37%   -27%
       clock   -71%   -71%   -40%   -34%   -21%
       hits     94%    54%    48%    24%    14%

   Still decays with hit rate, so the closure criterion is NOT met. Not
   wired into the default heuristic -- it is a build artifact, and the
   engine must work without it (`yutsis.patterns`,
   `scripts/build_patterns.py`).

   **Pushed to `n <= 18` (v0.12.0), and it decays anyway.** 470,975
   entries, closed, 166.8 MB, 2h 12m on one core. Over sizes 20..36,
   five seeds each, as mean-of-ratios / ratio-of-means:

       n            20    22    24    26    28    30    32    34    36
       n<=18 m-o-r -43%  -51%  -51%  -77%  -50%  -63%  -44%  -14%  -21%
       n<=18 r-o-m -49%  -72%  -67%  -78%  -34%  -34%  -15%   -5%   -8%
       n<=16 m-o-r -41%  -38%  -43%  -32%  -18%  -28%  -10%   -4%   -5%
       hit rate     97%   79%   83%   52%   26%   36%   15%    4%    7%

   Two to four times the shipped table through n = 32, single digits by
   n = 34 on both aggregates. The cut buys about FOUR IN N -- the n<=16
   table is spent by n = 30, this one by n = 34 -- at 10x the entries
   and 14x the build. `saved` still tracks the hit rate down, so the
   closure criterion is still NOT met, for the fourth candidate running.

   Load is 0.10s and 211 MB resident, and wall clock tracks nodes at
   every size including a 3% hit rate returning -19% seconds, so there
   is no Lemma 6 reversal: the cost is the build and the storage, not
   the lookup.

   **Two measurement rules, both learned by getting it wrong here.**
   SINGLE-SEED EVIDENCE IS NOT EVIDENCE: five sizes at `seed = 7n` read
   -64/-85/-70/-81/-75, a flat `saved` column and an apparent closure,
   which four more seeds per size dissolved -- at n = 30 that seed is an
   easy instance, 1,921 expansions against a 7,202 mean, and the
   per-instance spread at n = 32 runs -92% to -7%. And THE AGGREGATE IS
   PART OF THE CLAIM: a ratio of means weights the hardest instance of
   a size almost exclusively and read -8% where instances read -41% and
   -15%. Report both, and exclude sizes where the expansion cap lets
   only easy instances finish -- a mean over survivors is a selection
   effect (this is why nothing above n = 36 is quoted).

   **A seeding hypothesis, raised and refuted in the same session.**
   The n<=16 closure seeded to 16 holds 47,284 states against 130,559
   in the same range inside the n<=18 closure, which looked like it
   should explain the decay. Instrumenting coverage beside hits shows
   them EQUAL in every row: every n <= 16 state a search actually meets
   is already in the shipped table. The n<=18 table restricted to a
   cutoff of 16 reproduces the shipped expansions exactly, row for row.

   **Landmarks: refuted (v0.11.2, Lemma 8).** The one family that
   scaled by construction -- `k ~ n/13`, ratio to `S` constant -- clean
   on 44 roots and refuted on the interior, 5 violations in 700
   mid-search states. A bubble excision elsewhere contracts the graph
   and pulls structure into the certified-empty ball. Not repairable by
   widening the radius: contraction changes distances.

   **THE RULE, and it should gate every future proposal.** Only
   REACHABILITY-based bounds survive. Static properties -- width, 6j
   decomposition, landmarks -- are all refuted or inert, because the
   moves are free to change the structure they read. Reducibility, the
   flip ladder and the pattern database are all reachability
   properties, and all work subject only to evaluation cost. **If a
   proposal can be evaluated without following moves, it is already
   suspect.**

   The price is Lemma 6: reachability is expensive. So the live design
   problem is a CHEAP reachability bound -- which is what the pattern
   database is, paying the cost once, offline.

   **What is left.** Six sessions of candidates have improved the
   constant and left the asymptote alone. Every one of them was
   admissible, most were measured, and none moved the decay. The
   remaining moves are to accept a constant-factor engine and say so, or
   to attack discrimination at the SUM_PENALTY granularity that Lemma 5
   says is the only granularity that changes a decision.

   **GPU (RTX 5070, sm_120): the offline build, not the search, and
   third in line.** Profiled on the n<=14 enumeration, `canonical()` is
   47% of the walk -- so an infinitely fast canonicaliser is a 1.9x
   ceiling on that phase, before a line of CUDA. More than half of that
   47% is not graph theory but pynauty marshalling (`set_adjacency_dict`
   plus 24.4M `_check_vertices` calls); nauty's own C kernel is 22%.
   And the walk makes 84 `canonical()` calls per distinct state, since
   every successor is a fresh object. So: kill the redundancy, then use
   the 24 idle cores the build never touches, then bypass the
   marshalling -- and only then consider a GPU.

   A GPU would suit the shape of the remaining work (millions of
   independent 18-vertex graphs, an adjacency bitmatrix in registers,
   VRAM a non-issue at ~31 MB packed), but it needs a FIXED-COST
   canonical form, because refinement-with-backtracking is exactly the
   divergence GPUs punish. A* itself is a poor target regardless --
   sequential, queue-driven, and its `h` is already a dict lookup.

   The gate is the result above, and it has fallen: since `saved` still
   tracks the hit rate, a faster builder buys `n = 20` and a few more
   sizes of CONSTANT, not the asymptote. Fund it as engineering
   throughput if the constant is worth it, not as a route to closure.

2. **Closed off, recorded so nobody re-derives them**: width invariants
   (Lemma 4), the k=1-extended decomposition split (Lemma 5), and
   magnitude-only bounds (Lemma 4). Each has a counterexample or a
   measurement in docs/BOUNDS.md.

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

**Resolved in v0.8.4, and not the way this predicted.** The inference
"therefore build a bound that scales with n" was wrong, because a
scaling term is not what a heuristic needs. See Lemma 4 and "What the
search actually lacks" in docs/BOUNDS.md, and `scripts/width_probe.py`
for the evidence:

- `S >= cw - 3` is FALSE -- refuted by tetrahedron, prism and a random
  n=10 graph. The 6j identity collapses a 4-line cut for free, so the
  rewrite calculus beats generic contraction and any width invariant
  over-charges.
- Carving width does not separate the cases (cw = 4 for tetrahedron,
  prism, K3,3 and cube, whose S are 0, 0, 1, 1) and does not scale
  (cw goes 4 -> 5 while n goes 8 -> 14 and S goes 1 -> 3).
- Adding `(n-2)/2` -- a correct term growing linearly in n -- to the
  shipped heuristic changes expanded-node counts by ZERO at every size.
  A term that is a function of depth shifts every frontier state
  equally and discriminates between none.

What the search lacks is DISCRIMINATION. Over all 97 states at n = 8
with a computable optimum, true `C*` takes six distinct values and the
shipped bound takes two -- it returns 0 for 93 states whose true costs
are 0, 1, 2 and 3. The variation it misses is in the 6j count, not the
summation count.

Closure criterion, unchanged in spirit and now correctly aimed: a bound
whose `saved` column does not decay with n -- achieved by telling
same-depth states apart, not by being larger.

## Standing lesson from v0.6.1

The girth-5 wall was retired by nauty in v0.5.0 and nobody noticed for
two versions, because the benchmark that justified the workaround was
never re-run. **Re-run the benchmark that justified a workaround after
changing anything upstream of it.**
