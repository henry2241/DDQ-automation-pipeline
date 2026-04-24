"""
DDQ RAG Pipeline Package
"""

__version__ = "1.0.0"

# Import main components from all modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import settings, BASE_DIR, DATA_DIR, RAW_DATA_DIR, INDEX_DIR, LOG_DIR
from .ingestion import batch_ingest_documents
from .query_processor import QueryProcessor, ProcessedQuery
from .retrieval import create_retrieval_engine
from .synthesis import EvidenceSynthesizer

# Define public API
__all__ = [
    "settings",
    "BASE_DIR",
    "DATA_DIR", 
    "RAW_DATA_DIR",
    "INDEX_DIR",
    "LOG_DIR",
    "batch_ingest_documents",
    "QueryProcessor",
    "ProcessedQuery",
    "create_retrieval_engine",
    "EvidenceSynthesizer"
]