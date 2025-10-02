"""Target selection component for agent decision-making."""

from .base import TargetSelectionStrategy, TargetCandidate
from .resource_selection import ResourceTargetStrategy

__all__ = ["TargetSelectionStrategy", "TargetCandidate", "ResourceTargetStrategy"]
