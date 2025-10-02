"""Base classes for target selection strategies."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from ...grid import Grid
    from ....preferences.base import Preference

Position = tuple[int, int]

@dataclass
class TargetCandidate:
    """Structured result from target selection."""
    position: Position
    delta_u_raw: float
    distance: int
    kind: str  # 'resource' or 'pairing'
    aux: dict  # Optional metadata

class TargetSelectionStrategy(ABC):
    """Base class for agent target selection strategies."""
    
    @abstractmethod
    def select_target(
        self,
        agent_pos: Position,
        current_bundle: Tuple[float, float],
        preference: 'Preference',
        grid: 'Grid',
        **kwargs
    ) -> Optional[TargetCandidate]:
        """Select the best target for the agent."""
        pass
