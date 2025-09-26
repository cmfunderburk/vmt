#!/usr/bin/env python3
"""
Manual Test 3: High Density with Local Perception
=================================================

Test Configuration:
- Agents: 100
- Grid: 30x30
- Resource Density: 0.5 (very dense resources)
- Perception Radius: 2 (local perception only)
- Preferences: Random Mix

This test validates behavior with many agents in a resource-rich environment with limited perception.
Tests scalability and local decision-making with high competition for nearby resources.

Expected Behavior by Phase:
1-200: Both behaviors - high competition, frequent local trades, resource contention
201-400: Forage only - intense local resource competition, many agents per resource
401-600: Exchange only - dense local trading with short-range partner finding
601-800: Both disabled - mass return home, potential crowding
801-1000: Both re-enabled - resume high-density unified selection
1001-1050: Final idle - coordinated return to homes

Watch for: Performance with 100 agents, local clustering, resource competition patterns.
"""

import sys
import os
import random
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from econsim.gui.main_window import MainWindow
from econsim.simulation.config import SimConfig

def create_test_config():
    """Create the test configuration with dense resources."""
    # Calculate number of resources based on density
    grid_area = 30 * 30
    num_resources = int(grid_area * 0.5)  # Very dense
    
    # Generate random resource positions
    resource_rng = random.Random(34567)
    positions = set()
    while len(positions) < num_resources:
        x = resource_rng.randint(0, 29)
        y = resource_rng.randint(0, 29)
        positions.add((x, y))
    
    # Create resources with alternating types
    resources = []
    for i, (x, y) in enumerate(positions):
        resource_type = 'A' if i % 2 == 0 else 'B'
        resources.append((x, y, resource_type))
    
    return SimConfig(
        grid_size=(30, 30),
        initial_resources=resources,
        seed=34567,
        enable_respawn=True,
        enable_metrics=True
    )

def create_test_agents():
    """Create 100 agents with random preferences."""
    def preference_factory(idx: int):
        import random
        pref_rng = random.Random(76543 + idx + 2000)
        pref_types = ['cobb_douglas', 'perfect_substitutes', 'leontief']
        chosen_type = pref_rng.choice(pref_types)
        
        if chosen_type == 'cobb_douglas':
            from econsim.preferences.cobb_douglas import CobbDouglasPreference
            return CobbDouglasPreference(alpha=0.5)
        elif chosen_type == 'perfect_substitutes':
            from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference
            return PerfectSubstitutesPreference(a=1.0, b=1.0)
        elif chosen_type == 'leontief':
            from econsim.preferences.leontief import LeontiefPreference
            return LeontiefPreference(a=1.0, b=1.0)
    
    agent_positions = []
    agent_rng = random.Random(76543)
    
    # Generate 100 random agent positions
    positions = set()
    while len(positions) < 100:
        x = agent_rng.randint(0, 29)
        y = agent_rng.randint(0, 29)
        positions.add((x, y))
    
    return list(positions), preference_factory

class Test3Controller:
    """Controller to manage phase transitions during the test."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_turn = 0
        self.phase = 1
        
        # Set up timer to check turns
        self.phase_timer = QTimer()
        self.phase_timer.timeout.connect(self.check_phase_transition)
        self.phase_timer.start(100)  # Check every 100ms
        
        print("=" * 60)
        print("MANUAL TEST 3: High Density with Local Perception")
        print("=" * 60)
        print("Configuration: 100 agents, 30x30 grid, 0.5 density, radius 2, random preferences")
        print("\nFocus: Scalability and local competition with many agents")
        print("Watch for: Performance, resource contention, local clustering patterns")
        print("\nPhase Schedule:")
        print("  1-200: Both foraging and exchange enabled")
        print("  201-400: Only foraging enabled") 
        print("  401-600: Only exchange enabled")
        print("  601-800: Both disabled")
        print("  801-1000: Both enabled")
        print("  1001-1050: Both disabled")
        print("\nStarting Phase 1: Both behaviors enabled (100 agents)")
        print("-" * 40)
    
    def check_phase_transition(self):
        """Check if we need to transition to a new phase."""
        if hasattr(self.main_window, 'controller') and hasattr(self.main_window.controller, 'simulation'):
            sim = self.main_window.controller.simulation
            if sim:
                new_turn = sim._steps
                
                if new_turn != self.current_turn:
                    self.current_turn = new_turn
                    
                    # Status update every 50 turns for performance monitoring
                    if self.current_turn % 50 == 0:
                        print(f"Turn {self.current_turn}: Phase {self.phase} - 100 agents active")
                    
                    # Check for phase transitions
                    if self.current_turn == 201 and self.phase == 1:
                        self.transition_to_phase_2()
                    elif self.current_turn == 401 and self.phase == 2:
                        self.transition_to_phase_3()
                    elif self.current_turn == 601 and self.phase == 3:
                        self.transition_to_phase_4()
                    elif self.current_turn == 801 and self.phase == 4:
                        self.transition_to_phase_5()
                    elif self.current_turn == 1001 and self.phase == 5:
                        self.transition_to_phase_6()
                    elif self.current_turn == 1050:
                        self.test_complete()
    
    def transition_to_phase_2(self):
        """Phase 2: Only foraging enabled."""
        print(f"\n>>> TURN {self.current_turn}: PHASE 2 - FORAGE ONLY <<<")
        print("Focus: Local resource competition among 100 agents")
        os.environ['ECONSIM_TRADE_DRAFT'] = '0'
        os.environ['ECONSIM_TRADE_EXEC'] = '0'
        self.phase = 2
        
    def transition_to_phase_3(self):
        """Phase 3: Only exchange enabled."""
        print(f"\n>>> TURN {self.current_turn}: PHASE 3 - EXCHANGE ONLY <<<") 
        print("Focus: Dense local trading with short perception radius")
        os.environ['ECONSIM_FORAGE_ENABLED'] = '0'
        os.environ['ECONSIM_TRADE_DRAFT'] = '1'
        os.environ['ECONSIM_TRADE_EXEC'] = '1'
        self.phase = 3
        
    def transition_to_phase_4(self):
        """Phase 4: Both disabled."""
        print(f"\n>>> TURN {self.current_turn}: PHASE 4 - BOTH DISABLED <<<")
        print("Focus: Mass return home behavior - watch for crowding/performance")
        os.environ['ECONSIM_FORAGE_ENABLED'] = '0'
        os.environ['ECONSIM_TRADE_DRAFT'] = '0'
        os.environ['ECONSIM_TRADE_EXEC'] = '0'
        self.phase = 4
        
    def transition_to_phase_5(self):
        """Phase 5: Both re-enabled."""
        print(f"\n>>> TURN {self.current_turn}: PHASE 5 - BOTH RE-ENABLED <<<")
        print("Focus: High-density unified selection resumption")
        os.environ['ECONSIM_FORAGE_ENABLED'] = '1'
        os.environ['ECONSIM_TRADE_DRAFT'] = '1'
        os.environ['ECONSIM_TRADE_EXEC'] = '1'
        self.phase = 5
        
    def transition_to_phase_6(self):
        """Phase 6: Final idle phase."""
        print(f"\n>>> TURN {self.current_turn}: PHASE 6 - FINAL IDLE <<<")
        print("Focus: Coordinated shutdown of 100 agents")
        os.environ['ECONSIM_FORAGE_ENABLED'] = '0'
        os.environ['ECONSIM_TRADE_DRAFT'] = '0'
        os.environ['ECONSIM_TRADE_EXEC'] = '0'
        self.phase = 6
        
    def test_complete(self):
        """Test completed."""
        print(f"\n>>> TURN {self.current_turn}: TEST COMPLETE <<<")
        print("Test 3 completed successfully!")
        print("Review scalability and performance with 100 agents.")
        print("=" * 60)

def main():
    # Set initial environment for Phase 1
    os.environ['ECONSIM_FORAGE_ENABLED'] = '1'
    os.environ['ECONSIM_TRADE_DRAFT'] = '1' 
    os.environ['ECONSIM_TRADE_EXEC'] = '1'
    os.environ['ECONSIM_UNIFIED_SELECTION_ENABLE'] = '1'
    
    app = QApplication(sys.argv)
    
    # Create test configuration
    config = create_test_config()
    agent_positions, preference_factory = create_test_agents()
    
    # Create main window
    main_window = MainWindow()
    
    # Set up the simulation with test parameters
    main_window.start_simulation_with_config(
        config=config,
        agent_positions=agent_positions,
        preference_factory=preference_factory,
        perception_radius=2  # Very local perception
    )
    
    # Set up test controller
    test_controller = Test3Controller(main_window)
    
    main_window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()