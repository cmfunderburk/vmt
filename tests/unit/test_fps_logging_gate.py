"""Test FPS logging gating via ECONSIM_DEBUG_FPS env variable.

We create the EmbeddedPygameWidget, run enough ticks (>1s simulated wall time sliced),
and capture stdout to ensure no [FPS] line without flag and at least one with the flag.
To accelerate, we monkeypatch FRAME_INTERVAL_MS to a small value and manually invoke _on_tick.
"""
from __future__ import annotations

import os
import time
import io
import contextlib
from PyQt6.QtWidgets import QApplication

from econsim.gui.embedded_pygame import EmbeddedPygameWidget
from econsim.simulation.world import Simulation
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent
from econsim.preferences.cobb_douglas import CobbDouglasPreference

app = QApplication.instance() or QApplication([])


def _build_sim():
    grid = Grid(5,5, resources=[(1,1,'A')])
    pref = CobbDouglasPreference(alpha=0.5)
    agent = Agent(id=0, x=0, y=0, preference=pref)
    return Simulation(grid=grid, agents=[agent])


def _run_ticks(widget: EmbeddedPygameWidget, target_seconds: float):
    # Speed up by invoking _on_tick frequently; rely on internal perf_counter for FPS gating window.
    end = time.perf_counter() + target_seconds
    while time.perf_counter() < end:
        widget._on_tick()  # type: ignore[attr-defined]


def test_fps_logging_suppressed_without_flag(monkeypatch):
    monkeypatch.delenv('ECONSIM_DEBUG_FPS', raising=False)
    sim = _build_sim()
    w = EmbeddedPygameWidget(simulation=sim)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _run_ticks(w, 1.1)
    out = buf.getvalue()
    assert '[FPS]' not in out, f"Unexpected FPS output without gate flag: {out[:120]}"
    w.close()


def test_fps_logging_present_with_flag(monkeypatch):
    monkeypatch.setenv('ECONSIM_DEBUG_FPS', '1')
    sim = _build_sim()
    w = EmbeddedPygameWidget(simulation=sim)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _run_ticks(w, 1.1)
    out = buf.getvalue()
    assert '[FPS]' in out, "Expected FPS output when gate flag set"
    w.close()
