# HexaBank Compliance Assistant

An AI-powered RAG (Retrieval-Augmented Generation) application that helps compliance officers at HexaBank interpret and analyze regulatory documents from ACPR, ECB, and EU AI Act.

## 🎯 Overview

The HexaBank Compliance Assistant is a full-stack application that combines:
- **Document Processing**: Upload and process PDF, DOCX, and TXT regulatory documents
- **Vector Search**: Semantic search using BAAI/bge-m3 embeddings and PostgreSQL with pgvector
- **LLM Integration**: OpenAI GPT-4 for intelligent question answering with streaming responses
- **Citation System**: Automatic source citation for transparency and compliance validation

## 🏗️ Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   React + Vite  │ ──────> │  FastAPI + RAG  │ ──────> │  PostgreSQL +   │
│    Frontend     │  SSE    │     Backend     │         │    pgvector     │
└─────────────────┘         └─────────────────┘         └─────────────────┘
        │                            │
        │                            │
        └────────────────────────────┴───────────────────> OpenAI API
                                                           (GPT-4 + Embeddings)
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **LLM**: OpenAI GPT-4 with streaming support
- **Embeddings**: BAAI/bge-m3 (multilingual, 1024 dimensions)
- **Database**: PostgreSQL 15+ with pgvector extension
- **ORM**: SQLAlchemy 2.0
- **Document Processing**: PyMuPDF, python-docx, tiktoken
- **Async**: AsyncIO with OpenAI async client

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Styling**: Tailwind CSS
- **State Management**: React Hooks
- **Streaming**: Server-Sent Events (SSE)

### Database Schema
- **Documents**: Stores uploaded files metadata
- **DocumentChunks**: Text chunks with vector embeddings (1024-dim)
- **Indexes**: HNSW index for fast vector similarity search

## 📋 Prerequisites

- **Node.js**: 18+ and npm
- **Python**: 3.11+
- **PostgreSQL**: 15+ with pgvector extension
- **OpenAI API Key**: For GPT-4 and embeddings

## 🚀 Quick Start

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

## 📁 Project Structure

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

## 🔑 Key Features

### 1. Document Processing Pipeline
```
Upload → Text Extraction → Chunking (500 tokens) → Embedding → Vector Storage
```

### 2. RAG Query Flow
```
User Query → Embedding → Vector Search (top 5) → Context Building → LLM → Streaming Response
```

### 3. Response Formatting
The system uses intelligent regex-based post-processing to ensure:
- ✅ Blank lines before numbered lists (1., 2., 3.)
- ✅ Proper spacing for section headers
- ✅ Protected decimal numbers (2.5%) and dates (December 31, 2025)
- ✅ Line breaks between sentences
- ✅ Preserved bullet points formatting

### 4. Streaming Architecture
- **Backend**: Collects full LLM response → Normalizes formatting → Encodes newlines → Streams via SSE
- **Frontend**: Accumulates chunks → Decodes newlines → Renders with proper formatting

### 5. Cost & Performance Tracking
Real-time metrics for each query:
- Token usage (input/output)
- API cost calculation
- Similarity scores
- Latency measurement

## 🧪 API Endpoints

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
    "message": "What are the key requirements of ACPR Regulation 2024-15?",
    "history": []
  }'
```

## 🔧 Configuration

### Backend (.env)
```bash
# OpenAI
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-3-large

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/hexabank_compliance

# RAG Settings
TOP_K_RESULTS=5
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Storage
STORAGE_PATH=./storage/documents
```

### Frontend (vite.config.ts)
```typescript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill processes on ports 3000 and 8000
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

### CORS Issues
Make sure `localhost:3000` and `localhost:3001` are in the CORS allowed origins in `backend/app/main.py`.

### Database Connection Failed
```bash
# Check PostgreSQL is running
brew services list

# Restart if needed
brew services restart postgresql@15
```

### Embedding Model Loading Slow
First run downloads ~2GB model from Hugging Face. Subsequent runs use cached model.

## 📊 Performance Considerations

- **Embedding**: ~200ms per query (BAAI/bge-m3 on CPU)
- **Vector Search**: <50ms with HNSW index (5k chunks)
- **LLM Response**: 2-5s streaming (depends on context size)
- **Total Latency**: ~3-6s for typical query

### Optimization Tips
1. Use GPU for embeddings (3-5x faster)
2. Adjust `CHUNK_SIZE` based on document type
3. Tune `TOP_K_RESULTS` for accuracy vs speed
4. Use smaller embedding model for faster inference

## 🔒 Security Notes

- API keys stored in `.env` (never commit!)
- CORS configured for development (restrict in production)
- SQL injection protected by SQLAlchemy ORM
- File uploads validated by extension
- No authentication implemented (add for production)

## 📈 Future Enhancements

- [ ] Multi-user authentication (JWT)
- [ ] Document version control
- [ ] Advanced filtering (date, document type)
- [ ] Export chat history
- [ ] Fine-tuned embedding model
- [ ] Caching layer (Redis)
- [ ] Kubernetes deployment
- [ ] Monitoring with Prometheus/Grafana

## 🤝 Contributing

This is a student project for Albert School. Contributions welcome!

## 📄 License

Educational project - Albert School Year 2

## 🙋 Support

For issues or questions, please contact the development team.

---

**Built with ❤️ at Albert School**