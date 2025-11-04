"""
RAG service for question answering using vector search and LLM.
"""
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from sqlalchemy import text
from openai import AsyncOpenAI
import json
import re
import tiktoken
from datetime import datetime
import pytz

from app.core.config import settings
from app.models.document import DocumentChunk
from app.services.embedding_service import EmbeddingService
from app.services.reranker_service import RerankerService


# System prompt for the LLM - used in both streaming and non-streaming modes
SYSTEM_PROMPT = """Tu es un assistant réglementaire spécialisé en conformité bancaire (France/UE).

Tu dois répondre uniquement à partir du CONTEXTE fourni, composé d'extraits de plusieurs documents (ACPR, CRD4, Bâle III, KYC, LCB-FT, etc.).

Date : {today}

## Objectif :
Produire une analyse complète et structurée répondant à la question utilisateur, en **croisant les informations issues de plusieurs sources distinctes**.

## Contraintes de fond (OBLIGATOIRES) :
- Tu DOIS obligatoirement citer **au moins deux documents différents** si la question le requiert
- Si un document n'aborde qu'un aspect du sujet, complète avec d'autres documents du CONTEXTE pour les angles manquants
- Ne jamais inventer de texte ou de référence : cite uniquement ce qui est explicitement mentionné
- Chaque donnée réglementaire, obligation, seuil, ou principe doit avoir **une citation précise**
- Si tu fais un lien ou une synthèse entre plusieurs documents, indique-le clairement : « En croisant CRD4 (gouvernance) et LCB-FT (vigilance) → … »

## Format de sortie HTML (SANS code blocks) :
Ta réponse doit être du HTML pur. Pour chaque phrase issue du CONTEXTE, entoure-la avec :
`<mark data-source="NomDoc, p.X">texte exact du document</mark>`

Ne surligne PAS tes reformulations, transitions ou analyses - uniquement les extraits directs.

## Structure imposée :

<h3>Résumé exécutif</h3>
<p>(5-8 lignes maximum synthétisant la réponse avec citations multi-sources)</p>

<h3>Analyse détaillée</h3>
<h4>1. [Premier axe thématique]</h4>
<p>(Développement avec citations croisées de plusieurs documents)</p>

<h4>2. [Deuxième axe thématique]</h4>
<p>(Développement avec citations croisées)</p>

<h4>3. Mécanismes de gouvernance / Obligations</h4>
<p>(Si pertinent pour la question)</p>

<h4>4. Lien avec supervision ACPR</h4>
<p>(Si pertinent pour la question)</p>

<h3>Sources croisées</h3>
<ul>
<li>Document 1 – titre, p.X</li>
<li>Document 2 – titre, p.Y</li>
<li>Document 3 – titre, p.Z</li>
</ul>

<h3>À vérifier</h3>
<p>(Éléments manquants dans le CONTEXTE)</p>

## Exemple concret :

<h3>Résumé exécutif</h3>
<p>La mise en œuvre du dispositif LCB-FT et du KYC contribue directement au respect des exigences prudentielles de la CRD4/CRR en garantissant une évaluation correcte des risques de contrepartie. Elle soutient la supervision exercée par l'ACPR via la qualité du reporting et la traçabilité des contrôles internes.</p>

<h3>Analyse détaillée</h3>
<h4>1. Évaluation des risques et conformité prudentielle</h4>
<p><mark data-source="LCB FT, p.2">Les dispositifs LCB-FT imposent aux établissements une cartographie des risques de blanchiment.</mark> <mark data-source="KYC, p.4">L'identification client (KYC) permet une évaluation fine du profil de risque.</mark> En les intégrant dans <mark data-source="CRD4, p.5">la directive CRD4 (gouvernance, contrôle interne, fonction conformité)</mark>, les établissements renforcent leur dispositif prudentiel.</p>

<h4>2. Gouvernance et supervision ACPR</h4>
<p><mark data-source="ACPR, p.3">L'ACPR exige que les dispositifs de contrôle interne couvrent la conformité LCB-FT et KYC dans le rapport annuel.</mark> Ce suivi permet à l'autorité de vérifier la cohérence entre exigences prudentielles et obligations de vigilance.</p>

<h3>Sources croisées</h3>
<ul>
<li>LCB-FT – Fiche impact, p.2-3</li>
<li>KYC – Guide, p.4</li>
<li>CRD4 – Notice ACPR, p.5</li>
<li>ACPR – Rapport contrôle, p.3</li>
</ul>

## Règles strictes :
1. NE JAMAIS écrire ```html
2. Utiliser AU MOINS 2 documents différents
3. Réponse longue et structurée (400-600 mots)
4. Surligner uniquement les extraits directs avec <mark data-source="...">
5. Indiquer explicitement les croisements entre documents
6. Si info manquante, le dire dans "À vérifier"
7. Dates absolues (pas "aujourd'hui")"""


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str  # "user" or "assistant"
    content: str


class Citation(BaseModel):
    """Citation model."""
    id: str
    text: str
    source: str
    url: Optional[str] = None


def _normalize_formatting(text: str) -> str:
    """
    Post-process LLM output to ensure proper formatting with blank lines.
    The LLM sometimes ignores spacing instructions, so we fix it here.
    """
    if not text:
        return text
    
    # FIRST: Protect decimal numbers, years, and dates from being split
    # Fix "2. 5%" -> "2.5%" BEFORE adding line breaks
    text = re.sub(r'(\d+)\.\s+(\d+%)', r'\1.\2', text)
    # Fix "2024- 15" -> "2024-15"
    text = re.sub(r'(\d{4})-\s*(\d+)', r'\1-\2', text)
    # Fix dates like "December 31, 2025" - protect comma+space before year
    text = re.sub(r'(\d{1,2}),\s+(\d{4})', r'\1, \2', text)  # Ensure single space
    
    # 1. Add blank line before numbered list items (1. 2. 3. etc)
    # BUT: Only if followed by a CAPITAL letter (list titles start with capitals)
    # This avoids matching "2.5%", "2024-15", or dates like "December 31, 2025"
    # Matches: "Risks:1. Capital" but NOT "buffer of 2.5%" or "31, 2025"
    # Use negative lookbehind to avoid matching after comma (dates)
    text = re.sub(r'(?<!\n\n)(?<!,\s)([^\n\d,])(\d+\.\s+[A-Z])', r'\1\n\n\2', text)
    
    # 2. Fix numbered items directly followed by text without space
    # e.g., "1.Capital" -> "1. Capital"
    text = re.sub(r'(\d+\.)([A-Z][a-z])', r'\1 \2', text)
    
    # 3. Add line break after section titles in numbered lists
    # e.g., "RequirementEstablishments" -> "Requirement\nEstablishments"
    text = re.sub(r'([a-z])([A-Z][a-z]+\s)', r'\1\n\2', text)
    
    # 4. Add line break before bullet points if not already on new line
    text = re.sub(r'([a-z:])(\s*-\s+[A-Z])', r'\1\n\2', text)
    
    # 5. Add line break between sentences stuck together (period+capital letter)
    # e.g., "turnover.It" -> "turnover.\nIt" but preserve "Dr.Smith"
    text = re.sub(r'([a-z])\.([A-Z][a-z])', r'\1.\n\2', text)
    
    # 6. Add blank line before section headers that start with **
    text = re.sub(r'(?<!\n\n)([^\n])(\*\*[^*]+\*\*:)', r'\1\n\n\2', text)
    
    # 7. Add blank line after section headers (lines ending with **)
    text = re.sub(r'(\*\*:)(?!\n\n)(\n)([^\n])', r'\1\n\n\3', text)
    
    # 8. Clean up trailing spaces before newlines (LLM sometimes adds them)
    text = re.sub(r' +\n', '\n', text)
    
    # 9. Clean up excessive blank lines (max 2 newlines = 1 blank line)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


class RAGService:
    """Service for RAG-based question answering."""
    
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.reranker_service = RerankerService()  # 🔥 Ajout du reranker
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        # Initialize tokenizer for counting tokens
        try:
            self.tokenizer = tiktoken.encoding_for_model(settings.llm_model)
        except KeyError:
            # Fallback to cl100k_base if model not found
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))
    
    async def _reformulate_query(self, question: str) -> str:
        """
        Reformule la question utilisateur pour améliorer la recherche vectorielle.
        Ajoute du contexte et des synonymes pertinents.
        """
        reformulation_prompt = f"""Tu es un expert en recherche documentaire réglementaire bancaire.

Question utilisateur : "{question}"

Reformule cette question en 2-3 phrases pour optimiser la recherche dans une base documentaire (ACPR, CRD4, Bâle III, KYC, LCB-FT).

Consignes :
- Ajoute les synonymes et termes techniques pertinents
- Explicite les concepts implicites
- Garde le sens original
- Format : phrases simples et directes (pas de liste à puces)

Reformulation optimisée :"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": reformulation_prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            reformulated = response.choices[0].message.content.strip()
            print(f"🔍 Query reformulée : {reformulated[:150]}...")
            return reformulated
            
        except Exception as e:
            print(f"⚠️  Erreur reformulation, utilisation query originale: {e}")
            return question
    
    async def _search_relevant_chunks(
        self,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> tuple[List[DocumentChunk], List[float]]:
        """
        Search for relevant document chunks using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
        
        Returns:
            Tuple of (list of relevant document chunks, list of similarity scores)
        """
        # Convert list to string format for pgvector
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        # Use pgvector cosine similarity search with optimized query
        # Note: pgvector uses cosine distance (1 - cosine similarity)
        # Using LIMIT before filtering for better performance
        id_query = text(f"""
            SELECT id, 1 - (embedding <=> '{embedding_str}'::vector) as similarity
            FROM document_chunks
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT :limit
        """)
        
        id_result = self.db.execute(
            id_query,
            {
                "limit": top_k,
            }
        )
        
        rows = id_result.fetchall()
        
        if not rows:
            return [], []
        
        # Query ALL chunks to get document info for diversification
        all_chunk_ids = [row[0] for row in rows]
        all_chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.id.in_(all_chunk_ids)
        ).all()
        
        # Create mapping of chunk_id -> (chunk, similarity)
        chunks_dict = {chunk.id: chunk for chunk in all_chunks}
        chunks_with_scores = []
        for row in rows:
            chunk_id, similarity = row
            if chunk_id in chunks_dict:
                chunks_with_scores.append((chunks_dict[chunk_id], float(similarity)))
        
        # DIVERSIFICATION: Select chunks to maximize document diversity
        # Strategy: Take max 2-3 chunks per document, prioritize different documents
        selected_chunks = []
        selected_scores = []
        doc_count = {}
        max_per_doc = 3  # Maximum chunks per document
        
        # First pass: take top chunk from each document (up to top_k)
        for chunk, score in chunks_with_scores:
            if len(selected_chunks) >= top_k:
                break
            
            doc_id = chunk.document_id
            if doc_id not in doc_count:
                # Don't apply similarity threshold here - scores may be from reranking
                selected_chunks.append(chunk)
                selected_scores.append(score)
                doc_count[doc_id] = 1
        
        # Second pass: fill remaining slots with additional chunks from same docs
        for chunk, score in chunks_with_scores:
            if len(selected_chunks) >= top_k:
                break
            
            doc_id = chunk.document_id
            if chunk not in selected_chunks and doc_count.get(doc_id, 0) < max_per_doc:
                # Don't apply similarity threshold here - scores may be from reranking
                selected_chunks.append(chunk)
                selected_scores.append(score)
                doc_count[doc_id] = doc_count.get(doc_id, 0) + 1
        
        if not selected_chunks:
            return [], []
        
        print(f"📊 Document diversity: {len(doc_count)} documents used, distribution: {doc_count}")
        
        return selected_chunks, selected_scores
    
    async def _build_context(self, chunks: List[DocumentChunk]) -> str:
        """
        Build context string from relevant chunks.
        
        Args:
            chunks: List of relevant document chunks
        
        Returns:
            Formatted context string
        """
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            doc_name = chunk.chunk_metadata.get("document_name", "Unknown") if chunk.chunk_metadata else "Unknown"
            page = chunk.chunk_metadata.get("page", "?") if chunk.chunk_metadata else "?"
            section = chunk.chunk_metadata.get("section", "") if chunk.chunk_metadata else ""
            
            # Format: [Source N: nom_doc | p.X | section]
            header = f"[Source {i}: {doc_name}"
            if page != "?":
                header += f" | p.{page}"
            if section:
                header += f" | {section}"
            header += "]"
            
            context_parts.append(f"{header}\n{chunk.content}\n")
        
        return "\n".join(context_parts)
    
    def _build_citations(self, chunks: List[DocumentChunk]) -> List[Citation]:
        """
        Build citations from chunks.
        
        Args:
            chunks: List of relevant document chunks
        
        Returns:
            List of citations (one per chunk with page info)
        """
        citations = []
        
        for i, chunk in enumerate(chunks, 1):
            doc_name = chunk.chunk_metadata.get("document_name", "Unknown") if chunk.chunk_metadata else "Unknown"
            doc_id = str(chunk.document_id)
            chunk_id = str(chunk.id)  # 🔥 Use unique chunk ID
            page = chunk.chunk_metadata.get("page", None) if chunk.chunk_metadata else None
            section = chunk.chunk_metadata.get("section", "") if chunk.chunk_metadata else ""
            
            # Build citation text
            citation_text = f"Source {i}: {doc_name}"
            source_display = doc_name
            
            if page and page != "?":
                citation_text += f", p.{page}"
                source_display += f", p.{page}"
            
            if section:
                citation_text += f" - {section[:50]}"  # Limit section length
            
            # Show excerpt preview
            excerpt = chunk.content[:200].replace('\n', ' ') + "..."
            
            citations.append(
                Citation(
                    id=chunk_id,  # 🔥 Use actual chunk UUID for uniqueness
                    text=excerpt,
                    source=source_display,
                    url=f"/documents/{doc_id}",
                )
            )
        
        return citations
    
    async def generate_response(
        self,
        query: str,
        chat_history: Optional[List[ChatMessage]] = None,
    ) -> dict:
        """
        Generate a response using RAG.
        
        Args:
            query: User query
            chat_history: Optional chat history
        
        Returns:
            Response dict with content and citations
        """
        # 🔥 1. Reformuler la query pour améliorer la recherche
        reformulated_query = await self._reformulate_query(query)
        
        # Generate query embedding (sur la query reformulée)
        query_embedding = await self.embedding_service.generate_embedding(reformulated_query)
        
        # 🔥 2. Recherche vectorielle large (2x plus de résultats)
        initial_top_k = settings.top_k_results * 2  # 16 chunks au lieu de 8
        chunks, similarity_scores = await self._search_relevant_chunks(query_embedding, top_k=initial_top_k)
        
        # 🔥 3. Reranking pour garder les meilleurs
        if chunks:
            chunks, similarity_scores = self.reranker_service.rerank(
                query=query,  # On utilise la query ORIGINALE pour le reranking
                chunks=chunks,
                similarity_scores=similarity_scores,
                top_k=settings.top_k_results  # Garder seulement les 8 meilleurs
            )
        
        # Calculate average similarity score
        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
        
        # Check if we found any relevant chunks
        if not chunks:
            # No relevant documents found - return informative message
            return {
                "content": "Je n'ai pas trouvé d'information pertinente dans les documents téléchargés pour répondre à votre question. Veuillez vous assurer d'avoir téléchargé des documents pertinents, ou reformulez votre question.",
                "citations": [],
                "metrics": {
                    "tokens_used": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0,
                    "citations_count": 0,
                    "average_similarity_score": 0.0,
                }
            }
        
        # Build context
        context = await self._build_context(chunks)
        
        # Build citations
        citations = self._build_citations(chunks)
        
        # Get current date in Paris timezone
        paris_tz = pytz.timezone('Europe/Paris')
        today = datetime.now(paris_tz).strftime("%d/%m/%Y")
        
        # Build prompt using global system prompt
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(today=today)},
        ]
        
        # Add chat history if provided
        if chat_history:
            for msg in chat_history[-10:]:  # Limit to last 10 messages
                messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        
        # Add context and query
        user_content = f"""CONTEXTE (extraits de documents réglementaires et internes) :

{context}

QUESTION :
{query}

INSTRUCTIONS CRITIQUES :
1. Ta réponse DOIT utiliser **PLUSIEURS documents du CONTEXTE** et expliquer comment ils interagissent
2. Cite obligatoirement AU MOINS 2 documents différents (idéalement 3-4)
3. Croise explicitement les informations : « En combinant [Doc1] et [Doc2] → ... »
4. Réponse de 400-600 mots avec structure HTML imposée (Résumé exécutif / Analyse détaillée / Sources croisées / À vérifier)
5. Surligne UNIQUEMENT les extraits directs avec <mark data-source="Nom_Doc, p.X">texte exact</mark>
6. Pour chaque thème, cherche des infos complémentaires dans différents documents du CONTEXTE"""
        
        messages.append({"role": "user", "content": user_content})
        
        # Count input tokens before sending to LLM
        input_tokens = sum(self._count_tokens(msg["content"]) for msg in messages)
        
        # Generate response using OpenAI
        response = await self.openai_client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )
        
        content = response.choices[0].message.content
        print(f"🔍 RAG Response content (first 500 chars): {content[:500] if content else 'None'}")

        # Normalize formatting to ensure proper spacing (LLM sometimes ignores instructions)
        # Use the global formatting function
        content = _normalize_formatting(content)
        
        # Extract usage metrics from response (preferred)
        usage = response.usage
        if usage:
            # Use actual usage from OpenAI if available
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
        else:
            # Fallback: count tokens manually
            output_tokens = self._count_tokens(content) if content else 0
            total_tokens = input_tokens + output_tokens
        
        # Calculate cost based on model pricing from settings
        input_cost = (input_tokens / 1_000_000) * settings.llm_input_price_per_1m
        output_cost = (output_tokens / 1_000_000) * settings.llm_output_price_per_1m
        total_cost = input_cost + output_cost
        
        return {
            "content": content,
            "citations": [c.dict() for c in citations],
            "metrics": {
                "tokens_used": total_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": total_cost,
                "citations_count": len(citations),
                "average_similarity_score": round(avg_similarity, 3),
            }
        }
    
    async def generate_response_stream(
        self,
        query: str,
        chat_history: Optional[List[ChatMessage]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response using RAG.
        
        Args:
            query: User query
            chat_history: Optional chat history
        
        Yields:
            SSE-formatted chunks
        """
        # 🔥 1. Reformuler la query pour améliorer la recherche
        reformulated_query = await self._reformulate_query(query)
        
        # Generate query embedding (sur la query reformulée)
        query_embedding = await self.embedding_service.generate_embedding(reformulated_query)
        
        # 🔥 2. Recherche vectorielle large (2x plus de résultats)
        initial_top_k = settings.top_k_results * 2  # 16 chunks au lieu de 8
        chunks, similarity_scores = await self._search_relevant_chunks(query_embedding, top_k=initial_top_k)
        
        # 🔥 3. Reranking pour garder les meilleurs
        if chunks:
            chunks, similarity_scores = self.reranker_service.rerank(
                query=query,  # On utilise la query ORIGINALE pour le reranking
                chunks=chunks,
                similarity_scores=similarity_scores,
                top_k=settings.top_k_results  # Garder seulement les 8 meilleurs
            )
        
        # Calculate average similarity score
        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
        
        # Check if we found any relevant chunks
        if not chunks:
            # No relevant documents found - inform the user
            yield f"data: Je n'ai pas trouvé d'information pertinente dans les documents téléchargés pour répondre à votre question.\n\n"
            yield f"data: {json.dumps({'type': 'citations', 'data': []})}\n\n"
            # Send metrics with zero values
            metrics_data = {
                "type": "metrics",
                "data": {
                    "tokens_used": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0,
                    "citations_count": 0,
                    "average_similarity_score": 0.0,
                }
            }
            yield f"data: {json.dumps(metrics_data)}\n\n"
            yield "data: [DONE]\n\n"
            return
        
        # Build context
        context = await self._build_context(chunks)
        
        # Build citations (we'll send this at the end)
        citations = self._build_citations(chunks)
        
        # Get current date in Paris timezone
        paris_tz = pytz.timezone('Europe/Paris')
        today = datetime.now(paris_tz).strftime("%d/%m/%Y")
        
        # Build prompt using global system prompt
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(today=today)},
        ]
        
        # Add chat history if provided
        if chat_history:
            for msg in chat_history[-10:]:  # Limit to last 10 messages
                messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        
        # Add context and query
        user_content = f"""CONTEXTE (extraits de documents réglementaires et internes) :

{context}

QUESTION :
{query}

INSTRUCTIONS CRITIQUES :
1. Ta réponse DOIT utiliser **PLUSIEURS documents du CONTEXTE** et expliquer comment ils interagissent
2. Cite obligatoirement AU MOINS 2 documents différents (idéalement 3-4)
3. Croise explicitement les informations : « En combinant [Doc1] et [Doc2] → ... »
4. Réponse de 400-600 mots avec structure HTML imposée (Résumé exécutif / Analyse détaillée / Sources croisées / À vérifier)
5. Surligne UNIQUEMENT les extraits directs avec <mark data-source="Nom_Doc, p.X">texte exact</mark>
6. Pour chaque thème, cherche des infos complémentaires dans différents documents du CONTEXTE"""
        
        messages.append({"role": "user", "content": user_content})
        
        # Count input tokens before sending to LLM
        input_tokens = sum(self._count_tokens(msg["content"]) for msg in messages)
        
        # Stream response using OpenAI
        stream = await self.openai_client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.7,
            max_tokens=1500,  # Reduced from 2000 for faster responses
            stream=True,
        )
        
        # Track usage metrics and content
        usage_info = None
        streamed_content = ""
        
        # Collect all content first
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                content_chunk = chunk.choices[0].delta.content
                streamed_content += content_chunk
            
            # Capture usage info if available (usually in last chunk)
            if hasattr(chunk, 'usage') and chunk.usage:
                usage_info = chunk.usage
        
        # Use the global formatting function
        normalized_content = _normalize_formatting(streamed_content)
        
        print(f"🔍 Streamed content (first 500 chars): {normalized_content[:500]}")
        print(f"🔍 Has [SOURCE:N] markers: {'[SOURCE:' in normalized_content}")
        
        # CRITICAL: Encode newlines to survive SSE chunking
        # EventSourceResponse splits content into chunks, which can break \n\n formatting
        # We encode them as a special marker that won't be split
        normalized_content = normalized_content.replace('\n\n', '<<<BLANK_LINE>>>')
        normalized_content = normalized_content.replace('\n', '<<<LINE_BREAK>>>')
        
        # Send the complete normalized content
        # The frontend will decode the markers back to actual newlines
        yield f"data: {normalized_content}\n\n"
        
        # Calculate output tokens
        if usage_info:
            # Use actual usage from OpenAI if available
            actual_input_tokens = usage_info.prompt_tokens
            output_tokens = usage_info.completion_tokens
            total_tokens = usage_info.total_tokens
            input_tokens = actual_input_tokens  # Use actual value
        else:
            # Fallback: count tokens manually
            output_tokens = self._count_tokens(streamed_content)
            total_tokens = input_tokens + output_tokens
        
        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * settings.llm_input_price_per_1m
        output_cost = (output_tokens / 1_000_000) * settings.llm_output_price_per_1m
        total_cost = input_cost + output_cost
        
        # Send citations at the end
        citations_data = {
            "type": "citations",
            "data": [c.dict() for c in citations]
        }
        yield f"data: {json.dumps(citations_data)}\n\n"
        
        # Send usage metrics at the end
        metrics_data = {
            "type": "metrics",
            "data": {
                "tokens_used": total_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": total_cost,
                "citations_count": len(citations),
                "average_similarity_score": round(avg_similarity, 3),
            }
        }
        yield f"data: {json.dumps(metrics_data)}\n\n"
        
        yield "data: [DONE]\n\n"

