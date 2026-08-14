
## Session 6 — v0.2.1: pairing fix lands in the solver

`reduce_triangle` now emits its 6j with the opposite-edge pairing proved
by the prism phase theorem: column i pairs the inside edge not touching
triangle vertex i with the leg at vertex i, built from the cap
construction directly. Guarded against doubled inside edges. Regression
test compares the solver's emitted prism factor pairing against the
theorem's column pairs exactly. Overall signs still await oriented,
slot-ordered graph states — the remaining half of milestone 2.
14 tests green.

## Session 7 — v0.3.0: oriented states, exact signs

`oriented.py`: OGraph states carry edge orientations and vertex slot
orders. reduce_triangle_exact computes its factor's sign constructively
(cap tetrahedron via tetra_to_6j, plus a (-1)^(2j) dual-pairing
correction per head-at-triangle leg); the residual vertex inherits the
legs' endpoint roles; theta_sign evaluates the final two-vertex state.
End-to-end: the oriented prism reduces by the GENERAL machinery — no
prism-specific derivation — to a phase and two 6j's matching the oracle
value-exactly (3/3, half-integers included), and agreeing with the
hand-derived theorem up to (-1)^(2(j1+j2-j3)) = +1 on triads. Milestone
2's sign engine now exists for the workhorse move. Remaining: exact
bubble and interchange factors, then wiring OGraph into the search.

## Session 8 — v0.4.0: milestone 2 complete

Exact bubble excision derived from 3j orthogonality in oracle
conventions: canonical factor (-1)^(2p+2q) delta(a,b)/(2a+1), general
case by local normalization with materialized flips. Exact interchange:
output convention fixed, 6j structure forced by the flip tetrahedron
({p e r; q x s}, opposite pairs (p,q),(e,x),(r,s)), and the phase
determined by constrained fit against wigner_9j over 22 K3,3 labelings
including half-integers: 8 survivors out of 8192 candidate laws, one
triad-equivalence class, canonical representative (-1)^(p+q+e+x) — the
textbook recoupling phase, recovered by machine. PhaseExpr gained a
constant parity bit.

Threading: structural moves now emit deterministic replayable
descriptors; solve_exact runs the structural A* for the plan and
replays it with exact operations, emitting a fully signed expression
(phase, deltas, weights, sums, 6j's) with a numeric evaluator.

Validated end-to-end: K3,3 fully signed formula equals wigner_9j to
1e-9 through the summation on integer and half-integer cases; a
dumbbell graph exercises the bubble path (delta, 1/(2j+1), sign)
against brute-force oracle evaluation, including a negative case.
Every move type now emits exact algebra. The oracle has graduated from
spot-checker to full-formula validator.

Remaining roadmap: nauty canonicalization (the 16-second cube),
cycle-targeted flips (Petersen), backends, learned guidance.

## Session 9 — v0.5.0: nauty and Petersen (Findings 1-3 retired)

Canonicalization now runs through nauty (pynauty), with the multigraph
subdivided into a two-color simple graph for exact certificates;
individualization-refinement is precisely 1-WL plus symmetry breaking
plus automorphism pruning — the cure Finding 1 prescribed. The 8!
brute force survives only as an import-failure fallback. The cube's
16-second canonicalization bill dropped to milliseconds.

Interchanges are now cycle-targeted (the girth strategy): one shortest
cycle is found by per-edge BFS, and only flips that contract it by one
are generated, cutting branching from ~4|E| to ~4L. Petersen — the
girth-5 wall that defeated both A* and weighted greedy under blind
flips — solves in 11 expansions / 0.01 s: 7 sixj, 3 sums (optimal
within the targeted move class; girth re-inflation during triangle
cascades explains the third sum).

Exact finale: solve_exact reduced the oriented Petersen to a fully
signed 15j formula (3 nested sums, 7 6j's, 13-term phase), verified
against brute-force oracle evaluation on a nonzero labeling —
+0.004629630 on both sides, a 995,328-term magnetic sum matched to
1e-9. One bug found en route: merged-vertex id schemes diverged between
structural and oriented layers ("W_a" vs "Wa"), invisible until a plan
referenced a merged vertex in a later move; fixed and exercised.

The correctness story and the performance story are now both closed at
benchmark scale. Remaining roadmap: general n-line separator cuts,
wigxjpf backend, learned move ordering (the GYutsis counter-example
says girth-first is not always optimal — a learned policy over
targeted candidates is the natural next experiment), and the quantum
Schur / CG-cascade application.

## Session 10 — v0.6.0: yutsis.circuits — the quantum payload

Coupling trees to verified recoupling gates, using the full system.
recoupling_graph glues any two binary coupling trees at leaves and root
into a closed OGraph; solve_exact reduces it; dimension factors
(sqrt(2j+1) per internal coupling of each tree) convert diagram values
to physical matrix elements. A SECOND oracle arrived: coupled states
built explicitly from sympy Clebsch-Gordan coefficients and overlapped
by brute force -- ground truth at the physical-state level,
independent of the diagram algebra.

The glue conventions differ from CG normalization by tree-shape-
dependent (-1)^(2j) parities; calibrate() pins them by GF(2) fit over
generated-valid labelings (valid by construction: couple up the tree),
then held-out cases verify: 20/20 value-exact across three tree pairs,
including a distance-2 pair reducing to two 6j's sum-free.

The compiler: flip_path BFS on the associahedron finds the shortest
elementary-recoupling sequence; gate_matrix builds each flip's unitary
block from calibrated matrix elements. For four spin-1/2 at J=1:
two-flip path, each 3x3 gate unitary to 3e-16, composition equal to
the direct transform to 2e-16. The Schur-transform gate family,
compiled and machine-verified three independent ways (state oracle,
unitarity, composition).

The 1983 search problem's modern payload exists: an optimizing,
self-calibrating, oracle-verified compiler from angular momentum
algebra toward quantum circuits. Next: larger trees and higher spins,
qudit generalization, Qiskit emission, and cost-aware path selection
(the solver's summation costs steering the associahedron search).

## Session 11 — v0.6.1 (2026-08-14): the guarantee was void

**What was built.** `yutsis.bounds`, carrying a corrected admissible
heuristic; `search.optimal_cost` and `solve(blind=True)`, the
ground-truth searchers; `tests/test_bounds.py` and
`scripts/certify_bounds.py`. Derivation, proof status and boundaries in
`docs/BOUNDS.md`.

**What broke — and it was already broken.** Reading `CLAUDE.md`'s iron
rule against the incumbent turned up a counterexample to the shipped
heuristic's admissibility. `search.heuristic` used `(n-2)/2` as its 6j
term. Lemma 0 makes the error exact: every reduction uses exactly
`(n-2)/2` vertex-removing moves, but bubble excisions are among them and
emit **zero** 6j, so

    #6j = (n-2)/2 - B + S

and the shipped bound silently assumed `B = 0`. It is an *over*-estimate
wherever a bubble is reachable, so A* was not guaranteed optimal — the
project's central claim, void in principle. Measured scale: **58 of 80**
reachable states with a computable optimum (72.5%). Not an exotic
corner.

Two counterexamples, now pinned as named regression tests:

- `BUBBLE_COUNTEREXAMPLE` (n=4 multigraph): excising its bubble lands
  directly on theta. `C* = 0`, `h_old = 1`.
- `TWO_DIAMOND_COUNTEREXAMPLE` (n=8, **simple** and bubble-free): two
  K4-minus-an-edge blocks joined by a 2-cut. Contracting a diamond's
  triangle *births* a parallel pair; excising it drops `n` by 4 for one
  6j. `C* = 2`, `h_old = 3`.

The second killed the first fix attempt. Discounting by the bubbles
*currently present* is wrong twice over: bubbles are created
mid-reduction, and bubble-free simple states over-estimate too. Scoping
admissibility to bubble-free states would have shipped a still-broken
guarantee.

Why no test caught it: `random_cubic` rejects parallel edges, so no
generated case could reach a bubble-bearing state, and every benchmark
optimum happens to use `B = 0` — which is why `#6j = (n-2)/2 + S`
reproduces all five published costs. The identity that made the
benchmarks look right was the identity hiding the bug.

**PETERSEN IS CERTIFIED: the minimum is three summations, not two.**
`C*(Petersen) = 37` by uniform-cost search (`h = 0`) over the *blind*
move set. By Lemma 0, `cost = 4 - B + 11*S`, so any `S = 2` reduction
costs at most 26. It costs 37. The shipped 7-6j / 3-sum formula is
optimal over the FULL move set, not merely the cycle-targeted class.
Confirmed three ways: uniform-cost 37, blind-move A* 37 (18
expansions), targeted A* 37 (11 expansions). Finding 3 prong 1, closed.

The premise of the girth-5 wall was **stale**. "Petersen defeats both A*
and weighted greedy under blind flips" was measured in v0.4.0, *before*
nauty landed in v0.5.0. The search dedups on anonymous topology, so
nauty collapsed the blind state space — blind-move A* now finishes in 18
expansions and 0.0 s. The move restriction was never load-bearing for
this benchmark, and nobody re-measured after the change that fixed it.

**What it taught.** Three things, and the last one changed the ship
decision.

*Under-splitting is unsafe; over-splitting is merely weak.* The first
decomposition skipped 2-cuts whose stubs landed on a common vertex,
silently under-decomposing and leaving 10 violations. Recognising that
the safe direction is asymmetric turned a subtle bug into a one-line
policy.

*Certify the induction step, not the outcome.* Sampling `h <= C*` only
covers states with a computable optimum. Certifying the potential-
function step `Phi(G) <= Phi(G') + d6` over every move covers everything
reachable — and it is what exposed the failure below. A narrower corpus
had reported this clean; widening it to n=10/12 seeds did not.

*A bound that cannot change a decision is not worth an unproven claim.*
The 2-cut decomposition bound is derived, elegant, exact on both
counterexamples, and empirically admissible (0 violations over 80
states, tight on 54). But its proof fails: **310 of 42,611 moves**
violate the step inequality, all at states carrying a self-loop or
bridge, where a move can *relocate* the degeneracy between pieces and
collapse `Phi` by 2 for one 6j (observed: `[6 clean, 2 degenerate]` ->
`[2 clean, 6 degenerate]`). Two repairs were rejected **by machine, not
by argument** — discounting self-loop vertices is *directly
inadmissible* (6 violations; it was the intuitively appealing fix), and
a whole-graph degeneracy gate still leaves 96 step violations.

Then the measurement that settled it: replacing the decomposition term
with **0** produces identical costs *and* identical expanded-node counts
on every benchmark and on random cubic graphs out to n=14. The term
never changed a single search decision. So the shipped `heuristic` is
the proven part only — `h = 0 + h_sum` — and the decomposition is
retained as an opt-in module (`sixj_bound_decomposition`) with its
certification status stated in its own docstring. Shipping the stronger
bound would have repeated v0.6.0's exact mistake: an empirically
validated, unproven bound that passes every test it has.

**Verification.**

- Re-certification: benchmark costs recomputed by uniform-cost search
  (`h = 0`, blind moves): tetrahedron 1, prism 2, K3,3 13, cube 14,
  Petersen 37 — all equal to the v0.6.0 published costs. **The
  guarantee was void; the results were correct.**
- Shipped `h`: 0 admissibility violations over 80 states, 0 step
  violations over 42,611 moves.
- Opt-in decomposition: 0 admissibility violations; 310 step violations,
  **0 of them at clean states**, which is the documented boundary.
- 42 tests green (23 existing + 19 new), 2.0 s.

**Stress, before/after** (`scripts/stress.py --budget 30 --max-n 12`):
expanded-node counts and costs **identical** on every case —
tetrahedron 1, prism 2, K3,3 3, cube 4, Petersen 11 (A*) / 7 (greedy),
random n=8/10/12 at 4/4/7.

**Not addressed here.** The summation term is untouched and still weak
(`S >= 1` whenever girth `>= 4`), so Petersen is bounded at `S >= 1`
against a now-certified `S = 3` — the gap Finding 3 prong 2 must close,
with the redirect to edge-separator invariants (carving/branchwidth)
recorded in `NEXT_STEPS.md`. Ruff is deferred to that branch to keep
this hotfix reviewable.

**Review addendum (same day).** Three review items settled before merge.
Lemma 1 gained its explicit proof in `docs/BOUNDS.md`, and writing it
out corrected a premise: self-loop states do NOT report low girth and
skip the bonus — `girth_lower()` returns 4 for a tadpole (a `(u,u)`
edge is not a `bubbles()` pair), so they DO receive it, correctly,
because their only successors are flips. The proof turns out not to use
girth at all: `girth_lower()` computes no cycle length, it is a
move-availability predicate wearing a girth costume, and that is the
whole basis of the bound.

Which exposes a trap for the branch that follows: **`girth_lower()` is
not a valid lower bound on girth** — it returns 4 on states whose true
girth is 1. Any carving/branchwidth bound wanting a real girth must
call `girth_cycle()`. Recorded as an entry condition in NEXT_STEPS.md
and pinned by `test_girth_lower_is_not_a_girth_bound_on_self_loop_states`.

`CITATION.cff` had drifted to 0.6.0. Bumped, and the three-way version
agreement (pyproject / `__init__` / CITATION) is now enforced by
`tests/test_metadata.py` instead of by memory — a bumped version that
turns CI red is the ritual working. 48 tests green.

## Session 12 — v0.7.0 (2026-08-14): the k=1 sector, half of it

**What was built.** Loop excision — the first `k = 1` move — plus the
oracle support, the goal-test fix, `true_girth()`, and the flip guard it
forced. Derivation in `docs/K1_SECTOR.md`. Bridge cut is deferred: it
splits the diagram in two, which the single-graph state model cannot
represent (see "Not yet handled").

**The prerequisite nobody had noticed.** The oracle could *represent* a
self-loop — the edge occupies two slots of one vertex, so the `uses==2`
guard passes — but could not *evaluate* one. `value()` assigns `+m` at
the tail and `-m` at the head by comparing vertex ids, and for a loop
tail == head, so both slots scored `+m`. The dumbbell returned `0.0`
against an analytic `2`. Ground truth cannot certify moves for a sector
it cannot express, so this had to land first. Fixed by slot order —
first occurrence is the tail, second the head — which leaves every
non-loop diagram bit-for-bit identical.

**The physics.** A closed diagram is a rotational scalar, so a single
line crossing a separation carries `j = 0`. Two lemmas, both verified
against the oracle before any move code was written:

    K1a  sum_m (-1)^(k-m) 3j(k k c; m -m mc) = sqrt(2k+1) d(c,0) d(mc,0)
    K1b  3j(a b 0; ma mb 0) = d(a,b) d(ma,-mb) (-1)^(a-ma)/sqrt(2a+1)

K1a on six `(k,f)` pairs including half-integers, sign included, plus
the vanishing case at `c != 0`. K1b by a tetrahedron with one edge at
`j = 0`, which caps at both ends and collapses to a theta at ratio
exactly `1/sqrt((2j1+1)(2j4+1))` — one `1/sqrt(2j+1)` per cap. They are
fused into one move because K1a alone leaves `c` dangling, and the graph
must stay closed and cubic between moves.

**What it fixed.** `theta-with-handle` used to reduce to the dumbbell,
which the old `is_goal` (`n <= 2`) accepted — terminating at cost 0 with
two deltas and every `j = 0` constraint dropped. Silent incorrectness on
valid input. It now reduces `bubble -> loop` to a true theta and emits
`loopw(c)*delta(e,0)*delta(f,g)/sqrt(2*f+1)`, with the forcing present
in the formula. `is_goal` is now `is_theta()` — two vertices, three
parallel edges, no loop.

**What it broke, found by machine.** Making loop states reachable and no
longer silently accepted exposed that `interchanges` was unguarded
against degenerate patterns. The flip phase was fitted against
`wigner_9j` on a GENERIC patch (v0.4.0) — `e=(u,v)`, `P` a neighbour of
`u`, `Q` of `v`, all distinct — and a self-loop makes `P == u`.
Unguarded, the dumbbell (an irreducible terminal) "reduced" at cost 11
through algebra never validated there. Both flip generators now skip
loop legs, and the dumbbell is an honest dead end.

**The coupling, and the vindication.** Loop excision is a FREE move, so
Lemma 1's "no bubble or triangle => every move is a flip => S >= 1"
became false at tadpole states. `sum_bound` now tests
`excisable_loops()`, in the same commit — without it `h` would have been
inadmissible at exactly the states the move was added to handle.

The sharper result is what happened to the **opt-in decomposition
bound**. It had 0 admissibility violations in v0.6.1. After one new free
move it has **7**, every one at a state with an excisable loop: free
vertex removal drops `C*` below `(n_i-2)/2` per piece. It was
empirically admissible against every state ever tested, and the very
next release broke it outright. **A bound verified against a move set is
only valid for that move set** — which is precisely why v0.6.1 shipped
the proven bound instead. Documented as unusable rather than quietly
patched; it can be re-derived once bridge cut dissolves the degenerate
states.

**What it taught.** Extend the oracle before the move set. The instinct
was to write loop excision and validate it afterwards; the oracle would
have returned `0.0` and the "validation" would have been meaningless
agreement between two broken things.

**Verification.**

- Shipped `h`: **0** admissibility violations over 75 states with a
  computable `C*`; **0** step violations over 42,052 moves.
  `scripts/certify_bounds.py` reports CERTIFIED (shipped heuristic).
- Benchmarks re-certified against `h = 0` blind uniform-cost:
  tetrahedron 1, prism 2, K3,3 13, cube 14, Petersen 37 — unchanged.
- 58 tests green, 1 xfail (the exact layer, below).

**Stress, before/after** (`--budget 30 --max-n 12`): all costs
identical, A* expansions identical (1/2/3/4/11, random 4/4/7). One
change: `petersen greedy` 7 -> 11 expansions at the same cost 37 — the
stricter goal test makes weighted greedy walk to a true theta. Greedy
carries no optimality guarantee, and A* is untouched.

**Not addressed here.** Bridge cut and the dumbbell terminal both need
the multi-component / empty-diagram state model (`is_goal` over
components, Lemma 0 at `(n-2C)/2`, per-component bounds) — next PR. The
exact layer has no oriented loop excision yet, so `solve_exact` still
meets a non-theta and raises; pinned as a strict xfail rather than
described.

## Session 13 — v0.7.1 (2026-08-14): the k=1 exact layer

**What was built.** `excise_loop_exact`: loop excision with exact signs,
completing the move started in v0.7.0. The expression grew `zeros`
(labels forced to `j = 0`) and `sqrt_num` / `sqrt_den`.

**The phase was measured, not guessed.** The canonical tadpole — `v`
slots `(k,k,c)` with the loop's tail first and `c: v->w`, `w` slots
`(c,a,b)` with `a`,`b` tailed at `w` — excises with factor
`sqrt(2k+1)/sqrt(2a+1) * d(c,0) * d(a,b)` and phase **exactly +1**: the
ratio `before/(factor*after)` came back `+1.0` on every labeling of the
canonical family, so there was no residual sign to fit. The general case
normalizes by slot permutations and orientation flips exactly as
`excise_bubble_exact` does. The loop needs no special orientation
handling — the oracle fixes its tail/head by slot order, so any
reordering preserving the relative order of the two `k` slots preserves
the orientation.

Verified across **all 576 slot-permutation x orientation configurations,
2880 comparisons, 0 mismatches**. End-to-end on `theta-with-handle`,
`solve_exact` matches brute-force magnetic summation on **256 labelings
(49 nonzero), 0 mismatches**, and vanishes identically at `j_e != 0`.

**What it exposed — a pre-existing evaluator bug, not a k=1 one.** Every
emitted identity (3j orthogonality for the bubble, Racah for the
triangle, K1a/K1b for the loop) is derived **assuming the source
vertex's triad exists**, and the final theta is folded into `theta_sign`
as a `+-1` phase presuming the same. Where a triad fails the diagram is
zero but the emitted factors are not, so `evaluate_expr` reported `+-1`
on vanishing diagrams.

Measured on the **existing bubble fixture, no k=1 move involved: 186 of
729 labelings wrong.** The shipped tests happened to sit on valid
labelings, which is exactly how it survived four releases. `replay` now
records the input triads and the final theta's labels; `evaluate_expr`
enforces the 3j conditions — integral triad sum and triangle inequality
— with the theta check *inside* the summation, since its labels can be
summation variables. Same sweep: **0 of 729**.

**What it taught.** A formula that agrees with the oracle on the
labelings you chose is not a formula that agrees with the oracle. The
bug had been reachable since v0.4.0 and was found only because a new
move produced a labeling family that sat on the boundary. Sweeping a
grid costs seconds; the existing tests each checked three points.

**Verification.**

- 74 tests green (up from 58 + 1 xfail; the strict xfail flipped and was
  replaced by real oracle-validated tests).
- `scripts/certify_bounds.py`: CERTIFIED (shipped heuristic) — the
  structural search is untouched.
- Stress: costs and A* expansions identical on every case.
- `scripts/verify_petersen.py`: still `+0.004629630 == +0.004629630`,
  so the triad enforcement does not disturb the flagship result.

**Not addressed here.** Bridge cut and the dumbbell terminal, both
needing the multi-component / empty-diagram state model — next.
