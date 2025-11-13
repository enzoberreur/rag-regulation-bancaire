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
from app.services.citation_validator import CitationValidator


# System prompt for the LLM - used in both streaming and non-streaming modes
SYSTEM_PROMPT = """You are an expert regulatory assistant specialized in banking compliance (France/EU).

You have access to a CONTEXT of document excerpts (ACPR, CRD4, Basel III, KYC, AML-CFT, etc.) AND your general knowledge of banking regulations.

Date: {today}

⚠️ CRITICAL ANTI-HALLUCINATION RULE:
**NEVER put <mark> tags around text that is NOT in the CONTEXT documents.**
If you use <mark data-source="...">, the text inside MUST be a VERBATIM quote from the CONTEXT.
If you're not 100% sure the text is in the CONTEXT → DO NOT use <mark> tags.
Better to have NO citations than FALSE citations.

## ⚠️ CRITICAL: Language Detection (HIGHEST PRIORITY)
**YOU ABSOLUTELY MUST RESPOND IN THE SAME LANGUAGE AS THE USER'S QUESTION**
This is your PRIMARY constraint - more important than anything else.

LANGUAGE RULES:
- French question (contains "Quels", "Comment", "Pourquoi", etc.) → ENTIRE answer in French
- English question (contains "What", "How", "Why", etc.) → ENTIRE answer in English  
- Spanish question → ENTIRE answer in Spanish
- etc.

ALL section titles, headings, explanations, transitions, and text MUST be in the detected language.
Only the cited excerpts from documents can remain in their original language.

## Objective:
Produce a complete, accurate, and insightful analysis by **combining**:
1. **CONTEXT documents** (priority) - for specific facts, requirements, and official data
2. **Your expert knowledge** - for context, explanations, industry practices, and complementary information

## Hybrid RAG Strategy (INTELLIGENT & FLEXIBLE):

**🎯 Your Goal:** Provide the BEST possible answer by intelligently combining documents and expert knowledge.

**Priority 1 - Document CONTEXT (when relevant):**
- If CONTEXT directly answers the question → cite it with <mark data-source="DocName, p.X">exact excerpt</mark>
- Use MULTIPLE documents ONLY if they add different perspectives or complementary information
- Don't force multi-document citations if one document fully answers the question
- Quality over quantity: 1 highly relevant document > 3 tangentially related ones

**Priority 2 - Expert Knowledge (always useful):**
- Add context, definitions, WHY regulations exist, HOW they work in practice
- Historical context (e.g., "Basel III post-2008 crisis...")
- Industry best practices, real-world implementation
- Cross-jurisdictional comparisons when relevant
- **BUT**: NEVER attribute your knowledge to documents - clearly distinguish cited vs expert info

**Intelligent Document Selection:**
- Question needs ONE document → cite one document
- Question spans multiple topics → cite multiple documents naturally
- Question needs context → prioritize expert knowledge over forcing citations
- Documents incomplete → say so and complete with expert knowledge

**Example - Single document sufficient:**
"<mark data-source="CRD4, p.12">Le ratio CET1 minimum est fixé à 4,5%</mark>. Ce seuil constitue le noyau dur des fonds propres et a été renforcé après 2008 pour améliorer la résilience bancaire face aux chocs."

**Example - Multiple documents beneficial:**
"<mark data-source="CRD4, p.12">Le ratio CET1 est de 4,5%</mark> selon la directive européenne. <mark data-source="ACPR Guide, p.34">En France, l'ACPR peut imposer des exigences supplémentaires aux établissements systémiques</mark>. En pratique, les grandes banques maintiennent 13-15% pour préserver leur notation."

## Content Philosophy:
- **Flexibility > Rigidity**: Adapt structure to question complexity
- **Relevance > Rules**: Cite what's useful, not what's required
- **Completeness > Brevity**: Better to be thorough than artificially constrained
- **Clarity > Formality**: Distinguish cited facts (with <mark>) from expert insights (without <mark>)

## HTML Output Format (WITHOUT code blocks):
Your answer must be pure HTML. For direct quotes from CONTEXT documents, use:
`<mark data-source="DocName, p.X">exact text from document</mark>`

For your expert knowledge, write normally WITHOUT <mark> tags.

## Flexible Structure (adapt to question complexity):

**For simple/focused questions (1 topic):**
<h3>Answer / Réponse</h3>
<p>(Direct answer with citations + expert context)</p>

<h3>Additional Context / Contexte additionnel</h3>
<p>(Expert insights, historical context, best practices)</p>

**For complex/multi-faceted questions (multiple topics):**
<h3>Executive Summary / Résumé exécutif</h3>
<p>(Brief overview)</p>

<h3>Detailed Analysis / Analyse détaillée</h3>
<h4>[Topic 1 - choose relevant title]</h4>
<p>(Citations + expert analysis)</p>

<h4>[Topic 2 - choose relevant title]</h4>
<p>(Citations + expert analysis)</p>

<h4>[Topic 3 - if needed]</h4>
<p>(Citations + expert analysis)</p>

<h3>Practical Implications / Implications pratiques</h3>
<p>(Expert insights on real-world application)</p>

**Always conclude with:**
<h3>Sources</h3>
<ul>
<li>[List only documents you actually cited with <mark> tags]</li>
</ul>

**Key principles:**
- Adapt structure to question: simple question = simple answer, complex question = detailed analysis
- Don't force sections if not needed
- Don't force multiple documents if one is sufficient
- Prioritize clarity and completeness over rigid structure

## Concrete Example - HYBRID RAG (French question):

**Question:** "Quels sont les ratios de capital requis par Bâle III ?"

<h3>Résumé exécutif</h3>
<p><mark data-source="CRD4, p.23">Le ratio CET1 minimum est fixé à 4,5% des actifs pondérés par les risques</mark>, complété par un coussin de conservation de 2,5% (Bâle III post-2008). En pratique, la plupart des grandes banques européennes maintiennent un CET1 entre 13% et 15% pour préserver leur notation de crédit et accéder aux marchés de capitaux. <mark data-source="ACPR Guide, p.12">L'ACPR supervise mensuellement ces ratios et peut imposer des exigences supplémentaires aux établissements systémiques</mark>.</p>

<h3>Analyse détaillée</h3>
<h4>1. Ratios de fonds propres réglementaires</h4>
<p>Le cadre Bâle III distingue trois niveaux de fonds propres. <mark data-source="CRD4, p.23">Le Common Equity Tier 1 (CET1) constitue le noyau dur avec un minimum de 4,5%</mark>. Le Tier 1 global inclut aussi les instruments hybrides et doit atteindre 6%. Le ratio total de solvabilité (incluant Tier 2) est fixé à 8%. Ces seuils ont été renforcés après la crise de 2008 pour garantir que les banques puissent absorber des pertes importantes sans menacer la stabilité financière.</p>

<h4>2. Coussins de capital supplémentaires</h4>
<p><mark data-source="CRD4, p.45">Le coussin de conservation obligatoire est de 2,5% en CET1</mark>, portant l'exigence minimale effective à 7%. Les banques systémiques doivent aussi constituer un coussin G-SIB pouvant aller jusqu'à 2,5% supplémentaires. En France, l'ACPR peut activer un coussin contra-cyclique jusqu'à 2,5% en période de croissance excessive du crédit.</p>

## Concrete Example - HYBRID RAG (English question):

**Question:** "What are the Basel III capital requirements?"

<h3>Executive Summary</h3>
<p><mark data-source="CRD4, p.23">The minimum CET1 ratio is set at 4.5% of risk-weighted assets</mark>, complemented by a 2.5% conservation buffer (Basel III post-2008). In practice, most major European banks maintain CET1 ratios between 13% and 15% to preserve their credit ratings and access capital markets. <mark data-source="ACPR Guide, p.12">ACPR supervises these ratios monthly and may impose additional requirements on systemic institutions</mark>.</p>

## Essential Rules:
1. NEVER write ```html - output pure HTML directly
2. **LANGUAGE MATCHING IS ABSOLUTE** - French question → French answer, English question → English answer
3. Use <mark data-source="...">citation</mark> ONLY for direct document quotes
4. Cite documents when they're relevant - 1 document is fine if sufficient, multiple if beneficial
5. ADD expert knowledge generously - context, explanations, best practices, historical background
6. Clearly distinguish: cited facts (with <mark>) vs expert knowledge (without <mark>)
7. Answer length: adapt to question complexity (200-800 words) - completeness matters more than word count
8. Structure: adapt to question - simple question = simple structure, complex question = detailed sections
9. If CONTEXT incomplete: acknowledge it and complete with expert knowledge
10. Use absolute dates (not "today" or "currently")"""


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
        self.citation_validator = CitationValidator(strict_mode=False)  # 🔥 Validateur de citations
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        # Initialize tokenizer for counting tokens
        try:
            self.tokenizer = tiktoken.encoding_for_model(settings.llm_model)
        except KeyError:
            # Fallback to cl100k_base if model not found
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def _detect_language(self, text: str) -> str:
        """
        Detect the language of the input text using simple heuristics.
        Returns language name in English.
        """
        text_lower = text.lower()
        
        # French indicators
        french_words = ['quels', 'quel', 'quelle', 'comment', 'pourquoi', 'où', 'sont', 'est-ce', 
                       'les', 'des', 'une', 'dans', 'pour', 'avec', 'sur', 'que', 'qui']
        french_count = sum(1 for word in french_words if word in text_lower)
        
        # English indicators  
        english_words = ['what', 'how', 'why', 'where', 'when', 'which', 'who', 'the', 'are', 
                        'is', 'can', 'does', 'do', 'should', 'would', 'could']
        english_count = sum(1 for word in english_words if word in text_lower)
        
        # Spanish indicators
        spanish_words = ['qué', 'cómo', 'cuál', 'cuáles', 'dónde', 'por qué', 'para', 'con', 'los', 'las']
        spanish_count = sum(1 for word in spanish_words if word in text_lower)
        
        # Determine language
        if french_count > english_count and french_count > spanish_count:
            return "French"
        elif english_count > french_count and english_count > spanish_count:
            return "English"
        elif spanish_count > 0:
            return "Spanish"
        else:
            # Default to English if unclear
            return "English"
    
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
    
    async def _is_relevant_query(self, query: str) -> tuple[bool, str]:
        """
        Check if the query is relevant to banking/compliance documents.
        Returns (is_relevant, language).
        """
        relevance_prompt = f"""You are a query classifier for a banking compliance assistant.

Question: "{query}"

Is this question relevant to:
- Banking regulations (Basel, CRD4, ACPR, ECB, MiFID, GDPR, AI Act, DORA)
- Compliance (KYC, AML-CFT, LCB-FT, data protection)
- Financial risk management
- Internal controls
- Banking supervision
- Technology/AI regulations affecting banking

Answer ONLY with: "YES" or "NO"

If NO, the question is about: weather, sports, cooking, entertainment, personal questions, etc.

Answer:"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": relevance_prompt}],
                temperature=0.0,
                max_tokens=10
            )
            
            answer = response.choices[0].message.content.strip().upper()
            is_relevant = "YES" in answer
            
            # Detect language
            detected_lang = self._detect_language(query)
            
            print(f"🎯 Query relevance: {answer} | Language: {detected_lang}")
            return is_relevant, detected_lang
            
        except Exception as e:
            print(f"⚠️ Erreur vérification pertinence: {e}")
            # En cas d'erreur, on suppose que c'est pertinent
            return True, self._detect_language(query)
    
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
        # 🎯 0. Vérifier la pertinence de la question
        is_relevant, detected_lang = await self._is_relevant_query(query)
        
        if not is_relevant:
            # Question hors sujet - réponse immédiate
            if detected_lang == "French":
                out_of_scope_msg = "Je suis un assistant spécialisé en conformité bancaire. Je peux uniquement répondre à des questions sur la réglementation bancaire (Bâle III, CRD4, ACPR), la conformité (KYC, LCB-FT), les risques financiers et le contrôle interne. Votre question ne concerne pas ces domaines."
            else:
                out_of_scope_msg = "I am a banking compliance assistant. I can only answer questions about banking regulations (Basel III, CRD4, ACPR), compliance (KYC, AML-CFT), financial risks, and internal controls. Your question is outside these topics."
            
            yield f"data: {out_of_scope_msg}\n\n"
            yield f"data: {json.dumps({'type': 'citations', 'data': []})}\n\n"
            metrics_data = {
                "type": "metrics",
                "data": {
                    "tokens_used": 50,
                    "input_tokens": 30,
                    "output_tokens": 20,
                    "cost": 0.00001,
                    "citations_count": 0,
                    "average_similarity_score": 0.0,
                }
            }
            yield f"data: {json.dumps(metrics_data)}\n\n"
            yield "data: [DONE]\n\n"
            return
        
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
        
        # Detect question language
        detected_lang = self._detect_language(query)
        print(f"🌍 Detected language: {detected_lang}")
        
        # Debug: Log the context being sent to LLM
        print(f"\n{'='*80}")
        print(f"🔍 CONTEXT SENT TO LLM ({len(chunks)} chunks):")
        print(f"{'='*80}")
        for i, chunk in enumerate(chunks, 1):
            doc_name = chunk.chunk_metadata.get("document_name", "Unknown") if chunk.chunk_metadata else "Unknown"
            page = chunk.chunk_metadata.get("page", "?") if chunk.chunk_metadata else "?"
            print(f"\n[Source {i}: {doc_name}, p.{page}]")
            print(f"Content preview: {chunk.content[:200]}...")
        print(f"{'='*80}\n")
        
        # Add context and query
        user_content = f"""CONTEXT (excerpts from regulatory and internal documents):

{context}

QUESTION (in {detected_lang}):
{query}

⚠️ CRITICAL INSTRUCTION #1: LANGUAGE
The question is in **{detected_lang}**.
You MUST write your ENTIRE answer in **{detected_lang}**.
ALL headings, explanations, transitions, and text must be in **{detected_lang}**.

CRITICAL INSTRUCTIONS - INTELLIGENT HYBRID MODE:

1. **LANGUAGE:** Your ENTIRE response MUST be in **{detected_lang.upper()}** - No exceptions

2. **ZERO HALLUCINATION RULE - READ THIS CAREFULLY:**
   ⚠️ **BEFORE putting <mark> tags, verify the text is ACTUALLY in the CONTEXT above**
   - Look at the CONTEXT section above
   - Find the EXACT sentence you want to cite
   - Copy it WORD-FOR-WORD inside <mark>
   - If you can't find it in CONTEXT → DON'T use <mark> tags
   - Better to have 0 citations than 1 false citation

3. **INTELLIGENT SOURCE COMBINATION:**
   - Use CONTEXT documents when they're relevant (cite with <mark data-source="DocName, p.X">exact text</mark>)
   - Add your expert knowledge generously (definitions, context, WHY, HOW, best practices)
   - 1 document is FINE if it answers the question - don't force multiple citations
   - Multiple documents are GREAT if they add complementary perspectives
   - Quality and relevance matter more than quantity

3. **CITATION STRATEGY - ZERO TOLERANCE FOR HALLUCINATION:**
   - <mark> tags = **ONLY if text is VERBATIM in the CONTEXT above**
   - Read the CONTEXT carefully - if you don't see the exact text → NO <mark> tag
   - DO NOT paraphrase, translate, or reformulate inside <mark> tags
   - DO NOT cite from your general knowledge - ONLY from CONTEXT
   - When in doubt → NO <mark> tag, just write normally
   
   **Examples:**
   - ✅ CONTEXT says: "Le ratio CET1 minimum est fixé à 4,5%"
     → You write: "<mark data-source="CRD4, p.5">Le ratio CET1 minimum est fixé à 4,5%</mark>"
   
   - ❌ CONTEXT says: "minimum CET1 ratio is 4.5%"
     → DON'T write: "<mark data-source="CRD4, p.5">Le ratio CET1 doit être de 4,5%</mark>" (translation/paraphrase)
     → DO write: "Le ratio CET1 doit être de 4,5% (based on CRD4 requirements)" (no mark tag)
   
   - ✅ If CONTEXT doesn't have the info:
     → "Selon les réglementations Bâle III, le ratio de levier compare les fonds propres Tier 1 à l'exposition totale. Les documents fournis ne contiennent pas les détails spécifiques de ce calcul."
   
   **Bottom line:** ONLY use <mark> if you can copy-paste the exact text from CONTEXT.

4. **FLEXIBLE STRUCTURE:**
   - Simple question → simple answer (1-2 sections, 200-400 words)
   - Complex question → detailed analysis (3-5 sections, 500-800 words)
   - Adapt HTML structure to fit the content naturally
   - Completeness > arbitrary word limits

5. **BE COMPREHENSIVE:**
   - Answer the question fully
   - Add valuable context even if not explicitly asked
   - Think: "What would a banking compliance expert want to know about this topic?"
"""
        
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
        
        # 🔥 VALIDATION DES CITATIONS (anti-hallucination)
        validation = self.citation_validator.validate_response(normalized_content, chunks)
        
        if not validation["is_valid"]:
            print(f"\n{'='*80}")
            print(f"⚠️  HALLUCINATION DÉTECTÉE!")
            print(f"{'='*80}")
            print(f"Citations totales: {validation['total_citations']}")
            print(f"Citations invalides: {len(validation['invalid_citations'])}")
            print(f"Taux d'hallucination: {validation['hallucination_rate']:.1%}")
            
            for i, invalid_citation in enumerate(validation['invalid_citations'], 1):
                print(f"\n❌ Citation invalide #{i}:")
                print(f"   {invalid_citation}")
            print(f"{'='*80}\n")
        else:
            print(f"✅ Toutes les citations sont valides ({validation['total_citations']} citations)")
        
        if validation['warnings']:
            print(f"⚠️  Avertissements sur les citations:")
            for warning in validation['warnings']:
                print(f"   - {warning}")
        
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

