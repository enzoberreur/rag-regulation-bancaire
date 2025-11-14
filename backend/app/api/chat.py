"""
Chat endpoints for RAG-based question answering.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_db
from app.services.rag_service import RAGService, Citation, ChatMessage

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None
    history: Optional[List[ChatMessage]] = []


@router.options("/stream")
async def chat_stream_options():
    """Handle CORS preflight for streaming endpoint."""
    return {}


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).
    
    Args:
        request: Chat request with message and optional history
        db: Database session
    """
    try:
        rag_service = RAGService(db)
        
        async def generate():
            async for chunk in rag_service.generate_response_stream(
                query=request.message,
                chat_history=request.history,
            ):
                yield chunk
        
        return EventSourceResponse(generate())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating stream: {str(e)}")

