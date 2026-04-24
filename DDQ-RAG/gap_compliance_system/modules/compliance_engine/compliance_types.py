"""
Compliance Types and Definitions
===============================

Defines compliance rules, violations, and disclaimer types for DDQ responses.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Callable
import json


@dataclass
class ComplianceContext:
    """Context for compliance checking."""
    
    response_text: str
    response_id: str
    firm_type: str = "investment_adviser"
    client_type: str = "institutional"
    source_documents: Optional[List[str]] = None


class ComplianceFramework(Enum):
    """Regulatory frameworks and standards."""
    
    SEC_INVESTMENT_ADVISERS_ACT = "sec_investment_advisers_act"
    SEC_INVESTMENT_COMPANY_ACT = "sec_investment_company_act"
    CFTC_COMMODITY_POOL_OPERATORS = "cftc_commodity_pool_operators"
    FINRA_RULES = "finra_rules"
    GDPR_DATA_PROTECTION = "gdpr_data_protection"
    FIDUCIARY_STANDARDS = "fiduciary_standards"
    ANTI_FRAUD_PROVISIONS = "anti_fraud_provisions"


class ViolationSeverity(Enum):
    """Severity levels for compliance violations."""
    
    CRITICAL = 4    # Immediate regulatory action required
    HIGH = 3        # Significant compliance risk
    MEDIUM = 2      # Moderate risk requiring attention
    LOW = 1         # Minor issue, best practice


class DisclaimerType(Enum):
    """Types of disclaimers that can be automatically inserted."""
    
    PAST_PERFORMANCE = auto()
    FORWARD_LOOKING_STATEMENTS = auto()
    RISK_WARNING = auto()
    NO_GUARANTEE = auto()
    HYPOTHETICAL_RESULTS = auto()
    MARKET_VOLATILITY = auto()
    INVESTMENT_SUITABILITY = auto()
    REGULATORY_COMPLIANCE = auto()
    DATA_ACCURACY = auto()
    THIRD_PARTY_INFORMATION = auto()


@dataclass
class ComplianceRule:
    """Represents a compliance rule for DDQ responses."""
    
    rule_id: str
    name: str
    framework: ComplianceFramework
    description: str
    pattern: str  # Regex pattern to match violations
    severity: ViolationSeverity
    auto_fix: bool = False  # Can this be automatically fixed?
    fix_action: Optional[str] = None  # How to fix
    disclaimer_type: Optional[DisclaimerType] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'framework': self.framework.value,
            'description': self.description,
            'pattern': self.pattern,
            'severity': self.severity.value,
            'auto_fix': self.auto_fix,
            'fix_action': self.fix_action,
            'disclaimer_type': self.disclaimer_type.name if self.disclaimer_type else None
        }


@dataclass
class ComplianceViolation:
    """Represents a detected compliance violation."""
    
    rule_id: str
    rule_name: str
    framework: ComplianceFramework
    severity: ViolationSeverity
    location: str
    matched_text: str
    description: str
    recommendation: str
    auto_fixable: bool = False
    suggested_fix: Optional[str] = None
    disclaimer_needed: Optional[DisclaimerType] = None
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert violation to dictionary."""
        return {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'framework': self.framework.value,
            'severity': self.severity.value,
            'location': self.location,
            'matched_text': self.matched_text,
            'description': self.description,
            'recommendation': self.recommendation,
            'auto_fixable': self.auto_fixable,
            'suggested_fix': self.suggested_fix,
            'disclaimer_needed': self.disclaimer_needed.name if self.disclaimer_needed else None,
            'confidence': self.confidence
        }


@dataclass
class ComplianceReport:
    """Comprehensive compliance analysis report."""
    
    response_id: str
    violations: List[ComplianceViolation]
    overall_risk_score: float  # 0-100, higher is riskier
    compliance_grade: str  # A, B, C, D, F
    critical_issues: int
    auto_fixable_issues: int
    required_disclaimers: List[DisclaimerType]
    recommendations: List[str]
    
    def to_json(self) -> str:
        """Export report as JSON."""
        return json.dumps({
            'response_id': self.response_id,
            'violations': [v.to_dict() for v in self.violations],
            'overall_risk_score': self.overall_risk_score,
            'compliance_grade': self.compliance_grade,
            'critical_issues': self.critical_issues,
            'auto_fixable_issues': self.auto_fixable_issues,
            'required_disclaimers': [d.name for d in self.required_disclaimers],
            'recommendations': self.recommendations
        }, indent=2)
    
    def get_violations_by_framework(self, framework: ComplianceFramework) -> List[ComplianceViolation]:
        """Get violations for specific regulatory framework."""
        return [v for v in self.violations if v.framework == framework]
    
    def get_violations_by_severity(self, min_severity: ViolationSeverity) -> List[ComplianceViolation]:
        """Get violations above minimum severity threshold."""
        return [v for v in self.violations if v.severity.value >= min_severity.value]


# Standard compliance rules for DDQ responses
STANDARD_COMPLIANCE_RULES = [
    ComplianceRule(
        rule_id="SEC-IA-001",
        name="No Performance Guarantees",
        framework=ComplianceFramework.SEC_INVESTMENT_ADVISERS_ACT,
        description="Prohibits guaranteeing investment performance or returns",
        pattern=r'(?:guarantee|assure|promise|ensure)s?\s+(?:return|performance|profit|gain)',
        severity=ViolationSeverity.CRITICAL,
        auto_fix=True,
        fix_action="Remove guarantee language and add appropriate disclaimers",
        disclaimer_type=DisclaimerType.NO_GUARANTEE
    ),
    
    ComplianceRule(
        rule_id="SEC-IA-002", 
        name="Past Performance Disclaimer Required",
        framework=ComplianceFramework.SEC_INVESTMENT_ADVISERS_ACT,
        description="Past performance discussions require appropriate disclaimers",
        pattern=r'(?:historical|past|previous)\s+(?:performance|return|result)',
        severity=ViolationSeverity.HIGH,
        auto_fix=True,
        fix_action="Add past performance disclaimer",
        disclaimer_type=DisclaimerType.PAST_PERFORMANCE
    ),
    
    ComplianceRule(
        rule_id="SEC-AF-001",
        name="No Misleading Statements",
        framework=ComplianceFramework.ANTI_FRAUD_PROVISIONS,
        description="Prohibits misleading or deceptive statements",
        pattern=r'(?:always|never|consistently)\s+(?:profitable|successful|positive|outperform)',
        severity=ViolationSeverity.CRITICAL,
        auto_fix=True,
        fix_action="Qualify absolute statements with appropriate disclaimers"
    ),
    
    ComplianceRule(
        rule_id="CFTC-CPO-001",
        name="Hypothetical Results Warning",
        framework=ComplianceFramework.CFTC_COMMODITY_POOL_OPERATORS,
        description="Hypothetical or model results require specific warnings",
        pattern=r'(?:model|hypothetical|simulated|backtested)\s+(?:result|performance|return)',
        severity=ViolationSeverity.HIGH,
        auto_fix=True,
        fix_action="Add hypothetical results disclaimer",
        disclaimer_type=DisclaimerType.HYPOTHETICAL_RESULTS
    ),
    
    ComplianceRule(
        rule_id="FID-001",
        name="Forward-Looking Statement Qualification",
        framework=ComplianceFramework.FIDUCIARY_STANDARDS,
        description="Forward-looking statements must be qualified",
        pattern=r'(?:will|expect|anticipate|project|forecast)\s+(?:\w+\s+)?(?:achieve|deliver|generate|return)',
        severity=ViolationSeverity.MEDIUM,
        auto_fix=True,
        fix_action="Add forward-looking statement disclaimer",
        disclaimer_type=DisclaimerType.FORWARD_LOOKING_STATEMENTS
    ),
    
    ComplianceRule(
        rule_id="RISK-001",
        name="Risk Disclosure Required",
        framework=ComplianceFramework.FIDUCIARY_STANDARDS,
        description="Investment discussions require risk disclosures",
        pattern=r'(?:investment|strategy|portfolio|fund)\s+(?:approach|method|process)(?!\s+(?:risk|volatility|disclaimer))',
        severity=ViolationSeverity.MEDIUM,
        auto_fix=True,
        fix_action="Add risk warning disclaimer",
        disclaimer_type=DisclaimerType.RISK_WARNING
    )
]


# Standard disclaimer templates
DISCLAIMER_TEMPLATES = {
    DisclaimerType.PAST_PERFORMANCE: """
**IMPORTANT DISCLAIMER:** Past performance is not indicative of future results. 
Investment returns and principal value will fluctuate, and investments may be worth 
more or less than their original cost when redeemed.
""".strip(),
    
    DisclaimerType.NO_GUARANTEE: """
**IMPORTANT DISCLAIMER:** No guarantee of investment performance or returns is made. 
All investments involve risk, including the potential loss of principal.
""".strip(),
    
    DisclaimerType.FORWARD_LOOKING_STATEMENTS: """
**FORWARD-LOOKING STATEMENTS:** This response contains forward-looking statements 
based on current expectations and assumptions. Actual results may differ materially 
from those projected or implied.
""".strip(),
    
    DisclaimerType.RISK_WARNING: """
**RISK WARNING:** All investments carry risk of loss. Investors should carefully 
consider investment objectives, risks, charges, and expenses before investing.
""".strip(),
    
    DisclaimerType.HYPOTHETICAL_RESULTS: """
**HYPOTHETICAL RESULTS:** Model or hypothetical performance results have inherent 
limitations and do not reflect actual trading. Hypothetical results do not represent 
actual performance and may not reflect the impact of material economic factors.
""".strip(),
    
    DisclaimerType.MARKET_VOLATILITY: """
**MARKET VOLATILITY WARNING:** Market volatility and other factors may cause 
actual results to vary significantly from projections or expectations expressed herein.
""".strip(),
    
    DisclaimerType.INVESTMENT_SUITABILITY: """
**SUITABILITY WARNING:** This information is not intended as investment advice. 
Investors should consult with qualified professionals before making investment decisions.
""".strip(),
    
    DisclaimerType.REGULATORY_COMPLIANCE: """
**REGULATORY NOTICE:** This response is provided for informational purposes and 
should not be construed as a solicitation or recommendation to purchase or sell securities.
""".strip(),
    
    DisclaimerType.DATA_ACCURACY: """
**DATA ACCURACY:** While information is obtained from sources believed reliable, 
accuracy and completeness cannot be guaranteed. Data is subject to change without notice.
""".strip(),
    
    DisclaimerType.THIRD_PARTY_INFORMATION: """
**THIRD PARTY INFORMATION:** Third party information is provided for reference only. 
The firm does not endorse or guarantee the accuracy of third party data or analysis.
""".strip()
}


# Risk scoring weights for different violation types
RISK_SCORING_WEIGHTS = {
    ViolationSeverity.CRITICAL: 25,
    ViolationSeverity.HIGH: 15,
    ViolationSeverity.MEDIUM: 8,
    ViolationSeverity.LOW: 3
}


# Compliance grade thresholds
COMPLIANCE_GRADE_THRESHOLDS = {
    'A': 5,    # 0-5 points
    'B': 15,   # 6-15 points  
    'C': 30,   # 16-30 points
    'D': 50,   # 31-50 points
    'F': 999   # 51+ points
}