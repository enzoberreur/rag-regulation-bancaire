from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Set environment variable to avoid tokenizers forking warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from app.api import chat, documents, health
from app.core.config import settings
from app.services.embedding_service import EmbeddingService

app = FastAPI(
    title="HexaBank Compliance Assistant API",
    description="Backend RAG pour l'assistant de conformité réglementaire HexaBank",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",  # Vite fallback port
        "http://localhost:5173",  # Vite default dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Preload embedding model on startup for better performance
@app.on_event("startup")
async def startup_event():
    """Preload embedding model on startup to avoid delay on first request."""
    # The singleton pattern ensures the model is only loaded once, even across reloads
    print("🚀 Preloading embedding model...")
    embedding_service = EmbeddingService()
    # Trigger model loading - singleton ensures this only happens once per process
    _ = embedding_service.model
    print("✅ Embedding model preloaded and ready!")
    print("ℹ️  Model will be reused for all requests (singleton pattern)")

# Include routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "HexaBank Compliance Assistant API", "version": "0.1.0"}

