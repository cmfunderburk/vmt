#!/usr/bin/env python3
"""Debug script to check trade event serialization format."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from econsim.observability.serializers.optimized_serializer import OptimizedEventSerializer
from econsim.observability.events import TradeExecutionEvent

# Create a sample trade event using factory method
trade_event = TradeExecutionEvent.create(
    step=124,
    seller_id=1,
    buyer_id=2,
    give_type='resource1',
    take_type='resource2',
    delta_u_seller=0.5,
    delta_u_buyer=0.3,
    trade_location_x=5,
    trade_location_y=7
)

# Initialize serializer
serializer = OptimizedEventSerializer()

print("Original trade event:")
print(f"Step: {trade_event.step}")
print(f"Timestamp: {trade_event.timestamp}")
print(f"Event type: {trade_event.event_type}")
print(f"Seller ID: {trade_event.seller_id}")
print(f"Buyer ID: {trade_event.buyer_id}")
print()

# Serialize the event
serialized = serializer.serialize_event(trade_event)
print("Serialized trade event:")
print(serialized)
print()

# Test optimized event dict creation
optimized_dict = serializer._optimize_event_dict(trade_event)
print("Optimized event dict:")
print(optimized_dict)
print()

# Simulate what _compress_other_event would do
print("Simulating _compress_other_event processing...")
compressed_other_event = {}
for key, value in optimized_dict.items():
    if key in ['s', 'step']:
        continue
    compressed_other_event[key] = value

print("After _compress_other_event:")
print(compressed_other_event)
print()

# This is what gets passed to semantic compression in the 'other_events' list
print("This dictionary would be passed to _compress_single_event_semantic as 'other' event type")
print("And since it's a dict with 'e': 'trade', it should match the new compression logic")
print()

# Show what the problematic string representation looks like 
print("If it falls back to str() representation:")
print(f"str(compressed_other_event) = {str(compressed_other_event)}")
print()
print("But we want semantic compression instead!")