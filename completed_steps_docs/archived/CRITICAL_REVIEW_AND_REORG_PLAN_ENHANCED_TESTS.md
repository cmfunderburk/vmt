**Title**
**Executiv**What's Working Well**
- VMT launcher UX and features are coherent and useful:
  - Test gallery with side-by-side "original" vs "framework" launch.
  - Comparison**Acceptance Criteria (Alpha Packaging)**
- `pip install -e .[launcher]` and `econsim-launcher` launches the same UI as today's `make enhanced-tests`.
- `pip install -e .` provides core simulation without GUI dependencies (headless operation, programmatic API).
- Adding a new test requires a single edit to `framework/test_configs.py` and optionally a small runner stub—no filename map edits in UI code.
- Presets, bookmarks, and custom tests persist outside the repo by default; repo stays clean after normal use.
- Logs default to an appdata/state directory; `gui_logs/` at repo root is deprecated but accessible via env override.
- CI runs lint/type/smoke tests on both core and launcher packages; `MANUAL_TESTS/` remains for examples and wrappers only.
- Graceful degradation: attempting to run launcher without PyQt6 shows helpful error message directing to `pip install econsim-vmt[launcher]`.selection and batch launch.
  - Live configuration editor, presets, and custom-test generation.
  - Bookmark manager and batch runner integrations.ary**
- The VMT launcher is feature-rich and serves as the primary user interface for demos, education, and development. However, implementation is monolithic and relies on path hacks and subprocesses to run scripts by filename, which is brittle.
- "Framework" code that should be part of the library lives in `MANUAL_TESTS/framework`, causing import gymnastics and duplication with `src/econsim/gui/*`.
- Data and logs are written into the repo tree (e.g., `gui_logs/`, `MANUAL_TESTS/config_presets.json`, `MANUAL_TESTS/custom_tests/`), which will pollute the working tree and complicate packaging.
- A modest structural refactor will convert the current launcher into a proper package with a console script and clean data locations, while preserving the GUI experience and Makefile UX.cal Review and Reorganization Plan for VMT Launcher (Main User Environment)

**Date**
2025-09-27

**Scope**
- Focuses on the canonical workflow launched via `make enhanced-tests` and the related code under `MANUAL_TESTS/` and `src/econsim/`.
- Goal: streamline development and delivery of the VMT launcher (primary user interface) for an alpha release, reduce drift/duplication, and create a stable packaged entrypoint.

**Executive Summary**
- The enhanced launcher is feature-rich and usable for demos and development. However, implementation is monolithic and relies on path hacks and subprocesses to run scripts by filename, which is brittle.
- “Framework” code that should be part of the library lives in `MANUAL_TESTS/framework`, causing import gymnastics and duplication with `src/econsim/gui/*`.
- Data and logs are written into the repo tree (e.g., `gui_logs/`, `MANUAL_TESTS/config_presets.json`, `MANUAL_TESTS/custom_tests/`), which will pollute the working tree and complicate packaging.
- A modest structural refactor will convert the current launcher into a proper package with a console script and clean data locations, while preserving the GUI experience and Makefile UX.

**What’s Working Well**
- Enhanced launcher UX and features are coherent and useful:
  - Test gallery with side-by-side “original” vs “framework” launch.
  - Comparison mode selection and batch launch.
  - Live configuration editor, presets, and custom-test generation.
  - Bookmark manager and batch runner integrations.
- Good movement toward centralization under `MANUAL_TESTS/framework/` (e.g., `base_test`, `phase_manager`, `ui_components`, `test_configs`).
- Centralized GUI logging system in `src/econsim/gui/debug_logger.py` with sane env flags and compact formats.
- Documentation is strong and up-to-date for the current reality and educational goals.

**Key Findings (Risks and Anti‑Patterns)**
- Monolithic launcher and UI composition
  - `MANUAL_TESTS/enhanced_test_launcher_v2.py:1` is ~41K and blends widgets, styling, tabs, card logic, parsing files, and process launching. Hard to test and evolve.
- Brittle path manipulation and split “framework” location
  - Manual `sys.path` modification and imports from `MANUAL_TESTS/framework/` appear in several files (e.g., `MANUAL_TESTS/framework/simulation_factory.py:1`, `MANUAL_TESTS/enhanced_test_launcher_v2.py:15`).
  - Shared framework elements should be in `src/` to avoid implicit working-directory contracts.
- Script-by-filename launch coupling and drift risk
  - Mapping dicts of test IDs to filenames duplicate truth and are already drifting. Example: `_launch_original_test()` references `test_2_sparse_longrange.py` and `test_3_dense_shortrange.py` but repo has `MANUAL_TESTS/test_2_sparse_new.py` and `MANUAL_TESTS/test_3_highdensity_local.py` (naming mismatch). See `MANUAL_TESTS/enhanced_test_launcher_v2.py:804`.
- Repo-polluting data locations
  - Logs: `gui_logs/` (root) instead of an appdata or XDG location (`src/econsim/gui/debug_logger.py:1`).
  - Presets and generated tests: `MANUAL_TESTS/config_presets.json` and `MANUAL_TESTS/custom_tests/` are useful for dev, but will dirty the repo for users.
- Subprocess per test
  - Launching via `subprocess.Popen([sys.executable, str(test_path)])` (e.g., `MANUAL_TESTS/enhanced_test_launcher_v2.py:876`) is simple but locks us into file-based scenarios, prevents a stable Python API for programmatic runs, and duplicates env wiring.
- Packaging integration missing
  - No console script entry for the launcher; `make enhanced-tests` shells into `MANUAL_TESTS/`. Hard to ship as a package.
- Styling and platform fixes are embedded
  - `_apply_platform_styling()` is large and UI-specific within the launcher (e.g., `MANUAL_TESTS/enhanced_test_launcher_v2.py:1078`). Should be factored for reuse.

**Target Architecture (Package the VMT Launcher)**
- Create a proper, importable package under `src/econsim/tools/launcher/` with a console script. Keep `MANUAL_TESTS/` as thin dev wrappers and examples.

- Proposed package layout:
  - `src/econsim/tools/launcher/__main__.py` — module entrypoint to support `python -m econsim.tools.launcher`.
  - `src/econsim/tools/launcher/app.py` — `VMTLauncher` main window and application wiring.
  - `src/econsim/tools/launcher/cards.py` — `TestCardWidget`, `CustomTestCardWidget`.
  - `src/econsim/tools/launcher/gallery.py` — grid/population and comparison mode management.
  - `src/econsim/tools/launcher/tabs/config_editor.py` — current `live_config_editor.py` moved and adapted.
  - `src/econsim/tools/launcher/tabs/batch_runner.py` — current `batch_test_runner.py` moved and adapted.
  - `src/econsim/tools/launcher/tabs/bookmarks.py` — current `test_bookmarks.py` moved and adapted.
  - `src/econsim/tools/launcher/custom_tests.py` — discovery, parsing, open/edit/delete actions.
  - `src/econsim/tools/launcher/runner.py` — programmatic test execution; replaces direct script launching.
  - `src/econsim/tools/launcher/framework/` — relocate from `MANUAL_TESTS/framework/`:
    - `test_configs.py`, `base_test.py`, `phase_manager.py`, `ui_components.py`, `simulation_factory.py`, `test_utils.py`.
  - `src/econsim/tools/launcher/style.py` — platform styling helpers (current `_apply_platform_styling`).

- Console scripts and optional dependencies structure:
  - Add to `pyproject.toml`:
    - `[project.scripts] econsim-launcher = "econsim.tools.launcher.app:main"` (or `vmt-launcher`)
    - `[project.optional-dependencies] launcher = ["PyQt6>=6.5.0"]` - allows core simulation install without GUI tools
    - Core dependencies remain minimal (numpy, pygame for headless rendering)
  - Update `make enhanced-tests` to call `python -m econsim.tools.launcher` and set sane defaults for env flags (keep the current compact educational logging experience).

- Data locations (with migration):
  - Use XDG Base Directory or per-OS appdata defaults with project overrides:
    - Presets: `~/.config/econsim/launcher/presets.json` (fallback to repo during dev).
    - Bookmarks: `~/.config/econsim/launcher/bookmarks.json`.
    - Custom tests: `~/.local/share/econsim/launcher/custom_tests/`.
    - Logs: `~/.local/state/econsim/gui_logs/` (symlink or fallback to `./gui_logs` in dev).
  - First-run migration: if repo-local files exist, copy them into appdata; keep reading from new location afterward.

**Detailed Reorg Plan (Phased, Low-Risk)**

- Phase 0: Stabilize and tag alpha
  - Freeze launcher behavior, tag the repo, and document current Makefile UX for reference.
  - Capture “known-good” env flags for educational logging.

- Phase 1: Extract and package shared framework
  - Move `MANUAL_TESTS/framework/*` to `src/econsim/tools/launcher/framework/`.
  - Replace `sys.path` hacks with absolute package imports.
  - Ensure no circular dependencies with `src/econsim/` (the factory must only depend on public econsim APIs).
  - Acceptance: all manual tests import the package modules successfully via `from econsim.tools.launcher.framework import ...` and run unchanged.

- Phase 2: Factor the launcher into modules
  - Split `MANUAL_TESTS/enhanced_test_launcher_v2.py` into `app.py`, `cards.py`, `gallery.py`, `style.py`, and `custom_tests.py` under the new package.
  - Preserve widget look-and-feel and comparison semantics.
  - Acceptance: `python -m econsim.tools.launcher` launches the same UI; `make enhanced-tests` uses the module.

- Phase 3: Introduce a programmatic runner
  - Implement `runner.py` with APIs:
    - `run_config(config: TestConfiguration) -> None`
    - `run_by_id(test_id: int) -> None`
    - `run_original(config_id)` and `run_framework(config_id)` if “original vs framework” needs to be kept during transition.
  - Replace subprocess-based file launching with the runner, or keep subprocess but target `python -m econsim.tools.launcher.runner --config-id N` to decouple from filenames.
  - Acceptance: Launcher starts tests via runner, no file-path mapping dicts.

- Phase 4: Centralize test registry and metadata
  - Extend `TestConfiguration` to include optional metadata fields for runnable targets if needed during transition:
    - `original_entry: Optional[str]` and `framework_entry: Optional[str]` specifying module:callable or script fallback.
  - Build a single registry in `framework/test_configs.py` that the launcher uses (no ad-hoc filename maps).
  - Acceptance: adding a new test only requires touching `test_configs.py`.

- Phase 5: Data and logs relocation (with migration and fallbacks)
  - Implement an appdata resolver utility:
    - `get_data_dir()`, `get_config_dir()`, `get_state_dir()` respecting XDG/Windows/macOS conventions.
  - Migrate `config_presets.json`, bookmarks, and custom tests to appdata on first run; keep dev override via env var `ECONSIM_APPDATA_DIR` pointing to repo.
  - Point GUI debug logs to `state_dir/gui_logs`. Keep a dev symlink or environment override to maintain current habit.
  - Acceptance: presets persist across runs without modifying the repo; `gui_logs` no longer dirties the repo by default.

- Phase 6: Packaging and CLI
  - Add console script `econsim-launcher` (or `vmt-launcher`).
  - Implement optional dependencies structure in `pyproject.toml`:
    - Core package: simulation engine, headless capabilities, basic dependencies
    - `[launcher]` extra: PyQt6, GUI tools, full interactive environment
    - Installation: `pip install econsim-vmt` (core) vs `pip install econsim-vmt[launcher]` (full GUI)
  - Provide CLI flags mirroring current env toggles:
    - `--log-level`, `--log-format`, `--bundle-trades`.
    - `--open-tab=gallery|editor|batch|bookmarks|custom-tests`.
    - `--run TEST_ID[,TEST_ID...]` to quick-launch without clicking.
  - Update `Makefile:enhanced-tests` to use module entry and pass default flags; keep the env vars as backward-compatibility.
  - Acceptance: `pip install -e .[launcher]` then `econsim-launcher` works outside the repo; `pip install -e .` provides core simulation only.

- Phase 7: Tests and CI
  - Add smoke tests for the runner and registry (no GUI event loop):
    - Validate that configs load, and runner resolves targets.
  - Lint/Type check includes new package paths; exclude `MANUAL_TESTS/` from distribution but keep as examples.
  - Acceptance: CI passes; no coupling on working directory for imports.

- Phase 8: Documentation and deprecation path
  - New doc: `docs/LAUNCHER.md` explaining packaged usage and appdata locations.
  - Update `README.md` quick start to prefer `econsim-launcher`; keep `make enhanced-tests` for dev.
  - Thin wrappers in `MANUAL_TESTS/` import and call the package for backward compatibility; mark old script names as deprecated.

**Directory Tree (Target)**
- `src/econsim/tools/launcher/`
  - `__main__.py`
  - `app.py`
  - `cards.py`
  - `gallery.py`
  - `custom_tests.py`
  - `runner.py`
  - `style.py`
  - `framework/`
    - `__init__.py`
    - `test_configs.py`
    - `base_test.py`
    - `phase_manager.py`
    - `ui_components.py`
    - `simulation_factory.py`
    - `test_utils.py`
  - `tabs/`
    - `config_editor.py`
    - `batch_runner.py`
    - `bookmarks.py`

**Makefile and Build Updates**
- `Makefile:enhanced-tests` executes the packaged module and applies the current env defaults for educational logging:
  - Keep: `ECONSIM_LOG_LEVEL=EVENTS ECONSIM_LOG_FORMAT=COMPACT ECONSIM_DEBUG_AGENT_MODES=1 ECONSIM_DEBUG_TRADES=1 ECONSIM_DEBUG_ECONOMICS=1 ECONSIM_LOG_BUNDLE_TRADES=1`.
  - Replace the `cd MANUAL_TESTS && python enhanced_test_launcher_v2.py` with `python -m econsim.tools.launcher`.
- Add optional `LAUNCHER_ARGS` to forward flags.

**Immediate Code Smells to Address During Move**
- Replace hard-coded ID→filename maps in `EnhancedTestLauncher` with calls into the registry in `framework/test_configs.py`.
- Remove `sys.path` mutations in anything under the new package.
- Normalize naming and deduplicate `test_*.py` originals vs framework variants; place originals under `MANUAL_TESTS/originals/` or annotate in config registry.
- Centralize platform styling helpers into `style.py` and reuse in tabs.

**Risks and Mitigations**
- Risk: GUI regressions during refactor
  - Mitigation: split components file-for-file first (copy-move), keep public signatures; write a minimal manual smoke run for each tab.
- Risk: Import breakage for dev scripts
  - Mitigation: add thin compatibility imports in `MANUAL_TESTS/` that proxy to the new package; update `PYTHONPATH` only in wrappers if needed.
- Risk: Data migration confusion
  - Mitigation: on first run, prompt where presets/custom tests should live and offer a one-click copy from repo; log the chosen path in the status area.

**Acceptance Criteria (Alpha Packaging)**
- `pip install -e .[dev]` and `econsim-enhanced-tests` launches the same UI as today’s `make enhanced-tests`.
- Adding a new test requires a single edit to `framework/test_configs.py` and optionally a small runner stub—no filename map edits in UI code.
- Presets, bookmarks, and custom tests persist outside the repo by default; repo stays clean after normal use.
- Logs default to an appdata/state directory; `gui_logs/` at repo root is deprecated but accessible via env override.
- CI runs lint/type/smoke tests on the new package; `MANUAL_TESTS/` remains for examples and wrappers only.

**Suggested Timeline**
- 1 day: Phase 0–1 (extract framework) + wiring tests
- 1–2 days: Phase 2 (split launcher) + basic runner
- 0.5 day: Phase 3–4 (registry + remove filename maps)
- 0.5–1 day: Phase 5–6 (data paths + console script + Makefile changes)
- 0.5 day: Phase 7–8 (docs + wrappers + final polish)

**Follow‑ups**
- Explore a headless comparison runner that reuses the same registry for CI perf checks.
- Consider additional optional extras for specialized use cases (e.g., `[research]` for advanced analytics tools, `[education]` for classroom-specific features).

