"""yutsis: optimal-form reduction of angular-momentum recoupling graphs.

A* search over the classical Yutsis rewrite rules, with a brute-force
magnetic-sum oracle (yutsis.oracle) as numerical ground truth.
"""
from .graph import Graph
from .search import solve, heuristic, SUM_PENALTY
from . import benchmarks, oracle, phase, oriented, circuits

__version__ = "0.6.0"
__all__ = ["Graph", "solve", "heuristic", "SUM_PENALTY", "benchmarks", "oracle", "phase"]
