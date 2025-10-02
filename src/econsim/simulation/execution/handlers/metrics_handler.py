"""Metrics handler: performance timing & spike detection.

Extracts rolling steps/sec and performance spike logic from legacy step code.
Flush/observer coordination remains in world.step to keep this handler focused
on metric derivation only.
"""

from __future__ import annotations

import os
import time
from typing import List

from ..context import StepContext
from ..result import StepResult
from . import BaseStepHandler


class MetricsHandler(BaseStepHandler):
	def __init__(self) -> None:
		super().__init__("metrics")
		self._step_times: List[float] = []  # monotonically increasing perf_counter stamps

	def _execute_impl(self, context: StepContext) -> StepResult:
		now = time.perf_counter()
		self._step_times.append(now)
		if len(self._step_times) > 30:
			self._step_times.pop(0)

		steps_per_sec = None
		rolling_mean_ms = None
		spike = False
		spike_factor = float(os.environ.get("ECONSIM_PERF_SPIKE_FACTOR", "1.35"))

		if len(self._step_times) >= 2:
			time_window = self._step_times[-1] - self._step_times[0]
			if time_window > 0:
				steps_per_sec = (len(self._step_times) - 1) / time_window
		# Compute rolling mean of recent frame durations for spike detection
		if len(self._step_times) >= 10:
			durations = []
			for i in range(1, len(self._step_times)):
				durations.append((self._step_times[i] - self._step_times[i-1]) * 1000)
			if durations:
				rolling_mean_ms = sum(durations) / len(durations)
				# Current frame duration = last duration
				current_ms = durations[-1]
				if rolling_mean_ms > 0 and current_ms > rolling_mean_ms * spike_factor:
					spike = True

					# Emit performance spike event using observer pattern
					try:  # pragma: no cover
						from ....observability.observer_logger import get_global_observer_logger
						logger = get_global_observer_logger()
						if logger:
							# Create structured performance spike message
							message = (
								f"Performance spike - Step: {context.step_number}, "
								f"Time: {current_ms:.2f}ms, "
								f"Rolling mean: {rolling_mean_ms:.2f}ms, "
								f"Agents: {len(context.simulation.agents)}, "
								f"Resources: {context.simulation.grid.resource_count()}"
							)
							logger.log_performance(message, context.step_number)
					except Exception:
						pass

		return StepResult.with_metrics(
			self.handler_name,
			steps_per_sec=steps_per_sec if steps_per_sec is not None else 0.0,
			rolling_mean_ms=rolling_mean_ms if rolling_mean_ms is not None else 0.0,
			perf_spike=spike,
		)

