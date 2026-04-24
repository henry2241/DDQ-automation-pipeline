"""
Audit Trail Types and Definitions
=================================

Defines comprehensive audit event types, quality metrics, and verification
structures for DDQ processing audit trails.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import json
import uuid


class AuditEventType(Enum):
    """Types of audit events that can be logged."""
    
    # Processing lifecycle events
    RESPONSE_RECEIVED = "response_received"
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"
    PROCESSING_ERROR = "processing_error"
    
    # Gap detection events
    GAP_DETECTION_STARTED = "gap_detection_started"
    GAP_DETECTION_COMPLETED = "gap_detection_completed"
    GAP_DETECTED = "gap_detected"
    GAP_ANALYSIS_FAILED = "gap_analysis_failed"
    
    # Compliance events
    COMPLIANCE_CHECK_STARTED = "compliance_check_started"
    COMPLIANCE_CHECK_COMPLETED = "compliance_check_completed"
    COMPLIANCE_VIOLATION_FOUND = "compliance_violation_found"
    COMPLIANCE_CHECK_FAILED = "compliance_check_failed"
    
    # Depth analysis events
    DEPTH_ANALYSIS_STARTED = "depth_analysis_started"
    DEPTH_ANALYSIS_COMPLETED = "depth_analysis_completed"
    DEPTH_ISSUE_IDENTIFIED = "depth_issue_identified"
    
    # Risk assessment events
    RISK_ASSESSMENT_STARTED = "risk_assessment_started"
    RISK_ASSESSMENT_COMPLETED = "risk_assessment_completed"
    RISK_FACTOR_IDENTIFIED = "risk_factor_identified"
    CRITICAL_RISK_DETECTED = "critical_risk_detected"
    
    # Disclaimer and modification events
    DISCLAIMER_INSERTION = "disclaimer_insertion"
    TEXT_MODIFICATION = "text_modification"
    AUTO_FIX_APPLIED = "auto_fix_applied"
    
    # Quality assurance events
    QUALITY_CHECK_STARTED = "quality_check_started"
    QUALITY_CHECK_COMPLETED = "quality_check_completed"
    QUALITY_CHECK_FAILED = "quality_check_failed"
    QUALITY_THRESHOLD_EXCEEDED = "quality_threshold_exceeded"
    
    # Manual review events
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    MANUAL_REVIEW_REQUESTED = "manual_review_requested"
    MANUAL_REVIEW_COMPLETED = "manual_review_completed"
    
    # Verification events
    VERIFICATION_STARTED = "verification_started"
    VERIFICATION_COMPLETED = "verification_completed"
    VERIFICATION_FAILED = "verification_failed"
    
    # System events
    CONFIGURATION_CHANGE = "configuration_change"
    SYSTEM_ERROR = "system_error"
    PERFORMANCE_ALERT = "performance_alert"


class AuditLevel(Enum):
    """Audit log levels for event severity."""
    
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class QualityDimension(Enum):
    """Dimensions of quality measurement."""
    
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"


class VerificationStatus(Enum):
    """Status of verification checks."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class AuditEvent:
    """Individual audit event record."""
    
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    level: AuditLevel
    description: str
    details: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    response_id: Optional[str] = None
    source_module: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Generate event ID if not provided."""
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps({
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.name,
            'description': self.description,
            'details': self.details or {},
            'session_id': self.session_id,
            'response_id': self.response_id,
            'source_module': self.source_module,
            'user_context': self.user_context or {}
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.name,
            'description': self.description,
            'details': self.details or {},
            'session_id': self.session_id,
            'response_id': self.response_id,
            'source_module': self.source_module,
            'user_context': self.user_context or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Create event from dictionary."""
        return cls(
            event_id=data['event_id'],
            event_type=AuditEventType(data['event_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            level=AuditLevel[data['level']],
            description=data['description'],
            details=data.get('details'),
            session_id=data.get('session_id'),
            response_id=data.get('response_id'),
            source_module=data.get('source_module'),
            user_context=data.get('user_context')
        )


@dataclass
class QualityMetric:
    """Quality measurement for audit tracking."""
    
    metric_name: str
    dimension: QualityDimension
    value: float
    max_value: float
    threshold: float
    passed: bool
    description: str
    measurement_time: Optional[datetime] = None
    context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Set measurement time if not provided."""
        if self.measurement_time is None:
            self.measurement_time = datetime.now()
    
    @property
    def score_percentage(self) -> float:
        """Get metric score as percentage."""
        if self.max_value <= 0:
            return 0.0
        return (self.value / self.max_value) * 100
    
    @property
    def threshold_percentage(self) -> float:
        """Get threshold as percentage."""
        if self.max_value <= 0:
            return 0.0
        return (self.threshold / self.max_value) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        return {
            'metric_name': self.metric_name,
            'dimension': self.dimension.value,
            'value': self.value,
            'max_value': self.max_value,
            'threshold': self.threshold,
            'passed': self.passed,
            'score_percentage': self.score_percentage,
            'threshold_percentage': self.threshold_percentage,
            'description': self.description,
            'measurement_time': self.measurement_time.isoformat() if self.measurement_time else None,
            'context': self.context or {}
        }


@dataclass
class VerificationResult:
    """Result of a verification check."""
    
    check_name: str
    status: VerificationStatus
    passed: bool
    score: Optional[float] = None
    max_score: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    recommendations: Optional[List[str]] = None
    verification_time: Optional[datetime] = None
    
    def __post_init__(self):
        """Set verification time if not provided."""
        if self.verification_time is None:
            self.verification_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'check_name': self.check_name,
            'status': self.status.value,
            'passed': self.passed,
            'score': self.score,
            'max_score': self.max_score,
            'details': self.details or {},
            'error_message': self.error_message,
            'recommendations': self.recommendations or [],
            'verification_time': self.verification_time.isoformat() if self.verification_time else None
        }


@dataclass
class AuditTrail:
    """Complete audit trail for a DDQ processing session."""
    
    session_id: str
    response_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "active"
    events: List[AuditEvent] = field(default_factory=list)
    quality_metrics: List[QualityMetric] = field(default_factory=list)
    verification_results: List[VerificationResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def add_event(self, event: AuditEvent):
        """Add an audit event to the trail."""
        self.events.append(event)
        self._update_summary()
    
    def add_quality_metric(self, metric: QualityMetric):
        """Add a quality metric to the trail."""
        self.quality_metrics.append(metric)
        self._update_summary()
    
    def add_verification_result(self, result: VerificationResult):
        """Add a verification result to the trail."""
        self.verification_results.append(result)
        self._update_summary()
    
    def finalize(self, final_status: str):
        """Finalize the audit trail."""
        self.end_time = datetime.now()
        self.status = final_status
        self._update_summary()
    
    def get_events_by_type(self, event_type: AuditEventType) -> List[AuditEvent]:
        """Get all events of a specific type."""
        return [event for event in self.events if event.event_type == event_type]
    
    def get_events_by_level(self, min_level: AuditLevel) -> List[AuditEvent]:
        """Get events above minimum severity level."""
        return [event for event in self.events if event.level.value >= min_level.value]
    
    def get_quality_metrics_by_dimension(self, dimension: QualityDimension) -> List[QualityMetric]:
        """Get quality metrics by dimension."""
        return [metric for metric in self.quality_metrics if metric.dimension == dimension]
    
    def get_failed_quality_metrics(self) -> List[QualityMetric]:
        """Get quality metrics that failed thresholds."""
        return [metric for metric in self.quality_metrics if not metric.passed]
    
    def get_verification_failures(self) -> List[VerificationResult]:
        """Get failed verification checks."""
        return [result for result in self.verification_results if not result.passed]
    
    def _update_summary(self):
        """Update trail summary statistics."""
        
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        else:
            duration = (datetime.now() - self.start_time).total_seconds()
        
        # Event statistics
        event_counts = {}
        for event in self.events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Quality statistics
        quality_scores = {}
        failed_quality_checks = 0
        
        for metric in self.quality_metrics:
            dimension = metric.dimension.value
            if dimension not in quality_scores:
                quality_scores[dimension] = []
            quality_scores[dimension].append(metric.score_percentage)
            
            if not metric.passed:
                failed_quality_checks += 1
        
        # Calculate average scores by dimension
        avg_quality_scores = {}
        for dimension, scores in quality_scores.items():
            avg_quality_scores[dimension] = sum(scores) / len(scores) if scores else 0
        
        # Verification statistics
        verification_summary = {
            'total_checks': len(self.verification_results),
            'passed': sum(1 for r in self.verification_results if r.passed),
            'failed': sum(1 for r in self.verification_results if not r.passed),
            'errors': sum(1 for r in self.verification_results if r.status == VerificationStatus.ERROR)
        }
        
        self.summary = {
            'duration_seconds': duration,
            'status': self.status,
            'total_events': len(self.events),
            'event_counts': event_counts,
            'error_events': len([e for e in self.events if e.level.value >= AuditLevel.ERROR.value]),
            'warning_events': len([e for e in self.events if e.level == AuditLevel.WARNING]),
            'quality_metrics_count': len(self.quality_metrics),
            'failed_quality_checks': failed_quality_checks,
            'quality_scores': avg_quality_scores,
            'verification_summary': verification_summary,
            'last_updated': datetime.now().isoformat()
        }
    
    def to_json(self) -> str:
        """Export trail as JSON."""
        return json.dumps({
            'session_id': self.session_id,
            'response_id': self.response_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'events': [event.to_dict() for event in self.events],
            'quality_metrics': [metric.to_dict() for metric in self.quality_metrics],
            'verification_results': [result.to_dict() for result in self.verification_results],
            'summary': self.summary
        }, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trail to dictionary."""
        return {
            'session_id': self.session_id,
            'response_id': self.response_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'events': [event.to_dict() for event in self.events],
            'quality_metrics': [metric.to_dict() for metric in self.quality_metrics],
            'verification_results': [result.to_dict() for result in self.verification_results],
            'summary': self.summary
        }


# Event criticality mapping for prioritization
EVENT_CRITICALITY = {
    AuditEventType.CRITICAL_RISK_DETECTED: AuditLevel.CRITICAL,
    AuditEventType.SYSTEM_ERROR: AuditLevel.CRITICAL,
    AuditEventType.PROCESSING_ERROR: AuditLevel.ERROR,
    AuditEventType.COMPLIANCE_VIOLATION_FOUND: AuditLevel.ERROR,
    AuditEventType.QUALITY_CHECK_FAILED: AuditLevel.ERROR,
    AuditEventType.VERIFICATION_FAILED: AuditLevel.ERROR,
    AuditEventType.MANUAL_REVIEW_REQUIRED: AuditLevel.WARNING,
    AuditEventType.QUALITY_THRESHOLD_EXCEEDED: AuditLevel.WARNING,
    AuditEventType.PERFORMANCE_ALERT: AuditLevel.WARNING,
    AuditEventType.GAP_DETECTED: AuditLevel.INFO,
    AuditEventType.RISK_FACTOR_IDENTIFIED: AuditLevel.INFO,
    AuditEventType.AUTO_FIX_APPLIED: AuditLevel.INFO,
    AuditEventType.DISCLAIMER_INSERTION: AuditLevel.INFO,
}


# Standard quality metric definitions
STANDARD_QUALITY_METRICS = {
    'gap_detection_accuracy': {
        'dimension': QualityDimension.ACCURACY,
        'threshold': 85.0,
        'description': 'Accuracy of gap detection process'
    },
    'compliance_coverage': {
        'dimension': QualityDimension.COMPLIANCE,
        'threshold': 95.0,
        'description': 'Coverage of compliance requirements'
    },
    'depth_analysis_score': {
        'dimension': QualityDimension.COMPLETENESS,
        'threshold': 70.0,
        'description': 'Depth and completeness of response analysis'
    },
    'consistency_score': {
        'dimension': QualityDimension.CONSISTENCY,
        'threshold': 75.0,
        'description': 'Consistency with other responses'
    },
    'processing_performance': {
        'dimension': QualityDimension.PERFORMANCE,
        'threshold': 90.0,
        'description': 'Overall processing performance'
    },
    'system_reliability': {
        'dimension': QualityDimension.RELIABILITY,
        'threshold': 95.0,
        'description': 'System reliability and error rate'
    }
}


# Standard verification checks
STANDARD_VERIFICATION_CHECKS = [
    'gap_detection_completeness',
    'compliance_rule_coverage',
    'disclaimer_insertion_accuracy',
    'risk_assessment_thoroughness',
    'depth_analysis_consistency',
    'audit_trail_integrity',
    'data_accuracy_verification',
    'regulatory_compliance_check'
]


def create_audit_event(
    event_type: AuditEventType,
    description: str,
    level: Optional[AuditLevel] = None,
    details: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    response_id: Optional[str] = None,
    source_module: Optional[str] = None
) -> AuditEvent:
    """Factory function to create audit events with proper defaults."""
    
    if level is None:
        level = EVENT_CRITICALITY.get(event_type, AuditLevel.INFO)
    
    return AuditEvent(
        event_id="",  # Will be auto-generated
        event_type=event_type,
        timestamp=datetime.now(),
        level=level,
        description=description,
        details=details,
        session_id=session_id,
        response_id=response_id,
        source_module=source_module
    )


def create_quality_metric(
    metric_name: str,
    value: float,
    max_value: float = 100.0,
    threshold: Optional[float] = None,
    dimension: Optional[QualityDimension] = None,
    description: Optional[str] = None
) -> QualityMetric:
    """Factory function to create quality metrics with proper defaults."""
    
    # Use standard metric definitions if available
    if metric_name in STANDARD_QUALITY_METRICS and threshold is None:
        standard_metric = STANDARD_QUALITY_METRICS[metric_name]
        threshold = standard_metric['threshold']
        if dimension is None:
            dimension = standard_metric['dimension']
        if description is None:
            description = standard_metric['description']
    
    if threshold is None:
        threshold = max_value * 0.8  # Default to 80% threshold
    
    if dimension is None:
        dimension = QualityDimension.ACCURACY
    
    if description is None:
        description = f"Quality metric for {metric_name}"
    
    passed = value >= threshold
    
    return QualityMetric(
        metric_name=metric_name,
        dimension=dimension,
        value=value,
        max_value=max_value,
        threshold=threshold,
        passed=passed,
        description=description
    )


def create_verification_result(
    check_name: str,
    passed: bool,
    score: Optional[float] = None,
    max_score: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    recommendations: Optional[List[str]] = None
) -> VerificationResult:
    """Factory function to create verification results."""
    
    if passed:
        status = VerificationStatus.PASSED
    elif error_message:
        status = VerificationStatus.ERROR
    else:
        status = VerificationStatus.FAILED
    
    return VerificationResult(
        check_name=check_name,
        status=status,
        passed=passed,
        score=score,
        max_score=max_score,
        details=details,
        error_message=error_message,
        recommendations=recommendations
    )