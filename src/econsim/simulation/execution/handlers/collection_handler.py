"""Collection handler for resource acquisition and spatial optimization.

This handler manages resource collection logic extracted from the monolithic
Simulation.step() method. It handles both integrated decision-mode collection
(part of step_decision) and explicit legacy-mode collection with proper
resource iteration patterns.

Collection Modes:
- Integrated: Collection handled within agent step_decision (modern path)
- Legacy Explicit: Separate collection pass after movement (legacy random path)
- Feature Gated: Respects ECONSIM_FORAGE_ENABLED flag

Design Principles:
- Preserve Grid.iter_resources_sorted() ordering for determinism
- Maintain distance-based tie-breaking rules  
- Route collection events through observer system
- Support behavioral analytics integration
- O(n) resource iteration with spatial indexing
"""

from __future__ import annotations

from typing import Set
from .. import BaseStepHandler, StepContext, StepResult
from ...agent import Agent


class CollectionHandler(BaseStepHandler):
    """Handles resource collection with spatial optimization.
    
    Extracts resource collection logic from Simulation.step() while maintaining
    identical behavior patterns. Supports both integrated decision-mode and
    explicit legacy-mode collection patterns.
    """
    
    def __init__(self):
        super().__init__("collection")
    
    def _execute_impl(self, context: StepContext) -> StepResult:
        """Execute resource collection for the current step."""
        resources_collected = 0
        agents_collected = set()
        
        # Collection is handled differently based on movement mode
        if context.feature_flags.legacy_random_movement:
            # Legacy mode: explicit collection pass after movement
            resources_collected, agents_collected = self._handle_legacy_collection(context)
        else:
            # Decision mode: collection is integrated in step_decision 
            # This handler tracks metrics but doesn't perform collection
            # (Collection already happened in MovementHandler via step_decision calls)
            resources_collected, agents_collected = self._track_decision_mode_collection(context)
        
        return StepResult.with_metrics(
            self.handler_name,
            resources_collected=resources_collected,
            agents_that_collected=len(agents_collected),
            foraging_enabled=context.feature_flags.forage_enabled,
            collection_mode="legacy_explicit" if context.feature_flags.legacy_random_movement else "integrated"
        )
    
    def _handle_legacy_collection(self, context: StepContext) -> tuple[int, Set[int]]:
        """Handle explicit collection pass for legacy random movement mode."""
        total_collected = 0
        collecting_agents = set()
        
        # In legacy mode, each agent attempts collection at their current position
        # after the movement phase has completed
        for agent in context.simulation.agents:
            # Use step context for behavioral tracking  
            collected = agent.collect(context.simulation.grid, context.step_number, context.observer_registry)
            if collected:
                total_collected += 1
                collecting_agents.add(agent.id)
                # Note: ResourceCollectionEvent is now emitted directly from agent.collect()
                # self._notify_collection_event(context, agent)  # No longer needed
        
        # Provide transient foraged IDs too (legacy path) for trading gating consistency
        try:
            context.simulation._transient_foraged_ids = set(collecting_agents)  # noqa: SLF001
        except Exception:
            pass
        return total_collected, collecting_agents
    
    def _track_decision_mode_collection(self, context: StepContext) -> tuple[int, Set[int]]:
        """Track collection metrics for decision mode (collection integrated in step_decision)."""
        # Estimate based on pre-step snapshot vs current resource count.
        sim = context.simulation
        baseline = sim.pre_step_resource_count
        if baseline is None:
            return 0, set()
        current = sim.grid.resource_count()
        diff = baseline - current
        if diff < 0:
            diff = 0  # Ignore anomaly (should not happen before respawn)
        return diff, set()
    
    def _notify_collection_event(self, context: StepContext, agent: Agent) -> None:
        """Notify observer system of resource collection events."""
        from ....observability.events import ResourceCollectionEvent
        
        if context.observer_registry.has_observers():
            # Get the resource type at agent's current position
            resource_type = "unknown"
            try:
                # Try to get resource type from grid at agent position
                grid_resource = context.simulation.grid.get_resource_at(agent.x, agent.y)
                if grid_resource:
                    resource_type = grid_resource.resource_type
            except Exception:
                pass  # Keep default "unknown" if we can't determine type
                
            event = ResourceCollectionEvent.create(
                step=context.step_number,
                agent_id=agent.id,
                x=agent.x,
                y=agent.y,
                resource_type=resource_type,
                amount_collected=1  # Default assumption
            )
            context.observer_registry.notify(event)
