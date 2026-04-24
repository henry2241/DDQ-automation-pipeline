"""
Gap Detection Engine
===================

Core engine for detecting documentation gaps, content issues, and compliance risks
in DDQ responses using pattern matching, NLP analysis, and rule-based detection.
"""

import re
import json
from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from collections import Counter, defaultdict

from .gap_types import (
    Gap, GapType, GapSeverity, GapCategory, GapReport,
    GAP_DETECTION_RULES, COMPLIANCE_RISK_THRESHOLDS
)


@dataclass
class DetectionContext:
    """Context for gap detection analysis."""
    
    response_text: str
    question_text: str
    source_documents: List[str]
    response_id: str
    question_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class GapDetector:
    """
    Advanced gap detection system for DDQ responses.
    
    Features:
    - Pattern-based detection for common gap types
    - Source verification and fact-checking
    - Interpretive content analysis
    - Compliance risk assessment
    - Depth consistency analysis
    """
    
    def __init__(self):
        self.detection_rules = GAP_DETECTION_RULES.copy()
        self.compliance_thresholds = COMPLIANCE_RISK_THRESHOLDS.copy()
        self.custom_patterns = {}
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
        
        # Source verification patterns
        self.source_patterns = {
            'citation': r'(?:as stated|per|according to|from).*(?:section|page|\d+)',
            'quote': r'["\'].*["\']',
            'reference': r'(?:document|file|source|material).*states?'
        }
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        for gap_type, rule in self.detection_rules.items():
            if 'patterns' in rule:
                rule['compiled_patterns'] = [
                    re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                    for pattern in rule['patterns']
                ]
    
    def detect_gaps(self, context: DetectionContext) -> GapReport:
        """
        Main gap detection method.
        
        Args:
            context: Detection context with response, question, and sources
            
        Returns:
            Comprehensive gap report with findings and recommendations
        """
        gaps = []
        
        # Run all detection methods
        gaps.extend(self._detect_pattern_gaps(context))
        gaps.extend(self._detect_interpretive_content(context))
        gaps.extend(self._detect_factual_inconsistencies(context))
        gaps.extend(self._detect_evasive_responses(context))
        gaps.extend(self._detect_compliance_risks(context))
        gaps.extend(self._detect_depth_inconsistencies(context))
        gaps.extend(self._detect_missing_disclaimers(context))
        
        # Generate comprehensive report
        return self._generate_report(context, gaps)
    
    def _detect_pattern_gaps(self, context: DetectionContext) -> List[Gap]:
        """Detect gaps using predefined pattern rules."""
        gaps = []
        text = context.response_text
        
        for gap_type, rule in self.detection_rules.items():
            if 'compiled_patterns' not in rule:
                continue
                
            matches = []
            for pattern in rule['compiled_patterns']:
                pattern_matches = list(pattern.finditer(text))
                matches.extend(pattern_matches)
            
            if matches:
                # Calculate confidence based on match count and context
                confidence = min(1.0, len(matches) * 0.2)
                
                evidence = [match.group(0) for match in matches[:5]]  # Limit evidence
                
                gap = Gap(
                    gap_type=gap_type,
                    severity=rule.get('severity', GapSeverity.MEDIUM),
                    category=rule.get('category', GapCategory.CONTENT_QUALITY),
                    description=self._get_gap_description(gap_type, len(matches)),
                    location=f"Multiple locations ({len(matches)} matches)",
                    evidence=evidence,
                    recommendation=self._get_gap_recommendation(gap_type),
                    confidence=confidence
                )
                gaps.append(gap)
        
        return gaps
    
    def _detect_interpretive_content(self, context: DetectionContext) -> List[Gap]:
        """Detect excessive interpretive content in responses."""
        gaps = []
        text = context.response_text
        
        # Count interpretive phrases
        interpretive_patterns = [
            r'(?:likely|probably|appears?|seems?)\s+(?:to|that)',
            r'(?:suggests?|implies?|indicates?)\s+(?:that|the)',
            r'(?:sophisticated|advanced|comprehensive)\s+(?:understanding|approach)',
            r'(?:leverages?|utilizes?|employs?)\s+(?:its|the|advanced)',
            r'(?:based on|due to|given)\s+(?:its|the|general)',
            r'(?:typical|standard|common)\s+(?:approach|method|practice)'
        ]
        
        total_words = len(text.split())
        interpretive_matches = 0
        evidence = []
        
        for pattern in interpretive_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            interpretive_matches += len(matches)
            evidence.extend([match.group(0) for match in matches[:3]])
        
        if total_words > 0:
            interpretive_ratio = interpretive_matches / (total_words / 100)  # Per 100 words
            
            if interpretive_ratio > 5:  # More than 5 interpretive phrases per 100 words
                severity = GapSeverity.HIGH if interpretive_ratio > 10 else GapSeverity.MEDIUM
                
                gap = Gap(
                    gap_type=GapType.EXCESSIVE_INTERPRETATION,
                    severity=severity,
                    category=GapCategory.CONTENT_QUALITY,
                    description=f"High interpretive content ratio: {interpretive_ratio:.1f} per 100 words",
                    location="Throughout response",
                    evidence=evidence[:5],
                    recommendation="Replace interpretive language with direct source quotes and facts",
                    confidence=min(1.0, interpretive_ratio / 15)
                )
                gaps.append(gap)
        
        return gaps
    
    def _detect_factual_inconsistencies(self, context: DetectionContext) -> List[Gap]:
        """Detect potential factual inconsistencies and unverified claims."""
        gaps = []
        text = context.response_text
        
        # Look for unsourced numerical claims
        numerical_patterns = [
            r'sharpe\s+ratio\s+(?:of\s+)?(\d+\.?\d*)',
            r'correlation\s+(?:of\s+)?(\d+\.?\d*)%?',
            r'(?:aum|assets)\s+(?:growth|increase)\s+(?:of\s+)?(\d+\.?\d*)%',
            r'(?:return|performance)\s+(?:of\s+)?(\d+\.?\d*)%',
            r'volatility\s+(?:of\s+)?(\d+\.?\d*)%'
        ]
        
        unsourced_claims = []
        for pattern in numerical_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                # Check if claim is properly sourced within 50 characters
                start_pos = max(0, match.start() - 50)
                end_pos = min(len(text), match.end() + 50)
                context_text = text[start_pos:end_pos]
                
                # Look for source indicators
                source_indicators = ['source:', 'per', 'according to', 'stated in', 'document', 'file']
                has_source = any(indicator in context_text.lower() for indicator in source_indicators)
                
                if not has_source:
                    unsourced_claims.append(match.group(0))
        
        if unsourced_claims:
            gap = Gap(
                gap_type=GapType.FACTUAL_INCONSISTENCY,
                severity=GapSeverity.HIGH,
                category=GapCategory.FACTUAL_ACCURACY,
                description=f"Found {len(unsourced_claims)} unsourced numerical claims",
                location="Multiple locations",
                evidence=unsourced_claims[:5],
                recommendation="Verify all numerical claims against source documents or add disclaimers",
                confidence=0.8
            )
            gaps.append(gap)
        
        return gaps
    
    def _detect_evasive_responses(self, context: DetectionContext) -> List[Gap]:
        """Detect evasive or incomplete responses to investor queries."""
        gaps = []
        text = context.response_text
        
        evasive_patterns = [
            r'(?:materials?|documents?|information)\s+(?:do\s+not|does\s+not|lack)\s+(?:specify|detail|contain)',
            r'(?:not\s+)?(?:explicitly|specifically|clearly)\s+(?:detailed|stated|mentioned)',
            r'would\s+require\s+(?:further|additional)\s+(?:inquiry|investigation|due\s+diligence)',
            r'(?:may|might|could)\s+be\s+(?:proprietary|confidential|sensitive)',
            r'beyond\s+the\s+scope\s+of\s+(?:this|these)\s+(?:materials?|documents?)'
        ]
        
        evasive_matches = []
        for pattern in evasive_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            evasive_matches.extend([match.group(0) for match in matches])
        
        if evasive_matches:
            # Check if evasive language is followed by due diligence guidance
            has_guidance = bool(re.search(
                r'(?:recommend|suggest|advise).*(?:due\s+diligence|follow.*up|contact)',
                text, re.IGNORECASE
            ))
            
            severity = GapSeverity.MEDIUM if has_guidance else GapSeverity.HIGH
            
            gap = Gap(
                gap_type=GapType.EVASIVE_RESPONSE,
                severity=severity,
                category=GapCategory.CONTENT_QUALITY,
                description=f"Found {len(evasive_matches)} evasive phrases",
                location="Multiple locations",
                evidence=evasive_matches[:5],
                recommendation="Replace evasive language with specific guidance or source-backed alternatives",
                confidence=0.9
            )
            gaps.append(gap)
        
        return gaps
    
    def _detect_compliance_risks(self, context: DetectionContext) -> List[Gap]:
        """Detect potential compliance and regulatory risks."""
        gaps = []
        text = context.response_text
        
        # High-risk compliance patterns
        high_risk_patterns = [
            r'(?:guarantees?|assures?|promises?)\s+(?:returns?|performance|results?)',
            r'(?:will\s+(?:achieve|deliver|generate))\s+(?:\d+%?|returns?)',
            r'(?:outperform|beat|exceed)\s+(?:market|benchmark|index)',
            r'(?:risk-free|no\s+risk|guaranteed)\s+(?:investment|strategy|approach)',
            r'(?:always|never|consistently)\s+(?:profitable|successful|positive)'
        ]
        
        medium_risk_patterns = [
            r'(?:expects?|anticipates?|projects?)\s+(?:\d+%?|returns?|growth)',
            r'(?:likely|probably)\s+(?:to\s+)?(?:achieve|deliver|generate)',
            r'historical\s+(?:performance|returns?)\s+(?:indicate|suggest)',
            r'(?:model|strategy)\s+(?:shows?|demonstrates?)\s+(?:ability|capability)'
        ]
        
        high_risk_matches = []
        medium_risk_matches = []
        
        for pattern in high_risk_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            high_risk_matches.extend([match.group(0) for match in matches])
        
        for pattern in medium_risk_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            medium_risk_matches.extend([match.group(0) for match in matches])
        
        if high_risk_matches:
            gap = Gap(
                gap_type=GapType.REGULATORY_EXPOSURE,
                severity=GapSeverity.CRITICAL,
                category=GapCategory.COMPLIANCE_LEGAL,
                description="High-risk compliance language detected",
                location="Multiple locations",
                evidence=high_risk_matches[:3],
                recommendation="Remove or modify language that implies guarantees or assured outcomes",
                confidence=0.95
            )
            gaps.append(gap)
        
        if medium_risk_matches:
            gap = Gap(
                gap_type=GapType.FIDUCIARY_RISK,
                severity=GapSeverity.HIGH,
                category=GapCategory.COMPLIANCE_LEGAL,
                description="Medium-risk compliance language detected",
                location="Multiple locations",
                evidence=medium_risk_matches[:3],
                recommendation="Add appropriate disclaimers and qualify forward-looking statements",
                confidence=0.85
            )
            gaps.append(gap)
        
        return gaps
    
    def _detect_depth_inconsistencies(self, context: DetectionContext) -> List[Gap]:
        """Detect inconsistent depth and structural coverage issues."""
        gaps = []
        text = context.response_text
        
        # Analyze question components vs response coverage
        question_parts = self._extract_question_parts(context.question_text)
        coverage_analysis = self._analyze_coverage(text, question_parts)
        
        uncovered_parts = [part for part, covered in coverage_analysis.items() if not covered]
        
        if uncovered_parts:
            gap = Gap(
                gap_type=GapType.INCOMPLETE_COVERAGE,
                severity=GapSeverity.HIGH,
                category=GapCategory.STRUCTURAL_DEPTH,
                description=f"Incomplete coverage of {len(uncovered_parts)} question components",
                location="Structural",
                evidence=uncovered_parts,
                recommendation="Ensure all question sub-parts are systematically addressed",
                confidence=0.9
            )
            gaps.append(gap)
        
        return gaps
    
    def _detect_missing_disclaimers(self, context: DetectionContext) -> List[Gap]:
        """Detect responses that should have disclaimers but don't."""
        gaps = []
        text = context.response_text
        
        # Situations requiring disclaimers
        disclaimer_triggers = [
            r'(?:forecast|predict|project|expect|anticipate)',
            r'(?:model|algorithm|system)\s+(?:will|can|able)',
            r'(?:historical|past)\s+(?:performance|results?)',
            r'(?:risk|volatility)\s+(?:management|control)',
            r'(?:capabilities?|able\s+to)\s+(?:handle|manage|process)'
        ]
        
        disclaimer_present = bool(re.search(
            r'(?:disclaimer|past\s+performance|no\s+guarantee|subject\s+to\s+risk)',
            text, re.IGNORECASE
        ))
        
        trigger_matches = []
        if not disclaimer_present:
            for pattern in disclaimer_triggers:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                trigger_matches.extend([match.group(0) for match in matches])
        
        if trigger_matches and not disclaimer_present:
            gap = Gap(
                gap_type=GapType.MISSING_DISCLAIMERS,
                severity=GapSeverity.HIGH,
                category=GapCategory.COMPLIANCE_LEGAL,
                description=f"Missing disclaimers for {len(trigger_matches)} risk-related statements",
                location="End of response",
                evidence=trigger_matches[:3],
                recommendation="Add appropriate risk disclaimers and past performance warnings",
                confidence=0.8
            )
            gaps.append(gap)
        
        return gaps
    
    def _extract_question_parts(self, question: str) -> List[str]:
        """Extract distinct parts/sub-questions from a DDQ question."""
        # Simple heuristic: split on common separators and question markers
        separators = [r'\?', r':', r';', r'\n', r'\d+\)', r'[a-z]\)']
        
        parts = [question]
        for sep in separators:
            new_parts = []
            for part in parts:
                new_parts.extend(re.split(sep, part))
            parts = [p.strip() for p in new_parts if p.strip()]
        
        return parts
    
    def _analyze_coverage(self, response: str, question_parts: List[str]) -> Dict[str, bool]:
        """Analyze which question parts are covered in the response."""
        coverage = {}
        
        for part in question_parts:
            # Extract key terms from question part
            key_terms = self._extract_key_terms(part)
            
            # Check if terms are addressed in response
            covered = False
            if key_terms:
                # At least 50% of key terms should be mentioned
                mentioned_terms = sum(1 for term in key_terms 
                                    if re.search(re.escape(term), response, re.IGNORECASE))
                covered = (mentioned_terms / len(key_terms)) >= 0.5
            
            coverage[part] = covered
        
        return coverage
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text for coverage analysis."""
        # Remove common words and extract meaningful terms
        stop_words = {'the', 'is', 'at', 'which', 'on', 'and', 'a', 'to', 'are', 'as', 'an', 'or', 'be'}
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        key_terms = [word for word in words if word not in stop_words]
        
        # Return most frequent terms (up to 5)
        term_counts = Counter(key_terms)
        return [term for term, count in term_counts.most_common(5)]
    
    def _generate_report(self, context: DetectionContext, gaps: List[Gap]) -> GapReport:
        """Generate comprehensive gap analysis report."""
        total_gaps = len(gaps)
        critical_gaps = sum(1 for gap in gaps if gap.severity == GapSeverity.CRITICAL)
        high_priority_gaps = sum(1 for gap in gaps if gap.severity.value >= GapSeverity.HIGH.value)
        
        # Calculate overall score (0-100, higher is better)
        base_score = 100
        score_deductions = sum(self._get_score_deduction(gap) for gap in gaps)
        overall_score = max(0, base_score - score_deductions)
        
        # Determine compliance risk level
        compliance_risk = self._assess_compliance_risk(critical_gaps, high_priority_gaps, len(gaps))
        
        # Generate recommendations
        recommendations = self._generate_recommendations(gaps)
        
        return GapReport(
            response_id=context.response_id,
            question_id=context.question_id,
            total_gaps=total_gaps,
            critical_gaps=critical_gaps,
            high_priority_gaps=high_priority_gaps,
            gaps=gaps,
            overall_score=overall_score,
            compliance_risk=compliance_risk,
            recommendations=recommendations
        )
    
    def _get_score_deduction(self, gap: Gap) -> int:
        """Calculate score deduction for a gap."""
        deductions = {
            GapSeverity.CRITICAL: 25,
            GapSeverity.HIGH: 15,
            GapSeverity.MEDIUM: 8,
            GapSeverity.LOW: 3
        }
        return int(deductions[gap.severity] * gap.confidence)
    
    def _assess_compliance_risk(self, critical: int, high: int, total: int) -> str:
        """Assess overall compliance risk level."""
        for risk_level, thresholds in self.compliance_thresholds.items():
            if critical >= thresholds.get('critical', 0) and high >= thresholds.get('high', 0):
                return risk_level
            if 'medium' in thresholds and total >= thresholds['medium']:
                return risk_level
            if 'low' in thresholds and total >= thresholds['low']:
                return risk_level
        
        return 'LOW'
    
    def _generate_recommendations(self, gaps: List[Gap]) -> List[str]:
        """Generate prioritized recommendations based on identified gaps."""
        recommendations = []
        
        # Group by category and prioritize
        by_category = defaultdict(list)
        for gap in gaps:
            by_category[gap.category].append(gap)
        
        # Prioritize compliance issues
        if GapCategory.COMPLIANCE_LEGAL in by_category:
            recommendations.append(
                "PRIORITY 1: Address all compliance and legal risks immediately"
            )
        
        # Factual accuracy
        if GapCategory.FACTUAL_ACCURACY in by_category:
            recommendations.append(
                "PRIORITY 2: Verify all factual claims against source documents"
            )
        
        # Content quality
        if GapCategory.CONTENT_QUALITY in by_category:
            recommendations.append(
                "PRIORITY 3: Reduce interpretive content and improve directness"
            )
        
        # Structural improvements
        if GapCategory.STRUCTURAL_DEPTH in by_category:
            recommendations.append(
                "PRIORITY 4: Ensure consistent depth and comprehensive coverage"
            )
        
        return recommendations
    
    def _get_gap_description(self, gap_type: GapType, match_count: int) -> str:
        """Get human-readable description for gap type."""
        descriptions = {
            GapType.EXCESSIVE_INTERPRETATION: f"Excessive interpretive content detected ({match_count} instances)",
            GapType.FACTUAL_INCONSISTENCY: f"Potential factual inconsistencies identified ({match_count} instances)",
            GapType.EVASIVE_RESPONSE: f"Evasive or incomplete response patterns ({match_count} instances)",
            GapType.MISSING_DISCLAIMERS: f"Missing required disclaimers ({match_count} trigger points)",
            GapType.REGULATORY_EXPOSURE: f"High regulatory risk language detected ({match_count} instances)",
            GapType.INCOMPLETE_COVERAGE: f"Incomplete question coverage identified ({match_count} gaps)"
        }
        return descriptions.get(gap_type, f"Gap detected: {gap_type.name}")
    
    def _get_gap_recommendation(self, gap_type: GapType) -> str:
        """Get specific recommendation for gap type."""
        recommendations = {
            GapType.EXCESSIVE_INTERPRETATION: "Replace interpretive language with direct source citations",
            GapType.FACTUAL_INCONSISTENCY: "Verify all claims against source documents",
            GapType.EVASIVE_RESPONSE: "Provide direct answers or specific due diligence guidance",
            GapType.MISSING_DISCLAIMERS: "Add appropriate risk disclaimers and qualifications",
            GapType.REGULATORY_EXPOSURE: "Remove language implying guarantees or assured outcomes",
            GapType.INCOMPLETE_COVERAGE: "Systematically address all question components"
        }
        return recommendations.get(gap_type, "Review and address identified gap")