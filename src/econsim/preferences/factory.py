"""Preference factory & registry (Gate 2).

Central construction point so future agent/grid code depends only on
string identifiers, not concrete class definitions.
"""
from __future__ import annotations
from typing import Dict, Type, List, Any, Mapping

from .base import Preference, PreferenceError
from .cobb_douglas import CobbDouglasPreference
from .perfect_substitutes import PerfectSubstitutesPreference
from .leontief import LeontiefPreference

_REGISTRY: Dict[str, Type[Preference]] = {
    CobbDouglasPreference.TYPE_NAME: CobbDouglasPreference,
    PerfectSubstitutesPreference.TYPE_NAME: PerfectSubstitutesPreference,
    LeontiefPreference.TYPE_NAME: LeontiefPreference,
}


def register_preference(name: str, cls: Type[Preference]) -> None:
    if name in _REGISTRY:
        raise PreferenceError(f"Preference type '{name}' already registered")
    _REGISTRY[name] = cls


def list_preferences() -> List[str]:
    return sorted(_REGISTRY)


class PreferenceFactory:
    @staticmethod
    def create(type_name: str, **params: Any) -> Preference:
        cls = _REGISTRY.get(type_name)
        if cls is None:
            available = ", ".join(list_preferences())
            raise PreferenceError(f"Unknown preference type '{type_name}'. Available: {available}")
        return cls(**params)  # type: ignore[arg-type]

    @staticmethod
    def from_serialized(data: Mapping[str, Any]) -> Preference:
        type_name = data.get("type")
        if not isinstance(type_name, str):
            raise PreferenceError("Serialized preference missing 'type' string")
        cls = _REGISTRY.get(type_name)
        if cls is None:
            available = ", ".join(list_preferences())
            raise PreferenceError(f"Unknown preference type '{type_name}'. Available: {available}")
        return cls.deserialize(data)

    # Future: add validation hooks for versioned serialization formats if schema evolves.


__all__ = [
    "PreferenceFactory",
    "register_preference",
    "list_preferences",
]
