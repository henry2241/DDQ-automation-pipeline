"""
DDQ Depth Analyzer Module
=========================

This module provides consistent depth analysis and standardization
for DDQ responses, ensuring comprehensive and uniform coverage quality.
"""

from .depth_analyzer import DepthAnalyzer
from .depth_types import DepthMetric, CoverageGap, StandardizationRule, DepthLevel, DepthAnalysisContext

__all__ = [
    'DepthAnalyzer',
    'DepthMetric',
    'CoverageGap',
    'StandardizationRule',
    'DepthLevel',
    'DepthAnalysisContext'
]

__version__ = "1.0.0"