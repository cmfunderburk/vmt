# GUI Layer (`econsim.gui`)

PyQt6 layer embedding a single Pygame Surface for deterministic visualization. Provides user controls, start menu, inspector panels, and educational overlays.

## Design Principles
- Single QTimer inside `EmbeddedPygameWidget` orchestrates step + render.
- No secondary threads/timers; avoid blocking calls.
- Rendering is a pure view over simulation state (no mutations besides highlight bookkeeping).

## File Inventory
### `embedded_pygame.py`
Core widget bridging PyQt6 and Pygame.
- Class `EmbeddedPygameWidget`: owns off-screen Pygame Surface, QTimer, frame loop.
  - `_on_tick()`: Steps simulation (if present), throttles via controller, triggers scene update + repaint.
  - `_update_scene()`: Draw background, grid, resources, agents, overlays, blinking variance block, trade highlights, paused watermark.
  - `paintEvent()`: Blits RGBA bytes into a `QImage` for on-screen display.
  - `closeEvent()`: Ref-counted `pygame.quit()` + safe surface nulling to prevent segfaults.
  - `_draw_selected_agent_highlight()`: Draws highlight border for selected agent.
  - `get_surface_bytes()`: Testing helper to retrieve raw RGBA bytes.
  - `_show_overlay` property: Legacy compatibility alias for overlay regression tests.

### `simulation_controller.py`
Controller façade mediating GUI interactions with `Simulation`.
- Playback & pacing: `set_playback_tps`, `_should_step_now`.
- Pause/resume: `pause()`, `resume()`, `is_paused()`.
- Decision vs legacy movement: `set_decision_mode()`.
- Foraging / bilateral exchange flags: `set_forage_enabled()`, `set_bilateral_enabled()`, accessors.
- Trade inspector support: `trade_draft_enabled()`, `trade_execution_enabled()`, `get_active_intents()`, welfare and pair counting helpers.
- Respawn controls, hash retrieval, agent introspection (IDs, bundles, utility, preference type).
- Trade event log updater `_update_trade_history()` maintaining last N trades.

### `session_factory.py`
Factory utilities (if implemented) that construct a `Simulation`, attach `SimulationController`, and configure GUI widgets (e.g., panels, central widget) based on menu selection. Ensures deterministic seeding and optional metrics/respawn wiring.

### `start_menu.py`
Start menu Qt widget for scenario configuration.
- `MenuSelection` dataclass: captures chosen scenario, seed, grid size, agent count, density, metrics flag, decision mode, perception radius, viewport size.
- `StartMenuPage`: Builds form controls, disables non-implemented scenarios (`bilateral_exchange`, `money_market`), validates input, emits selection to launch callback.

### `main_window.py`
Top-level application window.
- Assembles `EmbeddedPygameWidget`, controller, and panel dock widgets.
- Wires menu actions (pause, step, hash refresh, overlays toggles) to controller and widget.
- Manages layout & teardown.

### `overlay_state.py`
Lightweight state container for overlay toggles.
- Class `OverlayState`: boolean flags controlling display of grid lines, agent IDs, target arrows, trade lines, home labels; potentially extended for future overlays.

### `_enhanced_trade_visualization.py` (experimental / optional)
Rendering helpers for richer trade visualization (arrows, highlights) — currently gated / partially disabled. Functions expect a Pygame surface + active trade intents to overlay directional indicators.

### `_trade_debug_overlay.py` (legacy/debug)
Earlier diagnostic overlay path (currently disabled in main render loop) showing raw trade intent information for debugging; may be retired or refactored.

### Panels Subpackage (`gui/panels/`)
See separate README in `panels/` for per-panel details.

## Extensibility Notes
- Add new panels by querying controller read-only APIs; avoid mutating simulation directly.
- For new overlays, extend `OverlayState` and integrate in `_update_scene()` within a single guarded block to preserve performance.
- Maintain O(n) rendering: no per-pixel Python loops; batch simple primitive draws or sprite blits only.
