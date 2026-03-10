"""
Pipways Trading Platform API - Production Debug & System Completion v3.5.2
FastAPI serves frontend directly - No CORS required
"""

import os
import re
import jwt
import bcrypt
import asyncpg
import logging
import base64
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field, field_validator
from dotenv import load_dotenv
import httpx
from contextlib import asynccontextmanager

# Optional Cloudinary import
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False
    logging.warning("Cloudinary not installed. Using local storage for uploads.")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-min-32-chars-long")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@pipways.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    
    # Cloudinary Config
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

    # Models
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    OPENROUTER_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "anthropic/claude-3.5-sonnet")

    # CORS - simplified for same-origin
    CORS_ORIGINS = ["*"]

settings = Settings()

# Configure Cloudinary
if CLOUDINARY_AVAILABLE and settings.CLOUDINARY_CLOUD_NAME:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET
    )

# Database pool
db_pool: Optional[asyncpg.Pool] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    try:
        dsn = settings.DATABASE_URL
        if dsn and "render.com" in dsn and "sslmode" not in dsn:
            dsn += "?sslmode=require"
        
        if not dsn:
            logger.error("DATABASE_URL not set!")
            raise ValueError("DATABASE_URL environment variable is required")
            
        db_pool = await asyncpg.create_pool(
            dsn, 
            min_size=2, 
            max_size=10,
            command_timeout=60,
            server_settings={'jit': 'off'}
        )
        await init_db()
        
        # Ensure uploads directory exists
        os.makedirs("uploads", exist_ok=True)
        
        logger.info("Database and storage initialized successfully")
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        raise
    yield
    if db_pool:
        await db_pool.close()

app = FastAPI(title="Pipways API", version="3.5.2", lifespan=lifespan)

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

# CRITICAL: Create uploads directory BEFORE mounting StaticFiles
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

security = HTTPBearer(auto_error=False)

# ============================================================================
# Pydantic Models
# ============================================================================

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

class BlogPostCreate(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = None
    is_premium: bool = False
    status: str = Field(default="published", pattern="^(draft|published|scheduled)$")
    scheduled_at: Optional[datetime] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    slug: Optional[str] = None
    featured_image: Optional[str] = None
    tags: Optional[List[str]] = []
    category: Optional[str] = None

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    is_premium: Optional[bool] = None
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    slug: Optional[str] = None
    featured_image: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None

class WebinarCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=1)
    is_premium: bool = False
    meeting_link: Optional[str] = None
    max_participants: Optional[int] = 100
    recording_link: Optional[str] = None
    reminder_message: Optional[str] = None

class WebinarUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    is_premium: Optional[bool] = None
    meeting_link: Optional[str] = None
    max_participants: Optional[int] = None
    recording_link: Optional[str] = None
    reminder_message: Optional[str] = None

class SignalCreate(BaseModel):
    pair: str = Field(..., min_length=1)
    direction: str = Field(..., pattern="^(buy|sell)$")
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    risk_reward_ratio: Optional[str] = None
    expires_at: Optional[datetime] = None
    timeframe: str = "1H"
    analysis: Optional[str] = None
    is_premium: bool = False

class SignalUpdate(BaseModel):
    pair: Optional[str] = None
    direction: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    risk_reward_ratio: Optional[str] = None
    expires_at: Optional[datetime] = None
    timeframe: Optional[str] = None
    analysis: Optional[str] = None
    is_premium: Optional[bool] = None
    status: Optional[str] = None
    result: Optional[str] = None

class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    is_premium: bool = False
    level: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")
    duration_hours: Optional[float] = None
    thumbnail: Optional[str] = None
    modules: Optional[List[Dict]] = None

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    is_premium: Optional[bool] = None
    level: Optional[str] = None
    duration_hours: Optional[float] = None
    thumbnail: Optional[str] = None

class ModuleCreate(BaseModel):
    title: str = Field(..., min_length=1)
    content: Optional[str] = None
    video_url: Optional[str] = None
    sort_order: Optional[int] = 0
    is_premium: bool = False

class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    video_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_premium: Optional[bool] = None

class QuizCreate(BaseModel):
    course_id: int
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    passing_score: int = Field(default=70, ge=0, le=100)
    questions: Optional[List[Dict]] = []

class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    passing_score: Optional[int] = None

class QuizQuestionCreate(BaseModel):
    quiz_id: int
    question_text: str
    question_type: str = Field(default="multiple_choice", pattern="^(multiple_choice|true_false|text)$")
    options: Optional[List[str]] = []
    correct_answer: str
    points: int = Field(default=1, ge=1)
    sort_order: Optional[int] = 0

class QuizAttempt(BaseModel):
    quiz_id: int
    answers: Dict[str, Any]

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context: Optional[str] = ""
    history: Optional[List[Dict[str, str]]] = []
    include_knowledge: Optional[bool] = True

class UserUpdate(BaseModel):
    role: Optional[str] = None
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None
    full_name: Optional[str] = None

class SiteSettingsUpdate(BaseModel):
    site_name: Optional[str] = None
    telegram_free_link: Optional[str] = None
    telegram_vip_link: Optional[str] = None
    vip_price: Optional[float] = None
    vip_price_currency: Optional[str] = None
    seo_default_title: Optional[str] = None
    seo_default_description: Optional[str] = None
    contact_email: Optional[str] = None

class SignalResultUpdate(BaseModel):
    result: str = Field(..., pattern="^(WIN|LOSS|PARTIAL|EXPIRED)$")

# ============================================================================
# Database Initialization
# ============================================================================

async def init_db():
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

        # Blog posts table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                excerpt TEXT,
                author_id INTEGER REFERENCES users(id),
                is_premium BOOLEAN DEFAULT FALSE,
                status VARCHAR(20) DEFAULT 'published',
                scheduled_at TIMESTAMP,
                meta_title VARCHAR(255),
                meta_description TEXT,
                slug VARCHAR(255) UNIQUE,
                featured_image VARCHAR(500),
                tags TEXT[],
                category VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                published_at TIMESTAMP
            )
        """)

        # Signals table - Enhanced
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id SERIAL PRIMARY KEY,
                pair VARCHAR(20) NOT NULL,
                direction VARCHAR(10) NOT NULL,
                entry_price DECIMAL(10,5),
                stop_loss DECIMAL(10,5),
                take_profit_1 DECIMAL(10,5),
                take_profit_2 DECIMAL(10,5),
                risk_reward_ratio VARCHAR(20),
                timeframe VARCHAR(20),
                analysis TEXT,
                status VARCHAR(20) DEFAULT 'active',
                result VARCHAR(20) DEFAULT NULL,
                pips_gain DECIMAL(10,2),
                is_premium BOOLEAN DEFAULT FALSE,
                expires_at TIMESTAMP,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP
            )
        """)

        # Webinars table - FIXED: Removed thumbnail column
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS webinars (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                scheduled_at TIMESTAMP NOT NULL,
                duration_minutes INTEGER DEFAULT 60,
                meeting_link VARCHAR(500),
                is_premium BOOLEAN DEFAULT FALSE,
                max_participants INTEGER DEFAULT 100,
                recording_link VARCHAR(500),
                reminder_message TEXT,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Courses table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                content TEXT,
                level VARCHAR(20) DEFAULT 'beginner',
                duration_hours DECIMAL(5,2),
                thumbnail VARCHAR(500),
                is_premium BOOLEAN DEFAULT FALSE,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Course modules table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS course_modules (
                id SERIAL PRIMARY KEY,
                course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                content TEXT,
                video_url VARCHAR(500),
                sort_order INTEGER DEFAULT 0,
                is_premium BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Course quizzes table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS course_quizzes (
                id SERIAL PRIMARY KEY,
                course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                passing_score INTEGER DEFAULT 70,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Quiz questions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id SERIAL PRIMARY KEY,
                quiz_id INTEGER REFERENCES course_quizzes(id) ON DELETE CASCADE,
                question_text TEXT NOT NULL,
                question_type VARCHAR(20) DEFAULT 'multiple_choice',
                options JSONB,
                correct_answer TEXT NOT NULL,
                points INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Quiz attempts table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id SERIAL PRIMARY KEY,
                quiz_id INTEGER REFERENCES course_quizzes(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                answers JSONB,
                score INTEGER,
                max_score INTEGER,
                percentage DECIMAL(5,2),
                passed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # User course progress table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_course_progress (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                module_id INTEGER REFERENCES course_modules(id) ON DELETE CASCADE,
                completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                UNIQUE(user_id, module_id)
            )
        """)

        # Chat history table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Media files table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS media_files (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                url VARCHAR(500) NOT NULL,
                file_type VARCHAR(50),
                size_bytes INTEGER,
                uploaded_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # AI Chart Analysis table - User isolated
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chart_analyses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                pair VARCHAR(20),
                timeframe VARCHAR(10),
                image_url VARCHAR(500),
                analysis_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Performance analyses table - User isolated
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_analyses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                analysis_data JSONB NOT NULL,
                raw_trades JSONB,
                trader_score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # AI Usage Logs table - NEW
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_usage_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                analysis_type VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Site settings table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS site_settings (
                id SERIAL PRIMARY KEY,
                site_name VARCHAR(255) DEFAULT 'Pipways',
                telegram_free_link VARCHAR(500),
                telegram_vip_link VARCHAR(500),
                vip_price DECIMAL(10,2) DEFAULT 99.00,
                vip_price_currency VARCHAR(3) DEFAULT 'USD',
                seo_default_title VARCHAR(255),
                seo_default_description TEXT,
                contact_email VARCHAR(255),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert default settings if not exists
        await conn.execute("""
            INSERT INTO site_settings (id, site_name, telegram_free_link, telegram_vip_link, vip_price)
            SELECT 1, 'Pipways', 'https://t.me/pipways_free', 'https://t.me/pipways_vip', 99.00
            WHERE NOT EXISTS (SELECT 1 FROM site_settings WHERE id = 1)
        """)

        # Create default admin
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
            logger.error(f"Error creating admin: {e}")

# ============================================================================
# Auth Utilities
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

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

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            return None
        if datetime.utcnow().timestamp() > payload.get("exp", 0):
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        return payload
    except Exception as e:
        logger.debug(f"Optional auth error: {e}")
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        if datetime.utcnow().timestamp() > payload.get("exp", 0):
            raise HTTPException(status_code=401, detail="Token expired")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        async with db_pool.acquire() as conn:
            user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", int(user_id))
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            return dict(user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    role = current_user.get("role", "user")
    if role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# ============================================================================
# AI Usage Tracking
# ============================================================================

async def check_ai_usage_limit(user_id: int, analysis_type: str, tier: str) -> bool:
    """Check if user has exceeded AI usage limits"""
    async with db_pool.acquire() as conn:
        if analysis_type == "chart":
            if tier in ["premium", "vip"]:
                # 3 per day for premium
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM ai_usage_logs 
                    WHERE user_id = $1 AND analysis_type = 'chart' 
                    AND created_at > NOW() - INTERVAL '1 day'
                """, user_id)
                return count < 3
            else:
                # 3 total for free
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM ai_usage_logs 
                    WHERE user_id = $1 AND analysis_type = 'chart'
                """, user_id)
                return count < 3
        elif analysis_type == "performance":
            if tier in ["premium", "vip"]:
                # 1 per week for premium
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM ai_usage_logs 
                    WHERE user_id = $1 AND analysis_type = 'performance' 
                    AND created_at > NOW() - INTERVAL '7 days'
                """, user_id)
                return count < 1
            else:
                # 1 total for free
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM ai_usage_logs 
                    WHERE user_id = $1 AND analysis_type = 'performance'
                """, user_id)
                return count < 1
    return False

async def log_ai_usage(user_id: int, analysis_type: str):
    """Log AI usage for tracking"""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO ai_usage_logs (user_id, analysis_type)
            VALUES ($1, $2)
        """, user_id, analysis_type)

# ============================================================================
# Auth Endpoints
# ============================================================================

@app.post("/auth/register", response_model=Token)
async def register(user_data: UserRegister):
    async with db_pool.acquire() as conn:
        existing = await conn.fetchval("SELECT id FROM users WHERE email = $1", user_data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_pw = get_password_hash(user_data.password)
        user_id = await conn.fetchval("""
            INSERT INTO users (email, password_hash, full_name, subscription_tier, subscription_status, role)
            VALUES ($1, $2, $3, 'free', 'active', 'user')
            RETURNING id
        """, user_data.email, hashed_pw, user_data.full_name)

        token_data = {
            "sub": str(user_id),
            "email": user_data.email,
            "full_name": user_data.full_name,
            "role": "user",
            "subscription_tier": "free"
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": str(user_id)})

        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": dict(user) if user else {"id": user_id, "email": user_data.email, "role": "user"}
        }

@app.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", credentials.email)
        if not user or not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        await conn.execute("UPDATE users SET last_login = NOW() WHERE id = $1", user["id"])

        token_data = {
            "sub": str(user["id"]),
            "email": user["email"],
            "full_name": user.get("full_name", ""),
            "role": user.get("role", "user"),
            "subscription_tier": user.get("subscription_tier", "free")
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": str(user["id"])})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": dict(user)
        }

@app.post("/auth/refresh")
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id = payload.get("sub")
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", int(user_id))
            if not user:
                raise HTTPException(status_code=401, detail="User not found")

            token_data = {
                "sub": str(user["id"]),
                "email": user["email"],
                "full_name": user.get("full_name", ""),
                "role": user.get("role", "user"),
                "subscription_tier": user.get("subscription_tier", "free")
            }
            new_access = create_access_token(token_data)
            new_refresh = create_refresh_token({"sub": str(user["id"])})
            return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

# ============================================================================
# Admin Endpoints
# ============================================================================

@app.get("/admin/stats")
async def get_admin_stats(admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users") or 0
        total_signals = await conn.fetchval("SELECT COUNT(*) FROM signals") or 0
        active_signals = await conn.fetchval("SELECT COUNT(*) FROM signals WHERE status = 'active'") or 0
        premium_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE subscription_tier IN ('premium', 'vip')") or 0
        total_posts = await conn.fetchval("SELECT COUNT(*) FROM blog_posts") or 0
        total_courses = await conn.fetchval("SELECT COUNT(*) FROM courses") or 0
        total_webinars = await conn.fetchval("SELECT COUNT(*) FROM webinars") or 0
        
        return {
            "total_users": total_users,
            "total_signals": total_signals,
            "active_signals": active_signals,
            "premium_users": premium_users,
            "conversion_rate": round((premium_users / total_users * 100), 2) if total_users > 0 else 0,
            "content_stats": {
                "blog_posts": total_posts,
                "courses": total_courses,
                "webinars": total_webinars
            }
        }

@app.get("/admin/users")
async def get_all_users(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: dict = Depends(get_admin_user)
):
    async with db_pool.acquire() as conn:
        where_clauses = ["1=1"]
        params = []

        if search:
            where_clauses.append(f"(email ILIKE ${len(params)+1} OR full_name ILIKE ${len(params)+1})")
            params.append(f"%{search}%")

        if role:
            where_clauses.append(f"role = ${len(params)+1}")
            params.append(role)

        count_query = f"SELECT COUNT(*) FROM users WHERE {' AND '.join(where_clauses)}"
        total = await conn.fetchval(count_query, *params)

        offset = (page - 1) * limit
        query = f"""
            SELECT id, email, full_name, role, subscription_tier, subscription_status,
                   email_verified, created_at, last_login
            FROM users
            WHERE {' AND '.join(where_clauses)}
            ORDER BY created_at DESC
            LIMIT ${len(params)+1} OFFSET ${len(params)+2}
        """
        params.extend([limit, offset])

        rows = await conn.fetch(query, *params)
        return {
            "users": [dict(row) for row in rows],
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }

@app.put("/admin/users/{user_id}")
async def update_user(user_id: int, update_data: UserUpdate, admin: dict = Depends(get_admin_user)):
    """Update user role and subscription details"""
    async with db_pool.acquire() as conn:
        # Prevent self-demotion
        admin_id = admin.get("id") or admin.get("sub")
        if int(user_id) == int(admin_id) and update_data.role and update_data.role != "admin":
            raise HTTPException(status_code=400, detail="Cannot remove your own admin privileges")

        # Build update query dynamically
        update_fields = []
        params = []
        
        if update_data.role is not None:
            update_fields.append(f"role = ${len(params)+1}")
            params.append(update_data.role)
            
        if update_data.subscription_tier is not None:
            update_fields.append(f"subscription_tier = ${len(params)+1}")
            params.append(update_data.subscription_tier)
            
        if update_data.subscription_status is not None:
            update_fields.append(f"subscription_status = ${len(params)+1}")
            params.append(update_data.subscription_status)
            
        if update_data.full_name is not None:
            update_fields.append(f"full_name = ${len(params)+1}")
            params.append(update_data.full_name)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        update_fields.append("updated_at = NOW()")
        params.append(user_id)
        
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ${len(params)} RETURNING id"
        result = await conn.fetchval(query, *params)
        
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"message": "User updated successfully", "id": user_id}

@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        admin_id = admin.get("id") or admin.get("sub")
        if int(user_id) == int(admin_id):
            raise HTTPException(status_code=400, detail="Cannot delete yourself")
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        return {"message": "User deleted"}

# ============================================================================
# Site Settings Endpoints
# ============================================================================

@app.get("/admin/settings")
async def get_site_settings(admin: dict = Depends(get_admin_user)):
    """Get site settings"""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM site_settings WHERE id = 1")
        if not row:
            raise HTTPException(status_code=404, detail="Settings not found")
        return dict(row)

@app.put("/admin/settings")
async def update_site_settings(settings_update: SiteSettingsUpdate, admin: dict = Depends(get_admin_user)):
    """Update site settings"""
    async with db_pool.acquire() as conn:
        # Build update query dynamically
        update_fields = []
        params = []
        
        if settings_update.site_name is not None:
            update_fields.append(f"site_name = ${len(params)+1}")
            params.append(settings_update.site_name)
            
        if settings_update.telegram_free_link is not None:
            update_fields.append(f"telegram_free_link = ${len(params)+1}")
            params.append(settings_update.telegram_free_link)
            
        if settings_update.telegram_vip_link is not None:
            update_fields.append(f"telegram_vip_link = ${len(params)+1}")
            params.append(settings_update.telegram_vip_link)
            
        if settings_update.vip_price is not None:
            update_fields.append(f"vip_price = ${len(params)+1}")
            params.append(settings_update.vip_price)
            
        if settings_update.vip_price_currency is not None:
            update_fields.append(f"vip_price_currency = ${len(params)+1}")
            params.append(settings_update.vip_price_currency)
            
        if settings_update.seo_default_title is not None:
            update_fields.append(f"seo_default_title = ${len(params)+1}")
            params.append(settings_update.seo_default_title)
            
        if settings_update.seo_default_description is not None:
            update_fields.append(f"seo_default_description = ${len(params)+1}")
            params.append(settings_update.seo_default_description)
            
        if settings_update.contact_email is not None:
            update_fields.append(f"contact_email = ${len(params)+1}")
            params.append(settings_update.contact_email)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        update_fields.append("updated_at = NOW()")
        params.append(1)  # id = 1
        
        query = f"UPDATE site_settings SET {', '.join(update_fields)} WHERE id = ${len(params)} RETURNING id"
        result = await conn.fetchval(query, *params)
        
        if not result:
            raise HTTPException(status_code=404, detail="Settings not found")
            
        # Return updated settings
        row = await conn.fetchrow("SELECT * FROM site_settings WHERE id = 1")
        return dict(row)

@app.get("/settings/public")
async def get_public_settings():
    """Get public site settings (no auth required)"""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT site_name, telegram_free_link, telegram_vip_link, vip_price, 
                   vip_price_currency, seo_default_title, seo_default_description, contact_email 
            FROM site_settings WHERE id = 1
        """)
        if not row:
            return {
                "site_name": "Pipways",
                "telegram_free_link": "https://t.me/pipways_free",
                "telegram_vip_link": "https://t.me/pipways_vip",
                "vip_price": 99.00,
                "vip_price_currency": "USD"
            }
        return dict(row)

# ============================================================================
# Blog Management
# ============================================================================

@app.get("/blog/posts")
async def get_blog_posts(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    limit: int = Query(10, le=50),
    page: int = Query(1, ge=1),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    async with db_pool.acquire() as conn:
        where_clauses = ["1=1"]
        params = []
        
        if not current_user or current_user.get("role") not in ["admin", "moderator"]:
            where_clauses.append("(status = 'published' OR status IS NULL)")
            where_clauses.append("(scheduled_at IS NULL OR scheduled_at <= NOW())")
        elif status:
            where_clauses.append(f"status = ${len(params)+1}")
            params.append(status)
            
        if category:
            where_clauses.append(f"category = ${len(params)+1}")
            params.append(category)
            
        if tag:
            where_clauses.append(f"${len(params)+1} = ANY(tags)")
            params.append(tag)

        count_query = f"SELECT COUNT(*) FROM blog_posts WHERE {' AND '.join(where_clauses)}"
        total = await conn.fetchval(count_query, *params)
        
        offset = (page - 1) * limit
        query = f"""
            SELECT bp.*, u.full_name as author_name 
            FROM blog_posts bp
            LEFT JOIN users u ON bp.author_id = u.id
            WHERE {' AND '.join(where_clauses)}
            ORDER BY bp.created_at DESC
            LIMIT ${len(params)+1} OFFSET ${len(params)+2}
        """
        params.extend([limit, offset])
        
        rows = await conn.fetch(query, *params)
        return {"posts": [dict(row) for row in rows], "total": total, "page": page, "pages": (total + limit - 1) // limit}

@app.get("/blog/posts/{slug}")
async def get_blog_post_by_slug(slug: str, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get single blog post by slug (public)"""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT bp.*, u.full_name as author_name 
            FROM blog_posts bp
            LEFT JOIN users u ON bp.author_id = u.id
            WHERE bp.slug = $1
        """, slug)
        
        if not row:
            raise HTTPException(status_code=404, detail="Post not found")
            
        post = dict(row)
        
        # Check if premium content and user has access
        if post.get("is_premium"):
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required for premium content")
            if current_user.get("subscription_tier") not in ["premium", "vip"] and current_user.get("role") not in ["admin", "moderator"]:
                raise HTTPException(status_code=403, detail="Premium subscription required")
        
        # Check if draft and user is not admin
        if post.get("status") == "draft" and (not current_user or current_user.get("role") not in ["admin", "moderator"]):
            raise HTTPException(status_code=404, detail="Post not found")
            
        return post

@app.get("/admin/blog/{post_id}")
async def get_blog_post_by_id(post_id: int, admin: dict = Depends(get_admin_user)):
    """Get single blog post by ID (admin only)"""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT bp.*, u.full_name as author_name 
            FROM blog_posts bp
            LEFT JOIN users u ON bp.author_id = u.id
            WHERE bp.id = $1
        """, post_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Post not found")
            
        return dict(row)

@app.post("/admin/blog")
async def create_blog_post(post: BlogPostCreate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        admin_id = admin.get("id") or admin.get("sub")
        
        base_slug = post.slug or re.sub(r'[^\w\s-]', '', post.title.lower().replace(" ", "-"))[:50]
        slug = base_slug
        
        counter = 1
        while await conn.fetchval("SELECT id FROM blog_posts WHERE slug = $1", slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        published_at = datetime.utcnow() if post.status == "published" and not post.scheduled_at else None
        
        post_id = await conn.fetchval("""
            INSERT INTO blog_posts (
                title, content, excerpt, author_id, is_premium, status, 
                scheduled_at, meta_title, meta_description, slug, featured_image, tags, category, published_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            RETURNING id
        """, post.title, post.content, post.excerpt, int(admin_id), post.is_premium, 
             post.status, post.scheduled_at, post.meta_title, post.meta_description,
             slug, post.featured_image, post.tags, post.category, published_at)
             
        return {"id": post_id, "slug": slug, "message": "Blog post created"}

@app.put("/admin/blog/{post_id}")
async def update_blog_post(post_id: int, post_update: BlogPostUpdate, admin: dict = Depends(get_admin_user)):
    """Update blog post"""
    async with db_pool.acquire() as conn:
        # Check if post exists
        existing = await conn.fetchrow("SELECT * FROM blog_posts WHERE id = $1", post_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        if post_update.title is not None:
            update_fields.append(f"title = ${len(params)+1}")
            params.append(post_update.title)
            
        if post_update.content is not None:
            update_fields.append(f"content = ${len(params)+1}")
            params.append(post_update.content)
            # Update excerpt automatically if content changed
            excerpt = post_update.content.replace("<[^>]*>", "")[:150] + "..."
            update_fields.append(f"excerpt = ${len(params)+1}")
            params.append(excerpt)
            
        if post_update.is_premium is not None:
            update_fields.append(f"is_premium = ${len(params)+1}")
            params.append(post_update.is_premium)
            
        if post_update.status is not None:
            update_fields.append(f"status = ${len(params)+1}")
            params.append(post_update.status)
            # Update published_at if status changed to published
            if post_update.status == "published" and existing["status"] != "published":
                update_fields.append(f"published_at = NOW()")
            
        if post_update.scheduled_at is not None:
            update_fields.append(f"scheduled_at = ${len(params)+1}")
            params.append(post_update.scheduled_at)
            
        if post_update.meta_title is not None:
            update_fields.append(f"meta_title = ${len(params)+1}")
            params.append(post_update.meta_title)
            
        if post_update.meta_description is not None:
            update_fields.append(f"meta_description = ${len(params)+1}")
            params.append(post_update.meta_description)
            
        if post_update.slug is not None:
            # Check slug uniqueness if changing
            if post_update.slug != existing["slug"]:
                slug_exists = await conn.fetchval("SELECT id FROM blog_posts WHERE slug = $1 AND id != $2", post_update.slug, post_id)
                if slug_exists:
                    raise HTTPException(status_code=400, detail="Slug already exists")
            update_fields.append(f"slug = ${len(params)+1}")
            params.append(post_update.slug)
            
        if post_update.featured_image is not None:
            update_fields.append(f"featured_image = ${len(params)+1}")
            params.append(post_update.featured_image)
            
        if post_update.tags is not None:
            update_fields.append(f"tags = ${len(params)+1}")
            params.append(post_update.tags)
            
        if post_update.category is not None:
            update_fields.append(f"category = ${len(params)+1}")
            params.append(post_update.category)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        update_fields.append("updated_at = NOW()")
        params.append(post_id)
        
        query = f"UPDATE blog_posts SET {', '.join(update_fields)} WHERE id = ${len(params)} RETURNING id"
        result = await conn.fetchval(query, *params)
        
        if not result:
            raise HTTPException(status_code=404, detail="Post not found")
            
        return {"message": "Blog post updated successfully", "id": post_id}

@app.delete("/admin/blog/{post_id}")
async def delete_blog_post(post_id: int, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM blog_posts WHERE id = $1", post_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Post not found")
        return {"message": "Post deleted"}

# ============================================================================
# Media Upload & Management
# ============================================================================

@app.post("/admin/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    admin: dict = Depends(get_admin_user)
):
    try:
        contents = await file.read()
        file_ext = file.filename.split(".")[-1].lower()
        unique_name = f"{uuid.uuid4().hex}.{file_ext}"
        
        if len(contents) > 50 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 50MB)")
        
        # Try Cloudinary first if available
        if CLOUDINARY_AVAILABLE and settings.CLOUDINARY_CLOUD_NAME:
            try:
                result = cloudinary.uploader.upload(
                    contents,
                    folder="pipways",
                    resource_type="auto",
                    public_id=unique_name.split('.')[0]
                )
                
                admin_id = admin.get("id") or admin.get("sub")
                async with db_pool.acquire() as conn:
                    media_id = await conn.fetchval("""
                        INSERT INTO media_files (filename, url, file_type, size_bytes, uploaded_by)
                        VALUES ($1, $2, $3, $4, $5)
                        RETURNING id
                    """, file.filename, result["secure_url"], result["resource_type"], result["bytes"], int(admin_id))
                    
                return {
                    "id": media_id,
                    "url": result["secure_url"],
                    "filename": file.filename,
                    "source": "cloudinary"
                }
            except Exception as cloud_err:
                logger.warning(f"Cloudinary failed, using local: {cloud_err}")
        
        # Local storage fallback
        file_path = os.path.join("uploads", unique_name)
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        file_type = "image" if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp'] else \
                   "video" if file_ext in ['mp4', 'webm', 'mov'] else "document"
        
        admin_id = admin.get("id") or admin.get("sub")
        async with db_pool.acquire() as conn:
            media_id = await conn.fetchval("""
                INSERT INTO media_files (filename, url, file_type, size_bytes, uploaded_by)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, file.filename, f"/uploads/{unique_name}", file_type, len(contents), int(admin_id))
            
        return {
            "id": media_id,
            "url": f"/uploads/{unique_name}",
            "filename": file.filename,
            "source": "local"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/admin/media/list")
async def list_media(
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    admin: dict = Depends(get_admin_user)
):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT m.*, u.full_name as uploader_name 
               FROM media_files m 
               LEFT JOIN users u ON m.uploaded_by = u.id 
               ORDER BY m.created_at DESC 
               LIMIT $1 OFFSET $2""",
            limit, offset
        )
        return {"files": [dict(row) for row in rows]}

@app.delete("/admin/media/{media_id}")
async def delete_media(media_id: int, admin: dict = Depends(get_admin_user)):
    """Delete media file with usage checking"""
    async with db_pool.acquire() as conn:
        # Get media info
        media = await conn.fetchrow("SELECT * FROM media_files WHERE id = $1", media_id)
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
        
        url = media["url"]
        
        # Check if used in blog posts
        blog_usage = await conn.fetchval("""
            SELECT COUNT(*) FROM blog_posts 
            WHERE featured_image = $1
        """, url)
        
        # Check if used in courses
        course_usage = await conn.fetchval("""
            SELECT COUNT(*) FROM courses 
            WHERE thumbnail = $1
        """, url)
        
        # Check if used in webinars
        webinar_usage = await conn.fetchval("""
            SELECT COUNT(*) FROM webinars 
            WHERE thumbnail = $1
        """, url)
        
        total_usage = blog_usage + course_usage + webinar_usage
        
        if total_usage > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete: Media is used in {blog_usage} blog posts, {course_usage} courses, {webinar_usage} webinars"
            )
        
        # Delete from storage if local file
        if url.startswith("/uploads/"):
            file_path = os.path.join("uploads", url.replace("/uploads/", ""))
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Delete from database
        await conn.execute("DELETE FROM media_files WHERE id = $1", media_id)
        
        return {"message": "Media deleted successfully"}

# ============================================================================
# Courses - Admin Management
# ============================================================================

@app.get("/admin/courses")
async def get_admin_courses(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: dict = Depends(get_admin_user)
):
    """Get all courses for admin with pagination and search"""
    async with db_pool.acquire() as conn:
        where_clauses = ["1=1"]
        params = []

        if search:
            where_clauses.append(f"(title ILIKE ${len(params)+1} OR description ILIKE ${len(params)+1})")
            params.append(f"%{search}%")

        count_query = f"SELECT COUNT(*) FROM courses WHERE {' AND '.join(where_clauses)}"
        total = await conn.fetchval(count_query, *params)

        offset = (page - 1) * limit
        query = f"""
            SELECT c.*, u.full_name as creator_name,
                   (SELECT COUNT(*) FROM course_modules WHERE course_id = c.id) as module_count,
                   (SELECT COUNT(*) FROM course_quizzes WHERE course_id = c.id) as quiz_count
            FROM courses c
            LEFT JOIN users u ON c.created_by = u.id
            WHERE {' AND '.join(where_clauses)}
            ORDER BY c.created_at DESC
            LIMIT ${len(params)+1} OFFSET ${len(params)+2}
        """
        params.extend([limit, offset])

        rows = await conn.fetch(query, *params)
        return {
            "courses": [dict(row) for row in rows],
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }

@app.get("/admin/courses/{course_id}")
async def get_admin_course_detail(course_id: int, admin: dict = Depends(get_admin_user)):
    """Get detailed course info with modules for admin"""
    async with db_pool.acquire() as conn:
        course = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        modules = await conn.fetch(
            "SELECT * FROM course_modules WHERE course_id = $1 ORDER BY sort_order, id",
            course_id
        )
        
        quizzes = await conn.fetch(
            "SELECT * FROM course_quizzes WHERE course_id = $1",
            course_id
        )
        
        return {
            "course": dict(course),
            "modules": [dict(m) for m in modules],
            "quizzes": [dict(q) for q in quizzes]
        }

@app.post("/admin/courses")
async def create_course(course: CourseCreate, admin: dict = Depends(get_admin_user)):
    """Create new course with modules"""
    async with db_pool.acquire() as conn:
        admin_id = admin.get("id") or admin.get("sub")
        
        # Create course
        course_id = await conn.fetchval("""
            INSERT INTO courses (title, description, content, level, duration_hours, thumbnail, is_premium, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """, course.title, course.description, course.content, course.level, 
             course.duration_hours, course.thumbnail, course.is_premium, int(admin_id))
        
        # Create modules if provided
        if course.modules:
            for idx, module in enumerate(course.modules):
                await conn.execute("""
                    INSERT INTO course_modules (course_id, title, content, video_url, sort_order, is_premium)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, course_id, module.get("title"), module.get("content"), 
                     module.get("video_url"), idx, module.get("is_premium", False))
        
        return {"id": course_id, "message": "Course created successfully"}

@app.put("/admin/courses/{course_id}")
async def update_course(course_id: int, course_update: CourseUpdate, admin: dict = Depends(get_admin_user)):
    """Update course details"""
    async with db_pool.acquire() as conn:
        # Check if course exists
        existing = await conn.fetchval("SELECT id FROM courses WHERE id = $1", course_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Course not found")
        
        update_fields = []
        params = []
        
        if course_update.title is not None:
            update_fields.append(f"title = ${len(params)+1}")
            params.append(course_update.title)
            
        if course_update.description is not None:
            update_fields.append(f"description = ${len(params)+1}")
            params.append(course_update.description)
            
        if course_update.content is not None:
            update_fields.append(f"content = ${len(params)+1}")
            params.append(course_update.content)
            
        if course_update.level is not None:
            update_fields.append(f"level = ${len(params)+1}")
            params.append(course_update.level)
            
        if course_update.duration_hours is not None:
            update_fields.append(f"duration_hours = ${len(params)+1}")
            params.append(course_update.duration_hours)
            
        if course_update.thumbnail is not None:
            update_fields.append(f"thumbnail = ${len(params)+1}")
            params.append(course_update.thumbnail)
            
        if course_update.is_premium is not None:
            update_fields.append(f"is_premium = ${len(params)+1}")
            params.append(course_update.is_premium)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        update_fields.append("updated_at = NOW()")
        params.append(course_id)
        
        query = f"UPDATE courses SET {', '.join(update_fields)} WHERE id = ${len(params)} RETURNING id"
        result = await conn.fetchval(query, *params)
        
        return {"message": "Course updated successfully", "id": course_id}

@app.delete("/admin/courses/{course_id}")
async def delete_course(course_id: int, admin: dict = Depends(get_admin_user)):
    """Delete course and all related data"""
    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM courses WHERE id = $1", course_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Course not found")
        return {"message": "Course deleted successfully"}

# ============================================================================
# Module Management
# ============================================================================

@app.post("/admin/courses/{course_id}/modules")
async def create_module(course_id: int, module: ModuleCreate, admin: dict = Depends(get_admin_user)):
    """Create new module for course"""
    async with db_pool.acquire() as conn:
        course_exists = await conn.fetchval("SELECT id FROM courses WHERE id = $1", course_id)
        if not course_exists:
            raise HTTPException(status_code=404, detail="Course not found")
        
        module_id = await conn.fetchval("""
            INSERT INTO course_modules (course_id, title, content, video_url, sort_order, is_premium)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """, course_id, module.title, module.content, module.video_url, 
             module.sort_order or 0, module.is_premium)
        
        return {"id": module_id, "message": "Module created successfully"}

@app.put("/admin/modules/{module_id}")
async def update_module(module_id: int, module_update: ModuleUpdate, admin: dict = Depends(get_admin_user)):
    """Update module"""
    async with db_pool.acquire() as conn:
        existing = await conn.fetchval("SELECT id FROM course_modules WHERE id = $1", module_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Module not found")
        
        update_fields = []
        params = []
        
        if module_update.title is not None:
            update_fields.append(f"title = ${len(params)+1}")
            params.append(module_update.title)
            
        if module_update.content is not None:
            update_fields.append(f"content = ${len(params)+1}")
            params.append(module_update.content)
            
        if module_update.video_url is not None:
            update_fields.append(f"video_url = ${len(params)+1}")
            params.append(module_update.video_url)
            
        if module_update.sort_order is not None:
            update_fields.append(f"sort_order = ${len(params)+1}")
            params.append(module_update.sort_order)
            
        if module_update.is_premium is not None:
            update_fields.append(f"is_premium = ${len(params)+1}")
            params.append(module_update.is_premium)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        params.append(module_id)
        
        query = f"UPDATE course_modules SET {', '.join(update_fields)} WHERE id = ${len(params)} RETURNING id"
        result = await conn.fetchval(query, *params)
        
        return {"message": "Module updated successfully", "id": module_id}

@app.delete("/admin/modules/{module_id}")
async def delete_module(module_id: int, admin: dict = Depends(get_admin_user)):
    """Delete module"""
    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM course_modules WHERE id = $1", module_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Module not found")
        return {"message": "Module deleted successfully"}

@app.post("/admin/modules/reorder")
async def reorder_modules(module_order: Dict[int, int], admin: dict = Depends(get_admin_user)):
    """Reorder modules - receives dict of {module_id: sort_order}"""
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            for module_id, sort_order in module_order.items():
                await conn.execute(
                    "UPDATE course_modules SET sort_order = $1 WHERE id = $2",
                    sort_order, module_id
                )
        return {"message": "Modules reordered successfully"}

# ============================================================================
# Quiz Management
# ============================================================================

@app.get("/admin/courses/{course_id}/quizzes")
async def get_course_quizzes(course_id: int, admin: dict = Depends(get_admin_user)):
    """Get all quizzes for a course"""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM course_quizzes WHERE course_id = $1 ORDER BY created_at DESC",
            course_id
        )
        return {"quizzes": [dict(row) for row in rows]}

@app.post("/admin/quizzes")
async def create_quiz(quiz: QuizCreate, admin: dict = Depends(get_admin_user)):
    """Create new quiz for course"""
    async with db_pool.acquire() as conn:
        course_exists = await conn.fetchval("SELECT id FROM courses WHERE id = $1", quiz.course_id)
        if not course_exists:
            raise HTTPException(status_code=404, detail="Course not found")
        
        admin_id = admin.get("id") or admin.get("sub")
        
        # Create quiz
        quiz_id = await conn.fetchval("""
            INSERT INTO course_quizzes (course_id, title, description, passing_score, created_by)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, quiz.course_id, quiz.title, quiz.description, quiz.passing_score, int(admin_id))
        
        # Add questions if provided
        if quiz.questions:
            for idx, q in enumerate(quiz.questions):
                await conn.execute("""
                    INSERT INTO quiz_questions 
                    (quiz_id, question_text, question_type, options, correct_answer, points, sort_order)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, quiz_id, q.get("question_text"), q.get("question_type", "multiple_choice"),
                     json.dumps(q.get("options", [])), q.get("correct_answer"), 
                     q.get("points", 1), idx)
        
        return {"id": quiz_id, "message": "Quiz created successfully"}

@app.get("/admin/quizzes/{quiz_id}")
async def get_quiz_detail(quiz_id: int, admin: dict = Depends(get_admin_user)):
    """Get quiz with questions"""
    async with db_pool.acquire() as conn:
        quiz = await conn.fetchrow("SELECT * FROM course_quizzes WHERE id = $1", quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        questions = await conn.fetch(
            "SELECT * FROM quiz_questions WHERE quiz_id = $1 ORDER BY sort_order",
            quiz_id
        )
        
        return {
            "quiz": dict(quiz),
            "questions": [dict(q) for q in questions]
        }

@app.put("/admin/quizzes/{quiz_id}")
async def update_quiz(quiz_id: int, quiz_update: QuizUpdate, admin: dict = Depends(get_admin_user)):
    """Update quiz"""
    async with db_pool.acquire() as conn:
        existing = await conn.fetchval("SELECT id FROM course_quizzes WHERE id = $1", quiz_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        update_fields = []
        params = []
        
        if quiz_update.title is not None:
            update_fields.append(f"title = ${len(params)+1}")
            params.append(quiz_update.title)
            
        if quiz_update.description is not None:
            update_fields.append(f"description = ${len(params)+1}")
            params.append(quiz_update.description)
            
        if quiz_update.passing_score is not None:
            update_fields.append(f"passing_score = ${len(params)+1}")
            params.append(quiz_update.passing_score)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        update_fields.append("updated_at = NOW()")
        params.append(quiz_id)
        
        query = f"UPDATE course_quizzes SET {', '.join(update_fields)} WHERE id = ${len(params)} RETURNING id"
        result = await conn.fetchval(query, *params)
        
        return {"message": "Quiz updated successfully", "id": quiz_id}

@app.delete("/admin/quizzes/{quiz_id}")
async def delete_quiz(quiz_id: int, admin: dict = Depends(get_admin_user)):
    """Delete quiz"""
    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM course_quizzes WHERE id = $1", quiz_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Quiz not found")
        return {"message": "Quiz deleted successfully"}

@app.post("/admin/quizzes/{quiz_id}/questions")
async def add_quiz_question(quiz_id: int, question: QuizQuestionCreate, admin: dict = Depends(get_admin_user)):
    """Add question to quiz"""
    async with db_pool.acquire() as conn:
        quiz_exists = await conn.fetchval("SELECT id FROM course_quizzes WHERE id = $1", quiz_id)
        if not quiz_exists:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        question_id = await conn.fetchval("""
            INSERT INTO quiz_questions 
            (quiz_id, question_text, question_type, options, correct_answer, points, sort_order)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """, quiz_id, question.question_text, question.question_type,
             json.dumps(question.options), question.correct_answer,
             question.points, question.sort_order)
        
        return {"id": question_id, "message": "Question added successfully"}

@app.delete("/admin/questions/{question_id}")
async def delete_question(question_id: int, admin: dict = Depends(get_admin_user)):
    """Delete question"""
    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM quiz_questions WHERE id = $1", question_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Question not found")
        return {"message": "Question deleted successfully"}

# ============================================================================
# Public Courses & Quizzes
# ============================================================================

@app.get("/courses")
async def get_courses(
    level: Optional[str] = Query(None),
    limit: int = Query(20),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    async with db_pool.acquire() as conn:
        query = "SELECT * FROM courses WHERE 1=1"
        params = []
        
        if level:
            query += f" AND level = ${len(params)+1}"
            params.append(level)
            
        tier = current_user.get("subscription_tier", "free") if current_user else "free"
        if tier == "free":
            query += " AND is_premium = FALSE"
            
        query += f" ORDER BY created_at DESC LIMIT ${len(params)+1}"
        params.append(limit)
        
        rows = await conn.fetch(query, *params)
        
        courses = []
        for row in rows:
            course = dict(row)
            modules = await conn.fetch(
                "SELECT * FROM course_modules WHERE course_id = $1 ORDER BY sort_order",
                course["id"]
            )
            course["modules"] = [dict(m) for m in modules]
            courses.append(course)
            
        return courses

@app.get("/courses/{course_id}")
async def get_course_by_id(course_id: int, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get single course by ID"""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
        if not row:
            raise HTTPException(status_code=404, detail="Course not found")
            
        course = dict(row)
        
        # Check premium access
        if course.get("is_premium"):
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            if current_user.get("subscription_tier") not in ["premium", "vip"] and current_user.get("role") not in ["admin", "moderator"]:
                raise HTTPException(status_code=403, detail="Premium subscription required")
        
        modules = await conn.fetch(
            "SELECT * FROM course_modules WHERE course_id = $1 ORDER BY sort_order",
            course_id
        )
        course["modules"] = [dict(m) for m in modules]
        
        # Get quizzes
        quizzes = await conn.fetch(
            "SELECT id, title, description, passing_score FROM course_quizzes WHERE course_id = $1",
            course_id
        )
        course["quizzes"] = [dict(q) for q in quizzes]
        
        return course

@app.get("/courses/{course_id}/quiz/{quiz_id}")
async def get_quiz_for_user(
    course_id: int, 
    quiz_id: int, 
    current_user: dict = Depends(get_current_user)
):
    """Get quiz questions for user (without correct answers)"""
    async with db_pool.acquire() as conn:
        # Verify access
        course = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
            
        if course["is_premium"] and current_user.get("subscription_tier") not in ["premium", "vip"]:
            raise HTTPException(status_code=403, detail="Premium subscription required")
        
        quiz = await conn.fetchrow(
            "SELECT * FROM course_quizzes WHERE id = $1 AND course_id = $2",
            quiz_id, course_id
        )
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        questions = await conn.fetch(
            """SELECT id, question_text, question_type, options, points, sort_order 
               FROM quiz_questions WHERE quiz_id = $1 ORDER BY sort_order""",
            quiz_id
        )
        
        return {
            "quiz": dict(quiz),
            "questions": [dict(q) for q in questions]
        }

@app.post("/quiz/{quiz_id}/submit")
async def submit_quiz_attempt(
    quiz_id: int, 
    attempt: QuizAttempt,
    current_user: dict = Depends(get_current_user)
):
    """Submit quiz attempt and grade"""
    async with db_pool.acquire() as conn:
        quiz = await conn.fetchrow("SELECT * FROM course_quizzes WHERE id = $1", quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Get all questions with correct answers
        questions = await conn.fetch(
            "SELECT id, correct_answer, points FROM quiz_questions WHERE quiz_id = $1",
            quiz_id
        )
        
        total_score = 0
        max_score = sum(q["points"] for q in questions)
        user_answers = attempt.answers
        
        for q in questions:
            user_answer = user_answers.get(str(q["id"]))
            if user_answer and str(user_answer).strip().lower() == str(q["correct_answer"]).strip().lower():
                total_score += q["points"]
        
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        passed = percentage >= quiz["passing_score"]
        
        # Save attempt
        attempt_id = await conn.fetchval("""
            INSERT INTO quiz_attempts 
            (quiz_id, user_id, answers, score, max_score, percentage, passed)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """, quiz_id, current_user["id"], json.dumps(user_answers),
             total_score, max_score, percentage, passed)
        
        return {
            "attempt_id": attempt_id,
            "score": total_score,
            "max_score": max_score,
            "percentage": round(percentage, 2),
            "passed": passed,
            "passing_score": quiz["passing_score"]
        }

@app.get("/quiz/results/me")
async def get_my_quiz_results(current_user: dict = Depends(get_current_user)):
    """Get current user's quiz results"""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT qa.*, cq.title as quiz_title, c.title as course_title
            FROM quiz_attempts qa
            JOIN course_quizzes cq ON qa.quiz_id = cq.id
            JOIN courses c ON cq.course_id = c.id
            WHERE qa.user_id = $1
            ORDER BY qa.completed_at DESC
        """, current_user["id"])
        
        return {"results": [dict(row) for row in rows]}

# ============================================================================
# Webinars (Fixed - Removed thumbnail)
# ============================================================================

@app.get("/webinars")
async def get_webinars(
    upcoming: bool = Query(True),
    limit: int = Query(20),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    async with db_pool.acquire() as conn:
        query = "SELECT * FROM webinars WHERE 1=1"
        params = []
        
        if upcoming:
            query += " AND scheduled_at > NOW()"
            
        tier = current_user.get("subscription_tier", "free") if current_user else "free"
        if tier == "free":
            query += " AND is_premium = FALSE"
            
        query += " ORDER BY scheduled_at ASC LIMIT $1"
        params.append(limit)
        
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]

@app.get("/webinars/{webinar_id}")
async def get_webinar_by_id(webinar_id: int, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get single webinar by ID"""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM webinars WHERE id = $1", webinar_id)
        if not row:
            raise HTTPException(status_code=404, detail="Webinar not found")
            
        webinar = dict(row)
        
        # Check premium access
        if webinar.get("is_premium"):
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            if current_user.get("subscription_tier") not in ["premium", "vip"] and current_user.get("role") not in ["admin", "moderator"]:
                raise HTTPException(status_code=403, detail="Premium subscription required")
        
        return webinar

@app.post("/admin/webinars")
async def create_webinar(webinar: WebinarCreate, admin: dict = Depends(get_admin_user)):
    """Create webinar - Fixed: removed thumbnail"""
    async with db_pool.acquire() as conn:
        admin_id = admin.get("id") or admin.get("sub")
        try:
            webinar_id = await conn.fetchval("""
                INSERT INTO webinars (
                    title, description, scheduled_at, duration_minutes, meeting_link, 
                    is_premium, max_participants, recording_link, reminder_message, created_by
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """, webinar.title, webinar.description, webinar.scheduled_at, 
                 webinar.duration_minutes, webinar.meeting_link, webinar.is_premium, 
                 webinar.max_participants, webinar.recording_link,
                 webinar.reminder_message, int(admin_id))
            return {"id": webinar_id, "message": "Webinar created successfully"}
        except Exception as e:
            logger.error(f"Error creating webinar: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create webinar: {str(e)}")

@app.put("/admin/webinars/{webinar_id}")
async def update_webinar(webinar_id: int, webinar: WebinarUpdate, admin: dict = Depends(get_admin_user)):
    """Update webinar - Fixed: removed thumbnail"""
    async with db_pool.acquire() as conn:
        existing = await conn.fetchval("SELECT id FROM webinars WHERE id = $1", webinar_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Webinar not found")
        
        update_fields = []
        params = []
        
        if webinar.title is not None:
            update_fields.append(f"title = ${len(params)+1}")
            params.append(webinar.title)
            
        if webinar.description is not None:
            update_fields.append(f"description = ${len(params)+1}")
            params.append(webinar.description)
            
        if webinar.scheduled_at is not None:
            update_fields.append(f"scheduled_at = ${len(params)+1}")
            params.append(webinar.scheduled_at)
            
        if webinar.duration_minutes is not None:
            update_fields.append(f"duration_minutes = ${len(params)+1}")
            params.append(webinar.duration_minutes)
            
        if webinar.meeting_link is not None:
            update_fields.append(f"meeting_link = ${len(params)+1}")
            params.append(webinar.meeting_link)
            
        if webinar.is_premium is not None:
            update_fields.append(f"is_premium = ${len(params)+1}")
            params.append(webinar.is_premium)
            
        if webinar.max_participants is not None:
            update_fields.append(f"max_participants = ${len(params)+1}")
            params.append(webinar.max_participants)
            
        if webinar.recording_link is not None:
            update_fields.append(f"recording_link = ${len(params)+1}")
            params.append(webinar.recording_link)
            
        if webinar.reminder_message is not None:
            update_fields.append(f"reminder_message = ${len(params)+1}")
            params.append(webinar.reminder_message)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        params.append(webinar_id)
        
        query = f"UPDATE webinars SET {', '.join(update_fields)} WHERE id = ${len(params)} RETURNING id"
        result = await conn.fetchval(query, *params)
        
        return {"message": "Webinar updated successfully", "id": webinar_id}

@app.delete("/admin/webinars/{webinar_id}")
async def delete_webinar(webinar_id: int, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM webinars WHERE id = $1", webinar_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Webinar not found")
        return {"message": "Webinar deleted successfully"}

# ============================================================================
# Signals (Fixed and Enhanced)
# ============================================================================

@app.get("/signals")
async def get_signals(
    status: Optional[str] = Query(None),
    pair: Optional[str] = Query(None),
    limit: int = Query(50),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    async with db_pool.acquire() as conn:
        query = "SELECT * FROM signals WHERE 1=1"
        params = []
        
        if status:
            query += f" AND status = ${len(params)+1}"
            params.append(status)
        if pair:
            query += f" AND pair ILIKE ${len(params)+1}"
            params.append(f"%{pair}%")
            
        tier = current_user.get("subscription_tier", "free") if current_user else "free"
        if tier == "free":
            query += " AND is_premium = FALSE"
            
        query += f" ORDER BY created_at DESC LIMIT ${len(params)+1}"
        params.append(limit)
        
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]

@app.get("/signals/{signal_id}")
async def get_signal_by_id(signal_id: int, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get single signal by ID with full details"""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM signals WHERE id = $1", signal_id)
        if not row:
            raise HTTPException(status_code=404, detail="Signal not found")
            
        signal = dict(row)
        
        # Check premium access
        if signal.get("is_premium"):
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            if current_user.get("subscription_tier") not in ["premium", "vip"] and current_user.get("role") not in ["admin", "moderator"]:
                raise HTTPException(status_code=403, detail="Premium subscription required")
        
        return signal

@app.post("/admin/signals")
async def create_signal(signal: SignalCreate, admin: dict = Depends(get_admin_user)):
    """Create signal - Fixed: ensured all columns match"""
    async with db_pool.acquire() as conn:
        admin_id = admin.get("id") or admin.get("sub")
        try:
            signal_id = await conn.fetchval("""
                INSERT INTO signals (pair, direction, entry_price, stop_loss, take_profit_1, take_profit_2, 
                    risk_reward_ratio, timeframe, analysis, is_premium, expires_at, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING id
            """, signal.pair.upper(), signal.direction, signal.entry_price, signal.stop_loss,
                 signal.take_profit_1, signal.take_profit_2, signal.risk_reward_ratio, 
                 signal.timeframe, signal.analysis, signal.is_premium, signal.expires_at, int(admin_id))
            return {"id": signal_id, "message": "Signal created successfully"}
        except Exception as e:
            logger.error(f"Error creating signal: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create signal: {str(e)}")

@app.put("/admin/signals/{signal_id}")
async def update_signal(signal_id: int, signal: SignalUpdate, admin: dict = Depends(get_admin_user)):
    """Update signal including result - Fixed: ensures 405 error is resolved"""
    async with db_pool.acquire() as conn:
        existing = await conn.fetchval("SELECT id FROM signals WHERE id = $1", signal_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Signal not found")
            
        update_fields = []
        params = []
        
        if signal.pair is not None:
            update_fields.append(f"pair = ${len(params)+1}")
            params.append(signal.pair.upper())
        if signal.direction is not None:
            update_fields.append(f"direction = ${len(params)+1}")
            params.append(signal.direction)
        if signal.entry_price is not None:
            update_fields.append(f"entry_price = ${len(params)+1}")
            params.append(signal.entry_price)
        if signal.stop_loss is not None:
            update_fields.append(f"stop_loss = ${len(params)+1}")
            params.append(signal.stop_loss)
        if signal.take_profit_1 is not None:
            update_fields.append(f"take_profit_1 = ${len(params)+1}")
            params.append(signal.take_profit_1)
        if signal.take_profit_2 is not None:
            update_fields.append(f"take_profit_2 = ${len(params)+1}")
            params.append(signal.take_profit_2)
        if signal.risk_reward_ratio is not None:
            update_fields.append(f"risk_reward_ratio = ${len(params)+1}")
            params.append(signal.risk_reward_ratio)
        if signal.timeframe is not None:
            update_fields.append(f"timeframe = ${len(params)+1}")
            params.append(signal.timeframe)
        if signal.analysis is not None:
            update_fields.append(f"analysis = ${len(params)+1}")
            params.append(signal.analysis)
        if signal.is_premium is not None:
            update_fields.append(f"is_premium = ${len(params)+1}")
            params.append(signal.is_premium)
        if signal.status is not None:
            update_fields.append(f"status = ${len(params)+1}")
            params.append(signal.status)
        if signal.result is not None:
            update_fields.append(f"result = ${len(params)+1}")
            params.append(signal.result)
            if signal.result in ["WIN", "LOSS", "PARTIAL", "EXPIRED"]:
                update_fields.append(f"closed_at = NOW()")
        if signal.expires_at is not None:
            update_fields.append(f"expires_at = ${len(params)+1}")
            params.append(signal.expires_at)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        update_fields.append("updated_at = NOW()")
        params.append(signal_id)
        
        query = f"UPDATE signals SET {', '.join(update_fields)} WHERE id = ${len(params)} RETURNING id"
        result = await conn.fetchval(query, *params)
        
        if not result:
            raise HTTPException(status_code=404, detail="Signal not found")
            
        return {"message": "Signal updated successfully", "id": signal_id}

@app.put("/admin/signals/{signal_id}/result")
async def update_signal_result(
    signal_id: int, 
    result_update: SignalResultUpdate, 
    admin: dict = Depends(get_admin_user)
):
    """Dedicated endpoint for updating signal result only"""
    async with db_pool.acquire() as conn:
        existing = await conn.fetchval("SELECT id FROM signals WHERE id = $1", signal_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        # Update result and closed_at
        await conn.execute("""
            UPDATE signals 
            SET result = $1, 
                status = 'closed',
                closed_at = NOW(),
                updated_at = NOW()
            WHERE id = $2
        """, result_update.result, signal_id)
        
        return {
            "message": "Signal result updated successfully", 
            "id": signal_id,
            "result": result_update.result
        }

@app.delete("/admin/signals/{signal_id}")
async def delete_signal(signal_id: int, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM signals WHERE id = $1", signal_id)
        return {"message": "Signal deleted"}

# ============================================================================
# AI Chat (Mentor) with Knowledge Retrieval
# ============================================================================

async def search_knowledge_base(query: str, user_id: int):
    """Search platform content for relevant context"""
    async with db_pool.acquire() as conn:
        context_parts = []
        
        # Search blog posts
        blog_results = await conn.fetch("""
            SELECT title, content, category FROM blog_posts 
            WHERE status = 'published' AND (title ILIKE $1 OR content ILIKE $1 OR category ILIKE $1)
            LIMIT 3
        """, f"%{query}%")
        
        if blog_results:
            context_parts.append("## Relevant Blog Posts:")
            for post in blog_results:
                excerpt = post["content"][:200] + "..." if len(post["content"]) > 200 else post["content"]
                context_parts.append(f"- {post['title']} ({post['category']}): {excerpt}")
        
        # Search courses
        course_results = await conn.fetch("""
            SELECT c.title, c.description, c.level FROM courses c
            WHERE c.title ILIKE $1 OR c.description ILIKE $1
            LIMIT 2
        """, f"%{query}%")
        
        if course_results:
            context_parts.append("\n## Relevant Courses:")
            for course in course_results:
                context_parts.append(f"- {course['title']} ({course['level']}): {course['description'][:150]}...")
        
        # Search webinars
        webinar_results = await conn.fetch("""
            SELECT title, description, scheduled_at FROM webinars
            WHERE scheduled_at > NOW() AND (title ILIKE $1 OR description ILIKE $1)
            ORDER BY scheduled_at ASC
            LIMIT 2
        """, f"%{query}%")
        
        if webinar_results:
            context_parts.append("\n## Upcoming Webinars:")
            for w in webinar_results:
                context_parts.append(f"- {w['title']} on {w['scheduled_at'].strftime('%Y-%m-%d')}")
        
        # Get user performance summary for personalization
        perf_results = await conn.fetch("""
            SELECT analysis_data->>'trader_score' as score, 
                   analysis_data->>'performance_summary' as summary
            FROM performance_analyses 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT 1
        """, user_id)
        
        user_context = ""
        if perf_results:
            user_context = f"\n## User's Recent Trading Performance: Score {perf_results[0]['score'] or 'N/A'}"
        
        return "\n".join(context_parts) + user_context

@app.post("/chat")
async def chat_with_ai(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    try:
        # Search knowledge base if requested
        knowledge_context = ""
        if request.include_knowledge:
            knowledge_context = await search_knowledge_base(request.message, current_user["id"])
        
        system_prompt = """You are an expert trading mentor with 20+ years of experience in forex, stocks, and crypto trading. You provide personalized, actionable advice on trading strategies, risk management, trading psychology, and market analysis. 
        
        Important guidelines:
        1. Keep responses concise but informative (max 3 paragraphs unless detailed analysis requested)
        2. Always emphasize risk management and discipline
        3. Reference specific platform content when relevant (courses, blog posts, webinars)
        4. Consider the user's trading history and performance when providing advice
        5. Be encouraging but realistic about trading expectations"""
        
        if knowledge_context:
            system_prompt += f"\n\n## Platform Knowledge Base Context:\n{knowledge_context}\n\nUse this context to provide relevant, specific recommendations referencing our courses and materials when appropriate."
        
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        if request.history:
            messages.extend(request.history[-5:])
            
        messages.append({"role": "user", "content": request.message})
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://pipways.com",
                    "X-Title": "Pipways AI Mentor"
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": messages,
                    "max_tokens": 800,
                    "temperature": 0.7
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="AI service error")
            
            result = response.json()
            ai_message = result["choices"][0]["message"]["content"]
            
            # Store in chat history with user isolation
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO chat_history (user_id, message, response, context)
                    VALUES ($1, $2, $3, $4)
                """, current_user["id"], request.message, ai_message, knowledge_context[:500])
            
            return {"response": ai_message, "timestamp": datetime.utcnow().isoformat()}
            
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/history")
async def get_chat_history(
    limit: int = Query(20),
    current_user: dict = Depends(get_current_user)
):
    """Get chat history - user isolated"""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT message, response, created_at 
            FROM chat_history 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
        """, current_user["id"], limit)
        return {"history": [dict(row) for row in rows]}

# ============================================================================
# AI Performance Analyzer with Vision (UPDATED)
# ============================================================================

@app.post("/analyze/performance")
async def analyze_performance(
    file: UploadFile = File(...),
    account_balance: Optional[float] = Form(None),
    trading_period_days: Optional[int] = Form(30),
    current_user: dict = Depends(get_current_user)
):
    """Vision-based performance analysis from screenshots/PDFs"""
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    # Check usage limits
    can_use = await check_ai_usage_limit(current_user["id"], "performance", current_user.get("subscription_tier", "free"))
    if not can_use:
        raise HTTPException(status_code=429, detail="AI usage limit exceeded. Upgrade to premium for more analyses.")

    try:
        contents = await file.read()
        file_ext = file.filename.split(".")[-1].lower()
        
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")

        # For PDFs, we'll extract text using simple approach since we can't add PyPDF2
        if file_ext == 'pdf':
            raise HTTPException(status_code=400, detail="PDF support coming soon. Please upload image screenshots (JPG/PNG) for now.")
        
        # Process image with vision AI
        image_base64 = base64.b64encode(contents).decode()

        system_prompt = """You are an expert trading data extraction and analysis AI. Your task is to:
1. Extract all visible trade data from the trading statement/screenshot
2. Identify: Pair/Symbol, Entry Price, Exit Price, Lots/Size, Profit/Loss in pips or currency, Direction (Buy/Sell), Date/Time if visible
3. Calculate performance metrics
4. Provide professional trading analysis

Respond in strict JSON format with:
{
  "extracted_trades": [{"pair": "EURUSD", "direction": "buy", "entry": 1.0850, "exit": 1.0900, "lots": 0.1, "pips": 50, "profit": 500}],
  "performance_summary": {"total_trades": 10, "win_rate": "65%", "net_pips": 150, "avg_win": 30, "avg_loss": -20, "risk_reward_ratio": "1:1.5", "profit_factor": 1.8, "max_drawdown": "5%"},
  "trader_score": 75,
  "strengths": ["identified strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "top_mistakes": ["mistake 1", "mistake 2"],
  "improvement_plan": {
    "immediate_actions": ["action 1", "action 2"],
    "strategy_improvements": ["improvement 1"],
    "risk_management_fixes": ["fix 1"]
  },
  "recommended_courses": ["Risk Management", "Technical Analysis"],
  "mentor_advice": "Personalized advice based on the trading patterns observed"
}"""

        user_prompt = f"""Analyze this trading statement screenshot. Extract all trade data and provide comprehensive performance analysis.

Account Balance (if provided by user): {account_balance or 'Not provided'}
Trading Period: {trading_period_days} days

Extract every visible trade and calculate all metrics accurately."""

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://pipways.com",
                    "X-Title": "Pipways Vision Analyzer"
                },
                json={
                    "model": settings.OPENROUTER_VISION_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/{file_ext};base64,{image_base64}"}}
                            ]
                        }
                    ],
                    "max_tokens": 2500,
                    "temperature": 0.4
                }
            )

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="AI vision analysis failed")

            result = response.json()
            ai_content = result["choices"][0]["message"]["content"]
            
            try:
                cleaned = ai_content.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                    cleaned = cleaned.strip()
                
                analysis_data = json.loads(cleaned)
                
                # Store analysis with user isolation
                async with db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO performance_analyses (user_id, analysis_data, raw_trades, trader_score)
                        VALUES ($1, $2, $3, $4)
                    """, current_user["id"], json.dumps(analysis_data), 
                         json.dumps(analysis_data.get("extracted_trades", [])),
                         analysis_data.get("trader_score", 0))
                
                # Log usage
                await log_ai_usage(current_user["id"], "performance")
                
                return {
                    "analysis": analysis_data,
                    "timestamp": datetime.utcnow().isoformat(),
                    "extracted_trades": analysis_data.get("extracted_trades", [])
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}, content: {ai_content[:200]}")
                return {"raw_analysis": ai_content, "error": "Parse error - but analysis completed", "extracted_text": ai_content[:1000]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vision analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze/performance/history")
async def get_performance_history(
    limit: int = Query(10),
    current_user: dict = Depends(get_current_user)
):
    """Get user's performance analysis history - USER ISOLATED"""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, analysis_data, trader_score, created_at
            FROM performance_analyses
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, current_user["id"], limit)
        
        return {"history": [dict(row) for row in rows]}

@app.delete("/analysis/performance/{analysis_id}")
async def delete_performance_analysis(analysis_id: int, current_user: dict = Depends(get_current_user)):
    """Delete user's own performance analysis"""
    async with db_pool.acquire() as conn:
        # Verify ownership
        owner = await conn.fetchval(
            "SELECT user_id FROM performance_analyses WHERE id = $1", 
            analysis_id
        )
        if not owner:
            raise HTTPException(status_code=404, detail="Analysis not found")
        if owner != current_user["id"]:
            raise HTTPException(status_code=403, detail="Can only delete your own analyses")
        
        await conn.execute("DELETE FROM performance_analyses WHERE id = $1", analysis_id)
        return {"message": "Analysis deleted"}

# ============================================================================
# AI Chart Analysis (Screenshot Analysis) - USER ISOLATED
# ============================================================================

@app.post("/analyze/chart")
async def analyze_chart(
    file: UploadFile = File(...),
    pair: Optional[str] = Form("EURUSD"),
    timeframe: Optional[str] = Form("1H"),
    additional_info: Optional[str] = Form(""),
    current_user: dict = Depends(get_current_user)
):
    """AI Chart Screenshot Analysis - User isolated with usage limits"""
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    # Check usage limits
    can_use = await check_ai_usage_limit(current_user["id"], "chart", current_user.get("subscription_tier", "free"))
    if not can_use:
        raise HTTPException(status_code=429, detail="AI usage limit exceeded. Free users get 3 analyses total. Upgrade to premium for 3 per day.")

    try:
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")

        image_base64 = base64.b64encode(contents).decode()

        prompt = f"""Analyze this {pair} chart on {timeframe}. Context: {additional_info}

Provide a detailed technical analysis including trend direction, key support/resistance levels, pattern recognition, and a trading recommendation if applicable. Format your response as a professional trading report."""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://pipways.com",
                    "X-Title": "Pipways AI Analysis"
                },
                json={
                    "model": settings.OPENROUTER_VISION_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                            ]
                        }
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.3
                }
            )

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="AI service error")

            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
            formatted_report = f"""📊 TECHNICAL ANALYSIS: {pair} ({timeframe})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{ai_response}

[Analysis generated by AI at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}]"""

            # Store analysis with user isolation
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO chart_analyses (user_id, pair, timeframe, analysis_text)
                    VALUES ($1, $2, $3, $4)
                """, current_user["id"], pair, timeframe, formatted_report)
            
            # Log usage
            await log_ai_usage(current_user["id"], "chart")
            
            return {
                "analysis": formatted_report,
                "pair": pair,
                "timeframe": timeframe
            }
                
    except Exception as e:
        logger.error(f"Chart analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze/chart/history")
async def get_chart_analysis_history(
    limit: int = Query(10),
    current_user: dict = Depends(get_current_user)
):
    """Get user's chart analysis history - USER ISOLATED"""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, pair, timeframe, analysis_text, created_at
            FROM chart_analyses
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, current_user["id"], limit)
        
        return {"history": [dict(row) for row in rows]}

@app.delete("/analysis/chart/{analysis_id}")
async def delete_chart_analysis(analysis_id: int, current_user: dict = Depends(get_current_user)):
    """Delete user's own chart analysis"""
    async with db_pool.acquire() as conn:
        # Verify ownership
        owner = await conn.fetchval(
            "SELECT user_id FROM chart_analyses WHERE id = $1", 
            analysis_id
        )
        if not owner:
            raise HTTPException(status_code=404, detail="Analysis not found")
        if owner != current_user["id"]:
            raise HTTPException(status_code=403, detail="Can only delete your own analyses")
        
        await conn.execute("DELETE FROM chart_analyses WHERE id = $1", analysis_id)
        return {"message": "Analysis deleted"}

@app.get("/ai/usage")
async def get_ai_usage(current_user: dict = Depends(get_current_user)):
    """Get current AI usage stats for user"""
    async with db_pool.acquire() as conn:
        tier = current_user.get("subscription_tier", "free")
        
        # Chart usage
        if tier in ["premium", "vip"]:
            chart_used = await conn.fetchval("""
                SELECT COUNT(*) FROM ai_usage_logs 
                WHERE user_id = $1 AND analysis_type = 'chart' 
                AND created_at > NOW() - INTERVAL '1 day'
            """, current_user["id"])
            chart_limit = 3
        else:
            chart_used = await conn.fetchval("""
                SELECT COUNT(*) FROM ai_usage_logs 
                WHERE user_id = $1 AND analysis_type = 'chart'
            """, current_user["id"])
            chart_limit = 3
        
        # Performance usage
        if tier in ["premium", "vip"]:
            perf_used = await conn.fetchval("""
                SELECT COUNT(*) FROM ai_usage_logs 
                WHERE user_id = $1 AND analysis_type = 'performance' 
                AND created_at > NOW() - INTERVAL '7 days'
            """, current_user["id"])
            perf_limit = 1
        else:
            perf_used = await conn.fetchval("""
                SELECT COUNT(*) FROM ai_usage_logs 
                WHERE user_id = $1 AND analysis_type = 'performance'
            """, current_user["id"])
            perf_limit = 1
        
        return {
            "chart_analysis": {
                "used": chart_used,
                "limit": chart_limit,
                "remaining": max(0, chart_limit - chart_used)
            },
            "performance_analysis": {
                "used": perf_used,
                "limit": perf_limit,
                "remaining": max(0, perf_limit - perf_used)
            },
            "tier": tier
        }

# ============================================================================
# Health Check & Frontend Serving
# ============================================================================

@app.get("/health")
async def health_check():
    db_status = "unknown"
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "version": "3.5.2",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# Serve frontend at root
@app.get("/")
async def serve_frontend():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "Pipways API v3.5.2 - Place index.html in root directory"}

# SPA catch-all route (must be LAST)
@app.get("/{path:path}")
async def spa_catch_all(path: str, request: Request):
    # Skip API routes
    if path.startswith(("auth", "admin", "blog", "courses", "webinars", "signals", "chat", "analyze", "uploads", "health", "settings", "quiz", "ai")):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Check if requesting a blog post slug (path doesn't contain dots and isn't a file)
    if path and "." not in path and not path.startswith(("api", "static", "assets")):
        # Let frontend handle routing
        if os.path.exists("index.html"):
            return FileResponse("index.html")
    
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "Pipways API v3.5.2"}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
