# Admissible bounds for the reduction search

The A* optimality guarantee is only as good as the heuristic's
admissibility. This document derives the bounds, states what is proved
and what is merely machine-certified, and marks the boundary of each.

Notation: `G` is a closed cubic multigraph on `n` vertices; the goal is
the theta graph (`n = 2`). Cost is `#6j + SUM_PENALTY * #sums`, with
`SUM_PENALTY = 10`.

## Lemma 0 (move accounting)

The three moves act on `n` and emit factors as follows:

| move | `n` | 6j | sums |
|---|---|---|---|
| bubble excision | `n - 2` | 0 | 0 |
| triangle contraction | `n - 2` | 1 | 0 |
| interchange (flip) | `n` | 1 | 1 |

Only bubbles and triangles change `n`, each by exactly 2, and the goal
has `n = 2`. So **every** complete reduction of `G` uses exactly
`(n-2)/2` vertex-removing moves, split into `B` bubbles and `T`
triangles, plus `S` flips:

    #6j  = T + S = (n-2)/2 - B + S
    cost = (n-2)/2 - B + (1 + SUM_PENALTY) * S

This identity reproduces all five benchmark costs exactly (tetrahedron
1, prism 2, K3,3 13, cube 14, Petersen 37), and it is what certifies
Petersen below.

**Consequence, and the origin of the v0.6.0 defect.** A lower bound on
cost requires an *upper* bound on `B`. The v0.6.0 heuristic used
`(n-2)/2` as its 6j term, which silently assumes `B = 0`. That is false
in general, so the heuristic was an over-estimate and A* was not
guaranteed optimal — on 58 of 80 reachable states with a computable
optimum (72.5%). See "The counterexamples".

## The shipped heuristic

    h(G) = 0  +  h_sum(G)

**Lemma 1 (summation bound). PROVEN.**

    h_sum(G) = SUM_PENALTY  if n > 2 and girth_lower(G) >= 4, else 0.

*Proof.* `Graph.girth_lower()` returns 2 if `bubbles()` is non-empty,
3 if `triangles()` is non-empty, and 4 otherwise — so `girth_lower(G)
>= 4` holds **exactly when** `G` has neither a bubble nor a triangle.
The move set is `{bubble excision, triangle contraction, interchange}`,
and the first two have those patterns as their guards. So no
vertex-removing move applies, and every move out of `G` is an
interchange. `n > 2` means `G` is not the goal, so a complete reduction
must make at least one move; that move is a flip, which emits one
summation. Hence `S >= 1` and `cost >= SUM_PENALTY`. If no move applies
at all, `G` is a dead end, `C*` is infinite, and any `h` is admissible.
∎

Note what the proof does **not** use: the girth of `G`. Despite its
name, `girth_lower()` computes no cycle length — it is a
move-availability predicate, and the bound rests only on that.

### Degenerate states need no special case here

This is why the summation term, unlike the decomposition bound, has no
trouble with self-loops and bridges.

A tadpole is a 1-cycle, so a self-loop state has true girth 1 — yet
`girth_lower()` reports 4 for it, because a self-loop `(u,u)` is not
counted by `bubbles()` (which looks for a *pair* of vertices joined by
two parallel edges). Such a state therefore **does** receive the
`SUM_PENALTY` bonus. That is correct: measured over the corpus, states
carrying a self-loop with no bubble and no triangle have flips as their
*only* successors, so `S >= 1` genuinely holds — e.g. an `n = 8`
instance with `C* = 13 >= 10`. The `n > 2` guard separately excludes the
theta-with-loops case, where `girth_lower()` is also 4 but the state is
already the goal (`C* = 0`).

**Trap for future work.** `girth_lower()` is *not* a valid lower bound
on girth: it returns 4 on states whose true girth is 1 or 2. It is sound
only as the move-availability predicate proved above. Any carving- or
branchwidth bound that wants an actual girth must compute one
(`girth_cycle()`), not reuse this function.

**The 6j term is 0.** Trivially a valid lower bound. This is a
deliberate choice of a smaller proven bound over a larger conjectured
one, and it is *free*: with `SUM_PENALTY = 10` the summation term
dominates, and on every benchmark plus random cubic graphs out to
`n = 14` the decomposition bound below yields identical costs **and
identical expanded-node counts**. A term that cannot change a single
search decision does not justify an unproven admissibility claim.

`h_sum` is weak — it returns `SUM_PENALTY` whether the true answer is
one flip or five, so it bounds Petersen at `S >= 1` against a certified
`S = 3`. Strengthening it is Finding 3.

## The k-line anchor and the 2-cut decomposition (opt-in)

In the k-line calculus a k-line separation of a closed diagram costs
`max(0, k-3)` summation variables: **2- and 3-line cuts are free.** The
free case `k = 2` is what governs `B`, because a bubble is precisely the
minimal 2-line cut: the two vertices of a bubble meet the rest of the
diagram in exactly two edges. Bubbles are not an independent phenomenon
to be discounted by inspection — they are creatures of 2-edge-cuts, so
the discount should be *derived* from the cut structure.

Split `G` along a 2-edge-cut `{e1, e2}` into `G_A` and `G_B`, where each
side keeps its internal edges plus **one** new edge joining its two
dangling stubs — exactly the rewiring `excise_bubble` performs. Repeat
until no 2-edge-cut remains, giving 3-edge-connected pieces `P_1..P_k`.

```mermaid
graph LR
  subgraph G["G  (n = 8, k = 2 pieces)  -- the two-diamond counterexample"]
    direction LR
    A0(( )) --- A1(( ))
    A1 --- A2(( ))
    A0 --- A2
    A0 --- A3(( ))
    A1 --- A3
    A2 -- "e1" --- B0(( ))
    A3 -- "e2" --- B1(( ))
    B0 --- B2(( ))
    B1 --- B2
    B0 --- B3(( ))
    B1 --- B3
    B2 --- B3
  end
```

Each split is size-preserving and lowers the running total by one, so

    Phi(G) := sum_i (n_i - 2)/2  =  (n-2)/2 - (k-1).

Equivalently the claim is `B <= (k-1) + S`.

### Why this is opt-in and not the default

The intended proof is a potential-function argument: `Phi(theta) = 0`,
so `Phi` bounds the 6j count provided

    Phi(G) <= Phi(G') + d6      for every move G -> G'.          (*)

Expanding `Phi = (n-2)/2 - (k-1)`, `(*)` reduces to three claims —
bubble: `k' = k-1` (holds by construction, a bubble *is* a size-2
piece); triangle: `k' <= k`; flip: `k' <= k+1`.

**`(*)` fails.** Measured over the corpus: **310 of 42,611 moves**
violate it. Every failure sits at a state carrying a **self-loop**
(a tadpole, which `excise_bubble` creates when a bubble's two external
stubs land on the same vertex) or a **bridge** (a 1-line cut). Such
pieces fall outside the decomposition argument and are scored 0, and a
move can then *relocate* the degeneracy between pieces: in the observed
case a flip took `[6 clean, 2 degenerate]` (`Phi = 2`) to
`[2 clean, 6 degenerate]` (`Phi = 0`), a drop of 2 for one 6j.

So the bound is **certified, not proven**:

- 0 violations of `Phi <= C*` over 80 states with computable optimum,
  tight on 54 — it is empirically admissible everywhere tested;
- but its proof has a hole at degenerate states, which is exactly the
  epistemic position that let v0.6.0 ship broken (that bound also
  passed every test it had).

Rejected repairs, both by machine rather than by argument:

- **discount self-loop vertices** (`n_eff = n_i - 2 * loops`): *directly
  inadmissible*, 6 violations of `h <= C*`. This was the intuitively
  appealing fix.
- **whole-graph gate** (any degeneracy anywhere ⇒ 0): admissible, but
  still 96 step violations — a clean state can move to a degenerate one
  and collapse `Phi`.

`sixj_bound_decomposition` is retained because it is the foundation for
the carving/branchwidth bound of Finding 3, where the degenerate cases
must be handled properly rather than scored 0. It is not wired into
`heuristic`.

## Petersen, certified

`optimal_cost` runs uniform-cost search (`h = 0`) over the **blind**
move set: no heuristic, no move restriction, so the answer rests on no
claim in this document except the cost model itself.

    C*(Petersen) = 37

By Lemma 0, `cost = (n-2)/2 - B + 11*S = 4 - B + 11*S`. A two-summation
reduction would cost at most `4 + 22 = 26 < 37`. Therefore **`S = 2` is
impossible: Petersen's minimum is three summations**, and the shipped
`7` 6j / `3` sum formula is optimal over the full move set — not merely
within the cycle-targeted class. Confirmed three ways: uniform-cost
(37), blind-move A* (37; 7 6j, 3 sums; 18 expansions), shipped targeted
A* (37; 11 expansions).

## The counterexamples

Both are pinned as named regression tests. Neither is producible by
`random_cubic`, which rejects parallel edges — which is why no test ever
surfaced them.

**1. Bubble counterexample** (`n = 4`, a multigraph state):

    (1,2,a) (1,2,b)  (3,4,c) (3,4,d)  (1,3,e) (2,4,f)

Excising bubble `(1,2)` joins the two external stubs into `(3,4,e)`,
landing directly on theta. `C* = 0`, but `h_old = (4-2)//2 = 1`.
Decomposition: two pieces of size 2, `Phi = 0`. Correct.

**2. Two-diamond counterexample** (`n = 8`, a *simple* graph — so
restricting attention to bubble-free simple states does not rescue the
old bound):

    two K4-minus-an-edge blocks joined by a 2-edge-cut

Contracting a diamond's triangle *births* a parallel pair; excising it
drops `n` by 4 for a single 6j. `C* = 2`, but `h_old = (8-2)//2 = 3`.
Decomposition: two pieces of size 4, `Phi = 1 + 1 = 2`. Correct, tight,
and diagrammed above.

## Certification record

Measured over the reachable-state corpus (BFS over the real blind move
set from the five benchmarks and random cubic `n = 8, 10, 12` seeds;
multigraph, self-loop and bridge states included), by
`scripts/certify_bounds.py`:

- Benchmarks re-certified against `h = 0` uniform-cost search over the
  blind move set: tetrahedron 1, prism 2, K3,3 13, cube 14,
  Petersen 37 — all equal to the v0.6.0 published costs. **The
  guarantee was void; the published results were nonetheless correct.**
- `h_old`: 58 of 80 states with computable `C*` violate `h <= C*`
  (72.5%).
- Shipped `h`: 0 admissibility violations, 0 step violations.
- Opt-in decomposition: 0 admissibility violations, tight on 54; 310
  step violations, all at degenerate states, 0 at clean states.
