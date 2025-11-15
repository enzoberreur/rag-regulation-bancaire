#!/usr/bin/env python3
"""
Script pour reprocesser tous les documents avec les nouvelles améliorations RAG.
Efface les anciens chunks et régénère avec:
- Extraction correcte des numéros de page
- Détection améliorée des sections
- Chunking optimisé
- Métadonnées enrichies
"""
import sys
import os
import asyncio

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.document import Document, DocumentChunk
from app.services.document_processor import DocumentProcessor


async def reprocess_document(document_id: str, doc_name: str):
    """Retraite un document."""
    print(f"\n{'='*80}")
    print(f"📄 Retraitement: {doc_name}")
    print(f"{'='*80}")
    
    db = SessionLocal()
    
    try:
        # Supprimer les anciens chunks
        old_chunks_count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).count()
        
        print(f"   🗑️  Suppression de {old_chunks_count} anciens chunks...")
        
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete()
        db.commit()
        
        # Reprocesser avec les améliorations
        processor = DocumentProcessor(db)
        await processor.process_document(document_id)
        
        # Vérifier les nouveaux chunks
        new_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).all()
        
        # Statistiques
        chunks_with_section = sum(
            1 for c in new_chunks 
            if c.chunk_metadata and c.chunk_metadata.get('section')
        )
        
        chunks_with_page_extracted = sum(
            1 for c in new_chunks 
            if c.chunk_metadata and c.chunk_metadata.get('page_extracted')
        )
        
        print(f"\n   ✅ Résultats:")
        print(f"      Anciens chunks: {old_chunks_count}")
        print(f"      Nouveaux chunks: {len(new_chunks)}")
        print(f"      Avec section: {chunks_with_section} ({chunks_with_section/len(new_chunks)*100:.1f}%)")
        print(f"      Pages extraites: {chunks_with_page_extracted} ({chunks_with_page_extracted/len(new_chunks)*100:.1f}%)")
        
        # Afficher un exemple
        if new_chunks:
            example = new_chunks[0]
            print(f"\n   📋 Exemple de métadonnées:")
            if example.chunk_metadata:
                print(f"      Page: {example.chunk_metadata.get('page')}")
                print(f"      Page extraite: {example.chunk_metadata.get('page_extracted')}")
                print(f"      Position physique: {example.chunk_metadata.get('physical_position')}")
                section = example.chunk_metadata.get('section') if example.chunk_metadata else None
                section_display = section if section else "None"
                print(f"      Section: {section_display[:80]}")
        
        return {
            'success': True,
            'old_chunks': old_chunks_count,
            'new_chunks': len(new_chunks),
            'chunks_with_section': chunks_with_section,
            'chunks_with_page_extracted': chunks_with_page_extracted
        }
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        db.close()


async def main():
    """Retraite tous les documents."""
    print("\n" + "🔄 " + "="*76 + " 🔄")
    print("           RETRAITEMENT DE TOUS LES DOCUMENTS")
    print("🔄 " + "="*76 + " 🔄")
    
    db = SessionLocal()
    
    # Récupérer tous les documents
    documents = db.query(Document).all()
    
    print(f"\n📊 {len(documents)} documents à retraiter")
    
    db.close()
    
    # Confirmer
    response = input("\n⚠️  Cela va SUPPRIMER tous les chunks existants et les régénérer. Continuer? (oui/non): ")
    
    if response.lower() not in ['oui', 'yes', 'y', 'o']:
        print("❌ Annulé")
        return
    
    # Retraiter chaque document
    results = []
    total_old_chunks = 0
    total_new_chunks = 0
    total_sections = 0
    total_pages_extracted = 0
    
    for i, doc in enumerate(documents, 1):
        print(f"\n[{i}/{len(documents)}]", end=" ")
        result = await reprocess_document(str(doc.id), doc.name)
        results.append(result)
        
        if result['success']:
            total_old_chunks += result['old_chunks']
            total_new_chunks += result['new_chunks']
            total_sections += result['chunks_with_section']
            total_pages_extracted += result['chunks_with_page_extracted']
    
    # Résumé final
    print("\n" + "="*80)
    print("📊 RÉSUMÉ FINAL")
    print("="*80)
    
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"\n✅ Documents retraités avec succès: {successful}/{len(documents)}")
    if failed > 0:
        print(f"❌ Échecs: {failed}")
    
    print(f"\n📈 Statistiques globales:")
    print(f"   Total anciens chunks: {total_old_chunks}")
    print(f"   Total nouveaux chunks: {total_new_chunks}")
    print(f"   Différence: {total_new_chunks - total_old_chunks:+d} chunks")
    
    if total_new_chunks > 0:
        section_rate = (total_sections / total_new_chunks) * 100
        page_extracted_rate = (total_pages_extracted / total_new_chunks) * 100
        
        print(f"\n🎯 Qualité des améliorations:")
        print(f"   Chunks avec section: {total_sections} ({section_rate:.1f}%)")
        if section_rate >= 80:
            print(f"      ✅ Excellent! (objectif: 80%)")
        elif section_rate >= 50:
            print(f"      ⚠️  Acceptable (objectif: 80%)")
        else:
            print(f"      ❌ Insuffisant (objectif: 80%)")
        
        print(f"   Pages extraites du contenu: {total_pages_extracted} ({page_extracted_rate:.1f}%)")
        if page_extracted_rate >= 70:
            print(f"      ✅ Excellent! (objectif: 70%)")
        elif page_extracted_rate >= 40:
            print(f"      ⚠️  Acceptable (objectif: 70%)")
        else:
            print(f"      ❌ Insuffisant (objectif: 70%)")
    
    print("\n✅ Retraitement terminé!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
