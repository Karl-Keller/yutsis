# UML diagram set (v0.12.0)

Core structural views of the `yutsis` system, derived from the source
at `src/yutsis/` and rendered with Mermaid (GitHub renders these inline).
Four diagrams: **class**, **process/activity**, **sequence**, and
**state**.

A note on altitude: `yutsis` is a functional Python package, not a deep
class hierarchy. Only five real types carry state
(`Graph`, `OGraph`, `PhaseExpr`, `ClosedDiagram`, and the
`TruncatedEnumeration` exception); the reduction logic lives in
module-level functions. The class diagram therefore shows those five
types with their members, plus the collaborating modules as
`<<module>>` participants so the dependency structure is visible.

Two layers run in parallel and should be read together:

- **Structural layer** (`Graph`, `search`, `moves`, `bounds`,
  `patterns`) — searches the rewrite space for the *cheapest plan*. It
  never touches physics; a move is a topological pattern with a constant
  cost.
- **Exact/algebra layer** (`OGraph`, `replay`, `exact_moves`, `phase`,
  `oracle`, `circuits`) — *replays* that plan on the oriented diagram to
  emit signed algebra (6j symbols, phases, deltas), then checks it
  numerically.

---

## 1. Class diagram

```mermaid
classDiagram
    direction LR

    class Graph {
        +tuple edges
        +dict adj
        -_canon
        +n() int
        +bubbles() list
        +triangles() list
        +self_loops() list
        +excisable_loops() list
        +bridges() list
        +cuttable_bridges() list
        +components() list
        +component_graphs() list
        +girth_lower() int
        +true_girth() number
        +is_theta() bool
        +is_dumbbell() bool
        +is_terminal() bool
        +canonical() Any
    }

    class OGraph {
        +dict edges
        +dict verts
        +n() int
        +triangles() list
    }

    class PhaseExpr {
        +dict c
        +int k0
        +add_triad(labels) None
        +add_2j(lab) None
        +add_const(k) None
        +__mul__(other) PhaseExpr
        +evaluate(jmap) int
    }

    class ClosedDiagram {
        +dict edges
        +dict vertices
        +value() float
    }

    class TruncatedEnumeration {
        <<exception>>
    }
    RuntimeError <|-- TruncatedEnumeration

    Graph "1" o-- "1..*" Graph : component_graphs()
    OGraph "1" o-- "1..*" OGraph : og_components()

    class search {
        <<module>>
        +solve(g, greedy, blind) dict
        +optimal_cost(g) int
        +successors(g, blind) list
        +is_goal(g) bool
    }
    class moves {
        <<module>>
        +excise_bubble(g, pair) tuple
        +excise_loop(g, v) tuple
        +cut_bridge(g, lab) tuple
        +reduce_triangle(g, tri) tuple
        +interchanges(g) list
        +targeted_interchanges(g) list
    }
    class bounds {
        <<module>>
        +SUM_PENALTY int
        +heuristic(g) int
        +sum_bound(g) int
        +flip_free_reducible(g) bool
    }
    class patterns {
        <<module>>
        +enumerate_states(max_n, seeds) dict
        +build_table(states) dict
        +heuristic_with(table) Callable
        +save(table, path) None
        +load(path) dict
    }
    class replay {
        <<module>>
        +solve_exact(og, greedy) dict
        +replay(og, moves) dict
        +evaluate_expr(expr, jmap) float
    }
    class exact_moves {
        <<module>>
        +reduce_triangle_exact(og, tri) tuple
        +excise_bubble_exact(og, pair) tuple
        +excise_loop_exact(og, v) tuple
        +cut_bridge_exact(og, lab) tuple
        +interchange_exact(og, e, P, Q) tuple
        +dumbbell_factor(og) tuple
        +theta_sign(og) PhaseExpr
    }
    class phase {
        <<module>>
        +tetra_to_6j(edges, verts) tuple
        +prism_theorem() tuple
    }
    class oracle {
        <<module>>
        +theta(j1, j2, j3) ClosedDiagram
        +tetrahedron(args) ClosedDiagram
        +prism(args) ClosedDiagram
        +k33(args) ClosedDiagram
    }
    class circuits {
        <<module>>
        +recoupling_graph(t_ket, t_bra) OGraph
        +matrix_element(t_ket, t_bra, jmap) float
        +overlap_oracle(t_ket, t_bra, jmap) float
        +compile_recoupling(t_from, t_to, leaf_j, J) tuple
    }
    class benchmarks {
        <<module>>
        +tetrahedron() Graph
        +petersen() Graph
        +oriented_petersen() OGraph
    }

    search ..> Graph : nodes
    search ..> moves : generate children
    search ..> bounds : h(g)
    moves ..> Graph : build child
    bounds ..> Graph : reachability + canonical
    patterns ..> Graph : enumerate topologies
    patterns ..> search : optimal_cost as ground truth
    replay ..> search : structural plan
    replay ..> exact_moves : per-move algebra
    replay ..> PhaseExpr : accumulate sign
    exact_moves ..> OGraph : rewrite
    exact_moves ..> PhaseExpr : emit
    phase ..> PhaseExpr : build
    oracle ..> ClosedDiagram : build reference
    circuits ..> OGraph : recoupling graph
    circuits ..> oracle : cross-check
    benchmarks ..> Graph : fixtures
    benchmarks ..> OGraph : oriented fixtures
```

**Reading it.** `Graph` is the search node — a bare cubic multigraph
whose methods are all topological queries (pattern guards) plus
`canonical()` for deduplication. `component_graphs()` returns `Graph`
instances (a graph is a set of components), which is why bridge cutting
can split one node into several. `OGraph` is the oriented twin used only
in the exact layer; `PhaseExpr` is the running sign, multiplied move by
move. `ClosedDiagram` is the independent brute-force oracle.

---

## 2. Process / activity diagram

The full pipeline: search for a plan, then (optionally) replay it into
signed algebra and verify.

```mermaid
flowchart TD
    A["Input: cubic multigraph G"] --> B["A* init: push (w*h(G), 0, G, [], []); best = {canonical(G): 0}; w = 5 if greedy else 1"]
    B --> C{"open heap empty?"}
    C -- "yes" --> Z["return None"]
    C -- "no" --> D["pop lowest-f node (cost, cur, facs, descs)"]
    D --> E{"is_goal(cur)?<br/>every component theta or dumbbell"}
    E -- "yes" --> R["return {factors, moves, sixj, sums, cost, expanded, timeout:false}"]
    E -- "no" --> F{"expanded > max_expanded?"}
    F -- "yes" --> T["return {timeout: true}"]
    F -- "no" --> G["successors(cur, blind)"]
    G --> H{"any free move?<br/>bubble / loop / bridge / triangle"}
    H -- "yes" --> I["children = free moves<br/>bubble, loop, bridge: cost +0<br/>triangle: +1 6j"]
    H -- "no, and not blind" --> J["children = targeted or full interchanges<br/>flip: +1 6j, +1 sum (SUM_PENALTY)"]
    H -- "blind" --> J
    I --> K["for each child (ng, fac, d6, ds, desc)"]
    J --> K
    K --> L["nc = cost + d6 + SUM_PENALTY * ds"]
    L --> M{"canonical(ng) in best<br/>and best[key] <= nc?"}
    M -- "yes (duplicate, no better)" --> C
    M -- "no" --> N["best[key] = nc<br/>push (nc + w*h(ng), nc, ng, facs+[fac], descs+[desc])"]
    N --> C

    R --> P1["solve_exact: replay plan on OGraph"]
    P1 --> P2["for each move: *_exact(og, args) -> (og', PhaseExpr, factors); total_phase *= move_phase"]
    P2 --> P3["finalize each component: theta_sign() or dumbbell_factor()"]
    P3 --> P4["signed expression {phase, sixjs, sums, deltas, zeros, ...}"]
    P4 --> V["evaluate_expr(expr, jmap) and/or ClosedDiagram.value(): numeric cross-check to ~1e-9"]
```

**Key invariants.** Free moves (bubble/loop/bridge) cost nothing and
drop `n` by 2; a triangle costs one 6j; a flip costs one 6j **and** one
summation (`SUM_PENALTY = 10`). Flips are only generated when no free
move applies (the girth strategy) unless `blind=True`, which enumerates
the full flip set for optimality claims over the unrestricted move
class. The `best` map keyed by `canonical()` is the deduplication gate:
an isomorphic topology already reached at equal-or-lower cost is
dropped (sound by Lemma 3 — cost is an isomorphism invariant).

---

## 3. Sequence diagram — `solve_exact` end to end

The exact path wraps the structural `solve`, then replays and verifies.

```mermaid
sequenceDiagram
    autonumber
    actor U as caller
    participant RX as replay.solve_exact
    participant S as search.solve
    participant MV as moves
    participant B as bounds.heuristic
    participant G as Graph
    participant RP as replay.replay
    participant EX as exact_moves
    participant PH as PhaseExpr
    participant EV as replay.evaluate_expr

    U->>RX: solve_exact(og)
    RX->>S: solve(Graph(og.edges))

    loop A* until goal or timeout
        S->>S: pop lowest-f node
        S->>G: is_terminal()
        alt goal reached
            S-->>RX: {moves, factors, cost, sixj, sums}
        else expand node
            S->>MV: successors(cur, blind)
            MV->>G: build child graphs
            MV-->>S: [(ng, fac, d6, ds, desc)]
            loop each child
                S->>B: heuristic(ng)
                B->>G: flip_free_reducible / canonical
                B-->>S: h
                S->>G: canonical()
                S->>S: dedup gate, then push (nc + w*h)
            end
        end
    end

    RX->>RP: replay(og, moves)
    loop each move in the plan
        RP->>EX: bubble/loop/bridge/triangle/flip _exact(og, args)
        EX->>PH: build and multiply phase
        EX-->>RP: (og', PhaseExpr, factors)
    end
    RP->>EX: theta_sign / dumbbell_factor per component
    RP-->>RX: {phase, sixjs, sums, deltas, zeros, weights}
    RX-->>U: signed expression

    U->>EV: evaluate_expr(expr, jmap)
    EV-->>U: numeric value

    Note over U,EV: independently cross-checked against oracle.ClosedDiagram.value()
```

The two-layer split is visible: everything left of `replay.replay` is
pure topology (no j-labels, no signs); everything right of it is exact
algebra keyed off the plan `solve` produced.

---

## 4. State diagram — a diagram's reduction lifecycle

A search node is a `Graph` (possibly multi-component). Moves transition
it toward a terminal; the goal is a property of **every** component.

```mermaid
stateDiagram-v2
    [*] --> NonTerminal : input cubic multigraph (n>=3), canonicalized

    NonTerminal --> NonTerminal : excise_bubble / excise_loop  (free, n-2)
    NonTerminal --> NonTerminal : reduce_triangle  (+1 6j, n-2)
    NonTerminal --> NonTerminal : interchange / flip  (+1 6j, +1 sum, n unchanged)
    NonTerminal --> MultiComponent : cut_bridge  (free, n-2, splits diagram)

    MultiComponent --> MultiComponent : reduce each component independently
    MultiComponent --> Terminal : every component is Theta or Dumbbell

    NonTerminal --> Terminal : single component reduced to Theta

    state Terminal {
        Theta : 2 vertices, 3 parallel edges (true goal)
        Dumbbell : two tadpoles joined by a bridge (k=1 irreducible)
    }
    Terminal --> [*] : is_goal == is_terminal()

    note right of NonTerminal
        Flips fire only when no free move
        applies (default / girth strategy);
        blind=True enumerates all flips.
        Isomorphic states merge via
        canonical() (Lemma 3).
    end note
```

**The k=1 subtlety.** `cut_bridge` and `excise_loop` are the k=1 sector:
a single line crossing a cut must carry `j = 0`. A bridge cut is the
only transition that raises the component count, so `MultiComponent` is
reachable only through it. A `Dumbbell` (two tadpoles joined by a
bridge) is irreducible — capping it would leave a bare circle — so it is
an accepting terminal alongside the `Theta`. `is_goal` accepts iff every
component is one of the two.

---

## Regenerating / trusting these

These diagrams are hand-authored from the code at v0.12.0, not
machine-generated, so they can drift. The load-bearing facts to
re-check against source after any structural change:

- move cost signature `(graph, factor, d6, ds, desc)` and the cost
  formula `nc = cost + d6 + SUM_PENALTY*ds` (`search.solve`)
- terminal definition `is_terminal = all(theta or dumbbell)`
  (`graph.py`, `search.is_goal`)
- the flip-gating condition (`search.successors`)
- the five stateful types and their members (`graph`, `state`, `phase`,
  `oracle`, `patterns`)
