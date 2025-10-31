# Connexion Frontend-Backend

Le frontend est maintenant connecté au backend ! Voici ce qui a été fait :

## ✅ Fonctionnalités connectées

### 1. Upload de documents
- Les documents uploadés via l'interface sont maintenant envoyés au backend
- Le backend traite automatiquement les documents (extraction texte, chunking, embeddings)
- Les documents sont stockés dans PostgreSQL avec leurs embeddings pour le RAG

### 2. Chargement des documents
- Au démarrage de l'application, les documents déjà uploadés sont chargés depuis le backend
- L'interface affiche tous les documents disponibles

### 3. Chat avec RAG
- Les questions posées dans le chat utilisent maintenant le vrai backend RAG
- Le backend recherche dans tous les documents uploadés et traités
- Les réponses sont générées avec streaming SSE
- Les citations sont extraites et affichées

### 4. Suppression de documents
- La suppression d'un document supprime aussi le fichier et tous ses chunks du backend

## 🔄 Flux complet

1. **Upload** → Frontend envoie le fichier au backend → Backend traite et stocke
2. **Chunking** → Backend extrait le texte → Découpe en chunks (900-1200 tokens) → Génère embeddings
3. **Stockage** → Chunks + embeddings stockés dans PostgreSQL avec pgvector
4. **Question** → Frontend envoie la question → Backend cherche les chunks pertinents → Génère réponse avec LLM
5. **Réponse** → Streaming SSE → Frontend affiche la réponse en temps réel + citations

## 📝 Configuration nécessaire

1. Créer un fichier `.env` à la racine du projet frontend (optionnel) :
```env
VITE_API_URL=http://localhost:8000
```

Par défaut, l'API utilise `http://localhost:8000`

## 🚀 Prochaines étapes

1. Lancer le backend :
```bash
cd backend
uv run python run.py
```

2. Lancer le frontend :
```bash
npm run dev
```

3. Uploader des documents et poser des questions !

Les documents uploadés seront automatiquement utilisés pour le RAG !

