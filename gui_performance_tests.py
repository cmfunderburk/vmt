#!/usr/bin/env python3
"""
GUI Performance Tests for VMT Bilateral Exchange System

Test 1: 40 agents, 64x64 grid, density 0.5, perception 10
Test 2: 100 agents, 64x64 grid, density 0.5, perception 15

Each test runs for 1000 turns:
- Turns 1-500: Forage only mode
- Turn 501: Disable forage, agents return home
- Turns 502-1000: Bilateral exchange mode

Metrics recorded: min/max/avg FPS, trade count, resource collection count
"""

import sys
import os
import time
import json
from time import perf_counter
from typing import List, Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set headless mode for testing
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication
from econsim.gui.session_factory import SessionFactory, SimulationSessionDescriptor


def run_performance_test(test_name: str, agents: int, grid_size: tuple[int, int], 
                        density: float, perception: int, target_steps: int = 1000) -> Dict[str, Any]:
    """Run a single performance test with the specified parameters"""
    
    print(f"\n=== Starting {test_name} ===")
    print(f"Agents: {agents}, Grid: {grid_size[0]}x{grid_size[1]}, Density: {density}, Perception: {perception}")
    print(f"Target steps: {target_steps}")
    
    # Phase boundaries
    forage_phase_end = 500
    exchange_phase_start = 502
    
    # Set initial environment for forage-only mode
    os.environ['ECONSIM_FORAGE_ENABLED'] = '1'
    os.environ['ECONSIM_TRADE_DRAFT'] = '0'
    os.environ['ECONSIM_TRADE_EXEC'] = '0'
    
    # Create simulation
    descriptor = SimulationSessionDescriptor(
        name=test_name,
        mode="continuous",
        seed=42,
        grid_size=grid_size,
        agents=agents,
        density=density,
        enable_respawn=True,
        enable_metrics=True,
        preference_type="random",
        turn_auto_interval_ms=None,
        viewport_size=640,  # Large enough for big grids
        start_paused=False
    )
    
    controller = SessionFactory.build(descriptor)
    
    # Track performance and metrics
    fps_samples = []
    step_times = []
    
    # Initial metrics
    initial_trades = 0
    initial_resources = 0
    if controller.simulation and hasattr(controller.simulation, 'metrics_collector'):
        if controller.simulation.metrics_collector:
            try:
                metrics = controller.simulation.metrics_collector.get_metrics()
                initial_trades = len(metrics.get('trade_history', []))
                initial_resources = metrics.get('total_resources_collected', 0)
            except Exception:
                pass
    
    # Timing phases
    test_start = perf_counter()
    forage_end_time = 0.0
    exchange_start_time = 0.0
    
    print("Phase 1: Forage only (steps 1-500)")
    
    # Main simulation loop
    for step in range(target_steps):
        step_start = perf_counter()
        
        # Phase transitions
        if step == forage_phase_end:
            print(f"Step {step}: Ending forage phase")
            forage_end_time = perf_counter()
            os.environ['ECONSIM_FORAGE_ENABLED'] = '0'
            
        elif step == forage_phase_end + 1:
            print(f"Step {step}: Agents returning home...")
            
        elif step == exchange_phase_start:
            print(f"Step {step}: Starting bilateral exchange phase")  
            exchange_start_time = perf_counter()
            os.environ['ECONSIM_TRADE_DRAFT'] = '1'
            os.environ['ECONSIM_TRADE_EXEC'] = '1'
        
        # Step simulation using the controller's manual RNG
        if controller.simulation:
            try:
                controller.simulation.step(controller._manual_rng, use_decision=True)
                # Record step timing performance for stepped advancement
                if hasattr(controller, '_record_step_timestamp'):
                    controller._record_step_timestamp()
            except Exception as e:
                print(f"Step {step} error: {e}")
                break
        
        step_end = perf_counter()
        step_time = step_end - step_start
        step_times.append(step_time)
        
        # Calculate FPS from step time
        if step_time > 0:
            fps_samples.append(1.0 / step_time)
        
        # Progress reporting
        if step % 100 == 0:
            elapsed = step_end - test_start
            avg_fps = len(fps_samples) / elapsed if elapsed > 0 else 0
            print(f"Step {step}/{target_steps} - Elapsed: {elapsed:.1f}s - Avg FPS: {avg_fps:.1f}")
    
    test_end = perf_counter()
    total_duration = test_end - test_start
    
    # Final metrics
    final_trades = 0
    final_resources = 0
    if controller.simulation and hasattr(controller.simulation, 'metrics_collector'):
        if controller.simulation.metrics_collector:
            try:
                metrics = controller.simulation.metrics_collector.get_metrics()
                final_trades = len(metrics.get('trade_history', []))
                final_resources = metrics.get('total_resources_collected', 0)
            except Exception:
                pass
    
    # Calculate performance statistics
    min_fps = min(fps_samples) if fps_samples else 0.0
    max_fps = max(fps_samples) if fps_samples else 0.0
    avg_fps = sum(fps_samples) / len(fps_samples) if fps_samples else 0.0
    
    results = {
        'test_name': test_name,
        'config': {
            'agents': agents,
            'grid_size': grid_size,
            'density': density,
            'perception': perception
        },
        'performance': {
            'min_fps': min_fps,
            'max_fps': max_fps, 
            'avg_fps': avg_fps,
            'total_steps': len(step_times),
            'avg_step_time_ms': (sum(step_times) / len(step_times) * 1000) if step_times else 0.0
        },
        'simulation': {
            'total_trades': final_trades - initial_trades,
            'total_resources_collected': final_resources - initial_resources
        },
        'timing': {
            'forage_phase_duration': forage_end_time - test_start if forage_end_time else 0.0,
            'exchange_phase_duration': test_end - exchange_start_time if exchange_start_time else 0.0,
            'total_test_duration': total_duration
        }
    }
    
    print(f"\n=== {test_name} Complete ===")
    print(f"Total duration: {total_duration:.1f}s")
    print(f"FPS - Min: {min_fps:.1f}, Max: {max_fps:.1f}, Avg: {avg_fps:.1f}")
    print(f"Trades executed: {final_trades - initial_trades}")
    print(f"Resources collected: {final_resources - initial_resources}")
    
    return results


def run_all_tests() -> List[Dict[str, Any]]:
    """Run all performance tests"""
    
    test_configs = [
        {
            'name': 'Test 1: 40 agents, perception 10',
            'agents': 40,
            'grid_size': (64, 64),
            'density': 0.5,
            'perception': 10
        },
        {
            'name': 'Test 2: 100 agents, perception 15',
            'agents': 100,
            'grid_size': (64, 64),
            'density': 0.5,
            'perception': 15
        }
    ]
    
    print("=== VMT GUI Performance Test Suite ===")
    print("Testing bilateral exchange system under high load")
    print(f"Running {len(test_configs)} tests...")
    
    results = []
    
    for i, config in enumerate(test_configs):
        print(f"\n{'='*60}")
        print(f"TEST {i+1}/{len(test_configs)}")
        
        result = run_performance_test(
            config['name'],
            config['agents'],
            config['grid_size'],
            config['density'],
            config['perception']
        )
        results.append(result)
        
        # Brief pause between tests
        time.sleep(1)
    
    return results


def save_results(results: List[Dict[str, Any]]) -> str:
    """Save test results to JSON file"""
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = f'gui_performance_results_{timestamp}.json'
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n=== Performance Test Suite Complete ===")
    print(f"Results saved to: {filename}")
    print("\nSummary:")
    for result in results:
        print(f"{result['test_name']}")
        print(f"  FPS: {result['performance']['avg_fps']:.1f} avg "
              f"({result['performance']['min_fps']:.1f}-{result['performance']['max_fps']:.1f})")
        print(f"  Step Time: {result['performance']['avg_step_time_ms']:.2f}ms avg")
        print(f"  Trades: {result['simulation']['total_trades']}")
        print(f"  Resources: {result['simulation']['total_resources_collected']}")
        print(f"  Duration: {result['timing']['total_test_duration']:.1f}s")
    
    return filename


if __name__ == '__main__':
    try:
        # Initialize Qt application for potential GUI components
        app = QApplication.instance() or QApplication(sys.argv)
        
        # Run tests
        results = run_all_tests()
        
        # Save results
        filename = save_results(results)
        
        print(f"\nPerformance testing complete. Results in {filename}")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        sys.exit(1)