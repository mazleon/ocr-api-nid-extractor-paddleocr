"""
Application configuration management with environment variables and settings.
"""
from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "NID Information Extraction API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    ENABLE_DOCS: bool = True
    ENABLE_REDOC: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]
    
    # File Upload
    MAX_FILE_SIZE: int = Field(default=5 * 1024 * 1024, description="Max file size in bytes (5MB)")
    ALLOWED_EXTENSIONS: set[str] = {"jpg", "jpeg", "png", "bmp"}
    
    # PaddleOCR Configuration
    OCR_LANG: str = "en"
    OCR_VERSION: str = "PP-OCRv5"
    OCR_DET_MODEL: str = "PP-OCRv5_mobile_det"
    OCR_REC_MODEL: str = "en_PP-OCRv5_mobile_rec"
    OCR_USE_GPU: bool = False
    OCR_CONFIDENCE_THRESHOLD: float = 0.3
    OCR_ENABLE_MKLDNN: bool = True
    OCR_CPU_THREADS: int = 8
    OCR_REC_BATCH_NUM: int = 6
    OCR_MAX_IMAGE_DIMENSION: int | None = 640

    # Model Cache Directories (None = auto-download to default cache)
    OCR_MODEL_CACHE_DIR: str | None = None  # Base cache directory
    OCR_DET_MODEL_DIR: str | None = None    # Detection model directory
    OCR_REC_MODEL_DIR: str | None = None    # Recognition model directory
    
    # Caching
    ENABLE_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    CACHE_MAX_SIZE: int = 1000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "logs/app.log"
    LOG_ROTATION: str = "500 MB"
    LOG_RETENTION: str = "10 days"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures we only create one settings instance.
    """
    return Settings()
