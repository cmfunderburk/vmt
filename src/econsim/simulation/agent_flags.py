"""Feature flags for agent refactor rollout."""

import os
from typing import Dict

def get_refactor_flags() -> Dict[str, bool]:
    """Get current refactor feature flag values."""
    return {
        "events": os.environ.get("ECONSIM_AGENT_EVENTS_REFACTOR", "0") == "1",
        "inventory": os.environ.get("ECONSIM_AGENT_INVENTORY_REFACTOR", "0") == "1",
        "trading": os.environ.get("ECONSIM_AGENT_TRADING_REFACTOR", "0") == "1",
        "selection": os.environ.get("ECONSIM_AGENT_SELECTION_REFACTOR", "0") == "1",
        "state_machine": os.environ.get("ECONSIM_AGENT_STATE_MACHINE_REFACTOR", "0") == "1",
    }

def is_refactor_enabled(component: str) -> bool:
    """Check if specific refactor component is enabled."""
    flags = get_refactor_flags()
    return flags.get(component, False)
