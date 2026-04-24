"""
Risk Assessment Types and Definitions
====================================

Defines risk levels, categories, and assessment frameworks for DDQ responses.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple
import json
from datetime import datetime


@dataclass
class RiskAssessmentContext:
    """Context for risk assessment analysis."""
    
    response_text: str
    response_id: str
    firm_type: str = "investment_adviser"
    client_type: str = "institutional"
    question_text: Optional[str] = None
    source_documents: Optional[List[str]] = None


class RiskLevel(Enum):
    """Risk severity levels."""
    
    CRITICAL = 5    # Immediate regulatory action required
    HIGH = 4        # Significant compliance exposure
    MEDIUM = 3      # Moderate risk requiring monitoring
    LOW = 2         # Minor risk, best practice improvement
    MINIMAL = 1     # Very low risk, no action needed


class RiskCategory(Enum):
    """Categories of regulatory risks."""
    
    # SEC Risks
    PERFORMANCE_ADVERTISING = "performance_advertising"
    MISLEADING_STATEMENTS = "misleading_statements"
    INADEQUATE_DISCLOSURE = "inadequate_disclosure"
    FIDUCIARY_BREACH = "fiduciary_breach"
    
    # CFTC Risks
    COMMODITY_MISREPRESENTATION = "commodity_misrepresentation"
    INADEQUATE_RISK_DISCLOSURE = "inadequate_risk_disclosure"
    POOL_OPERATOR_VIOLATIONS = "pool_operator_violations"
    
    # General Compliance Risks
    ANTI_FRAUD_VIOLATIONS = "anti_fraud_violations"
    RECORD_KEEPING_ISSUES = "record_keeping_issues"
    OPERATIONAL_RISK = "operational_risk"
    CYBERSECURITY_RISK = "cybersecurity_risk"
    
    # Fiduciary Risks
    SUITABILITY_CONCERNS = "suitability_concerns"
    CONFLICTS_OF_INTEREST = "conflicts_of_interest"
    CLIENT_BEST_INTEREST = "client_best_interest"


class RegulatoryFramework(Enum):
    """Regulatory frameworks for risk assessment."""
    
    SEC_INVESTMENT_ADVISERS = "sec_investment_advisers_act_1940"
    SEC_INVESTMENT_COMPANY = "sec_investment_company_act_1940" 
    CFTC_CEA = "cftc_commodity_exchange_act"
    FINRA_CONDUCT = "finra_conduct_rules"
    DOL_FIDUCIARY = "dol_fiduciary_rule"
    GDPR_PRIVACY = "gdpr_data_protection"
    ANTI_MONEY_LAUNDERING = "aml_requirements"


class FiduciaryStandard(Enum):
    """Fiduciary duty standards."""
    
    DUTY_OF_LOYALTY = "duty_of_loyalty"
    DUTY_OF_CARE = "duty_of_care"
    DUTY_OF_GOOD_FAITH = "duty_of_good_faith"
    DUTY_TO_MONITOR = "duty_to_monitor"
    DISCLOSURE_OBLIGATIONS = "disclosure_obligations"


@dataclass
class RiskFactor:
    """Individual risk factor identification."""
    
    factor_id: str
    name: str
    category: RiskCategory
    level: RiskLevel
    description: str
    evidence: List[str]
    regulatory_basis: RegulatoryFramework
    potential_consequences: List[str]
    mitigation_actions: List[str]
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'factor_id': self.factor_id,
            'name': self.name,
            'category': self.category.value,
            'level': self.level.value,
            'description': self.description,
            'evidence': self.evidence,
            'regulatory_basis': self.regulatory_basis.value,
            'potential_consequences': self.potential_consequences,
            'mitigation_actions': self.mitigation_actions,
            'confidence': self.confidence
        }


@dataclass
class FiduciaryRisk:
    """Specific fiduciary duty risk."""
    
    standard: FiduciaryStandard
    violation_type: str
    severity: RiskLevel
    description: str
    client_impact: str
    regulatory_exposure: str
    recommended_action: str
    confidence: float = 1.0


@dataclass
class RiskAssessmentReport:
    """Comprehensive risk assessment report."""
    
    response_id: str
    assessment_date: datetime
    overall_risk_score: float  # 0-100, higher is riskier
    risk_grade: str  # A, B, C, D, F
    risk_factors: List[RiskFactor]
    fiduciary_risks: List[FiduciaryRisk]
    regulatory_exposure: Dict[RegulatoryFramework, float]  # Framework -> risk score
    immediate_actions: List[str]
    monitoring_requirements: List[str]
    
    def to_json(self) -> str:
        """Export report as JSON."""
        return json.dumps({
            'response_id': self.response_id,
            'assessment_date': self.assessment_date.isoformat(),
            'overall_risk_score': self.overall_risk_score,
            'risk_grade': self.risk_grade,
            'risk_factors': [rf.to_dict() for rf in self.risk_factors],
            'fiduciary_risks': [
                {
                    'standard': fr.standard.value,
                    'violation_type': fr.violation_type,
                    'severity': fr.severity.value,
                    'description': fr.description,
                    'client_impact': fr.client_impact,
                    'regulatory_exposure': fr.regulatory_exposure,
                    'recommended_action': fr.recommended_action,
                    'confidence': fr.confidence
                }
                for fr in self.fiduciary_risks
            ],
            'regulatory_exposure': {
                framework.value: score 
                for framework, score in self.regulatory_exposure.items()
            },
            'immediate_actions': self.immediate_actions,
            'monitoring_requirements': self.monitoring_requirements
        }, indent=2)
    
    def get_critical_risks(self) -> List[RiskFactor]:
        """Get critical risk factors requiring immediate attention."""
        return [rf for rf in self.risk_factors if rf.level == RiskLevel.CRITICAL]
    
    def get_risks_by_category(self, category: RiskCategory) -> List[RiskFactor]:
        """Get risk factors by category."""
        return [rf for rf in self.risk_factors if rf.category == category]


# Risk factor templates and patterns
RISK_FACTOR_PATTERNS = {
    RiskCategory.PERFORMANCE_ADVERTISING: {
        'patterns': [
            r'(?:guarantee|assure|promise)\s+(?:return|performance|profit)',
            r'(?:outperform|beat|exceed)\s+(?:market|benchmark|index)',
            r'\d+%\s+(?:annual|yearly)\s+return(?:s)?',
            r'(?:consistent|always|never)\s+(?:profitable|successful)',
            r'(?:track\s+record|historical\s+performance)(?!\s+(?:disclaimer|warning))'
        ],
        'consequences': [
            'SEC enforcement action',
            'Client litigation risk',
            'Regulatory censure',
            'Monetary penalties'
        ],
        'mitigations': [
            'Add performance disclaimers',
            'Remove guarantee language',
            'Qualify statements with risk warnings',
            'Review advertising compliance'
        ]
    },
    
    RiskCategory.MISLEADING_STATEMENTS: {
        'patterns': [
            r'(?:risk-free|no\s+risk|guaranteed)\s+(?:investment|strategy)',
            r'(?:always|never|consistently)\s+(?:profitable|outperform)',
            r'(?:certain|sure|definite)\s+(?:return|outcome|result)',
            r'(?:perfect|flawless|foolproof)\s+(?:strategy|approach|system)'
        ],
        'consequences': [
            'Anti-fraud violations',
            'Client damages claims',
            'SEC investigation',
            'Registration suspension'
        ],
        'mitigations': [
            'Remove absolute statements',
            'Add appropriate qualifications',
            'Include risk disclosures',
            'Legal review of materials'
        ]
    },
    
    RiskCategory.INADEQUATE_DISCLOSURE: {
        'patterns': [
            r'(?:conflict|fee|compensation)(?!\s+(?:disclosure|warning))',
            r'(?:commission|incentive|payment)(?!\s+(?:disclosed|noted))',
            r'(?:material\s+fact|important\s+information)(?!\s+(?:disclosed|provided))',
            r'(?:relationship|agreement|arrangement)(?!\s+(?:disclosed|documented))'
        ],
        'consequences': [
            'Fiduciary duty violations',
            'Client relationship damage',
            'Regulatory enforcement',
            'Professional liability claims'
        ],
        'mitigations': [
            'Implement disclosure procedures',
            'Review all material relationships',
            'Document conflict management',
            'Enhance transparency protocols'
        ]
    },
    
    RiskCategory.FIDUCIARY_BREACH: {
        'patterns': [
            r'(?:suitable|appropriate|right\s+for)(?!\s+(?:careful|thorough)\s+(?:analysis|review))',
            r'(?:recommend|suggest|advise)(?!\s+(?:after|following)\s+(?:analysis|review))',
            r'(?:client\s+interest|best\s+interest)(?!\s+(?:primary|paramount|foremost))',
            r'(?:self-interest|firm\s+benefit|internal\s+gain)'
        ],
        'consequences': [
            'Breach of fiduciary duty claims',
            'Client compensation requirements',
            'Professional sanctions',
            'Reputational damage'
        ],
        'mitigations': [
            'Strengthen fiduciary procedures',
            'Enhanced client suitability analysis',
            'Regular compliance training',
            'Client interest prioritization'
        ]
    },
    
    RiskCategory.INADEQUATE_RISK_DISCLOSURE: {
        'patterns': [
            r'(?:investment|strategy|approach)(?!\s+(?:risk|volatility|loss|adverse))',
            r'(?:leverage|derivatives|complex\s+instruments)(?!\s+risk)',
            r'(?:market|credit|operational|liquidity)\s+(?:exposure|position)(?!\s+risk)',
            r'(?:concentration|correlation|model)\s+(?:risk)?(?!\s+(?:management|mitigation))'
        ],
        'consequences': [
            'Inadequate risk disclosure claims',
            'Client unexpected losses',
            'Regulatory scrutiny',
            'Suitability violations'
        ],
        'mitigations': [
            'Comprehensive risk disclosure',
            'Client risk tolerance assessment',
            'Regular risk communication',
            'Enhanced risk documentation'
        ]
    }
}


# Fiduciary duty assessment criteria
FIDUCIARY_ASSESSMENT_CRITERIA = {
    FiduciaryStandard.DUTY_OF_LOYALTY: {
        'indicators': [
            'client interest prioritization',
            'conflict identification and management',
            'independence of advice',
            'transparency in relationships'
        ],
        'violations': [
            'self-dealing without disclosure',
            'undisclosed conflicts of interest',
            'prioritizing firm over client interests',
            'inadequate conflict management'
        ]
    },
    
    FiduciaryStandard.DUTY_OF_CARE: {
        'indicators': [
            'thorough due diligence processes',
            'competent investment analysis',
            'ongoing monitoring procedures',
            'reasonable investment decisions'
        ],
        'violations': [
            'inadequate due diligence',
            'lack of investment oversight',
            'unreasonable investment decisions',
            'failure to monitor performance'
        ]
    },
    
    FiduciaryStandard.DISCLOSURE_OBLIGATIONS: {
        'indicators': [
            'comprehensive material disclosures',
            'clear and understandable language',
            'timely information provision',
            'accessible documentation'
        ],
        'violations': [
            'material omissions',
            'misleading statements',
            'inadequate transparency',
            'delayed disclosure of material changes'
        ]
    }
}


# Risk scoring weights by category
RISK_SCORING_WEIGHTS = {
    RiskCategory.PERFORMANCE_ADVERTISING: 25,
    RiskCategory.MISLEADING_STATEMENTS: 30,
    RiskCategory.INADEQUATE_DISCLOSURE: 20,
    RiskCategory.FIDUCIARY_BREACH: 35,
    RiskCategory.INADEQUATE_RISK_DISCLOSURE: 20,
    RiskCategory.COMMODITY_MISREPRESENTATION: 25,
    RiskCategory.ANTI_FRAUD_VIOLATIONS: 30,
    RiskCategory.SUITABILITY_CONCERNS: 20,
    RiskCategory.CONFLICTS_OF_INTEREST: 25,
    RiskCategory.CLIENT_BEST_INTEREST: 30
}


# Risk grade thresholds
RISK_GRADE_THRESHOLDS = {
    'A': 10,   # 0-10 points (Excellent)
    'B': 25,   # 11-25 points (Good)
    'C': 45,   # 26-45 points (Acceptable)
    'D': 70,   # 46-70 points (Poor)
    'F': 999   # 71+ points (Unacceptable)
}


# Regulatory framework risk weights
REGULATORY_FRAMEWORK_WEIGHTS = {
    RegulatoryFramework.SEC_INVESTMENT_ADVISERS: 1.2,  # Higher weight for IA risks
    RegulatoryFramework.SEC_INVESTMENT_COMPANY: 1.1,
    RegulatoryFramework.CFTC_CEA: 1.0,
    RegulatoryFramework.FINRA_CONDUCT: 0.9,
    RegulatoryFramework.DOL_FIDUCIARY: 1.3,  # Highest weight for fiduciary
    RegulatoryFramework.GDPR_PRIVACY: 0.8,
    RegulatoryFramework.ANTI_MONEY_LAUNDERING: 0.7
}