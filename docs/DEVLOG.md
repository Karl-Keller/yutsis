
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
