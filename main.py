"""
Pipways Trading Platform API - Production v3.4.0
With PDF/CSV Analysis, SEO Features, and Enhanced AI Context
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
import io
import csv
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

# PDF processing
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Optional Cloudinary import
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

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
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    OPENROUTER_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "anthropic/claude-3.5-sonnet")
    CORS_ORIGINS = ["*"]

settings = Settings()

if CLOUDINARY_AVAILABLE and settings.CLOUDINARY_CLOUD_NAME:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET
    )

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
        os.makedirs("uploads", exist_ok=True)
        logger.info("Database and storage initialized successfully")
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        raise
    yield
    if db_pool:
        await db_pool.close()

app = FastAPI(title="Pipways API", version="3.4.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

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

class WebinarUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    is_premium: Optional[bool] = None
    meeting_link: Optional[str] = None
    max_participants: Optional[int] = None

class SignalCreate(BaseModel):
    pair: str = Field(..., min_length=1)
    direction: str = Field(..., pattern="^(buy|sell)$")
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timeframe: str = "1H"
    analysis: Optional[str] = None
    is_premium: bool = False

class SignalUpdate(BaseModel):
    pair: Optional[str] = None
    direction: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timeframe: Optional[str] = None
    analysis: Optional[str] = None
    is_premium: Optional[bool] = None
    status: Optional[str] = None

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
    modules: Optional[List[Dict]] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context: Optional[str] = ""

class PerformanceAnalysisRequest(BaseModel):
    account_balance: Optional[float] = None
    trading_period_days: Optional[int] = 30

# ============================================================================
# Database Initialization
# ============================================================================

async def init_db():
    async with db_pool.acquire() as conn:
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
                published_at TIMESTAMP,
                seo_score INTEGER DEFAULT 0,
                keyword_density JSONB
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id SERIAL PRIMARY KEY,
                pair VARCHAR(20) NOT NULL,
                direction VARCHAR(10) NOT NULL,
                entry_price DECIMAL(10,5),
                stop_loss DECIMAL(10,5),
                take_profit DECIMAL(10,5),
                timeframe VARCHAR(20),
                analysis TEXT,
                status VARCHAR(20) DEFAULT 'active',
                pips_gain DECIMAL(10,2),
                is_premium BOOLEAN DEFAULT FALSE,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP
            )
        """)

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
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

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

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                context TEXT,
                user_context JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

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

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_analyses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                analysis_data JSONB NOT NULL,
                raw_trades JSONB,
                trader_score INTEGER,
                file_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

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

async def get_user_full_context(user_id: int) -> Dict[str, Any]:
    """Fetch complete user profile for AI context"""
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("""
            SELECT id, email, full_name, role, subscription_tier, subscription_status, created_at
            FROM users WHERE id = $1
        """, user_id)
        
        if not user:
            return {}
        
        # Get trading stats
        total_trades = await conn.fetchval(
            "SELECT COUNT(*) FROM performance_analyses WHERE user_id = $1", user_id
        ) or 0
        
        recent_analysis = await conn.fetchrow("""
            SELECT trader_score, created_at FROM performance_analyses 
            WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1
        """, user_id)
        
        return {
            "name": user["full_name"],
            "email": user["email"],
            "subscription": user["subscription_tier"],
            "role": user["role"],
            "member_since": user["created_at"].strftime("%Y-%m-%d") if user["created_at"] else "N/A",
            "total_analyses": total_trades,
            "last_trader_score": recent_analysis["trader_score"] if recent_analysis else None
        }

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

@app.get("/users/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get full user profile with stats for AI context"""
    user_id = int(current_user.get("id") or current_user.get("sub"))
    context = await get_user_full_context(user_id)
    return context

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

@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        admin_id = admin.get("id") or admin.get("sub")
        if int(user_id) == int(admin_id):
            raise HTTPException(status_code=400, detail="Cannot delete yourself")
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        return {"message": "User deleted"}

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
        return {"posts": [dict(row) for row in rows], "total": total, "page": page}

@app.get("/blog/posts/{post_id}")
async def get_single_post(post_id: int, current_user: Optional[dict] = Depends(get_current_user_optional)):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT bp.*, u.full_name as author_name 
            FROM blog_posts bp
            LEFT JOIN users u ON bp.author_id = u.id
            WHERE bp.id = $1
        """, post_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Post not found")
            
        post = dict(row)
        if post.get("status") != "published" and (not current_user or current_user.get("role") not in ["admin", "moderator"]):
            raise HTTPException(status_code=403, detail="Access denied")
            
        if post.get("is_premium") and (not current_user or current_user.get("subscription_tier") == "free"):
            raise HTTPException(status_code=403, detail="Premium content")
            
        return post

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
        
        # Calculate initial SEO score
        seo_score = calculate_seo_score(post.title, post.content, post.meta_description, post.tags)
        
        post_id = await conn.fetchval("""
            INSERT INTO blog_posts (
                title, content, excerpt, author_id, is_premium, status, 
                scheduled_at, meta_title, meta_description, slug, featured_image, tags, category,
                published_at, seo_score
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            RETURNING id
        """, post.title, post.content, post.excerpt, int(admin_id), post.is_premium, 
             post.status, post.scheduled_at, post.meta_title, post.meta_description,
             slug, post.featured_image, post.tags, post.category, published_at, seo_score)
             
        return {"id": post_id, "slug": slug, "message": "Blog post created", "seo_score": seo_score}

@app.put("/admin/blog/{post_id}")
async def update_blog_post(post_id: int, post: BlogPostUpdate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        # Build dynamic update query
        update_fields = []
        params = []
        
        if post.title is not None:
            update_fields.append(f"title = ${len(params)+1}")
            params.append(post.title)
        if post.content is not None:
            update_fields.append(f"content = ${len(params)+1}")
            params.append(post.content)
            # Recalculate SEO score when content changes
            current = await conn.fetchrow("SELECT title, meta_description, tags FROM blog_posts WHERE id = $1", post_id)
            if current:
                seo_score = calculate_seo_score(
                    post.title or current["title"], 
                    post.content, 
                    post.meta_description or current["meta_description"], 
                    post.tags or current["tags"]
                )
                update_fields.append(f"seo_score = ${len(params)+1}")
                params.append(seo_score)
        if post.excerpt is not None:
            update_fields.append(f"excerpt = ${len(params)+1}")
            params.append(post.excerpt)
        if post.is_premium is not None:
            update_fields.append(f"is_premium = ${len(params)+1}")
            params.append(post.is_premium)
        if post.status is not None:
            update_fields.append(f"status = ${len(params)+1}")
            params.append(post.status)
        if post.scheduled_at is not None:
            update_fields.append(f"scheduled_at = ${len(params)+1}")
            params.append(post.scheduled_at)
        if post.meta_title is not None:
            update_fields.append(f"meta_title = ${len(params)+1}")
            params.append(post.meta_title)
        if post.meta_description is not None:
            update_fields.append(f"meta_description = ${len(params)+1}")
            params.append(post.meta_description)
        if post.featured_image is not None:
            update_fields.append(f"featured_image = ${len(params)+1}")
            params.append(post.featured_image)
        if post.tags is not None:
            update_fields.append(f"tags = ${len(params)+1}")
            params.append(post.tags)
        if post.category is not None:
            update_fields.append(f"category = ${len(params)+1}")
            params.append(post.category)
            
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        update_fields.append("updated_at = NOW()")
        params.append(post_id)
        
        query = f"UPDATE blog_posts SET {', '.join(update_fields)} WHERE id = ${len(params)} RETURNING id"
        result = await conn.fetchval(query, *params)
        
        if not result:
            raise HTTPException(status_code=404, detail="Post not found")
            
        return {"id": post_id, "message": "Blog post updated"}

@app.delete("/admin/blog/{post_id}")
async def delete_blog_post(post_id: int, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM blog_posts WHERE id = $1", post_id)
        return {"message": "Post deleted"}

def calculate_seo_score(title: str, content: str, meta_desc: Optional[str], tags: Optional[List[str]]) -> int:
    """Calculate SEO score 0-100"""
    score = 0
    
    # Title checks (20 points)
    if title:
        if len(title) >= 50 and len(title) <= 60:
            score += 10
        else:
            score += 5
        if any(c.isupper() for c in title):
            score += 5
        if any(c.isdigit() for c in title):
            score += 5
    
    # Content length (30 points)
    if content:
        word_count = len(content.split())
        if word_count >= 300:
            score += 30
        elif word_count >= 150:
            score += 20
        else:
            score += 10
    
    # Meta description (20 points)
    if meta_desc and len(meta_desc) >= 120 and len(meta_desc) <= 160:
        score += 20
    elif meta_desc:
        score += 10
    
    # Tags (15 points)
    if tags and len(tags) >= 3:
        score += 15
    elif tags:
        score += 5
    
    # Content structure (15 points)
    if content:
        if '<h2>' in content or '<h3>' in content:
            score += 10
        if '<img' in content:
            score += 5
    
    return min(score, 100)

@app.post("/admin/analyze-seo")
async def analyze_seo_endpoint(
    title: str = Form(...),
    content: str = Form(...),
    meta_description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    admin: dict = Depends(get_admin_user)
):
    """Real-time SEO analysis endpoint"""
    tag_list = [t.strip() for t in tags.split(',')] if tags else []
    score = calculate_seo_score(title, content, meta_description, tag_list)
    
    # Generate suggestions
    suggestions = []
    if len(title) < 50 or len(title) > 60:
        suggestions.append("Title should be 50-60 characters")
    if not meta_description or len(meta_description) < 120:
        suggestions.append("Meta description should be 120-160 characters")
    if len(content.split()) < 300:
        suggestions.append("Content should be at least 300 words")
    if len(tag_list) < 3:
        suggestions.append("Add at least 3 tags")
    if '<h2>' not in content and '<h3>' not in content:
        suggestions.append("Add subheadings (H2/H3) for better structure")
    
    return {
        "score": score,
        "suggestions": suggestions,
        "grade": "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"
    }

# ============================================================================
# Media Upload
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
        
        file_path = os.path.join(UPLOADS_DIR, unique_name)
        
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

# ============================================================================
# Courses
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

@app.post("/admin/courses")
async def create_course(course: CourseCreate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        admin_id = admin.get("id") or admin.get("sub")
        course_id = await conn.fetchval("""
            INSERT INTO courses (title, description, content, level, duration_hours, thumbnail, is_premium, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """, course.title, course.description, course.content, course.level, 
             course.duration_hours, course.thumbnail, course.is_premium, int(admin_id))
        
        if course.modules:
            for idx, module in enumerate(course.modules):
                await conn.execute("""
                    INSERT INTO course_modules (course_id, title, content, video_url, sort_order, is_premium)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, course_id, module.get("title"), module.get("content"), 
                     module.get("video_url"), idx, module.get("is_premium", False))
        
        return {"id": course_id, "message": "Course created"}

@app.get("/admin/courses/{course_id}")
async def get_course(course_id: int, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        course = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        modules = await conn.fetch(
            "SELECT * FROM course_modules WHERE course_id = $1 ORDER BY sort_order",
            course_id
        )
        
        result = dict(course)
        result["modules"] = [dict(m) for m in modules]
        return result

@app.put("/admin/courses/{course_id}")
async def update_course(course_id: int, course: CourseUpdate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        update_fields = []
        params = []
        
        if course.title is not None:
            update_fields.append(f"title = ${len(params)+1}")
            params.append(course.title)
        if course.description is not None:
            update_fields.append(f"description = ${len(params)+1}")
            params.append(course.description)
        if course.content is not None:
            update_fields.append(f"content = ${len(params)+1}")
            params.append(course.content)
        if course.level is not None:
            update_fields.append(f"level = ${len(params)+1}")
            params.append(course.level)
        if course.duration_hours is not None:
            update_fields.append(f"duration_hours = ${len(params)+1}")
            params.append(course.duration_hours)
        if course.thumbnail is not None:
            update_fields.append(f"thumbnail = ${len(params)+1}")
            params.append(course.thumbnail)
        if course.is_premium is not None:
            update_fields.append(f"is_premium = ${len(params)+1}")
            params.append(course.is_premium)
            
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        update_fields.append("updated_at = NOW()")
        params.append(course_id)
        
        query = f"UPDATE courses SET {', '.join(update_fields)} WHERE id = ${len(params)} RETURNING id"
        result = await conn.fetchval(query, *params)
        
        if not result:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Update modules if provided
        if course.modules is not None:
            await conn.execute("DELETE FROM course_modules WHERE course_id = $1", course_id)
            for idx, module in enumerate(course.modules):
                await conn.execute("""
                    INSERT INTO course_modules (course_id, title, content, video_url, sort_order, is_premium)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, course_id, module.get("title"), module.get("content"), 
                     module.get("video_url"), idx, module.get("is_premium", False))
        
        return {"id": course_id, "message": "Course updated"}

@app.delete("/admin/courses/{course_id}")
async def delete_course(course_id: int, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM courses WHERE id = $1", course_id)
        return {"message": "Course deleted"}

# ============================================================================
# Webinars
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

@app.post("/admin/webinars")
async def create_webinar(webinar: WebinarCreate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        admin_id = admin.get("id") or admin.get("sub")
        webinar_id = await conn.fetchval("""
            INSERT INTO webinars (title, description, scheduled_at, duration_minutes, meeting_link, is_premium, created_by, max_participants)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """, webinar.title, webinar.description, webinar.scheduled_at, 
             webinar.duration_minutes, webinar.meeting_link, webinar.is_premium, int(admin_id), webinar.max_participants)
        return {"id": webinar_id, "message": "Webinar created"}

@app.get("/admin/webinars/{webinar_id}")
async def get_webinar(webinar_id: int, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        webinar = await conn.fetchrow("SELECT * FROM webinars WHERE id = $1", webinar_id)
        if not webinar:
            raise HTTPException(status_code=404, detail="Webinar not found")
        return dict(webinar)

@app.put("/admin/webinars/{webinar_id}")
async def update_webinar(webinar_id: int, webinar: WebinarUpdate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
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
            
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        update_fields.append("updated_at = NOW()")
        params.append(webinar_id)
        
        query = f"UPDATE webinars SET {', '.join(update_fields)} WHERE id = ${len(params)} RETURNING id"
        result = await conn.fetchval(query, *params)
        
        if not result:
            raise HTTPException(status_code=404, detail="Webinar not found")
            
        return {"id": webinar_id, "message": "Webinar updated"}

@app.delete("/admin/webinars/{webinar_id}")
async def delete_webinar(webinar_id: int, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM webinars WHERE id = $1", webinar_id)
        return {"message": "Webinar deleted"}

# ============================================================================
# Signals
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

@app.post("/admin/signals")
async def create_signal(signal: SignalCreate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        admin_id = admin.get("id") or admin.get("sub")
        signal_id = await conn.fetchval("""
            INSERT INTO signals (pair, direction, entry_price, stop_loss, take_profit, timeframe, analysis, is_premium, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """, signal.pair.upper(), signal.direction, signal.entry_price, signal.stop_loss,
             signal.take_profit, signal.timeframe, signal.analysis, signal.is_premium, int(admin_id))
        return {"id": signal_id, "message": "Signal created"}

@app.get("/admin/signals/{signal_id}")
async def get_signal(signal_id: int, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        signal = await conn.fetchrow("SELECT * FROM signals WHERE id = $1", signal_id)
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        return dict(signal)

@app.put("/admin/signals/{signal_id}")
async def update_signal(signal_id: int, signal: SignalUpdate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
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
        if signal.take_profit is not None:
            update_fields.append(f"take_profit = ${len(params)+1}")
            params.append(signal.take_profit)
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
            
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        update_fields.append("updated_at = NOW()")
        params.append(signal_id)
        
        query = f"UPDATE signals SET {', '.join(update_fields)} WHERE id = ${len(params)} RETURNING id"
        result = await conn.fetchval(query, *params)
        
        if not result:
            raise HTTPException(status_code=404, detail="Signal not found")
            
        return {"id": signal_id, "message": "Signal updated"}

@app.delete("/admin/signals/{signal_id}")
async def delete_signal(signal_id: int, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM signals WHERE id = $1", signal_id)
        return {"message": "Signal deleted"}

# ============================================================================
# AI Chat with User Context
# ============================================================================

@app.post("/chat")
async def chat_with_ai(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    try:
        # Get full user context
        user_id = int(current_user.get("id") or current_user.get("sub"))
        user_context = await get_user_full_context(user_id)
        
        system_prompt = f"""You are an expert trading mentor with 20+ years of experience. You are speaking to {user_context.get('name', 'Trader')}, who is a {user_context.get('subscription', 'free')} member since {user_context.get('member_since', 'N/A')}. 
        
Their trading history shows {user_context.get('total_analyses', 0)} performance analyses completed. Their last trader score was {user_context.get('last_trader_score', 'not recorded') if user_context.get('last_trader_score') else 'not recorded yet'}.

Be personal, encouraging, and specific to their level. If they're a free user, occasionally mention premium features that could help them. Address them by name when appropriate."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.message}
        ]
        
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
            
            # Save to history with context
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO chat_history (user_id, message, response, context, user_context)
                    VALUES ($1, $2, $3, $4, $5)
                """, user_id, request.message, ai_message, request.context, json.dumps(user_context))
            
            return {
                "response": ai_message,
                "timestamp": datetime.utcnow().isoformat(),
                "user_context_used": True
            }
            
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/history")
async def get_chat_history(
    limit: int = Query(20),
    current_user: dict = Depends(get_current_user)
):
    async with db_pool.acquire() as conn:
        user_id = current_user.get("id") or current_user.get("sub")
        rows = await conn.fetch("""
            SELECT message, response, created_at 
            FROM chat_history 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
        """, int(user_id), limit)
        return {"history": [dict(row) for row in rows]}

# ============================================================================
# AI Performance Analyzer with File Upload
# ============================================================================

@app.post("/analyze/performance")
async def analyze_performance(
    file: UploadFile = File(...),
    account_balance: Optional[float] = Form(None),
    trading_period_days: Optional[int] = Form(30),
    current_user: dict = Depends(get_current_user)
):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    try:
        contents = await file.read()
        file_ext = file.filename.split(".")[-1].lower()
        
        trades = []
        
        # Parse CSV
        if file_ext == "csv":
            csv_text = contents.decode('utf-8')
            reader = csv.DictReader(io.StringIO(csv_text))
            for row in reader:
                trade = {
                    "date": row.get("Date", row.get("date", "")),
                    "pair": row.get("Pair", row.get("pair", row.get("Symbol", "UNKNOWN"))),
                    "direction": row.get("Direction", row.get("direction", "buy")).lower(),
                    "entry": float(row.get("Entry", row.get("entry", 0)) or 0),
                    "exit": float(row.get("Exit", row.get("exit", 0)) or 0),
                    "lots": float(row.get("Lots", row.get("lots", row.get("Size", 0.1))) or 0.1),
                    "pips": float(row.get("Pips", row.get("pips", row.get("Profit", 0))) or 0),
                    "notes": row.get("Notes", row.get("notes", ""))
                }
                trades.append(trade)
        
        # Parse PDF (basic text extraction)
        elif file_ext == "pdf" and PDF_SUPPORT:
            pdf_file = io.BytesIO(contents)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            # Try to extract trades from PDF text using regex or send to AI
            trades.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "pair": "PDF_REPORT",
                "direction": "buy",
                "entry": 0,
                "exit": 0,
                "lots": 0,
                "pips": 0,
                "notes": f"PDF Report extracted: {text[:500]}..."
            })
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_ext}. Please upload CSV or PDF.")
        
        if not trades:
            raise HTTPException(status_code=400, detail="No trades found in file")
        
        # Analysis logic
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.get("pips", 0) > 0])
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        system_prompt = """You are a professional trading performance analyst with over 20 years of experience in institutional trading, risk management, and trader psychology."""

        user_prompt = f"""Analyze the following trading performance data imported from file:

Account Balance: {account_balance or 'Not provided'}
Trading Period: {trading_period_days or 'Not provided'} days
Total Trades: {total_trades}
Win Rate: {win_rate:.1f}%
File Type: {file_ext.upper()}

Trade History:
{json.dumps(trades[:50], indent=2)}  # Limit to first 50 trades

Provide analysis in strict JSON format with fields: performance_summary (with total_trades, win_rate, net_pips, avg_win, avg_loss, risk_reward_ratio, expectancy, profit_factor, max_drawdown), trader_score (1-100), strengths (array), weaknesses (array), behavior_patterns (array), top_mistakes (array), improvement_plan (object with immediate_actions, strategy_improvements, risk_management_fixes arrays), recommended_courses (array), mentor_advice (string)."""

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://pipways.com",
                    "X-Title": "Pipways Performance Analyzer"
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 2500,
                    "temperature": 0.4
                }
            )

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="AI analysis failed")

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
                
                user_id = current_user.get("id") or current_user.get("sub")
                async with db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO performance_analyses (user_id, analysis_data, raw_trades, trader_score, file_type)
                        VALUES ($1, $2, $3, $4, $5)
                    """, int(user_id), json.dumps(analysis_data), json.dumps(trades),
                         analysis_data.get("trader_score", 0), file_ext)
                
                return {
                    "analysis": analysis_data,
                    "timestamp": datetime.utcnow().isoformat(),
                    "trades_analyzed": total_trades,
                    "file_type": file_ext
                }
                
            except json.JSONDecodeError:
                return {"raw_analysis": ai_content, "error": "Parse error", "file_type": file_ext}

    except Exception as e:
        logger.error(f"Performance analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# AI Chart Analysis
# ============================================================================

@app.post("/analyze/chart")
async def analyze_chart(
    file: UploadFile = File(...),
    pair: Optional[str] = Form("EURUSD"),
    timeframe: Optional[str] = Form("1H"),
    additional_info: Optional[str] = Form(""),
    current_user: dict = Depends(get_current_user)
):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

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

            return {
                "analysis": formatted_report,
                "pair": pair,
                "timeframe": timeframe
            }
                
    except Exception as e:
        logger.error(f"Chart analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Recent Posts for Overview
# ============================================================================

@app.get("/blog/posts/recent")
async def get_recent_posts(
    limit: int = Query(5, ge=1, le=10),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get recent posts for overview/dashboard"""
    async with db_pool.acquire() as conn:
        query = """
            SELECT bp.id, bp.title, bp.excerpt, bp.featured_image, bp.category, bp.created_at, bp.slug,
                   u.full_name as author_name
            FROM blog_posts bp
            LEFT JOIN users u ON bp.author_id = u.id
            WHERE (status = 'published' OR status IS NULL)
            AND (scheduled_at IS NULL OR scheduled_at <= NOW())
        """
        
        tier = current_user.get("subscription_tier", "free") if current_user else "free"
        if tier == "free":
            query += " AND is_premium = FALSE"
            
        query += " ORDER BY bp.created_at DESC LIMIT $1"
        
        rows = await conn.fetch(query, limit)
        return {"posts": [dict(row) for row in rows]}

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
        "version": "3.4.0",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def serve_frontend():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "Pipways API v3.4.0 - Place index.html in root directory"}

@app.get("/{path:path}")
async def spa_catch_all(path: str):
    api_paths = ("auth", "admin", "blog", "courses", "webinars", "signals", "chat", "analyze", "uploads", "health", "users")
    if path.startswith(api_paths):
        raise HTTPException(status_code=404, detail="Not found")
    
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "Pipways API v3.4.0"}

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
