"""
DDQ Gap Compliance System
========================

Enterprise-grade gap detection and compliance system for DDQ workflows.
Provides systematic gap handling and regulatory safeguards for Clara.
"""

__version__ = "1.0.0"
__author__ = "DDQ System Team"
__description__ = "Bulletproof DDQ gap handling and compliance safeguards"

# Core exports
from .core.clara_integration import (
    ClaraIntegrationLayer,
    DDQProcessingRequest,
    DDQProcessingResult,
    create_clara_integration,
    quick_quality_check,
    process_single_response
)

from .core.configuration_manager import (
    ConfigurationManager,
    create_default_configuration,
    create_development_configuration
)

__all__ = [
    'ClaraIntegrationLayer',
    'DDQProcessingRequest', 
    'DDQProcessingResult',
    'ConfigurationManager',
    'create_clara_integration',
    'quick_quality_check',
    'process_single_response',
    'create_default_configuration',
    'create_development_configuration'
]