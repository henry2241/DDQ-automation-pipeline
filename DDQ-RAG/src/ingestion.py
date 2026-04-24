"""
Document Ingestion Module for Financial Documents
Handles multiple file types (PDF, MD, TXT, etc.) with table extraction and metadata enrichment
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
from loguru import logger

# Document processing - using unstructured for all file types
from unstructured.partition.auto import partition
from unstructured.documents.elements import Table, Title, NarrativeText

# LlamaIndex imports
from llama_index.legacy import Document
from llama_index.legacy.node_parser import (
    SentenceWindowNodeParser,
    HierarchicalNodeParser
)
from llama_index.legacy.schema import TextNode, NodeRelationship, RelatedNodeInfo

import sys
sys.path.append('..')
from config import (
    settings,
    DOCUMENT_CONFIGS,
    FINANCIAL_METRICS,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR
)


class FinancialDocumentIngestion:
    """Handles ingestion of financial documents with table preservation"""

    def __init__(self):
        self.processed_docs_cache = {}
        self.sentence_parser = SentenceWindowNodeParser.from_defaults(
            window_size=settings.sentence_window_size,
            window_metadata_key="window",
            original_text_metadata_key="original_text"
        )

        # Setup logging
        logger.add(
            "logs/ingestion.log",
            rotation="100 MB",
            retention="30 days",
            level="INFO"
        )

    def process_documents(self, document_paths: List[str]) -> List[TextNode]:
        """Process multiple documents and return enriched nodes"""
        all_nodes = []

        for doc_path in document_paths:
            logger.info(f"Processing document: {doc_path}")
            doc_type = self._identify_document_type(doc_path)
            nodes = self._process_single_document(doc_path, doc_type)
            all_nodes.extend(nodes)
            logger.info(f"Extracted {len(nodes)} nodes from {doc_path}")

        return all_nodes

    def _identify_document_type(self, file_path: str) -> str:
        """Identify document type based on filename and content patterns"""
        file_name = Path(file_path).stem.lower()

        for doc_type, config in DOCUMENT_CONFIGS.items():
            for pattern in config["patterns"]:
                if pattern in file_name:
                    return doc_type

        # If no pattern matches, analyze first part of content
        try:
            # Use unstructured to get a quick preview
            elements = partition(filename=file_path, max_partition=1)
            if elements:
                first_content = str(elements[0])[:500].lower()
                for doc_type, config in DOCUMENT_CONFIGS.items():
                    for pattern in config["patterns"]:
                        if pattern in first_content:
                            return doc_type
        except Exception as e:
            logger.warning(f"Could not analyze document type: {e}")

        return "General"

    def _process_single_document(self, file_path: str, doc_type: str) -> List[TextNode]:
        """Process a single document with intelligent chunking"""
        nodes = []

        # Check cache
        doc_hash = self._get_file_hash(file_path)
        cache_path = PROCESSED_DATA_DIR / f"{doc_hash}.json"

        if cache_path.exists():
            logger.info(f"Loading cached nodes for {file_path}")
            cached_nodes = self._load_cached_nodes(cache_path)
            if cached_nodes:  # Only use cache if it loaded successfully
                return cached_nodes
            else:
                logger.info(f"Cache invalid, will reprocess {file_path}")
                # Delete the invalid cache file
                cache_path.unlink()

        try:
            # Extract elements using unstructured (works for all file types)
            elements = self._extract_document_elements(file_path)

            # Process elements into nodes
            current_section = None
            current_subsection = None

            for idx, element in enumerate(elements):
                # Update section tracking
                if isinstance(element, Title):
                    # Check if it's a main title or subtitle based on the element type
                    current_section = element.text
                    current_subsection = None

                # Create node based on element type
                if isinstance(element, Table):
                    node = self._create_table_node(
                        element, file_path, doc_type, 
                        current_section, current_subsection, idx
                    )
                else:
                    node = self._create_text_node(
                        element, file_path, doc_type,
                        current_section, current_subsection, idx
                    )

                nodes.append(node)

            # Apply sentence window parsing to text nodes
            text_nodes = [n for n in nodes if n.metadata.get("element_type") == "text"]
            if text_nodes:
                windowed_nodes = self._apply_sentence_windows(text_nodes)
                # Replace text nodes with windowed versions
                nodes = [n for n in nodes if n.metadata.get("element_type") != "text"]
                nodes.extend(windowed_nodes)

            # Cache processed nodes
            self._cache_nodes(nodes, cache_path)

        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            raise

        return nodes

    def _extract_document_elements(self, file_path: str) -> List[Any]:
        """Extract structured elements from any document type using unstructured"""
        try:
            # Use partition auto to handle any file type
            elements = partition(
                filename=file_path,
                strategy="hi_res",  # Use high resolution for better quality
                infer_table_structure=True,
                include_page_breaks=True,
                extract_images_in_pdf=False,
                languages=["eng"]
            )
            return elements
        except Exception as e:
            logger.error(f"Error extracting elements from {file_path}: {e}")
            # Return basic text extraction as fallback
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
                return [{"text": text, "type": "text"}]

    def _create_table_node(
        self, 
        element: Table,
        file_path: str,
        doc_type: str,
        section: Optional[str],
        subsection: Optional[str],
        idx: int
    ) -> TextNode:
        """Create a node from a table element"""

        # Convert table to markdown
        table_text = str(element)

        # Detect financial metrics in table
        detected_metrics = self._detect_financial_metrics(table_text)

        # Ensure all metadata values are ChromaDB compatible types (str, int, float, None)
        page_num = getattr(element.metadata, 'page_number', None) if hasattr(element, 'metadata') else None
        if page_num is not None:
            page_num = int(page_num) if str(page_num).isdigit() else None
        
        node = TextNode(
            text=table_text,
            id_=f"{Path(file_path).stem}_table_{idx}",
            metadata={
                "source_file": str(Path(file_path).name),
                "document_type": str(doc_type),
                "page_number": page_num,
                "element_type": "table",
                "section_header": str(section) if section else None,
                "subsection": str(subsection) if subsection else None,
                "detected_metrics": ",".join(detected_metrics) if detected_metrics else "",
                "priority": int(DOCUMENT_CONFIGS.get(doc_type, {}).get("priority", 5)),
                "extraction_timestamp": str(datetime.now().isoformat())
            }
        )

        return node

    def _create_text_node(
        self,
        element: Any,
        file_path: str,
        doc_type: str,
        section: Optional[str],
        subsection: Optional[str],
        idx: int
    ) -> TextNode:
        """Create a node from a text element"""

        text = element.text if hasattr(element, 'text') else str(element)

        # Detect financial metrics in text
        detected_metrics = self._detect_financial_metrics(text)

        # Ensure all metadata values are ChromaDB compatible types (str, int, float, None)
        page_num = getattr(element.metadata, 'page_number', None) if hasattr(element, 'metadata') else None
        if page_num is not None:
            page_num = int(page_num) if str(page_num).isdigit() else None

        node = TextNode(
            text=text,
            id_=f"{Path(file_path).stem}_text_{idx}",
            metadata={
                "source_file": str(Path(file_path).name),
                "document_type": str(doc_type),
                "page_number": page_num,
                "element_type": "text",
                "section_header": str(section) if section else None,
                "subsection": str(subsection) if subsection else None,
                "detected_metrics": ",".join(detected_metrics) if detected_metrics else "",
                "priority": int(DOCUMENT_CONFIGS.get(doc_type, {}).get("priority", 5)),
                "extraction_timestamp": str(datetime.now().isoformat())
            }
        )

        return node

    def _apply_sentence_windows(self, text_nodes: List[TextNode]) -> List[TextNode]:
        """Apply sentence window parsing to text nodes"""
        documents = [Document(text=node.text, metadata=node.metadata) for node in text_nodes]
        return self.sentence_parser.get_nodes_from_documents(documents)

    def _detect_financial_metrics(self, text: str) -> List[str]:
        """Detect financial metrics mentioned in text"""
        detected = []
        text_lower = text.lower()

        for metric_category, keywords in FINANCIAL_METRICS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.append(f"{metric_category}:{keyword}")

        return list(set(detected))

    def _get_file_hash(self, file_path: str) -> str:
        """Generate hash for file caching"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def _cache_nodes(self, nodes: List[TextNode], cache_path: Path):
        """Cache processed nodes to disk"""
        serialized_nodes = []
        for node in nodes:
            serialized_nodes.append({
                "id": node.id_,
                "text": node.text,
                "metadata": node.metadata
            })
        
        with open(cache_path, 'w') as f:
            json.dump(serialized_nodes, f)
        logger.info(f"Cached {len(nodes)} nodes to {cache_path}")

    def _load_cached_nodes(self, cache_path: Path) -> List[TextNode]:
        """Load nodes from cache"""
        try:
            with open(cache_path, 'r') as f:
                nodes_data = json.load(f)
            
            nodes = []
            for node_data in nodes_data:
                # Handle both old and new cache formats
                if "id" in node_data:
                    metadata = node_data["metadata"].copy()
                    
                    # Fix detected_metrics if it's a list (old format)
                    if "detected_metrics" in metadata and isinstance(metadata["detected_metrics"], list):
                        logger.info("Converting detected_metrics from list to string in cached node")
                        metadata["detected_metrics"] = ",".join(metadata["detected_metrics"])
                    
                    # New format (with metadata fix)
                    node = TextNode(
                        text=node_data["text"],
                        id_=node_data["id"],
                        metadata=metadata
                    )
                else:
                    # Old format - regenerate with new structure
                    logger.warning("Old cache format detected, skipping cache")
                    return []
                nodes.append(node)
            return nodes
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}, will reprocess document")
            return []

def batch_ingest_documents(directory: Path = RAW_DATA_DIR) -> List[TextNode]:
    """Batch process all documents in a directory"""
    ingestion = FinancialDocumentIngestion()

    supported_extensions = ['.pdf', '.md', '.txt', '.docx', '.html', '.csv']
    document_files = [f for ext in supported_extensions for f in directory.glob(f"*{ext}")]

    if not document_files:
        logger.warning(f"No supported documents found in {directory}")
        return []

    logger.info(f"Found {len(document_files)} documents to process")

    all_nodes = ingestion.process_documents([str(f) for f in document_files])

    logger.info(f"Total nodes created: {len(all_nodes)}")

    summary_path = PROCESSED_DATA_DIR / "ingestion_summary.json"
    summary = {
        "total_nodes": len(all_nodes),
        "documents_processed": len(document_files),
        "timestamp": datetime.now().isoformat(),
        "node_breakdown": {
            "text_nodes": len([n for n in all_nodes if n.metadata.get("element_type") == "text"]),
            "table_nodes": len([n for n in all_nodes if n.metadata.get("element_type") == "table"])
        },
        "documents": [f.name for f in document_files]
    }

    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    return all_nodes
