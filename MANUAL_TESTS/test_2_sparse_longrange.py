#!/usr/bin/env python3
"""
Manual Test 2: Sparse Long-Range Unified Target Selection Test

Test Configuration:
- Agents: 10
- Grid: 40x40
- Resource Density: 0.05 (sparse resources)
- Perception Radius: 15 (long range)
- Preferences: Random Mix

This test validates behavior in a sparse resource environment with long perception radius.
Agents should be able to find distant resources but may need to travel longer distances.

Expected Behavior by Phase:
1-200: Both behaviors - agents use long perception to find sparse resources and partners
201-400: Forage only - focus on distant resource collection
401-600: Exchange only - partners should find each other across long distances  
601-800: Both disabled - agents return home across long distances
801-1000: Both re-enabled - resume long-range seeking
1001-1050: Final idle - return home and stay idle

Watch for: Long-distance movement patterns, efficient resource location with sparse distribution.
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
    """Create the test configuration with sparse resources."""
    # Calculate number of resources based on density
    grid_area = 40 * 40
    num_resources = int(grid_area * 0.05)  # Very sparse
    
    # Generate random resource positions
    resource_rng = random.Random(23456)
    positions = set()
    while len(positions) < num_resources:
        x = resource_rng.randint(0, 39)
        y = resource_rng.randint(0, 39)
        positions.add((x, y))
    
    # Create resources with alternating types
    resources = []
    for i, (x, y) in enumerate(positions):
        resource_type = 'A' if i % 2 == 0 else 'B'
        resources.append((x, y, resource_type))
    
    return SimConfig(
        grid_size=(40, 40),
        initial_resources=resources,
        seed=23456,
        enable_respawn=True,
        enable_metrics=True
    )

def create_test_agents():
    """Create 10 agents with random preferences."""
    def preference_factory(idx: int):
        import random
        pref_rng = random.Random(65432 + idx + 2000)
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
    agent_rng = random.Random(65432)
    
    # Generate 10 random agent positions
    positions = set()
    while len(positions) < 10:
        x = agent_rng.randint(0, 39)
        y = agent_rng.randint(0, 39)
        positions.add((x, y))
    
    return list(positions), preference_factory

class Test2Controller:
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
        print("MANUAL TEST 2: Sparse Resources with Long Perception")
        print("=" * 60)
        print("Configuration: 10 agents, 40x40 grid, 0.05 density, radius 15, random preferences")
        print("\nFocus: Long-range perception in sparse resource environment")
        print("Watch for: Efficient resource finding, long-distance partner interactions")
        print("\nPhase Schedule:")
        print("  1-200: Both foraging and exchange enabled")
        print("  201-400: Only foraging enabled") 
        print("  401-600: Only exchange enabled")
        print("  601-800: Both disabled")
        print("  801-1000: Both enabled")
        print("  1001-1050: Both disabled")
        print("\nStarting Phase 1: Both behaviors enabled")
        print("-" * 40)
    
    def check_phase_transition(self):
        """Check if we need to transition to a new phase."""
        if hasattr(self.main_window, 'controller') and hasattr(self.main_window.controller, 'simulation'):
            sim = self.main_window.controller.simulation
            if sim:
                new_turn = sim._steps
                
                if new_turn != self.current_turn:
                    self.current_turn = new_turn
                    
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
        print("Focus: Long-range resource seeking in sparse environment")
        os.environ['ECONSIM_TRADE_DRAFT'] = '0'
        os.environ['ECONSIM_TRADE_EXEC'] = '0'
        self.phase = 2
        
    def transition_to_phase_3(self):
        """Phase 3: Only exchange enabled."""
        print(f"\n>>> TURN {self.current_turn}: PHASE 3 - EXCHANGE ONLY <<<") 
        print("Focus: Long-distance partner finding and convergence")
        os.environ['ECONSIM_FORAGE_ENABLED'] = '0'
        os.environ['ECONSIM_TRADE_DRAFT'] = '1'
        os.environ['ECONSIM_TRADE_EXEC'] = '1'
        self.phase = 3
        
    def transition_to_phase_4(self):
        """Phase 4: Both disabled."""
        print(f"\n>>> TURN {self.current_turn}: PHASE 4 - BOTH DISABLED <<<")
        print("Focus: Long-distance return home behavior")
        os.environ['ECONSIM_FORAGE_ENABLED'] = '0'
        os.environ['ECONSIM_TRADE_DRAFT'] = '0'
        os.environ['ECONSIM_TRADE_EXEC'] = '0'
        self.phase = 4
        
    def transition_to_phase_5(self):
        """Phase 5: Both re-enabled."""
        print(f"\n>>> TURN {self.current_turn}: PHASE 5 - BOTH RE-ENABLED <<<")
        print("Focus: Resumption of long-range unified selection")
        os.environ['ECONSIM_FORAGE_ENABLED'] = '1'
        os.environ['ECONSIM_TRADE_DRAFT'] = '1'
        os.environ['ECONSIM_TRADE_EXEC'] = '1'
        self.phase = 5
        
    def transition_to_phase_6(self):
        """Phase 6: Final idle phase."""
        print(f"\n>>> TURN {self.current_turn}: PHASE 6 - FINAL IDLE <<<")
        print("Focus: Final return home across large distances")
        os.environ['ECONSIM_FORAGE_ENABLED'] = '0'
        os.environ['ECONSIM_TRADE_DRAFT'] = '0'
        os.environ['ECONSIM_TRADE_EXEC'] = '0'
        self.phase = 6
        
    def test_complete(self):
        """Test completed."""
        print(f"\n>>> TURN {self.current_turn}: TEST COMPLETE <<<")
        print("Test 2 completed successfully!")
        print("Review long-range behavior patterns observed.")
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
        perception_radius=15  # Long perception radius
    )
    
    # Set up test controller
    test_controller = Test2Controller(main_window)
    
    main_window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()