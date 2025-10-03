"""Specialized observer for economic behavior analysis using raw data architecture.

This module implements the EconomicObserver class that provides
comprehensive economic behavior analysis and metrics calculation
for educational and research purposes using the new raw data recording
architecture for zero-overhead performance.

Features:
- Zero-overhead raw data recording during simulation
- Deferred economic analysis using DataTranslator
- Comprehensive economic metrics and behavioral insights
- Raw data storage with human-readable translation on demand
- Performance-optimized for educational and research use

Architecture:
- Inherits from both BaseObserver (for configuration) and RawDataObserver (for storage)
- Uses DataTranslator for converting raw data to analysis-ready format
- No processing overhead during simulation execution
- Analysis performed only when needed (GUI display, file output)
"""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

from .base_observer import BaseObserver
from ..raw_data.raw_data_observer import RawDataObserver
from ..raw_data.data_translator import DataTranslator
from ..raw_data.raw_data_writer import RawDataWriter

if TYPE_CHECKING:
    from ..config import ObservabilityConfig
    from ..events import SimulationEvent


@dataclass(slots=True)
class EconomicMetrics:
    """Economic metrics accumulator for real-time analysis.
    
    Tracks various economic indicators and behaviors during
    simulation execution for comprehensive analysis.
    """
    # Agent behavior metrics
    total_mode_changes: int = 0
    total_resource_collections: int = 0
    total_trades_executed: int = 0
    total_decisions_made: int = 0
    
    # Resource metrics
    resources_collected_by_type: Dict[str, int] = field(default_factory=dict)
    total_resources_collected: int = 0
    
    # Trading metrics
    trades_by_type: Dict[str, int] = field(default_factory=dict)
    total_utility_gained: float = 0.0
    total_utility_lost: float = 0.0
    
    # Agent-specific metrics
    agent_activity_counts: Dict[int, int] = field(default_factory=dict)
    agent_mode_histories: Dict[int, List[str]] = field(default_factory=dict)
    
    # Performance metrics
    events_processed: int = 0
    processing_time_ms: float = 0.0
    
    def update_mode_change(self, agent_id: int, old_mode: str, new_mode: str) -> None:
        """Update metrics for agent mode changes."""
        self.total_mode_changes += 1
        self.agent_activity_counts[agent_id] = self.agent_activity_counts.get(agent_id, 0) + 1
        
        # Track mode history for this agent
        if agent_id not in self.agent_mode_histories:
            self.agent_mode_histories[agent_id] = []
        self.agent_mode_histories[agent_id].append(f"{old_mode}→{new_mode}")
    
    def update_resource_collection(self, agent_id: int, resource_type: str, amount: int = 1) -> None:
        """Update metrics for resource collection."""
        self.total_resource_collections += 1
        self.total_resources_collected += amount
        self.resources_collected_by_type[resource_type] = self.resources_collected_by_type.get(resource_type, 0) + amount
        self.agent_activity_counts[agent_id] = self.agent_activity_counts.get(agent_id, 0) + 1
    
    def update_trade_execution(self, seller_id: int, buyer_id: int, give_type: str, take_type: str, 
                             delta_u_seller: float, delta_u_buyer: float) -> None:
        """Update metrics for trade execution."""
        self.total_trades_executed += 1
        
        # Track trades by type
        trade_type = f"{give_type}→{take_type}"
        self.trades_by_type[trade_type] = self.trades_by_type.get(trade_type, 0) + 1
        
        # Track utility changes
        if delta_u_seller > 0:
            self.total_utility_gained += delta_u_seller
        else:
            self.total_utility_lost += abs(delta_u_seller)
            
        if delta_u_buyer > 0:
            self.total_utility_gained += delta_u_buyer
        else:
            self.total_utility_lost += abs(delta_u_buyer)
        
        # Update agent activity
        self.agent_activity_counts[seller_id] = self.agent_activity_counts.get(seller_id, 0) + 1
        self.agent_activity_counts[buyer_id] = self.agent_activity_counts.get(buyer_id, 0) + 1
    
    def update_decision_made(self, agent_id: int) -> None:
        """Update metrics for agent decisions."""
        self.total_decisions_made += 1
        self.agent_activity_counts[agent_id] = self.agent_activity_counts.get(agent_id, 0) + 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all economic metrics."""
        return {
            "total_mode_changes": self.total_mode_changes,
            "total_resource_collections": self.total_resource_collections,
            "total_trades_executed": self.total_trades_executed,
            "total_decisions_made": self.total_decisions_made,
            "total_resources_collected": self.total_resources_collected,
            "resources_by_type": self.resources_collected_by_type.copy(),
            "trades_by_type": self.trades_by_type.copy(),
            "total_utility_gained": self.total_utility_gained,
            "total_utility_lost": self.total_utility_lost,
            "net_utility_change": self.total_utility_gained - self.total_utility_lost,
            "active_agents": len(self.agent_activity_counts),
            "events_processed": self.events_processed,
            "processing_time_ms": self.processing_time_ms,
        }


class EconomicObserver(BaseObserver, RawDataObserver):
    """Specialized observer for economic behavior analysis using raw data architecture.
    
    Provides comprehensive economic behavior analysis including
    agent decision patterns, resource utilization, trading behavior,
    and utility optimization tracking using zero-overhead raw data recording.
    
    Architecture:
    - Inherits from both BaseObserver (for configuration) and RawDataObserver (for storage)
    - Uses DataTranslator for converting raw data to analysis-ready format
    - Zero-overhead recording during simulation, analysis deferred to when needed
    - Raw data storage with human-readable translation on demand
    """
    
    def __init__(self, config: ObservabilityConfig, output_dir: str = None):
        """Initialize the economic observer with raw data architecture.
        
        Args:
            config: Observability configuration
            output_dir: Optional output directory for analysis files
        """
        # Economic event types we're interested in (define before super().__init__)
        self._economic_event_types = {
            'agent_mode_change',
            'resource_collection', 
            'trade_execution',
            'agent_decision',
            'debug_log',
            'performance_monitor',
            'economic_decision',
            'resource_event',
        }
        
        # Initialize both parent classes
        BaseObserver.__init__(self, config)
        RawDataObserver.__init__(self)
        
        self.output_dir = output_dir
        self._economic_metrics = EconomicMetrics()
        self._step_start_time = 0.0
        self._current_step = 0
        
        # Initialize data translator for analysis
        self._data_translator = DataTranslator()
        
        # Initialize raw data writer for disk persistence
        self._raw_data_writer = RawDataWriter(
            compress=True,
            compression_level=6,
            max_file_size_mb=100,
            enable_rotation=True,
            atomic_writes=True
        )
    
    def _initialize_event_filtering(self) -> None:
        """Initialize event filtering for economic analysis.
        
        EconomicObserver focuses on economic-relevant events
        and can be configured to filter based on categories.
        """
        self._enabled_event_types = self._economic_event_types.copy()
        
        # Add behavioral events if behavioral aggregation is enabled
        if getattr(self._config, 'behavioral_aggregation', False):
            self._enabled_event_types.add('behavioral_aggregation')
    
    def notify(self, event: SimulationEvent) -> None:
        """Handle a simulation event by recording raw data.
        
        This method now uses the raw data recording architecture for zero-overhead
        performance. Events are stored as raw dictionaries with no processing.
        Economic analysis is deferred to when data is actually needed.
        
        Args:
            event: The simulation event to log
        """
        if not self.is_enabled(event.event_type):
            return
        
        # Extract raw data from event and record using appropriate method
        step = getattr(event, 'step', 0)
        
        if event.event_type == 'trade_execution':
            self.record_trade(
                step=step,
                seller_id=getattr(event, 'seller_id', -1),
                buyer_id=getattr(event, 'buyer_id', -1),
                give_type=getattr(event, 'give_type', ''),
                take_type=getattr(event, 'take_type', ''),
                delta_u_seller=getattr(event, 'delta_u_seller', 0.0),
                delta_u_buyer=getattr(event, 'delta_u_buyer', 0.0),
                trade_location_x=getattr(event, 'trade_location_x', -1),
                trade_location_y=getattr(event, 'trade_location_y', -1)
            )
        elif event.event_type == 'agent_mode_change':
            self.record_mode_change(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                old_mode=getattr(event, 'old_mode', ''),
                new_mode=getattr(event, 'new_mode', ''),
                reason=getattr(event, 'reason', '')
            )
        elif event.event_type == 'resource_collection':
            self.record_resource_collection(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                x=getattr(event, 'x', -1),
                y=getattr(event, 'y', -1),
                resource_type=getattr(event, 'resource_type', ''),
                amount_collected=getattr(event, 'amount_collected', 1),
                utility_gained=getattr(event, 'utility_gained', 0.0),
                carrying_after=getattr(event, 'carrying_after', None)
            )
        elif event.event_type == 'agent_decision':
            self.record_agent_decision(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                decision_type=getattr(event, 'decision_type', ''),
                decision_details=getattr(event, 'decision_details', ''),
                utility_delta=getattr(event, 'utility_delta', 0.0),
                position_x=getattr(event, 'position_x', -1),
                position_y=getattr(event, 'position_y', -1)
            )
        elif event.event_type == 'debug_log':
            self.record_debug_log(
                step=step,
                category=getattr(event, 'category', ''),
                message=getattr(event, 'message', ''),
                agent_id=getattr(event, 'agent_id', -1)
            )
        elif event.event_type == 'performance_monitor':
            self.record_performance_monitor(
                step=step,
                metric_name=getattr(event, 'metric_name', ''),
                metric_value=getattr(event, 'metric_value', 0.0),
                threshold_exceeded=getattr(event, 'threshold_exceeded', False),
                details=getattr(event, 'details', '')
            )
        elif event.event_type == 'economic_decision':
            self.record_economic_decision(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                decision_type=getattr(event, 'decision_type', ''),
                decision_context=getattr(event, 'decision_context', ''),
                utility_before=getattr(event, 'utility_before', 0.0),
                utility_after=getattr(event, 'utility_after', 0.0),
                opportunity_cost=getattr(event, 'opportunity_cost', 0.0),
                alternatives_considered=getattr(event, 'alternatives_considered', 0),
                decision_time_ms=getattr(event, 'decision_time_ms', 0.0),
                position_x=getattr(event, 'position_x', -1),
                position_y=getattr(event, 'position_y', -1)
            )
        elif event.event_type == 'resource_event':
            self.record_resource_event(
                step=step,
                event_type_detail=getattr(event, 'event_type_detail', ''),
                position_x=getattr(event, 'position_x', -1),
                position_y=getattr(event, 'position_y', -1),
                resource_type=getattr(event, 'resource_type', ''),
                amount=getattr(event, 'amount', 1),
                agent_id=getattr(event, 'agent_id', -1)
            )
        else:
            # For unknown event types, record as generic debug log
            self.record_debug_log(
                step=step,
                category='UNKNOWN_EVENT',
                message=f"Unknown event type: {event.event_type}",
                agent_id=-1
            )
    
    def flush_step(self, step: int) -> None:
        """Handle end-of-step boundary with zero overhead.
        
        In the raw data architecture, no processing is done at step boundaries.
        All data is stored in memory and analysis is performed only when needed.
        
        Args:
            step: The simulation step that just completed
        """
        # Zero overhead - no processing during simulation
        # Raw data is stored in memory and analysis is deferred
        self._current_step = step
    
    def _write_analysis_results(self) -> None:
        """Write economic analysis results to file using raw data and translation.
        
        Creates comprehensive analysis files including metrics,
        summaries, and behavioral insights using the DataTranslator.
        """
        if not self.output_dir:
            return
        
        try:
            import json
            from pathlib import Path
            
            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate analysis from raw data using DataTranslator
            analysis_results = self._generate_analysis_from_raw_data()
            
            # Write comprehensive analysis
            analysis_file = output_path / f"economic_analysis_step_{self._current_step}.json"
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_results, f, indent=2)
            
            # Write raw data for reference
            raw_data_file = output_path / f"raw_data_step_{self._current_step}.jsonl"
            with open(raw_data_file, 'w', encoding='utf-8') as f:
                for event in self.get_all_events():
                    json.dump(event, f, separators=(',', ':'))
                    f.write('\n')
            
        except Exception as e:
            print(f"Warning: Failed to write economic analysis results: {e}")
    
    def _generate_analysis_from_raw_data(self) -> Dict[str, Any]:
        """Generate comprehensive economic analysis from raw data using DataTranslator.
        
        Returns:
            Dictionary containing comprehensive economic analysis
        """
        # Get all raw events
        all_events = self.get_all_events()
        
        # Translate events to human-readable format
        translated_events = []
        for event in all_events:
            try:
                if event['type'] == 'trade':
                    translated_events.append(self._data_translator.translate_trade_event(event))
                elif event['type'] == 'mode_change':
                    translated_events.append(self._data_translator.translate_mode_change_event(event))
                elif event['type'] == 'resource_collection':
                    translated_events.append(self._data_translator.translate_resource_collection_event(event))
                elif event['type'] == 'agent_decision':
                    translated_events.append(self._data_translator.translate_agent_decision_event(event))
                elif event['type'] == 'economic_decision':
                    translated_events.append(self._data_translator.translate_economic_decision_event(event))
                else:
                    # Keep raw event for unknown types
                    translated_events.append(event)
            except Exception as e:
                # Keep raw event if translation fails
                translated_events.append(event)
        
        # Generate comprehensive analysis
        analysis = {
            "step": self._current_step,
            "total_events": len(all_events),
            "event_types": self.get_event_type_counts(),
            "step_range": self.get_statistics()['step_range'],
            "translated_events": translated_events,
            "economic_metrics": self._calculate_economic_metrics_from_raw_data(),
            "agent_behavior_analysis": self._analyze_agent_behavior_from_raw_data(),
            "trading_analysis": self._analyze_trading_behavior_from_raw_data(),
            "resource_utilization_analysis": self._analyze_resource_utilization_from_raw_data(),
        }
        
        return analysis
    
    def _calculate_economic_metrics_from_raw_data(self) -> Dict[str, Any]:
        """Calculate economic metrics from raw data."""
        trade_events = self.get_events_by_type('trade')
        mode_change_events = self.get_events_by_type('mode_change')
        resource_collection_events = self.get_events_by_type('resource_collection')
        agent_decision_events = self.get_events_by_type('agent_decision')
        
        # Calculate metrics
        total_trades = len(trade_events)
        total_mode_changes = len(mode_change_events)
        total_resource_collections = len(resource_collection_events)
        total_decisions = len(agent_decision_events)
        
        # Calculate utility metrics
        total_utility_gained = 0.0
        total_utility_lost = 0.0
        for event in trade_events:
            delta_u_seller = event.get('delta_u_seller', 0.0)
            delta_u_buyer = event.get('delta_u_buyer', 0.0)
            if delta_u_seller > 0:
                total_utility_gained += delta_u_seller
            else:
                total_utility_lost += abs(delta_u_seller)
            if delta_u_buyer > 0:
                total_utility_gained += delta_u_buyer
            else:
                total_utility_lost += abs(delta_u_buyer)
        
        # Calculate resource metrics
        resources_by_type = {}
        total_resources = 0
        for event in resource_collection_events:
            resource_type = event.get('resource_type', 'unknown')
            amount = event.get('amount_collected', 1)
            resources_by_type[resource_type] = resources_by_type.get(resource_type, 0) + amount
            total_resources += amount
        
        return {
            "total_trades": total_trades,
            "total_mode_changes": total_mode_changes,
            "total_resource_collections": total_resource_collections,
            "total_decisions": total_decisions,
            "total_utility_gained": total_utility_gained,
            "total_utility_lost": total_utility_lost,
            "net_utility_change": total_utility_gained - total_utility_lost,
            "total_resources_collected": total_resources,
            "resources_by_type": resources_by_type,
        }
    
    def _analyze_agent_behavior_from_raw_data(self) -> Dict[str, Any]:
        """Analyze agent behavior patterns from raw data."""
        mode_change_events = self.get_events_by_type('mode_change')
        agent_decision_events = self.get_events_by_type('agent_decision')
        
        # Track agent activity
        agent_activity = {}
        agent_mode_transitions = {}
        
        for event in mode_change_events:
            agent_id = event.get('agent_id', -1)
            if agent_id >= 0:
                agent_activity[agent_id] = agent_activity.get(agent_id, 0) + 1
                
                # Track mode transitions
                if agent_id not in agent_mode_transitions:
                    agent_mode_transitions[agent_id] = []
                transition = f"{event.get('old_mode', '?')} → {event.get('new_mode', '?')}"
                agent_mode_transitions[agent_id].append(transition)
        
        for event in agent_decision_events:
            agent_id = event.get('agent_id', -1)
            if agent_id >= 0:
                agent_activity[agent_id] = agent_activity.get(agent_id, 0) + 1
        
        # Find most active agents
        most_active = sorted(agent_activity.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "active_agents": len(agent_activity),
            "most_active_agents": most_active,
            "agent_mode_transitions": agent_mode_transitions,
            "total_agent_activity": sum(agent_activity.values()),
        }
    
    def _analyze_trading_behavior_from_raw_data(self) -> Dict[str, Any]:
        """Analyze trading behavior patterns from raw data."""
        trade_events = self.get_events_by_type('trade')
        
        # Analyze trade types
        trade_types = {}
        utility_by_trade_type = {}
        
        for event in trade_events:
            give_type = event.get('give_type', 'unknown')
            take_type = event.get('take_type', 'unknown')
            trade_type = f"{give_type} → {take_type}"
            
            trade_types[trade_type] = trade_types.get(trade_type, 0) + 1
            
            # Track utility by trade type
            if trade_type not in utility_by_trade_type:
                utility_by_trade_type[trade_type] = {'gained': 0.0, 'lost': 0.0}
            
            delta_u_seller = event.get('delta_u_seller', 0.0)
            delta_u_buyer = event.get('delta_u_buyer', 0.0)
            
            if delta_u_seller > 0:
                utility_by_trade_type[trade_type]['gained'] += delta_u_seller
            else:
                utility_by_trade_type[trade_type]['lost'] += abs(delta_u_seller)
            
            if delta_u_buyer > 0:
                utility_by_trade_type[trade_type]['gained'] += delta_u_buyer
            else:
                utility_by_trade_type[trade_type]['lost'] += abs(delta_u_buyer)
        
        return {
            "total_trades": len(trade_events),
            "trade_types": trade_types,
            "utility_by_trade_type": utility_by_trade_type,
            "most_common_trade": max(trade_types.items(), key=lambda x: x[1]) if trade_types else None,
        }
    
    def _analyze_resource_utilization_from_raw_data(self) -> Dict[str, Any]:
        """Analyze resource utilization patterns from raw data."""
        resource_collection_events = self.get_events_by_type('resource_collection')
        
        # Analyze resource collection patterns
        resources_by_type = {}
        resources_by_agent = {}
        utility_by_resource_type = {}
        
        for event in resource_collection_events:
            resource_type = event.get('resource_type', 'unknown')
            amount = event.get('amount_collected', 1)
            agent_id = event.get('agent_id', -1)
            utility_gained = event.get('utility_gained', 0.0)
            
            # Track by type
            resources_by_type[resource_type] = resources_by_type.get(resource_type, 0) + amount
            
            # Track by agent
            if agent_id >= 0:
                if agent_id not in resources_by_agent:
                    resources_by_agent[agent_id] = {}
                resources_by_agent[agent_id][resource_type] = resources_by_agent[agent_id].get(resource_type, 0) + amount
            
            # Track utility by resource type
            if resource_type not in utility_by_resource_type:
                utility_by_resource_type[resource_type] = 0.0
            utility_by_resource_type[resource_type] += utility_gained
        
        return {
            "total_resources_collected": sum(resources_by_type.values()),
            "resources_by_type": resources_by_type,
            "resources_by_agent": resources_by_agent,
            "utility_by_resource_type": utility_by_resource_type,
            "most_collected_resource": max(resources_by_type.items(), key=lambda x: x[1]) if resources_by_type else None,
        }
    
    def get_economic_metrics(self) -> Dict[str, Any]:
        """Get the current economic metrics calculated from raw data.
        
        Returns:
            Dictionary containing current economic metrics
        """
        return self._calculate_economic_metrics_from_raw_data()
    
    def get_observer_stats(self) -> Dict[str, Any]:
        """Get economic observer statistics.
        
        Returns:
            Dictionary containing observer statistics
        """
        base_stats = super().get_observer_stats()
        raw_data_stats = self.get_statistics()
        
        economic_stats = {
            'observer_type': 'economic',
            'economic_metrics': self._calculate_economic_metrics_from_raw_data(),
            'output_dir': self.output_dir,
            'current_step': self._current_step,
            'enabled_event_types': list(self._enabled_event_types),
            'raw_data_events': raw_data_stats['total_events'],
            'raw_data_types': list(raw_data_stats['event_types']),
            'step_range': raw_data_stats['step_range'],
        }
        
        return {**base_stats, **economic_stats}
    
    def close(self) -> None:
        """Close the economic observer and write final results."""
        # Write final analysis results
        if self._current_step > 0:
            self._write_analysis_results()
        
        # Write raw data to disk if output directory is specified
        if self.output_dir and len(self._events) > 0:
            try:
                from pathlib import Path
                output_path = Path(self.output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                
                # Write raw data using RawDataWriter
                raw_data_file = output_path / f"economic_raw_data_final.jsonl.gz"
                write_result = self._raw_data_writer.flush_to_disk(
                    events=self.get_all_events(),
                    filepath=raw_data_file,
                    append=False
                )
                
                print(f"EconomicObserver closed. Wrote {write_result['events_written']} events "
                      f"({write_result['bytes_written']} bytes) to {raw_data_file}")
                
            except Exception as e:
                print(f"Warning: Failed to write final raw data: {e}")
        
        # Call parent close method
        super().close()
        
        # Clear raw data from memory after writing
        self.clear_events()
    
    def __repr__(self) -> str:
        """String representation of the economic observer."""
        raw_data_stats = self.get_statistics()
        return f"EconomicObserver(step={self._current_step}, events={raw_data_stats['total_events']}, types={len(raw_data_stats['event_types'])}, closed={self._closed})"
