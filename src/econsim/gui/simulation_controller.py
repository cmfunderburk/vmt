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
