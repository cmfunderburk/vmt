"""Cobb-Douglas preference implementation (Gate 2).

Utility function: U(x, y) = x**alpha * y**(1 - alpha) with 0 < alpha < 1.
Edge handling: if x == 0 or y == 0 => utility 0 (standard convention).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .base import Preference, PreferenceError, PreferenceMeta
from .types import Bundle

_ALPHA_EPS = 1e-9


@dataclass
class _Params:
    alpha: float


class CobbDouglasPreference(Preference):
    TYPE_NAME = "cobb_douglas"

    def __init__(self, alpha: float = 0.5) -> None:
        self._params = _Params(alpha=self._validate_alpha(alpha))
        super().__init__(PreferenceMeta(self.TYPE_NAME, "Cobb-Douglas (x^a * y^(1-a))"))

    # --- Validation ---------------------------------------------------
    @staticmethod
    def _validate_alpha(value: float) -> float:
        # Accept numeric (int/float); rely on float conversion and range check
        try:
            f = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:  # pragma: no cover (defensive)
            raise PreferenceError("alpha must be numeric") from exc
        if not (0.0 < f < 1.0):
            raise PreferenceError("alpha must be in (0,1)")
        return f

    # --- API ----------------------------------------------------------
    def utility(self, bundle: Bundle) -> float:  # type: ignore[override]
        self._ensure_non_negative(bundle)
        x, y = bundle
        if x <= 0.0 or y <= 0.0:
            return 0.0
        a = self._params.alpha
        return (x**a) * (y ** (1.0 - a))

    def describe_parameters(self):  # type: ignore[override]
        return {"alpha": "share parameter in (0,1) controlling x vs y weight"}

    def update_params(self, **params: Any) -> None:  # type: ignore[override]
        if "alpha" in params:
            new_alpha = self._validate_alpha(params["alpha"])
            self._params.alpha = new_alpha
        unknown = set(params) - {"alpha"}
        if unknown:
            raise PreferenceError(f"Unknown parameter(s): {', '.join(sorted(unknown))}")

    def serialize(self) -> dict[str, Any]:  # type: ignore[override]
        return {"type": self.TYPE_NAME, "params": {"alpha": self._params.alpha}}

    @classmethod
    def deserialize(cls, payload: Mapping[str, Any]):  # type: ignore[override]
        params_obj = payload.get("params", {})
        alpha_val: float = 0.5
        if isinstance(params_obj, Mapping):
            # Copy into a plain dict[str, Any] to help type checker
            tmp: dict[str, Any] = dict(params_obj)  # type: ignore[arg-type]
            raw_alpha_any = tmp.get("alpha", 0.5)
            try:
                alpha_val = float(raw_alpha_any)  # type: ignore[arg-type]
            except (TypeError, ValueError):  # pragma: no cover
                alpha_val = 0.5
        return cls(alpha=alpha_val)

    # Convenience property
    @property
    def alpha(self) -> float:
        return self._params.alpha


__all__ = ["CobbDouglasPreference"]
