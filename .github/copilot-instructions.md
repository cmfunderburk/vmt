## VMT Copilot Quick Instructions (Keep Responses Lean & Actionable)
Purpose: Fast orientation for AI agents contributing to VMT (PyQt6 desktop app embedding a Pygame surface). Focus on implemented functionality (Gates 1-2 complete) and enforced gate workflow discipline.

### Architecture Snapshot
Single process, single event loop. PyQt6 `QApplication` hosts a main window (`econsim.main:create_window`) whose central widget is `EmbeddedPygameWidget` (`src/econsim/gui/embedded_pygame.py`). Widget owns a QTimer (~16ms) that updates an off‑screen Pygame Surface (320x240) then repaints via `paintEvent` (Surface→RGBA bytes→`QImage`→draw). No threading, no background loops; all timing via QTimer + `app.processEvents()` in tests/perf. Preferences module (`src/econsim/preferences/`) provides Cobb-Douglas, Perfect Substitutes, and Leontief utility formulations with validation/serialization.

### Current Scope (Gates 1-2 Complete; Gate 3 Planning)
In-scope: widget maintenance, preferences system, performance/stability, documentation, test robustness, Gate 3 scaffolding (grid/agent foundations).
Out-of-scope until later gates: agent decision logic, advanced UI (menus/toolbars), threading, packaging, logging layers, analytics.

### Mandatory Gate Workflow (ENFORCE BEFORE ANY GIT PUSH)
**CRITICAL**: All gate work must follow this sequence. NO exceptions.

1. **Generate Todo List**: Create `Gate_N_todos.md` with scope, acceptance criteria, step-by-step plan
2. **Create Checklist**: Extract acceptance criteria into checkable `GATE_N_CHECKLIST.md` 
3. **Discuss & Agree**: Review scope, risks, timeline with stakeholder before implementation
4. **Execute Systematically**: Work through agreed steps; update todos/checklist as completed
5. **Write Retrospective Eval**: Create `GATE_N_EVAL.md` in critical evaluation style (map criteria to evidence, identify gaps/risks, assess readiness)
6. **ONLY THEN**: Git commit/push after retrospective eval documents the gate completion

**Violation = Scope creep risk**. Always document what was delivered vs promised, performance impact, technical debt created, and readiness for next gate.

### Core Developer Workflow
Activate env then use Make targets:
`make dev` (run GUI), `make test` (25 tests pass), `make lint` (ruff+black check), `make format`, `make type` (mypy), `make perf` (runs `scripts/perf_stub.py --mode widget`). Headless CI sets `SDL_VIDEODRIVER=dummy` and `QT_QPA_PLATFORM=offscreen` (see perf & tests). Prefer adding new Make targets rather than ad-hoc scripts.

### Key Files
`src/econsim/main.py` – entry + window factory.
`src/econsim/gui/embedded_pygame.py` – core Gate 1 widget (timer, frame loop, paint, teardown).
`scripts/perf_stub.py` – performance harness (synthetic + real widget modes).
`tests/unit/*` – smoke (`test_embedded_widget`), render progression (`test_render_smoke`), perf threshold (`test_perf_widget`), clean shutdown (`test_shutdown`). Use existing patterns when adding tests (headless env guards, short durations, skip instead of hard fail for flaky perf edge cases).

### Patterns & Conventions
Environment adaptation: before initializing Pygame or Qt in headless context, set `SDL_VIDEODRIVER=dummy`, `QT_QPA_PLATFORM=offscreen` (mirror existing tests & perf script). No global while-loops; rely on QTimer or explicit `app.processEvents()` loops with small sleeps. Internal widget counters (e.g., `_frame`) can be probed in performance/testing, but keep underscore prefix and avoid public API commitment yet.

### Performance Guardrails
Target: ≥30 FPS trivial workload (current ~62). If FPS regression: (1) verify no extra per-frame allocations (beware repeated conversions), (2) keep Surface small, (3) confirm QTimer interval unchanged. Use `scripts/perf_stub.py --mode widget --duration 2 --json` for quick check. Only optimize when below threshold or adding unavoidable cost.

### Shutdown Discipline
Always stop QTimer and call `pygame.quit()` in `closeEvent`. Tests assert pygame not initialized after widget close. If adding resources (surfaces, timers), mirror this teardown pattern.

### Safe Change Examples
GOOD: Add optional CLI flag in `perf_stub.py` to vary surface size; add test asserting FPS above floor. BAD: Introduce threading for render loop; expand widget into full simulation manager.

### When Unsure
Default to minimal diff preserving current frame loop contract. Reference planning docs in `orientation_docs/` only for clarification—do not implement future gate deliverables preemptively. If a task seems to require out-of-scope features, document constraint and propose smallest deferrable stub.

### Response Style (For AI Agents)
Each reply: brief Goal | Actions | Result | Next. Avoid restating these instructions verbatim; link specific files/functions instead.

---
Questions or ambiguity while staying within guardrails? Surface a concise options list (A/B) and recommended path.