"""Where does the build actually spend its time? Amdahl before CUDA."""
import cProfile
import io
import pstats

from yutsis import benchmarks as B
from yutsis.patterns import enumerate_states

SEEDS = [B.petersen(), B.cube(), B.k33(), B.prism(), B.tetrahedron()]
for n in (10, 12, 14):
    SEEDS += [B.random_cubic(n, seed=n * 77 + s) for s in range(10)]

pr = cProfile.Profile()
pr.enable()
st = enumerate_states(14, SEEDS, budget=300)
pr.disable()
s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats("tottime")
ps.print_stats(14)
print(f"states: {len(st)}")
print(s.getvalue()[:3000])
