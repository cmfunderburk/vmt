"""Shared dataclasses for launcher modules (Step 5 implementation).

These dataclasses form the stable, serialization‑friendly contracts between
non‑UI launcher components. They intentionally avoid importing PyQt types to
keep them lightweight and broadly reusable (e.g., for headless tests or
future CLI APIs).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Dict


@dataclass
class CustomTestInfo:
    id: str
    name: str
    path: Path
    tags: List[str]
    summary: str


@dataclass
class TestConfiguration:
    """Canonical definition of a test configuration entry.

    Fields:
        id: Stable numeric identifier.
        label: Human readable name (unique within registry domain).
        mode: Launch mode identifier (e.g., 'original', 'framework').
        file: Optional path to underlying script (None for builtins).
        meta: Arbitrary metadata map (JSON‑serializable preferred).
    """
    id: int
    label: str
    mode: str
    file: Path | None
    meta: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "mode": self.mode,
            "file": str(self.file) if self.file else None,
            "meta": self.meta,
        }


@dataclass
class ExecutionResult:
    """Structured outcome of a launch attempt."""
    success: bool
    launched: bool
    errors: List[str]
    command: List[str]

    def failed(self) -> bool:
        return not self.success


@dataclass
class ExecutionRecord:
    """Historical record entry for executed (or attempted) launches."""
    test_ids: List[str]
    timestamp: float
    mode: str
    result: ExecutionResult


@dataclass
class RegistryValidationResult:
    """Aggregate result from registry self‑validation."""
    ok: bool
    duplicates: List[str]
    missing: List[str]
