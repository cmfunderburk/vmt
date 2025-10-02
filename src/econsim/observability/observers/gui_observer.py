"""GUI Event Observer for translating simulation events to GUI updates.

This module implements comprehensive GUI observers that handle all simulation events
and translate them into GUI display updates without creating circular dependencies.
The observers provide event-to-display mapping and efficient GUI update batching.

Features:
- Comprehensive event-to-GUI mapping
- Efficient display update batching
- Performance monitoring for GUI responsiveness
- Event filtering for GUI-relevant information
- Minimal coupling between simulation and GUI layers

Architecture:
- GUIEventObserver: Main GUI event handler
- DisplayUpdateBatcher: Batches GUI updates for performance
- EventToDisplayMapper: Maps events to display elements
- GUIPerformanceMonitor: Tracks GUI responsiveness
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional, Callable, Set, Union, TYPE_CHECKING, Protocol
from dataclasses import dataclass, field

from ..observers.base_observer import BaseObserver
from ..events import (
    SimulationEvent, AgentModeChangeEvent, TradeExecutionEvent,
    ResourceCollectionEvent, DebugLogEvent, PerformanceMonitorEvent,
    AgentDecisionEvent, ResourceEvent, GUIDisplayEvent
)

if TYPE_CHECKING:
    from ..config import ObservabilityConfig
    from ...gui.main_window import MainWindow


class EventHandler(Protocol):
    """Protocol for event handler functions."""
    def __call__(self, event: SimulationEvent) -> List[DisplayUpdate]:
        ...


@dataclass
class DisplayUpdate:
    """Represents a display update for the GUI.
    
    Encapsulates information needed to update a specific GUI element
    based on simulation events.
    """
    element_id: str
    update_type: str  # "highlight", "text", "value", "state", etc.
    data: dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher = more urgent
    timestamp: float = field(default_factory=time.time)


@dataclass
class GUIMetrics:
    """Performance metrics for GUI event processing."""
    events_processed: int = 0
    updates_generated: int = 0
    batches_flushed: int = 0
    average_processing_time: float = 0.0
    peak_processing_time: float = 0.0
    gui_lag_ms: float = 0.0


class EventToDisplayMapper:
    """Maps simulation events to GUI display updates.
    
    Provides centralized logic for converting observer events into
    specific GUI element updates while maintaining clean separation
    between simulation and GUI concerns.
    """
    
    def __init__(self):
        """Initialize event-to-display mapping system."""
        self._event_handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._setup_default_mappings()
    
    def _setup_default_mappings(self) -> None:
        """Set up default event-to-display mappings."""
        
        # Agent mode change mappings
        self.register_mapping("agent_mode_change", self._handle_agent_mode_change)
        
        # Trade event mappings  
        self.register_mapping("trade_execution", self._handle_trade_execution)
        
        # Resource event mappings
        self.register_mapping("resource_collection", self._handle_resource_collection)
        self.register_mapping("resource_event", self._handle_resource_event)
        
        # Performance event mappings
        self.register_mapping("performance_monitor", self._handle_performance_monitor)
        
        # Debug log mappings
        self.register_mapping("debug_log", self._handle_debug_log)
        
        # Agent decision mappings
        self.register_mapping("agent_decision", self._handle_agent_decision)
    
    def register_mapping(self, event_type: str, handler: EventHandler) -> None:
        """Register a mapping from event type to display handler.
        
        Args:
            event_type: Type of event to handle
            handler: Function to convert event to display updates
        """
        self._event_handlers[event_type].append(handler)
    
    def map_event_to_updates(self, event: SimulationEvent) -> List[DisplayUpdate]:
        """Convert a simulation event to GUI display updates.
        
        Args:
            event: Simulation event to convert
            
        Returns:
            List of display updates for GUI elements
        """
        updates = []
        
        handlers = self._event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler_updates = handler(event)
                if handler_updates:
                    updates.extend(handler_updates)
            except Exception as e:
                # Log error but don't break GUI
                print(f"Warning: Display mapping failed for {event.event_type}: {e}")
        
        return updates
    
    # Default event handlers
    
    def _handle_agent_mode_change(self, event: SimulationEvent) -> List[DisplayUpdate]:
        """Handle agent mode change events."""
        if not isinstance(event, AgentModeChangeEvent):
            return []
            
        updates = []
        
        # Update agent inspector if agent is selected
        updates.append(DisplayUpdate(
            element_id=f"agent_inspector_{event.agent_id}",
            update_type="mode_change",
            data={
                "agent_id": event.agent_id,
                "old_mode": event.old_mode,
                "new_mode": event.new_mode,
                "reason": event.reason,
                "step": event.step
            },
            priority=3
        ))
        
        # Update agent visual representation  
        updates.append(DisplayUpdate(
            element_id=f"agent_visual_{event.agent_id}",
            update_type="mode_indicator",
            data={
                "agent_id": event.agent_id,
                "mode": event.new_mode
            },
            priority=2
        ))
        
        return updates
    
    def _handle_trade_execution(self, event: SimulationEvent) -> List[DisplayUpdate]:
        """Handle trade execution events."""
        if not isinstance(event, TradeExecutionEvent):
            return []
            
        updates = []
        
        # Highlight trade location if available
        if event.trade_location_x >= 0:
            updates.append(DisplayUpdate(
                element_id=f"grid_cell_{event.trade_location_x}_{event.trade_location_y}",
                update_type="highlight", 
                data={
                    "color": "yellow",
                    "duration": 2000,  # 2 second highlight
                    "type": "trade"
                },
                priority=4
            ))
        
        # Update trade inspector
        updates.append(DisplayUpdate(
            element_id="trade_inspector",
            update_type="trade_event",
            data={
                "seller_id": event.seller_id,
                "buyer_id": event.buyer_id,
                "give_type": event.give_type,
                "take_type": event.take_type,
                "delta_u_seller": event.delta_u_seller,
                "delta_u_buyer": event.delta_u_buyer,
                "step": event.step
            },
            priority=3
        ))
        
        # Update metrics panel
        updates.append(DisplayUpdate(
            element_id="metrics_panel",
            update_type="trade_count",
            data={"increment": 1},
            priority=1
        ))
        
        return updates
    
    def _handle_resource_collection(self, event: SimulationEvent) -> List[DisplayUpdate]:
        """Handle resource collection events."""
        if not isinstance(event, ResourceCollectionEvent):
            return []
            
        updates = []
        
        # Update grid visualization
        updates.append(DisplayUpdate(
            element_id=f"grid_cell_{event.x}_{event.y}",
            update_type="resource_collected",
            data={
                "agent_id": event.agent_id,
                "resource_type": event.resource_type,
                "amount": event.amount_collected
            },
            priority=2
        ))
        
        # Update agent inspector
        updates.append(DisplayUpdate(
            element_id=f"agent_inspector_{event.agent_id}",
            update_type="inventory_update", 
            data={
                "agent_id": event.agent_id,
                "resource_type": event.resource_type,
                "amount_change": event.amount_collected
            },
            priority=2
        ))
        
        return updates
    
    def _handle_resource_event(self, event: SimulationEvent) -> List[DisplayUpdate]:
        """Handle general resource events (spawn, despawn, etc.)."""
        if not isinstance(event, ResourceEvent):
            return []
            
        updates = []
        
        if event.event_type_detail in ["spawn", "respawn"]:
            updates.append(DisplayUpdate(
                element_id=f"grid_cell_{event.position_x}_{event.position_y}",
                update_type="resource_spawn",
                data={
                    "resource_type": event.resource_type,
                    "amount": event.amount,
                    "event_type": event.event_type_detail
                },
                priority=1
            ))
        
        return updates
    
    def _handle_performance_monitor(self, event: SimulationEvent) -> List[DisplayUpdate]:
        """Handle performance monitoring events."""
        if not isinstance(event, PerformanceMonitorEvent):
            return []
            
        updates = []
        
        # Update performance display
        updates.append(DisplayUpdate(
            element_id="performance_display",
            update_type="metric_update",
            data={
                "metric_name": event.metric_name,
                "metric_value": event.metric_value,
                "threshold_exceeded": event.threshold_exceeded,
                "details": event.details
            },
            priority=1 if not event.threshold_exceeded else 4
        ))
        
        return updates
    
    def _handle_debug_log(self, event: SimulationEvent) -> List[DisplayUpdate]:
        """Handle debug log events."""
        if not isinstance(event, DebugLogEvent):
            return []
            
        updates = []
        
        # Update event log panel
        updates.append(DisplayUpdate(
            element_id="event_log_panel",
            update_type="log_entry",
            data={
                "category": event.category,
                "message": event.message,
                "step": event.step,
                "agent_id": getattr(event, 'agent_id', -1)
            },
            priority=1
        ))
        
        return updates
    
    def _handle_agent_decision(self, event: SimulationEvent) -> List[DisplayUpdate]:
        """Handle agent decision events."""
        if not isinstance(event, AgentDecisionEvent):
            return []
            
        updates = []
        
        # Update agent inspector with decision info
        updates.append(DisplayUpdate(
            element_id=f"agent_inspector_{event.agent_id}",
            update_type="decision_update",
            data={
                "agent_id": event.agent_id,
                "decision_type": event.decision_type,
                "decision_details": event.decision_details,
                "utility_delta": event.utility_delta
            },
            priority=2
        ))
        
        return updates


class DisplayUpdateBatcher:
    """Batches display updates for efficient GUI processing.
    
    Collects display updates and processes them in batches to reduce
    GUI update overhead and improve responsiveness.
    """
    
    def __init__(self, batch_size: int = 50, flush_interval: float = 0.1):
        """Initialize display update batcher.
        
        Args:
            batch_size: Maximum updates per batch
            flush_interval: Maximum time between flushes (seconds)
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        self._pending_updates: List[DisplayUpdate] = []
        self._last_flush: float = time.time()
        self._update_callbacks: List[Callable[[List[DisplayUpdate]], None]] = []
        
    def add_update_callback(self, callback: Callable[[List[DisplayUpdate]], None]) -> None:
        """Add callback for processing batched updates.
        
        Args:
            callback: Function to call with batched updates
        """
        self._update_callbacks.append(callback)
    
    def queue_update(self, update: DisplayUpdate) -> None:
        """Queue a display update for batching.
        
        Args:
            update: Display update to queue
        """
        self._pending_updates.append(update)
        
        # Auto-flush if batch is full or interval exceeded
        current_time = time.time()
        should_flush = (
            len(self._pending_updates) >= self.batch_size or
            (current_time - self._last_flush) >= self.flush_interval
        )
        
        if should_flush:
            self.flush_updates()
    
    def flush_updates(self) -> int:
        """Process all pending updates.
        
        Returns:
            Number of updates processed
        """
        if not self._pending_updates:
            return 0
        
        # Sort by priority (higher priority first)
        self._pending_updates.sort(key=lambda u: u.priority, reverse=True)
        
        # Process updates through callbacks
        for callback in self._update_callbacks:
            try:
                callback(self._pending_updates.copy())
            except Exception as e:
                print(f"Warning: GUI update callback failed: {e}")
        
        update_count = len(self._pending_updates)
        self._pending_updates.clear()
        self._last_flush = time.time()
        
        return update_count


class GUIEventObserver(BaseObserver):
    """Comprehensive GUI event observer for simulation-to-GUI translation.
    
    Handles all simulation events and converts them to appropriate GUI
    updates while maintaining performance and clean architecture.
    """
    
    def __init__(self, config: ObservabilityConfig, gui_reference: Optional[Any] = None):
        """Initialize GUI event observer.
        
        Args:
            config: Observer configuration
            gui_reference: Optional reference to main GUI window
        """
        super().__init__(config)
        
        self.gui_reference = gui_reference
        self.event_mapper = EventToDisplayMapper()
        self.update_batcher = DisplayUpdateBatcher()
        
        # Performance metrics
        self.metrics = GUIMetrics()
        self._processing_times: deque[float] = deque(maxlen=100)
        
        # Event filtering for GUI relevance
        self._setup_gui_event_filtering()
        
        # Connect batcher to GUI updates
        if gui_reference:
            self.update_batcher.add_update_callback(self._apply_gui_updates)
    
    def _setup_gui_event_filtering(self) -> None:
        """Set up event filtering for GUI-relevant events."""
        # Enable events that affect GUI display
        gui_relevant_events = {
            "agent_mode_change", "trade_execution", "resource_collection",
            "resource_event", "performance_monitor", "debug_log", "agent_decision"
        }
        
        for event_type in gui_relevant_events:
            self.enable_event_type(event_type)
    
    def notify(self, event: SimulationEvent) -> None:
        """Process simulation event and generate GUI updates.
        
        Args:
            event: Simulation event to process
        """
        if not self.is_enabled(event.event_type):
            return
        
        start_time = time.perf_counter()
        
        try:
            # Convert event to display updates
            updates = self.event_mapper.map_event_to_updates(event)
            
            # Queue updates for batched processing  
            for update in updates:
                self.update_batcher.queue_update(update)
            
            # Update metrics
            self.metrics.events_processed += 1
            self.metrics.updates_generated += len(updates)
            
        except Exception as e:
            print(f"Warning: GUI event processing failed for {event.event_type}: {e}")
        
        # Track processing performance
        processing_time = time.perf_counter() - start_time
        self._processing_times.append(processing_time)
        
        # Update performance metrics
        if self._processing_times:
            self.metrics.average_processing_time = sum(self._processing_times) / len(self._processing_times)
            self.metrics.peak_processing_time = max(self._processing_times)
    
    def flush_step(self, step: int) -> None:
        """Handle step boundary and flush pending updates.
        
        Args:
            step: Simulation step that just completed
        """
        # Flush any remaining updates
        updates_processed = self.update_batcher.flush_updates()
        if updates_processed > 0:
            self.metrics.batches_flushed += 1
    
    def _apply_gui_updates(self, updates: List[DisplayUpdate]) -> None:
        """Apply batched display updates to GUI elements.
        
        Args:
            updates: List of display updates to apply
        """
        if not self.gui_reference:
            return
        
        # Group updates by element for efficiency
        updates_by_element = defaultdict(list)
        for update in updates:
            updates_by_element[update.element_id].append(update)
        
        # Apply updates to GUI elements
        for element_id, element_updates in updates_by_element.items():
            try:
                self._update_gui_element(element_id, element_updates)
            except Exception as e:
                print(f"Warning: Failed to update GUI element {element_id}: {e}")
    
    def _update_gui_element(self, element_id: str, updates: List[DisplayUpdate]) -> None:
        """Update a specific GUI element with batched updates.
        
        Args:
            element_id: ID of GUI element to update
            updates: Updates to apply to the element
        """
        # This is where we would integrate with actual GUI components
        # For now, we'll demonstrate the interface
        
        if element_id.startswith("agent_inspector_"):
            self._update_agent_inspector(element_id, updates)
        elif element_id.startswith("grid_cell_"):
            self._update_grid_cell(element_id, updates)
        elif element_id == "trade_inspector":
            self._update_trade_inspector(updates)
        elif element_id == "event_log_panel":
            self._update_event_log(updates)
        elif element_id == "metrics_panel":
            self._update_metrics_panel(updates)
        elif element_id == "performance_display":
            self._update_performance_display(updates)
    
    def _update_agent_inspector(self, element_id: str, updates: List[DisplayUpdate]) -> None:
        """Update agent inspector panel."""
        # Extract agent ID from element_id
        agent_id = int(element_id.split("_")[-1]) if "_" in element_id else -1
        
        for update in updates:
            if update.update_type == "mode_change":
                # Update agent mode display
                if hasattr(self.gui_reference, 'update_agent_mode'):
                    self.gui_reference.update_agent_mode(
                        agent_id, update.data["new_mode"], update.data["reason"]
                    )
            elif update.update_type == "inventory_update":
                # Update agent inventory display
                if hasattr(self.gui_reference, 'update_agent_inventory'):
                    self.gui_reference.update_agent_inventory(
                        agent_id, update.data["resource_type"], update.data["amount_change"]
                    )
            elif update.update_type == "decision_update":
                # Update agent decision display
                if hasattr(self.gui_reference, 'update_agent_decision'):
                    self.gui_reference.update_agent_decision(
                        agent_id, update.data["decision_type"], update.data["decision_details"]
                    )
    
    def _update_grid_cell(self, element_id: str, updates: List[DisplayUpdate]) -> None:
        """Update grid cell visualization."""
        # Extract coordinates from element_id
        parts = element_id.split("_")
        if len(parts) >= 3:
            x, y = int(parts[2]), int(parts[3])
            
            for update in updates:
                if update.update_type == "highlight":
                    # Highlight grid cell
                    if hasattr(self.gui_reference, 'highlight_grid_cell'):
                        self.gui_reference.highlight_grid_cell(
                            x, y, update.data.get("color", "yellow"),
                            update.data.get("duration", 1000)
                        )
                elif update.update_type == "resource_collected":
                    # Show resource collection animation
                    if hasattr(self.gui_reference, 'show_resource_collection'):
                        self.gui_reference.show_resource_collection(
                            x, y, update.data["agent_id"], update.data["resource_type"]
                        )
                elif update.update_type == "resource_spawn":
                    # Update resource visualization
                    if hasattr(self.gui_reference, 'update_resource_display'):
                        self.gui_reference.update_resource_display(
                            x, y, update.data["resource_type"], update.data["amount"]
                        )
    
    def _update_trade_inspector(self, updates: List[DisplayUpdate]) -> None:
        """Update trade inspector panel."""
        for update in updates:
            if update.update_type == "trade_event":
                if hasattr(self.gui_reference, 'update_trade_display'):
                    self.gui_reference.update_trade_display(update.data)
    
    def _update_event_log(self, updates: List[DisplayUpdate]) -> None:
        """Update event log panel."""
        for update in updates:
            if update.update_type == "log_entry":
                if hasattr(self.gui_reference, 'add_log_entry'):
                    self.gui_reference.add_log_entry(
                        update.data["category"], update.data["message"], 
                        update.data["step"]
                    )
    
    def _update_metrics_panel(self, updates: List[DisplayUpdate]) -> None:
        """Update metrics panel."""
        for update in updates:
            if update.update_type == "trade_count":
                if hasattr(self.gui_reference, 'increment_trade_count'):
                    self.gui_reference.increment_trade_count()
    
    def _update_performance_display(self, updates: List[DisplayUpdate]) -> None:
        """Update performance display."""
        for update in updates:
            if update.update_type == "metric_update":
                if hasattr(self.gui_reference, 'update_performance_metric'):
                    self.gui_reference.update_performance_metric(
                        update.data["metric_name"], update.data["metric_value"],
                        update.data.get("threshold_exceeded", False)
                    )
    
    def get_gui_metrics(self) -> Dict[str, Any]:
        """Get GUI performance metrics.
        
        Returns:
            Dictionary with GUI processing metrics
        """
        return {
            "events_processed": self.metrics.events_processed,
            "updates_generated": self.metrics.updates_generated,
            "batches_flushed": self.metrics.batches_flushed,
            "average_processing_time_ms": self.metrics.average_processing_time * 1000,
            "peak_processing_time_ms": self.metrics.peak_processing_time * 1000,
            "pending_updates": len(self.update_batcher._pending_updates)
        }
    
    def register_custom_mapping(self, event_type: str, handler: EventHandler) -> None:
        """Register custom event-to-display mapping.
        
        Args:
            event_type: Type of event to handle
            handler: Function to convert event to display updates
        """
        self.event_mapper.register_mapping(event_type, handler)


class GUIPerformanceMonitor(BaseObserver):
    """Specialized observer for monitoring GUI performance and responsiveness.
    
    Tracks GUI-specific performance metrics including update latency,
    event processing overhead, and responsiveness indicators.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """Initialize GUI performance monitor.
        
        Args:
            config: Observer configuration
        """
        super().__init__(config)
        
        self.gui_metrics = {
            "total_gui_events": 0,
            "gui_processing_time": 0.0,
            "gui_update_count": 0,
            "gui_lag_warnings": 0,
            "peak_gui_latency": 0.0
        }
        
        self._gui_processing_times: deque[float] = deque(maxlen=1000)
        self._lag_threshold_ms = 16.0  # 60 FPS threshold
    
    def notify(self, event: SimulationEvent) -> None:
        """Monitor GUI-relevant event processing.
        
        Args:
            event: Simulation event being processed
        """
        if not self.is_enabled(event.event_type):
            return
        
        start_time = time.perf_counter()
        
        # Track GUI-relevant events
        gui_relevant_events = {
            "agent_mode_change", "trade_execution", "resource_collection",
            "performance_monitor", "debug_log"
        }
        
        if event.event_type in gui_relevant_events:
            self.gui_metrics["total_gui_events"] += 1
            
            # Simulate GUI processing time (in real implementation, this would
            # measure actual GUI update time)
            processing_time = time.perf_counter() - start_time
            self._gui_processing_times.append(processing_time * 1000)  # Convert to ms
            
            self.gui_metrics["gui_processing_time"] += processing_time
            
            # Check for performance issues
            if processing_time * 1000 > self._lag_threshold_ms:
                self.gui_metrics["gui_lag_warnings"] += 1
            
            # Track peak latency
            current_latency = processing_time * 1000
            if current_latency > self.gui_metrics["peak_gui_latency"]:
                self.gui_metrics["peak_gui_latency"] = current_latency
    
    def flush_step(self, step: int) -> None:
        """Process step boundary for GUI performance analysis.
        
        Args:
            step: Simulation step that completed
        """
        # Calculate rolling GUI performance metrics
        if self._gui_processing_times and step % 10 == 0:  # Every 10 steps
            avg_latency = sum(self._gui_processing_times) / len(self._gui_processing_times)
            
            # Emit performance warning if GUI is lagging
            if avg_latency > self._lag_threshold_ms:
                print(f"Warning: GUI performance degraded - avg latency {avg_latency:.2f}ms")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive GUI performance report.
        
        Returns:
            Dictionary with GUI performance analysis
        """
        if not self._gui_processing_times:
            return {"status": "no_data"}
        
        processing_times = list(self._gui_processing_times)
        
        return {
            "total_gui_events": self.gui_metrics["total_gui_events"],
            "total_processing_time_ms": self.gui_metrics["gui_processing_time"] * 1000,
            "average_latency_ms": sum(processing_times) / len(processing_times),
            "peak_latency_ms": max(processing_times),
            "min_latency_ms": min(processing_times),
            "lag_warnings": self.gui_metrics["gui_lag_warnings"],
            "responsiveness_score": min(100, max(0, 100 - (sum(processing_times) / len(processing_times)))),
            "samples_collected": len(processing_times)
        }


# Factory functions for easy integration

def create_gui_observer(config: ObservabilityConfig, gui_reference: Optional[Any] = None) -> GUIEventObserver:
    """Create a GUI event observer for simulation-to-GUI translation.
    
    Args:
        config: Observer configuration
        gui_reference: Optional reference to main GUI window
        
    Returns:
        Configured GUI event observer
    """
    return GUIEventObserver(config, gui_reference)


def create_gui_performance_monitor(config: ObservabilityConfig) -> GUIPerformanceMonitor:
    """Create a GUI performance monitor.
    
    Args:
        config: Observer configuration
        
    Returns:
        Configured GUI performance monitor
    """
    return GUIPerformanceMonitor(config)