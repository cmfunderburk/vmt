"""Agent trading partner management and coordination.

HASH CONTRACT: This component manages trading state that participates in determinism hash:
- trade_partner_id, meeting_point, is_trading, trade_cooldown, partner_cooldowns
- The component itself is NOT serialized - only the state it manages
"""

from __future__ import annotations
from typing import Optional, Dict, List, Tuple, TYPE_CHECKING
from ..movement.utils import manhattan_distance, calculate_meeting_point
from ...constants import default_PERCEPTION_RADIUS

if TYPE_CHECKING:
    from ...agent import Agent

Position = tuple[int, int]

class TradingPartner:
    """Manages trading partner relationships, cooldowns, and meeting coordination."""
    
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
        self.trade_partner_id: Optional[int] = None
        self.meeting_point: Optional[Position] = None
        self.is_trading: bool = False
        self.trade_cooldown: int = 0
        self.partner_cooldowns: Dict[int, int] = {}
        
        # Stagnation tracking
        self.last_trade_mode_utility: float = 0.0
        self.trade_stagnation_steps: int = 0
    
    def find_nearby_agents(self, agent_pos: Position, all_agents: List["Agent"]) -> List[Tuple["Agent", int]]:
        """Find other agents within perception radius, sorted deterministically."""
        candidates = []
        for other_agent in all_agents:
            if other_agent.id == self.agent_id:
                continue
            
            distance = manhattan_distance(agent_pos[0], agent_pos[1], other_agent.x, other_agent.y)
            if distance <= default_PERCEPTION_RADIUS:
                candidates.append((other_agent, distance))
        
        # Deterministic sort: distance, then position
        candidates.sort(key=lambda x: (x[1], x[0].x, x[0].y))
        return candidates
    
    def can_pair_with(self, other_agent: "Agent") -> bool:
        """Check if pairing is allowed (no cooldowns, both available)."""
        if self.trade_cooldown > 0:
            return False
        if other_agent.id in self.partner_cooldowns:
            return False
        if self.trade_partner_id is not None:
            return False
        if other_agent._trading_partner.trade_partner_id is not None:
            return False
        return True
    
    def establish_pairing(self, agent_pos: Position, other_agent: "Agent") -> None:
        """
        Establish mutual pairing with deterministic ordering.
        Lower agent.id processes first.
        """
        meeting_point = calculate_meeting_point(agent_pos, (other_agent.x, other_agent.y))
        
        self.trade_partner_id = other_agent.id
        self.meeting_point = meeting_point
        
        other_agent._trading_partner.trade_partner_id = self.agent_id
        other_agent._trading_partner.meeting_point = meeting_point
    
    def end_trading_session(self, other_agent: "Agent") -> None:
        """End trading session with per-partner cooldowns."""
        # Set per-partner cooldown (20 steps)
        self.partner_cooldowns[other_agent.id] = 20
        other_agent._trading_partner.partner_cooldowns[self.agent_id] = 20
        
        # Clear state (general cooldown = 3)
        self.clear_trade_partner()
        other_agent._trading_partner.clear_trade_partner()
    
    def clear_trade_partner(self) -> None:
        """Clear trade partner state with general cooldown."""
        self.trade_partner_id = None
        self.meeting_point = None
        self.is_trading = False
        self.trade_cooldown = 3
    
    def update_cooldowns(self) -> None:
        """Decrement all cooldowns by 1."""
        if self.trade_cooldown > 0:
            self.trade_cooldown -= 1
        
        for partner_id in list(self.partner_cooldowns.keys()):
            self.partner_cooldowns[partner_id] -= 1
            if self.partner_cooldowns[partner_id] <= 0:
                del self.partner_cooldowns[partner_id]
    
    def can_trade_with_partner(self, partner_id: int) -> bool:
        """Check if this agent can trade with a specific partner (no active cooldown)."""
        return partner_id not in self.partner_cooldowns
