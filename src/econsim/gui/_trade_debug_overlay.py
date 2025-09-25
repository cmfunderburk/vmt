"""Trade draft debug overlay helper (Gate Bilateral1 Phase 2).

Pure rendering adapter; reads simulation.trade_intents (if present) and draws up to N
lines of intent summary. Feature-flag gated by `ECONSIM_TRADE_DRAFT=1` and presence
of intents. No state mutation.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
import os
import pygame

@runtime_checkable
class _SurfaceLike(Protocol):  # minimal protocol for blit
    def blit(self, source: Any, dest: Any) -> Any: ...  # pragma: no cover

@runtime_checkable
class _FontLike(Protocol):  # minimal font protocol
    def render(self, text: str, antialias: bool, color: Any) -> Any: ...  # pragma: no cover

MAX_LINES = 3


def render_trade_debug(surface: _SurfaceLike, font: _FontLike, simulation: Any, *, x_offset: int = 4, y_offset: int = 4) -> None:
    """Render up to MAX_LINES trade intents for debug.

    Defensive: verifies feature flag, presence of intents, and basic protocol conformance.
    Swallows exceptions (non-critical overlay path).
    """
    if os.environ.get("ECONSIM_TRADE_DRAFT") != "1":
        return
    intents = getattr(simulation, "trade_intents", None)
    if not intents:
        return
    # Protocol runtime checks (best-effort; skip if fails to avoid overhead exceptions)
    if not isinstance(surface, pygame.Surface):  # common case fast-path
        if not isinstance(surface, _SurfaceLike):  # type: ignore[arg-type]
            return
    try:
        for idx, intent in enumerate(intents[:MAX_LINES]):
            seller_id = getattr(intent, "seller_id", None)
            buyer_id = getattr(intent, "buyer_id", None)
            give_type = getattr(intent, "give_type", "?")
            take_type = getattr(intent, "take_type", "?")
            quantity = getattr(intent, "quantity", "?")
            if seller_id is None or buyer_id is None:
                continue
            line = f"T{idx}: A{seller_id}->{buyer_id} {give_type}->{take_type} q={quantity}"
            txt = font.render(line, True, (255, 255, 210))
            shadow = font.render(line, True, (0, 0, 0))
            surface.blit(shadow, (x_offset + 1, y_offset + idx * (txt.get_height() + 2) + 1))
            surface.blit(txt, (x_offset, y_offset + idx * (txt.get_height() + 2)))
    except Exception:  # pragma: no cover - purely defensive
        return


__all__ = ["render_trade_debug"]
