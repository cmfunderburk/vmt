"""Unit tests for AgentMovement component."""

import pytest
import random
from unittest.mock import Mock
from econsim.simulation.components.movement import AgentMovement, manhattan_distance, calculate_meeting_point

class TestAgentMovement:
    def test_move_random_within_bounds(self):
        movement = AgentMovement(agent_id=1)
        grid = Mock(width=10, height=10)
        rng = random.Random(42)
        
        pos = movement.move_random((5, 5), grid, rng)
        assert 0 <= pos[0] < 10
        assert 0 <= pos[1] < 10
    
    def test_move_random_boundary_handling(self):
        movement = AgentMovement(agent_id=1)
        grid = Mock(width=10, height=10)
        rng = random.Random(42)
        
        # Test corner position - should stay in bounds
        pos = movement.move_random((0, 0), grid, rng)
        assert 0 <= pos[0] < 10
        assert 0 <= pos[1] < 10
        
        # Test edge position
        pos = movement.move_random((9, 9), grid, rng)
        assert 0 <= pos[0] < 10
        assert 0 <= pos[1] < 10
    
    def test_move_toward_target_horizontal_priority(self):
        movement = AgentMovement(agent_id=1)
        pos = movement.move_toward_target((2, 2), (5, 3))
        assert pos == (3, 2)  # Horizontal first since abs(3) > abs(1)
    
    def test_move_toward_target_vertical_movement(self):
        movement = AgentMovement(agent_id=1)
        pos = movement.move_toward_target((2, 2), (2, 5))
        assert pos == (2, 3)  # Only vertical movement needed
    
    def test_move_toward_target_already_at_target(self):
        movement = AgentMovement(agent_id=1)
        pos = movement.move_toward_target((5, 5), (5, 5))
        assert pos == (5, 5)  # No movement when already at target
    
    def test_move_toward_meeting_point(self):
        movement = AgentMovement(agent_id=1)
        pos = movement.move_toward_meeting_point((1, 1), (4, 4))
        assert pos == (1, 2)  # Vertical movement when abs(dx) == abs(dy)
    
    def test_deterministic_movement_sequence(self):
        movement = AgentMovement(agent_id=1)
        grid = Mock(width=10, height=10)
        
        rng1 = random.Random(12345)
        rng2 = random.Random(12345)
        
        pos1 = pos2 = (5, 5)
        for _ in range(10):
            pos1 = movement.move_random(pos1, grid, rng1)
            pos2 = movement.move_random(pos2, grid, rng2)
            assert pos1 == pos2, f"Determinism broken: {pos1} != {pos2}"

class TestMovementUtils:
    def test_manhattan_distance(self):
        assert manhattan_distance(0, 0, 3, 4) == 7
        assert manhattan_distance(1, 1, 1, 1) == 0
        assert manhattan_distance(-1, -1, 1, 1) == 4
    
    def test_calculate_meeting_point(self):
        assert calculate_meeting_point((0, 0), (4, 4)) == (2, 2)
        assert calculate_meeting_point((1, 3), (5, 7)) == (3, 5)
        assert calculate_meeting_point((0, 0), (1, 1)) == (0, 0)  # Integer division
