"""
Evidence Synthesis Module
Generates coherent answers from retrieved evidence using Claude
"""

from typing import List
from loguru import logger
import anthropic

from llama_index.legacy.schema import NodeWithScore
from llama_index.legacy import PromptTemplate

import sys
sys.path.append('..')
from config import settings


class EvidenceSynthesizer:
    """Synthesizes retrieved evidence into coherent answers"""
    
    def __init__(self):
        """Initialize the synthesizer with Anthropic Claude LLM"""
        logger.info("Initializing EvidenceSynthesizer with Claude")
        
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key is required for synthesis")
        
        # Initialize Anthropic client with Messages API
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.llm_model
        self.temperature = 0.0  # Use deterministic responses for consistency
        self.max_tokens = 2048
        
        # Super simple synthesis prompt
        self.synthesis_prompt = PromptTemplate(
            """You are writing an answer for sophisticated investors.

RULES:
1. Use ONLY facts from the evidence below
2. Find specific numbers, names, and details in the evidence and USE THEM
3. Write 250-600 words (flexible - let content depth determine length)
4. Be specific, not vague

FIND AND USE EVERY SPECIFIC DETAIL:
- Exact numbers: contract counts, headcount, dollar amounts, percentages, ratios
- Financial data: returns, fees, allocations, performance metrics, Sharpe ratios
- Times and dates: trading hours, settlement periods, durations, frequencies
- Specific names: systems, platforms, exchanges, locations, ISOs
- Operational details: processes, procedures, organizational structure

ALWAYS REPLACE VAGUE WITH SPECIFIC:
- "multiple contracts" → exact contract count from evidence
- "strong performance" → exact return percentage from evidence  
- "trading hours" → exact time periods from evidence
- "portfolio allocation" → exact percentages from evidence
- "regularly" → exact frequency from evidence
- "experienced team" → exact team size and details from evidence

CRITICAL: Scan every piece of evidence for numbers, percentages, and specific data before writing each sentence.

USER QUESTION:
{query}

EVIDENCE:
{context}

Write a detailed answer using the specific facts from the evidence."""
        )
        
        logger.info(f"EvidenceSynthesizer initialized with model: {self.model}")
    
    def synthesize(self, query: str, retrieved_nodes: List[NodeWithScore]) -> str:
        """
        Synthesize a final answer from retrieved evidence
        
        Args:
            query: The original user query
            retrieved_nodes: List of retrieved nodes with scores
            
        Returns:
            str: The synthesized answer
        """
        logger.info(f"Synthesizing answer from {len(retrieved_nodes)} retrieved nodes")
        
        if not retrieved_nodes:
            logger.warning("No evidence retrieved for synthesis")
            return "I couldn't find any relevant information to answer your question. Please try rephrasing or ensure the relevant documents have been indexed."
        
        # Format the context from retrieved nodes
        context_parts = []
        for i, node_with_score in enumerate(retrieved_nodes, 1):
            node = node_with_score.node
            score = node_with_score.score
            
            # Extract source information from metadata
            source = node.metadata.get('source_file', 'Unknown source')
            
            # Format each piece of evidence
            evidence = f"""
Evidence {i}:
Source: {source}
Content: {node.text}
---"""
            context_parts.append(evidence)
        
        # Combine all evidence
        context = "\n".join(context_parts)
        
        # Log context size for monitoring
        logger.info(f"Context size: {len(context)} characters from {len(retrieved_nodes)} sources")
        
        # Generate the synthesis prompt
        prompt = self.synthesis_prompt.format(
            query=query,
            context=context
        )
        
        try:
            # Call Claude using Messages API
            logger.info("Calling Claude for synthesis...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract the text from the response
            answer = response.content[0].text.strip()
            
            logger.info(f"Synthesis complete - generated {len(answer)} character response")
            
            return answer
            
        except Exception as e:
            logger.error(f"Error during synthesis: {e}")
            return f"An error occurred while generating the answer: {str(e)}. Please check your API key and try again."