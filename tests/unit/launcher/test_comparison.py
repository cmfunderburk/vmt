import pytest

from econsim.tools.launcher.comparison import ComparisonController, AddResult


def test_add_and_selected_order():
    c = ComparisonController(max_selections=4)
    r1 = c.add("baseline")
    r2 = c.add("candidate1")
    assert r1.added and r2.added
    assert c.selected() == ["baseline", "candidate1"]
    assert c.can_launch() is True


def test_duplicate_rejected():
    c = ComparisonController(max_selections=3)
    c.add("A")
    dup = c.add("A")
    assert not dup.added
    assert dup.reason == "duplicate"
    assert c.selected() == ["A"]


def test_capacity_enforced():
    c = ComparisonController(max_selections=2)
    assert c.add("A").added
    assert c.add("B").added
    over = c.add("C")
    assert not over.added and over.reason == "capacity"
    assert c.selected() == ["A", "B"]


def test_remove_and_remove_absent():
    c = ComparisonController(max_selections=3)
    c.add("A")
    c.add("B")
    assert c.remove("A") is True
    assert c.remove("A") is False  # already removed
    assert c.selected() == ["B"]


def test_clear():
    c = ComparisonController(max_selections=3)
    c.add("A")
    c.add("B")
    c.clear()
    assert c.selected() == []
    assert c.can_launch() is False


def test_invalid_and_snapshot():
    c = ComparisonController(max_selections=3)
    invalid = c.add("   ")
    assert not invalid.added and invalid.reason == "invalid"
    c.add("A")
    c.add("B")
    snap = c.snapshot()
    assert snap["labels"] == ["A", "B"]
    assert snap["capacity"] == 3
    assert snap["remaining"] == 1
    assert snap["can_launch"] is True


def test_minimum_two_requirement():
    c = ComparisonController()
    assert c.add("one").added
    assert not c.can_launch()
    assert c.add("two").added
    assert c.can_launch()


def test_constructor_minimum_enforced():
    with pytest.raises(ValueError):
        ComparisonController(max_selections=1)
