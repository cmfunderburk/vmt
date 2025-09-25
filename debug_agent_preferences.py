#!/usr/bin/env python3
"""Debug which preference types are actually being assigned in Test 2."""

import os
import sys
import random

# Add src to path
sys.path.insert(0, "/home/chris/PROJECTS/vmt/src")

from econsim.preferences.factory import PreferenceFactory

def debug_preference_assignment():
    """Debug the mixed preference factory assignment."""
    
    print("=== Preference Assignment Debug ===\n")
    
    def create_mixed_preference_factory():
        """Create factory that randomly assigns different preference types."""
        preferences = ["cobb_douglas", "leontief", "perfect_substitutes"]
        
        def factory(agent_id: int):
            # Use agent_id as seed for deterministic but varied assignment
            local_rng = random.Random(agent_id * 17 + 42)
            pref_type = local_rng.choice(preferences)
            return PreferenceFactory.create(pref_type)
        
        return factory
    
    # Test with 40 agents (same as Test 2)
    factory = create_mixed_preference_factory()
    
    print("Agent preference assignments for Test 2 (40 agents):")
    pref_counts = {"cobb_douglas": 0, "leontief": 0, "perfect_substitutes": 0}
    
    for agent_id in range(40):
        # Simulate the factory logic
        local_rng = random.Random(agent_id * 17 + 42)
        pref_type = local_rng.choice(["cobb_douglas", "leontief", "perfect_substitutes"])
        pref_counts[pref_type] += 1
        
        if agent_id < 10:  # Show first 10 for detail
            print(f"  Agent {agent_id}: {pref_type}")
    
    print(f"\nTotal distribution:")
    for pref_type, count in pref_counts.items():
        print(f"  {pref_type}: {count} agents ({count/40*100:.1f}%)")
    
    # Check which pairs might trade
    print(f"\nAgent pairs that might generate trade intents:")
    trade_pairs = []
    
    for i in range(40):
        local_rng_i = random.Random(i * 17 + 42)
        pref_i = local_rng_i.choice(["cobb_douglas", "leontief", "perfect_substitutes"])
        
        for j in range(i + 1, 40):
            local_rng_j = random.Random(j * 17 + 42)
            pref_j = local_rng_j.choice(["cobb_douglas", "leontief", "perfect_substitutes"])
            
            # Perfect substitutes won't trade with anyone (MU always equal)
            if pref_i == "perfect_substitutes" or pref_j == "perfect_substitutes":
                continue
                
            # Other combinations might trade
            if pref_i != pref_j or pref_i == "cobb_douglas" or pref_i == "leontief":
                trade_pairs.append((i, j, pref_i, pref_j))
    
    print(f"  Found {len(trade_pairs)} potential trading pairs (excluding perfect_substitutes)")
    
    if len(trade_pairs) > 0:
        print("  Examples (first 5):")
        for i, (agent_i, agent_j, pref_i, pref_j) in enumerate(trade_pairs[:5]):
            print(f"    Agent {agent_i} ({pref_i}) <-> Agent {agent_j} ({pref_j})")
    
    # Specifically check agents 18 and 39 (from the test output)
    print(f"\nSpecific agents from test output:")
    for agent_id in [18, 22, 39]:
        local_rng = random.Random(agent_id * 17 + 42)
        pref_type = local_rng.choice(["cobb_douglas", "leontief", "perfect_substitutes"])
        print(f"  Agent {agent_id}: {pref_type}")

if __name__ == "__main__":
    debug_preference_assignment()