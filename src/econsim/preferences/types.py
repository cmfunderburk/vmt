"""Type aliases and lightweight protocol hints for preferences (Gate 2).

Bundle is a pair of non-negative floats representing quantities of two goods.
Future: generalize to Sequence[float] for N goods.
"""
from __future__ import annotations
from typing import Tuple

Bundle = Tuple[float, float]

__all__ = ["Bundle"]
