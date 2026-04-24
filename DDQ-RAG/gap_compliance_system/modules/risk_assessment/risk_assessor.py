"""
Risk Assessor Engine
===================

Core risk assessment engine for identifying and evaluating regulatory
and fiduciary risks in DDQ responses.
"""

import re
import json
from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass
from collections import defaultdict, Counter
from datetime import datetime
from statistics import mean

from .risk_types import (
    RiskFactor, RiskLevel, RiskCategory, RegulatoryFramework, 
    FiduciaryRisk, FiduciaryStandard, RiskAssessmentReport,
    RISK_FACTOR_PATTERNS, FIDUCIARY_ASSESSMENT_CRITERIA,
    RISK_SCORING_WEIGHTS, RISK_GRADE_THRESHOLDS,
    REGULATORY_FRAMEWORK_WEIGHTS
)


@dataclass
class RiskAssessmentContext:
    """Context for risk assessment."""
    
    response_text: str
    response_id: str
    firm_type: str  # investment_adviser, cpo, etc.
    client_types: List[str]  # institutional, retail, etc.
    services_provided: List[str]  # advisory, management, etc.
    regulatory_registrations: List[RegulatoryFramework]
    assessment_date: Optional[datetime] = None
    
    def __post_init__(self):
        if self.assessment_date is None:
            self.assessment_date = datetime.now()


class RiskAssessor:
    """
    Advanced regulatory risk assessment system.
    
    Features:
    - Multi-framework regulatory risk analysis
    - Fiduciary duty compliance assessment
    - Risk factor identification and quantification
    - Regulatory exposure calculation
    - Automated risk grading and reporting
    """
    
    def __init__(self, custom_patterns: Optional[Dict[RiskCategory, Dict]] = None):
        """Initialize risk assessor with patterns and criteria."""
        
        self.risk_patterns = RISK_FACTOR_PATTERNS.copy()
        if custom_patterns:
            self.risk_patterns.update(custom_patterns)
        
        self.fiduciary_criteria = FIDUCIARY_ASSESSMENT_CRITERIA.copy()
        self.scoring_weights = RISK_SCORING_WEIGHTS.copy()
        self.framework_weights = REGULATORY_FRAMEWORK_WEIGHTS.copy()
        
        # Compile regex patterns for efficiency
        self._compile_risk_patterns()
        
        # Risk assessment history for trend analysis
        self.assessment_history = {}
    
    def _compile_risk_patterns(self):
        """Pre-compile regex patterns for all risk categories."""
        for category, pattern_data in self.risk_patterns.items():
            if 'patterns' in pattern_data:
                pattern_data['compiled_patterns'] = [
                    re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                    for pattern in pattern_data['patterns']
                ]
    
    def assess_risks(self, context: RiskAssessmentContext) -> RiskAssessmentReport:
        """
        Main risk assessment method.
        
        Args:
            context: Risk assessment context with response and firm details
            
        Returns:
            Comprehensive risk assessment report
        """
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(context)
        
        # Assess fiduciary risks
        fiduciary_risks = self._assess_fiduciary_risks(context)
        
        # Calculate regulatory exposure
        regulatory_exposure = self._calculate_regulatory_exposure(
            risk_factors, context.regulatory_registrations
        )
        
        # Calculate overall risk score and grade
        overall_risk_score = self._calculate_overall_risk_score(risk_factors, fiduciary_risks)
        risk_grade = self._calculate_risk_grade(overall_risk_score)
        
        # Generate action items
        immediate_actions = self._generate_immediate_actions(risk_factors, fiduciary_risks)
        monitoring_requirements = self._generate_monitoring_requirements(risk_factors)
        
        # Create comprehensive report
        report = RiskAssessmentReport(
            response_id=context.response_id,
            assessment_date=context.assessment_date,
            overall_risk_score=overall_risk_score,
            risk_grade=risk_grade,
            risk_factors=risk_factors,
            fiduciary_risks=fiduciary_risks,
            regulatory_exposure=regulatory_exposure,
            immediate_actions=immediate_actions,
            monitoring_requirements=monitoring_requirements
        )
        
        # Store in history for trend analysis
        self.assessment_history[context.response_id] = report
        
        return report
    
    def _identify_risk_factors(self, context: RiskAssessmentContext) -> List[RiskFactor]:
        """Identify risk factors in the response text."""
        
        risk_factors = []
        text = context.response_text
        
        for category, pattern_data in self.risk_patterns.items():
            if 'compiled_patterns' not in pattern_data:
                continue
            
            # Find matches for this risk category
            category_matches = []
            for pattern in pattern_data['compiled_patterns']:
                matches = list(pattern.finditer(text))
                category_matches.extend(matches)
            
            if category_matches:
                # Analyze risk severity
                risk_level = self._assess_risk_severity(category_matches, text, category, context)
                
                # Extract evidence
                evidence = [match.group(0) for match in category_matches[:5]]  # Limit evidence
                
                # Determine regulatory framework
                regulatory_framework = self._map_category_to_framework(category, context)
                
                # Create risk factor
                risk_factor = RiskFactor(
                    factor_id=f"{category.value}_{context.response_id}",
                    name=category.value.replace('_', ' ').title(),
                    category=category,
                    level=risk_level,
                    description=self._get_risk_description(category, len(category_matches)),
                    evidence=evidence,
                    regulatory_basis=regulatory_framework,
                    potential_consequences=pattern_data.get('consequences', []),
                    mitigation_actions=pattern_data.get('mitigations', []),
                    confidence=self._calculate_risk_confidence(category_matches, text)
                )
                risk_factors.append(risk_factor)
        
        return risk_factors
    
    def _assess_risk_severity(
        self,
        matches: List[re.Match],
        text: str,
        category: RiskCategory,
        context: RiskAssessmentContext
    ) -> RiskLevel:
        """Assess the severity level of identified risks."""
        
        match_count = len(matches)
        text_length = len(text.split())
        
        # Base severity on match density
        match_density = match_count / (text_length / 100) if text_length > 0 else 0
        
        # Category-specific severity thresholds
        severity_thresholds = {
            RiskCategory.PERFORMANCE_ADVERTISING: {'critical': 3, 'high': 2, 'medium': 1},
            RiskCategory.MISLEADING_STATEMENTS: {'critical': 2, 'high': 1, 'medium': 0.5},
            RiskCategory.FIDUCIARY_BREACH: {'critical': 2, 'high': 1, 'medium': 0.5},
            RiskCategory.INADEQUATE_DISCLOSURE: {'critical': 4, 'high': 2, 'medium': 1}
        }
        
        thresholds = severity_thresholds.get(category, {'critical': 3, 'high': 2, 'medium': 1})
        
        # Adjust for firm type and client type
        risk_multiplier = self._get_risk_multiplier(context)
        adjusted_density = match_density * risk_multiplier
        
        if adjusted_density >= thresholds['critical']:
            return RiskLevel.CRITICAL
        elif adjusted_density >= thresholds['high']:
            return RiskLevel.HIGH
        elif adjusted_density >= thresholds['medium']:
            return RiskLevel.MEDIUM
        elif match_count > 0:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL
    
    def _get_risk_multiplier(self, context: RiskAssessmentContext) -> float:
        """Calculate risk multiplier based on firm and client characteristics."""
        
        multiplier = 1.0
        
        # Firm type adjustments
        if context.firm_type == 'investment_adviser':
            multiplier *= 1.2  # Higher standard for IAs
        elif context.firm_type == 'commodity_pool_operator':
            multiplier *= 1.1
        
        # Client type adjustments
        if 'retail' in context.client_types:
            multiplier *= 1.3  # Higher protection for retail
        if 'institutional' in context.client_types and 'retail' not in context.client_types:
            multiplier *= 0.9  # Slightly lower for institutional-only
        
        # Service type adjustments
        if 'discretionary_management' in context.services_provided:
            multiplier *= 1.2  # Higher fiduciary standard
        
        return multiplier
    
    def _map_category_to_framework(
        self,
        category: RiskCategory,
        context: RiskAssessmentContext
    ) -> RegulatoryFramework:
        """Map risk category to applicable regulatory framework."""
        
        # Category to framework mapping
        category_framework_map = {
            RiskCategory.PERFORMANCE_ADVERTISING: RegulatoryFramework.SEC_INVESTMENT_ADVISERS,
            RiskCategory.MISLEADING_STATEMENTS: RegulatoryFramework.SEC_INVESTMENT_ADVISERS,
            RiskCategory.INADEQUATE_DISCLOSURE: RegulatoryFramework.SEC_INVESTMENT_ADVISERS,
            RiskCategory.FIDUCIARY_BREACH: RegulatoryFramework.DOL_FIDUCIARY,
            RiskCategory.COMMODITY_MISREPRESENTATION: RegulatoryFramework.CFTC_CEA,
            RiskCategory.INADEQUATE_RISK_DISCLOSURE: RegulatoryFramework.CFTC_CEA,
            RiskCategory.ANTI_FRAUD_VIOLATIONS: RegulatoryFramework.SEC_INVESTMENT_ADVISERS,
            RiskCategory.SUITABILITY_CONCERNS: RegulatoryFramework.FINRA_CONDUCT,
            RiskCategory.CONFLICTS_OF_INTEREST: RegulatoryFramework.SEC_INVESTMENT_ADVISERS,
            RiskCategory.CLIENT_BEST_INTEREST: RegulatoryFramework.DOL_FIDUCIARY
        }
        
        primary_framework = category_framework_map.get(category)
        
        # Check if framework applies to this firm
        if primary_framework in context.regulatory_registrations:
            return primary_framework
        
        # Fall back to most relevant registered framework
        if context.regulatory_registrations:
            return context.regulatory_registrations[0]
        
        return RegulatoryFramework.SEC_INVESTMENT_ADVISERS  # Default
    
    def _assess_fiduciary_risks(self, context: RiskAssessmentContext) -> List[FiduciaryRisk]:
        """Assess specific fiduciary duty risks."""
        
        fiduciary_risks = []
        text = context.response_text
        
        for standard, criteria in self.fiduciary_criteria.items():
            # Check for violations of this fiduciary standard
            violations = self._check_fiduciary_violations(text, standard, criteria)
            
            for violation in violations:
                fiduciary_risk = FiduciaryRisk(
                    standard=standard,
                    violation_type=violation['type'],
                    severity=violation['severity'],
                    description=violation['description'],
                    client_impact=violation['client_impact'],
                    regulatory_exposure=violation['regulatory_exposure'],
                    recommended_action=violation['recommended_action'],
                    confidence=violation['confidence']
                )
                fiduciary_risks.append(fiduciary_risk)
        
        return fiduciary_risks
    
    def _check_fiduciary_violations(
        self,
        text: str,
        standard: FiduciaryStandard,
        criteria: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """Check for specific fiduciary standard violations."""
        
        violations = []
        
        if standard == FiduciaryStandard.DUTY_OF_LOYALTY:
            violations.extend(self._check_loyalty_violations(text))
        elif standard == FiduciaryStandard.DUTY_OF_CARE:
            violations.extend(self._check_care_violations(text))
        elif standard == FiduciaryStandard.DISCLOSURE_OBLIGATIONS:
            violations.extend(self._check_disclosure_violations(text))
        
        return violations
    
    def _check_loyalty_violations(self, text: str) -> List[Dict[str, Any]]:
        """Check for duty of loyalty violations."""
        
        violations = []
        
        # Self-dealing indicators
        self_dealing_patterns = [
            r'(?:firm|we|our)\s+(?:benefit|advantage|profit|gain)',
            r'(?:internal|proprietary)\s+(?:product|fund|investment)',
            r'(?:revenue|income|fee)\s+(?:generation|enhancement|optimization)',
            r'(?:conflict|interest)(?!\s+(?:management|disclosure|policy))'
        ]
        
        self_dealing_matches = []
        for pattern in self_dealing_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            self_dealing_matches.extend(matches)
        
        if self_dealing_matches:
            violations.append({
                'type': 'potential_self_dealing',
                'severity': RiskLevel.HIGH,
                'description': f'Found {len(self_dealing_matches)} potential self-dealing indicators',
                'client_impact': 'Client interests may be subordinated to firm interests',
                'regulatory_exposure': 'Fiduciary duty breach claims possible',
                'recommended_action': 'Review for conflicts and enhance disclosure',
                'confidence': 0.8
            })
        
        # Inadequate conflict management
        conflict_mentions = len(re.findall(r'conflict', text, re.IGNORECASE))
        disclosure_mentions = len(re.findall(r'(?:disclose|disclosure)', text, re.IGNORECASE))
        
        if conflict_mentions > 0 and disclosure_mentions == 0:
            violations.append({
                'type': 'inadequate_conflict_disclosure',
                'severity': RiskLevel.MEDIUM,
                'description': 'Conflicts mentioned without adequate disclosure',
                'client_impact': 'Client may not understand potential conflicts',
                'regulatory_exposure': 'Disclosure requirement violations',
                'recommended_action': 'Add comprehensive conflict disclosures',
                'confidence': 0.9
            })
        
        return violations
    
    def _check_care_violations(self, text: str) -> List[Dict[str, Any]]:
        """Check for duty of care violations."""
        
        violations = []
        
        # Inadequate due diligence indicators
        due_diligence_patterns = [
            r'(?:due\s+diligence|research|analysis|review)',
            r'(?:monitor|oversight|supervision)',
            r'(?:evaluate|assess|examine|investigate)'
        ]
        
        dd_matches = 0
        for pattern in due_diligence_patterns:
            dd_matches += len(re.findall(pattern, text, re.IGNORECASE))
        
        # Investment decision indicators
        investment_patterns = [
            r'(?:investment|strategy|allocation|selection)',
            r'(?:recommend|advise|suggest|propose)',
            r'(?:portfolio|fund|security|asset)'
        ]
        
        investment_matches = 0
        for pattern in investment_patterns:
            investment_matches += len(re.findall(pattern, text, re.IGNORECASE))
        
        # Calculate due diligence ratio
        if investment_matches > 0:
            dd_ratio = dd_matches / investment_matches
            
            if dd_ratio < 0.3:  # Less than 30% due diligence mentions
                violations.append({
                    'type': 'inadequate_due_diligence',
                    'severity': RiskLevel.MEDIUM,
                    'description': f'Low due diligence ratio: {dd_ratio:.2f}',
                    'client_impact': 'Investment decisions may lack proper analysis',
                    'regulatory_exposure': 'Duty of care violations possible',
                    'recommended_action': 'Enhance due diligence documentation and processes',
                    'confidence': 0.7
                })
        
        return violations
    
    def _check_disclosure_violations(self, text: str) -> List[Dict[str, Any]]:
        """Check for disclosure obligation violations."""
        
        violations = []
        
        # Material information without disclosure
        material_patterns = [
            r'(?:material|significant|important)\s+(?:fact|information|relationship)',
            r'(?:fee|compensation|payment|commission)',
            r'(?:conflict|interest|relationship|agreement)'
        ]
        
        material_matches = []
        for pattern in material_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            material_matches.extend(matches)
        
        # Check if material items have disclosure language nearby
        undisclosed_items = []
        for match in material_matches:
            context_window = text[max(0, match.start()-50):min(len(text), match.end()+50)]
            has_disclosure = bool(re.search(
                r'(?:disclose|disclosure|inform|notify|transparent)',
                context_window, re.IGNORECASE
            ))
            
            if not has_disclosure:
                undisclosed_items.append(match.group(0))
        
        if undisclosed_items:
            violations.append({
                'type': 'inadequate_material_disclosure',
                'severity': RiskLevel.HIGH,
                'description': f'Found {len(undisclosed_items)} material items without disclosure',
                'client_impact': 'Clients may lack material information for decisions',
                'regulatory_exposure': 'Disclosure requirement violations',
                'recommended_action': 'Implement comprehensive disclosure procedures',
                'confidence': 0.8
            })
        
        return violations
    
    def _calculate_regulatory_exposure(
        self,
        risk_factors: List[RiskFactor],
        registered_frameworks: List[RegulatoryFramework]
    ) -> Dict[RegulatoryFramework, float]:
        """Calculate regulatory exposure by framework."""
        
        exposure = defaultdict(float)
        
        for risk_factor in risk_factors:
            framework = risk_factor.regulatory_basis
            
            # Base score from risk level
            level_scores = {
                RiskLevel.CRITICAL: 25,
                RiskLevel.HIGH: 15,
                RiskLevel.MEDIUM: 8,
                RiskLevel.LOW: 3,
                RiskLevel.MINIMAL: 0
            }
            
            base_score = level_scores[risk_factor.level]
            
            # Apply framework weight and confidence
            framework_weight = self.framework_weights.get(framework, 1.0)
            adjusted_score = base_score * framework_weight * risk_factor.confidence
            
            exposure[framework] += adjusted_score
        
        # Normalize scores to 0-100 range
        if exposure:
            max_possible = max(exposure.values()) if exposure.values() else 1
            for framework in exposure:
                exposure[framework] = min(100, (exposure[framework] / max_possible) * 100)
        
        return dict(exposure)
    
    def _calculate_overall_risk_score(
        self,
        risk_factors: List[RiskFactor],
        fiduciary_risks: List[FiduciaryRisk]
    ) -> float:
        """Calculate overall risk score (0-100, higher is riskier)."""
        
        total_score = 0.0
        
        # Score from risk factors
        for risk_factor in risk_factors:
            category_weight = self.scoring_weights.get(risk_factor.category, 10)
            level_multipliers = {
                RiskLevel.CRITICAL: 2.0,
                RiskLevel.HIGH: 1.5,
                RiskLevel.MEDIUM: 1.0,
                RiskLevel.LOW: 0.5,
                RiskLevel.MINIMAL: 0.1
            }
            
            level_multiplier = level_multipliers[risk_factor.level]
            risk_score = category_weight * level_multiplier * risk_factor.confidence
            total_score += risk_score
        
        # Score from fiduciary risks
        for fiduciary_risk in fiduciary_risks:
            fiduciary_multipliers = {
                RiskLevel.CRITICAL: 30,
                RiskLevel.HIGH: 20,
                RiskLevel.MEDIUM: 10,
                RiskLevel.LOW: 5,
                RiskLevel.MINIMAL: 1
            }
            
            fiduciary_score = fiduciary_multipliers[fiduciary_risk.severity] * fiduciary_risk.confidence
            total_score += fiduciary_score
        
        return min(100, total_score)  # Cap at 100
    
    def _calculate_risk_grade(self, risk_score: float) -> str:
        """Calculate risk grade based on overall risk score."""
        
        for grade, threshold in RISK_GRADE_THRESHOLDS.items():
            if risk_score <= threshold:
                return grade
        
        return 'F'  # Worst case
    
    def _generate_immediate_actions(
        self,
        risk_factors: List[RiskFactor],
        fiduciary_risks: List[FiduciaryRisk]
    ) -> List[str]:
        """Generate immediate action items based on identified risks."""
        
        actions = []
        
        # Critical risk factor actions
        critical_factors = [rf for rf in risk_factors if rf.level == RiskLevel.CRITICAL]
        for factor in critical_factors:
            actions.append(f"CRITICAL: {factor.mitigation_actions[0] if factor.mitigation_actions else 'Address ' + factor.name}")
        
        # High-severity fiduciary risks
        high_fiduciary = [fr for fr in fiduciary_risks if fr.severity in [RiskLevel.CRITICAL, RiskLevel.HIGH]]
        for risk in high_fiduciary:
            actions.append(f"FIDUCIARY: {risk.recommended_action}")
        
        # Category-specific actions
        category_counts = Counter([rf.category for rf in risk_factors])
        for category, count in category_counts.most_common(3):
            if count >= 2:  # Multiple instances of same category
                actions.append(f"Review {category.value.replace('_', ' ')} procedures: {count} issues identified")
        
        return actions[:10]  # Limit to top 10 actions
    
    def _generate_monitoring_requirements(self, risk_factors: List[RiskFactor]) -> List[str]:
        """Generate ongoing monitoring requirements."""
        
        monitoring = []
        
        # Framework-based monitoring
        frameworks = set(rf.regulatory_basis for rf in risk_factors)
        for framework in frameworks:
            framework_factors = [rf for rf in risk_factors if rf.regulatory_basis == framework]
            if len(framework_factors) >= 2:
                monitoring.append(f"Enhanced {framework.value.replace('_', ' ')} compliance monitoring")
        
        # Category-based monitoring
        high_risk_categories = [rf.category for rf in risk_factors if rf.level.value >= 3]
        if high_risk_categories:
            category_names = [cat.value.replace('_', ' ') for cat in set(high_risk_categories)]
            monitoring.append(f"Regular review of: {', '.join(category_names[:3])}")
        
        # General monitoring
        if any(rf.level == RiskLevel.CRITICAL for rf in risk_factors):
            monitoring.append("Weekly critical risk factor review until resolved")
        
        if len(risk_factors) > 5:
            monitoring.append("Monthly comprehensive risk assessment")
        
        return monitoring
    
    def _get_risk_description(self, category: RiskCategory, match_count: int) -> str:
        """Get human-readable description for risk category."""
        
        descriptions = {
            RiskCategory.PERFORMANCE_ADVERTISING: f"Performance advertising concerns identified ({match_count} instances)",
            RiskCategory.MISLEADING_STATEMENTS: f"Potentially misleading statements detected ({match_count} instances)",
            RiskCategory.INADEQUATE_DISCLOSURE: f"Disclosure adequacy issues found ({match_count} instances)",
            RiskCategory.FIDUCIARY_BREACH: f"Potential fiduciary duty concerns ({match_count} instances)",
            RiskCategory.INADEQUATE_RISK_DISCLOSURE: f"Risk disclosure gaps identified ({match_count} instances)"
        }
        
        return descriptions.get(category, f"Risk factor identified: {category.value} ({match_count} instances)")
    
    def _calculate_risk_confidence(self, matches: List[re.Match], text: str) -> float:
        """Calculate confidence level for risk identification."""
        
        base_confidence = 0.8
        
        # Adjust based on match quality
        if matches:
            avg_match_length = sum(len(match.group(0)) for match in matches) / len(matches)
            if avg_match_length > 20:  # Longer matches are more confident
                base_confidence *= 1.1
            
            # Check for context that might reduce confidence (e.g., disclaimers)
            for match in matches:
                context_window = text[max(0, match.start()-50):min(len(text), match.end()+50)]
                if any(term in context_window.lower() 
                      for term in ['disclaimer', 'hypothetical', 'example', 'illustration']):
                    base_confidence *= 0.9
                    break
        
        return min(1.0, base_confidence)
    
    def get_risk_trends(self, response_ids: List[str]) -> Dict[str, Any]:
        """Analyze risk trends across multiple assessments."""
        
        if not response_ids or not self.assessment_history:
            return {}
        
        relevant_reports = [
            self.assessment_history[rid] for rid in response_ids 
            if rid in self.assessment_history
        ]
        
        if not relevant_reports:
            return {}
        
        # Risk score trends
        risk_scores = [report.overall_risk_score for report in relevant_reports]
        
        # Category trends
        category_counts = defaultdict(int)
        for report in relevant_reports:
            for factor in report.risk_factors:
                category_counts[factor.category] += 1
        
        # Grade distribution
        grade_distribution = Counter([report.risk_grade for report in relevant_reports])
        
        trends = {
            'total_assessments': len(relevant_reports),
            'average_risk_score': mean(risk_scores),
            'score_trend': 'improving' if len(risk_scores) > 1 and risk_scores[-1] < risk_scores[0] else 'stable',
            'most_common_risks': dict(category_counts.most_common(5)),
            'grade_distribution': dict(grade_distribution),
            'improvement_needed': sum(1 for score in risk_scores if score > 50)
        }
        
        return trends