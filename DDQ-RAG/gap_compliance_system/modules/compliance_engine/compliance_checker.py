"""
Compliance Checker Engine
=========================

Core compliance checking engine that validates DDQ responses against
regulatory requirements and identifies potential compliance violations.
"""

import re
import json
from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass
from collections import defaultdict

from .compliance_types import (
    ComplianceRule, ComplianceViolation, ComplianceReport, ComplianceFramework,
    ViolationSeverity, DisclaimerType, STANDARD_COMPLIANCE_RULES,
    RISK_SCORING_WEIGHTS, COMPLIANCE_GRADE_THRESHOLDS
)


@dataclass
class ComplianceContext:
    """Context for compliance checking."""
    
    response_text: str
    response_id: str
    firm_type: str  # "investment_adviser", "commodity_pool_operator", etc.
    client_type: str  # "institutional", "retail", "qualified_purchaser"
    jurisdiction: str = "US"  # Regulatory jurisdiction
    custom_rules: List[ComplianceRule] = None
    
    def __post_init__(self):
        if self.custom_rules is None:
            self.custom_rules = []


class ComplianceChecker:
    """
    Advanced compliance checking system for DDQ responses.
    
    Features:
    - Multi-framework regulatory compliance (SEC, CFTC, FINRA)
    - Automatic violation detection and scoring
    - Risk assessment and grading
    - Compliance rule customization
    - Detailed violation reporting
    """
    
    def __init__(self, custom_rules: Optional[List[ComplianceRule]] = None):
        """Initialize compliance checker with standard and custom rules."""
        
        self.standard_rules = STANDARD_COMPLIANCE_RULES.copy()
        self.custom_rules = custom_rules or []
        self.all_rules = self.standard_rules + self.custom_rules
        
        # Compile regex patterns for efficiency
        self._compile_rule_patterns()
        
        # Framework-specific configurations
        self.framework_configs = self._load_framework_configs()
    
    def _compile_rule_patterns(self):
        """Pre-compile regex patterns for all rules."""
        for rule in self.all_rules:
            if rule.pattern:
                rule._compiled_pattern = re.compile(
                    rule.pattern, 
                    re.IGNORECASE | re.MULTILINE
                )
    
    def _load_framework_configs(self) -> Dict[ComplianceFramework, Dict]:
        """Load framework-specific configurations."""
        return {
            ComplianceFramework.SEC_INVESTMENT_ADVISERS_ACT: {
                'strict_mode': True,
                'performance_language_forbidden': True,
                'past_performance_disclaimer_required': True
            },
            ComplianceFramework.CFTC_COMMODITY_POOL_OPERATORS: {
                'hypothetical_results_warning_required': True,
                'risk_disclosure_mandatory': True
            },
            ComplianceFramework.FIDUCIARY_STANDARDS: {
                'forward_looking_qualification_required': True,
                'investment_suitability_warning': True
            }
        }
    
    def check_compliance(self, context: ComplianceContext) -> ComplianceReport:
        """
        Main compliance checking method.
        
        Args:
            context: Compliance checking context with response and metadata
            
        Returns:
            Comprehensive compliance report with violations and recommendations
        """
        violations = []
        
        # Apply all relevant rules
        applicable_rules = self._get_applicable_rules(context)
        
        for rule in applicable_rules:
            rule_violations = self._check_rule(rule, context)
            violations.extend(rule_violations)
        
        # Perform framework-specific checks
        framework_violations = self._perform_framework_checks(context)
        violations.extend(framework_violations)
        
        # Generate comprehensive report
        return self._generate_compliance_report(context, violations)
    
    def _get_applicable_rules(self, context: ComplianceContext) -> List[ComplianceRule]:
        """Get rules applicable to the given context."""
        applicable_rules = []
        
        for rule in self.all_rules:
            # Check if rule applies to firm type
            if self._rule_applies_to_context(rule, context):
                applicable_rules.append(rule)
        
        return applicable_rules
    
    def _rule_applies_to_context(self, rule: ComplianceRule, context: ComplianceContext) -> bool:
        """Determine if a rule applies to the given context."""
        
        # Framework applicability based on firm type
        framework_applicability = {
            ComplianceFramework.SEC_INVESTMENT_ADVISERS_ACT: ["investment_adviser", "ria"],
            ComplianceFramework.CFTC_COMMODITY_POOL_OPERATORS: ["commodity_pool_operator", "cpo", "cta"],
            ComplianceFramework.FINRA_RULES: ["broker_dealer", "bd"],
            ComplianceFramework.FIDUCIARY_STANDARDS: ["investment_adviser", "ria", "pension_manager"],
            ComplianceFramework.ANTI_FRAUD_PROVISIONS: ["all"]  # Applies to all
        }
        
        applicable_firm_types = framework_applicability.get(rule.framework, ["all"])
        
        if "all" in applicable_firm_types:
            return True
            
        return context.firm_type.lower() in applicable_firm_types
    
    def _check_rule(self, rule: ComplianceRule, context: ComplianceContext) -> List[ComplianceViolation]:
        """Check a single compliance rule against the response."""
        violations = []
        
        if not hasattr(rule, '_compiled_pattern') or not rule._compiled_pattern:
            return violations
        
        # Find all matches for the rule pattern
        matches = list(rule._compiled_pattern.finditer(context.response_text))
        
        for match in matches:
            # Calculate confidence based on context analysis
            confidence = self._calculate_match_confidence(match, context.response_text, rule)
            
            # Only report high-confidence matches
            if confidence >= 0.6:
                violation = ComplianceViolation(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    framework=rule.framework,
                    severity=rule.severity,
                    location=f"Position {match.start()}-{match.end()}",
                    matched_text=match.group(0),
                    description=rule.description,
                    recommendation=self._get_violation_recommendation(rule),
                    auto_fixable=rule.auto_fix,
                    suggested_fix=rule.fix_action,
                    disclaimer_needed=rule.disclaimer_type,
                    confidence=confidence
                )
                violations.append(violation)
        
        return violations
    
    def _calculate_match_confidence(self, match: re.Match, text: str, rule: ComplianceRule) -> float:
        """Calculate confidence score for a pattern match."""
        
        # Base confidence
        confidence = 0.8
        
        # Context analysis - look at surrounding text
        start_pos = max(0, match.start() - 50)
        end_pos = min(len(text), match.end() + 50)
        context_text = text[start_pos:end_pos].lower()
        
        # Reduce confidence if already disclaimed
        disclaimer_indicators = [
            'disclaimer', 'warning', 'risk', 'not guaranteed', 'no assurance',
            'subject to', 'may vary', 'past performance', 'hypothetical'
        ]
        
        if any(indicator in context_text for indicator in disclaimer_indicators):
            confidence *= 0.7
        
        # Increase confidence for certain rule types
        high_confidence_rules = ['SEC-IA-001', 'SEC-AF-001']  # Performance guarantees, misleading statements
        if rule.rule_id in high_confidence_rules:
            confidence *= 1.2
        
        # Adjust for match quality
        match_text = match.group(0).lower()
        if len(match_text) > 10:  # Longer matches are more confident
            confidence *= 1.1
        
        return min(1.0, confidence)
    
    def _perform_framework_checks(self, context: ComplianceContext) -> List[ComplianceViolation]:
        """Perform framework-specific compliance checks."""
        violations = []
        
        # SEC Investment Advisers Act specific checks
        if context.firm_type in ['investment_adviser', 'ria']:
            violations.extend(self._check_sec_ia_requirements(context))
        
        # CFTC Commodity Pool Operator specific checks  
        if context.firm_type in ['commodity_pool_operator', 'cpo']:
            violations.extend(self._check_cftc_cpo_requirements(context))
        
        # Fiduciary standards checks
        violations.extend(self._check_fiduciary_requirements(context))
        
        return violations
    
    def _check_sec_ia_requirements(self, context: ComplianceContext) -> List[ComplianceViolation]:
        """Check SEC Investment Advisers Act specific requirements."""
        violations = []
        text = context.response_text
        
        # Check for performance advertising rules
        performance_patterns = [
            r'(?:beat|outperform|exceed).*(?:market|benchmark|index)',
            r'(?:top|best|superior).*(?:performance|manager|fund)',
            r'\d+%.*(?:annual|yearly).*return'
        ]
        
        for pattern in performance_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                # Check if properly disclaimed
                context_window = text[max(0, match.start()-100):min(len(text), match.end()+100)]
                has_disclaimer = bool(re.search(r'past performance|no guarantee|not indicative', 
                                               context_window, re.IGNORECASE))
                
                if not has_disclaimer:
                    violation = ComplianceViolation(
                        rule_id="SEC-IA-PERF",
                        rule_name="SEC Performance Advertising Rules",
                        framework=ComplianceFramework.SEC_INVESTMENT_ADVISERS_ACT,
                        severity=ViolationSeverity.HIGH,
                        location=f"Position {match.start()}-{match.end()}",
                        matched_text=match.group(0),
                        description="Performance claims require appropriate disclaimers",
                        recommendation="Add SEC-compliant performance disclaimer",
                        auto_fixable=True,
                        disclaimer_needed=DisclaimerType.PAST_PERFORMANCE
                    )
                    violations.append(violation)
        
        return violations
    
    def _check_cftc_cpo_requirements(self, context: ComplianceContext) -> List[ComplianceViolation]:
        """Check CFTC Commodity Pool Operator specific requirements."""
        violations = []
        text = context.response_text
        
        # Check for required risk disclosures
        commodity_mentions = re.findall(r'(?:commodity|futures|derivatives?|swap)', text, re.IGNORECASE)
        
        if commodity_mentions:
            # Check for adequate risk disclosure
            risk_disclosures = re.findall(r'risk|volatility|loss|adverse', text, re.IGNORECASE)
            
            risk_ratio = len(risk_disclosures) / len(commodity_mentions)
            
            if risk_ratio < 0.5:  # Less than 1 risk mention per 2 commodity mentions
                violation = ComplianceViolation(
                    rule_id="CFTC-RISK",
                    rule_name="CFTC Risk Disclosure Requirements",
                    framework=ComplianceFramework.CFTC_COMMODITY_POOL_OPERATORS,
                    severity=ViolationSeverity.HIGH,
                    location="Throughout response",
                    matched_text=f"Commodity mentions: {len(commodity_mentions)}, Risk disclosures: {len(risk_disclosures)}",
                    description="Insufficient risk disclosure for commodity investments",
                    recommendation="Add comprehensive risk warnings for commodity investments",
                    auto_fixable=True,
                    disclaimer_needed=DisclaimerType.RISK_WARNING
                )
                violations.append(violation)
        
        return violations
    
    def _check_fiduciary_requirements(self, context: ComplianceContext) -> List[ComplianceViolation]:
        """Check fiduciary standard requirements."""
        violations = []
        text = context.response_text
        
        # Check for client best interest considerations
        recommendation_patterns = [
            r'recommend|suggest|advise|should',
            r'suitable|appropriate|right\s+for',
            r'best.*(?:choice|option|approach)'
        ]
        
        recommendation_matches = []
        for pattern in recommendation_patterns:
            recommendation_matches.extend(list(re.finditer(pattern, text, re.IGNORECASE)))
        
        if recommendation_matches:
            # Check for suitability disclaimers
            suitability_disclaimers = re.findall(
                r'suitability|investment objectives|risk tolerance|consult.*advisor',
                text, re.IGNORECASE
            )
            
            if not suitability_disclaimers:
                violation = ComplianceViolation(
                    rule_id="FID-SUIT",
                    rule_name="Investment Suitability Disclosure",
                    framework=ComplianceFramework.FIDUCIARY_STANDARDS,
                    severity=ViolationSeverity.MEDIUM,
                    location="Multiple locations",
                    matched_text=f"{len(recommendation_matches)} recommendation phrases found",
                    description="Recommendations require suitability disclaimers",
                    recommendation="Add investment suitability disclaimer",
                    auto_fixable=True,
                    disclaimer_needed=DisclaimerType.INVESTMENT_SUITABILITY
                )
                violations.append(violation)
        
        return violations
    
    def _get_violation_recommendation(self, rule: ComplianceRule) -> str:
        """Get specific recommendation for a compliance rule."""
        
        base_recommendations = {
            ComplianceFramework.SEC_INVESTMENT_ADVISERS_ACT: "Ensure compliance with SEC advertising and disclosure rules",
            ComplianceFramework.CFTC_COMMODITY_POOL_OPERATORS: "Add CFTC-required risk disclosures",
            ComplianceFramework.FIDUCIARY_STANDARDS: "Consider client best interests and add suitability warnings",
            ComplianceFramework.ANTI_FRAUD_PROVISIONS: "Remove potentially misleading statements"
        }
        
        if rule.fix_action:
            return rule.fix_action
            
        return base_recommendations.get(rule.framework, "Review and address compliance concern")
    
    def _generate_compliance_report(self, context: ComplianceContext, violations: List[ComplianceViolation]) -> ComplianceReport:
        """Generate comprehensive compliance report."""
        
        # Count violations by severity
        critical_issues = sum(1 for v in violations if v.severity == ViolationSeverity.CRITICAL)
        auto_fixable_issues = sum(1 for v in violations if v.auto_fixable)
        
        # Calculate risk score
        risk_score = sum(RISK_SCORING_WEIGHTS[v.severity] * v.confidence for v in violations)
        
        # Determine compliance grade
        compliance_grade = self._calculate_compliance_grade(risk_score)
        
        # Collect required disclaimers
        required_disclaimers = list(set(v.disclaimer_needed for v in violations if v.disclaimer_needed))
        
        # Generate prioritized recommendations
        recommendations = self._generate_compliance_recommendations(violations)
        
        return ComplianceReport(
            response_id=context.response_id,
            violations=violations,
            overall_risk_score=risk_score,
            compliance_grade=compliance_grade,
            critical_issues=critical_issues,
            auto_fixable_issues=auto_fixable_issues,
            required_disclaimers=required_disclaimers,
            recommendations=recommendations
        )
    
    def _calculate_compliance_grade(self, risk_score: float) -> str:
        """Calculate compliance grade based on risk score."""
        for grade, threshold in COMPLIANCE_GRADE_THRESHOLDS.items():
            if risk_score <= threshold:
                return grade
        return 'F'  # Worst case
    
    def _generate_compliance_recommendations(self, violations: List[ComplianceViolation]) -> List[str]:
        """Generate prioritized compliance recommendations."""
        recommendations = []
        
        # Group by severity and framework
        critical_violations = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
        high_violations = [v for v in violations if v.severity == ViolationSeverity.HIGH]
        
        if critical_violations:
            recommendations.append(
                f"CRITICAL: Address {len(critical_violations)} critical compliance issues immediately"
            )
        
        if high_violations:
            recommendations.append(
                f"HIGH PRIORITY: Resolve {len(high_violations)} high-risk compliance concerns"
            )
        
        # Framework-specific recommendations
        by_framework = defaultdict(list)
        for violation in violations:
            by_framework[violation.framework].append(violation)
        
        for framework, framework_violations in by_framework.items():
            if len(framework_violations) > 1:
                recommendations.append(
                    f"Review {framework.value.replace('_', ' ').title()} compliance: {len(framework_violations)} issues"
                )
        
        # Auto-fixable issues
        auto_fixable = [v for v in violations if v.auto_fixable]
        if auto_fixable:
            recommendations.append(
                f"Consider auto-fix for {len(auto_fixable)} automatically resolvable issues"
            )
        
        return recommendations
    
    def get_violation_statistics(self, violations: List[ComplianceViolation]) -> Dict[str, Any]:
        """Generate violation statistics for analysis."""
        
        stats = {
            'total_violations': len(violations),
            'by_severity': {
                'critical': sum(1 for v in violations if v.severity == ViolationSeverity.CRITICAL),
                'high': sum(1 for v in violations if v.severity == ViolationSeverity.HIGH),
                'medium': sum(1 for v in violations if v.severity == ViolationSeverity.MEDIUM),
                'low': sum(1 for v in violations if v.severity == ViolationSeverity.LOW)
            },
            'by_framework': {},
            'auto_fixable': sum(1 for v in violations if v.auto_fixable),
            'avg_confidence': sum(v.confidence for v in violations) / len(violations) if violations else 0
        }
        
        # Framework breakdown
        for violation in violations:
            framework_name = violation.framework.value
            if framework_name not in stats['by_framework']:
                stats['by_framework'][framework_name] = 0
            stats['by_framework'][framework_name] += 1
        
        return stats
    
    def add_custom_rule(self, rule: ComplianceRule):
        """Add a custom compliance rule."""
        self.custom_rules.append(rule)
        self.all_rules.append(rule)
        
        # Compile the new rule's pattern
        if rule.pattern:
            rule._compiled_pattern = re.compile(
                rule.pattern,
                re.IGNORECASE | re.MULTILINE
            )
    
    def update_rule(self, rule_id: str, updated_rule: ComplianceRule):
        """Update an existing compliance rule."""
        for i, rule in enumerate(self.all_rules):
            if rule.rule_id == rule_id:
                self.all_rules[i] = updated_rule
                # Recompile pattern
                if updated_rule.pattern:
                    updated_rule._compiled_pattern = re.compile(
                        updated_rule.pattern,
                        re.IGNORECASE | re.MULTILINE
                    )
                break
    
    def remove_rule(self, rule_id: str):
        """Remove a compliance rule."""
        self.all_rules = [rule for rule in self.all_rules if rule.rule_id != rule_id]
        self.custom_rules = [rule for rule in self.custom_rules if rule.rule_id != rule_id]