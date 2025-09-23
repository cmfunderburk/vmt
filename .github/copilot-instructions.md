## VMT Copilot Instructions (High-Signal Operational Guide)
Context: PyQt6 desktop shell embedding a fixed 320x240 Pygame surface driving a deterministic spatial micro‑econ agent simulation. Preserve determinism, frame pipeline, and O(agents+resources) step cost.

### Core Loop (Do NOT Alter Structure)
`EmbeddedPygameWidget` (`src/econsim/gui/embedded_pygame.py`) owns a single `QTimer` (16 ms). No while True, no threads. Frame = (optional `Simulation.step` → `_update_scene` → `update()` → `paintEvent` blits existing Surface → QImage). Never reallocate the main Surface; never change `SURFACE_SIZE` or `FRAME_INTERVAL_MS` without gate justification.

### Determinism Invariants
Tie-break key EXACT: (-ΔU, distance, x, y) (see `tests/unit/test_tiebreak_ordering.py`). Resource iteration order must remain sorted + stable; agent list order determines contest priority (`test_competition.py`). Constants `EPSILON_UTILITY`, `default_PERCEPTION_RADIUS` fixed (`simulation/constants.py`). Metrics hash (see `simulation/metrics.py`) must not drift unless an intentional model change (update tests then).

### Construction / Preferred Entry
Use `Simulation.from_config(SimConfig, preference_factory, agent_positions)` (seeds internal RNG, conditionally attaches `RespawnScheduler`, `MetricsCollector`). Direct `Simulation(...)` only in legacy tests. Preferences: pure `utility(bundle)` / no mutation; register new types via `PreferenceFactory` with serialization + parameter validation tests.

### Optional Hooks (Inert When Absent)
`respawn_scheduler.step` and `metrics_collector.record` each run O(agents+resources). Any new hook: single None check → early return; no hidden iteration expansion.

### Performance Guardrails
Target ~62 FPS (floor ≥30). If regression: 1) Surface reallocation? 2) Per‑frame object churn in `_on_tick`/`paintEvent`? 3) Blocking I/O? Use `python scripts/perf_stub.py --mode widget --duration 2 --json` or `make perf`. Overlays / HUD must not add >~2% overhead (prove or document).

### Snapshot & Replay
Serialization order: extend only (do not reorder existing keys). Snapshot → restore must yield identical metrics hash for unchanged logic (`test_snapshot_replay.py`). When adding state: include in serialize/restore AFTER existing fields, update determinism tests deliberately.

### Complexity Bound
Per step stays linear in agents + resources. Avoid all‑pairs scans (agent↔resource nested loops) beyond existing bounded neighborhood scan. Gate any experimental search/path logic behind a feature flag + micro benchmark.

### Rendering Rules
Keep conversion pipeline: `pygame.image.tostring(surface,'RGBA')` → `QImage` → `QPainter.drawImage`. No scaling intermediate surfaces, no per‑pixel Python loops. Overlay additions must reuse existing Surface and cached fonts.
Home Label Overlay: Each agent's home cell may display a small `H{id}` label. Font must be cached (reuse existing overlay font) and drawn after agent rectangles. Do not introduce per-frame font creation or variable-length text measurement loops beyond the minimal blit. Maintain O(agents) overlay complexity.

### Teardown Discipline
`closeEvent`: stop timer → `pygame.quit()` → super call. Mirror this order for new subsystems (stop → dispose → quit). Ensure no active timers post‑close.

### Allowed vs Forbidden
Allowed: new preference type (+ tests), lightweight overlay toggle, deterministic factory config extension, metrics field append (hash adjusted intentionally), doc sync. Forbidden: threads/custom loops, surface size change, silent tie-break or constant edits, mutating preference during `utility`, unordered iteration, hidden randomness outside seeded RNGs.

### Workflow Commands
Env: `pip install -e .[dev]`  |  GUI: `make dev`  |  Tests: `make test`  |  Perf: `python scripts/perf_stub.py --mode widget --duration 2 --json`  |  Legacy random: `ECONSIM_LEGACY_RANDOM=1 make dev`.

### Contribution Style
State intent → minimal diff → verify (tests/perf/hash) → summarize (Goal | Actions | Result | Next). Offer the smallest safe option set when ambiguity exists—do not widen scope without gate alignment (`ROADMAP_REVISED.md`).

### When Extending
New state: append serialize fields + update replay/hash tests. New preference: add type, register in factory, add serialization + parameter validation test. New overlay: prove negligible FPS hit. Maintain determinism first; performance second; pedagogy visuals third.

Reference anchors: `README.md` (current scope), `ROADMAP_REVISED.md` (forward gates), `tests/unit/*` (behavioral guarantees).
Home Placement: Random non-overlapping agent home positions chosen once using deterministic secondary RNG seed (`seed+9973`) via `random.sample` over ordered cell list. Any change to seed offset or sampling order is a determinism-impacting modification and must be gated (update roadmap + tests).

### Respawn Policy (Baseline Alternation)
Current respawn implementation (Gate Docs Update increment) introduces deterministic multi-type diversity:
* Scheduler alternates resource types A ↔ B each spawn via an internal boolean toggle.
* No additional RNG draws: alternation is O(1) per spawned resource.
* Complexity remains O(agents + resources) per step; respawn still bounded by `max_spawn_per_tick` and early empty-cell enumeration.
* Determinism: Spawn type sequence is fully determined by (seeded shuffle ordering + toggle parity). Identical seeds and consumption patterns yield identical resource type layouts.
* Hash Stability: Metrics hash includes resource type in serialization; alternating policy preserved parity for identical seeds (see `test_respawn_type_diversity.py`). Any future change (weighted ratios, adaptive strategies) MUST:
	1. Be gated (roadmap item) with performance micro-benchmark.
	2. Update or add diversity & determinism tests.
	3. Document new policy rationale here and in `README.md`.
Non-goals at this stage: proportional weighting, adaptive feedback (consumption rate), spatial clustering. These require explicit future gate approval.

### Playback Pacing & Logging (Gate GUI Fix Addendum)
Playback control now lives in `ControlsPanel` with a speed dropdown including an explicit `Unlimited` option (`None` => per-frame). Mode defaults:
* Turn mode: 1.0 tps throttled (pacing label shows `(pacing)`).
* Continuous & legacy: Unlimited (no pacing label text).

Changing speed updates `SimulationController.set_playback_tps`; the embedded widget consults `_should_step_now(now)` each tick for throttled modes. Do NOT introduce alternative timers or sleep loops—extend only via controller logic if needed.

Manual vs auto determinism: `SimulationController.manual_step` uses a persistent RNG seeded from `simulation.config.seed` and a mode flag (`set_decision_mode`). Mixing manual and automatic steps must yield identical metrics hash as pure automatic stepping for the same total count (see `test_manual_auto_hash_parity.py`). Any change risking divergence requires updating that test and documenting rationale.

FPS logging: Default stdout is silent. Enable per-second FPS diagnostics only via `ECONSIM_DEBUG_FPS=1`. Never reintroduce unconditional frame prints; add new diagnostics behind explicit env flags or a verbose mode.

Pause semantics: Turn mode starts paused (button text `Resume`), other modes start running (`Pause`). Keep this invariant; update `test_pause_button_initial_label.py` if intentionally changed.

When adding pacing-related features, prove no regression in step throughput under Unlimited and that throttled pacing still meets educational intent (1.0 tps within small tolerance). Add/extend tests rather than relying on manual observation.

### Mandatory Gate Workflow (Before Any Push)
1. Gate Todos: create `Gate_N_todos.md` (scope, acceptance criteria, ordered steps).
2. Checklist: derive `GATE_N_CHECKLIST.md` (binary check items from criteria).
3. Agreement: review scope/risks/timeline with stakeholder; freeze scope.
4. Execute: follow steps; update todos + checklist as items complete (no silent scope creep).
5. Retrospective: write `GATE_N_EVAL.md` mapping each criterion → evidence, note perf impact, debt, residual risks, readiness.
6. Only Then Commit/Push: after retrospective exists and reflects delivered vs promised.
Violations risk hidden scope & regression; always document deltas, performance impact, technical debt, and next‑gate readiness.