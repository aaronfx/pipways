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

    # CORS handling - safely parse from env or default to all
    CORS_ORIGINS: List[str] = ["*"]
    
    def model_post_init(self, __context):
        """Parse CORS_ORIGINS from env after initialization - handles both JSON and comma-separated"""
        cors_env = os.getenv("CORS_ORIGINS")
        if cors_env:
            try:
                # Try JSON format: ["http://localhost", "https://site.com"]
                parsed = json.loads(cors_env)
                if isinstance(parsed, list):
                    self.CORS_ORIGINS = parsed
            except (json.JSONDecodeError, TypeError):
                # Try comma-separated: http://localhost,https://site.com
                try:
                    self.CORS_ORIGINS = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
                except:
                    # If all fails, use default
                    self.CORS_ORIGINS = ["*"]
        # Ensure we always have at least one origin
        if not self.CORS_ORIGINS:
            self.CORS_ORIGINS = ["*"]
    
    class Config:
        env_file = ".env"

settings = Settings()

# Validate admin password is set
if not settings.ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD environment variable must be set")
