"""Full Petersen 15j verification: solve_exact's signed formula vs
brute-force oracle on a nonzero labeling (outer 1/2, spokes 1, inner
(1/2,1/2,1/2,3/2,3/2)). ~1M oracle terms; run before releases."""
import time
from sympy import S
import yutsis.oriented as O
from yutsis.benchmarks import oriented_petersen
from yutsis.oracle import ClosedDiagram


og = oriented_petersen()
expr = O.solve_exact(og)
print(f"{len(expr['sixjs'])} sixj, {len(expr['sums'])} sums, phase={expr['phase']}")
h = S(1) / 2
jm = {f"o{u}": h for u in range(5)}
jm.update({f"s{u}": S(1) for u in range(5)})
jm.update(dict(i0=h, i1=h, i2=h, i3=S(3)/2, i4=S(3)/2))
ve = O.evaluate_expr(expr, jm, xmax=S(4))
t0 = time.time()
vo = ClosedDiagram({lab: (t, hh, jm[lab]) for lab, (t, hh) in og.edges.items()},
                   og.verts).value()
assert abs(ve - vo) < 1e-8, (ve, vo)
print(f"expression {ve:+.9f} == oracle {vo:+.9f}  ({time.time()-t0:.0f}s)  MATCH")
