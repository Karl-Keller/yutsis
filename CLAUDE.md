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

## Current task: the width-derived summation bound (Finding 5 / Finding 3)

Prerequisites are now met. The k=1 sector is closed (v0.8.0), so
degenerate states are dissolved rather than scored around;
`Graph.true_girth()` is the one function that sees 1-cycles; and
v0.8.2 split the exact layer so `bounds.py` can grow without dragging
662 lines of physics behind it.

WHAT THE MEASUREMENT SAYS THIS MUST BE (docs/NEXT_STEPS.md, Finding 5).
Not "tighten the bound". At n = 30 the search expands 2010 nodes for a
25-move plan and the shipped heuristic removes ~2% of that waste, a
figure that DECAYS with n (20% at n=16). The provable girth
strengthening `S >= true_girth - 3` was implemented and measured at
0-3%: no better. The arithmetic is why -- at n = 30 the cost is 135, of
which summations are ~110, and any LOCAL bound returns at most 20.

    The bound must estimate remaining summations and SCALE WITH n.

CLOSURE CRITERION: a bound whose `saved` column in scripts/headroom.py
does not decay with n. That is the test; a tighter-looking formula that
fails it has not closed this.

1. DERIVE first, in docs/BOUNDS.md, as Lemma 4. The anchor is the
   k-line calculus already stated there: a k-line separation costs
   max(0, k-3) summations, so 2- and 3-line cuts are free and the
   summation count is a property of the EDGE-separator structure. For
   cubic graphs the natural invariants are carving width and
   branchwidth, NOT vertex treewidth -- and note the recorded
   counterexample: prism and K3,3 both have treewidth 3 but S = 0 and
   S = 1, so treewidth alone cannot separate them. Do NOT bake in an
   unproven inequality.
2. ADMISSIBILITY IS STILL THE CROWN JEWEL. Exact carving width is
   NP-hard, so any approximation must be a LOWER bound on the
   invariant (a lower bound of a lower bound stays admissible).
   Upper-bound estimators -- min-fill, min-degree, and the greedy
   orderings the tensor-network literature reaches for first -- are
   UNSAFE here. When in doubt ship `max(h_old, h_width)` and keep both.
3. MECHANIZE in src/yutsis/bounds.py; search.py stays physics-free.
   Reach for `true_girth()`, never `girth_lower()` (a move-availability
   predicate) or `girth_cycle()` (blind to self-loops).
4. VERIFY. The admissibility corpus in tests/test_bounds.py and
   scripts/certify_bounds.py is the ground truth; both must stay at 0
   violations. Then run scripts/headroom.py and report the `saved`
   column against the closure criterion -- a bound that is admissible
   but still decays is an honest negative result and gets written up as
   one.
5. RE-DERIVE THE OPT-IN DECOMPOSITION BOUND while you are here. It sits
   at 8 admissibility violations under the completed move set, because
   each free move added in the k=1 sector lowered C* below (n_i-2)/2
   per piece. It needs re-deriving against the move set as it now
   stands, not repairing.

THE STANDING RULE, which bit twice in the k=1 sector: any new FREE move
must be added to `bounds.sum_bound`'s move-availability test in the
SAME commit that adds the move, with the corpus re-run.

Housekeeping per session: dated docs/DEVLOG.md entry (what was built,
what broke, what it taught); update NEXT_STEPS.md and the README
Findings; bump the version in ALL THREE of pyproject.toml,
src/yutsis/__init__.py and CITATION.cff (version AND date-released) --
tests/test_metadata.py enforces the three-way agreement, so a red CI
after a bump is the ritual working; re-run scripts/stress.py and
scripts/headroom.py and record the numbers.

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
