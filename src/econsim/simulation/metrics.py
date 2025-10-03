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
import statistics
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
    
    # Utility & Wealth Metrics (hash-excluded for determinism stability):
    _utility_history: List[List[float]] = field(default_factory=lambda: [])  # Per-step utility snapshots
    _wealth_distribution_history: List[Dict[str, Any]] = field(default_factory=lambda: [])  # Per-step wealth stats
    total_system_utility: float = 0.0
    avg_utility_per_agent: float = 0.0
    utility_variance: float = 0.0
    utility_gini_coefficient: float = 0.0
    utility_growth_rate: float = 0.0
    previous_total_utility: float = 0.0
    
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
        
        # Update utility & wealth metrics (hash-excluded)
        self._update_utility_metrics(step, sim)

    def _update_utility_metrics(self, step: int, sim: "Simulation") -> None:
        """Update utility and wealth distribution metrics for current step."""
        if not self.enabled:
            return
            
        # Calculate per-agent utilities
        agent_utilities = []
        agent_wealth_data = []
        
        for agent in sim.agents:
            utility = agent.current_utility()
            agent_utilities.append(utility)
            
            # Collect wealth data for distribution analysis
            carrying_total = sum(agent.carrying.values())
            home_total = sum(agent.home_inventory.values())
            total_wealth = carrying_total + home_total
            
            agent_wealth_data.append({
                'agent_id': agent.id,
                'utility': utility,
                'carrying_wealth': carrying_total,
                'home_wealth': home_total,
                'total_wealth': total_wealth,
                'preference_type': type(agent.preference).__name__
            })
        
        # Store utility snapshot
        self._utility_history.append(agent_utilities.copy())
        
        # Calculate aggregate statistics
        if agent_utilities:
            self.total_system_utility = sum(agent_utilities)
            self.avg_utility_per_agent = self.total_system_utility / len(agent_utilities)
            
            if len(agent_utilities) > 1:
                self.utility_variance = statistics.variance(agent_utilities)
                self.utility_gini_coefficient = self._calculate_gini_coefficient(agent_utilities)
            else:
                self.utility_variance = 0.0
                self.utility_gini_coefficient = 0.0
            
            # Calculate growth rate
            if self.previous_total_utility > 0:
                self.utility_growth_rate = (self.total_system_utility - self.previous_total_utility) / self.previous_total_utility
            else:
                self.utility_growth_rate = 0.0
            self.previous_total_utility = self.total_system_utility
        
        # Store wealth distribution data
        wealth_stats = {
            'step': step,
            'agent_count': len(agent_wealth_data),
            'total_system_utility': self.total_system_utility,
            'avg_utility': self.avg_utility_per_agent,
            'utility_variance': self.utility_variance,
            'utility_gini': self.utility_gini_coefficient,
            'utility_growth_rate': self.utility_growth_rate,
            'agents': agent_wealth_data
        }
        self._wealth_distribution_history.append(wealth_stats)
        
        # Keep only last 100 steps to prevent memory growth
        if len(self._utility_history) > 100:
            self._utility_history.pop(0)
        if len(self._wealth_distribution_history) > 100:
            self._wealth_distribution_history.pop(0)

    def _calculate_gini_coefficient(self, values: List[float]) -> float:
        """Calculate Gini coefficient for wealth/utility inequality measurement."""
        if len(values) <= 1:
            return 0.0
        
        # Sort values
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        # Calculate Gini coefficient using standard formula
        cumsum = 0.0
        for i, value in enumerate(sorted_values):
            cumsum += value * (2 * i - n + 1)
        
        mean_value = sum(sorted_values) / n
        if mean_value == 0:
            return 0.0
            
        gini = cumsum / (n * n * mean_value)
        return abs(gini)  # Ensure positive result

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

    def get_utility_stats(self) -> Dict[str, Any]:
        """Get current utility and wealth distribution statistics."""
        return {
            "total_system_utility": round(self.total_system_utility, 3),
            "avg_utility_per_agent": round(self.avg_utility_per_agent, 3),
            "utility_growth_rate": round(self.utility_growth_rate, 6),
            "utility_variance": round(self.utility_variance, 3),
            "utility_gini_coefficient": round(self.utility_gini_coefficient, 3)
        }
    
    def get_utility_history(self, steps: int = 10) -> List[List[float]]:
        """Get recent utility history for trend analysis."""
        return self._utility_history[-steps:]
    
    def get_wealth_distribution_history(self, steps: int = 10) -> List[Dict[str, Any]]:
        """Get recent wealth distribution data."""
        return self._wealth_distribution_history[-steps:]
    
    def get_utility_trend_slope(self, window: int = 10) -> float:
        """Calculate utility trend slope over recent window."""
        if len(self._utility_history) < 2:
            return 0.0
            
        recent_totals = []
        for step_utilities in self._utility_history[-window:]:
            recent_totals.append(sum(step_utilities))
        
        if len(recent_totals) < 2:
            return 0.0
            
        # Simple linear regression slope
        n = len(recent_totals)
        x_values = list(range(n))
        x_mean = sum(x_values) / n
        y_mean = sum(recent_totals) / n
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, recent_totals))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return 0.0
            
        return numerator / denominator


__all__ = ["MetricsCollector"]
