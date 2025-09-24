"""SessionFactory – builds Simulation + controller wrapper from a descriptor.

Phase A: minimal mapping from descriptor → SimConfig → Simulation.from_config.
Adds agent spawning & simple resource seeding using density (if provided).
"""
from __future__ import annotations

from dataclasses import dataclass
import random
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .simulation_controller import SimulationController

from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation


@dataclass
class SimulationSessionDescriptor:
    name: str
    mode: str  # 'continuous' | 'legacy'
    seed: int
    grid_size: tuple[int, int]
    agents: int
    density: float | None
    enable_respawn: bool
    enable_metrics: bool
    preference_type: str
    turn_auto_interval_ms: int | None
    start_paused: bool = False


class SessionFactory:
    @staticmethod
    def build(descriptor: SimulationSessionDescriptor) -> "SimulationController":  # type: ignore[name-defined]
        # Derive initial resources
        resources: List[tuple[int, int, str]] = []
        rng = random.Random(descriptor.seed)
        gw, gh = descriptor.grid_size
        if descriptor.density and descriptor.density > 0:
            target = int(gw * gh * min(1.0, max(0.0, descriptor.density)))
            placed = 0
            while placed < target:
                x = rng.randint(0, gw - 1)
                y = rng.randint(0, gh - 1)
                t = 'A' if rng.random() < 0.5 else 'B'
                resources.append((x, y, t))
                placed += 1
        cfg = SimConfig(
            grid_size=descriptor.grid_size,
            initial_resources=resources,
            seed=descriptor.seed,
            enable_respawn=descriptor.enable_respawn,
            enable_metrics=descriptor.enable_metrics,
        )

        # Preference factory mapping (single preference type Phase A)
        def pref_factory(idx: int):  # minimal switch
            if descriptor.preference_type == 'cobb_douglas':
                from econsim.preferences.cobb_douglas import CobbDouglasPreference
                return CobbDouglasPreference(alpha=0.5)
            if descriptor.preference_type == 'perfect_substitutes':
                from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference
                return PerfectSubstitutesPreference(a=1.0, b=1.0)
            if descriptor.preference_type == 'leontief':
                from econsim.preferences.leontief import LeontiefPreference
                return LeontiefPreference(a=1.0, b=1.0)
            raise ValueError(f"Unknown preference type: {descriptor.preference_type}")

        # Agent spawn positions: deterministic random non-overlapping homes.
        # Use a secondary RNG keyed off seed+constant so resource layout (above) remains identical
        # to historical behavior for a given seed (avoids silent test drift tied to RNG draw order).
        positions: List[tuple[int, int]] = []
        if descriptor.agents > 0:
            agent_rng = random.Random(descriptor.seed + 9973)
            # Population ordered lexicographically (y,x) for stability.
            population: list[tuple[int, int]] = [(x, y) for y in range(gh) for x in range(gw)]
            if descriptor.agents > len(population):  # defensive: clamp to available cells
                take = len(population)
            else:
                take = descriptor.agents
            # random.sample preserves deterministic order under fixed seed & population ordering.
            positions = agent_rng.sample(population, take)
            # Assign remaining agents (if any due to clamp) none – but current descriptors shouldn't exceed grid.

        sim = Simulation.from_config(cfg, pref_factory, agent_positions=positions)
        from .simulation_controller import SimulationController  # local import to avoid cycle
        controller = SimulationController(sim)
        # Apply initial paused state if requested (replaces old turn_mode scenario)
        if getattr(descriptor, "start_paused", False):
            controller.pause()
        return controller

__all__ = [
    "SimulationSessionDescriptor",
    "SessionFactory",
]
