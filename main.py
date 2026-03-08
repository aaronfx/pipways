"""
Pipways Trading Platform API
Debug version with comprehensive error handling
"""

import os
import sys
import traceback
import jwt
import bcrypt
import asyncpg
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, field_validator
from dotenv import load_dotenv
import httpx
import base64
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    RESET_TOKEN_EXPIRE_HOURS = 1
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@pipways.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-opus-20240229")
    OPENROUTER_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "anthropic/claude-3-opus-20240229")
    CORS_ORIGINS = [
        "https://pipways-web-nhem.onrender.com",
        "http://localhost:3000", 
        "http://localhost:5173",
        "http://127.0.0.1:5500",
        "null",
        "*"
    ]

settings = Settings()

# Check critical env vars
if not settings.DATABASE_URL:
    logger.error("CRITICAL: DATABASE_URL not set!")
else:
    logger.info(f"Database URL configured: {settings.DATABASE_URL[:20]}...")

# Database pool
db_pool: Optional[asyncpg.Pool] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    try:
        logger.info("Initializing database pool...")
        db_pool = await asyncpg.create_pool(settings.DATABASE_URL, min_size=1, max_size=10)
        logger.info("Database pool created successfully")
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        logger.error(traceback.format_exc())
        # Continue anyway so we can see the error in health endpoint
    yield
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")

app = FastAPI(title="Pipways API", version="2.0.0", lifespan=lifespan)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Error handling middleware
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error", 
                "error": str(e),
                "type": type(e).__name__
            }
        )

# Security
security = HTTPBearer(auto_error=False)

# Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain a lowercase letter')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain an uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain a number')
        if not any(c in '@$!%*?&' for c in v):
            raise ValueError('Password must contain a special character (@$!%*?&)')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

# Database initialization
async def init_db():
    if not db_pool:
        logger.error("No database pool available for init_db")
        return
    
    try:
        async with db_pool.acquire() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    role VARCHAR(20) DEFAULT 'user',
                    subscription_tier VARCHAR(20) DEFAULT 'free',
                    subscription_status VARCHAR(20) DEFAULT 'inactive',
                    email_verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    reset_token VARCHAR(255),
                    reset_token_expires TIMESTAMP
                )
            """)
            
            # Create default admin
            await create_default_admin(conn)
            logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Error in init_db: {str(e)}")
        logger.error(traceback.format_exc())
        raise

async def create_default_admin(conn):
    try:
        admin_exists = await conn.fetchval("SELECT id FROM users WHERE email = $1", settings.ADMIN_EMAIL)
        if not admin_exists:
            hashed = bcrypt.hashpw(settings.ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
            await conn.execute("""
                INSERT INTO users (email, password_hash, full_name, role, subscription_tier, subscription_status, email_verified)
                VALUES ($1, $2, $3, 'admin', 'vip', 'active', TRUE)
            """, settings.ADMIN_EMAIL, hashed, "System Administrator")
            logger.info(f"Default admin created: {settings.ADMIN_EMAIL}")
    except Exception as e:
        logger.error(f"Error creating admin: {str(e)}")
        raise

# Auth utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# Auth endpoints with detailed error handling
@app.post("/auth/login")
async def login(credentials: UserLogin):
    logger.info(f"Login attempt for: {credentials.email}")
    
    if not db_pool:
        logger.error("Database pool not available")
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        async with db_pool.acquire() as conn:
            logger.info("Acquired DB connection")
            user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", credentials.email)
            
            if not user:
                logger.warning(f"User not found: {credentials.email}")
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            logger.info(f"User found: {user['email']}, checking password...")
            
            if not verify_password(credentials.password, user["password_hash"]):
                logger.warning("Password verification failed")
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            logger.info("Password verified, updating last login...")
            await conn.execute("UPDATE users SET last_login = NOW() WHERE id = $1", user["id"])
            
            access_token = create_access_token({"sub": str(user["id"])})
            refresh_token = create_refresh_token({"sub": str(user["id"])})
            
            logger.info(f"Login successful for: {credentials.email}")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": dict(user)
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/auth/register")
async def register(user_data: UserRegister):
    logger.info(f"Registration attempt for: {user_data.email}")
    
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        async with db_pool.acquire() as conn:
            existing = await conn.fetchval("SELECT id FROM users WHERE email = $1", user_data.email)
            if existing:
                raise HTTPException(status_code=400, detail="Email already registered")
            
            hashed_pw = get_password_hash(user_data.password)
            user_id = await conn.fetchval("""
                INSERT INTO users (email, password_hash, full_name, subscription_tier, subscription_status)
                VALUES ($1, $2, $3, 'free', 'active')
                RETURNING id
            """, user_data.email, hashed_pw, user_data.full_name)
            
            access_token = create_access_token({"sub": str(user_id)})
            refresh_token = create_refresh_token({"sub": str(user_id)})
            
            user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            
            logger.info(f"Registration successful for: {user_data.email}")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": dict(user)
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.get("/health")
async def health_check():
    db_status = "connected" if db_pool else "disconnected"
    return {
        "status": "healthy", 
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# ... (keep all other endpoints from previous version but with similar error handling)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
