"""
Pipways Trading Platform API - Complete Production Version
Features: Auth, Roles (Admin/Mod/User), AI Integration, Admin Dashboard
"""

import os
import sys
import traceback
import jwt
import bcrypt
import asyncpg
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Query, Request, status
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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

# Verify critical settings
if not settings.DATABASE_URL:
    logger.error("CRITICAL: DATABASE_URL not set!")
if not settings.OPENROUTER_API_KEY:
    logger.warning("WARNING: OPENROUTER_API_KEY not set - AI features will fail")

# Database pool
db_pool: Optional[asyncpg.Pool] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    try:
        logger.info("Connecting to database...")
        db_pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=2,
            max_size=20,
            command_timeout=60
        )
        logger.info("Database connected successfully")
        await init_db()
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.error(traceback.format_exc())
    yield
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")

app = FastAPI(
    title="Pipways API",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENV") != "production" else None
)

# CORS Middleware - MUST BE FIRST
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Global error handler
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except HTTPException as he:
        logger.warning(f"HTTP Exception {he.status_code}: {he.detail}")
        return JSONResponse(
            status_code=he.status_code,
            content={"detail": he.detail, "type": "http_error"}
        )
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error": str(e), "type": type(e).__name__}
        )

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

class UserUpdateRole(BaseModel):
    role: str = Field(..., pattern="^(user|moderator|admin)$")

class UserUpdateSubscription(BaseModel):
    tier: str = Field(..., pattern="^(free|premium|vip)$")
    status: str = Field(..., pattern="^(active|inactive|cancelled)$")

class SignalCreate(BaseModel):
    pair: str = Field(..., min_length=1, max_length=20)
    direction: str = Field(..., pattern="^(buy|sell)$")
    entry_price: float = Field(..., gt=0)
    stop_loss: Optional[float] = Field(None, gt=0)
    take_profit: Optional[float] = Field(None, gt=0)
    take_profit_2: Optional[float] = Field(None, gt=0)
    timeframe: str = Field(default="1H", pattern="^(1M|5M|15M|30M|1H|4H|D1|W1)$")
    analysis: Optional[str] = Field(None, max_length=2000)
    is_premium: bool = False
    risk_percent: float = Field(default=1.0, ge=0.1, le=5.0)

class SignalClose(BaseModel):
    pips_gain: float

class BlogPostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = Field(None, max_length=500)
    is_premium: bool = False

class WebinarCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=15, le=180)
    is_premium: bool = False
    meeting_link: Optional[str] = Field(None, max_length=500)

class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    is_premium: bool = False

class MentorChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    context: Optional[str] = Field(None, max_length=500)

# ==========================================
# DATABASE INITIALIZATION & MIGRATIONS
# ==========================================

async def init_db():
    """Initialize database with auto-migration support"""
    if not db_pool:
        raise Exception("Database pool not initialized")
    
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add columns if missing (migrations)
        await add_column_if_not_exists(conn, 'users', 'last_login', 'TIMESTAMP')
        await add_column_if_not_exists(conn, 'users', 'reset_token', 'VARCHAR(255)')
        await add_column_if_not_exists(conn, 'users', 'reset_token_expires', 'TIMESTAMP')
        await add_column_if_not_exists(conn, 'users', 'created_by', 'INTEGER REFERENCES users(id)')
        
        # Signals table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id SERIAL PRIMARY KEY,
                pair VARCHAR(20) NOT NULL,
                direction VARCHAR(10) NOT NULL,
                entry_price DECIMAL(15,5) NOT NULL,
                stop_loss DECIMAL(15,5),
                take_profit DECIMAL(15,5),
                take_profit_2 DECIMAL(15,5),
                timeframe VARCHAR(10) DEFAULT '1H',
                analysis TEXT,
                status VARCHAR(20) DEFAULT 'active',
                pips_gain DECIMAL(10,2),
                risk_percent DECIMAL(5,2) DEFAULT 1.0,
                is_premium BOOLEAN DEFAULT FALSE,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP
            )
        """)
        
        # Blog posts
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
        
        # Webinars
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS webinars (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                scheduled_at TIMESTAMP NOT NULL,
                duration_minutes INTEGER DEFAULT 60,
                meeting_link VARCHAR(500),
                is_premium BOOLEAN DEFAULT FALSE,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Courses
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                content TEXT NOT NULL,
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
        
        # Create default admin
        await create_default_admin(conn)
        logger.info("Database initialized successfully")

async def add_column_if_not_exists(conn, table, column, datatype):
    """Add column if it doesn't exist (migration helper)"""
    try:
        result = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name=$1 AND column_name=$2
        """, table, column)
        
        if not result:
            await conn.execute(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {datatype}')
            logger.info(f"Added column {column} to {table}")
    except Exception as e:
        logger.error(f"Error adding column {column}: {e}")

async def create_default_admin(conn):
    """Create default admin user"""
    try:
        admin_exists = await conn.fetchval("SELECT id FROM users WHERE email = $1", settings.ADMIN_EMAIL)
        if not admin_exists:
            hashed = bcrypt.hashpw(settings.ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
            await conn.execute("""
                INSERT INTO users (email, password_hash, full_name, role, subscription_tier, subscription_status, email_verified)
                VALUES ($1, $2, $3, 'admin', 'vip', 'active', TRUE)
            """, settings.ADMIN_EMAIL, hashed, "System Administrator")
            logger.info(f"Admin created: {settings.ADMIN_EMAIL}")
    except Exception as e:
        logger.error(f"Error creating admin: {e}")

# ==========================================
# AUTH UTILITIES
# ==========================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except Exception:
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

def create_reset_token():
    import secrets
    return secrets.token_urlsafe(32)

# ==========================================
# ROLE & AUTH DEPENDENCIES
# ==========================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
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
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

async def require_moderator(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Moderator access required")
    return current_user

def check_premium_access(user: dict, content_is_premium: bool):
    """Check if user can access premium content"""
    if not content_is_premium:
        return True
    if user["subscription_tier"] in ["premium", "vip"] and user["subscription_status"] == "active":
        return True
    return False

# ==========================================
# AUTH ENDPOINTS
# ==========================================

@app.post("/auth/register")
async def register(user_data: UserRegister):
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
        
        access_token = create_access_token({"sub": str(user_id), "role": "user"})
        refresh_token = create_refresh_token({"sub": str(user_id)})
        
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": dict(user)
        }

@app.post("/auth/login")
async def login(credentials: UserLogin):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", credentials.email)
        if not user or not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Update last login (wrapped in try for safety)
        try:
            await conn.execute("UPDATE users SET last_login = NOW() WHERE id = $1", user["id"])
        except Exception as e:
            logger.warning(f"Could not update last_login: {e}")
        
        access_token = create_access_token({"sub": str(user["id"]), "role": user["role"]})
        refresh_token = create_refresh_token({"sub": str(user["id"])})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": dict(user)
        }

@app.post("/auth/refresh")
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("sub")
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", int(user_id))
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            
            new_access = create_access_token({"sub": str(user_id), "role": user["role"]})
            return {"access_token": new_access, "token_type": "bearer"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/auth/forgot-password")
async def forgot_password(request: Request):
    data = await request.json()
    email = data.get("email")
    
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
        if not user:
            return {"message": "If email exists, reset link sent"}
        
        reset_token = create_reset_token()
        expires = datetime.utcnow() + timedelta(hours=settings.RESET_TOKEN_EXPIRE_HOURS)
        
        await conn.execute("""
            UPDATE users SET reset_token = $1, reset_token_expires = $2 WHERE id = $3
        """, reset_token, expires, user["id"])
        
        reset_url = f"https://pipways-web-nhem.onrender.com?reset_token={reset_token}"
        logger.info(f"Reset URL for {email}: {reset_url}")
        
        return {"message": "If email exists, reset link sent"}

@app.post("/auth/reset-password")
async def reset_password(request: Request):
    data = await request.json()
    token = data.get("token")
    new_password = data.get("new_password")
    
    # Validate password
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password too short")
    
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("""
            SELECT * FROM users 
            WHERE reset_token = $1 AND reset_token_expires > NOW()
        """, token)
        
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
        
        hashed_pw = get_password_hash(new_password)
        await conn.execute("""
            UPDATE users 
            SET password_hash = $1, reset_token = NULL, reset_token_expires = NULL, updated_at = NOW()
            WHERE id = $2
        """, hashed_pw, user["id"])
        
        return {"message": "Password reset successful"}

@app.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Logged out successfully"}

# ==========================================
# ADMIN DASHBOARD ENDPOINTS
# ==========================================

@app.get("/admin/stats")
async def get_admin_stats(admin: dict = Depends(require_admin)):
    async with db_pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        total_signals = await conn.fetchval("SELECT COUNT(*) FROM signals")
        active_signals = await conn.fetchval("SELECT COUNT(*) FROM signals WHERE status = 'active'")
        premium_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE subscription_tier IN ('premium', 'vip')")
        free_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE subscription_tier = 'free'")
        moderator_count = await conn.fetchval("SELECT COUNT(*) FROM users WHERE role = 'moderator'")
        
        # Conversion rate
        conversion_rate = round((premium_users / total_users * 100), 2) if total_users > 0 else 0
        
        return {
            "total_users": total_users,
            "free_users": free_users,
            "premium_users": premium_users,
            "moderators": moderator_count,
            "total_signals": total_signals,
            "active_signals": active_signals,
            "conversion_rate": conversion_rate
        }

@app.get("/admin/users")
async def get_all_users(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin)
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
            
        if tier:
            where_clauses.append(f"subscription_tier = ${len(params)+1}")
            params.append(tier)
        
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
    role_data: UserUpdateRole,
    admin: dict = Depends(require_admin)
):
    # Prevent self-demotion if you're the only admin
    async with db_pool.acquire() as conn:
        if int(admin["id"]) == user_id and role_data.role != "admin":
            # Check if there are other admins
            admin_count = await conn.fetchval("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            if admin_count <= 1:
                raise HTTPException(status_code=400, detail="Cannot demote yourself - you are the only admin")
        
        # Moderators cannot create admins
        if admin["role"] == "moderator" and role_data.role == "admin":
            raise HTTPException(status_code=403, detail="Moderators cannot promote users to Admin")
        
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        await conn.execute(
            "UPDATE users SET role = $1, updated_at = NOW() WHERE id = $2",
            role_data.role, user_id
        )
        return {"message": f"User role updated to {role_data.role}"}

@app.put("/admin/users/{user_id}/subscription")
async def update_user_subscription(
    user_id: int,
    sub_data: UserUpdateSubscription,
    admin: dict = Depends(require_moderator)  # Mods can do this too
):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Moderators cannot modify admin subscriptions
        if user["role"] == "admin" and admin["role"] != "admin":
            raise HTTPException(status_code=403, detail="Cannot modify admin subscriptions")
        
        await conn.execute("""
            UPDATE users 
            SET subscription_tier = $1, subscription_status = $2, updated_at = NOW()
            WHERE id = $3
        """, sub_data.tier, sub_data.status, user_id)
        
        return {"message": f"Subscription updated to {sub_data.tier} ({sub_data.status})"}

@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, admin: dict = Depends(require_admin)):
    if int(admin["id"]) == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT role FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user["role"] == "admin":
            raise HTTPException(status_code=403, detail="Cannot delete admin users")
        
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        return {"message": "User deleted successfully"}

# ==========================================
# TRADING SIGNALS
# ==========================================

@app.get("/signals")
async def get_signals(
    status: Optional[str] = Query(None),
    pair: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    current_user: dict = Depends(get_current_user)
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
        
        query += " ORDER BY created_at DESC"
        query += f" LIMIT ${len(params)+1}"
        params.append(limit)
        
        rows = await conn.fetch(query, *params)
        
        # Process signals - redact sensitive data for free users on premium signals
        signals = []
        for row in rows:
            signal = dict(row)
            is_premium_signal = signal.get("is_premium", False)
            
            if is_premium_signal and not check_premium_access(current_user, True):
                # Redact sensitive data for free users
                signal["entry_price"] = None
                signal["stop_loss"] = None
                signal["take_profit"] = None
                signal["take_profit_2"] = None
                signal["analysis"] = "🔒 Upgrade to Premium to view this signal"
                signal["locked"] = True
            else:
                signal["locked"] = False
            
            signals.append(signal)
        
        return signals

@app.post("/signals")
async def create_signal(signal: SignalCreate, mod: dict = Depends(require_moderator)):
    async with db_pool.acquire() as conn:
        signal_id = await conn.fetchval("""
            INSERT INTO signals (pair, direction, entry_price, stop_loss, take_profit, take_profit_2, timeframe, analysis, is_premium, risk_percent, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
        """, signal.pair, signal.direction, signal.entry_price, signal.stop_loss,
             signal.take_profit, signal.take_profit_2, signal.timeframe, signal.analysis, 
             signal.is_premium, signal.risk_percent, mod["id"])
        
        return {"id": signal_id, "message": "Signal created successfully"}

@app.put("/signals/{signal_id}/close")
async def close_signal(signal_id: int, close_data: SignalClose, mod: dict = Depends(require_moderator)):
    async with db_pool.acquire() as conn:
        signal = await conn.fetchrow("SELECT * FROM signals WHERE id = $1", signal_id)
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        await conn.execute("""
            UPDATE signals 
            SET status = 'closed', pips_gain = $1, closed_at = NOW(), updated_at = NOW()
            WHERE id = $2
        """, close_data.pips_gain, signal_id)
        return {"message": "Signal closed successfully"}

# ==========================================
# AI ANALYSIS (FIXED OPENROUTER INTEGRATION)
# ==========================================

@app.post("/analyze/chart")
async def analyze_chart(
    file: UploadFile = File(...),
    pair: Optional[str] = Form("Unknown"),
    timeframe: Optional[str] = Form("1H"),
    additional_info: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    # Check file size (10MB limit)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
    
    # Verify image type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    image_base64 = base64.b64encode(contents).decode()
    
    prompt = f"""Analyze this forex/crypto chart for {pair} on {timeframe} timeframe.
Additional context: {additional_info or 'None'}

Provide analysis in this format:
- Trend Direction (Bullish/Bearish/Neutral)
- Key Support Levels
- Key Resistance Levels  
- Entry Suggestion (if any)
- Risk Management advice
- Confidence Level (1-10)"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://pipways.com",
                    "X-Title": "Pipways AI Analysis",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.OPENROUTER_VISION_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{file.content_type};base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ]
                }
            )
            
            if response.status_code != 200:
                logger.error(f"OpenRouter error: {response.text}")
                raise HTTPException(status_code=500, detail="AI service error")
            
            result = response.json()
            
            if "choices" not in result or not result["choices"]:
                logger.error(f"Unexpected OpenRouter response: {result}")
                raise HTTPException(status_code=500, detail="Invalid AI response")
            
            analysis = result["choices"][0]["message"]["content"]
            
            return {
                "success": True,
                "analysis": analysis,
                "pair": pair,
                "timeframe": timeframe,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI analysis timed out")
    except Exception as e:
        logger.error(f"AI Analysis error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/mentor/chat")
async def mentor_chat(
    message: MentorChatMessage,
    current_user: dict = Depends(get_current_user)
):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    async with db_pool.acquire() as conn:
        # Get last 5 messages for context
        history = await conn.fetch("""
            SELECT message, response FROM chat_history 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT 5
        """, current_user["id"])
        
        messages = []
        # Add system message
        messages.append({
            "role": "system",
            "content": "You are an expert forex trading mentor. Provide clear, actionable advice. Be encouraging but realistic about risks. Keep responses concise (under 200 words)."
        })
        
        # Add history (oldest first)
        for row in reversed(history):
            messages.append({"role": "user", "content": row["message"]})
            messages.append({"role": "assistant", "content": row["response"]})
        
        # Add current message with context
        context_prompt = f"{message.message}"
        if message.context:
            context_prompt += f"\n\nContext: {message.context}"
        
        messages.append({"role": "user", "content": context_prompt})
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        "HTTP-Referer": "https://pipways.com",
                        "X-Title": "Pipways AI Mentor",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": settings.OPENROUTER_MODEL,
                        "messages": messages
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"OpenRouter chat error: {response.text}")
                    raise HTTPException(status_code=500, detail="AI service error")
                
                result = response.json()
                ai_response = result["choices"][0]["message"]["content"]
                
                # Save to history
                await conn.execute("""
                    INSERT INTO chat_history (user_id, message, response, context)
                    VALUES ($1, $2, $3, $4)
                """, current_user["id"], message.message, ai_response, message.context)
                
                return {
                    "success": True,
                    "response": ai_response,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="AI mentor timed out")
        except Exception as e:
            logger.error(f"Mentor chat error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

# ==========================================
# CONTENT MANAGEMENT (BLOG, WEBINARS, COURSES)
# ==========================================

@app.get("/blog/posts")
async def get_blog_posts(
    limit: int = Query(10, le=50),
    current_user: dict = Depends(get_current_user)
):
    async with db_pool.acquire() as conn:
        query = """
            SELECT bp.*, u.full_name as author_name 
            FROM blog_posts bp
            LEFT JOIN users u ON bp.author_id = u.id
            ORDER BY bp.created_at DESC 
            LIMIT $1
        """
        rows = await conn.fetch(query, limit)
        
        posts = []
        for row in rows:
            post = dict(row)
            if post["is_premium"] and not check_premium_access(current_user, True):
                post["content"] = "🔒 This is premium content. Upgrade to access."
                post["locked"] = True
            else:
                post["locked"] = False
            posts.append(post)
        
        return posts

@app.post("/blog/posts")
async def create_blog_post(post: BlogPostCreate, mod: dict = Depends(require_moderator)):
    async with db_pool.acquire() as conn:
        post_id = await conn.fetchval("""
            INSERT INTO blog_posts (title, content, excerpt, author_id, is_premium)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, post.title, post.content, post.excerpt or post.content[:200], mod["id"], post.is_premium)
        return {"id": post_id, "message": "Blog post created"}

@app.get("/webinars")
async def get_webinars(current_user: dict = Depends(get_current_user)):
    async with db_pool.acquire() as conn:
        query = """
            SELECT w.*, u.full_name as creator_name 
            FROM webinars w
            LEFT JOIN users u ON w.created_by = u.id
            WHERE w.scheduled_at > NOW()
            ORDER BY w.scheduled_at ASC
        """
        rows = await conn.fetch(query)
        
        webinars = []
        for row in rows:
            webinar = dict(row)
            if webinar["is_premium"] and not check_premium_access(current_user, True):
                webinar["meeting_link"] = None
                webinar["locked"] = True
            else:
                webinar["locked"] = False
            webinars.append(webinar)
        
        return webinars

@app.post("/webinars")
async def create_webinar(webinar: WebinarCreate, mod: dict = Depends(require_moderator)):
    async with db_pool.acquire() as conn:
        webinar_id = await conn.fetchval("""
            INSERT INTO webinars (title, description, scheduled_at, duration_minutes, meeting_link, is_premium, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """, webinar.title, webinar.description, webinar.scheduled_at, 
             webinar.duration_minutes, webinar.meeting_link, webinar.is_premium, mod["id"])
        return {"id": webinar_id, "message": "Webinar created"}

@app.get("/courses")
async def get_courses(current_user: dict = Depends(get_current_user)):
    async with db_pool.acquire() as conn:
        query = """
            SELECT c.*, u.full_name as creator_name 
            FROM courses c
            LEFT JOIN users u ON c.created_by = u.id
            ORDER BY c.created_at DESC
        """
        rows = await conn.fetch(query)
        
        courses = []
        for row in rows:
            course = dict(row)
            if course["is_premium"] and not check_premium_access(current_user, True):
                course["content"] = "🔒 Premium course. Upgrade to view content."
                course["locked"] = True
            else:
                course["locked"] = False
            courses.append(course)
        
        return courses

@app.post("/courses")
async def create_course(course: CourseCreate, mod: dict = Depends(require_moderator)):
    async with db_pool.acquire() as conn:
        course_id = await conn.fetchval("""
            INSERT INTO courses (title, description, content, is_premium, created_by)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, course.title, course.description, course.content, course.is_premium, mod["id"])
        return {"id": course_id, "message": "Course created"}

# ==========================================
# CONFIG & HEALTH
# ==========================================

@app.get("/config")
async def get_config():
    return {
        "telegram_free_channel": "https://t.me/pipways_free",
        "telegram_premium_channel": "https://t.me/pipways_vip",
        "features": {
            "ai_analysis": bool(settings.OPENROUTER_API_KEY),
            "mentor_chat": bool(settings.OPENROUTER_API_KEY),
            "auth_required": True
        }
    }

@app.get("/health")
async def health_check():
    db_status = "connected" if db_pool else "disconnected"
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
