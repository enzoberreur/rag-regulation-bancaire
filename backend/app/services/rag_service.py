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

from app.core.config import settings
from app.models.document import DocumentChunk
from app.services.embedding_service import EmbeddingService


# System prompt for the LLM - used in both streaming and non-streaming modes
SYSTEM_PROMPT = """You are an internal assistant that reads, interprets, and summarises new ACPR / ECB / EU AI Act regulations, automatically mapping them to HexaBank's internal risk and compliance policies. 

You can draft compliance updates, highlight potential non-conformities, and recommend required documentation changes.

CRITICAL: Always respond in ENGLISH, even if the source documents are in French or other languages. Translate and summarize the key points in clear, professional English.

MANDATORY INLINE CITATIONS - THIS IS CRITICAL:
You MUST add [SOURCE:N] after EVERY sentence that contains specific information from a source document.
- N is the source number (1, 2, 3, etc.) as shown in the context below
- Place [SOURCE:N] immediately after the period, BEFORE the next sentence
- Use the exact format: [SOURCE:N] (capital letters, colon, number, no spaces)

Example response format:
"Financial institutions must maintain a capital buffer of 2.5%[SOURCE:1]. The committee must consist of at least three independent members[SOURCE:2]. Compliance is required by December 31, 2025[SOURCE:1]."

IMPORTANT: Add [SOURCE:N] citations throughout your entire response. Do NOT skip this step.

Be precise, professional, and focus on actionable compliance insights.

CRITICAL FORMATTING RULES - YOU MUST FOLLOW THESE EXACTLY:

When you write numbered lists:
- Add a blank line BEFORE each numbered item (1., 2., 3., etc.)
- Format: "1. Title" then content on next line
- Example:

1. First Point
Content for first point here.

2. Second Point
Content for second point here.

When you write section headers:
- Add blank line BEFORE the header
- Add blank line AFTER the header
- Use **bold** for headers followed by colon
- Example:

**Section Title:**

Content starts here.

For bullet lists:
- Use "- " format
- No blank lines between bullets
- Example:
- First item
- Second item

Add blank lines between paragraphs for readability."""


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
        
        # Filter results by similarity threshold, but keep at least one result if any exist
        chunk_ids = []
        similarity_scores = []
        for row in rows:
            chunk_id, similarity = row
            if similarity >= settings.similarity_threshold or len(chunk_ids) == 0:
                chunk_ids.append(chunk_id)
                similarity_scores.append(float(similarity))
        
        if not chunk_ids:
            return [], []
        
        # Query chunks normally using SQLAlchemy ORM
        chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.id.in_(chunk_ids)
        ).all()
        
        # Sort by original order (by similarity)
        chunks_dict = {chunk.id: chunk for chunk in chunks}
        chunks = [chunks_dict[chunk_id] for chunk_id in chunk_ids if chunk_id in chunks_dict]
        
        return chunks, similarity_scores
    
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
            context_parts.append(
                f"[Source {i}: {doc_name}]\n{chunk.content}\n"
            )
        return "\n".join(context_parts)
    
    def _build_citations(self, chunks: List[DocumentChunk]) -> List[Citation]:
        """
        Build citations from chunks.
        
        Args:
            chunks: List of relevant document chunks
        
        Returns:
            List of citations
        """
        citations = []
        seen_docs = set()
        
        for chunk in chunks:
            doc_name = chunk.chunk_metadata.get("document_name", "Unknown") if chunk.chunk_metadata else "Unknown"
            doc_id = str(chunk.document_id)
            
            if doc_id not in seen_docs:
                citations.append(
                    Citation(
                        id=doc_id,
                        text=f"Excerpt from {doc_name}",
                        source=doc_name,
                        url=f"/documents/{doc_id}",
                    )
                )
                seen_docs.add(doc_id)
        
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
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        # Search for relevant chunks
        chunks, similarity_scores = await self._search_relevant_chunks(query_embedding, top_k=settings.top_k_results)
        
        # Calculate average similarity score
        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
        
        # Check if we found any relevant chunks
        if not chunks:
            # No relevant documents found - return informative message
            return {
                "content": "I couldn't find any relevant information in the uploaded documents to answer your question. Please make sure you have uploaded relevant documents, or try rephrasing your question.",
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
        
        # Build prompt using global system prompt
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        
        # Add chat history if provided
        if chat_history:
            for msg in chat_history[-10:]:  # Limit to last 10 messages
                messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        
        # Add context and query
        user_content = f"""Context from regulatory documents and policies:

{context}

User Question: {query}

Please provide a detailed answer based on the context above. Do not include source citations or references in your response - they are handled automatically by the system."""
        
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
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        # Search for relevant chunks
        chunks, similarity_scores = await self._search_relevant_chunks(query_embedding, top_k=settings.top_k_results)
        
        # Calculate average similarity score
        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
        
        # Check if we found any relevant chunks
        if not chunks:
            # No relevant documents found - inform the user
            yield f"data: I couldn't find any relevant information in the uploaded documents to answer your question.\n\n"
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
        
        # Build prompt using global system prompt
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        
        # Add chat history if provided
        if chat_history:
            for msg in chat_history[-10:]:  # Limit to last 10 messages
                messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        
        # Add context and query
        user_content = f"""Context from regulatory documents and policies:

{context}

User Question: {query}

Please provide a detailed answer based on the context above. Do not include source citations or references in your response - they are handled automatically by the system."""
        
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

