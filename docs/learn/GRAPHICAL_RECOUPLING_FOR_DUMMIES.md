# Graphical Angular Momentum Recoupling for Dummies

*A step-by-step introduction from first principles. No term is used
before it is defined. Every number in this document was computed and
verified by the code in this repository — nothing is illustrative.*

*This is Volume II. Volume I ("Angular Momentum Recoupling for
Dummies", docs/learn/RECOUPLING_FOR_DUMMIES.md) built the algebra:
states as recipes, overlaps, Clebsch-Gordan coefficients, coupling
trees, the 6j symbol, and phases. This volume turns all of it into
pictures — and then into a game a computer can win.*

---

## 0. Why pictures

Volume I ended with a warning: as systems grow, recoupling formulas
become nested summations over products of 6j symbols, and the algebra
explodes. A four-spin recoupling already involves sums over six
Clebsch-Gordan tables. A fifteen-spin one, written longhand, is a sum
over 995,328 terms. Nobody manipulates that by hand without errors —
historically, the errors were almost always *signs*.

In the 1960s, Yutsis, Levinson and Vanagas discovered that these
monsters have a shape. Every recoupling expression is secretly a
**graph** — dots joined by lines — and every algebraic manipulation is
**surgery** on that graph: snip here, contract there, each operation
emitting a known factor. Simplifying the algebra becomes simplifying a
picture. This volume teaches the pictures, the surgeries, their exact
prices, and the game of doing the surgery *cheaply* — which is the
problem this repository's solver plays, optimally, with a machine
double-checking every move.

> **Jargon so far:** graph (dots and lines; the dots are called
> **vertices**, the lines **edges**), surgery (a rewrite of the graph
> that preserves its value while emitting a factor).

---

## 1. The vertex: three lines meeting

Volume I's Clebsch-Gordan coefficient couples spins j1 and j2 into j3.
It has a democratized cousin, the **Wigner 3j symbol**, which treats
all three spins on equal footing (divide out a dimension factor
sqrt(2j3+1), adjust one sign convention, and the three slots become
interchangeable up to simple phases). The 3j symbol is a number
depending on three spins (j1, j2, j3) and their three M-values
(m1, m2, m3), and it vanishes unless m1+m2+m3 = 0 and the three spins
can form a triangle (each one no bigger than the sum of the other two —
the **triad condition**).

**The drawing rule.** Draw a 3j symbol as a **vertex**: one dot with
three lines sticking out, one line per spin. Two bits of bookkeeping
attach to the picture, and both matter:

- **Slot order.** The three spins of a 3j symbol come in a definite
  order, and swapping two of them multiplies the symbol by
  (−1)^(j1+j2+j3). So each vertex remembers a cyclic reading order of
  its three lines. Reversing that order costs the phase just quoted —
  this is the first of exactly two phase rules in the whole calculus.
- **Arrows.** Each line carries a direction (an arrow). The arrow
  records which end of the line contributes +m and which contributes
  −m, together with one **metric factor** (−1)^(j−m) per line.
  Reversing one line's arrow multiplies the diagram by (−1)^(2j) —
  the second and last phase rule, and (Volume I, Section 6) it is
  the famous 720° fact wearing graph clothing.

Those two rules — odd slot reorder costs (−1)^(sum of the triad),
arrow flip costs (−1)^(2j) — generate *every* phase in this subject.
This repository's phase engine is nothing but those two rules, tracked
symbolically with exponents kept modulo 4.

> **New jargon:** 3j symbol (the symmetric CG), triad condition,
> vertex (a 3j drawn as a dot with three lines), slot order, arrow,
> metric factor.

---

## 2. Edges, and the meaning of a closed diagram

Joining two lines into one **edge** means: set the two spins equal and
**sum over the shared m** (with the metric factor along for the ride).
Summing over an m is the graphical act of saying "this quantity is
internal — no one outside will ever ask about it."

Now the central definition. A **closed diagram** is a graph in which
*every* line is an internal edge — no loose ends. Every m has been
summed. What remains depends on no m at all, and (because 3j symbols
are rotationally invariant) on no choice of laboratory orientation
either. **A closed diagram is a pure number.**

Two immediate consequences organize everything that follows:

**First: every vertex has exactly three edges.** So closed diagrams are
**cubic graphs** — the tidy universe where all our surgery happens.

**Second: any closed diagram can be evaluated the dumb way** — just
grind the sum: for every assignment of every m, multiply the 3j values
and the metric signs, and add. This brute-force evaluation is
astronomically expensive but *perfectly trustworthy*, and it is this
repository's **oracle**: the ground truth against which every clever
formula is checked. (Volume I's closing rule — trust verification, not
authority — is implemented here as software.)

> **New jargon:** edge (a summed-over shared line), closed diagram (no
> loose ends; a pure number), cubic graph (every vertex has three
> edges), oracle (brute-force evaluation as ground truth).

---

## 3. First shapes: theta, bubble, and the k = 1 rules

**The theta graph** — two vertices joined by three parallel edges
(shaped like θ) — is the smallest closed diagram. Its value is ±1 when
the three spins satisfy the triad condition and 0 otherwise; with
matching slot orders and consistent arrows it is exactly +1, and any
deviation is priced by the two phase rules. The theta is the
calculus's "empty" answer: reductions end here.

**The bubble** — two vertices joined by *two* parallel edges, each
vertex with one line continuing outward — is the graphical form of
Volume I's orthogonality (perpendicular rows of the CG table). A bubble
collapses: the two outward lines must carry equal spins (a **delta**,
written δ(a,b): the factor that is 1 if a = b and 0 otherwise), the
bubble vanishes into the factor δ(a,b)/(2a+1) times a phase, and the
two outward lines fuse into one. Price: **free** — no 6j, no
summation.

**The k = 1 rules** are the strangest and simplest. A closed diagram is
a rotationally invariant number, and an invariant cannot depend on a
single spinning line crossing a boundary — so any **bridge** (an edge
whose removal disconnects the diagram) must carry spin exactly 0, and
the diagram splits into two independent closed pieces. A **self-loop**
(an edge from a vertex back to itself) forces the vertex's third line
to spin 0 similarly. Both are free surgeries. (Historical note from
this repository's log: these were first mis-treated as annoying edge
cases; recognizing them as the k = 1 rung of a ladder — see Section 6 —
fixed a genuine completeness bug. Edge cases are usually theorems in
disguise.)

> **New jargon:** theta graph, bubble, delta δ(a,b), bridge, self-loop.

---

## 4. The triangle rule and the tetrahedron

Here is the workhorse. A **triangle** — three vertices mutually joined,
each with one outward line — contracts to a *single vertex* on the
three outward lines, and the surgery emits exactly one **6j symbol**
whose six arguments are the triangle's three inside edges and three
outward lines. Price: **one 6j, no summation.** One important subtlety,
caught in this repository by a machine-derived theorem: the 6j's
argument *pairing* matters — each inside edge pairs with the outward
line *opposite* it (the one at the vertex it does not touch). An
earlier, plausible-looking pairing was structurally wrong and slipped
past tests only because symmetric examples masked it. Plausible is not
verified.

Apply the triangle rule to the smallest interesting closed diagram, the
**tetrahedron** (four vertices, six edges, every trio of... every face
a triangle): one triangle contraction turns it into a theta. So the
tetrahedron *is* a single 6j symbol — in fact, the brute-force
evaluation of the tetrahedron diagram is precisely the classical
defining sum for the 6j, and this repository's oracle reproduces
library 6j values from it, sign included, on integer and half-integer
spins. The atom of Volume I has a shape, and the shape has four corners.

**A worked reduction: the prism.** Take the triangular prism (two
triangles joined by three rungs — six vertices, nine edges). Contract
one triangle (one 6j), and what remains is a tetrahedron; contract
again (second 6j), leaving a theta. Total price: **two 6j's, zero
summations** — the prism *factorizes*. The exact statement, derived by
this repository's phase engine from the two phase rules and verified
value-exactly against the oracle on twelve random spin assignments
including half-integers:

    prism = (−1)^(j1+j2+j3 + 2·l1 + 2·k2 + 2·k3) × {6j} × {6j}

Read the phase with Volume I's eyes: the j1+j2+j3 term is slot-order
bookkeeping on the rungs; the 2·l terms are 720° facts, alive only for
half-integer spins.

> **New jargon:** triangle rule (one 6j, no sum), tetrahedron (= the 6j
> itself), factorization (reduction with zero summations).

---

## 5. The flip: where summations are born

Not every diagram has a triangle. The **girth** of a graph is the
length of its shortest cycle; bubbles are girth-2, triangles girth-3.
When the girth is 4 or more, none of the free-or-cheap rules apply, and
the calculus provides exactly one more move.

**The interchange (or flip)** is the graphical form of Volume I's
re-pairing (a b) c → a (b c). Pick an internal edge e between vertices
u and v; swap one of u's other lines with one of v's. The graph rewires
— crucially, cycles through e get *shorter*, so triangles eventually
appear — and the price is steep: the flipped edge's spin is replaced by
a brand-new **summed spin x**, and one 6j is emitted whose arguments
are the local spins and x. Price: **one 6j AND one surviving
summation Σ_x (2x+1)(...).** The flip's phase, in this repository, was
determined by fitting against an independent 9j implementation over 22
spin assignments: of 8192 candidate sign laws, the survivors formed one
equivalence class whose representative is (−1)^(p+q+e+x) — the
textbook recoupling phase, recovered by machine from raw agreement.

**Worked example: K3,3 is the 9j.** The complete bipartite graph K3,3
(two rows of three vertices, every top joined to every bottom — nine
edges) has girth 4: no triangle anywhere. One flip creates triangles;
two triangle contractions then finish it. Total: three 6j's, one
summation — exactly Volume I's 9j formula, Σ_x (2x+1)(−1)^(2x)
{6j}{6j}{6j}, and the oracle confirms the closed K3,3 diagram equals
the library 9j to the last digit. The twisted prism *is* the 9j; the
twist is what costs the summation.

> **New jargon:** girth, interchange/flip (one 6j plus one summation;
> the price of re-pairing), summed spin.

---

## 6. The ladder of cuts: why summations are the currency

Step back and see the pattern. Call a set of k edges whose removal
splits the diagram a **k-line cut**. The rules line up on a ladder:

    k = 1 (bridge):        free — the line carries spin 0
    k = 2 (bubble-style):  free — a delta ties the two lines
    k = 3 (triangle/prism-style): free — one 6j-type factorization
    k = 4 and above:       each step past 3 costs one summation

The general law: separating a diagram across k lines costs
**(k − 3) summations** (never less than zero). Three lines' worth of
information can always be repackaged into one vertex; anything wider
leaves residue that must be summed over. So the *shape* of a diagram —
how narrowly it can be cut apart — governs the cheapest formula it can
have, and **summations are the currency** in which shape is priced.
(A caution from this repository's log, recorded after an honest
refutation: the tempting converse — "minimum summations equals
narrowest-cut width minus three" — is FALSE, because the 6j identity
collapses some 4-line cuts for free. The rewrite calculus is strictly
*stronger* than generic cut-counting. Read forward, that is a positive
discovery: spin networks can be contracted more cheaply than their
graph width suggests.)

> **New jargon:** k-line cut, the (k−3) law, width (informally, the
> narrowest way to cut a graph apart everywhere).

---

## 7. The game, and a certified championship match

Now assemble the game the way a computer sees it. A **state** is a
closed cubic graph. The **moves** are the five surgeries: bubble
excision, self-loop excision, bridge cut (free), triangle contraction
(one 6j), and the flip (one 6j plus one summation). The **goal** is the
theta (or a collection of them). The **cost** of a finished reduction
counts its 6j's, with each surviving summation priced at ten 6j's
(evaluating a Σ means running everything inside it many times). Finding
the cheapest reduction is a search problem — and it is genuinely hard
in general (deciding the relevant graph property is NP-complete), which
is why it was attacked heuristically in the 1990s–2000s and why this
repository attacks it with optimal search plus proofs.

**The Petersen match.** The Petersen graph — ten vertices, fifteen
edges, girth five, the most famous graph in combinatorics — is a
fifteen-spin recoupling coefficient with no bubble or triangle
anywhere. The solver's certified-optimal reduction: three flips
(purchasing the triangles that girth five denies, at one summation
each) and four triangle contractions, finishing at a theta. Total:
**seven 6j's, three summations, cost 37** — and *certified minimal*:
a heuristic-free exhaustive search over the full move set returns 37,
and the cost accounting proves any two-summation plan would cost at
most 26, so three summations is a theorem, not an observation. The
resulting formula (three nested Σ's, seven 6j's, a thirteen-term
phase) was then evaluated at a specific spin assignment and compared
against the oracle's brute-force sum over 995,328 magnetic
assignments:

    formula:      +0.004629630
    brute force:  +0.004629630      MATCH

Nothing in that chain rests on trust. The moves were derived from the
two phase rules; the plan was found by search; the certification used
no heuristic; and the final number was checked against quantum
mechanics done the dumb way. (An animated replay of this exact
reduction, factor by factor, lives at docs/petersen_15j_reduction.html
— every frame drawn from the real solver trace.)

> **New jargon:** state/move/goal/cost (the search formulation),
> certified minimal (proven optimal, not just best-found).

---

## 8. Reading a real formula

Fluency test. Here are three factors from the machine's Petersen
output, exactly as emitted:

    Σ_x_o1 (2x+1) · {o0 o1 s1; o2 x_o1 s2}      ← a flip: new summed
                                                   spin x_o1, one 6j
    {s0 o0 o4; x_s2 i3 i0}                       ← a triangle: one 6j,
                                                   opposite-edge pairing
    (−1)^( i0 + i1 + 2·i2 + ... + x_o1 + ... )   ← the phase: slot
                                  reorders (coefficient 1 = half-turns)
                                  and 720° facts (coefficient 2)

If each line now parses — you can say what kind of surgery emitted it,
what it costs, and where its signs come from — you read Yutsis. That is
the entire literacy this volume promised.

---

## 9. From pictures to programs

For the reader who wants to touch the machinery, the map of this
repository in this volume's vocabulary: `graph.py` holds the states
(cubic graphs, with an exact fingerprint for recognizing the same shape
twice — a subtler problem than it sounds); `moves.py` the five
surgeries; `search.py` the game-player; `phase.py` the two phase rules
tracked symbolically; `oriented.py` the exact (sign-carrying) surgeries
and full-formula emission; `oracle.py` the brute-force ground truth;
`circuits.py` the bridge onward — coupling trees compiled into verified
quantum-gate blocks, because the change-of-pairing matrices of Volume I
are exactly the unitaries a quantum computer's Schur-transform circuits
are made of, and cheap formulas mean cheap circuits. The development
log (docs/DEVLOG.md) records not just what worked but every refuted
conjecture with its counterexample — in this craft, the graveyard is
part of the curriculum.

---

## Glossary (in order of appearance)

- **vertex / edge** — a 3j symbol / a summed-over shared line.
- **3j symbol** — the symmetric form of the Clebsch-Gordan coefficient;
  vanishes without the triad condition.
- **slot order** — a vertex's reading order; odd reorder costs
  (−1)^(sum of its three spins).
- **arrow / metric factor** — a line's ±m orientation with its
  (−1)^(j−m); arrow reversal costs (−1)^(2j) (the 720° fact).
- **closed diagram** — no loose ends; a pure, orientation-independent
  number.
- **cubic graph** — every vertex trivalent; the arena.
- **oracle** — brute-force evaluation by summing every m; ground truth.
- **theta / bubble / bridge / self-loop** — the free shapes: value ±1;
  δ(a,b)/(2a+1); forced spin-0 split; forced spin-0 third line.
- **triangle rule** — contract a triangle for one 6j, no summation;
  pairing is opposite-edge.
- **tetrahedron** — the 6j symbol's own shape.
- **girth** — shortest cycle length; girth ≥ 4 means no free progress.
- **flip / interchange** — the re-pairing move: one 6j plus one new
  summed spin; phase (−1)^(p+q+e+x).
- **k-line cut / the (k−3) law** — separating across k lines costs
  max(0, k−3) summations.
- **cost** — 6j count plus ten per surviving summation; the game's
  score.
- **certified minimal** — optimality proven by exhaustive search plus
  accounting, not merely observed.
