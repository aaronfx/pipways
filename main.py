"""
Pipways Trading Platform API - Production Fix v2.1
Fixes: Professional AI prompts, image handling, admin visibility, error handling
"""

import os
import re
import jwt
import bcrypt
import asyncpg
import logging
import base64
import json
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

app = FastAPI(title="Pipways API", version="2.1.0", lifespan=lifespan)

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

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

    @field_validator('new_password')
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
    message: str = Field(..., min_length=1)
    context: Optional[str] = ""

# Database initialization
async def init_db():
    async with db_pool.acquire() as conn:
        # Check if users table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """)

        if table_exists:
            # Check if role column exists, add if not
            role_column_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'role'
                )
            """)

            if not role_column_exists:
                logger.info("Adding role column to existing users table...")
                await conn.execute("""
                    ALTER TABLE users 
                    ADD COLUMN role VARCHAR(20) DEFAULT 'user'
                """)
                await conn.execute("""
                    UPDATE users SET role = 'user' WHERE role IS NULL
                """)
                logger.info("Role column added successfully")

        # Create users table if not exists
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

        # Create signals table
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

        # Create blog_posts table
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

        # Create webinars table
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

        # Create courses table
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

        # Create chat_history table
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
                # Ensure admin has admin role
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

@app.post("/auth/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", request.email)
        if not user:
            return {"message": "If email exists, reset link sent"}

        reset_token = create_reset_token()
        expires = datetime.utcnow() + timedelta(hours=settings.RESET_TOKEN_EXPIRE_HOURS)

        await conn.execute("""
            UPDATE users SET reset_token = $1, reset_token_expires = $2 WHERE id = $3
        """, reset_token, expires, user["id"])

        reset_url = f"https://pipways-web-nhem.onrender.com?reset_token={reset_token}"
        logger.info(f"Password reset URL for {request.email}: {reset_url}")

        return {"message": "If email exists, reset link sent"}

@app.post("/auth/reset-password")
async def reset_password(reset_data: PasswordReset):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("""
            SELECT * FROM users 
            WHERE reset_token = $1 AND reset_token_expires > NOW()
        """, reset_data.token)

        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        hashed_pw = get_password_hash(reset_data.new_password)
        await conn.execute("""
            UPDATE users 
            SET password_hash = $1, reset_token = NULL, reset_token_expires = NULL, updated_at = NOW()
            WHERE id = $2
        """, hashed_pw, user["id"])

        return {"message": "Password reset successful"}

@app.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Logged out successfully"}

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

        return {
            "total_users": total_users,
            "total_signals": total_signals,
            "active_signals": active_signals,
            "premium_users": premium_users,
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

# Enhanced AI Analysis with Professional Trading Format
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

        # ENHANCED PROMPT: Professional structured analysis format
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
            
            # Parse and format the structured response
            try:
                cleaned = ai_response.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                    cleaned = cleaned.strip()
                
                analysis_data = json.loads(cleaned)
                
                # Format as professional text report
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
                    "image_base64": image_base64,  # Return image for frontend display
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

# Enhanced AI Mentor with Professional Persona
@app.post("/mentor/chat")
async def mentor_chat(
    request: MentorChatRequest,
    current_user: dict = Depends(get_current_user)
):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    try:
        user_id = current_user.get("id") or current_user.get("sub")
        async with db_pool.acquire() as conn:
            history = await conn.fetch("""
                SELECT message, response FROM chat_history 
                WHERE user_id = $1 
                ORDER BY created_at DESC 
                LIMIT 5
            """, int(user_id))

            system_prompt = """You are a professional forex and crypto trading mentor with 15+ years of experience trading institutional and retail accounts. Your expertise includes technical analysis, risk management, trading psychology, and strategy development.

CORE PRINCIPLES:
1. RISK MANAGEMENT FIRST: Always emphasize position sizing (1-2% risk per trade), stop losses, and capital preservation
2. PSYCHOLOGY MATTERS: Address emotional control, discipline, patience, and the mental aspects of trading when relevant
3. ACTIONABLE ADVICE: Give specific, practical guidance rather than vague suggestions. Include concrete examples.
4. REALISTIC EXPECTATIONS: Warn against get-rich-quick thinking. Emphasize consistency over big wins.
5. CONTEXT-AWARE: Adapt advice based on whether the trader is beginner, intermediate, or advanced based on their questions.

WHEN DISCUSSING STRATEGIES:
- Explain the logic behind the strategy (why it works)
- Include specific entry/exit rules
- Warn about market conditions where it fails
- Suggest optimal timeframes and pairs

WHEN REVIEWING TRADES/IDEAS:
- Ask for chart context if not provided
- Point out logical flaws in the setup
- Suggest improvements to risk management
- Comment on risk/reward ratio

WHEN DISCUSSING PSYCHOLOGY:
- Share techniques for managing FOMO, revenge trading, and overtrading
- Explain the importance of trading plans and journals
- Discuss drawdown recovery strategies

Tone: Professional, encouraging but firm on risk management, patient with beginners, challenging for experienced traders to think deeper. Never promise profits."""

            messages = [{"role": "system", "content": system_prompt}]

            for row in reversed(history):
                messages.append({"role": "user", "content": row["message"]})
                messages.append({"role": "assistant", "content": row["response"]})

            messages.append({
                "role": "user",
                "content": f"Question: {request.message}\nAdditional Context: {request.context}\n\nPlease provide professional trading mentorship on this topic."
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
                    logger.error(f"OpenRouter model not found: {settings.OPENROUTER_MODEL}")
                    raise HTTPException(status_code=503, detail="AI mentor model not available")

                if response.status_code != 200:
                    logger.error(f"OpenRouter mentor error: {response.text}")
                    raise HTTPException(status_code=500, detail=f"AI service error: {response.status_code}")

                result = response.json()
                ai_response = result["choices"][0]["message"]["content"]

                await conn.execute("""
                    INSERT INTO chat_history (user_id, message, response, context)
                    VALUES ($1, $2, $3, $4)
                """, int(user_id), request.message, ai_response, request.context)

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
    return {
        "status": "healthy", 
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
