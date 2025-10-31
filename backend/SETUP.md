# Backend RAG - LLMOPS Product

## Structure créée

✅ Backend Python avec FastAPI  
✅ Configuration avec Pydantic Settings  
✅ Modèles SQLAlchemy (Document, DocumentChunk)  
✅ Endpoints API (chat, documents, health)  
✅ Service RAG complet  
✅ Embeddings BAAI/bge-m3  
✅ Chunking LangChain (900-1200 tokens)  
✅ Streaming SSE  
✅ Extraction texte (PDF, DOCX, TXT)  

## Prochaines étapes

1. Créer la base de données PostgreSQL avec pgvector
2. Configurer le fichier `.env`
3. Installer les dépendances avec `uv`
4. Initialiser la base de données
5. Connecter le frontend React

## Commandes à exécuter

```bash
# 1. Installer uv (si pas déjà fait)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Aller dans le dossier backend
cd backend

# 3. Créer le fichier .env (copier depuis env.example et modifier)
cp env.example .env
# Puis éditer .env avec vos credentials

# 4. Installer les dépendances
uv sync

# 5. Créer la base de données PostgreSQL
createdb llmops_db

# 6. Installer pgvector dans PostgreSQL (si pas déjà fait)
# Dans psql:
psql llmops_db -c "CREATE EXTENSION vector;"

# 7. Initialiser les tables
uv run python scripts/init_db.py

# 8. Lancer le serveur
uv run python run.py
# Ou directement:
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/` - Liste documents
- `DELETE /api/documents/{id}` - Supprimer document
- `POST /api/chat/` - Chat non-streaming
- `POST /api/chat/stream` - Chat avec streaming SSE

## Documentation

Une fois le serveur lancé: `http://localhost:8000/docs`

