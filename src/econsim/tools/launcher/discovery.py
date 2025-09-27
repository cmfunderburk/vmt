"""Custom test discovery logic (Phase 1 scaffold).

The real parsing logic will be migrated from the monolithic launcher.
This scaffold provides deterministic ordering & basic structure.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from .types import CustomTestInfo


class CustomTestDiscovery:
    def __init__(self, tests_dir: Path) -> None:
        self._tests_dir = tests_dir

    def discover(self) -> List[CustomTestInfo]:  # pragma: no cover - placeholder
        if not self._tests_dir.exists():
            return []
        results: List[CustomTestInfo] = []
        for path in sorted(self._tests_dir.glob("*.py")):
            info = self.parse(path)
            if info:
                results.append(info)
        return results

    def parse(self, file_path: Path) -> CustomTestInfo | None:  # pragma: no cover - placeholder
        # Placeholder metadata extraction; real version will parse headers.
        name = file_path.stem
        return CustomTestInfo(id=name, name=name, path=file_path, tags=[], summary="")

    def validate(self, file_path: Path) -> bool:  # pragma: no cover - placeholder
        return file_path.is_file() and file_path.suffix == ".py"
