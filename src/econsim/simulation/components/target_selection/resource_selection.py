"""Resource target selection strategy."""

from typing import Optional, Tuple, TYPE_CHECKING
from .base import TargetSelectionStrategy, TargetCandidate
from ...constants import default_PERCEPTION_RADIUS, EPSILON_UTILITY
from ..movement.utils import manhattan_distance

if TYPE_CHECKING:
    from ...grid import Grid
    from ....preferences.base import Preference

Position = tuple[int, int]

# A→good1, B→good2
RESOURCE_TYPE_TO_GOOD = {
    "A": "good1",
    "B": "good2",
}

class ResourceTargetStrategy(TargetSelectionStrategy):
    """Strategy for selecting resource targets based on utility maximization."""
    
    def select_target(
        self,
        agent_pos: Position,
        current_bundle: Tuple[float, float],
        preference: 'Preference',
        grid: 'Grid',
        **kwargs
    ) -> Optional[TargetCandidate]:
        """Find highest utility resource within perception radius.
        
        Uses canonical priority tuple: (-ΔU_adj, distance, x, y) for deterministic
        tie-breaking. Applies distance discount to utility gains.
        """
        best_candidate = None
        best_priority = None  # (-delta_u_adj, distance, x, y)
        
        # Apply epsilon augmentation for baseline utility evaluation
        if current_bundle[0] == 0.0 or current_bundle[1] == 0.0:
            bundle = (current_bundle[0] + EPSILON_UTILITY, current_bundle[1] + EPSILON_UTILITY)
        else:
            bundle = current_bundle
        base_u = preference.utility(bundle)
        
        # Deterministic iteration
        iterator = getattr(grid, 'iter_resources_sorted', grid.iter_resources)()
        
        for rx, ry, rtype in iterator:
            distance = manhattan_distance(agent_pos[0], agent_pos[1], rx, ry)
            if distance > default_PERCEPTION_RADIUS:
                continue
            
            # Calculate utility gain
            delta_u = self._calculate_delta_utility(bundle, rtype, preference)
            
            if delta_u <= 0.0:
                continue
                
            # Apply distance discount
            delta_u_adj = delta_u / (1 + 0.1 * distance * distance)
            
            # Canonical priority tuple
            priority = (-delta_u_adj, distance, rx, ry)
            
            if best_priority is None or priority < best_priority:
                best_priority = priority
                best_candidate = TargetCandidate(
                    position=(rx, ry),
                    delta_u_raw=delta_u,
                    distance=distance,
                    kind='resource',
                    aux={'resource_type': rtype}
                )
        
        return best_candidate
    
    def _calculate_delta_utility(self, bundle: Tuple[float, float], rtype: str, pref: 'Preference') -> float:
        """Calculate utility gain from collecting resource."""
        good = RESOURCE_TYPE_TO_GOOD.get(rtype)
        if not good:
            return 0.0
            
        if good == "good1":
            test_bundle = (bundle[0] + 1.0, bundle[1])
        else:
            test_bundle = (bundle[0], bundle[1] + 1.0)
            
        # Apply epsilon augmentation for test bundle if needed
        if test_bundle[0] == 0.0 or test_bundle[1] == 0.0:
            tb0 = test_bundle[0] if test_bundle[0] > 0 else EPSILON_UTILITY
            tb1 = test_bundle[1] if test_bundle[1] > 0 else EPSILON_UTILITY
            test_bundle = (tb0, tb1)
            
        new_u = pref.utility(test_bundle)
        base_u = pref.utility(bundle)
        return new_u - base_u
