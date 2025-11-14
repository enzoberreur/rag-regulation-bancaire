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
    chunking_strategy: str = "sentence"  # "sentence" or "token"
    sentences_per_chunk: int = 5
    sentence_overlap: int = 1
    chunk_size: int = 800  # Fallback for token-based chunking
    chunk_overlap: int = 200  # Fallback for token-based chunking
    
    # RAG settings
    top_k_results: int = 8
    initial_top_k: int = 20
    similarity_threshold: float = 0.65
    rerank_threshold: float = 0.3
    enforce_diversity: bool = False
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    
    class Config:
        # Look for .env in the backend directory
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = False


settings = Settings()

