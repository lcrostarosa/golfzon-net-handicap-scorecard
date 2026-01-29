"""
Configuration management for Golfzon OCR application.
"""
import os
from typing import Optional


class Config:
    """Application configuration."""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///golfzon_league.db"
    )
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # Security
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "dev-secret-key-change-in-production"
    )
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # OCR Configuration
    TESSERACT_CMD: Optional[str] = os.getenv("TESSERACT_CMD")
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    ALLOWED_EXTENSIONS: list = os.getenv(
        "ALLOWED_EXTENSIONS",
        "jpg,jpeg,png"
    ).split(",")
    
    # Streamlit
    STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    STREAMLIT_SERVER_ADDRESS: str = os.getenv("STREAMLIT_SERVER_ADDRESS", "0.0.0.0")
    
    # Redis (optional)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    
    # Sentry (optional)
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    
    # New Relic (optional)
    NEW_RELIC_LICENSE_KEY: Optional[str] = os.getenv("NEW_RELIC_LICENSE_KEY")
    NEW_RELIC_APP_NAME: Optional[str] = os.getenv("NEW_RELIC_APP_NAME", "golfzon-ocr")
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration."""
        if cls.ENVIRONMENT == "production":
            if cls.SECRET_KEY == "dev-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be set in production")
            if cls.DATABASE_URL.startswith("sqlite"):
                raise ValueError("SQLite is not suitable for production. Use PostgreSQL.")
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production."""
        return cls.ENVIRONMENT == "production"
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development."""
        return cls.ENVIRONMENT == "development"


# Initialize config
config = Config()

# Validate on import (only in production)
if config.is_production():
    config.validate()

