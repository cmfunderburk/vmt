# Gate 1 Technical Validation Checklist

Objective: Establish a functional PyQt6 application embedding (or blitting from) a Pygame surface rendering a moving primitive with stable frame updates, instrumented FPS, and clean shutdown.

## Definition of Done (All Required)
- [ ] PyQt6 window launches and closes without warnings/exceptions.
- [ ] Pygame initialized and quit safely (no lingering SDL resources).
- [ ] Embedded (or off-screen) Pygame surface renders moving rect / color cycle.
- [ ] Sustains ≥30 FPS average over ≥5 seconds (stretch goal: ≥55–60 FPS) with trivial render.
- [ ] FPS stats printed (or JSON) including frames, duration, avg_fps.
- [ ] No zombie Python process after window close (process exits normally).
- [ ] CI workflow passes: lint + relaxed type + smoke test.
- [ ] Scope guardrails honored (no agents, economics, analytics, tutorials, persistence, threading, packaging).

## Explicit Out-of-Scope for Gate 1
- Economic preference implementation logic.
- Agent movement / grid simulation.
- Data analytics or export features.
- Tutorial / educational scenario system.
- Packaging (PyInstaller) or distribution artifacts.
- Complex logging or configuration layering.
- Visual regression harness.

## Implementation Steps (Recommended Order)
1. Skeleton (DONE): project structure, pyproject, main window stub.
2. Dual init: add pygame init/quit function to verify coexistence.
3. Embedded widget: QWidget subclass with off-screen Surface.
4. Render loop: QTimer driving frame updates + moving primitive.
5. FPS instrumentation: frame count + elapsed time output.
6. Graceful teardown: ensure `pygame.quit()` in widget close event.
7. CI verification: smoke test that creates and destroys widget.
8. Refine performance: confirm ≥30 FPS; shrink surface if needed.

## Fallback Strategies
| Issue | Action |
|-------|--------|
| Direct embed unstable | Use off-screen Surface -> QImage paint path |
| FPS <30 early | Reduce surface size (<= 320x240); avoid per-frame scaling |
| Event loop freeze | Remove any loops; rely solely on QTimer(16ms) |
| Teardown errors | Centralize cleanup; guard idempotent `pygame.quit()` |
| High CPU | Lower timer frequency temporarily (e.g. 33ms) |

## Instrumentation Plan
- Temporary `scripts/perf_stub.py` runs to produce JSON: `{frames, duration_s, avg_fps}`.
- Later extension: add stdev, frame time histogram.

## Acceptance Review
Before merging Gate 1 completion PR:
- [ ] Checklist items all checked.
- [ ] Screenshot (optional) of moving primitive.
- [ ] Perf stub JSON pasted in PR description.
- [ ] Notes on any deviations or compromises.

## Post-Gate 1 Next Steps (Do Not Start Before Completion)
1. Abstract render/update interface.
2. Introduce grid scaffold (no agents).
3. Add agent placeholder + tick mechanism.
4. Implement preference interface skeleton (no math yet).
5. Prepare Gate 2 checklist.

---
Owner: Chris F.
Created: 2025-09-22
