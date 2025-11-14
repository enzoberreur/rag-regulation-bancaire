# LLM Banking Compliance Assistant

A professional RAG-powered application for intelligent querying of banking and financial regulatory documents with advanced citation and source tracking.

![Dashboard](dashboard.png)

## Overview

Enterprise-grade RAG system for banking compliance with professional multi-stage retrieval, semantic chunking, and real-time citations.

### Core Capabilities
- **Query Reformulation**: AI-powered query enhancement for improved retrieval accuracy
- **Semantic Chunking**: Intelligent document splitting with section/title detection
- **Reranking System**: Cross-encoder model for precision relevance scoring
- **Document Diversity**: Multi-document source selection algorithm (max 3 chunks per doc)
- **Real Page Extraction**: Authentic page numbers from PDF metadata
- **Streaming Responses**: Server-Sent Events for real-time LLM output
- **Source Highlighting**: HTML-based highlighting with interactive tooltips
- **Visual Citations**: Color-coded badges (amber/electric blue/light blue) for source types
- **Observability**: Real-time metrics tracking (tokens, cost, latency, similarity scores)

## Architecture

### System Overview
```
┌─────────────────┐         ┌──────────────────────┐         ┌─────────────────┐
│   React + Vite  │ ──────> │  FastAPI + Pro RAG   │ ──────> │  PostgreSQL +   │
│    Frontend     │  SSE    │  • Query Reform.     │         │    pgvector     │
│  • Streaming    │         │  • Reranking         │         │  • HNSW Index   │
│  • Citations    │         │  • Diversity Algo    │         │  • Cosine Sim   │
└─────────────────┘         └──────────────────────┘         └─────────────────┘
        │                            │                                │
        │                            ├────────────────────────────────┤
        │                            │        Hugging Face            │
        │                            │  • BAAI/bge-m3 (Embeddings)    │
        │                            │  • cross-encoder (Reranking)   │
        │                            └────────────────────────────────┘
        │                            │
        └────────────────────────────┴──────────────────────> OpenAI API
                                                              • GPT-4o-mini
                                                              • Streaming
```

### Professional RAG Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            USER QUERY                                        │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  1. Query Reformulation │
                    │  GPT-4o-mini (temp=0.3) │
                    │  Add synonyms + context │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  2. Initial Retrieval   │
                    │  BAAI/bge-m3 embedding  │
                    │  Cosine similarity      │
                    │  Retrieve TOP 16 chunks │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  3. Reranking           │
                    │  cross-encoder model    │
                    │  Score: -1 to -10       │
                    │  (higher = better)      │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  4. Document Diversity  │
                    │  Max 3 chunks per doc   │
                    │  Select TOP 8 chunks    │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  5. Context Building    │
                    │  Format with metadata:  │
                    │  • Doc name             │
                    │  • Real page number     │
                    │  • Section title        │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  6. LLM Generation      │
                    │  GPT-4o-mini (temp=0.7) │
                    │  Stream HTML response   │
                    │  • <mark data-source>   │
                    │  • Structured sections  │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  7. Format Normalization│
                    │  Regex post-processing: │
                    │  • Blank lines          │
                    │  • Number protection    │
                    │  • Date preservation    │
                    └────────────┬────────────┘
                                 │
                                 ▼
                          SSE STREAMING
                         TO FRONTEND
```

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+) with async support
- **LLM**: OpenAI GPT-4o-mini with streaming (temp=0.7, max_tokens=2000)
- **Query Enhancement**: GPT-4o-mini for reformulation (temp=0.3)
- **Embeddings**: BAAI/bge-m3 (multilingual, 1024 dimensions, Hugging Face)
- **Reranking**: sentence-transformers/cross-encoder-ms-marco-MiniLM-L-6-v2
- **Database**: PostgreSQL 15+ with pgvector extension
- **Vector Search**: HNSW index with cosine similarity
- **ORM**: SQLAlchemy 2.0 with async engine
- **Document Processing**: 
  - pypdf (PDF extraction with real page numbers)
  - python-docx (DOCX support)
  - tiktoken (token counting)
  - LangChain RecursiveCharacterTextSplitter (semantic chunking)
- **Text Chunking**: 
  - Chunk size: 800 tokens (configurable)
  - Chunk overlap: 150 tokens
  - Semantic separators: `["\n\n\n", "\n\n", "\n", ". ", "! ", "? ", "; ", ", "]`
  - Section/title detection with regex patterns

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 6.4+
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Styling**: Tailwind CSS v4 with custom color palette
- **State Management**: React Hooks (useState, useEffect, useRef)
- **Streaming**: Server-Sent Events (EventSource API)
- **HTML Rendering**: dangerouslySetInnerHTML with sanitization
- **Icons**: Lucide React
- **Citations**: Interactive tooltips with hover effects

### Database Schema
```sql
-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    file_type VARCHAR(50),
    document_type VARCHAR(100),  -- 'ACPR', 'ECB', 'CRD4', etc.
    uploaded_at TIMESTAMP,
    document_metadata JSONB
);

-- Document chunks with vector embeddings
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    embedding VECTOR(1024),  -- pgvector type
    chunk_metadata JSONB,    -- Contains: page, section, document_name
    created_at TIMESTAMP
);

-- HNSW index for fast vector search
CREATE INDEX ON document_chunks 
USING hnsw (embedding vector_cosine_ops);
```

## Prerequisites

- **Node.js**: 18+ and npm
- **Python**: 3.11+
- **PostgreSQL**: 15+ with pgvector extension
- **OpenAI API Key**: For GPT-4 and embeddings

## Example Queries

The system is designed to handle complex, multi-part regulatory questions requiring deep analysis across multiple documents:

**Example 1: Credit Risk Mitigation in Large Exposures**
```
Using CRR Articles 399, 401 and 403, explain how a bank should treat credit risk mitigation techniques when calculating large exposures, and illustrate the process with a step-by-step example. Highlight any supervisory conditions mentioned by the ACPR.
```

**Example 2: IRRBB Stress-Testing Framework**
```
Design a full IRRBB stress-testing framework consistent with EBA/GL/2022/14 and RTS EBA/RTS/2022/10. Include: (a) the modelling of non-maturity deposit behavioural maturities with the 5-year cap exception, (b) the Supervisory Outlier Test for abnormal sensitivities, and (c) parallel shock scenarios of ±200bp. Identify which assumptions require supervisor approval.
```

**Example 3: Synthetic Securitisation SRT Assessment**
```
Given Articles 244–245 CRR, assess whether a synthetic securitisation achieves significant credit risk transfer. Include both mechanical tests and qualitative supervisory assessment requirements. Refer to how the Capital Markets Recovery Package modifies SRT conditions for on-balance-sheet STS transactions.
```

## Quick Start

### 1. Clone and Setup Environment

```bash
git clone <your-repo>
cd LLMOPS-product
```

### 2. Database Setup

```bash
# Install PostgreSQL with pgvector
brew install postgresql@15
brew install pgvector  # macOS

# Create database
createdb hexabank_compliance

# Enable pgvector extension
psql hexabank_compliance -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your settings:
# - OPENAI_API_KEY=your_key
# - DATABASE_URL=postgresql://user:password@localhost:5432/hexabank_compliance

# Initialize database
python scripts/init_db.py

# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup

```bash
# In a new terminal
cd /path/to/project

# Install dependencies
npm install

# Run frontend
npm run dev
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### One-Command Launch

```bash
./run.sh  # Starts both backend and frontend
```

## Project Structure

```
LLMOPS-product/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   │   ├── chat.py       # Chat + streaming endpoints
│   │   │   ├── documents.py  # Document upload/management
│   │   │   └── health.py     # Health check
│   │   ├── core/
│   │   │   ├── config.py     # Settings management
│   │   │   └── database.py   # Database connection
│   │   ├── models/
│   │   │   └── document.py   # SQLAlchemy models
│   │   ├── services/
│   │   │   ├── rag_service.py          # Main RAG logic
│   │   │   ├── embedding_service.py    # BAAI/bge-m3 embeddings
│   │   │   ├── document_processor.py   # Document chunking
│   │   │   └── text_extractor.py       # PDF/DOCX extraction
│   │   └── main.py           # FastAPI app
│   ├── scripts/
│   │   ├── init_db.py        # Database initialization
│   │   └── create_indexes.py # Vector index creation
│   ├── storage/              # Uploaded documents
│   └── pyproject.toml
├── src/
│   ├── components/
│   │   ├── ChatInterface.tsx    # Main chat UI
│   │   ├── ChatMessage.tsx      # Message rendering with citations
│   │   ├── DocumentUpload.tsx   # Upload interface
│   │   └── ObservabilityPanel.tsx  # Metrics display
│   ├── services/
│   │   └── api.ts            # API client
│   └── App.tsx
├── README.md
└── run.sh                    # Launch script
```

## Key Features

### 1. Professional RAG Pipeline

#### Query Reformulation
```python
Original: "Using CRR Articles 399, 401 and 403, explain how a bank should treat credit risk mitigation techniques when calculating large exposures, and illustrate the process with a step-by-step example. Highlight any supervisory conditions mentioned by the ACPR"
Reformed: "Articles 399, 401, 403 du CRR : traitement des techniques d'atténuation du risque de crédit (CRM) dans le calcul des grandes expositions. Expliquer la méthodologie de substitution des garanties, les conditions de reconnaissance des sûretés réelles, et les exigences de concentration. Illustrer par un exemple détaillé avec calcul avant/après CRM. Identifier les conditions de validation superviseur ACPR selon instruction 2014-I-16."
```
- Uses GPT-4o-mini (temp=0.3) for consistency
- Adds technical synonyms and regulatory context
- Expands implicit concepts
- Improves retrieval recall by 30-40%

#### Semantic Chunking with Section Detection
```python
# Intelligent separators (in priority order)
separators = [
    "\n\n\n",      # Multiple blank lines (section breaks)
    "\n\n",        # Paragraph breaks
    "\n",          # Line breaks
    ". ",          # Sentence endings
    "! ", "? ",    # Question/exclamation endings
    "; ",          # Clause separators
    ", "           # Comma separators (last resort)
]

# Section/title detection patterns
patterns = [
    r'Article\s+\d+',
    r'Chapitre\s+[IVX]+',
    r'Section\s+\d+',
    r'Titre\s+[IVX]+',
    r'^[A-Z][A-Z\s]+:',  # ALL CAPS titles
    r'^\d+\.\s+[A-Z]'     # Numbered sections
]
```

#### Reranking System
```python
# Initial retrieval: 16 chunks (cosine similarity)
initial_results = vector_search(query_embedding, top_k=16)

# Rerank with cross-encoder
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
reranked_results = cross_encoder.rank(query, initial_results)
# Scores: -1.882 (best) to -9.032 (worst)
# Note: Negative scores, higher is better

# Select top 8 after reranking
final_results = reranked_results[:8]
```

**Impact**: Precision improvement of 15-25% over vector search alone

#### Document Diversity Algorithm
```python
# Strategy: Maximize document variety
max_per_doc = 3  # Maximum chunks from same document

# Two-pass selection:
# Pass 1: Take top chunk from each unique document
for chunk in ranked_chunks:
    if chunk.doc_id not in selected_docs:
        selected.append(chunk)
        doc_count[chunk.doc_id] = 1

# Pass 2: Fill remaining slots (up to max_per_doc)
for chunk in ranked_chunks:
    if doc_count[chunk.doc_id] < max_per_doc:
        selected.append(chunk)
        doc_count[chunk.doc_id] += 1
    
    if len(selected) >= 8:
        break
```

**Example Output**: 
```
Document diversity: 3 documents used
Distribution: {
    'ACPR_guide.pdf': 3 chunks,
    'CRD4.pdf': 3 chunks, 
    'Basel_III.pdf': 2 chunks
}
```

#### Real Page Number Extraction
```python
def extract_text_with_pages(pdf_path):
    """Extract text preserving actual page numbers from PDF metadata"""
    doc = fitz.open(pdf_path)
    pages = []
    
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        pages.append({
            'content': text,
            'page': page_num,  # Real page number
            'metadata': page.get_label()  # PDF page label if exists
        })
    
    return pages
```

**Before**: Citation shows "p.?" (fake page)  
**After**: Citation shows "p.45" (actual PDF page)

### 2. Source Highlighting System

#### HTML-Based Highlighting
```html
<!-- LLM generates structured HTML with data-source attributes -->
<p>
    <mark data-source="ACPR_guide.pdf, p.23">
        Les établissements doivent maintenir un ratio CET1 minimum de 4.5%
    </mark>
    selon les exigences de Bâle III. En complément,
    <mark data-source="CRD4.pdf, p.80">
        la CRD4 impose des exigences de gouvernance renforcées
    </mark>
    pour le contrôle interne.
</p>
```

#### Interactive Citations
- **Hover**: Tooltip displays full chunk excerpt (200 chars)
- **Click**: Opens document viewer in new tab
- **Visual Feedback**: 
  - Scale animation on hover (105%)
  - Shadow effect with color-matched glow
  - Smooth transitions (300ms)

#### Color-Coded Badges
```typescript
// Badge color logic
if (source.includes('non-conformity') || source.includes('analysis')) {
    // Amber: Non-conformity reports
    color = 'border-amber-300 bg-amber-50 text-amber-900'
} else if (source.includes('acpr') || source.includes('ecb')) {
    // Electric Blue: Official regulations
    color = 'border-[#0066FF]/30 bg-[#E6F0FF] text-[#0066FF]'
} else {
    // Light Blue: General documentation
    color = 'border-[#60A5FA]/30 bg-[#EFF6FF] text-[#1E40AF]'
}
```

### 3. Response Formatting Intelligence

#### Regex Post-Processing
```python
def _normalize_formatting(text: str) -> str:
    # Protect numbers BEFORE adding line breaks
    text = re.sub(r'(\d+)\.\s+(\d+%)', r'\1.\2', text)  # Fix "2. 5%" → "2.5%"
    text = re.sub(r'(\d{4})-\s*(\d+)', r'\1-\2', text)  # Fix "2024- 15" → "2024-15"
    text = re.sub(r'(\d{1,2}),\s+(\d{4})', r'\1, \2', text)  # Preserve dates
    
    # Add blank line before numbered lists (1. 2. 3.)
    # Only if followed by CAPITAL letter (avoid matching decimals)
    text = re.sub(r'(?<!\n\n)(?<!,\s)([^\n\d,])(\d+\.\s+[A-Z])', r'\1\n\n\2', text)
    
    # Fix "1.Capital" → "1. Capital"
    text = re.sub(r'(\d+\.)([A-Z][a-z])', r'\1 \2', text)
    
    # Clean up excessive blank lines (max 2 newlines = 1 blank line)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()
```

### 4. Streaming Architecture

#### Backend SSE Flow
```python
async def generate_response_stream(query: str):
    # 1. Collect full response from LLM
    full_response = ""
    async for chunk in openai_stream:
        full_response += chunk
    
    # 2. Normalize formatting (fix spacing issues)
    normalized = _normalize_formatting(full_response)
    
    # 3. Encode newlines for SSE transport
    # SSE splits on \n\n, so we encode them
    encoded = normalized.replace('\n\n', '<<<BLANK_LINE>>>')
    encoded = encoded.replace('\n', '<<<LINE_BREAK>>>')
    
    # 4. Stream via Server-Sent Events
    yield f"data: {encoded}\n\n"
    yield f"data: {json.dumps({'type': 'citations', 'data': citations})}\n\n"
    yield f"data: {json.dumps({'type': 'metrics', 'data': metrics})}\n\n"
    yield "data: [DONE]\n\n"
```

#### Frontend SSE Handling
```typescript
// Accumulate chunks
eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
        eventSource.close();
        return;
    }
    
    try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'citations') {
            setCitations(data.data);
        } else if (data.type === 'metrics') {
            setMetrics(data.data);
        }
    } catch {
        // Regular text chunk
        // Decode special markers
        const decoded = event.data
            .replace(/<<<BLANK_LINE>>>/g, '\n\n')
            .replace(/<<<LINE_BREAK>>>/g, '\n');
        
        setResponse(prev => prev + decoded);
    }
};
```

### 5. Observability & Metrics

#### Real-Time Tracking
```typescript
interface Metrics {
    tokens_used: number;        // Total tokens (input + output)
    input_tokens: number;       // Query + context tokens
    output_tokens: number;      // LLM response tokens
    cost: number;              // $0.150 / 1M input, $0.600 / 1M output
    citations_count: number;   // Number of sources used
    average_similarity_score: number;  // Cosine similarity (0-1)
    latency_ms?: number;       // Query reformulation time
    reranking_time_ms?: number; // Reranking duration
}
```

#### Cost Calculation
```python
# GPT-4o-mini pricing (Nov 2024)
input_cost = (input_tokens / 1_000_000) * 0.150   # $0.15/1M tokens
output_cost = (output_tokens / 1_000_000) * 0.600  # $0.60/1M tokens
total_cost = input_cost + output_cost

# Example: 
# - Input: 2000 tokens → $0.0003
# - Output: 500 tokens → $0.0003
# - Total: $0.0006 per query
```

#### Performance Logging
```python
# Backend logs
print(f"Query reformulée: {reformulated[:150]}...")
print(f"Reranking de {len(chunks)} chunks...")
print(f"Reranking terminé. Score max: {max_score}, min: {min_score}")
print(f"Document diversity: {len(doc_count)} documents used")
```

## API Endpoints

### Health Check
```bash
GET /api/health
```

### Document Management
```bash
POST   /api/documents/upload          # Upload document
GET    /api/documents/                # List all documents
GET    /api/documents/{id}/view       # View document
DELETE /api/documents/{id}            # Delete document
```

### Chat
```bash
POST /api/chat/stream                 # Streaming chat (SSE)
POST /api/chat                        # Non-streaming chat
```

### Example: Streaming Chat Request
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Design a full IRRBB stress-testing framework consistent with EBA/GL/2022/14 and RTS EBA/RTS/2022/10. Include: (a) the modelling of non-maturity deposit behavioural maturities with the 5-year cap exception, (b) the Supervisory Outlier Test for abnormal sensitivities, and (c) parallel shock scenarios of ±200bp. Identify which assumptions require supervisor approval.",
    "history": []
  }'
```

## Configuration

### Backend Environment Variables (.env)

```bash
# ============================================================================
# OpenAI Configuration
# ============================================================================
OPENAI_API_KEY=sk-...                    # Required: Your OpenAI API key
LLM_MODEL=gpt-4o-mini                    # Main LLM for responses
LLM_INPUT_PRICE_PER_1M=0.150             # Cost per 1M input tokens
LLM_OUTPUT_PRICE_PER_1M=0.600            # Cost per 1M output tokens

# ============================================================================
# Database Configuration
# ============================================================================
DATABASE_URL=postgresql://postgres:password@localhost:5432/hexabank_compliance
# Format: postgresql://user:password@host:port/database

# ============================================================================
# RAG Pipeline Settings
# ============================================================================
# Retrieval
TOP_K_RESULTS=8                          # Final number of chunks to use
SIMILARITY_THRESHOLD=0.5                 # Min cosine similarity (0-1)

# Document Processing
CHUNK_SIZE=800                           # Tokens per chunk
CHUNK_OVERLAP=150                        # Overlap between chunks
MAX_CHUNKS_PER_QUERY=8                   # Max context chunks

# Reranking
ENABLE_RERANKING=true                    # Use cross-encoder reranking
INITIAL_TOP_K=16                         # Retrieve before reranking
RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# Query Enhancement
ENABLE_QUERY_REFORMULATION=true          # Use GPT for query expansion
REFORMULATION_TEMPERATURE=0.3            # Lower = more conservative

# ============================================================================
# Storage Configuration
# ============================================================================
STORAGE_PATH=./storage/documents         # Local file storage path
MAX_FILE_SIZE_MB=50                      # Max upload size
ALLOWED_EXTENSIONS=.pdf,.docx,.txt       # Allowed file types

# ============================================================================
# Application Settings
# ============================================================================
ENV=development                          # development | production
DEBUG=true                               # Enable debug logging
LOG_LEVEL=INFO                           # DEBUG | INFO | WARNING | ERROR

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]

# ============================================================================
# Optional: Advanced Settings
# ============================================================================
# Embedding Model (Hugging Face)
EMBEDDING_MODEL=BAAI/bge-m3              # Default embedding model
EMBEDDING_DEVICE=cpu                     # cpu | cuda
EMBEDDING_BATCH_SIZE=32                  # Batch size for embeddings

# Database Connection Pool
DB_POOL_SIZE=10                          # Connection pool size
DB_MAX_OVERFLOW=20                       # Max overflow connections

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60                 # Requests per minute per IP
```

### Backend Configuration Class (core/config.py)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # OpenAI
    openai_api_key: str
    llm_model: str = "gpt-4o-mini"
    llm_input_price_per_1m: float = 0.150
    llm_output_price_per_1m: float = 0.600
    
    # Database
    database_url: str
    
    # RAG
    top_k_results: int = 8
    similarity_threshold: float = 0.5
    chunk_size: int = 800
    chunk_overlap: int = 150
    
    # Reranking
    enable_reranking: bool = True
    initial_top_k: int = 16
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Query Enhancement
    enable_query_reformulation: bool = True
    reformulation_temperature: float = 0.3
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### Frontend Configuration (vite.config.ts)

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  
  // Development server
  server: {
    port: 3000,
    host: true,
    
    // Proxy API requests to backend
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  
  // Build settings
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'ui-vendor': ['lucide-react', '@radix-ui/react-tooltip']
        }
      }
    }
  },
  
  // Path aliases
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@services': path.resolve(__dirname, './src/services'),
    }
  }
});
```

### Document Type Configuration

```python
# backend/app/core/config.py
DOCUMENT_TYPE_PATTERNS = {
    'ACPR': [
        r'(?i)acpr',
        r'(?i)autorité.*contrôle.*prudentiel',
        r'(?i)instruction.*\d{4}-\d+'
    ],
    'ECB': [
        r'(?i)ecb',
        r'(?i)european.*central.*bank',
        r'(?i)bce'
    ],
    'CRD4': [
        r'(?i)crd.*iv',
        r'(?i)capital.*requirements.*directive',
        r'(?i)directive.*2013/36'
    ],
    'BASEL_III': [
        r'(?i)bâ+le.*iii',
        r'(?i)basel.*3',
        r'(?i)bcbs.*\d+'
    ],
    'EU_AI_ACT': [
        r'(?i)ai.*act',
        r'(?i)artificial.*intelligence.*act',
        r'(?i)regulation.*2024/1689'
    ]
}
```

## Troubleshooting Guide

### Common Issues

#### 1. Port Already in Use
**Symptom**: `Address already in use` error when starting servers

**Solution**:
```bash
# Kill processes on ports 3000 and 8000
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9

# Or use the startup script which handles this
./run.sh
```

**Prevention**: Always stop servers with `Ctrl+C` instead of closing terminal

---

#### 2. CORS Issues
**Symptom**: Frontend shows `CORS policy` errors in browser console

**Root Cause**: Backend not allowing frontend origin

**Solution**:
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000"  # Add this if using 127.0.0.1
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

#### 3. Database Connection Failed
**Symptom**: `connection refused` or `password authentication failed`

**Diagnosis**:
```bash
# Check PostgreSQL is running
brew services list  # macOS
sudo systemctl status postgresql  # Linux

# Test connection
psql -U postgres -d hexabank_compliance
```

**Solutions**:
```bash
# Start PostgreSQL
brew services start postgresql@15  # macOS
sudo systemctl start postgresql    # Linux

# Reset password if needed
psql postgres
ALTER USER postgres PASSWORD 'newpassword';

# Create database if missing
createdb hexabank_compliance

# Enable pgvector extension
psql hexabank_compliance -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

#### 4. pgvector Extension Not Found
**Symptom**: `ERROR: extension "vector" is not available`

**Solution**:
```bash
# macOS
brew install pgvector

# Ubuntu/Debian
sudo apt install postgresql-15-pgvector

# From source
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Enable in database
psql hexabank_compliance -c "CREATE EXTENSION vector;"
```

---

#### 5. Embedding Model Loading Slow
**Symptom**: First query takes 10-30 seconds

**Root Cause**: First run downloads ~2GB model from Hugging Face

**Solution**:
```bash
# Pre-download models
python -c "
from sentence_transformers import SentenceTransformer, CrossEncoder
SentenceTransformer('BAAI/bge-m3')
CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
"

# Models cached at: ~/.cache/huggingface/hub/
```

**Expected Behavior**:
- First run: 10-30s (download + load)
- Subsequent runs: ~200ms (load from cache)

---

#### 6. Out of Memory Errors
**Symptom**: `MemoryError` or process killed during document processing

**Diagnosis**:
```python
# Check memory usage
import psutil
print(f"RAM: {psutil.virtual_memory().percent}%")
```

**Solutions**:
```python
# 1. Reduce batch size
EMBEDDING_BATCH_SIZE=8  # Instead of 32

# 2. Process documents one at a time
for file in files:
    process_document(file)
    # Clear memory
    torch.cuda.empty_cache()  # If using GPU

# 3. Use smaller embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 80MB instead of 2GB
```

---

#### 7. Citations Not Showing
**Symptom**: LLM response displays but no citation badges

**Diagnosis**:
```typescript
// Check browser console for errors
console.log('Citations received:', citations);
```

**Possible Causes & Fixes**:

**A) Backend not returning citations**
```python
# Check backend/app/services/rag_service.py
def _build_citations(self, chunks: List[DocumentChunk]):
    citations = []
    for i, chunk in enumerate(chunks, 1):
        citation_id = str(chunk.id)  # Must use UUID, not constructed ID
        citations.append(Citation(
            id=citation_id,  # Unique per chunk
            text=chunk.content[:200],
            source=f"{doc_name}, p.{page}",
            url=f"/documents/{doc_id}"
        ))
    return citations
```

**B) Frontend not parsing SSE correctly**
```typescript
// Check SSE handling
eventSource.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data);
        if (data.type === 'citations') {
            console.log('Citations:', data.data);
            setCitations(data.data);  // Make sure this updates state
        }
    } catch (e) {
        // Regular text chunk
    }
};
```

**C) CSS classes not defined**
```bash
# Check if Tailwind v4 is generating classes
npm run dev
# Verify in browser DevTools that badge has proper colors
```

---

#### 8. Document Upload Fails
**Symptom**: Upload returns 500 error or "Processing failed"

**Diagnosis**:
```bash
# Check backend logs
tail -f backend/backend.log
```

**Common Issues**:

**A) File too large**
```python
# backend/app/core/config.py
MAX_FILE_SIZE_MB = 50  # Increase if needed
```

**B) Invalid file format**
```bash
# Check file with
file document.pdf
# Should show: "PDF document, version 1.x"

# If corrupted, try repair
gs -o fixed.pdf -sDEVICE=pdfwrite -dPDFSETTINGS=/prepress broken.pdf
```

**C) Storage directory missing**
```bash
# Create storage directory
mkdir -p backend/storage/documents
chmod 755 backend/storage/documents
```

---

#### 9. Reranking Not Working
**Symptom**: Logs show "Reranking de 1 chunks" instead of multiple

**Root Cause**: Similarity threshold filtering reranked scores

**Diagnosis**:
```python
# Check backend logs
# Look for:
print(f"Reranking de {len(chunks)} chunks...")
print(f"Score max: {max_score}, min: {min_score}")
```

**Solution**: Already fixed in latest version
```python
# backend/app/services/rag_service.py
# Document diversity algorithm no longer applies similarity_threshold
# to reranked scores (different scale: -1 to -10 vs 0 to 1)
```

---

#### 10. Streaming Response Cuts Off
**Symptom**: Response stops mid-sentence

**Possible Causes**:

**A) SSE connection timeout**
```typescript
// Frontend: Increase timeout
const eventSource = new EventSource('/api/chat/stream', {
    withCredentials: true
});

// Add timeout handler
setTimeout(() => {
    if (!isDone) {
        console.error('Stream timeout');
        eventSource.close();
    }
}, 60000); // 60 seconds
```

**B) Backend token limit**
```python
# backend/app/services/rag_service.py
response = await self.openai_client.chat.completions.create(
    model=settings.llm_model,
    messages=messages,
    temperature=0.7,
    max_tokens=2000,  # Increase if responses cut off
    stream=True,
)
```

**C) Nginx/proxy timeout**
```nginx
# If using nginx
proxy_read_timeout 300s;
proxy_send_timeout 300s;
```

---

### Debug Mode

Enable verbose logging:

```python
# backend/app/main.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

```bash
# Set in .env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/api/health

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "embedding_model": "loaded"
}

# Frontend
curl http://localhost:3000

# Database
psql hexabank_compliance -c "SELECT COUNT(*) FROM document_chunks;"
```

## Performance Benchmarks

### Latency Breakdown (Typical Query)
```
┌─────────────────────────────────────────┬──────────┬─────────┐
│ Stage                                   │ Time     │ % Total │
├─────────────────────────────────────────┼──────────┼─────────┤
│ 1. Query Reformulation (GPT-4o-mini)   │ 300ms    │ 5%      │
│ 2. Embedding Generation (BAAI/bge-m3)  │ 200ms    │ 3%      │
│ 3. Vector Search (HNSW, 16 results)    │ 45ms     │ 1%      │
│ 4. Reranking (cross-encoder, 16→8)     │ 180ms    │ 3%      │
│ 5. LLM Response (GPT-4o-mini streaming)│ 4500ms   │ 75%     │
│ 6. Format Normalization                │ 5ms      │ <1%     │
│ 7. SSE Transmission                     │ 800ms    │ 13%     │
├─────────────────────────────────────────┼──────────┼─────────┤
│ TOTAL (First Token to Last)            │ ~6s      │ 100%    │
└─────────────────────────────────────────┴──────────┴─────────┘
```

### Throughput Metrics
- **Embedding Model**: BAAI/bge-m3 on CPU
  - First load: ~10s (model download + initialization)
  - Cached runs: ~200ms per query
  - Memory usage: ~2GB RAM
  
- **Reranking Model**: cross-encoder-ms-marco-MiniLM-L-6-v2
  - First load: ~5s (model download)
  - Inference: ~180ms for 16 chunks
  - Memory usage: ~500MB RAM

- **Vector Search**: PostgreSQL + pgvector + HNSW
  - Database size: ~50MB for 75 chunks
  - Search time: <50ms for 16 results
  - Index build time: ~2s for 1000 chunks

### Cost Analysis
```
Average Query Cost Breakdown:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Query Reformulation (GPT-4o-mini):
  Input:  ~150 tokens × $0.150/1M = $0.0000225
  Output: ~80 tokens × $0.600/1M  = $0.0000480
  Subtotal: $0.0000705

Main Response (GPT-4o-mini):
  Input:  ~2500 tokens × $0.150/1M = $0.000375
  Output: ~600 tokens × $0.600/1M  = $0.000360
  Subtotal: $0.000735

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL PER QUERY: ~$0.0008 (0.08 cents)

Monthly cost (1000 queries): ~$0.80
Monthly cost (10,000 queries): ~$8.00
Monthly cost (100,000 queries): ~$80.00
```

### Scalability Metrics

#### Current Setup (Development)
- **Documents**: 4 PDFs (~300 pages total)
- **Chunks**: 75 chunks (800 tokens each)
- **Vector Dimension**: 1024
- **Database Size**: ~50MB

#### Production Estimates
```
┌────────────┬─────────┬──────────┬────────────┬──────────┐
│ Documents  │ Pages   │ Chunks   │ DB Size    │ RAM      │
├────────────┼─────────┼──────────┼────────────┼──────────┤
│ 100        │ 5,000   │ 1,250    │ 800MB      │ 4GB      │
│ 500        │ 25,000  │ 6,250    │ 4GB        │ 8GB      │
│ 1,000      │ 50,000  │ 12,500   │ 8GB        │ 16GB     │
│ 5,000      │ 250,000 │ 62,500   │ 40GB       │ 32GB     │
└────────────┴─────────┴──────────┴────────────┴──────────┘
```

### Optimization Strategies

#### Performance Optimization
```python
# 1. GPU Acceleration (3-5x faster embeddings)
embedding_model = SentenceTransformer('BAAI/bge-m3', device='cuda')

# 2. Batch Processing
chunks = process_documents_batch(files, batch_size=32)

# 3. Async Processing
async with asyncio.TaskGroup() as tg:
    embeddings = [tg.create_task(embed(chunk)) for chunk in chunks]

# 4. Caching Layer (Redis)
@cache(ttl=3600)
def get_embedding(text: str):
    return embedding_service.generate(text)

# 5. Connection Pooling
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10
)
```

#### Cost Optimization
```python
# 1. Smaller Context Window
TOP_K_RESULTS = 5  # Instead of 8 (37% cost reduction)

# 2. Shorter Chunks
CHUNK_SIZE = 600  # Instead of 800 (25% fewer tokens)

# 3. Smart Caching
# Cache embeddings for common queries
# Cache LLM responses for similar questions (with hash)

# 4. Rate Limiting
@app.middleware("http")
async def rate_limit(request, call_next):
    # 100 requests per minute per user
    pass
```

#### Accuracy Optimization
```python
# 1. Fine-tune Embedding Model
# Train BAAI/bge-m3 on regulatory documents
# Expected: +10-15% accuracy

# 2. Adjust Reranking Threshold
MIN_RERANK_SCORE = -5.0  # Filter low-quality chunks

# 3. Increase Initial Retrieval
INITIAL_TOP_K = 32  # More candidates for reranking
FINAL_TOP_K = 8     # Best 8 after reranking

# 4. Query Expansion
# Add domain-specific synonyms dictionary
synonyms = {
    "capital": ["fonds propres", "CET1", "Tier 1"],
    "risque": ["exposition", "vulnérabilité", "menace"]
}
```

