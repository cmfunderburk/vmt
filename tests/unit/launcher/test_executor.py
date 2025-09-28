import time
from pathlib import Path

from econsim.tools.launcher.executor import TestExecutor
from econsim.tools.launcher.types import TestConfiguration, ExecutionResult
from econsim.tools.launcher.registry import TestRegistry


# Helper sources

def builtin_source():
    return [
        TestConfiguration(id=1, label="baseline", mode="original", file=Path("baseline.py"), meta={}),
        TestConfiguration(id=2, label="candA", mode="framework", file=Path("candA.py"), meta={}),
        TestConfiguration(id=3, label="candB", mode="framework", file=Path("candB.py"), meta={}),
    ]


def test_single_launch_original():
    reg = TestRegistry(builtin_source)
    exe = TestExecutor(reg, launcher_script=Path("run_launcher.py"), python_cmd=["python"])
    result = exe.launch_original("baseline")
    assert result.success and result.launched
    assert result.command == ["python", "run_launcher.py", "--mode", "original", "--label", "baseline"]
    assert len(exe.history()) == 1


def test_single_launch_unknown_label():
    reg = TestRegistry(builtin_source)
    exe = TestExecutor(reg, launcher_script=Path("run_launcher.py"))
    result = exe.launch_framework("missing")
    assert not result.success and not result.launched
    assert "unknown label" in result.errors[0]
    assert result.command == []


def test_comparison_success():
    reg = TestRegistry(builtin_source)
    exe = TestExecutor(reg, launcher_script=Path("run_launcher.py"), python_cmd=["py"])
    result = exe.launch_comparison(["baseline", "candA", "candB"])
    assert result.success and result.launched
    assert result.command == [
        "py",
        "run_launcher.py",
        "--mode",
        "comparison",
        "--label",
        "baseline",
        "--label",
        "candA",
        "--label",
        "candB",
    ]
    # History includes previous operations (none here) + this one
    assert len(exe.history()) == 1


def test_comparison_too_few():
    reg = TestRegistry(builtin_source)
    exe = TestExecutor(reg, launcher_script=Path("run_launcher.py"))
    result = exe.launch_comparison(["baseline"])  # only one
    assert not result.success and not result.launched
    assert "at least two" in result.errors[0]


def test_comparison_missing_label():
    reg = TestRegistry(builtin_source)
    exe = TestExecutor(reg, launcher_script=Path("run_launcher.py"))
    result = exe.launch_comparison(["baseline", "unknown"])  # missing second
    assert not result.success
    assert "unknown labels" in result.errors[0]


def test_history_accumulates():
    reg = TestRegistry(builtin_source)
    exe = TestExecutor(reg, launcher_script=Path("run_launcher.py"))
    exe.launch_original("baseline")
    exe.launch_framework("candA")
    exe.launch_comparison(["baseline", "candA"])  # should succeed
    h = exe.history()
    assert len(h) == 3
    # Ensure timestamps monotonic non-decreasing
    ts = [r.timestamp for r in h]
    assert ts == sorted(ts)

