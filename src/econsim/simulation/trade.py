"""Trade intent structures (Gate Bilateral1 Phase 2 - Draft Enumeration).

Feature-flagged via environment variable `ECONSIM_TRADE_DRAFT=1`.
No state mutation or economic effect here; provides deterministic intent list
for future execution logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional
import os

from .agent import Agent
from econsim.preferences.helpers import marginal_utility

# Priority key structure for deterministic ordering:
# (-combined_delta_u, seller_id, buyer_id, give_type, take_type)
PriorityKey = Tuple[float, int, int, str, str]

# Minimum combined utility improvement required to keep/execute an intent.
# Filters out micro-swaps that cause oscillation and appear as ΔU=0.000 after rounding.
MIN_TRADE_DELTA = 1e-5


def _compute_exact_utility_delta(agent_i: Agent, agent_j: Agent, 
                                give_type: str, take_type: str) -> float:
    """Compute exact combined utility change from a trade.
    
    Args:
        agent_i: The agent giving 'give_type' and receiving 'take_type'
        agent_j: The agent giving 'take_type' and receiving 'give_type' 
        give_type: Good type that agent_i gives to agent_j
        take_type: Good type that agent_j gives to agent_i
        
    Returns:
        Combined utility delta (agent_i_after + agent_j_after - agent_i_before - agent_j_before)
    """
    # Current utility for both agents (based on total wealth: carrying + home)
    # Add small epsilon to avoid corner bundle issues with Cobb-Douglas
    EPSILON = 1e-12
    def total_bundle(agent: Agent) -> tuple[float, float]:
        carrying = agent.carrying
        home = agent.home_inventory
        good1_total = carrying.get("good1", 0) + home.get("good1", 0) + EPSILON
        good2_total = carrying.get("good2", 0) + home.get("good2", 0) + EPSILON
        return (float(good1_total), float(good2_total))
    
    bundle_i_before = total_bundle(agent_i)
    bundle_j_before = total_bundle(agent_j)
    
    utility_i_before = agent_i.preference.utility(bundle_i_before)
    utility_j_before = agent_j.preference.utility(bundle_j_before)
    
    # Post-trade bundles (simulate the 1-unit exchange)
    if give_type == "good1" and take_type == "good2":
        bundle_i_after = (bundle_i_before[0] - 1, bundle_i_before[1] + 1)
        bundle_j_after = (bundle_j_before[0] + 1, bundle_j_before[1] - 1)
    elif give_type == "good2" and take_type == "good1":
        bundle_i_after = (bundle_i_before[0] + 1, bundle_i_before[1] - 1)
        bundle_j_after = (bundle_j_before[0] - 1, bundle_j_before[1] + 1)
    else:
        # Unsupported trade types
        return 0.0
    
    # Ensure non-negative bundles (trade shouldn't create negative inventories)
    if any(x < 0 for x in bundle_i_after) or any(x < 0 for x in bundle_j_after):
        return 0.0
    
    utility_i_after = agent_i.preference.utility(bundle_i_after)
    utility_j_after = agent_j.preference.utility(bundle_j_after)
    
    return (utility_i_after + utility_j_after) - (utility_i_before + utility_j_before)


@dataclass(slots=True)
class TradeIntent:
    seller_id: int
    buyer_id: int
    give_type: str
    take_type: str
    quantity: int
    priority: PriorityKey
    # New (Gate Bilateral2 Phase 1): combined utility delta (buyer+seller) if executed (placeholder until integrated)
    delta_utility: float = 0.0

    def as_tuple(self) -> Tuple[int, int, str, str, int, PriorityKey]:
        return (
            self.seller_id,
            self.buyer_id,
            self.give_type,
            self.take_type,
            self.quantity,
            self.priority,
        )


def enumerate_intents_for_cell(agents: List[Agent]) -> List[TradeIntent]:
    """Generate trade intents among co-located agents.

    Phase 3 rule (marginal utility test): For each unordered pair (i,j) compute marginal utility
    dictionaries MU_i, MU_j over aggregated bundles (carrying+home). Produce intent (i gives g1, j gives g2)
    iff MU_i[g2] > MU_i[g1] AND MU_j[g1] > MU_j[g2] and each agent holds at least 1 unit (in carrying)
    of the good it would give. Likewise test the opposite direction. Quantity fixed at 1.

    Deterministic: no RNG; ordering enforced via priority tuple.
    """
    out: List[TradeIntent] = []
    n = len(agents)
    if n < 2:
        return out
    # Pre-compute marginal utilities
    mu_cache: dict[int, dict[str, float]] = {}
    for a in agents:
        mu_cache[a.id] = marginal_utility(
            a.preference,
            a.carrying,
            a.home_inventory,
            epsilon_lift=True,
            include_missing_two_goods=True,
        )
    use_delta_priority = os.environ.get("ECONSIM_TRADE_PRIORITY_DELTA") == "1"
    for i in range(n):
        ai = agents[i]
        mui = mu_cache.get(ai.id, {})
        for j in range(i + 1, n):
            aj = agents[j]
            muj = mu_cache.get(aj.id, {})
            # Direction: ai gives good1, aj gives good2
            if (
                ai.carrying.get("good1", 0) > 0
                and aj.carrying.get("good2", 0) > 0
                and mui.get("good2", 0.0) > mui.get("good1", 0.0)
                and muj.get("good1", 0.0) > muj.get("good2", 0.0)
            ):
                # Compute exact combined utility delta
                delta_u: float = _compute_exact_utility_delta(ai, aj, "good1", "good2")
                if delta_u >= MIN_TRADE_DELTA:
                    if use_delta_priority:
                        priority: PriorityKey = (-delta_u, ai.id, aj.id, "good1", "good2")
                    else:
                        priority = (0.0, ai.id, aj.id, "good1", "good2")
                    out.append(
                        TradeIntent(
                            seller_id=ai.id,
                            buyer_id=aj.id,
                            give_type="good1",
                            take_type="good2",
                            quantity=1,
                            priority=priority,
                            delta_utility=delta_u,
                        )
                    )
            # Opposite direction: ai gives good2, aj gives good1
            if (
                ai.carrying.get("good2", 0) > 0
                and aj.carrying.get("good1", 0) > 0
                and mui.get("good1", 0.0) > mui.get("good2", 0.0)
                and muj.get("good2", 0.0) > muj.get("good1", 0.0)
            ):
                delta_u = _compute_exact_utility_delta(ai, aj, "good2", "good1")
                if delta_u >= MIN_TRADE_DELTA:
                    if use_delta_priority:
                        priority: PriorityKey = (-delta_u, ai.id, aj.id, "good2", "good1")
                    else:
                        priority = (0.0, ai.id, aj.id, "good2", "good1")
                    out.append(
                        TradeIntent(
                            seller_id=ai.id,
                            buyer_id=aj.id,
                            give_type="good2",
                            take_type="good1",
                            quantity=1,
                            priority=priority,
                            delta_utility=delta_u,
                        )
                    )
    # Deterministic ordering (sort by priority tuple)
    out.sort(key=lambda t: t.priority)
    return out


__all__ = ["TradeIntent", "enumerate_intents_for_cell"]


def execute_single_intent(intents: List[TradeIntent], agents_by_id: dict[int, Agent]) -> Optional[TradeIntent]:
    """Execute the first viable intent (already priority-sorted) if inventories allow.

    Viability rules (Phase 3 minimal):
    - Seller must have at least 1 unit of give_type in carrying.
    - Buyer must have at least 1 unit of take_type in carrying.
    - Swap: seller give_type -1, buyer +1; buyer take_type -1, seller +1.
    - Home inventory untouched (carrying-only invariant).

    Returns the executed intent or None if none applied. Does not mutate the intents list.
    Deterministic: linear scan in given order.
    """
    for intent in intents:
        seller = agents_by_id.get(intent.seller_id)
        buyer = agents_by_id.get(intent.buyer_id)
        if seller is None or buyer is None:
            continue
        if seller.carrying.get(intent.give_type, 0) <= 0:
            continue
        if buyer.carrying.get(intent.take_type, 0) <= 0:
            continue
        # Perform swap (normal execution). Hash neutrality (if desired) is handled by restoration
        # logic in Simulation.step when ECONSIM_TRADE_HASH_NEUTRAL=1.
        seller.carrying[intent.give_type] -= 1
        buyer.carrying[intent.give_type] = buyer.carrying.get(intent.give_type, 0) + 1
        buyer.carrying[intent.take_type] -= 1
        seller.carrying[intent.take_type] = seller.carrying.get(intent.take_type, 0) + 1
        return intent
    return None

__all__.append("execute_single_intent")
