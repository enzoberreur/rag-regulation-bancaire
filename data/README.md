# Documents de test pour LLMOPS Product

Ce dossier contient des faux PDFs réglementaires pour tester l'application RAG.

## 📄 Documents disponibles

### Regulations (à classifier comme "Regulation")

1. **ACPR_Regulation_2024-15_Climate_Capital.pdf**
   - Régulation ACPR sur les exigences de capital climatique
   - Contient les articles 12, 15, 18, 22
   - Mentionne les exigences de reporting mensuel et de capital buffer

2. **ECB_Guidelines_2024-08_AI_Compliance.pdf**
   - Guidelines ECB sur l'utilisation de l'IA dans les opérations bancaires
   - 5 principes de conformité (Transparence, Qualité des données, Supervision humaine, etc.)

3. **EU_AI_Act_2024_Banking_Requirements.pdf**
   - EU AI Act - Exigences pour le secteur bancaire
   - Articles 6, 9, 13, 15, 72 sur les systèmes d'IA à haut risque

### Policies (à classifier comme "Policy")

4. **HexaBank_RMP-2024-03_Risk_Management_Policy.pdf**
   - Politique interne HexaBank sur la gestion des risques
   - Section 4.2 sur le cadre de gestion des risques climatiques
   - ⚠️ Mentionne que l'évaluation quantitative n'est pas encore implémentée

5. **HexaBank_AI_Compliance_Policy_2024.pdf**
   - Politique interne HexaBank sur la conformité IA
   - Structure de gouvernance, exigences de documentation, monitoring

## 🧪 Scénarios de test

### Test 1: Gap Analysis
**Question à poser :**
> "Compare la régulation ACPR 2024-15 avec la politique RMP-2024-03 d'HexaBank. Quels sont les écarts de conformité ?"

**Résultat attendu :**
- Identification du gap : ACPR exige une quantification quantitative, mais RMP-2024-03 n'a qu'une approche qualitative
- Citation des articles pertinents
- Recommandations d'actions

### Test 2: Cross-Reference
**Question à poser :**
> "Quelles sont les exigences de gouvernance pour les risques climatiques selon ACPR et comment HexaBank doit-il se conformer ?"

**Résultat attendu :**
- Article 15 ACPR sur le Comité des Risques Climatiques
- Comparaison avec la structure actuelle d'HexaBank

### Test 3: AI Compliance
**Question à poser :**
> "Résume les exigences de l'EU AI Act et de l'ECB pour les systèmes d'IA bancaires et vérifie si la politique HexaBank est conforme."

**Résultat attendu :**
- Synthèse des exigences EU AI Act et ECB
- Vérification de conformité avec la politique interne
- Identification des gaps potentiels

### Test 4: Multi-document Analysis
**Question à poser :**
> "Quelles sont toutes les exigences de reporting et de monitoring pour les systèmes d'IA dans les différents documents réglementaires ?"

**Résultat attendu :**
- Compilation des exigences de différents documents
- Citations de chaque source
- Synthèse structurée

## 📝 Comment utiliser

1. Lancez le backend et le frontend
2. Dans l'interface, cliquez sur l'icône 📎 (Paperclip)
3. Uploadez les PDFs en les classant correctement :
   - **Regulations** : ACPR, ECB, EU AI Act
   - **Policies** : Les deux documents HexaBank
4. Attendez que les documents soient traités (chunking + embeddings)
5. Posez les questions de test ci-dessus

## ✅ Vérifications

Après l'upload, vérifiez que :
- Les documents apparaissent dans la liste
- Le nombre de chunks est indiqué (si disponible dans l'UI)
- Les questions renvoient des réponses pertinentes avec citations
- Les citations pointent vers les bons documents

## 🎯 Points d'attention

- Les documents sont fictifs mais réalistes
- Ils contiennent des références croisées intentionnelles pour tester le RAG
- Le document RMP-2024-03 mentionne explicitement un gap (pas de quantification), ce qui devrait être détecté par le RAG

