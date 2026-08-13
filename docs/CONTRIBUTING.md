# Contributing

- Every rewrite rule or phase change must come with an oracle test:
  build the closed diagram, evaluate by direct magnetic summation,
  compare against the emitted formula numerically. No formula is trusted
  on inspection.
- Keep moves local and guards explicit; the search layer must never need
  to know physics.
- Findings (walls, failure modes) are documentation, not embarrassments —
  add them to the README when you hit one.
