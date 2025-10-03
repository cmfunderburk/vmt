"""
Unit tests for DataTranslator - GUI translation layer.

Tests the translation system that converts raw simulation data (dictionaries)
to human-readable format for GUI consumption.

Test Categories:
- Specific translation methods: All translate_*_event() methods
- Generic translation: translate_event() method for any event type
- Batch translation: translate_events(), translate_events_by_type(), etc.
- Human-readable descriptions: get_human_readable_description() methods
- Formatting helpers: All _format_*() helper methods
- Edge cases: Unknown event types, missing fields, etc.
"""

import pytest
from typing import Dict, List, Any

from src.econsim.observability.raw_data.data_translator import DataTranslator


class TestDataTranslatorSpecificMethods:
    """Test specific translate_*_event() methods for different event types."""
    
    def test_translate_trade_event_basic(self):
        """Test basic trade event translation."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'trade',
            'step': 100,
            'seller_id': 1,
            'buyer_id': 2,
            'give_type': 'wood',
            'take_type': 'stone',
            'delta_u_seller': 5.5,
            'delta_u_buyer': 3.2,
            'trade_location_x': 10,
            'trade_location_y': 20
        }
        
        translated = translator.translate_trade_event(raw_event)
        
        assert translated['event_type'] == 'Trade Execution'
        assert translated['step'] == 100
        assert translated['seller_id'] == 1
        assert translated['buyer_id'] == 2
        assert translated['give_type'] == 'wood'
        assert translated['take_type'] == 'stone'
        assert translated['delta_u_seller'] == 5.5
        assert translated['delta_u_buyer'] == 3.2
        assert translated['trade_location_x'] == 10
        assert translated['trade_location_y'] == 20
        
        # Check human-readable fields
        assert 'description' in translated
        assert 'summary' in translated
        assert 'utility_summary' in translated
        assert 'location_summary' in translated
        assert 'raw_data' in translated
        
        # Verify description format
        description = translated['description']
        assert 'Agent 1' in description
        assert 'wood' in description
        assert 'stone' in description
        assert 'Agent 2' in description
        assert '5.50' in description  # Utility formatting
        assert '3.20' in description
        assert '(10, 20)' in description
    
    def test_translate_trade_event_minimal(self):
        """Test trade event translation with minimal data."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'trade',
            'step': 100,
            'seller_id': 1,
            'buyer_id': 2,
            'give_type': 'wood',
            'take_type': 'stone'
        }
        
        translated = translator.translate_trade_event(raw_event)
        
        assert translated['event_type'] == 'Trade Execution'
        assert translated['delta_u_seller'] == 0.0
        assert translated['delta_u_buyer'] == 0.0
        assert translated['trade_location_x'] == -1
        assert translated['trade_location_y'] == -1
        
        # Check that description doesn't include utility or location info
        description = translated['description']
        assert 'utility' not in description.lower()
        assert 'location' not in description.lower()
    
    def test_translate_mode_change_event_basic(self):
        """Test basic mode change event translation."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'mode_change',
            'step': 101,
            'agent_id': 1,
            'old_mode': 'foraging',
            'new_mode': 'trading',
            'reason': 'found partner'
        }
        
        translated = translator.translate_mode_change_event(raw_event)
        
        assert translated['event_type'] == 'Agent Mode Change'
        assert translated['step'] == 101
        assert translated['agent_id'] == 1
        assert translated['old_mode'] == 'foraging'
        assert translated['new_mode'] == 'trading'
        assert translated['reason'] == 'found partner'
        
        # Check human-readable fields
        assert 'description' in translated
        assert 'summary' in translated
        assert 'reason_summary' in translated
        assert 'transition_type' in translated
        
        # Verify description format
        description = translated['description']
        assert 'Agent 1' in description
        assert 'foraging' in description
        assert 'trading' in description
        assert 'found partner' in description
        
        # Check transition classification
        assert translated['transition_type'] == 'Forage to Trade'
    
    def test_translate_mode_change_event_no_reason(self):
        """Test mode change event translation without reason."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'mode_change',
            'step': 101,
            'agent_id': 1,
            'old_mode': 'idle',
            'new_mode': 'foraging',
            'reason': ''
        }
        
        translated = translator.translate_mode_change_event(raw_event)
        
        assert translated['reason'] == ''
        assert translated['transition_type'] == 'Activation'
        
        # Check that description doesn't include reason
        description = translated['description']
        assert ':' not in description or not description.split(':')[1].strip()
    
    def test_translate_resource_collection_event_basic(self):
        """Test basic resource collection event translation."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'resource_collection',
            'step': 102,
            'agent_id': 1,
            'x': 5,
            'y': 10,
            'resource_type': 'wood',
            'amount_collected': 2,
            'utility_gained': 5.5,
            'carrying_after': {'wood': 3, 'stone': 1}
        }
        
        translated = translator.translate_resource_collection_event(raw_event)
        
        assert translated['event_type'] == 'Resource Collection'
        assert translated['step'] == 102
        assert translated['agent_id'] == 1
        assert translated['x'] == 5
        assert translated['y'] == 10
        assert translated['resource_type'] == 'wood'
        assert translated['amount_collected'] == 2
        assert translated['utility_gained'] == 5.5
        assert translated['carrying_after'] == {'wood': 3, 'stone': 1}
        
        # Check human-readable fields
        assert 'description' in translated
        assert 'summary' in translated
        assert 'location_summary' in translated
        assert 'inventory_summary' in translated
        assert 'utility_summary' in translated
        
        # Verify description format
        description = translated['description']
        assert 'Agent 1' in description
        assert 'collected 2 wood' in description
        assert '(5, 10)' in description
        assert 'utility gained: +5.50' in description
        
        # Check inventory summary
        assert '3 wood' in translated['inventory_summary']
        assert '1 stone' in translated['inventory_summary']
    
    def test_translate_debug_log_event_basic(self):
        """Test basic debug log event translation."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'debug_log',
            'step': 103,
            'category': 'TRADE',
            'message': 'Trade executed successfully',
            'agent_id': 5
        }
        
        translated = translator.translate_debug_log_event(raw_event)
        
        assert translated['event_type'] == 'Debug Log'
        assert translated['step'] == 103
        assert translated['category'] == 'TRADE'
        assert translated['message'] == 'Trade executed successfully'
        assert translated['agent_id'] == 5
        
        # Check human-readable fields
        assert 'description' in translated
        assert 'summary' in translated
        assert 'category_summary' in translated
        assert 'agent_context' in translated
        assert 'severity' in translated
        
        # Verify description format
        description = translated['description']
        assert '[TRADE]' in description
        assert 'Trade executed successfully' in description
        assert '(Agent 5)' in description
        
        # Check severity classification
        assert translated['severity'] == 'Medium'
        assert translated['category_summary'] == 'Trading activities'
    
    def test_translate_debug_log_event_no_agent(self):
        """Test debug log event translation without agent context."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'debug_log',
            'step': 103,
            'category': 'ERROR',
            'message': 'System error occurred',
            'agent_id': -1
        }
        
        translated = translator.translate_debug_log_event(raw_event)
        
        assert translated['agent_id'] == -1
        assert translated['severity'] == 'High'
        assert translated['agent_context'] == 'No agent context'
        
        # Check that description doesn't include agent info
        description = translated['description']
        assert '(Agent' not in description
    
    def test_translate_performance_monitor_event_basic(self):
        """Test basic performance monitor event translation."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'performance_monitor',
            'step': 104,
            'metric_name': 'steps_per_sec',
            'metric_value': 60.5,
            'threshold_exceeded': False,
            'details': 'Normal performance'
        }
        
        translated = translator.translate_performance_monitor_event(raw_event)
        
        assert translated['event_type'] == 'Performance Monitor'
        assert translated['step'] == 104
        assert translated['metric_name'] == 'steps_per_sec'
        assert translated['metric_value'] == 60.5
        assert translated['threshold_exceeded'] == False
        assert translated['details'] == 'Normal performance'
        
        # Check human-readable fields
        assert 'description' in translated
        assert 'summary' in translated
        assert 'status_summary' in translated
        assert 'value_summary' in translated
        assert 'threshold_summary' in translated
        
        # Verify description format
        description = translated['description']
        assert 'steps_per_sec: 60.50' in description
        assert 'Normal performance' in description
        assert 'THRESHOLD EXCEEDED' not in description
        
        # Check status summary
        assert translated['status_summary'] == '✅ Within normal range'
    
    def test_translate_performance_monitor_event_threshold_exceeded(self):
        """Test performance monitor event translation with threshold exceeded."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'performance_monitor',
            'step': 104,
            'metric_name': 'memory_usage',
            'metric_value': 1024.0,
            'threshold_exceeded': True,
            'details': 'Memory usage above 1GB threshold'
        }
        
        translated = translator.translate_performance_monitor_event(raw_event)
        
        assert translated['threshold_exceeded'] == True
        
        # Check description includes threshold warning
        description = translated['description']
        assert 'THRESHOLD EXCEEDED' in description
        assert 'Memory usage above 1GB threshold' in description
        
        # Check status summary
        assert translated['status_summary'] == '⚠️ Threshold exceeded'
    
    def test_translate_agent_decision_event_basic(self):
        """Test basic agent decision event translation."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'agent_decision',
            'step': 105,
            'agent_id': 1,
            'decision_type': 'movement',
            'decision_details': 'Moving toward resource at (5, 10)',
            'utility_delta': 2.5,
            'position_x': 5,
            'position_y': 10
        }
        
        translated = translator.translate_agent_decision_event(raw_event)
        
        assert translated['event_type'] == 'Agent Decision'
        assert translated['step'] == 105
        assert translated['agent_id'] == 1
        assert translated['decision_type'] == 'movement'
        assert translated['decision_details'] == 'Moving toward resource at (5, 10)'
        assert translated['utility_delta'] == 2.5
        assert translated['position_x'] == 5
        assert translated['position_y'] == 10
        
        # Check human-readable fields
        assert 'description' in translated
        assert 'summary' in translated
        assert 'decision_summary' in translated
        assert 'utility_summary' in translated
        assert 'position_summary' in translated
        
        # Verify description format
        description = translated['description']
        assert 'Agent 1' in description
        assert 'movement decision' in description
        assert 'Moving toward resource at (5, 10)' in description
        assert 'utility change: +2.50' in description
    
    def test_translate_resource_event_basic(self):
        """Test basic resource event translation."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'resource_event',
            'step': 106,
            'event_type_detail': 'spawn',
            'position_x': 15,
            'position_y': 20,
            'resource_type': 'stone',
            'amount': 3,
            'agent_id': -1
        }
        
        translated = translator.translate_resource_event(raw_event)
        
        assert translated['event_type'] == 'Resource Event'
        assert translated['step'] == 106
        assert translated['event_type_detail'] == 'spawn'
        assert translated['position_x'] == 15
        assert translated['position_y'] == 20
        assert translated['resource_type'] == 'stone'
        assert translated['amount'] == 3
        assert translated['agent_id'] == -1
        
        # Check human-readable fields
        assert 'description' in translated
        assert 'summary' in translated
        assert 'event_summary' in translated
        assert 'location_summary' in translated
        assert 'agent_context' in translated
        
        # Verify description format
        description = translated['description']
        assert 'Spawn 3 stone at (15, 20)' in description
        
        # Check agent context
        assert translated['agent_context'] == 'No agent context'
    
    def test_translate_economic_decision_event_basic(self):
        """Test basic economic decision event translation."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'economic_decision',
            'step': 107,
            'agent_id': 1,
            'decision_type': 'resource_selection',
            'decision_context': 'Choosing between wood and stone resources',
            'utility_before': 10.0,
            'utility_after': 15.0,
            'utility_delta': 5.0,
            'opportunity_cost': 2.0,
            'alternatives_considered': 3,
            'decision_time_ms': 5.5,
            'position_x': 10,
            'position_y': 15
        }
        
        translated = translator.translate_economic_decision_event(raw_event)
        
        assert translated['event_type'] == 'Economic Decision'
        assert translated['step'] == 107
        assert translated['agent_id'] == 1
        assert translated['decision_type'] == 'resource_selection'
        assert translated['decision_context'] == 'Choosing between wood and stone resources'
        assert translated['utility_before'] == 10.0
        assert translated['utility_after'] == 15.0
        assert translated['utility_delta'] == 5.0
        assert translated['opportunity_cost'] == 2.0
        assert translated['alternatives_considered'] == 3
        assert translated['decision_time_ms'] == 5.5
        assert translated['position_x'] == 10
        assert translated['position_y'] == 15
        
        # Check human-readable fields
        assert 'description' in translated
        assert 'summary' in translated
        assert 'utility_analysis' in translated
        assert 'decision_analysis' in translated
        assert 'performance_analysis' in translated
        
        # Verify description format
        description = translated['description']
        assert 'Agent 1' in description
        assert 'resource_selection economic decision' in description
        assert 'Choosing between wood and stone resources' in description
        assert 'utility change: +5.00' in description
        assert 'considered 3 alternatives' in description
        
        # Check utility analysis
        assert '10.00 → 15.00 (Δ+5.00)' in translated['utility_analysis']
        assert 'Opportunity cost: 2.00' in translated['utility_analysis']
    
    def test_translate_gui_display_event_basic(self):
        """Test basic GUI display event translation."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'gui_display',
            'step': 108,
            'display_type': 'highlight',
            'element_id': 'agent_1',
            'data': {'color': 'red', 'duration': 2.0}
        }
        
        translated = translator.translate_gui_display_event(raw_event)
        
        assert translated['event_type'] == 'GUI Display'
        assert translated['step'] == 108
        assert translated['display_type'] == 'highlight'
        assert translated['element_id'] == 'agent_1'
        assert translated['data'] == {'color': 'red', 'duration': 2.0}
        
        # Check human-readable fields
        assert 'description' in translated
        assert 'summary' in translated
        assert 'display_summary' in translated
        assert 'data_summary' in translated
        
        # Verify description format
        description = translated['description']
        assert 'GUI highlight update for agent_1' in description
        assert 'with 2 data fields' in description
        
        # Check data summary
        assert 'color' in translated['data_summary']
        assert 'duration' in translated['data_summary']


class TestDataTranslatorGenericMethod:
    """Test generic translate_event() method for any event type."""
    
    def test_translate_event_trade(self):
        """Test generic translation for trade event."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'trade',
            'step': 100,
            'seller_id': 1,
            'buyer_id': 2,
            'give_type': 'wood',
            'take_type': 'stone'
        }
        
        translated = translator.translate_event(raw_event)
        
        assert translated['event_type'] == 'Trade Execution'
        assert 'description' in translated
        assert 'summary' in translated
        assert 'raw_data' in translated
    
    def test_translate_event_mode_change(self):
        """Test generic translation for mode change event."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'mode_change',
            'step': 101,
            'agent_id': 1,
            'old_mode': 'foraging',
            'new_mode': 'trading',
            'reason': 'found partner'
        }
        
        translated = translator.translate_event(raw_event)
        
        assert translated['event_type'] == 'Agent Mode Change'
        assert 'description' in translated
        assert 'summary' in translated
        assert 'raw_data' in translated
    
    def test_translate_event_unknown(self):
        """Test generic translation for unknown event type."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'unknown_event',
            'step': 100,
            'some_field': 'some_value'
        }
        
        translated = translator.translate_event(raw_event)
        
        assert translated['event_type'] == 'Unknown Event'
        assert 'Unknown event type: unknown_event' in translated['description']
        assert 'Unknown event at step 100' in translated['summary']
        assert 'raw_data' in translated
    
    def test_translate_event_missing_type(self):
        """Test generic translation for event with missing type."""
        translator = DataTranslator()
        
        raw_event = {
            'step': 100,
            'some_field': 'some_value'
        }
        
        translated = translator.translate_event(raw_event)
        
        assert translated['event_type'] == 'Unknown Event'
        assert 'Unknown event type: unknown' in translated['description']


class TestDataTranslatorBatchMethods:
    """Test batch translation methods."""
    
    def test_translate_events(self):
        """Test translating a list of events."""
        translator = DataTranslator()
        
        raw_events = [
            {
                'type': 'trade',
                'step': 100,
                'seller_id': 1,
                'buyer_id': 2,
                'give_type': 'wood',
                'take_type': 'stone'
            },
            {
                'type': 'mode_change',
                'step': 101,
                'agent_id': 1,
                'old_mode': 'foraging',
                'new_mode': 'trading',
                'reason': 'found partner'
            }
        ]
        
        translated_events = translator.translate_events(raw_events)
        
        assert len(translated_events) == 2
        assert translated_events[0]['event_type'] == 'Trade Execution'
        assert translated_events[1]['event_type'] == 'Agent Mode Change'
    
    def test_translate_events_by_type(self):
        """Test translating events of a specific type."""
        translator = DataTranslator()
        
        raw_events = [
            {
                'type': 'trade',
                'step': 100,
                'seller_id': 1,
                'buyer_id': 2,
                'give_type': 'wood',
                'take_type': 'stone'
            },
            {
                'type': 'mode_change',
                'step': 101,
                'agent_id': 1,
                'old_mode': 'foraging',
                'new_mode': 'trading',
                'reason': 'found partner'
            },
            {
                'type': 'trade',
                'step': 102,
                'seller_id': 2,
                'buyer_id': 3,
                'give_type': 'stone',
                'take_type': 'wood'
            }
        ]
        
        trade_events = translator.translate_events_by_type(raw_events, 'trade')
        
        assert len(trade_events) == 2
        assert all(event['event_type'] == 'Trade Execution' for event in trade_events)
        assert trade_events[0]['seller_id'] == 1
        assert trade_events[1]['seller_id'] == 2
    
    def test_translate_events_by_step(self):
        """Test translating events from a specific step."""
        translator = DataTranslator()
        
        raw_events = [
            {
                'type': 'trade',
                'step': 100,
                'seller_id': 1,
                'buyer_id': 2,
                'give_type': 'wood',
                'take_type': 'stone'
            },
            {
                'type': 'mode_change',
                'step': 101,
                'agent_id': 1,
                'old_mode': 'foraging',
                'new_mode': 'trading',
                'reason': 'found partner'
            },
            {
                'type': 'debug_log',
                'step': 100,
                'category': 'TRADE',
                'message': 'Trade completed',
                'agent_id': -1
            }
        ]
        
        step_100_events = translator.translate_events_by_step(raw_events, 100)
        
        assert len(step_100_events) == 2
        assert step_100_events[0]['event_type'] == 'Trade Execution'
        assert step_100_events[1]['event_type'] == 'Debug Log'


class TestDataTranslatorHumanReadableMethods:
    """Test human-readable description methods."""
    
    def test_get_human_readable_description(self):
        """Test getting human-readable description for an event."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'trade',
            'step': 100,
            'seller_id': 1,
            'buyer_id': 2,
            'give_type': 'wood',
            'take_type': 'stone'
        }
        
        description = translator.get_human_readable_description(raw_event)
        
        assert isinstance(description, str)
        assert 'Agent 1' in description
        assert 'wood' in description
        assert 'stone' in description
        assert 'Agent 2' in description
    
    def test_get_human_readable_summary(self):
        """Test getting human-readable summary for an event."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'mode_change',
            'step': 101,
            'agent_id': 1,
            'old_mode': 'foraging',
            'new_mode': 'trading',
            'reason': 'found partner'
        }
        
        summary = translator.get_human_readable_summary(raw_event)
        
        assert isinstance(summary, str)
        assert 'Agent 1' in summary
        assert 'foraging' in summary
        assert 'trading' in summary
    
    def test_get_human_readable_descriptions(self):
        """Test getting human-readable descriptions for a list of events."""
        translator = DataTranslator()
        
        raw_events = [
            {
                'type': 'trade',
                'step': 100,
                'seller_id': 1,
                'buyer_id': 2,
                'give_type': 'wood',
                'take_type': 'stone'
            },
            {
                'type': 'mode_change',
                'step': 101,
                'agent_id': 1,
                'old_mode': 'foraging',
                'new_mode': 'trading',
                'reason': 'found partner'
            }
        ]
        
        descriptions = translator.get_human_readable_descriptions(raw_events)
        
        assert len(descriptions) == 2
        assert isinstance(descriptions[0], str)
        assert isinstance(descriptions[1], str)
        assert 'Agent 1' in descriptions[0]
        assert 'foraging' in descriptions[1]


class TestDataTranslatorUtilityMethods:
    """Test utility methods and edge cases."""
    
    def test_clear_cache(self):
        """Test clearing translation cache."""
        translator = DataTranslator()
        
        # Cache should be empty by default
        cache_stats = translator.get_cache_stats()
        assert cache_stats['cache_size'] == 0
        
        # Clear cache (should not error)
        translator.clear_cache()
        
        # Cache should still be empty
        cache_stats = translator.get_cache_stats()
        assert cache_stats['cache_size'] == 0
    
    def test_enable_cache(self):
        """Test enabling/disabling translation cache."""
        translator = DataTranslator()
        
        # Cache should be disabled by default
        cache_stats = translator.get_cache_stats()
        assert not cache_stats['cache_enabled']
        
        # Enable cache
        translator.enable_cache(True)
        cache_stats = translator.get_cache_stats()
        assert cache_stats['cache_enabled']
        
        # Disable cache
        translator.enable_cache(False)
        cache_stats = translator.get_cache_stats()
        assert not cache_stats['cache_enabled']
    
    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        translator = DataTranslator()
        
        cache_stats = translator.get_cache_stats()
        
        assert 'cache_enabled' in cache_stats
        assert 'cache_size' in cache_stats
        assert 'cache_hit_rate' in cache_stats
        
        assert isinstance(cache_stats['cache_enabled'], bool)
        assert isinstance(cache_stats['cache_size'], int)
        assert isinstance(cache_stats['cache_hit_rate'], float)
    
    def test_repr_method(self):
        """Test __repr__ method."""
        translator = DataTranslator()
        
        repr_str = repr(translator)
        
        assert 'DataTranslator' in repr_str
        assert 'cache_enabled' in repr_str
        assert 'cache_size' in repr_str


class TestDataTranslatorEdgeCases:
    """Test edge cases and error handling."""
    
    def test_missing_fields_handling(self):
        """Test handling of missing fields in raw events."""
        translator = DataTranslator()
        
        # Trade event with missing fields
        raw_event = {
            'type': 'trade',
            'step': 100
            # Missing seller_id, buyer_id, etc.
        }
        
        translated = translator.translate_trade_event(raw_event)
        
        # Should use default values
        assert translated['seller_id'] == -1
        assert translated['buyer_id'] == -1
        assert translated['give_type'] == 'unknown'
        assert translated['take_type'] == 'unknown'
        
        # Description should still be generated
        assert 'description' in translated
        assert isinstance(translated['description'], str)
    
    def test_empty_string_fields(self):
        """Test handling of empty string fields."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'mode_change',
            'step': 101,
            'agent_id': 1,
            'old_mode': '',
            'new_mode': '',
            'reason': ''
        }
        
        translated = translator.translate_mode_change_event(raw_event)
        
        assert translated['old_mode'] == ''
        assert translated['new_mode'] == ''
        assert translated['reason'] == ''
        
        # Description should still be generated
        assert 'description' in translated
        assert isinstance(translated['description'], str)
    
    def test_none_values_handling(self):
        """Test handling of None values in raw events."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'debug_log',
            'step': 103,
            'category': 'TRADE',
            'message': None,
            'agent_id': None
        }
        
        translated = translator.translate_debug_log_event(raw_event)
        
        # Should handle None values gracefully
        assert translated['message'] is None
        assert translated['agent_id'] is None
        
        # Description should still be generated
        assert 'description' in translated
        assert isinstance(translated['description'], str)
    
    def test_large_data_handling(self):
        """Test handling of large data in raw events."""
        translator = DataTranslator()
        
        # Create event with large data
        large_string = "x" * 1000
        large_dict = {f"key_{i}": f"value_{i}" for i in range(100)}
        
        raw_event = {
            'type': 'gui_display',
            'step': 108,
            'display_type': 'overlay',
            'element_id': 'large_panel',
            'data': {
                'large_string': large_string,
                'large_dict': large_dict
            }
        }
        
        translated = translator.translate_gui_display_event(raw_event)
        
        assert translated['data']['large_string'] == large_string
        assert translated['data']['large_dict'] == large_dict
        
        # Description should still be generated
        assert 'description' in translated
        assert 'with 2 data fields' in translated['description']
    
    def test_unicode_handling(self):
        """Test handling of unicode characters in raw events."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'debug_log',
            'step': 103,
            'category': 'UNICODE',
            'message': 'Hello 世界 🌍 émojis',
            'agent_id': 1
        }
        
        translated = translator.translate_debug_log_event(raw_event)
        
        assert translated['message'] == 'Hello 世界 🌍 émojis'
        
        # Description should handle unicode
        description = translated['description']
        assert '世界' in description
        assert '🌍' in description
        assert 'émojis' in description
    
    def test_numeric_precision_handling(self):
        """Test handling of numeric precision in raw events."""
        translator = DataTranslator()
        
        raw_event = {
            'type': 'trade',
            'step': 100,
            'seller_id': 1,
            'buyer_id': 2,
            'give_type': 'wood',
            'take_type': 'stone',
            'delta_u_seller': 5.123456789,
            'delta_u_buyer': -2.987654321
        }
        
        translated = translator.translate_trade_event(raw_event)
        
        # Should preserve original precision
        assert translated['delta_u_seller'] == 5.123456789
        assert translated['delta_u_buyer'] == -2.987654321
        
        # Description should format with reasonable precision
        description = translated['description']
        assert '5.12' in description or '5.1' in description
        assert '-2.99' in description or '-3.0' in description


if __name__ == "__main__":
    pytest.main([__file__])
