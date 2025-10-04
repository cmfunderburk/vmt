#!/usr/bin/env python3
"""Custom observer example for VMT EconSim observability.

This example demonstrates how to create custom observers that implement
the Observer interface for specialized event processing.

Usage:
    python custom_observer.py

Output:
    - Shows real-time event processing
    - Demonstrates custom observer implementation
    - Provides specialized event filtering and analysis
"""

import sys
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))

from econsim.observability.base_observer import BaseObserver
from econsim.observability.config import ObservabilityConfig
from econsim.observability.registry import ObserverRegistry


class TradeAnalyzer(BaseObserver):
    """Custom observer that analyzes trade patterns in real-time.
    
    This observer tracks trade relationships, cooperation levels,
    and economic dynamics during simulation execution.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """Initialize the trade analyzer."""
        super().__init__(config)
        
        # Trade analysis state
        self.trade_count = 0
        self.trade_pairs: Dict[str, int] = defaultdict(int)
        self.cooperation_events = 0
        self.competition_events = 0
        self.total_utility_exchanged = 0.0
        
        # Agent trading profiles
        self.agent_trades: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
            'trades_made': 0,
            'utility_gained': 0.0,
            'utility_lost': 0.0,
            'trading_partners': set()
        })
        
        print("TradeAnalyzer initialized")
    
    def _initialize_event_filtering(self) -> None:
        """Only process trade-related events."""
        self._enabled_event_types = {'trade_execution'}
    
    def notify(self, event) -> None:
        """Process trade execution events."""
        if not self.is_enabled(event.event_type):
            return
        
        if event.event_type == 'trade_execution':
            self._analyze_trade(event)
    
    def _analyze_trade(self, event) -> None:
        """Analyze a trade execution event."""
        seller_id = getattr(event, 'seller_id', -1)
        buyer_id = getattr(event, 'buyer_id', -1)
        delta_u_seller = getattr(event, 'delta_u_seller', 0.0)
        delta_u_buyer = getattr(event, 'delta_u_buyer', 0.0)
        
        # Update trade count
        self.trade_count += 1
        
        # Track trading relationships
        if seller_id >= 0 and buyer_id >= 0:
            pair_key = f"{min(seller_id, buyer_id)}-{max(seller_id, buyer_id)}"
            self.trade_pairs[pair_key] += 1
            
            # Update agent profiles
            self.agent_trades[seller_id]['trades_made'] += 1
            self.agent_trades[seller_id]['utility_gained'] += delta_u_seller
            self.agent_trades[seller_id]['utility_lost'] += -delta_u_seller
            self.agent_trades[seller_id]['trading_partners'].add(buyer_id)
            
            self.agent_trades[buyer_id]['trades_made'] += 1
            self.agent_trades[buyer_id]['utility_gained'] += delta_u_buyer
            self.agent_trades[buyer_id]['utility_lost'] += -delta_u_buyer
            self.agent_trades[buyer_id]['trading_partners'].add(seller_id)
        
        # Analyze cooperation vs competition
        if delta_u_seller > 0 and delta_u_buyer > 0:
            self.cooperation_events += 1
        else:
            self.competition_events += 1
        
        # Track total utility
        self.total_utility_exchanged += abs(delta_u_seller) + abs(delta_u_buyer)
        
        # Real-time analysis output
        if self.trade_count % 5 == 0:  # Show progress every 5 trades
            self._print_analysis_update()
    
    def _print_analysis_update(self) -> None:
        """Print real-time analysis update."""
        cooperation_rate = self.cooperation_events / self.trade_count if self.trade_count > 0 else 0
        
        print(f"  Trade Analysis Update:")
        print(f"    Total trades: {self.trade_count}")
        print(f"    Cooperation rate: {cooperation_rate:.2%}")
        print(f"    Active trading pairs: {len(self.trade_pairs)}")
        print(f"    Total utility exchanged: {self.total_utility_exchanged:.2f}")
    
    def flush_step(self, step: int) -> None:
        """Handle step boundaries."""
        # Could perform batch analysis here if needed
        pass
    
    def close(self) -> None:
        """Close the analyzer and print final results."""
        super().close()
        self._print_final_analysis()
    
    def _print_final_analysis(self) -> None:
        """Print final trade analysis."""
        print("\n=== Final Trade Analysis ===")
        print(f"Total trades analyzed: {self.trade_count}")
        print(f"Cooperation events: {self.cooperation_events}")
        print(f"Competition events: {self.competition_events}")
        print(f"Cooperation rate: {self.cooperation_events/self.trade_count:.2%}" if self.trade_count > 0 else "No trades")
        print(f"Total utility exchanged: {self.total_utility_exchanged:.2f}")
        
        print(f"\nTrading relationships:")
        for pair, count in sorted(self.trade_pairs.items(), key=lambda x: x[1], reverse=True):
            print(f"  Agents {pair}: {count} trades")
        
        print(f"\nAgent trading profiles:")
        for agent_id, profile in self.agent_trades.items():
            if profile['trades_made'] > 0:
                net_utility = profile['utility_gained'] - profile['utility_lost']
                print(f"  Agent {agent_id}: {profile['trades_made']} trades, "
                      f"net utility: {net_utility:+.2f}, "
                      f"partners: {len(profile['trading_partners'])}")


class ResourceTracker(BaseObserver):
    """Custom observer that tracks resource collection patterns.
    
    This observer monitors resource collection efficiency,
    spatial patterns, and resource competition.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """Initialize the resource tracker."""
        super().__init__(config)
        
        # Resource tracking state
        self.collection_count = 0
        self.resource_types: Dict[str, int] = defaultdict(int)
        self.location_usage: Dict[str, int] = defaultdict(int)
        self.agent_efficiency: Dict[int, List[float]] = defaultdict(list)
        
        print("ResourceTracker initialized")
    
    def _initialize_event_filtering(self) -> None:
        """Only process resource-related events."""
        self._enabled_event_types = {'resource_collection'}
    
    def notify(self, event) -> None:
        """Process resource collection events."""
        if not self.is_enabled(event.event_type):
            return
        
        if event.event_type == 'resource_collection':
            self._track_collection(event)
    
    def _track_collection(self, event) -> None:
        """Track a resource collection event."""
        agent_id = getattr(event, 'agent_id', -1)
        x = getattr(event, 'x', -1)
        y = getattr(event, 'y', -1)
        resource_type = getattr(event, 'resource_type', 'unknown')
        utility_gained = getattr(event, 'utility_gained', 0.0)
        
        # Update counts
        self.collection_count += 1
        self.resource_types[resource_type] += 1
        
        # Track location usage
        if x >= 0 and y >= 0:
            location_key = f"({x},{y})"
            self.location_usage[location_key] += 1
        
        # Track agent efficiency
        if agent_id >= 0 and utility_gained > 0:
            self.agent_efficiency[agent_id].append(utility_gained)
        
        # Real-time updates
        if self.collection_count % 10 == 0:
            self._print_tracking_update()
    
    def _print_tracking_update(self) -> None:
        """Print real-time tracking update."""
        print(f"  Resource Tracking Update:")
        print(f"    Collections: {self.collection_count}")
        print(f"    Resource types: {dict(self.resource_types)}")
        print(f"    Active locations: {len(self.location_usage)}")
    
    def flush_step(self, step: int) -> None:
        """Handle step boundaries."""
        pass
    
    def close(self) -> None:
        """Close the tracker and print final results."""
        super().close()
        self._print_final_tracking()
    
    def _print_final_tracking(self) -> None:
        """Print final resource tracking analysis."""
        print("\n=== Final Resource Analysis ===")
        print(f"Total collections: {self.collection_count}")
        print(f"Resource type distribution: {dict(self.resource_types)}")
        
        # Find competition hotspots (locations with multiple collections)
        hotspots = [(loc, count) for loc, count in self.location_usage.items() if count > 1]
        if hotspots:
            print(f"Competition hotspots: {len(hotspots)}")
            for loc, count in sorted(hotspots, key=lambda x: x[1], reverse=True)[:3]:
                print(f"  {loc}: {count} collections")
        
        # Agent efficiency analysis
        if self.agent_efficiency:
            print(f"Agent efficiency (avg utility per collection):")
            for agent_id, utilities in self.agent_efficiency.items():
                avg_utility = sum(utilities) / len(utilities)
                print(f"  Agent {agent_id}: {avg_utility:.3f} avg utility ({len(utilities)} collections)")


class PerformanceMonitor(BaseObserver):
    """Custom observer that monitors simulation performance.
    
    This observer tracks event processing rates, step timing,
    and performance metrics during simulation execution.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """Initialize the performance monitor."""
        super().__init__(config)
        
        # Performance tracking state
        self.events_processed = 0
        self.steps_processed = 0
        self.step_times: List[float] = []
        self.event_times: List[float] = []
        self.start_time = None
        
        print("PerformanceMonitor initialized")
    
    def _initialize_event_filtering(self) -> None:
        """Process all event types for performance monitoring."""
        self._enabled_event_types = None  # Accept all events
    
    def notify(self, event) -> None:
        """Process any event for performance monitoring."""
        if not self.is_enabled(event.event_type):
            return
        
        import time
        
        if self.start_time is None:
            self.start_time = time.time()
        
        # Track event processing
        event_start = time.time()
        self.events_processed += 1
        
        # Simulate some processing time
        time.sleep(0.0001)  # 0.1ms processing time
        
        event_time = time.time() - event_start
        self.event_times.append(event_time)
        
        # Show performance updates
        if self.events_processed % 50 == 0:
            self._print_performance_update()
    
    def flush_step(self, step: int) -> None:
        """Track step completion."""
        import time
        
        if self.start_time is not None:
            step_time = time.time() - self.start_time
            self.step_times.append(step_time)
            self.steps_processed += 1
    
    def _print_performance_update(self) -> None:
        """Print real-time performance update."""
        if not self.event_times:
            return
        
        avg_event_time = sum(self.event_times) / len(self.event_times)
        events_per_second = 1.0 / avg_event_time if avg_event_time > 0 else 0
        
        print(f"  Performance Update:")
        print(f"    Events processed: {self.events_processed}")
        print(f"    Avg event time: {avg_event_time*1000:.3f}ms")
        print(f"    Events/sec: {events_per_second:.0f}")
    
    def close(self) -> None:
        """Close the monitor and print final results."""
        super().close()
        self._print_final_performance()
    
    def _print_final_performance(self) -> None:
        """Print final performance analysis."""
        if not self.event_times:
            return
        
        total_time = sum(self.event_times)
        avg_event_time = sum(self.event_times) / len(self.event_times)
        events_per_second = len(self.event_times) / total_time if total_time > 0 else 0
        
        print("\n=== Final Performance Analysis ===")
        print(f"Total events processed: {self.events_processed}")
        print(f"Total processing time: {total_time:.3f}s")
        print(f"Average event time: {avg_event_time*1000:.3f}ms")
        print(f"Events per second: {events_per_second:.0f}")
        print(f"Steps processed: {self.steps_processed}")


def create_mock_simulation_events():
    """Create mock simulation events for demonstration."""
    events = []
    
    # Simulate 50 steps of a simulation
    for step in range(50):
        # Add trade events
        if step % 5 == 0 and step > 5:
            events.append({
                'event_type': 'trade_execution',
                'step': step,
                'seller_id': 0,
                'buyer_id': 1,
                'give_type': 'wood',
                'take_type': 'stone',
                'delta_u_seller': 0.5 if step % 2 == 0 else -0.2,  # Mix of cooperation/competition
                'delta_u_buyer': 0.3 if step % 2 == 0 else 0.1
            })
        
        # Add resource collection events
        if step % 3 == 0:
            events.append({
                'event_type': 'resource_collection',
                'step': step,
                'agent_id': step % 3,
                'x': (step * 2) % 8,
                'y': (step * 3) % 8,
                'resource_type': 'wood' if step % 2 == 0 else 'stone',
                'amount_collected': 1,
                'utility_gained': 0.1 + (step % 5) * 0.02  # Varying utility
            })
        
        # Add some debug events for performance monitoring
        if step % 10 == 0:
            events.append({
                'event_type': 'debug_log',
                'step': step,
                'category': 'PERFORMANCE',
                'message': f'Step {step} performance check',
                'agent_id': -1
            })
    
    return events


def custom_observer_example():
    """Demonstrate custom observers with specialized functionality."""
    print("=== Custom Observer Example ===")
    
    # Create observability configuration
    config = ObservabilityConfig.from_environment()
    
    # Create custom observers
    trade_analyzer = TradeAnalyzer(config)
    resource_tracker = ResourceTracker(config)
    performance_monitor = PerformanceMonitor(config)
    
    # Create observer registry and register observers
    registry = ObserverRegistry()
    registry.register(trade_analyzer)
    registry.register(resource_tracker)
    registry.register(performance_monitor)
    
    print(f"Registered {registry.observer_count()} custom observers")
    
    # Create mock simulation events
    mock_events = create_mock_simulation_events()
    print(f"Created {len(mock_events)} mock simulation events")
    
    # Process events through registry
    print("Processing events through custom observers...")
    
    for i, event_data in enumerate(mock_events):
        # Create a simple event object
        class MockEvent:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        event = MockEvent(**event_data)
        
        # Notify all observers through registry
        registry.notify(event)
        
        # Handle step boundaries
        if (i + 1) % 10 == 0:
            registry.flush_step(i // 10)
        
        # Show progress
        if (i + 1) % 15 == 0:
            print(f"  Processed {i + 1}/{len(mock_events)} events")
    
    print("Event processing complete")
    
    # Close all observers
    print("Closing observers...")
    registry.close_all()
    
    print("\n=== Example Complete ===")
    print("Custom observers have analyzed the simulation data")
    print("Each observer provided specialized insights:")
    print("  - TradeAnalyzer: Economic relationship analysis")
    print("  - ResourceTracker: Resource collection patterns")
    print("  - PerformanceMonitor: Event processing performance")
    
    return True


if __name__ == "__main__":
    success = custom_observer_example()
    if success:
        print("\n✓ Custom observer example completed successfully!")
    else:
        print("\n✗ Custom observer example failed!")
        sys.exit(1)
