"""Data and configuration directory resolution (Step 3 implementation).

Implements a minimal, side‑effect free path resolution layer for the launcher
subsystem with support for:

* XDG Base Directory Specification on Linux / other POSIX (fallback to HOME).
* Platform placeholders for Windows / macOS (documented TODO, returning
    deterministic paths under HOME so tests remain stable until specialized
    handling is added).
* Legacy path detection (current monolith locations) for future migration.
* Dry‑run migration planning (returns structured actions; does not write).
* Optional execution mode that creates target directories (idempotent), but
    still does NOT move/copy files yet (Phase 1 scope constraint: no external
    side‑effects beyond directory creation when explicitly requested).

Design Goals (Part 1 Scope):
1. Deterministic path computation (pure functions derived from env + app name).
2. Zero I/O on import; directory creation only when `migrate(execute=True)`.
3. Structured outputs (`MigrationAction`, `MigrationReport`) for testability.
4. Forward compatibility for future file move/copy operations.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Iterable
import os
import sys

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class MigrationAction:
    source: Path
    destination: Path
    exists: bool


@dataclass
class MigrationReport:
    planned: List[MigrationAction]
    executed: List[MigrationAction]


class DataLocationResolver:
    """Resolve configuration / data / state directories for the launcher.

    The resolver follows the XDG Base Directory Specification where
    applicable (Linux / POSIX) and uses deterministic HOME‑anchored fallbacks
    elsewhere (macOS, Windows) until specialized handling is implemented.

    No directories are created during initialization. Directory creation is
    performed only when `migrate(execute=True)` is called.
    """

    def __init__(self, app_name: str = "econsim_launcher") -> None:
        self._app_name = app_name
        self._home = Path(os.path.expanduser("~"))

    # ------------------------------------------------------------------
    # Public directory accessors
    # ------------------------------------------------------------------
    def config_dir(self) -> Path:
        if self._is_linux_like():
            base = _first_existing_or_default([
                os.environ.get("XDG_CONFIG_HOME"),
                str(self._home / ".config"),
            ], default=str(self._home / ".config"))
        else:
            # TODO (macOS/Windows specialization): keep stable deterministic path.
            base = str(self._home / ".config")
        return Path(base) / self._app_name

    def data_dir(self) -> Path:
        if self._is_linux_like():
            base = _first_existing_or_default([
                os.environ.get("XDG_DATA_HOME"),
                str(self._home / ".local" / "share"),
            ], default=str(self._home / ".local" / "share"))
        else:
            # Placeholder path; will later adapt to AppData / Library semantics.
            base = str(self._home / ".local" / "share")
        return Path(base) / self._app_name

    def state_dir(self) -> Path:
        if self._is_linux_like():
            base = _first_existing_or_default([
                os.environ.get("XDG_STATE_HOME"),
                str(self._home / ".local" / "state"),
            ], default=str(self._home / ".local" / "state"))
        else:
            base = str(self._home / ".local" / "state")
        return Path(base) / self._app_name

    # ------------------------------------------------------------------
    # Legacy path enumeration (current monolith locations)
    # ------------------------------------------------------------------
    def legacy_paths(self) -> Dict[str, Path]:
        # Presently only custom tests root; expand as monolith extraction progresses.
        return {
            "custom_tests": Path("MANUAL_TESTS") / "custom_tests",
            # Potential future additions: bookmarks file, comparison snapshots, etc.
        }

    # ------------------------------------------------------------------
    # Migration planning & execution (non‑destructive placeholder)
    # ------------------------------------------------------------------
    def migration_plan(self) -> List[MigrationAction]:
        plan: List[MigrationAction] = []
        target_root = self.data_dir()
        for name, legacy_path in self.legacy_paths().items():
            plan.append(
                MigrationAction(
                    source=legacy_path,
                    destination=target_root / name,
                    exists=legacy_path.exists(),
                )
            )
        return plan

    def migrate(self, execute: bool = False) -> MigrationReport:
        plan = self.migration_plan()
        executed: List[MigrationAction] = []
        if execute:
            # Create destination directories only (non‑destructive; no file moves yet).
            for action in plan:
                try:
                    action.destination.parent.mkdir(parents=True, exist_ok=True)
                    action.destination.mkdir(parents=True, exist_ok=True)
                except Exception:
                    # Directory creation failures are ignored for now; future
                    # implementation may collect errors.
                    pass
                executed.append(action)
        return MigrationReport(planned=plan, executed=executed)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _is_linux_like() -> bool:
        return sys.platform.startswith("linux") or sys.platform.startswith("freebsd")


# ---------------------------------------------------------------------------
# Utility Functions (module‑private)
# ---------------------------------------------------------------------------
def _first_existing_or_default(candidates: Iterable[str | None], default: str) -> str:
    for c in candidates:
        if c and c.strip():
            return c  # We don't require the directory to already exist.
    return default

