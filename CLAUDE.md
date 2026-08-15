# CLAUDE.md — project conventions (yutsis)

## Workflow: always work in a branch

Never commit directly to main. For every task, however small:

1. Create a feature branch (`feature/<short-name>` or `fix/<short-name>`)
   from an up-to-date main.
2. Commit incrementally there with clear messages.
3. Open a PR to main when the work is coherent and CI-green locally
   (`pytest -q`, plus `ruff check src tests` once linting lands).
4. The PR description should read like a draft DEVLOG entry: what was
   built, what broke, what it taught.
5. Merge happens only after the GitHub Actions run is green and the
   human maintainer has reviewed. Do not merge your own PRs.

Main is the certified state of the project; branches are where the
uncertainty lives.

## The iron rule

No formula or bound is trusted on inspection. Every rewrite rule change
ships with an oracle test; every heuristic change ships with an
admissibility test. CI must stay green.

## Current task: Refactor brief — feature/refactor-oriented (behavior-preserving, v0.8.2)

DEFINITION (non-negotiable): refactoring changes structure, clarity, and
performance; observable behavior is FIXED. No new moves, no bound
changes, no new features. Any functionality change belongs in its own PR.

THE REFACTOR ORACLE — must be byte-identical before/after, and stated in
the PR description:
  - all 91 tests green
  - scripts/certify_bounds.py: CERTIFIED, same violation counts (0/0)
  - benchmark table: tetra 1, prism 2, K3,3 13, cube 14, Petersen 37
  - scripts/stress.py: identical costs AND expansion counts
  - scripts/verify_petersen.py: +0.004629630
  - scripts/headroom.py: identical table

DIFF DISCIPLINE: a refactor diff must not change any numeric constant,
phase coefficient, cost weight, or bound expression. If a change touches
a number, it is not a refactor — split it into its own PR. The oracle
table is necessary, not sufficient: it certifies behavior where measured;
the diff rule certifies intent everywhere.

TARGETS, in order:
  1. Split oriented.py (662 lines, seven concerns) into state.py
     (OGraph, components), exact_moves.py (the five exact moves),
     replay.py (replay, solve_exact, evaluate_expr). Keep
     `yutsis.oriented` as a re-export shim so no import breaks.
  2. Rewrite the interchange_exact normalization block (the
     want_tail / tail_should_be loop) as a single principled
     canonicalize-endpoint helper. Same phases, same graph out; the
     existing K3,3/9j and Petersen tests are the guard.
  3. Consolidate builders: oriented_petersen, oriented_k33, dumbbell
     move to benchmarks.py once; tests and scripts import them.
     Hand-rolled matmul in tests -> a tiny tests/helpers.py.
  4. Review test_bounds.py and test_k1_sector.py for redundancy and
     naming; merge duplicates, keep coverage identical.
  5. Land ruff (line-length 88) + CI step; fix only what it flags.

Branch, PR, no self-merge. DEVLOG entry: what moved, what was renamed,
and the oracle table proving nothing else changed.

## Testing conventions

- CI-fast tests use small j values (oracle sums grow as the product of
  (2j+1)); slow full sweeps live in scripts/verify_*.py and run before
  releases, not in CI.
- Every new closed-diagram convention or emitted factor gets validated
  numerically against yutsis.oracle (diagram level) and, where states
  are involved, against explicit CG-built overlaps (state level,
  yutsis.circuits.overlap_oracle).
- Regression tests pin structural facts (e.g. opposite-edge 6j pairing,
  the fitted flip phase) so they cannot silently drift.

## Style

- Prose docstrings that state derivations and their boundaries.
- Findings (walls, failure modes) are documentation, not
  embarrassments: add them to README "Next steps" and the DEVLOG when
  you hit one.
- Prefer a smaller proven bound over a larger conjectured one.
- The search layer never needs to know physics; the physics layer never
  needs to know search.
