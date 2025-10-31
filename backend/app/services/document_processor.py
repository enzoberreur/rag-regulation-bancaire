"""
Service for processing documents: extracting text, chunking, and generating embeddings.
"""
import os
from typing import List
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
        
        # Text splitter with custom chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1050,  # ~900-1200 tokens (roughly 1.2 chars per token)
            chunk_overlap=100,
            length_function=self._count_tokens,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))
    
    async def process_document(self, document_id: str):
        """
        Process a document: extract text, chunk, and generate embeddings.
        
        Args:
            document_id: UUID of the document to process
        """
        # Get document
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found")
        
        # Extract text from file
        text = await self.text_extractor.extract_text(doc.file_path, doc.file_type)
        
        if not text.strip():
            raise ValueError("No text extracted from document")
        
        # Split into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Create LangChain documents for embedding
        langchain_docs = [
            LangchainDocument(page_content=chunk, metadata={"chunk_index": i})
            for i, chunk in enumerate(chunks)
        ]
        
        # Generate embeddings for all chunks
        embeddings = await self.embedding_service.generate_embeddings(
            [doc.page_content for doc in langchain_docs]
        )
        
        # Save chunks to database
        for i, (langchain_doc, embedding) in enumerate(zip(langchain_docs, embeddings)):
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
                },
            )
            self.db.add(chunk)
        
        # Mark document as processed
        doc.document_metadata = {"processed": True, "chunk_count": len(chunks)}
        self.db.commit()

