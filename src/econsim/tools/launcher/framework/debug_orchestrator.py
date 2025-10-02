"""
Debug Output Orchestrator - Centralized debug flag management.

Configures environment variables for comprehensive test logging.

DEFAULT BEHAVIOR: COMPREHENSIVE LOGGING ENABLED
===============================================
This orchestrator now defaults to enabling ALL logging categories and structured
logging features. This ensures that future enhancements (like Phase 3.2 behavior
tracking, Phase 3.4 event clustering, etc.) are automatically incorporated in
test runs without needing to remember specific environment flags.

To reduce logging when needed:
- Use disable_log_categories(['PERF', 'STAGNATION']) for selective reduction
- Use set_minimal_logging() for performance testing
- Set ECONSIM_LOG_CATEGORIES manually if you need precise control

This "comprehensive by default, selective disable" approach ensures that the
educational logging system keeps growing in value with each enhancement.
"""

import os
from typing import List

from .test_configs import TestConfiguration


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
        
        # ===== STRUCTURED LOGGING SYSTEM (DEFAULT: EVERYTHING ENABLED) =====
        # Enable comprehensive structured logging by default so future enhancements
        # are automatically incorporated without needing to remember specific flags
        
        # Set logging level and format (unless already configured)
        if 'ECONSIM_LOG_LEVEL' not in os.environ:
            os.environ['ECONSIM_LOG_LEVEL'] = 'DEBUG'
        if 'ECONSIM_LOG_FORMAT' not in os.environ:
            os.environ['ECONSIM_LOG_FORMAT'] = 'structured'
            
        # Enable ALL logging categories by default (comprehensive logging)
        # This ensures Phase 3.2 behavior tracking, Phase 3.4 clustering, etc. work automatically
        if 'ECONSIM_LOG_CATEGORIES' not in os.environ:
            os.environ['ECONSIM_LOG_CATEGORIES'] = 'ALL'
            
        # Enable explanations and decision reasoning for educational value
        if 'ECONSIM_LOG_EXPLANATIONS' not in os.environ:
            os.environ['ECONSIM_LOG_EXPLANATIONS'] = '1'
        if 'ECONSIM_LOG_DECISION_REASONING' not in os.environ:
            os.environ['ECONSIM_LOG_DECISION_REASONING'] = '1'
        
        # ===== ECONOMIC LOGGING SYSTEM (DEFAULT: ENABLED) =====
        # Enable economic logging by default for comprehensive behavior analysis
        if 'ECONSIM_ECONOMIC_LOGGING' not in os.environ:
            os.environ['ECONSIM_ECONOMIC_LOGGING'] = '1'
        if 'ECONSIM_ECONOMIC_LOG_LEVEL' not in os.environ:
            os.environ['ECONSIM_ECONOMIC_LOG_LEVEL'] = 'INFO'
        if 'ECONSIM_ECONOMIC_LOG_CATEGORIES' not in os.environ:
            os.environ['ECONSIM_ECONOMIC_LOG_CATEGORIES'] = 'ALL'
        if 'ECONSIM_ECONOMIC_USE_OPTIMIZED' not in os.environ:
            os.environ['ECONSIM_ECONOMIC_USE_OPTIMIZED'] = '1'  # 73%+ size reduction
        
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
                
    def disable_log_categories(self, categories: List[str]):
        """Disable specific structured logging categories when needed.
        
        Use this to reduce log volume for performance testing or when focusing
        on specific aspects. Default behavior is comprehensive logging.
        
        Example: disable_log_categories(['PERF', 'STAGNATION']) for cleaner output
        """
        current_categories = os.environ.get('ECONSIM_LOG_CATEGORIES', 'ALL')
        
        if current_categories == 'ALL':
            # If currently logging everything, create exclude list
            # This preserves the comprehensive logging principle while allowing selective reduction
            excluded = ','.join(f'!{cat}' for cat in categories)
            os.environ['ECONSIM_LOG_CATEGORIES'] = excluded
        else:
            # If already using specific categories, remove the disabled ones
            enabled_cats = [cat.strip() for cat in current_categories.split(',') if cat.strip() and not cat.startswith('!')]
            enabled_cats = [cat for cat in enabled_cats if cat not in categories]
            if enabled_cats:
                os.environ['ECONSIM_LOG_CATEGORIES'] = ','.join(enabled_cats)
            else:
                os.environ['ECONSIM_LOG_CATEGORIES'] = 'NONE'
                
    def set_minimal_logging(self):
        """Set minimal logging for performance testing - only critical events."""
        os.environ['ECONSIM_LOG_CATEGORIES'] = 'AGENT_BEHAVIOR_SUMMARY,PAIRING_SUMMARY,CAUSAL_CHAIN'
        os.environ['ECONSIM_LOG_EXPLANATIONS'] = '0'
        os.environ['ECONSIM_LOG_DECISION_REASONING'] = '0'