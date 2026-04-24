"""
Depth Analyzer Engine
====================

Core engine for analyzing response depth, consistency, and coverage quality
in DDQ responses to ensure comprehensive and standardized answers.
"""

import re
import json
from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass
from collections import Counter, defaultdict
from statistics import mean, stdev

from .depth_types import (
    DepthMetric, DepthLevel, CoverageGap, CoverageType, DepthAnalysisReport,
    STANDARD_DEPTH_METRICS, COMPONENT_PATTERNS, COVERAGE_TEMPLATES,
    DEPTH_SCORING_WEIGHTS
)


@dataclass
class DepthAnalysisContext:
    """Context for depth analysis."""
    
    response_text: str
    question_text: str
    response_id: str
    question_type: Optional[str] = None  # strategy, operational, risk, performance
    expected_depth: Optional[DepthLevel] = None
    source_documents: Optional[List[str]] = None


class DepthAnalyzer:
    """
    Advanced depth analysis system for DDQ responses.
    
    Features:
    - Multi-dimensional depth measurement
    - Component coverage analysis
    - Consistency scoring across responses
    - Standardization validation
    - Automated depth improvement suggestions
    """
    
    def __init__(self, custom_metrics: Optional[Dict[str, Any]] = None):
        """Initialize depth analyzer with metrics and templates."""
        
        self.depth_metrics = STANDARD_DEPTH_METRICS.copy()
        if custom_metrics:
            self.depth_metrics.update(custom_metrics)
        
        self.component_patterns = COMPONENT_PATTERNS.copy()
        self.coverage_templates = COVERAGE_TEMPLATES.copy()
        self.scoring_weights = DEPTH_SCORING_WEIGHTS.copy()
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
        
        # Analysis cache for consistency comparison
        self.analysis_cache = {}
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        for component_type, patterns in self.component_patterns.items():
            self.component_patterns[component_type] = [
                re.compile(pattern, re.IGNORECASE) 
                for pattern in patterns
            ]
    
    def analyze_depth(self, context: DepthAnalysisContext) -> DepthAnalysisReport:
        """
        Main depth analysis method.
        
        Args:
            context: Analysis context with response and question details
            
        Returns:
            Comprehensive depth analysis report
        """
        
        # Calculate individual depth metrics
        depth_metrics = self._calculate_depth_metrics(context)
        
        # Analyze component coverage
        coverage_gaps = self._analyze_component_coverage(context)
        
        # Detect standardization issues
        standardization_issues = self._detect_standardization_issues(context)
        
        # Calculate overall scores
        overall_depth_score = self._calculate_overall_depth_score(depth_metrics)
        consistency_score = self._calculate_consistency_score(context)
        depth_level = self._determine_depth_level(overall_depth_score, depth_metrics)
        
        # Generate recommendations
        recommendations = self._generate_depth_recommendations(
            depth_metrics, coverage_gaps, standardization_issues
        )
        
        # Create comprehensive report
        report = DepthAnalysisReport(
            response_id=context.response_id,
            overall_depth_score=overall_depth_score,
            depth_level=depth_level,
            depth_metrics=depth_metrics,
            coverage_gaps=coverage_gaps,
            standardization_issues=standardization_issues,
            consistency_score=consistency_score,
            recommendations=recommendations
        )
        
        # Cache for consistency analysis
        self.analysis_cache[context.response_id] = report
        
        return report
    
    def _calculate_depth_metrics(self, context: DepthAnalysisContext) -> List[DepthMetric]:
        """Calculate all depth metrics for the response."""
        
        metrics = []
        text = context.response_text
        
        # Word count metric
        word_count = len(text.split())
        word_count_metric = DepthMetric(
            metric_name="word_count",
            value=word_count,
            max_value=self.depth_metrics['word_count']['max_threshold'],
            description=self.depth_metrics['word_count']['description'],
            weight=self.depth_metrics['word_count']['weight']
        )
        metrics.append(word_count_metric)
        
        # Specificity score
        specificity_score = self._calculate_specificity_score(text)
        specificity_metric = DepthMetric(
            metric_name="specificity_score",
            value=specificity_score,
            max_value=1.0,
            description=self.depth_metrics['specificity_score']['description'],
            weight=self.depth_metrics['specificity_score']['weight']
        )
        metrics.append(specificity_metric)
        
        # Source citation density
        citation_density = self._calculate_citation_density(text)
        citation_metric = DepthMetric(
            metric_name="source_citation_density", 
            value=citation_density,
            max_value=self.depth_metrics['source_citation_density']['target_density'] * 2,
            description=self.depth_metrics['source_citation_density']['description'],
            weight=self.depth_metrics['source_citation_density']['weight']
        )
        metrics.append(citation_metric)
        
        # Component coverage
        coverage_percentage = self._calculate_component_coverage(context)
        coverage_metric = DepthMetric(
            metric_name="component_coverage",
            value=coverage_percentage,
            max_value=100.0,
            description=self.depth_metrics['component_coverage']['description'],
            weight=self.depth_metrics['component_coverage']['weight']
        )
        metrics.append(coverage_metric)
        
        # Factual density
        factual_density = self._calculate_factual_density(text)
        factual_metric = DepthMetric(
            metric_name="factual_density",
            value=factual_density,
            max_value=1.0,
            description=self.depth_metrics['factual_density']['description'],
            weight=self.depth_metrics['factual_density']['weight']
        )
        metrics.append(factual_metric)
        
        # Analytical depth
        analytical_depth = self._calculate_analytical_depth(text)
        analytical_metric = DepthMetric(
            metric_name="analytical_depth",
            value=analytical_depth,
            max_value=1.0,
            description=self.depth_metrics['analytical_depth']['description'],
            weight=self.depth_metrics['analytical_depth']['weight']
        )
        metrics.append(analytical_metric)
        
        return metrics
    
    def _calculate_specificity_score(self, text: str) -> float:
        """Calculate how specific vs general the content is."""
        
        # Specific indicators (names, numbers, processes, tools)
        specific_patterns = [
            r'\b[A-Z][a-zA-Z]+\s+(?:system|platform|model|algorithm|tool)\b',  # Proper nouns + tech terms
            r'\d+\.?\d*%',  # Percentages
            r'\$[\d,]+(?:\.\d{2})?',  # Dollar amounts
            r'\b(?:daily|weekly|monthly|quarterly|annually)\b',  # Time specifics
            r'\b(?:bloomberg|reuters|refinitiv|factset)\b',  # Specific vendors
            r'(?:section|page|paragraph|line)\s+\d+',  # Document references
            r'\b(?:model|algorithm|system|process)\s+[A-Z]\w+',  # Named systems
        ]
        
        # General/vague indicators
        general_patterns = [
            r'\b(?:various|multiple|several|numerous|different)\b',
            r'\b(?:generally|typically|usually|normally|often)\b',
            r'\b(?:comprehensive|sophisticated|advanced|robust)\b',
            r'\b(?:approach|strategy|method|process)\b(?!\s+[A-Z])',  # Generic without names
            r'\b(?:may|might|could|would|should)\b',
        ]
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        specific_count = sum(len(re.findall(pattern, text, re.IGNORECASE)) 
                           for pattern in specific_patterns)
        general_count = sum(len(re.findall(pattern, text, re.IGNORECASE))
                          for pattern in general_patterns)
        
        if specific_count + general_count == 0:
            return 0.5  # Neutral if no indicators found
        
        return specific_count / (specific_count + general_count)
    
    def _calculate_citation_density(self, text: str) -> float:
        """Calculate source citation density per 100 words."""
        
        citation_patterns = [
            r'(?:as\s+stated|per|according\s+to|from)\s+[^,\n]{5,}',
            r'(?:source|document|file|material).*(?:states?|shows?|indicates?)',
            r'["\'][^"\']{10,}["\']',  # Direct quotes
            r'(?:section|page|paragraph)\s+\d+',
            r'(?:exhibit|appendix|schedule)\s+[A-Z0-9]',
        ]
        
        word_count = len(text.split())
        if word_count == 0:
            return 0.0
        
        citation_count = sum(len(re.findall(pattern, text, re.IGNORECASE))
                           for pattern in citation_patterns)
        
        return (citation_count / word_count) * 100
    
    def _calculate_component_coverage(self, context: DepthAnalysisContext) -> float:
        """Calculate percentage of question components addressed."""
        
        # Extract question components
        question_components = self._extract_question_components(context.question_text)
        
        if not question_components:
            return 100.0  # If can't parse components, assume covered
        
        # Check coverage in response
        covered_components = 0
        response_lower = context.response_text.lower()
        
        for component in question_components:
            component_terms = self._extract_key_terms(component)
            
            # Check if majority of component terms are mentioned
            mentioned_terms = sum(1 for term in component_terms 
                                if term.lower() in response_lower)
            
            if mentioned_terms >= len(component_terms) * 0.6:  # 60% threshold
                covered_components += 1
        
        return (covered_components / len(question_components)) * 100
    
    def _calculate_factual_density(self, text: str) -> float:
        """Calculate ratio of factual statements to total statements."""
        
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        factual_count = 0
        
        for sentence in sentences:
            # Factual indicators
            has_numbers = bool(re.search(r'\d', sentence))
            has_specific_nouns = bool(re.search(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?\b', sentence))
            has_citations = bool(re.search(r'(?:source|document|stated|per)', sentence, re.IGNORECASE))
            has_concrete_terms = bool(re.search(
                r'\b(?:system|model|process|algorithm|platform|tool|method)\b', 
                sentence, re.IGNORECASE
            ))
            
            # Opinion/interpretive indicators (reduce factual score)
            has_opinion = bool(re.search(
                r'\b(?:believe|think|feel|seems?|appears?|likely|probably)\b',
                sentence, re.IGNORECASE
            ))
            has_vague = bool(re.search(
                r'\b(?:various|multiple|several|generally|typically)\b',
                sentence, re.IGNORECASE
            ))
            
            # Score sentence
            factual_score = sum([has_numbers, has_specific_nouns, has_citations, has_concrete_terms])
            opinion_penalty = sum([has_opinion, has_vague]) * 0.5
            
            if factual_score - opinion_penalty >= 1.5:  # Threshold for factual
                factual_count += 1
        
        return factual_count / len(sentences)
    
    def _calculate_analytical_depth(self, text: str) -> float:
        """Calculate presence of analysis, reasoning, and context."""
        
        # Analytical indicators
        analytical_patterns = [
            r'\b(?:because|since|due\s+to|as\s+a\s+result|therefore|thus|hence)\b',
            r'\b(?:enables?|allows?|facilitates?|supports?|enhances?)\b',
            r'\b(?:implications?|impact|effect|consequences?|outcomes?)\b',
            r'\b(?:rationale|reason|purpose|objective|goal)\b',
            r'\b(?:compares?|contrast|versus|relative\s+to|compared\s+to)\b',
            r'\b(?:advantage|benefit|strength|weakness|limitation)\b',
        ]
        
        # Context indicators  
        context_patterns = [
            r'\b(?:market|industry|economic|regulatory|competitive)\s+(?:environment|context|conditions?)\b',
            r'\b(?:background|history|evolution|development)\b',
            r'\b(?:relationship|correlation|connection|linkage)\b',
            r'\b(?:framework|structure|architecture|design)\b',
        ]
        
        word_count = len(text.split())
        if word_count == 0:
            return 0.0
        
        analytical_count = sum(len(re.findall(pattern, text, re.IGNORECASE))
                             for pattern in analytical_patterns)
        context_count = sum(len(re.findall(pattern, text, re.IGNORECASE))
                          for pattern in context_patterns)
        
        # Normalize by word count and combine scores
        analytical_density = (analytical_count / word_count) * 100  # Per 100 words
        context_density = (context_count / word_count) * 100
        
        # Scale to 0-1 range
        combined_score = min(1.0, (analytical_density + context_density) / 10)  # Target: 10 per 100 words
        
        return combined_score
    
    def _analyze_component_coverage(self, context: DepthAnalysisContext) -> List[CoverageGap]:
        """Analyze coverage gaps for question components."""
        
        gaps = []
        
        # Determine question type and expected components
        question_type = self._classify_question_type(context.question_text)
        expected_components = self._get_expected_components(question_type)
        
        # Analyze each component
        for component in expected_components:
            coverage_analysis = self._analyze_component_coverage_detail(
                context.response_text, component, question_type
            )
            
            if coverage_analysis['has_gap']:
                gap = CoverageGap(
                    gap_type=coverage_analysis['gap_type'],
                    component=component,
                    severity=coverage_analysis['severity'],
                    description=coverage_analysis['description'],
                    expected_content=coverage_analysis['expected_content'],
                    actual_coverage=coverage_analysis['actual_coverage'],
                    recommendation=coverage_analysis['recommendation'],
                    confidence=coverage_analysis['confidence']
                )
                gaps.append(gap)
        
        return gaps
    
    def _classify_question_type(self, question: str) -> str:
        """Classify the type of DDQ question."""
        
        question_lower = question.lower()
        
        # Strategy question indicators
        if any(term in question_lower for term in ['strategy', 'approach', 'methodology', 'philosophy']):
            return 'strategy_question'
        
        # Risk question indicators
        if any(term in question_lower for term in ['risk', 'control', 'mitigation', 'hedge', 'exposure']):
            return 'risk_question'
        
        # Performance question indicators
        if any(term in question_lower for term in ['performance', 'return', 'track record', 'results']):
            return 'performance_question'
        
        # Operational question indicators  
        if any(term in question_lower for term in ['process', 'procedure', 'operation', 'implementation']):
            return 'operational_question'
        
        return 'general_question'
    
    def _get_expected_components(self, question_type: str) -> List[str]:
        """Get expected components for question type."""
        
        if question_type in self.coverage_templates:
            return self.coverage_templates[question_type]['required_components']
        
        # Default components for general questions
        return ['overview', 'details', 'context']
    
    def _analyze_component_coverage_detail(self, response: str, component: str, question_type: str) -> Dict[str, Any]:
        """Analyze coverage detail for a specific component."""
        
        # Component-specific patterns
        component_patterns = {
            'overview': [r'overview|summary|introduction|general\s+approach'],
            'methodology': [r'method(?:ology)?|approach|technique|framework'],
            'implementation': [r'implement(?:ation)?|execut(?:e|ion)|deploy|apply'],
            'rationale': [r'rationale|reason|purpose|why|objective|goal'],
            'process': [r'process|procedure|workflow|step|stage|phase'],
            'tools': [r'tool|system|platform|software|technology|vendor'],
            'frequency': [r'frequency|timing|schedule|when|how\s+often'],
            'oversight': [r'oversight|supervision|monitoring|governance|review'],
            'identification': [r'identif(?:y|ication)|detect|recognize|assess'],
            'measurement': [r'measur(?:e|ement)|quantif(?:y|ication)|metric|gauge'],
            'management': [r'manag(?:e|ement)|control|mitigate|handle|address'],
            'monitoring': [r'monitor|track|watch|observe|surveil'],
            'metrics': [r'metric|measure|kpi|indicator|benchmark|statistic'],
            'attribution': [r'attribution|source|driver|factor|contributor'],
            'benchmarks': [r'benchmark|comparison|relative|versus|peer'],
            'disclaimers': [r'disclaimer|risk|warning|past\s+performance|guarantee']
        }
        
        patterns = component_patterns.get(component, [component])
        
        # Search for component mentions
        mentions = []
        for pattern in patterns:
            matches = list(re.finditer(pattern, response, re.IGNORECASE))
            mentions.extend(matches)
        
        # Analyze coverage quality
        if not mentions:
            return {
                'has_gap': True,
                'gap_type': CoverageType.MISSING_COMPONENT,
                'severity': 'HIGH',
                'description': f"Component '{component}' not addressed in response",
                'expected_content': f"Should include discussion of {component}",
                'actual_coverage': "No coverage found",
                'recommendation': f"Add section addressing {component}",
                'confidence': 0.9
            }
        
        # Check depth of coverage
        coverage_context = self._extract_coverage_context(response, mentions)
        coverage_depth = self._assess_coverage_depth(coverage_context, component)
        
        if coverage_depth < 0.5:  # Insufficient depth
            return {
                'has_gap': True,
                'gap_type': CoverageType.INSUFFICIENT_DETAIL,
                'severity': 'MEDIUM',
                'description': f"Component '{component}' mentioned but lacks sufficient detail",
                'expected_content': f"Should provide comprehensive coverage of {component}",
                'actual_coverage': f"Superficial mention: {coverage_context[:100]}...",
                'recommendation': f"Expand coverage of {component} with specific details",
                'confidence': 0.8
            }
        
        # Coverage is adequate
        return {'has_gap': False}
    
    def _extract_coverage_context(self, response: str, mentions: List[re.Match]) -> str:
        """Extract context around component mentions."""
        
        if not mentions:
            return ""
        
        # Combine context around all mentions
        contexts = []
        for match in mentions:
            start = max(0, match.start() - 100)
            end = min(len(response), match.end() + 100)
            context = response[start:end]
            contexts.append(context)
        
        return " ... ".join(contexts)
    
    def _assess_coverage_depth(self, context: str, component: str) -> float:
        """Assess the depth of coverage for a component."""
        
        if not context:
            return 0.0
        
        # Depth indicators
        depth_indicators = [
            'specific', 'detail', 'comprehensive', 'thorough',
            'process', 'method', 'approach', 'system',
            'example', 'instance', 'case', 'scenario'
        ]
        
        # Count depth indicators
        depth_score = sum(1 for indicator in depth_indicators 
                         if indicator in context.lower())
        
        # Normalize by context length (words)
        word_count = len(context.split())
        if word_count == 0:
            return 0.0
        
        return min(1.0, depth_score / (word_count / 50))  # Target: 1 depth indicator per 50 words
    
    def _detect_standardization_issues(self, context: DepthAnalysisContext) -> List[Dict[str, Any]]:
        """Detect standardization and consistency issues."""
        
        issues = []
        text = context.response_text
        
        # Format consistency issues
        header_formats = re.findall(r'(?:^|\n)((?:\*\*[^*]+\*\*|#+\s+[^\n]+|[A-Z][^:\n]*:))', text, re.MULTILINE)
        if len(set(header_formats)) > 1:  # Multiple header formats
            issues.append({
                'type': 'format_inconsistency',
                'description': 'Inconsistent header formatting detected',
                'details': f"Found {len(set(header_formats))} different header formats",
                'severity': 'MEDIUM',
                'auto_fixable': True
            })
        
        # Citation consistency
        citation_formats = re.findall(
            r'(?:as\s+stated\s+in|per|according\s+to|source:|from)\s+[^,\n.]{5,}',
            text, re.IGNORECASE
        )
        if len(citation_formats) > 1:
            # Analyze citation format consistency
            format_variations = self._analyze_citation_formats(citation_formats)
            if format_variations > 2:
                issues.append({
                    'type': 'citation_inconsistency',
                    'description': 'Inconsistent citation formatting',
                    'details': f"Found {format_variations} different citation styles",
                    'severity': 'LOW',
                    'auto_fixable': False
                })
        
        # Tone consistency
        informal_terms = re.findall(
            r'\b(?:we\s+believe|i\s+think|personally|obviously|clearly|simply)\b',
            text, re.IGNORECASE
        )
        if informal_terms:
            issues.append({
                'type': 'tone_inconsistency',
                'description': 'Informal language detected',
                'details': f"Found informal terms: {', '.join(informal_terms[:3])}",
                'severity': 'HIGH',
                'auto_fixable': True
            })
        
        # Structure consistency
        sections = self._detect_sections(text)
        if len(sections) > 1:
            structure_consistency = self._analyze_section_structure(sections)
            if structure_consistency < 0.7:
                issues.append({
                    'type': 'structure_variation',
                    'description': 'Inconsistent section structure',
                    'details': f"Structure consistency score: {structure_consistency:.2f}",
                    'severity': 'MEDIUM',
                    'auto_fixable': False
                })
        
        return issues
    
    def _analyze_citation_formats(self, citations: List[str]) -> int:
        """Analyze consistency of citation formats."""
        
        format_patterns = []
        
        for citation in citations:
            # Categorize citation format
            if 'source:' in citation.lower():
                format_patterns.append('source_colon')
            elif 'as stated in' in citation.lower():
                format_patterns.append('as_stated_in')
            elif 'per ' in citation.lower():
                format_patterns.append('per_format')
            elif 'according to' in citation.lower():
                format_patterns.append('according_to')
            else:
                format_patterns.append('other')
        
        return len(set(format_patterns))
    
    def _detect_sections(self, text: str) -> List[Dict[str, Any]]:
        """Detect sections in the response."""
        
        sections = []
        
        # Header patterns
        header_patterns = [
            (r'(?:^|\n)(#+\s+)([^\n]+)', 'markdown_header'),
            (r'(?:^|\n)(\*\*)([^*]+)(\*\*)', 'bold_header'),
            (r'(?:^|\n)([A-Z][^:\n]*)(:\s*)', 'colon_header'),
        ]
        
        for pattern, header_type in header_patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE))
            for match in matches:
                sections.append({
                    'start': match.start(),
                    'end': match.end(),
                    'title': match.group(2) if len(match.groups()) >= 2 else match.group(0),
                    'type': header_type,
                    'level': len(match.group(1)) if header_type == 'markdown_header' else 1
                })
        
        return sorted(sections, key=lambda x: x['start'])
    
    def _analyze_section_structure(self, sections: List[Dict[str, Any]]) -> float:
        """Analyze consistency of section structure."""
        
        if len(sections) < 2:
            return 1.0
        
        # Check header type consistency
        header_types = [section['type'] for section in sections]
        type_consistency = len(set(header_types)) == 1
        
        # Check level consistency for markdown headers
        markdown_sections = [s for s in sections if s['type'] == 'markdown_header']
        level_consistency = True
        
        if len(markdown_sections) > 1:
            levels = [s['level'] for s in markdown_sections]
            level_consistency = len(set(levels)) <= 2  # Allow at most 2 header levels
        
        # Calculate overall consistency score
        consistency_factors = [type_consistency, level_consistency]
        return sum(consistency_factors) / len(consistency_factors)
    
    def _calculate_overall_depth_score(self, depth_metrics: List[DepthMetric]) -> float:
        """Calculate weighted overall depth score."""
        
        if not depth_metrics:
            return 0.0
        
        weighted_scores = []
        total_weight = 0
        
        for metric in depth_metrics:
            normalized_score = metric.normalized_score
            weight = metric.weight
            weighted_scores.append(normalized_score * weight)
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return (sum(weighted_scores) / total_weight) * 100
    
    def _calculate_consistency_score(self, context: DepthAnalysisContext) -> float:
        """Calculate consistency score compared to other responses."""
        
        if len(self.analysis_cache) < 2:
            return 100.0  # Perfect score if no comparison data
        
        # Compare with similar responses in cache
        current_metrics = self._calculate_depth_metrics(context)
        
        consistency_scores = []
        
        for cached_id, cached_report in self.analysis_cache.items():
            if cached_id != context.response_id:
                # Compare metric distributions
                metric_consistency = self._compare_metric_distributions(
                    current_metrics, cached_report.depth_metrics
                )
                consistency_scores.append(metric_consistency)
        
        if not consistency_scores:
            return 100.0
        
        return mean(consistency_scores) * 100
    
    def _compare_metric_distributions(
        self, 
        metrics1: List[DepthMetric], 
        metrics2: List[DepthMetric]
    ) -> float:
        """Compare two sets of depth metrics for consistency."""
        
        # Create metric dictionaries for easier comparison
        metrics1_dict = {m.metric_name: m.normalized_score for m in metrics1}
        metrics2_dict = {m.metric_name: m.normalized_score for m in metrics2}
        
        # Compare common metrics
        common_metrics = set(metrics1_dict.keys()) & set(metrics2_dict.keys())
        
        if not common_metrics:
            return 0.5  # Neutral if no common metrics
        
        differences = []
        for metric_name in common_metrics:
            score1 = metrics1_dict[metric_name]
            score2 = metrics2_dict[metric_name]
            difference = abs(score1 - score2)
            differences.append(difference)
        
        # Consistency is inverse of average difference
        avg_difference = mean(differences)
        consistency = max(0.0, 1.0 - avg_difference)
        
        return consistency
    
    def _determine_depth_level(self, overall_score: float, metrics: List[DepthMetric]) -> DepthLevel:
        """Determine the depth level based on overall score and specific metrics."""
        
        # Score thresholds for depth levels
        if overall_score >= 90:
            return DepthLevel.EXPERT
        elif overall_score >= 75:
            return DepthLevel.COMPREHENSIVE
        elif overall_score >= 60:
            return DepthLevel.ANALYTICAL
        elif overall_score >= 40:
            return DepthLevel.DESCRIPTIVE
        else:
            return DepthLevel.SURFACE
    
    def _generate_depth_recommendations(
        self,
        metrics: List[DepthMetric],
        gaps: List[CoverageGap],
        standardization_issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate prioritized recommendations for depth improvement."""
        
        recommendations = []
        
        # Metric-based recommendations
        for metric in metrics:
            if metric.normalized_score < 0.6:  # Below 60% threshold
                recommendations.append(
                    f"Improve {metric.metric_name}: Currently {metric.percentage:.1f}%, "
                    f"target 60%+ - {metric.description}"
                )
        
        # Coverage gap recommendations
        high_priority_gaps = [gap for gap in gaps if gap.severity in ['HIGH', 'CRITICAL']]
        if high_priority_gaps:
            recommendations.append(
                f"Address {len(high_priority_gaps)} high-priority coverage gaps: "
                f"{', '.join([gap.component for gap in high_priority_gaps[:3]])}"
            )
        
        # Standardization recommendations
        critical_issues = [issue for issue in standardization_issues if issue['severity'] == 'HIGH']
        if critical_issues:
            recommendations.append(
                f"Fix {len(critical_issues)} critical standardization issues: "
                f"{', '.join([issue['type'] for issue in critical_issues[:3]])}"
            )
        
        # General improvement suggestions
        low_metrics = [m for m in metrics if m.normalized_score < 0.5]
        if len(low_metrics) > 2:
            recommendations.append(
                "Overall depth improvement needed: Focus on specificity, source citations, and analytical content"
            )
        
        return recommendations
    
    def _extract_question_components(self, question: str) -> List[str]:
        """Extract distinct components from a DDQ question."""
        
        # Split on common separators
        separators = [r'\?', r':', r';', r'\n', r'\d+\)', r'[a-z]\)', r'\band\b', r'\bor\b']
        
        components = [question]
        for separator in separators:
            new_components = []
            for component in components:
                parts = re.split(separator, component, flags=re.IGNORECASE)
                new_components.extend([p.strip() for p in parts if p.strip()])
            components = new_components
        
        # Filter out very short components
        return [comp for comp in components if len(comp) > 10]
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text for analysis."""
        
        # Remove common stop words
        stop_words = {
            'the', 'is', 'at', 'which', 'on', 'and', 'a', 'to', 'are', 'as', 'an', 'or', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'can', 'shall', 'this', 'that', 'these', 'those'
        }
        
        # Extract meaningful terms (3+ characters, not stop words)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        key_terms = [word for word in words if word not in stop_words]
        
        # Return most significant terms (by frequency)
        term_counts = Counter(key_terms)
        return [term for term, count in term_counts.most_common(10)]
    
    def get_depth_statistics(self, reports: List[DepthAnalysisReport]) -> Dict[str, Any]:
        """Generate depth analysis statistics across multiple reports."""
        
        if not reports:
            return {}
        
        # Overall depth scores
        depth_scores = [report.overall_depth_score for report in reports]
        
        # Consistency scores
        consistency_scores = [report.consistency_score for report in reports]
        
        # Gap counts by severity
        gap_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'CRITICAL': 0}
        for report in reports:
            for gap in report.coverage_gaps:
                gap_counts[gap.severity] = gap_counts.get(gap.severity, 0) + 1
        
        # Depth level distribution
        depth_levels = [report.depth_level.name for report in reports]
        depth_distribution = Counter(depth_levels)
        
        stats = {
            'total_responses': len(reports),
            'depth_scores': {
                'average': mean(depth_scores),
                'min': min(depth_scores),
                'max': max(depth_scores),
                'std_dev': stdev(depth_scores) if len(depth_scores) > 1 else 0
            },
            'consistency_scores': {
                'average': mean(consistency_scores),
                'min': min(consistency_scores),
                'max': max(consistency_scores)
            },
            'gap_statistics': gap_counts,
            'depth_distribution': dict(depth_distribution),
            'improvement_needed': sum(1 for score in depth_scores if score < 70)
        }
        
        return stats