"""
Depth Analysis Types and Definitions
===================================

Defines metrics, gaps, and rules for depth consistency analysis.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple
import json


@dataclass
class DepthAnalysisContext:
    """Context for depth analysis."""
    
    response_text: str
    question_text: str
    response_id: str
    question_type: Optional[str] = None  # strategy, operational, risk, performance
    expected_depth: Optional['DepthLevel'] = None
    source_documents: Optional[List[str]] = None


class DepthLevel(Enum):
    """Levels of response depth."""
    
    SURFACE = 1      # Basic facts only
    DESCRIPTIVE = 2  # Facts with basic context
    ANALYTICAL = 3   # Facts with analysis and reasoning
    COMPREHENSIVE = 4 # Complete analysis with implications
    EXPERT = 5       # Expert-level with strategic insights


class CoverageType(Enum):
    """Types of coverage gaps."""
    
    MISSING_COMPONENT = auto()    # Question component not addressed
    INSUFFICIENT_DETAIL = auto()  # Component addressed but lacks detail
    UNBALANCED_COVERAGE = auto()  # Some components detailed, others superficial
    MISSING_CONTEXT = auto()      # Facts without proper context
    INCONSISTENT_DEPTH = auto()   # Depth varies significantly across response


class StandardizationType(Enum):
    """Types of standardization issues."""
    
    FORMAT_INCONSISTENCY = auto()  # Inconsistent formatting
    STRUCTURE_VARIATION = auto()   # Different structural approaches
    TONE_INCONSISTENCY = auto()    # Varying professional tone
    DETAIL_IMBALANCE = auto()      # Imbalanced detail levels
    CITATION_INCONSISTENCY = auto() # Inconsistent source citations


@dataclass
class DepthMetric:
    """Represents a depth measurement for response analysis."""
    
    metric_name: str
    value: float
    max_value: float
    description: str
    weight: float = 1.0
    
    @property
    def normalized_score(self) -> float:
        """Get normalized score (0-1)."""
        return self.value / self.max_value if self.max_value > 0 else 0
    
    @property
    def percentage(self) -> float:
        """Get percentage score."""
        return self.normalized_score * 100


@dataclass
class CoverageGap:
    """Represents a coverage gap in the response."""
    
    gap_type: CoverageType
    component: str  # Which question component
    severity: str   # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    expected_content: str
    actual_coverage: str
    recommendation: str
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'gap_type': self.gap_type.name,
            'component': self.component,
            'severity': self.severity,
            'description': self.description,
            'expected_content': self.expected_content,
            'actual_coverage': self.actual_coverage,
            'recommendation': self.recommendation,
            'confidence': self.confidence
        }


@dataclass
class StandardizationRule:
    """Rule for response standardization."""
    
    rule_id: str
    name: str
    rule_type: StandardizationType
    pattern: str  # What to look for
    expected_format: str  # How it should be
    auto_fix: bool = False
    priority: int = 1  # 1=high, 3=low
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'rule_type': self.rule_type.name,
            'pattern': self.pattern,
            'expected_format': self.expected_format,
            'auto_fix': self.auto_fix,
            'priority': self.priority
        }


@dataclass
class DepthAnalysisReport:
    """Comprehensive depth analysis report."""
    
    response_id: str
    overall_depth_score: float  # 0-100
    depth_level: DepthLevel
    depth_metrics: List[DepthMetric]
    coverage_gaps: List[CoverageGap]
    standardization_issues: List[Dict[str, Any]]
    consistency_score: float  # 0-100
    recommendations: List[str]
    
    def to_json(self) -> str:
        """Export report as JSON."""
        return json.dumps({
            'response_id': self.response_id,
            'overall_depth_score': self.overall_depth_score,
            'depth_level': self.depth_level.name,
            'depth_metrics': [
                {
                    'metric_name': m.metric_name,
                    'value': m.value,
                    'max_value': m.max_value,
                    'normalized_score': m.normalized_score,
                    'percentage': m.percentage,
                    'description': m.description,
                    'weight': m.weight
                }
                for m in self.depth_metrics
            ],
            'coverage_gaps': [gap.to_dict() for gap in self.coverage_gaps],
            'standardization_issues': self.standardization_issues,
            'consistency_score': self.consistency_score,
            'recommendations': self.recommendations
        }, indent=2)
    
    def get_gaps_by_severity(self, min_severity: str) -> List[CoverageGap]:
        """Get gaps above minimum severity."""
        severity_order = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
        min_level = severity_order.get(min_severity.upper(), 1)
        
        return [
            gap for gap in self.coverage_gaps 
            if severity_order.get(gap.severity.upper(), 1) >= min_level
        ]


# Standard depth metrics for DDQ responses
STANDARD_DEPTH_METRICS = {
    'word_count': {
        'description': 'Total word count of response',
        'min_threshold': 200,
        'target_range': (300, 500),
        'max_threshold': 800,
        'weight': 0.2
    },
    
    'specificity_score': {
        'description': 'Ratio of specific facts to general statements',
        'target_ratio': 0.7,  # 70% specific content
        'weight': 0.3
    },
    
    'source_citation_density': {
        'description': 'Number of source citations per 100 words',
        'target_density': 2.0,  # 2 citations per 100 words
        'weight': 0.2
    },
    
    'component_coverage': {
        'description': 'Percentage of question components addressed',
        'target_percentage': 100,
        'weight': 0.3
    },
    
    'factual_density': {
        'description': 'Ratio of factual statements to total statements',
        'target_ratio': 0.8,  # 80% factual content
        'weight': 0.25
    },
    
    'analytical_depth': {
        'description': 'Presence of analysis, reasoning, and context',
        'target_score': 0.6,  # 60% analytical content
        'weight': 0.25
    }
}


# Question component patterns for coverage analysis
COMPONENT_PATTERNS = {
    'strategy_components': [
        r'strateg(?:y|ies)',
        r'approach(?:es)?',
        r'method(?:s|ology)?',
        r'process(?:es)?'
    ],
    
    'operational_components': [
        r'operat(?:ion|ional)',
        r'implement(?:ation)?',
        r'execut(?:e|ion)',
        r'manag(?:e|ement)'
    ],
    
    'risk_components': [
        r'risk(?:s)?',
        r'control(?:s)?',
        r'mitigat(?:e|ion)',
        r'hedge(?:s|ing)?'
    ],
    
    'performance_components': [
        r'perform(?:ance)?',
        r'return(?:s)?',
        r'result(?:s)?',
        r'track\s+record'
    ],
    
    'quantitative_components': [
        r'\d+\.?\d*%',
        r'\$[\d,]+',
        r'\d+\.\d+\s*(?:ratio|multiple)',
        r'(?:sharpe|alpha|beta|correlation)'
    ]
}


# Standardization rules for consistent formatting
STANDARDIZATION_RULES = [
    StandardizationRule(
        rule_id="FORMAT-001",
        name="Consistent Header Formatting",
        rule_type=StandardizationType.FORMAT_INCONSISTENCY,
        pattern=r'(?:^|\n)(?:\*\*|##?\s*|[A-Z][^:\n]*:)',
        expected_format="**Header Text:**",
        auto_fix=True,
        priority=1
    ),
    
    StandardizationRule(
        rule_id="FORMAT-002", 
        name="Consistent Citation Format",
        rule_type=StandardizationType.CITATION_INCONSISTENCY,
        pattern=r'(?:source|document|file|per|according\s+to)',
        expected_format="as stated in [Source Name], Section X",
        auto_fix=False,
        priority=2
    ),
    
    StandardizationRule(
        rule_id="STRUCTURE-001",
        name="Consistent Section Structure",
        rule_type=StandardizationType.STRUCTURE_VARIATION,
        pattern=r'(?:overview|approach|process|implementation)',
        expected_format="Standard section order: Overview → Approach → Implementation → Results",
        auto_fix=False,
        priority=2
    ),
    
    StandardizationRule(
        rule_id="TONE-001",
        name="Professional Tone Consistency",
        rule_type=StandardizationType.TONE_INCONSISTENCY,
        pattern=r'(?:we\s+believe|i\s+think|personally|obviously)',
        expected_format="Use declarative firm voice: 'The firm employs...', 'The firm utilizes...'",
        auto_fix=True,
        priority=1
    )
]


# Coverage depth templates for different question types
COVERAGE_TEMPLATES = {
    'strategy_question': {
        'required_components': ['overview', 'methodology', 'implementation', 'rationale'],
        'expected_depth': DepthLevel.ANALYTICAL,
        'min_word_count': 300,
        'target_specificity': 0.7
    },
    
    'operational_question': {
        'required_components': ['process', 'tools', 'frequency', 'oversight'],
        'expected_depth': DepthLevel.DESCRIPTIVE,
        'min_word_count': 250,
        'target_specificity': 0.8
    },
    
    'risk_question': {
        'required_components': ['identification', 'measurement', 'management', 'monitoring'],
        'expected_depth': DepthLevel.COMPREHENSIVE,
        'min_word_count': 350,
        'target_specificity': 0.75
    },
    
    'performance_question': {
        'required_components': ['metrics', 'attribution', 'benchmarks', 'disclaimers'],
        'expected_depth': DepthLevel.ANALYTICAL,
        'min_word_count': 300,
        'target_specificity': 0.85
    }
}


# Depth scoring weights
DEPTH_SCORING_WEIGHTS = {
    'completeness': 0.3,      # All components addressed
    'specificity': 0.25,      # Specific facts vs general statements
    'source_backing': 0.2,    # Source citations and verification
    'analytical_content': 0.15, # Analysis and reasoning
    'structural_quality': 0.1  # Organization and flow
}