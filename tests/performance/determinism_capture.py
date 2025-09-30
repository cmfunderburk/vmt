#!/usr/bin/env python3
"""
VMT EconSim Determinism Hash Capture

Captures determinism hashes from all 7 educational scenarios for refactor validation.
Runs quick simulations to establish reference hashes that must remain identical
after refactoring to ensure behavioral preservation.

Usage:
    pytest -q --capture-determinism-hash > baselines/determinism_reference.txt
    python tests/performance/determinism_capture.py > baselines/determinism_hashes.json
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional
import random

# Add src to Python path for imports
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Set headless environment for testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["SDL_VIDEODRIVER"] = "dummy" 
os.environ["ECONSIM_HEADLESS_RENDER"] = "1"

from econsim.tools.launcher.framework.test_configs import ALL_TEST_CONFIGS
from econsim.tools.launcher.framework.simulation_factory import SimulationFactory


@dataclass
class DeterminismRecord:
    """Determinism validation record for a scenario."""
    scenario_id: int
    scenario_name: str
    seed: int
    steps_executed: int
    agent_count: int
    resource_count: int
    determinism_hash: Optional[str] = None
    simulation_state_summary: Optional[Dict] = None
    

@dataclass
class DeterminismBaseline:
    """Complete determinism baseline for refactor validation."""
    timestamp: str
    python_version: str
    validation_steps: int
    scenarios: List[DeterminismRecord]
    

class DeterminismCapture:
    """Capture determinism baselines for refactor validation."""
    
    def __init__(self, validation_steps: int = 500):
        self.validation_steps = validation_steps
        self.ext_rng = random.Random(42)  # Fixed seed for deterministic capture
        
    def capture_scenario_hash(self, scenario_id: int) -> DeterminismRecord:
        """Capture determinism hash for a single scenario."""
        if scenario_id not in ALL_TEST_CONFIGS:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")
            
        config = ALL_TEST_CONFIGS[scenario_id]
        print(f"📊 Capturing determinism for Scenario {scenario_id}: {config.name}")
        
        # Create simulation with deterministic seed from config
        simulation = SimulationFactory.create_simulation(config)
        
        # Reset external RNG to known state
        self.ext_rng.seed(42)
        
        # Run validation steps 
        for step in range(self.validation_steps):
            simulation.step(self.ext_rng, use_decision=True)
            
        # Capture final state
        agent_count = len(simulation.agents)
        resource_count = len(list(simulation.grid.iter_resources()))
        
        # Attempt to capture determinism hash (if available)
        determinism_hash = None
        try:
            # Try common hash method names
            if hasattr(simulation, 'compute_hash'):
                determinism_hash = simulation.compute_hash()
            elif hasattr(simulation, 'get_hash'):
                determinism_hash = simulation.get_hash()
            elif hasattr(simulation, 'determinism_hash'):
                determinism_hash = simulation.determinism_hash()
            else:
                # Compute a simple state-based hash as fallback
                import hashlib
                state_data = []
                
                # Agent positions and inventories
                for agent in simulation.agents:
                    state_data.append(f"agent_{agent.id}_{agent.x}_{agent.y}")
                    if hasattr(agent, 'carried') and agent.carried:
                        for res_type, count in sorted(agent.carried.items()):
                            state_data.append(f"carried_{agent.id}_{res_type}_{count}")
                    if hasattr(agent, 'home_inventory') and agent.home_inventory:
                        for res_type, count in sorted(agent.home_inventory.items()):
                            state_data.append(f"home_{agent.id}_{res_type}_{count}")
                
                # Resource positions (grid resources - static)
                for x, y, rtype in simulation.grid.iter_resources_sorted():  # Correct tuple unpacking
                    state_data.append(f"resource_{x}_{y}_{rtype}")  # Use tuple elements directly
                
                # Create hash from sorted state
                state_str = "|".join(sorted(state_data))
                determinism_hash = hashlib.md5(state_str.encode()).hexdigest()[:16]
                
        except Exception as e:
            print(f"   Warning: Could not capture determinism hash: {e}")
        
        # Create state summary
        state_summary = {
            "total_agents": agent_count,
            "total_resources": resource_count,
            "final_step": self.validation_steps
        }
        
        # Add agent position summary
        if simulation.agents:
            positions = [(agent.x, agent.y) for agent in simulation.agents]
            state_summary["agent_positions_hash"] = hash(tuple(sorted(positions)))
        
        record = DeterminismRecord(
            scenario_id=scenario_id,
            scenario_name=config.name,
            seed=config.seed,
            steps_executed=self.validation_steps,
            agent_count=agent_count,
            resource_count=resource_count,
            determinism_hash=determinism_hash,
            simulation_state_summary=state_summary
        )
        
        print(f"   ✅ Hash: {determinism_hash or 'N/A'}, "
              f"Agents: {agent_count}, Resources: {resource_count}")
        
        return record
    
    def capture_all_scenarios(self) -> DeterminismBaseline:
        """Capture determinism baselines for all scenarios."""
        print("🔒 VMT EconSim Determinism Baseline Capture")
        print(f"   Validation steps per scenario: {self.validation_steps}")
        print("=" * 60)
        
        records = []
        
        # Capture determinism for all scenarios
        for scenario_id in sorted(ALL_TEST_CONFIGS.keys()):
            try:
                record = self.capture_scenario_hash(scenario_id)
                records.append(record)
            except Exception as e:
                print(f"❌ Scenario {scenario_id} failed: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        baseline = DeterminismBaseline(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            python_version=sys.version.split()[0],
            validation_steps=self.validation_steps,
            scenarios=records
        )
        
        print("=" * 60)
        print("🔒 Determinism Capture Summary:")
        print(f"   Scenarios captured: {len(records)}/7")
        if records:
            hash_count = sum(1 for r in records if r.determinism_hash)
            print(f"   Determinism hashes: {hash_count}/{len(records)}")
        
        return baseline


def main():
    """Command-line interface for determinism capture."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="VMT EconSim Determinism Hash Capture for Refactor Validation"
    )
    
    parser.add_argument(
        "--steps", 
        type=int, 
        default=500,
        help="Number of validation steps per scenario (default: 500)"
    )
    
    parser.add_argument(
        "--scenario", 
        type=int, 
        choices=list(ALL_TEST_CONFIGS.keys()),
        help="Capture single scenario (1-7). If not specified, captures all scenarios."
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (default: stdout)"
    )
    
    args = parser.parse_args()
    
    try:
        capture = DeterminismCapture(validation_steps=args.steps)
        
        if args.scenario:
            # Single scenario mode
            record = capture.capture_scenario_hash(args.scenario)
            
            baseline = DeterminismBaseline(
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
                python_version=sys.version.split()[0],
                validation_steps=args.steps,
                scenarios=[record]
            )
        else:
            # All scenarios mode
            baseline = capture.capture_all_scenarios()
        
        # Output results
        results_json = json.dumps(asdict(baseline), indent=2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(results_json)
            print(f"\n📁 Determinism baseline saved to: {args.output}")
        else:
            print(results_json)
            
    except KeyboardInterrupt:
        print("\n⏹️  Determinism capture interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Determinism capture failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()