def record_step(self, simulation: Simulation, step: int) -> SimulationDelta:
    """Record comprehensive delta for a simulation step.
    
    Args:
        simulation: Current simulation state
        step: Current step number
        
    Returns:
        SimulationDelta containing all changes from previous step
    """
    import os
    
    # Check if delta recording is disabled via environment variable
    if os.environ.get('ECONSIM_DISABLE_DELTA_RECORDING') == '1':
        # Still provide performance prints but skip all delta recording
        print(f"🎬 Step {step}: Delta recording disabled (ECONSIM_DISABLE_DELTA_RECORDING=1)")
        return SimulationDelta(
            step=step,
            visual_changes=VisualDelta(step=step, agent_moves=[], agent_state_changes=[], resource_changes=[]),
            agent_moves=[],
            agent_mode_changes=[],
            agent_inventory_changes=[],
            agent_target_changes=[],
            agent_utility_changes=[],
            resource_collections=[],
            resource_spawns=[],
            resource_depletions=[],
            trade_events=[],
            trade_intents=[],
            economic_decisions=[],
            performance_metrics=[],
            debug_events=[]
        )
    
    # Single-pass agent processing for maximum efficiency
    visual_delta, agent_moves, agent_mode_changes, agent_inventory_changes, agent_target_changes, agent_utility_changes = self._record_agents_single_pass(simulation, step)
    
    # Record resource events (still separate as they're not agent-specific)
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
