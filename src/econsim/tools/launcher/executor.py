"""Test execution command builder (Phase 1 scaffold)."""
from __future__ import annotations

import time
import sys
from typing import Sequence, Any

from .types import ExecutionResult, ExecutionRecord
from .registry import TestRegistry


class TestExecutor:
    def __init__(self, registry: TestRegistry, launcher_script: Any, python_cmd: Sequence[str] | None = None) -> None:
        self._registry = registry
        self._launcher_script = launcher_script
        self._python_cmd = list(python_cmd) if python_cmd else [sys.executable]
        self._history: list[ExecutionRecord] = []

    # Placeholder command construction (real logic will reflect current monolith)
    def _build_command(self, label: str, mode: str) -> list[str]:
        return [*self._python_cmd, str(self._launcher_script), "--mode", mode, "--test", label]

    def launch_original(self, label: str) -> ExecutionResult:
        cmd = self._build_command(label, "original")
        result = ExecutionResult(success=True, launched=False, errors=[], command=cmd)
        self._history.append(ExecutionRecord(test_ids=[label], timestamp=time.time(), mode="original", result=result))
        return result

    def launch_framework(self, label: str) -> ExecutionResult:
        cmd = self._build_command(label, "framework")
        result = ExecutionResult(success=True, launched=False, errors=[], command=cmd)
        self._history.append(ExecutionRecord(test_ids=[label], timestamp=time.time(), mode="framework", result=result))
        return result

    def launch_comparison(self, labels: list[str]) -> ExecutionResult:
        cmd = [*self._python_cmd, str(self._launcher_script), "--comparison", *labels]
        result = ExecutionResult(success=True, launched=False, errors=[], command=cmd)
        self._history.append(ExecutionRecord(test_ids=list(labels), timestamp=time.time(), mode="comparison", result=result))
        return result

    def history(self) -> list[ExecutionRecord]:  # pragma: no cover - trivial
        return list(self._history)
