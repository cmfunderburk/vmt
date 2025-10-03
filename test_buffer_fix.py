#!/usr/bin/env python3
"""Test the BasicEventBuffer fix for trade events."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from econsim.observability.buffers.event_buffer import BasicEventBuffer
from econsim.observability.events import TradeExecutionEvent

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

print("Original trade event fields:")
print(f"  seller_id: {trade_event.seller_id}")
print(f"  buyer_id: {trade_event.buyer_id}")
print(f"  give_type: {trade_event.give_type}")
print(f"  take_type: {trade_event.take_type}")
print(f"  delta_u_seller: {trade_event.delta_u_seller}")
print(f"  delta_u_buyer: {trade_event.delta_u_buyer}")
print(f"  trade_location_x: {trade_event.trade_location_x}")
print(f"  trade_location_y: {trade_event.trade_location_y}")
print()

# Test BasicEventBuffer
buffer = BasicEventBuffer()
buffer.add_event(trade_event)

# Flush the buffer
buffered_events = buffer.flush_step(124)
print("Buffered event (should now contain ALL fields):")
if buffered_events:
    event_dict = buffered_events[0]
    print(f"  Keys in buffered event: {list(event_dict.keys())}")
    print(f"  seller_id: {event_dict.get('seller_id', 'MISSING!')}")
    print(f"  buyer_id: {event_dict.get('buyer_id', 'MISSING!')}")
    print(f"  give_type: {event_dict.get('give_type', 'MISSING!')}")
    print(f"  take_type: {event_dict.get('take_type', 'MISSING!')}")
    print(f"  delta_u_seller: {event_dict.get('delta_u_seller', 'MISSING!')}")
    print(f"  delta_u_buyer: {event_dict.get('delta_u_buyer', 'MISSING!')}")
    print(f"  Full event dict: {event_dict}")
else:
    print("  No events in buffer!")