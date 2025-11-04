#!/usr/bin/env python3
"""
Script to run the FastAPI development server.
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    # Simplified configuration to avoid pathlib compatibility issues
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
        reload_excludes=[
            "*.venv/*",
            "*/.venv/*",
            "*/site-packages/*",
            "*/__pycache__/*",
        ],
    )

