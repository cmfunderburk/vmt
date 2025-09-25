"""Overlay state container (Phase A fast-path).

Lightweight dataclass holding toggle flags consumed by the embedded
pygame widget during paint/update. Kept separate to decouple future
UI panels from widget internal attributes.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OverlayState:
    # All options default True per updated UI requirement (user can disable)
    show_grid: bool = True
    show_agent_ids: bool = True
    show_target_arrow: bool = True
    show_home_labels: bool = True
    show_trade_lines: bool = True  # Show lines connecting trading partners

__all__ = ["OverlayState"]
