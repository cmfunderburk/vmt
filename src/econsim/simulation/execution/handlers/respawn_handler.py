"""Respawn handler: periodic resource regeneration logic.

Moves respawn interval decision & logging from monolithic step into a
dedicated handler. Determinism preserved (interval arithmetic only).
"""

from __future__ import annotations

from ..context import StepContext
from ..result import StepResult
from . import BaseStepHandler


class RespawnHandler(BaseStepHandler):
	def __init__(self) -> None:
		super().__init__("respawn")

	def _execute_impl(self, context: StepContext) -> StepResult:
		sim = context.simulation
		scheduler = sim.respawn_scheduler
		if scheduler is None or sim._rng is None:  # noqa: SLF001
			return StepResult.with_metrics(self.handler_name, respawn_attempted=0, respawned=0, respawn_skipped_reason="inactive")

		interval = sim._respawn_interval  # noqa: SLF001
		if not interval or interval <= 0:
			return StepResult.with_metrics(self.handler_name, respawn_attempted=0, respawned=0, respawn_skipped_reason="disabled")

		prev_steps = sim._steps  # noqa: SLF001
		if (prev_steps % interval) != 0:
			return StepResult.with_metrics(self.handler_name, respawn_attempted=0, respawned=0, respawn_skipped_reason="interval")

		# Density snapshot before
		total_cells = sim.grid.width * sim.grid.height
		before_count = sim.grid.resource_count()
		target_density = getattr(scheduler, 'target_density', 0.0)
		target_count = int(target_density * total_cells) if total_cells > 0 else 0

		spawned_count = 0
		try:
			spawned_count = scheduler.step(sim.grid, sim._rng, step_index=prev_steps)  # noqa: SLF001
		except Exception:  # pragma: no cover
			return StepResult.with_metrics(self.handler_name, respawn_attempted=1, respawned=0, respawn_skipped_reason="error")

		after_count = sim.grid.resource_count()
		current_density = after_count / total_cells if total_cells > 0 else 0.0
		reason = "ok" if spawned_count > 0 else ("adequate" if after_count >= target_count else "blocked")

		return StepResult.with_metrics(
			self.handler_name,
			respawn_attempted=1,
			respawned=spawned_count,
			respawn_skipped_reason=reason if spawned_count == 0 else "",
			respawn_before=before_count,
			respawn_after=after_count,
			respawn_target=target_count,
			respawn_density=current_density,
		)

