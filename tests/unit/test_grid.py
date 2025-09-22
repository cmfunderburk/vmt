from econsim.simulation.grid import Grid
import pytest


def test_grid_add_and_query():
    g = Grid(10, 5)
    g.add_resource(3, 2)
    assert g.has_resource(3, 2)
    assert not g.has_resource(1, 1)
    assert g.resource_count() == 1


def test_grid_take_resource():
    g = Grid(4, 4, resources=[(1, 1), (2, 2)])
    assert g.take_resource(1, 1) is True
    assert g.take_resource(1, 1) is False  # already removed
    assert g.resource_count() == 1


def test_grid_bounds_validation():
    g = Grid(3, 3)
    with pytest.raises(ValueError):
        g.add_resource(-1, 0)
    with pytest.raises(ValueError):
        g.has_resource(3, 0)
    with pytest.raises(ValueError):
        g.take_resource(0, 3)


def test_grid_serialize_round_trip():
    g = Grid(5, 5, resources=[(0, 0), (2, 3)])
    data = g.serialize()
    g2 = Grid.deserialize(data)
    assert g2.width == 5 and g2.height == 5
    for (x, y) in [(0, 0), (2, 3)]:
        assert g2.has_resource(x, y)
    assert g2.resource_count() == 2
