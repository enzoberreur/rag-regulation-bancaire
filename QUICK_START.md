# 🚀 LLMOPS Product - Quick Start Guide

## Lancer l'application

### Option 1 : Tout ensemble (backend + frontend)
```bash
./run.sh
# ou
npm start
```

### Option 2 : Séparément (recommandé pour le développement)

**Terminal 1 - Backend:**
```bash
./run-backend.sh
# ou
npm run start:backend
```

**Terminal 2 - Frontend:**
```bash
./run-frontend.sh
# ou
npm run start:frontend
```

### Option 3 : Manuellement

**Terminal 1 - Backend:**
```bash
cd backend && uv run python run.py
```

**Terminal 2 - Frontend:**
```bash
npm run dev
```

## Arrêter l'application

Appuyez sur `Ctrl+C` dans le terminal où le serveur tourne.

## URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Logs

Les logs sont affichés directement dans le terminal où vous avez lancé les serveurs.


