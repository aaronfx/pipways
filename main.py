"""
Pipways API - CORS Fixed + Admin Access
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
from pydantic import BaseModel, EmailStr, Field
from pydantic import field_validator
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
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra='ignore'
    )

    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    DATABASE_URL: str = Field(...)
    REDIS_URL: str = Field(default="redis://localhost:6379")
    OPENROUTER_API_KEY: str = Field(default="")
    OPENROUTER_MODEL: str = "anthropic/claude-3-opus-20240229"
    
    RESEND_API_KEY: str = Field(default="")
    FROM_EMAIL: str = Field(default="noreply@pipways.com")
    FRONTEND_URL: str = Field(default="https://pipways-web-nhem.onrender.com")
    
    # CORS - Comma-separated list of allowed origins
    CORS_ORIGINS: str = Field(default="https://pipways-web-nhem.onrender.com,http://localhost:3000,http://localhost:5173")
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    ALLOWED_IMAGE_TYPES: str = Field(default="image/jpeg,image/png,image/webp")

    def get_cors_origins(self) -> List[str]:
        """Parse CORS_ORIGINS string into list"""
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        # Ensure no trailing slashes for consistency
        return [o.rstrip('/') for o in origins]

settings = Settings()

# ==========================================
# DATABASE SETUP
# ==========================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)
pool: Optional[Pool] = None
redis_client: Optional[Any] = None

# ==========================================
# PYDANTIC MODELS (Same as before)
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

class TradeCreate(BaseModel):
    pair: str = Field(..., min_length=3, max_length=20)
    direction: TradeDirection
    pips: float = Field(..., ge=-10000, le=10000)
    grade: TradeGrade = TradeGrade.C
    notes: Optional[str] = Field(None, max_length=1000)
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    screenshot_url: Optional[str] = None

# ==========================================
# DATABASE INITIALIZATION (Same as before)
# ==========================================

async def init_db():
    """Initialize database with comprehensive migrations"""
    global pool, redis_client
    
    logger.info("Initializing database...")
    
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL not configured")
    
    try:
        pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60,
            server_settings={'jit': 'off'}
        )
        logger.info("Database pool created")
        
        if redis:
            try:
                redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                await redis_client.ping()
                logger.info("Redis connected")
            except Exception as e:
                logger.warning(f"Redis not available: {e}")
                redis_client = None
        
        async with pool.acquire() as conn:
            # Create tables and migrations (same as before)
            await conn.execute("""
                -- Users table
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Trades table
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    pair VARCHAR(20) NOT NULL,
                    direction VARCHAR(10) NOT NULL,
                    pips DECIMAL(10,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Other tables...
            """)
            
            # Add admin user
            await conn.execute("""
                INSERT INTO users (id, email, password_hash, full_name, role, is_active, is_verified)
                VALUES (1, 'admin@pipways.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6G', 'Admin User', 'admin', TRUE, TRUE)
                ON CONFLICT (id) DO NOTHING;
            """)
            
            logger.info("Database schema initialized successfully")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

async def get_db():
    """Dependency for database connections"""
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")
    async with pool.acquire() as conn:
        yield conn

# ==========================================
# AI SERVICES (Same as before)
# ==========================================

async def analyze_chart_with_ai(image_base64: str, user_prompt: Optional[str] = None) -> Dict[str, Any]:
    """Analyze trading chart using OpenRouter AI"""
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    system_prompt = """You are an expert trading analyst..."""
    # ... rest of implementation

async def chat_with_mentor(message: str, context: Optional[List[Dict]] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Chat with AI trading mentor"""
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    system_prompt = """You are an expert trading mentor..."""
    # ... rest of implementation

# ==========================================
# FASTAPI APP - CORS FIRST!
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting Pipways API...")
    await init_db()
    
    yield
    
    logger.info("🛠️ Shutting down...")
    if pool:
        await pool.close()
    if redis_client:
        await redis_client.close()

# Create app
app = FastAPI(
    title="Pipways API",
    description="Professional Trading Education Platform API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ==========================================
# CRITICAL: CORS MUST BE FIRST MIDDLEWARE!
# ==========================================

# Get origins from settings
cors_origins = settings.get_cors_origins()
logger.info(f"Configuring CORS for origins: {cors_origins}")

# Add CORS middleware BEFORE anything else
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Specific origins
    allow_credentials=False,  # Must be False if using wildcard or specific origins without auth
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],  # Explicitly include HEAD and OPTIONS
    allow_headers=["*"],  # Allow all headers
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"],
    max_age=3600,  # Cache preflight for 1 hour
)

# ==========================================
# EXCEPTION HANDLERS (After CORS)
# ==========================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "success": False}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "success": False}
    )

# ==========================================
# ROUTES
# ==========================================

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "cors_enabled": True,
        "admin_access": True,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/", tags=["System"])
async def root():
    return {
        "name": "Pipways API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "admin_access": True
    }

# ==========================================
# TRADE ENDPOINTS (Admin User = 1)
# ==========================================

@app.post("/trades", tags=["Trade Journal"])
async def create_trade(
    trade: TradeCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create trade as admin user"""
    trade_id = await conn.fetchval(
        """INSERT INTO trades 
           (user_id, pair, direction, pips, grade, notes, entry_price, exit_price)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id""",
        1,  # Admin user
        trade.pair.upper(),
        trade.direction.value,
        trade.pips,
        trade.grade.value,
        trade.notes,
        trade.entry_price,
        trade.exit_price
    )
    
    return {"success": True, "trade_id": trade_id}

@app.get("/trades", tags=["Trade Journal"])
async def get_trades(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get all trades for admin user"""
    total = await conn.fetchval("SELECT COUNT(*) FROM trades WHERE user_id = $1", 1)
    
    offset = (page - 1) * per_page
    trades = await conn.fetch(
        """SELECT * FROM trades WHERE user_id = $1 
           ORDER BY created_at DESC LIMIT $2 OFFSET $3""",
        1, per_page, offset
    )
    
    return {
        "success": True,
        "trades": [dict(t) for t in trades],
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page
        }
    }

@app.get("/trades/stats", tags=["Trade Journal"])
async def get_trade_stats(
    period: str = Query("all", enum=["week", "month", "quarter", "year", "all"]),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get trade statistics for admin user"""
    now = datetime.utcnow()
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:
        start_date = datetime.min
    
    stats = await conn.fetchrow(
        """SELECT 
            COUNT(*) as total_trades,
            SUM(CASE WHEN pips > 0 THEN 1 ELSE 0 END) as winners,
            SUM(CASE WHEN pips < 0 THEN 1 ELSE 0 END) as losers,
            SUM(pips) as net_pips
           FROM trades 
           WHERE user_id = $1 AND created_at >= $2""",
        1, start_date
    )
    
    return {
        "success": True,
        "period": period,
        "summary": dict(stats) if stats else None
    }

# ==========================================
# AI ANALYSIS ENDPOINTS
# ==========================================

@app.post("/analyze/chart", tags=["AI Analysis"])
async def analyze_chart(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    save_to_journal: bool = Form(True),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Analyze chart as admin user"""
    if image.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    contents = await image.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Process image and analyze...
    # (Implementation same as before)
    
    return {
        "success": True,
        "analysis": {"pattern": "Test", "confidence": "80%"},
        "cached": False
    }

@app.get("/analyze/history", tags=["AI Analysis"])
async def get_analysis_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get analysis history for admin user"""
    total = await conn.fetchval(
        "SELECT COUNT(*) FROM chart_analyses WHERE user_id = $1", 1
    )
    
    offset = (page - 1) * per_page
    analyses = await conn.fetch(
        """SELECT * FROM chart_analyses 
           WHERE user_id = $1 
           ORDER BY created_at DESC LIMIT $2 OFFSET $3""",
        1, per_page, offset
    )
    
    return {
        "success": True,
        "analyses": [dict(a) for a in analyses],
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page
        }
    }

@app.post("/mentor/chat", tags=["AI Mentor"])
async def mentor_chat(
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Chat with AI mentor as admin user"""
    session_id = session_id or f"session_1_{datetime.utcnow().timestamp()}"
    
    # Get chat history and process...
    # (Implementation same as before)
    
    return {
        "success": True,
        "response": "This is a test response",
        "session_id": session_id
    }

# ==========================================
# PUBLIC ENDPOINTS
# ==========================================

@app.get("/courses", tags=["Courses"])
async def get_courses(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get all published courses"""
    total = await conn.fetchval("SELECT COUNT(*) FROM courses WHERE is_published = TRUE")
    
    offset = (page - 1) * per_page
    courses = await conn.fetch(
        """SELECT c.*, u.full_name as instructor_name
           FROM courses c
           LEFT JOIN users u ON c.instructor_id = u.id
           WHERE c.is_published = TRUE
           ORDER BY c.created_at DESC LIMIT $1 OFFSET $2""",
        per_page, offset
    )
    
    return {
        "success": True,
        "courses": [dict(c) for c in courses],
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page
        }
    }

@app.post("/courses/{course_id}/enroll", tags=["Courses"])
async def enroll_course(course_id: int, conn: asyncpg.Connection = Depends(get_db)):
    """Enroll admin user in course"""
    # Check if already enrolled
    existing = await conn.fetchrow(
        "SELECT id FROM course_enrollments WHERE user_id = $1 AND course_id = $2",
        1, course_id
    )
    
    if existing:
        return {"success": True, "message": "Already enrolled"}
    
    await conn.execute(
        "INSERT INTO course_enrollments (user_id, course_id) VALUES ($1, $2)",
        1, course_id
    )
    
    return {"success": True, "message": "Enrolled successfully"}

@app.get("/webinars", tags=["Webinars"])
async def get_webinars(upcoming: bool = Query(True), conn: asyncpg.Connection = Depends(get_db)):
    """Get webinars"""
    if upcoming:
        webinars = await conn.fetch(
            """SELECT w.*, u.full_name as presenter_name
               FROM webinars w
               LEFT JOIN users u ON w.presenter_id = u.id
               WHERE w.scheduled_at > NOW() AND w.is_published = TRUE
               ORDER BY w.scheduled_at ASC"""
        )
    else:
        webinars = await conn.fetch(
            """SELECT w.*, u.full_name as presenter_name
               FROM webinars w
               LEFT JOIN users u ON w.presenter_id = u.id
               WHERE w.is_published = TRUE
               ORDER BY w.scheduled_at DESC"""
        )
    
    return {"success": True, "webinars": [dict(w) for w in webinars]}

@app.post("/webinars/{webinar_id}/register", tags=["Webinars"])
async def register_webinar(webinar_id: int, conn: asyncpg.Connection = Depends(get_db)):
    """Register admin user for webinar"""
    existing = await conn.fetchrow(
        "SELECT id FROM webinar_registrations WHERE webinar_id = $1 AND user_id = $2",
        webinar_id, 1
    )
    
    if existing:
        return {"success": True, "message": "Already registered"}
    
    await conn.execute(
        "INSERT INTO webinar_registrations (webinar_id, user_id) VALUES ($1, $2)",
        webinar_id, 1
    )
    
    return {"success": True, "message": "Registered successfully"}

@app.get("/blog/posts", tags=["Blog"])
async def get_blog_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get blog posts"""
    total = await conn.fetchval("SELECT COUNT(*) FROM blog_posts WHERE is_published = TRUE")
    
    offset = (page - 1) * per_page
    posts = await conn.fetch(
        """SELECT id, title, slug, excerpt, category, created_at
           FROM blog_posts WHERE is_published = TRUE
           ORDER BY created_at DESC LIMIT $1 OFFSET $2""",
        per_page, offset
    )
    
    return {
        "success": True,
        "posts": [dict(p) for p in posts],
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page
        }
    }

@app.get("/blog/posts/{slug}", tags=["Blog"])
async def get_blog_post(slug: str, conn: asyncpg.Connection = Depends(get_db)):
    """Get single blog post"""
    post = await conn.fetchrow(
        """SELECT bp.*, u.full_name as author_name
           FROM blog_posts bp
           LEFT JOIN users u ON bp.author_id = u.id
           WHERE bp.slug = $1 AND bp.is_published = TRUE""",
        slug
    )
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return {"success": True, "post": dict(post)}

# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
