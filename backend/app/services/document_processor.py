"""
Service for processing documents: extracting text, chunking, and generating embeddings.
"""
import os
from typing import List, Optional
from sqlalchemy.orm import Session
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument
import tiktoken

from app.models.document import Document, DocumentChunk
from app.services.embedding_service import EmbeddingService
from app.services.text_extractor import TextExtractor


class DocumentProcessor:
    """Process documents for RAG."""
    
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.text_extractor = TextExtractor()
        
        # Initialize tokenizer for counting tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Text splitter with semantic chunking - ne coupe JAMAIS au milieu d'une phrase
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1050,  # ~900-1200 tokens (roughly 1.2 chars per token)
            chunk_overlap=150,  # Plus d'overlap pour garder le contexte
            length_function=self._count_tokens,
            # Ordre de priorité : sections > paragraphes > phrases > mots
            separators=[
                "\n\n\n",  # Sections multiples
                "\n\n",    # Paragraphes
                "\n",      # Lignes
                ". ",      # Phrases (avec espace après le point)
                "! ",      # Phrases exclamatives
                "? ",      # Phrases interrogatives
                "; ",      # Points-virgules
                ", ",      # Virgules (dernier recours)
                " ",       # Mots
                ""         # Caractères (évité grâce aux autres)
            ],
        )
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))
    
    def _detect_section_title(self, text: str) -> Optional[str]:
        """
        Détecte si le texte commence par un titre de section.
        Patterns typiques : "Article 5", "Section 3.2.1", "CHAPITRE II", etc.
        """
        import re
        
        # Prendre les premières lignes
        first_lines = text.strip().split('\n')[:3]
        
        for line in first_lines:
            line = line.strip()
            if not line:
                continue
            
            # Patterns de titres courants
            patterns = [
                r'^(ARTICLE|Article|CHAPITRE|Chapitre|SECTION|Section|TITRE|Titre)\s+[IVX\d]+',
                r'^[IVX\d]+\.\s+[A-Z]',  # "3. TITRE"
                r'^[IVX\d]+\.[IVX\d]+',  # "3.2.1"
                r'^[A-Z][A-Z\s]{5,}$',   # TITRE EN MAJUSCULES (au moins 5 chars)
            ]
            
            for pattern in patterns:
                if re.match(pattern, line):
                    return line[:100]  # Max 100 chars pour le titre
        
        return None
    
    async def process_document(self, document_id: str):
        """
        Process a document: extract text, chunk, and generate embeddings.
        Uses optimized batch processing for faster embedding generation.
        
        Args:
            document_id: UUID of the document to process
        """
        # Get document
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found")
        
        print(f"📄 Processing document: {doc.name}")
        
        # Extract text from file with page information
        print(f"   ⏳ Extracting text with page info...")
        pages = await self.text_extractor.extract_text_with_pages(doc.file_path, doc.file_type)
        
        if not pages:
            raise ValueError("No text extracted from document")
        
        total_chars = sum(len(p["content"]) for p in pages)
        print(f"   ✅ Extracted {total_chars} characters from {len(pages)} pages")
        
        # Split into chunks while preserving page information
        print(f"   ⏳ Splitting into chunks...")
        langchain_docs = []
        chunk_index = 0
        
        for page_info in pages:
            page_num = page_info["page"]
            page_content = page_info["content"]
            
            # Split this page's content into chunks
            page_chunks = self.text_splitter.split_text(page_content)
            
            for chunk in page_chunks:
                # Détecter si le chunk contient un titre de section
                section_title = self._detect_section_title(chunk)
                
                langchain_docs.append(
                    LangchainDocument(
                        page_content=chunk,
                        metadata={
                            "chunk_index": chunk_index,
                            "page": page_num,
                            "section": section_title  # 🔥 Ajout du titre de section
                        }
                    )
                )
                chunk_index += 1
        
        print(f"   ✅ Created {len(langchain_docs)} chunks")
        
        # Generate embeddings in optimized batches
        print(f"   ⏳ Generating embeddings (batch size: 32)...")
        batch_size = 32  # Process 32 chunks at a time for optimal performance
        all_embeddings = []
        
        for i in range(0, len(langchain_docs), batch_size):
            batch = langchain_docs[i:i + batch_size]
            batch_texts = [doc.page_content for doc in batch]
            
            # Generate embeddings for this batch
            batch_embeddings = await self.embedding_service.generate_embeddings(batch_texts)
            all_embeddings.extend(batch_embeddings)
            
            # Progress feedback
            progress = min(i + batch_size, len(langchain_docs))
            print(f"      Progress: {progress}/{len(langchain_docs)} chunks ({int(progress/len(langchain_docs)*100)}%)")
        
        print(f"   ✅ Generated {len(all_embeddings)} embeddings")
        
        # Save chunks to database in batches (faster than one by one)
        print(f"   ⏳ Saving to database...")
        chunk_objects = []
        for i, (langchain_doc, embedding) in enumerate(zip(langchain_docs, all_embeddings)):
            token_count = self._count_tokens(langchain_doc.page_content)
            
            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=i,
                content=langchain_doc.page_content,
                token_count=token_count,
                embedding=embedding,
                chunk_metadata={
                    "document_name": doc.name,
                    "document_type": doc.document_type,
                    "page": langchain_doc.metadata.get("page"),  # Page number
                    "section": langchain_doc.metadata.get("section"),  # 🔥 Section title
                },
            )
            chunk_objects.append(chunk)
        
        # Bulk insert for better performance
        self.db.bulk_save_objects(chunk_objects)
        
        # Mark document as processed
        doc.document_metadata = {"processed": True, "chunk_count": len(langchain_docs)}
        self.db.commit()
        
        print(f"✅ Document processed successfully: {doc.name} ({len(langchain_docs)} chunks)")
        print()

