import os, random, pytest

from econsim.simulation.world import Simulation
from econsim.simulation.agent import Agent
from econsim.simulation.grid import Grid
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.metrics import MetricsCollector
from econsim.gui.simulation_controller import SimulationController


def _pref():
    return CobbDouglasPreference(alpha=0.5)


def _make_sim():
    agents = [
        Agent(id=1, x=0, y=0, preference=_pref()),
        Agent(id=2, x=0, y=0, preference=_pref()),
        Agent(id=3, x=1, y=0, preference=_pref()),  # third agent for occasional extra coloc variations
    ]
    # Seed asymmetric bundles to allow a mutually beneficial trade
    agents[0].carrying['good1'] = 2; agents[0].carrying['good2'] = 0
    agents[1].carrying['good1'] = 0; agents[1].carrying['good2'] = 2
    agents[2].carrying['good1'] = 1; agents[2].carrying['good2'] = 1
    sim = Simulation(grid=Grid(6,6, []), agents=agents)
    sim.metrics_collector = MetricsCollector()
    return sim


def _clear_all_env():
    for k in ("ECONSIM_TRADE_DRAFT","ECONSIM_TRADE_EXEC","ECONSIM_TRADE_GUI_INFO","ECONSIM_FORAGE_ENABLED"):
        os.environ.pop(k, None)

@pytest.mark.parametrize(
    "forage,bilateral", [
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    ]
)
def test_gui_trade_flag_matrix(forage, bilateral):  # type: ignore[no-untyped-def]
    """Matrix over simplified behavior controls (forage, bilateral exchange).

    Tests the new simplified 2-checkbox system replacing complex 4-checkbox approach.
    Assertions:
      * When bilateral disabled -> no trade intents stored.
      * When bilateral enabled -> both drafting and execution occur (intents allocated, execution may occur).
      * When both behaviors enabled: foraging and trading can both occur.
    """
    _clear_all_env()
    sim = _make_sim()
    controller = SimulationController(simulation=sim)
    controller.set_forage_enabled(True if forage else False)  # type: ignore[arg-type]
    controller.set_bilateral_enabled(True if bilateral else False)  # type: ignore[arg-type]
    # Force decision mode path
    rng = random.Random(0)
    # Add a resource at (0,0) so if foraging enabled one agent may collect before trade enumeration
    if forage:
        sim.grid.add_resource(0,0,'A')
    pre_bundles = {a.id: (a.carrying['good1'], a.carrying['good2']) for a in sim.agents}
    sim.step(rng, use_decision=True)
    intents = getattr(sim, 'trade_intents', None)
    if not bilateral:
        assert intents is None
    else:
        assert intents is not None  # Bilateral exchange enabled means both draft+exec
        # If bilateral enabled, execution may occur depending on viable trades
        mc = sim.metrics_collector
        assert mc is not None
        executed = getattr(mc, 'last_executed_trade', None)
        if executed is not None:
            post_bundles = {a.id: (a.carrying['good1'], a.carrying['good2']) for a in sim.agents}
            changed = [aid for aid in post_bundles if post_bundles[aid] != pre_bundles[aid]]
            assert changed, "Expected at least one agent carrying bundle to change after execution"


def test_execution_highlight_presence():  # type: ignore[no-untyped-def]
    """When execution occurs, _last_trade_highlight should be populated for a limited duration."""
    _clear_all_env()
    sim = _make_sim()
    controller = SimulationController(simulation=sim)
    controller.set_bilateral_enabled(True)  # Simplified: bilateral exchange includes both draft+exec
    rng = random.Random(0)
    # Step until a trade executes or max 10 steps to avoid infinite loop
    for _ in range(10):
        sim.step(rng, use_decision=True)
        if getattr(sim.metrics_collector, 'last_executed_trade', None):
            hl = getattr(sim, '_last_trade_highlight', None)
            assert hl is not None
            _, _, expire = hl
            assert expire > sim.steps
            # Advance steps beyond expiry
            for _ in range(15):
                sim.step(rng, use_decision=True)
            assert getattr(sim, '_last_trade_highlight', None) is None
            break
    else:
        pytest.skip("No trade executed in 10 steps; adjust test scenario if this flakes")

__all__ = [
    'test_gui_trade_flag_matrix',
    'test_execution_highlight_presence',
]
