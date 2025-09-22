# Preferences Module

This package implements the Gate 2 preference architecture: a minimal, validated utility layer for two-good bundles.

## Core Principles
- Keep computation pure & O(1).
- Validation up front: invalid params or negative quantities raise `PreferenceError`.
- Serialization is simple dict form; no versioning yet (add key when schema evolves).
- Factory decouples callers from concrete classes.

## Adding a New Preference Type
1. Create a new file (e.g., `quasi_linear.py`).
2. Implement a subclass of `Preference` with:
   - Class attribute `TYPE_NAME: str`.
   - `__init__(...)` capturing parameters & calling validation helpers.
   - `utility(bundle)` returning a float (no mutation).
   - `describe_parameters()` returning brief constraints.
   - `update_params(**kwargs)` performing validation before mutation.
   - `serialize()` returning `{ 'type': TYPE_NAME, 'params': {...} }` (mirror existing patterns).
   - `@classmethod deserialize(cls, data)` reconstructing safely.
3. Add to `_REGISTRY` in `factory.py` (or call `register_preference`).
4. Add unit tests:
   - Parameter validation (invalid values raise `PreferenceError`).
   - Utility correctness for a few canonical bundles.
   - Round-trip serialization test.
5. Run:
```bash
make test
make lint
make type
```

## Current Implementations
| Type | File | Notes |
|------|------|-------|
| Cobb-Douglas | `cobb_douglas.py` | alpha in (0,1) enforced |
| Perfect Substitutes | `perfect_substitutes.py` | Positive coefficients required |
| Leontief | `leontief.py` | Min-based fixed proportions |

## Deferred (Future Gates)
- Price/budget-based optimization or demand derivations.
- N-good generalization.
- Analytical marginal utilities / MRS helpers.

Keep additions small; avoid anticipatory parameters until agents & grid require them.
