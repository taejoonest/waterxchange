"""
Application configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./waterxchange.db"
    
    # JWT Authentication
    JWT_SECRET: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 168  # 7 days for demo
    
    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # App Settings
    APP_NAME: str = "WaterXchange"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()
