Gate 2 — Flexible Preferences Implementation Plan (Authoritative Copy)

(Preview hook explicitly deferred until grid/agents exist.)

Goal
----
Establish a robust, extensible **Preference Architecture** enabling multiple microeconomic preference types (Cobb‑Douglas, Perfect Substitutes, Leontief) with real‑time parameter adjustment pathway and clean integration path to forthcoming spatial/agent systems (without implementing agents yet). Provide foundations (interfaces, factory, parameter management, validation, test harness) while staying within scope (no full grid/agent simulation logic, no premature visualization hook).

Contract (tiny)
----------------
- Inputs: Existing Gate 1 widget loop; Python 3.11+; planned preference specs.
- Outputs: Preference core modules (`preferences/` package) with: base interface, concrete stubs + at least one full implementation (Cobb‑Douglas), parameter schema + validation, factory/registry, serialization scaffolding, test suite & perf sanity.
- Error modes: Invalid parameter ranges, unregistered type, numerical instability, unexpected perf regression.
- Success criteria: API stable for later agent integration; parameter mutation <100ms; ≥30 FPS still; tests & lint green.

Acceptance Criteria (must pass all)
-----------------------------------
1. Base `Preference` abstract class: `utility(bundle)`, `describe_parameters()`, `update_params(**kwargs)`, `serialize()/deserialize()`.
2. Registry/factory returns configured instances; unknown types raise controlled error listing available types.
3. Validation enforced per preference (e.g., Cobb‑Douglas alpha ∈ (0,1)); invalid updates raise `PreferenceError`.
4. Cobb‑Douglas, Perfect Substitutes, and Leontief all fully implemented (original plan allowed PS & Leontief as stubs; enhancement delivered early).
5. Round‑trip serialization works (create → serialize → deserialize → equivalent utility values for sample bundles).
6. Tests cover creation, mutation, validation errors, serialization symmetry, and utility correctness for implemented preference.
7. (Deferred) Preview hook removed from Gate 2 scope; to be implemented once spatial/agent context exists.
8. Docstrings convey economic meaning & parameter constraints (concise).
9. Quality gates pass (`make lint`, `make type`, `make test`, `make perf` unchanged).
10. Event loop discipline preserved (no threads / blocking loops introduced).

Step-by-Step Plan
------------------
(Executed – see tmp_plans version for historical timing notes.)

Quick Commands
--------------
source vmt-dev/bin/activate
make test
make lint
make type
make perf  # should remain ≥30 FPS

Edge Cases & Notes
------------------
- Zero quantity in Cobb‑Douglas returns 0 utility (documented behavior).
- Negative quantities in any good raise `PreferenceError` across all preference types.
- Parameter update validation prevents silent invalid state (e.g., alpha outside (0,1)).
- Future N-good expansion: revise Bundle alias and implementations; not needed now.
- Avoid premature caching/optimization; current operations are O(1) and trivial cost.

Deferred Items (Out of Gate 2 Scope)
------------------------------------
- Visual preview/color mapping of utility.
- Multi-good generalization.
- Agent decision integration.
- Preference comparison UI / parameter sliders.

Success Metrics Summary
-----------------------
- Functional: Factory + all three (Cobb‑Douglas, Perfect Substitutes, Leontief) operational (MET).
- Quality: 25 unit tests covering utility correctness, validation, serialization round-trips (MET).
- Performance: No measurable FPS drop (baseline ~62 FPS) (MET).
- Extensibility: New preference ≤50 lines including tests (ACHIEVABLE with current design).
- Robustness: Serialization symmetry and parameter mutation safety validated for all three types.

Delta vs Original Plan
----------------------
- Up-scoped: Perfect Substitutes & Leontief moved from planned stubs to full implementations.
- Deferred: Visualization/preview hook explicitly postponed for contextual integration later.
- Added: Comprehensive serialization tests for all preferences (not strictly required initially).

Status
------
Implementation complete (all three preferences fully implemented) with preview hook deferred; ready for formal Gate 2 acceptance review and transition planning toward grid/agent integration.
