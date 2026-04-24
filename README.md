# DDQ RAG Pipeline

A production RAG (Retrieval-Augmented Generation) pipeline for automating Due Diligence
Questionnaire responses from institutional financial documents. The system ingests fund
documents, builds a vector index, retrieves relevant evidence, and synthesizes accurate
answers using Claude — with a full compliance and gap detection layer on top.

---

## Architecture

The system is built in two layers:

**Layer 1 — RAG Pipeline (`src/`)**
Ingests financial documents (DDQs, PPMs, financial statements, tearsheets), chunks and
indexes them using LlamaIndex and ChromaDB, then retrieves relevant content using dual
search — vector similarity and BM25 keyword search simultaneously — before synthesizing
answers with Claude.

**Layer 2 — Gap Compliance System (`gap_compliance_system/`)**
Runs on top of the RAG output to validate every answer against institutional standards:
detects missing information, checks regulatory compliance across SEC/CFTC/FINRA frameworks,
scores answer depth, assesses fiduciary risk, and maintains a full audit trail.

```
Document Question
       ↓
  query_processor.py       Decomposes complex questions
       ↓
  retrieval.py             Vector search + BM25 dual retrieval
       ↓
  synthesis.py             Claude generates answer from evidence
       ↓
  gap_detector.py          Finds missing or incomplete content
       ↓
  compliance_checker.py    Validates against regulatory frameworks
       ↓
  depth_analyzer.py        Scores answer quality and coverage
       ↓
  risk_assessor.py         Flags fiduciary and regulatory risk
       ↓
  audit_logger.py          Logs full lifecycle for audit trail
       ↓
  Final Validated Answer
```

---

## Stack

| | |
|---|---|
| Language | Python 3.10+ |
| LLM | Anthropic Claude API |
| RAG Framework | LlamaIndex |
| Vector Store | ChromaDB |
| Embeddings | BAAI/bge-small-en-v1.5 (HuggingFace) |
| Retrieval | Vector similarity + BM25 hybrid |
| Compliance | Custom SEC/CFTC/FINRA rule engine |

---

## Project Structure

```
DDQ-RAG/
├── src/                          ← RAG pipeline
│   ├── main.py                   ← CLI entry point and orchestrator
│   ├── ingestion.py              ← Document ingestion, chunking, metadata
│   ├── retrieval.py              ← Dual retrieval engine (vector + BM25)
│   ├── synthesis.py              ← Claude answer synthesis
│   ├── query_processor.py        ← Query decomposition
│   └── config.py                 ← Settings and environment config
│
├── gap_compliance_system/        ← Compliance and validation layer
│   ├── core/
│   │   ├── system_orchestrator.py
│   │   ├── configuration_manager.py
│   │   └── clara_integration.py
│   ├── modules/
│   │   ├── gap_detection/        ← Detects 16 types of missing content
│   │   ├── compliance_engine/    ← SEC, CFTC, FINRA, GDPR rule checking
│   │   ├── depth_analyzer/       ← Answer quality scoring
│   │   ├── risk_assessment/      ← Fiduciary risk flagging
│   │   └── audit_trail/          ← Full lifecycle audit logging
│   └── config/
│       ├── development.json
│       └── production.json
│
├── data/
│   └── raw/                      ← Place source documents here
├── indexes/                      ← Generated at runtime (ChromaDB, embeddings)
├── logs/                         ← Generated at runtime
├── requirements.txt
└── .env.example
```

---

## Development

This system was built through several iterations, evolving from simple Claude prompting
to a full production RAG pipeline:

- **V1:** Direct Claude prompting with manual document loading — fast to build, limited
  scalability and no source grounding
- **V2:** Python answer machines with batch processing and validation scripts — better
  throughput but still no true retrieval
- **V3 (current):** Full RAG pipeline with LlamaIndex, ChromaDB vector store, hybrid
  retrieval, and a modular compliance layer — source-grounded answers with institutional
  validation

Built using Claude Code and Cursor as development tools throughout.

---

## Running Locally

All core dependencies are installed and all modules import cleanly. The pipeline is
fully operational — add documents and it runs.

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Add your documents to data/raw/
# Supported: .pdf, .md, .txt

# Build the index
python src/main.py --rebuild

# Ask questions
python src/main.py --interactive
```

The `indexes/`, `data/processed/`, and `logs/` directories are generated automatically
when the pipeline runs — they do not need to exist beforehand.

---

## Key Features

- **Hybrid retrieval** — vector similarity and BM25 run simultaneously, results merged
  for maximum coverage
- **16 gap types detected** — missing documentation, insufficient detail, incorrect
  interpretation, unsupported claims, and more
- **Regulatory compliance grading** — A through F scoring against SEC Investment Advisers
  Act, CFTC, FINRA, and fiduciary standards
- **Automatic disclaimer insertion** — 10 disclaimer types inserted contextually
- **Full audit trail** — 35 event types logged across the complete answer lifecycle
- **Dev and prod configs** — separate thresholds and settings for each environment
