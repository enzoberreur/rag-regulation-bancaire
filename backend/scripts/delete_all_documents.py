#!/usr/bin/env python3
"""
Script to delete all documents from the database.
This will remove all documents and their chunks from the database.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.document import Document, DocumentChunk


def delete_all_documents():
    """Delete all documents and their chunks from the database."""
    print(f"Connecting to database: {settings.database_url.split('@')[-1]}")
    
    try:
        db = SessionLocal()
        
        # Count documents before deletion
        doc_count = db.query(Document).count()
        chunk_count = db.query(DocumentChunk).count()
        
        print(f"\nFound {doc_count} documents and {chunk_count} chunks")
        
        if doc_count == 0:
            print("✅ No documents to delete")
            return
        
        # Delete all chunks first (cascade should handle this, but doing it explicitly)
        print("\nDeleting all document chunks...")
        db.query(DocumentChunk).delete()
        
        # Delete all documents
        print("Deleting all documents...")
        db.query(Document).delete()
        
        # Commit changes
        db.commit()
        
        print(f"✅ Successfully deleted {doc_count} documents and {chunk_count} chunks")
        
        # Verify deletion
        remaining_docs = db.query(Document).count()
        remaining_chunks = db.query(DocumentChunk).count()
        
        if remaining_docs == 0 and remaining_chunks == 0:
            print("✅ Database is now empty - ready for fresh start!")
        else:
            print(f"⚠️  Warning: {remaining_docs} documents and {remaining_chunks} chunks still remain")
        
        db.close()
        
    except Exception as e:
        print(f"\n❌ Error deleting documents: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("⚠️  WARNING: This will delete ALL documents from the database!")
    print("This action cannot be undone.\n")
    
    response = input("Do you want to continue? (yes/no): ")
    if response.lower() != "yes":
        print("Cancelled.")
        sys.exit(0)
    
    delete_all_documents()

