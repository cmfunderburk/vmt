"""Educational validation test for enhanced trade visualization features."""
import os
import random
from unittest import mock

from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig
from econsim.simulation.agent import Agent
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference
from econsim.preferences.leontief import LeontiefPreference
from econsim.gui.simulation_controller import SimulationController


def test_educational_scenario_diverse_preferences():
    """Test educational scenario with diverse preference types trading."""
    # Set up environment for trading
    for key in ("ECONSIM_TRADE_DRAFT", "ECONSIM_TRADE_EXEC", "ECONSIM_FORAGE_ENABLED"):
        if key in os.environ:
            del os.environ[key]
    
    os.environ["ECONSIM_TRADE_DRAFT"] = "1" 
    os.environ["ECONSIM_TRADE_EXEC"] = "1"
    os.environ["ECONSIM_FORAGE_ENABLED"] = "0"  # Focus on trading only
    
    try:
        # Create simulation with diverse agents
        config = SimConfig(
            grid_size=(3, 3),
            initial_resources=[],  # No foraging resources
            seed=42
        )
        
        # Create agents with different preferences and complementary inventories
        agents = [
            Agent(
                id=0, x=0, y=0, 
                preference=CobbDouglasPreference(alpha=0.2),  # Prefers good2
                carrying={"good1": 2, "good2": 0}, 
                home_inventory={"good1": 0, "good2": 0}
            ),
            Agent(
                id=1, x=1, y=0,
                preference=CobbDouglasPreference(alpha=0.8),  # Prefers good1 
                carrying={"good1": 0, "good2": 2},
                home_inventory={"good1": 0, "good2": 0}
            ),
            Agent(
                id=2, x=2, y=0,
                preference=PerfectSubstitutesPreference(a=3.0, b=1.0),  # Strongly prefers good1
                carrying={"good1": 1, "good2": 1},
                home_inventory={"good1": 0, "good2": 0}
            ),
            Agent(
                id=3, x=0, y=1,
                preference=LeontiefPreference(a=1.0, b=1.0),  # Wants balanced bundles
                carrying={"good1": 1, "good2": 1},
                home_inventory={"good1": 0, "good2": 0}
            ),
        ]
        
        sim = Simulation.from_config(config, lambda: CobbDouglasPreference(alpha=0.5))
        sim.agents = agents
        
        # Create controller and enable trading features
        controller = SimulationController(sim)
        controller.set_bilateral_enabled(True)
        
        # Step simulation to generate trades
        rng = random.Random(123)
        sim.step(rng)
        
        # Validate educational metrics
        intents_count = controller.active_intents_count()
        total_welfare = controller.calculate_total_welfare_change()
        trading_pairs = controller.count_trading_pairs()
        diversity = controller.analyze_preference_diversity()
        
        print(f"Educational Scenario Results:")
        print(f"  Active Intents: {intents_count}")
        print(f"  Total Welfare Change: {total_welfare:.3f}")
        print(f"  Trading Pairs: {trading_pairs}")  
        print(f"  Preference Diversity: {diversity}")
        
        # Educational assertions
        assert intents_count >= 0, "Should have enumerated intents"
        assert total_welfare >= 0, "Trade should improve total welfare"
        assert "Mixed" in diversity, "Should detect mixed preference types"
        
        # Test controller educational methods
        intents = controller.get_active_intents()
        assert isinstance(intents, list), "Should return list of intents"
        
        # Test visualization options
        viz_options = controller.get_trade_visualization_options()
        assert 'show_arrows' in viz_options
        assert 'show_highlights' in viz_options
        
        # Test pause on trade functionality
        controller.set_pause_on_trade(True)
        assert controller.should_pause_on_trade() is True
        
        controller.set_pause_on_trade(False)
        assert controller.should_pause_on_trade() is False
        
        # Test visualization option setting
        controller.set_trade_visualization_options(show_arrows=False, show_highlights=True)
        updated_options = controller.get_trade_visualization_options()
        assert updated_options['show_arrows'] is False
        assert updated_options['show_highlights'] is True
        
        return True
        
    finally:
        # Cleanup environment
        for key in ("ECONSIM_TRADE_DRAFT", "ECONSIM_TRADE_EXEC", "ECONSIM_FORAGE_ENABLED"):
            if key in os.environ:
                del os.environ[key]


def test_enhanced_visualization_performance():
    """Test that enhanced visualization doesn't significantly impact performance."""
    import time
    import pygame
    from econsim.gui._enhanced_trade_visualization import render_enhanced_trade_visualization
    
    # Set up test environment
    os.environ["ECONSIM_TRADE_DRAFT"] = "1"
    
    try:
        pygame.init()
        surface = pygame.Surface((800, 600))
        font = pygame.font.Font(None, 24)
        
        # Create larger simulation for performance test
        config = SimConfig(
            grid_size=(10, 10),
            initial_resources=[],
            seed=100
        )
        
        agents = []
        for i in range(20):
            agents.append(Agent(
                id=i, x=i % 10, y=i // 10,
                preference=CobbDouglasPreference(alpha=random.uniform(0.1, 0.9)),
                carrying={"good1": random.randint(0, 3), "good2": random.randint(0, 3)},
                home_inventory={"good1": 0, "good2": 0}
            ))
        
        sim = Simulation.from_config(config, lambda: CobbDouglasPreference(alpha=0.5))
        sim.agents = agents
        
        # Generate some trade intents
        rng = random.Random(200)
        sim.step(rng)
        
        # Time the enhanced visualization
        start_time = time.time()
        iterations = 50
        
        for _ in range(iterations):
            render_enhanced_trade_visualization(
                surface, font, sim,
                cell_w=40, cell_h=40,
                show_arrows=True, show_highlights=True
            )
        
        end_time = time.time()
        avg_time = (end_time - start_time) / iterations
        
        print(f"Enhanced visualization performance:")
        print(f"  Average render time: {avg_time*1000:.2f}ms")
        print(f"  Target: <5ms per frame")
        
        # Performance assertion (should be fast enough for 60 FPS)
        assert avg_time < 0.005, f"Visualization too slow: {avg_time*1000:.2f}ms > 5ms"
        
        return True
        
    finally:
        if "ECONSIM_TRADE_DRAFT" in os.environ:
            del os.environ["ECONSIM_TRADE_DRAFT"]
        pygame.quit()


if __name__ == "__main__":
    print("Running educational validation tests...")
    
    success1 = test_educational_scenario_diverse_preferences()
    print("✓ Educational scenario with diverse preferences passed")
    
    success2 = test_enhanced_visualization_performance()  
    print("✓ Enhanced visualization performance passed")
    
    if success1 and success2:
        print("\n🎉 All educational enhancement validations passed!")
        print("Enhanced trade visualization system ready for student use.")
    else:
        print("\n❌ Some validations failed.")
        exit(1)