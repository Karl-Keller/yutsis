import random, time
from yutsis import Graph, solve

def random_cubic(n, seed):
    rng = random.Random(seed)
    while True:
        stubs = [v for v in range(n) for _ in range(3)]
        rng.shuffle(stubs)
        edges = [(stubs[i], stubs[i+1]) for i in range(0, len(stubs), 2)]
        if any(u == v for u, v in edges): continue
        if len({tuple(sorted(e)) for e in edges}) != len(edges): continue
        adj = {v: set() for v in range(n)}
        for u, v in edges: adj[u].add(v); adj[v].add(u)
        seen, stack = {0}, [0]
        while stack:
            for w in adj[stack.pop()]:
                if w not in seen: seen.add(w); stack.append(w)
        if len(seen) == n:
            return Graph([(u, v, f"j{i}") for i, (u, v) in enumerate(edges)])

def petersen():
    e, i = [], 0
    for u in range(5):
        e.append((u, (u+1) % 5, f"o{u}")); e.append((u, u+5, f"s{u}"))
        e.append((u+5, (u+2) % 5 + 5, f"i{u}"))
    return Graph(e)

print(f"{'graph':24s} {'n':>3s} {'girth>=':>7s} {'sixj':>5s} {'sums':>5s} {'cost':>5s} {'expanded':>9s} {'sec':>7s}")
tests = [("petersen (girth 5)", petersen())]
for n in (8, 10, 12, 14):
    tests.append((f"random cubic n={n}", random_cubic(n, seed=n * 7)))
for name, g in tests:
    t0 = time.time()
    r = solve(g)
    dt = time.time() - t0
    print(f"{name:24s} {g.n:>3d} {g.girth_lower():>7d} {r['sixj']:>5d} {r['sums']:>5d} "
          f"{r['cost']:>5d} {r['expanded']:>9d} {dt:>7.2f}")
