"""Test enhanced trade visualization for educational improvements."""
import os
import pygame
from unittest import mock

from econsim.gui._enhanced_trade_visualization import render_enhanced_trade_visualization
from econsim.simulation.agent import Agent
from econsim.simulation.trade import TradeIntent
from econsim.preferences.cobb_douglas import CobbDouglasPreference


def test_enhanced_visualization_smoke():
    """Test that enhanced visualization renders without crashing."""
    # Set up test environment
    os.environ["ECONSIM_TRADE_DRAFT"] = "1"
    
    # Create minimal pygame surface and font
    pygame.init()
    surface = pygame.Surface((800, 600))
    font = pygame.font.Font(None, 24)
    
    # Create mock simulation with agents and trade intents
    sim = mock.MagicMock()
    
    # Create test agents
    agent1 = Agent(
        id=0, x=1, y=1, 
        carrying={"good1": 1, "good2": 0},
        home_inventory={"good1": 0, "good2": 0},
        preference=CobbDouglasPreference(alpha=0.2)
    )
    agent2 = Agent(
        id=1, x=2, y=1,
        carrying={"good1": 0, "good2": 1},
        home_inventory={"good1": 0, "good2": 0},
        preference=CobbDouglasPreference(alpha=0.8)
    )
    
    # Create trade intent
    trade_intent = TradeIntent(
        seller_id=0,
        buyer_id=1,
        give_type="good1",
        take_type="good2", 
        quantity=1,
        priority=(0.0, 0, 1, "good1", "good2"),
        delta_utility=0.5
    )
    
    sim.agents = [agent1, agent2]
    sim.trade_intents = [trade_intent]
    sim.metrics_collector = None  # No executed trades
    
    # Test rendering with various configurations
    try:
        # Basic rendering
        render_enhanced_trade_visualization(
            surface, font, sim, 
            cell_w=40, cell_h=40,
            show_arrows=True, show_highlights=True
        )
        
        # Arrows only
        render_enhanced_trade_visualization(
            surface, font, sim,
            cell_w=40, cell_h=40, 
            show_arrows=True, show_highlights=False
        )
        
        # Highlights only
        render_enhanced_trade_visualization(
            surface, font, sim,
            cell_w=40, cell_h=40,
            show_arrows=False, show_highlights=True
        )
        
        # Should complete without exceptions
        assert True
        
    finally:
        # Cleanup
        if "ECONSIM_TRADE_DRAFT" in os.environ:
            del os.environ["ECONSIM_TRADE_DRAFT"]
        pygame.quit()


def test_enhanced_visualization_with_executed_trade():
    """Test visualization highlighting of executed trades."""
    os.environ["ECONSIM_TRADE_DRAFT"] = "1"
    
    pygame.init()
    surface = pygame.Surface((800, 600))
    font = pygame.font.Font(None, 24)
    
    sim = mock.MagicMock()
    
    # Mock metrics collector with executed trade
    metrics_collector = mock.MagicMock()
    metrics_collector.last_executed_trade = {
        'seller': 0,
        'buyer': 1,
        'give_type': 'good1',
        'take_type': 'good2',
        'delta_utility': 0.75
    }
    sim.metrics_collector = metrics_collector
    
    # Create agents and intents as before
    agent1 = Agent(
        id=0, x=0, y=0,
        carrying={"good1": 1, "good2": 0}, 
        home_inventory={"good1": 0, "good2": 0},
        preference=CobbDouglasPreference(alpha=0.3)
    )
    agent2 = Agent(
        id=1, x=1, y=0,
        carrying={"good1": 0, "good2": 1},
        home_inventory={"good1": 0, "good2": 0},
        preference=CobbDouglasPreference(alpha=0.7)
    )
    
    trade_intent = TradeIntent(
        seller_id=0,
        buyer_id=1,
        give_type="good1",
        take_type="good2",
        quantity=1,
        priority=(0.0, 0, 1, "good1", "good2"),
        delta_utility=0.75
    )
    
    sim.agents = [agent1, agent2]
    sim.trade_intents = [trade_intent]
    
    try:
        # This should highlight the executed trade with different color
        render_enhanced_trade_visualization(
            surface, font, sim,
            cell_w=50, cell_h=50,
            show_arrows=True, show_highlights=True
        )
        
        # Should complete without exceptions
        assert True
        
    finally:
        if "ECONSIM_TRADE_DRAFT" in os.environ:
            del os.environ["ECONSIM_TRADE_DRAFT"]
        pygame.quit()


if __name__ == "__main__":
    test_enhanced_visualization_smoke()
    test_enhanced_visualization_with_executed_trade()
    print("Enhanced trade visualization tests passed!")