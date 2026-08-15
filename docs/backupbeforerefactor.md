## Current task: treewidth-derived admissible bound (NEXT_STEPS.md, Finding 3)

1. DERIVE first: state the lemma precisely in docs/BOUNDS.md — the exact
   relationship between a width invariant (treewidth / branchwidth /
   carving width of the anonymous cubic multigraph) and the minimum
   number of surviving summation variables, with a proof sketch.
   Anchor: a k-line separation costs (k-3) summations; 2- and 3-line
   cuts are free. Do NOT bake in an unproven inequality.
2. ADMISSIBILITY IS THE CROWN JEWEL: an over-tight h silently destroys
   the A* optimality claim — the project's central guarantee. Since
   exact treewidth is NP-hard, any approximation used must be a LOWER
   bound on the invariant (a lower bound of a lower bound stays
   admissible); an upper-bound estimator (min-fill, min-degree
   orderings) is UNSAFE here even though the tensor-network literature
   reaches for them first. When in doubt: h_new = max(h_old,
   h_treewidth), and keep both implementations.
3. MECHANIZE: new code in src/yutsis/bounds.py; search.py imports the
   bound but stays physics-free. Small, documented functions.
4. VERIFY (tests/test_bounds.py):
   - Admissibility corpus: for every small graph whose true optimum C*
     is known or computable by exhaustive blind-move A* (tetrahedron=1,
     prism=2, K3,3=13, cube=14, plus random cubic n<=8 via blind
     exhaustive search), assert h(root) <= C*. This corpus is to
     heuristics what the magnetic-sum oracle is to formulas: ground
     truth, one layer up.
   - Dominance: assert h_new >= h_old across the corpus.
   - The payoff: attempt to CERTIFY Petersen with blind-move A* under
     the new bound (generous budget; mark slow or place in scripts/).
     Whether it certifies 3 sums or finds 2, record the answer in the
     DEVLOG — either result is a publishable fact.
5. Housekeeping per session: append a dated entry to docs/DEVLOG.md
   (what was built, what broke, what it taught); update NEXT_STEPS.md
   Finding 3 status and the README "Next steps" section; bump version
   in ALL THREE of pyproject.toml, src/yutsis/__init__.py and
   CITATION.cff (version AND date-released) (0.7.0 on completion);
   rerun scripts/stress.py and record expanded-node counts
   before/after in the DEVLOG entry.

   CITATION.cff drifted to 0.6.0 while the package moved on, so the
   three-way version agreement is now enforced by
   tests/test_metadata.py rather than by memory. If you bump a version
   and CI goes red, that is the ritual working.
6. Linting: add ruff (pyproject [tool.ruff], line-length 88) and a
   `ruff check src tests` step to .github/workflows/ci.yml; fix what it
   flags in touched files only.