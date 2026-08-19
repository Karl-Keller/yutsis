# Measurement probes (session 23, v0.12.0)

Exploratory scripts kept for provenance and reuse. **These are not part
of CI** and carry no compatibility promise — they are the instruments
that produced the numbers in `docs/DEVLOG.md` (session 23),
`docs/BOUNDS.md` (Lemma 7) and PR #18, plus the follow-up probes that
came after that PR and are not yet reflected in any release.

Anything here that becomes load-bearing should graduate to `scripts/`
with tests, not be trusted in place.

## Tables are not committed

The pattern tables are build artifacts of 15-167 MB. Build them with
`scripts/build_patterns.py` and point the probes at them:

    python scripts/build_patterns.py --max-n 16 --cap 60000  --out tables/pdb16_shipped.pkl
    python scripts/build_patterns.py --max-n 18 --cap 500000 --budget 6000 --out tables/pdb18.pkl
    export YUTSIS_TABLES=$PWD/tables

Probes default to `scripts/probes/tables/` if `YUTSIS_TABLES` is unset.
The n<=18 build is ~2h 12m on one core and needs ~4 GB.

## What each probe established

| script | question | finding |
|---|---|---|
| `bench18.py` | four-arm payoff: shipped bound / n<=16 / n<=18 | reproduces the published v0.11.0 numbers exactly; `new16` == `ship16` row for row |
| `sweep2.py` | does `saved` stop decaying? | **no** — reports mean-of-ratios AND ratio-of-means because they disagree by 3x |
| `price.py` | load time, residency, wall clock at low hit rate | 0.10s load, 211 MB resident, no Lemma 6 reversal even at 3% hits |
| `profile_build.py` | where does the build spend time? | `canonical()` is 47% (Amdahl ceiling 1.9x); >half of that is pynauty marshalling, not nauty |
| `memprobe.py` | why did n=18 need 31 GB? | 360-byte certs materialised per edge, twice |
| `oracle_check.py` | is `build_table` exact above CI sizes? | agrees with `optimal_cost`; CI only covers n<=8 |
| `docaudit.py` | did a bulk edit mangle prose? | `ast.get_docstring` diff vs any git ref — the v0.8.2 failure mode |
| `wastar.py` | weighted A* + **frontier min-f** | a certified LOWER bound on `C*` when the search is cut off |
| `wastar_check.py` | is that wrapper trustworthy? | identical costs *and* expansions to `solve()` on 9 sizes + 3 benchmarks |
| `fallback.py` | does weighted search scale? | **no** — every arm walls at n=40; `h` is constant above the table's reach |
| `rollout.py` | does a queueless greedy descent scale? | **no** — cycles at n=40 |
| `rollout2.py` | does it scale with cycle memory? | **yes** — n=150 (225j) in 24 min; the wall was missing memory, not a barrier |

`results/` holds the raw output behind each claim, including
`closure_sweep_raw.json` (per-instance rows, so the aggregates can be
recomputed rather than taken on trust).

## Post-PR#18 findings, not yet in any release

1. **`greedy=True` is inert.** `sum_bound` returns a constant 10 on
   these states, so weighted best-first multiplies a constant and
   reorders nothing. It walls exactly where A* does (83 vs 88
   expansions at n=20; 1919 vs 1921 at n=30). Lemma 4's mechanism.
2. **There is no scale fallback in the shipped engine.** Every search
   arm fails at n>=40 (60j).
3. **A rollout with cycle memory reaches 225j.** Cost is +30% against
   the optimum where the optimum is known (179 vs 135 at n=30, 193 vs
   149 at n=36) and degrades beyond. The emitted formula is exact
   physics either way — only minimality is lost.
4. **Answers can be bracketed.** Frontier min-f gives a certified lower
   bound (>=125 at 60j) and a rollout gives an upper bound, so a
   non-optimal answer can be reported with its quality attached.

Caveat on 3: single seed per size. The session already paid once for
trusting a single-seed reading — see Lemma 7's measurement caveat.
