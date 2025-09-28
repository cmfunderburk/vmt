"""Test execution abstraction (Step 8 / Gate G7).

Constructs deterministic command arrays for different launch modes without
actually spawning subprocesses yet. This makes command generation unit-testable
and defers process strategy decisions to a later integration layer.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Sequence, List

from .types import ExecutionResult, ExecutionRecord, TestConfiguration
from .registry import TestRegistry


class TestExecutor:
    __slots__ = ("_registry", "_launcher", "_python_cmd", "_history")

    def __init__(
        self,
        registry: TestRegistry,
        launcher_script: Path | str,
        python_cmd: Sequence[str] | None = None,
    ) -> None:
        self._registry = registry
        self._launcher = Path(launcher_script)
        self._python_cmd: List[str] = list(python_cmd) if python_cmd else [sys.executable]
        self._history: list[ExecutionRecord] = []

    # Public launch methods --------------------------------------------
    def launch_original(self, label: str) -> ExecutionResult:
        return self._launch_single(label, mode="original")

    def launch_framework(self, label: str) -> ExecutionResult:
        return self._launch_single(label, mode="framework")

    def launch_comparison(self, labels: list[str]) -> ExecutionResult:
        if len(labels) < 2:
            result = ExecutionResult(
                success=False,
                launched=False,
                errors=["comparison requires at least two labels"],
                command=[],
            )
            self._append_history(labels, "comparison", result)
            return result

        missing: list[str] = []
        for lab in labels:
            if self._registry.by_label(lab) is None:
                missing.append(lab)
        if missing:
            result = ExecutionResult(
                success=False,
                launched=False,
                errors=[f"unknown labels: {', '.join(missing)}"],
                command=[],
            )
            self._append_history(labels, "comparison", result)
            return result

        cmd = self._build_command_multi(labels, mode="comparison")
        result = ExecutionResult(success=True, launched=True, errors=[], command=cmd)
        self._append_history(labels, "comparison", result)
        return result

    def history(self) -> list[ExecutionRecord]:  # pragma: no cover - trivial
        return list(self._history)

    # Internal helpers -------------------------------------------------
    def _launch_single(self, label: str, mode: str) -> ExecutionResult:
        cfg = self._registry.by_label(label)
        if cfg is None:
            result = ExecutionResult(
                success=False,
                launched=False,
                errors=[f"unknown label: {label}"],
                command=[],
            )
            self._append_history([label], mode, result)
            return result
        cmd = self._build_command(cfg.label, mode=mode)
        result = ExecutionResult(success=True, launched=True, errors=[], command=cmd)
        self._append_history([cfg.label], mode, result)
        return result

    def _build_command(self, label: str, mode: str) -> list[str]:
        return [*self._python_cmd, str(self._launcher), "--mode", mode, "--label", label]

    def _build_command_multi(self, labels: list[str], mode: str) -> list[str]:
        base = [*self._python_cmd, str(self._launcher), "--mode", mode]
        for lab in labels:
            base.extend(["--label", lab])
        return base

    def _append_history(self, labels: list[str], mode: str, result: ExecutionResult) -> None:
        self._history.append(
            ExecutionRecord(
                test_ids=list(labels),  # labels double as IDs for now
                timestamp=time.time(),
                mode=mode,
                result=result,
            )
        )


__all__ = ["TestExecutor"]
