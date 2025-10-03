"""
Phase Management - Centralized phase transition logic.

Handles the standard 6-phase educational testing schedule.
"""

import os
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class PhaseDefinition:
    """Definition of a single test phase."""
    number: int
    turn_start: int
    turn_end: int
    description: str
    forage_enabled: bool
    trade_enabled: bool
    
    @property
    def duration(self) -> int:
        """Get the duration of this phase in turns."""
        return self.turn_end - self.turn_start + 1
    
    def __post_init__(self):
        """Validate phase definition."""
        if self.turn_start < 1:
            raise ValueError(f"Phase {self.number}: turn_start must be >= 1")
        if self.turn_end < self.turn_start:
            raise ValueError(f"Phase {self.number}: turn_end must be >= turn_start")


@dataclass
class PhaseBehavior:
    """Represents the behavior settings for a phase."""
    name: str
    description: str
    forage_enabled: bool
    trade_enabled: bool
    
    @classmethod
    def both_enabled(cls) -> 'PhaseBehavior':
        return cls("Both enabled", "Both foraging and exchange enabled", True, True)
    
    @classmethod
    def forage_only(cls) -> 'PhaseBehavior':
        return cls("Forage only", "Only foraging enabled", True, False)
        
    @classmethod
    def exchange_only(cls) -> 'PhaseBehavior':
        return cls("Exchange only", "Only exchange enabled", False, True)
        
    @classmethod
    def both_disabled(cls) -> 'PhaseBehavior':
        return cls("Both disabled", "Both systems disabled - agents should idle", False, False)


@dataclass  
class PhaseTransition:
    """Result of a phase transition check."""
    new_phase: int
    description: str
    forage_enabled: bool
    trade_enabled: bool


class PhaseManager:
    """Handles phase transitions and environment configuration."""
    
    def __init__(self, phases: List[PhaseDefinition]):
        self.phases = {p.number: p for p in phases}
        self._validate_phases()
        
    def _validate_phases(self):
        """Validate that phases form a continuous sequence without gaps or overlaps."""
        if not self.phases:
            raise ValueError("At least one phase must be defined")
            
        sorted_phases = sorted(self.phases.values(), key=lambda p: p.turn_start)
        
        for i, phase in enumerate(sorted_phases):
            if i == 0:
                if phase.turn_start != 1:
                    raise ValueError(f"First phase must start at turn 1, got {phase.turn_start}")
            else:
                prev_phase = sorted_phases[i-1]
                if phase.turn_start != prev_phase.turn_end + 1:
                    raise ValueError(f"Phase {phase.number} starts at {phase.turn_start}, expected {prev_phase.turn_end + 1}")
        
    @classmethod
    def create_standard_phases(cls) -> 'PhaseManager':
        """Create the standard 6-phase schedule used by most tests."""
        phases = [
            PhaseDefinition(1, 1, 200, "Both foraging and exchange enabled", True, True),
            PhaseDefinition(2, 201, 400, "Only foraging enabled", True, False),
            PhaseDefinition(3, 401, 600, "Only exchange enabled", False, True),
            PhaseDefinition(4, 601, 650, "Both disabled - agents should idle", False, False),
            PhaseDefinition(5, 651, 850, "Both enabled again", True, True),
            PhaseDefinition(6, 851, 900, "Final disabled phase", False, False)
        ]
        return cls(phases)
    
    @classmethod
    def create_custom_phases(cls, phase_configs: List[tuple[PhaseBehavior, int]]) -> 'PhaseManager':
        """Create a custom phase schedule from behavior-duration pairs.
        
        Args:
            phase_configs: List of (PhaseBehavior, duration_in_turns) tuples
            
        Returns:
            PhaseManager with custom phase schedule
            
        Example:
            PhaseManager.create_custom_phases([
                (PhaseBehavior.forage_only(), 100),
                (PhaseBehavior.both_enabled(), 200),
                (PhaseBehavior.both_disabled(), 50)
            ])
        """
        phases = []
        current_turn = 1
        
        for phase_num, (behavior, duration) in enumerate(phase_configs, 1):
            turn_end = current_turn + duration - 1
            phase = PhaseDefinition(
                number=phase_num,
                turn_start=current_turn,
                turn_end=turn_end,
                description=behavior.description,
                forage_enabled=behavior.forage_enabled,
                trade_enabled=behavior.trade_enabled
            )
            phases.append(phase)
            current_turn = turn_end + 1
            
        return cls(phases)
    
    @classmethod 
    def create_simple_phases(cls, **kwargs) -> 'PhaseManager':
        """Create a simple phase schedule using keyword arguments.
        
        Args:
            forage_only: Duration for forage-only phase (default: 0)
            both_enabled: Duration for both-enabled phase (default: 200) 
            exchange_only: Duration for exchange-only phase (default: 0)
            both_disabled: Duration for both-disabled phase (default: 0)
            
        Returns:
            PhaseManager with requested phases (skipping zero-duration phases)
            
        Example:
            # Simple test: 150 turns forage, 100 turns both, 50 turns idle
            PhaseManager.create_simple_phases(
                forage_only=150, 
                both_enabled=100, 
                both_disabled=50
            )
        """
        phase_sequence = [
            (PhaseBehavior.forage_only(), kwargs.get('forage_only', 0)),
            (PhaseBehavior.both_enabled(), kwargs.get('both_enabled', 200)),
            (PhaseBehavior.exchange_only(), kwargs.get('exchange_only', 0)),
            (PhaseBehavior.both_disabled(), kwargs.get('both_disabled', 0)),
        ]
        
        # Filter out zero-duration phases
        active_phases = [(behavior, duration) for behavior, duration in phase_sequence if duration > 0]
        
        if not active_phases:
            # Default to 200 turns of both enabled if nothing specified
            active_phases = [(PhaseBehavior.both_enabled(), 200)]
            
        return cls.create_custom_phases(active_phases)
        
    def check_transition(self, current_turn: int, current_phase: int) -> Optional[PhaseTransition]:
        """Check if we need to transition to a new phase."""
        for phase_num, phase_def in self.phases.items():
            if (current_turn == phase_def.turn_start and 
                current_phase == phase_num - 1):
                
                # Configure environment variables
                os.environ['ECONSIM_FORAGE_ENABLED'] = '1' if phase_def.forage_enabled else '0'
                os.environ['ECONSIM_TRADE_DRAFT'] = '1' if phase_def.trade_enabled else '0'
                os.environ['ECONSIM_TRADE_EXEC'] = '1' if phase_def.trade_enabled else '0'
                
                # Phase transition logging now handled by base_test.py via observer system
                # Removed console print to avoid duplication with observer logging
                
                return PhaseTransition(
                    new_phase=phase_num,
                    description=phase_def.description,
                    forage_enabled=phase_def.forage_enabled,
                    trade_enabled=phase_def.trade_enabled
                )
        
        return None
        
    def get_phase_description(self, phase_number: int) -> str:
        """Get description for a phase number."""
        phase = self.phases.get(phase_number)
        return phase.description if phase else f"Phase {phase_number}"
        
    def is_test_complete(self, current_turn: int) -> bool:
        """Check if all phases are complete."""
        max_turn = max(p.turn_end for p in self.phases.values())
        return current_turn >= max_turn
    
    def get_total_turns(self) -> int:
        """Get the total number of turns for all phases."""
        return max(p.turn_end for p in self.phases.values())
    
    def get_phase_count(self) -> int:
        """Get the number of phases."""
        return len(self.phases)
    
    def get_phase_summary(self) -> str:
        """Get a human-readable summary of all phases."""
        sorted_phases = sorted(self.phases.values(), key=lambda p: p.turn_start)
        summary_parts = []
        
        for phase in sorted_phases:
            behavior_name = "Both" if phase.forage_enabled and phase.trade_enabled else \
                           "Forage" if phase.forage_enabled else \
                           "Exchange" if phase.trade_enabled else \
                           "Idle"
            summary_parts.append(f"{behavior_name} ({phase.turn_start}-{phase.turn_end})")
        
        return " → ".join(summary_parts)
    
    def get_current_phase_info(self, current_turn: int) -> Optional[PhaseDefinition]:
        """Get information about the current phase for a given turn."""
        for phase in self.phases.values():
            if phase.turn_start <= current_turn <= phase.turn_end:
                return phase
        return None