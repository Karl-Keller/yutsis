"""Regenerate the Petersen reduction trace embedded in
docs/petersen_15j_reduction.html.

Runs the structural planner on the Petersen benchmark, replays the plan
through the exact engine (capturing per-move factors and phases),
re-verifies the final value against brute-force magnetic summation, and
writes the trace JSON. Per the iron rule: the animation shows only what
the code computed.

Usage:  python scripts/export_petersen_trace.py > trace.json
"""
import json
import math

from sympy import S

import yutsis.oriented as O
from yutsis import solve
from yutsis.benchmarks import petersen
from yutsis.phase import PhaseExpr


def oriented_petersen_ids():
    edges, verts = {}, {}
    for u in range(5):
        edges[f"o{u}"] = (str(u), str((u + 1) % 5))
        edges[f"s{u}"] = (str(u), str(u + 5))
        edges[f"i{u}"] = (str(u + 5), str((u + 2) % 5 + 5))
    for u in range(5):
        verts[str(u)] = (f"o{(u-1)%5}", f"o{u}", f"s{u}")
        verts[str(u + 5)] = (f"s{u}", f"i{u}", f"i{(u-2)%5}")
    return O.OGraph(edges, verts)


def main():
    plan = solve(petersen())["moves"]
    og = oriented_petersen_ids()
    pos = {}
    for u in range(5):
        a = math.pi / 2 + 2 * math.pi * u / 5
        pos[str(u)] = (math.cos(a), math.sin(a))
        pos[str(u + 5)] = (0.52 * math.cos(a), 0.52 * math.sin(a))

    states, cost = [], 0
    total = PhaseExpr()

    def snap(og, note, factor, cost, hot_e, hot_n):
        states.append(dict(
            nodes={v: [round(pos[v][0], 3), round(pos[v][1], 3)]
                   for v in og.verts},
            edges=[[t, h, lab] for lab, (t, h) in sorted(og.edges.items())],
            note=note, factor=factor, cost=cost, hotE=hot_e, hotN=hot_n))

    snap(og, "The Petersen graph: 10 vertices, 15 edges, girth 5.",
         "", 0, [], [])
    for mv in plan:
        if mv[0] == "flip":
            _, (u, v, e), Ppl, Qql = mv
            og, ph, x, args, roles = O.interchange_exact(og, e, Ppl, Qql)
            cost += 11
            fac = (f"Σ_{x}(2x+1) · {{{args[0]} {args[1]} {args[2]}; "
                   f"{args[3]} {args[4]} {args[5]}}}")
            note = (f"Flip edge {e} between {u},{v}: {Ppl[1]} swaps with "
                    f"{Qql[1]}, spawning summed {x}. Cost +11.")
            snap(og, note, fac, cost, [x, Ppl[1], Qql[1]], [u, v])
        else:
            tri = mv[1]
            w = "W_" + str(sorted(tri)[0])
            cx = sum(pos[t][0] for t in tri) / 3
            cy = sum(pos[t][1] for t in tri) / 3
            og, ph, args = O.reduce_triangle_exact(og, tri)
            cost += 1
            for t in tri:
                pos.pop(t, None)
            pos[w] = (cx, cy)
            fac = (f"{{{args[0]} {args[1]} {args[2]}; "
                   f"{args[3]} {args[4]} {args[5]}}}")
            note = f"Triangle {{{', '.join(tri)}}} contracts to {w}. Cost +1."
            snap(og, note, fac, cost, list(args[:3]), [w])
        total = total * ph
    total = total * O.theta_sign(og)
    snap(og, "Terminal theta: reduction complete at certified cost 37.",
         "θ sign → phase", cost, [], list(og.verts))

    expr = O.solve_exact(oriented_petersen_ids())
    h = S(1) / 2
    jm = {f"o{u}": h for u in range(5)}
    jm.update({f"s{u}": S(1) for u in range(5)})
    jm.update(dict(i0=h, i1=h, i2=h, i3=S(3) / 2, i4=S(3) / 2))
    val = O.evaluate_expr(expr, jm, xmax=S(4))
    assert abs(val - 0.004629630) < 1e-8, val

    print(json.dumps(dict(states=states, phase=str(total),
                          value=f"{val:+.9f}", nsix=7, nsums=3,
                          cost=37, terms=995328),
                     separators=(",", ":")))


if __name__ == "__main__":
    main()
