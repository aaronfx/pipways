import os
from pydantic_settings import BaseSettings
from typing import Optional, List
import json

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/pipways")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security: No default password - must be set in env
    ADMIN_PASSWORD: Optional[str] = os.getenv("ADMIN_PASSWORD")
    
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    OPENROUTER_VISION_MODEL: str = os.getenv("OPENROUTER_VISION_MODEL", "anthropic/claude-3.5-sonnet")
    
    # CORS handling - supports both JSON string and comma-separated
    CORS_ORIGINS: List[str] = ["*"]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse CORS_ORIGINS from env if set
        cors_env = os.getenv("CORS_ORIGINS")
        if cors_env:
            try:
                # Try JSON format: ["http://localhost", "https://site.com"]
                self.CORS_ORIGINS = json.loads(cors_env)
            except json.JSONDecodeError:
                # Try comma-separated: http://localhost,https://site.com
                self.CORS_ORIGINS = [origin.strip() for origin in cors_env.split(",")]
    
    class Config:
        env_file = ".env"

settings = Settings()

# Validate admin password is set
if not settings.ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD environment variable must be set")
