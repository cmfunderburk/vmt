# Comprehensive GUI Plan (Draft v0.1) – Post Gate 6 Foundation

Status: DRAFT (to iterate). Scope: Define a scalable, deterministic, educational GUI that launches to a menu before any simulation starts.

---
## 1. Grounding Constraints (Must Not Break)
- Single Qt event loop; frame pacing via existing `QTimer` (16 ms) in `EmbeddedPygameWidget`.
- Fixed embedded Pygame surface: 320x240 RGBA; no per-frame surface reallocation.
- Determinism invariants: tie-break key (−ΔU, dist, x, y); sorted resource iteration; agent list ordering; `EPSILON_UTILITY` bootstrap constants unchanged.
- Optional hooks (`respawn_scheduler`, `metrics_collector`) remain O(agents+resources) and inert when absent.
- Snapshot/replay hash parity must hold for identical configs.
- Per-step complexity target: O(agents + resources); no all-pairs expansions.
- FPS baseline ~62 (floor ≥30); forbid new blocking waits, background threads, or hidden loops.
- Rendering extras (HUD, overlays, inspector panels) must not mutate simulation state.

## 2. High-Level GUI Objectives
Educational:
1. Let users select distinct “visual runs” (scenarios) illustrating economic concepts (preferences, decision vs random, density/respawn dynamics, turn mode pacing).
2. Provide transparent, inspectable state (agent inventories, utility values, chosen targets, resource counts) without polluting core simulation purity.
3. Support controlled stepping (pause, single-step, multi-step burst) for classroom explanation.
4. Enable consistent reproducibility (display seed & scenario parameters; export/share config snapshot).

Operational:
1. Launch to a **Start Menu** (no simulation created yet) → choose scenario type, parameters template, and run mode.
2. Allow returning to menu (dispose existing simulation cleanly) to load another run.
3. Modular panels: simulation viewport, controls panel, metrics/inspector panel, optional log/output panel.
4. Keep integration friction low (wrap existing `EmbeddedPygameWidget`, not rewrite rendering path).

## 3. First-Class Requirement (New): Start Menu
Purpose: Avoid auto-starting a default simulation; encourage explicit selection & parameterization.
Menu Features (Phase 1):
- Scenario list (cards or list view) with short description & icon.
- Run modes (toggle / dropdown): Continuous (current), Turn Mode (educational pacing), Performance Probe, Preference Comparison (single-agent demos), Legacy Random Walk.
- Basic parameter presets: grid size, agents count, resource density, enable respawn/metrics.
- Seed entry (with randomize button) + deterministic indicator.
- Launch button (validates selections → build config → instantiate simulation window stack page).
- Footer: version, gates summary, link to docs.

Back Navigation:
- In-run toolbar “Return to Menu” → confirm dialog → destroys active simulation widget (ensuring timer stopped before disposal) → shows menu page.

## 4. Functional Requirements (Aggregated)
Controls (In-Run):
- Run / Pause toggle
- Step 1, Step N (configurable, e.g., 5)
- Speed selector (0.25×, 1×, 2×, 5×) – modifies decision step cadence (NOT frame timer)
- Overlay toggles: grid, resource labels, agent IDs, utility values, target arrow, heat/contour (future)
- Metrics snapshot: compute & display determinism hash + counts
- Export: Save current simulation snapshot (JSON) & optional replay script stub
- Scenario reset (same seed) & reseed (new seed) buttons

Inspector / Panels:
- Agent list panel: select agent → detail view (position, inventories, target, last ΔU, preference parameters)
- Resource summary: remaining counts per type, density estimate, respawn stats (if enabled)
- Metrics panel: ticks elapsed, steps/sec (decision), FPS (optional), determinism hash, respawn events
- Event log (optional deferred): structured entries for resource collection, tie-break contest outcomes, respawns

Menu Scenario Types (Initial Set):
1. Baseline Decision Mode (multi-agent)
2. Turn Mode (pedagogical stepping overlays)
3. Preference Comparison (runs small single-agent sequences sequentially in tabs or composite view)
4. Respawn Dynamics (density vs time visualization)
5. Performance Probe (high agent/resource count; collects throughput numbers)
6. Legacy Random Walk (for contrast / regression)

## 5. Proposed Architecture
Top-Level Window (`MainWindow`):
- Central `QStackedWidget` with pages: `StartMenuPage`, `SimulationPage`.
- Menu builds a `SimulationSessionDescriptor` (pure dataclass) → passed to a `SessionFactory` which:
  1. Translates selection → `SimConfig`
  2. Picks/constructs `preference_factory` (single or set)
  3. Seeds RNG, invokes `Simulation.from_config`
  4. Returns `SimulationController` (GUI wrapper + references)

Simulation Page Layout (Horizontal Split):
- Left: `EmbeddedPygameWidget` (existing) inside a frame
- Right (tabbed or stacked panel): Controls | Inspector | Metrics | (optional Log)
- Status bar: seed, tick, steps/sec, determinism hash (live, throttled)

Controllers & Separation:
- `SimulationController`: owns simulation instance, RNG, timing policy (decision cadence), step queue for Turn Mode.
- `OverlayManager`: resolves which overlays to render (flag state only; drawing still inside Pygame widget or sub-surface pass).
- `InspectorModel`: cached read-only snapshots (poll at throttled interval e.g., 4 Hz) to avoid per-frame heavy UI updates.
- `EventBus` (lightweight): Qt signals (e.g., step_completed, snapshot_ready, agent_selected) – avoid custom loop.

Navigation Flow:
1. Launch → `StartMenuPage`
2. User selects scenario & parameters → “Launch” → build descriptor → instantiate session → push to `SimulationPage`.
3. Return to Menu → controller `.teardown()` (stop timer → detach hooks → release refs) → delete widget(s) → show menu.

## 6. State Management & Data Flow
- Simulation state is canonical inside `Simulation` object (no duplication in GUI objects).
- Read access only for UI; transformations occur in read-only snapshot structs (e.g., `AgentView`, `ResourceStatsView`).
- Update cadence:
  - Frame (≈62 Hz): render only (no UI model rebuild except cheap counters)
  - Stats / inspector poll (e.g., every 250 ms via separate QTimer) to refresh heavy panels
  - Decision steps triggered by: continuous cadence timer OR Turn Mode queued steps
- Turn Mode: queue ensures only one step can be “pending”; autoplay enqueues one after previous finishes to preserve deterministic ordering.

## 7. Performance & Determinism Safeguards
- Budget: Additional GUI overhead < 2 ms cumulative per 16 ms frame (soft target).
- Inspector polling: capped object allocations; reuse view objects or simple tuples.
- Overlay toggles: boolean flags; avoid branching explosion in main loop—compose into a single render pass that conditionally draws.
- Determinism Test Hook: Provide `--gui-smoketest` headless invocation that launches a scenario, runs N steps, outputs hash.
- Prohibited: per-agent Qt widgets inside hot step path, cross-thread simulation stepping, dynamic resizing of base surface.

## 8. Phased Implementation Roadmap (Aligned to Future Gates)
Phase A (Gate 7 Adjacent – Foundations):
- Start Menu (Baseline scenarios list + seed + launch)
- SessionFactory + SimulationPage skeleton
- Return to Menu teardown path
- Basic controls: Run/Pause, Step 1, Step 5
- Determinism hash display (manual refresh button)

Phase B:
- Agent inspector panel (read-only)
- Metrics panel (steps/sec, FPS, respawn stats)
- Speed selector & configurable step burst size
- Snapshot export (JSON)

Phase C:
- Preference Comparison scenario orchestration
- Turn Mode integration (queue + autoplay + overlay adaptors)
- Overlay toggles (grid, IDs, targets, utility text)

Phase D:
- Performance Probe scenario (auto run & summarized stats)
- Event log (structured) with optional filtering
- Scenario reset & reseed actions

Phase E:
- Advanced overlays (utility contours, heatmaps) – perf gated
- Scenario save/load (persist descriptor + seed)
- Multi-window “compare two runs” view (optional stretch)

Acceptance per Phase: tests (headless), reproduction of determinism hash, no FPS regression (> -5%).

## 9. Testing Strategy
Headless GUI Tests:
- Use `QT_QPA_PLATFORM=offscreen` + `SDL_VIDEODRIVER=dummy` to launch menu, programmatically select scenario, run N steps.
- Hash parity test: menu launch → run → snapshot → restart same descriptor → verify identical hash.
Component Tests:
- `SessionFactory` produces expected `SimConfig` for presets.
- Turn queue ensures single outstanding step; burst stepping integrity.
Performance:
- Automated perf baseline: measure steps/sec pre/post GUI expansion (allow small fixed overhead).
Regression Visual (Optional Later):
- Byte diff overlay test remains (extend cases for new overlays with tolerant thresholds).

## 10. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Over-updating UI each frame | FPS drop | Throttle inspector refresh; diff-based updates |
| Determinism break via UI ordering | Invalid tests | All simulation actions funneled through controller single method; no parallel timers |
| Overlay complexity bloat | Render slowdown | Group draw calls; precompute static layers |
| Memory churn from snapshots | GC pauses | Reuse structs / namedtuples; limit allocations per poll |
| Multi-scenario menu sprawl | UX confusion | Categorize scenario types + concise descriptors |
| Turn Mode step race | Ordering instability | Single queue + processing flag; tests for order |

## 11. Implementation Artifacts (Planned Modules)
- `src/econsim/gui/main_window.py` (new)
- `src/econsim/gui/start_menu.py`
- `src/econsim/gui/session_factory.py`
- `src/econsim/gui/simulation_controller.py`
- `src/econsim/gui/panels/controls_panel.py`
- `src/econsim/gui/panels/inspector_panel.py`
- `src/econsim/gui/panels/metrics_panel.py`
- `src/econsim/gui/overlays/` (future advanced overlays)

## 12. Data Structures (Draft)
`SimulationSessionDescriptor`:
```python
dataclass SimulationSessionDescriptor:
    name: str                # scenario name key
    mode: str                # 'continuous' | 'turn' | 'perf' | 'pref_compare' | 'legacy'
    seed: int
    grid_size: tuple[int,int]
    agents: int
    density: float | None
    enable_respawn: bool
    enable_metrics: bool
    preference_type: str | list[str]
    turn_auto_interval_ms: int | None
```

`InspectorSnapshot` (polled): positions, inventories, targets (immutable tuples), resource counts.

## 13. Open Questions (For Next Iteration)
1. Do we prioritize Preference Comparison or Turn Mode polish first in Gate 7 context?
2. Should the menu allow custom arbitrary parameter editing (expert mode) or only presets initially?
3. Required minimal overlay set for first public educational demo?
4. Is a compact deterministic hash (8 chars) sufficient in UI vs full hex?
5. Do we show utility values live per agent, or only on selection (performance tradeoff)?

## 14. Immediate Next Steps (Suggested)
1. Approve scope of Phase A (menu + session factory + core controls + hash display).
2. Confirm initial scenario catalog (baseline, turn, legacy, perf?).
3. Decide on parameter preset names (e.g., "Small Lab", "Crowded", "Sparse").
4. Greenlight data structure for `SimulationSessionDescriptor`.

---
Feedback Focus Request: Which Phase A items (if any) should be trimmed or expanded before code scaffolding? Any additional mandatory menu fields?
