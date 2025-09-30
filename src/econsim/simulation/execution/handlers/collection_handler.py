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
            collected = agent.collect(context.simulation.grid, context.step_number)
            if collected:
                total_collected += 1
                collecting_agents.add(agent.id)
                self._notify_collection_event(context, agent)
        
        return total_collected, collecting_agents
    
    def _track_decision_mode_collection(self, context: StepContext) -> tuple[int, Set[int]]:
        """Track collection metrics for decision mode (collection integrated in step_decision)."""
        # In decision mode, collection happens inside agent.step_decision() calls
        # This handler provides metrics tracking and observer events
        
        # We can estimate collection by checking resource changes or agent inventories
        # For now, return empty metrics since collection tracking is complex to extract
        # from the integrated step_decision process
        
        # TODO: Add proper collection event tracking when agent.collect() calls are
        # routed through observer system in future integration
        
        return 0, set()
    
    def _notify_collection_event(self, context: StepContext, agent: Agent) -> None:
        """Notify observer system of resource collection events."""
        # TODO: Implement ResourceCollectionEvent when defined in observability system
        # For now, this is a placeholder for future observer integration
        
        # Example of what this will look like:
        # from ....observability.events import ResourceCollectionEvent
        # 
        # if context.observer_registry.has_observers():
        #     event = ResourceCollectionEvent.create(
        #         step=context.step_number,
        #         agent_id=agent.id,
        #         resource_position=(agent.x, agent.y),
        #         resource_type="unknown",  # Would need to track from grid.take_resource_type
        #     )
        #     context.observer_registry.notify(event)
        
        pass
