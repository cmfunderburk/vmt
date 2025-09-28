"""Unit tests for launcher cards component.

Gate G11: Card model/build pure & deterministic - stable ordering vs legacy snapshot.
"""
import pytest
from pathlib import Path

from econsim.tools.launcher.cards import TestCardModel, build_card_models
from econsim.tools.launcher.registry import TestRegistry
from econsim.tools.launcher.types import TestConfiguration


@pytest.fixture
def mock_registry():
    """Create a mock registry with test data."""
    def mock_builtin_source():
        return [
            TestConfiguration(
                id=1,
                label="Test Alpha",
                mode="framework",
                file=Path("test_1.py"),
                meta={"description": "First test"}
            ),
            TestConfiguration(
                id=3,
                label="Test Gamma", 
                mode="original",
                file=Path("test_3.py"),
                meta={"description": "Third test"}
            ),
            TestConfiguration(
                id=2,
                label="Test Beta",
                mode="framework", 
                file=Path("test_2.py"),
                meta={"description": "Second test"}
            ),
        ]
    
    return TestRegistry(builtin_source=mock_builtin_source)


def test_card_model_dataclass():
    """Test card model basic functionality."""
    model = TestCardModel(
        id=1,
        label="Test Card",
        mode="framework",
        file=Path("test.py"),
        order=1,
        meta={"key": "value"}
    )
    
    assert model.id == 1
    assert model.label == "Test Card"
    assert model.mode == "framework"
    assert model.file == Path("test.py")
    assert model.order == 1
    assert model.meta == {"key": "value"}


def test_card_model_to_dict():
    """Test card model serialization."""
    model = TestCardModel(
        id=1,
        label="Test Card",
        mode="framework", 
        file=Path("test.py"),
        order=1,
        meta={"key": "value"}
    )
    
    result = model.to_dict()
    expected = {
        "id": 1,
        "label": "Test Card",
        "mode": "framework",
        "file": "test.py",
        "order": 1,
        "meta": {"key": "value"}
    }
    
    assert result == expected


def test_card_model_none_file():
    """Test card model with None file."""
    model = TestCardModel(
        id=1,
        label="Test Card",
        mode="framework",
        file=None,
        order=1,
        meta={}
    )
    
    result = model.to_dict()
    assert result["file"] is None


def test_build_card_models_deterministic_ordering(mock_registry):
    """Test that build_card_models produces deterministic ordering by ID.
    
    Gate G11: Stable ordering verification - should be sorted by test ID regardless
    of registry insertion order.
    """
    models = build_card_models(mock_registry)
    
    # Should be 3 models
    assert len(models) == 3
    
    # Should be ordered by ID (1, 2, 3) not insertion order (1, 3, 2)
    assert models[0].id == 1
    assert models[1].id == 2  
    assert models[2].id == 3
    
    # Order field should reflect position
    assert models[0].order == 1
    assert models[1].order == 2
    assert models[2].order == 3


def test_build_card_models_content_mapping(mock_registry):
    """Test that model content correctly maps from registry."""
    models = build_card_models(mock_registry)
    
    # Check first model (ID=1)
    model_1 = models[0]
    assert model_1.label == "Test Alpha"
    assert model_1.mode == "framework"
    assert model_1.file == Path("test_1.py")
    assert model_1.meta == {"description": "First test"}
    
    # Check second model (ID=2, but was inserted last in registry)
    model_2 = models[1]
    assert model_2.label == "Test Beta"
    assert model_2.mode == "framework"
    assert model_2.file == Path("test_2.py")
    assert model_2.meta == {"description": "Second test"}


def test_build_card_models_empty_registry():
    """Test build_card_models with empty registry."""
    def empty_source():
        return []
    
    registry = TestRegistry(builtin_source=empty_source)
    models = build_card_models(registry)
    
    assert models == []


def test_build_card_models_snapshot_stability():
    """Test that model labels produce consistent snapshot for regression detection.
    
    Gate G11: Snapshot test pattern - changes to ordering should be explicit.
    """
    def stable_source():
        return [
            TestConfiguration(id=1, label="Baseline", mode="framework", file=None, meta={}),
            TestConfiguration(id=2, label="Sparse Long-Range", mode="framework", file=None, meta={}),
            TestConfiguration(id=3, label="Dense Short-Range", mode="framework", file=None, meta={}),
        ]
    
    registry = TestRegistry(builtin_source=stable_source)
    models = build_card_models(registry)
    
    # Extract labels in order
    labels = [m.label for m in models]
    
    # Expected stable ordering (by ID, not alphabetical)
    expected_labels = ["Baseline", "Sparse Long-Range", "Dense Short-Range"]
    
    assert labels == expected_labels, f"Label ordering changed: {labels} != {expected_labels}"


def test_card_model_immutable():
    """Test that TestCardModel is immutable (frozen dataclass)."""
    model = TestCardModel(
        id=1, label="Test", mode="framework", file=None, order=1, meta={}
    )
    
    # Should not be able to modify frozen dataclass
    with pytest.raises(AttributeError):
        model.id = 2  # type: ignore[misc]
    
    with pytest.raises(AttributeError):
        model.label = "Modified"  # type: ignore[misc]