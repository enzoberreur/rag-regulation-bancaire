# 📊 Analyse du Chunking & Reranking - Système RAG

## 🔍 État Actuel du Système

### 1. **Stratégie de Chunking** (config actuelle)

#### Chunking par Phrases (ACTIF) 
```python
chunking_strategy: "sentence"
sentences_per_chunk: 5      # 5 phrases par chunk
sentence_overlap: 1         # 1 phrase de chevauchement
```

**Comment ça marche:**
- Découpe le texte en phrases individuelles avec regex
- Groupe 5 phrases ensemble → 1 chunk
- Overlap de 1 phrase entre chunks consécutifs
- Ignore phrases < 10 caractères

**Avantages:** ✅
- Chunks sémantiquement cohérents
- Maintient le contexte de phrases complètes
- Overlap naturel

**Problèmes:** ❌
- **Chunks trop courts** pour questions complexes (5 phrases = ~100-200 mots)
- Ne capture pas les sections entières (ex: Article + sous-articles)
- Pas de hiérarchie documentaire (titre → paragraphe → article)

---

#### Chunking par Tokens (DISPONIBLE mais désactivé)
```python
chunking_strategy: "token"  # Désactivé actuellement
chunk_size: 800            # 800 tokens (~600 mots)
chunk_overlap: 200         # 200 tokens de chevauchement
```

**Comment ça marche:**
- RecursiveCharacterTextSplitter de LangChain
- Découpe intelligente avec priorité aux séparateurs:
  1. `\n\n\n` (sections multiples)
  2. `\nARTICLE ` (début d'article)
  3. `\nSection ` (début de section)
  4. `\n\n` (paragraphes)
  5. `. ` (phrases)
  6. `, ` (virgules en dernier recours)

**Avantages:** ✅
- **Chunks plus longs** → plus de contexte
- Respect structure documentaire (articles, sections)
- Overlap de 25% (200/800)

**Problèmes:** ❌
- Actuellement **DÉSACTIVÉ**

---

### 2. **Pipeline de Retrieval**

```
1. HyDE génère réponse hypothétique (250 tokens)
   ↓
2. Embedding de la réponse hypothétique
   ↓
3. Recherche vectorielle: TOP 40 chunks (initial_top_k=40)
   ↓
4. Reranking avec bge-reranker-v2-m3 (tous les 40)
   ↓
5. Filtrage par seuil: rerank_threshold=0.05
   ↓
6. Diversité: 1 chunk max par document si enforce_diversity=True
   ↓
7. Limite finale: top_k_results=12 chunks
```

---

### 3. **Problème Identifié avec MREL/Buffer**

**Logs de ton test:**
```
📊 Raw reranker scores - min: 0.000, max: 0.020
⚙️  Rerank filter disabled — every reranked chunk is kept
🎯 Diversity applied: 1 documents used, distribution: {UUID(...): 3}
```

**Diagnostic:**
1. ❌ **Reranker scores catastrophiques**: max=0.020 (normalisé 0-1)
   - Signifie: le reranker trouve les chunks **très peu pertinents**
   - Raison probable: chunks trop courts (5 phrases) ne contiennent pas assez de contexte

2. ❌ **1 seul document trouvé** (CRD4.pdf)
   - Diversité enforcée mais un seul doc pertinent
   - Seulement 3 chunks retenus → contexte insuffisant

3. ❌ **Pages trouvées peu pertinentes**: p.92, p.66 (table matières), p.12 (périmètre)
   - p.93 manquante (contient M-MDA détaillé)
   - Chunks ne capturent pas la section complète sur MREL/buffer interaction

---

## 💡 Solutions d'Amélioration

### **Option A: Chunks plus longs (RECOMMANDÉ)** 🏆

**Action:** Passer au chunking par tokens avec chunks plus gros

```python
# Dans .env ou config.py
CHUNKING_STRATEGY=token
CHUNK_SIZE=1200           # ↑ de 800 à 1200 tokens (~900 mots)
CHUNK_OVERLAP=300         # ↑ de 200 à 300 (25% overlap)
```

**Avantages:**
- ✅ Plus de contexte par chunk (900 mots vs 100-200 actuellement)
- ✅ Capture sections complètes (Article + sous-articles + explications)
- ✅ Meilleurs scores de reranking (plus de contenu pertinent)
- ✅ Respect structure documentaire (ARTICLE, Section, etc.)

**Inconvénients:**
- ⚠️ Chunks plus gros = plus de tokens envoyés au LLM
- ⚠️ Coût légèrement supérieur (mais offset par meilleure qualité)

---

### **Option B: Augmenter initial_top_k**

```python
INITIAL_TOP_K=60          # ↑ de 40 à 60
TOP_K_RESULTS=15          # ↑ de 12 à 15
```

**Avantages:**
- ✅ Plus de chunks candidats pour le reranking
- ✅ Meilleure chance de trouver p.93 M-MDA

**Inconvénients:**
- ⚠️ Reranking plus lent (60 chunks vs 40)
- ⚠️ Ne résout pas le problème de chunks trop courts

---

### **Option C: Ajuster le seuil de reranking**

```python
RERANK_THRESHOLD=0.01     # ↓ de 0.05 à 0.01 (plus permissif)
```

**Avantages:**
- ✅ Garde plus de chunks après reranking

**Inconvénients:**
- ❌ Risque de garder des chunks non pertinents
- ❌ Bruit dans le contexte

---

### **Option D: Injection manuelle de sections critiques** 🎯

**Action:** Détecter mots-clés et injecter sections spécifiques

```python
# Dans rag_service.py _augment_with_targeted_sections()
if "MREL" in query and ("buffer" in query or "CBR" in query):
    # Injecter chunks des pages 92-93 avec metadata section="MREL-Buffer"
    targeted_chunks = self._fetch_chunks_by_section("MREL", "buffer")
```

**Avantages:**
- ✅ Garantit que le contenu pertinent arrive au LLM
- ✅ Pas de dépendance au retrieval vectoriel

**Inconvénients:**
- ⚠️ Maintenance manuelle des mappings query → sections
- ⚠️ Pas scalable si beaucoup de topics

---

## 🎯 Plan d'Action Recommandé

### **Phase 1: Améliorer le chunking (PRIORITÉ 1)** ⭐

1. **Activer chunking par tokens:**
   ```bash
   # Dans backend/.env
   CHUNKING_STRATEGY=token
   CHUNK_SIZE=1200
   CHUNK_OVERLAP=300
   ```

2. **Reprocesser les documents:**
   ```bash
   cd backend
   python3 scripts/reprocess_all_documents.py
   ```

3. **Tester avec la même query MREL/buffer:**
   - Vérifier les reranker scores (devrait être > 0.3)
   - Vérifier les pages trouvées (devrait inclure p.93)

---

### **Phase 2: Optimiser le retrieval (PRIORITÉ 2)** ⭐

Si Phase 1 ne suffit pas:

1. **Augmenter initial_top_k:**
   ```python
   INITIAL_TOP_K=60
   TOP_K_RESULTS=15
   ```

2. **Ajuster enforce_diversity:**
   ```python
   ENFORCE_DIVERSITY=False  # Autorise plusieurs chunks du même doc
   ```

---

### **Phase 3: Injection manuelle (PRIORITÉ 3)** 🔧

En dernier recours, si questions récurrentes sur MREL/buffer:

1. Ajouter détection de keywords dans `_augment_with_targeted_sections()`
2. Mapper query patterns → sections précises
3. Injecter avec similarity=1.0

---

## 📈 Métriques à Surveiller Après Changements

```
✅ Reranker scores > 0.3 (actuellement 0.020)
✅ Diversity: 1-3 documents (actuellement 1)
✅ Pages trouvées: p.92, p.93, p.85 (actuellement p.92, p.66, p.12)
✅ Citations dans réponse: 6-10 <mark> tags (actuellement 2)
✅ Longueur chunks: 800-1200 tokens (actuellement ~100-200 mots/5 phrases)
```

---

## 🔄 Comparaison Chunking Strategies

| Critère | Sentence (actuel) | Token (recommandé) |
|---------|-------------------|-------------------|
| Taille chunk | 5 phrases (~100-200 mots) | 1200 tokens (~900 mots) |
| Overlap | 1 phrase | 300 tokens (25%) |
| Structure doc | ❌ Ignorée | ✅ Respectée (ARTICLE, Section) |
| Contexte | ⚠️ Limité | ✅ Large |
| Reranker scores | ❌ 0.020 | ✅ Attendu >0.3 |
| Pertinence | ⚠️ Fragments | ✅ Sections complètes |
| Coût LLM | ✅ Bas | ⚠️ Moyen (+30%) |
| Qualité réponse | ❌ Générique | ✅ Détaillée avec citations |

---

## 🚀 Commande Rapide pour Tester

```bash
# 1. Modifier .env
echo "CHUNKING_STRATEGY=token" >> backend/.env
echo "CHUNK_SIZE=1200" >> backend/.env
echo "CHUNK_OVERLAP=300" >> backend/.env

# 2. Reprocesser documents
cd backend
python3 scripts/reprocess_all_documents.py

# 3. Relancer backend
python3 run.py

# 4. Retester query MREL/buffer dans frontend
```
