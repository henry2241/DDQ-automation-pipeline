"""
DDQ Risk Assessment Module
=========================

This module provides regulatory risk assessment and flagging
for DDQ responses, ensuring compliance with fiduciary standards.
"""

from .risk_assessor import RiskAssessor
from .risk_types import RiskLevel, RiskCategory, RegulatoryFramework, FiduciaryRisk, RiskAssessmentContext

__all__ = [
    'RiskAssessor',
    'RiskLevel', 
    'RiskCategory',
    'RegulatoryFramework',
    'FiduciaryRisk',
    'RiskAssessmentContext'
]

__version__ = "1.0.0"