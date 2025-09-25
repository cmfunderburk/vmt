#!/usr/bin/env python3
"""Debug marginal utilities for perfect substitutes."""

import sys
sys.path.insert(0, "/home/chris/PROJECTS/vmt/src")

from econsim.preferences.factory import PreferenceFactory
from econsim.preferences.helpers import marginal_utility

def test_perfect_substitutes_marginal_utilities():
    """Test marginal utilities for perfect substitutes with different bundles."""
    
    print("=== Perfect Substitutes Marginal Utility Debug ===\n")
    
    pref = PreferenceFactory.create("perfect_substitutes")  # Default a=1.0, b=1.0
    
    test_cases = [
        ("Equal bundles", {"good1": 5, "good2": 5}, {"good1": 0, "good2": 0}),
        ("More good1", {"good1": 10, "good2": 2}, {"good1": 0, "good2": 0}),
        ("More good2", {"good1": 2, "good2": 10}, {"good1": 0, "good2": 0}),
        ("Only good1", {"good1": 8, "good2": 0}, {"good1": 0, "good2": 0}),
        ("Only good2", {"good1": 0, "good2": 8}, {"good1": 0, "good2": 0}),
    ]
    
    for description, carrying, home in test_cases:
        print(f"{description}: carrying={carrying}, home={home}")
        
        # Calculate total bundle
        total_good1 = carrying.get("good1", 0) + home.get("good1", 0)
        total_good2 = carrying.get("good2", 0) + home.get("good2", 0)
        total_bundle = (total_good1, total_good2)
        
        # Calculate utility
        utility = pref.utility(total_bundle)
        print(f"  Total bundle: {total_bundle}, utility: {utility}")
        
        # Calculate marginal utilities
        mu = marginal_utility(pref, carrying, home, epsilon_lift=True, include_missing_two_goods=True)
        print(f"  Marginal utilities: {mu}")
        
        # For perfect substitutes, marginal utility should equal the coefficient
        # MU_good1 = a = 1.0, MU_good2 = b = 1.0 (regardless of bundle composition)
        print(f"  Expected MU: good1=1.0, good2=1.0 (coefficients)")
        print()

if __name__ == "__main__":
    test_perfect_substitutes_marginal_utilities()