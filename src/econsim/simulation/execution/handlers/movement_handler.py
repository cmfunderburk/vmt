"""Movement handler for agent positioning and target pursuit.

This handler manages all agent movement logic extracted from the monolithic
Simulation.step() method. It coordinates different movement modes based on
feature flags and agent states while preserving deterministic behavior.

Movement Modes:
- Unified Selection: Distance-discounted utility for resource/partner targeting
- Decision Mode: Agent-driven movement toward selected targets  
- Legacy Random: Random walk movement for regression testing
- Bilateral Exchange: Partner-seeking movement in trading scenarios

Design Principles:
- Preserve exact RNG call patterns for determinism
- Maintain agent iteration order and tie-breaking rules
- Route mode changes through observer system
- Support all existing feature flag combinations
"""

from __future__ import annotations

import os
from typing import Dict, List, Set
from .. import BaseStepHandler, StepContext, StepResult
from ...agent import Agent, AgentMode


class MovementHandler(BaseStepHandler):
    """Handles agent movement decisions and execution.
    
    Extracts movement logic from Simulation.step() while maintaining
    identical behavior patterns. Supports unified selection, decision
    mode, legacy random movement, and bilateral exchange scenarios.
    """
    
    def __init__(self):
        super().__init__("movement")
    
    def _execute_impl(self, context: StepContext) -> StepResult:
        """Execute agent movement for the current step."""
        agents_moved = 0
        mode_changes = 0
        
        # Get current feature flag state
        forage_enabled = context.feature_flags.forage_enabled
        use_decision = not context.feature_flags.legacy_random_movement
        draft_enabled = context.feature_flags.trade_draft_enabled
        exec_enabled = context.feature_flags.trade_execution_enabled
        
        # Check unified selection flags (preserve original logic)
        unified_disabled = os.environ.get("ECONSIM_UNIFIED_SELECTION_DISABLE") == "1"
        explicit_unified = os.environ.get("ECONSIM_UNIFIED_SELECTION_ENABLE") == "1"
        
        # Initialize foraged_ids set for trade gating coordination with other handlers
        foraged_ids: Set[int] = set()
        
        if use_decision and forage_enabled and (not unified_disabled) and (exec_enabled or explicit_unified):
            # Unified selection mode: evaluate resource vs partner for all agents
            agents_moved, new_foraged_ids = self._unified_selection_pass(context)
            foraged_ids.update(new_foraged_ids)
            
        elif use_decision and forage_enabled:
            # Standard decision mode with foraging enabled
            for agent in context.simulation.agents:
                try:
                    collected = agent.step_decision(context.simulation.grid)
                    if collected:
                        foraged_ids.add(agent.id)
                        agents_moved += 1
                except TypeError:
                    # Legacy fallback
                    agent.step_decision(context.simulation.grid) 
                    agents_moved += 1
                    
        elif use_decision and not forage_enabled:
            # Decision mode but foraging disabled
            mode_changes += self._handle_no_forage_movement(context, draft_enabled, exec_enabled)
            agents_moved = len(context.simulation.agents)
            
        else:
            # Legacy random movement mode
            agents_moved = self._handle_legacy_random_movement(context)
        
        # Store transient foraged IDs for TradingHandler gating (cleared end-of-step)
        try:
            context.simulation._transient_foraged_ids = set(foraged_ids)  # noqa: SLF001
        except Exception:
            pass

        result = StepResult.with_metrics(
            self.handler_name,
            agents_moved=agents_moved,
            mode_changes=mode_changes,
            foraged_agent_count=len(foraged_ids),
            movement_mode="unified" if (use_decision and forage_enabled and not unified_disabled) else
                         "decision" if use_decision else "legacy_random"
        )
        return result

    
    def _unified_selection_pass(self, context: StepContext) -> tuple[int, Set[int]]:
        """Execute unified selection pass for resource vs partner targeting."""
        # Delegate to existing simulation method to preserve exact behavior
        foraged_ids: Set[int] = set()
        context.simulation._unified_selection_pass(context.ext_rng, foraged_ids, context.step_number)
        return len(context.simulation.agents), foraged_ids
    
    def _handle_no_forage_movement(self, context: StepContext, draft_enabled: bool, exec_enabled: bool) -> int:
        """Handle movement when foraging is disabled but decision mode is active."""
        mode_changes = 0
        exchange_any = draft_enabled or exec_enabled
        
        if not exchange_any:
            # Neither foraging nor exchange: agents return home then idle
            for agent in context.simulation.agents:
                # Clear any existing target first
                agent.target = None
                
                if not agent.at_home():
                    if agent.mode != AgentMode.RETURN_HOME:
                        self._set_agent_mode(context, agent, AgentMode.RETURN_HOME, "no_forage_return_home")
                        mode_changes += 1
                else:
                    # Already at home, deposit and idle
                    agent.maybe_deposit()
                    if agent.mode != AgentMode.IDLE:
                        self._set_agent_mode(context, agent, AgentMode.IDLE, "no_forage_idle")
                        mode_changes += 1
                
                # Execute movement step
                agent.step_decision(context.simulation.grid)
        else:
            # Exchange enabled but foraging disabled
            for agent in context.simulation.agents:
                
                # Transition FORAGE agents to IDLE when foraging disabled
                if agent.mode == AgentMode.FORAGE and not context.feature_flags.forage_enabled:
                    self._set_agent_mode(context, agent, AgentMode.IDLE, "forage_disabled")
                    agent.target = None
                    mode_changes += 1
                
                # Handle home inventory withdrawal for trading
                if agent.at_home() and sum(agent.home_inventory.values()) > 0:
                    agent.withdraw_all()
                    if agent.mode != AgentMode.IDLE:
                        self._set_agent_mode(context, agent, AgentMode.IDLE, "withdraw_for_trade")
                        agent.target = None
                        mode_changes += 1
                
                # Handle RETURN_HOME agents in exchange mode
                if agent.mode == AgentMode.RETURN_HOME:
                    if not getattr(agent, "force_deposit_once", False):
                        # Convert to IDLE for exchange search (legacy behavior)
                        self._set_agent_mode(context, agent, AgentMode.IDLE, "exchange_mode")
                        agent.target = None
                        mode_changes += 1
                    else:
                        # Preserve forced deposit
                        try:
                            agent.step_decision(context.simulation.grid)
                        except Exception:
                            pass
                        continue
                
                # Execute bilateral exchange movement for IDLE agents
                if agent.mode == AgentMode.IDLE:
                    context.simulation._handle_bilateral_exchange_movement(agent, context.ext_rng, context.step_number)
        
        return mode_changes
    
    def _handle_legacy_random_movement(self, context: StepContext) -> int:
        """Handle legacy random walk movement mode."""
        for agent in context.simulation.agents:
            agent.move_random(context.simulation.grid, context.ext_rng)
        return len(context.simulation.agents)
    
    def _set_agent_mode(self, context: StepContext, agent: Agent, new_mode: AgentMode, reason: str) -> None:
        """Set agent mode using centralized utility with observer events."""
        from ...agent_mode_utils import set_agent_mode
        
        set_agent_mode(
            agent=agent,
            new_mode=new_mode,
            reason=reason,
            step=context.step_number,
            observer_registry=context.observer_registry
        )
    
    def _notify_mode_change(self, context: StepContext, agent: Agent, old_mode: AgentMode, new_mode: AgentMode, reason: str) -> None:
        """DEPRECATED: Use _set_agent_mode instead."""
        from ...observability.events import AgentModeChangeEvent
        
        if context.observer_registry.has_observers():
            event = AgentModeChangeEvent.create(
                step=context.step_number,
                agent_id=agent.id,
                old_mode=old_mode.value,
                new_mode=new_mode.value,
                reason=reason
            )
            context.observer_registry.notify(event)

    # NOTE: execute override removed; transient assignment handled inside _execute_impl
