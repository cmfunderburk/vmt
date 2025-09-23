"""Overlay state container (Phase A fast-path).

Lightweight dataclass holding toggle flags consumed by the embedded
pygame widget during paint/update. Kept separate to decouple future
UI panels from widget internal attributes.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OverlayState:
    show_grid: bool = False
    show_agent_ids: bool = False
    show_target_arrow: bool = False

__all__ = ["OverlayState"]
