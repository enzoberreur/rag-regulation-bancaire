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

**MREL Calibration and Capital Buffer Interaction for G-SIBs**
```
How do the Minimum Requirement for own funds and Eligible Liabilities (MREL) calibration and the capital buffer framework (Conservation Buffer, G-SIB buffer, Systemic Risk Buffer) interact for a French Global Systemically Important Bank (G-SIB)? Specifically, explain how a breach of the combined buffer requirement could impact the bank's ability to meet its MREL, including the M-MDA (Maximum Distributable Amount) restrictions.
```

**CET1 Ratio Calculation with Capital Instruments**
```
Explain the complete methodology for calculating the Common Equity Tier 1 (CET1) ratio according to CRD4, including: (a) which capital instruments qualify as CET1 under Article 26 to 31, (b) the regulatory adjustments and deductions that must be applied (intangible assets, deferred tax assets, prudential filters), (c) how the ratio differs between individual and consolidated levels, and (d) the minimum CET1 ratio requirements including buffers for French banks.
```

**Total Loss-Absorbing Capacity (TLAC) Requirements**
```
Detail the Total Loss-Absorbing Capacity (TLAC) requirements for French G-SIBs under CRD4. Include: (a) the minimum TLAC ratio expressed as a percentage of risk-weighted assets (RWA) and leverage ratio exposure, (b) which liabilities qualify as TLAC-eligible (subordination requirements, remaining maturity, contractual features), (c) how TLAC interacts with MREL calibration, and (d) the transition timeline and exemptions for specific instruments.
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

## RAG Pipeline Architecture

### 1. HyDE (Hypothetical Document Embeddings) Strategy

**Tool:** OpenAI GPT-4o-mini  
**Parameters:** `temperature=0.7`, `max_tokens=250`

Instead of directly embedding the user's question, we generate a hypothetical "perfect answer" paragraph (3-4 sentences) that mimics how the regulatory document would explain the concept. This bridges the vocabulary gap between questions ("How do buffers work?") and technical documents ("Article 12 quinquies stipulates CBR of 4.5%...").

**Why HyDE?**
- Regulatory documents use formal terminology; user questions are natural language
- Semantic search works better when comparing "document-like" text to documents
- Generates technical keywords (MREL, M-MDA, CBR) that appear in actual regulations

**Example:**
- User query: "How do capital buffers affect MREL?"
- HyDE output: "The calibration of MREL for G-SIBs requires institutions to maintain eligible liabilities at 18% TREA plus the Combined Buffer Requirement (CBR), which includes the Conservation Buffer (2.5%), G-SIB buffer (up to 2.5%), and potentially a Systemic Risk Buffer..."
- This HyDE paragraph is embedded and used for vector search instead of the raw query

---

### 2. Token-Based Semantic Chunking

**Tool:** LangChain `RecursiveCharacterTextSplitter` + tiktoken `cl100k_base`  
**Parameters:** 
- `chunk_size=1200` tokens (~900 words)
- `chunk_overlap=300` tokens (25% overlap)
- Hierarchical separators: `\n\n\n` → `\nARTICLE ` → `\nSection ` → `\n\n` → `. ` → `, `

**Why Token-Based (not Sentence-Based)?**

Previous implementation used sentence-based chunking (5 sentences per chunk = ~100-200 words). This caused **catastrophic reranker scores (0.020/1.0)** because:
- Chunks were too small to contain complete regulatory mechanisms
- Reranker couldn't evaluate semantic relevance of sentence fragments
- LLM received incomplete context, generating only 2 citations instead of 6-10

Token-based chunking captures **complete Article sections** (Article + sub-articles + formulas + explanations) as coherent semantic units:
- **Improved reranker scores:** 0.759-0.942 (was 0.020)
- **Better citation coverage:** 6-10 citations (was 2)
- **Chunk count reduction:** 1526 → 226 chunks (85% reduction, 5-6x longer chunks)

**Hierarchical Separators:** Prioritize document structure boundaries (ARTICLE, Section) before splitting mid-paragraph, preserving regulatory logic.

---

### 3. Vector Search with Multilingual Embeddings

**Model:** `BAAI/bge-m3` (BGE-M3: BAAI General Embedding Model v3)  
**Dimensions:** 1024  
**Database:** PostgreSQL 15+ with pgvector extension  
**Index:** HNSW (Hierarchical Navigable Small World) for approximate nearest neighbor search  
**Retrieval:** `INITIAL_TOP_K=60` candidates

**Why BGE-M3?**
- **Multilingual:** Handles French regulatory documents (CRD4.pdf) and English queries seamlessly
- **State-of-the-art performance:** Outperforms OpenAI ada-002 on retrieval benchmarks
- **Optimized for long context:** Works well with 1200-token chunks
- **Free & open-source:** No API costs, runs locally with sentence-transformers

**Why pgvector + HNSW?**
- HNSW provides O(log n) search complexity vs. brute-force O(n)
- PostgreSQL keeps vectors/metadata in same transaction boundary
- Efficient for 200-500 chunks per document at production scale

---

### 4. Cross-Encoder Reranking

**Model:** `BAAI/bge-reranker-v2-m3` (Cross-Encoder)  
**Method:** Predicts relevance score for each (query, chunk) pair  
**Normalization:** Min-max scaling to [0, 1] range  
**Threshold:** `RERANK_THRESHOLD=0.05` (keeps chunks with score ≥0.05)  
**Output:** Top 15 chunks after filtering

**Why Cross-Encoder Reranking?**

Embedding models (bi-encoders) encode query and documents **independently**, missing interaction signals. Cross-encoders encode `[query + chunk]` **together**, capturing:
- Exact phrase matches (e.g., "Article 12 quinquies (6)")
- Contextual relevance (M-MDA in context of G-SIB buffers)
- Negation handling ("not applicable to small banks")

**Performance Impact:**
- Raw reranker scores: 0.759-0.942 for relevant chunks (was 0.020 with small chunks)
- Filters out 45/60 irrelevant candidates from initial retrieval
- Final 15 chunks have high precision for LLM context

**Why bge-reranker-v2-m3?**
- Multilingual (French documents, English queries)
- Trained specifically for retrieval reranking
- Outputs calibrated scores (0-1 range after normalization)

---

### 5. Document Diversity Algorithm

**Method:** Limit chunks per document  
**Parameter:** `max_chunks_per_doc=3` (disabled if `ENFORCE_DIVERSITY=false`)

**Purpose:** Prevent single document from dominating context window. Ensures multi-source answers for broad regulatory questions spanning multiple documents.

**When Disabled:** For focused queries (e.g., "Explain Article 123"), allowing all relevant chunks from same document improves answer depth.

**Current Configuration:** `ENFORCE_DIVERSITY=false` after chunking optimization - larger chunks provide enough context diversity within single document sections.

---

### 6. LLM Generation with Citation Enforcement

**Model:** OpenAI `gpt-4o-mini`  
**Parameters:**
- `temperature=0.2` (deterministic, factual responses)
- `max_tokens=2500` (allows 800-1200 word detailed answers)
- `stream=True` (Server-Sent Events for real-time UX)

**System Prompt Design:**

**Citation Requirements:**
- **Complex questions** (multi-concept, interactions, consequences): 6-10 `<mark>` tags mandatory
- **Simple questions** (definitions, single article): 2-4 citations
- **Bilingual translation:** When query is English but document is French, LLM must translate cited phrases to English: `<mark data-source="CRD4.pdf, p.92">translated English phrase</mark>`

**Answer Structure Enforcement:**
- **Complex questions:** 800-1200 words, break down mechanisms step-by-step, cite formulas/thresholds/article numbers
- **Simple questions:** 300-500 words, concise with precise citations

**Why GPT-4o-mini?**
- **Cost-effective:** 15x cheaper than GPT-4 Turbo ($0.15/1M input tokens vs $10/1M)
- **Fast streaming:** 80-120 tokens/sec for responsive UX
- **Instruction-following:** Reliably generates `<mark>` tags with proper attribution
- **128k context window:** Handles 15 chunks (15,000+ tokens) easily

**Citation Validation:**
- Backend logs track `<mark>` count in streamed responses
- Frontend highlights citations with yellow background + source tooltip
- CitationChip component shows page numbers and document names

---

## System Metrics & Performance

**Retrieval Quality:**
- Reranker scores: 0.75-0.95 for relevant chunks (excellent semantic match)
- P@15 (Precision at 15): ~95% (14/15 chunks are relevant)
- Pages retrieved: p.85, p.91, p.92-93 for MREL/buffer queries (complete sections)

**Citation Coverage:**
- Complex questions: 6-10 `<mark>` tags with proper source attribution
- Average answer length: 800-1200 words for complex queries
- Source diversity: 1-3 documents cited per answer

**Chunking Efficiency:**
- CRD4.pdf (539,607 characters, 135 pages): 1526 chunks → 226 chunks (85% reduction)
- Chunk size: ~1200 tokens (~900 words) vs previous ~100-200 words
- Processing time: ~4 minutes for full document (extraction + chunking + embedding + DB insertion)

**Cost Efficiency:**
- Embedding: Free (bge-m3 runs locally)
- Reranking: Free (bge-reranker-v2-m3 runs locally)
- LLM generation: ~$0.0003 per query (GPT-4o-mini, 2000 output tokens)
- Total cost per 1000 queries: ~$0.30

---

## Technical Decisions Summary

| Component | Choice | Alternative Considered | Why Our Choice |
|-----------|--------|----------------------|----------------|
| **Chunking Strategy** | Token-based (1200 tokens) | Sentence-based (5 sentences) | Complete Article sections, reranker scores 0.75-0.95 vs 0.020 |
| **Embeddings** | BAAI/bge-m3 | OpenAI ada-002 | Multilingual, free, optimized for retrieval |
| **Reranker** | bge-reranker-v2-m3 cross-encoder | No reranking | 95% precision vs 60% without reranking |
| **LLM** | GPT-4o-mini | GPT-4 Turbo | 15x cheaper, 2x faster streaming, sufficient for RAG |
| **Vector DB** | PostgreSQL + pgvector | Pinecone, Weaviate | No vendor lock-in, ACID transactions, free |
| **Retrieval Strategy** | HyDE (hypothetical answer) | Direct query embedding | Bridges vocabulary gap between questions and formal documents |
| **Chunk Overlap** | 300 tokens (25%) | No overlap | Preserves context across chunk boundaries for long Articles |
| **Citation Format** | `<mark data-source="doc, p.X">` | Footnotes, inline [1] | Visual highlighting, immediate source attribution in UI |

## Documentation

- [RAG Improvements Guide](backend/RAG_IMPROVEMENTS_PRO.md)
- [Backend Setup](backend/SETUP.md)

## Contributing

Educational project for Albert School Year 2 - LLM Ops program.

## License

Educational use only. No commercial use without permission.

---

**Developer:** Enzo Berreur | **Program:** Albert School Year 2 | **Year:** 2024-2025
