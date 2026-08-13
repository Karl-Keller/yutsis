"""python -m yutsis : run the benchmark suite."""
from .benchmarks import tetrahedron, prism, k33, cube
from .search import solve

for name, g in [("tetrahedron (6j)", tetrahedron()),
                ("prism (separable)", prism()),
                ("K3,3 (9j core)", k33()),
                ("cube Q3 (12j class)", cube())]:
    r = solve(g)
    print(f"{name:22s} n={g.n}  ->  {r['sixj']} sixj, {r['sums']} sums, "
          f"cost={r['cost']}, expanded={r['expanded']}")
    for fa in r["factors"]:
        print("     ", fa)
    print()
