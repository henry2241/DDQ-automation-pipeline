"""
Comprehensive Retrieval Engine Module
Implements DDQ-style aggressive search with multiple passes for complete coverage
"""

from typing import List, Set, Dict
from loguru import logger
import re

from llama_index.legacy import VectorStoreIndex
from llama_index.legacy.retrievers import BM25Retriever, VectorIndexRetriever
from llama_index.legacy.query_engine import RetrieverQueryEngine
from llama_index.legacy.schema import NodeWithScore, QueryBundle

import sys
sys.path.append('..')
from config import settings


class ComprehensiveRetriever:
    """DDQ-style comprehensive retriever that finds ALL relevant content"""
    
    def __init__(self, index: VectorStoreIndex, nodes: List, embed_model):
        self.index = index
        self.nodes = nodes
        self.embed_model = embed_model
        
        # Create base retrievers
        self.vector_retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=settings.retrieval_top_k,
            filters=None,
            vector_store_query_mode="default"
        )
        
        self.bm25_retriever = BM25Retriever.from_defaults(
            nodes=nodes,
            similarity_top_k=settings.retrieval_top_k
        )
        
        logger.info(f"ComprehensiveRetriever initialized with {len(nodes)} nodes")
    
    def generate_search_variations(self, query: str) -> List[str]:
        """Generate multiple search variations like DDQ system"""
        variations = [query.strip()]  # Original query
        
        # Extract key terms and create variations
        words = query.lower().split()
        key_terms = [w for w in words if len(w) > 3 and w not in ['what', 'how', 'when', 'where', 'which', 'are', 'is', 'the', 'and', 'or', 'but', 'with']]
        
        # Single key terms
        for term in key_terms:
            variations.append(term)
        
        # Pairs of key terms
        for i, term1 in enumerate(key_terms):
            for term2 in key_terms[i+1:]:
                variations.append(f"{term1} {term2}")
        
        # AGGRESSIVE domain-specific expansions to match DDQ system
        if 'trading' in query.lower():
            variations.extend(['trading strategies', 'trade execution', 'market making', 'arbitrage', 
                             'day-ahead', 'real-time', 'power trading', 'electricity trading',
                             'energy trading', 'virtual power', 'FTR', 'financial transmission rights',
                             'ISO', 'RTO', 'grid trading', 'congestion', 'nodal', 'LMP'])
        if 'power' in query.lower() or 'grid' in query.lower():
            variations.extend(['electricity', 'energy', 'transmission', 'ISO', 'RTO', 'congestion',
                             'power grid', 'electrical grid', 'transmission grid', 'grid operations',
                             'grid management', 'power markets', 'electricity markets', 'CAISO', 'PJM', 'ERCOT'])
        if 'risk' in query.lower():
            variations.extend(['risk management', 'VaR', 'exposure', 'hedging', 'risk control',
                             'portfolio risk', 'market risk', 'operational risk', 'risk limits'])
        
        # Add financial and operational terms for comprehensive coverage
        variations.extend(['strategy', 'strategies', 'approach', 'methodology', 'process', 'operations',
                          'management', 'system', 'systems', 'protocol', 'protocols'])
        
        logger.info(f"Generated {len(variations)} search variations from query: {query}")
        return variations
    
    def comprehensive_retrieve(self, query: str) -> List[NodeWithScore]:
        """Retrieve using multiple search passes for comprehensive coverage"""
        all_results = {}
        search_variations = self.generate_search_variations(query)
        
        logger.info(f"Starting comprehensive retrieval with {len(search_variations)} variations")
        
        for i, variation in enumerate(search_variations):  # USE ALL VARIATIONS - no limits
            query_bundle = QueryBundle(query_str=variation)
            
            # Vector search for this variation
            try:
                vector_results = self.vector_retriever.retrieve(query_bundle)
                for node_score in vector_results:
                    node_id = node_score.node.node_id
                    if node_id not in all_results:
                        all_results[node_id] = node_score
                    else:
                        # Boost score for multiple matches
                        existing_score = all_results[node_id].score or 0
                        new_score = node_score.score or 0
                        all_results[node_id].score = max(existing_score, new_score) * 1.1
            except Exception as e:
                logger.warning(f"Vector search failed for '{variation}': {e}")
            
            # BM25 search for this variation
            try:
                bm25_results = self.bm25_retriever.retrieve(query_bundle)
                for node_score in bm25_results:
                    node_id = node_score.node.node_id
                    if node_id not in all_results:
                        all_results[node_id] = node_score
                    else:
                        # Boost score for multiple matches
                        existing_score = all_results[node_id].score or 0
                        new_score = node_score.score or 0
                        all_results[node_id].score = max(existing_score, new_score) * 1.1
            except Exception as e:
                logger.warning(f"BM25 search failed for '{variation}': {e}")
        
        # Convert to list and sort by score
        final_results = list(all_results.values())
        final_results.sort(key=lambda x: x.score or 0, reverse=True)
        
        # SMART DEDUPLICATION - Keep top chunks but limit total context size
        # Target: ~100K characters (~50K tokens) to stay under rate limits
        target_chars = 100000
        current_chars = 0
        deduplicated_results = []
        
        for node_score in final_results:
            node_text = node_score.node.text or ""
            node_chars = len(node_text)
            
            # Add if we're under the limit
            if current_chars + node_chars <= target_chars:
                deduplicated_results.append(node_score)
                current_chars += node_chars
            else:
                # Stop adding - we've hit our limit
                break
        
        logger.info(f"Smart deduplication: {len(final_results)} → {len(deduplicated_results)} chunks")
        logger.info(f"Context reduced: {sum(len(n.node.text or '') for n in final_results)} → {current_chars} characters")
        return deduplicated_results


def create_retrieval_engine(index: VectorStoreIndex, nodes: List, embed_model):
    """
    Creates a comprehensive retrieval engine matching DDQ system's aggressive approach
    
    Args:
        index: The LlamaIndex VectorStoreIndex
        nodes: The list of document nodes for BM25 retrieval
        embed_model: The embedding model to use in ServiceContext
        
    Returns:
        ComprehensiveRetriever: The comprehensive retrieval system
    """
    logger.info("Creating comprehensive retrieval engine matching DDQ system")
    
    # Create the comprehensive retriever
    comprehensive_retriever = ComprehensiveRetriever(index, nodes, embed_model)
    
    logger.info("Comprehensive retrieval engine successfully created")
    
    return comprehensive_retriever