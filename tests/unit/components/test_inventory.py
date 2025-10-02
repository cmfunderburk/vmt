"""Unit tests for AgentInventory component."""

import pytest
from unittest.mock import Mock
from econsim.simulation.components.inventory import AgentInventory
from econsim.preferences.cobb_douglas import CobbDouglasPreference


class TestAgentInventory:
    def test_init(self):
        """Test AgentInventory initialization."""
        preference = CobbDouglasPreference(alpha=0.5)
        inventory = AgentInventory(preference)
        
        assert inventory.preference == preference
        assert inventory.carrying == {"good1": 0, "good2": 0}
        assert inventory.home_inventory == {"good1": 0, "good2": 0}
        assert inventory.inventory == inventory.carrying  # Alias test
    
    def test_carrying_total(self):
        """Test carrying total calculation."""
        preference = CobbDouglasPreference(alpha=0.5)
        inventory = AgentInventory(preference)
        
        assert inventory.carrying_total() == 0
        
        inventory.carrying["good1"] = 3
        inventory.carrying["good2"] = 2
        assert inventory.carrying_total() == 5
    
    def test_current_bundle(self):
        """Test current bundle calculation from total wealth."""
        preference = CobbDouglasPreference(alpha=0.5)
        inventory = AgentInventory(preference)
        
        # Test empty inventory
        bundle = inventory.current_bundle()
        assert bundle == (0.0, 0.0)
        
        # Test carrying only
        inventory.carrying["good1"] = 2
        inventory.carrying["good2"] = 1
        bundle = inventory.current_bundle()
        assert bundle == (2.0, 1.0)
        
        # Test home inventory only
        inventory.carrying["good1"] = 0
        inventory.carrying["good2"] = 0
        inventory.home_inventory["good1"] = 3
        inventory.home_inventory["good2"] = 2
        bundle = inventory.current_bundle()
        assert bundle == (3.0, 2.0)
        
        # Test combined
        inventory.carrying["good1"] = 1
        inventory.carrying["good2"] = 1
        bundle = inventory.current_bundle()
        assert bundle == (4.0, 3.0)
    
    def test_current_utility(self):
        """Test current utility calculation."""
        preference = CobbDouglasPreference(alpha=0.5)
        inventory = AgentInventory(preference)
        
        # Test with zero bundle (should use epsilon)
        utility = inventory.current_utility()
        assert utility > 0  # Should be positive due to epsilon
        
        # Test with non-zero bundle
        inventory.carrying["good1"] = 4
        inventory.carrying["good2"] = 4
        utility = inventory.current_utility()
        expected = preference.utility((4.0, 4.0))
        assert utility == expected
    
    def test_deposit_all(self):
        """Test depositing all carried goods."""
        preference = CobbDouglasPreference(alpha=0.5)
        inventory = AgentInventory(preference)
        
        # Test empty carrying
        result = inventory.deposit_all()
        assert result is False
        assert inventory.carrying == {"good1": 0, "good2": 0}
        assert inventory.home_inventory == {"good1": 0, "good2": 0}
        
        # Test with goods to deposit
        inventory.carrying["good1"] = 3
        inventory.carrying["good2"] = 2
        result = inventory.deposit_all()
        assert result is True
        assert inventory.carrying == {"good1": 0, "good2": 0}
        assert inventory.home_inventory == {"good1": 3, "good2": 2}
        
        # Test partial deposit
        inventory.carrying["good1"] = 1
        inventory.home_inventory["good1"] = 2  # Existing
        result = inventory.deposit_all()
        assert result is True
        assert inventory.carrying == {"good1": 0, "good2": 0}
        assert inventory.home_inventory == {"good1": 3, "good2": 2}  # Accumulated
    
    def test_withdraw_all(self):
        """Test withdrawing all home inventory."""
        preference = CobbDouglasPreference(alpha=0.5)
        inventory = AgentInventory(preference)
        
        # Test empty home inventory
        result = inventory.withdraw_all()
        assert result is False
        assert inventory.carrying == {"good1": 0, "good2": 0}
        assert inventory.home_inventory == {"good1": 0, "good2": 0}
        
        # Test with goods to withdraw
        inventory.home_inventory["good1"] = 3
        inventory.home_inventory["good2"] = 2
        result = inventory.withdraw_all()
        assert result is True
        assert inventory.carrying == {"good1": 3, "good2": 2}
        assert inventory.home_inventory == {"good1": 0, "good2": 0}
        
        # Test partial withdraw
        inventory.carrying["good1"] = 1  # Existing
        inventory.home_inventory["good1"] = 2
        result = inventory.withdraw_all()
        assert result is True
        assert inventory.carrying == {"good1": 3, "good2": 2}  # Accumulated
        assert inventory.home_inventory == {"good1": 0, "good2": 0}
    
    def test_collect_resource(self):
        """Test resource collection."""
        preference = CobbDouglasPreference(alpha=0.5)
        inventory = AgentInventory(preference)
        
        # Test collecting resource A
        inventory.collect_resource("A")
        assert inventory.carrying == {"good1": 1, "good2": 0}
        
        # Test collecting resource B
        inventory.collect_resource("B")
        assert inventory.carrying == {"good1": 1, "good2": 1}
        
        # Test multiple collections
        inventory.collect_resource("A")
        inventory.collect_resource("A")
        assert inventory.carrying == {"good1": 3, "good2": 1}
    
    def test_total_inventory(self):
        """Test total inventory calculation."""
        preference = CobbDouglasPreference(alpha=0.5)
        inventory = AgentInventory(preference)
        
        # Test empty inventory
        total = inventory.total_inventory()
        assert total == {}
        
        # Test with goods
        inventory.carrying["good1"] = 2
        inventory.home_inventory["good2"] = 3
        total = inventory.total_inventory()
        assert total == {"good1": 2, "good2": 3}
        
        # Test with overlapping goods
        inventory.carrying["good2"] = 1
        total = inventory.total_inventory()
        assert total == {"good1": 2, "good2": 4}  # 3 + 1


class TestInventoryMutationInvariants:
    """Critical tests for mutation invariants - dict identity preservation."""
    
    def test_alias_identity_preserved_deposit(self):
        """Verify dict objects maintain identity through deposit operations."""
        preference = CobbDouglasPreference(alpha=0.5)
        inventory = AgentInventory(preference)
        
        carrying_id = id(inventory.carrying)
        home_id = id(inventory.home_inventory)
        
        # Perform deposit operations
        inventory.carrying["good1"] = 5
        inventory.deposit_all()
        
        # Verify identity preserved
        assert id(inventory.carrying) == carrying_id
        assert id(inventory.home_inventory) == home_id
    
    def test_alias_identity_preserved_withdraw(self):
        """Verify dict objects maintain identity through withdraw operations."""
        preference = CobbDouglasPreference(alpha=0.5)
        inventory = AgentInventory(preference)
        
        carrying_id = id(inventory.carrying)
        home_id = id(inventory.home_inventory)
        
        # Perform withdraw operations
        inventory.home_inventory["good1"] = 5
        inventory.withdraw_all()
        
        # Verify identity preserved
        assert id(inventory.carrying) == carrying_id
        assert id(inventory.home_inventory) == home_id
    
    def test_alias_identity_preserved_collect(self):
        """Verify dict objects maintain identity through collect operations."""
        preference = CobbDouglasPreference(alpha=0.5)
        inventory = AgentInventory(preference)
        
        carrying_id = id(inventory.carrying)
        home_id = id(inventory.home_inventory)
        
        # Perform collect operations
        inventory.collect_resource("A")
        inventory.collect_resource("B")
        
        # Verify identity preserved
        assert id(inventory.carrying) == carrying_id
        assert id(inventory.home_inventory) == home_id
    
    def test_inventory_alias_identity(self):
        """Verify inventory alias points to carrying dict."""
        preference = CobbDouglasPreference(alpha=0.5)
        inventory = AgentInventory(preference)
        
        # Verify alias relationship
        assert id(inventory.inventory) == id(inventory.carrying)
        
        # Verify alias works correctly
        inventory.inventory["good1"] = 5
        assert inventory.carrying["good1"] == 5
        
        inventory.carrying["good2"] = 3
        assert inventory.inventory["good2"] == 3
