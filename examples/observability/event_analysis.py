#!/usr/bin/env python3
"""Event analysis example for VMT EconSim observability.

This example demonstrates how to analyze recorded simulation events
from compressed JSONL files to extract insights and patterns.

Usage:
    python event_analysis.py [input_file.jsonl.gz]

Output:
    - Comprehensive analysis of simulation events
    - Statistical summaries and pattern detection
    - Visualization-ready data structures
"""

import sys
import os
import json
import gzip
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple
import statistics

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))


def load_simulation_events(file_path: Path) -> List[Dict[str, Any]]:
    """Load simulation events from a compressed JSONL file.
    
    Args:
        file_path: Path to the compressed JSONL file
        
    Returns:
        List of event dictionaries
    """
    events = []
    
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    print(f"Loading events from: {file_path}")
    
    # Handle compressed files
    if file_path.suffix == '.gz':
        with gzip.open(file_path, 'rt') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    event = json.loads(line.strip())
                    events.append(event)
                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON on line {line_num}: {e}")
    else:
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    event = json.loads(line.strip())
                    events.append(event)
                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON on line {line_num}: {e}")
    
    print(f"Loaded {len(events)} events")
    return events


def analyze_event_distribution(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the distribution of event types.
    
    Args:
        events: List of event dictionaries
        
    Returns:
        Dictionary containing event distribution analysis
    """
    event_counts = Counter(event.get('event_type', 'unknown') for event in events)
    
    total_events = len(events)
    
    analysis = {
        'total_events': total_events,
        'event_type_counts': dict(event_counts),
        'event_type_percentages': {
            event_type: (count / total_events) * 100 
            for event_type, count in event_counts.items()
        },
        'unique_event_types': len(event_counts),
        'most_common_event': event_counts.most_common(1)[0] if event_counts else None
    }
    
    return analysis


def analyze_temporal_patterns(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze temporal patterns in the simulation.
    
    Args:
        events: List of event dictionaries
        
    Returns:
        Dictionary containing temporal analysis
    """
    # Extract step information
    steps = [event.get('step', 0) for event in events if 'step' in event]
    
    if not steps:
        return {'error': 'No step information found in events'}
    
    step_range = (min(steps), max(steps))
    
    # Events per step
    events_per_step = defaultdict(int)
    for event in events:
        step = event.get('step', 0)
        events_per_step[step] += 1
    
    # Calculate statistics
    step_event_counts = list(events_per_step.values())
    
    analysis = {
        'step_range': step_range,
        'total_steps': len(events_per_step),
        'events_per_step': {
            'mean': statistics.mean(step_event_counts),
            'median': statistics.median(step_event_counts),
            'std_dev': statistics.stdev(step_event_counts) if len(step_event_counts) > 1 else 0,
            'min': min(step_event_counts),
            'max': max(step_event_counts)
        },
        'busiest_steps': sorted(events_per_step.items(), key=lambda x: x[1], reverse=True)[:5],
        'quietest_steps': sorted(events_per_step.items(), key=lambda x: x[1])[:5]
    }
    
    return analysis


def analyze_trade_patterns(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze trade execution patterns.
    
    Args:
        events: List of event dictionaries
        
    Returns:
        Dictionary containing trade analysis
    """
    trade_events = [event for event in events if event.get('event_type') == 'trade']
    
    if not trade_events:
        return {'total_trades': 0, 'message': 'No trade events found'}
    
    # Trade relationship analysis
    trade_pairs = defaultdict(int)
    cooperation_events = 0
    competition_events = 0
    
    # Resource type analysis
    give_types = Counter()
    take_types = Counter()
    
    # Utility analysis
    seller_utilities = []
    buyer_utilities = []
    
    for event in trade_events:
        seller_id = event.get('seller_id', -1)
        buyer_id = event.get('buyer_id', -1)
        delta_u_seller = event.get('delta_u_seller', 0.0)
        delta_u_buyer = event.get('delta_u_buyer', 0.0)
        give_type = event.get('give_type', '')
        take_type = event.get('take_type', '')
        
        # Track trading pairs
        if seller_id >= 0 and buyer_id >= 0:
            pair_key = f"{min(seller_id, buyer_id)}-{max(seller_id, buyer_id)}"
            trade_pairs[pair_key] += 1
        
        # Analyze cooperation vs competition
        if delta_u_seller > 0 and delta_u_buyer > 0:
            cooperation_events += 1
        else:
            competition_events += 1
        
        # Track resource types
        if give_type:
            give_types[give_type] += 1
        if take_type:
            take_types[take_type] += 1
        
        # Track utilities
        seller_utilities.append(delta_u_seller)
        buyer_utilities.append(delta_u_buyer)
    
    total_trades = len(trade_events)
    cooperation_rate = cooperation_events / total_trades if total_trades > 0 else 0
    
    analysis = {
        'total_trades': total_trades,
        'cooperation_events': cooperation_events,
        'competition_events': competition_events,
        'cooperation_rate': cooperation_rate,
        'active_trading_pairs': len(trade_pairs),
        'most_active_pairs': sorted(trade_pairs.items(), key=lambda x: x[1], reverse=True)[:5],
        'resource_types_given': dict(give_types),
        'resource_types_taken': dict(take_types),
        'utility_analysis': {
            'seller_utility': {
                'mean': statistics.mean(seller_utilities),
                'median': statistics.median(seller_utilities),
                'std_dev': statistics.stdev(seller_utilities) if len(seller_utilities) > 1 else 0,
                'min': min(seller_utilities),
                'max': max(seller_utilities)
            },
            'buyer_utility': {
                'mean': statistics.mean(buyer_utilities),
                'median': statistics.median(buyer_utilities),
                'std_dev': statistics.stdev(buyer_utilities) if len(buyer_utilities) > 1 else 0,
                'min': min(buyer_utilities),
                'max': max(buyer_utilities)
            }
        }
    }
    
    return analysis


def analyze_agent_behavior(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze agent behavior patterns.
    
    Args:
        events: List of event dictionaries
        
    Returns:
        Dictionary containing agent behavior analysis
    """
    # Extract agent IDs from all events
    agent_ids = set()
    for event in events:
        for key in ['agent_id', 'seller_id', 'buyer_id']:
            if key in event and event[key] >= 0:
                agent_ids.add(event[key])
    
    if not agent_ids:
        return {'message': 'No agent information found in events'}
    
    # Analyze mode changes
    mode_events = [event for event in events if event.get('event_type') == 'mode_change']
    
    agent_modes = defaultdict(list)
    mode_transitions = defaultdict(int)
    
    for event in mode_events:
        agent_id = event.get('agent_id', -1)
        old_mode = event.get('old_mode', '')
        new_mode = event.get('new_mode', '')
        
        if agent_id >= 0:
            agent_modes[agent_id].append(new_mode)
            if old_mode and new_mode:
                transition = f"{old_mode} → {new_mode}"
                mode_transitions[transition] += 1
    
    # Analyze resource collection
    resource_events = [event for event in events if event.get('event_type') == 'resource_collection']
    
    agent_collections = defaultdict(int)
    agent_utilities = defaultdict(list)
    
    for event in resource_events:
        agent_id = event.get('agent_id', -1)
        utility_gained = event.get('utility_gained', 0.0)
        
        if agent_id >= 0:
            agent_collections[agent_id] += 1
            if utility_gained > 0:
                agent_utilities[agent_id].append(utility_gained)
    
    # Calculate agent activity scores
    agent_activity = {}
    for agent_id in agent_ids:
        activity_score = 0
        activity_score += agent_collections.get(agent_id, 0) * 1
        activity_score += len(agent_modes.get(agent_id, [])) * 2
        
        # Add trade participation
        trade_participation = sum(1 for event in events 
                                if event.get('event_type') == 'trade' 
                                and (event.get('seller_id') == agent_id or event.get('buyer_id') == agent_id))
        activity_score += trade_participation * 3
        
        agent_activity[agent_id] = activity_score
    
    analysis = {
        'total_agents': len(agent_ids),
        'agent_ids': sorted(agent_ids),
        'mode_changes': len(mode_events),
        'most_common_transitions': sorted(mode_transitions.items(), key=lambda x: x[1], reverse=True)[:5],
        'agent_activity_ranking': sorted(agent_activity.items(), key=lambda x: x[1], reverse=True),
        'resource_collections_by_agent': dict(agent_collections),
        'agent_efficiency': {
            agent_id: {
                'collections': agent_collections.get(agent_id, 0),
                'avg_utility': statistics.mean(agent_utilities.get(agent_id, [0])) if agent_utilities.get(agent_id) else 0,
                'total_utility': sum(agent_utilities.get(agent_id, []))
            }
            for agent_id in agent_ids
        }
    }
    
    return analysis


def analyze_spatial_patterns(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze spatial patterns in the simulation.
    
    Args:
        events: List of event dictionaries
        
    Returns:
        Dictionary containing spatial analysis
    """
    # Extract spatial events
    spatial_events = []
    for event in events:
        if any(key in event for key in ['x', 'y', 'position_x', 'position_y']):
            spatial_events.append(event)
    
    if not spatial_events:
        return {'message': 'No spatial information found in events'}
    
    # Collect coordinates
    coordinates = []
    location_usage = defaultdict(int)
    
    for event in spatial_events:
        x = event.get('x', event.get('position_x', -1))
        y = event.get('y', event.get('position_y', -1))
        
        if x >= 0 and y >= 0:
            coordinates.append((x, y))
            location_usage[(x, y)] += 1
    
    if not coordinates:
        return {'message': 'No valid coordinates found in events'}
    
    # Calculate spatial statistics
    x_coords = [coord[0] for coord in coordinates]
    y_coords = [coord[1] for coord in coordinates]
    
    # Find hotspots (locations with multiple events)
    hotspots = [(loc, count) for loc, count in location_usage.items() if count > 1]
    
    analysis = {
        'total_spatial_events': len(spatial_events),
        'unique_locations': len(location_usage),
        'spatial_range': {
            'x': (min(x_coords), max(x_coords)),
            'y': (min(y_coords), max(y_coords))
        },
        'spatial_center': {
            'x': statistics.mean(x_coords),
            'y': statistics.mean(y_coords)
        },
        'location_usage': {
            'mean_events_per_location': statistics.mean(location_usage.values()),
            'max_events_per_location': max(location_usage.values()),
            'hotspots_count': len(hotspots)
        },
        'most_active_locations': sorted(hotspots, key=lambda x: x[1], reverse=True)[:5]
    }
    
    return analysis


def generate_analysis_report(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a comprehensive analysis report.
    
    Args:
        events: List of event dictionaries
        
    Returns:
        Dictionary containing complete analysis
    """
    print("Generating comprehensive analysis report...")
    
    report = {
        'metadata': {
            'total_events': len(events),
            'analysis_timestamp': str(Path.cwd()),
            'file_size_bytes': 0  # Will be set by caller
        },
        'event_distribution': analyze_event_distribution(events),
        'temporal_patterns': analyze_temporal_patterns(events),
        'trade_patterns': analyze_trade_patterns(events),
        'agent_behavior': analyze_agent_behavior(events),
        'spatial_patterns': analyze_spatial_patterns(events)
    }
    
    return report


def print_analysis_summary(report: Dict[str, Any]) -> None:
    """Print a human-readable summary of the analysis.
    
    Args:
        report: Analysis report dictionary
    """
    print("\n" + "="*60)
    print("SIMULATION EVENT ANALYSIS SUMMARY")
    print("="*60)
    
    # Metadata
    metadata = report['metadata']
    print(f"Total Events: {metadata['total_events']:,}")
    
    # Event Distribution
    event_dist = report['event_distribution']
    print(f"\nEvent Types ({event_dist['unique_event_types']} types):")
    for event_type, count in sorted(event_dist['event_type_counts'].items(), key=lambda x: x[1], reverse=True):
        percentage = event_dist['event_type_percentages'][event_type]
        print(f"  {event_type}: {count:,} ({percentage:.1f}%)")
    
    # Temporal Patterns
    temporal = report['temporal_patterns']
    if 'error' not in temporal:
        print(f"\nTemporal Analysis:")
        print(f"  Step Range: {temporal['step_range'][0]} - {temporal['step_range'][1]}")
        print(f"  Total Steps: {temporal['total_steps']}")
        print(f"  Events per Step: {temporal['events_per_step']['mean']:.1f} ± {temporal['events_per_step']['std_dev']:.1f}")
        print(f"  Busiest Step: {temporal['busiest_steps'][0] if temporal['busiest_steps'] else 'N/A'}")
    
    # Trade Patterns
    trades = report['trade_patterns']
    if trades['total_trades'] > 0:
        print(f"\nTrade Analysis:")
        print(f"  Total Trades: {trades['total_trades']}")
        print(f"  Cooperation Rate: {trades['cooperation_rate']:.1%}")
        print(f"  Active Trading Pairs: {trades['active_trading_pairs']}")
        if trades['most_active_pairs']:
            print(f"  Most Active Pair: {trades['most_active_pairs'][0]}")
    
    # Agent Behavior
    agents = report['agent_behavior']
    if 'message' not in agents:
        print(f"\nAgent Behavior:")
        print(f"  Total Agents: {agents['total_agents']}")
        print(f"  Mode Changes: {agents['mode_changes']}")
        if agents['agent_activity_ranking']:
            most_active = agents['agent_activity_ranking'][0]
            print(f"  Most Active Agent: {most_active[0]} (score: {most_active[1]})")
    
    # Spatial Patterns
    spatial = report['spatial_patterns']
    if 'message' not in spatial:
        print(f"\nSpatial Analysis:")
        print(f"  Spatial Events: {spatial['total_spatial_events']}")
        print(f"  Unique Locations: {spatial['unique_locations']}")
        print(f"  Spatial Range: X{spatial['spatial_range']['x']}, Y{spatial['spatial_range']['y']}")
        print(f"  Competition Hotspots: {spatial['location_usage']['hotspots_count']}")
    
    print("\n" + "="*60)


def save_analysis_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the analysis report to a JSON file.
    
    Args:
        report: Analysis report dictionary
        output_path: Path to save the report
    """
    print(f"Saving analysis report to: {output_path}")
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    file_size = output_path.stat().st_size
    print(f"Report saved ({file_size:,} bytes)")


def main():
    """Main function for event analysis example."""
    print("=== Event Analysis Example ===")
    
    # Determine input file
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    else:
        # Look for example output file
        example_dir = Path("example_output")
        input_file = example_dir / "basic_simulation.jsonl.gz"
        
        if not input_file.exists():
            print(f"Input file not found: {input_file}")
            print("Please provide a path to a JSONL file or run basic_recording.py first")
            return False
    
    try:
        # Load events
        events = load_simulation_events(input_file)
        
        if not events:
            print("No events found in the input file")
            return False
        
        # Generate analysis report
        report = generate_analysis_report(events)
        
        # Set file size in metadata
        report['metadata']['file_size_bytes'] = input_file.stat().st_size
        
        # Print summary
        print_analysis_summary(report)
        
        # Save detailed report
        output_file = input_file.parent / f"{input_file.stem}_analysis.json"
        save_analysis_report(report, output_file)
        
        print(f"\n✓ Analysis complete!")
        print(f"  Input: {input_file}")
        print(f"  Output: {output_file}")
        print(f"  Events analyzed: {len(events):,}")
        
        return True
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
