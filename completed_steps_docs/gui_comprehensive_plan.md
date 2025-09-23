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
# Comprehensive GUI Plan (Draft v0.2) – Post Gate 6 Foundation

Status: UPDATED with Phase A decisions (Baseline Decision, Turn Mode, Legacy Random Walk; free-form advanced mode; dual hash display; early overlays: grid + agent IDs + target arrow; single preference per run; simple metrics panel).

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
1. Illustrate discrete economic concepts via selectable “visual runs”.
2. Reveal internal state (inventories, targets, utility) without polluting core logic.
3. Support classroom pacing (pause, step, small bursts).
4. Uphold reproducibility (seed + scenario descriptor surfaced, exportable).

Operational:
1. Launch to Start Menu (no simulation yet) → explicit scenario selection.
2. Return-to-menu navigation with safe teardown (stop timer → dispose → show menu).
3. Modular panels: viewport, controls, metrics/inspector (log deferred).
4. Integrate by wrapping existing widget—avoid altering core loop.

## 3. Start Menu (Phase A Scope)
Features:
- Scenario list (Baseline Decision / Turn Mode / Legacy Random Walk).
- Mode selection inside scenario (Turn Mode implies queued stepping).
- Presets + free-form advanced input (grid size, agents, density, seed, respawn/metrics toggles, preference type).
- Seed field + randomize button + deterministic badge.
- Launch button (validates, constructs descriptor → session factory → simulation page).
- Footer: version, gate summary link(s).
Back Nav: Toolbar "Return to Menu" (confirmation) triggers controller teardown (stop timer first).

## 4. Functional Requirements (Aggregated)
Controls:
- Run/Pause, Step 1, Step 5.
- Determinism hash (full + 8-char truncated) manual refresh.
- Overlays toggles (Phase A): grid lines, agent IDs, target arrow.
- Simple metrics mini-panel: ticks, remaining resources, steps/sec (decision) estimate.
- (Deferred) Speed selector, utility text overlay, snapshot export, reseed/reset.

Inspector / Panels (Deferred to later phases except mini metrics):
- Agent inspector, resource summary, extended metrics, event log.

Menu Scenario Types (Phase A Implemented):
1. Baseline Decision Mode (multi-agent)
2. Turn Mode (pedagogical stepping overlays)
3. Legacy Random Walk (contrast / regression)

Deferred: Preference Comparison, Respawn Dynamics, Performance Probe.

## 5. Architecture Overview
`MainWindow` (QStackedWidget pages): StartMenuPage | SimulationPage.
Session flow: StartMenu builds `SimulationSessionDescriptor` → `SessionFactory` returns `SimulationController` → SimulationPage wires controller + widget + panels.

Controllers & Separation:
- `SimulationController`: orchestrates stepping (continuous vs turn queue), stores descriptor, exposes read-only views.
- `OverlayManager`: simple flag container consumed by widget (no simulation coupling).
- `InspectorModel` (later): periodic snapshot builder (throttled QTimer ~250 ms).
- Signals (Qt): step_completed, hash_updated, metrics_updated, teardown_requested.

## 6. State & Data Flow
- Single source of truth: `Simulation` object.
- GUI never mutates simulation directly; actions call controller methods (which call `Simulation.step`).
- Frame loop unchanged (widget timer). Turn Mode: controller enqueues one step at a time—no parallel stepping timers.
- Hash refresh: user-triggered button (later optional auto mode).

## 7. Performance & Determinism Safeguards
- Added GUI CPU/frame budget < 2 ms average.
- Metrics/ID/target overlays: draw conditionally in existing pass; no extra surfaces.
- Free-form validation rejects pathological grid sizes or agent counts early.
- No threads; timers only: frame timer (existing) + optional low-frequency metrics poll.
- Test hook: headless scenario launch producing hash (future smoke test).

## 8. Phase Roadmap (Revised)
Phase A (now defined): Start Menu, free-form advanced mode, Baseline/Turn/Legacy scenarios, single preference, basic controls, overlays (grid/IDs/target), metrics mini-panel, hash dual display.
Phase B: Agent inspector, speed selector, snapshot export, full metrics panel, reseed/reset.
Phase C: Preference Comparison, Turn Mode autoplay polish (queue UX), overlay utility text.
Phase D: Respawn Dynamics & Performance Probe scenarios, event log, scenario reset UI.
Phase E: Advanced overlays (utility contours), scenario save/load, multi-run comparison view.

## 9. Testing Strategy (Initial)
- Headless smoke: construct descriptor → build simulation via factory (no window) → N steps → compute hash.
- Menu automation (later): programmatically select fields (QtTest) offscreen.
- Determinism: repeat same descriptor twice, verify identical hash + resource counts.
- Perf guard: measure decision steps/sec with / without overlays (allow <2% diff Phase A).

## 10. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Free-form inputs degrade perf | Large grids reduce FPS | Clamp & warn; preset defaults prominent |
| Turn queue error races | Determinism break | Single queue flag + test ordering |
| Overlay expansion creep | Render slowdown | Gate new overlays; perf test each addition |
| Hash confusion (dual display) | UX clutter | Truncate inline; full on hover / details pane |
| Metrics poll too frequent | Frame stutter | Throttle to 4 Hz; reuse objects |

## 11. Implementation Artifacts (Planned)
- `src/econsim/gui/main_window.py`
- `src/econsim/gui/start_menu.py`
- `src/econsim/gui/session_factory.py`
- `src/econsim/gui/simulation_controller.py`
- `src/econsim/gui/panels/controls_panel.py`
- `src/econsim/gui/panels/metrics_panel.py` (mini panel)
- (Deferred) inspector_panel, overlays/, log panel

## 12. Data Structures
```python
@dataclass
class SimulationSessionDescriptor:
    name: str                 # scenario key
    mode: str                 # 'continuous' | 'turn' | 'legacy'
    seed: int
    grid_size: tuple[int, int]
    agents: int
    density: float | None
    enable_respawn: bool
    enable_metrics: bool
    preference_type: str      # single preference only Phase A
    turn_auto_interval_ms: int | None
```
`InspectorSnapshot` (later): agent tuples, resource counts, timestamp.

## 13. Open Questions (Next Iteration)
1. Turn Mode polish scope (tails/fade) include now or Phase B?
2. Preset naming & exact param matrix (provide or accept proposed defaults?).
3. Advanced mode validation style (inline vs modal) & error messaging tone.
4. Auto hash refresh toggle (default off) priority? Add in Phase A or B?
5. Metrics expansion trigger: which additional indicators justify full panel (respawn stats, decision throughput history)?

## 14. Immediate Next Steps
1. Scaffold Phase A modules (empty shells + docstrings + TODO markers).
2. Add `SimulationSessionDescriptor` + `SessionFactory.build()` mapping descriptor → `Simulation`.
3. Provide headless smoke test for descriptor→simulation path.
4. (Optional) Env flag to opt-in new MainWindow until stabilized.

---
Feedback: Confirm whether Turn Mode visual polish should slip into Phase A before coding scaffolds. If no change, scaffolding proceeds as above.
