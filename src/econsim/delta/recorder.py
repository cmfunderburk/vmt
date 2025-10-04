"""
Comprehensive Delta Recorder

Records complete simulation state changes including visual, agent, resource, economic,
and system events. Replaces the VisualDeltaRecorder with a comprehensive system
that captures everything needed for both visual playback and economic analysis.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, TYPE_CHECKING
from collections import defaultdict

from .data_structures import (
    SimulationDelta, VisualDelta, VisualState,
    AgentMove, AgentModeChange, InventoryChange, TargetChange, UtilityChange,
    ResourceCollection, ResourceSpawn, ResourceDepletion,
    TradeEvent, TradeIntent, EconomicDecision,
    PerformanceMetrics, DebugEvent
)
from .serializer import DeltaSerializer

if TYPE_CHECKING:
    from ..simulation.world import Simulation
    from ..simulation.agent import Agent
    from ..simulation.grid import Grid


class ComprehensiveDeltaRecorder:
    """Records comprehensive simulation deltas during execution."""
    
    def __init__(self, output_path: str):
        """Initialize comprehensive delta recorder.
        
        Args:
            output_path: Path where deltas will be saved
        """
        self.output_path = Path(output_path)
        self.deltas: List[SimulationDelta] = []
        self.serializer = DeltaSerializer()
        
        # State tracking for delta detection
        self._last_agent_positions: Dict[int, Tuple[int, int]] = {}
        self._last_agent_states: Dict[int, bool] = {}
        self._last_agent_modes: Dict[int, str] = {}
        self._last_agent_inventories: Dict[int, Dict[str, Dict[str, int]]] = {}  # agent_id -> {carrying/home -> inventory}
        self._last_agent_targets: Dict[int, Optional[Tuple[int, int]]] = {}
        self._last_agent_utilities: Dict[int, float] = {}
        self._last_resources: Dict[Tuple[int, int], str] = {}
        
        # Economic event tracking
        self._trade_intents: List[TradeIntent] = []
        self._economic_decisions: List[EconomicDecision] = []
        
        # Performance tracking
        self._step_start_time: float = 0.0
        
        # Initial state (step 0)
        self._initial_state: Optional[VisualState] = None
    
    def record_initial_state(self, simulation: Simulation) -> None:
        """Record the initial comprehensive state (step 0).
        
        Args:
            simulation: Initial simulation state
        """
        agent_positions = {}
        agent_states = {}
        resource_positions = {}
        
        # Record initial agent positions and states
        for agent in simulation.agents:
            agent_positions[agent.id] = (agent.x, agent.y)
            # Check if agent is actually carrying anything
            carrying_dict = getattr(agent, 'carrying', {})
            is_carrying = any(count > 0 for count in carrying_dict.values()) if carrying_dict else False
            agent_states[agent.id] = is_carrying
            
            # Record initial agent state
            self._last_agent_modes[agent.id] = agent.mode.value
            self._last_agent_inventories[agent.id] = {
                'carrying': dict(getattr(agent, 'carrying', {})),
                'home': dict(getattr(agent, 'home_inventory', {}))
            }
            self._last_agent_targets[agent.id] = agent.target
            self._last_agent_utilities[agent.id] = 0.0  # Will be calculated during simulation
        
        # Record initial resource positions
        try:
            for x, y, resource_type in simulation.grid.iter_resources():
                resource_positions[(x, y)] = str(resource_type)
        except Exception as e:
            print(f"Warning: Could not record initial resources: {e}")
        
        self._initial_state = VisualState(
            step=0,
            agent_positions=agent_positions,
            agent_states=agent_states,
            resource_positions=resource_positions
        )
        
        # Initialize tracking state
        self._last_agent_positions = agent_positions.copy()
        self._last_agent_states = agent_states.copy()
        self._last_resources = resource_positions.copy()
        
        print(f"📊 Recorded initial state: {len(agent_positions)} agents, {len(resource_positions)} resources")
    
    def start_step_recording(self, step: int) -> None:
        """Start recording a simulation step.
        
        Args:
            step: Current step number
        """
        self._step_start_time = time.time()
        self._trade_intents.clear()
        self._economic_decisions.clear()
    
    def record_step(self, simulation: Simulation, step: int) -> SimulationDelta:
        """Record comprehensive delta for a simulation step.
        
        Args:
            simulation: Current simulation state
            step: Current step number
            
        Returns:
            SimulationDelta containing all changes from previous step
        """
        # Record visual changes (for pygame rendering)
        visual_delta = self._record_visual_changes(simulation, step)
        
        # Record agent events
        agent_moves = self._record_agent_moves(simulation, step)
        agent_mode_changes = self._record_agent_mode_changes(simulation, step)
        agent_inventory_changes = self._record_agent_inventory_changes(simulation, step)
        agent_target_changes = self._record_agent_target_changes(simulation, step)
        agent_utility_changes = self._record_agent_utility_changes(simulation, step)
        
        # Record resource events
        resource_collections = self._record_resource_collections(simulation, step)
        resource_spawns = self._record_resource_spawns(simulation, step)
        resource_depletions = self._record_resource_depletions(simulation, step)
        
        # Record economic events (already collected during step execution)
        trade_events = self._record_trade_events(simulation, step)
        trade_intents = self._trade_intents.copy()
        economic_decisions = self._economic_decisions.copy()
        
        # Record system events
        performance_metrics = self._record_performance_metrics(simulation, step)
        debug_events = self._record_debug_events(simulation, step)
        
        # Create comprehensive delta
        delta = SimulationDelta(
            step=step,
            visual_changes=visual_delta,
            agent_moves=agent_moves,
            agent_mode_changes=agent_mode_changes,
            agent_inventory_changes=agent_inventory_changes,
            agent_target_changes=agent_target_changes,
            agent_utility_changes=agent_utility_changes,
            resource_collections=resource_collections,
            resource_spawns=resource_spawns,
            resource_depletions=resource_depletions,
            trade_events=trade_events,
            trade_intents=trade_intents,
            economic_decisions=economic_decisions,
            performance_metrics=performance_metrics,
            debug_events=debug_events
        )
        
        # Store delta
        self.deltas.append(delta)
        
        # Debug output for non-empty deltas
        if not delta.is_empty():
            print(f"🎬 {delta.get_summary()}")
        
        return delta
    
    def _record_visual_changes(self, simulation: Simulation, step: int) -> VisualDelta:
        """Record visual changes for pygame rendering."""
        agent_moves = []
        agent_state_changes = []
        resource_changes = []
        
        # Track agent movements and state changes
        for agent in simulation.agents:
            agent_id = agent.id
            current_pos = (agent.x, agent.y)
            carrying_dict = getattr(agent, 'carrying', {})
            current_carrying = any(count > 0 for count in carrying_dict.values()) if carrying_dict else False
            
            # Check for position changes
            if agent_id in self._last_agent_positions:
                last_pos = self._last_agent_positions[agent_id]
                if current_pos != last_pos:
                    agent_moves.append((agent_id, last_pos[0], last_pos[1], current_pos[0], current_pos[1]))
            
            # Check for state changes
            if agent_id in self._last_agent_states:
                last_carrying = self._last_agent_states[agent_id]
                if current_carrying != last_carrying:
                    agent_state_changes.append((agent_id, current_carrying))
            
            # Update tracking state
            self._last_agent_positions[agent_id] = current_pos
            self._last_agent_states[agent_id] = current_carrying
        
        # Track resource changes
        current_resources = {}
        try:
            for x, y, resource_type in simulation.grid.iter_resources():
                current_resources[(x, y)] = str(resource_type)
        except Exception as e:
            print(f"Warning: Could not record resources at step {step}: {e}")
        
        # Find resource changes
        all_resource_positions = set(self._last_resources.keys()) | set(current_resources.keys())
        for pos in all_resource_positions:
            old_type = self._last_resources.get(pos)
            new_type = current_resources.get(pos)
            
            if old_type != new_type:
                resource_changes.append((pos[0], pos[1], new_type))
        
        # Update tracking state
        self._last_resources = current_resources
        
        return VisualDelta(
            step=step,
            agent_moves=agent_moves,
            agent_state_changes=agent_state_changes,
            resource_changes=resource_changes
        )
    
    def _record_agent_moves(self, simulation: Simulation, step: int) -> List[AgentMove]:
        """Record agent movement events."""
        moves = []
        
        for agent in simulation.agents:
            agent_id = agent.id
            current_pos = (agent.x, agent.y)
            
            if agent_id in self._last_agent_positions:
                last_pos = self._last_agent_positions[agent_id]
                if current_pos != last_pos:
                    # Determine movement reason based on agent state
                    reason = self._determine_movement_reason(agent)
                    moves.append(AgentMove(
                        agent_id=agent_id,
                        old_x=last_pos[0],
                        old_y=last_pos[1],
                        new_x=current_pos[0],
                        new_y=current_pos[1],
                        reason=reason
                    ))
        
        return moves
    
    def _record_agent_mode_changes(self, simulation: Simulation, step: int) -> List[AgentModeChange]:
        """Record agent mode transition events."""
        mode_changes = []
        
        for agent in simulation.agents:
            agent_id = agent.id
            current_mode = agent.mode.value
            
            if agent_id in self._last_agent_modes:
                last_mode = self._last_agent_modes[agent_id]
                if current_mode != last_mode:
                    # Calculate utility before/after (simplified)
                    utility_before = self._calculate_agent_utility(agent, last_mode)
                    utility_after = self._calculate_agent_utility(agent, current_mode)
                    
                    mode_changes.append(AgentModeChange(
                        agent_id=agent_id,
                        old_mode=last_mode,
                        new_mode=current_mode,
                        reason=self._determine_mode_change_reason(agent, last_mode, current_mode),
                        utility_before=utility_before,
                        utility_after=utility_after
                    ))
            
            # Update tracking state
            self._last_agent_modes[agent_id] = current_mode
        
        return mode_changes
    
    def _record_agent_inventory_changes(self, simulation: Simulation, step: int) -> List[InventoryChange]:
        """Record agent inventory change events."""
        inventory_changes = []
        
        for agent in simulation.agents:
            agent_id = agent.id
            current_carrying = dict(getattr(agent, 'carrying', {}))
            current_home = dict(getattr(agent, 'home_inventory', {}))
            
            if agent_id in self._last_agent_inventories:
                last_inventories = self._last_agent_inventories[agent_id]
                last_carrying = last_inventories.get('carrying', {})
                last_home = last_inventories.get('home', {})
                
                # Check carrying inventory changes
                if current_carrying != last_carrying:
                    change_type = self._determine_inventory_change_type(agent, 'carrying', last_carrying, current_carrying)
                    inventory_changes.append(InventoryChange(
                        agent_id=agent_id,
                        inventory_type='carrying',
                        old_inventory=last_carrying,
                        new_inventory=current_carrying,
                        change_type=change_type
                    ))
                
                # Check home inventory changes
                if current_home != last_home:
                    change_type = self._determine_inventory_change_type(agent, 'home', last_home, current_home)
                    inventory_changes.append(InventoryChange(
                        agent_id=agent_id,
                        inventory_type='home',
                        old_inventory=last_home,
                        new_inventory=current_home,
                        change_type=change_type
                    ))
            
            # Update tracking state
            self._last_agent_inventories[agent_id] = {
                'carrying': current_carrying,
                'home': current_home
            }
        
        return inventory_changes
    
    def _record_agent_target_changes(self, simulation: Simulation, step: int) -> List[TargetChange]:
        """Record agent target selection events."""
        target_changes = []
        
        for agent in simulation.agents:
            agent_id = agent.id
            current_target = agent.target
            
            if agent_id in self._last_agent_targets:
                last_target = self._last_agent_targets[agent_id]
                if current_target != last_target:
                    target_type = self._determine_target_type(agent, current_target)
                    target_changes.append(TargetChange(
                        agent_id=agent_id,
                        old_target=last_target,
                        new_target=current_target,
                        target_type=target_type,
                        selection_reason=self._determine_target_selection_reason(agent, last_target, current_target)
                    ))
            
            # Update tracking state
            self._last_agent_targets[agent_id] = current_target
        
        return target_changes
    
    def _record_agent_utility_changes(self, simulation: Simulation, step: int) -> List[UtilityChange]:
        """Record agent utility calculation events."""
        utility_changes = []
        
        for agent in simulation.agents:
            agent_id = agent.id
            current_utility = self._calculate_agent_utility(agent, agent.mode.value)
            
            if agent_id in self._last_agent_utilities:
                last_utility = self._last_agent_utilities[agent_id]
                if abs(current_utility - last_utility) > 0.001:  # Avoid floating point precision issues
                    utility_changes.append(UtilityChange(
                        agent_id=agent_id,
                        old_utility=last_utility,
                        new_utility=current_utility,
                        utility_delta=current_utility - last_utility,
                        calculation_context=self._determine_utility_context(agent)
                    ))
            
            # Update tracking state
            self._last_agent_utilities[agent_id] = current_utility
        
        return utility_changes
    
    def _record_resource_collections(self, simulation: Simulation, step: int) -> List[ResourceCollection]:
        """Record resource collection events."""
        collections = []
        
        # This would need to be integrated with the simulation's collection logic
        # For now, we'll detect collections by comparing resource positions
        # In a full implementation, this would hook into the agent.collect() method
        
        return collections
    
    def _record_resource_spawns(self, simulation: Simulation, step: int) -> List[ResourceSpawn]:
        """Record resource spawn events."""
        spawns = []
        
        # This would need to be integrated with the simulation's respawn logic
        # For now, we'll detect spawns by comparing resource positions
        
        return spawns
    
    def _record_resource_depletions(self, simulation: Simulation, step: int) -> List[ResourceDepletion]:
        """Record resource depletion events."""
        depletions = []
        
        # Detect resource depletions by comparing resource positions
        current_resources = {}
        try:
            for x, y, resource_type in simulation.grid.iter_resources():
                current_resources[(x, y)] = str(resource_type)
        except Exception:
            pass
        
        # Find resources that were present last step but not this step
        for pos, resource_type in self._last_resources.items():
            if pos not in current_resources:
                depletions.append(ResourceDepletion(
                    resource_type=resource_type,
                    position_x=pos[0],
                    position_y=pos[1],
                    depletion_reason="collected"
                ))
        
        return depletions
    
    def _record_trade_events(self, simulation: Simulation, step: int) -> List[TradeEvent]:
        """Record executed trade events."""
        trade_events = []
        
        # This would need to be integrated with the simulation's trading system
        # For now, we'll return empty list
        
        return trade_events
    
    def _record_performance_metrics(self, simulation: Simulation, step: int) -> Optional[PerformanceMetrics]:
        """Record performance metrics for the step."""
        step_duration_ms = (time.time() - self._step_start_time) * 1000
        
        # Get simulation metrics
        agents_processed = len(simulation.agents)
        resources_processed = len(list(simulation.grid.iter_resources())) if hasattr(simulation.grid, 'iter_resources') else 0
        trade_intents = getattr(simulation, 'trade_intents', None)
        trades_attempted = len(trade_intents) if trade_intents is not None else 0
        last_trade_highlight = getattr(simulation, '_last_trade_highlight', None)
        trades_executed = 1 if last_trade_highlight is not None else 0  # Simplified
        
        # Estimate memory usage (simplified)
        import sys
        memory_usage_mb = sys.getsizeof(simulation) / 1024 / 1024
        
        return PerformanceMetrics(
            step_duration_ms=step_duration_ms,
            agents_processed=agents_processed,
            resources_processed=resources_processed,
            trades_attempted=trades_attempted,
            trades_executed=trades_executed,
            memory_usage_mb=memory_usage_mb
        )
    
    def _record_debug_events(self, simulation: Simulation, step: int) -> List[DebugEvent]:
        """Record debug events for the step."""
        debug_events = []
        
        # This would integrate with the simulation's debug logging system
        # For now, we'll return empty list
        
        return debug_events
    
    # Helper methods for determining event context
    def _determine_movement_reason(self, agent: Agent) -> str:
        """Determine the reason for agent movement."""
        if agent.mode.value == "FORAGE":
            return "target_seeking"
        elif agent.mode.value == "RETURN_HOME":
            return "returning_home"
        elif agent.mode.value == "MOVE_TO_PARTNER":
            return "partner_seeking"
        else:
            return "random"
    
    def _determine_mode_change_reason(self, agent: Agent, old_mode: str, new_mode: str) -> str:
        """Determine the reason for mode change."""
        if new_mode == "RETURN_HOME":
            return "collected_resource"
        elif new_mode == "FORAGE":
            return "returned_home"
        elif new_mode == "MOVE_TO_PARTNER":
            return "found_trading_partner"
        else:
            return "mode_transition"
    
    def _determine_inventory_change_type(self, agent: Agent, inventory_type: str, old_inv: Dict[str, int], new_inv: Dict[str, int]) -> str:
        """Determine the type of inventory change."""
        if inventory_type == "carrying":
            # Check if this was a collection or deposit
            if sum(new_inv.values()) > sum(old_inv.values()):
                return "collect"
            elif sum(new_inv.values()) < sum(old_inv.values()):
                return "deposit"
            else:
                return "trade"
        else:
            # Home inventory changes
            if sum(new_inv.values()) > sum(old_inv.values()):
                return "deposit"
            else:
                return "withdraw"
    
    def _determine_target_type(self, agent: Agent, target: Optional[Tuple[int, int]]) -> str:
        """Determine the type of target."""
        if target is None:
            return "None"
        elif target == (agent.home_x, agent.home_y):
            return "home"
        else:
            # Check if target is a resource
            try:
                if hasattr(agent, '_simulation') and agent._simulation.grid.has_resource(target[0], target[1]):
                    return "resource"
            except:
                pass
            return "partner"
    
    def _determine_target_selection_reason(self, agent: Agent, old_target: Optional[Tuple[int, int]], new_target: Optional[Tuple[int, int]]) -> str:
        """Determine the reason for target selection change."""
        if new_target is None:
            return "no_target_needed"
        elif old_target is None:
            return "new_target_selected"
        else:
            return "target_changed"
    
    def _calculate_agent_utility(self, agent: Agent, mode: str) -> float:
        """Calculate agent utility (simplified)."""
        # This is a simplified utility calculation
        # In a full implementation, this would use the agent's preference function
        carrying_total = sum(getattr(agent, 'carrying', {}).values())
        home_total = sum(getattr(agent, 'home_inventory', {}).values())
        return carrying_total + home_total * 0.5  # Simplified utility
    
    def _determine_utility_context(self, agent: Agent) -> str:
        """Determine the context for utility calculation."""
        if agent.mode.value == "FORAGE":
            return "foraging_utility"
        elif agent.mode.value == "RETURN_HOME":
            return "returning_utility"
        else:
            return "general_utility"
    
    def save_deltas(self) -> None:
        """Save comprehensive deltas to disk using MessagePack."""
        if not self._initial_state:
            raise RuntimeError("Cannot save deltas without initial state")
        
        # Save using MessagePack serializer
        self.serializer.save_to_file(self.deltas, self.output_path)
        
        print(f"💾 Saved {len(self.deltas)} comprehensive deltas to {self.output_path}")
    
    @classmethod
    def load_deltas(cls, file_path: str) -> Tuple[VisualState, List[SimulationDelta]]:
        """Load comprehensive deltas from disk.
        
        Args:
            file_path: Path to delta file
            
        Returns:
            Tuple of (initial_state, deltas)
        """
        serializer = DeltaSerializer()
        deltas = serializer.load_from_file(file_path)
        
        # Extract initial state from first delta's visual changes
        if deltas:
            first_delta = deltas[0]
            initial_state = VisualState(
                step=0,
                agent_positions=dict(first_delta.visual_changes.agent_moves),  # Simplified
                agent_states={},  # Would need to be reconstructed
                resource_positions={}  # Would need to be reconstructed
            )
        else:
            initial_state = VisualState(step=0, agent_positions={}, agent_states={}, resource_positions={})
        
        print(f"📁 Loaded {len(deltas)} comprehensive deltas from {file_path}")
        
        return initial_state, deltas
