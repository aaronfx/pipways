
import os
from pydantic_settings import BaseSettings
from typing import Optional

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

    CORS_ORIGINS: list = ["*"]  # Change in production

    class Config:
        env_file = ".env"

settings = Settings()

# Validate admin password is set
if not settings.ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD environment variable must be set")
