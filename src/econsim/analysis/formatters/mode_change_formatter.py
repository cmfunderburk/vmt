"""
Mode Change Event Formatter: GUI display formatting for agent mode transitions.

This module provides specialized formatting for mode change events, converting raw
mode transition dictionaries into various GUI-friendly formats while maintaining
complete separation from the raw data storage layer.

Key Features:
- Human-readable mode transition summaries
- Transition pattern analysis and classification
- Mode duration and frequency tracking
- Behavioral analysis for agent decision patterns
"""

from typing import Dict, List, Any, Union, Tuple
from .base_formatter import EventFormatter


class ModeChangeEventFormatter(EventFormatter):
    """
    Formatter for mode change events from the simulation.
    
    Handles conversion of raw mode change dictionaries (from RawDataObserver) into
    GUI-friendly formats for display, analysis, and behavioral pattern tracking.
    
    Raw Mode Change Event Schema:
    {
        'type': 'mode_change',
        'step': int,
        'agent_id': int,
        'old_mode': str,
        'new_mode': str,
        'reason': str
    }
    """
    
    # Common mode mappings for display
    MODE_DISPLAY_NAMES = {
        'idle': 'Idle',
        'foraging': 'Foraging',
        'trading': 'Trading',
        'moving': 'Moving',
        'waiting': 'Waiting',
        'exploring': 'Exploring',
        'depositing': 'Depositing',
        'seeking_partner': 'Seeking Partner',
        'negotiating': 'Negotiating'
    }
    
    # Transition classifications
    TRANSITION_PATTERNS = {
        ('idle', 'foraging'): 'activation',
        ('foraging', 'idle'): 'deactivation', 
        ('idle', 'trading'): 'direct_engagement',
        ('foraging', 'trading'): 'resource_to_trade',
        ('trading', 'foraging'): 'trade_to_resource',
        ('moving', 'foraging'): 'arrive_and_forage',
        ('moving', 'trading'): 'arrive_and_trade',
        ('trading', 'moving'): 'trade_complete_move',
        ('foraging', 'moving'): 'forage_complete_move'
    }
    
    def to_display_text(self, raw_event: Dict[str, Any]) -> str:
        """
        Convert raw mode change event to human-readable display text.
        
        Args:
            raw_event: Raw mode change dictionary from RawDataObserver
            
        Returns:
            Concise, human-readable mode transition summary
            
        Example:
            "Agent 3 changed from Foraging to Trading (found partner)"
        """
        try:
            agent_id = self._safe_get(raw_event, 'agent_id', '?')
            old_mode = self._safe_get(raw_event, 'old_mode', 'unknown')
            new_mode = self._safe_get(raw_event, 'new_mode', 'unknown')
            reason = self._safe_get(raw_event, 'reason', '')
            
            # Format mode names for display
            old_display = self._format_mode_name(old_mode)
            new_display = self._format_mode_name(new_mode)
            
            base_text = f"Agent {agent_id} changed from {old_display} to {new_display}"
            
            if reason and reason != 'unknown':
                # Clean up reason text for display
                clean_reason = self._format_reason_text(reason)
                return f"{base_text} ({clean_reason})"
            else:
                return base_text
                
        except Exception as e:
            return self._handle_formatting_error(raw_event, e, 'to_display_text')
    
    def to_analysis_data(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw mode change event to analysis-friendly structure.
        
        Args:
            raw_event: Raw mode change dictionary from RawDataObserver
            
        Returns:
            Dictionary with enriched analysis data
            
        Example:
            {
                'agent_id': 3,
                'transition': 'foraging_to_trading',
                'transition_type': 'resource_to_trade',
                'step': 25,
                'modes': {'from': 'foraging', 'to': 'trading'},
                'reason_category': 'partner_found',
                'behavioral_pattern': 'productive_transition'
            }
        """
        try:
            agent_id = raw_event.get('agent_id', -1)
            old_mode = raw_event.get('old_mode', '')
            new_mode = raw_event.get('new_mode', '')
            reason = raw_event.get('reason', '')
            step = raw_event.get('step', -1)
            
            # Create transition identifier
            transition = f"{old_mode}_to_{new_mode}" if old_mode and new_mode else 'unknown_transition'
            
            # Classify transition type
            transition_type = self._classify_transition((old_mode, new_mode))
            
            # Categorize reason
            reason_category = self._categorize_reason(reason)
            
            # Analyze behavioral pattern
            behavioral_pattern = self._analyze_behavioral_pattern(old_mode, new_mode, reason)
            
            return {
                'agent_id': agent_id,
                'transition': transition,
                'transition_type': transition_type,
                'step': step,
                'modes': {
                    'from': old_mode,
                    'to': new_mode
                },
                'reason_category': reason_category,
                'reason_text': reason,
                'behavioral_pattern': behavioral_pattern,
                'is_productive': self._is_productive_transition(old_mode, new_mode),
                'activity_level': self._assess_activity_level(new_mode)
            }
            
        except Exception as e:
            return {
                'error': f"Analysis formatting error: {e}",
                'raw_event': raw_event
            }
    
    def to_table_row(self, raw_event: Dict[str, Any]) -> List[Union[str, int, float]]:
        """
        Convert raw mode change event to table row format.
        
        Args:
            raw_event: Raw mode change dictionary from RawDataObserver
            
        Returns:
            List of values for table display: [Step, Type, Agent, Transition, Reason]
            
        Example:
            [25, "Mode Change", "Agent 3", "Foraging → Trading", "partner found"]
        """
        try:
            step = raw_event.get('step', -1)
            agent_id = self._safe_get(raw_event, 'agent_id', '?')
            old_mode = self._safe_get(raw_event, 'old_mode', '?')
            new_mode = self._safe_get(raw_event, 'new_mode', '?')
            reason = self._safe_get(raw_event, 'reason', '')
            
            # Format transition
            old_display = self._format_mode_name(old_mode)
            new_display = self._format_mode_name(new_mode)
            transition = f"{old_display} → {new_display}"
            
            # Clean reason for table display
            clean_reason = self._format_reason_text(reason)
            if len(clean_reason) > 20:  # Truncate long reasons for table
                clean_reason = clean_reason[:17] + "..."
            
            return [step, "Mode Change", f"Agent {agent_id}", transition, clean_reason]
            
        except Exception as e:
            step = raw_event.get('step', -1)
            return [step, "Mode Change", "[Error]", "[Error]", "[Error]"]
    
    def to_detailed_view(self, raw_event: Dict[str, Any]) -> Dict[str, str]:
        """
        Convert raw mode change event to detailed view format.
        
        Args:
            raw_event: Raw mode change dictionary from RawDataObserver
            
        Returns:
            Dictionary mapping field names to formatted display values
        """
        try:
            detailed = {}
            
            # Basic event info
            detailed['Event Type'] = 'Mode Change'
            detailed['Step'] = str(raw_event.get('step', 'Unknown'))
            detailed['Agent'] = self._format_agent_id(raw_event.get('agent_id', -1))
            
            # Mode transition details
            old_mode = raw_event.get('old_mode', 'Unknown')
            new_mode = raw_event.get('new_mode', 'Unknown')
            detailed['Previous Mode'] = self._format_mode_name(old_mode)
            detailed['New Mode'] = self._format_mode_name(new_mode)
            
            # Transition analysis
            transition_type = self._classify_transition((old_mode, new_mode))
            detailed['Transition Type'] = transition_type.replace('_', ' ').title()
            
            # Reason analysis
            reason = raw_event.get('reason', '')
            detailed['Reason'] = self._format_reason_text(reason) if reason else 'No reason specified'
            detailed['Reason Category'] = self._categorize_reason(reason).replace('_', ' ').title()
            
            # Behavioral analysis
            behavioral_pattern = self._analyze_behavioral_pattern(old_mode, new_mode, reason)
            detailed['Behavioral Pattern'] = behavioral_pattern.replace('_', ' ').title()
            
            is_productive = self._is_productive_transition(old_mode, new_mode)
            detailed['Productive Transition'] = 'Yes' if is_productive else 'No'
            
            activity_level = self._assess_activity_level(new_mode)
            detailed['Activity Level'] = activity_level.title()
            
            return detailed
            
        except Exception as e:
            return {
                'Event Type': 'Mode Change',
                'Error': f'Formatting error: {e}',
                'Raw Data': str(raw_event)
            }
    
    def get_table_headers(self) -> List[str]:
        """
        Get table column headers for mode change events.
        
        Returns:
            List of column header strings
        """
        return ["Step", "Event Type", "Agent", "Transition", "Reason"]
    
    def get_supported_event_type(self) -> str:
        """
        Get the event type this formatter supports.
        
        Returns:
            Event type string: 'mode_change'
        """
        return 'mode_change'
    
    # ============================================================================
    # MODE CHANGE SPECIFIC HELPER METHODS
    # ============================================================================
    
    def _format_mode_name(self, mode: str) -> str:
        """
        Format mode name for display.
        
        Args:
            mode: Raw mode string from simulation
            
        Returns:
            Human-readable mode name
        """
        return self.MODE_DISPLAY_NAMES.get(mode.lower(), mode.replace('_', ' ').title())
    
    def _format_reason_text(self, reason: str) -> str:
        """
        Format reason text for display.
        
        Args:
            reason: Raw reason string from simulation
            
        Returns:
            Cleaned reason text suitable for display
        """
        if not reason or reason.lower() in ['unknown', 'none', '']:
            return 'No specific reason'
        
        # Clean up common technical reason patterns
        clean_reason = reason.replace('_', ' ')
        clean_reason = clean_reason.replace('  ', ' ')
        
        # Handle common patterns
        if 'partner' in clean_reason.lower():
            return clean_reason.replace('found partner', 'found trading partner')
        elif 'resource' in clean_reason.lower():
            return clean_reason.replace('found resource', 'found resource to collect')
        elif 'inventory' in clean_reason.lower():
            return clean_reason.replace('inventory full', 'inventory is full')
        
        return clean_reason.strip()
    
    def _classify_transition(self, transition_tuple: Tuple[str, str]) -> str:
        """
        Classify the type of mode transition.
        
        Args:
            transition_tuple: (old_mode, new_mode) tuple
            
        Returns:
            Transition classification string
        """
        return self.TRANSITION_PATTERNS.get(transition_tuple, 'unclassified_transition')
    
    def _categorize_reason(self, reason: str) -> str:
        """
        Categorize the reason for mode change.
        
        Args:
            reason: Raw reason string
            
        Returns:
            Reason category string
        """
        if not reason:
            return 'unspecified'
        
        reason_lower = reason.lower()
        
        if 'partner' in reason_lower:
            return 'partner_related'
        elif 'resource' in reason_lower or 'forage' in reason_lower:
            return 'resource_related'
        elif 'inventory' in reason_lower or 'full' in reason_lower:
            return 'inventory_related'
        elif 'timeout' in reason_lower or 'wait' in reason_lower:
            return 'time_related'
        elif 'location' in reason_lower or 'move' in reason_lower:
            return 'location_related'
        elif 'decision' in reason_lower or 'choice' in reason_lower:
            return 'decision_based'
        else:
            return 'other'
    
    def _analyze_behavioral_pattern(self, old_mode: str, new_mode: str, reason: str) -> str:
        """
        Analyze the behavioral pattern represented by this transition.
        
        Args:
            old_mode: Previous mode
            new_mode: New mode
            reason: Reason for change
            
        Returns:
            Behavioral pattern classification
        """
        if old_mode == 'idle' and new_mode in ['foraging', 'trading']:
            return 'activation_pattern'
        elif old_mode in ['foraging', 'trading'] and new_mode == 'idle':
            return 'deactivation_pattern'
        elif old_mode == 'foraging' and new_mode == 'trading':
            return 'productive_transition'
        elif old_mode == 'trading' and new_mode == 'foraging':
            return 'resource_seeking'
        elif 'partner' in reason.lower():
            return 'social_interaction'
        elif 'resource' in reason.lower():
            return 'resource_driven'
        else:
            return 'general_transition'
    
    def _is_productive_transition(self, old_mode: str, new_mode: str) -> bool:
        """
        Determine if this is a productive transition (towards active behavior).
        
        Args:
            old_mode: Previous mode
            new_mode: New mode
            
        Returns:
            True if transition is towards more productive activity
        """
        productive_modes = {'foraging', 'trading', 'exploring', 'depositing'}
        idle_modes = {'idle', 'waiting'}
        
        old_productive = old_mode in productive_modes
        new_productive = new_mode in productive_modes
        
        # Transition from idle to productive
        if old_mode in idle_modes and new_mode in productive_modes:
            return True
        
        # Transition between productive modes (generally good)
        if old_productive and new_productive:
            return True
        
        # Transition to idle (generally less productive)
        if new_mode in idle_modes:
            return False
        
        return False
    
    def _assess_activity_level(self, mode: str) -> str:
        """
        Assess the activity level of a mode.
        
        Args:
            mode: Mode string
            
        Returns:
            Activity level: 'high', 'medium', 'low'
        """
        high_activity = {'trading', 'foraging', 'exploring', 'moving'}
        medium_activity = {'seeking_partner', 'negotiating', 'depositing'}
        
        if mode in high_activity:
            return 'high'
        elif mode in medium_activity:
            return 'medium'
        else:
            return 'low'
    
    def analyze_mode_patterns(self, raw_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze patterns across multiple mode change events.
        
        Args:
            raw_events: List of raw mode change dictionaries
            
        Returns:
            Dictionary with pattern analysis
        """
        if not raw_events:
            return {
                'total_transitions': 0,
                'unique_agents': 0,
                'most_common_transitions': [],
                'activity_patterns': {}
            }
        
        # Count transitions
        transition_counts = {}
        agent_transitions = {}
        reason_categories = {}
        
        for event in raw_events:
            agent_id = event.get('agent_id', -1)
            old_mode = event.get('old_mode', '')
            new_mode = event.get('new_mode', '')
            reason = event.get('reason', '')
            
            # Track transitions
            transition = f"{old_mode}_to_{new_mode}"
            transition_counts[transition] = transition_counts.get(transition, 0) + 1
            
            # Track per-agent patterns
            if agent_id not in agent_transitions:
                agent_transitions[agent_id] = []
            agent_transitions[agent_id].append(transition)
            
            # Track reason categories
            category = self._categorize_reason(reason)
            reason_categories[category] = reason_categories.get(category, 0) + 1
        
        # Find most common transitions
        sorted_transitions = sorted(transition_counts.items(), key=lambda x: x[1], reverse=True)
        most_common = sorted_transitions[:5]
        
        return {
            'total_transitions': len(raw_events),
            'unique_agents': len(agent_transitions),
            'most_common_transitions': most_common,
            'reason_distribution': reason_categories,
            'transitions_per_agent': {agent: len(transitions) 
                                    for agent, transitions in agent_transitions.items()},
            'average_transitions_per_agent': len(raw_events) / len(agent_transitions) if agent_transitions else 0
        }