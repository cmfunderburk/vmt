"""Tests for shared launcher dataclasses (Step 5 gating: part of G4)."""
from __future__ import annotations

from dataclasses import asdict
import time

from pathlib import Path

from econsim.tools.launcher.types import (
    TestConfiguration,
    ExecutionResult,
    ExecutionRecord,
    RegistryValidationResult,
    CustomTestInfo,
)


def test_testconfiguration_round_trip() -> None:
    cfg = TestConfiguration(id=1, label="Baseline", mode="original", file=None, meta={"difficulty": "easy"})
    d = cfg.to_dict()
    # Round trip via dict -> new dataclass (manual reconstruction)
    cfg2 = TestConfiguration(id=d["id"], label=d["label"], mode=d["mode"], file=None, meta=d["meta"])
    assert cfg == cfg2
    assert d["file"] is None


def test_executionresult_and_record_helpers() -> None:
    result = ExecutionResult(success=False, launched=True, errors=["boom"], command=["python", "run.py"])  # failing
    assert result.failed()
    ts = time.time()
    rec = ExecutionRecord(test_ids=["t1", "t2"], timestamp=ts, mode="framework", result=result)
    # Ensure dataclass conversion retains nested structure
    rd = asdict(rec)
    assert rd["result"]["errors"] == ["boom"]
    assert rd["test_ids"] == ["t1", "t2"]


def test_registry_validation_result() -> None:
    vr = RegistryValidationResult(ok=False, duplicates=["A"], missing=["B"])  # failing state example
    d = asdict(vr)
    assert d == {"ok": False, "duplicates": ["A"], "missing": ["B"]}


def test_custom_test_info_dataclass() -> None:
    cti = CustomTestInfo(id="foo", name="Foo Test", path=Path(__file__), tags=["x"], summary="test")
    d = asdict(cti)
    assert d["name"] == "Foo Test"
    assert d["tags"] == ["x"]