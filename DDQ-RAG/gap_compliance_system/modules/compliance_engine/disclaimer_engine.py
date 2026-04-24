"""
Disclaimer Engine
================

Automated disclaimer insertion system for DDQ responses based on 
content analysis and compliance requirements.
"""

import re
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum

from .compliance_types import (
    DisclaimerType, ComplianceViolation, DISCLAIMER_TEMPLATES
)


class InsertionStrategy(Enum):
    """Strategies for disclaimer insertion."""
    
    IMMEDIATE = "immediate"          # Insert right after trigger content
    END_OF_SECTION = "end_of_section"  # Insert at end of current section
    END_OF_RESPONSE = "end_of_response"  # Insert at end of entire response
    CONTEXTUAL = "contextual"        # Insert based on content context


@dataclass
class DisclaimerContext:
    """Context for disclaimer insertion decisions."""
    
    trigger_text: str
    trigger_position: int
    surrounding_text: str
    section_context: str
    disclaimer_type: DisclaimerType
    insertion_strategy: InsertionStrategy = InsertionStrategy.CONTEXTUAL


@dataclass
class DisclaimerInsertion:
    """Represents a disclaimer to be inserted."""
    
    disclaimer_type: DisclaimerType
    template: str
    position: int
    strategy: InsertionStrategy
    trigger_context: str
    confidence: float = 1.0


class DisclaimerEngine:
    """
    Intelligent disclaimer insertion engine.
    
    Features:
    - Context-aware disclaimer placement
    - Duplicate disclaimer prevention
    - Template customization and formatting
    - Multiple insertion strategies
    - Compliance-driven automation
    """
    
    def __init__(self, custom_templates: Optional[Dict[DisclaimerType, str]] = None):
        """Initialize disclaimer engine with templates."""
        
        self.templates = DISCLAIMER_TEMPLATES.copy()
        if custom_templates:
            self.templates.update(custom_templates)
        
        # Disclaimer trigger patterns
        self.trigger_patterns = self._build_trigger_patterns()
        
        # Insertion preferences by disclaimer type
        self.insertion_preferences = self._build_insertion_preferences()
        
        # Content analysis patterns
        self.content_analyzers = self._build_content_analyzers()
    
    def _build_trigger_patterns(self) -> Dict[DisclaimerType, List[str]]:
        """Build pattern matching for disclaimer triggers."""
        return {
            DisclaimerType.PAST_PERFORMANCE: [
                r'(?:historical|past|previous)\s+(?:performance|return|result)',
                r'track\s+record',
                r'(?:since|from)\s+\d{4}',
                r'\d+%.*(?:annual|yearly|return)'
            ],
            
            DisclaimerType.FORWARD_LOOKING_STATEMENTS: [
                r'(?:will|expect|anticipate|project|forecast|estimate)',
                r'(?:future|expected|projected)\s+(?:performance|return|result)',
                r'(?:outlook|guidance|target)',
                r'going\s+forward'
            ],
            
            DisclaimerType.NO_GUARANTEE: [
                r'guarantee|assure|promise|ensure',
                r'certain|definite|sure\s+to',
                r'always.*(?:profitable|successful)',
                r'risk-free|no\s+risk'
            ],
            
            DisclaimerType.RISK_WARNING: [
                r'investment|strategy|portfolio|fund',
                r'allocation|position|exposure',
                r'trading|market\s+activity',
                r'derivatives|leverage|margin'
            ],
            
            DisclaimerType.HYPOTHETICAL_RESULTS: [
                r'(?:model|hypothetical|simulated|backtested)',
                r'theoretical|assumed',
                r'if.*had.*invested',
                r'pro\s+forma'
            ],
            
            DisclaimerType.MARKET_VOLATILITY: [
                r'market\s+(?:condition|environment|volatility)',
                r'economic\s+(?:factor|condition|environment)',
                r'interest\s+rate|inflation|recession',
                r'geopolitical|systemic\s+risk'
            ]
        }
    
    def _build_insertion_preferences(self) -> Dict[DisclaimerType, InsertionStrategy]:
        """Define preferred insertion strategies by disclaimer type."""
        return {
            DisclaimerType.PAST_PERFORMANCE: InsertionStrategy.IMMEDIATE,
            DisclaimerType.NO_GUARANTEE: InsertionStrategy.IMMEDIATE,
            DisclaimerType.HYPOTHETICAL_RESULTS: InsertionStrategy.IMMEDIATE,
            DisclaimerType.FORWARD_LOOKING_STATEMENTS: InsertionStrategy.END_OF_SECTION,
            DisclaimerType.RISK_WARNING: InsertionStrategy.END_OF_SECTION,
            DisclaimerType.MARKET_VOLATILITY: InsertionStrategy.END_OF_SECTION,
            DisclaimerType.INVESTMENT_SUITABILITY: InsertionStrategy.END_OF_RESPONSE,
            DisclaimerType.REGULATORY_COMPLIANCE: InsertionStrategy.END_OF_RESPONSE,
            DisclaimerType.DATA_ACCURACY: InsertionStrategy.END_OF_RESPONSE
        }
    
    def _build_content_analyzers(self) -> Dict[str, callable]:
        """Build content analysis functions for intelligent insertion."""
        return {
            'section_detector': self._detect_sections,
            'performance_context': self._analyze_performance_context,
            'risk_context': self._analyze_risk_context,
            'regulatory_context': self._analyze_regulatory_context
        }
    
    def auto_insert_disclaimers(
        self,
        response_text: str,
        required_disclaimers: List[DisclaimerType],
        compliance_violations: Optional[List[ComplianceViolation]] = None
    ) -> Tuple[str, List[DisclaimerInsertion]]:
        """
        Automatically insert required disclaimers into response.
        
        Args:
            response_text: Original response text
            required_disclaimers: List of disclaimer types to insert
            compliance_violations: Optional compliance violations for context
            
        Returns:
            Tuple of (modified_text, list_of_insertions)
        """
        
        # Analyze content for optimal insertion points
        insertion_points = self._analyze_insertion_points(response_text, required_disclaimers)
        
        # Remove duplicates and consolidate similar disclaimers
        consolidated_insertions = self._consolidate_disclaimers(insertion_points)
        
        # Apply insertions in reverse order to preserve positions
        modified_text = response_text
        applied_insertions = []
        
        for insertion in sorted(consolidated_insertions, key=lambda x: x.position, reverse=True):
            try:
                modified_text, actual_insertion = self._apply_insertion(modified_text, insertion)
                applied_insertions.append(actual_insertion)
            except Exception as e:
                # Log insertion failure but continue
                print(f"Failed to insert disclaimer {insertion.disclaimer_type}: {e}")
        
        return modified_text, list(reversed(applied_insertions))
    
    def _analyze_insertion_points(
        self,
        text: str,
        required_disclaimers: List[DisclaimerType]
    ) -> List[DisclaimerInsertion]:
        """Analyze text to find optimal disclaimer insertion points."""
        
        insertions = []
        
        for disclaimer_type in required_disclaimers:
            # Check if disclaimer is already present
            if self._disclaimer_already_present(text, disclaimer_type):
                continue
            
            # Find trigger patterns for this disclaimer type
            trigger_patterns = self.trigger_patterns.get(disclaimer_type, [])
            trigger_matches = []
            
            for pattern in trigger_patterns:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                trigger_matches.extend(matches)
            
            if trigger_matches:
                # Use first trigger match for positioning
                primary_match = trigger_matches[0]
                
                # Determine insertion position based on strategy
                position = self._calculate_insertion_position(
                    text, primary_match, disclaimer_type
                )
                
                insertion = DisclaimerInsertion(
                    disclaimer_type=disclaimer_type,
                    template=self.templates[disclaimer_type],
                    position=position,
                    strategy=self.insertion_preferences.get(disclaimer_type, InsertionStrategy.CONTEXTUAL),
                    trigger_context=primary_match.group(0),
                    confidence=0.9
                )
                insertions.append(insertion)
            
            else:
                # No specific triggers found, use general strategy
                position = self._get_default_position(text, disclaimer_type)
                
                insertion = DisclaimerInsertion(
                    disclaimer_type=disclaimer_type,
                    template=self.templates[disclaimer_type],
                    position=position,
                    strategy=InsertionStrategy.END_OF_RESPONSE,
                    trigger_context="General requirement",
                    confidence=0.7
                )
                insertions.append(insertion)
        
        return insertions
    
    def _disclaimer_already_present(self, text: str, disclaimer_type: DisclaimerType) -> bool:
        """Check if a disclaimer is already present in the text."""
        
        # Key phrases that indicate disclaimer presence
        disclaimer_indicators = {
            DisclaimerType.PAST_PERFORMANCE: [
                'past performance', 'not indicative', 'historical results'
            ],
            DisclaimerType.NO_GUARANTEE: [
                'no guarantee', 'no assurance', 'cannot guarantee'
            ],
            DisclaimerType.FORWARD_LOOKING_STATEMENTS: [
                'forward-looking', 'actual results may differ', 'projections'
            ],
            DisclaimerType.RISK_WARNING: [
                'risk of loss', 'investment risk', 'all investments'
            ],
            DisclaimerType.HYPOTHETICAL_RESULTS: [
                'hypothetical', 'model results', 'simulated performance'
            ]
        }
        
        indicators = disclaimer_indicators.get(disclaimer_type, [])
        text_lower = text.lower()
        
        return any(indicator in text_lower for indicator in indicators)
    
    def _calculate_insertion_position(
        self,
        text: str,
        trigger_match: re.Match,
        disclaimer_type: DisclaimerType
    ) -> int:
        """Calculate optimal insertion position based on strategy."""
        
        strategy = self.insertion_preferences.get(disclaimer_type, InsertionStrategy.CONTEXTUAL)
        
        if strategy == InsertionStrategy.IMMEDIATE:
            # Insert right after the trigger match
            return trigger_match.end() + 1
        
        elif strategy == InsertionStrategy.END_OF_SECTION:
            # Find the end of current section
            return self._find_section_end(text, trigger_match.start())
        
        elif strategy == InsertionStrategy.END_OF_RESPONSE:
            return len(text)
        
        else:  # CONTEXTUAL
            # Analyze context to determine best position
            return self._find_contextual_position(text, trigger_match, disclaimer_type)
    
    def _find_section_end(self, text: str, start_pos: int) -> int:
        """Find the end of the current section containing start_pos."""
        
        # Look for section breaks (double newlines, headers, etc.)
        section_breaks = [r'\n\s*\n', r'\n#+\s', r'\n\*\*[^*]+\*\*', r'\n\d+\.']
        
        for pattern in section_breaks:
            match = re.search(pattern, text[start_pos:])
            if match:
                return start_pos + match.start() + 1
        
        # If no section break found, use end of response
        return len(text)
    
    def _find_contextual_position(
        self,
        text: str,
        trigger_match: re.Match,
        disclaimer_type: DisclaimerType
    ) -> int:
        """Find contextually appropriate insertion position."""
        
        # Analyze surrounding sentences
        sentences = self._split_into_sentences(text)
        trigger_sentence_idx = self._find_sentence_containing_position(
            sentences, trigger_match.start()
        )
        
        if trigger_sentence_idx is None:
            return trigger_match.end() + 1
        
        # For performance-related disclaimers, insert after performance discussion
        if disclaimer_type in [DisclaimerType.PAST_PERFORMANCE, DisclaimerType.HYPOTHETICAL_RESULTS]:
            # Look for end of performance-related content
            for i in range(trigger_sentence_idx + 1, min(len(sentences), trigger_sentence_idx + 3)):
                if not self._sentence_relates_to_performance(sentences[i]):
                    position = sum(len(s) + 1 for s in sentences[:i])  # +1 for spaces/periods
                    return position
        
        # Default to end of trigger sentence
        position = sum(len(s) + 1 for s in sentences[:trigger_sentence_idx + 1])
        return position
    
    def _get_default_position(self, text: str, disclaimer_type: DisclaimerType) -> int:
        """Get default insertion position when no triggers found."""
        
        # Risk warnings generally go at the end
        if disclaimer_type in [DisclaimerType.RISK_WARNING, DisclaimerType.INVESTMENT_SUITABILITY]:
            return len(text)
        
        # Regulatory disclaimers at the very end
        if disclaimer_type in [DisclaimerType.REGULATORY_COMPLIANCE, DisclaimerType.DATA_ACCURACY]:
            return len(text)
        
        # Others can go at reasonable break points
        return self._find_reasonable_break_point(text)
    
    def _find_reasonable_break_point(self, text: str) -> int:
        """Find a reasonable position to insert disclaimer."""
        
        # Look for paragraph breaks in the last third of the response
        start_search = len(text) * 2 // 3
        
        paragraph_breaks = list(re.finditer(r'\n\s*\n', text[start_search:]))
        if paragraph_breaks:
            return start_search + paragraph_breaks[-1].end()
        
        return len(text)
    
    def _consolidate_disclaimers(
        self,
        insertions: List[DisclaimerInsertion]
    ) -> List[DisclaimerInsertion]:
        """Consolidate similar disclaimers and remove duplicates."""
        
        # Group by position ranges (within 50 characters)
        groups = []
        
        for insertion in sorted(insertions, key=lambda x: x.position):
            placed = False
            
            for group in groups:
                if any(abs(insertion.position - existing.position) < 50 for existing in group):
                    group.append(insertion)
                    placed = True
                    break
            
            if not placed:
                groups.append([insertion])
        
        # Consolidate each group
        consolidated = []
        for group in groups:
            if len(group) == 1:
                consolidated.append(group[0])
            else:
                # Create combined disclaimer for groups
                combined_insertion = self._combine_disclaimer_group(group)
                consolidated.append(combined_insertion)
        
        return consolidated
    
    def _combine_disclaimer_group(
        self,
        group: List[DisclaimerInsertion]
    ) -> DisclaimerInsertion:
        """Combine multiple disclaimers into a single consolidated disclaimer."""
        
        # Use the earliest position
        position = min(insertion.position for insertion in group)
        
        # Combine templates intelligently
        combined_template = self._merge_disclaimer_templates([ins.template for ins in group])
        
        # Use the most specific disclaimer type or create a composite
        primary_type = max(group, key=lambda x: x.confidence).disclaimer_type
        
        return DisclaimerInsertion(
            disclaimer_type=primary_type,
            template=combined_template,
            position=position,
            strategy=InsertionStrategy.CONTEXTUAL,
            trigger_context=f"Combined: {', '.join(ins.trigger_context for ins in group)}",
            confidence=sum(ins.confidence for ins in group) / len(group)
        )
    
    def _merge_disclaimer_templates(self, templates: List[str]) -> str:
        """Merge multiple disclaimer templates into a coherent single disclaimer."""
        
        # Remove duplicates while preserving order
        unique_templates = []
        seen = set()
        
        for template in templates:
            if template not in seen:
                unique_templates.append(template)
                seen.add(template)
        
        if len(unique_templates) == 1:
            return unique_templates[0]
        
        # Create consolidated disclaimer
        combined = "**IMPORTANT DISCLAIMERS:**\n\n"
        
        for i, template in enumerate(unique_templates, 1):
            # Extract the content after the disclaimer header
            content = re.sub(r'^\*\*[^*]+\*\*:?\s*', '', template.strip())
            combined += f"{i}. {content}\n\n"
        
        return combined.rstrip()
    
    def _apply_insertion(
        self,
        text: str,
        insertion: DisclaimerInsertion
    ) -> Tuple[str, DisclaimerInsertion]:
        """Apply a disclaimer insertion to the text."""
        
        position = min(insertion.position, len(text))
        
        # Format disclaimer for insertion
        formatted_disclaimer = self._format_disclaimer_for_insertion(
            insertion.template, text, position
        )
        
        # Insert disclaimer
        modified_text = (
            text[:position] + 
            formatted_disclaimer + 
            text[position:]
        )
        
        # Update insertion record with actual position
        actual_insertion = DisclaimerInsertion(
            disclaimer_type=insertion.disclaimer_type,
            template=formatted_disclaimer,
            position=position,
            strategy=insertion.strategy,
            trigger_context=insertion.trigger_context,
            confidence=insertion.confidence
        )
        
        return modified_text, actual_insertion
    
    def _format_disclaimer_for_insertion(self, template: str, text: str, position: int) -> str:
        """Format disclaimer template for insertion at specific position."""
        
        # Add appropriate spacing
        prefix = ""
        suffix = ""
        
        # Check if we need spacing before
        if position > 0 and not text[position - 1].isspace():
            prefix = "\n\n"
        elif position > 0 and text[position - 1] == '\n':
            prefix = "\n"
        
        # Check if we need spacing after
        if position < len(text) and not text[position].isspace():
            suffix = "\n\n"
        elif position < len(text) and text[position] == '\n':
            suffix = "\n"
        
        return prefix + template + suffix
    
    def _detect_sections(self, text: str) -> List[Tuple[int, int, str]]:
        """Detect sections in the text."""
        sections = []
        
        # Look for headers and natural breaks
        section_patterns = [
            r'\n#+\s+([^\n]+)',  # Markdown headers
            r'\n\*\*([^*]+)\*\*',  # Bold headers
            r'\n(\d+[\.\)]\s+[^\n]+)',  # Numbered sections
            r'\n([A-Z][^:\n]*):',  # Capitalized labels
        ]
        
        current_pos = 0
        
        for pattern in section_patterns:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                if match.start() > current_pos:
                    section_title = match.group(1) if match.groups() else "Section"
                    sections.append((current_pos, match.start(), section_title))
                    current_pos = match.start()
        
        # Add final section
        if current_pos < len(text):
            sections.append((current_pos, len(text), "Final Section"))
        
        return sections
    
    def _analyze_performance_context(self, text: str, position: int) -> Dict[str, Any]:
        """Analyze performance-related context around position."""
        
        # Extract context window
        start = max(0, position - 200)
        end = min(len(text), position + 200)
        context = text[start:end]
        
        performance_indicators = [
            'return', 'performance', 'gain', 'profit', 'loss',
            'sharpe', 'alpha', 'beta', 'volatility', 'drawdown'
        ]
        
        indicator_count = sum(1 for indicator in performance_indicators 
                            if indicator in context.lower())
        
        return {
            'performance_density': indicator_count / len(context.split()) if context else 0,
            'has_numerical_performance': bool(re.search(r'\d+\.?\d*%', context)),
            'has_time_series': bool(re.search(r'\d{4}', context))
        }
    
    def _analyze_risk_context(self, text: str, position: int) -> Dict[str, Any]:
        """Analyze risk-related context around position."""
        
        start = max(0, position - 200)
        end = min(len(text), position + 200)
        context = text[start:end]
        
        risk_indicators = [
            'risk', 'volatility', 'loss', 'adverse', 'downside',
            'market', 'economic', 'systematic', 'idiosyncratic'
        ]
        
        risk_count = sum(1 for indicator in risk_indicators 
                        if indicator in context.lower())
        
        return {
            'risk_density': risk_count / len(context.split()) if context else 0,
            'has_risk_metrics': bool(re.search(r'(?:var|value at risk|standard deviation)', context, re.IGNORECASE))
        }
    
    def _analyze_regulatory_context(self, text: str, position: int) -> Dict[str, Any]:
        """Analyze regulatory context around position."""
        
        start = max(0, position - 200)
        end = min(len(text), position + 200)
        context = text[start:end]
        
        regulatory_indicators = [
            'sec', 'cftc', 'finra', 'regulation', 'compliance',
            'fiduciary', 'disclosure', 'advisory', 'registered'
        ]
        
        reg_count = sum(1 for indicator in regulatory_indicators 
                       if indicator in context.lower())
        
        return {
            'regulatory_density': reg_count / len(context.split()) if context else 0,
            'mentions_advisor': 'advisor' in context.lower() or 'adviser' in context.lower()
        }
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting on periods, exclamation marks, and question marks
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _find_sentence_containing_position(self, sentences: List[str], position: int) -> Optional[int]:
        """Find which sentence contains the given position."""
        current_pos = 0
        
        for i, sentence in enumerate(sentences):
            sentence_end = current_pos + len(sentence) + 1  # +1 for separator
            if current_pos <= position < sentence_end:
                return i
            current_pos = sentence_end
        
        return None
    
    def _sentence_relates_to_performance(self, sentence: str) -> bool:
        """Check if sentence relates to performance discussion."""
        performance_terms = [
            'return', 'performance', 'gain', 'profit', 'outperform',
            'achieve', 'deliver', 'generate', 'sharpe', 'alpha'
        ]
        
        sentence_lower = sentence.lower()
        return any(term in sentence_lower for term in performance_terms)
    
    def customize_template(self, disclaimer_type: DisclaimerType, new_template: str):
        """Customize a disclaimer template."""
        self.templates[disclaimer_type] = new_template
    
    def get_available_disclaimers(self) -> List[DisclaimerType]:
        """Get list of available disclaimer types."""
        return list(self.templates.keys())
    
    def preview_disclaimer_insertion(
        self,
        response_text: str,
        disclaimer_types: List[DisclaimerType]
    ) -> List[Dict[str, Any]]:
        """Preview where disclaimers would be inserted without applying them."""
        
        insertion_points = self._analyze_insertion_points(response_text, disclaimer_types)
        
        previews = []
        for insertion in insertion_points:
            preview = {
                'disclaimer_type': insertion.disclaimer_type.name,
                'position': insertion.position,
                'strategy': insertion.strategy.value,
                'trigger_context': insertion.trigger_context,
                'template_preview': insertion.template[:100] + '...' if len(insertion.template) > 100 else insertion.template,
                'confidence': insertion.confidence
            }
            previews.append(preview)
        
        return previews