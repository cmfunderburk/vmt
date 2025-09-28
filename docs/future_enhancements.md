# VMT Future Enhancements Enabled by Programmatic Runner

**Updated**: September 28, 2025  
**Phase**: 6 - Programmatic Runner Foundation Complete

## Overview

The programmatic TestRunner implementation has unlocked significant new capabilities for the VMT Educational Simulation platform. By eliminating subprocess dependencies and providing direct framework access, we can now implement advanced automation, integration, and analysis features.

## Enabled Capabilities Summary

### 🔄 **Automated Test Sequences**
Execute multiple tests programmatically for tutorials, demonstrations, and validation workflows.

### 📊 **Parameter Sweeping**  
Dynamically modify simulation parameters and collect results for educational analysis.

### 🔗 **External Framework Integration**
Connect VMT to CI/CD pipelines, automated testing systems, and educational platforms.

### 📦 **Batch Test Execution**
Run multiple configurations in parallel or sequence for comprehensive evaluation.

## Implementation Guides

### 1. Automated Test Sequences

#### Tutorial Automation
```python
"""Educational tutorial automation using programmatic TestRunner."""

from src.econsim.tools.launcher.test_runner import create_test_runner
import time

class VMTTutorial:
    """Automated tutorial system for economic concepts."""
    
    def __init__(self):
        self.runner = create_test_runner()
        self.tutorial_steps = []
    
    def add_tutorial_step(self, test_id, duration, description):
        """Add tutorial step with test, timing, and educational context."""
        self.tutorial_steps.append({
            'test_id': test_id,
            'duration': duration,
            'description': description
        })
    
    def run_tutorial(self, interactive=True):
        """Execute complete tutorial sequence."""
        print("🎓 Starting VMT Economics Tutorial")
        
        for i, step in enumerate(self.tutorial_steps, 1):
            print(f"\n📚 Step {i}: {step['description']}")
            
            # Launch test
            self.runner.run_by_id(step['test_id'], "framework")
            
            if interactive:
                input(f"Press Enter when ready for next step...")
                self.runner.close_current_test()
            else:
                time.sleep(step['duration'])
                self.runner.close_current_test()

# Example: Economic Preferences Tutorial
def create_preferences_tutorial():
    """Create tutorial covering different economic preference types."""
    tutorial = VMTTutorial()
    
    # Tutorial sequence
    tutorial.add_tutorial_step(1, 30, "Baseline Behavior - Mixed Preferences")
    tutorial.add_tutorial_step(5, 30, "Pure Cobb-Douglas - Substitutable Goods") 
    tutorial.add_tutorial_step(6, 30, "Pure Leontief - Complementary Goods")
    tutorial.add_tutorial_step(7, 30, "Perfect Substitutes - Identical Utility")
    
    return tutorial

# Usage
tutorial = create_preferences_tutorial()
tutorial.run_tutorial(interactive=True)
```

#### Demonstration Sequences
```python
"""Automated demonstration system for classroom presentation."""

class VMTDemonstration:
    """Presentation-ready demonstration sequences."""
    
    def __init__(self):
        self.runner = create_test_runner()
    
    def spatial_behavior_demo(self):
        """Demonstrate spatial economic behavior patterns."""
        demos = [
            (2, "Sparse Long-Range: Agents seek distant opportunities"),
            (3, "High Density Local: Agents prefer nearby interactions"),
            (4, "Large World Global: Macro-scale economic patterns")
        ]
        
        for test_id, description in demos:
            print(f"\n🎯 {description}")
            self.runner.run_by_id(test_id, "framework")
            
            # Pause for presentation/discussion
            input("Press Enter to continue to next demonstration...")
            self.runner.close_current_test()
    
    def preference_comparison_demo(self):
        """Side-by-side preference type comparison.""" 
        preference_tests = [
            (5, "Cobb-Douglas: Balanced substitution behavior"),
            (6, "Leontief: Must have both goods equally"),
            (7, "Perfect Substitutes: Complete interchangeability")
        ]
        
        print("🔬 Economic Preference Types Comparison")
        for test_id, description in preference_tests:
            print(f"\n📊 {description}")
            self.runner.run_by_id(test_id, "framework")
            
            # Educational pause
            input("Observe agent behavior, then press Enter...")
            self.runner.close_current_test()

# Usage in classroom
demo = VMTDemonstration()
demo.spatial_behavior_demo()
demo.preference_comparison_demo()
```

### 2. Parameter Sweeping Capabilities

#### Dynamic Configuration Modification
```python
"""Parameter sweeping for educational analysis and research."""

from src.econsim.tools.launcher.framework.test_configs import TestConfiguration
from src.econsim.simulation.config import SimConfig
import itertools

class VMTParameterSweep:
    """Systematic parameter variation for educational exploration."""
    
    def __init__(self):
        self.runner = create_test_runner()
        self.results = []
    
    def sweep_distance_scaling(self, base_test_id=1):
        """Sweep distance scaling factor to show spatial behavior impact."""
        distance_factors = [0.0, 1.0, 2.5, 5.0]  # k=0 to k=5
        
        print("📈 Distance Scaling Factor Analysis")
        print("Demonstrates how distance affects agent economic decisions")
        
        for k in distance_factors:
            print(f"\n🎯 Testing k={k} (distance penalty factor)")
            
            # Create modified configuration
            modified_config = self._create_modified_config(
                base_test_id, 
                distance_scaling_factor=k
            )
            
            # Run with modified parameters
            self.runner.run_config(modified_config, "framework")
            
            # Educational observation period
            input(f"Observe agent behavior with k={k}, then press Enter...")
            self.runner.close_current_test()
            
            # Record observations (could be automated with metrics)
            behavior = input("Describe observed behavior: ")
            self.results.append({
                'distance_factor': k,
                'behavior': behavior
            })
    
    def sweep_grid_density(self):
        """Explore economic behavior across different population densities."""
        grid_configs = [
            ((8, 8), "Low density - sparse interactions"),
            ((12, 12), "Medium density - balanced interactions"), 
            ((16, 16), "High density - frequent interactions")
        ]
        
        print("🏘️ Population Density Impact Analysis")
        
        for grid_size, description in grid_configs:
            print(f"\n📊 {description} - {grid_size[0]}x{grid_size[1]} grid")
            
            modified_config = self._create_modified_config(
                1,  # Base configuration
                grid_size=grid_size
            )
            
            self.runner.run_config(modified_config, "framework")
            
            input(f"Observe {description}, then press Enter...")
            self.runner.close_current_test()
    
    def _create_modified_config(self, base_id, **modifications):
        """Create TestConfiguration with parameter modifications."""
        # Get base configuration
        base_config = self.runner._get_config_by_id(base_id)
        
        # Create modified SimConfig 
        modified_sim_config = SimConfig(
            grid_size=modifications.get('grid_size', base_config.sim_config.grid_size),
            distance_scaling_factor=modifications.get('distance_scaling_factor', 
                                                    base_config.sim_config.distance_scaling_factor),
            # Preserve other base parameters
            seed=base_config.sim_config.seed,
            enable_respawn=base_config.sim_config.enable_respawn,
            enable_metrics=base_config.sim_config.enable_metrics
        )
        
        # Create new TestConfiguration
        return TestConfiguration(
            id=base_config.id,
            name=f"{base_config.name} (Modified)",
            sim_config=modified_sim_config
        )

# Usage for educational exploration
sweep = VMTParameterSweep()
sweep.sweep_distance_scaling()
sweep.sweep_grid_density()

# Review collected results
for result in sweep.results:
    print(f"k={result['distance_factor']}: {result['behavior']}")
```

#### Automated Parameter Studies
```python
"""Research-grade parameter studies with data collection."""

class VMTResearchSweep:
    """Systematic parameter analysis with metric collection."""
    
    def __init__(self):
        self.runner = create_test_runner()
        self.data = []
    
    def comprehensive_preference_study(self):
        """Study all preference types across parameter ranges."""
        preference_tests = [5, 6, 7]  # Cobb-Douglas, Leontief, Perfect Substitutes
        distance_factors = [0.0, 2.5, 5.0]
        grid_sizes = [(8, 8), (12, 12), (16, 16)]
        
        # Full factorial design
        for test_id, k, grid in itertools.product(preference_tests, distance_factors, grid_sizes):
            print(f"🔬 Running: Test {test_id}, k={k}, grid={grid}")
            
            # Create configuration
            config = self._create_research_config(test_id, k, grid)
            
            # Run simulation (could be automated with metrics collection)
            self.runner.run_config(config, "framework")
            
            # Collect data (placeholder - would integrate with metrics system)
            # In full implementation: collect trade counts, efficiency metrics, etc.
            self.data.append({
                'test_id': test_id,
                'distance_factor': k,
                'grid_size': grid,
                'timestamp': time.time()
            })
            
            # Brief observation period  
            time.sleep(5)  # Or integrate metrics collection
            self.runner.close_current_test()
        
        return self.data
    
    def _create_research_config(self, test_id, distance_factor, grid_size):
        """Create research configuration with specific parameters."""
        base_config = self.runner._get_config_by_id(test_id)
        
        research_sim_config = SimConfig(
            grid_size=grid_size,
            distance_scaling_factor=distance_factor,
            seed=42,  # Fixed seed for reproducibility
            enable_respawn=True,
            enable_metrics=True  # Enable for data collection
        )
        
        return TestConfiguration(
            id=test_id,
            name=f"Research: {base_config.name} k={distance_factor} {grid_size}",
            sim_config=research_sim_config
        )
```

### 3. External Framework Integration

#### CI/CD Pipeline Integration
```python
"""Integration with continuous integration and deployment systems."""

import subprocess
import json
from pathlib import Path

class VMTCIPipeline:
    """CI/CD integration for automated testing and validation."""
    
    def __init__(self):
        self.runner = create_test_runner()
    
    def validate_all_configurations(self):
        """Validate all test configurations launch successfully."""
        results = {}
        available_tests = self.runner.get_available_tests()
        
        print("🔍 CI/CD Validation: Testing all configurations")
        
        for test_id, test_name in available_tests.items():
            try:
                print(f"  Testing {test_id}: {test_name}...")
                
                # Launch test
                start_time = time.time()
                self.runner.run_by_id(test_id, "framework")
                launch_time = time.time() - start_time
                
                # Validate window creation
                status = self.runner.get_status()
                window_created = status['current_test']
                
                # Close test
                self.runner.close_current_test()
                
                results[test_id] = {
                    'status': 'PASS',
                    'launch_time': launch_time,
                    'window_created': window_created
                }
                
                print(f"    ✅ PASS ({launch_time:.3f}s)")
                
            except Exception as e:
                results[test_id] = {
                    'status': 'FAIL',
                    'error': str(e)
                }
                print(f"    ❌ FAIL: {e}")
        
        return results
    
    def generate_ci_report(self, results):
        """Generate CI-compatible test report."""
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r['status'] == 'PASS')
        
        report = {
            'summary': {
                'total': total_tests,
                'passed': passed_tests,
                'failed': total_tests - passed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0
            },
            'details': results,
            'timestamp': time.time()
        }
        
        # Save report for CI system
        report_path = Path("test_results.json")
        with report_path.open('w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 CI Report: {passed_tests}/{total_tests} tests passed")
        print(f"Report saved to: {report_path}")
        
        return report

# Usage in CI/CD pipeline
def ci_validation():
    """Main CI validation entry point."""
    pipeline = VMTCIPipeline()
    results = pipeline.validate_all_configurations()
    report = pipeline.generate_ci_report(results)
    
    # Return appropriate exit code for CI system
    return 0 if report['summary']['failed'] == 0 else 1

if __name__ == "__main__":
    exit_code = ci_validation()
    sys.exit(exit_code)
```

#### Educational Platform Integration
```python
"""Integration with Learning Management Systems (LMS)."""

class VMTLMSIntegration:
    """Integration layer for educational platforms."""
    
    def __init__(self, lms_api_key=None):
        self.runner = create_test_runner()
        self.lms_api_key = lms_api_key
        self.session_data = []
    
    def create_assignment_session(self, student_id, assignment_config):
        """Create guided learning session for individual student."""
        print(f"📚 Starting assignment session for student {student_id}")
        
        session = {
            'student_id': student_id,
            'start_time': time.time(),
            'tests_completed': [],
            'observations': []
        }
        
        for step in assignment_config['steps']:
            test_id = step['test_id']
            prompt = step.get('prompt', '')
            duration = step.get('duration', 300)  # 5 minutes default
            
            print(f"\n📖 {prompt}")
            print(f"🎯 Launching Test {test_id}")
            
            # Launch test
            self.runner.run_by_id(test_id, "framework")
            
            # Collect student observations
            observation = input("Describe what you observe: ")
            session['observations'].append({
                'test_id': test_id,
                'observation': observation,
                'timestamp': time.time()
            })
            
            session['tests_completed'].append(test_id)
            self.runner.close_current_test()
        
        session['end_time'] = time.time()
        session['duration'] = session['end_time'] - session['start_time']
        
        # Submit to LMS (placeholder)
        self._submit_session_to_lms(session)
        
        return session
    
    def _submit_session_to_lms(self, session):
        """Submit session data to Learning Management System."""
        # Placeholder for LMS API integration
        print(f"📤 Submitting session data to LMS for student {session['student_id']}")
        print(f"   Duration: {session['duration']:.0f}s")
        print(f"   Tests completed: {len(session['tests_completed'])}")

# Example assignment configuration
preferences_assignment = {
    'name': 'Economic Preferences Exploration',
    'steps': [
        {
            'test_id': 1,
            'prompt': 'Observe the baseline mixed-preference behavior',
            'duration': 180
        },
        {
            'test_id': 5, 
            'prompt': 'Compare with pure Cobb-Douglas preferences',
            'duration': 180
        },
        {
            'test_id': 6,
            'prompt': 'Contrast with Leontief complementary goods',
            'duration': 180
        }
    ]
}

# Usage
lms = VMTLMSIntegration()
session = lms.create_assignment_session("student_123", preferences_assignment)
```

### 4. Batch Test Execution Modes

#### Parallel Test Execution
```python
"""Parallel execution for performance testing and analysis."""

import concurrent.futures
import threading

class VMTBatchExecutor:
    """Batch and parallel test execution capabilities."""
    
    def __init__(self, max_workers=3):
        self.max_workers = max_workers
        self.results = []
        self.lock = threading.Lock()
    
    def parallel_validation_suite(self):
        """Run validation tests in parallel for speed."""
        test_configs = [
            {'test_id': 1, 'description': 'Baseline validation'},
            {'test_id': 3, 'description': 'High density validation'},
            {'test_id': 5, 'description': 'Cobb-Douglas validation'}
        ]
        
        print(f"🚀 Running {len(test_configs)} tests in parallel")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tests
            future_to_config = {
                executor.submit(self._run_single_test, config): config 
                for config in test_configs
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_config):
                config = future_to_config[future]
                try:
                    result = future.result()
                    with self.lock:
                        self.results.append(result)
                    print(f"✅ {config['description']} completed")
                except Exception as e:
                    print(f"❌ {config['description']} failed: {e}")
        
        return self.results
    
    def _run_single_test(self, config):
        """Run individual test (thread-safe)."""
        # Each thread gets its own runner instance
        runner = create_test_runner()
        
        start_time = time.time()
        runner.run_by_id(config['test_id'], "framework")
        
        # Brief execution period
        time.sleep(2)  # Simulate test execution
        
        runner.close_current_test()
        execution_time = time.time() - start_time
        
        return {
            'test_id': config['test_id'],
            'description': config['description'],
            'execution_time': execution_time,
            'success': True
        }
    
    def sequential_comparison_suite(self):
        """Run tests sequentially for comparative analysis."""
        comparison_pairs = [
            (2, 3, "Sparse vs Dense Population"),
            (5, 6, "Cobb-Douglas vs Leontief"),
            (6, 7, "Leontief vs Perfect Substitutes")
        ]
        
        print("🔍 Sequential Comparison Analysis")
        
        for test_a, test_b, description in comparison_pairs:
            print(f"\n📊 {description}")
            
            # Run first test
            runner = create_test_runner()
            print(f"  Running Test {test_a}...")
            runner.run_by_id(test_a, "framework")
            
            input("  Observe first test behavior, then press Enter...")
            runner.close_current_test()
            
            # Run second test
            print(f"  Running Test {test_b}...")
            runner.run_by_id(test_b, "framework")
            
            input("  Observe second test behavior, then press Enter...")
            runner.close_current_test()
            
            # Collect comparison
            comparison = input("  Describe the key differences: ")
            
            self.results.append({
                'comparison': description,
                'test_a': test_a,
                'test_b': test_b,
                'differences': comparison
            })

# Usage examples
batch = VMTBatchExecutor()

# Parallel validation
parallel_results = batch.parallel_validation_suite()

# Sequential comparison
batch.sequential_comparison_suite()
```

## Implementation Roadmap

### Phase 1: Tutorial System (Immediate)
- ✅ Programmatic TestRunner foundation complete
- 🔄 Implement `VMTTutorial` class with step sequences
- 🔄 Create standard educational tutorial configurations
- 🔄 Add interactive and automated execution modes

### Phase 2: Parameter Sweeping (Short-term)
- 🔄 Implement dynamic TestConfiguration modification
- 🔄 Create educational parameter exploration tools
- 🔄 Add data collection and visualization integration
- 🔄 Build research-grade systematic analysis tools

### Phase 3: External Integration (Medium-term) 
- 🔄 Develop CI/CD pipeline integration utilities
- 🔄 Create LMS integration framework
- 🔄 Build API endpoints for external system access
- 🔄 Implement authentication and session management

### Phase 4: Advanced Analytics (Long-term)
- 🔄 Integrate with simulation metrics system
- 🔄 Automated performance benchmarking
- 🔄 Statistical analysis and reporting tools
- 🔄 Machine learning integration for pattern analysis

## Technical Requirements

### Dependencies
- **Core**: Programmatic TestRunner (✅ Complete)
- **Parallel Processing**: `concurrent.futures` (Python standard library)
- **Data Analysis**: `pandas`, `numpy` (optional, for advanced analytics)
- **Web Integration**: `requests`, `flask` (for LMS/API integration)

### Performance Considerations
- **Memory Management**: Each TestRunner instance is stateless
- **Resource Limits**: Parallel execution limited by system resources
- **Cleanup**: Ensure proper window closure in batch operations
- **Error Handling**: Robust exception handling for production use

### Security Considerations
- **API Keys**: Secure storage for external system integration
- **Data Privacy**: Student data handling compliance (FERPA, etc.)
- **Network Security**: HTTPS for external API communication
- **Access Control**: User authentication for advanced features

---

**The programmatic TestRunner foundation enables all these advanced capabilities while maintaining the educational focus and deterministic behavior that makes VMT valuable for teaching microeconomics.**