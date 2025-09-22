Gate 1 — Implementation Plan

Goal
----
Prove a stable PyQt6 + Pygame embedded rendering widget with a working offscreen fallback and measurable performance (>=30 FPS, target 60 FPS). This is the spatial foundation for later agent/grid work.

Contract (tiny)
----------------
- Inputs: Python 3.11+ runtime, installed dependencies (PyQt6, pygame)
- Outputs: Runnable `make dev` that opens a PyQt6 window with an embedded Pygame surface or an offscreen fallback that renders to a QImage.
- Error modes: Missing deps, display/X not available, event loop conflicts.
- Success criteria: App runs, renders primitives, maintains >=30 FPS for 5s, clean shutdown with no zombie processes.

Acceptance criteria (must pass all)
-----------------------------------
1. The embedded widget displays moving primitives (rect/circle) and a frame counter.
2. The render loop runs at >=30 FPS for 5 seconds on a typical dev laptop.
3. App quits cleanly with pygame.quit() and QApplication.quit() without lingering processes.
4. Offscreen fallback works in headless CI using SDL_VIDEODRIVER=dummy and still passes a smoke render test.
5. `scripts/perf_stub.py --mode widget` returns JSON with avg_fps >=30.

Step-by-step plan
------------------
1) Environment verification (1-2 hours)
   - Verify active Python is 3.11+ and `vmt-dev` virtualenv exists.
   - Check installed packages: PyQt6 (>=6.4), pygame (>=2.0), pytest.
   - If missing, add `requirements.txt` or update `pyproject.toml` with pinned versions.

2) Create minimal example (2-4 hours)
   - Build a tiny PyQt6 app that creates a window and embeds a pygame Surface via offscreen QImage blit.
   - Render a moving rectangle and frame counter.
   - Provide `make dev` target to run this example.

3) Add headless/offscreen fallback (1-2 hours)
   - Implement SDL_VIDEODRIVER=dummy fallback when no display is present.
   - Ensure QImage conversion path still works for screenshots.

4) Add perf probe and run baseline (1 hour)
   - Use `scripts/perf_stub.py` to capture avg FPS for 5-10s.
   - Record results and tweak surface size if needed.

5) Tune frame loop & resource management (2-4 hours)
   - Adjust QTimer intervals, surface scaling, and conversion paths to reduce frame jitter.
   - Ensure clean shutdown sequence: stop timer, pygame.quit(), QApplication.quit().

6) Tests & CI integration (2-3 hours)
   - Add pytest tests for import, render smoke (headless), and perf probe with lenient thresholds.
   - Update `.github/workflows/ci.yml` to set SDL_VIDEODRIVER=dummy for headless runs and include the perf smoke test.

7) Documentation and final validation (1-2 hours)
   - Update `README.md` and `orientation_docs/Week0/Week 0 Success Metrics.md` with results and instructions.
   - Run the acceptance checklist and finalize Gate 1 status in docs.

Estimated total: 10-18 hours (spread across 1-3 days depending on interruptions)

Quick commands
--------------
# Activate env
source vmt-dev/bin/activate

# Run app
make dev

# Perf probe
python3 scripts/perf_stub.py --mode widget --duration 5

Testing
-------
- Happy path: `make dev`, observe render & FPS >=30 for 5s.
- Headless CI: `SDL_VIDEODRIVER=dummy python -m pytest tests/unit/test_render_smoke.py` should pass.

Edge cases
----------
- Missing PyQt6 or pygame: fail with explict message and instructions to pip install -r requirements.txt
- Display present but QPA mismatch: document using QT_QPA_PLATFORM=offscreen where necessary
- Slow hardware: document shrinking surface size or lowering target FPS for dev runs

Notes
-----
- Keep frame buffer small initially (e.g., 320x240) to make reaching targets easier.
- Prefer QTimer over busy loops to play well with Qt event loop.
- If problems embedding directly, use an offscreen pygame Surface and blit to QImage for painting.
