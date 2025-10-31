#!/usr/bin/env python3
"""
Script to create indexes for better performance.
Run this if you already have a database but want to add indexes.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings


def create_indexes():
    """Create indexes for better performance."""
    print(f"Connecting to database: {settings.database_url.split('@')[-1]}")
    
    try:
        engine = create_engine(settings.database_url)
        
        with engine.begin() as conn:
            # Create index on embedding column for faster vector searches
            print("Creating indexes for performance...")
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
                    ON document_chunks 
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                """))
                print("✓ Vector index (ivfflat) created successfully")
            except Exception as idx_error:
                # ivfflat might not be available, fallback to basic index
                print(f"⚠️  Could not create ivfflat index: {idx_error}")
                print("   Trying GIN index instead...")
                try:
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
                        ON document_chunks 
                        USING gin (embedding vector_cosine_ops)
                    """))
                    print("✓ GIN index created successfully")
                except Exception as gin_error:
                    print(f"⚠️  Could not create GIN index: {gin_error}")
                    print("   Continuing without index (searches will be slower)")
            
            # Create index on document_id for faster joins
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx 
                    ON document_chunks (document_id)
                """))
                print("✓ Document ID index created successfully")
            except Exception as e:
                print(f"⚠️  Could not create document_id index: {e}")
            
            print("\n✅ Indexes created successfully!")
            
    except Exception as e:
        print(f"\n❌ Error creating indexes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    create_indexes()

