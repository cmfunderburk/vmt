"""
MessagePack Serialization for Comprehensive Simulation Deltas

Provides efficient binary serialization with debugging utilities and schema versioning.
"""

from __future__ import annotations

import json
import msgpack
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict

from .data_structures import SimulationDelta


# Schema versioning
SCHEMA_VERSION = "1.0.0"
FILE_MAGIC = b"VMTDELTA"  # 8-byte magic header for file identification


class DeltaSerializer:
    """Handles serialization and deserialization of SimulationDelta objects."""
    
    def __init__(self, schema_version: str = SCHEMA_VERSION):
        self.schema_version = schema_version
    
    def serialize_delta(self, delta: SimulationDelta) -> bytes:
        """Serialize a single SimulationDelta to MessagePack bytes."""
        # Convert dataclass to dict, handling nested structures
        delta_dict = self._dataclass_to_dict(delta)
        
        # Add metadata
        delta_dict['_metadata'] = {
            'schema_version': self.schema_version,
            'serialized_at': time.time(),
            'serializer': 'DeltaSerializer'
        }
        
        return msgpack.packb(delta_dict, use_bin_type=True)
    
    def deserialize_delta(self, data: bytes) -> SimulationDelta:
        """Deserialize MessagePack bytes to SimulationDelta."""
        delta_dict = msgpack.unpackb(data, raw=False, strict_map_key=False)
        
        # Remove metadata
        metadata = delta_dict.pop('_metadata', {})
        
        # Convert dict back to SimulationDelta
        return self._dict_to_dataclass(delta_dict)
    
    def serialize_deltas(self, deltas: List[SimulationDelta], initial_state: Optional[Any] = None) -> bytes:
        """Serialize a list of SimulationDelta objects to MessagePack bytes with optional initial state."""
        # Convert all deltas to dicts
        delta_dicts = [self._dataclass_to_dict(delta) for delta in deltas]
        
        # Create file structure with metadata
        file_data = {
            'header': {
                'magic': FILE_MAGIC.decode('ascii'),
                'schema_version': self.schema_version,
                'created_at': time.time(),
                'delta_count': len(deltas),
                'serializer': 'DeltaSerializer'
            },
            'deltas': delta_dicts
        }
        
        # Add initial state if provided
        if initial_state is not None:
            file_data['initial_state'] = self._dataclass_to_dict(initial_state)
        
        return msgpack.packb(file_data, use_bin_type=True)
    
    def deserialize_deltas(self, data: bytes) -> List[SimulationDelta]:
        """Deserialize MessagePack bytes to list of SimulationDelta objects."""
        file_data = msgpack.unpackb(data, raw=False, strict_map_key=False)
        
        # Validate header
        header = file_data.get('header', {})
        if header.get('magic') != FILE_MAGIC.decode('ascii'):
            raise ValueError("Invalid file format: missing or incorrect magic header")
        
        # Check schema version compatibility
        file_version = header.get('schema_version', 'unknown')
        if file_version != self.schema_version:
            print(f"Warning: Schema version mismatch. File: {file_version}, Expected: {self.schema_version}")
        
        # Convert delta dicts back to SimulationDelta objects
        deltas = []
        for delta_dict in file_data.get('deltas', []):
            deltas.append(self._dict_to_dataclass(delta_dict))
        
        return deltas
    
    def load_from_file_with_initial_state(self, filepath: Union[str, Path]) -> tuple[List[SimulationDelta], Optional[Any]]:
        """Load deltas and initial state from a MessagePack file."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Delta file not found: {filepath}")
        
        with open(filepath, 'rb') as f:
            data = f.read()
        
        file_data = msgpack.unpackb(data, raw=False, strict_map_key=False)
        
        # Validate header
        header = file_data.get('header', {})
        if header.get('magic') != FILE_MAGIC.decode('ascii'):
            raise ValueError("Invalid file format: missing or incorrect magic header")
        
        # Check schema version compatibility
        file_version = header.get('schema_version', 'unknown')
        if file_version != self.schema_version:
            print(f"Warning: Schema version mismatch. File: {file_version}, Expected: {self.schema_version}")
        
        # Convert delta dicts back to SimulationDelta objects
        deltas = []
        for delta_dict in file_data.get('deltas', []):
            deltas.append(self._dict_to_dataclass(delta_dict))
        
        # Load initial state if present
        initial_state = None
        if 'initial_state' in file_data:
            initial_state = self._dict_to_dataclass(file_data['initial_state'])
        
        return deltas, initial_state
    
    def save_to_file(self, deltas: List[SimulationDelta], filepath: Union[str, Path], initial_state: Optional[Any] = None) -> None:
        """Save deltas to a MessagePack file with optional initial state."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.serialize_deltas(deltas, initial_state)
        with open(filepath, 'wb') as f:
            f.write(data)
    
    def load_from_file(self, filepath: Union[str, Path]) -> List[SimulationDelta]:
        """Load deltas from a MessagePack file."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Delta file not found: {filepath}")
        
        with open(filepath, 'rb') as f:
            data = f.read()
        
        return self.deserialize_deltas(data)
    
    def _dataclass_to_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert dataclass to dictionary, handling nested structures."""
        if hasattr(obj, '__dataclass_fields__'):
            # It's a dataclass
            result = {}
            for field_name, field_value in asdict(obj).items():
                if isinstance(field_value, list):
                    # Convert list items, handling tuples specially
                    converted_list = []
                    for item in field_value:
                        if isinstance(item, tuple):
                            # Convert tuple to list for MessagePack compatibility
                            converted_list.append(list(item))
                        elif hasattr(item, '__dataclass_fields__'):
                            converted_list.append(self._dataclass_to_dict(item))
                        else:
                            converted_list.append(item)
                    result[field_name] = converted_list
                elif isinstance(field_value, tuple):
                    # Convert tuple to list for MessagePack compatibility
                    result[field_name] = list(field_value)
                elif isinstance(field_value, dict):
                    # Handle dictionaries with tuple keys
                    converted_dict = {}
                    for k, v in field_value.items():
                        if isinstance(k, tuple):
                            # Convert tuple key to string representation
                            converted_dict[f"{k[0]},{k[1]}"] = v
                        else:
                            converted_dict[k] = v
                    result[field_name] = converted_dict
                elif hasattr(field_value, '__dataclass_fields__'):
                    result[field_name] = self._dataclass_to_dict(field_value)
                else:
                    result[field_name] = field_value
            return result
        else:
            # Not a dataclass, return as-is
            return obj
    
    def _dict_to_dataclass(self, data: Dict[str, Any]) -> Any:
        """Convert dictionary back to dataclass, handling list-to-tuple conversions."""
        # Check if this is a SimulationDelta or VisualState
        if 'visual_changes' in data:
            # This is a SimulationDelta
            return self._dict_to_simulation_delta(data)
        elif 'agent_positions' in data:
            # This is a VisualState
            return self._dict_to_visual_state(data)
        else:
            # Unknown dataclass, try to reconstruct as SimulationDelta
            return self._dict_to_simulation_delta(data)
    
    def _dict_to_simulation_delta(self, data: Dict[str, Any]) -> SimulationDelta:
        """Convert dictionary back to SimulationDelta dataclass."""
        # Handle visual_changes
        visual_data = data.get('visual_changes', {})
        from .data_structures import VisualDelta
        visual_changes = VisualDelta(
            step=visual_data.get('step', 0),
            agent_moves=[tuple(move) if isinstance(move, list) else move for move in visual_data.get('agent_moves', [])],
            agent_state_changes=[tuple(change) if isinstance(change, list) else change for change in visual_data.get('agent_state_changes', [])],
            resource_changes=[tuple(change) if isinstance(change, list) else change for change in visual_data.get('resource_changes', [])]
        )
        
        # Create main SimulationDelta
        return SimulationDelta(
            step=data.get('step', 0),
            timestamp=data.get('timestamp', time.time()),
            visual_changes=visual_changes,
            agent_moves=[],  # TODO: Reconstruct from data
            agent_mode_changes=[],  # TODO: Reconstruct from data
            agent_inventory_changes=[],  # TODO: Reconstruct from data
            agent_target_changes=[],  # TODO: Reconstruct from data
            agent_utility_changes=[],  # TODO: Reconstruct from data
            resource_collections=[],  # TODO: Reconstruct from data
            resource_spawns=[],  # TODO: Reconstruct from data
            resource_depletions=[],  # TODO: Reconstruct from data
            trade_events=[],  # TODO: Reconstruct from data
            trade_intents=[],  # TODO: Reconstruct from data
            economic_decisions=[],  # TODO: Reconstruct from data
            performance_metrics=None,  # TODO: Reconstruct from data
            debug_events=[]  # TODO: Reconstruct from data
        )
    
    def _dict_to_visual_state(self, data: Dict[str, Any]) -> Any:
        """Convert dictionary back to VisualState dataclass."""
        from .data_structures import VisualState
        
        # Convert resource_positions string keys back to tuples
        resource_positions = {}
        for k, v in data.get('resource_positions', {}).items():
            if isinstance(k, str) and ',' in k:
                # Convert "x,y" string back to (x, y) tuple
                x, y = k.split(',')
                resource_positions[(int(x), int(y))] = v
            else:
                resource_positions[k] = v
        
        return VisualState(
            step=data.get('step', 0),
            agent_positions={int(k): tuple(v) if isinstance(v, list) else v for k, v in data.get('agent_positions', {}).items()},
            agent_states={int(k): v for k, v in data.get('agent_states', {}).items()},
            resource_positions=resource_positions,
            grid_width=data.get('grid_width', 20),
            grid_height=data.get('grid_height', 20)
        )


class DeltaDebugger:
    """Debugging utilities for MessagePack delta files."""
    
    @staticmethod
    def export_to_json(delta_file: Union[str, Path], output_file: Union[str, Path], 
                      pretty: bool = True) -> None:
        """Convert MessagePack delta file to human-readable JSON."""
        serializer = DeltaSerializer()
        deltas = serializer.load_from_file(delta_file)
        
        # Convert to JSON-serializable format
        json_data = []
        for delta in deltas:
            json_data.append(delta.__dict__)
        
        # Write to JSON file
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            if pretty:
                json.dump(json_data, f, indent=2, default=str)
            else:
                json.dump(json_data, f, default=str)
    
    @staticmethod
    def print_delta_summary(delta_file: Union[str, Path], step: Optional[int] = None) -> None:
        """Print a summary of delta file contents."""
        serializer = DeltaSerializer()
        deltas = serializer.load_from_file(delta_file)
        
        if step is not None:
            # Print specific step
            for delta in deltas:
                if delta.step == step:
                    print(f"Step {step} Summary:")
                    print(f"  {delta.get_summary()}")
                    print(f"  Event counts: {delta.get_event_counts()}")
                    return
            print(f"Step {step} not found in file")
        else:
            # Print file summary
            print(f"Delta File Summary:")
            print(f"  Total steps: {len(deltas)}")
            print(f"  First step: {deltas[0].step if deltas else 'N/A'}")
            print(f"  Last step: {deltas[-1].step if deltas else 'N/A'}")
            
            # Count events by type
            total_events = {}
            for delta in deltas:
                counts = delta.get_event_counts()
                for event_type, count in counts.items():
                    total_events[event_type] = total_events.get(event_type, 0) + count
            
            print(f"  Total events by type:")
            for event_type, count in sorted(total_events.items()):
                if count > 0:
                    print(f"    {event_type}: {count}")
    
    @staticmethod
    def find_events(delta_file: Union[str, Path], event_type: str, 
                   agent_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find specific events in delta file."""
        serializer = DeltaSerializer()
        deltas = serializer.load_from_file(delta_file)
        
        events = []
        for delta in deltas:
            if hasattr(delta, event_type):
                delta_events = getattr(delta, event_type)
                if isinstance(delta_events, list):
                    for event in delta_events:
                        if agent_id is None or getattr(event, 'agent_id', None) == agent_id:
                            events.append(event.__dict__)
        
        return events
    
    @staticmethod
    def validate_file(delta_file: Union[str, Path]) -> Dict[str, Any]:
        """Validate a delta file and return validation results."""
        filepath = Path(delta_file)
        
        if not filepath.exists():
            return {'valid': False, 'error': 'File not found'}
        
        try:
            serializer = DeltaSerializer()
            deltas = serializer.load_from_file(delta_file)
            
            return {
                'valid': True,
                'delta_count': len(deltas),
                'steps': [delta.step for delta in deltas],
                'schema_version': SCHEMA_VERSION
            }
        except Exception as e:
            return {'valid': False, 'error': str(e)}


# Convenience functions for common operations
def save_deltas(deltas: List[SimulationDelta], filepath: Union[str, Path]) -> None:
    """Save deltas to MessagePack file."""
    serializer = DeltaSerializer()
    serializer.save_to_file(deltas, filepath)


def load_deltas(filepath: Union[str, Path]) -> List[SimulationDelta]:
    """Load deltas from MessagePack file."""
    serializer = DeltaSerializer()
    return serializer.load_from_file(filepath)


def debug_deltas(filepath: Union[str, Path], output_json: Optional[Union[str, Path]] = None) -> None:
    """Debug utility - print summary and optionally export to JSON."""
    DeltaDebugger.print_delta_summary(filepath)
    
    if output_json:
        DeltaDebugger.export_to_json(filepath, output_json)
        print(f"Exported to JSON: {output_json}")
