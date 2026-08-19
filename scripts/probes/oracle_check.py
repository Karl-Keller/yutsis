import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yutsis import benchmarks as B
from yutsis.patterns import build_table, enumerate_states
from yutsis.patterns import build_table as lean_build_table
from yutsis.search import optimal_cost


def rss():
    with open("/proc/self/statm") as f:
        return int(f.read().split()[1]) * os.sysconf("SC_PAGE_SIZE") / 1e6

SEEDS = [B.petersen(), B.cube(), B.k33(), B.prism(), B.tetrahedron()]
for n in (10, 12, 14):
    SEEDS += [B.random_cubic(n, seed=n * 77 + s) for s in range(10)]

for maxn in (10, 12, 14):
    st = enumerate_states(maxn, SEEDS, budget=600)
    a = rss()
    t0 = time.time()
    ref = build_table(st)
    t1 = time.time()
    b = rss()
    lean = lean_build_table(st)
    t2 = time.time()
    c = rss()
    same = ref == lean
    print(f"n<={maxn}: {len(st):>6} states  ref={len(ref):>6} lean={len(lean):>6}  "
          f"IDENTICAL={same}  ref {t1-t0:5.1f}s / lean {t2-t1:5.1f}s  "
          f"peak +{b-a:.0f}MB / +{c-b:.0f}MB", flush=True)
    if not same:
        diff = [k for k in set(ref) | set(lean) if ref.get(k) != lean.get(k)]
        print(f"   !! {len(diff)} disagreements, e.g. "
              f"{ref.get(diff[0])} vs {lean.get(diff[0])}")
        sys.exit(1)

# independent ground truth, not just self-consistency
st = enumerate_states(8, SEEDS, budget=120)
lean = lean_build_table(st)
checked = bad = 0
for cert, g in st.items():
    c = optimal_cost(g)
    if c is None:
        continue
    checked += 1
    if lean[cert] != c:
        bad += 1
print(f"lean vs optimal_cost: {checked} checked, {bad} mismatches")
sys.exit(1 if bad else 0)
