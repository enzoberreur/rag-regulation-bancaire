#!/usr/bin/env python3
"""
Script de test pour vérifier les améliorations du RAG.
Teste l'extraction de pages, la détection de sections, et la validation des citations.
"""
import sys
import os

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.document import Document, DocumentChunk
from app.services.text_extractor import TextExtractor
from app.services.document_processor import DocumentProcessor
from sqlalchemy import func


def test_page_extraction():
    """Teste l'extraction des numéros de pages réels."""
    print("\n" + "="*80)
    print("📄 TEST 1: EXTRACTION DES NUMÉROS DE PAGE")
    print("="*80)
    
    db = SessionLocal()
    
    # Prendre un document PDF
    doc = db.query(Document).filter(Document.file_type == 'pdf').first()
    
    if not doc:
        print("❌ Aucun document PDF trouvé")
        db.close()
        return
    
    print(f"\n📁 Document: {doc.name}")
    print(f"   Fichier: {doc.file_path}")
    
    # Extraire les pages
    extractor = TextExtractor()
    import asyncio
    pages = asyncio.run(extractor.extract_text_with_pages(doc.file_path, doc.file_type))
    
    print(f"\n✅ {len(pages)} pages extraites")
    print("\nExemples de mapping:")
    print("-" * 80)
    print(f"{'Position physique':<20} {'Page extraite':<20} {'Extrait?':<20}")
    print("-" * 80)
    
    for page_info in pages[:10]:  # Afficher les 10 premières
        physical = page_info.get('physical_position', '?')
        real_page = page_info.get('page', '?')
        extracted = "✅ Oui" if page_info.get('page_extracted', False) else "❌ Non (physique)"
        
        print(f"{physical:<20} {real_page:<20} {extracted:<20}")
    
    if len(pages) > 10:
        print(f"... et {len(pages) - 10} autres pages")
    
    db.close()


def test_section_detection():
    """Teste la détection des titres de sections."""
    print("\n" + "="*80)
    print("📑 TEST 2: DÉTECTION DES SECTIONS")
    print("="*80)
    
    db = SessionLocal()
    
    # Compter les chunks avec sections
    total_chunks = db.query(DocumentChunk).count()
    chunks_with_section = db.query(DocumentChunk).filter(
        DocumentChunk.chunk_metadata['section'].astext != None
    ).count()
    
    percentage = (chunks_with_section / total_chunks * 100) if total_chunks > 0 else 0
    
    print(f"\n📊 Statistiques:")
    print(f"   Total de chunks: {total_chunks}")
    print(f"   Chunks avec section: {chunks_with_section}")
    print(f"   Pourcentage: {percentage:.1f}%")
    
    # Objectif: 80%+
    if percentage >= 80:
        print(f"   ✅ Excellent! (objectif: 80%)")
    elif percentage >= 50:
        print(f"   ⚠️  Acceptable (objectif: 80%)")
    else:
        print(f"   ❌ Insuffisant (objectif: 80%)")
    
    # Afficher quelques exemples
    print("\n📝 Exemples de sections détectées:")
    print("-" * 80)
    
    chunks_with_sections = db.query(DocumentChunk).filter(
        DocumentChunk.chunk_metadata['section'].astext != None
    ).limit(10).all()
    
    for chunk in chunks_with_sections:
        section = chunk.chunk_metadata.get('section', 'N/A')
        doc_name = chunk.chunk_metadata.get('document_name', 'Unknown')
        page = chunk.chunk_metadata.get('page', '?')
        
        print(f"\n📄 {doc_name}, p.{page}")
        print(f"   Section: {section[:100]}")
    
    db.close()


def test_chunk_quality():
    """Teste la qualité du chunking."""
    print("\n" + "="*80)
    print("✂️  TEST 3: QUALITÉ DU CHUNKING")
    print("="*80)
    
    db = SessionLocal()
    
    # Statistiques sur les chunks
    chunks = db.query(DocumentChunk).all()
    
    if not chunks:
        print("❌ Aucun chunk trouvé")
        db.close()
        return
    
    # Calculer des métriques
    token_counts = [chunk.token_count for chunk in chunks]
    avg_tokens = sum(token_counts) / len(token_counts)
    min_tokens = min(token_counts)
    max_tokens = max(token_counts)
    
    print(f"\n📊 Statistiques de chunking:")
    print(f"   Nombre de chunks: {len(chunks)}")
    print(f"   Tokens moyens: {avg_tokens:.0f}")
    print(f"   Tokens min: {min_tokens}")
    print(f"   Tokens max: {max_tokens}")
    
    # Vérifier si les chunks commencent bien (pas au milieu d'une phrase)
    chunks_starting_lowercase = 0
    chunks_ending_incomplete = 0
    
    for chunk in chunks[:100]:  # Échantillon de 100
        content = chunk.content.strip()
        if content and content[0].islower():
            chunks_starting_lowercase += 1
        if content and content[-1] not in '.!?\n':
            chunks_ending_incomplete += 1
    
    print(f"\n📋 Qualité des frontières (échantillon de 100):")
    print(f"   Chunks commençant en minuscule: {chunks_starting_lowercase} (objectif: <5)")
    print(f"   Chunks finissant incomplets: {chunks_ending_incomplete} (objectif: <10)")
    
    if chunks_starting_lowercase < 5:
        print("   ✅ Excellent début de chunks")
    else:
        print("   ⚠️  Beaucoup de chunks commencent au milieu d'une phrase")
    
    if chunks_ending_incomplete < 10:
        print("   ✅ Bonnes fins de chunks")
    else:
        print("   ⚠️  Beaucoup de chunks finissent au milieu d'une phrase")
    
    db.close()


def test_metadata_enrichment():
    """Teste l'enrichissement des métadonnées."""
    print("\n" + "="*80)
    print("🏷️  TEST 4: ENRICHISSEMENT DES MÉTADONNÉES")
    print("="*80)
    
    db = SessionLocal()
    
    # Vérifier les métadonnées enrichies
    chunk = db.query(DocumentChunk).first()
    
    if not chunk:
        print("❌ Aucun chunk trouvé")
        db.close()
        return
    
    metadata = chunk.chunk_metadata or {}
    
    print(f"\n📋 Métadonnées disponibles:")
    print("-" * 80)
    
    fields = [
        ('document_name', 'Nom du document'),
        ('document_type', 'Type de document'),
        ('page', 'Numéro de page'),
        ('page_extracted', 'Page extraite du contenu?'),
        ('physical_position', 'Position physique dans PDF'),
        ('section', 'Titre de section')
    ]
    
    for field, description in fields:
        value = metadata.get(field)
        status = "✅" if value is not None else "❌"
        print(f"{status} {description:<30} : {value}")
    
    print("\n📄 Exemple complet de métadonnées:")
    print("-" * 80)
    import json
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    
    db.close()


def print_summary():
    """Affiche un résumé des améliorations."""
    print("\n" + "="*80)
    print("📊 RÉSUMÉ DES AMÉLIORATIONS")
    print("="*80)
    
    print("""
✅ Phase 1: Extraction de pages réelles
   - Extraction depuis le contenu du PDF (footer/header)
   - Patterns: "Page X", "X/Y", "- X -", "p. X"
   - Fallback: position physique si non trouvé
   - Métadonnée: page_extracted (True/False)

✅ Phase 2: Détection de sections améliorée
   - Patterns étendus: ARTICLE, CHAPITRE, SECTION, ANNEXE, etc.
   - Détection des numérotations: X.Y.Z, I.II.III
   - Détection des titres en majuscules
   - Objectif: 80%+ des chunks avec section

✅ Phase 3: Chunking optimisé
   - Overlap augmenté: 150 → 200 caractères (19%)
   - Séparateurs spécifiques: ARTICLE, Section, Chapitre
   - Nettoyage des frontières (début/fin de chunks)
   - Skip des chunks trop petits (<100 chars)

✅ Phase 4: Validation des citations
   - CitationValidator: détecte les hallucinations
   - Exact match + fuzzy match (90%+)
   - Rapport détaillé: taux d'hallucination, citations invalides
   - Intégré dans le streaming RAG

✅ Phase 5: Métadonnées enrichies
   - page: numéro de page (réel ou physique)
   - page_extracted: True si extrait du contenu
   - physical_position: position dans le PDF
   - section: titre de section
   - document_name, document_type

🎯 RÉSULTATS ATTENDUS:
   - Pages: 95%+ de précision (vs 40% avant)
   - Sections: 80%+ détectées (vs 20% avant)
   - Citations: <1% hallucinations (vs 5% avant)
   - Chunking: <5% chunks avec frontières incorrectes

📝 PROCHAINES ÉTAPES:
   1. Reprocesser tous les documents avec les nouvelles améliorations
   2. Tester avec des questions connues
   3. Vérifier les citations manuellement
   4. Ajuster les seuils si nécessaire
    """)


if __name__ == "__main__":
    print("\n" + "🔍 " + "="*76 + " 🔍")
    print("           TESTS DES AMÉLIORATIONS RAG")
    print("🔍 " + "="*76 + " 🔍")
    
    try:
        test_page_extraction()
        test_section_detection()
        test_chunk_quality()
        test_metadata_enrichment()
        print_summary()
        
        print("\n✅ Tous les tests sont terminés!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
