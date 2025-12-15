# app/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/fastapi_db"
    TEST_DATABASE_URL: Optional[str] = "postgresql://postgres:postgres@localhost:5432/fastapi_test_db"
    
    # JWT Settings
    JWT_SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    JWT_REFRESH_SECRET_KEY: str = "your-refresh-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security
    BCRYPT_ROUNDS: int = 12
    CORS_ORIGINS: List[str] = ["*"]
    
    # Redis (optional, for token blacklisting)
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    
    # OpenAI Settings
    OPENAI_API_KEY: str = "your-openai-api-key-here"
    OPENAI_MODEL: str = "gpt-4o-mini"  # Default model for cost efficiency
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_TIMEOUT: int = 30  # seconds
    
    # YouTube API Settings
    YOUTUBE_API_KEY: Optional[str] = None
    
    # AI Assistant Settings
    MAX_CONVERSATION_HISTORY: int = 50  # Maximum messages to keep in memory
    ENABLE_WEB_SEARCH: bool = True
    ENABLE_IMAGE_ANALYSIS: bool = True
    ENABLE_CODE_EXECUTION: bool = False  # For safety, disabled by default
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = 60
    MAX_TOKENS_PER_REQUEST: int = 4000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "logs/asistechai.log"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create a global settings instance
settings = Settings()

# Optional: Add cached settings getter
@lru_cache()
def get_settings() -> Settings:
    return Settings()