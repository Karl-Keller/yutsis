"""yutsis: optimal-form reduction of angular-momentum recoupling graphs.

A* search over the classical Yutsis rewrite rules, with a brute-force
magnetic-sum oracle (yutsis.oracle) as numerical ground truth.
"""
from . import benchmarks, bounds, circuits, oracle, oriented, phase
from .graph import Graph
from .search import SUM_PENALTY, heuristic, solve

__version__ = "0.8.3"
__all__ = ["Graph", "solve", "heuristic", "SUM_PENALTY",
           "benchmarks", "bounds", "circuits", "oracle", "oriented", "phase"]
