# LLMOPS Product Backend

Backend RAG pour l'assistant de conformité réglementaire HexaBank.

## Stack Technique

- **Framework**: FastAPI
- **Base de données**: PostgreSQL + pgvector
- **Embeddings**: BAAI/bge-m3 (1024 dimensions)
- **LLM**: OpenAI GPT-4o-mini
- **Chunking**: LangChain (900-1200 tokens)
- **Gestionnaire de paquets**: uv

## Installation

### Prérequis

- Python 3.11+
- PostgreSQL avec pgvector installé
- [uv](https://github.com/astral-sh/uv) installé

### Installation des dépendances

```bash
# Installer uv si ce n'est pas déjà fait
curl -LsSf https://astral.sh/uv/install.sh | sh

# Installer les dépendances
uv sync
```

### Configuration

1. Copier le fichier `.env.example` vers `.env`:
```bash
cp .env.example .env
```

2. Modifier `.env` avec vos configurations:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/llmops_db
OPENAI_API_KEY=your_openai_api_key_here
```

### Initialisation de la base de données

```bash
# Créer la base de données PostgreSQL
createdb llmops_db

# Initialiser les tables et pgvector
uv run python scripts/init_db.py
```

## Lancement

```bash
# Lancer le serveur de développement
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Le serveur sera accessible sur `http://localhost:8000`

## API Documentation

Une fois le serveur lancé, la documentation interactive est disponible sur:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Structure du projet

```
backend/
├── app/
│   ├── api/           # Endpoints FastAPI
│   ├── core/          # Configuration et database
│   ├── models/        # Modèles SQLAlchemy
│   └── services/      # Services métier (RAG, embeddings, etc.)
├── scripts/           # Scripts utilitaires
├── storage/           # Stockage local des documents
└── pyproject.toml     # Configuration uv
```

## Endpoints principaux

- `POST /api/documents/upload` - Upload un document
- `GET /api/documents/` - Lister les documents
- `DELETE /api/documents/{id}` - Supprimer un document
- `POST /api/chat/` - Chat non-streaming
- `POST /api/chat/stream` - Chat avec streaming SSE

