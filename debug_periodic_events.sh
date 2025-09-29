#!/bin/bash
# Debug script to set all periodic emission intervals to 1 (every step)
# This makes it easier to see if the instrumentation is working

echo "Setting all periodic emission intervals to 1 (every step) for debugging..."

# Selection sample - normally every 200 steps, now every step
export ECONSIM_SELECTION_SAMPLE_PERIOD=1

# Target churn - normally every 500 steps, now every step  
export ECONSIM_CHURN_EMIT_PERIOD=1

# Partner search sample - normally every 1 step (already frequent)
export ECONSIM_PARTNER_SEARCH_SAMPLE_PERIOD=1

# Churn window - normally 100 steps, reduce to 10 for more frequent updates
export ECONSIM_CHURN_WINDOW=10

# Performance spike factor - lower threshold to catch more spikes
export ECONSIM_PERF_SPIKE_FACTOR=1.1

# Enable all debug categories
export ECONSIM_LOG_LEVEL=VERBOSE
export ECONSIM_LOG_FORMAT=STRUCTURED

# Enable all debug flags
export ECONSIM_DEBUG_AGENT_MODES=1
export ECONSIM_DEBUG_ECONOMICS=1
export ECONSIM_DEBUG_TRADES=1
export ECONSIM_DEBUG_PERFORMANCE=1
export ECONSIM_DEBUG_DECISIONS=1
export ECONSIM_DEBUG_RESOURCES=1
export ECONSIM_DEBUG_SPATIAL=1
export ECONSIM_DEBUG_PHASES=1
export ECONSIM_DEBUG_SIMULATION=1

# Enable trade features
export ECONSIM_TRADE_DRAFT=1
export ECONSIM_TRADE_EXEC=1

# Enable foraging
export ECONSIM_FORAGE_ENABLED=1

echo "Environment variables set:"
echo "  ECONSIM_SELECTION_SAMPLE_PERIOD=$ECONSIM_SELECTION_SAMPLE_PERIOD"
echo "  ECONSIM_CHURN_EMIT_PERIOD=$ECONSIM_CHURN_EMIT_PERIOD"
echo "  ECONSIM_PARTNER_SEARCH_SAMPLE_PERIOD=$ECONSIM_PARTNER_SEARCH_SAMPLE_PERIOD"
echo "  ECONSIM_CHURN_WINDOW=$ECONSIM_CHURN_WINDOW"
echo "  ECONSIM_PERF_SPIKE_FACTOR=$ECONSIM_PERF_SPIKE_FACTOR"
echo "  ECONSIM_LOG_LEVEL=$ECONSIM_LOG_LEVEL"
echo ""
echo "Now run your manual tests - all periodic events should emit every step!"
echo ""
echo "To run the simulation with these settings:"
echo "  source vmt-dev/bin/activate"
echo "  make dev"
