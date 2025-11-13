# 🚀 Setup Guide - New Machine

## 📋 Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 14+ with pgvector extension
- OpenAI API key

---

## 🔧 Step 1: PostgreSQL Setup

### Install PostgreSQL with pgvector

```bash
# macOS
brew install postgresql@14
brew services start postgresql@14

# Install pgvector extension
brew install pgvector

# Connect to PostgreSQL
psql postgres

# Create database and enable pgvector
CREATE DATABASE llmops_db;
\c llmops_db
CREATE EXTENSION vector;
\q
```

### Verify installation

```bash
psql llmops_db -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
# Should show: vector | 0.7.0 or similar
```

---

## 🐍 Step 2: Python Backend Setup

### 1. Create virtual environment

```bash
cd /Users/enzoberreur/Documents/Albert\ School/Year\ 2/LLMOPS-product

# Create venv
python3.12 -m venv .venv

# Activate
source .venv/bin/activate
```

### 2. Install dependencies

```bash
# Install Python packages
pip install --upgrade pip
pip install -r backend/requirements.txt

# Or use poetry if available
cd backend
poetry install
```

### 3. Configure environment

```bash
cd backend

# Copy example env file
cp env.example .env

# Edit .env file
nano .env
```

**Required variables in `.env`:**

```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/llmops_db

# OpenAI (GET YOUR KEY FROM: https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx

# Models
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o
LLM_INPUT_PRICE_PER_1M=2.5
LLM_OUTPUT_PRICE_PER_1M=10.0

# RAG Config
TOP_K_RESULTS=8
CHUNK_SIZE=1050
CHUNK_OVERLAP=200

# App
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
STORAGE_PATH=./storage/documents
```

### 4. Initialize database

```bash
cd backend

# Create tables
python scripts/init_db.py

# Create vector indexes (important for performance!)
python scripts/create_indexes.py
```

---

## 📚 Step 3: Upload Documents

### Upload all documents from data folder

```bash
cd backend

# Upload all PDFs from ../data/
python scripts/upload_all_documents.py

# Or upload from root directory
cd ..
python upload_all.py
```

This will:
1. Extract text from PDFs (with real page numbers!)
2. Chunk documents intelligently (800-1000 tokens)
3. Generate embeddings (OpenAI text-embedding-3-small)
4. Store in PostgreSQL with metadata

**Expected output:**
```
📁 Uploading: ACPR.pdf
   ⏳ Extracting text with page info...
   ✅ Extracted 125,432 characters from 45 pages
   ⏳ Splitting into chunks...
   ✅ Created 87 chunks
   ⏳ Generating embeddings (batch size: 32)...
   ✅ Generated 87 embeddings
   ✅ Document processed: ACPR.pdf (87 chunks)

📊 TOTAL: 8 documents, 642 chunks uploaded
```

---

## 🎨 Step 4: Frontend Setup

### 1. Install Node dependencies

```bash
cd /Users/enzoberreur/Documents/Albert\ School/Year\ 2/LLMOPS-product

# Install packages
npm install
```

### 2. Verify Vite config

```bash
cat vite.config.ts
```

Should have proxy to backend:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

---

## ▶️ Step 5: Run the Application

### Terminal 1: Backend

```bash
cd /Users/enzoberreur/Documents/Albert\ School/Year\ 2/LLMOPS-product
source .venv/bin/activate
cd backend

# Run FastAPI server
python run.py

# Or use uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
🔄 Chargement du modèle de reranking...
✅ Modèle de reranking chargé
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Terminal 2: Frontend

```bash
cd /Users/enzoberreur/Documents/Albert\ School/Year\ 2/LLMOPS-product

# Run Vite dev server
npm run dev
```

**Expected output:**
```
  VITE v6.4.0  ready in 523 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.1.x:5173/
  ➜  press h + enter to show help
```

### Open browser

Navigate to: **http://localhost:5173/**

---

## ✅ Step 6: Verify Everything Works

### 1. Check backend health

```bash
curl http://localhost:8000/api/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "documents_count": 8
}
```

### 2. Check documents in database

```bash
source .venv/bin/activate
cd backend

python -c "
from app.core.database import SessionLocal
from app.models.document import Document, DocumentChunk

db = SessionLocal()
doc_count = db.query(Document).count()
chunk_count = db.query(DocumentChunk).count()
print(f'✅ Documents: {doc_count}')
print(f'✅ Chunks: {chunk_count}')
print(f'✅ Average: {chunk_count/doc_count:.1f} chunks/doc')
db.close()
"
```

### 3. Test a question

In the frontend, click one of the example prompts or type:

```
What are the main Basel III requirements for the CET1 capital ratio?
```

Should return a detailed answer with citations from your documents!

---

## 🐛 Troubleshooting

### PostgreSQL connection error

```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Restart if needed
brew services restart postgresql@14

# Check connection
psql llmops_db -c "SELECT 1;"
```

### pgvector not found

```bash
# Install pgvector
brew install pgvector

# Reconnect and enable
psql llmops_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### No documents in frontend

```bash
# Re-upload documents
cd backend
python scripts/upload_all_documents.py

# Check count
python -c "from app.core.database import SessionLocal; from app.models.document import Document; db = SessionLocal(); print(db.query(Document).count()); db.close()"
```

### Backend errors about embeddings

Check that `OPENAI_API_KEY` in `.env` is valid:

```bash
# Test OpenAI connection
python -c "
from openai import OpenAI
import os
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
print('✅ OpenAI API key is valid')
"
```

### Frontend doesn't connect to backend

1. Check backend is running on port 8000
2. Check vite.config.ts has proxy
3. Check browser console for errors

---

## 📊 Database Schema

```sql
-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    file_path TEXT,
    file_size INTEGER,
    file_type VARCHAR(50),
    document_type VARCHAR(100),
    uploaded_at TIMESTAMP,
    document_metadata JSONB
);

-- Document chunks table
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER,
    content TEXT,
    token_count INTEGER,
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small
    chunk_metadata JSONB,
    created_at TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## 🎯 Quick Test Commands

```bash
# Full pipeline test
cd backend

# 1. Check DB
python -c "from app.core.database import engine; print(engine.url)"

# 2. Count documents
python -c "from app.core.database import SessionLocal; from app.models.document import Document; db = SessionLocal(); print(f'Documents: {db.query(Document).count()}'); db.close()"

# 3. Test embeddings
python -c "from app.services.embedding_service import EmbeddingService; import asyncio; svc = EmbeddingService(); print(asyncio.run(svc.generate_embedding('test'))[:5])"

# 4. Search in chunks
python scripts/search_in_chunks.py "Basel III"

# 5. Test RAG improvements
python scripts/test_rag_improvements.py
```

---

## 📦 Documents You Have

From your `data/` folder:

- ✅ **ACPR.pdf** - French banking regulator guidelines
- ✅ **AI ACT.pdf** - EU AI regulation
- ✅ **APPLICATION CRD3 ET 4.pdf** - Capital Requirements Directive
- ✅ **BALE 3.pdf** - Basel III framework
- ✅ **CRD4.pdf** - Full CRD4 regulation
- ✅ **CYBER.pdf** - Cybersecurity requirements
- ✅ **KYC.pdf** - Know Your Customer guidelines
- ✅ **LCB FT.pdf** - Anti-money laundering

---

## 🚀 Next Steps

1. ✅ Setup complete? Test with the example prompts in the UI
2. 📊 Check metrics in the Observability panel (right side)
3. 📄 Upload more documents if needed (Upload button in chat)
4. 🔍 Use `search_in_chunks.py` to verify citations
5. 📈 Monitor `backend.log` for debugging

---

**Need help? Check:**
- `README.md` - Full documentation
- `RAG_AUDIT_ET_AMELIORATIONS.md` - RAG improvements details
- `GUIDE_AMELIORATIONS_RAG.md` - Implementation guide
- Backend logs: `backend/backend.log`
