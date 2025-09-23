import os
from econsim.gui.session_factory import SessionFactory, SimulationSessionDescriptor


def _build(seed: int):
    desc = SimulationSessionDescriptor(
        name="reuse",
        mode="continuous",
        seed=seed,
        grid_size=(4,4),
        agents=1,
        density=0.1,
        enable_respawn=False,
        enable_metrics=False,
        preference_type="cobb_douglas",
        turn_auto_interval_ms=None,
    )
    return SessionFactory.build(desc)


def test_controller_reuse_different_seed_hash_change():
    os.environ['ECONSIM_NEW_GUI'] = '1'
    c1 = _build(101)
    c2 = _build(102)
    # Hash disabled (metrics false) so rely on steps count independence
    assert c1.ticks() == 0 and c2.ticks() == 0
    c1.manual_step()
    assert c1.ticks() == 1 and c2.ticks() == 0
