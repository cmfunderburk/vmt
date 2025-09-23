import random

from econsim.simulation.grid import Grid


def _build_grid(width: int = 20, height: int = 15, *, density: float, seed: int) -> Grid:
    rng = random.Random(seed + 1001)
    g = Grid(width, height)
    placed = 0
    for y in range(height):
        for x in range(width):
            if rng.random() <= density:
                rtype = "A" if (placed % 2 == 0) else "B"
                g.add_resource(x, y, rtype)
                placed += 1
    return g


def test_density_grid_determinism():
    seed = 4321
    density = 0.2
    g1 = _build_grid(density=density, seed=seed)
    g2 = _build_grid(density=density, seed=seed)
    assert sorted(g1.iter_resources()) == sorted(g2.iter_resources())


def test_density_grid_variation_with_seed():
    density = 0.2
    g1 = _build_grid(density=density, seed=111)
    g2 = _build_grid(density=density, seed=222)
    r1 = sorted(g1.iter_resources())
    r2 = sorted(g2.iter_resources())
    assert r1 != r2 or len(r1) == 0


def test_density_bounds():
    density = 0.5
    g = _build_grid(density=density, seed=123)
    expected = g.width * g.height * density
    assert abs(g.resource_count() - expected) < expected * 0.6
