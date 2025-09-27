"""Data and configuration directory resolution (Phase 1 scaffold).

Implements XDG / platform-specific directory logic and legacy data migration
planning for the launcher subsystem.

Real logic will be implemented in Step 3 of Part 1 plan.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict
import os


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

    Placeholder implementation; real XDG + platform logic forthcoming.
    """

    def __init__(self, app_name: str = "econsim_launcher") -> None:
        self._app_name = app_name

    # --- Directory Accessors -------------------------------------------------
    def config_dir(self) -> Path:
        return Path(os.getcwd()) / ".launcher_config_placeholder"

    def data_dir(self) -> Path:
        return Path(os.getcwd()) / ".launcher_data_placeholder"

    def state_dir(self) -> Path:
        return Path(os.getcwd()) / ".launcher_state_placeholder"

    # --- Legacy + Migration --------------------------------------------------
    def legacy_paths(self) -> Dict[str, Path]:
        return {"legacy_root": Path("MANUAL_TESTS") / "custom_tests"}

    def migration_plan(self) -> List[MigrationAction]:
        actions: List[MigrationAction] = []
        for name, path in self.legacy_paths().items():
            target = self.data_dir() / name
            actions.append(MigrationAction(source=path, destination=target, exists=path.exists()))
        return actions

    def migrate(self, execute: bool = False) -> MigrationReport:
        plan = self.migration_plan()
        executed: List[MigrationAction] = []
        if execute:  # Real file operations will be added later.
            for action in plan:
                # Intentionally no side-effects yet.
                executed.append(action)
        return MigrationReport(planned=plan, executed=executed)
