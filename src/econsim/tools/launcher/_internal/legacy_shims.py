"""Temporary shim helpers for referencing legacy structures during extraction.

This file should shrink over time and be deleted once the monolith is retired.
"""

from typing import Any


def not_implemented_placeholder(*_args: Any, **_kwargs: Any):  # pragma: no cover - transitional
    raise NotImplementedError("Legacy shim not wired yet during Phase 1 scaffold")
