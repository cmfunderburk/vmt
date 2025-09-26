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

---

## File Inventory & API Overview

### `base.py`
- `PreferenceError`: Exception for validation issues.
- Abstract base `Preference`:
   - `utility(bundle)`: Must return float utility for 2-good bundle (tuple or mapping).
   - `describe_parameters()`: Short human-readable param description.
   - `update_params(**kwargs)`: Validated in-place parameter update.
   - `serialize()` / `deserialize(data)`: Round-trip contract preserving type + params.

### `cobb_douglas.py`
- `CobbDouglasPreference(alpha: float)`: Utility U = x^alpha * y^(1-alpha). Validates 0 < alpha < 1.
   - `utility(bundle)`: Accepts tuple/list/mapping; negative values disallowed.
   - `update_params(alpha=...)`: Revalidates domain.
   - `TYPE_NAME = "cobb_douglas"`.

### `perfect_substitutes.py`
- `PerfectSubstitutesPreference(a: float, b: float)`: Utility U = a*x + b*y with positive coefficients.
   - `utility(bundle)`: Linear; rejects negative goods.
   - `update_params(a=..., b=...)`: Requires both > 0.
   - `TYPE_NAME = "perfect_substitutes"`.

### `leontief.py`
- `LeontiefPreference(a: float, b: float)`: Utility U = min(x/a, y/b) for fixed proportions (a,b>0).
   - `utility(bundle)`: Computes limiting ratio.
   - `update_params(a=..., b=...)` with validation.
   - `TYPE_NAME = "leontief"`.

### `helpers.py`
- Validation helpers: e.g., `require_positive(name, value)`, `require_unit_interval(name,value)` (exact function names may vary) centralize precondition checks used by preferences.
- Bundle normalization helper to unify tuple/list/dict into (x,y) numeric form.

### `factory.py`
- Registry `_REGISTRY: dict[str, Type[Preference]]` mapping `TYPE_NAME`→class.
- `register_preference(cls)`: Extensible plugin hook.
- `build_preference(type_name, **params)`: Construct instance with validation.
- `deserialize(data)`: Rehydrate based on embedded `type` key.

### `types.py`
- Type aliases / Protocols used across preferences and callers (e.g., `BundleLike = Union[Tuple[float,float], Mapping[str,float]]`).

### `__init__.py`
- Re-exports canonical preferences & factory helpers for convenient import paths.

## Usage Patterns
Typical construction via factory:
```python
from econsim.preferences.factory import build_preference
pref = build_preference('cobb_douglas', alpha=0.6)
u = pref.utility((4,3))
```

Serialization round-trip:
```python
data = pref.serialize()
restored = build_preference(data['type'], **data['params'])
```

## Refactor Opportunities
- Introduce marginal utility helpers (MU_x, MU_y) for trading layer accuracy.
- Add Quasi-linear or CES preference types behind feature flag with perf tests.
- Generalize to N goods (keep 2-good specialized fast path for current simulation).
