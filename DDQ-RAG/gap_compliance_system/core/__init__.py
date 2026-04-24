"""
DDQ Gap Handling and Compliance System - Core Integration Layer
==============================================================

This module provides the integration layer for Clara architecture,
orchestrating all gap handling and compliance safeguard systems.
"""

from .clara_integration import ClaraIntegrationLayer
from .system_orchestrator import SystemOrchestrator
from .configuration_manager import ConfigurationManager
from .processing_pipeline import ProcessingPipeline

__all__ = [
    'ClaraIntegrationLayer',
    'SystemOrchestrator',
    'ConfigurationManager',
    'ProcessingPipeline'
]

__version__ = "1.0.0"