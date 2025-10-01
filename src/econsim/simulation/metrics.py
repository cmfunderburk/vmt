"""Per-step simulation metrics and bilateral trading analytics.

Collects aggregate inventory counts and maintains a determinism hash for
regression testing. Also tracks bilateral trading statistics including
per-agent trade histories and utility gains.

Capabilities:
* Streaming SHA256 hash sensitive to agent state and resource layout
* Per-step aggregate records (inventory totals, resource counts)  
* Bilateral trade tracking with rolling per-agent histories
* Utility gain aggregation and fairness metrics

Future Enhancements:
* Derived economic indicators and inequality metrics
* Granular metric enable/disable controls
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any, Iterable, List, Dict, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .world import Simulation


@dataclass(slots=True)
class MetricsCollector:
    """Dual-purpose metrics collector for determinism verification and trading analytics.
    
    Maintains a streaming SHA256 hash for regression testing and tracks bilateral
    trading statistics including per-agent histories and utility measurements.
    """

    enabled: bool = True
    
    # Trading metrics (hash-excluded for determinism stability):
    trade_intents_generated: int = 0
    trades_executed: int = 0
    realized_utility_gain_total: float = 0.0
    trade_ticks: int = 0
    no_trade_ticks: int = 0
    last_executed_trade: dict[str, object] | None = None  # {seller,buyer,give,take,delta_utility,step}
    fairness_round: int = 0  # Increments per executed trade (advisory metric)
    agent_trade_histories: Dict[int, List[Dict[str, Any]]] = field(default_factory=lambda: {})  # Rolling history (last 5 trades per agent)
    
    # Determinism tracking (hash-included):
    _records: List[Dict[str, Any]] = field(default_factory=lambda: [])
    _hash: Any | None = field(default=None, init=False, repr=False)  # sha256 object

    def __post_init__(self) -> None:
        """Initialize SHA256 hash for determinism tracking."""
        self._hash = hashlib.sha256()

    def _update_hash(self, payload: str) -> None:
        """Update determinism hash with canonical simulation state."""
        if self._hash is not None:
            self._hash.update(payload.encode())

    def record(self, step: int, sim: "Simulation") -> None:
        """Record per-step metrics and update determinism hash."""
        if not self.enabled or self._hash is None:
            return

        # Aggregate metrics
        agent_count = len(sim.agents)
        resource_count = sim.grid.resource_count()

        total_carrying_good1 = 0
        total_carrying_good2 = 0
        total_home_good1 = 0
        total_home_good2 = 0

        agent_snap: list[tuple[int, int, int, int, int, int]] = []
        # (id,x,y,cg1,cg2,hg1,hg2) but keep tuple small; combine some
        for a in sim.agents:
            cg1 = a.carrying.get("good1", 0)
            cg2 = a.carrying.get("good2", 0)
            hg1 = a.home_inventory.get("good1", 0)
            hg2 = a.home_inventory.get("good2", 0)
            total_carrying_good1 += cg1
            total_carrying_good2 += cg2
            total_home_good1 += hg1
            total_home_good2 += hg2
            agent_snap.append((a.id, a.x, a.y, cg1, cg2, hg1 + hg2))

        entry = {
            "step": step,
            "agents": agent_count,
            "resources": resource_count,
            "carry_g1": total_carrying_good1,
            "carry_g2": total_carrying_good2,
            "home_g1": total_home_good1,
            "home_g2": total_home_good2,
        }
        self._records.append(entry)

        # Canonical serialization for hash: step|agent_count|resource_count|sorted(agent tuples)|sorted(resources)
        # Resources already have a stable order via serialize()
        resource_serial = sim.grid.serialize()["resources"]  # list[(x,y,type)] sorted
        agent_snap.sort()  # sort by id, then position
        # Build a compact string
        comp = [
            f"s={step}",
            f"ac={agent_count}",
            f"rc={resource_count}",
            "A=" + ";".join(
                f"{i},{x},{y},{c1},{c2},{h}" for (i, x, y, c1, c2, h) in agent_snap
            ),
            "R=" + ";".join(f"{x},{y},{t}" for (x, y, t) in resource_serial),
        ]
        payload = "|".join(comp)
        self._update_hash(payload)

    def determinism_hash(self) -> str:
        """Return current SHA256 hash digest for regression testing."""
        if self._hash is None:
            return ""
        return self._hash.hexdigest()

    def records(self) -> Iterable[Dict[str, Any]]:
        """Return immutable view of per-step aggregate records."""
        return tuple(self._records)

    def record_bilateral_trade(self, step: int, agent1_id: int, agent2_id: int, 
                               agent1_give: str, agent1_take: str, 
                               agent1_delta_u: float, agent2_delta_u: float) -> None:
        """Record trade in per-agent histories without updating global counters.
        
        Maintains rolling history (last 5 trades) per agent and updates last_executed_trade.
        Called by register_executed_trade to avoid double-counting.
        """
        # Create trade records for both agents
        trade_record_1: Dict[str, Any] = {
            "step": step,
            "partner_id": agent2_id,
            "gave": agent1_give,
            "received": agent1_take,
            "delta_utility": agent1_delta_u,
            "role": "trader"
        }
        
        trade_record_2: Dict[str, Any] = {
            "step": step,
            "partner_id": agent1_id,
            "gave": agent1_take,  # What agent1 took is what agent2 gave
            "received": agent1_give,  # What agent1 gave is what agent2 received
            "delta_utility": agent2_delta_u,
            "role": "trader"
        }
        
        # Add to agent1's history
        if agent1_id not in self.agent_trade_histories:
            self.agent_trade_histories[agent1_id] = []
        self.agent_trade_histories[agent1_id].append(trade_record_1)
        if len(self.agent_trade_histories[agent1_id]) > 5:
            self.agent_trade_histories[agent1_id].pop(0)  # Keep only last 5
            
        # Add to agent2's history  
        if agent2_id not in self.agent_trade_histories:
            self.agent_trade_histories[agent2_id] = []
        self.agent_trade_histories[agent2_id].append(trade_record_2)
        if len(self.agent_trade_histories[agent2_id]) > 5:
            self.agent_trade_histories[agent2_id].pop(0)  # Keep only last 5
        
        # Update global last trade (for backward compatibility)
        self.last_executed_trade = {
            "step": step,
            "seller": agent1_id,
            "buyer": agent2_id,
            "give_type": agent1_give,
            "take_type": agent1_take,
            "delta_utility": agent1_delta_u,
        }
        
    def register_executed_trade(self, *, step: int, agent1_id: int, agent2_id: int,
                                agent1_give: str, agent1_take: str,
                                agent1_delta_u: float, agent2_delta_u: float,
                                realized_utility_gain: float | None = None) -> None:
        """Register completed bilateral trade with full metrics tracking.
        
        Updates global counters, utility totals, and delegates to record_bilateral_trade
        for per-agent history tracking. Single entry point prevents double-counting.
        
        Args:
            step: Current simulation step
            agent1_id, agent2_id: Trading partners (agent1 = seller in current model)
            agent1_give, agent1_take: Resource types exchanged
            agent1_delta_u, agent2_delta_u: Utility changes for each agent
            realized_utility_gain: Optional explicit utility gain (defaults to agent1_delta_u)
        """
        # Counters
        self.trades_executed += 1
        self.trade_ticks += 1
        # Fairness advisory metric (one increment per executed trade)
        try:
            self.fairness_round += 1
        except Exception:  # pragma: no cover - defensive
            pass
        # Realized utility aggregation (always enabled for economic coherence)
        try:
            gain = realized_utility_gain
            if gain is None:
                gain = float(agent1_delta_u)
            self.realized_utility_gain_total += float(gain)
        except Exception:  # pragma: no cover
            pass
        # Delegate to history recorder (no counters inside)
        self.record_bilateral_trade(
            step=step,
            agent1_id=agent1_id,
            agent2_id=agent2_id,
            agent1_give=agent1_give,
            agent1_take=agent1_take,
            agent1_delta_u=agent1_delta_u,
            agent2_delta_u=agent2_delta_u,
        )


__all__ = ["MetricsCollector"]
