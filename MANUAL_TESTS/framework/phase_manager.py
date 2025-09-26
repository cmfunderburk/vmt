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
        
    def check_transition(self, current_turn: int, current_phase: int) -> Optional[PhaseTransition]:
        """Check if we need to transition to a new phase."""
        for phase_num, phase_def in self.phases.items():
            if (current_turn == phase_def.turn_start and 
                current_phase == phase_num - 1):
                
                # Configure environment variables
                os.environ['ECONSIM_FORAGE_ENABLED'] = '1' if phase_def.forage_enabled else '0'
                os.environ['ECONSIM_TRADE_DRAFT'] = '1' if phase_def.trade_enabled else '0'
                os.environ['ECONSIM_TRADE_EXEC'] = '1' if phase_def.trade_enabled else '0'
                
                # Log transition using centralized debug logger
                try:
                    # Add src to Python path if needed
                    import sys
                    import os as path_os
                    src_path = path_os.path.join(path_os.path.dirname(path_os.path.abspath(__file__)), '..', '..', 'src')
                    if src_path not in sys.path:
                        sys.path.insert(0, src_path)
                    
                    from econsim.gui.debug_logger import log_phase_transition, log_comprehensive
                    log_phase_transition(phase_num, current_turn, phase_def.description)
                    log_comprehensive(f"PHASE TRANSITION: {current_phase} -> {phase_num} at turn {current_turn}", current_turn)
                except ImportError:
                    # Fallback if debug logger not available
                    print(f"PHASE TRANSITION: {current_phase} -> {phase_num} at turn {current_turn}")
                
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