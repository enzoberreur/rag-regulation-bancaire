"""
Script to search for specific text in document chunks.
Usage: python scripts/search_in_chunks.py "texte à chercher"
"""
import sys
from app.core.database import SessionLocal
from app.models.document import DocumentChunk

def search_text(query_text: str):
    """Search for text in chunks."""
    db = SessionLocal()
    
    # Search in chunk content
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.content.ilike(f"%{query_text}%")
    ).all()
    
    print(f"\n🔍 Recherche: '{query_text}'")
    print(f"📊 Résultats: {len(chunks)} chunks trouvés\n")
    
    for i, chunk in enumerate(chunks, 1):
        doc_name = chunk.chunk_metadata.get("document_name", "Unknown") if chunk.chunk_metadata else "Unknown"
        page = chunk.chunk_metadata.get("page", "?") if chunk.chunk_metadata else "?"
        
        print(f"{'='*80}")
        print(f"[{i}] Document: {doc_name}, Page: {page}")
        print(f"{'='*80}")
        
        # Highlight the found text
        content = chunk.content
        start_idx = content.lower().find(query_text.lower())
        if start_idx != -1:
            # Show context around the match
            context_start = max(0, start_idx - 100)
            context_end = min(len(content), start_idx + len(query_text) + 100)
            context = content[context_start:context_end]
            
            # Highlight the match
            match_start = start_idx - context_start
            match_end = match_start + len(query_text)
            highlighted = (
                context[:match_start] + 
                f">>>{context[match_start:match_end]}<<<" + 
                context[match_end:]
            )
            print(f"{highlighted}\n")
        else:
            print(f"{content[:300]}...\n")
    
    db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/search_in_chunks.py \"texte à chercher\"")
        sys.exit(1)
    
    search_text(sys.argv[1])
