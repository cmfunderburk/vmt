"""Custom Generated Test: Duplicate ID Scenario
Created: 2025-09-27
"""

# Same stem name pattern as valid_case purposely not — but we will simulate duplicate by copying stem name.
# To force duplicate ID we reuse filename 'valid_case' pattern by referencing within test (discovery uses stem) —
# Instead we create a second file with same metadata but unique filename; duplicate detection left to registry later.
CUSTOM_CONFIG = TestConfiguration(
    grid_size=(12, 12),
    agent_count=20,
    resource_density=0.25,
    preference_mix="perfect_substitutes",
)
