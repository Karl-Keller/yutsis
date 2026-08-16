# Angular Momentum Recoupling for Dummies

*A step-by-step introduction from first principles. No term is used
before it is defined. Every number in this document was computed and
verified by the code in this repository — nothing is illustrative.*

*Companion volume: "Graphical Angular Momentum Recoupling for Dummies"
(docs/learn/GRAPHICAL_RECOUPLING_FOR_DUMMIES.md), which redoes this
subject in pictures. Read this one first.*

---

## 0. The promise

By the end of this document you will understand what a Clebsch-Gordan
coefficient is, what a 6j symbol is, what "recoupling" means, and why a
computer program might spend its life searching for the cheapest way to
do it — and you will have *derived* the key numbers yourself using
nothing beyond fractions, square roots, and the idea of perpendicular.

One ground rule, borrowed from this repository's engineering practice:
**no formula is trusted on inspection.** Every claim below was checked
numerically against independent machinery. When we say a number is 1/2,
a machine summed something ugly and got 0.500000000.

---

## 1. Spin: the smallest possible fact

Some particles (electrons, protons, neutrons) carry a built-in quantity
called **spin**. Despite the name, *nothing is rotating* — spin is a
label for how the particle's description responds when you rotate your
laboratory, and that is all it is. The smallest nonzero spin is called
**spin one-half** (written spin-1/2), and a spin-1/2 particle measured
along any chosen axis gives exactly one of two answers: **up (↑)** or
**down (↓)**. Two answers, never a third. That is the entire menu.

A **state** is a complete description of a particle (or a group of
them) at one instant. It is a noun, not a motion — a thing, not a
process. For one spin-1/2 particle the possible descriptions are built
from just ↑ and ↓.

Here is the first genuinely quantum idea. A state is generally a
**recipe**: a list of basic patterns, each with an **amount** attached.
The amounts are called **amplitudes**. Amplitudes can be negative (we
will see why that matters enormously), and the *probability* of finding
a given pattern when you look is the amplitude **squared**. Because
probabilities must total 1, the squares of a recipe's amounts must add
to 1 — we then call the recipe **normalized**.

> **Jargon so far:** spin (response-to-rotation label), state (a
> complete description), amplitude (the amount of a pattern in a
> recipe), normalized (squares of amounts total 1).

---

## 2. Two arrows, and the machine that builds everything

Take two spin-1/2 particles, a and b. The basic patterns are now the
four combinations ↑↑, ↑↓, ↓↑, ↓↓. A useful bookkeeping number is
**M**: count +1/2 for each ↑ and −1/2 for each ↓ and add. So ↑↑ has
M = 1, ↓↓ has M = −1, and both ↑↓ and ↓↑ have M = 0.

Physics supplies exactly one machine for organizing these patterns into
meaningful families. It is called the **lowering operator** (symbol
J−), and its rule is simple enough for a ten-year-old:

> **The flip-down machine:** visit each arrow once, flip it from ↑ to
> ↓ (an arrow already ↓ gives nothing), and add up all the results.

Let's run it. Feed in ↑↑:

    flip arrow 1:  ↓↑
    flip arrow 2:  ↑↓
    output:        ↓↑ + ↑↓

How "long" is the recipe ↓↑ + ↑↓? Treat the amounts (1 and 1) as the
sides of a right triangle: length = sqrt(1² + 1²) = sqrt(2). To make it
a normalized state, divide by its length:

    (↑↓ + ↓↑) / sqrt(2)

We have just built a family by lowering. Start at the top pattern ↑↑
(the only pattern with M = 1, so no mixing is possible there), lower
once to get the equal mix above at M = 0, lower again (try it — you get
↓↓ twice, which normalizes to ↓↓) at M = −1. Three states, one family.
This family is called **total spin 1** (also "the triplet"). The number
of family members is always 2×(spin)+1, and 2×1+1 = 3. ✓

But the M = 0 room has *two* independent directions (↑↓ and ↓↑), and
the family only used one mix of them. What is the other? Here is the
second great tool: **perpendicularity**. Two recipes are perpendicular
when their overlap is zero, where the **overlap** of two recipes is
computed by the simplest rule imaginable:

> **Overlap:** line up matching patterns, multiply their amounts, add.

The triplet's M = 0 member has amounts (1, 1)/sqrt(2) on (↑↓, ↓↑). The
perpendicular direction is (1, −1)/sqrt(2), since 1·1 + 1·(−1) = 0.
That lone state,

    (↑↓ − ↓↑) / sqrt(2)

is a one-member family: **total spin 0** (the "singlet"; 2×0+1 = 1 ✓).
Notice what distinguishes them: the spin-1 state is **symmetric** —
swap the two arrows and nothing changes — while the spin-0 state is
**antisymmetric** — swapping flips its overall sign. Remember this; it
is the key that unlocks Section 4.

That minus sign is physical. Amplitudes with opposite signs *cancel*
when combined — the phenomenon called **interference**. A minus sign is
not bookkeeping; it is a wave arriving crest-on-trough. (For the full
picture of signs as clock hands, see Section 7.)

> **New jargon:** lowering operator / flip-down machine, overlap
> (multiply matching amounts and add — mathematicians call it the inner
> product), perpendicular (overlap zero), symmetric/antisymmetric
> (behavior under swapping), triplet, singlet, interference.

---

## 3. Clebsch-Gordan coefficients: the conversion table

What we built in Section 2 is a **change of description**. The same
four-dimensional space of two-arrow states has two natural coordinate
systems: the **product basis** (the raw patterns ↑↑, ↑↓, ↓↑, ↓↓) and
the **coupled basis** (organized by total spin and M: the three triplet
states and the singlet). The conversion table between them:

                     ↑↑       ↑↓        ↓↑       ↓↓
    |spin1, M=+1>     1        0         0        0
    |spin1, M= 0>     0     1/√2      1/√2       0
    |spin0, M= 0>     0     1/√2     −1/√2       0
    |spin1, M=−1>     0        0         0        1

The entries of this table are the famous **Clebsch-Gordan (CG)
coefficients**. That is all they are: the amounts in the conversion
recipes between "describe each particle separately" and "describe the
team by its total." This table is a matrix; it is *unitary* (its rows
are normalized and mutually perpendicular — check any pair by the
overlap rule), which is the mathematical way of saying no information
is created or destroyed by changing description.

Why does anyone care about total spin? Because rotations of the
laboratory respect it: this one fixed table simultaneously untangles
*every* rotation into independent blocks, one per family. (We verified
this numerically: conjugating an arbitrary rotation by the table above
produces a clean 3×3 spin-1 block and a 1×1 spin-0 block, off-blocks
exactly zero.) Families of definite total spin are the natural
vocabulary of anything rotationally well-behaved — which is most of
physics. This is why CG tables saturate atomic, nuclear, and particle
physics.

> **New jargon:** product basis, coupled basis, Clebsch-Gordan
> coefficient (a conversion-table entry), unitary (a lossless change of
> description).

---

## 4. Three arrows: where recoupling is born

Now the main event. Take three spin-1/2 particles a, b, c, and ask for
team states with total spin 1/2 and M = +1/2. Exactly three raw
patterns have M = +1/2:

    ↑↑↓     ↑↓↑     ↓↑↑

so every candidate state is a recipe (x, y, z) over those three
patterns — a point in a three-direction "pattern room."

**Rule 1 (perpendicularity).** There is also a total-spin-3/2 family.
Its top state is ↑↑↑ (the only M = 3/2 pattern), and one pass of the
flip-down machine gives ↓↑↑ + ↑↓↑ + ↑↑↓ — each pattern once — of
length sqrt(3). So the 3/2 family's M = 1/2 member is the perfect
diagonal (1, 1, 1)/sqrt(3). Different-total-spin families are always
perpendicular, so any spin-1/2 recipe must satisfy

    x + y + z = 0.

**Rule 2 (a pairing choice).** One equation leaves a whole plane of
candidates. To pick a direction we must decide *which two particles to
pair first* — and this choice is the entire subject of this monograph.

**Plan A: pair (a, b) at spin 1.** From Section 2, "the pair has spin
1" means *symmetric under swapping a and b*. Swapping the first two
arrows leaves ↑↑↓ alone and exchanges ↑↓↑ ↔ ↓↑↑, so symmetry demands
y = z. Solve the two little equations:

    x + y + z = 0  and  y = z   ⟹   x + 2y = 0.

Pick y = −1; then x = +2. Length = sqrt(4+1+1) = sqrt(6). So

    Plan A = ( 2·↑↑↓ − 1·↑↓↑ − 1·↓↑↑ ) / sqrt(6).

Every coefficient derived; nothing looked up. (These match the CG-table
construction exactly — we checked by machine.)

**Plan B: pair (b, c) at spin 1.** Symmetry under swapping the *last*
two arrows exchanges ↑↑↓ ↔ ↑↓↑, so x = y, hence z = −2x:

    Plan B = ( 1·↑↑↓ + 1·↑↓↑ − 2·↓↑↑ ) / sqrt(6).

**The recoupling coefficient.** Same three particles, same total spin,
same M — two legitimate descriptions. How similar are they? Apply the
overlap rule:

    (2)(1) + (−1)(1) + (−1)(−2) = 2 − 1 + 2 = 3,   then ÷ (√6·√6 = 6):

    ⟨Plan B | Plan A⟩ = 1/2.

That number — the overlap between two different pairing schemes of the
same system — is called a **recoupling coefficient**. You have just
computed your first one, by hand, with integer arithmetic. Note the
interference: the −1 terms partially canceled the +2. Note also the
geometry: normalized recipes are points on a unit sphere in pattern
space, overlap is the cosine of the angle between them, and cos⁻¹(1/2)
= 60°. Plan A and Plan B are sixty degrees apart.

One more, because it completes the physics. Plan B could instead pair
(b, c) at spin 0 (the antisymmetric option): Plan B′ = (↑↓↑ − ↑↑↓)
/sqrt(2) up to sign, and ⟨Plan B′|Plan A⟩ = sqrt(3)/2. Squares:
(1/2)² = 1/4 and (√3/2)² = 3/4, and 1/4 + 3/4 = 1. If the team was
built by Plan A and you measure "what is the (b,c) pair's spin?", you
get 1 with probability 1/4 and 0 with probability 3/4 — and the
probabilities exhaust certainty. Recoupling coefficients are how one
legitimate description distributes over another. That is their meaning.

> **Deep fact worth pausing on:** nothing moved, nothing pushed on
> anything. Pairing is *bookkeeping*, not interaction. Forces enter one
> door later: real interaction energies (like S₁·S₂ terms in magnets
> and atoms) happen to be *sharp* in one pairing's basis, which makes
> that pairing the natural description — and then the recoupling
> coefficient is the exact exchange rate between two natural
> descriptions of two different physical situations.

> **New jargon:** pattern room (the space of recipes), recoupling
> coefficient (overlap between two pairing schemes), pairing/coupling
> scheme.

---

## 5. Coupling trees and the 6j symbol

Bookkeeping for bigger systems needs notation. A **coupling tree** is a
diagram of pairing order: Plan A is ((a b) c) — pair a with b, then the
pair with c — and Plan B is (a (b c)). Each internal joint of the tree
carries an **intermediate spin** (the pair's total; 1 in our examples),
and the root carries the grand total.

For three spins, the recoupling coefficient between the two possible
trees can be written, for *any* spins j1, j2, j3 with intermediates and
total, as a dimension factor times one universal number:

    ⟨(j1,(j2 j3) at j23) J | ((j1 j2) at j12, j3) J⟩
        = (phase) · sqrt( (2·j12+1)(2·j23+1) ) · {j1 j2 j12; j3 J j23}

The object in curly braces is the **Wigner 6j symbol**: a pure number
depending on six spins, tabulated once and reused forever. It is the
irreducible atom of all recoupling. For our example, the machine
reports {1/2 1/2 1; 1/2 1/2 1} = 1/6, the dimension factor is
sqrt(3)·sqrt(3) = 3, the phase is +1, and 3 × 1/6 = 1/2 — the same
answer as our integer arithmetic, now factored into (convention-free
atom) × (bookkeeping). The sqrt(2j+1) factors are called **dimension
factors** because 2j+1 counts a family's members.

Why physicists revere this machinery: the **Wigner-Eckart theorem**
says that for any rotationally well-behaved quantity, all the
orientation-dependence of its measured values is carried by CG
coefficients — pure geometry — leaving one physics number per family.
Geometry factors out of dynamics. CG tables and 6j symbols are that
factored-out geometry.

**Scaling up.** Four spins have more trees, and comparing trees that
differ by more than one re-pairing produces sums: the recoupling
between ((j1 j2)(j3 j4)) and ((j1 j3)(j2 j4)) requires the **9j
symbol**, which is not a single 6j but a *weighted sum of products of
three 6j's* over one auxiliary spin x:

    {9j} = Σ_x (2x+1) (−1)^(2x) {6j}{6j}{6j}

(verified in this repository to ten decimal places on integer and
half-integer cases). And there is the crucial new word: **Σ (a
summation)**. As systems grow, recoupling coefficients become sums over
products of 6j's, and *how many nested summations survive* is what
makes a formula cheap or expensive to evaluate. Choosing the pairing
manipulations that minimize surviving summations is a genuine
optimization problem — the one this repository's solver performs, and
the subject of the companion (graphical) monograph.

> **New jargon:** coupling tree, intermediate spin, 6j symbol (the
> universal three-spin recoupling atom), dimension factor sqrt(2j+1),
> 9j symbol, summation cost.

---

## 6. Phases: the sign system, demystified

Everything above used real numbers, but many formulas sprout factors
like (−1)^(j1+j2+j3) or (−1)^(2j). Here is the complete mental model.

In full quantum mechanics an amplitude is a **clock hand**: a length
plus a dial angle. Combining amplitudes adds hands tip-to-tail; hands
pointing the same way reinforce, opposite hands cancel — interference,
again. A **phase** is a dial angle. In recoupling algebra with standard
conventions all final answers are real, so the dial is pinned to the
horizontal: **+1 (hand forward) or −1 (hand reversed)**. Intermediate
bookkeeping can visit the vertical stops ±i (quarter turns), which is
why this repository's phase engine stores exponents modulo 4 — four
stops on the dial — and asserts that every physically closed answer
lands back on the horizontal axis.

Where do the signs come from? Exactly two places, and keeping them
separate is the whole discipline:

**Structural signs** are forced by perpendicularity — the −1's in Plan
A exist because x + 2y = 0 has no all-positive solution. These are
physical: no convention can remove them, and their consequences (the
1/4 vs 3/4 split, interference patterns) are measurable.

**Conventional signs** encode a state's relationship to reference
choices: which direction is up, which slot order, which arrow
orientation. The strangest of these is genuinely deep: rotate the
laboratory one full turn (360°) and an integer-spin state returns to
itself, but a **half-integer-spin state returns with a minus sign** —
it needs 720° to come home. (Measured in the lab; this is real.) Every
factor (−1)^(2j) in every recoupling formula is that 720° fact
surfacing in the bookkeeping. Conventional signs shuffle when you
change conventions, and the point of a *phase engine* — like the one in
this repository, whose rules are "an odd reordering of a joint's three
spins costs (−1)^(their sum)" and "reversing a line's arrow costs
(−1)^(2j)" — is to track the shuffle so exactly that it cancels out of
every physical answer. The engine is a machine for keeping conventional
signs from contaminating structural physics.

> **New jargon:** phase (dial angle of an amplitude), the 720° fact
> ((−1)^(2j) under a full turn for half-integer spin), structural vs
> conventional signs.

---

## 7. The bra-ket dictionary (so you can read the literature)

Physicists write states in **Dirac notation**, and it encodes exactly
the ontology of this document. A **ket** |ψ⟩ is a noun — one recipe,
one point in state space; |Plan A⟩ *is* (2, −1, −1)/√6. A **bra** ⟨φ|
is the same object flipped into a question: "how much φ-ness?" Closing
a bra on a ket gives the **bracket** ⟨φ|ψ⟩ — the overlap, computed by
multiply-matching-and-add. (When amplitudes are complex clock hands,
forming the bra reverses every hand, which guarantees ⟨ψ|ψ⟩ is a real,
positive length². The dial explains the dagger.) Operators are verbs
acting on descriptions — the flip-down machine is the operator J−. And
note what the notation quietly insists: none of these are motions. A
ket does not travel; when time enters, the *description* rotates in
state space, each energy component's clock hand turning at its own
rate. Motion, when it occurs, is a pattern in how descriptions change.

---

## 8. Where this leads

You now own the complete conceptual stack: states are recipes;
families are built by the flip-down machine and separated by
perpendicularity; CG coefficients are the conversion table between
separate and total descriptions; recoupling coefficients are overlaps
between pairing schemes; the 6j symbol is their universal atom;
larger systems cost summations; and signs split cleanly into physics
and convention, with the 720° fact haunting every half-integer spin.

Two continuations. The **companion monograph** redoes all of this in
pictures — where states become graphs, algebra becomes surgery on
them, and "minimize the summations" becomes a search problem over
graph rewrites, culminating in a fifteen-spin coefficient reduced to
seven 6j's and three summations and verified against a brute-force sum
of 995,328 terms. And the **interactive animations** in this
repository's learn suite walk every derivation above with moving
parts, in the order this document did.

A closing provenance note, in this project's spirit: the numbers 1/2,
1/6, sqrt(3)/2, (2,−1,−1)/√6, and the 9j identity above were each
computed at least two independent ways — by explicit recipe arithmetic
and by separate library machinery — and agreed to at least nine decimal
places. Trust built on verification transfers. Trust built on authority
does not. Welcome to the craft.

---

## Glossary (in order of appearance)

- **spin** — a particle's built-in label for how its description
  responds to rotations; nothing physically rotates.
- **state** — a complete description of a system at an instant; a noun.
- **amplitude** — the amount of a basic pattern in a state's recipe;
  may be negative (or, in general, a complex clock hand).
- **normalized** — squares of a recipe's amounts total 1.
- **M** — sum of +1/2 per ↑ and −1/2 per ↓; conserved bookkeeping.
- **lowering operator (J−)** — the flip-down machine: visit each arrow,
  flip ↑ to ↓, add results.
- **overlap / inner product / bracket** — multiply matching amounts,
  add; measures similarity of two recipes; cosine of their angle.
- **perpendicular** — overlap zero.
- **symmetric / antisymmetric** — unchanged / sign-flipped under
  swapping two particles; corresponds to pair spin 1 / 0 for two
  spin-1/2's.
- **interference** — amplitudes adding or canceling by sign (or dial
  angle).
- **product basis / coupled basis** — describe-each-separately vs
  describe-by-totals coordinate systems.
- **Clebsch-Gordan coefficient** — an entry of the unitary conversion
  table between those bases.
- **coupling tree / pairing scheme** — the order in which particles are
  paired; each internal joint carries an intermediate spin.
- **recoupling coefficient** — the overlap between two pairing schemes
  of the same system.
- **6j symbol** — the universal, convention-free atom of three-spin
  recoupling.
- **dimension factor** — sqrt(2j+1); counts family members.
- **9j symbol** — the four-spin recoupling atom; a single-summation
  combination of three 6j's.
- **summation cost** — the number of surviving Σ's in a recoupling
  formula; the currency of the optimization problem.
- **phase** — an amplitude's dial angle; ±1 in this algebra's answers.
- **the 720° fact** — half-integer spins acquire (−1) under a 360°
  rotation; the origin of every (−1)^(2j).
- **ket / bra** — a state as noun / the same state as question.
