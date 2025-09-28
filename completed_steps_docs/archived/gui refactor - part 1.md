# GUI Refactor – Part 1 (Hybrid Option C Execution Guide)

**Date:** 2025-09-27  
**Authoring Context:** Launcher modularization (Hybrid strategy – Option C)  
**Scope of This Part:** Phases 1 & 2 (Utilities + Core Business Logic) groundwork, gating criteria, and preparation for UI modularization (Phases 3 & 4).  
**Monolith Source:** `MANUAL_TESTS/enhanced_test_launcher_v2.py` (≈1153 lines)  
**Target Package Root:** `src/econsim/tools/launcher/`  
**Primary Constraints:** Determinism invariants (simulation loop untouched), no new timers/threads, zero behavior regression in existing launcher workflows, performance neutrality (<2% startup delta).

---
## 0. Strategy Overview (Why Hybrid)
| Aspect | Pure Incremental | Big Bang | Hybrid (Chosen) |
|--------|------------------|---------|-----------------|
| Risk Containment | High | Low | High |
| Speed to Foundational Wins | Slow | Fast | Medium-Fast |
| Regression Visibility | Clear | Opaque | Clear |
| Parallelizability | Limited | High (but brittle) | Moderate |
| Early Testability | Strong | Weak | Strong |

Hybrid = deliberate risk ramp: (1) Pure utilities → (2) Business logic → (3) UI components → (4) Coordinator shell.

---
## 1. Guiding Principles
1. **Blast-Radius Minimization:** Only refactor code already *logically isolated*; defer UI rewiring until stable utility/business layers land.  
2. **Stable Interfaces Early:** Introduce docstring-specified public contracts *before* internal rewiring.  
3. **Test-Led Extraction:** Each extracted module gains at least one dedicated unit test file.  
4. **No Behavior Drift:** Maintain feature parity: comparison mode, custom tests, bookmarks, batch runs.  
5. **Explicit Gating:** Each sub-phase has objective acceptance criteria (green tests + measurable invariants).  
6. **Reversible Steps:** Keep monolith authoritative until Phase 2 completion; only then prune duplicated logic.  
7. **No Hidden State:** New modules avoid implicit globals; pass dependencies via constructors.

---
## 2. Phase & Sub-Phase Map (Part 1 Focus Highlighted)
| Phase | Sub-Phase | Description | This Document Scope | Exit Gate |
|-------|-----------|-------------|---------------------|-----------|
| 1 | 1.1 | PlatformStyler extraction | ✅ | Tests + imported by monolith |
| 1 | 1.2 | DataLocationResolver (XDG + migration stubs) | ✅ | Dry-run tests pass |
| 1 | 1.3 | CustomTestDiscovery (pure file parsing) | ✅ | Discovery parity tests |
| 1 | 1.4 | Shared types & result dataclasses | ✅ | Central `types.py` added |
| 2 | 2.1 | TestRegistry (wrap existing config + id map) | ✅ | Registry parity tests |
| 2 | 2.2 | ComparisonController (state logic) | ✅ | Edge-case tests |
| 2 | 2.3 | TestExecutor (abstract launch API) | ✅ | Simulated launch tests |
| 2 | 2.4 | Transitional integration layer (adapters) | ✅ | Monolith switched to modules |
| 3 | 3.x | UI components (cards, gallery, tabs) | ❌ (Next Part) | N/A |
| 4 | 4.x | Slim VMTLauncher & CLI wiring | ❌ | N/A |

---
## 3. Directory Bootstrap (To Be Created in Part 1)
```
src/econsim/tools/launcher/
  __init__.py
  style.py                 # PlatformStyler
  data.py                  # DataLocationResolver
  discovery.py             # CustomTestDiscovery
  types.py                 # Shared dataclasses / Protocols
  registry.py              # TestRegistry
  comparison.py            # ComparisonController
  executor.py              # TestExecutor
  adapters.py              # Transitional glue (Phase 2.4)
  _internal/
    legacy_shims.py        # Temporary import bridges (if needed)
    constants.py           # Non-simulation, launcher-only constants
```
Future (Part 2 / later): `cards.py`, `gallery.py`, `tabs/`, `app.py`, `runner.py`.

---
## 4. Module Contracts (Initial Draft Interfaces)
### 4.1 `style.py`
Responsibilities: UI palette normalization, platform quirks isolation.
```
class PlatformStyler:
    @staticmethod
    def configure_application(app: QApplication) -> None: ...
    @staticmethod
    def base_stylesheet() -> str: ...
    @staticmethod
    def apply_post_init_fixes(app: QApplication) -> None: ...
```
Acceptance: Idempotent, free of side-effects beyond styling, no implicit imports of heavy modules.

### 4.2 `data.py`
```
class DataLocationResolver:
    def __init__(self, app_name: str = "econsim_launcher") -> None: ...
    def config_dir(self) -> Path: ...
    def data_dir(self) -> Path: ...
    def state_dir(self) -> Path: ...
    def legacy_paths(self) -> dict[str, Path]: ...
    def migration_plan(self) -> list["MigrationAction"]: ...  # dry-run structure
    def migrate(self, execute: bool = False) -> "MigrationReport": ...
```
Constraints: Must support dry-run; no writes in constructor.

### 4.3 `discovery.py`
```
class CustomTestDiscovery:
    def __init__(self, tests_dir: Path) -> None
    def discover(self) -> list[CustomTestInfo]
    def parse(self, file_path: Path) -> CustomTestInfo
    def validate(self, file_path: Path) -> bool
```
Edge Cases: Empty file, malformed metadata header, duplicate IDs.

### 4.4 `types.py` (Dataclasses)
```
@dataclass
class CustomTestInfo: id: str; name: str; path: Path; tags: list[str]; summary: str
@dataclass
class TestConfiguration: id: int; label: str; mode: str; file: Path | None; meta: dict[str, Any]
@dataclass
class ExecutionResult: success: bool; launched: bool; errors: list[str]; command: list[str]
@dataclass
class ExecutionRecord: test_ids: list[str]; timestamp: float; mode: str; result: ExecutionResult
@dataclass
class RegistryValidationResult: ok: bool; duplicates: list[str]; missing: list[str]
```

### 4.5 `registry.py`
```
class TestRegistry:
    def __init__(self, builtin_source: Callable[[], list[TestConfiguration]], custom_source: Callable[[], list[TestConfiguration]] | None = None): ...
    def all(self) -> dict[int, TestConfiguration]: ...
    def by_id(self, test_id: int) -> TestConfiguration: ...
    def by_label(self, label: str) -> TestConfiguration | None: ...
    def validate(self) -> RegistryValidationResult: ...
```

### 4.6 `comparison.py`
```
class ComparisonController:
    def __init__(self, max_selections: int = 4): ...
    def add(self, label: str) -> bool: ...
    def remove(self, label: str) -> bool: ...
    def clear(self) -> None: ...
    def selected(self) -> list[str]: ...
    def can_launch(self) -> bool: ...
```
Edge Cases: Adding duplicates, over capacity, removing absent.

### 4.7 `executor.py`
```
class TestExecutor:
    def __init__(self, registry: TestRegistry, launcher_script: Path, python_cmd: Sequence[str] = (sys.executable,))
    def launch_original(self, label: str) -> ExecutionResult
    def launch_framework(self, label: str) -> ExecutionResult
    def launch_comparison(self, labels: list[str]) -> ExecutionResult
    def history(self) -> list[ExecutionRecord]
```
Rules: No direct GUI calls; return structured results only.

### 4.8 `adapters.py`
Transitional bridging layer: functions that adapt legacy monolith calls to new API while refactor in progress.
```
def load_registry_from_monolith() -> TestRegistry: ...
```
Removed after Phase 2 finalization.

---
## 5. Detailed Step-by-Step Execution (Part 1)
### Step 1: Scaffold Package Structure
- Create directory tree (see §3) with placeholder files + module docstrings.
- Add `__all__` exports in `__init__.py` for extracted modules.
- Commit (Refactor Scaffold) – no logic yet.

### Step 2: Extract Platform Styling (1.1)
- Copy styling logic block (lines ~901–1078 of monolith) into `style.py` while:
  - Replace helper lambdas with pure functions (naming clarity).
  - Remove any side-effect code that does not strictly relate to styling.
- Add unit test: `tests/unit/launcher/test_style.py` verifying stylesheet non-empty + idempotency of application.
- Modify monolith: replace in-place styling function body with import & delegation.
- Gate: All unit tests still pass.

### Step 3: Implement DataLocationResolver (1.2)
- Define XDG resolution (Linux) + placeholder for Windows/macOS (document TODO if not implemented yet).
- Add dry-run migration logic comparing legacy paths to new layout.
- Unit test: `tests/unit/launcher/test_data_locations.py` covering path shapes & dry-run baseline (no exceptions).
- (No monolith integration yet—safe staging.)

### Step 4: Implement CustomTestDiscovery (1.3)
- Identify current parsing logic in monolith (custom tests widget section).
- Extract only pure parsing & metadata extraction (no widget references).
- Add test fixtures in `tests/fixtures/custom_tests/` with: valid file, malformed file, duplicate id scenario.
- Unit test ensures parity: discovered count matches current baseline (establish reference snapshot via initial run).
- Gate: Discovery stable & deterministic ordering (sort by filename).

### Step 5: Introduce Shared Types (1.4)
- Create dataclasses in `types.py`; avoid importing PyQt types.
- Replace temporary ad-hoc dict structures in new modules with these dataclasses.
- Backfill minimal unit test ensuring `asdict()` round-trip integrity.

### Step 6: Build Registry (2.1)
- Extract existing builtin test configuration list generation (currently mapping IDs to file paths in monolith).
- Provide injection boundary: `builtin_source()` returns canonical list.
- Implement duplicate detection (ID + label uniqueness).
- Unit test validates: count > 0, no duplicates, retrieval API works.

### Step 7: ComparisonController (2.2)
- Implement capacity, duplicate, and validation logic.
- Unit tests: add, overfill, remove absent, clear.
- Keep independent (no registry coupling yet—string labels only).

### Step 8: TestExecutor (2.3)
- Abstract command array formation (no subprocess invocation yet OR mockable strategy).
- Provide internal `_build_command(label, mode)` returning list[str].
- Integrate simple history append.
- Unit test with monkeypatch/mocking to ensure command formation matches current invocation style in monolith.

### Step 9: Transitional Integration (2.4)
- Add `adapters.py` to assemble `TestRegistry` using existing monolith data feed.
- Modify monolith incrementally:
  1. Import `TestRegistry`, `ComparisonController`, `TestExecutor`.
  2. Replace internal dicts & lists with calls to these objects (keep UI event handlers unchanged beyond delegation).
  3. Keep legacy helper functions until UI phases.
- Add integration test (if feasible) launching the monolith in headless mode with env flag `ECONSIM_HEADLESS_RENDER=1` to assert no exceptions (optional if current infra supports).

### Step 10: Cleanup & Gating Review
- Ensure no cyclic imports (run `ruff check --select F401,F403,F405,F821`).
- Add documentation section to refactor plan summarizing newly added modules (append to existing breakdown plan).
- Mark Part 1 completion once all gates (below) pass.

---
## 6. Acceptance Gates (Part 1)
| Gate | Description | Verification |
|------|-------------|--------------|
| G1 | Styling extraction functional | Monolith starts + visual smoke | Manual + test_style.py |
| G2 | Data resolver stable | Unit tests pass | test_data_locations.py |
| G3 | Discovery parity | Baseline & post-extraction counts equal | test_discovery.py |
| G4 | Types standardized | No remaining launcher-only ad-hoc dict parsing | grep + code review |
| G5 | Registry validated | test_registry.py (duplicate detection) | CI green |
| G6 | Comparison logic isolated | test_comparison.py | CI green |
| G7 | Executor commands stable | test_executor.py (command arrays) | CI green |
| G8 | Monolith delegating to modules | Manual path diff (lines replaced) | Review |
| G9 | No performance regression | perf stub (<2% startup delta) | `scripts/perf_stub.py` |
| G10 | Docs updated | Added Part 1 summary in planning docs | Commit diff |

Failure Policy: If any gate fails, revert that module integration (not previous phases) and patch.

---
## 7. Risk Matrix (Part 1)
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Hidden coupling in styling | Medium | Low | Keep original function until parity confirmed |
| Discovery order drift | Medium | Medium | Explicit filename sort & test snapshot |
| Registry duplicate oversight | Low | High | Validation test + CI fail-fast |
| Executor path assumptions | Medium | Medium | Mock-driven tests + command diff logs |
| Monolith partial integration break | Medium | Medium | Integrate modules sequentially w/ checkpoints |

---
## 8. Metrics & Tracking
| Metric | Baseline Source | Target Delta |
|--------|-----------------|-------------|
| Monolith LOC | wc -l before Phase 1 | -20% by end Phase 2 |
| Avg Function Length (launcher) | `radon` report | -30% by end Phase 2 |
| New Module Coverage | `coverage.xml` | ≥80% per new module |
| Startup Time | perf stub 2s sample | ≤ +2% |

---
## 9. Follow-On Prep (For Part 2 Document)
Will define UI component extraction sequencing: cards → gallery → tabs → coordinator replacement → CLI console script (`econsim-launcher`).

---
## 13. Progress Log (Incremental Updates)
### 2025-09-27 (Step 2 Complete)
- Extracted platform styling block into `src/econsim/tools/launcher/style.py` implementing `PlatformStyler` facade.
- Removed legacy inline styling helper from monolith and delegated via `PlatformStyler.configure_application()`.
- Added unit test `tests/unit/launcher/test_style.py` (verifies non-empty base stylesheet + idempotent application) – passes.
- Full test suite post-extraction: 210 passed, 7 skipped, 2 xpassed (expected), no new failures introduced.
- Gate G1 satisfied.
- Next Focus: Step 3 (DataLocationResolver) – implement XDG path resolution + dry-run migration tests before monolith integration.

### 2025-09-27 (Step 3 Complete)
- Implemented `DataLocationResolver` in `data.py` with XDG resolution (Linux/POSIX) and deterministic HOME fallbacks for macOS/Windows (documented TODOs for specialization).
- Added structured migration planning (`migration_plan`) returning `MigrationAction` list and non-destructive `migrate(execute=...)` (creates destination dirs only when execute=True).
- Added unit test `tests/unit/launcher/test_data_locations.py` (path resolution, dry-run plan, execute idempotency) – passes.
- Full suite after addition: 212 passed, 7 skipped, 2 xpassed (expected), no regressions; Gate G2 satisfied.
- Next Focus: Step 4 (CustomTestDiscovery) – extract pure metadata parsing & add fixture-driven tests.

### 2025-09-27 (Step 4 Complete)
- Implemented `CustomTestDiscovery` with deterministic filename ordering and metadata parsing (name, created date, grid, agents, density, preference mix) independent of UI.
- Added fixtures: `valid_case.py`, `malformed_case.py`, `duplicate_id_case.py` under `tests/fixtures/custom_tests/`.
- Added unit test `tests/unit/launcher/test_discovery.py` validating ordering, parsing correctness, malformed fallback, and tolerance of duplicate IDs.
- Full suite: 214 passed, 7 skipped, 2 xpassed (expected); Gate G3 satisfied.
- Next Focus: Step 5 (Shared types dataclasses) – introduce and test serialization round-trip before registry extraction.

### 2025-09-27 (Step 5 Complete)
- Expanded `types.py` with docstring-rich dataclasses (`TestConfiguration`, `ExecutionResult`, `ExecutionRecord`, `RegistryValidationResult`) plus helper methods (`to_dict`, `failed`).
- Added `tests/unit/launcher/test_types.py` covering asdict round-trip, helper semantics, and basic integrity checks.
- Full suite now: 218 passed, 7 skipped, 2 xpassed (expected); Gate G4 (types standardized) partially satisfied pending later grep review for remaining ad-hoc dicts (none in new modules so far).
- Next Focus: Step 6 (TestRegistry) – extract builtin config list, implement duplicate detection, add registry tests.

Dependencies to Clarify Before Part 2:
- Confirm final naming for console script (tentatively `econsim-launcher`).
- Decide whether `TestExecutor` handles actual subprocess spawn vs delegated runner object.
- Determine feasibility of headless integration test harness for launcher (PyQt6 + offscreen).

---
## 10. Immediate Action Checklist (Actionable Commits Sequence)
1. Commit 1: Scaffold package files (empty contracts + docstrings).  
2. Commit 2: Styling extraction + tests.  
3. Commit 3: Data resolver + tests.  
4. Commit 4: Discovery module + fixtures + tests.  
5. Commit 5: Types + registry + tests.  
6. Commit 6: Comparison + executor + tests.  
7. Commit 7: Monolith integration (delegation) + adapter layer.  
8. Commit 8: Perf + doc updates + finalize Part 1 gating tick list.  

---
## 11. Completion Definition (Exit Part 1)
Part 1 is COMPLETE when: All gates G1–G10 pass, monolith delegates to extracted modules for styling, registry, discovery, comparison, and command construction; no functional regressions observed; documentation updated; metrics collected.

---
## 12. Appendix: Suggested Test File Layout
```
tests/unit/launcher/
  test_style.py
  test_data_locations.py
  test_discovery.py
  test_types.py
  test_registry.py
  test_comparison.py
  test_executor.py
```
Fixtures: `tests/fixtures/custom_tests/{valid_case.py, malformed_case.py, duplicate_id_case.py}`

---
**Next (Part 2):** Draft UI component extraction plan (cards/gallery/tabs) + incremental visual validation strategy.
**See Also:** `gui refactor - part 2.md` (Phase 3 UI extraction & runner API plan).

### 2025-09-27 (Step 9 Integration & Perf Validation)
- Implemented transitional integration (Step 9 / Phase 2.4): added `adapters.py` producing a `TestRegistry` from legacy `ALL_TEST_CONFIGS`.
- Monolith (`enhanced_test_launcher_v2.py`) now delegates: comparison management via `ComparisonController`, command construction & history via `TestExecutor`, and registry access through adapter-generated registry (legacy list still used ONLY for card ordering during transition).
- Resolved regression where launching a framework test reopened the launcher (root cause: executor command pointed at launcher script); fixed by spawning original test scripts directly while still recording executor history.
- Added adapter integration test validating transformed registry (> baseline tests count, no duplicates).
- Grep audit: No stray anonymous ad-hoc dicts for launcher logic beyond intentional legacy `ALL_TEST_CONFIGS` iteration (acceptable until Phase 3 UI extraction). Gate G4 final audit satisfied.
- Performance (Gate G9): Ran `scripts/perf_stub.py --mode widget --duration 2 --json` post-integration. Result: avg_fps=62.4804 vs prior new GUI baseline 62.4953 (delta -0.024%), well within ≤2% threshold. Startup/render loop unaffected (single QTimer path preserved). Gate G9 satisfied.
- Gates Status Update: G8 (delegation) satisfied; G9 (perf neutrality) satisfied.
- Next Actions (Step 10 / Gates G9–G10 wrap): finalize documentation updates (this entry), optional minor lint sweep, and declare Part 1 completion once merged.

### Gate Summary After Step 9
| Gate | Status | Notes |
|------|--------|-------|
| G1 | ✅ | Styling extracted & tested |
| G2 | ✅ | Data resolver tests green |
| G3 | ✅ | Discovery deterministic |
| G4 | ✅ | Types standardized; audit done |
| G5 | ✅ | Registry duplicate detection |
| G6 | ✅ | ComparisonController tests |
| G7 | ✅ | Executor command tests |
| G8 | ✅ | Monolith delegates modules |
| G9 | ✅ | Perf delta -0.024% (<2%) |
| G10 | ⏳ | Final doc consolidation (in progress) |

### Pending for Part 1 Completion
1. Merge this updated plan (satisfies G10 once committed).
2. (Optional) Add a brief README snippet referencing new launcher modules (defer if Part 2 doc will subsume).
3. Tag follow-up tasks for Phase 3 (UI extraction) in new Part 2 guide.

No functional regressions observed; deterministic behavior retained; performance stable.
