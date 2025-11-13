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
            chunk_overlap=200,  # 19% overlap (augmenté de 150 à 200) pour meilleur contexte
            length_function=self._count_tokens,
            # Ordre de priorité : sections > paragraphes > phrases > mots
            separators=[
                "\n\n\n",           # Sections multiples
                "\n\n",             # Paragraphes
                "\nARTICLE ",       # 🔥 Début d'article (réglementaire)
                "\nArticle ",       # 🔥 Début d'article (minuscule)
                "\nSECTION ",       # 🔥 Début de section
                "\nSection ",       # 🔥 Début de section (minuscule)
                "\nCHAPITRE ",      # 🔥 Début de chapitre
                "\nChapitre ",      # 🔥 Début de chapitre (minuscule)
                "\n\n",             # Double saut (répété pour priorité)
                "\n",               # Lignes simples
                ". ",               # Phrases (avec espace après le point)
                "! ",               # Phrases exclamatives
                "? ",               # Phrases interrogatives
                "; ",               # Points-virgules
                ", ",               # Virgules (dernier recours)
                " ",                # Mots
                ""                  # Caractères (évité grâce aux autres)
            ],
        )
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))
    
    def _clean_chunk_boundaries(self, chunk: str) -> str:
        """
        Nettoie les frontières de chunk pour éviter les coupures en plein milieu.
        
        Règles:
        - Si le chunk commence en minuscule (milieu de phrase) → trouver la première phrase complète
        - Si le chunk finit sans ponctuation → supprimer la phrase incomplète
        """
        if not chunk or len(chunk) < 50:
            return chunk
        
        original_length = len(chunk)
        
        # 1. Nettoyer le début si ça commence au milieu d'une phrase
        if chunk[0].islower() or (len(chunk) > 1 and chunk[0] == ' ' and chunk[1].islower()):
            # Trouver le premier point suivi d'une majuscule
            import re
            match = re.search(r'[\.\!\?]\s+[A-ZÀ-Ÿ]', chunk)
            if match:
                # Garder à partir de la majuscule
                chunk = chunk[match.start() + match.group().index(match.group()[-1]):]
        
        # 2. Nettoyer la fin si ça finit au milieu d'une phrase
        if chunk and not chunk[-1] in '.!?\n':
            # Trouver le dernier point avant la fin
            last_period_idx = max(
                chunk.rfind('.'),
                chunk.rfind('!'),
                chunk.rfind('?')
            )
            
            # Garder seulement si on ne perd pas plus de 30% du chunk
            if last_period_idx > len(chunk) * 0.7:
                chunk = chunk[:last_period_idx + 1]
        
        # Log si on a coupé beaucoup
        if len(chunk) < original_length * 0.8:
            chars_removed = original_length - len(chunk)
            # print(f"   ✂️  Chunk boundary cleaned: removed {chars_removed} chars")
        
        return chunk.strip()
    
    def _detect_section_title(self, text: str) -> Optional[str]:
        """
        Détecte si le texte commence par un titre de section.
        Patterns typiques : "Article 5", "Section 3.2.1", "CHAPITRE II", etc.
        
        Amélioration: patterns étendus pour détecter plus de sections.
        """
        import re
        
        # Prendre les 5 premières lignes (au lieu de 3)
        first_lines = text.strip().split('\n')[:5]
        
        for line in first_lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Pattern 1: Mots-clés de section (haute priorité)
            section_keywords = [
                'ARTICLE', 'CHAPITRE', 'CHAPTER', 'SECTION', 'TITRE', 'TITLE', 'PARTIE', 'PART',
                'ANNEXE', 'ANNEX', 'APPENDIX', 'INTRODUCTION', 'CONCLUSION',
                'DÉFINITIONS', 'DEFINITIONS', 'GLOSSAIRE', 'GLOSSARY',
                'PRÉAMBULE', 'PREAMBLE', 'RÉSUMÉ', 'SUMMARY', 'ABSTRACT'
            ]
            line_upper = line.upper()
            if any(kw in line_upper for kw in section_keywords):
                return line[:150]  # Max 150 chars
            
            # Pattern 2: Numérotation classique avec chiffres romains ou arabes
            if re.match(r'^[IVX\d]+[\.\)\s]+[A-ZÀ-Ÿ]', line):
                return line[:150]
            
            # Pattern 3: Format "X.Y.Z Titre" (multi-niveau)
            if re.match(r'^\d+(\.\d+)*\s+[A-ZÀ-Ÿ]', line):
                return line[:150]
            
            # Pattern 4: Ligne entière en majuscules (probable titre)
            # Mais pas si c'est juste des acronymes ou trop court
            if len(line) > 15 and line.isupper() and not line.endswith('.') and line.count(' ') >= 2:
                return line[:150]
            
            # Pattern 5: Commence par un numéro + point + espace
            if re.match(r'^\d+\.\s+[A-ZÀ-Ÿ].{5,}', line):
                return line[:150]
            
            # Pattern 6: Format réglementaire "Article X.Y :" ou "Section X :"
            if re.match(r'^(Article|Section|Chapitre|Partie)\s+[\dIVX]+(\.\d+)?\s*:', line, re.IGNORECASE):
                return line[:150]
        
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
                # 🔥 Nettoyer les frontières du chunk
                chunk_clean = self._clean_chunk_boundaries(chunk)
                
                # Skip si le chunk est devenu trop petit après nettoyage
                if len(chunk_clean) < 100:
                    continue
                
                # Détecter si le chunk contient un titre de section
                section_title = self._detect_section_title(chunk_clean)
                
                # Récupérer les métadonnées de page
                page_extracted = page_info.get("page_extracted", False)
                physical_position = page_info.get("physical_position", page_num)
                
                langchain_docs.append(
                    LangchainDocument(
                        page_content=chunk_clean,
                        metadata={
                            "chunk_index": chunk_index,
                            "page": page_num,
                            "page_extracted": page_extracted,  # 🔥 Info si numéro extrait ou physique
                            "physical_position": physical_position,  # 🔥 Position physique dans le PDF
                            "section": section_title  # 🔥 Titre de section
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
                    "page": langchain_doc.metadata.get("page"),  # Page number (real or physical)
                    "page_extracted": langchain_doc.metadata.get("page_extracted", False),  # 🔥 True si extrait du contenu
                    "physical_position": langchain_doc.metadata.get("physical_position"),  # 🔥 Position physique dans PDF
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

