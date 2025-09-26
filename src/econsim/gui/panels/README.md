# GUI Panels (`econsim.gui.panels`)

Modular Qt widgets providing focused educational or control functionality. Each panel is read-mostly over simulation/controller state; all mutation flows through `SimulationController` APIs.

## Panels Overview
### `agent_inspector_panel.py`
- Panel: displays per-agent details (carrying bundle, home inventory, utility, preference type).
- Typical functions/classes:
  - `AgentInspectorPanel`: Dropdown of agent IDs, refresh timer updating displayed stats, selection propagation (used by `EmbeddedPygameWidget` for highlight).

### `controls_panel.py`
- Simulation control panel (play/pause, step, pacing selection, respawn interval/rate, feature toggles for foraging/bilateral exchange).
- Key roles:
  - Bind UI controls to `SimulationController` (pause/resume, set playback TPS, toggle foraging/trade, adjust respawn).
  - Exposes `_speed_box`, `_pacing_label` used by pacing tests.

### `event_log_panel.py`
- Displays chronological trade events and (future) decision/target selection events.
- Pulls data via controller `get_recent_trades()` each refresh tick; formats readable lines.

### `metrics_panel.py`
- Snapshot of aggregate simulation metrics (steps, remaining resources, determinism hash, optional trade counters).
- Refresh timer calls controller methods: `ticks()`, `remaining_resources()`, `determinism_hash()`, plus direct metrics collector fields when present.

### `overlays_panel.py`
- Checkbox matrix controlling `OverlayState` flags (grid lines, agent IDs, target arrows, home labels, trade lines).
- Emits state changes that the `EmbeddedPygameWidget` reads from its `overlay_state` attribute.

### `status_footer_bar.py`
- Lightweight status bar (FPS estimate, step count, hash snippet) for bottom UI region.
- Periodically queries controller for steps and performance (`steps_per_second_estimate()`).

### `trade_inspector_panel.py`
- Educational insight into current trading layer.
- Sections: Trade Status, Active Intents, Economic Insights, Educational Controls.
- Uses controller methods: `trade_draft_enabled()`, `trade_execution_enabled()`, `active_intents_count()`, `get_active_intents()`, `calculate_total_welfare_change()`, `count_trading_pairs()`, `analyze_preference_diversity()`, `last_trade_summary()`.
- Provides visualization toggles (arrows, highlights) forwarded to controller for potential render integration.

## Common Patterns
- Each panel uses a QTimer (≈4 Hz) for refresh; keep logic O(agents) worst-case.
- Defensive try/except wrappers prevent UI stalls due to transient simulation state.
- Avoid direct mutation of agent or grid state; panels remain observers.

## Refactor Opportunities
- Consolidate refresh timers into a shared panel refresh dispatcher to reduce timer overhead.
- Standardize panel interface (e.g., `refresh()` method) for easier dynamic composition.
- Introduce typed dataclasses for event / trade records instead of raw dicts for clarity.
