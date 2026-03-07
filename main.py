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
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    DATABASE_URL: str = Field(...)
    REDIS_URL: str = Field(default="redis://localhost:6379")
    OPENROUTER_API_KEY: str = Field(...)
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True

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
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class TradeCreate(BaseModel):
    pair: str = Field(..., min_length=3, max_length=20)
    direction: TradeDirection
    pips: float = Field(..., ge=-10000, le=10000)
    grade: TradeGrade = TradeGrade.C
    notes: Optional[str] = Field(None, max_length=1000)
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    screenshot_url: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class AIAnalysisRequest(BaseModel):
    prompt: Optional[str] = Field(None, max_length=500)

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    context: Optional[List[Dict[str, str]]] = None

# ==========================================
# DATABASE INITIALIZATION
# ==========================================

async def init_db():
    """Initialize database with proper schema"""
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
        
        # Initialize Redis if available
        if redis:
            try:
                redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                await redis_client.ping()
                logger.info("Redis connected")
            except Exception as e:
                logger.warning(f"Redis not available: {e}")
                redis_client = None
        
        async with pool.acquire() as conn:
            # Create tables with proper constraints
            await conn.execute("""
                -- Users table with enhanced fields
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255),
                    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'admin', 'mentor')),
                    is_active BOOLEAN DEFAULT TRUE,
                    is_verified BOOLEAN DEFAULT FALSE,
                    email_verification_token VARCHAR(255),
                    password_reset_token VARCHAR(255),
                    password_reset_expires TIMESTAMP,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Create index on email for faster lookups
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                CREATE INDEX IF NOT EXISTS idx_users_reset_token ON users(password_reset_token) 
                    WHERE password_reset_token IS NOT NULL;
                
                -- Trades table with enhanced fields
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    pair VARCHAR(20) NOT NULL,
                    direction VARCHAR(10) NOT NULL CHECK (direction IN ('LONG', 'SHORT')),
                    pips DECIMAL(10,2) NOT NULL,
                    grade VARCHAR(5) DEFAULT 'C' CHECK (grade IN ('A', 'B', 'C', 'D', 'F')),
                    notes TEXT,
                    entry_price DECIMAL(15,5),
                    exit_price DECIMAL(15,5),
                    screenshot_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
                CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at);
                
                -- Courses table
                CREATE TABLE IF NOT EXISTS courses (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) UNIQUE NOT NULL,
                    description TEXT,
                    content TEXT,
                    level VARCHAR(20) DEFAULT 'beginner' CHECK (level IN ('beginner', 'intermediate', 'advanced', 'expert')),
                    price DECIMAL(10,2) DEFAULT 0,
                    is_published BOOLEAN DEFAULT FALSE,
                    thumbnail_url TEXT,
                    video_url TEXT,
                    duration_minutes INTEGER,
                    instructor_id INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_courses_slug ON courses(slug);
                CREATE INDEX IF NOT EXISTS idx_courses_published ON courses(is_published) WHERE is_published = TRUE;
                
                -- Course enrollments
                CREATE TABLE IF NOT EXISTS course_enrollments (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    progress_percent INTEGER DEFAULT 0 CHECK (progress_percent BETWEEN 0 AND 100),
                    UNIQUE(user_id, course_id)
                );
                
                -- Webinars table
                CREATE TABLE IF NOT EXISTS webinars (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    presenter_id INTEGER REFERENCES users(id),
                    scheduled_at TIMESTAMP NOT NULL,
                    duration_minutes INTEGER DEFAULT 60,
                    zoom_link TEXT,
                    max_attendees INTEGER DEFAULT 100,
                    price DECIMAL(10,2) DEFAULT 0,
                    is_published BOOLEAN DEFAULT FALSE,
                    recording_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_webinars_scheduled ON webinars(scheduled_at);
                
                -- Webinar registrations
                CREATE TABLE IF NOT EXISTS webinar_registrations (
                    id SERIAL PRIMARY KEY,
                    webinar_id INTEGER REFERENCES webinars(id) ON DELETE CASCADE,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    attended BOOLEAN DEFAULT FALSE,
                    UNIQUE(webinar_id, user_id)
                );
                
                -- Blog posts
                CREATE TABLE IF NOT EXISTS blog_posts (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    excerpt TEXT,
                    featured_image TEXT,
                    category VARCHAR(50) DEFAULT 'general',
                    tags TEXT[],
                    is_published BOOLEAN DEFAULT FALSE,
                    published_at TIMESTAMP,
                    author_id INTEGER REFERENCES users(id),
                    meta_title VARCHAR(255),
                    meta_description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_blog_posts_slug ON blog_posts(slug);
                CREATE INDEX IF NOT EXISTS idx_blog_posts_published ON blog_posts(is_published, published_at) 
                    WHERE is_published = TRUE;
                
                -- Chart analyses with AI integration
                CREATE TABLE IF NOT EXISTS chart_analyses (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    image_url TEXT NOT NULL,
                    image_hash VARCHAR(64) UNIQUE,
                    analysis_text TEXT NOT NULL,
                    pattern_detected VARCHAR(100),
                    confidence_score DECIMAL(3,2),
                    support_levels DECIMAL(10,5)[],
                    resistance_levels DECIMAL(10,5)[],
                    entry_zone VARCHAR(50),
                    stop_loss VARCHAR(50),
                    take_profit_1 VARCHAR(50),
                    take_profit_2 VARCHAR(50),
                    risk_reward_ratio VARCHAR(10),
                    indicators JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON chart_analyses(user_id);
                
                -- Mentor chat history
                CREATE TABLE IF NOT EXISTS mentor_chats (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    session_id VARCHAR(100) NOT NULL,
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    context JSONB,
                    tokens_used INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_mentor_chats_session ON mentor_chats(session_id);
                CREATE INDEX IF NOT EXISTS idx_mentor_chats_user ON mentor_chats(user_id, created_at);
                
                -- Password reset tokens
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    token_hash VARCHAR(64) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_reset_tokens_hash ON password_reset_tokens(token_hash);
                
                -- Insert default admin user if none exists
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM users WHERE role = 'admin' LIMIT 1) THEN
                        INSERT INTO users (email, password_hash, full_name, role, is_active, is_verified)
                        VALUES ('admin@pipways.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6G', 'Admin User', 'admin', TRUE, TRUE);
                    END IF;
                END $$;
            """)
            
            logger.info("Database schema initialized")
            
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
# AUTHENTICATION UTILITIES
# ==========================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow()
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow()
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def create_password_reset_token() -> str:
    """Generate secure random token for password reset"""
    return secrets.token_urlsafe(32)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn: asyncpg.Connection = Depends(get_db)
) -> Dict[str, Any]:
    """Validate JWT and return current user"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=["HS256"])
        
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Fetch fresh user data from database
        user = await conn.fetchrow(
            "SELECT id, email, full_name, role, is_active, is_verified FROM users WHERE email = $1",
            email
        )
        
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        if not user["is_active"]:
            raise HTTPException(status_code=403, detail="Account disabled")
        
        return dict(user)
        
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_admin(
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Verify user is admin"""
    if current_user["role"] != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# ==========================================
# EMAIL SERVICE
# ==========================================

async def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send email using Resend API"""
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured, email not sent")
        # In development, just log the email
        logger.info(f"Would send email to {to_email}: {subject}")
        return True
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
                json={
                    "from": settings.FROM_EMAIL,
                    "to": to_email,
                    "subject": subject,
                    "html": html_content
                }
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

async def send_password_reset_email(email: str, token: str) -> bool:
    """Send password reset email"""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ display: inline-block; padding: 12px 24px; background: #6366f1; color: white; text-decoration: none; border-radius: 8px; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Reset Your Pipways Password</h2>
            <p>Hello,</p>
            <p>We received a request to reset your password. Click the button below to create a new password:</p>
            <p><a href="{reset_url}" class="button">Reset Password</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{reset_url}</p>
            <p>This link will expire in 1 hour.</p>
            <div class="footer">
                <p>If you didn't request this, please ignore this email.</p>
                <p>Pipways - Professional Trading Education</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_email(email, "Reset Your Pipways Password", html)

# ==========================================
# AI/ML SERVICES
# ==========================================

async def analyze_chart_with_ai(image_base64: str, user_prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze trading chart using OpenRouter AI (Claude 3 Opus)
    """
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    system_prompt = """You are an expert trading analyst with 20+ years of experience in forex, crypto, and stock trading. 
    Analyze the provided chart image and provide detailed technical analysis including:
    
    1. Pattern Recognition - Identify any chart patterns (head and shoulders, triangles, flags, etc.)
    2. Support and Resistance Levels - Key price levels
    3. Trend Analysis - Short, medium, and long term trends
    4. Entry and Exit Points - Specific price zones
    5. Risk Management - Stop loss and take profit levels with risk/reward ratio
    6. Technical Indicators - RSI, MACD, Moving Averages if visible
    
    Respond in JSON format with these exact keys:
    {
        "pattern": "pattern name or 'None detected'",
        "summary": "brief analysis summary",
        "support_levels": ["1.0850", "1.0820"],
        "resistance_levels": ["1.0920", "1.0950"],
        "short_term_trend": "Bullish/Bearish/Neutral",
        "medium_term_trend": "Bullish/Bearish/Neutral", 
        "long_term_trend": "Bullish/Bearish/Neutral",
        "entry_zone": "1.0870 - 1.0880",
        "stop_loss": "1.0830",
        "take_profit_1": "1.0920",
        "take_profit_2": "1.0950",
        "risk_reward": "1:2.5",
        "confidence": "75%",
        "indicators": {
            "rsi": "62 (Neutral)",
            "macd": "Bullish crossover",
            "ema": "Price above 50 EMA",
            "volume": "Above average"
        }
    }"""
    
    user_message = user_prompt or "Analyze this chart and provide trading insights."
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": settings.FRONTEND_URL,
                    "X-Title": "Pipways Trading Analysis"
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user", 
                            "content": [
                                {"type": "text", "text": user_message},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                                }
                            ]
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.3
                }
            )
            
            if response.status_code != 200:
                logger.error(f"OpenRouter error: {response.text}")
                raise HTTPException(status_code=503, detail="AI analysis failed")
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Extract JSON from response (handle markdown code blocks)
            import re
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            analysis = json.loads(content)
            return analysis
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI analysis timed out")
    except json.JSONDecodeError:
        logger.error(f"Failed to parse AI response: {content}")
        raise HTTPException(status_code=503, detail="Invalid AI response format")
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        raise HTTPException(status_code=503, detail="AI service unavailable")

async def chat_with_mentor(message: str, context: Optional[List[Dict]] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Chat with AI trading mentor using conversation history
    """
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    system_prompt = """You are an expert trading mentor with decades of experience. Your role is to:
    - Provide personalized trading advice and education
    - Explain technical and fundamental analysis concepts
    - Help with risk management and psychology
    - Answer questions about specific trading strategies
    - Review trade ideas and provide constructive feedback
    
    Be encouraging but realistic. Always emphasize risk management. 
    If the user mentions specific trades, ask about their stop loss and position sizing.
    
    Keep responses concise (2-4 paragraphs) unless detailed explanation is requested."""
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation context if provided
    if context:
        for msg in context[-5:]:  # Keep last 5 messages for context
            messages.append(msg)
    
    messages.append({"role": "user", "content": message})
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": settings.FRONTEND_URL,
                    "X-Title": "Pipways AI Mentor"
                },
                json={
                    "model": "anthropic/claude-3-sonnet-20240229",
                    "messages": messages,
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )
            
            if response.status_code != 200:
                logger.error(f"OpenRouter error: {response.text}")
                raise HTTPException(status_code=503, detail="Mentor service failed")
            
            result = response.json()
            response_text = result["choices"][0]["message"]["content"]
            tokens_used = result.get("usage", {}).get("total_tokens", 0)
            
            return {
                "response": response_text,
                "tokens_used": tokens_used,
                "context": messages + [{"role": "assistant", "content": response_text}]
            }
            
    except Exception as e:
        logger.error(f"Mentor chat error: {e}")
        raise HTTPException(status_code=503, detail="Mentor service unavailable")

# ==========================================
# FASTAPI APP
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting Pipways API...")
    await init_db()
    
    yield
    
    logger.info("🛑 Shutting down...")
    if pool:
        await pool.close()
    if redis_client:
        await redis_client.close()

app = FastAPI(
    title="Pipways API",
    description="Professional Trading Education Platform API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"],
    max_age=3600
)

# ==========================================
# ERROR HANDLERS
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
# HEALTH & INFO
# ==========================================

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "database": "connected" if pool else "disconnected",
        "redis": "connected" if redis_client else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/", tags=["System"])
async def root():
    """API root"""
    return {
        "name": "Pipways API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# ==========================================
# AUTHENTICATION ENDPOINTS
# ==========================================

@app.post("/auth/register", response_model=TokenResponse, tags=["Authentication"])
async def register(
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    password: str = Form(...),
    full_name: Optional[str] = Form(None),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Register new user"""
    # Validate input
    try:
        user_data = UserCreate(email=email, password=password, full_name=full_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Check if user exists
    existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = get_password_hash(password)
    user_id = await conn.fetchval(
        """INSERT INTO users (email, password_hash, full_name, role, is_active, is_verified) 
           VALUES ($1, $2, $3, 'user', TRUE, FALSE) RETURNING id""",
        email, hashed_password, full_name
    )
    
    # Generate tokens
    access_token = create_access_token({"sub": email, "user_id": user_id, "role": "user"})
    refresh_token = create_refresh_token({"sub": email, "user_id": user_id})
    
    # TODO: Send verification email in background
    
    logger.info(f"User registered: {email}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "role": UserRole.USER,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    }

@app.post("/auth/login", response_model=TokenResponse, tags=["Authentication"])
async def login(
    email: str = Form(...),
    password: str = Form(...),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Login user"""
    # Fetch user with password hash
    user = await conn.fetchrow(
        """SELECT id, email, password_hash, full_name, role, is_active, is_verified 
           FROM users WHERE email = $1""",
        email
    )
    
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="Account disabled")
    
    # Update last login
    await conn.execute("UPDATE users SET last_login = NOW() WHERE id = $1", user["id"])
    
    # Generate tokens
    access_token = create_access_token({
        "sub": email, 
        "user_id": user["id"], 
        "role": user["role"]
    })
    refresh_token = create_refresh_token({
        "sub": email, 
        "user_id": user["id"]
    })
    
    logger.info(f"User logged in: {email}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "is_active": user["is_active"],
            "created_at": datetime.utcnow()
        }
    }

@app.post("/auth/refresh", response_model=TokenResponse, tags=["Authentication"])
async def refresh_token(
    refresh_token: str = Form(...),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Refresh access token"""
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        email = payload.get("sub")
        user_id = payload.get("user_id")
        
        # Verify user still exists and is active
        user = await conn.fetchrow(
            "SELECT email, role, is_active FROM users WHERE id = $1 AND email = $2",
            user_id, email
        )
        
        if not user or not user["is_active"]:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        # Generate new tokens
        new_access = create_access_token({
            "sub": email,
            "user_id": user_id,
            "role": user["role"]
        })
        new_refresh = create_refresh_token({"sub": email, "user_id": user_id})
        
        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user_id,
                "email": user["email"],
                "full_name": user.get("full_name"),
                "role": user["role"],
                "is_active": user["is_active"],
                "created_at": datetime.utcnow()
            }
        }
        
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@app.post("/auth/password-reset-request", tags=["Authentication"])
async def password_reset_request(
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Request password reset"""
    user = await conn.fetchrow("SELECT id, email, full_name FROM users WHERE email = $1", email)
    
    # Always return success to prevent email enumeration
    if not user:
        return {"success": True, "message": "If the email exists, a reset link has been sent"}
    
    # Generate token
    token = create_password_reset_token()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires = datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
    
    # Store token
    await conn.execute(
        """INSERT INTO password_reset_tokens (user_id, token_hash, expires_at) 
           VALUES ($1, $2, $3)
           ON CONFLICT (user_id) DO UPDATE 
           SET token_hash = $2, expires_at = $3, used_at = NULL""",
        user["id"], token_hash, expires
    )
    
    # Send email in background
    background_tasks.add_task(send_password_reset_email, email, token)
    
    logger.info(f"Password reset requested for: {email}")
    
    return {"success": True, "message": "If the email exists, a reset link has been sent"}

@app.post("/auth/password-reset-confirm", tags=["Authentication"])
async def password_reset_confirm(
    token: str = Form(...),
    new_password: str = Form(...),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Confirm password reset"""
    # Validate password
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Find valid token
    reset_record = await conn.fetchrow(
        """SELECT t.user_id, t.expires_at, t.used_at 
           FROM password_reset_tokens t
           WHERE t.token_hash = $1""",
        token_hash
    )
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    if reset_record["used_at"]:
        raise HTTPException(status_code=400, detail="Token already used")
    
    if reset_record["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")
    
    # Update password
    hashed_password = get_password_hash(new_password)
    await conn.execute(
        "UPDATE users SET password_hash = $1 WHERE id = $2",
        hashed_password, reset_record["user_id"]
    )
    
    # Mark token as used
    await conn.execute(
        "UPDATE password_reset_tokens SET used_at = NOW() WHERE token_hash = $1",
        token_hash
    )
    
    logger.info(f"Password reset completed for user: {reset_record['user_id']}")
    
    return {"success": True, "message": "Password reset successful"}

@app.get("/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_me(current_user: Dict = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(**current_user)

@app.post("/auth/logout", tags=["Authentication"])
async def logout(current_user: Dict = Depends(get_current_user)):
    """Logout user (client should discard tokens)"""
    # In a more advanced setup, we'd blacklist the token in Redis
    return {"success": True, "message": "Logged out successfully"}

# ==========================================
# TRADE JOURNAL ENDPOINTS
# ==========================================

@app.post("/trades", tags=["Trade Journal"])
async def create_trade(
    trade: TradeCreate,
    current_user: Dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new trade entry"""
    trade_id = await conn.fetchval(
        """INSERT INTO trades 
           (user_id, pair, direction, pips, grade, notes, entry_price, exit_price, screenshot_url)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING id""",
        current_user["id"],
        trade.pair.upper(),
        trade.direction.value,
        trade.pips,
        trade.grade.value,
        trade.notes,
        trade.entry_price,
        trade.exit_price,
        trade.screenshot_url
    )
    
    return {"success": True, "trade_id": trade_id}

@app.get("/trades", tags=["Trade Journal"])
async def get_trades(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    pair: Optional[str] = None,
    direction: Optional[TradeDirection] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: Dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get user's trades with filtering"""
    # Build query dynamically
    conditions = ["user_id = $1"]
    params = [current_user["id"]]
    param_idx = 2
    
    if pair:
        conditions.append(f"pair ILIKE ${param_idx}")
        params.append(f"%{pair}%")
        param_idx += 1
    
    if direction:
        conditions.append(f"direction = ${param_idx}")
        params.append(direction.value)
        param_idx += 1
    
    if start_date:
        conditions.append(f"created_at >= ${param_idx}")
        params.append(start_date)
        param_idx += 1
    
    if end_date:
        conditions.append(f"created_at <= ${param_idx}")
        params.append(end_date)
        param_idx += 1
    
    where_clause = " AND ".join(conditions)
    
    # Get total count
    total = await conn.fetchval(f"SELECT COUNT(*) FROM trades WHERE {where_clause}", *params)
    
    # Get paginated results
    offset = (page - 1) * per_page
    params.extend([per_page, offset])
    
    trades = await conn.fetch(
        f"""SELECT * FROM trades WHERE {where_clause} 
            ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}""",
        *params
    )
    
    # Calculate statistics
    stats = await conn.fetchrow(
        """SELECT 
            COUNT(*) as total_trades,
            SUM(CASE WHEN pips > 0 THEN 1 ELSE 0 END) as winning_trades,
            SUM(pips) as total_pips,
            AVG(pips) as avg_pips,
            MAX(pips) as best_trade,
            MIN(pips) as worst_trade
           FROM trades WHERE user_id = $1""",
        current_user["id"]
    )
    
    return {
        "success": True,
        "trades": [dict(t) for t in trades],
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        },
        "statistics": dict(stats) if stats else None
    }

@app.get("/trades/stats", tags=["Trade Journal"])
async def get_trade_stats(
    period: str = Query("all", enum=["week", "month", "quarter", "year", "all"]),
    current_user: Dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get detailed trade statistics"""
    # Calculate date range
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
            SUM(CASE WHEN pips = 0 THEN 1 ELSE 0 END) as breakeven,
            SUM(pips) as net_pips,
            AVG(pips) as avg_pips,
            AVG(CASE WHEN pips > 0 THEN pips END) as avg_win,
            AVG(CASE WHEN pips < 0 THEN pips END) as avg_loss,
            MAX(pips) as max_win,
            MIN(pips) as max_loss
           FROM trades 
           WHERE user_id = $1 AND created_at >= $2""",
        current_user["id"], start_date
    )
    
    # Grade distribution
    grades = await conn.fetch(
        "SELECT grade, COUNT(*) as count FROM trades WHERE user_id = $1 AND created_at >= $2 GROUP BY grade",
        current_user["id"], start_date
    )
    
    # Monthly trend
    monthly = await conn.fetch(
        """SELECT 
            DATE_TRUNC('month', created_at) as month,
            COUNT(*) as trades,
            SUM(pips) as pips
           FROM trades 
           WHERE user_id = $1 AND created_at >= $2
           GROUP BY DATE_TRUNC('month', created_at)
           ORDER BY month""",
        current_user["id"], start_date
    )
    
    return {
        "success": True,
        "period": period,
        "summary": dict(stats) if stats else None,
        "grade_distribution": {g["grade"]: g["count"] for g in grades},
        "monthly_trend": [dict(m) for m in monthly]
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
    current_user: Dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db)
):
    """
    Analyze trading chart using AI vision model
    """
    # Validate file
    if image.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Use PNG, JPG, or WebP")
    
    contents = await image.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB")
    
    # Calculate image hash for deduplication
    image_hash = hashlib.sha256(contents).hexdigest()
    
    # Check for existing analysis
    existing = await conn.fetchrow(
        "SELECT id, analysis_text FROM chart_analyses WHERE image_hash = $1 AND user_id = $2",
        image_hash, current_user["id"]
    )
    
    if existing:
        return {
            "success": True,
            "analysis_id": existing["id"],
            "analysis": json.loads(existing["analysis_text"]),
            "cached": True
        }
    
    # Encode image for AI
    image_base64 = base64.b64encode(contents).decode()
    
    # Call AI analysis
    analysis = await analyze_chart_with_ai(image_base64, prompt)
    
    # Store in database
    analysis_id = await conn.fetchval(
        """INSERT INTO chart_analyses 
           (user_id, image_url, image_hash, analysis_text, pattern_detected, 
            confidence_score, support_levels, resistance_levels, entry_zone,
            stop_loss, take_profit_1, take_profit_2, risk_reward_ratio, indicators)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14) RETURNING id""",
        current_user["id"],
        image.filename,
        image_hash,
        json.dumps(analysis),
        analysis.get("pattern"),
        float(analysis.get("confidence", "0%").rstrip("%")) / 100,
        [float(x) for x in analysis.get("support_levels", [])],
        [float(x) for x in analysis.get("resistance_levels", [])],
        analysis.get("entry_zone"),
        analysis.get("stop_loss"),
        analysis.get("take_profit_1"),
        analysis.get("take_profit_2"),
        analysis.get("risk_reward"),
        json.dumps(analysis.get("indicators", {}))
    )
    
    return {
        "success": True,
        "analysis_id": analysis_id,
        "analysis": analysis,
        "cached": False
    }

@app.get("/analyze/history", tags=["AI Analysis"])
async def get_analysis_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    current_user: Dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get user's chart analysis history"""
    total = await conn.fetchval(
        "SELECT COUNT(*) FROM chart_analyses WHERE user_id = $1",
        current_user["id"]
    )
    
    offset = (page - 1) * per_page
    analyses = await conn.fetch(
        """SELECT id, image_url, analysis_text, pattern_detected, 
                  confidence_score, created_at
           FROM chart_analyses 
           WHERE user_id = $1 
           ORDER BY created_at DESC LIMIT $2 OFFSET $3""",
        current_user["id"], per_page, offset
    )
    
    return {
        "success": True,
        "analyses": [{
            **dict(a),
            "analysis": json.loads(a["analysis_text"])
        } for a in analyses],
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
    current_user: Dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db)
):
    """
    Chat with AI trading mentor
    """
    # Get conversation history
    session_id = session_id or f"session_{current_user['id']}_{datetime.utcnow().timestamp()}"
    
    history = await conn.fetch(
        """SELECT message, response FROM mentor_chats 
           WHERE user_id = $1 AND session_id = $2 
           ORDER BY created_at DESC LIMIT 10""",
        current_user["id"], session_id
    )
    
    context = []
    for h in reversed(history):
        context.append({"role": "user", "content": h["message"]})
        context.append({"role": "assistant", "content": h["response"]})
    
    # Get AI response
    result = await chat_with_mentor(message, context, current_user["id"])
    
    # Store in database
    await conn.execute(
        """INSERT INTO mentor_chats 
           (user_id, session_id, message, response, context, tokens_used)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        current_user["id"],
        session_id,
        message,
        result["response"],
        json.dumps(context),
        result["tokens_used"]
    )
    
    return {
        "success": True,
        "response": result["response"],
        "session_id": session_id,
        "tokens_used": result["tokens_used"]
    }

# ==========================================
# ADMIN ENDPOINTS
# ==========================================

@app.post("/admin/courses", tags=["Admin"])
async def admin_create_course(
    title: str = Form(...),
    slug: str = Form(...),
    description: str = Form(...),
    content: str = Form(...),
    level: str = Form(...),
    price: float = Form(0),
    is_published: bool = Form(False),
    current_user: Dict = Depends(get_current_admin),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new course (admin only)"""
    try:
        course_id = await conn.fetchval(
            """INSERT INTO courses 
               (title, slug, description, content, level, price, is_published, instructor_id)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id""",
            title, slug, description, content, level, price, is_published, current_user["id"]
        )
        
        return {"success": True, "course_id": course_id}
        
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=400, detail="Course slug already exists")

@app.put("/admin/courses/{course_id}", tags=["Admin"])
async def admin_update_course(
    course_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    level: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    is_published: Optional[bool] = Form(None),
    current_user: Dict = Depends(get_current_admin),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update course (admin only)"""
    # Build update dynamically
    updates = []
    params = []
    param_idx = 1
    
    fields = {
        "title": title,
        "description": description,
        "content": content,
        "level": level,
        "price": price,
        "is_published": is_published
    }
    
    for field, value in fields.items():
        if value is not None:
            updates.append(f"{field} = ${param_idx}")
            params.append(value)
            param_idx += 1
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    updates.append("updated_at = NOW()")
    params.append(course_id)
    
    result = await conn.execute(
        f"UPDATE courses SET {', '.join(updates)} WHERE id = ${param_idx}",
        *params
    )
    
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Course not found")
    
    return {"success": True}

@app.post("/admin/blog", tags=["Admin"])
async def admin_create_blog_post(
    title: str = Form(...),
    slug: str = Form(...),
    content: str = Form(...),
    excerpt: Optional[str] = Form(None),
    category: str = Form("general"),
    tags: Optional[str] = Form(None),
    is_published: bool = Form(False),
    current_user: Dict = Depends(get_current_admin),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create blog post (admin only)"""
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    
    try:
        post_id = await conn.fetchval(
            """INSERT INTO blog_posts 
               (title, slug, content, excerpt, category, tags, is_published, 
                published_at, author_id, meta_title, meta_description)
               VALUES ($1, $2, $3, $4, $5, $6, $7, CASE WHEN $7 THEN NOW() END, $8, $9, $10) RETURNING id""",
            title, slug, content, excerpt or content[:200], category, tag_list,
            is_published, current_user["id"], title, excerpt or content[:160]
        )
        
        return {"success": True, "post_id": post_id}
        
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=400, detail="Blog slug already exists")

@app.post("/admin/webinars", tags=["Admin"])
async def admin_create_webinar(
    title: str = Form(...),
    description: str = Form(...),
    scheduled_at: datetime = Form(...),
    duration_minutes: int = Form(60),
    max_attendees: int = Form(100),
    price: float = Form(0),
    zoom_link: Optional[str] = Form(None),
    current_user: Dict = Depends(get_current_admin),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create webinar (admin only)"""
    webinar_id = await conn.fetchval(
        """INSERT INTO webinars 
           (title, description, presenter_id, scheduled_at, duration_minutes, 
            max_attendees, price, zoom_link, is_published)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, TRUE) RETURNING id""",
        title, description, current_user["id"], scheduled_at, duration_minutes,
        max_attendees, price, zoom_link
    )
    
    return {"success": True, "webinar_id": webinar_id}

@app.get("/admin/users", tags=["Admin"])
async def admin_list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: Dict = Depends(get_current_admin),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List all users (admin only)"""
    conditions = ["1=1"]
    params = []
    
    if search:
        conditions.append("(email ILIKE $1 OR full_name ILIKE $1)")
        params.append(f"%{search}%")
    
    where_clause = " AND ".join(conditions)
    
    total = await conn.fetchval(f"SELECT COUNT(*) FROM users WHERE {where_clause}", *params)
    
    offset = (page - 1) * per_page
    params.extend([per_page, offset])
    
    users = await conn.fetch(
        f"""SELECT id, email, full_name, role, is_active, is_verified, 
                   last_login, created_at
            FROM users WHERE {where_clause}
            ORDER BY created_at DESC LIMIT ${len(params)-1} OFFSET ${len(params)}""",
        *params
    )
    
    return {
        "success": True,
        "users": [dict(u) for u in users],
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page
        }
    }

# ==========================================
# PUBLIC ENDPOINTS
# ==========================================

@app.get("/courses", tags=["Courses"])
async def get_courses(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    level: Optional[str] = None,
    search: Optional[str] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get published courses"""
    conditions = ["is_published = TRUE"]
    params = []
    param_idx = 1
    
    if level:
        conditions.append(f"level = ${param_idx}")
        params.append(level)
        param_idx += 1
    
    if search:
        conditions.append(f"(title ILIKE ${param_idx} OR description ILIKE ${param_idx})")
        params.append(f"%{search}%")
        param_idx += 1
    
    where_clause = " AND ".join(conditions)
    
    total = await conn.fetchval(f"SELECT COUNT(*) FROM courses WHERE {where_clause}", *params)
    
    offset = (page - 1) * per_page
    params.extend([per_page, offset])
    
    courses = await conn.fetch(
        f"""SELECT c.*, u.full_name as instructor_name
            FROM courses c
            LEFT JOIN users u ON c.instructor_id = u.id
            WHERE {where_clause}
            ORDER BY c.created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}""",
        *params
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

@app.get("/courses/{slug}", tags=["Courses"])
async def get_course_detail(
    slug: str,
    current_user: Optional[Dict] = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get course details"""
    course = await conn.fetchrow(
        """SELECT c.*, u.full_name as instructor_name
           FROM courses c
           LEFT JOIN users u ON c.instructor_id = u.id
           WHERE c.slug = $1 AND c.is_published = TRUE""",
        slug
    )
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    result = dict(course)
    
    # Check enrollment if user is logged in
    if current_user:
        enrollment = await conn.fetchrow(
            "SELECT * FROM course_enrollments WHERE user_id = $1 AND course_id = $2",
            current_user["id"], course["id"]
        )
        result["enrolled"] = enrollment is not None
        result["progress"] = enrollment["progress_percent"] if enrollment else 0
    
    return {"success": True, "course": result}

@app.post("/courses/{course_id}/enroll", tags=["Courses"])
async def enroll_course(
    course_id: int,
    current_user: Dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Enroll in a course"""
    # Check if course exists and is published
    course = await conn.fetchrow(
        "SELECT id, price FROM courses WHERE id = $1 AND is_published = TRUE",
        course_id
    )
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if already enrolled
    existing = await conn.fetchrow(
        "SELECT id FROM course_enrollments WHERE user_id = $1 AND course_id = $2",
        current_user["id"], course_id
    )
    
    if existing:
        return {"success": True, "message": "Already enrolled"}
    
    # TODO: Handle paid courses with Stripe
    
    await conn.execute(
        "INSERT INTO course_enrollments (user_id, course_id) VALUES ($1, $2)",
        current_user["id"], course_id
    )
    
    return {"success": True, "message": "Enrolled successfully"}

@app.get("/webinars", tags=["Webinars"])
async def get_webinars(
    upcoming: bool = Query(True),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get webinars"""
    if upcoming:
        webinars = await conn.fetch(
            """SELECT w.*, u.full_name as presenter_name,
                      (SELECT COUNT(*) FROM webinar_registrations WHERE webinar_id = w.id) as registered_count
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

@app.get("/blog/posts", tags=["Blog"])
async def get_blog_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    category: Optional[str] = None,
    tag: Optional[str] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get blog posts"""
    conditions = ["is_published = TRUE"]
    params = []
    param_idx = 1
    
    if category:
        conditions.append(f"category = ${param_idx}")
        params.append(category)
        param_idx += 1
    
    if tag:
        conditions.append(f"${param_idx} = ANY(tags)")
        params.append(tag)
        param_idx += 1
    
    where_clause = " AND ".join(conditions)
    
    total = await conn.fetchval(f"SELECT COUNT(*) FROM blog_posts WHERE {where_clause}", *params)
    
    offset = (page - 1) * per_page
    params.extend([per_page, offset])
    
    posts = await conn.fetch(
        f"""SELECT id, title, slug, excerpt, featured_image, category, 
                   tags, created_at, updated_at
            FROM blog_posts WHERE {where_clause}
            ORDER BY published_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}""",
        *params
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
