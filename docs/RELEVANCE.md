# Relevance check: an honest assessment

Written at v0.8.1 (August 2026), before external review, to state plainly
what this project does and does not add to the field. Outreach and any
paper should make these claims — and no stronger ones.

## What is not novel

The core solver — states as Yutsis graphs, moves as bubble excision,
triangle reduction and the Biedenharn-Elliott flip, search for a cheap
summation formula — is the 1992-2006 program: Williams & Silbar (1992),
NJGRAF/NJSYM (Bar-Shalom & Klapisch), Fritzsche's RACAH, and GYutsis
(Van Dyck & Fack, 2003). Those tools work. For the practitioners who
need recoupling reduction day to day (atomic structure, the nuclear
shell model), they have been good enough for twenty years, and this
project offers them no compelling reason to switch.

Nor is the connection between reduction cost and width invariants new
in the abstract: the tensor-network community has understood since the
2000s that contraction complexity is governed by treewidth-family
invariants. Any competent reviewer will say both of these things, so
this document says them first.

## What is genuinely new

1. **Optimal search with a certified admissible bound.** Every
   predecessor is heuristic by declared design. Optimality with a
   machine-certified bound (`scripts/certify_bounds.py`) yields two
   things the field did not have: certified minima — the Petersen 15j
   is proven three-summation-minimal *within the rewrite calculus*, from
   h = 0, three independent ways — and a rigorous quantitative language
   for where the problem is actually hard (Finding 5's headroom curve).
   Small theorem-grade facts, but new ones.

2. **The verification architecture.** A brute-force magnetic-sum oracle
   at the diagram level, a state-level Clebsch-Gordan overlap oracle,
   and every rewrite's phase required to pass both in CI. In a field
   whose folk knowledge is "the signs are where everything goes wrong,"
   an oracle-certified reduction engine is a qualitative change in
   trustworthiness. It is engineering, and it produced results: the
   textbook flip phase recovered by constrained fit; the prism phase
   theorem; the k=1 sector derived and validated; a latent
   admissibility bug found by principle rather than luck.

3. **The recoupling-to-circuits compiler.** The quantum Schur-transform
   literature computes with a fixed sequential coupling order. The
   observation that coupling-order choice is a circuit-optimization
   problem, that its cost is a summation-formula size, and that a
   certified reduction engine can compile arbitrary tree-to-tree
   recouplings into verified 6j-weighted unitaries — this appears not
   to have been built. It is the bridge from a program dormant since
   2006 to a live field, and the principal reason the project is not a
   reinvented wheel.

4. **The tensor-network bridge, reversed.** The project expected to
   BORROW from tensor-network theory: contraction complexity is
   governed by width invariants, so the summation count should be too.
   Measurement refuted it (docs/BOUNDS.md, Lemma 4). `S >= cw(G) - 3`
   fails on the two simplest benchmarks, because a triangle reduction
   collapses a tetrahedron -- an object with a 4-line cut -- in one step
   via Racah's identity, never materializing the 4-line intermediate.

   Read forward instead of backward, that refutation is a positive
   claim about SU(2) structure: **symmetric tensor networks can be
   contracted more cheaply than their width suggests, because
   recoupling identities collapse cuts that generic contraction must
   pay for.** The bridge did not break; it changed direction. This is a
   message TO the tensor-network community rather than a borrowing FROM
   it, and it is a sharper thesis than the one this document originally
   sketched -- with a certified engine and an exhaustive-search oracle
   behind it, which is exactly what such a claim needs to be credible.

## Aspirations versus implementation: they inverted

The 1983 aspiration — search finds cheap recoupling formulas — proved
*easier* than expected: nauty canonicalization, cycle-targeted moves
and exact phases dispatched every benchmark, and each "wall" dissolved
into a stale premise once re-measured. What proved *harder* is what no
one could have measured in 1983: at n ~ 30, admissible bounds collect
about 2% of the search waste and *decay* with scale (Finding 5), because
summation counts are governed by width invariants and no local
structure predicts them. That is not an implementation shortfall; it is
the discovery that recoupling optimization shares the hardness profile
of tensor-network contraction ordering — with the physics-specific
structure (free 2- and 3-line cuts) as the lever that may carry it
further than the generic case. The novelty migrated from where it was
expected to where it actually was, and the DEVLOG records the
migration.

## Calibrated verdicts

- **Groundbreaking?** No, and outreach must never say so; the reviewer
  who knows GYutsis will dismiss everything else if it does.
- **A strong contribution?** Yes — at SciPost Physics Codebases / JOSS
  level as it stands; at CPC / JCP level once the width-derived bound
  lands with a scaling result, or the compiler with a worked qudit
  example.
- **A research platform?** Unusually good: anyone can build learned
  heuristics on a certified, oracle-verified engine without inheriting
  sign anxiety.
- **Relevant?** Yes — pointing forward, at spin-foam evaluation, SU(2)-
  symmetric tensor networks, and Schur-family circuit compilation; not
  backward at practitioners who already have RACAH.

## The human fact

A 1983 undergraduate insight — that recoupling is a path search between
binary coupling trees — entered the literature in 1992. Its originator
returned forty-three years later with the field's modern tools, built
the certified version of his own idea, discovered exactly where it gets
hard, and pointed it at quantum hardware. Whatever the eventual
citation count, that is a story worth telling honestly — and honesty is
what makes it credible.
