"""Preference architecture package (Gate 2 foundation).

Contains base interfaces, concrete preference implementations, and a
factory/registry for constructing preference objects by name.

Current implemented preference:
- CobbDouglasPreference (utility = x**alpha * y**(1-alpha))

Stubs:
- PerfectSubstitutesPreference (planned)
- LeontiefPreference (planned)

Design Notes:
- Keep bundle representation minimal (tuple[float, float]) for Gate 2.
- Future expansion to N goods will introduce a sequence-based bundle type.
"""
from .types import Bundle
from .base import Preference, PreferenceError
from .cobb_douglas import CobbDouglasPreference
from .perfect_substitutes import PerfectSubstitutesPreference
from .leontief import LeontiefPreference
from .factory import PreferenceFactory, register_preference, list_preferences

__all__ = [
    "Bundle",
    "Preference",
    "CobbDouglasPreference",
    "PerfectSubstitutesPreference",
    "LeontiefPreference",
    "PreferenceFactory",
    "register_preference",
    "list_preferences",
    "PreferenceError",
]
