# The problem, and where it comes from

Angular momentum recoupling — re-expressing the same quantum state under a
different order of coupling its constituent momenta — generates algebra
that grows brutally with the number of momenta involved. Yutsis, Levinson
and Vanagas showed in the 1960s that these expressions are exactly closed
cubic graphs, and that simplification is graph surgery: excise bubbles,
reduce triangles, interchange across edges, each move emitting tabulated
factors (deltas, 6j symbols) and, when unavoidable, summation variables.
The cost of the final formula is dominated by how many summations survive.
Choosing the order of moves to minimize that cost is a search problem.

Threads that meet here:

- 1961: J. Slagle's SAINT thesis founds symbolic computation as heuristic
  search over transformations; the lineage runs through Moses's SIN to
  Macsyma. Slagle's advice to a young physicist decades later: keep it
  simple.
- 1960s-80s: M. Danos (NBS) disciplines the graphical calculus — vertex
  normalizations and phase conventions rigid enough that diagram
  manipulation becomes fully mechanical. H. T. Williams (NBS-associated)
  develops and applies the symbolic recoupling machinery.
- 1983: an undergraduate under Williams attacks the reduction-ordering
  problem as machine search — independently of the AI-search literature
  then being written (Nilsson 1980, Pearl 1984), on Slagle's simplicity
  principle: binary search over paths between binary coupling trees.
  This repository is that work's long-delayed continuation by the same
  hands.
- 1992: the formulation enters the literature. H. T. Williams and
  R. R. Silbar, "Automated angular momentum recoupling algebra,"
  J. Comput. Phys. 99(2), 299-309 (1992),
  doi:10.1016/0021-9991(92)90209-H — heuristic rules whose general
  problem "reduces to that of finding an optimal path from one binary
  tree ... to another," implemented in LISP on a microcomputer as a
  code called RACAH (a name Fritzsche's later Jena package would carry
  forward). The binary-tree path formulation seeded in 1983 is the
  paper's central framing — and it is precisely the problem this
  repository's yutsis.circuits module solves today as the quantum
  recoupling-gate compiler (flip_path on the associahedron, each edge a
  machine-verified unitary), rebuilt independently thirty-four years
  later from the quantum-circuits direction.
- 1990s-2000s: automation arrives — NJGRAF/NJSYM (Bar-Shalom & Klapisch),
  Fritzsche's RACAH, and GYutsis (Van Dyck & Fack 2003), which reduces
  Yutsis graphs with hand-crafted, pluggable heuristics and documents a
  counter-example showing girth-first greediness is not always optimal.
  Deciding the underlying Yutsis property is NP-complete.
- 2000s-now: the demand side grows — SU(2)-symmetric tensor networks,
  spin-network methods, and quantum computing, where the Schur transform
  is a Clebsch-Gordan cascade and formula size becomes gate count.

What this project adds: optimal search (A* with admissible physics-derived
bounds) in place of fixed heuristics; a brute-force magnetic-sum oracle so
that every emitted formula is numerically validated rather than trusted;
and an explicit road to learned guidance for the sizes where exact search
must yield.
