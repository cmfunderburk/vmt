"""
Debug Log Event Formatter: GUI display formatting for debug log events.

This module provides specialized formatting for debug log events, converting raw
debug log dictionaries into various GUI-friendly formats while maintaining
complete separation from the raw data storage layer.

Key Features:
- Human-readable debug message formatting
- Severity classification and filtering
- Category-based organization and filtering
- Technical detail extraction and display
"""

from typing import Dict, List, Any, Union
from .base_formatter import EventFormatter


class DebugLogEventFormatter(EventFormatter):
    """
    Formatter for debug log events from the simulation.
    
    Handles conversion of raw debug log dictionaries (from RawDataObserver) into
    GUI-friendly formats for display, analysis, and debugging support.
    
    Raw Debug Log Event Schema:
    {
        'type': 'debug_log',
        'step': int,
        'category': str,  # TRADE, MODE, ECON, etc.
        'message': str,   # Technical message
        'agent_id': int   # -1 if not agent-specific
    }
    """
    
    # Category display mappings
    CATEGORY_DISPLAY_NAMES = {
        'trade': 'Trade Debug',
        'mode': 'Mode Change',
        'econ': 'Economics',
        'agent_mode': 'Agent Behavior',
        'resource': 'Resource Management',
        'movement': 'Agent Movement',
        'decision': 'Decision Making',
        'performance': 'Performance',
        'system': 'System'
    }
    
    # Severity classification based on message content
    SEVERITY_KEYWORDS = {
        'error': ['error', 'failed', 'exception', 'crash', 'critical'],
        'warning': ['warning', 'warn', 'deprecated', 'unexpected', 'invalid'],
        'info': ['info', 'initialized', 'started', 'completed', 'finished'],
        'debug': ['debug', 'trace', 'detailed', 'verbose', 'checking']
    }
    
    # Color coding for categories (for GUI display)
    CATEGORY_COLORS = {
        'trade': 'blue',
        'mode': 'green',
        'econ': 'purple',
        'agent_mode': 'orange',
        'resource': 'brown',
        'movement': 'cyan',
        'decision': 'magenta',
        'performance': 'red',
        'system': 'gray'
    }
    
    def to_display_text(self, raw_event: Dict[str, Any]) -> str:
        """
        Convert raw debug log event to human-readable display text.
        
        Args:
            raw_event: Raw debug log dictionary from RawDataObserver
            
        Returns:
            Formatted debug message for display
            
        Example:
            "[Trade] Agent 1: Delta utility calculation: seller=1.5, buyer=2.3"
        """
        try:
            category = self._safe_get(raw_event, 'category', 'debug')
            message = self._safe_get(raw_event, 'message', 'No message')
            agent_id = raw_event.get('agent_id', -1)
            
            # Format category for display
            category_display = self._format_category_name(category)
            
            # Clean up message
            clean_message = self._clean_debug_message(message)
            
            # Add agent context if applicable
            if agent_id >= 0:
                return f"[{category_display}] Agent {agent_id}: {clean_message}"
            else:
                return f"[{category_display}] {clean_message}"
                
        except Exception as e:
            return self._handle_formatting_error(raw_event, e, 'to_display_text')
    
    def to_analysis_data(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw debug log event to analysis-friendly structure.
        
        Args:
            raw_event: Raw debug log dictionary from RawDataObserver
            
        Returns:
            Dictionary with enriched analysis data
            
        Example:
            {
                'category': 'trade',
                'severity': 'debug',
                'agent_specific': True,
                'message_type': 'calculation_detail',
                'technical_level': 'high'
            }
        """
        try:
            category = raw_event.get('category', '')
            message = raw_event.get('message', '')
            agent_id = raw_event.get('agent_id', -1)
            step = raw_event.get('step', -1)
            
            # Classify message severity
            severity = self._classify_severity(message)
            
            # Determine message type
            message_type = self._classify_message_type(message)
            
            # Assess technical level
            technical_level = self._assess_technical_level(message)
            
            # Extract key information
            key_info = self._extract_key_information(message)
            
            return {
                'category': category,
                'category_display': self._format_category_name(category),
                'severity': severity,
                'message_type': message_type,
                'technical_level': technical_level,
                'agent_specific': agent_id >= 0,
                'agent_id': agent_id if agent_id >= 0 else None,
                'step': step,
                'message_length': len(message),
                'key_information': key_info,
                'raw_message': message,
                'color_hint': self.CATEGORY_COLORS.get(category, 'gray')
            }
            
        except Exception as e:
            return {
                'error': f"Analysis formatting error: {e}",
                'raw_event': raw_event
            }
    
    def to_table_row(self, raw_event: Dict[str, Any]) -> List[Union[str, int, float]]:
        """
        Convert raw debug log event to table row format.
        
        Args:
            raw_event: Raw debug log dictionary from RawDataObserver
            
        Returns:
            List of values for table display: [Step, Type, Category, Agent, Message]
            
        Example:
            [42, "Debug", "Trade", "Agent 1", "Delta utility calculation..."]
        """
        try:
            step = raw_event.get('step', -1)
            category = self._safe_get(raw_event, 'category', 'debug')
            agent_id = raw_event.get('agent_id', -1)
            message = self._safe_get(raw_event, 'message', 'No message')
            
            # Format for table display
            category_display = self._format_category_name(category)
            agent_display = f"Agent {agent_id}" if agent_id >= 0 else "System"
            
            # Truncate long messages for table
            display_message = self._truncate_for_table(message, max_length=50)
            
            return [step, "Debug", category_display, agent_display, display_message]
            
        except Exception as e:
            step = raw_event.get('step', -1)
            return [step, "Debug", "[Error]", "[Error]", "[Error]"]
    
    def to_detailed_view(self, raw_event: Dict[str, Any]) -> Dict[str, str]:
        """
        Convert raw debug log event to detailed view format.
        
        Args:
            raw_event: Raw debug log dictionary from RawDataObserver
            
        Returns:
            Dictionary mapping field names to formatted display values
        """
        try:
            detailed = {}
            
            # Basic event info
            detailed['Event Type'] = 'Debug Log'
            detailed['Step'] = str(raw_event.get('step', 'Unknown'))
            
            # Category and classification
            category = raw_event.get('category', 'unknown')
            detailed['Category'] = self._format_category_name(category)
            
            # Agent information
            agent_id = raw_event.get('agent_id', -1)
            detailed['Agent'] = self._format_agent_id(agent_id) if agent_id >= 0 else 'System-wide'
            
            # Message analysis
            message = raw_event.get('message', '')
            detailed['Message'] = message if len(message) <= 200 else f"{message[:197]}..."
            
            # Technical analysis
            severity = self._classify_severity(message)
            detailed['Severity'] = severity.upper()
            
            message_type = self._classify_message_type(message)
            detailed['Message Type'] = message_type.replace('_', ' ').title()
            
            technical_level = self._assess_technical_level(message)
            detailed['Technical Level'] = technical_level.replace('_', ' ').title()
            
            # Key information extraction
            key_info = self._extract_key_information(message)
            if key_info:
                detailed['Key Information'] = ', '.join(key_info)
            
            # Metadata
            detailed['Message Length'] = f"{len(message)} characters"
            detailed['Category Color'] = self.CATEGORY_COLORS.get(category, 'gray')
            
            return detailed
            
        except Exception as e:
            return {
                'Event Type': 'Debug Log',
                'Error': f'Formatting error: {e}',
                'Raw Data': str(raw_event)
            }
    
    def get_table_headers(self) -> List[str]:
        """
        Get table column headers for debug log events.
        
        Returns:
            List of column header strings
        """
        return ["Step", "Event Type", "Category", "Agent", "Message"]
    
    def get_supported_event_type(self) -> str:
        """
        Get the event type this formatter supports.
        
        Returns:
            Event type string: 'debug_log'
        """
        return 'debug_log'
    
    # ============================================================================
    # DEBUG LOG SPECIFIC HELPER METHODS
    # ============================================================================
    
    def _format_category_name(self, category: str) -> str:
        """
        Format category name for display.
        
        Args:
            category: Raw category string
            
        Returns:
            Human-readable category name
        """
        return self.CATEGORY_DISPLAY_NAMES.get(category.lower(), category.replace('_', ' ').title())
    
    def _clean_debug_message(self, message: str) -> str:
        """
        Clean up debug message for display.
        
        Args:
            message: Raw debug message
            
        Returns:
            Cleaned message suitable for display
        """
        if not message:
            return 'No message'
        
        # Remove excessive whitespace
        clean_message = ' '.join(message.split())
        
        # Handle common technical patterns
        clean_message = clean_message.replace('_', ' ')
        
        # Capitalize first letter if not already
        if clean_message and clean_message[0].islower():
            clean_message = clean_message[0].upper() + clean_message[1:]
        
        return clean_message
    
    def _classify_severity(self, message: str) -> str:
        """
        Classify message severity based on content.
        
        Args:
            message: Debug message text
            
        Returns:
            Severity level: 'error', 'warning', 'info', 'debug'
        """
        if not message:
            return 'debug'
        
        message_lower = message.lower()
        
        for severity, keywords in self.SEVERITY_KEYWORDS.items():
            if any(keyword in message_lower for keyword in keywords):
                return severity
        
        # Default classification based on message characteristics
        if message_lower.startswith('error') or '!' in message:
            return 'error'
        elif message_lower.startswith('warning') or '?' in message:
            return 'warning'
        elif any(char.isupper() for char in message):
            return 'info'
        else:
            return 'debug'
    
    def _classify_message_type(self, message: str) -> str:
        """
        Classify the type of debug message.
        
        Args:
            message: Debug message text
            
        Returns:
            Message type classification
        """
        if not message:
            return 'unknown'
        
        message_lower = message.lower()
        
        if 'calculation' in message_lower or 'compute' in message_lower:
            return 'calculation_detail'
        elif 'state' in message_lower or 'status' in message_lower:
            return 'state_information'
        elif 'decision' in message_lower or 'choice' in message_lower:
            return 'decision_logic'
        elif 'error' in message_lower or 'fail' in message_lower:
            return 'error_report'
        elif 'performance' in message_lower or 'timing' in message_lower:
            return 'performance_metric'
        elif 'init' in message_lower or 'start' in message_lower:
            return 'initialization'
        elif '=' in message or ':' in message:
            return 'value_assignment'
        else:
            return 'general_debug'
    
    def _assess_technical_level(self, message: str) -> str:
        """
        Assess the technical complexity level of the message.
        
        Args:
            message: Debug message text
            
        Returns:
            Technical level: 'low', 'medium', 'high'
        """
        if not message:
            return 'low'
        
        # Count technical indicators
        technical_indicators = 0
        
        # Check for technical patterns
        if any(char in message for char in '=()[]{}'):
            technical_indicators += 1
        if any(word in message.lower() for word in ['delta', 'utility', 'algorithm', 'compute']):
            technical_indicators += 1
        if len([char for char in message if char.isupper()]) > 3:
            technical_indicators += 1
        if len(message.split()) > 10:
            technical_indicators += 1
        
        if technical_indicators >= 3:
            return 'high'
        elif technical_indicators >= 1:
            return 'medium'
        else:
            return 'low'
    
    def _extract_key_information(self, message: str) -> List[str]:
        """
        Extract key pieces of information from debug message.
        
        Args:
            message: Debug message text
            
        Returns:
            List of key information strings
        """
        key_info = []
        
        if not message:
            return key_info
        
        # Extract numeric values
        import re
        numbers = re.findall(r'-?\d+\.?\d*', message)
        if numbers:
            key_info.extend([f"Value: {num}" for num in numbers[:3]])  # Limit to 3
        
        # Extract agent IDs
        agent_matches = re.findall(r'agent\s*(\d+)', message.lower())
        if agent_matches:
            key_info.extend([f"Agent: {agent_id}" for agent_id in agent_matches[:2]])
        
        # Extract resource types
        resource_types = ['wood', 'stone', 'food', 'water', 'metal', 'energy']
        found_resources = [res for res in resource_types if res in message.lower()]
        if found_resources:
            key_info.extend([f"Resource: {res}" for res in found_resources[:2]])
        
        return key_info[:5]  # Limit total key info items
    
    def _truncate_for_table(self, message: str, max_length: int = 50) -> str:
        """
        Truncate message for table display.
        
        Args:
            message: Full message text
            max_length: Maximum length for table display
            
        Returns:
            Truncated message with ellipsis if needed
        """
        if not message:
            return 'No message'
        
        if len(message) <= max_length:
            return message
        
        # Try to truncate at word boundary
        words = message[:max_length].split()
        if len(words) > 1:
            truncated = ' '.join(words[:-1])
            if len(truncated) > max_length - 3:
                return truncated[:max_length-3] + '...'
            else:
                return truncated + '...'
        else:
            return message[:max_length-3] + '...'
    
    def categorize_severity(self, message: str) -> str:
        """
        Public method for severity classification.
        
        Args:
            message: Debug message text
            
        Returns:
            Severity classification string
        """
        return self._classify_severity(message)
    
    def format_technical_details(self, raw_event: Dict[str, Any]) -> Dict[str, str]:
        """
        Format technical details for developer inspection.
        
        Args:
            raw_event: Raw debug log dictionary
            
        Returns:
            Dictionary with technical analysis
        """
        message = raw_event.get('message', '')
        
        return {
            'Raw Message': message,
            'Message Type': self._classify_message_type(message),
            'Severity': self._classify_severity(message),
            'Technical Level': self._assess_technical_level(message),
            'Character Count': str(len(message)),
            'Word Count': str(len(message.split())),
            'Key Information': ', '.join(self._extract_key_information(message)) or 'None extracted'
        }
    
    def analyze_debug_patterns(self, raw_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze patterns across multiple debug log events.
        
        Args:
            raw_events: List of raw debug log dictionaries
            
        Returns:
            Dictionary with debug pattern analysis
        """
        if not raw_events:
            return {
                'total_messages': 0,
                'category_distribution': {},
                'severity_distribution': {},
                'agent_activity': {}
            }
        
        # Track patterns
        category_counts: Dict[str, int] = {}
        severity_counts: Dict[str, int] = {}
        agent_activity: Dict[int, int] = {}
        message_types: Dict[str, int] = {}
        
        for event in raw_events:
            category = event.get('category', 'unknown')
            message = event.get('message', '')
            agent_id = event.get('agent_id', -1)
            
            # Count categories
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Count severities
            severity = self._classify_severity(message)
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count message types
            msg_type = self._classify_message_type(message)
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            # Track agent activity
            if agent_id >= 0:
                agent_activity[agent_id] = agent_activity.get(agent_id, 0) + 1
        
        return {
            'total_messages': len(raw_events),
            'category_distribution': category_counts,
            'severity_distribution': severity_counts,
            'message_type_distribution': message_types,
            'agent_activity': agent_activity,
            'agents_with_debug_activity': len(agent_activity),
            'most_common_category': max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else 'none',
            'most_common_severity': max(severity_counts.items(), key=lambda x: x[1])[0] if severity_counts else 'none'
        }