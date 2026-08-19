"""Where do the 130 KB/state go? Fixable representation, or intrinsic?"""
import os
import pickle
import sys

from yutsis import benchmarks as B
from yutsis.patterns import enumerate_states
from yutsis.search import successors


def rss():
    with open("/proc/self/statm") as f:
        return int(f.read().split()[1]) * os.sysconf("SC_PAGE_SIZE") / 1e6

g = B.random_cubic(18, seed=7*18)
cert = g.canonical()
_n = len(cert) if hasattr(cert, "__len__") else "-"
print(f"cert type={type(cert).__name__} len={_n}")
print(f"cert repr head: {repr(cert)[:160]}")
print(f"sys.getsizeof(cert) = {sys.getsizeof(cert)} B")
print(f"pickled Graph      = {len(pickle.dumps(g))} B")
print(f"pickled cert       = {len(pickle.dumps(cert))} B")
print(f"successors(blind)  = {len(list(successors(g, blind=True)))} per state")
print(f"Graph __dict__ keys: {list(vars(g))[:12]}")
for k, v in vars(g).items():
    print(f"   {k:>14}: {type(v).__name__:>12} size~{len(pickle.dumps(v))} B")

base = rss()
st = enumerate_states(14, [B.petersen(), B.cube(), B.k33()], cap=6000, budget=120)
after = rss()
print(f"\nenumerate n<=14: {len(st)} states, RSS +{after-base:.0f} MB "
      f"=> {(after-base)*1e3/max(1,len(st)):.1f} KB/state (states dict only)")
