#!/usr/bin/env python3
"""
VMT EconSim Phase 0 Baseline Capture

Comprehensive performance testing across all 7 educational test scenarios.
This replaces the deprecated perf_stub.py approach with scenario-specific
simulation step performance measurement.

Execution Mode: Headless simulation-only (no GUI rendering)
Focus: Simulation.step() performance in steps per second
Output: JSON baseline for Phase 0 refactor validation

Usage:
    python tests/performance/baseline_capture.py > baselines/performance_baseline.json
    python tests/performance/baseline_capture.py --scenario 1 --steps 500 --warmup 50
"""

from __future__ import annotations

import argparse
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


def setup_raw_data_observers(simulation, test_config):
    """Set up raw data observers externally for performance testing.
    
    This function creates the raw data logging infrastructure outside of the simulation,
    maintaining clean separation between simulation logic and logging.
    """
    try:
        from pathlib import Path
        import datetime
        
        # Create output directory for this test run
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        test_name = test_config.name.replace(" ", "_").replace("/", "_")
        output_dir = Path("economic_analysis_logs") / f"{timestamp}_{test_name}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write session configuration
        config_data = {
            "scenario_id": test_config.id,
            "scenario_name": test_config.name,
            "grid_size": test_config.grid_size,
            "agent_count": test_config.agent_count,
            "resource_density": test_config.resource_density,
            "preference_mix": test_config.preference_mix,
            "seed": test_config.seed,
            "timestamp": timestamp,
            "architecture": "pure_raw_data"
        }
        
        import json
        with open(output_dir / "config.json", "w") as f:
            json.dump(config_data, f, indent=2)
        
        # Create raw data observer for simulation events
        from econsim.observability.raw_data.raw_data_observer import RawDataObserver
        from econsim.observability.raw_data.raw_data_writer import RawDataWriter
        
        simulation_events_file = output_dir / "simulation_events.jsonl"
        raw_data_observer = RawDataObserver()
        raw_data_writer = RawDataWriter(compress=False)
        
        # Register the observer with the simulation's observer registry
        simulation._observer_registry.register(raw_data_observer)
        
        # Store the output file path for later writing
        raw_data_writer._output_file = simulation_events_file
        
        print(f"Comprehensive simulation logging enabled: {simulation_events_file}")
        
        return raw_data_writer
        
    except Exception as e:
        print(f"Warning: Failed to set up raw data observers: {e}")
        return None


@dataclass
class ScenarioPerformanceResult:
    """Performance metrics for a single test scenario."""
    scenario_id: int
    scenario_name: str
    grid_size: tuple[int, int]
    agent_count: int
    resource_density: float
    total_steps: int
    warmup_steps: int
    execution_time_seconds: float
    steps_per_second: float
    memory_usage_mb: Optional[float] = None
    determinism_hash: Optional[str] = None


@dataclass
class BaselineResults:
    """Complete baseline capture results."""
    timestamp: str
    python_version: str
    scenarios: List[ScenarioPerformanceResult]
    summary: Dict[str, float]


class BaselineCapture:
    """Headless performance baseline capture for all educational scenarios."""
    
    def __init__(self, steps_per_scenario: int = 1000, warmup_steps: int = 100):
        self.steps_per_scenario = steps_per_scenario
        self.warmup_steps = warmup_steps
        self.ext_rng = random.Random(999)  # Consistent external RNG for all tests
        
    def run_scenario_benchmark(self, scenario_id: int) -> ScenarioPerformanceResult:
        """Run performance benchmark for a single scenario."""
        if scenario_id not in ALL_TEST_CONFIGS:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")
            
        config = ALL_TEST_CONFIGS[scenario_id]
        print(f"🔄 Benchmarking Scenario {scenario_id}: {config.name}")
        print(f"   Grid: {config.grid_size}, Agents: {config.agent_count}, "
              f"Density: {config.resource_density:.2f}")
        
        # Set up feature flags using the same orchestrator as the test gallery
        from econsim.tools.launcher.framework.debug_orchestrator import DebugOrchestrator
        debug_orchestrator = DebugOrchestrator(config)
        
        # Create simulation using factory
        simulation = SimulationFactory.create_simulation(config)
        
        # Set up external raw data observers (clean separation from simulation)
        raw_data_writer = setup_raw_data_observers(simulation, config)
        
        # Reset external RNG for consistency
        self.ext_rng.seed(999)
        
        # Warmup phase - not counted in performance
        if self.warmup_steps > 0:
            print(f"   Warming up ({self.warmup_steps} steps)...")
            for _ in range(self.warmup_steps):
                simulation.step(self.ext_rng)
        
        # Capture determinism hash after warmup 
        determinism_hash = None
        try:
            if hasattr(simulation, 'get_determinism_hash'):
                determinism_hash = simulation.get_determinism_hash()
            elif hasattr(simulation, 'compute_hash'):
                determinism_hash = simulation.compute_hash()
        except Exception as e:
            print(f"   Warning: Could not capture determinism hash: {e}")
        
        # Performance measurement phase
        print(f"   Measuring performance ({self.steps_per_scenario} steps)...")
        
        # Measure memory usage before benchmark (optional)
        memory_before_mb = None
        try:
            import psutil
            process = psutil.Process()
            memory_before_mb = process.memory_info().rss / 1024 / 1024
        except ImportError:
            pass  # psutil optional
        
        # Time the actual simulation steps
        start_time = time.perf_counter()
        
        for step in range(self.steps_per_scenario):
            simulation.step(self.ext_rng)
            
            # Progress indicator for long benchmarks
            if step > 0 and step % 200 == 0:
                elapsed = time.perf_counter() - start_time
                rate = step / elapsed if elapsed > 0 else 0
                print(f"   Progress: {step}/{self.steps_per_scenario} steps "
                      f"({rate:.1f} steps/sec)")
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        steps_per_second = self.steps_per_scenario / execution_time if execution_time > 0 else 0
        
        # Measure memory usage after benchmark (optional)
        memory_after_mb = None
        try:
            if memory_before_mb is not None:
                memory_after_mb = process.memory_info().rss / 1024 / 1024
        except Exception:
            pass  # Ignore memory measurement errors
        
        result = ScenarioPerformanceResult(
            scenario_id=scenario_id,
            scenario_name=config.name,
            grid_size=config.grid_size,
            agent_count=config.agent_count,
            resource_density=config.resource_density,
            total_steps=self.steps_per_scenario,
            warmup_steps=self.warmup_steps,
            execution_time_seconds=execution_time,
            steps_per_second=steps_per_second,
            memory_usage_mb=memory_after_mb,
            determinism_hash=determinism_hash
        )
        
        print(f"   ✅ Result: {steps_per_second:.1f} steps/sec "
              f"({execution_time:.2f}s total)")
        
        # Clean up raw data writer and write events to disk
        if raw_data_writer:
            try:
                # Get all events from the observer and write to disk
                raw_data_observer = simulation._observer_registry._observers[0]  # Should be our RawDataObserver
                if hasattr(raw_data_observer, 'get_all_events'):
                    events = raw_data_observer.get_all_events()
                    output_file = getattr(raw_data_writer, '_output_file', None)
                    if output_file:
                        raw_data_writer.flush_to_disk(events, str(output_file))
            except Exception:
                pass  # Ignore cleanup errors
        
        return result
    
    def run_all_scenarios(self) -> BaselineResults:
        """Run performance benchmarks for all 7 educational scenarios."""
        print("🚀 VMT EconSim Phase 0 Baseline Capture")
        print(f"   Steps per scenario: {self.steps_per_scenario}")
        print(f"   Warmup steps: {self.warmup_steps}")
        print("=" * 60)
        
        results = []
        total_start_time = time.perf_counter()
        
        # Run all scenarios in sequence
        for scenario_id in sorted(ALL_TEST_CONFIGS.keys()):
            try:
                result = self.run_scenario_benchmark(scenario_id)
                results.append(result)
            except Exception as e:
                print(f"❌ Scenario {scenario_id} failed: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        total_execution_time = time.perf_counter() - total_start_time
        
        # Calculate summary statistics
        if results:
            steps_per_sec_values = [r.steps_per_second for r in results]
            summary = {
                "total_scenarios": len(results),
                "total_execution_time_seconds": total_execution_time,
                "mean_steps_per_second": sum(steps_per_sec_values) / len(steps_per_sec_values),
                "min_steps_per_second": min(steps_per_sec_values),
                "max_steps_per_second": max(steps_per_sec_values),
                "total_simulation_steps": sum(r.total_steps for r in results)
            }
        else:
            summary = {"error": "No scenarios completed successfully"}
        
        baseline_results = BaselineResults(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            python_version=sys.version.split()[0],
            scenarios=results,
            summary=summary
        )
        
        print("=" * 60)
        print("📊 Baseline Capture Summary:")
        if results:
            print(f"   Scenarios completed: {len(results)}/7")
            print(f"   Mean performance: {summary['mean_steps_per_second']:.1f} steps/sec")
            print(f"   Range: {summary['min_steps_per_second']:.1f} - "
                  f"{summary['max_steps_per_second']:.1f} steps/sec")
            print(f"   Total time: {total_execution_time:.1f}s")
        else:
            print("   ❌ No scenarios completed successfully")
        
        return baseline_results


def main():
    """Command-line interface for baseline capture."""
    parser = argparse.ArgumentParser(
        description="VMT EconSim Phase 0 Performance Baseline Capture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full baseline capture (all scenarios)
  python tests/performance/baseline_capture.py > baselines/performance_baseline.json
  
  # Single scenario with custom parameters
  python tests/performance/baseline_capture.py --scenario 1 --steps 500 --warmup 50
  
  # Quick test run
  python tests/performance/baseline_capture.py --steps 100 --warmup 10
        """
    )
    
    parser.add_argument(
        "--scenario", 
        type=int, 
        choices=list(ALL_TEST_CONFIGS.keys()),
        help="Run single scenario (1-7). If not specified, runs all scenarios."
    )
    
    parser.add_argument(
        "--steps", 
        type=int, 
        default=1000,
        help="Number of simulation steps per scenario (default: 1000)"
    )
    
    parser.add_argument(
        "--warmup", 
        type=int, 
        default=100,
        help="Number of warmup steps before measurement (default: 100)"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (default: stdout)"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output (JSON only)"
    )
    
    args = parser.parse_args()
    
    # Suppress progress output if quiet mode
    if args.quiet:
        import io
        sys.stdout = io.StringIO()  # Temporarily redirect stdout
        original_stdout = sys.__stdout__
    
    try:
        capture = BaselineCapture(
            steps_per_scenario=args.steps,
            warmup_steps=args.warmup
        )
        
        if args.scenario:
            # Single scenario mode
            result = capture.run_scenario_benchmark(args.scenario)
            
            # Create minimal baseline result for single scenario
            baseline_results = BaselineResults(
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
                python_version=sys.version.split()[0],
                scenarios=[result],
                summary={
                    "total_scenarios": 1,
                    "mean_steps_per_second": result.steps_per_second,
                    "min_steps_per_second": result.steps_per_second,
                    "max_steps_per_second": result.steps_per_second,
                    "total_simulation_steps": result.total_steps
                }
            )
        else:
            # All scenarios mode
            baseline_results = capture.run_all_scenarios()
        
        # Restore stdout if quiet mode
        if args.quiet:
            sys.stdout = original_stdout
        
        # Output results
        results_json = json.dumps(asdict(baseline_results), indent=2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(results_json)
            if not args.quiet:
                print(f"\n📁 Results saved to: {args.output}")
        else:
            print(results_json)
            
    except KeyboardInterrupt:
        if args.quiet:
            sys.stdout = original_stdout
        print("\n⏹️  Baseline capture interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if args.quiet:
            sys.stdout = original_stdout
        print(f"\n❌ Baseline capture failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()