"""
Application configuration using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str
    
    # OpenAI
    openai_api_key: str
    
    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    
    # Storage
    storage_path: str = "./storage/documents"
    
    # Models
    embedding_model: str = "BAAI/bge-m3"
    llm_model: str = "gpt-4o-mini"
    
    # LLM Pricing (per 1M tokens) - Update as needed
    llm_input_price_per_1m: float = 0.15  # $0.15 per 1M input tokens for gpt-4o-mini
    llm_output_price_per_1m: float = 0.60  # $0.60 per 1M output tokens for gpt-4o-mini
    
    # Chunking settings
    chunking_strategy: str = "token"  # "sentence" or "token" - using token for better context
    sentences_per_chunk: int = 5
    sentence_overlap: int = 1
    chunk_size: int = 1200  # Increased from 800 for better context capture (~900 words)
    chunk_overlap: int = 300  # Increased from 200 (25% overlap)
    min_sentence_chunk_chars: int = 0  # Autorise les phrases courtes
    min_token_chunk_chars: int = 100  # Par défaut pour les chunks basés tokens
    
    # RAG settings
    top_k_results: int = 15  # Increased from 12 for more context
    initial_top_k: int = 60  # Increased from 40 for better retrieval coverage
    similarity_threshold: float = 0.65
    rerank_threshold: float = 0.05  # Très bas pour conserver plus de phrases
    enforce_diversity: bool = False  # Disabled to allow multiple chunks from same document
    disable_rerank_filter: bool = False  # Permet de garder tous les chunks rerankés
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    
    class Config:
        # Look for .env in the backend directory
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = False


settings = Settings()

