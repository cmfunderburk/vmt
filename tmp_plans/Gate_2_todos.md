Gate 2 — Flexible Preferences Implementation Plan

Goal
----
Establish a robust, extensible **Preference Architecture** enabling multiple microeconomic preference types (Cobb‑Douglas, Perfect Substitutes, Leontief) with real‑time parameter adjustment and clean integration path to forthcoming spatial/agent systems (without implementing agents yet). Provide foundations (interfaces, factory, parameter management, validation, test harness) while staying within current scope (no full grid/agent simulation logic).

Contract (tiny)
----------------
- Inputs: Existing Gate 1 widget loop; Python 3.11+; planned preference specifications.
- Outputs: Preference core modules (`preferences/` package) with: base interface, concrete stubs + at least one full implementation (start with Cobb‑Douglas), parameter schema + validation, factory/registry, serialization scaffolding, test suite & perf sanity.
- Error modes: Invalid parameter ranges, unregistered preference type, numerical instability, performance regressions in widget loop if integrated preview is added.
- Success criteria: API stable for later agent integration; real-time parameter mutation (<100ms apply) reflected in a lightweight demo visualization hook; ≥30 FPS maintained; full test & lint gates green.

Acceptance Criteria (must pass all)
-----------------------------------
1. Base `Preference` abstract class defines standard methods: `utility(bundle)`, `describe_parameters()`, `update_params(**kwargs)`, `serialize()/deserialize()`.
2. Registry/factory: `PreferenceFactory.create(type_name, **params)` returns configured instance; unknown type raises controlled error.
3. Parameter validation: Each preference enforces domain constraints (e.g., Cobb‑Douglas alpha ∈ (0,1)). Invalid updates raise `ValueError` with clear message.
4. At least one fully implemented preference (Cobb‑Douglas) with correct analytical utility for 2-good bundle; others may start as structured stubs with TODO markers unless time permits.
5. Round‑trip serialization (dict) works for implemented preferences (create → serialize → deserialize → equivalent behavior).
6. Unit tests cover: factory creation, parameter mutation, validation errors, serialization symmetry, basic utility correctness.
7. (Deferred) Preview hook: Will be implemented post grid/agent introduction so visualization can reflect meaningful state (removed from Gate 2 required scope).
8. Documentation comments (module & class docstrings) explain economic meaning & parameter constraints (concise, non‑tutorial).
9. All quality gates pass: `make lint`, `make type` (mypy clean for new modules), `make test` (new tests included), `make perf` unaffected.
10. No introduction of threading or long blocking loops; event loop discipline preserved.

Step-by-Step Plan
------------------
1) Directory & Skeleton (0.5h)
   - Create `src/econsim/preferences/` with `__init__.py`, `base.py`, `factory.py`, `cobb_douglas.py`, `perfect_substitutes.py` (stub), `leontief.py` (stub), `types.py` (type aliases / Protocols if needed).
2) Define Base Interface (0.5h)
   - Abstract base class or `Protocol` + minimal dataclass for common metadata.
   - Decide on bundle representation (tuple[float,float] for 2-good initial scope) with note for future generalization.
3) Implement Cobb‑Douglas (1h)
   - Parameters: alpha in (0,1); goods bundle (x,y) -> utility = x**alpha * y**(1-alpha).
   - Add numerical guards for zero/near-zero (define behavior for x=0 or y=0).
4) Stubs for PS & Leontief (0.5h)
   - Each returns placeholder utility (raise NotImplementedError if used directly) with defined parameter schema.
5) Factory & Registry (0.5h)
   - Map string keys to classes; provide list/enumeration function for UI later.
6) Validation & Errors (0.5h)
   - Central helper for range checking; consistent error messages.
7) Serialization (0.5h)
   - `to_dict()/from_dict()` or `serialize()/deserialize()` returning canonical dict: `{type, params}`.
8) Tests (1.5h)
   - `tests/unit/test_preferences_cobb_douglas.py`: creation, utility correctness, parameter update, invalid alpha.
   - `tests/unit/test_preferences_factory.py`: factory success/failure, registry listing.
   - `tests/unit/test_preferences_serialize.py`: round-trip equivalence.
9) Optional Widget Preview Hook (0.5h)
   - Tiny function modifying rectangle color intensity based on utility of a sample bundle; guard with feature flag/env var.
10) Type & Lint Integration (0.25h)
   - Ensure mypy strategy (use `Protocol` or ABC) and no stray `Any`.
11) Performance Sanity (0.25h)
   - Run `make perf` with preview disabled/enabled; record FPS delta (<5% acceptable).
12) Polish & Docs (0.5h)
   - Docstrings & short README section addition stub (future).
13) Final Review (0.25h)
   - Cross-check acceptance list; open follow-up TODOs for Gate 3 (e.g., multi-good generalization, agent integration hooks).

Quick Commands
--------------
# (Same environment as Gate 1)
source vmt-dev/bin/activate

# Run tests (after adding new ones)
make test

# Lint & type
make lint
make type

# Perf (ensure still near baseline)
make perf  # should remain ≥30 FPS

Testing
-------
- Golden Cobb‑Douglas utility examples (alpha=0.5, bundle (4,9) => 4**0.5 * 9**0.5 = 6).
- Parameter mutation: update alpha from 0.3→0.6 preserves other params.
- Validation: alpha=0, alpha=1, alpha=-0.1 raise ValueError.
- Serialization: instance → dict → instance; utilities match for sample bundles.
- Factory: unknown key 'logit' raises ValueError with available types listed.
- Preview hook (if enabled) does not drop FPS <30 in 2s perf run; otherwise skip test gracefully if env flag not set.

Edge Cases
----------
- alpha extremely close to 0 or 1 (use epsilon clamp?).
- bundle containing zeros (utility = 0 for Cobb‑Douglas if any good is 0; document).
- Very large bundle values risk float overflow (document: not normalized yet; future scaling).
- Serialization dict missing param: raise ValueError with field list.
- Repeated parameter update with no change should not alter internal cached metadata (if any) nor raise.

Notes
-----
- Keep base interface narrow; expand only when integrating agents/grid.
- Avoid premature generalization to N goods—document extension point.
- Do not wire into a complex GUI panel yet; a minimal preview hook suffices.
- Maintain Gate 1 performance discipline; preference calculations are trivial vs render cost—avoid per-frame heap churn.
- Future (Gate 3+) placeholder TODOs should be clearly marked and not executed.

Planned Follow-Ups (post Gate 2)
--------------------------------
- Multi-good generalization (list-based bundles)
- Preference comparison utilities / explanatory text generator
- Integration with agent decision loop
- Parameter UI controls & live editing

Success Metrics Summary
-----------------------
- Functional: Factory + 1 implemented preference (Cobb‑Douglas) fully operational.
- Quality: 100% test coverage of implemented logic paths (excluding deliberate stubs), zero lint errors, mypy clean.
- Performance: No measurable (>5%) FPS drop with preview disabled; <10% drop with preview enabled.
- Extensibility: Adding new preference type ≤50 lines including tests.
