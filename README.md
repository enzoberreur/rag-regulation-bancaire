# LLM Banking Compliance Assistant

Professional RAG-powered application for intelligent querying of banking and financial regulatory documents.

![Dashboard](dashboard.png)

## Overview

Enterprise-grade RAG system combining semantic search, cross-encoder reranking, and GPT-4o-mini for accurate, cited answers to complex regulatory questions.

**Key Features:**
- Multi-stage RAG pipeline with query reformulation and reranking
- Semantic chunking with BAAI/bge-m3 embeddings (1024-dim)
- Real-time streaming responses with source citations
- PostgreSQL + pgvector for efficient vector search
- Document diversity algorithm ensuring multi-source answers

## Tech Stack

**Backend:** FastAPI, Python 3.12, PostgreSQL + pgvector, OpenAI GPT-4o-mini, BAAI/bge-m3, cross-encoder reranker  
**Frontend:** React 18, TypeScript, Vite, TailwindCSS, shadcn/ui  
**Infrastructure:** Server-Sent Events (SSE), HNSW vector indexing

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 15+ with pgvector extension
- Node.js 18+
- OpenAI API key

### Installation

```bash
# 1. Clone repository
git clone <your-repo>
cd LLM_PRODUCT

# 2. Database setup
createdb llmops_db
psql llmops_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 3. Backend setup
cd backend
poetry install
cp env.example .env
# Edit .env with your OPENAI_API_KEY and DATABASE_URL
poetry run python scripts/init_db.py

# 4. Frontend setup
cd ..
npm install

# 5. Launch
./run.sh  # Starts both backend (port 8000) and frontend (port 5173)
```

## Example Queries

**Credit Risk Mitigation in Large Exposures**
```
Using CRR Articles 399, 401 and 403, explain how a bank should treat credit risk mitigation techniques when calculating large exposures, and illustrate the process with a step-by-step example. Highlight any supervisory conditions mentioned by the ACPR.
```

**IRRBB Stress-Testing Framework**
```
Design a full IRRBB stress-testing framework consistent with EBA/GL/2022/14 and RTS EBA/RTS/2022/10. Include: (a) the modelling of non-maturity deposit behavioural maturities with the 5-year cap exception, (b) the Supervisory Outlier Test for abnormal sensitivities, and (c) parallel shock scenarios of ±200bp. Identify which assumptions require supervisor approval.
```

**Synthetic Securitisation SRT Assessment**
```
Given Articles 244–245 CRR, assess whether a synthetic securitisation achieves significant credit risk transfer. Include both mechanical tests and qualitative supervisory assessment requirements. Refer to how the Capital Markets Recovery Package modifies SRT conditions for on-balance-sheet STS transactions.
```

## Configuration

Key environment variables (`backend/.env`):

```bash
# OpenAI
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/llmops_db

# RAG Pipeline
TOP_K_RESULTS=8
INITIAL_TOP_K=20
SIMILARITY_THRESHOLD=0.65
RERANK_THRESHOLD=0.3
CHUNK_SIZE=800
CHUNK_OVERLAP=200

# Models
EMBEDDING_MODEL=BAAI/bge-m3
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
```

## API Endpoints

```bash
GET  /health                    # Health check
POST /api/chat/stream           # Streaming chat (SSE)
POST /api/documents/upload      # Upload document
GET  /api/documents/            # List documents
DELETE /api/documents/{id}      # Delete document
```

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── services/         # RAG, embeddings, reranking
│   │   ├── models/           # Database models
│   │   └── core/             # Configuration
│   ├── scripts/              # DB init, document upload
│   └── storage/              # Uploaded documents
├── src/
│   ├── components/           # React UI components
│   └── services/             # API client
└── data/                     # Sample documents
```

## RAG Pipeline

1. **Query Reformulation**: Expand query with GPT-4o-mini (temp=0.3)
2. **Vector Search**: Retrieve top 20 chunks via BAAI/bge-m3 embeddings
3. **Reranking**: Cross-encoder scoring, filter by threshold (≥0.3)
4. **Document Diversity**: Max 3 chunks per document
5. **LLM Generation**: GPT-4o-mini with streaming, cited responses

## Documentation

- [RAG Improvements Guide](backend/RAG_IMPROVEMENTS_PRO.md)
- [Backend Setup](backend/SETUP.md)

## Contributing

Educational project for Albert School Year 2 - LLM Ops program.

## License

Educational use only. No commercial use without permission.

---

**Developer:** Enzo Berreur | **Program:** Albert School Year 2 | **Year:** 2024-2025
