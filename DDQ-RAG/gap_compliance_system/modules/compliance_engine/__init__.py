"""
DDQ Compliance Engine Module
===========================

This module provides automated compliance checking and disclaimer insertion
for DDQ responses, ensuring regulatory compliance and risk management.
"""

from .compliance_checker import ComplianceChecker
from .disclaimer_engine import DisclaimerEngine
from .regulatory_validator import RegulatoryValidator
from .compliance_types import ComplianceRule, ComplianceViolation, DisclaimerType

__all__ = [
    'ComplianceChecker',
    'DisclaimerEngine', 
    'RegulatoryValidator',
    'ComplianceRule',
    'ComplianceViolation',
    'DisclaimerType'
]

__version__ = "1.0.0"