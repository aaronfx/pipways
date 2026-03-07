"""
Pipways API - Production Ready
Week 1: Core Infrastructure + AI + Auth + Admin
"""

import os
import sys
import json
import base64
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager
from enum import Enum
import hashlib
import secrets
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Third-party imports
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Query, Request, BackgroundTasks, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext
import httpx
import asyncpg
from asyncpg import Pool
from pydantic import BaseModel, EmailStr, validator, Field

# Import BaseSettings from pydantic_settings for Pydantic v2
from pydantic_settings import BaseSettings, SettingsConfigDict

# Optional imports with fallbacks
try:
    import redis.asyncio as redis
except ImportError:
    redis = None

# ==========================================
# CONFIGURATION
# ==========================================

class Settings(BaseSettings):
    """Application settings with validation"""
    # Use SettingsConfigDict for Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra='ignore'  # Ignore extra fields from environment
    )

    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    DATABASE_URL: str = Field(...)
    REDIS_URL: str = Field(default="redis://localhost:6379")
    OPENROUTER_API_KEY: str = Field(default="")
    OPENROUTER_MODEL: str = "anthropic/claude-3-opus-20240229"
    
    # Email settings (Resend/SendGrid)
    RESEND_API_KEY: str = Field(default="")
    FROM_EMAIL: str = Field(default="noreply@pipways.com")
    
    # Frontend URL for password reset links
    FRONTEND_URL: str = Field(default="https://pipways-web-nhem.onrender.com")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(default=["https://pipways-web-nhem.onrender.com", "http://localhost:3000"])
    
    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    
    # File upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = Field(default=["image/jpeg", "image/png", "image/webp"])

settings = Settings()

# ==========================================
# DATABASE SETUP
# ==========================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)
pool: Optional[Pool] = None
redis_client: Optional[Any] = None

# ==========================================
# PYDANTIC MODELS
# ==========================================

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MENTOR = "mentor"

class TradeDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"

class TradeGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)
    
    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes =
