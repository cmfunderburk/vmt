from __future__ import annotations

import os
import random
from typing import List, Tuple, Optional, Sequence, TypeVar

import pytest

from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig

# Feature flag matrices (subset to keep runtime reasonable)
FLAG_MATRIX: List[Tuple[int,int,int,int]] = [
    # (legacy_random, forage_enabled, trade_draft, trade_exec)
    (0, 1, 0, 0),  # decision + forage only
    (0, 1, 1, 0),  # decision + forage + draft
    (0, 1, 1, 1),  # decision + forage + draft+exec
    (0, 0, 1, 1),  # decision no forage trading
    (1, 1, 0, 0),  # legacy random
]

AGENT_POSITIONS = [(0,0),(2,2),(4,1),(1,4)]


def build_sim(seed: int, positions: Optional[List[Tuple[int,int]]] = None) -> Simulation:
    cfg = SimConfig(
        grid_size=(8,8),
        initial_resources=[],
        perception_radius=6,
        respawn_target_density=0.0,
        respawn_rate=0.0,
        max_spawn_per_tick=0,
        seed=seed,
        enable_respawn=False,
        enable_metrics=True,
    )
    return Simulation.from_config(cfg, agent_positions=positions or AGENT_POSITIONS)


T = TypeVar("T")


class CountingRNG(random.Random):
    """RNG wrapper that counts number of calls capturing determinism-sensitive API usage.
    Only wraps methods used by simulation (randrange / randint / random / choice / shuffle).
    """
    def __init__(self, seed: int):
        super().__init__(seed)
        self.calls = 0
    def random(self):  # type: ignore[override]
        self.calls += 1
        return super().random()
    def randrange(self, start: int, stop: Optional[int] = None, step: int = 1) -> int:  # type: ignore[override]
        self.calls += 1
        if stop is None:
            return super().randrange(start)
        return super().randrange(start, stop, step)
    def randint(self, a, b):  # type: ignore[override]
        self.calls += 1
        return super().randint(a,b)
    def choice(self, seq: Sequence[T]) -> T:  # type: ignore[override]
        self.calls += 1
        return super().choice(seq)
    def shuffle(self, x: List[T]) -> None:  # type: ignore[override]
        self.calls += 1
        super().shuffle(x)

def run_scenario(flags: Tuple[int,int,int,int], steps: int = 25) -> Tuple[str, int]:
    legacy, forage, draft, exec_ = flags
    # Set environment
    os.environ['ECONSIM_LEGACY_RANDOM'] = str(legacy)
    os.environ['ECONSIM_FORAGE_ENABLED'] = str(forage)
    os.environ['ECONSIM_TRADE_DRAFT'] = str(draft)
    os.environ['ECONSIM_TRADE_EXEC'] = str(exec_)
    sim = build_sim(seed=123)
    rng = CountingRNG(999)
    for _ in range(steps):
        sim.step(rng, use_decision=(legacy == 0))
    h = sim.metrics_collector.determinism_hash() if sim.metrics_collector else ""
    return h, rng.calls


@pytest.mark.parametrize("flags", FLAG_MATRIX)
def test_step_decomposition_does_not_inflate_rng_calls(flags):  # type: ignore[missing-annotations]
    # Baseline run (fresh environment) repeated twice to assert identical RNG call counts
    h1, calls1 = run_scenario(flags)
    # Reset any side effects
    for var in ["ECONSIM_LEGACY_RANDOM","ECONSIM_FORAGE_ENABLED","ECONSIM_TRADE_DRAFT","ECONSIM_TRADE_EXEC"]:
        os.environ.pop(var, None)
    h2, calls2 = run_scenario(flags)
    assert calls1 == calls2, f"RNG call count drifted for flags {flags}: {calls1} vs {calls2}"
    assert h1 == h2, f"Determinism hash drift for flags {flags}: {h1} vs {h2}"

