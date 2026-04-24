"""
DDQ Gap Detection Module
=======================

This module provides systematic documentation gap detection and handling
for DDQ workflow responses, ensuring comprehensive coverage of investor queries.
"""

from .gap_detector import GapDetector
from .gap_types import GapType, GapSeverity, GapCategory, Gap, GapReport, DetectionContext

__all__ = [
    'GapDetector',
    'GapType',
    'GapSeverity', 
    'GapCategory',
    'Gap',
    'GapReport',
    'DetectionContext'
]

__version__ = "1.0.0"