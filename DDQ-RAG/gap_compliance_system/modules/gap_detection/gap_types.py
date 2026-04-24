"""
Gap Type Definitions
===================

Defines comprehensive gap types, severities, and categories for DDQ responses.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import json


@dataclass
class DetectionContext:
    """Context for gap detection analysis."""
    
    response_text: str
    question_text: str
    source_documents: List[str]
    response_id: str
    question_id: str
    firm_type: Optional[str] = "investment_adviser"
    client_type: Optional[str] = "institutional"


class GapType(Enum):
    """Types of gaps identified in DDQ responses."""
    
    # Documentation Gaps
    MISSING_DOCUMENTATION = auto()
    INSUFFICIENT_DETAIL = auto()
    OUTDATED_INFORMATION = auto()
    CONFLICTING_SOURCES = auto()
    
    # Content Gaps
    EXCESSIVE_INTERPRETATION = auto()
    FACTUAL_INCONSISTENCY = auto()
    EVASIVE_RESPONSE = auto()
    INCOMPLETE_COVERAGE = auto()
    
    # Compliance Gaps
    UNVERIFIED_CLAIMS = auto()
    MISSING_DISCLAIMERS = auto()
    REGULATORY_EXPOSURE = auto()
    FIDUCIARY_RISK = auto()
    
    # Structural Gaps
    INCONSISTENT_DEPTH = auto()
    MISSING_SPECIFICS = auto()
    UNBALANCED_CLAIMS = auto()
    POOR_ORGANIZATION = auto()


class GapSeverity(Enum):
    """Severity levels for identified gaps."""
    
    CRITICAL = 4    # Direct regulatory/compliance exposure
    HIGH = 3        # Factual errors, credibility risks
    MEDIUM = 2      # Interpretive content, subjectivity issues
    LOW = 1         # Minor formatting, completeness issues


class GapCategory(Enum):
    """High-level categorization of gaps."""
    
    COMPLIANCE_LEGAL = "compliance_legal"
    FACTUAL_ACCURACY = "factual_accuracy" 
    CONTENT_QUALITY = "content_quality"
    STRUCTURAL_DEPTH = "structural_depth"


@dataclass
class Gap:
    """Represents a single identified gap."""
    
    gap_type: GapType
    severity: GapSeverity
    category: GapCategory
    description: str
    location: str  # Where in the response
    evidence: List[str]  # Supporting evidence
    recommendation: str  # How to fix
    source_reference: Optional[str] = None
    confidence: float = 1.0  # Detection confidence (0-1)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert gap to dictionary for serialization."""
        return {
            'gap_type': self.gap_type.name,
            'severity': self.severity.value,
            'category': self.category.value,
            'description': self.description,
            'location': self.location,
            'evidence': self.evidence,
            'recommendation': self.recommendation,
            'source_reference': self.source_reference,
            'confidence': self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Gap':
        """Create gap from dictionary."""
        return cls(
            gap_type=GapType[data['gap_type']],
            severity=GapSeverity(data['severity']),
            category=GapCategory(data['category']),
            description=data['description'],
            location=data['location'],
            evidence=data['evidence'],
            recommendation=data['recommendation'],
            source_reference=data.get('source_reference'),
            confidence=data.get('confidence', 1.0)
        )


@dataclass
class GapReport:
    """Comprehensive gap analysis report."""
    
    response_id: str
    question_id: str
    total_gaps: int
    critical_gaps: int
    high_priority_gaps: int
    gaps: List[Gap]
    overall_score: float  # 0-100, higher is better
    compliance_risk: str  # LOW, MEDIUM, HIGH, CRITICAL
    recommendations: List[str]
    
    def to_json(self) -> str:
        """Export report as JSON."""
        return json.dumps({
            'response_id': self.response_id,
            'question_id': self.question_id,
            'total_gaps': self.total_gaps,
            'critical_gaps': self.critical_gaps,
            'high_priority_gaps': self.high_priority_gaps,
            'gaps': [gap.to_dict() for gap in self.gaps],
            'overall_score': self.overall_score,
            'compliance_risk': self.compliance_risk,
            'recommendations': self.recommendations
        }, indent=2)
    
    def get_gaps_by_category(self, category: GapCategory) -> List[Gap]:
        """Get all gaps in a specific category."""
        return [gap for gap in self.gaps if gap.category == category]
    
    def get_gaps_by_severity(self, min_severity: GapSeverity) -> List[Gap]:
        """Get gaps above minimum severity threshold."""
        return [gap for gap in self.gaps if gap.severity.value >= min_severity.value]


# Gap detection patterns and rules
GAP_DETECTION_RULES = {
    GapType.EXCESSIVE_INTERPRETATION: {
        'patterns': [
            r'likely|probably|appears to|seems to|suggests|implies',
            r'sophisticated understanding|leverages|due to',
            r'based on.*expertise|typical.*approach',
        ],
        'threshold': 0.3,  # 30% interpretive content triggers
        'category': GapCategory.CONTENT_QUALITY,
        'severity': GapSeverity.MEDIUM
    },
    
    GapType.MISSING_DISCLAIMERS: {
        'patterns': [
            r'(?!.*disclaimer).*capabilities.*real-time',
            r'(?!.*due diligence).*specific.*model',
            r'implied.*without.*verification'
        ],
        'category': GapCategory.COMPLIANCE_LEGAL,
        'severity': GapSeverity.HIGH
    },
    
    GapType.FACTUAL_INCONSISTENCY: {
        'patterns': [
            r'sharpe.*ratio.*\d+\.\d+(?!.*source)',
            r'correlation.*\d+\.\d+%?(?!.*documented)',
            r'growth.*\d+%.*without.*redemption'
        ],
        'category': GapCategory.FACTUAL_ACCURACY,
        'severity': GapSeverity.HIGH
    },
    
    GapType.EVASIVE_RESPONSE: {
        'patterns': [
            r'materials do not specify(?!.*due diligence)',
            r'not detailed in.*documentation',
            r'would require.*further.*inquiry'
        ],
        'category': GapCategory.CONTENT_QUALITY,
        'severity': GapSeverity.MEDIUM
    }
}


# Compliance risk thresholds
COMPLIANCE_RISK_THRESHOLDS = {
    'CRITICAL': {'critical': 1, 'high': 3},
    'HIGH': {'critical': 0, 'high': 2}, 
    'MEDIUM': {'high': 1, 'medium': 3},
    'LOW': {'medium': 2, 'low': 5}
}