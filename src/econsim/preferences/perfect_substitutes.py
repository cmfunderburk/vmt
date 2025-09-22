"""Perfect Substitutes preference stub (Gate 2).

Planned utility (future): U(x,y) = a*x + b*y with a,b > 0.
Current Gate 2 scope: parameter schema + NotImplemented utility to keep
focus on core architecture until at least one full implementation is stable.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Mapping

from .types import Bundle
from .base import Preference, PreferenceMeta, PreferenceError


@dataclass
class _Params:
    a: float
    b: float


class PerfectSubstitutesPreference(Preference):
    TYPE_NAME = "perfect_substitutes"

    def __init__(self, a: float = 1.0, b: float = 1.0) -> None:
        self._params = _Params(a=self._validate_coeff(a), b=self._validate_coeff(b))
        super().__init__(PreferenceMeta(self.TYPE_NAME, "Perfect Substitutes (a*x + b*y)"))

    @staticmethod
    def _validate_coeff(value: float) -> float:
        try:
            f = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):  # pragma: no cover
            raise PreferenceError("coefficient must be numeric")
        if f <= 0:
            raise PreferenceError("coefficient must be > 0")
        return f

    def utility(self, bundle: Bundle) -> float:  # type: ignore[override]
        self._ensure_non_negative(bundle)
        x, y = bundle
        # U = a*x + b*y
        return (self._params.a * x) + (self._params.b * y)

    def describe_parameters(self):  # type: ignore[override]
        return {"a": ">0 weight for good x", "b": ">0 weight for good y"}

    def update_params(self, **params: Any) -> None:  # type: ignore[override]
        updated = False
        if "a" in params:
            self._params.a = self._validate_coeff(params["a"])
            updated = True
        if "b" in params:
            self._params.b = self._validate_coeff(params["b"])
            updated = True
        unknown = set(params) - {"a", "b"}
        if unknown:
            raise PreferenceError(f"Unknown parameter(s): {', '.join(sorted(unknown))}")
        if not updated and params:
            raise PreferenceError("No valid parameters provided")

    def serialize(self) -> Dict[str, Any]:  # type: ignore[override]
        return {"type": self.TYPE_NAME, "params": {"a": self._params.a, "b": self._params.b}}

    @classmethod
    def deserialize(cls, payload: Mapping[str, Any]):  # type: ignore[override]
        params_obj = payload.get("params", {})
        a_val: float = 1.0
        b_val: float = 1.0
        if isinstance(params_obj, Mapping):
            try:
                a_val = float(params_obj.get("a", 1.0))  # type: ignore[arg-type]
                b_val = float(params_obj.get("b", 1.0))  # type: ignore[arg-type]
            except (TypeError, ValueError):  # pragma: no cover
                a_val, b_val = 1.0, 1.0
        return cls(a=a_val, b=b_val)


__all__ = ["PerfectSubstitutesPreference"]
