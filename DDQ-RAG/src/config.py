"""
Configuration module for DDQ RAG Pipeline
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
INDEX_DIR = BASE_DIR / "indexes"
LOG_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, INDEX_DIR, LOG_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Keys
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Model Configuration
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5", env="EMBEDDING_MODEL")
    llm_model: str = Field(default="claude-3-5-haiku-20241022", env="LLM_MODEL")  # 50K input TPM + newer!
    llm_temperature: float = Field(default=0.0, env="LLM_TEMPERATURE")
    
    # Vector Store Configuration
    vector_store_type: str = Field(default="chromadb", env="VECTOR_STORE_TYPE")
    collection_name: str = Field(default="ddq_pipeline", env="COLLECTION_NAME")
    
    # Chunking Configuration
    chunk_size: int = Field(default=512, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=128, env="CHUNK_OVERLAP")
    sentence_window_size: int = Field(default=3, env="SENTENCE_WINDOW_SIZE")
    
    # Retrieval Configuration - Optimized for Sonnet's capabilities  
    retrieval_top_k: int = Field(default=150, env="RETRIEVAL_TOP_K")  # ~600 chunks for comprehensive coverage
    rerank_top_k: int = Field(default=75, env="RERANK_TOP_K")
    bm25_weight: float = Field(default=0.5, env="BM25_WEIGHT")
    vector_weight: float = Field(default=0.5, env="VECTOR_WEIGHT")
    
    # Processing Configuration
    batch_size: int = Field(default=10, env="BATCH_SIZE")
    max_workers: int = Field(default=4, env="MAX_WORKERS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Document type configurations
DOCUMENT_CONFIGS = {
    "PPM": {
        "patterns": ["private placement", "offering memorandum", "ppm"],
        "priority": 1,
        "sections": [
            "Executive Summary",
            "Investment Strategy",
            "Risk Factors",
            "Fund Terms",
            "Fee Structure"
        ]
    },
    "DDQ": {
        "patterns": ["due diligence", "questionnaire", "ddq"],
        "priority": 2,
        "sections": [
            "Organization",
            "Investment Process",
            "Risk Management",
            "Operations",
            "Compliance"
        ]
    },
    "Financials": {
        "patterns": ["audited", "financial statements", "balance sheet"],
        "priority": 3,
        "sections": [
            "Balance Sheet",
            "Income Statement",
            "Cash Flow",
            "Notes to Financial Statements"
        ]
    },
    "Tearsheet": {
        "patterns": ["tearsheet", "fact sheet", "performance summary"],
        "priority": 4,
        "sections": [
            "Performance",
            "Portfolio Statistics",
            "Risk Metrics",
            "Fund Information"
        ]
    }
}

# Query intent patterns
QUERY_INTENTS = {
    "FACT_EXTRACTION": {
        "keywords": ["what is", "how much", "when", "what are", "list"],
        "boost_bm25": True,
        "bm25_weight": 0.7
    },
    "PROCESS_EXPLANATION": {
        "keywords": ["how", "describe", "explain", "methodology", "process"],
        "boost_bm25": False,
        "bm25_weight": 0.4
    },
    "QUALITATIVE_ANALYSIS": {
        "keywords": ["evaluate", "assess", "compare", "sustainable", "impact"],
        "boost_bm25": False,
        "bm25_weight": 0.2
    }
}

# Financial metrics patterns for detection
FINANCIAL_METRICS = {
    "performance": ["return", "performance", "ytd", "mtd", "itd", "annualized"],
    "risk": ["sharpe", "sortino", "volatility", "var", "drawdown", "beta"],
    "liquidity": ["aum", "nav", "redemption", "subscription"],
    "fees": ["management fee", "performance fee", "hurdle", "high water mark"],
    "leverage": ["leverage", "exposure", "gross", "net", "margin"]
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}",
    "rotation": "100 MB",
    "retention": "30 days",
    "compression": "zip"
}

# Initialize settings
settings = Settings()