"""
Pipways Trading Platform API - Production v3.0
Features: Performance Analyzer, Rich Content, Media Upload, SEO, Enhanced Admin
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
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, field_validator
from dotenv import load_dotenv
import httpx
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
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
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

    # Use reliable vision-capable models
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    OPENROUTER_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "anthropic/claude-3.5-sonnet")

    # CORS origins from environment variable
    CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "*")
    @property
    def CORS_ORIGINS(self):
        if self.CORS_ORIGINS_STR == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",") if origin.strip()]

settings = Settings()

# Database pool
db_pool: Optional[asyncpg.Pool] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(settings.DATABASE_URL, min_size=2, max_size=10)
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise
    yield
    if db_pool:
        await db_pool.close()

app = FastAPI(title="Pipways API", version="3.0.0", lifespan=lifespan)

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

# Security
security = HTTPBearer(auto_error=False)

# Enhanced Models
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

class SignalCreate(BaseModel):
    pair: str = Field(..., min_length=1)
    direction: str = Field(..., pattern="^(buy|sell)$")
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timeframe: str = "1H"
    analysis: Optional[str] = None
    is_premium: bool = False

class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    is_premium: bool = False
    level: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")
    duration_hours: Optional[float] = None
    thumbnail: Optional[str] = None

class PerformanceAnalysisRequest(BaseModel):
    trades: List[Dict[str, Any]]
    account_balance: Optional[float] = None
    trading_period_days: Optional[int] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context: Optional[str] = ""

# Database initialization
async def init_db():
    async with db_pool.acquire() as conn:
        # Users table with enhanced fields
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

        # Enhanced blog posts with SEO and scheduling
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

        # Signals table
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

        # Enhanced webinars
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Enhanced courses
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

        # Chat history
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

        # Media files
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

        # Performance analyses
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_analyses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                analysis_data JSONB NOT NULL,
                raw_trades JSONB,
                trader_score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
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
            else:
                await conn.execute("""
                    UPDATE users SET role = 'admin' WHERE email = $1 AND role != 'admin'
                """, settings.ADMIN_EMAIL)
        except Exception as e:
            logger.error(f"Error creating admin: {e}")

# Auth utilities
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

def create_reset_token():
    import secrets
    return secrets.token_urlsafe(32)

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        if "role" in payload:
            return payload
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", int(user_id))
            return dict(user) if user else None
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        if "role" in payload and "email" in payload:
            return payload

        async with db_pool.acquire() as conn:
            user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", int(user_id))
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            return dict(user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    role = current_user.get("role", "user")
    if role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Auth endpoints
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
            return {"access_token": new_access, "token_type": "bearer"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

# Admin endpoints
@app.get("/admin/stats")
async def get_admin_stats(admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users") or 0
        total_signals = await conn.fetchval("SELECT COUNT(*) FROM signals") or 0
        active_signals = await conn.fetchval("SELECT COUNT(*) FROM signals WHERE status = 'active'") or 0
        premium_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE subscription_tier IN ('premium', 'vip')") or 0
        total_posts = await conn.fetchval("SELECT COUNT(*) FROM blog_posts") or 0
        draft_posts = await conn.fetchval("SELECT COUNT(*) FROM blog_posts WHERE status = 'draft'") or 0
        scheduled_posts = await conn.fetchval("SELECT COUNT(*) FROM blog_posts WHERE status = 'scheduled'") or 0
        
        return {
            "total_users": total_users,
            "total_signals": total_signals,
            "active_signals": active_signals,
            "premium_users": premium_users,
            "conversion_rate": round((premium_users / total_users * 100), 2) if total_users > 0 else 0,
            "content_stats": {
                "blog_posts": total_posts,
                "drafts": draft_posts,
                "scheduled": scheduled_posts
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

@app.put("/admin/users/{user_id}/role")
async def update_user_role(user_id: int, role: str = Query(...), admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE users SET role = $1 WHERE id = $2", role, user_id)
        return {"message": "Role updated"}

@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        return {"message": "User deleted"}

# Blog Management
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
        
        # Filter by status (admin sees all, users see only published)
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

@app.post("/admin/blog")
async def create_blog_post(post: BlogPostCreate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        admin_id = admin.get("id") or admin.get("sub")
        
        # Generate slug if not provided
        slug = post.slug or post.title.lower().replace(" ", "-")[:50]
        
        # Check slug uniqueness
        existing = await conn.fetchval("SELECT id FROM blog_posts WHERE slug = $1", slug)
        if existing:
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"
        
        published_at = None
        if post.status == "published" and not post.scheduled_at:
            published_at = datetime.utcnow()
        
        post_id = await conn.fetchval("""
            INSERT INTO blog_posts (
                title, content, excerpt, author_id, is_premium, status, 
                scheduled_at, meta_title, meta_description, slug, featured_image, tags, category,
                published_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            RETURNING id
        """, post.title, post.content, post.excerpt, int(admin_id), post.is_premium, 
             post.status, post.scheduled_at, post.meta_title, post.meta_description,
             slug, post.featured_image, post.tags, post.category, published_at)
             
        return {"id": post_id, "slug": slug, "message": "Blog post created"}

@app.put("/admin/blog/{post_id}")
async def update_blog_post(post_id: int, post: BlogPostUpdate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        # Build dynamic update query
        updates = []
        params = []
        
        if post.title is not None:
            updates.append(f"title = ${len(params)+1}")
            params.append(post.title)
        if post.content is not None:
            updates.append(f"content = ${len(params)+1}")
            params.append(post.content)
        if post.status is not None:
            updates.append(f"status = ${len(params)+1}")
            params.append(post.status)
            if post.status == "published":
                updates.append(f"published_at = NOW()")
                
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        params.append(post_id)
        query = f"UPDATE blog_posts SET {', '.join(updates)}, updated_at = NOW() WHERE id = ${len(params)}"
        await conn.execute(query, *params)
        return {"message": "Post updated"}

# Webinars
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

# Courses
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
            
        query += " ORDER BY created_at DESC LIMIT ${len(params)+1}"
        params.append(limit)
        
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]

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
        return {"id": course_id, "message": "Course created"}

# Signals
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

# AI Performance Analyzer
@app.post("/analyze/performance")
async def analyze_performance(
    request: PerformanceAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    try:
        # Calculate basic metrics for context
        total_trades = len(request.trades)
        winning_trades = len([t for t in request.trades if t.get("pips", 0) > 0 or t.get("profit", 0) > 0])
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Prepare comprehensive prompt
        system_prompt = """You are a professional trading performance analyst and trading mentor with over 20 years of experience in institutional trading, risk management, and trader psychology.

Your task is to analyze a trader's performance data and provide a detailed professional evaluation of their trading behavior, strengths, weaknesses, and improvement strategies.

Analyze the provided trade data carefully and return a structured JSON response."""

        user_prompt = f"""Analyze the following trading performance data:

Account Balance: {request.account_balance or 'Not provided'}
Trading Period: {request.trading_period_days or 'Not provided'} days
Total Trades Provided: {total_trades}
Calculated Win Rate: {win_rate:.1f}%

Trade History:
{json.dumps(request.trades, indent=2)}

Provide analysis in this exact JSON structure:
{{
  "performance_summary": {{
    "total_trades": number,
    "winning_trades": number,
    "losing_trades": number,
    "win_rate": "string with %",
    "net_pips": "string with +/-",
    "avg_win": number,
    "avg_loss": number,
    "risk_reward_ratio": "string like 1:2",
    "expectancy": "string description",
    "profit_factor": number,
    "max_drawdown": "string"
  }},
  "trader_score": number (1-100),
  "strengths": ["list", "of", "strengths"],
  "weaknesses": ["list", "of", "weaknesses"],
  "behavior_patterns": [
    "Pattern 1: description",
    "Pattern 2: description"
  ],
  "strategy_quality": {{
    "has_clear_strategy": boolean,
    "entry_quality": "High/Medium/Low",
    "exit_quality": "High/Medium/Low",
    "risk_management_adherence": "Good/Fair/Poor",
    "consistency": "High/Medium/Low"
  }},
  "risk_analysis": {{
    "avg_risk_per_trade": "string",
    "stop_loss_respect": "Good/Fair/Poor",
    "position_sizing": "Consistent/Inconsistent/Dangerous",
    "dangerous_habits": ["list", "or", "empty"]
  }},
  "psychological_analysis": {{
    "fear_of_losing": "High/Medium/Low",
    "fomo_level": "High/Medium/Low",
    "discipline_level": "High/Medium/Low",
    "emotional_trading_signs": ["list"]
  }},
  "top_mistakes": [
    "Mistake 1",
    "Mistake 2"
  ],
  "improvement_plan": {{
    "immediate_actions": ["list"],
    "strategy_improvements": ["list"],
    "risk_management_fixes": ["list"],
    "psychological_work": ["list"]
  }},
  "recommended_courses": [
    "Specific Course Name 1",
    "Specific Course Name 2"
  ],
  "mentor_advice": "Detailed paragraph of personalized advice"
}}

Rules:
1. Be honest but constructive
2. Base analysis ONLY on provided data
3. If data is insufficient for a field, use "N/A" or empty array
4. Trader score should reflect real performance, not encouragement
5. Specific course recommendations must match actual weaknesses found
6. Include specific examples from trades when possible"""

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
                logger.error(f"OpenRouter error: {response.text}")
                raise HTTPException(status_code=500, detail="AI analysis failed")

            result = response.json()
            ai_content = result["choices"][0]["message"]["content"]
            
            # Parse JSON
            try:
                cleaned = ai_content.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                    cleaned = cleaned.strip()
                
                analysis_data = json.loads(cleaned)
                
                # Save to database
                user_id = current_user.get("id") or current_user.get("sub")
                async with db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO performance_analyses (user_id, analysis_data, raw_trades, trader_score)
                        VALUES ($1, $2, $3, $4)
                    """, int(user_id), json.dumps(analysis_data), json.dumps(request.trades),
                         analysis_data.get("trader_score", 0))
                
                return {
                    "analysis": analysis_data,
                    "timestamp": datetime.utcnow().isoformat(),
                    "trades_analyzed": total_trades
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                return {
                    "raw_analysis": ai_content,
                    "error": "Failed to parse structured data",
                    "timestamp": datetime.utcnow().isoformat()
                }

    except Exception as e:
        logger.error(f"Performance analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze/performance/history")
async def get_performance_history(
    limit: int = Query(10),
    current_user: dict = Depends(get_current_user)
):
    async with db_pool.acquire() as conn:
        user_id = current_user.get("id") or current_user.get("sub")
        rows = await conn.fetch("""
            SELECT id, analysis_data, trader_score, created_at 
            FROM performance_analyses 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
        """, int(user_id), limit)
        return [dict(row) for row in rows]

# Chart Analysis (existing enhanced)
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
            raise HTTPException(status_code=413, detail="File too large")

        image_base64 = base64.b64encode(contents).decode()

        prompt = f"""You are an expert forex/crypto technical analyst. Analyze this {pair} chart on {timeframe} timeframe.

Context: {additional_info}

Provide analysis in this exact JSON structure:
{{
  "summary": "Brief technical overview",
  "signal": "BUY or SELL or NO TRADE",
  "entry_zone": "Specific price range",
  "stop_loss": "Exact price level",
  "take_profit": ["TP1", "TP2"],
  "risk_reward": "1:3",
  "confidence": "75%",
  "market_structure": "Bullish/Bearish explanation",
  "support_resistance": {{
    "support": ["S1", "S2"],
    "resistance": ["R1", "R2"]
  }},
  "key_observations": "Specific patterns"
}}"""

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
            
            try:
                cleaned = ai_response.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                    cleaned = cleaned.strip()
                
                analysis_data = json.loads(cleaned)
                
                formatted_report = f"""📊 TECHNICAL ANALYSIS: {pair} ({timeframe})

🎯 TRADING SIGNAL: {analysis_data.get('signal', 'UNKNOWN')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 ENTRY ZONE: {analysis_data.get('entry_zone', 'N/A')}
🛑 STOP LOSS: {analysis_data.get('stop_loss', 'N/A')}
🎯 TAKE PROFIT 1: {analysis_data.get('take_profit', ['N/A'])[0]}
🎯 TAKE PROFIT 2: {analysis_data.get('take_profit', ['N/A', 'N/A'])[1] if len(analysis_data.get('take_profit', [])) > 1 else 'N/A'}
⚖️ RISK/REWARD: {analysis_data.get('risk_reward', 'N/A')}
🎲 CONFIDENCE: {analysis_data.get('confidence', 'N/A')}

📝 SUMMARY:
{analysis_data.get('summary', 'No summary provided')}

🏗️ MARKET STRUCTURE:
{analysis_data.get('market_structure', 'N/A')}

📊 SUPPORT LEVELS: {', '.join(analysis_data.get('support_resistance', {}).get('support', []))}
📈 RESISTANCE LEVELS: {', '.join(analysis_data.get('support_resistance', {}).get('resistance', []))}

🔍 KEY OBSERVATIONS:
{analysis_data.get('key_observations', 'None')}"""

                return {
                    "analysis": formatted_report,
                    "structured_data": analysis_data,
                    "image_base64": image_base64,
                    "pair": pair,
                    "timeframe": timeframe
                }
                
            except json.JSONDecodeError:
                return {
                    "analysis": ai_response,
                    "image_base64": image_base64,
                    "pair": pair,
                    "timeframe": timeframe,
                    "parse_warning": "AI returned unstructured data"
                }
                
    except Exception as e:
        logger.error(f"Chart analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Media Upload Endpoint
@app.post("/admin/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    admin: dict = Depends(get_admin_user)
):
    try:
        # In production, integrate with Cloudinary or AWS S3
        # For now, save locally and return path
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_ext = file.filename.split(".")[-1]
        unique_name = f"{uuid.uuid4().hex}.{file_ext}"
        file_path = os.path.join(upload_dir, unique_name)
        
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Save to database
        admin_id = admin.get("id") or admin.get("sub")
        async with db_pool.acquire() as conn:
            media_id = await conn.fetchval("""
                INSERT INTO media_files (filename, url, file_type, size_bytes, uploaded_by)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, file.filename, f"/uploads/{unique_name}", file_ext, len(contents), int(admin_id))
            
        return {
            "id": media_id,
            "url": f"/uploads/{unique_name}",
            "filename": file.filename,
            "size": len(contents)
        }
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "3.0.0", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
