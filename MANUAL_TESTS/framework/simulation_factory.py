"""
Simulation Factory - Standardized simulation creation from configurations.

Handles resource generation, agent positioning, and preference factories.
"""

import sys
import os
import random

# Add src to Python path  
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))

from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation

from framework.test_configs import TestConfiguration


class SimulationFactory:
    """Standardized simulation creation from test configurations."""
    
    @staticmethod
    def create_simulation(test_config: TestConfiguration) -> Simulation:
        """Create simulation from test configuration."""
        
        # Generate resources using test-specific seed
        resources = SimulationFactory._generate_resources(test_config)
        
        # Generate agent positions
        agent_positions = SimulationFactory._generate_agent_positions(test_config)
        
        # Create preference factory
        preference_factory = SimulationFactory._create_preference_factory(test_config)
        
        # Build simulation config
        sim_config = SimConfig(
            grid_size=test_config.grid_size,
            initial_resources=resources,
            seed=test_config.seed,
            enable_respawn=True,
            enable_metrics=True,
            perception_radius=test_config.perception_radius,
            respawn_target_density=test_config.resource_density,
            respawn_rate=0.25,  # Standard rate from existing tests
            distance_scaling_factor=0.0,  # Default k=0.0
            viewport_size=test_config.viewport_size
        )
        
        # Create and return simulation
        return Simulation.from_config(sim_config, preference_factory, agent_positions=agent_positions)
        
    @staticmethod
    def _generate_resources(test_config: TestConfiguration) -> list:
        """Generate resources based on test configuration."""
        grid_w, grid_h = test_config.grid_size
        resource_count = int(grid_w * grid_h * test_config.resource_density)
        
        resource_rng = random.Random(test_config.seed)
        resources = []
        for _ in range(resource_count):
            x = resource_rng.randint(0, grid_w - 1)
            y = resource_rng.randint(0, grid_h - 1)
            resource_type = resource_rng.choice(['A', 'B'])
            resources.append((x, y, resource_type))
            
        return resources
        
    @staticmethod
    def _generate_agent_positions(test_config: TestConfiguration) -> list:
        """Generate non-overlapping agent positions."""
        grid_w, grid_h = test_config.grid_size
        
        # Use offset seed for positions (matching existing test pattern)
        pos_rng = random.Random(54321)  # Consistent with existing tests
        
        positions = set()
        while len(positions) < test_config.agent_count:
            x = pos_rng.randint(0, grid_w - 1)
            y = pos_rng.randint(0, grid_h - 1)
            positions.add((x, y))
            
        return list(positions)
        
    @staticmethod  
    def _create_preference_factory(test_config: TestConfiguration):
        """Create preference factory based on test configuration."""
        if test_config.preference_mix == "mixed":
            preferences = ['cobb_douglas', 'leontief', 'perfect_substitutes']
            # Use consistent seed for preference distribution (matching existing test)
            pref_rng = random.Random(9999)
            
            def preference_factory(idx: int):
                pref_type = pref_rng.choice(preferences)
                if pref_type == 'cobb_douglas':
                    from econsim.preferences.cobb_douglas import CobbDouglasPreference
                    alpha = pref_rng.uniform(0.2, 0.8)
                    return CobbDouglasPreference(alpha=alpha)
                elif pref_type == 'leontief':
                    from econsim.preferences.leontief import LeontiefPreference
                    return LeontiefPreference(a=1.0, b=1.0)
                else:
                    from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference
                    return PerfectSubstitutesPreference(a=1.0, b=1.0)
                    
            return preference_factory
                    
        elif test_config.preference_mix == "cobb_douglas":
            from econsim.preferences.cobb_douglas import CobbDouglasPreference
            preference_factory = lambda idx: CobbDouglasPreference(alpha=0.5)
            
        elif test_config.preference_mix == "leontief":
            from econsim.preferences.leontief import LeontiefPreference
            preference_factory = lambda idx: LeontiefPreference(a=1.0, b=1.0)
            
        elif test_config.preference_mix == "perfect_substitutes":
            from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference
            preference_factory = lambda idx: PerfectSubstitutesPreference(a=1.0, b=1.0)
            
        else:
            raise ValueError(f"Unknown preference mix: {test_config.preference_mix}")
            
        return preference_factory