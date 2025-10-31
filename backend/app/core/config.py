"""
Application configuration using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional


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
    
    # Chunking
    chunk_size: int = 1050
    chunk_overlap: int = 100
    
    # RAG
    top_k_results: int = 5
    similarity_threshold: float = 0.5  # Reduced from 0.7 to be more permissive
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

