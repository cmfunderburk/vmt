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
            # Pre-compute a simplistic combined marginal improvement estimate for each potential direction.
            # NOTE: We use marginal utility difference (desired - offered) per agent and sum; this is *not* yet
            # the full preference utility re-evaluation (keeps constant time & avoids allocations). A later
            # gate may tighten this to exact utility delta.
            # Direction: ai gives good1, aj gives good2
            if (
                ai.carrying.get("good1", 0) > 0
                and aj.carrying.get("good2", 0) > 0
                and mui.get("good2", 0.0) > mui.get("good1", 0.0)
                and muj.get("good1", 0.0) > muj.get("good2", 0.0)
            ):
                # Combined marginal lift approximation
                delta_u: float = (mui.get("good2", 0.0) - mui.get("good1", 0.0)) + (muj.get("good1", 0.0) - muj.get("good2", 0.0))
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
                delta_u = (mui.get("good1", 0.0) - mui.get("good2", 0.0)) + (muj.get("good2", 0.0) - muj.get("good1", 0.0))
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
        # Perform swap
        seller.carrying[intent.give_type] -= 1
        buyer.carrying[intent.give_type] = buyer.carrying.get(intent.give_type, 0) + 1
        buyer.carrying[intent.take_type] -= 1
        seller.carrying[intent.take_type] = seller.carrying.get(intent.take_type, 0) + 1
        return intent
    return None

__all__.append("execute_single_intent")
