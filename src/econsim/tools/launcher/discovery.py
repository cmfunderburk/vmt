"""Custom test discovery logic (Step 4 implementation).

Pure, UI‑agnostic metadata extraction from custom test files located in a
directory. Mirrors (in simplified form) the monolith's parsing logic used in
`populate_custom_tests()` / `parse_test_file`, while returning structured
`CustomTestInfo` dataclasses.

Determinism: results are sorted by filename. Duplicate IDs are allowed at
discovery time (caller may enforce uniqueness) but ordering remains stable.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import re

from .types import CustomTestInfo


class CustomTestDiscovery:
    def __init__(self, tests_dir: Path) -> None:
        self._tests_dir = tests_dir

    def discover(self) -> List[CustomTestInfo]:
        """Discover all custom test files in directory.

        Returns a list of `CustomTestInfo` sorted by filename for deterministic
        ordering. Invalid/malformed files are skipped.
        """
        if not self._tests_dir.exists():
            return []
        results: List[CustomTestInfo] = []
        for path in sorted(self._tests_dir.glob("*.py")):
            info = self.parse(path)
            if info is not None:
                results.append(info)
        return results

    def parse(self, file_path: Path) -> Optional[CustomTestInfo]:
        """Parse a custom test file extracting basic metadata.

        Extraction rules (mirroring monolith simplified):
        * Name: from docstring line 'Custom Generated Test: <Name>' else stem
        * Created: from 'Created: <date>' (stored in summary if present)
        * Config summary: collects grid_size, agent_count, resource_density,
          preference_mix if present inside `CUSTOM_CONFIG = TestConfiguration(...)`
        * ID: chosen as filename stem (stable and unique under normal usage)
        * Tags: currently empty list (future enhancement: parse '# tags: a,b')
        """
        if not self.validate(file_path):
            return None
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None

        name = self._extract(text, r"Custom Generated Test: (.+)") or file_path.stem
        created = self._extract(text, r"Created: (.+)") or "Unknown"
        block_match = re.search(r"CUSTOM_CONFIG = TestConfiguration\((.*?)\)\n", text, re.DOTALL)
        config_block = block_match.group(1) if block_match else None
        summary_parts: List[str] = []
        if created and created != "Unknown":
            summary_parts.append(f"Created: {created}")
        if config_block:
            # Grid size
            grid_match = re.search(r"grid_size=\((\d+), (\d+)\)", config_block)
            if grid_match:
                summary_parts.append(f"Grid: {grid_match.group(1)}x{grid_match.group(2)}")
            # Agent count
            agent_ct = self._extract(config_block, r"agent_count=(\d+)")
            if agent_ct:
                summary_parts.append(f"Agents: {agent_ct}")
            # Resource density
            density = self._extract(config_block, r"resource_density=([0-9.]+)")
            if density:
                try:
                    summary_parts.append(f"Density: {float(density):.2f}")
                except ValueError:
                    pass
            # Preference mix
            pref = self._extract(config_block, r"preference_mix=\"([^\"]+)\"")
            if pref:
                summary_parts.append(f"Prefs: {pref}")

        summary = " | ".join(summary_parts)
        return CustomTestInfo(
            id=file_path.stem,
            name=name,
            path=file_path,
            tags=[],
            summary=summary,
        )

    def validate(self, file_path: Path) -> bool:
        return file_path.is_file() and file_path.suffix == ".py"

    @staticmethod
    def _extract(text: str, pattern: str, flags: int = 0) -> Optional[str]:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip()
        return None
