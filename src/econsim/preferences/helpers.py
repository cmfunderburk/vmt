"""Helper utilities for preference-based economic calculations (Gate Bilateral1 Phase 1).

Currently exposes marginal_utility() to support future bilateral trade heuristics.
Design goals:
* Deterministic ordering of returned goods
* Pure function (no mutation of inputs or preference state)
* O(k) where k = number of distinct goods observed (currently fixed 2)
* Zero allocations avoided beyond tiny dict (acceptable scale)

Note: Uses carrying+home aggregate to reflect total wealth context while
trade operations will remain restricted to *carrying* inventory.
"""
from __future__ import annotations

from collections import Counter
from typing import Mapping, Dict

from econsim.simulation.agent import EPSILON_UTILITY  # reuse existing constant for determinism

from .base import Preference


def marginal_utility(
    preference: Preference,
    carrying: Mapping[str, int],
    home: Mapping[str, int],
    *,
    epsilon_lift: bool = False,
    include_missing_two_goods: bool = False,
) -> Dict[str, float]:
    """Compute approximate marginal utility for +1 unit of each observed good.

    Implementation: finite difference U(bundle + e_i) - U(bundle) where bundle is
    aggregate of carrying + home. For goods not present, we do not invent a baseline
    entry—only compute deltas for encountered keys to maintain determinism and
    avoid speculative proliferation.

    Determinism: keys sorted lexicographically in output.
    """
    # Merge counts (Counter addition preserves integer semantics)
    merged = Counter(carrying) + Counter(home)
    if not merged:
        return {}
    # Build a stable snapshot list of goods
    if include_missing_two_goods:
        goods = sorted(set(merged.keys()).union({"good1", "good2"}))
    else:
        goods = sorted(merged.keys())
    # Base utility once (preference expected pure)
    # Current preference interface expects a 2-good bundle (x,y); future generalization may adapt.
    # Map 'good1'/'good2' if present, else treat missing as 0.
    x = float(merged.get("good1", 0))
    y = float(merged.get("good2", 0))
    if epsilon_lift and (x == 0.0 or y == 0.0):
        # Lift both goods to epsilon for baseline; preserves relative comparisons and avoids zero utility plateau.
        x = x + EPSILON_UTILITY
        y = y + EPSILON_UTILITY
    base = preference.utility((x, y))  # type: ignore[arg-type]
    out: Dict[str, float] = {}
    for g in goods:
        if g == "good1":
            nx = x + 1.0
            ny = y
            if epsilon_lift and (nx == 0.0 or ny == 0.0):  # guard not strictly needed but symmetric
                nx = nx + EPSILON_UTILITY
                ny = ny + EPSILON_UTILITY
            new = preference.utility((nx, ny))  # type: ignore[arg-type]
        elif g == "good2":
            nx = x
            ny = y + 1.0
            if epsilon_lift and (nx == 0.0 or ny == 0.0):
                nx = nx + EPSILON_UTILITY
                ny = ny + EPSILON_UTILITY
            new = preference.utility((nx, ny))  # type: ignore[arg-type]
        else:
            # Unknown goods (future extension) -> skip to keep output stable & conservative
            continue
        out[g] = new - base
    return out


__all__ = ["marginal_utility"]
