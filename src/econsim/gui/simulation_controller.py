"""SimulationController – orchestrates high-level simulation control for GUI.

Phase A responsibilities:
* Hold reference to Simulation
* Provide step() for manual stepping in turn mode
* Provide metrics snapshot (ticks, remaining resources, hash if available)
* Teardown hook (future extension point)
"""
from __future__ import annotations

from typing import Optional, Deque
from collections import deque
from time import perf_counter

from econsim.simulation.world import Simulation


class SimulationController:
    def __init__(self, simulation: Simulation):
        self.simulation = simulation
        self._hash_cache: Optional[str] = None
        self._paused: bool = False
        self._step_times: Deque[float] = deque(maxlen=64)
        # Playback control (turn mode / educational pacing). None => unrestricted (per-frame) stepping.
        self._playback_tps: float | None = None
        self._last_auto_step_time: float | None = None

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def is_paused(self) -> bool:
        return self._paused

    def manual_step(self, count: int = 1) -> None:
        import random
        rng = random.Random(999)  # stable manual stepping RNG
        for _ in range(max(1, count)):
            self.simulation.step(rng, use_decision=True)
            self._record_step_timestamp()
        # Reset scheduling anchor so an immediate auto step does not fire right after manual stepping.
        self._last_auto_step_time = None

    # --- Playback Rate -------------------------------------------------
    def set_playback_tps(self, tps: float | None) -> None:
        """Set desired automatic playback stepping rate (turns per second).

        tps=None disables throttling (reverts to per-frame stepping when unpaused).
        Values <=0 are treated as None.
        """
        if tps is None or tps <= 0:
            self._playback_tps = None
        else:
            # Clamp to a reasonable upper bound to avoid UI accidents.
            self._playback_tps = min(float(tps), 20.0)
        self._last_auto_step_time = None

    def playback_tps(self) -> float | None:
        return self._playback_tps

    def _should_step_now(self, now: float) -> bool:
        """Return True if an auto step should occur at this timestamp.

        If no playback_tps is set, always returns True (legacy behavior).
        """
        if self._playback_tps is None:
            return True
        interval = 1.0 / max(0.0001, self._playback_tps)
        if self._last_auto_step_time is None:
            self._last_auto_step_time = now
            return True
        if now - self._last_auto_step_time >= interval:
            # Allow exactly one step; advance anchor by integer multiples to prevent drift build-up.
            skipped = int((now - self._last_auto_step_time) // interval)
            self._last_auto_step_time += max(1, skipped) * interval
            return True
        return False

    def determinism_hash(self) -> str:
        collector = getattr(self.simulation, "metrics_collector", None)
        if collector is None:
            return "(metrics disabled)"
        # Return cached if already computed
        if self._hash_cache is not None:
            return self._hash_cache
        return self.refresh_hash()

    def refresh_hash(self) -> str:
        collector = getattr(self.simulation, "metrics_collector", None)
        if collector is None:
            return "(metrics disabled)"
        try:
            h = collector.determinism_hash()
            self._hash_cache = h
            return h
        except Exception:
            return self._hash_cache or "<hash error>"

    def ticks(self) -> int:
        return self.simulation.steps

    def remaining_resources(self) -> int:
        grid = getattr(self.simulation, "grid", None)
        if grid is None:
            return 0
        try:
            return sum(1 for _ in grid.iter_resources())  # type: ignore[attr-defined]
        except Exception:
            return 0

    def steps_per_second_estimate(self) -> float:
        times = self._step_times
        if len(times) < 2:
            return 0.0
        span = times[-1] - times[0]
        if span <= 0:
            return 0.0
        return (len(times) - 1) / span

    # Internal hook used by widget when auto-stepping
    def _record_step_timestamp(self) -> None:
        self._step_times.append(perf_counter())
        # Invalidate hash cache (new step implies potential hash change)
        self._hash_cache = None

    def teardown(self) -> None:
        # Placeholder for future resource clean shutdown hooks
        pass

__all__ = ["SimulationController"]
