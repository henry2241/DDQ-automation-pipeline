"""
DDQ Audit Trail Module
======================

This module provides quality assurance and comprehensive audit trail
systems for DDQ response processing and gap remediation.
"""

from .audit_logger import AuditLogger
from .audit_types import AuditEvent, QualityMetric, VerificationResult, AuditEventType, AuditLevel

__all__ = [
    'AuditLogger',
    'AuditEvent',
    'QualityMetric',
    'VerificationResult',
    'AuditEventType',
    'AuditLevel'
]

__version__ = "1.0.0"