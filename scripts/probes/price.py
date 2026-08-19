"""The costs a node-count table hides: load time, residency, and whether
a 5%-hit-rate lookup still pays on the clock. Serial, no pool."""
import os
import pickle
import time
from pathlib import Path

import yutsis.bounds as bd
import yutsis.search as S
from yutsis import benchmarks as B
from yutsis.patterns import heuristic_with

SP = os.environ.get("YUTSIS_TABLES",
                    str(Path(__file__).resolve().parent / "tables"))
def rss():
    with open("/proc/self/statm") as f:
        return int(f.read().split()[1]) * os.sysconf("SC_PAGE_SIZE") / 1e6

for name, path in (("n<=16", f"{SP}/pdb16_shipped.pkl"), ("n<=18", f"{SP}/pdb18.pkl")):
    a = rss()
    t0 = time.perf_counter()
    tab = pickle.load(open(path, "rb"))
    t1 = time.perf_counter()
    b = rss()
    print(f"{name}: {len(tab):>7} entries  load {t1-t0:6.2f}s  "
          f"resident {b-a:7.0f} MB  "
          f"on disk {os.path.getsize(path)/1e6:6.1f} MB", flush=True)
    del tab

tab = pickle.load(open(f"{SP}/pdb18.pkl", "rb"))
print(f"\n{'n':>3} {'seed':>5} {'base sec':>9} {'tab sec':>8} {'d_sec':>7} "
      f"{'base exp':>9} {'tab exp':>8} {'d_exp':>7} {'hit':>5}", flush=True)
for n in (26, 30, 32, 34, 36):
    for seed in (7 * n, 7 * n + 1):
        g = B.random_cubic(n, seed=seed)
        S.heuristic = bd.sum_bound
        t0 = time.perf_counter()
        rb = S.solve(g, max_expanded=300_000)
        tb = time.perf_counter() - t0
        st = {"c": 0, "h": 0}
        h0 = heuristic_with(tab, max_n=18)
        def h(gr, st=st):
            st["c"] += 1
            if gr.n <= 18 and gr.canonical() in tab:
                st["h"] += 1
            return h0(gr)
        S.heuristic = h
        t0 = time.perf_counter()
        rt = S.solve(g, max_expanded=300_000)
        tt = time.perf_counter() - t0
        if rb["timeout"] or rt["timeout"]:
            print(f"{n:>3} {seed:>5}   WALL", flush=True)
            continue
        assert rb["cost"] == rt["cost"], f"COST MISMATCH {rb['cost']} {rt['cost']}"
        print(f"{n:>3} {seed:>5} {tb:>9.2f} {tt:>8.2f} "
              f"{100*(tt-tb)/max(1e-9,tb):>6.0f}% "
              f"{rb['expanded']:>9} {rt['expanded']:>8} "
              f"{100*(rt['expanded']-rb['expanded'])/max(1,rb['expanded']):>6.0f}% "
              f"{100*st['h']/max(1,st['c']):>4.0f}%", flush=True)
