"""Spatial utility functions."""

def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Calculate Manhattan distance between two points."""
    return abs(x1 - x2) + abs(y1 - y2)

def calculate_meeting_point(pos1: tuple[int, int], pos2: tuple[int, int]) -> tuple[int, int]:
    """Calculate midpoint between two positions for meeting."""
    x1, y1 = pos1
    x2, y2 = pos2
    return (x1 + x2) // 2, (y1 + y2) // 2
