# 🔍 AUDIT RAG & PLAN D'AMÉLIORATION

**Date:** 4 novembre 2025  
**Système:** RAG Banking Compliance Assistant

---

## 📊 ÉTAT ACTUEL DU SYSTÈME

### ✅ Ce qui fonctionne bien

1. **Architecture solide**
   - 8 documents, 642 chunks (moyenne: 80 chunks/doc)
   - Embeddings OpenAI text-embedding-3-small (1536 dimensions)
   - Reranking avec cross-encoder ms-marco-MiniLM-L-6-v2
   - Chunking sémantique avec RecursiveCharacterTextSplitter

2. **Métadonnées présentes**
   - Document name ✅
   - Page number ✅
   - Section titles (parfois) ✅
   - Token count ✅

3. **Pipeline RAG complet**
   - Query reformulation ✅
   - Vector search (16 chunks initiaux) ✅
   - Reranking (8 meilleurs chunks) ✅
   - Hybrid mode (documents + expert knowledge) ✅

---

## 🐛 PROBLÈMES IDENTIFIÉS

### 1. ❌ **PROBLÈME CRITIQUE: Numéros de pages inexacts**

**Symptôme:** Le LLM cite "page 4" mais le texte est ailleurs

**Cause racine:** 
- Le système utilise `enumerate(reader.pages, start=1)` qui donne la **position physique dans le PDF**
- Mais les documents réglementaires ont souvent:
  - Pages de garde (non numérotées)
  - Tables des matières (numérotées i, ii, iii)
  - Le contenu principal commence à "page 1" physique = page 3 ou 4 du PDF

**Exemple:**
```
PDF physique:  [Couverture] [Sommaire] [Page 1 contenu] [Page 2 contenu]
Position:           1            2            3                4
Numéro réel:       -            -            1                2
```

**Impact:** Citations incorrectes, perte de confiance de l'utilisateur

---

### 2. ⚠️ **Détection de sections insuffisante**

**État actuel:** Seulement 1 chunk sur 5 a un titre de section détecté

**Patterns actuels détectés:**
```python
r'^(ARTICLE|Article|CHAPITRE|Chapitre|SECTION|Section|TITRE|Titre)\s+[IVX\d]+'
r'^[IVX\d]+\.\s+[A-Z]'
r'^[IVX\d]+\.[IVX\d]+'
r'^[A-Z][A-Z\s]{5,}$'
```

**Problème:** Beaucoup de sections réglementaires ne matchent pas ces patterns:
- "Introduction"
- "Annexe A - Définitions"
- "Partie 1 : Cadre général"
- "6.2. Dispositif de contrôle des risques"

---

### 3. ⚠️ **Chunking pourrait être amélioré**

**Configuration actuelle:**
```python
chunk_size=1050 caractères  # ~800-900 tokens
chunk_overlap=150 caractères  # ~120 tokens
```

**Problèmes:**
- Taille variable (735 à 980 tokens observés) → difficile à prédire
- Overlap trop faible (14%) → risque de perdre du contexte entre chunks
- Pas de respect des frontières de sections

---

### 4. ⚠️ **Prompts pourraient être plus stricts**

**Problème actuel:** Le LLM peut paraphraser au lieu de citer exactement
- Prompt dit: "VERBATIM quote" mais LLM traduit parfois
- Exemple: "Tier 1 capital" → "fonds propres de catégorie 1"

---

### 5. ℹ️ **Pas de vérification post-génération**

**Manque:** Aucun système pour vérifier que les citations sont correctes après génération

---

## 🚀 PLAN D'AMÉLIORATION PRIORITAIRE

### 🔴 PRIORITÉ 1: Extraction correcte des numéros de page

**Solution:** Parser le numéro de page depuis le contenu du PDF

```python
def _extract_real_page_number(self, page_content: str) -> Optional[int]:
    """
    Extrait le vrai numéro de page depuis le contenu (footer/header).
    
    Patterns courants:
    - "Page 5"
    - "5/45"
    - "- 5 -"
    - "CRD4 | Page 5"
    """
    import re
    
    # Prendre les dernières lignes (footer) et premières lignes (header)
    lines = page_content.strip().split('\n')
    candidates = lines[:3] + lines[-3:]  # 3 premières + 3 dernières lignes
    
    for line in candidates:
        line = line.strip()
        
        # Pattern 1: "Page X" ou "PAGE X"
        match = re.search(r'\bPAGE\s+(\d+)\b', line, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Pattern 2: "X/Y" (page X sur Y)
        match = re.search(r'\b(\d+)\s*/\s*\d+\b', line)
        if match:
            return int(match.group(1))
        
        # Pattern 3: "- X -"
        match = re.search(r'-\s*(\d+)\s*-', line)
        if match:
            return int(match.group(1))
        
        # Pattern 4: Juste un nombre isolé (risqué)
        if re.match(r'^\d+$', line):
            return int(line)
    
    return None
```

**Fallback:** Si pas de numéro trouvé, utiliser la position physique mais ajouter un flag:
```python
{
    "page": physical_position,
    "page_extracted": True/False,
    "page_note": "Position dans le PDF, pas le numéro réel"
}
```

---

### 🔴 PRIORITÉ 2: Améliorer la détection de sections

**Ajouter plus de patterns:**

```python
def _detect_section_title(self, text: str) -> Optional[str]:
    """Détecte les titres de sections avec patterns étendus."""
    import re
    
    first_lines = text.strip().split('\n')[:5]  # 5 au lieu de 3
    
    for line in first_lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        
        # Pattern 1: Numérotation classique
        if re.match(r'^[IVX\d]+[\.\)]\s+[A-Z]', line):
            return line[:150]
        
        # Pattern 2: Mots-clés de section
        section_keywords = [
            'ARTICLE', 'CHAPITRE', 'SECTION', 'TITRE', 'PARTIE',
            'ANNEXE', 'APPENDIX', 'INTRODUCTION', 'CONCLUSION',
            'DÉFINITIONS', 'DEFINITIONS', 'GLOSSAIRE', 'GLOSSARY'
        ]
        if any(kw in line.upper() for kw in section_keywords):
            return line[:150]
        
        # Pattern 3: Ligne en majuscules (titre)
        if len(line) > 10 and line.isupper() and not line.endswith('.'):
            return line[:150]
        
        # Pattern 4: Format "X.Y.Z Titre"
        if re.match(r'^\d+(\.\d+)*\s+[A-Z]', line):
            return line[:150]
    
    return None
```

---

### 🟠 PRIORITÉ 3: Optimiser le chunking

**Nouvelle stratégie:**

```python
# 1. Augmenter l'overlap
chunk_overlap = 200  # 19% au lieu de 14%

# 2. Utiliser des séparateurs plus intelligents
separators = [
    "\n\n\n",           # Sections multiples
    "\n\n",             # Paragraphes
    "\nARTICLE ",       # Début d'article
    "\nSection ",       # Début de section
    "\n\n",             # Double saut
    "\n",               # Simple saut
    ". ",               # Fin de phrase
    " ",                # Espace
    ""                  # Caractère
]

# 3. Ajouter une post-processing pour éviter de couper en plein milieu
def _clean_chunk_boundaries(self, chunk: str) -> str:
    """Nettoie les frontières de chunk."""
    # Si le chunk commence au milieu d'une phrase, supprimer le début
    if not chunk[0].isupper() and '.' in chunk:
        chunk = chunk[chunk.index('.') + 1:].strip()
    
    # Si le chunk finit au milieu d'une phrase, supprimer la fin
    if not chunk.endswith(('.', '!', '?', '\n')):
        last_period = chunk.rfind('.')
        if last_period > len(chunk) * 0.7:  # Garder au moins 70%
            chunk = chunk[:last_period + 1]
    
    return chunk.strip()
```

---

### 🟠 PRIORITÉ 4: Renforcer les prompts anti-hallucination

**Modifications:**

```python
SYSTEM_PROMPT = """[...]

**RÈGLE ABSOLUE POUR LES CITATIONS:**

Avant d'utiliser <mark data-source="...">texte</mark>, fais cette vérification en 3 étapes:

1. **CHERCHER**: Parcours le CONTEXT ci-dessus, lis chaque [Source N: ...]
2. **COMPARER**: Le texte que tu veux citer est-il MOT-À-MOT dans une source?
3. **DÉCIDER**: 
   - OUI, identique → Utilise <mark>
   - NON, similaire → Écris normalement SANS <mark>
   - NON, manquant → Mentionne "Les documents fournis ne contiennent pas..."

**Exemples INTERDITS:**
❌ Source dit "Tier 1 capital ratio" → TU NE PEUX PAS écrire <mark>ratio de fonds propres Tier 1</mark>
❌ Source dit "4.5%" → TU NE PEUX PAS écrire <mark>quatre virgule cinq pour cent</mark>
❌ Tu connais la réponse mais elle n'est pas dans le CONTEXT → PAS de <mark>

**Exemples AUTORISÉS:**
✅ Source dit "Le ratio CET1 minimum est de 4,5%" → <mark data-source="...">Le ratio CET1 minimum est de 4,5%</mark>
✅ Pas dans CONTEXT → "Le ratio de levier compare les fonds propres Tier 1 à l'exposition totale (cette information ne figure pas dans les documents fournis)."
"""
```

---

### 🟡 PRIORITÉ 5: Ajouter une vérification post-génération

**Nouveau service `CitationValidator`:**

```python
class CitationValidator:
    """Valide que les citations sont correctes."""
    
    async def validate_response(
        self, 
        response_text: str, 
        context_chunks: List[DocumentChunk]
    ) -> Dict[str, any]:
        """
        Vérifie que toutes les citations sont dans le contexte.
        
        Returns:
            {
                "is_valid": bool,
                "invalid_citations": List[str],
                "warnings": List[str]
            }
        """
        import re
        from difflib import SequenceMatcher
        
        # Extraire toutes les citations
        citations = re.findall(r'<mark[^>]*>(.+?)</mark>', response_text, re.DOTALL)
        
        invalid = []
        warnings = []
        
        for citation in citations:
            # Nettoyer le texte
            citation_clean = citation.strip()
            
            # Chercher dans les chunks
            found = False
            best_match_ratio = 0
            
            for chunk in context_chunks:
                # Exact match
                if citation_clean in chunk.content:
                    found = True
                    break
                
                # Fuzzy match (90%+)
                ratio = SequenceMatcher(None, citation_clean, chunk.content).ratio()
                best_match_ratio = max(best_match_ratio, ratio)
                
                if ratio > 0.90:
                    found = True
                    if ratio < 0.98:
                        warnings.append(f"Citation approximative: {citation_clean[:50]}... (match: {ratio:.1%})")
                    break
            
            if not found:
                invalid.append(citation_clean[:100])
        
        return {
            "is_valid": len(invalid) == 0,
            "invalid_citations": invalid,
            "warnings": warnings,
            "total_citations": len(citations),
            "best_match_ratio": best_match_ratio
        }
```

**Intégration dans le stream:**

```python
# Après génération, avant d'envoyer au frontend
validation = await self.citation_validator.validate_response(normalized_content, chunks)

if not validation["is_valid"]:
    print(f"⚠️ HALLUCINATION DÉTECTÉE: {len(validation['invalid_citations'])} citations invalides")
    for invalid in validation["invalid_citations"]:
        print(f"   - {invalid}")
    
    # Option 1: Supprimer les <mark> invalides
    # Option 2: Ajouter un avertissement au frontend
    # Option 3: Régénérer avec un prompt plus strict
```

---

### 🟢 PRIORITÉ 6: Améliorer les métriques de qualité

**Ajouter des métriques avancées:**

```python
class RAGMetrics:
    """Métriques de qualité du RAG."""
    
    def calculate_metrics(
        self,
        query: str,
        chunks: List[DocumentChunk],
        response: str,
        validation: Dict
    ) -> Dict[str, any]:
        """Calcule des métriques complètes."""
        
        return {
            # Retrieval
            "chunks_retrieved": len(chunks),
            "unique_documents": len(set(c.document_id for c in chunks)),
            "avg_chunk_relevance": sum(scores) / len(scores),
            "page_coverage": list(set(c.chunk_metadata.get("page") for c in chunks)),
            
            # Generation
            "response_length": len(response),
            "citations_count": validation["total_citations"],
            "citations_valid": validation["is_valid"],
            "hallucination_risk": 1.0 - (len(validation["invalid_citations"]) / max(validation["total_citations"], 1)),
            
            # Quality
            "response_coherence": self._calculate_coherence(response),
            "context_utilization": self._calculate_context_usage(response, chunks),
        }
```

---

## 📋 CHECKLIST D'IMPLÉMENTATION

### Phase 1: Corrections critiques (1-2h)
- [ ] Implémenter `_extract_real_page_number()` dans `TextExtractor`
- [ ] Tester sur 3-4 documents différents
- [ ] Ajouter fallback pour pages non trouvées
- [ ] Améliorer `_detect_section_title()` avec patterns étendus

### Phase 2: Amélioration du chunking (1h)
- [ ] Augmenter `chunk_overlap` à 200
- [ ] Ajouter séparateurs spécifiques (ARTICLE, Section, etc.)
- [ ] Implémenter `_clean_chunk_boundaries()`
- [ ] Reprocesser tous les documents

### Phase 3: Validation (2h)
- [ ] Créer `CitationValidator` service
- [ ] Intégrer dans le streaming
- [ ] Ajouter logging des citations invalides
- [ ] Décider de la stratégie (supprimer/avertir/régénérer)

### Phase 4: Prompts (30min)
- [ ] Renforcer le SYSTEM_PROMPT avec vérification en 3 étapes
- [ ] Ajouter exemples INTERDITS/AUTORISÉS
- [ ] Tester avec questions connues

### Phase 5: Métriques (1h)
- [ ] Créer `RAGMetrics` service
- [ ] Ajouter métriques avancées au frontend
- [ ] Logger les métriques pour analyse

---

## 🎯 RÉSULTATS ATTENDUS

### Avant amélioration
- ❌ Numéros de pages incorrects (position physique)
- ⚠️ Citations approximatives (paraphrases)
- ⚠️ Sections mal détectées (1/5 seulement)
- ℹ️ Pas de validation des citations

### Après amélioration
- ✅ Numéros de pages réels (extraits du contenu)
- ✅ Citations exactes (vérifiées post-génération)
- ✅ Sections bien détectées (4/5 minimum)
- ✅ Validation automatique + alertes hallucination

---

## 📊 MÉTRIQUES DE SUCCÈS

| Métrique | Avant | Objectif | Comment mesurer |
|----------|-------|----------|-----------------|
| Page accuracy | 40% | 95% | Test sur 20 citations aléatoires |
| Citation exactitude | 70% | 95% | Validation automatique |
| Section détection | 20% | 80% | % chunks avec section |
| Hallucination rate | 5% | <1% | Citations invalides / total |
| User trust score | 6/10 | 9/10 | Feedback utilisateurs |

---

## 🔄 CYCLE D'AMÉLIORATION CONTINUE

1. **Monitoring:** Logger toutes les citations + validation
2. **Analyse:** Review hebdomadaire des hallucinations
3. **Ajustement:** Affiner prompts et patterns
4. **A/B Testing:** Tester nouvelles stratégies
5. **Feedback loop:** Intégrer retours utilisateurs

---

**Prochaine étape:** Implémenter Phase 1 (extraction pages réelles) 🚀
