"""
Agent inventory management with dual storage system.

CRITICAL INVARIANT: This component MUST mutate self.carrying and 
self.home_inventory dictionaries IN PLACE. Never rebind these references.
The Agent class exposes these dicts via aliases for backward compatibility,
and rebinding would break the alias connection.

Correct:   self.carrying["good1"] = 0
Incorrect: self.carrying = {"good1": 0, "good2": 0}

HASH CONTRACT: 
- carrying["good1"], carrying["good2"] participate in determinism hash
- home_inventory["good1"], home_inventory["good2"] participate in determinism hash
- This component instance is excluded from hash
"""

from __future__ import annotations
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ....preferences.base import Preference

class AgentInventory:
    """Manages agent's carrying and home inventory with utility calculations."""
    
    def __init__(self, preference: 'Preference'):
        # Create dicts ONCE - NEVER rebind these
        self.carrying: Dict[str, int] = {"good1": 0, "good2": 0}
        self.home_inventory: Dict[str, int] = {"good1": 0, "good2": 0}
        self.preference = preference
    
    @property
    def inventory(self) -> Dict[str, int]:
        """Backward compatibility alias for carrying inventory."""
        return self.carrying
    
    def carrying_total(self) -> int:
        """Return total number of goods currently being carried."""
        return sum(self.carrying.values())
    
    def current_bundle(self) -> tuple[float, float]:
        """Get current bundle (good1, good2) from total wealth."""
        total_good1 = float(self.carrying["good1"] + self.home_inventory["good1"])
        total_good2 = float(self.carrying["good2"] + self.home_inventory["good2"])
        return total_good1, total_good2
    
    def current_utility(self) -> float:
        """Calculate current utility from total wealth."""
        from ...constants import EPSILON_UTILITY
        raw_bundle = self.current_bundle()
        # Apply epsilon augmentation for consistent evaluation
        if raw_bundle[0] == 0.0 or raw_bundle[1] == 0.0:
            bundle = (raw_bundle[0] + EPSILON_UTILITY, raw_bundle[1] + EPSILON_UTILITY)
        else:
            bundle = raw_bundle
        return self.preference.utility(bundle)
    
    def deposit_all(self) -> bool:
        """Move all carried goods into home inventory. Returns True if any deposited."""
        moved = False
        # ✅ CRITICAL: In-place mutation only
        for key in list(self.carrying.keys()):
            if self.carrying[key] > 0:
                self.home_inventory[key] += self.carrying[key]
                self.carrying[key] = 0
                moved = True
        return moved
    
    def withdraw_all(self) -> bool:
        """Move all home inventory into carrying. Returns True if withdrawn."""
        moved = False
        # ✅ CRITICAL: In-place mutation only
        for key in list(self.home_inventory.keys()):
            if self.home_inventory[key] > 0:
                self.carrying[key] += self.home_inventory[key]
                self.home_inventory[key] = 0
                moved = True
        return moved
    
    def collect_resource(self, resource_type: str) -> None:
        """Add resource to carrying inventory."""
        # ✅ CRITICAL: In-place mutation only
        if resource_type == "A":
            self.carrying["good1"] += 1
        elif resource_type == "B":
            self.carrying["good2"] += 1
    
    def total_inventory(self) -> Dict[str, int]:
        """Return combined carrying + home inventory without mutation."""
        # Check if both inventories are effectively empty (all zeros)
        carrying_total = sum(self.carrying.values())
        home_total = sum(self.home_inventory.values())
        if carrying_total == 0 and home_total == 0:
            return {}
        
        # Copy home first, then overlay carrying counts
        combined: Dict[str, int] = dict(self.home_inventory)
        for k, v in self.carrying.items():
            if v:
                combined[k] = combined.get(k, 0) + v
        return combined
