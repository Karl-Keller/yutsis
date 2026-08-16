"""Rung two of the flip-count ladder, and why it is not shipped.

Kept as the reproducible evidence for Lemma 6 (docs/BOUNDS.md):
both forms are admissible and cut real nodes, and both LOSE badly
in wall clock, because evaluating the bound costs more than the
search it saves.

    correct form  12-35% node cut, 10x-23x SLOWER
    cheap form     4-19% node cut, 1.3x-6x SLOWER

Run the comparison with scripts/headroom.py after swapping
yutsis.bounds.sum_bound for one of these.
"""

from yutsis.bounds import _flip_free_children, flip_free_reducible
from yutsis.moves import interchanges

_FREE_REACH_CACHE = {}
_ONE_FLIP_CACHE = {}


def free_reach(g):
    """Every state reachable using no flip, g included."""
    cert = g.canonical()
    hit = _FREE_REACH_CACHE.get(cert)
    if hit is not None:
        return hit
    out, seen, stack = [], {cert}, [g]
    while stack:
        cur = stack.pop()
        out.append(cur)
        for c in _flip_free_children(cur):
            k = c.canonical()
            if k not in seen:
                seen.add(k)
                stack.append(c)
    _FREE_REACH_CACHE[cert] = out
    return out


def one_flip_suffices(g):
    """Can g reach a terminal using exactly one flip?"""
    cert = g.canonical()
    hit = _ONE_FLIP_CACHE.get(cert)
    if hit is not None:
        return hit
    result = False
    for h in free_reach(g):
        for child, *_rest in interchanges(h):
            if flip_free_reducible(child):
                result = True
                break
        if result:
            break
    _ONE_FLIP_CACHE[cert] = result
    return result


def sum_bound_rung2(g, penalty=10):
    if g.is_terminal():
        return 0
    if flip_free_reducible(g):
        return 0
    return penalty if one_flip_suffices(g) else 2 * penalty


_CHEAP_CACHE = {}


def sum_bound_rung2_cheap(g, penalty=10):
    """Rung two restricted to states with NO free move available.

    There FreeReach(g) = {g}, so quantifying over g's own flip children
    is sound -- no reduction can slip a free move in first. Costs 4|E|
    reducibility tests, and only on the rare states that qualify."""
    if g.is_terminal():
        return 0
    if flip_free_reducible(g):
        return 0
    if _flip_free_children(g):
        return penalty                 # free move exists: rung one only
    cert = g.canonical()
    hit = _CHEAP_CACHE.get(cert)
    if hit is None:
        hit = any(flip_free_reducible(c) for c, *_ in interchanges(g))
        _CHEAP_CACHE[cert] = hit
    return penalty if hit else 2 * penalty
