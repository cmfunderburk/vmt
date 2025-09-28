"""Tests for DataLocationResolver (Step 3 gating: G2).

Coverage:
1. Path resolution returns distinct config/data/state directories under expected base paths.
2. Dry-run migration plan returns actions referencing legacy custom tests path.
3. Execute migration creates destination directories (idempotent, no error on second run).

The test intentionally avoids asserting platform-specific absolute prefixes beyond
basic structural expectations so it remains portable across CI hosts.
"""
from __future__ import annotations

from pathlib import Path
import os
import shutil

from econsim.tools.launcher.data import DataLocationResolver


def test_path_resolution_basic(tmp_path: Path, monkeypatch) -> None:
    # Force HOME to tmp so we have deterministic base without touching real user dirs.
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    resolver = DataLocationResolver(app_name="econsim_launcher_test")

    cfg = resolver.config_dir()
    data = resolver.data_dir()
    state = resolver.state_dir()

    # Distinct and end with app name
    assert cfg.name.endswith("econsim_launcher_test")
    assert data.name.endswith("econsim_launcher_test")
    assert state.name.endswith("econsim_launcher_test")
    assert len({cfg, data, state}) == 3

    # Should all be under the synthetic HOME
    for p in (cfg, data, state):
        assert str(p).startswith(str(tmp_path / "home")), f"{p} not under synthetic HOME"


def test_migration_plan_and_execute(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()

    # Create a legacy path structure (simulate existing custom tests dir)
    legacy_root = Path("MANUAL_TESTS") / "custom_tests"
    legacy_root.mkdir(parents=True, exist_ok=True)
    sample_file = legacy_root / "example_test.py"
    sample_file.write_text("# legacy test placeholder\n")

    resolver = DataLocationResolver(app_name="econsim_launcher_test")
    plan = resolver.migration_plan()

    # Expect at least one action referencing our legacy custom tests
    assert any(a.source == legacy_root for a in plan)

    # Dry-run: executed list empty
    dry = resolver.migrate(execute=False)
    assert dry.executed == []
    assert len(dry.planned) == len(plan)

    # Execute: directories created
    exec_report = resolver.migrate(execute=True)
    assert len(exec_report.executed) == len(plan)
    for action in exec_report.executed:
        assert action.destination.exists(), "Destination directory not created during execute migration"

    # Idempotent second execute
    repeat_report = resolver.migrate(execute=True)
    assert len(repeat_report.executed) == len(plan)
