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

## Diff discipline (any refactor, not just the one that introduced it)

Refactoring changes structure, clarity and performance; observable
behavior is FIXED. A refactor diff must not change any numeric constant,
phase coefficient, cost weight, or bound expression. If a change touches
a number, it is not a refactor -- split it into its own PR.

An oracle table is necessary, not sufficient: it certifies behavior
where measured; the diff rule certifies intent everywhere. Capture the
oracle BEFORE the first edit, or "identical" is unfalsifiable.

Prose needs an oracle too. v0.8.2 mangled docstrings across 25 files
while every test stayed green, because tests do not read documentation.
Compare docstrings via `ast.get_docstring` after any bulk edit, and
commit before each risky one so revert is a one-liner.

Reuse the verified primitive. A scratch reimplementation is an
unverified one, and it will be wrong in the case the real one was fixed
for. v0.9.0 lost an hour to a scratch bridge finder that tested
reachability against ALL vertices, so in a DISCONNECTED state every edge
looked like a bridge; it produced "cubic" pieces with an odd number of
vertices, which is impossible, and briefly refuted a correct design.
`Graph.bridges()` had been per-component since v0.8.0.

Assert your replacements. `str.replace` that matches nothing fails
silently: two README edits no-op'd and left the version header stale at
v0.8.1 for three releases. Assert the old text is present before
writing. This is the prose twin of the iron rule -- green everywhere,
wrong on the page.

For bulk edits, use a tool of the right CATEGORY. String-ness and
comment-ness are properties of the token stream, not of a line, so no
line-local test can decide whether it is inside a docstring -- reach
for `tokenize` or `ast`, never substring guards. The v0.8.2 failure was
a `str.split(";")` behind "does not start with #" and "contains no
quote character"; both leak, because trailing comments do not start
with `#` and a triple-quoted string's interior lines contain no quotes.
Splitting inside a comment raises SyntaxError and is caught at once;
splitting inside a docstring is still valid Python and is caught by
nothing.

## Current task: the flip-count bound (Finding 5, and the last family standing)

THE DIAGNOSTIC IS DONE, and it eliminated one of the two attack
families outright. Over n = 16..30, every expanded node has `f < C*`:

    plateau share (f = C*): 0% at every size

`h` is CONSISTENT -- `certify_bounds` reports 0 step violations -- so
A* never re-expands and the split is exhaustive. The waste is therefore
100% MANDATORY given `h`. No tie-breaking, no queue discipline and no
learned ranker can remove a single node from this search. Only a
stronger admissible bound can.

(That also closes the "learn to order, not to bound" idea for this cost
model. It was the attractive option -- no admissibility obligation --
and it is worth nothing here. Do not revisit without re-running the
histogram, `scripts/plateau_probe.py`.)

WHAT SURVIVES, and it has a measured first rung. The sharper test for
`S >= 1` is not move-availability but REDUCIBILITY:

    flip_free_reducible(G): can G reach a terminal using only
                            bubble / loop / bridge / triangle moves?
    S >= 1  iff  not flip_free_reducible(G)

Trivially admissible -- if no flip-free path to a terminal exists, every
reduction uses a flip -- and a small search, since each such move drops
n by 2 and there are no flips to branch on. Measured against the
shipped `sum_bound`, which only asks whether a free move applies RIGHT
NOW:

    fires on 223 of 910 corpus states, against sum_bound's 35
    a strict superset (0 states where sum_bound fires and G is reducible)
    expansions cut 20% / 11% / 7% / 6% / 5% / 4% at n = 16..30, costs
    unchanged

That is the first bound since Finding 5 that removes any waste at all.
It still DECAYS, so it does not meet the closure criterion.

THE LADDER, which is the actual task:

    S >= k+1  iff  no sequence of k flips reaches a flip-free-reducible
                   state

1. Ship rung one (`S >= 1` by reducibility). Provable, measured, and it
   subsumes the current girth test -- keep `max()` with the old bound
   only if a corpus state is found where the old one is larger.
2. Build rung two (`S >= 2`): for every flip-child G', test
   `flip_free_reducible(G')`. Admissible by construction. Price it --
   roughly 4|E| reducibility tests per node -- and measure whether the
   expansion cut pays for the per-node cost in WALL CLOCK, not just in
   node counts.
3. Report the `saved` column against the closure criterion. If it still
   decays, say so; a ladder that buys a constant factor and not an
   asymptotic one is an honest result and should be written up as
   Lemma 6.

ALTERNATIVE, if the ladder prices out: an endgame pattern database --
exact `C*` memoized by canonical certificate for every topology up to
n ~ 10-12, giving EXACT h once the search descends into tabulated
territory. `scripts/certify_bounds.py` already builds most of the
corpus machinery. Exact h below the cut, admissible above it.

ADMISSIBILITY REMAINS THE CROWN JEWEL. `certify_bounds` must return 0
violations and 0 step violations; the discrimination columns are the
leading indicator, with Lemma 5's warning that discrimination must land
at the SUM_PENALTY granularity to change any decision.

Housekeeping per session: dated docs/DEVLOG.md entry; update
NEXT_STEPS.md and the README Findings; bump the version in ALL THREE of
pyproject.toml, src/yutsis/__init__.py and CITATION.cff (version AND
date-released); re-run scripts/stress.py, scripts/headroom.py and
scripts/certify_bounds.py and record the numbers.

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
