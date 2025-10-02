"""Unit tests for TradingPartner component."""

import pytest
from unittest.mock import Mock
from src.econsim.simulation.components.trading_partner import TradingPartner


class TestTradingPartner:
    def test_initialization(self):
        """Test TradingPartner initializes with correct default state."""
        trading = TradingPartner(agent_id=1)
        
        assert trading.agent_id == 1
        assert trading.trade_partner_id is None
        assert trading.meeting_point is None
        assert trading.is_trading is False
        assert trading.trade_cooldown == 0
        assert trading.partner_cooldowns == {}
        assert trading.last_trade_mode_utility == 0.0
        assert trading.trade_stagnation_steps == 0
    
    def test_find_nearby_agents_excludes_self(self):
        """Test find_nearby_agents excludes the agent itself."""
        trading = TradingPartner(agent_id=1)
        
        # Create mock agents
        agent1 = Mock(id=1, x=5, y=5)
        agent2 = Mock(id=2, x=6, y=5)
        agent3 = Mock(id=3, x=7, y=5)
        
        all_agents = [agent1, agent2, agent3]
        nearby = trading.find_nearby_agents((5, 5), all_agents)
        
        # Should exclude agent1 (self) and include others within perception radius
        assert len(nearby) == 2
        assert all(agent.id != 1 for agent, _ in nearby)
    
    def test_find_nearby_agents_deterministic_sorting(self):
        """Test find_nearby_agents sorts deterministically by distance then position."""
        trading = TradingPartner(agent_id=1)
        
        # Create agents at different distances and positions
        agent2 = Mock(id=2, x=6, y=5)  # distance 1, position (6,5)
        agent3 = Mock(id=3, x=5, y=6)  # distance 1, position (5,6) - should come first
        agent4 = Mock(id=4, x=7, y=5)  # distance 2, position (7,5)
        agent5 = Mock(id=5, x=5, y=7)  # distance 2, position (5,7) - should come first
        
        all_agents = [Mock(id=1, x=5, y=5), agent2, agent3, agent4, agent5]
        nearby = trading.find_nearby_agents((5, 5), all_agents)
        
        # Should be sorted by distance first, then by position (x, y)
        expected_order = [agent3, agent2, agent5, agent4]  # (5,6), (6,5), (5,7), (7,5)
        actual_order = [agent for agent, _ in nearby]
        assert actual_order == expected_order
    
    def test_can_pair_with_basic_conditions(self):
        """Test can_pair_with checks basic pairing conditions."""
        trading = TradingPartner(agent_id=1)
        other_agent = Mock(id=2)
        other_agent._trading_partner = Mock(trade_partner_id=None)
        
        # Should be able to pair when no cooldowns and both available
        assert trading.can_pair_with(other_agent) is True
    
    def test_can_pair_with_general_cooldown(self):
        """Test can_pair_with respects general cooldown."""
        trading = TradingPartner(agent_id=1)
        trading.trade_cooldown = 3
        
        other_agent = Mock(id=2)
        other_agent._trading_partner = Mock(trade_partner_id=None)
        
        assert trading.can_pair_with(other_agent) is False
    
    def test_can_pair_with_partner_cooldown(self):
        """Test can_pair_with respects per-partner cooldown."""
        trading = TradingPartner(agent_id=1)
        trading.partner_cooldowns[2] = 5
        
        other_agent = Mock(id=2)
        other_agent._trading_partner = Mock(trade_partner_id=None)
        
        assert trading.can_pair_with(other_agent) is False
    
    def test_can_pair_with_self_already_paired(self):
        """Test can_pair_with when self is already paired."""
        trading = TradingPartner(agent_id=1)
        trading.trade_partner_id = 3
        
        other_agent = Mock(id=2)
        other_agent._trading_partner = Mock(trade_partner_id=None)
        
        assert trading.can_pair_with(other_agent) is False
    
    def test_can_pair_with_other_already_paired(self):
        """Test can_pair_with when other agent is already paired."""
        trading = TradingPartner(agent_id=1)
        
        other_agent = Mock(id=2)
        other_agent._trading_partner = Mock(trade_partner_id=4)
        
        assert trading.can_pair_with(other_agent) is False
    
    def test_establish_pairing_mutual_setup(self):
        """Test establish_pairing sets up mutual pairing correctly."""
        trading1 = TradingPartner(agent_id=1)
        trading2 = TradingPartner(agent_id=2)
        
        other_agent = Mock(id=2, x=7, y=5)
        other_agent._trading_partner = trading2
        
        trading1.establish_pairing((5, 5), other_agent)
        
        # Check mutual pairing setup
        assert trading1.trade_partner_id == 2
        assert trading2.trade_partner_id == 1
        assert trading1.meeting_point == (6, 5)  # midpoint of (5,5) and (7,5)
        assert trading2.meeting_point == (6, 5)
    
    def test_end_trading_session_sets_cooldowns(self):
        """Test end_trading_session sets per-partner cooldowns correctly."""
        trading1 = TradingPartner(agent_id=1)
        trading2 = TradingPartner(agent_id=2)
        
        other_agent = Mock(id=2)
        other_agent._trading_partner = trading2
        
        trading1.end_trading_session(other_agent)
        
        # Check per-partner cooldowns set
        assert trading1.partner_cooldowns[2] == 20
        assert trading2.partner_cooldowns[1] == 20
        
        # Check state cleared
        assert trading1.trade_partner_id is None
        assert trading2.trade_partner_id is None
        assert trading1.trade_cooldown == 3
        assert trading2.trade_cooldown == 3
    
    def test_clear_trade_partner_state(self):
        """Test clear_trade_partner clears state and sets general cooldown."""
        trading = TradingPartner(agent_id=1)
        trading.trade_partner_id = 2
        trading.meeting_point = (6, 5)
        trading.is_trading = True
        
        trading.clear_trade_partner()
        
        assert trading.trade_partner_id is None
        assert trading.meeting_point is None
        assert trading.is_trading is False
        assert trading.trade_cooldown == 3
    
    def test_update_cooldowns_decrements_all(self):
        """Test update_cooldowns decrements all cooldowns correctly."""
        trading = TradingPartner(agent_id=1)
        trading.trade_cooldown = 5
        trading.partner_cooldowns = {2: 3, 3: 1}
        
        trading.update_cooldowns()
        
        assert trading.trade_cooldown == 4
        assert trading.partner_cooldowns[2] == 2
        assert 3 not in trading.partner_cooldowns  # Should be removed (was 1, now 0)
    
    def test_update_cooldowns_removes_expired(self):
        """Test update_cooldowns removes expired cooldowns."""
        trading = TradingPartner(agent_id=1)
        trading.partner_cooldowns = {2: 1, 3: 0}
        
        trading.update_cooldowns()
        
        assert 2 not in trading.partner_cooldowns  # Expired
        assert 3 not in trading.partner_cooldowns  # Already expired
    
    def test_can_trade_with_partner_checks_cooldown(self):
        """Test can_trade_with_partner checks partner cooldown correctly."""
        trading = TradingPartner(agent_id=1)
        
        # No cooldown - should be able to trade
        assert trading.can_trade_with_partner(2) is True
        
        # Active cooldown - should not be able to trade
        trading.partner_cooldowns[2] = 5
        assert trading.can_trade_with_partner(2) is False
        
        # Different partner - should be able to trade
        assert trading.can_trade_with_partner(3) is True
