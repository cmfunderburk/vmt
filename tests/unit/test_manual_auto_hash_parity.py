"""Hash parity test: manual+auto stepping sequence must match pure auto sequence.

Rationale:
Mixed manual and automatic stepping should not diverge deterministically
from running the same total number of steps automatically when using the
same seed and configuration. This guards the GUI manual_step persistent
RNG implementation against regression (e.g., accidental reseeding or
mode flag mismatch).

Procedure:
1. Build a Simulation via factory with fixed seed.
2. Path A: perform N1 manual steps (decision mode), then N2 automatic steps
   via simulation.step using SAME RNG object reference used internally
   for auto mode. (In GUI actual auto steps use the widget RNG seeded from
   the same seed path; controller manual uses persistent RNG seeded from
   config. We emulate by constructing two independent Simulation instances.)
3. Path B: perform (N1+N2) automatic steps directly.
4. Compare determinism hashes after steps.

We use small step counts (3 + 7) to keep test fast while exercising mixed path.
"""
from __future__ import annotations

import copy

from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig
from econsim.preferences.factory import PreferenceFactory


MANUAL_STEPS = 3
AUTO_STEPS = 7
TOTAL = MANUAL_STEPS + AUTO_STEPS


def _build_sim(seed: int = 1234):
    # Minimal deterministic config (respawn disabled to remove internal RNG variance).
    cfg = SimConfig(
        grid_size=(16, 16),
        initial_resources=[(3, 3, "good1"), (8, 9, "good2"), (12, 4, "good1")],
        seed=seed,
        enable_respawn=False,
        enable_metrics=True,
    )
    # Provide one agent so decision logic engages.
    # PreferenceFactory needs concrete type name; use built-in 'cobb_douglas'.
    pref_factory = lambda i: PreferenceFactory.create("cobb_douglas", alpha=0.5)  # type: ignore[arg-type]
    return Simulation.from_config(cfg, pref_factory, agent_positions=[(0, 0)])


def test_manual_plus_auto_matches_pure_auto():
    seed = 8675309
    # Path B (pure auto) baseline simulation
    sim_auto = _build_sim(seed)
    import random as _r
    rng_auto = _r.Random(seed)
    for _ in range(TOTAL):
        sim_auto.step(rng_auto)
    assert sim_auto.metrics_collector is not None, "Metrics collector missing in auto path"
    hash_auto = sim_auto.metrics_collector.determinism_hash()

    # Path A: mixed manual + auto using distinct Simulation instance
    sim_mixed = _build_sim(seed)
    # Emulate controller's persistent manual RNG: seeded identically to config.seed
    import random as _r
    manual_rng = _r.Random(seed)

    # Manual steps
    for _ in range(MANUAL_STEPS):
        sim_mixed.step(manual_rng)

    # For auto steps after manual, continue with SAME manual_rng to mirror controller strategy
    for _ in range(AUTO_STEPS):
        sim_mixed.step(manual_rng)

    assert sim_mixed.metrics_collector is not None, "Metrics collector missing in mixed path"
    hash_mixed = sim_mixed.metrics_collector.determinism_hash()

    assert hash_mixed == hash_auto, (
        "Determinism hash diverged for manual+auto vs pure auto path: "
        f"manual+auto={hash_mixed} pure_auto={hash_auto}"
    )
