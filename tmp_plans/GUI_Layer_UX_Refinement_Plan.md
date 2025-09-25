# GUI Layer & UX Refinement Plan (Phase A – No New Features)

Purpose
- Address the identified GUI Layer & UX issues without changing core simulation functionality or determinism.
- Keep changes surgical, with clear acceptance criteria and tests.

Non‑Goals
- No new economic mechanics or advanced overlays.
- Avoid large architectural shifts beyond a small API polish in the widget.

Guardrails
- Preserve determinism and existing hashes.
- Maintain performance targets (≥60 FPS typical; no unnecessary per‑frame work).
- Keep Start Menu → Simulation flow intact; tests should remain stable after updates.

---
## Summary of Issues to Address
1) Decision Mode radio is not respected in `MainWindow`.
2) Non‑baseline scenarios appear selectable (bounce back via QMessageBox).
3) Layout does not set stretch factors; viewport should remain pixel‑fixed while panels can expand.
4) Widget uses back‑reference `_controller_ref`; replace with a typed `controller` attribute (keep shim for compatibility).
5) Quit action calls `sys.exit(0)`; prefer `QApplication.quit()` for GUI hygiene.
6) Add basic tooltips/accessible names for controls (usability/accessibility polish).
7) Ensure viewport receives focus on simulation start for future shortcuts.
8) Add a minimal, consistent QSS style for groupings (visual polish).
9) Update/extend tests to cover the above behaviors.
10) Light documentation updates to reflect the wiring and UX behavior.

---
## Implementation Steps

### Step 1 – Wire Decision Mode Radio (Baseline Only)
- Intent: The “Decision Mode: Enabled/Disabled” radio should control simulation stepping mode in baseline scenario. Legacy scenario forces legacy.
- Files:
  - `src/econsim/gui/main_window.py`
  - `src/econsim/gui/start_menu.py`
  - (Optional) `src/econsim/gui/session_factory.py` (only if we decide to add a field)
- Changes:
  - Read `selection.decision_mode_enabled` in `MainWindow._on_launch_requested` and pass to:
    - `EmbeddedPygameWidget(..., decision_mode=selection.decision_mode_enabled)`
    - `controller.set_decision_mode(selection.decision_mode_enabled)`
  - If `selection.scenario == 'legacy_random'`: override `decision_mode=False` and (in Start Menu) disable the radio controls.
- Tests:
  - New test: Launch baseline with decision disabled → widget/controller use legacy path.
  - Existing tests should still pass; no determinism change by default.
- Acceptance:
  - Baseline: radio toggles mode. Legacy: radio disabled and legacy enforced.

Note on approach choices:
- Option A (Minimal): Do not change `SimulationSessionDescriptor`; use `selection.decision_mode_enabled` directly in `MainWindow` (recommended).
- Option B (Structured): Add `decision_enabled: bool` to `SimulationSessionDescriptor` and thread it through. Slightly more churn for limited gain.

### Step 2 – Disable Non‑Implemented Scenarios in Start Menu
- Intent: Avoid modal bounce; show disabled items with tooltip.
- Files: `src/econsim/gui/start_menu.py`
- Changes:
  - After populating `self.scenario_box`, disable non‑baseline entries using `setItemData(idx, False, Qt.ItemDataRole.UserRole - 1)` or the appropriate role to mark as disabled; add tooltip (“Not implemented yet”).
  - Keep baseline enabled and selected.
- Tests:
  - New test: Non‑baseline entries reported disabled; selection remains on baseline.
- Acceptance:
  - Users cannot select non‑baseline; baseline remains functional.

### Step 3 – Layout Stretch Factors
- Intent: Keep viewport pixel‑fixed; allow right panel to expand on window resize.
- Files: `src/econsim/gui/main_window.py`
- Changes:
  - After creating `content_layout = QHBoxLayout()`, set: `content_layout.setStretch(0, 0)` and `content_layout.setStretch(1, 1)`.
  - Viewport already uses `setFixedSize(descriptor.viewport_size, descriptor.viewport_size)`.
- Tests:
  - New smoke test: After resize, viewport width equals requested fixed size; right panel width increased.
- Acceptance:
  - Resizing window does not scale viewport; panels get extra space.

### Step 4 – Widget Controller Attachment (API Polish)
- Intent: Replace dynamic `_controller_ref` back‑reference with a typed attribute; keep shim for backward compatibility.
- Files:
  - `src/econsim/gui/embedded_pygame.py`
  - `src/econsim/gui/main_window.py`
- Changes:
  - Add `self.controller: Optional[SimulationController] = None` on the widget and use it in `_on_tick` instead of `getattr(..., "_controller_ref", None)`.
  - Maintain compatibility: if `self.controller` is None, fall back to `getattr(self, "_controller_ref", None)` once (do not re‑use `_controller_ref` in new code paths).
  - In `MainWindow`, set `pygame_widget.controller = controller` instead of `setattr(pygame_widget, "_controller_ref", controller)`.
- Tests:
  - Existing tests should continue to pass (shim present). Optional: add a test that manual/auto stepping still functions after the change.
- Acceptance:
  - No behavioral change, cleaner API surface.

### Step 5 – Quit Behavior
- Intent: Use Qt application shutdown semantics.
- Files: `src/econsim/gui/start_menu.py`
- Changes:
  - Replace `sys.exit(0)` with `QApplication.instance().quit()` (with defensive fallback if instance is None).
- Tests:
  - Add a small test that monkeypatches `QApplication.quit` to ensure it’s called.
- Acceptance:
  - Clean GUI shutdown via Qt.

### Step 6 – Tooltips & Accessible Names
- Intent: Incremental polish; aids discoverability without behavior changes.
- Files:
  - `src/econsim/gui/panels/controls_panel.py`
  - `src/econsim/gui/panels/overlays_panel.py`
  - `src/econsim/gui/panels/metrics_panel.py`
- Changes:
  - Add `setToolTip` for core controls (pause/resume, step, refresh, rate, respawn, overlay toggles, metrics update) and `setAccessibleName` for screen readers.
- Tests:
  - Not strictly required; keep as visual polish.
- Acceptance:
  - Tooltips present on hover; accessible names set.

### Step 7 – Focus the Viewport on Launch
- Intent: Ensure keyboard focus goes to the viewport (future shortcuts ready).
- Files: `src/econsim/gui/main_window.py`
- Changes:
  - After building the simulation page: `pygame_widget.setFocusPolicy(Qt.StrongFocus)` and `pygame_widget.setFocus()`.
- Tests:
  - Optional: Check `pygame_widget.hasFocus()` after launch.
- Acceptance:
  - Viewport holds focus by default.

### Step 8 – Minimal QSS Styling (Optional, Non‑Functional)
- Intent: Subtle visual coherence; group box headers and padding.
- Files: `src/econsim/gui/main_window.py` (apply to root) or panel widgets.
- Changes:
  - Apply a small stylesheet, e.g.:
    - `QGroupBox { font-weight: 600; margin-top: 8px; }`
    - `QGroupBox::title { subcontrol-origin: margin; left: 6px; }`
    - `QLabel { font-size: 11px; }`
- Tests:
  - None.
- Acceptance:
  - Visual consistency; no behavioral changes.

### Step 9 – Tests
- Additions (see steps above):
  - Decision radio wiring (baseline)
  - Scenario disabled state
  - Layout stretch => viewport fixed
  - Quit uses QApplication.quit
  - Optional: viewport focus
- Command: `pytest -q` (CI will run all; locally run target tests to iterate quickly).

### Step 10 – Documentation
- Files:
  - `API_GUIDE.md` – Note that the Start Menu decision radio controls mode in baseline; legacy ignores it.
  - `completed_steps_docs/current_status/gui_ascii_layouts.md` – Confirm panels, footer, decision mode note.
- Acceptance:
  - Docs in sync with UI behavior; no feature inflation.

---
## Rollout Plan (Phased)

- Phase 1 (Core wiring + layout)
  - Steps: 1, 2, 3, 4, 5
  - Rationale: Functional correctness and small API hygiene with minimal blast radius.

- Phase 2 (Polish)
  - Steps: 6, 7, 8
  - Rationale: UX improvements; safe and quick.

- Phase 3 (Tests + Docs)
  - Steps: 9, 10
  - Rationale: Lock in behavior and document reality.

---
## Options & Trade‑offs

- Decision Mode wiring
  - Option A (Minimal): Use `selection.decision_mode_enabled` directly in `MainWindow` (recommended).
  - Option B (Descriptor): Add `decision_enabled: bool` to `SimulationSessionDescriptor`. More explicit, but touches more code.

- Scenario handling
  - Option A: Disable non‑baseline entries in the combobox (recommended; no modal).
  - Option B: Keep modal bounce (current behavior); lower polish.

- Widget controller ref
  - Option A: Add `controller` attribute with `_controller_ref` fallback (recommended; minimal risk).
  - Option B: Hard cutover to `controller` only (riskier; needs thorough test sweep).

- QSS Styling
  - Option A: Minimal QSS as listed.
  - Option B: Defer styling to a separate visual pass.

---
## Acceptance Checklist
- Baseline decision radio toggles both widget `decision_mode` and controller mode.
- Legacy scenario forces legacy and disables radio controls.
- Non‑baseline scenarios visibly disabled; baseline remains default selection.
- Resizing window does not scale viewport; right panel expands.
- Widget uses `controller` attribute; `_controller_ref` kept only as compatibility fallback.
- Quit exits via `QApplication.quit()`.
- Tooltips on core controls; accessible names set.
- Viewport gains initial focus.
- Tests added/passing; docs updated.

---
## Verification Strategy
- Run targeted tests for new behaviors; then run full suite.
- Manual smoke: `make dev`, launch baseline; toggle decision radio; resize window; hover controls for tooltips; confirm footer states update and focus is on viewport.

---
Last updated: 2025‑09‑24

