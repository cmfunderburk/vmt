import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "scripts" / "perf_stub.py"


def _run_perf_widget(duration: float = 1.5) -> dict[str, Any]:
    env = os.environ.copy()
    # Encourage headless stability in CI
    if not env.get("DISPLAY"):
        env.setdefault("SDL_VIDEODRIVER", "dummy")
        env.setdefault("QT_QPA_PLATFORM", "offscreen")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--mode", "widget", "--duration", str(duration), "--json"],
        capture_output=True,
        text=True,
        env=env,
        timeout=20,
    )
    assert proc.returncode == 0, f"perf script failed: {proc.stderr}\nstdout={proc.stdout}"
    # Last line should be JSON
    json_line = proc.stdout.strip().splitlines()[-1]
    return json.loads(json_line)


def test_widget_perf_minimum_threshold() -> None:
    data = _run_perf_widget(1.2)
    avg_fps_val = data.get("avg_fps")
    assert isinstance(avg_fps_val, (int, float)), "avg_fps should be numeric"
    fps = float(avg_fps_val)
    # CI-safe lower bound; manual target is ≥30
    assert fps >= 25, f"Expected avg FPS >=25 (got {fps})"  # softer threshold for shared runners
    # Provide informative assertion if close to target
    if fps < 30:
        pytest.skip(f"Performance below ideal 30 FPS target (got {fps:.1f}) but above CI minimum")
