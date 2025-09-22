# Copilot Instructions for VMT (EconSim Platform)

## Repository Overview

**VMT** is an educational **Economic Simulation Platform** (EconSim) designed to teach microeconomic theory through spatial agent-based visualizations. This is a **Desktop GUI Application** built with PyQt6 that uses visualization-first development to help students understand abstract economic concepts through concrete spatial interactions.

### Key Repository Information
- **Project Type**: Desktop GUI Application with Educational Focus
- **Primary Language**: Python 3.11+
<!-- STREAMLINED OPERATIONAL INSTRUCTIONS (Gate 1 Focus) -->
# VMT Operational Copilot Instructions (Gate 1 – Technical Validation)

Archive of full planning-oriented instructions: see `copilot-instructions-full.md` in this directory.

## 1. Phase Context & Objective
Current Phase: Week 0 – Gate 1 implementation and validation (IN PROGRESS).
Status: Core implementation COMPLETE, validation and refinement phase.
Primary Objective: Validate and document Gate 1 completion criteria, prepare transition to Grid/Agent foundations.

## 2. Gate 1 Status Summary
IMPLEMENTATION: ✅ COMPLETE
VALIDATION: 🔄 IN PROGRESS

Achieved:
- ✅ PyQt6 window with embedded Pygame surface (EmbeddedPygameWidget)
- ✅ Stable 62.5 FPS rendering with moving primitives and color cycling
- ✅ Clean shutdown, no resource leaks or zombie processes
- ✅ CI workflow passes (lint, type check, unit tests)
- ✅ Performance instrumentation (perf_stub.py with widget mode)
- ✅ Headless compatibility (offscreen + SDL dummy driver)

Current Focus: Gate 1 completion validation, checklist updates, transition planning.

## 3. Current Development Environment
Environment: ✅ READY (vmt-dev virtual environment configured)
```bash
cd /home/chris/PROJECTS/vmt
source vmt-dev/bin/activate  # Dependencies installed and verified
make dev                     # Launches GUI with 62.5 FPS rendering
make test                    # All 3 tests pass
make lint                    # Code style enforced
```
Performance validation: `python3 scripts/perf_stub.py --mode widget --duration 5`

## 4. Scope Guardrails (Enforced)
In-Scope Now:
- Core app skeleton (PyQt6 QApplication + main window)
- Pygame surface creation + update loop via QTimer
- FPS measurement + print

Deferred (Do NOT build yet):
- Agents, grid logic, preference math, analytics, tutorials, packaging, persistence, advanced logging, visual regression harness.

## 5. Completed Work Units ✅
1. ✅ Skeleton project (pyproject, package, test_imports)
2. ✅ Dual init (PyQt6 + Pygame init/quit) with headless fallback
3. ✅ Embedded off-screen widget with paint pipeline
4. ✅ Moving primitive + frame counter (62.5 FPS sustained)
5. ✅ FPS measurement script with widget mode
6. ✅ CI workflow passes with offscreen compatibility

Current Phase: Gate 1 completion documentation and transition prep.

## 6. Core Commands Cheat Sheet
```bash
make install   # pip install -e .[dev]
make dev       # run app
make lint      # ruff + black --check
make format    # black src tests
make type      # mypy (relaxed initially)
make test      # pytest -q
make perf      # scripts/perf_stub.py (prints JSON)
make clean     # remove caches
```

## 7. File Landmarks (Early Stage)
- src/econsim/main.py – entry point
- src/econsim/gui/embedded_pygame.py – widget (planned)
- scripts/perf_stub.py – FPS probe
- tests/unit/test_imports.py – smoke
- .github/workflows/ci.yml – automation

## 8. AI Response Protocol
Each assistant response should supply:
Goal | Actions | Result | Next.
No rehashing of planning corpus unless explicitly requested.

## 9. Performance Targets (Gate 1)
- FPS: ≥30 (stretch 60) with trivial render.
- Frame pacing: stdev < 10ms (informal eyeball ok).
- CPU: single core not pegged continuously.
- Memory: stable (< +10MB drift over 10s).

## 10. Troubleshooting Fast Paths
Issue: Window freeze → Ensure no while True; rely on QTimer.
Issue: Low FPS → Avoid per-frame QImage conversions; keep Surface small.
Issue: Teardown error → Quit pygame before QApplication.quit().
Issue: Black window → Confirm paint/update chain calls self.update().

## 11. Fallback Strategies
- If direct embedding stalls: render to off-screen Surface, convert to bytes → QImage → paint.
- If FPS <30: reduce surface size (e.g., 320x240) before optimizing.
- If event loop conflict: remove any nested loops; only QTimer ticks.

## 12. Minimal Expansion Path (Post-DoD)
Next after Gate 1 success (in order):
1. Stable widget interface abstraction
2. Grid scaffolding (no agents)
3. Agent placeholder + tick loop
4. Preference interface (no math) + stub strategies

## 13. Do / Don’t Summary
Do: Small commits, measure FPS early, keep render path simple, codify guardrails.
Don’t: Add agents, optimize prematurely, introduce threading, build packaging.

## 14. Reference Pointers
Full architecture & planning: orientation_docs/README.md
Gates: orientation_docs/implementation_phase_gates.md
Scenarios spec: orientation_docs/educational_scenarios_specification.md
Transition plan: orientation_docs/validation_to_production_transition_plan.md

## 15. Metrics Collection Stub (Planned)
scripts/perf_stub.py output (example):
```json
{"frames": 300, "duration_s": 5.02, "avg_fps": 59.8}
```

## 16. Risk Snapshot (Live)
- Embedding complexity: fallback = off-screen blit.
- Event loop starvation: rely solely on QTimer(16ms).
- Performance regressions: run perf stub each meaningful render change.
- Scope creep: reject additions not enabling DoD.

## 17. Assistant Escalation Rules
If blocked >2 attempts on embed: log obstacle, switch to fallback path and continue.
If FPS unresolved after fallback: document constraint, proceed (still acceptable if ≥30). 

---
Operational mode engaged. Proceed with implementation tasks; archive retained for deep reference.
- **Educational goal**: Show that economic theory is flexible framework, not rigid assumptions

### Key Planning Document Sections
- **Architecture overview**: `initial_planning.md` lines 378-468
- **Build specifications**: `initial_planning.md` lines 470-556  
- **CI/CD workflows**: `initial_planning.md` lines 558-630
- **Quality gates**: `initial_planning.md` lines 848-857
- **Strategic decisions**: `Current_Assessment.md` lines 49-191

### Implementation Priorities
1. **Spatial foundation** before economic theory
2. **Visual feedback** for all parameter changes
3. **Cross-platform consistency** for educational use
4. **Performance optimization** to maintain educational thresholds