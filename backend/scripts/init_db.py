#!/usr/bin/env python3
"""
Script to initialize PostgreSQL database with pgvector extension.
Run this script after creating your PostgreSQL database.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings


def init_db():
    """Initialize the database with pgvector extension."""
    print(f"Connecting to database: {settings.database_url.split('@')[-1]}")
    
    try:
        engine = create_engine(settings.database_url)
        
        with engine.begin() as conn:  # Use begin() for auto-commit
            # Enable pgvector extension
            print("Enabling pgvector extension...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            print("✓ pgvector extension enabled")
            
            # Create all tables
            print("Creating tables...")
            from app.core.database import Base
            from app.models import document  # Import models to register them
            Base.metadata.create_all(bind=conn)
            print("✓ Tables created successfully")
            
            # Create index on embedding column for faster vector searches
            print("Creating indexes for performance...")
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
                    ON document_chunks 
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                """))
                print("✓ Vector index created successfully")
            except Exception as idx_error:
                # ivfflat might not be available, fallback to basic index
                print(f"⚠️  Could not create ivfflat index: {idx_error}")
                print("   Using basic index instead...")
                try:
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
                        ON document_chunks 
                        USING gin (embedding vector_cosine_ops)
                    """))
                    print("✓ GIN index created successfully")
                except Exception as gin_error:
                    print(f"⚠️  Could not create GIN index: {gin_error}")
                    print("   Continuing without index (slower searches)")
            
            # Create index on document_id for faster joins
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx 
                    ON document_chunks (document_id)
                """))
                print("✓ Document ID index created successfully")
            except Exception as e:
                print(f"⚠️  Could not create document_id index: {e}")
            
            print("✓ Indexes created")
            
        print("\n✅ Database initialized successfully!")
        
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        print("\nMake sure:")
        print("1. PostgreSQL is running")
        print("2. pgvector extension is installed: CREATE EXTENSION vector;")
        print("3. Database URL in .env is correct")
        sys.exit(1)


if __name__ == "__main__":
    init_db()
