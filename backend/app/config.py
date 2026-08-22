"""Sentinel AI Backend Configuration & Constants."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Sentinel AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # Database Configuration (PostgreSQL primary with asyncpg)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/sentinel_ai"
    SQL_ECHO: bool = False

    # JWT Authentication & Security
    JWT_SECRET_KEY: str = "sentinel_ai_local_dev_jwt_secret_key_849204829038490238"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours
    
    # Storage Directories
    UPLOAD_BASE_DIR: str = "data/uploads"
    REPORTS_BASE_DIR: str = "data/reports"
    
    # File Ingestion Limits
    MAX_UPLOAD_SIZE_BYTES: int = 500 * 1024 * 1024  # 500 MB limit for full datasets
    ALLOWED_EXTENSIONS: List[str] = [".csv"]
    
    # Validation Thresholds
    SEVERE_IMBALANCE_THRESHOLD: float = 0.05  # Below 5% positive class triggers imbalance warning
    HIGH_CARDINALITY_THRESHOLD: int = 100     # Categorical columns with >100 unique values
    MIN_DATASET_ROWS: int = 50                 # Minimum rows required for valid analysis
    
    # Session Management (In-Memory Fallback & Caching)
    SESSION_TTL_SECONDS: int = 3600            # 1 hour TTL
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

# Ensure local storage directories exist safely
os.makedirs(settings.UPLOAD_BASE_DIR, exist_ok=True)
os.makedirs(settings.REPORTS_BASE_DIR, exist_ok=True)
