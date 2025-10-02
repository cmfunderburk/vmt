"""Specialized observer for economic behavior analysis.

This module implements the EconomicObserver class that provides
comprehensive economic behavior analysis and metrics calculation
for educational and research purposes.
"""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

from .base_observer import BaseObserver

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


class EconomicObserver(BaseObserver):
    """Specialized observer for economic behavior analysis.
    
    Provides comprehensive economic behavior analysis including
    agent decision patterns, resource utilization, trading behavior,
    and utility optimization tracking.
    """
    
    def __init__(self, config: ObservabilityConfig, output_dir: str = None):
        """Initialize the economic observer.
        
        Args:
            config: Observability configuration
            output_dir: Optional output directory for analysis files
        """
        super().__init__(config)
        
        self.output_dir = output_dir
        self._economic_metrics = EconomicMetrics()
        self._step_start_time = 0.0
        self._current_step = 0
        
        # Economic event types we're interested in
        self._economic_event_types = {
            'agent_mode_change',
            'resource_collection', 
            'trade_execution',
            'agent_decision',
            'debug_log',
            'performance_monitor',
        }
        
        # Initialize event filtering
        self._initialize_event_filtering()
    
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
        """Process economic events and update metrics.
        
        Args:
            event: The simulation event to process
        """
        if not self.is_enabled(event.event_type):
            return
        
        start_time = time.perf_counter()
        
        try:
            if event.event_type in self._economic_event_types:
                self._process_economic_event(event)
                self._economic_metrics.events_processed += 1
                
                # Update processing time
                processing_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
                self._economic_metrics.processing_time_ms += processing_time
                
        except Exception as e:
            # Don't let economic analysis errors break the simulation
            print(f"Warning: EconomicObserver failed to process event {event.event_type}: {e}")
    
    def _process_economic_event(self, event: SimulationEvent) -> None:
        """Process specific economic events and update metrics.
        
        Args:
            event: The economic event to process
        """
        if event.event_type == 'agent_mode_change':
            # Extract agent mode change data
            agent_id = getattr(event, 'agent_id', -1)
            old_mode = getattr(event, 'old_mode', 'unknown')
            new_mode = getattr(event, 'new_mode', 'unknown')
            
            if agent_id >= 0:
                self._economic_metrics.update_mode_change(agent_id, old_mode, new_mode)
        
        elif event.event_type == 'resource_collection':
            # Extract resource collection data
            agent_id = getattr(event, 'agent_id', -1)
            resource_type = getattr(event, 'resource_type', 'unknown')
            amount = getattr(event, 'amount_collected', 1)
            
            if agent_id >= 0:
                self._economic_metrics.update_resource_collection(agent_id, resource_type, amount)
        
        elif event.event_type == 'trade_execution':
            # Extract trade execution data
            seller_id = getattr(event, 'seller_id', -1)
            buyer_id = getattr(event, 'buyer_id', -1)
            give_type = getattr(event, 'give_type', 'unknown')
            take_type = getattr(event, 'take_type', 'unknown')
            delta_u_seller = getattr(event, 'delta_u_seller', 0.0)
            delta_u_buyer = getattr(event, 'delta_u_buyer', 0.0)
            
            if seller_id >= 0 and buyer_id >= 0:
                self._economic_metrics.update_trade_execution(
                    seller_id, buyer_id, give_type, take_type, delta_u_seller, delta_u_buyer
                )
        
        elif event.event_type == 'agent_decision':
            # Extract agent decision data
            agent_id = getattr(event, 'agent_id', -1)
            
            if agent_id >= 0:
                self._economic_metrics.update_decision_made(agent_id)
    
    def flush_step(self, step: int) -> None:
        """Process step boundary and update analysis.
        
        Args:
            step: The simulation step that just completed
        """
        self._current_step = step
        
        # Calculate step-level metrics if needed
        # This could include efficiency calculations, trend analysis, etc.
        
        # Periodically write analysis results (every 100 steps)
        if step % 100 == 0:
            self._write_analysis_results()
    
    def _write_analysis_results(self) -> None:
        """Write economic analysis results to file.
        
        Creates comprehensive analysis files including metrics,
        summaries, and behavioral insights.
        """
        if not self.output_dir:
            return
        
        try:
            import json
            from pathlib import Path
            
            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Write metrics summary
            metrics_file = output_path / f"economic_metrics_step_{self._current_step}.json"
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(self._economic_metrics.get_summary(), f, indent=2)
            
            # Write detailed agent behavior analysis
            agent_analysis = self._generate_agent_analysis()
            agent_file = output_path / f"agent_analysis_step_{self._current_step}.json"
            with open(agent_file, 'w', encoding='utf-8') as f:
                json.dump(agent_analysis, f, indent=2)
            
        except Exception as e:
            print(f"Warning: Failed to write economic analysis results: {e}")
    
    def _generate_agent_analysis(self) -> Dict[str, Any]:
        """Generate detailed agent behavior analysis.
        
        Returns:
            Dictionary containing agent behavior analysis
        """
        analysis = {
            "step": self._current_step,
            "total_agents": len(self._economic_metrics.agent_activity_counts),
            "most_active_agents": [],
            "mode_transition_patterns": {},
            "agent_efficiency_metrics": {},
        }
        
        # Find most active agents
        if self._economic_metrics.agent_activity_counts:
            sorted_agents = sorted(
                self._economic_metrics.agent_activity_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            analysis["most_active_agents"] = sorted_agents[:10]  # Top 10
        
        # Analyze mode transition patterns
        for agent_id, mode_history in self._economic_metrics.agent_mode_histories.items():
            if len(mode_history) > 1:
                # Count transition patterns
                transitions = {}
                for i in range(len(mode_history) - 1):
                    transition = f"{mode_history[i]} → {mode_history[i+1]}"
                    transitions[transition] = transitions.get(transition, 0) + 1
                
                if transitions:
                    analysis["mode_transition_patterns"][agent_id] = transitions
        
        # Calculate agent efficiency metrics
        for agent_id in self._economic_metrics.agent_activity_counts:
            activity_count = self._economic_metrics.agent_activity_counts[agent_id]
            mode_changes = len(self._economic_metrics.agent_mode_histories.get(agent_id, []))
            
            analysis["agent_efficiency_metrics"][agent_id] = {
                "total_activity": activity_count,
                "mode_changes": mode_changes,
                "activity_per_step": activity_count / max(self._current_step, 1),
                "mode_change_rate": mode_changes / max(self._current_step, 1),
            }
        
        return analysis
    
    def get_economic_metrics(self) -> EconomicMetrics:
        """Get the current economic metrics.
        
        Returns:
            Current EconomicMetrics instance
        """
        return self._economic_metrics
    
    def get_observer_stats(self) -> Dict[str, Any]:
        """Get economic observer statistics.
        
        Returns:
            Dictionary containing observer statistics
        """
        base_stats = super().get_observer_stats()
        
        economic_stats = {
            'observer_type': 'economic',
            'economic_metrics': self._economic_metrics.get_summary(),
            'output_dir': self.output_dir,
            'current_step': self._current_step,
            'enabled_event_types': list(self._enabled_event_types),
        }
        
        return {**base_stats, **economic_stats}
    
    def close(self) -> None:
        """Close the economic observer and write final results."""
        super().close()
        
        # Write final analysis results
        if self._current_step > 0:
            self._write_analysis_results()
        
        print(f"EconomicObserver closed. Processed {self._economic_metrics.events_processed} events "
              f"in {self._economic_metrics.processing_time_ms:.2f}ms")
    
    def __repr__(self) -> str:
        """String representation of the economic observer."""
        return f"EconomicObserver(step={self._current_step}, events={self._economic_metrics.events_processed}, closed={self._closed})"
