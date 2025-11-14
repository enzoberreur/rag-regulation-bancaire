"""
Service for processing documents: extracting text, chunking, and generating embeddings.
"""
import os
import re
from typing import List, Optional
from sqlalchemy.orm import Session
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument
import tiktoken

from app.models.document import Document, DocumentChunk
from app.services.embedding_service import EmbeddingService
from app.services.text_extractor import TextExtractor
from app.core.config import settings


class SemanticSentenceChunker:
    """
    Chunking sémantique par phrases - approche professionnelle.
    Groupe N phrases ensemble avec overlap pour maintenir le contexte.
    """
    
    def __init__(self, sentences_per_chunk: int = 5, overlap: int = 1):
        """
        Args:
            sentences_per_chunk: Nombre de phrases par chunk
            overlap: Nombre de phrases en commun entre chunks consécutifs
        """
        self.sentences_per_chunk = sentences_per_chunk
        self.overlap = overlap
        
        # Patterns pour détecter les fins de phrases
        # Gère: ". ", "! ", "? " mais ignore "M. ", "Dr. ", etc.
        self.sentence_pattern = re.compile(
            r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+(?=[A-Z])'
        )
    
    def split_text(self, text: str) -> List[str]:
        """
        Découpe le texte en chunks de N phrases avec overlap.
        
        Args:
            text: Texte à découper
        
        Returns:
            Liste de chunks (strings)
        """
        # 1. Découper en phrases
        sentences = self._split_into_sentences(text)
        
        if not sentences:
            return []
        
        # 2. Grouper en chunks avec overlap
        chunks = []
        i = 0
        
        while i < len(sentences):
            # Prendre N phrases
            chunk_sentences = sentences[i:i + self.sentences_per_chunk]
            
            # Joindre en un seul chunk
            chunk = ' '.join(chunk_sentences)
            chunks.append(chunk.strip())
            
            # Avancer de (N - overlap) phrases
            step = max(1, self.sentences_per_chunk - self.overlap)
            i += step
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Découpe le texte en phrases individuelles.
        Gère les cas complexes (M., Dr., numéros, etc.)
        """
        # Nettoyer le texte
        text = text.strip()
        
        if not text:
            return []
        
        # Découper avec regex
        sentences = self.sentence_pattern.split(text)
        
        # Nettoyer chaque phrase
        cleaned = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Ignorer les phrases trop courtes
                cleaned.append(sentence)
        
        return cleaned


class DocumentProcessor:
    """Process documents for RAG."""
    
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.text_extractor = TextExtractor()
        
        # Initialize tokenizer for counting tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Initialize chunking strategy based on config
        if settings.chunking_strategy == "sentence":
            print(f"🔤 Using semantic sentence chunking: {settings.sentences_per_chunk} sentences/chunk, overlap={settings.sentence_overlap}")
            self.sentence_chunker = SemanticSentenceChunker(
                sentences_per_chunk=settings.sentences_per_chunk,
                overlap=settings.sentence_overlap
            )
            self.text_splitter = None
        else:
            print(f"🔢 Using token-based chunking: {settings.chunk_size} tokens, overlap={settings.chunk_overlap}")
            self.sentence_chunker = None
            # Text splitter with semantic chunking - ne coupe JAMAIS au milieu d'une phrase
            # Optimisé pour documents réglementaires : chunks plus courts, meilleur overlap
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
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
            
            # Split this page's content into chunks (sentence-based or token-based)
            if self.sentence_chunker:
                # Sentence-based chunking
                page_chunks = self.sentence_chunker.split_text(page_content)
            else:
                # Token-based chunking
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

