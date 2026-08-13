
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
