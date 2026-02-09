"""
Application Configuration
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # GCP Configuration
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "runner-platform-dublin")
    GCP_REGION: str = os.getenv("GCP_REGION", "europe-west1")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:8080",
        "http://localhost:3000",
        "https://*.run.app",  # Cloud Run URLs
    ]
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
