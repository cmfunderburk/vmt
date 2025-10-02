"""Feature flags for agent refactor rollout."""

import os
from typing import Dict

def get_refactor_flags() -> Dict[str, bool]:
    """Get current refactor feature flag values."""
    return {
        # All refactor flags have been removed - components are now permanent
    }

def is_refactor_enabled(component: str) -> bool:
    """Check if specific refactor component is enabled."""
    flags = get_refactor_flags()
    return flags.get(component, False)
