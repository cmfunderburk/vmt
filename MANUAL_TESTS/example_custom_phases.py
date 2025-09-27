#!/usr/bin/env python3
"""
Example Custom Phase Test - Demonstrates configurable phase scheduling.

This test shows how to create a custom phase schedule that differs from
the standard 6-phase pattern. It uses:
- 100 turns of forage-only behavior
- 200 turns of both systems enabled  
- 100 turns of exchange-only behavior
- 50 turns of idle behavior

This demonstrates the flexibility of the new phase configuration system
for educational scenarios focusing on specific economic behaviors.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from framework.base_test import StandardPhaseTest
from framework.test_configs import TestConfiguration
from framework.phase_manager import PhaseManager, PhaseBehavior


# Create custom phase configuration
def create_custom_phases():
    """Create a custom 4-phase schedule focused on behavioral transitions."""
    return PhaseManager.create_custom_phases([
        (PhaseBehavior.forage_only(), 100),     # Phase 1: Learn foraging behavior
        (PhaseBehavior.both_enabled(), 200),    # Phase 2: Introduce trading
        (PhaseBehavior.exchange_only(), 100),   # Phase 3: Focus on exchange
        (PhaseBehavior.both_disabled(), 50)     # Phase 4: Observe idle behavior
    ])


# Custom test configuration with phase schedule
CUSTOM_PHASE_CONFIG = TestConfiguration(
    id=101,
    name="Custom Phase Demo",
    description="Demonstrates configurable phase scheduling (Forage→Both→Exchange→Idle)",
    grid_size=(25, 25),
    agent_count=15,
    resource_density=0.3,
    perception_radius=6,
    distance_scaling_factor=0.0,
    preference_mix="mixed",
    seed=54321,
    custom_phases=list(create_custom_phases().phases.values())
)


class CustomPhaseTest(StandardPhaseTest):
    """Custom test with non-standard phase schedule."""
    
    def __init__(self):
        super().__init__(CUSTOM_PHASE_CONFIG)


def main():
    """Run the custom phase test."""
    # Set up comprehensive debug logging
    os.environ['ECONSIM_DEBUG_AGENT_MODES'] = '1'
    os.environ['ECONSIM_DEBUG_PHASES'] = '1'
    os.environ['ECONSIM_DEBUG_TRADES'] = '1'
    
    app = QApplication(sys.argv)
    test = CustomPhaseTest()
    test.show()
    
    print("Custom Phase Test Configuration:")
    print(f"- Grid: {CUSTOM_PHASE_CONFIG.grid_size[0]}×{CUSTOM_PHASE_CONFIG.grid_size[1]}")
    print(f"- Agents: {CUSTOM_PHASE_CONFIG.agent_count}")
    print(f"- Phases: 4 custom phases (450 total turns)")
    print("- Phase 1 (1-100): Forage only - agents learn resource collection")
    print("- Phase 2 (101-300): Both enabled - introduce trading dynamics") 
    print("- Phase 3 (301-400): Exchange only - focus on bilateral exchange")
    print("- Phase 4 (401-450): Both disabled - observe idle/stagnation behavior")
    print("\nThis demonstrates the flexibility of custom phase scheduling!")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()