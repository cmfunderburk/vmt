"""Tests for TestRegistry (Step 6 gating: G5)."""
from __future__ import annotations

from pathlib import Path
from typing import List

from econsim.tools.launcher.registry import TestRegistry
from econsim.tools.launcher.types import TestConfiguration


def _builtin_source() -> List[TestConfiguration]:
    return [
        TestConfiguration(id=1, label="Baseline Original", mode="original", file=None, meta={}),
        TestConfiguration(id=2, label="Baseline Framework", mode="framework", file=None, meta={}),
    ]


def _custom_source_no_dupes(tmp_path: Path) -> List[TestConfiguration]:
    script = tmp_path / "custom_case.py"
    script.write_text("print('hi')\n")
    return [TestConfiguration(id=100, label="Custom Case", mode="framework", file=script, meta={"tag": "x"})]


def test_registry_basic(tmp_path: Path) -> None:
    r = TestRegistry(builtin_source=_builtin_source, custom_source=lambda: _custom_source_no_dupes(tmp_path))
    all_items = r.all()
    assert len(all_items) == 3
    assert r.by_id(1).label == "Baseline Original"  # type: ignore[union-attr]
    assert r.by_label("Custom Case").id == 100  # type: ignore[union-attr]
    validation = r.validate()
    assert validation.ok
    assert validation.duplicates == []


def _custom_source_with_dupes(tmp_path: Path) -> List[TestConfiguration]:
    p = tmp_path / "dup.py"
    p.write_text("# dup\n")
    return [
        TestConfiguration(id=2, label="Baseline Framework", mode="framework", file=p, meta={}),  # duplicate id+label
        TestConfiguration(id=200, label="Baseline Original", mode="framework", file=p, meta={}),  # duplicate label only
    ]


def test_registry_duplicate_detection(tmp_path: Path) -> None:
    r = TestRegistry(builtin_source=_builtin_source, custom_source=lambda: _custom_source_with_dupes(tmp_path))
    validation = r.validate()
    assert not validation.ok
    # Expect both duplicate labels appearing sorted
    assert validation.duplicates == sorted(["Baseline Framework", "Baseline Original"])


def test_registry_reload(tmp_path: Path) -> None:
    # Start with no custom source
    captured = []
    def custom() -> List[TestConfiguration]:
        return captured

    r = TestRegistry(builtin_source=_builtin_source, custom_source=custom)
    assert len(r.all()) == 2
    # Add a custom entry then reload
    script = tmp_path / "added.py"
    script.write_text("# added\n")
    captured.append(TestConfiguration(id=500, label="New Custom", mode="framework", file=script, meta={}))
    r.reload()
    assert r.by_label("New Custom").id == 500  # type: ignore[union-attr]