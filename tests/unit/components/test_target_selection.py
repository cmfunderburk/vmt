"""Unit tests for target selection component."""

import pytest
from unittest.mock import Mock, MagicMock
from src.econsim.simulation.components.target_selection import (
    TargetSelectionStrategy, 
    TargetCandidate, 
    ResourceTargetStrategy
)


class TestTargetCandidate:
    def test_target_candidate_creation(self):
        """Test TargetCandidate dataclass creation."""
        candidate = TargetCandidate(
            position=(5, 3),
            delta_u_raw=2.5,
            distance=4,
            kind='resource',
            aux={'resource_type': 'A'}
        )
        
        assert candidate.position == (5, 3)
        assert candidate.delta_u_raw == 2.5
        assert candidate.distance == 4
        assert candidate.kind == 'resource'
        assert candidate.aux == {'resource_type': 'A'}


class TestResourceTargetStrategy:
    def test_select_target_no_resources(self):
        """Test target selection with no resources available."""
        strategy = ResourceTargetStrategy()
        grid = Mock()
        grid.iter_resources_sorted.return_value = []
        grid.iter_resources.return_value = []
        
        preference = Mock()
        preference.utility.return_value = 1.0
        
        result = strategy.select_target(
            agent_pos=(5, 5),
            current_bundle=(1.0, 1.0),
            preference=preference,
            grid=grid
        )
        
        assert result is None

    def test_select_target_with_resources(self):
        """Test target selection with available resources."""
        strategy = ResourceTargetStrategy()
        
        # Mock grid with resources
        grid = Mock()
        grid.iter_resources_sorted.return_value = [
            (3, 3, 'A'),  # Distance 4, should be selected
            (7, 7, 'B'),  # Distance 4, but lower priority due to position
        ]
        grid.iter_resources.return_value = [
            (3, 3, 'A'),
            (7, 7, 'B'),
        ]
        
        # Mock preference that gives higher utility for good1
        preference = Mock()
        def mock_utility(bundle):
            g1, g2 = bundle
            return g1 * 2.0 + g2 * 1.0  # Prefer good1
        preference.utility.side_effect = mock_utility
        
        result = strategy.select_target(
            agent_pos=(5, 5),
            current_bundle=(1.0, 1.0),
            preference=preference,
            grid=grid
        )
        
        assert result is not None
        assert result.position == (3, 3)  # Should select closer resource
        assert result.kind == 'resource'
        assert result.aux['resource_type'] == 'A'
        assert result.distance == 4

    def test_select_target_distance_filtering(self):
        """Test that resources beyond perception radius are filtered out."""
        strategy = ResourceTargetStrategy()
        
        # Mock grid with resources beyond perception radius
        grid = Mock()
        grid.iter_resources_sorted.return_value = [
            (20, 20, 'A'),  # Distance 30, beyond perception radius (8)
        ]
        grid.iter_resources.return_value = [
            (20, 20, 'A'),
        ]
        
        preference = Mock()
        preference.utility.return_value = 1.0
        
        result = strategy.select_target(
            agent_pos=(5, 5),
            current_bundle=(1.0, 1.0),
            preference=preference,
            grid=grid
        )
        
        assert result is None

    def test_select_target_negative_utility_filtering(self):
        """Test that resources with negative utility gain are filtered out."""
        strategy = ResourceTargetStrategy()
        
        # Mock grid with resources
        grid = Mock()
        grid.iter_resources_sorted.return_value = [
            (3, 3, 'A'),  # Should be filtered out due to negative utility
        ]
        grid.iter_resources.return_value = [
            (3, 3, 'A'),
        ]
        
        # Mock preference that gives lower utility for additional good1
        preference = Mock()
        def mock_utility(bundle):
            g1, g2 = bundle
            if g1 > 1.0:  # Additional good1 reduces utility
                return 0.5
            return 1.0
        preference.utility.side_effect = mock_utility
        
        result = strategy.select_target(
            agent_pos=(5, 5),
            current_bundle=(1.0, 1.0),
            preference=preference,
            grid=grid
        )
        
        assert result is None

    def test_select_target_deterministic_ordering(self):
        """Test that target selection uses deterministic ordering for tie-breaking."""
        strategy = ResourceTargetStrategy()
        
        # Mock grid with resources at same distance and utility
        grid = Mock()
        grid.iter_resources_sorted.return_value = [
            (7, 3, 'A'),  # Same distance, higher x,y
            (3, 7, 'A'),  # Same distance, lower x,y (should be selected)
        ]
        grid.iter_resources.return_value = [
            (7, 3, 'A'),
            (3, 7, 'A'),
        ]
        
        # Mock preference that gives positive utility gain
        preference = Mock()
        def mock_utility(bundle):
            g1, g2 = bundle
            return g1 * 2.0 + g2 * 1.0
        preference.utility.side_effect = mock_utility
        
        result = strategy.select_target(
            agent_pos=(5, 5),
            current_bundle=(1.0, 1.0),
            preference=preference,
            grid=grid
        )
        
        assert result is not None
        assert result.position == (3, 7)  # Should select lexicographically first

    def test_calculate_delta_utility(self):
        """Test utility calculation for resource collection."""
        strategy = ResourceTargetStrategy()
        
        preference = Mock()
        def mock_utility(bundle):
            g1, g2 = bundle
            return g1 * 2.0 + g2 * 1.0
        preference.utility.side_effect = mock_utility
        
        # Test good1 collection
        delta_u = strategy._calculate_delta_utility((1.0, 1.0), 'A', preference)
        assert delta_u == 2.0  # (2*2 + 1*1) - (2*1 + 1*1) = 5 - 3 = 2
        
        # Test good2 collection
        delta_u = strategy._calculate_delta_utility((1.0, 1.0), 'B', preference)
        assert delta_u == 1.0  # (2*1 + 1*2) - (2*1 + 1*1) = 4 - 3 = 1

    def test_calculate_delta_utility_epsilon_augmentation(self):
        """Test epsilon augmentation for zero-bundle edge cases."""
        strategy = ResourceTargetStrategy()
        
        preference = Mock()
        def mock_utility(bundle):
            g1, g2 = bundle
            return g1 * 2.0 + g2 * 1.0
        preference.utility.side_effect = mock_utility
        
        # Test with zero bundle - should use epsilon augmentation
        delta_u = strategy._calculate_delta_utility((0.0, 0.0), 'A', preference)
        # Should be positive due to epsilon augmentation
        assert delta_u > 0.0

    def test_select_target_epsilon_augmentation(self):
        """Test epsilon augmentation in target selection."""
        strategy = ResourceTargetStrategy()
        
        grid = Mock()
        grid.iter_resources_sorted.return_value = [
            (3, 3, 'A'),
        ]
        grid.iter_resources.return_value = [
            (3, 3, 'A'),
        ]
        
        preference = Mock()
        def mock_utility(bundle):
            g1, g2 = bundle
            # Return 0 for zero bundles, positive for non-zero
            if g1 == 0.0 or g2 == 0.0:
                return 0.0
            return g1 * 2.0 + g2 * 1.0
        preference.utility.side_effect = mock_utility
        
        # Test with zero bundle - should still find targets due to epsilon
        result = strategy.select_target(
            agent_pos=(5, 5),
            current_bundle=(0.0, 0.0),
            preference=preference,
            grid=grid
        )
        
        assert result is not None
        assert result.position == (3, 3)
