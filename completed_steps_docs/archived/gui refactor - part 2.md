# GUI Refactor – Part 2 (UI Component Extraction & Launcher Shell)

**Date:** 2025-09-27  
**Scope:** Phase 3 (UI Components) + early Phase 4 prep (public API shell)  
**Depends On:** Part 1 completion (G1–G10 all green)  
**Monolith Source:** `MANUAL_TESTS/enhanced_test_launcher_v2.py`  
**Target Package Root:** `src/econsim/tools/launcher/`

---
## 0. Objectives
1. Decompose monolithic UI into testable, self-contained components: Cards → Gallery → Tabs Container → Main Window shell.
2. Remove direct iteration over legacy `ALL_TEST_CONFIGS` in UI; replace with registry-driven view model preserving ordering determinism.
3. Provide headless smoke test to catch regression in basic window construction & teardown.
4. Establish stable public API (`runner.py:main()` + minimal programmatic entrypoint) for forthcoming console script `econsim-launcher`.
5. Maintain strict determinism & performance neutrality (no extra timers / threads).

---
## 1. Guiding Additions (Building on Part 1 Principles)
8. **Component Isolation:** Each UI component owns only presentation logic; state & business logic remain in extracted modules (registry/comparison/executor).
9. **Explicit Data Flow:** One-directional flow from registry → view model → UI components.
10. **Minimized Qt Coupling in Logic:** Non-Qt pure functions for model building (facilitates headless tests).
11. **Graceful Degradation:** If a component fails to load (unexpected), launcher surfaces error but continues minimal mode.
12. **Headless Safety:** Components must not assume a visible screen (tests run with `QT_QPA_PLATFORM=offscreen`).

---
## 2. Phase 3 Sub-Phases & Exit Gates
| Sub-Phase | Description | Output Artifacts | Gate |
|-----------|-------------|------------------|------|
| 3.1 | Card Model & Component Extraction | `cards.py` + `build_card_models()` | G11 |
| 3.2 | Gallery (Scrollable + Filter/Search future-ready) | `gallery.py` | G12 |
| 3.3 | Tabs Container (Home, Comparison, History) | `tabs/` package | G13 |
| 3.4 | Main Window Slimming | `app_window.py` interim shell | G14 |
| 3.5 | Headless Smoke Test | `test_launcher_smoke.py` | G15 |
| 3.6 | Public Runner API | `runner.py:main()` + doc | G16 |

### New Gates
| Gate | Description | Verification |
|------|-------------|--------------|
| G11 | Card model/build pure & deterministic | Unit test: stable ordering vs legacy snapshot |
| G12 | Gallery component delegates rendering only | Instantiation test + no business logic leakage |
| G13 | Tabs modular (no monolith conditionals) | Test: create tabs; sections present |
| G14 | Main window slim (≤30% LOC reduction vs original core) | Diff metrics / radon / manual review |
| G15 | Headless launcher smoke passes | `QT_QPA_PLATFORM=offscreen pytest -k launcher_smoke` |
| G16 | Public API stable | Import & run `runner.main()` returns 0 / constructs window in headless |

---
## 3. Sequencing Rationale
Order chosen to guarantee each layer can be validated in isolation: card models first (pure) → card widgets (thin) → gallery composition → tab container orchestration → main window slimming. Only after UI stabilized do we expose stable runner API.

---
## 4. Component Design Sketches
### 4.1 Card Model
```
@dataclass
class TestCardModel:
    id: int
    label: str
    mode: str
    file: Path | None
    order: int  # stable ordering value
    meta: dict[str, Any]
```
Pure builder: `build_card_models(registry: TestRegistry) -> list[TestCardModel]` producing list sorted by (id) OR legacy explicit ordering map (if required). Deterministic: iteration over `registry.all()` ordered by key.

### 4.2 Card Widget (Qt)
```
class TestCard(QWidget):
    def __init__(self, model: TestCardModel, comparison: ComparisonController, executor: TestExecutor): ...
```
Responsibilities: render label & metadata, emit signals for actions (launch original/framework/add to comparison). No registry access directly.

### 4.3 Gallery
```
class TestGallery(QWidget):
    def __init__(self, card_models: list[TestCardModel], comparison: ComparisonController, executor: TestExecutor): ...
    def rebuild(self, card_models: list[TestCardModel]) -> None: ...
```
Scroll area + grid or flow layout. Rebuild method pure except widget churn.

### 4.4 Tabs Container
```
class LauncherTabs(QTabWidget):
    def __init__(self, gallery: TestGallery, comparison: ComparisonController, executor: TestExecutor): ...
```
Tabs: (1) Tests (gallery), (2) Comparison (summary + launch button), (3) History (executor.history view). History view is read-only table built dynamically.

### 4.5 Main Window Slim Shell
```
class LauncherWindow(QMainWindow):
    def __init__(self, registry: TestRegistry):
        # builds models, components, sets central widget
```
No business logic beyond composition and connecting signals → executor calls.

---
## 5. Registry-Driven Ordering Replacement
Legacy: multiple loops over `ALL_TEST_CONFIGS.values()` for card creation & status messages.
Replacement Strategy:
1. Build models via `build_card_models(registry)`; ordering by ascending id (stable) OR replicate legacy order mapping if discovered divergent.
2. Provide optional hook for future sorting modes (e.g., alphabetical, tag-based) behind a pure function.
3. Monolith deprecation path: migrate card creation to new gallery; remove raw `ALL_TEST_CONFIGS` iteration; keep adapter only for registry assembly.
4. Document invariants: no filtering in builder; UI handles dynamic filters later.

---
## 6. Headless Smoke Test Strategy
Test file: `tests/unit/launcher/test_launcher_smoke.py`
```
- Set env ECONSIM_HEADLESS_RENDER=1 and QT_QPA_PLATFORM=offscreen.
- Import runner.main(headless=True) OR construct LauncherWindow directly using a lightweight registry fixture.
- Assert window.title contains expected keyword and that comparison/executor objects are wired.
- Close immediately to ensure teardown path clean (no zombie timers beyond simulation timer not used here).
```

Edge Cases: Missing PyQt offscreen plugin → mark test xfail with reason if env not suitable.

---
## 7. Public API Surface (Phase 4 Preview)
`runner.py`
```
def main(argv: list[str] | None = None, headless: bool = False) -> int:
    """Entry point for econsim-launcher.
    - Parses minimal args (e.g., --headless, --list-tests, --json-registry).
    - Initializes QApplication, PlatformStyler, builds registry via adapter, constructs LauncherWindow.
    - If headless and a query flag given (like --list-tests) prints JSON then exits.
    """
```
Console script later in `pyproject.toml`:
```
[project.scripts]
econsim-launcher = "econsim.tools.launcher.runner:main"
```

---
## 8. Risks & Mitigations (Phase 3)
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Qt layout churn performance | Medium | Rebuild only when necessary; reuse models |
| Signal duplication or leaks | Medium | Centralize connections in LauncherWindow |
| Ordering drift vs legacy | Low | Snapshot test for ordered labels |
| Headless flakiness (CI) | Medium | Guard with env detection + short timeout |
| Scope creep into feature redesign | Medium | Keep placeholder styling; isolate to extraction |

---
## 9. Metrics & Targets (Phase 3)
| Metric | Baseline (Monolith) | Target |
|--------|---------------------|--------|
| Launcher core LOC | ~1153 | -30% after window slimming |
| Component average LOC | N/A | <250 per UI file |
| Card model build time | negligible | negligible (<1ms typical) |
| Smoke test runtime | N/A | <1.0s |

---
## 10. Acceptance Summary for Part 2
Part 2 considered complete when Gates G11–G16 all pass, monolith UI creation replaced by new component composition path, and legacy `ALL_TEST_CONFIGS` iteration removed from UI code (remaining only in adapter until Phase 4 registry finalization).

---
## 11. Immediate Action Checklist (Planned Commits)
1. Add placeholders: `cards.py`, `gallery.py`, `tabs/__init__.py`, `runner.py` with docstrings & TODO markers.
2. Implement card model dataclass + `build_card_models` (pure) + unit test snapshot (ordering & model fields).
3. Implement `TestCard` widget (minimal) and gallery container with rebuild.
4. Add `LauncherTabs` and integrated History/Comparison simple panels.
5. Introduce `LauncherWindow` wrapper (slim) and modify monolith to optionally use it (feature flag `ECONSIM_NEW_UI_PART2=1`).
6. Add headless smoke test.
7. Add runner.main + minimal arg parsing + (optional) --list-tests JSON output.
8. Remove direct `ALL_TEST_CONFIGS` iteration from monolith when flag enabled.
9. Update docs & gate table; finalize Part 2.

---
## 12. Appendix: Snapshot Test Pattern
```
expected = [m.label for m in build_card_models(registry)]
# Compare against stored list in tests/data/expected_labels.txt
```
If mismatch: print diff suggestion (maintain explicit reviewer gate on intentional ordering change).

