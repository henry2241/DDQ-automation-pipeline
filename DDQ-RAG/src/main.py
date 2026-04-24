"""
Main Entry Point for DDQ RAG Pipeline
Orchestrates the complete RAG workflow with CLI interface
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import argparse
import pickle
from pathlib import Path
from typing import Optional
from loguru import logger

# LlamaIndex imports
from llama_index.legacy import VectorStoreIndex, StorageContext, load_index_from_storage, ServiceContext
from llama_index.legacy.embeddings import HuggingFaceEmbedding
from llama_index.legacy.vector_stores import ChromaVectorStore
import chromadb

# Local imports
from config import settings, INDEX_DIR, LOG_DIR, RAW_DATA_DIR
from ingestion import batch_ingest_documents
from query_processor import QueryProcessor
from retrieval import create_retrieval_engine
from synthesis import EvidenceSynthesizer


class DDQRAG:
    """Main orchestrator for the RAG pipeline"""
    
    def __init__(self):
        """Initialize the RAG pipeline components"""
        # Setup logging
        logger.add(
            LOG_DIR / "main.log",
            rotation="100 MB",
            retention="30 days",
            level="INFO"
        )
        logger.info("Initializing DDQ RAG Pipeline")
        
        # Initialize components
        self.query_processor = QueryProcessor()
        self.synthesizer = None  # Will be initialized when needed
        self.query_engine = None
        self.index = None
        self.nodes = None
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        self.embed_model = HuggingFaceEmbedding(
            model_name=settings.embedding_model,
            cache_folder=str(INDEX_DIR / "embeddings_cache")
        )
        
        # Setup ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=str(INDEX_DIR / "chroma_db")
        )
        
    def rebuild_index(self):
        """Rebuild the index from documents in the raw data directory"""
        print("\nStarting index rebuild process...")
        logger.info("Starting index rebuild")
        
        # Step 1: Clear old cache and ingest documents
        print("Clearing old cache...")
        processed_dir = RAW_DATA_DIR.parent / "processed"
        if processed_dir.exists():
            import shutil
            shutil.rmtree(processed_dir)
        processed_dir.mkdir(exist_ok=True)
        
        # Also clear any existing nodes.pkl file
        nodes_path = INDEX_DIR / "nodes.pkl"
        if nodes_path.exists():
            nodes_path.unlink()
            print("Cleared existing nodes cache")
        
        print("Ingesting documents...")
        nodes = batch_ingest_documents(RAW_DATA_DIR)
        
        if not nodes:
            print("ERROR: No documents found to index!")
            logger.error("No documents found in raw data directory")
            return False
        
        print(f"SUCCESS: Ingested {len(nodes)} text chunks")
        self.nodes = nodes
        
        # Step 2: Create/recreate ChromaDB collection
        print("Creating vector store...")
        logger.info("Creating ChromaDB collection")
        
        # Delete existing collection if it exists
        try:
            self.chroma_client.delete_collection(settings.collection_name)
            logger.info("Deleted existing collection")
        except:
            pass
        
        # Create new collection
        collection = self.chroma_client.create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Step 3: Create vector store and index
        print("Building vector index...")
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Create service context with no LLM and our embedding model
        service_context = ServiceContext.from_defaults(
            llm=None,  # Disable LLM for index creation
            embed_model=self.embed_model
        )
        
        self.index = VectorStoreIndex(
            nodes=nodes,
            storage_context=storage_context,
            service_context=service_context,
            show_progress=True
        )
        
        # Step 4: Save nodes to disk for later use
        nodes_path = INDEX_DIR / "nodes.pkl"
        with open(nodes_path, 'wb') as f:
            pickle.dump(nodes, f)
        logger.info(f"Saved {len(nodes)} nodes to {nodes_path}")
        
        # Step 5: Persist storage context
        storage_context.persist(persist_dir=str(INDEX_DIR / "storage"))
        logger.info("Persisted storage context")
        
        print(f"SUCCESS: Index built with {len(nodes)} chunks")
        print(f"Index saved to: {INDEX_DIR}")
        
        return True
    
    def load_index(self) -> bool:
        """Load the pre-built index from disk"""
        logger.info("Attempting to load index from disk")
        
        try:
            # Load nodes
            nodes_path = INDEX_DIR / "nodes.pkl"
            if not nodes_path.exists():
                logger.error("Nodes file not found")
                return False
            
            with open(nodes_path, 'rb') as f:
                self.nodes = pickle.load(f)
            logger.info(f"Loaded {len(self.nodes)} nodes")
            
            # Load storage context
            storage_dir = INDEX_DIR / "storage"
            if not storage_dir.exists():
                logger.error("Storage directory not found")
                return False
            
            # Get existing collection
            collection = self.chroma_client.get_collection(settings.collection_name)
            vector_store = ChromaVectorStore(chroma_collection=collection)
            
            # Create service context for loading
            service_context = ServiceContext.from_defaults(
                llm=None,  # Disable LLM for index loading
                embed_model=self.embed_model
            )
            
            # Load index
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store,
                persist_dir=str(storage_dir)
            )
            
            self.index = load_index_from_storage(
                storage_context,
                service_context=service_context
            )
            
            logger.info("Index loaded successfully")
            
            # Create query engine
            self.query_engine = create_retrieval_engine(self.index, self.nodes, self.embed_model)
            
            # Initialize synthesizer
            self.synthesizer = EvidenceSynthesizer()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False
    
    def query(self, question: str) -> str:
        """
        Process a query through the complete RAG pipeline
        
        Args:
            question: The user's question
            
        Returns:
            str: The synthesized answer
        """
        logger.info(f"Processing query: {question}")
        
        # Step 1: Process the query
        processed_query = self.query_processor.process_query(question)
        
        # Step 2: Retrieve relevant chunks using comprehensive search
        # For now, use the first sub-query (since we're doing pass-through)
        query_str = processed_query.sub_queries[0]
        source_nodes = self.query_engine.comprehensive_retrieve(query_str)
        logger.info(f"Retrieved {len(source_nodes)} relevant chunks")
        
        # Step 3: Synthesize final answer
        answer = self.synthesizer.synthesize(question, source_nodes)
        
        return answer
    
    def interactive_mode(self):
        """Run the pipeline in interactive mode"""
        print("\nDDQ RAG Pipeline - Interactive Mode")
        print("=" * 60)
        print("Type your questions below (or 'quit' to exit)")
        print("=" * 60)
        
        while True:
            try:
                # Get user input
                question = input("\nYour question: ").strip()
                
                # Check for exit command
                if question.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye!")
                    break
                
                if not question:
                    continue
                
                # Process the query
                print("\nSearching for relevant information...")
                answer = self.query(question)
                
                # Display the answer
                print("\n" + "=" * 60)
                print("Answer:")
                print("=" * 60)
                print(answer)
                print("=" * 60)
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nERROR: {e}")
                logger.error(f"Error in interactive mode: {e}")


def main():
    """Main entry point with CLI"""
    parser = argparse.ArgumentParser(
        description="DDQ RAG Pipeline - Financial Document Q&A System"
    )
    
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild the index from documents in data/raw/"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode for continuous Q&A"
    )
    
    args = parser.parse_args()
    
    # Initialize the pipeline
    rag = DDQRAG()
    
    if args.rebuild:
        # Rebuild the index
        success = rag.rebuild_index()
        if not success:
            print("\nERROR: Index rebuild failed. Please check the logs.")
            sys.exit(1)
        print("\nSUCCESS: Index rebuild complete!")
        
    elif args.interactive:
        # Load existing index and run interactive mode
        print("\nLoading existing index...")
        
        if not rag.load_index():
            print("\nERROR: Failed to load index!")
            print("Please run with --rebuild first to create the index:")
            print("  python src/main.py --rebuild")
            sys.exit(1)
        
        print("SUCCESS: Index loaded!")
        
        # Start interactive mode
        rag.interactive_mode()
        
    else:
        # No arguments provided - show help
        parser.print_help()
        print("\nExamples:")
        print("  Build index:     python src/main.py --rebuild")
        print("  Ask questions:   python src/main.py --interactive")


if __name__ == "__main__":
    main()