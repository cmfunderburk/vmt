"""Format migration tools for Phase 4E semantic compression.

This module provides tools for migrating between different log format versions,
with special support for V5_SEMANTIC format migration and backward compatibility.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Union, Optional
from enum import Enum

from .optimized_serializer import LogFormatVersion


class FormatMigrationError(Exception):
    """Exception raised during format migration operations."""
    pass


class LogFormatMigrator:
    """Tool for migrating between different log format versions.
    
    Supports migration from V1_BASIC through V5_SEMANTIC formats,
    with special handling for semantic compression features.
    """
    
    def __init__(self):
        """Initialize the format migrator."""
        self.supported_versions = [
            LogFormatVersion.V1_BASIC,
            LogFormatVersion.V2_OPTIMIZED,
            LogFormatVersion.V3_ADVANCED,
            LogFormatVersion.V4_ULTRA,
            LogFormatVersion.V5_SEMANTIC
        ]
    
    def detect_format_version(self, log_data: Union[str, Dict[str, Any]]) -> LogFormatVersion:
        """Detect the format version of log data.
        
        Args:
            log_data: Log data as string or dictionary
            
        Returns:
            Detected LogFormatVersion
            
        Raises:
            FormatMigrationError: If format cannot be detected
        """
        if isinstance(log_data, str):
            try:
                log_data = json.loads(log_data)
            except json.JSONDecodeError:
                raise FormatMigrationError("Invalid JSON format")
        
        # Check for V5_SEMANTIC format indicators
        if self._is_v5_semantic_format(log_data):
            return LogFormatVersion.V5_SEMANTIC
        
        # Check for V4_ULTRA format indicators
        if self._is_v4_ultra_format(log_data):
            return LogFormatVersion.V4_ULTRA
        
        # Check for V3_ADVANCED format indicators
        if self._is_v3_advanced_format(log_data):
            return LogFormatVersion.V3_ADVANCED
        
        # Check for V2_OPTIMIZED format indicators
        if self._is_v2_optimized_format(log_data):
            return LogFormatVersion.V2_OPTIMIZED
        
        # Default to V1_BASIC
        return LogFormatVersion.V1_BASIC
    
    def _is_v5_semantic_format(self, log_data: Dict[str, Any]) -> bool:
        """Check if log data is in V5_SEMANTIC format.
        
        Args:
            log_data: Log data dictionary
            
        Returns:
            True if V5_SEMANTIC format detected
        """
        # V5_SEMANTIC indicators:
        # - String-based event compression (e.g., "t0,1-5" instead of [["t0",[1,2,3,4,5]]])
        # - Context-aware compression patterns
        # - Semantic inference markers
        
        if 'c' in log_data and isinstance(log_data['c'], str):
            # Collection events as strings: "t0,1-5"
            return True
        
        if 'm' in log_data and isinstance(log_data['m'], str):
            # Mode events as strings: "1,t0,1-5"
            return True
        
        # Check for semantic compression patterns in nested structures
        if 'c' in log_data and isinstance(log_data['c'], list):
            for item in log_data['c']:
                if isinstance(item, str) and ',' in item:
                    return True
        
        if 'm' in log_data and isinstance(log_data['m'], list):
            for item in log_data['m']:
                if isinstance(item, str) and ',' in item:
                    return True
        
        return False
    
    def _is_v4_ultra_format(self, log_data: Dict[str, Any]) -> bool:
        """Check if log data is in V4_ULTRA format.
        
        Args:
            log_data: Log data dictionary
            
        Returns:
            True if V4_ULTRA format detected
        """
        # V4_ULTRA indicators:
        # - Ultra-compact step format with reduced nesting
        # - Pattern codes like "1", "2" instead of "P1", "P2"
        # - Advanced range compression
        
        if 'm' in log_data and isinstance(log_data['m'], list):
            for item in log_data['m']:
                if isinstance(item, list) and len(item) >= 1:
                    pattern = item[0]
                    if isinstance(pattern, str) and pattern.isdigit():
                        return True
        
        return False
    
    def _is_v3_advanced_format(self, log_data: Dict[str, Any]) -> bool:
        """Check if log data is in V3_ADVANCED format.
        
        Args:
            log_data: Log data dictionary
            
        Returns:
            True if V3_ADVANCED format detected
        """
        # V3_ADVANCED indicators:
        # - Advanced agent range compression
        # - Dictionary expansion features
        
        if 'c' in log_data and isinstance(log_data['c'], list):
            for item in log_data['c']:
                if isinstance(item, list) and len(item) >= 2:
                    agent_data = item[1]
                    if isinstance(agent_data, str) and ('-' in agent_data or ',' in agent_data):
                        return True
        
        return False
    
    def _is_v2_optimized_format(self, log_data: Dict[str, Any]) -> bool:
        """Check if log data is in V2_OPTIMIZED format.
        
        Args:
            log_data: Log data dictionary
            
        Returns:
            True if V2_OPTIMIZED format detected
        """
        # V2_OPTIMIZED indicators:
        # - Pattern codes like "P1", "P2"
        # - Basic behavioral pattern recognition
        
        if 'm' in log_data and isinstance(log_data['m'], list):
            for item in log_data['m']:
                if isinstance(item, list) and len(item) >= 1:
                    pattern = item[0]
                    if isinstance(pattern, str) and pattern.startswith('P'):
                        return True
        
        return False
    
    def migrate_to_v5_semantic(self, log_data: Dict[str, Any], 
                              source_version: LogFormatVersion) -> Dict[str, Any]:
        """Migrate log data to V5_SEMANTIC format.
        
        Args:
            log_data: Source log data
            source_version: Source format version
            
        Returns:
            Migrated log data in V5_SEMANTIC format
        """
        if source_version == LogFormatVersion.V5_SEMANTIC:
            return log_data  # Already in target format
        
        # Start with a copy of the source data
        migrated_data = log_data.copy()
        
        # Apply semantic compression based on source version
        if source_version in [LogFormatVersion.V4_ULTRA, LogFormatVersion.V3_ADVANCED, 
                             LogFormatVersion.V2_OPTIMIZED, LogFormatVersion.V1_BASIC]:
            migrated_data = self._apply_semantic_compression(migrated_data)
        
        return migrated_data
    
    def _apply_semantic_compression(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply semantic compression to log data.
        
        Args:
            log_data: Log data to compress
            
        Returns:
            Semantically compressed log data
        """
        compressed_data = log_data.copy()
        
        # Apply semantic compression to collection events
        if 'c' in compressed_data:
            compressed_data['c'] = self._compress_events_semantic(compressed_data['c'], 'collection')
        
        # Apply semantic compression to mode events
        if 'm' in compressed_data:
            compressed_data['m'] = self._compress_events_semantic(compressed_data['m'], 'mode')
        
        # Apply semantic compression to other events
        if 'o' in compressed_data:
            compressed_data['o'] = self._compress_events_semantic(compressed_data['o'], 'other')
        
        return compressed_data
    
    def _compress_events_semantic(self, events: Union[str, List], event_type: str) -> Union[str, List]:
        """Compress events using semantic inference.
        
        Args:
            events: Events to compress
            event_type: Type of events ('collection', 'mode', 'other')
            
        Returns:
            Semantically compressed events
        """
        if isinstance(events, str):
            return events  # Already compressed
        
        if not isinstance(events, list):
            return events
        
        if not events:
            return events
        
        # Single event semantic compression
        if len(events) == 1:
            return self._compress_single_event_semantic(events[0], event_type)
        
        # Multiple events - use context-aware grouping
        return self._compress_multiple_events_semantic(events, event_type)
    
    def _compress_single_event_semantic(self, event: Union[List, Dict], event_type: str) -> str:
        """Compress single event using semantic inference.
        
        Args:
            event: Single event to compress
            event_type: Type of event ('collection', 'mode', 'other')
            
        Returns:
            Semantically compressed string representation
        """
        if event_type == 'collection' and isinstance(event, list):
            if len(event) == 2:
                time_val, agent_data = event
                return f"{time_val},{agent_data}"
        
        elif event_type == 'mode' and isinstance(event, list):
            if len(event) == 2:
                # Pattern format: ["1", ["t0", "1-5"]]
                pattern, time_agent_data = event
                if isinstance(time_agent_data, list) and len(time_agent_data) == 2:
                    time_val, agent_data = time_agent_data
                    return f"{pattern},{time_val},{agent_data}"
            elif len(event) == 4:
                # Individual format: ["t0", 6, "fi", "nta"]
                time_val, agent_id, transition, reason = event
                return f"{time_val},{agent_id},{transition},{reason}"
        
        # Fallback to string representation
        return str(event)
    
    def _compress_multiple_events_semantic(self, events: List, event_type: str) -> List:
        """Compress multiple events using context-aware grouping.
        
        Args:
            events: List of events to compress
            event_type: Type of events ('collection', 'mode', 'other')
            
        Returns:
            Context-aware compressed events list
        """
        # Group events by semantic similarity
        semantic_groups = self._group_events_semantic(events, event_type)
        
        # Compress each semantic group
        compressed_groups = []
        for group in semantic_groups:
            if len(group) == 1:
                compressed_groups.append(self._compress_single_event_semantic(group[0], event_type))
            else:
                compressed_groups.append(self._compress_semantic_group(group, event_type))
        
        return compressed_groups
    
    def _group_events_semantic(self, events: List, event_type: str) -> List[List]:
        """Group events by semantic similarity.
        
        Args:
            events: List of events to group
            event_type: Type of events ('collection', 'mode', 'other')
            
        Returns:
            List of semantically similar event groups
        """
        from collections import defaultdict
        
        if event_type == 'collection':
            # Group collection events by time pattern
            time_groups = defaultdict(list)
            for event in events:
                if isinstance(event, list) and len(event) >= 1:
                    time_pattern = event[0]
                    time_groups[time_pattern].append(event)
            return list(time_groups.values())
        
        elif event_type == 'mode':
            # Group mode events by pattern similarity
            pattern_groups = defaultdict(list)
            for event in events:
                if isinstance(event, list):
                    if len(event) == 2:
                        # Pattern format: ["1", ["t0", "1-5"]]
                        pattern = event[0]
                        pattern_groups[f"pattern_{pattern}"].append(event)
                    elif len(event) == 4:
                        # Individual format: ["t0", 6, "fi", "nta"]
                        transition = event[2]
                        reason = event[3]
                        pattern_key = f"individual_{transition}_{reason}"
                        pattern_groups[pattern_key].append(event)
            return list(pattern_groups.values())
        
        # Default: no grouping
        return [[event] for event in events]
    
    def _compress_semantic_group(self, group: List, event_type: str) -> Union[str, List]:
        """Compress a group of semantically similar events.
        
        Args:
            group: List of similar events
            event_type: Type of events ('collection', 'mode', 'other')
            
        Returns:
            Compressed representation of the group
        """
        if event_type == 'collection':
            # Collection groups: merge by time pattern
            if len(group) > 1:
                merged_agents = []
                time_pattern = None
                
                for event in group:
                    if isinstance(event, list) and len(event) == 2:
                        time_val, agent_data = event
                        if time_pattern is None:
                            time_pattern = time_val
                        
                        if isinstance(agent_data, (list, str)):
                            if isinstance(agent_data, str):
                                agent_list = self._parse_agent_range(agent_data)
                            else:
                                agent_list = agent_data
                            merged_agents.extend(agent_list)
                
                if merged_agents:
                    unique_agents = sorted(list(set(merged_agents)))
                    compressed_agents = self._compress_agent_list(unique_agents)
                    return [time_pattern, compressed_agents]
        
        elif event_type == 'mode':
            # Mode groups: merge by pattern
            if len(group) > 1:
                merged_agents = []
                pattern = None
                time_pattern = None
                
                for event in group:
                    if isinstance(event, list):
                        if len(event) == 2:
                            # Pattern format: ["1", ["t0", "1-5"]]
                            pat, time_agent_data = event
                            if pattern is None:
                                pattern = pat
                            
                            if isinstance(time_agent_data, list) and len(time_agent_data) == 2:
                                time_val, agent_data = time_agent_data
                                if time_pattern is None:
                                    time_pattern = time_val
                                
                                if isinstance(agent_data, (list, str)):
                                    if isinstance(agent_data, str):
                                        agent_list = self._parse_agent_range(agent_data)
                                    else:
                                        agent_list = agent_data
                                    merged_agents.extend(agent_list)
                
                if merged_agents:
                    unique_agents = sorted(list(set(merged_agents)))
                    compressed_agents = self._compress_agent_list(unique_agents)
                    return [pattern, [time_pattern, compressed_agents]]
        
        # Fallback: return original group
        return group
    
    def _parse_agent_range(self, range_string: str) -> List[int]:
        """Parse agent range string back to list of agent IDs.
        
        Args:
            range_string: Compressed agent range string like "1-5,7,9-12"
            
        Returns:
            List of agent IDs
        """
        agents = []
        parts = range_string.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                # Range: "1-5"
                start, end = map(int, part.split('-'))
                agents.extend(range(start, end + 1))
            else:
                # Single: "7"
                agents.append(int(part))
        
        return sorted(agents)
    
    def _compress_agent_list(self, agent_list: List[int]) -> Union[str, List]:
        """Compress agent list using range compression.
        
        Args:
            agent_list: Sorted list of agent IDs
            
        Returns:
            Compressed representation
        """
        if len(agent_list) < 2:
            return agent_list[0] if agent_list else []
        
        # Find optimal ranges
        ranges = self._find_optimal_ranges(agent_list)
        
        # Compress ranges
        compressed_parts = []
        for start, end in ranges:
            if start == end:
                compressed_parts.append(str(start))
            elif end - start == 1:
                compressed_parts.extend([str(start), str(end)])
            else:
                compressed_parts.append(f"{start}-{end}")
        
        if len(compressed_parts) == 1:
            return compressed_parts[0]
        else:
            compressed_string = ",".join(compressed_parts)
            original_string = str(agent_list)
            
            if len(compressed_string) < len(original_string):
                return compressed_string
            else:
                return agent_list
    
    def _find_optimal_ranges(self, agent_list: List[int]) -> List[tuple]:
        """Find optimal ranges for agent list compression.
        
        Args:
            agent_list: Sorted list of agent IDs
            
        Returns:
            List of (start, end) tuples representing optimal ranges
        """
        if not agent_list:
            return []
        
        ranges = []
        current_start = agent_list[0]
        current_end = agent_list[0]
        
        for i in range(1, len(agent_list)):
            if agent_list[i] == current_end + 1:
                current_end = agent_list[i]
            else:
                ranges.append((current_start, current_end))
                current_start = agent_list[i]
                current_end = agent_list[i]
        
        ranges.append((current_start, current_end))
        return ranges
    
    def migrate_log_file(self, input_path: Path, output_path: Path, 
                        target_version: LogFormatVersion = LogFormatVersion.V5_SEMANTIC) -> None:
        """Migrate an entire log file to a different format version.
        
        Args:
            input_path: Path to input log file
            output_path: Path to output log file
            target_version: Target format version
            
        Raises:
            FormatMigrationError: If migration fails
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as infile:
                with open(output_path, 'w', encoding='utf-8') as outfile:
                    for line_num, line in enumerate(infile, 1):
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            log_data = json.loads(line)
                            source_version = self.detect_format_version(log_data)
                            
                            if target_version == LogFormatVersion.V5_SEMANTIC:
                                migrated_data = self.migrate_to_v5_semantic(log_data, source_version)
                            else:
                                # For now, only support migration to V5_SEMANTIC
                                raise FormatMigrationError(f"Migration to {target_version} not yet supported")
                            
                            outfile.write(json.dumps(migrated_data, separators=(',', ':')) + '\n')
                            
                        except json.JSONDecodeError as e:
                            raise FormatMigrationError(f"Invalid JSON on line {line_num}: {e}")
                        except Exception as e:
                            raise FormatMigrationError(f"Migration error on line {line_num}: {e}")
        
        except FileNotFoundError:
            raise FormatMigrationError(f"Input file not found: {input_path}")
        except Exception as e:
            raise FormatMigrationError(f"File migration failed: {e}")


def create_format_migrator() -> LogFormatMigrator:
    """Factory function to create a format migrator.
    
    Returns:
        Configured LogFormatMigrator instance
    """
    return LogFormatMigrator()
