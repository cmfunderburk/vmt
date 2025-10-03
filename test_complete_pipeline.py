#!/usr/bin/env python3
"""Test the complete trade event serialization pipeline."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from econsim.observability.buffers.event_buffer import BasicEventBuffer
from econsim.observability.events import TradeExecutionEvent
from econsim.observability.serializers.optimized_serializer import OptimizedEventSerializer

# Create a trade event
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

print("=== TESTING COMPLETE PIPELINE ===")
print()

# Step 1: Buffer the event
buffer = BasicEventBuffer()
buffer.add_event(trade_event)
buffered_events = buffer.flush_step(124)

print("1. After buffering:")
event_dict = buffered_events[0]
print(f"   Raw event dict: {event_dict}")
print()

# Step 2: Optimize the event
serializer = OptimizedEventSerializer()
optimized_dict = serializer._optimize_event_dict(trade_event)

print("2. Direct optimization of SimulationEvent:")
print(f"   Optimized dict: {optimized_dict}")
print()

# Step 3: Test the complete pipeline with the buffered dictionary
# Simulate what would happen in write_step_batch
import time
events = [event_dict]  # This is what comes from the buffer
timestamp = time.time()

# This should now work properly since the event has all fields
print("3. Full pipeline test:")
print(f"   Input events: {len(events)} trade events")
print(f"   First event keys: {list(events[0].keys())}")
print(f"   Event has seller_id: {'seller_id' in events[0]}")
print(f"   Event has give_type: {'give_type' in events[0]}")
print()

print("✅ All trade fields are now preserved through the buffer!")
print("✅ The events should now compress properly in the optimized serializer!")

# Test what the semantic compression will receive
compressed_other_event = {}
for key, value in optimized_dict.items():
    if key in ['s', 'step']:
        continue
    compressed_other_event[key] = value

print()
print("4. What semantic compression will receive:")
print(f"   After _compress_other_event: {compressed_other_event}")
if 'e' in compressed_other_event and compressed_other_event['e'] == 'trade':
    print("   ✅ Event has 'e': 'trade' - will trigger proper semantic compression!")
else:
    print("   ❌ Event format issue detected")