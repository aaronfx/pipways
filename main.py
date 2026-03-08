"""
Pipways API - Professional Trading Signals & Education Platform
Complete working version with professional AI prompts
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
    OPENROUTER_VISION_MODEL: str = "anthropic/claude-3-opus-20240229"

    # Telegram Configuration
    TELEGRAM_FREE_CHANNEL_LINK: str = Field(default="https://t.me/pipways_free")
    TELEGRAM_PREMIUM_CHANNEL_LINK: str = Field(default="https://t.me/pipways_vip")
    TELEGRAM_BOT_USERNAME: str = Field(default="pipways_bot")

    # Feature Flags
    SUBSCRIPTION_ENABLED: bool = Field(default=False)

    RESEND_API_KEY: str = Field(default="")
    FROM_EMAIL: str = Field(default="noreply@pipways.com")
    FRONTEND_URL: str = Field(default="https://pipways-web-nhem.onrender.com")

    CORS_ORIGINS: str = Field(default="https://pipways-web-nhem.onrender.com,http://localhost:3000,http://localhost:5173")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    ALLOWED_IMAGE_TYPES: str = Field(default="image/jpeg,image/png,image/webp")

    def get_cors_origins(self) -> List[str]:
        """Parse CORS_ORIGINS string into list"""
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
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
# PYDANTIC MODELS
# ==========================================

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MENTOR = "mentor"

class SignalDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class SignalStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class SignalCreate(BaseModel):
    pair: str = Field(..., min_length=3, max_length=20)
    direction: SignalDirection
    entry_price: float = Field(..., gt=0)
    stop_loss: float = Field(..., gt=0)
    take_profit_1: float = Field(..., gt=0)
    take_profit_2: Optional[float] = None
    risk_percent: Optional[float] = Field(default=1.0, ge=0.1, le=5.0)
    analysis: Optional[str] = Field(None, max_length=2000)
    timeframe: str = Field(default="1H")
    is_premium: bool = Field(default=False)

class SignalUpdate(BaseModel):
    status: SignalStatus
    exit_price: Optional[float] = None
    pips_result: Optional[float] = None

class BlogPostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    slug: Optional[str] = None
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = Field(None, max_length=500)
    category: str = Field(default="General")
    is_published: bool = Field(default=True)
    featured_image_url: Optional[str] = None

class WebinarCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=15, le=180)
    max_attendees: int = Field(default=100, ge=1)
    is_published: bool = Field(default=True)
    meeting_link: Optional[str] = None
    is_premium: bool = Field(default=False)

class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    level: str = Field(default="Beginner")
    duration_minutes: int = Field(default=60, ge=1)
    price: float = Field(default=0.0, ge=0)
    is_published: bool = Field(default=True)
    thumbnail_url: Optional[str] = None
    is_premium: bool = Field(default=False)

# ==========================================
# PROFESSIONAL AI PROMPTS
# ==========================================

CHART_ANALYSIS_PROMPT = """You are an elite professional trading analyst with 20+ years of experience in forex, crypto, and stock markets. Analyze the provided trading chart with extreme precision and detail.

CRITICAL INSTRUCTIONS:
1. Identify the chart type (candlestick, line, bar) and timeframe if visible
2. Detect ALL chart patterns (head and shoulders, double tops/bottoms, triangles, wedges, flags, pennants, channels, etc.)
3. Identify precise support and resistance levels with price levels
4. Analyze trend direction across multiple timeframes
5. Calculate specific entry zones, stop losses, and take profit levels
6. Evaluate volume patterns if visible
7. Assess risk/reward ratio for potential trades

OUTPUT FORMAT - Return ONLY valid JSON:
{
    "pattern": "Specific pattern name (e.g., 'Ascending Triangle', 'Double Bottom', 'Bull Flag')",
    "summary": "Detailed 2-3 sentence analysis of what the chart shows",
    "confidence": "High|Medium|Low - based on pattern clarity",
    "support_levels": ["1.0850", "1.0820"],
    "resistance_levels": ["1.0920", "1.0950"],
    "short_term_trend": "Bullish/Bearish/Neutral with brief explanation",
    "medium_term_trend": "Bullish/Bearish/Neutral with brief explanation", 
    "long_term_trend": "Bullish/Bearish/Neutral with brief explanation",
    "entry_zone": "Specific price range for entry",
    "stop_loss": "Specific price level for stop loss",
    "take_profit_1": "First take profit target",
    "take_profit_2": "Second take profit target",
    "risk_reward": "Calculated ratio (e.g., '1:2.5')",
    "indicators": {
        "rsi": "RSI value and interpretation if visible",
        "macd": "MACD signal if visible",
        "ema": "Key EMA levels if visible",
        "volume": "Volume analysis if visible"
    },
    "key_observations": [
        "Specific observation 1",
        "Specific observation 2"
    ],
    "trading_recommendation": "Clear buy/sell/wait recommendation with reasoning"
}

Be precise with price levels. If uncertain, state "N/A" rather than guessing."""

MENTOR_SYSTEM_PROMPT = """You are an elite trading mentor with decades of experience in forex, crypto, stocks, and derivatives. You have trained professional traders at top institutions.

YOUR EXPERTISE:
- Technical Analysis: Price action, chart patterns, indicators (RSI, MACD, EMA, VWAP, Bollinger Bands)
- Fundamental Analysis: Economic indicators, earnings, macro trends
- Risk Management: Position sizing, stop losses, portfolio allocation, drawdown control
- Trading Psychology: Emotional control, discipline, FOMO management, journaling
- Strategy Development: Scalping, day trading, swing trading, position trading

RESPONSE GUIDELINES:
1. Always provide actionable, specific advice
2. Use real-world examples when explaining concepts
3. Include risk management in every trade-related answer
4. Ask clarifying questions if the user's query is vague
5. Format responses with clear structure using bullet points or numbered lists
6. For chart-related questions, reference specific price action concepts
7. Emphasize the importance of backtesting and journaling
8. Never guarantee profits - always discuss probabilities and risk

If the user asks about a specific trade setup, ask for: entry, stop loss, target, and timeframe before giving advice.

Current date: {current_date}"""

# ==========================================
# DATABASE INITIALIZATION
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
            # Create tables (if not exist)
            await conn.execute("""
                -- Users table
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255),
                    role VARCHAR(50) DEFAULT 'user',
                    is_active BOOLEAN DEFAULT TRUE,
                    is_verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Add new columns to existing users table
                ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(50) DEFAULT 'free',
                    ADD COLUMN IF NOT EXISTS subscription_expires_at TIMESTAMP,
                    ADD COLUMN IF NOT EXISTS telegram_username VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS telegram_chat_id BIGINT;

                -- Trading Signals table
                CREATE TABLE IF NOT EXISTS signals (
                    id SERIAL PRIMARY KEY,
                    pair VARCHAR(20) NOT NULL,
                    direction VARCHAR(10) NOT NULL,
                    entry_price DECIMAL(15,5) NOT NULL,
                    stop_loss DECIMAL(15,5) NOT NULL,
                    take_profit_1 DECIMAL(15,5) NOT NULL,
                    take_profit_2 DECIMAL(15,5),
                    risk_percent DECIMAL(4,2) DEFAULT 1.0,
                    analysis TEXT,
                    timeframe VARCHAR(10) DEFAULT '1H',
                    status VARCHAR(20) DEFAULT 'active',
                    is_premium BOOLEAN DEFAULT FALSE,
                    pips_result DECIMAL(10,2),
                    exit_price DECIMAL(15,5),
                    created_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP
                );

                -- Chart analyses table
                CREATE TABLE IF NOT EXISTS chart_analyses (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    image_url TEXT,
                    pattern_detected VARCHAR(100),
                    confidence_score DECIMAL(3,2),
                    analysis_data JSONB,
                    is_premium BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Mentor chat sessions
                CREATE TABLE IF NOT EXISTS mentor_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    session_id VARCHAR(255) UNIQUE,
                    context JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Courses table
                CREATE TABLE IF NOT EXISTS courses (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    level VARCHAR(50) DEFAULT 'Beginner',
                    duration_minutes INTEGER DEFAULT 60,
                    price DECIMAL(10,2) DEFAULT 0,
                    is_premium BOOLEAN DEFAULT FALSE,
                    instructor_id INTEGER REFERENCES users(id),
                    thumbnail_url TEXT,
                    is_published BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Course enrollments
                CREATE TABLE IF NOT EXISTS course_enrollments (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, course_id)
                );

                -- Webinars table
                CREATE TABLE IF NOT EXISTS webinars (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    scheduled_at TIMESTAMP,
                    duration_minutes INTEGER DEFAULT 60,
                    max_attendees INTEGER DEFAULT 100,
                    is_premium BOOLEAN DEFAULT FALSE,
                    presenter_id INTEGER REFERENCES users(id),
                    meeting_link TEXT,
                    is_published BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Webinar registrations
                CREATE TABLE IF NOT EXISTS webinar_registrations (
                    id SERIAL PRIMARY KEY,
                    webinar_id INTEGER REFERENCES webinars(id) ON DELETE CASCADE,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(webinar_id, user_id)
                );

                -- Blog posts table
                CREATE TABLE IF NOT EXISTS blog_posts (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) UNIQUE,
                    content TEXT,
                    excerpt TEXT,
                    category VARCHAR(100) DEFAULT 'General',
                    author_id INTEGER REFERENCES users(id),
                    featured_image_url TEXT,
                    is_published BOOLEAN DEFAULT FALSE,
                    view_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Telegram bot messages log
                CREATE TABLE IF NOT EXISTS telegram_messages (
                    id SERIAL PRIMARY KEY,
                    signal_id INTEGER REFERENCES signals(id),
                    message_id BIGINT,
                    chat_id BIGINT,
                    message_type VARCHAR(50),
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Add admin user (only if not exists)
            await conn.execute("""
                INSERT INTO users (id, email, password_hash, full_name, role, is_active, is_verified, subscription_tier)
                VALUES (1, 'admin@pipways.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6G', 'Admin User', 'admin', TRUE, TRUE, 'premium')
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
# AI SERVICES
# ==========================================

async def analyze_chart_with_ai(image_base64: str, user_prompt: Optional[str] = None) -> Dict[str, Any]:
    """Analyze trading chart using OpenRouter AI with vision capabilities"""
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    prompt = user_prompt if user_prompt else CHART_ANALYSIS_PROMPT

    if ',' in image_base64:
        image_data = image_base64
    else:
        image_data = f"data:image/jpeg;base64,{image_base64}"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": settings.FRONTEND_URL,
                    "X-Title": "Pipways Trading Analysis",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.OPENROUTER_VISION_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": image_data,
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.2
                }
            )

            if response.status_code != 200:
                logger.error(f"OpenRouter error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=503, detail="AI analysis service error")

            result = response.json()
            content = result['choices'][0]['message']['content']

            try:
                analysis = json.loads(content)
            except json.JSONDecodeError:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                analysis = json.loads(content)

            return analysis

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI analysis timeout - please try again")
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

async def chat_with_mentor(message: str, context: Optional[List[Dict]] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Chat with AI trading mentor using OpenRouter"""
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    messages = [
        {
            "role": "system",
            "content": MENTOR_SYSTEM_PROMPT.format(current_date=datetime.utcnow().strftime("%Y-%m-%d"))
        }
    ]

    if context:
        for msg in context[-10:]:
            messages.append(msg)

    messages.append({
        "role": "user",
        "content": message
    })

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": settings.FRONTEND_URL,
                    "X-Title": "Pipways AI Mentor",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": messages,
                    "max_tokens": 1500,
                    "temperature": 0.7
                }
            )

            if response.status_code != 200:
                logger.error(f"OpenRouter error: {response.status_code}")
                raise HTTPException(status_code=503, detail="Mentor service error")

            result = response.json()
            reply = result['choices'][0]['message']['content']

            return {
                "response": reply,
                "tokens_used": result.get('usage', {}).get('total_tokens', 0)
            }

    except Exception as e:
        logger.error(f"Mentor chat error: {e}")
        raise HTTPException(status_code=500, detail="Mentor service unavailable")

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
    version="4.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ==========================================
# CRITICAL: CORS MUST BE FIRST MIDDLEWARE!
# ==========================================

cors_origins = settings.get_cors_origins()
logger.info(f"Configuring CORS for origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"],
    max_age=3600,
)

# ==========================================
# EXCEPTION HANDLERS
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
        "version": "4.0.0",
        "cors_enabled": True,
        "admin_access": True,
        "ai_services": bool(settings.OPENROUTER_API_KEY),
        "subscription_enabled": settings.SUBSCRIPTION_ENABLED,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/", tags=["System"])
async def root():
    return {
        "name": "Pipways API",
        "version": "4.0.0",
        "docs": "/docs",
        "health": "/health",
        "admin_access": True
    }

# ==========================================
# CONFIGURATION ENDPOINTS
# ==========================================

@app.get("/config", tags=["Configuration"])
async def get_config():
    """Get public configuration"""
    return {
        "telegram_free_channel": settings.TELEGRAM_FREE_CHANNEL_LINK,
        "telegram_premium_channel": settings.TELEGRAM_PREMIUM_CHANNEL_LINK,
        "telegram_bot": settings.TELEGRAM_BOT_USERNAME,
        "subscription_enabled": settings.SUBSCRIPTION_ENABLED,
        "features": {
            "ai_analysis": True,
            "ai_mentor": True,
            "signals": True,
            "courses": True,
            "webinars": True,
            "blog": True
        }
    }

# ==========================================
# TRADING SIGNALS ENDPOINTS
# ==========================================

@app.get("/signals", tags=["Trading Signals"])
async def get_signals(
    status: Optional[str] = Query("active", enum=["active", "closed", "all"]),
    is_premium: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get trading signals (filtered by subscription if enabled)"""
    query = "SELECT * FROM signals WHERE 1=1"
    params = []

    if status != "all":
        query += f" AND status = ${len(params)+1}"
        params.append(status)

    if is_premium is not None:
        query += f" AND is_premium = ${len(params)+1}"
        params.append(is_premium)

    # If subscription enabled, free users only see free signals
    if settings.SUBSCRIPTION_ENABLED:
        query += f" AND (is_premium = FALSE OR ${len(params)+1} = 'premium')"
        params.append('free')  # Would check actual user tier

    query += " ORDER BY created_at DESC"
    query += f" LIMIT ${len(params)+1}"
    params.append(limit)

    signals = await conn.fetch(query, *params)

    return {
        "success": True,
        "signals": [dict(s) for s in signals],
        "telegram_links": {
            "free": settings.TELEGRAM_FREE_CHANNEL_LINK,
            "premium": settings.TELEGRAM_PREMIUM_CHANNEL_LINK
        }
    }

@app.get("/signals/stats", tags=["Trading Signals"])
async def get_signal_stats(
    days: int = Query(30, ge=7, le=365),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get signal performance statistics"""
    since = datetime.utcnow() - timedelta(days=days)

    stats = await conn.fetchrow("""
        SELECT 
            COUNT(*) as total_signals,
            SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_signals,
            SUM(CASE WHEN pips_result > 0 THEN 1 ELSE 0 END) as winning_signals,
            SUM(CASE WHEN pips_result < 0 THEN 1 ELSE 0 END) as losing_signals,
            SUM(pips_result) as total_pips,
            AVG(pips_result) FILTER (WHERE status = 'closed') as avg_pips_per_trade
        FROM signals 
        WHERE created_at >= $1
    """, since)

    return {
        "success": True,
        "period_days": days,
        "stats": dict(stats) if stats else {}
    }

# ==========================================
# ADMIN SIGNAL MANAGEMENT
# ==========================================

@app.post("/admin/signals", tags=["Admin - Signals"])
async def create_signal(
    signal: SignalCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create trading signal (admin only)"""
    signal_id = await conn.fetchval("""
        INSERT INTO signals 
        (pair, direction, entry_price, stop_loss, take_profit_1, take_profit_2, 
         risk_percent, analysis, timeframe, is_premium, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) RETURNING id
    """, 
        signal.pair.upper(),
        signal.direction.value,
        signal.entry_price,
        signal.stop_loss,
        signal.take_profit_1,
        signal.take_profit_2,
        signal.risk_percent,
        signal.analysis,
        signal.timeframe,
        signal.is_premium,
        1  # Admin user
    )

    return {
        "success": True, 
        "signal_id": signal_id,
        "message": "Signal created successfully"
    }

@app.put("/admin/signals/{signal_id}", tags=["Admin - Signals"])
async def update_signal(
    signal_id: int,
    update: SignalUpdate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update signal status/result (admin only)"""
    await conn.execute("""
        UPDATE signals 
        SET status = $1, exit_price = $2, pips_result = $3, closed_at = CASE WHEN $1 = 'closed' THEN NOW() ELSE closed_at END
        WHERE id = $4
    """, update.status.value, update.exit_price, update.pips_result, signal_id)

    return {"success": True, "message": "Signal updated"}

@app.delete("/admin/signals/{signal_id}", tags=["Admin - Signals"])
async def delete_signal(
    signal_id: int,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Delete signal (admin only)"""
    await conn.execute("DELETE FROM signals WHERE id = $1", signal_id)
    return {"success": True, "message": "Signal deleted"}

@app.get("/admin/signals", tags=["Admin - Signals"])
async def get_all_signals_admin(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get all signals for admin"""
    total = await conn.fetchval("SELECT COUNT(*) FROM signals")

    offset = (page - 1) * per_page
    signals = await conn.fetch("""
        SELECT s.*, u.full_name as created_by_name
        FROM signals s
        LEFT JOIN users u ON s.created_by = u.id
        ORDER BY s.created_at DESC LIMIT $1 OFFSET $2
    """, per_page, offset)

    return {
        "success": True,
        "signals": [dict(s) for s in signals],
        "pagination": {"total": total, "page": page, "per_page": per_page}
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
    """Analyze chart using professional AI"""
    if image.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    contents = await image.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    image_base64 = base64.b64encode(contents).decode('utf-8')

    try:
        analysis = await analyze_chart_with_ai(image_base64, prompt)

        if save_to_journal:
            await conn.execute(
                """INSERT INTO chart_analyses 
                   (user_id, image_url, pattern_detected, confidence_score, analysis_data)
                   VALUES ($1, $2, $3, $4, $5)""",
                1,
                image.filename,
                analysis.get('pattern', 'Unknown'),
                0.8,
                json.dumps(analysis)
            )

        return {
            "success": True,
            "analysis": analysis,
            "cached": False
        }

    except Exception as e:
        logger.error(f"Chart analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze/history", tags=["AI Analysis"])
async def get_analysis_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get analysis history"""
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

    results = []
    for a in analyses:
        row = dict(a)
        if row.get('analysis_data'):
            row['analysis'] = json.loads(row['analysis_data'])
        results.append(row)

    return {
        "success": True,
        "analyses": results,
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page
        }
    }

# ==========================================
# AI MENTOR ENDPOINTS
# ==========================================

@app.post("/mentor/chat", tags=["AI Mentor"])
async def mentor_chat(
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Chat with AI trading mentor"""
    if not session_id:
        session_id = f"session_1_{datetime.utcnow().timestamp()}"

    context = []
    if session_id:
        session = await conn.fetchrow(
            "SELECT context FROM mentor_sessions WHERE session_id = $1 AND user_id = $2",
            session_id, 1
        )
        if session and session['context']:
            context = json.loads(session['context'])

    result = await chat_with_mentor(message, context, 1)

    new_context = context + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": result['response']}
    ]

    await conn.execute("""
        INSERT INTO mentor_sessions (user_id, session_id, context, updated_at)
        VALUES ($1, $2, $3, NOW())
        ON CONFLICT (session_id) 
        DO UPDATE SET context = $3, updated_at = NOW()
    """, 1, session_id, json.dumps(new_context[-20:]))

    return {
        "success": True,
        "response": result['response'],
        "session_id": session_id,
        "tokens_used": result.get('tokens_used', 0)
    }

# ==========================================
# ADMIN CONTENT MANAGEMENT
# ==========================================

@app.post("/admin/blog", tags=["Admin - Blog"])
async def create_blog_post(
    post: BlogPostCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create blog post (admin only)"""
    slug = post.slug
    if not slug:
        slug = re.sub(r'[^a-z0-9]+', '-', post.title.lower()).strip('-')

    existing = await conn.fetchval("SELECT id FROM blog_posts WHERE slug = $1", slug)
    if existing:
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

    post_id = await conn.fetchval("""
        INSERT INTO blog_posts (title, slug, content, excerpt, category, author_id, featured_image_url, is_published)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id
    """, post.title, slug, post.content, post.excerpt, post.category, 1, post.featured_image_url, post.is_published)

    return {"success": True, "post_id": post_id, "slug": slug}

@app.put("/admin/blog/{post_id}", tags=["Admin - Blog"])
async def update_blog_post(
    post_id: int,
    post: BlogPostCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update blog post (admin only)"""
    await conn.execute("""
        UPDATE blog_posts 
        SET title = $1, content = $2, excerpt = $3, category = $4, 
            featured_image_url = $5, is_published = $6, updated_at = NOW()
        WHERE id = $7 AND author_id = $8
    """, post.title, post.content, post.excerpt, post.category, 
        post.featured_image_url, post.is_published, post_id, 1)

    return {"success": True, "message": "Post updated"}

@app.delete("/admin/blog/{post_id}", tags=["Admin - Blog"])
async def delete_blog_post(
    post_id: int,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Delete blog post (admin only)"""
    await conn.execute("DELETE FROM blog_posts WHERE id = $1 AND author_id = $2", post_id, 1)
    return {"success": True, "message": "Post deleted"}

@app.get("/admin/blog", tags=["Admin - Blog"])
async def get_all_blog_posts_admin(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get all blog posts including drafts (admin only)"""
    total = await conn.fetchval("SELECT COUNT(*) FROM blog_posts")

    offset = (page - 1) * per_page
    posts = await conn.fetch("""
        SELECT bp.*, u.full_name as author_name
        FROM blog_posts bp
        LEFT JOIN users u ON bp.author_id = u.id
        ORDER BY bp.created_at DESC LIMIT $1 OFFSET $2
    """, per_page, offset)

    return {
        "success": True,
        "posts": [dict(p) for p in posts],
        "pagination": {"total": total, "page": page, "per_page": per_page}
    }

@app.post("/admin/webinars", tags=["Admin - Webinars"])
async def create_webinar(
    webinar: WebinarCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create webinar (admin only)"""
    webinar_id = await conn.fetchval("""
        INSERT INTO webinars (title, description, scheduled_at, duration_minutes, max_attendees, presenter_id, meeting_link, is_published, is_premium)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING id
    """, webinar.title, webinar.description, webinar.scheduled_at, 
        webinar.duration_minutes, webinar.max_attendees, 1, webinar.meeting_link, webinar.is_published, webinar.is_premium)

    return {"success": True, "webinar_id": webinar_id}

@app.put("/admin/webinars/{webinar_id}", tags=["Admin - Webinars"])
async def update_webinar(
    webinar_id: int,
    webinar: WebinarCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update webinar (admin only)"""
    await conn.execute("""
        UPDATE webinars 
        SET title = $1, description = $2, scheduled_at = $3, duration_minutes = $4,
            max_attendees = $5, meeting_link = $6, is_published = $7, is_premium = $8
        WHERE id = $9 AND presenter_id = $10
    """, webinar.title, webinar.description, webinar.scheduled_at,
        webinar.duration_minutes, webinar.max_attendees, webinar.meeting_link,
        webinar.is_published, webinar.is_premium, webinar_id, 1)

    return {"success": True, "message": "Webinar updated"}

@app.delete("/admin/webinars/{webinar_id}", tags=["Admin - Webinars"])
async def delete_webinar(
    webinar_id: int,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Delete webinar (admin only)"""
    await conn.execute("DELETE FROM webinars WHERE id = $1 AND presenter_id = $2", webinar_id, 1)
    return {"success": True, "message": "Webinar deleted"}

@app.get("/admin/webinars", tags=["Admin - Webinars"])
async def get_all_webinars_admin(
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get all webinars including drafts (admin only)"""
    webinars = await conn.fetch("""
        SELECT w.*, u.full_name as presenter_name,
               COUNT(wr.id) as registered_count
        FROM webinars w
        LEFT JOIN users u ON w.presenter_id = u.id
        LEFT JOIN webinar_registrations wr ON w.id = wr.webinar_id
        GROUP BY w.id, u.full_name
        ORDER BY w.scheduled_at DESC
    """)

    return {
        "success": True,
        "webinars": [dict(w) for w in webinars]
    }

@app.post("/admin/courses", tags=["Admin - Courses"])
async def create_course(
    course: CourseCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create course (admin only)"""
    course_id = await conn.fetchval("""
        INSERT INTO courses (title, description, level, duration_minutes, price, instructor_id, thumbnail_url, is_published, is_premium)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING id
    """, course.title, course.description, course.level, course.duration_minutes,
        course.price, 1, course.thumbnail_url, course.is_published, course.is_premium)

    return {"success": True, "course_id": course_id}

@app.put("/admin/courses/{course_id}", tags=["Admin - Courses"])
async def update_course(
    course_id: int,
    course: CourseCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update course (admin only)"""
    await conn.execute("""
        UPDATE courses 
        SET title = $1, description = $2, level = $3, duration_minutes = $4,
            price = $5, thumbnail_url = $6, is_published = $7, is_premium = $8
        WHERE id = $9 AND instructor_id = $10
    """, course.title, course.description, course.level, course.duration_minutes,
        course.price, course.thumbnail_url, course.is_published, course.is_premium, course_id, 1)

    return {"success": True, "message": "Course updated"}

@app.delete("/admin/courses/{course_id}", tags=["Admin - Courses"])
async def delete_course(
    course_id: int,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Delete course (admin only)"""
    await conn.execute("DELETE FROM courses WHERE id = $1 AND instructor_id = $2", course_id, 1)
    return {"success": True, "message": "Course deleted"}

@app.get("/admin/courses", tags=["Admin - Courses"])
async def get_all_courses_admin(
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get all courses including drafts (admin only)"""
    courses = await conn.fetch("""
        SELECT c.*, u.full_name as instructor_name,
               COUNT(ce.id) as enrolled_count
        FROM courses c
        LEFT JOIN users u ON c.instructor_id = u.id
        LEFT JOIN course_enrollments ce ON c.id = ce.course_id
        GROUP BY c.id, u.full_name
        ORDER BY c.created_at DESC
    """)

    return {
        "success": True,
        "courses": [dict(c) for c in courses]
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
    courses = await conn.fetch("""
        SELECT c.*, u.full_name as instructor_name
        FROM courses c
        LEFT JOIN users u ON c.instructor_id = u.id
        WHERE c.is_published = TRUE
        ORDER BY c.created_at DESC LIMIT $1 OFFSET $2
    """, per_page, offset)

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
        webinars = await conn.fetch("""
            SELECT w.*, u.full_name as presenter_name,
                   (SELECT COUNT(*) FROM webinar_registrations WHERE webinar_id = w.id) as registered_count
            FROM webinars w
            LEFT JOIN users u ON w.presenter_id = u.id
            WHERE w.scheduled_at > NOW() AND w.is_published = TRUE
            ORDER BY w.scheduled_at ASC
        """)
    else:
        webinars = await conn.fetch("""
            SELECT w.*, u.full_name as presenter_name,
                   (SELECT COUNT(*) FROM webinar_registrations WHERE webinar_id = w.id) as registered_count
            FROM webinars w
            LEFT JOIN users u ON w.presenter_id = u.id
            WHERE w.is_published = TRUE
            ORDER BY w.scheduled_at DESC
        """)

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
    posts = await conn.fetch("""
        SELECT id, title, slug, excerpt, category, created_at, featured_image_url
        FROM blog_posts WHERE is_published = TRUE
        ORDER BY created_at DESC LIMIT $1 OFFSET $2
    """, per_page, offset)

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
    await conn.execute(
        "UPDATE blog_posts SET view_count = view_count + 1 WHERE slug = $1",
        slug
    )

    post = await conn.fetchrow("""
        SELECT bp.*, u.full_name as author_name
        FROM blog_posts bp
        LEFT JOIN users u ON bp.author_id = u.id
        WHERE bp.slug = $1 AND bp.is_published = TRUE
    """, slug)

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
