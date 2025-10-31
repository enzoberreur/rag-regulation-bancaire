# Guide de démarrage - LLMOPS Product

## 🎯 Ce qui a été fait

✅ **Backend Python** avec FastAPI  
✅ **PostgreSQL + pgvector** configuré et initialisé  
✅ **RAG complet** avec embeddings BAAI/bge-m3 et OpenAI GPT-4o-mini  
✅ **Frontend React** connecté au backend  
✅ **Upload de documents** (PDF, DOCX, TXT)  
✅ **Chat avec streaming SSE**  
✅ **Tous les bugs corrigés**

## 🚀 Prochaines étapes

### 1. Lancer le backend

```bash
cd "/Users/enzoberreur/Documents/Albert School/Year 2/LLMOPS-product/backend"
uv run python run.py
```

Le serveur sera accessible sur `http://localhost:8000`

### 2. Lancer le frontend (dans un autre terminal)

```bash
cd "/Users/enzoberreur/Documents/Albert School/Year 2/LLMOPS-product"
npm run dev
```

Le frontend sera accessible sur `http://localhost:3000` (ou le port configuré par Vite)

### 3. Tester l'application

#### a) Uploader des documents
1. Ouvrez l'application dans le navigateur
2. Cliquez sur l'icône 📎 (Paperclip) en bas à gauche
3. Sélectionnez des documents PDF/DOCX/TXT
4. Choisissez le type : Regulation, Policy, ou Document
5. Les documents seront automatiquement traités (extraction, chunking, embeddings)

#### b) Poser des questions
1. Tapez une question dans le chat
2. L'assistant cherchera dans tous les documents uploadés
3. La réponse sera générée avec streaming en temps réel
4. Les citations seront affichées automatiquement

## 📋 Checklist de test

- [ ] Backend démarre sans erreur
- [ ] Frontend démarre sans erreur
- [ ] Upload d'un document PDF fonctionne
- [ ] Le document apparaît dans la liste
- [ ] Poser une question sur le document
- [ ] La réponse arrive avec streaming
- [ ] Les citations sont affichées

## 🔧 Configuration importante

### Fichier `.env` dans `backend/`
Assurez-vous que votre clé OpenAI est bien configurée :
```env
OPENAI_API_KEY=votre_clé_ici
DATABASE_URL=postgresql://enzoberreur@localhost:5432/llmops_db
```

### PostgreSQL 17
Assurez-vous que PostgreSQL 17 est démarré :
```bash
brew services start postgresql@17
```

## 🐛 Dépannage

### Le backend ne démarre pas
- Vérifiez que PostgreSQL 17 est démarré : `brew services list | grep postgresql`
- Vérifiez que le fichier `.env` existe et contient `OPENAI_API_KEY`

### Le frontend ne se connecte pas au backend
- Vérifiez que le backend tourne sur `http://localhost:8000`
- Vérifiez les erreurs dans la console du navigateur (F12)

### Les documents ne s'uploadent pas
- Vérifiez que le dossier `backend/storage/documents` existe
- Vérifiez les logs du backend pour les erreurs

## 📚 Documentation API

Une fois le backend lancé, vous pouvez accéder à :
- **Swagger UI** : `http://localhost:8000/docs`
- **ReDoc** : `http://localhost:8000/redoc`

## 🎨 Améliorations possibles

1. **Gestion d'erreurs** : Ajouter plus de feedback utilisateur
2. **Authentification** : Ajouter un système d'authentification si nécessaire
3. **Optimisation** : Cache des embeddings, batch processing
4. **UI/UX** : Améliorer l'affichage des citations, ajouter des statistiques
5. **Tests** : Ajouter des tests unitaires et d'intégration

## 📝 Notes importantes

- Les documents sont stockés localement dans `backend/storage/documents`
- Les embeddings sont stockés dans PostgreSQL avec pgvector
- Le modèle BAAI/bge-m3 génère des embeddings de 1024 dimensions
- Les chunks font environ 900-1200 tokens

## 🎓 Utilisation

1. **Upload** : Glissez-déposez vos documents réglementaires (ACPR, ECB, EU AI Act)
2. **Classification** : Classez-les comme Regulation, Policy, ou Document
3. **Question** : Posez des questions sur la conformité, les gaps, etc.
4. **Analyse** : L'assistant analyse automatiquement et propose des actions

Bonne chance avec votre application ! 🚀

