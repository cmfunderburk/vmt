"""Hash repeat demonstration script.

Runs two identical simulations with metrics enabled and prints determinism hash values
which should match, demonstrating repeatability.
"""
from econsim.gui.session_factory import SessionFactory, SimulationSessionDescriptor

DESC = SimulationSessionDescriptor(
    name="hashdemo",
    mode="continuous",
    seed=1234,
    grid_size=(8,8),
    agents=4,
    density=0.25,
    enable_respawn=False,
    enable_metrics=True,
    preference_type="cobb_douglas",
    turn_auto_interval_ms=None,
)

def run_hash():
    c = SessionFactory.build(DESC)
    # Step a few times with stable RNG for demonstration
    import random
    rng = random.Random(999)
    for _ in range(10):
        c.simulation.step(rng)
    return c.simulation.metrics_collector.determinism_hash()

if __name__ == "__main__":
    h1 = run_hash()
    h2 = run_hash()
    print("hash1=", h1)
    print("hash2=", h2)
    print("identical=", h1 == h2)
