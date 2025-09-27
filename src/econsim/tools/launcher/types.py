"""Shared datatypes for launcher modules (Phase 1 scaffold)."""
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
    id: int
    label: str
    mode: str
    file: Path | None
    meta: Dict[str, Any]


@dataclass
class ExecutionResult:
    success: bool
    launched: bool
    errors: List[str]
    command: List[str]


@dataclass
class ExecutionRecord:
    test_ids: List[str]
    timestamp: float
    mode: str
    result: ExecutionResult


@dataclass
class RegistryValidationResult:
    ok: bool
    duplicates: List[str]
    missing: List[str]
