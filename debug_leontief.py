#!/usr/bin/env python3
"""Debug Leontief delta utility calculation edge cases."""

import sys
sys.path.insert(0, "/home/chris/PROJECTS/vmt/src")

from econsim.preferences.factory import PreferenceFactory

def test_leontief_edge_cases():
    """Test specific Leontief scenarios that might yield 0 delta utility."""
    
    print("=== Leontief Delta Utility Edge Cases ===\n")
    
    pref = PreferenceFactory.create("leontief")  # Default a=1.0, b=1.0
    
    # Case 1: Agents at kink points (min constraint switches)
    print("Case 1: Both agents at kink points")
    
    # Agent A has excess good1 (constrained by good2)
    bundle_a = (10.0, 2.0)  # min(10, 2) = 2
    util_a_before = pref.utility(bundle_a)
    print(f"Agent A before: bundle={bundle_a}, utility={util_a_before}")
    
    # Agent B has excess good2 (constrained by good1)  
    bundle_b = (2.0, 10.0)  # min(2, 10) = 2
    util_b_before = pref.utility(bundle_b)
    print(f"Agent B before: bundle={bundle_b}, utility={util_b_before}")
    
    # After trade: A gives good1, B gives good2
    bundle_a_after = (9.0, 3.0)  # min(9, 3) = 3 -> +1 utility!
    bundle_b_after = (3.0, 9.0)  # min(3, 9) = 3 -> +1 utility!
    
    util_a_after = pref.utility(bundle_a_after)
    util_b_after = pref.utility(bundle_b_after)
    
    print(f"Agent A after:  bundle={bundle_a_after}, utility={util_a_after}")
    print(f"Agent B after:  bundle={bundle_b_after}, utility={util_b_after}")
    
    delta_u = (util_a_after + util_b_after) - (util_a_before + util_b_before)
    print(f"Delta utility: {delta_u} (should be +2)")
    
    print()
    
    # Case 2: Agents already at optimal balance
    print("Case 2: Both agents already balanced")
    
    bundle_a_balanced = (5.0, 5.0)  # min(5, 5) = 5
    bundle_b_balanced = (5.0, 5.0)  # min(5, 5) = 5
    
    util_a_balanced = pref.utility(bundle_a_balanced)
    util_b_balanced = pref.utility(bundle_b_balanced)
    
    print(f"Agent A before: bundle={bundle_a_balanced}, utility={util_a_balanced}")
    print(f"Agent B before: bundle={bundle_b_balanced}, utility={util_b_balanced}")
    
    # After trade: A gives good1, B gives good2  
    bundle_a_after_balanced = (4.0, 6.0)  # min(4, 6) = 4 -> -1 utility
    bundle_b_after_balanced = (6.0, 4.0)  # min(6, 4) = 4 -> -1 utility
    
    util_a_after_balanced = pref.utility(bundle_a_after_balanced)
    util_b_after_balanced = pref.utility(bundle_b_after_balanced)
    
    print(f"Agent A after:  bundle={bundle_a_after_balanced}, utility={util_a_after_balanced}")  
    print(f"Agent B after:  bundle={bundle_b_after_balanced}, utility={util_b_after_balanced}")
    
    delta_u_balanced = (util_a_after_balanced + util_b_after_balanced) - (util_a_balanced + util_b_balanced)
    print(f"Delta utility: {delta_u_balanced} (should be -2, so no trade should occur)")
    
    print()
    
    # Case 3: The problematic scenario - equal utilities but different constraints
    print("Case 3: Equal utilities, different constraints")
    
    # Both have utility=3, but different limiting factors
    bundle_a_prob = (8.0, 3.0)  # min(8, 3) = 3, limited by good2
    bundle_b_prob = (3.0, 8.0)  # min(3, 8) = 3, limited by good1
    
    util_a_prob = pref.utility(bundle_a_prob)
    util_b_prob = pref.utility(bundle_b_prob)
    
    print(f"Agent A before: bundle={bundle_a_prob}, utility={util_a_prob}")
    print(f"Agent B before: bundle={bundle_b_prob}, utility={util_b_prob}")
    
    # After trade: A gives good1, B gives good2
    bundle_a_after_prob = (7.0, 4.0)  # min(7, 4) = 4 -> +1 utility  
    bundle_b_after_prob = (4.0, 7.0)  # min(4, 7) = 4 -> +1 utility
    
    util_a_after_prob = pref.utility(bundle_a_after_prob)
    util_b_after_prob = pref.utility(bundle_b_after_prob)
    
    print(f"Agent A after:  bundle={bundle_a_after_prob}, utility={util_a_after_prob}")
    print(f"Agent B after:  bundle={bundle_b_after_prob}, utility={util_b_after_prob}")
    
    delta_u_prob = (util_a_after_prob + util_b_after_prob) - (util_a_prob + util_b_prob)
    print(f"Delta utility: {delta_u_prob} (should be +2)")
    
    # Now test with epsilon added (like in the actual calculation)
    print("\nTesting with epsilon (1e-12) like in _compute_exact_utility_delta:")
    
    EPSILON = 1e-12
    bundle_a_eps = (8.0 + EPSILON, 3.0 + EPSILON)
    bundle_b_eps = (3.0 + EPSILON, 8.0 + EPSILON) 
    
    util_a_eps = pref.utility(bundle_a_eps)
    util_b_eps = pref.utility(bundle_b_eps)
    
    print(f"Agent A before (with ε): bundle={bundle_a_eps}, utility={util_a_eps}")
    print(f"Agent B before (with ε): bundle={bundle_b_eps}, utility={util_b_eps}")
    
    bundle_a_after_eps = (7.0 + EPSILON, 4.0 + EPSILON)
    bundle_b_after_eps = (4.0 + EPSILON, 7.0 + EPSILON)
    
    util_a_after_eps = pref.utility(bundle_a_after_eps)
    util_b_after_eps = pref.utility(bundle_b_after_eps)
    
    print(f"Agent A after (with ε):  bundle={bundle_a_after_eps}, utility={util_a_after_eps}")
    print(f"Agent B after (with ε):  bundle={bundle_b_after_eps}, utility={util_b_after_eps}")
    
    delta_u_eps = (util_a_after_eps + util_b_after_eps) - (util_a_eps + util_b_eps)
    print(f"Delta utility (with ε): {delta_u_eps}")

if __name__ == "__main__":
    test_leontief_edge_cases()