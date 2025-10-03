"""
Translation layer for decompressing events using schemas.

This module provides functions to decompress log events back to human-readable
format using the event schemas. This is used by GUI tools and analysis systems
to translate the compressed log format back to readable data.

Key Features:
- Auto-translates any compressed event back to human readable
- Uses schema registry for field code lookup
- Handles all event types with consistent interface
- Supports round-trip compression/decompression
- Graceful handling of unknown events and malformed data

Usage:
    from econsim.observability.new_architecture.translator import translate_event
    
    # Decompress a log entry
    compressed_entry = {"s": 42, "dt": 0.1, "e": "trade", "d": "sid:1,bid:2,gt:good1,tt:good2"}
    readable_entry = translate_event(compressed_entry)
    # Returns: {"event_type": "trade", "step": 42, "timestamp": 0.1, "seller_id": "1", "buyer_id": "2", ...}
"""

import json
from typing import Dict, Any, Optional, List, Union

from .event_schemas import (
    SCHEMA_REGISTRY,
    create_reverse_mapping,
    get_schema_by_code,
    validate_schema
)


def translate_event(compressed_event: Dict[str, Any]) -> Dict[str, Any]:
    """Auto-translate any compressed event back to human readable format.
    
    Uses the schema registry to automatically decompress any event type.
    This is the main entry point for translating compressed log entries.
    
    Args:
        compressed_event: Compressed log entry with 's', 'dt', 'e', 'd' fields
        
    Returns:
        Dictionary with human-readable field names and values
        
    Example:
        Input: {"s": 42, "dt": 0.1, "e": "trade", "d": "sid:1,bid:2,gt:good1,tt:good2"}
        Output: {
            "event_type": "trade",
            "step": 42,
            "timestamp": 0.1,
            "seller_id": "1",
            "buyer_id": "2",
            "give_type": "good1",
            "take_type": "good2"
        }
    """
    if not isinstance(compressed_event, dict):
        return compressed_event  # Return as-is if not a dict
    
    # Extract basic fields
    event_code = compressed_event.get('e', 'unknown')
    step = compressed_event.get('s')
    delta_time = compressed_event.get('dt')
    compressed_data = compressed_event.get('d', '')
    
    # Get schema for this event type
    schema = get_schema_by_code(event_code)
    
    if not schema:
        # Fallback for unknown events - return with basic info
        return {
            'event_type': event_code,
            'step': step,
            'timestamp': delta_time,
            'compressed_data': compressed_data,
            'translation_status': 'unknown_event_type'
        }
    
    # Create reverse mapping from field codes to field names
    reverse_mapping = create_reverse_mapping(schema)
    
    # Parse compressed data
    readable_fields = _parse_compressed_data(compressed_data, reverse_mapping)
    
    # Build result with metadata
    result = {
        'event_type': event_code,
        'step': step,
        'timestamp': delta_time,
        'schema_category': schema.get('category', 'unknown'),
        'description': schema.get('description', ''),
        **readable_fields
    }
    
    return result


def _parse_compressed_data(compressed_data: str, reverse_mapping: Dict[str, str]) -> Dict[str, Any]:
    """Parse compressed data string into readable fields.
    
    Args:
        compressed_data: Compressed data string (e.g., "sid:1,bid:2,gt:good1")
        reverse_mapping: Dictionary mapping codes to field names
        
    Returns:
        Dictionary with readable field names and parsed values
    """
    if not compressed_data:
        return {}
    
    readable_fields = {}
    
    # Split by comma to get individual field assignments
    parts = compressed_data.split(',')
    i = 0
    
    while i < len(parts):
        part = parts[i]
        if ':' not in part:
            i += 1
            continue  # Skip malformed parts
        
        try:
            code, value = part.split(':', 1)  # Split on first colon only
            field_name = reverse_mapping.get(code, code)  # Use original code if not found
            
            # Check if this is a dict field that might span multiple parts
            if field_name in reverse_mapping.values() and i + 1 < len(parts):
                # Look ahead to see if the next part is a continuation of this dict
                next_part = parts[i + 1]
                if ':' in next_part and next_part.split(':', 1)[0] not in reverse_mapping:
                    # This looks like a dict continuation, collect all parts until we hit a known field code
                    dict_parts = [value]
                    j = i + 1
                    while j < len(parts):
                        next_part = parts[j]
                        if ':' in next_part:
                            next_code = next_part.split(':', 1)[0]
                            if next_code in reverse_mapping:
                                # Found a known field code, stop collecting
                                break
                            else:
                                # This is part of the dict, add it
                                dict_parts.append(next_part)
                                j += 1
                        else:
                            break
                    
                    # Join all dict parts and parse as dict
                    dict_value = ','.join(dict_parts)
                    parsed_value = _parse_field_value(dict_value)
                    readable_fields[field_name] = parsed_value
                    i = j  # Skip the parts we've processed
                    continue
            
            # Try to parse value as appropriate type
            parsed_value = _parse_field_value(value)
            readable_fields[field_name] = parsed_value
            i += 1
            
        except (ValueError, IndexError):
            # Skip malformed field assignments
            i += 1
            continue
    
    return readable_fields


def _parse_field_value(value: str) -> Union[str, int, float, bool, Dict[str, Any]]:
    """Parse a field value string into appropriate Python type.
    
    Args:
        value: String value from compressed data
        
    Returns:
        Parsed value in appropriate type
    """
    if not value:
        return value
    
    # Try to parse as boolean
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'
    
    # Try to parse as integer
    try:
        if '.' not in value and 'e' not in value.lower():
            return int(value)
    except ValueError:
        pass
    
    # Try to parse as float
    try:
        return float(value)
    except ValueError:
        pass
    
    # Try to parse as dict (for complex fields like carrying_after)
    # Only attempt dict parsing if it looks like a dict format
    if ',' in value and ':' in value and not value.startswith('http'):
        try:
            # Handle dict-like strings: "key1:value1,key2:value2"
            dict_parts = value.split(',')
            parsed_dict = {}
            for dict_part in dict_parts:
                if ':' in dict_part:
                    k, v = dict_part.split(':', 1)
                    parsed_dict[k] = _parse_field_value(v)
            # Only return dict if we successfully parsed multiple key-value pairs
            if len(parsed_dict) > 1:
                return parsed_dict
        except (ValueError, IndexError):
            pass
    
    # Return as string if all else fails
    return value


# ============================================================================
# SPECIFIC DECOMPRESSION FUNCTIONS
# ============================================================================

def decompress_trade_event(compressed_data: str) -> Dict[str, Any]:
    """Decompress trade execution event data.
    
    Args:
        compressed_data: Compressed trade data string
        
    Returns:
        Dictionary with readable trade fields
    """
    schema = get_schema_by_code('trade')
    if not schema:
        return {'compressed_data': compressed_data, 'error': 'trade_schema_not_found'}
    
    reverse_mapping = create_reverse_mapping(schema)
    return _parse_compressed_data(compressed_data, reverse_mapping)


def decompress_agent_mode_event(compressed_data: str) -> Dict[str, Any]:
    """Decompress agent mode change event data.
    
    Args:
        compressed_data: Compressed mode change data string
        
    Returns:
        Dictionary with readable mode change fields
    """
    schema = get_schema_by_code('mode')
    if not schema:
        return {'compressed_data': compressed_data, 'error': 'mode_schema_not_found'}
    
    reverse_mapping = create_reverse_mapping(schema)
    return _parse_compressed_data(compressed_data, reverse_mapping)


def decompress_resource_collection_event(compressed_data: str) -> Dict[str, Any]:
    """Decompress resource collection event data.
    
    Args:
        compressed_data: Compressed resource collection data string
        
    Returns:
        Dictionary with readable resource collection fields
    """
    schema = get_schema_by_code('collect')
    if not schema:
        return {'compressed_data': compressed_data, 'error': 'collect_schema_not_found'}
    
    reverse_mapping = create_reverse_mapping(schema)
    return _parse_compressed_data(compressed_data, reverse_mapping)


def decompress_debug_log_event(compressed_data: str) -> Dict[str, Any]:
    """Decompress debug log event data.
    
    Args:
        compressed_data: Compressed debug log data string
        
    Returns:
        Dictionary with readable debug log fields
    """
    schema = get_schema_by_code('debug')
    if not schema:
        return {'compressed_data': compressed_data, 'error': 'debug_schema_not_found'}
    
    reverse_mapping = create_reverse_mapping(schema)
    return _parse_compressed_data(compressed_data, reverse_mapping)


def decompress_performance_monitor_event(compressed_data: str) -> Dict[str, Any]:
    """Decompress performance monitor event data.
    
    Args:
        compressed_data: Compressed performance monitor data string
        
    Returns:
        Dictionary with readable performance monitor fields
    """
    schema = get_schema_by_code('perf')
    if not schema:
        return {'compressed_data': compressed_data, 'error': 'perf_schema_not_found'}
    
    reverse_mapping = create_reverse_mapping(schema)
    return _parse_compressed_data(compressed_data, reverse_mapping)


def decompress_agent_decision_event(compressed_data: str) -> Dict[str, Any]:
    """Decompress agent decision event data.
    
    Args:
        compressed_data: Compressed agent decision data string
        
    Returns:
        Dictionary with readable agent decision fields
    """
    schema = get_schema_by_code('decision')
    if not schema:
        return {'compressed_data': compressed_data, 'error': 'decision_schema_not_found'}
    
    reverse_mapping = create_reverse_mapping(schema)
    return _parse_compressed_data(compressed_data, reverse_mapping)


def decompress_resource_event(compressed_data: str) -> Dict[str, Any]:
    """Decompress resource event data.
    
    Args:
        compressed_data: Compressed resource event data string
        
    Returns:
        Dictionary with readable resource event fields
    """
    schema = get_schema_by_code('resource')
    if not schema:
        return {'compressed_data': compressed_data, 'error': 'resource_schema_not_found'}
    
    reverse_mapping = create_reverse_mapping(schema)
    return _parse_compressed_data(compressed_data, reverse_mapping)


def decompress_economic_decision_event(compressed_data: str) -> Dict[str, Any]:
    """Decompress economic decision event data.
    
    Args:
        compressed_data: Compressed economic decision data string
        
    Returns:
        Dictionary with readable economic decision fields
    """
    schema = get_schema_by_code('econ')
    if not schema:
        return {'compressed_data': compressed_data, 'error': 'econ_schema_not_found'}
    
    reverse_mapping = create_reverse_mapping(schema)
    return _parse_compressed_data(compressed_data, reverse_mapping)


def decompress_gui_display_event(compressed_data: str) -> Dict[str, Any]:
    """Decompress GUI display event data.
    
    Args:
        compressed_data: Compressed GUI display data string
        
    Returns:
        Dictionary with readable GUI display fields
    """
    schema = get_schema_by_code('gui')
    if not schema:
        return {'compressed_data': compressed_data, 'error': 'gui_schema_not_found'}
    
    reverse_mapping = create_reverse_mapping(schema)
    return _parse_compressed_data(compressed_data, reverse_mapping)


# ============================================================================
# BATCH TRANSLATION FUNCTIONS
# ============================================================================

def translate_log_file(log_file_path: str) -> List[Dict[str, Any]]:
    """Translate an entire log file from compressed to readable format.
    
    Args:
        log_file_path: Path to the compressed log file
        
    Returns:
        List of translated log entries
    """
    translated_entries = []
    
    try:
        with open(log_file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Parse JSON line
                    compressed_entry = json.loads(line)
                    translated_entry = translate_event(compressed_entry)
                    translated_entries.append(translated_entry)
                    
                except json.JSONDecodeError as e:
                    # Add error entry for malformed JSON
                    translated_entries.append({
                        'line_number': line_num,
                        'error': f'JSON decode error: {e}',
                        'raw_line': line
                    })
                except Exception as e:
                    # Add error entry for other translation errors
                    translated_entries.append({
                        'line_number': line_num,
                        'error': f'Translation error: {e}',
                        'raw_line': line
                    })
    
    except FileNotFoundError:
        return [{'error': f'Log file not found: {log_file_path}'}]
    except Exception as e:
        return [{'error': f'Error reading log file: {e}'}]
    
    return translated_entries


def translate_events_by_type(translated_entries: List[Dict[str, Any]], event_type: str) -> List[Dict[str, Any]]:
    """Filter translated entries by event type.
    
    Args:
        translated_entries: List of translated log entries
        event_type: Event type to filter by (e.g., 'trade', 'mode')
        
    Returns:
        List of entries matching the specified event type
    """
    return [entry for entry in translated_entries if entry.get('event_type') == event_type]


def get_translation_statistics(translated_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get statistics about translated log entries.
    
    Args:
        translated_entries: List of translated log entries
        
    Returns:
        Dictionary with translation statistics
    """
    stats = {
        'total_entries': len(translated_entries),
        'event_type_counts': {},
        'error_count': 0,
        'unknown_event_count': 0
    }
    
    for entry in translated_entries:
        if 'error' in entry:
            stats['error_count'] += 1
        elif entry.get('translation_status') == 'unknown_event_type':
            stats['unknown_event_count'] += 1
        else:
            event_type = entry.get('event_type', 'unknown')
            stats['event_type_counts'][event_type] = stats['event_type_counts'].get(event_type, 0) + 1
    
    return stats


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_compressed_event(compressed_event: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a compressed event structure.
    
    Args:
        compressed_event: Compressed event to validate
        
    Returns:
        Dictionary with validation results
    """
    result = {
        'is_valid': True,
        'errors': [],
        'warnings': []
    }
    
    if not isinstance(compressed_event, dict):
        result['is_valid'] = False
        result['errors'].append('Event must be a dictionary')
        return result
    
    # Check required fields
    required_fields = ['s', 'dt', 'e', 'd']
    for field in required_fields:
        if field not in compressed_event:
            result['is_valid'] = False
            result['errors'].append(f'Missing required field: {field}')
    
    # Check event type
    event_code = compressed_event.get('e')
    if event_code:
        schema = get_schema_by_code(event_code)
        if not schema:
            result['warnings'].append(f'Unknown event type: {event_code}')
    
    return result


def get_supported_event_types() -> List[str]:
    """Get list of supported event types for translation.
    
    Returns:
        List of event type codes that can be translated
    """
    return list(SCHEMA_REGISTRY.keys())


def is_event_type_supported(event_type: str) -> bool:
    """Check if an event type is supported for translation.
    
    Args:
        event_type: Event type code to check
        
    Returns:
        True if the event type is supported, False otherwise
    """
    return event_type in SCHEMA_REGISTRY
