"""
Pipways Trading Platform API - Enterprise v3.0
Features: Redis caching, rate limiting, trade journal, analytics, course lessons, media library
"""

import os
import re
import jwt
import bcrypt
import asyncpg
import logging
import base64
import json
import csv
import io
import uuid
import redis
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Query, Request, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, EmailStr, Field, field_validator
from dotenv import load_dotenv
import httpx
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    RESET_TOKEN_EXPIRE_HOURS = 1
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@pipways.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    OPENROUTER_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "anthropic/claude-3.5-sonnet")
    CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "*")
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
    RATE_LIMIT_CHART = "5 per minute"
    RATE_LIMIT_MENTOR = "10 per minute"
    RATE_LIMIT_GENERAL = "100 per minute"
    
    @property
    def CORS_ORIGINS(self):
        if self.CORS_ORIGINS_STR == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",") if origin.strip()]

settings = Settings()

# Initialize Redis
redis_client = None

# Database pool
db_pool: Optional[asyncpg.Pool] = None

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool, redis_client
    try:
        # Initialize PostgreSQL
        db_pool = await asyncpg.create_pool(settings.DATABASE_URL, min_size=2, max_size=10)
        
        # Initialize Redis
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        
        await init_db()
        logger.info("Database and Redis initialized successfully")
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        raise
    yield
    if db_pool:
        await db_pool.close()
    if redis_client:
        redis_client.close()

app = FastAPI(title="Pipways API", version="3.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware - Keeping existing permissive settings
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

# Pydantic Models
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

class TradeEntry(BaseModel):
    pair: str = Field(..., min_length=1, max_length=20, pattern=r'^[A-Za-z0-9]+$')
    direction: str = Field(..., pattern="^(buy|sell)$")
    entry_price: float = Field(..., gt=0)
    exit_price: Optional[float] = Field(None, gt=0)
    stop_loss: Optional[float] = Field(None, gt=0)
    take_profit: Optional[float] = Field(None, gt=0)
    result_pips: Optional[float] = None
    result_profit: Optional[float] = None
    rr_ratio: Optional[float] = Field(None, ge=0)
    emotion: Optional[str] = Field(None, max_length=50)
    strategy: Optional[str] = Field(None, max_length=100)
    session: Optional[str] = Field(None, pattern="^(London|NY|Asian|Other)$")
    notes: Optional[str] = Field(None, max_length=2000)

class LessonCreate(BaseModel):
    course_id: int
    title: str = Field(..., min_length=1, max_length=255)
    video_url: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=1)
    order_index: int = Field(0, ge=0)
    duration_minutes: Optional[int] = Field(None, ge=1)

class ProgressUpdate(BaseModel):
    lesson_id: int
    completed: bool = False
    progress_percent: int = Field(0, ge=0, le=100)

class SignalCreate(BaseModel):
    pair: str = Field(..., min_length=1)
    direction: str = Field(..., pattern="^(buy|sell)$")
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timeframe: str = "1H"
    analysis: Optional[str] = None
    is_premium: bool = False

class BlogPostCreate(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = None
    is_premium: bool = False

class WebinarCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=1)
    is_premium: bool = False
    meeting_link: Optional[str] = None

class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    is_premium: bool = False

class MentorChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    context: Optional[str] = Field("", max_length=500)

# Database initialization
async def init_db():
    async with db_pool.acquire() as conn:
        # Existing tables check/creation with new additions
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
            CREATE TABLE IF NOT EXISTS blog_posts (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                excerpt TEXT,
                author_id INTEGER REFERENCES users(id),
                is_premium BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                content TEXT,
                is_premium BOOLEAN DEFAULT FALSE,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

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

        # NEW: Trade Journal Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS trade_journal (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                pair VARCHAR(20) NOT NULL,
                direction VARCHAR(10) CHECK (direction IN ('buy', 'sell')),
                entry_price DECIMAL(10,5) NOT NULL,
                exit_price DECIMAL(10,5),
                stop_loss DECIMAL(10,5),
                take_profit DECIMAL(10,5),
                result_pips DECIMAL(10,2),
                result_profit DECIMAL(10,2),
                rr_ratio DECIMAL(4,2),
                emotion VARCHAR(50),
                strategy VARCHAR(100),
                session VARCHAR(20),
                screenshot_url VARCHAR(500),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exit_date TIMESTAMP
            )
        """)

        # NEW: Course Lessons Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS course_lessons (
                id SERIAL PRIMARY KEY,
                course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                video_url VARCHAR(500),
                content TEXT,
                order_index INTEGER DEFAULT 0,
                duration_minutes INTEGER,
                is_premium BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # NEW: Course Progress Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS course_progress (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                lesson_id INTEGER REFERENCES course_lessons(id) ON DELETE CASCADE,
                completed BOOLEAN DEFAULT FALSE,
                progress_percent INTEGER DEFAULT 0,
                completed_at TIMESTAMP,
                UNIQUE(user_id, lesson_id)
            )
        """)

        # NEW: Media Library Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS media_files (
                id SERIAL PRIMARY KEY,
                file_url VARCHAR(500) NOT NULL,
                file_type VARCHAR(50),
                file_name VARCHAR(255),
                uploaded_by INTEGER REFERENCES users(id),
                file_size INTEGER,
                used_in VARCHAR(50),
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

# Rate limiting key function for authenticated users
def get_user_id(request: Request):
    auth = request.headers.get("authorization")
    if auth and auth.startswith("Bearer "):
        try:
            token = auth.split(" ")[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload.get("sub", get_remote_address(request))
        except:
            return get_remote_address(request)
    return get_remote_address(request)

# Auth endpoints
@app.post("/auth/register")
@limiter.limit(settings.RATE_LIMIT_GENERAL)
async def register(request: Request, user_data: UserRegister):
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

@app.post("/auth/login")
@limiter.limit(settings.RATE_LIMIT_GENERAL)
async def login(request: Request, credentials: UserLogin):
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
@limiter.limit(settings.RATE_LIMIT_GENERAL)
async def refresh_token(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
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

# Trade Journal Endpoints
@app.post("/journal/trades")
async def create_trade(
    trade: TradeEntry,
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("id") or current_user.get("sub"))
    
    async with db_pool.acquire() as conn:
        # Validate pair format (alphanumeric only)
        if not re.match(r'^[A-Za-z0-9]+$', trade.pair):
            raise HTTPException(status_code=400, detail="Invalid pair format")
            
        trade_id = await conn.fetchval("""
            INSERT INTO trade_journal 
            (user_id, pair, direction, entry_price, exit_price, stop_loss, take_profit, 
             result_pips, result_profit, rr_ratio, emotion, strategy, session, notes)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            RETURNING id
        """, user_id, trade.pair.upper(), trade.direction, trade.entry_price, 
             trade.exit_price, trade.stop_loss, trade.take_profit,
             trade.result_pips, trade.result_profit, trade.rr_ratio,
             trade.emotion, trade.strategy, trade.session, trade.notes)
        
        return {"id": trade_id, "message": "Trade recorded successfully"}

@app.get("/journal/trades")
async def get_trades(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("id") or current_user.get("sub"))
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM trade_journal 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2 OFFSET $3
        """, user_id, limit, offset)
        
        total = await conn.fetchval("""
            SELECT COUNT(*) FROM trade_journal WHERE user_id = $1
        """, user_id)
        
        return {"trades": [dict(row) for row in rows], "total": total}

@app.post("/journal/upload-csv")
async def upload_trade_csv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("id") or current_user.get("sub"))
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")
    
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    try:
        csv_content = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        required_fields = ['pair', 'direction', 'entry_price']
        inserted = 0
        errors = []
        
        async with db_pool.acquire() as conn:
            for idx, row in enumerate(csv_reader, 1):
                try:
                    # Validate required fields
                    if not all(field in row and row[field] for field in required_fields):
                        errors.append(f"Row {idx}: Missing required fields")
                        continue
                    
                    # Sanitize and validate
                    pair = re.sub(r'[^A-Za-z0-9]', '', row['pair']).upper()
                    direction = row['direction'].lower()
                    if direction not in ['buy', 'sell']:
                        errors.append(f"Row {idx}: Invalid direction")
                        continue
                    
                    entry_price = float(row['entry_price'])
                    
                    await conn.execute("""
                        INSERT INTO trade_journal 
                        (user_id, pair, direction, entry_price, exit_price, stop_loss, 
                         take_profit, result_pips, emotion, strategy, session)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    """, user_id, pair, direction, entry_price,
                         float(row.get('exit_price', 0)) if row.get('exit_price') else None,
                         float(row.get('stop_loss', 0)) if row.get('stop_loss') else None,
                         float(row.get('take_profit', 0)) if row.get('take_profit') else None,
                         float(row.get('result_pips', 0)) if row.get('result_pips') else None,
                         row.get('emotion', '')[:50],
                         row.get('strategy', '')[:100],
                         row.get('session', 'Other'))
                    
                    inserted += 1
                except Exception as e:
                    errors.append(f"Row {idx}: {str(e)}")
        
        return {"inserted": inserted, "errors": errors}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parsing error: {str(e)}")

@app.get("/journal/analytics")
async def get_trade_analytics(current_user: dict = Depends(get_current_user)):
    user_id = int(current_user.get("id") or current_user.get("sub"))
    
    # Check Redis cache first
    cache_key = f"analytics:{user_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    async with db_pool.acquire() as conn:
        # Overall stats
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN result_pips > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN result_pips < 0 THEN 1 ELSE 0 END) as losing_trades,
                AVG(result_pips) as avg_pips,
                AVG(rr_ratio) as avg_rr,
                SUM(result_profit) as total_profit
            FROM trade_journal 
            WHERE user_id = $1
        """, user_id)
        
        # Emotion analysis
        emotion_stats = await conn.fetch("""
            SELECT emotion, COUNT(*) as count, AVG(result_pips) as avg_pips
            FROM trade_journal 
            WHERE user_id = $1 AND emotion IS NOT NULL AND emotion != ''
            GROUP BY emotion
            ORDER BY count DESC
        """, user_id)
        
        # Strategy performance
        strategy_stats = await conn.fetch("""
            SELECT strategy, COUNT(*) as count, 
                   SUM(CASE WHEN result_pips > 0 THEN 1 ELSE 0 END) as wins
            FROM trade_journal 
            WHERE user_id = $1 AND strategy IS NOT NULL AND strategy != ''
            GROUP BY strategy
            ORDER BY count DESC
            LIMIT 5
        """, user_id)
        
        # Monthly performance
        monthly = await conn.fetch("""
            SELECT 
                DATE_TRUNC('month', created_at) as month,
                COUNT(*) as trades,
                SUM(result_pips) as net_pips
            FROM trade_journal 
            WHERE user_id = $1 AND created_at > NOW() - INTERVAL '6 months'
            GROUP BY DATE_TRUNC('month', created_at)
            ORDER BY month DESC
        """, user_id)
        
        result = {
            "overall": dict(stats) if stats else {},
            "emotions": [dict(row) for row in emotion_stats],
            "strategies": [dict(row) for row in strategy_stats],
            "monthly_performance": [dict(row) for row in monthly]
        }
        
        # Cache for 5 minutes
        redis_client.setex(cache_key, 300, json.dumps(result))
        return result

@app.post("/journal/analyze-performance")
@limiter.limit(settings.RATE_LIMIT_MENTOR)
async def analyze_performance(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """AI-powered trade performance analysis"""
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    user_id = int(current_user.get("id") or current_user.get("sub"))
    
    async with db_pool.acquire() as conn:
        # Get recent trades for analysis
        trades = await conn.fetch("""
            SELECT pair, direction, result_pips, emotion, strategy, session, created_at
            FROM trade_journal 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT 30
        """, user_id)
        
        if len(trades) < 5:
            return {"analysis": "Insufficient trade history. Please log at least 5 trades for meaningful analysis.", "trades_count": len(trades)}
        
        # Calculate metrics for AI context
        wins = sum(1 for t in trades if t['result_pips'] and t['result_pips'] > 0)
        losses = len(trades) - wins
        win_rate = (wins / len(trades)) * 100
        
        emotions = {}
        strategies = {}
        for t in trades:
            if t['emotion']:
                emotions[t['emotion']] = emotions.get(t['emotion'], 0) + 1
            if t['strategy']:
                strategies[t['strategy']] = strategies.get(t['strategy'], 0) + 1
        
        trade_data = {
            "total_trades": len(trades),
            "win_rate": round(win_rate, 2),
            "emotions": emotions,
            "strategies": strategies,
            "recent_trades": [dict(t) for t in trades[:10]]
        }
        
        prompt = f"""Analyze this trader's performance data and provide professional feedback:
        
Trade Statistics:
- Total Recent Trades: {trade_data['total_trades']}
- Win Rate: {trade_data['win_rate']}%
- Emotional States: {json.dumps(trade_data['emotions'])}
- Strategies Used: {json.dumps(trade_data['strategies'])}

Provide analysis in this exact format:

TRADER PROFILE: [e.g., Impulsive Trader, Disciplined Trader, Overtrader]
WIN RATE: {trade_data['win_rate']}%
RISK DISCIPLINE SCORE: [High/Medium/Low with brief justification]
CONSISTENCY SCORE: [Estimate percentage based on strategy variety and emotion stability]

BEHAVIORAL PATTERNS:
- [Pattern 1 with evidence]
- [Pattern 2 with evidence]
- [Pattern 3 if applicable]

STRENGTHS:
- [Strength 1]
- [Strength 2]

AREAS FOR IMPROVEMENT:
- [Specific actionable advice 1]
- [Specific actionable advice 2]
- [Specific actionable advice 3]

RECOMMENDATION:
[2-3 sentence actionable trading plan adjustment]"""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://pipways.com",
                    "X-Title": "Pipways Performance Analysis"
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="AI analysis failed")
            
            result = response.json()
            analysis = result["choices"][0]["message"]["content"]
            
            return {
                "analysis": analysis,
                "statistics": trade_data,
                "timestamp": datetime.utcnow().isoformat()
            }

# Course Lessons Endpoints
@app.get("/courses/{course_id}/lessons")
async def get_course_lessons(
    course_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    async with db_pool.acquire() as conn:
        # Check course exists and access
        course = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        tier = current_user.get("subscription_tier", "free") if current_user else "free"
        if course['is_premium'] and tier == "free":
            raise HTTPException(status_code=403, detail="Premium content requires subscription")
        
        lessons = await conn.fetch("""
            SELECT * FROM course_lessons 
            WHERE course_id = $1 
            ORDER BY order_index ASC
        """, course_id)
        
        # Get progress if authenticated
        if current_user:
            user_id = int(current_user.get("id") or current_user.get("sub"))
            progress = await conn.fetch("""
                SELECT lesson_id, completed, progress_percent 
                FROM course_progress 
                WHERE user_id = $1 AND lesson_id = ANY($2)
            """, user_id, [l['id'] for l in lessons])
            
            progress_map = {p['lesson_id']: p for p in progress}
            
            lessons_with_progress = []
            for lesson in lessons:
                lesson_dict = dict(lesson)
                if lesson['id'] in progress_map:
                    lesson_dict['progress'] = dict(progress_map[lesson['id']])
                else:
                    lesson_dict['progress'] = {"completed": False, "progress_percent": 0}
                lessons_with_progress.append(lesson_dict)
            
            return {"lessons": lessons_with_progress}
        
        return {"lessons": [dict(l) for l in lessons]}

@app.post("/courses/lessons/progress")
async def update_lesson_progress(
    progress: ProgressUpdate,
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("id") or current_user.get("sub"))
    
    async with db_pool.acquire() as conn:
        # Verify lesson exists
        lesson = await conn.fetchrow("SELECT id FROM course_lessons WHERE id = $1", progress.lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        completed_at = datetime.utcnow() if progress.completed else None
        
        await conn.execute("""
            INSERT INTO course_progress (user_id, lesson_id, completed, progress_percent, completed_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id, lesson_id) 
            DO UPDATE SET completed = $3, progress_percent = $4, completed_at = $5
        """, user_id, progress.lesson_id, progress.completed, progress.progress_percent, completed_at)
        
        # Clear analytics cache when progress updates
        redis_client.delete(f"analytics:{user_id}")
        
        return {"message": "Progress updated"}

@app.post("/admin/lessons")
async def create_lesson(
    lesson: LessonCreate,
    admin: dict = Depends(get_admin_user)
):
    async with db_pool.acquire() as conn:
        lesson_id = await conn.fetchval("""
            INSERT INTO course_lessons (course_id, title, video_url, content, order_index, duration_minutes, is_premium)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """, lesson.course_id, lesson.title, lesson.video_url, lesson.content, 
             lesson.order_index, lesson.duration_minutes, True)
        
        return {"id": lesson_id, "message": "Lesson created"}

# Media Library Endpoints
@app.post("/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    used_in: str = Form("general"),
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("id") or current_user.get("sub"))
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'video/mp4', 'application/pdf']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed")
    
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
    
    # Generate unique filename
    ext = file.filename.split('.')[-1]
    unique_name = f"{uuid.uuid4()}.{ext}"
    
    # In production, upload to S3/Cloudinary here
    # For now, save to local storage and return path
    upload_dir = "/tmp/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_name)
    
    with open(file_path, "wb") as f:
        f.write(contents)
    
    file_url = f"/media/{unique_name}"
    
    async with db_pool.acquire() as conn:
        media_id = await conn.fetchval("""
            INSERT INTO media_files (file_url, file_type, file_name, uploaded_by, file_size, used_in)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """, file_url, file.content_type, file.filename, user_id, len(contents), used_in)
        
        return {
            "id": media_id,
            "url": file_url,
            "filename": file.filename,
            "size": len(contents)
        }

@app.get("/media")
async def list_media(
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT m.*, u.full_name as uploaded_by_name
            FROM media_files m
            JOIN users u ON m.uploaded_by = u.id
            ORDER BY m.created_at DESC
            LIMIT $1 OFFSET $2
        """, limit, offset)
        
        return {"media": [dict(row) for row in rows]}

# Admin endpoints
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
async def update_user_role(
    user_id: int, 
    role: str = Query(..., pattern="^(user|admin|moderator)$"), 
    admin: dict = Depends(get_admin_user)
):
    admin_id = admin.get("id") or admin.get("sub")
    if str(admin_id) == str(user_id) and role != "admin":
        raise HTTPException(status_code=400, detail="Cannot demote yourself")

    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        await conn.execute(
            "UPDATE users SET role = $1, updated_at = NOW() WHERE id = $2",
            role, user_id
        )
        return {"message": f"User role updated to {role}"}

@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, admin: dict = Depends(get_admin_user)):
    admin_id = admin.get("id") or admin.get("sub")
    if str(admin_id) == str(user_id):
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}

@app.post("/admin/users/{user_id}/toggle-subscription")
async def toggle_subscription(
    user_id: int,
    tier: str = Query(..., pattern="^(free|premium|vip)$"),
    status: str = Query(..., pattern="^(active|inactive|cancelled)$"),
    admin: dict = Depends(get_admin_user)
):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        await conn.execute("""
            UPDATE users 
            SET subscription_tier = $1, subscription_status = $2, updated_at = NOW()
            WHERE id = $3
        """, tier, status, user_id)

        return {"message": f"Subscription updated to {tier} ({status})"}

@app.get("/admin/stats")
async def get_admin_stats(admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users") or 0
        total_signals = await conn.fetchval("SELECT COUNT(*) FROM signals") or 0
        active_signals = await conn.fetchval("SELECT COUNT(*) FROM signals WHERE status = 'active'") or 0
        premium_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE subscription_tier IN ('premium', 'vip')") or 0
        total_trades = await conn.fetchval("SELECT COUNT(*) FROM trade_journal") or 0
        total_courses = await conn.fetchval("SELECT COUNT(*) FROM courses") or 0

        return {
            "total_users": total_users,
            "total_signals": total_signals,
            "active_signals": active_signals,
            "premium_users": premium_users,
            "total_trades": total_trades,
            "total_courses": total_courses,
            "conversion_rate": round((premium_users / total_users * 100), 2) if total_users > 0 else 0
        }

# Signals
@app.get("/signals")
async def get_signals(
    status: Optional[str] = Query(None),
    pair: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    try:
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

            query += " ORDER BY created_at DESC"
            query += f" LIMIT ${len(params)+1}"
            params.append(limit)

            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/signals")
async def create_signal(signal: SignalCreate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        admin_id = admin.get("id") or admin.get("sub")
        signal_id = await conn.fetchval("""
            INSERT INTO signals (pair, direction, entry_price, stop_loss, take_profit, timeframe, analysis, is_premium, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """, signal.pair, signal.direction, signal.entry_price, signal.stop_loss,
             signal.take_profit, signal.timeframe, signal.analysis, signal.is_premium, admin_id)

        return {"id": signal_id, "message": "Signal created successfully"}

@app.put("/signals/{signal_id}/close")
async def close_signal(
    signal_id: int,
    pips_gain: float,
    admin: dict = Depends(get_admin_user)
):
    async with db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE signals 
            SET status = 'closed', pips_gain = $1, closed_at = NOW(), updated_at = NOW()
            WHERE id = $2
        """, pips_gain, signal_id)
        return {"message": "Signal closed"}

# Enhanced AI Analysis with Rate Limiting
@app.post("/analyze/chart")
@limiter.limit(settings.RATE_LIMIT_CHART)
async def analyze_chart(
    request: Request,
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
        if len(contents) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large")

        image_base64 = base64.b64encode(contents).decode()

        prompt = f"""You are an expert forex/crypto technical analyst. Analyze this {pair} chart on {timeframe} timeframe.

Context provided by user: {additional_info}

Provide your analysis in this exact JSON structure:
{{
  "summary": "Brief technical overview of market structure and key levels",
  "signal": "BUY or SELL or NO TRADE",
  "entry_zone": "Specific price range (e.g., 1.0850-1.0860)",
  "stop_loss": "Exact price level",
  "take_profit": ["TP1 price", "TP2 price"],
  "risk_reward": "Ratio like 1:3",
  "confidence": "Percentage like 75%",
  "market_structure": "Bullish/Bearish/Consolidation with explanation",
  "support_resistance": {{
    "support": ["S1 price", "S2 price"],
    "resistance": ["R1 price", "R2 price"]
  }},
  "key_observations": "Specific patterns, candlestick formations, or indicator signals visible"
}}

Rules:
1. Be specific with price levels visible in the chart
2. Calculate realistic risk/reward based on visible price action
3. If no clear setup, return signal as "NO TRADE" with explanation
4. Confidence should reflect chart clarity (don't always say 90%)
5. Ensure valid JSON format - no markdown, no extra text outside JSON"""

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

            if response.status_code == 404:
                logger.error(f"OpenRouter model not found: {settings.OPENROUTER_VISION_MODEL}")
                raise HTTPException(status_code=503, detail="AI vision model not available")

            if response.status_code != 200:
                logger.error(f"OpenRouter error: {response.text}")
                raise HTTPException(status_code=500, detail=f"AI service error: {response.status_code}")

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
                    "timeframe": timeframe,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Failed to parse AI JSON response: {e}")
                return {
                    "analysis": ai_response,
                    "image_base64": image_base64,
                    "pair": pair,
                    "timeframe": timeframe,
                    "timestamp": datetime.utcnow().isoformat(),
                    "parse_warning": "AI returned unstructured data"
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced AI Mentor with Trade History Context and Rate Limiting
@app.post("/mentor/chat")
@limiter.limit(settings.RATE_LIMIT_MENTOR)
async def mentor_chat(
    request: Request,
    mentor_request: MentorChatRequest,
    current_user: dict = Depends(get_current_user)
):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    try:
        user_id = int(current_user.get("id") or current_user.get("sub"))
        
        async with db_pool.acquire() as conn:
            # Get user's recent trade history for context
            trades = await conn.fetch("""
                SELECT pair, direction, result_pips, emotion, strategy, created_at
                FROM trade_journal 
                WHERE user_id = $1 
                ORDER BY created_at DESC 
                LIMIT 10
            """, user_id)
            
            # Get course progress
            progress = await conn.fetch("""
                SELECT c.title, COUNT(l.id) as total_lessons,
                       COUNT(p.id) as completed_lessons
                FROM courses c
                JOIN course_lessons l ON c.id = l.course_id
                LEFT JOIN course_progress p ON l.id = p.lesson_id AND p.user_id = $1 AND p.completed = TRUE
                GROUP BY c.id, c.title
                LIMIT 3
            """, user_id)
            
            # Build context
            trade_context = ""
            if trades:
                wins = sum(1 for t in trades if t['result_pips'] and t['result_pips'] > 0)
                recent_emotions = list(set([t['emotion'] for t in trades if t['emotion']]))[:3]
                trade_context = f"""
User's Recent Trading History:
- Recent Win Rate: {(wins/len(trades)*100):.1f}% ({wins}/{len(trades)})
- Recent Emotions: {', '.join(recent_emotions) if recent_emotions else 'Not logged'}
- Recent Activity: {len(trades)} trades logged
"""
            
            course_context = ""
            if progress:
                course_context = "Course Progress:\n" + "\n".join([
                    f"- {p['title']}: {p['completed_lessons']}/{p['total_lessons']} lessons" 
                    for p in progress
                ])

            system_prompt = f"""You are a professional forex and crypto trading mentor with 15+ years of experience. 

CURRENT USER CONTEXT:
{trade_context}
{course_context}

CORE PRINCIPLES:
1. RISK MANAGEMENT FIRST: Always emphasize position sizing (1-2% risk per trade), stop losses
2. PSYCHOLOGY MATTERS: Address emotional control based on user's logged emotions
3. ACTIONABLE ADVICE: Give specific, practical guidance with concrete examples
4. CONTEXT-AWARE: Reference their trade history and course progress when relevant
5. NON-JUDGMENTAL: Encourage learning from losses, celebrate wins appropriately

When discussing their specific trades:
- Reference patterns you see in their history (e.g., "I notice you tend to...")
- Suggest specific improvements based on their actual performance
- If they show emotional trading patterns, address them gently

Tone: Professional, encouraging but firm on risk management, personalized based on their history."""

            # Get chat history
            history = await conn.fetch("""
                SELECT message, response FROM chat_history 
                WHERE user_id = $1 
                ORDER BY created_at DESC 
                LIMIT 5
            """, user_id)

            messages = [{"role": "system", "content": system_prompt}]

            for row in reversed(history):
                messages.append({"role": "user", "content": row["message"]})
                messages.append({"role": "assistant", "content": row["response"]})

            messages.append({
                "role": "user",
                "content": f"Question: {mentor_request.message}\nAdditional Context: {mentor_request.context}"
            })

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
                        "max_tokens": 1200,
                        "temperature": 0.7
                    }
                )

                if response.status_code == 404:
                    raise HTTPException(status_code=503, detail="AI mentor model not available")

                if response.status_code != 200:
                    raise HTTPException(status_code=500, detail=f"AI service error: {response.status_code}")

                result = response.json()
                ai_response = result["choices"][0]["message"]["content"]

                await conn.execute("""
                    INSERT INTO chat_history (user_id, message, response, context)
                    VALUES ($1, $2, $3, $4)
                """, user_id, mentor_request.message, ai_response, mentor_request.context)

                return {"response": ai_response, "timestamp": datetime.utcnow().isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mentor chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Content Management
@app.get("/blog/posts")
async def get_blog_posts(
    limit: int = Query(10, le=50),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    try:
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database not initialized")
            
        async with db_pool.acquire() as conn:
            query_parts = ["SELECT * FROM blog_posts"]
            params = []
            
            tier = current_user.get("subscription_tier", "free") if current_user else "free"
            if tier == "free":
                query_parts.append("WHERE is_premium = FALSE")
            
            query_parts.append("ORDER BY created_at DESC")
            query_parts.append(f"LIMIT ${len(params)+1}")
            params.append(limit)
            
            query = " ".join(query_parts)
            rows = await conn.fetch(query, *params)
            
            if not rows:
                return []
                
            return [dict(row) for row in rows]
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching blog posts: {e}")
        raise HTTPException(status_code=500, detail="Failed to load blog posts")

@app.post("/blog/posts")
async def create_blog_post(post: BlogPostCreate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        admin_id = admin.get("id") or admin.get("sub")
        post_id = await conn.fetchval("""
            INSERT INTO blog_posts (title, content, excerpt, author_id, is_premium)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, post.title, post.content, post.excerpt or post.content[:200], admin_id, post.is_premium)
        return {"id": post_id, "message": "Blog post created"}

@app.get("/webinars")
async def get_webinars(
    limit: int = Query(20, le=100),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    try:
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database not initialized")
            
        async with db_pool.acquire() as conn:
            query_parts = ["SELECT * FROM webinars WHERE scheduled_at > NOW()"]
            params = []
            
            tier = current_user.get("subscription_tier", "free") if current_user else "free"
            if tier == "free":
                query_parts.append("AND is_premium = FALSE")
            
            query_parts.append("ORDER BY scheduled_at ASC")
            query_parts.append(f"LIMIT ${len(params)+1}")
            params.append(limit)
            
            query = " ".join(query_parts)
            rows = await conn.fetch(query, *params)
            
            return [dict(row) for row in rows] if rows else []
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching webinars: {e}")
        raise HTTPException(status_code=500, detail="Failed to load webinars")

@app.post("/webinars")
async def create_webinar(webinar: WebinarCreate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        admin_id = admin.get("id") or admin.get("sub")
        webinar_id = await conn.fetchval("""
            INSERT INTO webinars (title, description, scheduled_at, duration_minutes, meeting_link, is_premium, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """, webinar.title, webinar.description, webinar.scheduled_at, 
             webinar.duration_minutes, webinar.meeting_link, webinar.is_premium, admin_id)
        return {"id": webinar_id, "message": "Webinar created"}

@app.get("/courses")
async def get_courses(
    limit: int = Query(20, le=100),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    try:
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database not initialized")
            
        async with db_pool.acquire() as conn:
            query_parts = ["SELECT * FROM courses"]
            params = []
            
            tier = current_user.get("subscription_tier", "free") if current_user else "free"
            if tier == "free":
                query_parts.append("WHERE is_premium = FALSE")
            
            query_parts.append("ORDER BY created_at DESC")
            query_parts.append(f"LIMIT ${len(params)+1}")
            params.append(limit)
            
            query = " ".join(query_parts)
            rows = await conn.fetch(query, *params)
            
            return [dict(row) for row in rows] if rows else []
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching courses: {e}")
        raise HTTPException(status_code=500, detail="Failed to load courses")

@app.post("/courses")
async def create_course(course: CourseCreate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        admin_id = admin.get("id") or admin.get("sub")
        course_id = await conn.fetchval("""
            INSERT INTO courses (title, description, content, is_premium, created_by)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, course.title, course.description, course.content, course.is_premium, admin_id)
        return {"id": course_id, "message": "Course created"}

@app.get("/config")
async def get_config():
    return {
        "features": {
            "ai_analysis": bool(settings.OPENROUTER_API_KEY),
            "mentor_chat": bool(settings.OPENROUTER_API_KEY),
            "auth_required": True
        }
    }

@app.get("/health")
async def health_check():
    db_status = "connected" if db_pool else "disconnected"
    redis_status = "connected" if redis_client and redis_client.ping() else "disconnected"
    return {
        "status": "healthy", 
        "database": db_status,
        "redis": redis_status,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
