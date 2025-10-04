#!/usr/bin/env python3
"""Playback example for VMT EconSim observability.

This example demonstrates how to load and replay recorded simulation events
from compressed JSONL files for visualization, debugging, or analysis.

Usage:
    python playback_example.py [input_file.jsonl.gz]

Output:
    - Step-by-step event playback
    - Real-time event processing
    - Custom observer integration for playback
"""

import sys
import os
import json
import gzip
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))

from econsim.observability.base_observer import BaseObserver
from econsim.observability.config import ObservabilityConfig
from econsim.observability.registry import ObserverRegistry


class PlaybackVisualizer(BaseObserver):
    """Custom observer for visualizing simulation playback.
    
    This observer provides real-time visualization of events during playback,
    showing agent movements, trades, and resource collections.
    """
    
    def __init__(self, config: ObservabilityConfig, playback_speed: float = 1.0):
        """Initialize the playback visualizer.
        
        Args:
            config: Observability configuration
            playback_speed: Speed multiplier for playback (1.0 = real-time)
        """
        super().__init__(config)
        
        self.playback_speed = playback_speed
        self.current_step = 0
        self.events_this_step = 0
        
        # Visualization state
        self.agent_positions: Dict[int, tuple] = {}
        self.agent_modes: Dict[int, str] = {}
        self.resource_locations: Dict[tuple, str] = {}
        self.trade_history: List[Dict[str, Any]] = []
        
        print(f"PlaybackVisualizer initialized (speed: {playback_speed}x)")
    
    def _initialize_event_filtering(self) -> None:
        """Process all events for comprehensive visualization."""
        self._enabled_event_types = None  # Accept all events
    
    def notify(self, event) -> None:
        """Process events during playback."""
        if not self.is_enabled(event.event_type):
            return
        
        event_step = getattr(event, 'step', 0)
        
        # Handle step transitions
        if event_step != self.current_step:
            if self.current_step > 0:
                self._print_step_summary()
            self.current_step = event_step
            self.events_this_step = 0
            print(f"\n--- Step {self.current_step} ---")
        
        self.events_this_step += 1
        
        # Process different event types
        if event.event_type == 'agent_mode_change':
            self._visualize_mode_change(event)
        elif event.event_type == 'trade_execution':
            self._visualize_trade(event)
        elif event.event_type == 'resource_collection':
            self._visualize_resource_collection(event)
        elif event.event_type == 'debug_log':
            self._visualize_debug_log(event)
        else:
            self._visualize_generic_event(event)
    
    def _visualize_mode_change(self, event) -> None:
        """Visualize agent mode change events."""
        agent_id = getattr(event, 'agent_id', -1)
        old_mode = getattr(event, 'old_mode', '')
        new_mode = getattr(event, 'new_mode', '')
        reason = getattr(event, 'reason', '')
        
        if agent_id >= 0:
            self.agent_modes[agent_id] = new_mode
            
            reason_text = f" ({reason})" if reason else ""
            print(f"  Agent {agent_id}: {old_mode} → {new_mode}{reason_text}")
    
    def _visualize_trade(self, event) -> None:
        """Visualize trade execution events."""
        seller_id = getattr(event, 'seller_id', -1)
        buyer_id = getattr(event, 'buyer_id', -1)
        give_type = getattr(event, 'give_type', '')
        take_type = getattr(event, 'take_type', '')
        delta_u_seller = getattr(event, 'delta_u_seller', 0.0)
        delta_u_buyer = getattr(event, 'delta_u_buyer', 0.0)
        
        if seller_id >= 0 and buyer_id >= 0:
            cooperation = "🤝" if delta_u_seller > 0 and delta_u_buyer > 0 else "⚔️"
            print(f"  Trade: Agent {seller_id} → Agent {buyer_id} ({give_type} for {take_type}) {cooperation}")
            print(f"    Seller utility: {delta_u_seller:+.2f}, Buyer utility: {delta_u_buyer:+.2f}")
            
            # Track trade history
            self.trade_history.append({
                'step': self.current_step,
                'seller_id': seller_id,
                'buyer_id': buyer_id,
                'give_type': give_type,
                'take_type': take_type,
                'cooperative': delta_u_seller > 0 and delta_u_buyer > 0
            })
    
    def _visualize_resource_collection(self, event) -> None:
        """Visualize resource collection events."""
        agent_id = getattr(event, 'agent_id', -1)
        x = getattr(event, 'x', -1)
        y = getattr(event, 'y', -1)
        resource_type = getattr(event, 'resource_type', '')
        utility_gained = getattr(event, 'utility_gained', 0.0)
        
        if agent_id >= 0 and x >= 0 and y >= 0:
            self.agent_positions[agent_id] = (x, y)
            self.resource_locations[(x, y)] = resource_type
            
            print(f"  Agent {agent_id} collected {resource_type} at ({x},{y}) (+{utility_gained:.2f} utility)")
    
    def _visualize_debug_log(self, event) -> None:
        """Visualize debug log events."""
        category = getattr(event, 'category', '')
        message = getattr(event, 'message', '')
        
        print(f"  [{category}] {message}")
    
    def _visualize_generic_event(self, event) -> None:
        """Visualize generic events."""
        event_type = event.event_type
        print(f"  {event_type}: {dict((k, v) for k, v in event.__dict__.items() if not k.startswith('_'))}")
    
    def _print_step_summary(self) -> None:
        """Print a summary of the current step."""
        if self.events_this_step > 0:
            print(f"    Step {self.current_step}: {self.events_this_step} events")
            
            # Show agent states
            if self.agent_modes:
                active_agents = len([mode for mode in self.agent_modes.values() if mode != 'IDLE'])
                if active_agents > 0:
                    print(f"    Active agents: {active_agents}")
    
    def flush_step(self, step: int) -> None:
        """Handle step boundaries."""
        # Add a small delay for realistic playback
        if self.playback_speed > 0:
            time.sleep(0.1 / self.playback_speed)
    
    def close(self) -> None:
        """Close the visualizer and print final summary."""
        super().close()
        self._print_playback_summary()
    
    def _print_playback_summary(self) -> None:
        """Print a summary of the playback."""
        print("\n=== Playback Summary ===")
        print(f"Total steps played: {self.current_step}")
        print(f"Total trades: {len(self.trade_history)}")
        
        if self.trade_history:
            cooperative_trades = sum(1 for trade in self.trade_history if trade['cooperative'])
            cooperation_rate = cooperative_trades / len(self.trade_history)
            print(f"Cooperation rate: {cooperation_rate:.1%}")
        
        if self.agent_modes:
            print(f"Agents tracked: {len(self.agent_modes)}")
            print(f"Agent modes: {dict(self.agent_modes)}")


class PlaybackAnalyzer(BaseObserver):
    """Custom observer for analyzing events during playback.
    
    This observer provides real-time analysis and statistics
    during the playback process.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """Initialize the playback analyzer."""
        super().__init__(config)
        
        # Analysis state
        self.step_analyses = {}
        self.event_counts = defaultdict(int)
        self.performance_metrics = []
        
        print("PlaybackAnalyzer initialized")
    
    def _initialize_event_filtering(self) -> None:
        """Process all events for comprehensive analysis."""
        self._enabled_event_types = None  # Accept all events
    
    def notify(self, event) -> None:
        """Analyze events during playback."""
        if not self.is_enabled(event.event_type):
            return
        
        # Count events
        self.event_counts[event.event_type] += 1
        
        # Analyze specific event types
        if event.event_type == 'trade_execution':
            self._analyze_trade(event)
        elif event.event_type == 'resource_collection':
            self._analyze_resource_collection(event)
    
    def _analyze_trade(self, event) -> None:
        """Analyze trade events."""
        step = getattr(event, 'step', 0)
        delta_u_seller = getattr(event, 'delta_u_seller', 0.0)
        delta_u_buyer = getattr(event, 'delta_u_buyer', 0.0)
        
        if step not in self.step_analyses:
            self.step_analyses[step] = {
                'trades': 0,
                'cooperative_trades': 0,
                'total_utility_exchanged': 0.0
            }
        
        analysis = self.step_analyses[step]
        analysis['trades'] += 1
        analysis['total_utility_exchanged'] += abs(delta_u_seller) + abs(delta_u_buyer)
        
        if delta_u_seller > 0 and delta_u_buyer > 0:
            analysis['cooperative_trades'] += 1
    
    def _analyze_resource_collection(self, event) -> None:
        """Analyze resource collection events."""
        step = getattr(event, 'step', 0)
        utility_gained = getattr(event, 'utility_gained', 0.0)
        
        if step not in self.step_analyses:
            self.step_analyses[step] = {
                'trades': 0,
                'cooperative_trades': 0,
                'total_utility_exchanged': 0.0,
                'resource_collections': 0,
                'total_utility_from_resources': 0.0
            }
        
        analysis = self.step_analyses[step]
        analysis['resource_collections'] = analysis.get('resource_collections', 0) + 1
        analysis['total_utility_from_resources'] = analysis.get('total_utility_from_resources', 0.0) + utility_gained
    
    def flush_step(self, step: int) -> None:
        """Analyze step completion."""
        if step in self.step_analyses:
            analysis = self.step_analyses[step]
            
            # Calculate step metrics
            cooperation_rate = (analysis['cooperative_trades'] / analysis['trades']) if analysis['trades'] > 0 else 0
            avg_utility_per_collection = (analysis['total_utility_from_resources'] / analysis['resource_collections']) if analysis['resource_collections'] > 0 else 0
            
            step_metrics = {
                'step': step,
                'cooperation_rate': cooperation_rate,
                'avg_utility_per_collection': avg_utility_per_collection,
                'total_utility_exchanged': analysis['total_utility_exchanged']
            }
            
            self.performance_metrics.append(step_metrics)
            
            # Print interesting step analysis
            if analysis['trades'] > 0 or analysis['resource_collections'] > 5:
                print(f"    Step {step} Analysis: {analysis['trades']} trades, {analysis['resource_collections']} collections, cooperation: {cooperation_rate:.1%}")
    
    def close(self) -> None:
        """Close the analyzer and print final analysis."""
        super().close()
        self._print_final_analysis()
    
    def _print_final_analysis(self) -> None:
        """Print final analysis results."""
        print("\n=== Playback Analysis ===")
        print(f"Event type distribution:")
        for event_type, count in sorted(self.event_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {event_type}: {count}")
        
        if self.performance_metrics:
            avg_cooperation = sum(m['cooperation_rate'] for m in self.performance_metrics) / len(self.performance_metrics)
            total_utility = sum(m['total_utility_exchanged'] for m in self.performance_metrics)
            
            print(f"Average cooperation rate: {avg_cooperation:.1%}")
            print(f"Total utility exchanged: {total_utility:.2f}")
            print(f"Steps analyzed: {len(self.performance_metrics)}")


def load_events_for_playback(file_path: Path) -> List[Dict[str, Any]]:
    """Load events from a file for playback.
    
    Args:
        file_path: Path to the event file
        
    Returns:
        List of event dictionaries sorted by step
    """
    events = []
    
    print(f"Loading events for playback from: {file_path}")
    
    # Load events based on file type
    if file_path.suffix == '.gz':
        with gzip.open(file_path, 'rt') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    events.append(event)
                except json.JSONDecodeError:
                    continue
    else:
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    events.append(event)
                except json.JSONDecodeError:
                    continue
    
    # Sort events by step
    events.sort(key=lambda e: e.get('step', 0))
    
    print(f"Loaded {len(events)} events for playback")
    return events


def create_event_object(event_data: Dict[str, Any]) -> Any:
    """Create an event object from dictionary data.
    
    Args:
        event_data: Event dictionary
        
    Returns:
        Event object with attributes
    """
    class EventObject:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    return EventObject(**event_data)


def playback_simulation(events: List[Dict[str, Any]], 
                       playback_speed: float = 1.0,
                       max_steps: Optional[int] = None) -> bool:
    """Playback simulation events with observers.
    
    Args:
        events: List of event dictionaries
        playback_speed: Speed multiplier for playback
        max_steps: Maximum number of steps to play (None = all)
        
    Returns:
        True if playback completed successfully
    """
    print(f"\n=== Starting Playback ===")
    print(f"Events: {len(events)}")
    print(f"Playback speed: {playback_speed}x")
    if max_steps:
        print(f"Max steps: {max_steps}")
    
    # Create observability configuration
    config = ObservabilityConfig.from_environment()
    
    # Create playback observers
    visualizer = PlaybackVisualizer(config, playback_speed)
    analyzer = PlaybackAnalyzer(config)
    
    # Create observer registry
    registry = ObserverRegistry()
    registry.register(visualizer)
    registry.register(analyzer)
    
    print(f"Registered {registry.observer_count()} playback observers")
    
    # Track playback statistics
    events_played = 0
    steps_played = 0
    current_step = -1
    
    try:
        # Process events in order
        for event_data in events:
            # Check step limit
            event_step = event_data.get('step', 0)
            if max_steps and event_step >= max_steps:
                break
            
            # Create event object
            event = create_event_object(event_data)
            
            # Notify observers
            registry.notify(event)
            events_played += 1
            
            # Handle step boundaries
            if event_step != current_step:
                if current_step >= 0:
                    registry.flush_step(current_step)
                    steps_played += 1
                current_step = event_step
            
            # Show progress
            if events_played % 50 == 0:
                print(f"  Playback progress: {events_played}/{len(events)} events, step {current_step}")
        
        # Flush final step
        if current_step >= 0:
            registry.flush_step(current_step)
            steps_played += 1
        
        print(f"\nPlayback completed: {events_played} events, {steps_played} steps")
        
        # Close observers
        registry.close_all()
        
        return True
        
    except KeyboardInterrupt:
        print(f"\nPlayback interrupted by user")
        registry.close_all()
        return False
    except Exception as e:
        print(f"\nPlayback error: {e}")
        registry.close_all()
        return False


def main():
    """Main function for playback example."""
    print("=== Playback Example ===")
    
    # Parse command line arguments
    playback_speed = 1.0
    max_steps = None
    input_file = None
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--speed' and i + 1 < len(sys.argv):
            playback_speed = float(sys.argv[i + 1])
            i += 2
        elif arg == '--max-steps' and i + 1 < len(sys.argv):
            max_steps = int(sys.argv[i + 1])
            i += 2
        elif not arg.startswith('--'):
            input_file = Path(arg)
            i += 1
        else:
            i += 1
    
    # Determine input file
    if input_file is None:
        # Look for example output file
        example_dir = Path("example_output")
        input_file = example_dir / "basic_simulation.jsonl.gz"
        
        if not input_file.exists():
            print(f"Input file not found: {input_file}")
            print("Please provide a path to a JSONL file or run basic_recording.py first")
            print("\nUsage: python playback_example.py [file.jsonl.gz] [--speed 2.0] [--max-steps 50]")
            return False
    
    try:
        # Load events
        events = load_events_for_playback(input_file)
        
        if not events:
            print("No events found in the input file")
            return False
        
        # Start playback
        success = playback_simulation(events, playback_speed, max_steps)
        
        if success:
            print(f"\n✓ Playback completed successfully!")
            print(f"  Input: {input_file}")
            print(f"  Speed: {playback_speed}x")
            if max_steps:
                print(f"  Max steps: {max_steps}")
        else:
            print(f"\n✗ Playback failed or was interrupted")
        
        return success
        
    except Exception as e:
        print(f"Error during playback: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
