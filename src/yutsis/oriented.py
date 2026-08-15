"""Backwards-compatible re-export shim.

This module was split in v0.8.2 into:

    yutsis.state        OGraph, og_components
    yutsis.exact_moves  the exact, sign-carrying rewrite moves
    yutsis.replay       replay, solve_exact, evaluate_expr

and the oriented builders moved to yutsis.benchmarks. Nothing moved
changed: the split was pure code motion, verified byte-identical.

`import yutsis.oriented as O` keeps working, and remains the convenient
entry point for the exact layer. New code should prefer the specific
module.
"""
from __future__ import annotations

from .benchmarks import oriented_prism
from .exact_moves import (
                          FLIP_PHI,
                          cut_bridge_exact,
                          dumbbell_factor,
                          excise_bubble_exact,
                          excise_loop_exact,
                          interchange_exact,
                          reduce_prism_exact,
                          reduce_triangle_exact,
                          theta_sign,
)
from .replay import evaluate_expr, replay, solve_exact
from .state import OGraph, og_components

__all__ = ["OGraph", "og_components", "theta_sign", "reduce_triangle_exact",
           "excise_bubble_exact", "excise_loop_exact", "cut_bridge_exact",
           "dumbbell_factor", "interchange_exact", "FLIP_PHI",
           "oriented_prism", "reduce_prism_exact",
           "replay", "solve_exact", "evaluate_expr"]
