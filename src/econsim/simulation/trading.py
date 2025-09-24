"""Trading subsystem (Gate 7 – bilateral_simple).

Deterministic, flag-gated primitive allowing agents that co‑locate in the
same grid cell to exchange 1 unit of goods when the trade strictly
improves (or at minimum does not reduce) each agent's utility according
to marginal utility comparison of a potential swap.

Constraints / Invariants:
* O(agents) per step (single pass grouping by (x,y)).
* No new randomness; ordering keyed by ascending agent id.
* At most one successful trade per agent per step.
* Uses carrying inventory only (Gate 7 excludes aggregated ownership logic).

Future Extensions (not implemented here):
* Adjacency-based partner search (would require path ordering tie-breaks).
* Partner memory / bitmask to avoid re-trading same pair repeatedly.
* Money / price mediated trades (separate economy subsystem).
"""
from __future__ import annotations

from typing import Protocol, List, Dict, Tuple, Any

# --- Protocol -------------------------------------------------------------
class TradePolicy(Protocol):  # pragma: no cover - structural typing only
    def apply(self, simulation: Any) -> None: ...

# --- Helpers --------------------------------------------------------------

def _marginal_utility(agent: Any, good: str) -> float:
    """Return marginal utility of +1 unit of `good` for agent given current carrying.

    Gate 7 simplification: call agent.preference.utility on (g1+delta, g2) or (g1, g2+delta)
    treating carrying counts as the bundle. (Home inventory ignored in this mode.)
    """
    pref = getattr(agent, "preference", None)
    if pref is None or not hasattr(pref, "utility"):
        return 0.0
    carry = getattr(agent, "carrying", {})
    g1 = float(carry.get("good1", 0))
    g2 = float(carry.get("good2", 0))
    if good == "good1":
        return float(pref.utility((g1 + 1.0, g2))) - float(pref.utility((g1, g2)))  # type: ignore[arg-type]
    else:
        return float(pref.utility((g1, g2 + 1.0))) - float(pref.utility((g1, g2)))  # type: ignore[arg-type]

# --- Implementation -------------------------------------------------------
class SimpleCoLocationTradePolicy:
    """Co-location based bilateral trade policy.

    For each cell containing >=2 agents, consider agents in ascending id order
    and attempt a single swap of one unit of complementary goods if marginal
    utility signals oppose (one values good1 more; the other values good2 more).
    """

    def apply(self, simulation: Any) -> None:  # pragma: no cover (indirectly tested)
        agents = getattr(simulation, "agents", [])
        if not agents:
            return
        # Group agents by cell (x,y)
        buckets: Dict[Tuple[int, int], List[Any]] = {}
        for a in agents:  # original order preserved; will sort by id explicitly
            key = (int(getattr(a, "x", 0)), int(getattr(a, "y", 0)))
            buckets.setdefault(key, []).append(a)
        traded_this_tick: set[int] = set()
        for cell_agents in buckets.values():
            if len(cell_agents) < 2:
                continue
            cell_agents.sort(key=lambda ag: getattr(ag, "id", 0))
            # Pairwise linear scan; each agent can trade at most once
            for i in range(len(cell_agents) - 1):
                a = cell_agents[i]
                if getattr(a, "id", None) in traded_this_tick:
                    continue
                for j in range(i + 1, len(cell_agents)):
                    b = cell_agents[j]
                    if getattr(b, "id", None) in traded_this_tick:
                        continue
                    # Evaluate inventories
                    ac = getattr(a, "carrying", {})
                    bc = getattr(b, "carrying", {})
                    a_g1 = ac.get("good1", 0)
                    a_g2 = ac.get("good2", 0)
                    b_g1 = bc.get("good1", 0)
                    b_g2 = bc.get("good2", 0)
                    # Require each side to have at least one unit of the good they might give
                    if a_g1 <= 0 and a_g2 <= 0:
                        continue
                    if b_g1 <= 0 and b_g2 <= 0:
                        continue
                    # Marginal utilities
                    mu_a_g1 = _marginal_utility(a, "good1")
                    mu_a_g2 = _marginal_utility(a, "good2")
                    mu_b_g1 = _marginal_utility(b, "good1")
                    mu_b_g2 = _marginal_utility(b, "good2")
                    # Determine if a should give good1 and receive good2 or vice versa
                    # Trade pattern 1: a gives good1, b gives good2
                    if a_g1 > 0 and b_g2 > 0 and mu_a_g2 > mu_a_g1 and mu_b_g1 > mu_b_g2:
                        ac["good1"] = a_g1 - 1
                        ac["good2"] = a_g2 + 1
                        bc["good1"] = b_g1 + 1
                        bc["good2"] = b_g2 - 1
                        traded_this_tick.add(getattr(a, "id"))
                        traded_this_tick.add(getattr(b, "id"))
                        break  # move to next i
                    # Trade pattern 2: a gives good2, b gives good1
                    if a_g2 > 0 and b_g1 > 0 and mu_a_g1 > mu_a_g2 and mu_b_g2 > mu_b_g1:
                        ac["good1"] = a_g1 + 1
                        ac["good2"] = a_g2 - 1
                        bc["good1"] = b_g1 - 1
                        bc["good2"] = b_g2 + 1
                        traded_this_tick.add(getattr(a, "id"))
                        traded_this_tick.add(getattr(b, "id"))
                        break
        # End policy

__all__ = ["TradePolicy", "SimpleCoLocationTradePolicy"]
