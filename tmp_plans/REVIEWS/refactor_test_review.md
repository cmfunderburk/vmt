# Test Review for Phase 3 Cleanup

**Date:** October 3, 2025  
**Purpose:** Review all existing tests to determine which should be kept vs removed  
**Process:** Place an X in [ ] after "Keep?" to indicate the test should be retained  

---

## Test Configuration Files

tests/conftest.py
*Shared test configuration and fixtures for pytest
Keep? [X]
--

tests/fixtures/custom_tests/duplicate_id_case.py
*Test fixture for duplicate ID validation cases
Keep? [X]
--

tests/fixtures/custom_tests/malformed_case.py
*Test fixture for malformed test case validation
Keep? [X]
--

tests/fixtures/custom_tests/valid_case.py
*Test fixture for valid test case validation
Keep? [X]
--

---

## Integration Tests

tests/integration/test_hash_stabilization.py
*Tests that simulation hash remains stable across runs (determinism)
Keep? [X]
--

tests/integration/test_refactor_safeguards.py
*Integration tests to validate refactor changes don't break core functionality
Keep? [ ]
--

---

## Observability Tests

tests/observability/simple_test_runner.py
*Simple test runner for observability components
Keep? [ ]
--

tests/observability/test_file_observer.py
*Tests for file observer functionality
Keep? [ ]
--

---

## Performance Tests

tests/performance/__init__.py
*Performance test package initialization
Keep? [ ]
--

tests/performance/baseline_capture.py
*Captures performance baselines for regression testing
Keep? [ ]
--

tests/performance/determinism_capture.py
*Captures determinism baselines for regression testing
Keep? [ ]
--

tests/performance/test_raw_data_performance.py
*Performance tests for raw data operations
Keep? [ ]
--

---

## Raw Data Tests

tests/test_raw_data_observer.py
*Tests for raw data observer functionality
Keep? [ ]
--

tests/test_raw_data_writer.py
*Tests for raw data writer functionality
Keep? [ ]
--

---

## Unit Tests - Components

tests/unit/components/__init__.py
*Components test package initialization
Keep? [X]
--

tests/unit/components/test_event_emitter.py
*Tests for event emitter component
Keep? [X]
--

tests/unit/components/test_inventory.py
*Tests for inventory management component
Keep? [X]
--

tests/unit/components/test_mode_state_machine.py
*Tests for agent mode state machine
Keep? [X]
--

tests/unit/components/test_movement.py
*Tests for agent movement logic
Keep? [X]
--

tests/unit/components/test_target_selection.py
*Tests for target selection logic
Keep? [X]
--

tests/unit/components/test_trading_partner.py
*Tests for trading partner matching logic
Keep? [X]
--

---

## Unit Tests - Launcher

tests/unit/launcher/test_cards.py
*Tests for test card widget functionality
Keep? [X]
--

tests/unit/launcher/test_comparison.py
*Tests for test comparison functionality
Keep? [X]
--

tests/unit/launcher/test_data_locations.py
*Tests for data location handling in launcher
Keep? [ ]
--

tests/unit/launcher/test_discovery.py
*Tests for test discovery mechanism
Keep? [X]
--

tests/unit/launcher/test_executor.py
*Tests for test execution in launcher
Keep? [X]
--

tests/unit/launcher/test_gallery.py
*Tests for test gallery widget
Keep? [X]
--

tests/unit/launcher/test_integration_registry_adapter.py
*Tests for integration registry adapter
Keep? [ ]
--

tests/unit/launcher/test_launcher_smoke.py
*Smoke tests for launcher functionality
Keep? [ ]
--

tests/unit/launcher/test_no_legacy_symbols.py
*Tests to prevent reintroduction of legacy symbols
Keep? [ ]
--

tests/unit/launcher/test_programmatic_runner.py
*Tests for programmatic test runner
Keep? [ ]
--

tests/unit/launcher/test_registry.py
*Tests for test registry functionality
Keep? [ ]
--

tests/unit/launcher/test_style.py
*Tests for launcher styling
Keep? [ ]
--

tests/unit/launcher/test_tab_manager.py
*Tests for tab management in launcher
Keep? [X]
--

tests/unit/launcher/test_types.py
*Tests for launcher type definitions
Keep? [ ]
--

tests/unit/launcher/test_vmt_launcher_window.py
*Tests for main launcher window
Keep? [X]
--

---

## Unit Tests - Core Simulation

tests/unit/test_agent.py
*Tests for agent behavior and state
Keep? [X]
--

tests/unit/test_agent_state.py
*Tests for agent state management
Keep? [X]
--

tests/unit/test_agent_typed_collect.py
*Tests for typed collection behavior in agents
Keep? [X]
--

tests/unit/test_bilateral_stagnation.py
*Tests for bilateral exchange stagnation scenarios
Keep? [X]
--

tests/unit/test_bootstrap_epsilon.py
*Tests for bootstrap epsilon behavior
Keep? [X]
--

tests/unit/test_collection_events.py
*Tests for resource collection events
Keep? [X]
--

tests/unit/test_competition.py
*Tests for competitive scenarios
Keep? [X]
--

tests/unit/test_decision_determinism.py
*Tests for decision-making determinism
Keep? [ ]
--

tests/unit/test_decision_determinism_adv.py
*Advanced tests for decision-making determinism
Keep? [ ]
--

tests/unit/test_demo_determinism.py
*Demo tests for determinism validation
Keep? [ ]
--

tests/unit/test_density_grid.py
*Tests for density-based grid operations
Keep? [X]
--

tests/unit/test_determinism_hash.py
*Tests for determinism hash calculation
Keep? [ ]
--

tests/unit/test_distance_scaling_factor.py
*Tests for distance scaling factor behavior
Keep? [X]
--

tests/unit/test_embedded_widget.py
*Tests for embedded pygame widget functionality
Keep? [ ]
--

tests/unit/test_enhanced_trade_visualization.py
*Tests for enhanced trade visualization features
Keep? [ ]
--

tests/unit/test_fairness_round_increments.py
*Tests for fairness in round increments
Keep? [ ]
--

tests/unit/test_grid.py
*Tests for grid functionality and operations
Keep? [ ]
--

tests/unit/test_imports.py
*Tests to validate import structure
Keep? [ ]
--

tests/unit/test_logging_micro_delta_threshold.py
*Tests for logging micro delta threshold behavior
Keep? [ ]
--

tests/unit/test_manual_auto_hash_parity.py
*Tests for parity between manual and automatic hash calculation
Keep? [ ]
--

tests/unit/test_metrics_integrity.py
*Tests for metrics collection integrity
Keep? [ ]
--

tests/unit/test_micro_delta_event_once.py
*Tests for micro delta event emission (once per step)
Keep? [ ]
--

tests/unit/test_no_guilogger.py
*Tests to ensure GUILogger is not present
Keep? [ ]
--

---

## Unit Tests - Performance

tests/unit/test_perf_decision_mode.py
*Performance tests for decision mode operations
Keep? [X]
--

tests/unit/test_perf_decision_throughput.py
*Performance tests for decision throughput
Keep? [X]
--

tests/unit/test_perf_handler_breakdown.py
*Performance tests for handler breakdown
Keep? [X]
--

tests/unit/test_perf_overhead.py
*Performance tests for system overhead
Keep? [X]
--

tests/unit/test_perf_simulation.py
*Performance tests for simulation operations
Keep? [ ]
--

tests/unit/test_perf_widget.py
*Performance tests for widget operations
Keep? [ ]
--

---

## Unit Tests - Playback and Recording

tests/unit/test_playback_engine.py
*Tests for playback engine functionality
Keep? [X]
--

tests/unit/test_recording_system.py
*Tests for recording system functionality
Keep? [X]
--

---

## Unit Tests - Preferences

tests/unit/test_preference_shift.py
*Tests for preference shifting behavior
Keep? [X]
--

tests/unit/test_preferences_cobb_douglas.py
*Tests for Cobb-Douglas preference implementation
Keep? [X]
--

tests/unit/test_preferences_factory.py
*Tests for preference factory functionality
Keep? [X]
--

tests/unit/test_preferences_leontief.py
*Tests for Leontief preference implementation
Keep? [X]
--

tests/unit/test_preferences_perfect_substitutes.py
*Tests for perfect substitutes preference implementation
Keep? [X]
--

tests/unit/test_preferences_sensitivity.py
*Tests for preference sensitivity analysis
Keep? [ ]
--

tests/unit/test_preferences_serialize.py
*Tests for preference serialization
Keep? [ ]
--

---

## Unit Tests - Priority and Delta

tests/unit/test_priority_delta_flag_reorders_intents.py
*Tests for priority delta flag reordering trade intents
Keep? [X]
--

tests/unit/test_priority_flag_intent_multiset_invariance.py
*Tests for priority flag intent multiset invariance
Keep? [X]
--

---

## Unit Tests - Rendering and UI

tests/unit/test_render_smoke.py
*Smoke tests for rendering functionality
Keep? [ ]
--

---

## Unit Tests - Respawn

tests/unit/test_respawn_density.py
*Tests for respawn density behavior
Keep? [X]
--

tests/unit/test_respawn_type_diversity.py
*Tests for respawn type diversity
Keep? [X]
--

---

## Unit Tests - Session and Validation

tests/unit/test_session_descriptor_validation.py
*Tests for session descriptor validation
Keep? [ ]
--

tests/unit/test_shutdown.py
*Tests for system shutdown behavior
Keep? [ ]
--

---

## Unit Tests - Simulation Core

tests/unit/test_simulation.py
*Core tests for simulation functionality
Keep? [X]
--

tests/unit/test_simulation_factory.py
*Tests for simulation factory
Keep? [X]
--

tests/unit/test_snapshot_replay.py
*Tests for snapshot and replay functionality
Keep? [ ]
--

---

## Unit Tests - Start Menu

tests/unit/test_start_menu_disabled_scenarios.py
*Tests for disabled scenarios in start menu
Keep? [ ]
--

tests/unit/test_start_menu_invalid_input_dialog.py
*Tests for invalid input dialog in start menu
Keep? [ ]
--

---

## Unit Tests - Step Processing

tests/unit/test_step_decomposition_parity.py
*Tests for step decomposition parity
Keep? [X]
--

tests/unit/test_step_handlers_core.py
*Tests for core step handlers
Keep? [X]
--

---

## Unit Tests - Tiebreaking

tests/unit/test_tiebreak_ordering.py
*Tests for tiebreaking ordering logic
Keep? [ ]
--

---

## Unit Tests - Trading

tests/unit/test_trade_draft_intents.py
*Tests for trade draft intent functionality
Keep? [X]
--

tests/unit/test_trade_economic_coherence.py
*Tests for trade economic coherence
Keep? [X]
--

tests/unit/test_trade_edge_cases.py
*Tests for trading edge cases
Keep? [X]
--

tests/unit/test_trade_intent_delta_utility_computed.py
*Tests for trade intent delta utility computation
Keep? [X]
--

tests/unit/test_trade_metrics_realized_gain_and_ticks.py
*Tests for trade metrics realized gain and ticks
Keep? [X]
--

tests/unit/test_trade_overlay_debug_smoke.py
*Smoke tests for trade overlay debug functionality
Keep? [ ]
--

tests/unit/test_trade_overlay_executed_highlight.py
*Tests for trade overlay executed highlight
Keep? [ ]
--

tests/unit/test_trade_phase1_foundations.py
*Tests for trade phase 1 foundations
Keep? [ ]
--

tests/unit/test_trade_phase3_execution.py
*Tests for trade phase 3 execution
Keep? [ ]
--

---

## Unit Tests - Unified Selection

tests/unit/test_unified_pair_convergence.py
*Tests for unified pair convergence
Keep? [X]
--

tests/unit/test_unified_selection.py
*Tests for unified selection logic
Keep? [X]
--

---

## Unit Tests - Widget and Teardown

tests/unit/test_widget_simulation_teardown.py
*Tests for widget simulation teardown
Keep? [ ]
--

---

## Summary

**Total Tests Found:** 103  
**Tests to Review:** 103  

**Instructions:**
1. Review each test above
2. Place an X in the [ ] after "Keep?" if the test should be retained
3. Leave [ ] empty if the test should be removed
4. Tests without X will be deleted during Phase 3 cleanup

**Criteria for Keeping:**
- Tests current production code behavior
- Tests a known bug that was fixed (regression test)
- Tests critical path (agent movement, trading, metrics)
- Tests determinism or performance guarantees
- Tests public API of a module

**Criteria for Removing:**
- Tests removed code or feature
- Tests intermediate refactoring state
- Tests internal implementation detail (not behavior)
- Duplicates another test's coverage
- Has misleading name or unclear purpose
