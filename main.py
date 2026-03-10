"""
Pipways Trading Platform API - Production v3.2.0
Single-file complete backend with all features
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
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Query, Request, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from dotenv import load_dotenv
import httpx
from contextlib import asynccontextmanager

# Optional imports with fallbacks
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

# ==========================================
# CONFIGURATION
# ==========================================
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

    # AI Models
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    OPENROUTER_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "anthropic/claude-3.5-sonnet")

    # CORS origins
    @property
    def CORS_ORIGINS(self):
        origins = [
            "https://pipways-web-nhem.onrender.com",
            "https://pipways.com",
            "https://www.pipways.com",
            "http://localhost:3000",
            "http://localhost:8080",
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            "http://localhost:8000",
            "null",
            "*"
        ]
        
        env_origins = os.getenv("CORS_ORIGINS", "")
        if env_origins:
            origins.extend([o.strip() for o in env_origins.split(",") if o.strip()])
        
        # Always include frontend URL from env if available
        frontend_url = os.getenv("FRONTEND_URL")
        if frontend_url and frontend_url not in origins:
            origins.append(frontend_url)
            
        return list(set(origins))

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

# ==========================================
# DATABASE SETUP
# ==========================================
async def init_db():
    """Initialize database tables"""
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
        
        # Create index on email
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        """)

        # Blog posts
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                slug VARCHAR(255) UNIQUE,
                content TEXT NOT NULL,
                excerpt TEXT,
                author_id INTEGER REFERENCES users(id),
                is_premium BOOLEAN DEFAULT FALSE,
                status VARCHAR(20) DEFAULT 'draft',
                scheduled_at TIMESTAMP,
                published_at TIMESTAMP,
                meta_title VARCHAR(255),
                meta_description TEXT,
                featured_image VARCHAR(500),
                tags TEXT[],
                category VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_blog_posts_status ON blog_posts(status);
            CREATE INDEX IF NOT EXISTS idx_blog_posts_slug ON blog_posts(slug);
        """)

        # Signals
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
                closed_at TIMESTAMP
            )
        """)

        # Webinars
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

        # Webinar registrations
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS webinar_registrations (
                id SERIAL PRIMARY KEY,
                webinar_id INTEGER REFERENCES webinars(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(webinar_id, user_id)
            )
        """)

        # Courses
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

        # Course modules
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS course_modules (
                id SERIAL PRIMARY KEY,
                course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                content TEXT,
                video_url VARCHAR(500),
                sort_order INTEGER DEFAULT 0,
                is_premium BOOLEAN DEFAULT FALSE,
                duration_minutes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # User progress
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                module_id INTEGER REFERENCES course_modules(id) ON DELETE CASCADE,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, module_id)
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
        
        # Chart analyses
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chart_analyses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                pair VARCHAR(20),
                timeframe VARCHAR(10),
                image_url VARCHAR(500),
                analysis_text TEXT,
                structured_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create default admin
        await create_default_admin(conn)

async def create_default_admin(conn):
    """Create default admin user if not exists"""
    try:
        admin_exists = await conn.fetchval(
            "SELECT id FROM users WHERE email = $1", 
            settings.ADMIN_EMAIL
        )
        if not admin_exists:
            hashed = bcrypt.hashpw(
                settings.ADMIN_PASSWORD.encode(), 
                bcrypt.gensalt()
            ).decode()
            await conn.execute("""
                INSERT INTO users 
                (email, password_hash, full_name, role, subscription_tier, subscription_status, email_verified)
                VALUES ($1, $2, $3, 'admin', 'vip', 'active', TRUE)
            """, settings.ADMIN_EMAIL, hashed, "System Administrator")
            logger.info(f"Default admin created: {settings.ADMIN_EMAIL}")
        else:
            # Ensure admin has admin role
            await conn.execute("""
                UPDATE users SET role = 'admin' 
                WHERE email = $1 AND role != 'admin'
            """, settings.ADMIN_EMAIL)
    except Exception as e:
        logger.error(f"Error creating admin: {e}")

# ==========================================
# LIFESPAN & APP INIT
# ==========================================
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
        logger.info("Database initialized successfully")
        
        # Create uploads directory
        os.makedirs("uploads", exist_ok=True)
        os.makedirs("uploads/images", exist_ok=True)
        os.makedirs("uploads/videos", exist_ok=True)
        os.makedirs("uploads/documents", exist_ok=True)
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise
    yield
    if db_pool:
        await db_pool.close()

app = FastAPI(
    title="Pipways API", 
    version="3.2.0", 
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

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

# Mount uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Security
security = HTTPBearer(auto_error=False)

# ==========================================
# PYDANTIC MODELS
# ==========================================
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
    status: str = Field(default="draft", pattern="^(draft|published|scheduled)$")
    scheduled_at: Optional[datetime] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    slug: Optional[str] = None
    featured_image: Optional[str] = None
    tags: Optional[List[str]] = []
    category: Optional[str] = "General"

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
    modules: Optional[List[Dict]] = []

class PerformanceAnalysisRequest(BaseModel):
    trades: List[Dict[str, Any]]
    account_balance: Optional[float] = None
    trading_period_days: Optional[int] = 30

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context: Optional[str] = ""

# ==========================================
# AUTH UTILITIES
# ==========================================
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
            if datetime.utcnow().timestamp() > payload.get("exp", 0):
                raise HTTPException(status_code=401, detail="Token expired")
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

# ==========================================
# AUTH ROUTES
# ==========================================
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
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

# ==========================================
# ADMIN ROUTES
# ==========================================
@app.get("/admin/stats")
async def get_admin_stats(admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users") or 0
        active_signals = await conn.fetchval("SELECT COUNT(*) FROM signals WHERE status = 'active'") or 0
        premium_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE subscription_tier IN ('premium', 'vip')") or 0
        total_posts = await conn.fetchval("SELECT COUNT(*) FROM blog_posts") or 0
        total_courses = await conn.fetchval("SELECT COUNT(*) FROM courses") or 0
        total_webinars = await conn.fetchval("SELECT COUNT(*) FROM webinars") or 0
        
        return {
            "total_users": total_users,
            "active_signals": active_signals,
            "premium_users": premium_users,
            "blog_posts": total_posts,
            "courses": total_courses,
            "webinars": total_webinars,
            "conversion_rate": round((premium_users / total_users * 100), 2) if total_users > 0 else 0
        }

@app.get("/admin/users")
async def get_all_users(
    search: Optional[str] = Query(None),
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

# ==========================================
# BLOG ROUTES
# ==========================================
@app.get("/blog/posts")
async def get_blog_posts(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(10, le=50),
    page: int = Query(1, ge=1),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    async with db_pool.acquire() as conn:
        where_clauses = ["1=1"]
        params = []
        
        # Public only sees published
        if not current_user or current_user.get("role") not in ["admin", "moderator"]:
            where_clauses.append("(status = 'published')")
            where_clauses.append("(scheduled_at IS NULL OR scheduled_at <= NOW())")
        elif status:
            where_clauses.append(f"status = ${len(params)+1}")
            params.append(status)
            
        if category:
            where_clauses.append(f"category = ${len(params)+1}")
            params.append(category)

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

@app.get("/blog/posts/{slug}")
async def get_blog_post(slug: str, current_user: Optional[dict] = Depends(get_current_user_optional)):
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
        
        # Check premium access
        if post.get("is_premium"):
            tier = current_user.get("subscription_tier", "free") if current_user else "free"
            if tier == "free" and (not current_user or current_user.get("role") != "admin"):
                raise HTTPException(status_code=403, detail="Premium content requires subscription")
                
        return post

@app.post("/admin/blog")
async def create_blog_post(post: BlogPostCreate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        admin_id = admin.get("id") or admin.get("sub")
        
        # Generate slug
        base_slug = post.slug or re.sub(r'[^\w\s-]', '', post.title.lower().replace(" ", "-"))[:50]
        slug = base_slug
        counter = 1
        while await conn.fetchval("SELECT id FROM blog_posts WHERE slug = $1", slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        published_at = None
        if post.status == "published" and not post.scheduled_at:
            published_at = datetime.utcnow()
        
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

@app.delete("/admin/blog/{post_id}")
async def delete_blog_post(post_id: int, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM blog_posts WHERE id = $1", post_id)
        return {"message": "Post deleted"}

# ==========================================
# MEDIA ROUTES
# ==========================================
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
        
        # Try Cloudinary first
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
                    "size": result["bytes"],
                    "source": "cloudinary"
                }
            except Exception as cloud_err:
                logger.warning(f"Cloudinary upload failed, falling back to local: {cloud_err}")
        
        # Local storage fallback
        file_type = "image" if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp'] else \
                   "video" if file_ext in ['mp4', 'webm', 'mov'] else "document"
        
        subdir = "images" if file_type == "image" else "videos" if file_type == "video" else "documents"
        file_path = f"uploads/{subdir}/{unique_name}"
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        admin_id = admin.get("id") or admin.get("sub")
        async with db_pool.acquire() as conn:
            media_id = await conn.fetchval("""
                INSERT INTO media_files (filename, url, file_type, size_bytes, uploaded_by)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, file.filename, f"/uploads/{subdir}/{unique_name}", file_type, len(contents), int(admin_id))
            
        return {
            "id": media_id,
            "url": f"/uploads/{subdir}/{unique_name}",
            "filename": file.filename,
            "size": len(contents),
            "source": "local"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/admin/media")
async def list_media(
    file_type: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    admin: dict = Depends(get_admin_user)
):
    async with db_pool.acquire() as conn:
        query = "SELECT m.*, u.full_name as uploader_name FROM media_files m LEFT JOIN users u ON m.uploaded_by = u.id"
        params = []
        
        if file_type:
            query += " WHERE m.file_type = $1"
            params.append(file_type)
            
        query += " ORDER BY m.created_at DESC LIMIT $%d" % (len(params) + 1)
        params.append(limit)
        
        rows = await conn.fetch(query, *params)
        return {"files": [dict(row) for row in rows]}

# ==========================================
# COURSE ROUTES
# ==========================================
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
async def get_course(course_id: int, current_user: Optional[dict] = Depends(get_current_user_optional)):
    async with db_pool.acquire() as conn:
        course = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
            
        course = dict(course)
        
        # Check access
        if course.get("is_premium"):
            tier = current_user.get("subscription_tier", "free") if current_user else "free"
            if tier == "free" and (not current_user or current_user.get("role") != "admin"):
                raise HTTPException(status_code=403, detail="Premium course requires subscription")
        
        modules = await conn.fetch(
            "SELECT * FROM course_modules WHERE course_id = $1 ORDER BY sort_order",
            course_id
        )
        course["modules"] = [dict(m) for m in modules]
        
        # Get user progress if logged in
        if current_user:
            user_id = current_user.get("id") or current_user.get("sub")
            progress = await conn.fetch(
                "SELECT module_id FROM user_progress WHERE user_id = $1 AND course_id = $2",
                int(user_id), course_id
            )
            completed_modules = {p["module_id"] for p in progress}
            for module in course["modules"]:
                module["completed"] = module["id"] in completed_modules
        
        return course

@app.post("/courses/{course_id}/modules/{module_id}/complete")
async def complete_module(
    course_id: int, 
    module_id: int,
    current_user: dict = Depends(get_current_user)
):
    async with db_pool.acquire() as conn:
        user_id = current_user.get("id") or current_user.get("sub")
        
        # Check if already completed
        existing = await conn.fetchval("""
            SELECT id FROM user_progress 
            WHERE user_id = $1 AND module_id = $2
        """, int(user_id), module_id)
        
        if not existing:
            await conn.execute("""
                INSERT INTO user_progress (user_id, course_id, module_id)
                VALUES ($1, $2, $3)
            """, int(user_id), course_id, module_id)
            
        return {"message": "Module marked as complete"}

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
        
        # Insert modules
        if course.modules:
            for idx, module in enumerate(course.modules):
                await conn.execute("""
                    INSERT INTO course_modules (course_id, title, content, video_url, sort_order, is_premium, duration_minutes)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, course_id, module.get("title"), module.get("content"), 
                     module.get("video_url"), idx, module.get("is_premium", False),
                     module.get("duration_minutes"))
        
        return {"id": course_id, "message": "Course created"}

# ==========================================
# WEBINAR ROUTES
# ==========================================
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
        
        # Add registration count
        webinars = []
        for row in rows:
            webinar = dict(row)
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM webinar_registrations WHERE webinar_id = $1",
                webinar["id"]
            )
            webinar["registrations"] = count
            
            # Check if current user is registered
            if current_user:
                user_id = current_user.get("id") or current_user.get("sub")
                registered = await conn.fetchval("""
                    SELECT id FROM webinar_registrations 
                    WHERE webinar_id = $1 AND user_id = $2
                """, webinar["id"], int(user_id))
                webinar["is_registered"] = registered is not None
            else:
                webinar["is_registered"] = False
                
            webinars.append(webinar)
            
        return webinars

@app.post("/webinars/{webinar_id}/register")
async def register_webinar(
    webinar_id: int,
    current_user: dict = Depends(get_current_user)
):
    async with db_pool.acquire() as conn:
        # Check if webinar exists and has space
        webinar = await conn.fetchrow("SELECT * FROM webinars WHERE id = $1", webinar_id)
        if not webinar:
            raise HTTPException(status_code=404, detail="Webinar not found")
            
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM webinar_registrations WHERE webinar_id = $1",
            webinar_id
        )
        
        if count >= webinar["max_participants"]:
            raise HTTPException(status_code=400, detail="Webinar is full")
        
        user_id = current_user.get("id") or current_user.get("sub")
        
        try:
            await conn.execute("""
                INSERT INTO webinar_registrations (webinar_id, user_id)
                VALUES ($1, $2)
            """, webinar_id, int(user_id))
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Already registered")
            
        return {"message": "Registered successfully"}

@app.post("/admin/webinars")
async def create_webinar(webinar: WebinarCreate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        admin_id = admin.get("id") or admin.get("sub")
        webinar_id = await conn.fetchval("""
            INSERT INTO webinars (title, description, scheduled_at, duration_minutes, meeting_link, is_premium, created_by, max_participants)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """, webinar.title, webinar.description, webinar.scheduled_at, 
             webinar.duration_minutes, webinar.meeting_link, webinar.is_premium, 
             int(admin_id), webinar.max_participants)
        return {"id": webinar_id, "message": "Webinar created"}

# ==========================================
# SIGNAL ROUTES
# ==========================================
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

# ==========================================
# AI ANALYSIS ROUTES
# ==========================================
@app.post("/analyze/performance")
async def analyze_performance(
    request: PerformanceAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    try:
        total_trades = len(request.trades)
        winning_trades = len([t for t in request.trades if t.get("pips", 0) > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        system_prompt = """You are a professional trading performance analyst with 20+ years of institutional trading experience."""
        
        user_prompt = f"""Analyze this trading data:
Account Balance: {request.account_balance or 'N/A'}
Period: {request.trading_period_days or 'N/A'} days
Total Trades: {total_trades}
Win Rate: {win_rate:.1f}%

Trades: {json.dumps(request.trades, indent=2)}

Return JSON with:
- performance_summary (total_trades, win_rate, net_pips, avg_win, avg_loss, risk_reward_ratio)
- trader_score (0-100)
- strengths (array)
- weaknesses (array)
- top_mistakes (array)
- improvement_plan (immediate_actions, strategy_improvements, risk_management_fixes)
- recommended_courses (array)
- mentor_advice (string)"""

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
            
            # Parse JSON from markdown if needed
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
                
    except Exception as e:
        logger.error(f"Performance analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

        prompt = f"""Analyze this {pair} chart on {timeframe} timeframe. 
Additional context: {additional_info}

Provide JSON with:
- summary (brief analysis)
- signal (BUY/SELL/NEUTRAL/WAIT)
- entry_zone (price range)
- stop_loss (price)
- take_profit (array of targets)
- risk_reward (ratio like 1:2)
- confidence (High/Medium/Low)
- market_structure (trend description)
- support_resistance (key levels)
- key_observations (list)"""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://pipways.com",
                    "X-Title": "Pipways Chart Analysis"
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
            
            # Parse JSON
            cleaned = ai_response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.strip()
            
            try:
                analysis_data = json.loads(cleaned)
            except:
                analysis_data = {"raw_response": ai_response}
            
            # Format nice report
            formatted_report = f"""📊 TECHNICAL ANALYSIS: {pair} ({timeframe})

🎯 SIGNAL: {analysis_data.get('signal', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 ENTRY ZONE: {analysis_data.get('entry_zone', 'N/A')}
🛑 STOP LOSS: {analysis_data.get('stop_loss', 'N/A')}
🎯 TAKE PROFITS: {', '.join(analysis_data.get('take_profit', []))}
⚖️ RISK/REWARD: {analysis_data.get('risk_reward', 'N/A')}
🎲 CONFIDENCE: {analysis_data.get('confidence', 'N/A')}

📝 SUMMARY:
{analysis_data.get('summary', 'No summary provided')}

🏗️ MARKET STRUCTURE:
{analysis_data.get('market_structure', 'N/A')}

📊 KEY LEVELS:
{analysis_data.get('support_resistance', 'N/A')}

🔍 OBSERVATIONS:
{analysis_data.get('key_observations', 'None')}"""

            # Save to database
            user_id = current_user.get("id") or current_user.get("sub")
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO chart_analyses (user_id, pair, timeframe, analysis_text, structured_data)
                    VALUES ($1, $2, $3, $4, $5)
                """, int(user_id), pair, timeframe, formatted_report, json.dumps(analysis_data))
            
            return {
                "analysis": formatted_report,
                "structured_data": analysis_data,
                "pair": pair,
                "timeframe": timeframe
            }
                
    except Exception as e:
        logger.error(f"Chart analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mentor/chat")
async def mentor_chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    try:
        # Get user history for context
        user_id = current_user.get("id") or current_user.get("sub")
        
        async with db_pool.acquire() as conn:
            # Get recent performance analysis
            perf = await conn.fetchrow("""
                SELECT analysis_data FROM performance_analyses 
                WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1
            """, int(user_id))
            
            # Get recent chat history
            history = await conn.fetch("""
                SELECT message, response FROM chat_history 
                WHERE user_id = $1 ORDER BY created_at DESC LIMIT 5
            """, int(user_id))
        
        context = ""
        if perf:
            analysis = json.loads(perf['analysis_data'])
            context = f"User trader score: {analysis.get('trader_score', 'N/A')}. "
            context += f"Top mistakes: {', '.join(analysis.get('top_mistakes', []))}. "
            context += f"Strengths: {', '.join(analysis.get('strengths', []))}."
        
        system_prompt = f"""You are a professional trading mentor. You know this about the user: {context}
Be encouraging but honest. Reference their specific weaknesses and strengths when relevant.
Suggest specific courses or improvements based on their profile."""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent history
        for h in reversed(history):
            messages.append({"role": "user", "content": h["message"]})
            messages.append({"role": "assistant", "content": h["response"]})
            
        messages.append({"role": "user", "content": request.message})
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": messages,
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="AI service error")
                
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
            # Save to history
            await conn.execute("""
                INSERT INTO chat_history (user_id, message, response, context)
                VALUES ($1, $2, $3, $4)
            """, int(user_id), request.message, ai_response, context)
            
            return {"response": ai_response}
            
    except Exception as e:
        logger.error(f"Mentor chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mentor/history")
async def get_mentor_history(
    limit: int = Query(20),
    current_user: dict = Depends(get_current_user)
):
    async with db_pool.acquire() as conn:
        user_id = current_user.get("id") or current_user.get("sub")
        rows = await conn.fetch("""
            SELECT message, response, created_at FROM chat_history 
            WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2
        """, int(user_id), limit)
        return {"history": [dict(row) for row in rows]}

# ==========================================
# HEALTH & ROOT
# ==========================================
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
        "version": "3.2.0",
        "database": db_status,
        "cloudinary_enabled": CLOUDINARY_AVAILABLE and bool(settings.CLOUDINARY_CLOUD_NAME),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Serve frontend if available, otherwise API info"""
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {
        "name": "Pipways API",
        "version": "3.2.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

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
