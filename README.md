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
    pytest -q                      # 94 tests: oracles, theorems, bounds, k=1, compiler
    python -m yutsis               # benchmark reductions

## Showcase: the Petersen graph (a 15j symbol)

The Petersen graph — girth 5, no local bubble or triangle anywhere — is
the classic hard case for recoupling reduction. The solver reduces it
in 11 node expansions (~0.01 s) to a fully signed formula: **three
nested summations, seven 6j symbols**, and a thirteen-term phase — and
as of v0.6.1 those three summations are **certified minimal** over the
unrestricted move set, not merely cheapest among the moves searched.

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

## Verified results (v0.10.1)

- **The k=1 sector, half closed** (`yutsis.moves.excise_loop`,
  [docs/K1_SECTOR.md](docs/K1_SECTOR.md)): a closed diagram is a
  rotational scalar, so a line crossing a 1-cut carries `j = 0`. Loop
  excision fuses two lemmas verified against the oracle *before* any
  move code — the tadpole weight `sqrt(2k+1)·δ(j_c,0)` on six labelings
  including half-integers, and the cap rule at ratio exactly
  `1/sqrt((2j₁+1)(2j₄+1))`. Fixing this required teaching the oracle the
  sector first: it scored both self-loop slots as tails and returned
  `0.0` where the analytic answer was `2`
- **Admissibility, repaired and certified** (`yutsis.bounds`,
  [docs/BOUNDS.md](docs/BOUNDS.md)): the v0.6.0 heuristic was
  inadmissible — its `(n-2)/2` 6j term assumed no bubble excision ever
  occurs, over-estimating on **58 of 80** reachable states with a
  computable optimum, which voided the A* optimality guarantee. Fixed,
  with both counterexamples pinned as regression tests. The published
  benchmark costs were **re-certified**, not caveated: recomputed by
  uniform-cost search (`h = 0`, blind moves) they are unchanged —
  tetrahedron 1, prism 2, K3,3 13, cube 14, Petersen 37
- **Petersen's minimum is three summations** — certified over the full
  move set, not merely the cycle-targeted class (see Findings below)
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

## Assessed Findings and Next Steps

The project's three original findings are retired at benchmark scale,
not resolved in principle — each carries a residual worth naming (full
analysis in [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md)):

1. **1-WL blindness** (two-thirds closed). Canonicalization is cured in
   principle by nauty's individualization-refinement. The open half:
   learned heuristics need expressivity beyond message passing, since
   plain GNNs are provably 1-WL-bounded and hence blind to the
   twisted-vs-untwisted distinction the cost model turns on. K3,3 vs
   the prism is the ready-made benchmark; closure is a learned value
   function that beats the hand-built one on held-out graphs.
2. **Dedup collapse** (closed in v0.8.1). Exact certificates on the
   subdivided multigraph solve it, and the label-discarding merge
   argument is now Lemma 3 of [docs/BOUNDS.md](docs/BOUNDS.md) — proved,
   machine-checked by relabelling, and with its boundary explicit: it
   fails for cost models pricing by magnitude, label sharing, or
   summation range, so a cost-model change is also a canonicalization
   change.
3. **Girth-5 wall** (Petersen closed in v0.6.1; the bound still open).
   **Petersen's minimum is three summations, certified**: uniform-cost
   search with `h = 0` over the *unrestricted* move set gives
   `C* = 37`, and since `cost = (n-2)/2 - B + 11S`, any two-summation
   reduction would cost at most 26. The wall's premise was also stale —
   "Petersen defeats blind flips" predates nauty, which collapsed the
   blind state space; blind-move A* now finishes in 18 expansions. What
   remains is the *bound*: the summation term still returns `S >= 1`
   whether the truth is one flip or five. The redirect that matters —
   for cubic graphs the live invariants are **edge**-separator ones
   (carving width, branchwidth), not vertex treewidth, since the
   `(k-3)` calculus lives on edge cuts.
4. **The k=1 sector** (closed in v0.8.0). Self-loops and bridges are
   the `k = 1` case of the separation calculus: a single line crossing
   a cut must carry `j = 0`. All three pieces now exist, each derived
   and oracle-verified before implementation
   ([docs/K1_SECTOR.md](docs/K1_SECTOR.md)) — **loop excision**
   (0 mismatches / 2880 comparisons), **bridge cut** (0 / 4608), and
   the **dumbbell terminal** (0 / 162). Bridge cut splits a diagram in
   two, so states are now multi-component and the goal is a property of
   every component. This closed a silent incorrectness — `solve()` used
   to terminate on two tadpoles joined by a bridge and emit a formula
   with every `j = 0` constraint dropped — and exposed two further bugs:
   the flip was unguarded against self-loop legs, and the evaluator
   never enforced the 3j triad conditions (186 of 729 labelings wrong on
   an existing fixture, no k=1 move involved)

5. **The heuristic is too coarse, not too small** (v0.8.4, and this
   corrects the v0.8.1 framing). The wall is at **n≈28**; turning the
   heuristic off costs ~2%, decaying with n. But the fix is not a
   bigger bound: adding `(n-2)/2` — a correct term growing linearly in
   n — changes expanded-node counts by **zero**, because a term that is
   a function of depth shifts every frontier state equally and
   separates none. Over all 97 states at n=8 with a computable optimum,
   true `C*` takes **six** distinct values and the shipped bound takes
   **two**. **Width invariants are closed off**: `S ≥ cw−3` is refuted
   by tetrahedron, prism and a random n=10 graph — the 6j identity
   collapses a 4-line cut for free, so cut-counting over-charges — and
   carving width neither separates the cases nor scales. The target is
   now the *discriminating* term: the 2-cut decomposition bound,
   re-derived to be admissible under the k=1 move set. Evidence in
   `scripts/width_probe.py`, derivation in
   [docs/BOUNDS.md](docs/BOUNDS.md) Lemma 4

Broader roadmap: cost-aware associahedron search and Qiskit emission in
`yutsis.circuits`; qudit generalization; general n-line separator cuts;
wigxjpf backend; learned move ordering with exact-search fallback;
SU(2) tensor-network contraction planning.

## Lineage

See [docs/HISTORY.md](docs/HISTORY.md) and [docs/DEVLOG.md](docs/DEVLOG.md)
— from Slagle's SAINT and the Yutsis–Levinson–Vanagas calculus through
Danos and Williams at NBS, the GYutsis heuristics of Van Dyck & Fack,
to this reframing with modern optimal search and machine-verified
phases.

MIT license. To cite, see [CITATION.cff](CITATION.cff).
