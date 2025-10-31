#!/usr/bin/env python3
"""
Script to run the FastAPI development server.
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
        reload_dirs=["app"],  # Only watch the app directory
        reload_excludes=[
            "*.pyc",
            "*.pyo",
            "*.pyd",
            "**/.venv/**",
            "**/venv/**",
            "**/__pycache__/**",
            "**/.git/**",
            "**/*.log",
            "**/storage/**",
            "**/node_modules/**",
            "**/.env",
            "**/.cache/**",
            "**/cache/**",
            "**/models/**",  # Exclude model cache directories
            "**/.cache/huggingface/**",  # HuggingFace cache
            "**/.cache/sentence_transformers/**",  # Sentence transformers cache
            "**/site-packages/**",  # Python packages
            "**/dist/**",
            "**/build/**",
            "**/*.egg-info/**",
            "**/.pytest_cache/**",
            "**/.mypy_cache/**",
            "**/.ruff_cache/**",
        ],
    )

