"""
Debug Output Orchestrator - Centralized debug flag management.

Configures environment variables for comprehensive test logging.
"""

import os
from typing import List

from framework.test_configs import TestConfiguration


class DebugOrchestrator:
    """Centralized debug output management."""
    
    # Standard debug categories available
    STANDARD_CATEGORIES = [
        'AGENT_MODES', 'TRADES', 'SIMULATION', 
        'PHASES', 'DECISIONS', 'RESOURCES'
    ]
    
    def __init__(self, test_config: TestConfiguration):
        self.test_config = test_config
        self.configure_base_logging()
        self.configure_test_specific_logging()
        
    def configure_base_logging(self):
        """Set up base debug environment variables for all tests."""
        # Enable comprehensive debug logging for all standard categories
        for category in self.STANDARD_CATEGORIES:
            os.environ[f'ECONSIM_DEBUG_{category}'] = '1'
            
        # Additional debug flags from existing tests
        os.environ['ECONSIM_TRADE_GUI_INFO'] = '1'
        os.environ['ECONSIM_TRADE_DEBUG_OVERLAY'] = '1'
        
        # Set initial environment for Phase 1 (both enabled)
        os.environ['ECONSIM_FORAGE_ENABLED'] = '1'
        os.environ['ECONSIM_TRADE_DRAFT'] = '1'
        os.environ['ECONSIM_TRADE_EXEC'] = '1'
        os.environ['ECONSIM_UNIFIED_SELECTION_ENABLE'] = '1'
        
    def configure_test_specific_logging(self):
        """Configure debug categories specific to this test."""
        if self.test_config.debug_categories:
            for category in self.test_config.debug_categories:
                os.environ[f'ECONSIM_DEBUG_{category}'] = '1'
                
        # Test-type specific configurations
        if self.test_config.preference_mix == 'leontief':
            # Enable complementary resource tracking for Leontief tests
            os.environ['ECONSIM_DEBUG_COMPLEMENTARY'] = '1'
            
        elif self.test_config.preference_mix == 'perfect_substitutes':
            # Enable substitution pattern tracking
            os.environ['ECONSIM_DEBUG_SUBSTITUTION'] = '1'
            
    def get_available_categories(self) -> List[str]:
        """Return all available debug categories."""
        return self.STANDARD_CATEGORIES.copy()
        
    def customize_logging(self, categories: List[str]):
        """Allow runtime customization of debug categories."""
        # Disable all first
        for category in self.STANDARD_CATEGORIES:
            os.environ[f'ECONSIM_DEBUG_{category}'] = '0'
            
        # Enable selected
        for category in categories:
            if category in self.STANDARD_CATEGORIES:
                os.environ[f'ECONSIM_DEBUG_{category}'] = '1'