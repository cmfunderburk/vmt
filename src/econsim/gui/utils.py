"""GUI utility functions for VMT EconSim.

Simple formatting functions extracted from legacy debug_logger
to support GUI components after GUILogger elimination.
"""

def format_agent_id(agent_id: int) -> str:
    """Format agent ID with consistent zero-padded format.
    
    Args:
        agent_id: Integer agent identifier
        
    Returns:
        Formatted agent string like "A000", "A001", "A002", etc.
        
    Examples:
        >>> format_agent_id(1)
        'A001'
        >>> format_agent_id(42)
        'A042'
        >>> format_agent_id(123)
        'A123'
    """
    return f"A{agent_id:03d}"


def format_delta(value: float) -> str:
    """Format delta values with consistent sign notation and near-zero handling.
    
    Args:
        value: Numeric delta value (utility change, etc.)
        
    Returns:
        Formatted delta string with consistent sign notation
        
    Behavior:
        - Eliminates `+-` artifacts by normalizing the value first
        - Rounds very small values (< 1e-6) to exactly 0.0 to avoid noise
        - Preserves small but meaningful changes (≥ 0.001) for educational clarity
        - Uses 3 decimal places to capture micro-utility changes in trading
        - Uses consistent `+X.XXX` / `-X.XXX` formatting
        
    Examples:
        >>> format_delta(1.234)
        '+1.234'
        >>> format_delta(-0.456)
        '-0.456'
        >>> format_delta(0.0000001)  # Very small rounds to zero
        '+0.000'
        >>> format_delta(0.001)  # Small but meaningful preserved
        '+0.001'
        >>> format_delta(0.0)
        '+0.000'
    """
    # Handle very small values by rounding to zero (avoid floating point noise)
    if abs(value) < 1e-6:
        value = 0.0
    
    # Format with consistent sign notation (3 decimal places for utility precision)
    return f"{value:+.3f}"


__all__ = ["format_agent_id", "format_delta"]