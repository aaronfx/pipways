"""
Pipways Trading Platform API
Complete implementation with auth, multi-admin, AI integration, and mobile-ready endpoints
"""

import os
import re
import jwt
import bcrypt
import asyncpg
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Query, Request
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
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-opus-20240229")
    OPENROUTER_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "anthropic/claude-3-opus-20240229")
    CORS_ORIGINS = [
        "https://pipways-web-nhem.onrender.com",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5500"
    ]

settings = Settings()

# Database pool
db_pool: Optional[asyncpg.Pool] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    db_pool = await asyncpg.create_pool(settings.DATABASE_URL, min_size=5, max_size=20)
    await init_db()
    yield
    await db_pool.close()

app = FastAPI(title="Pipways API", version="2.0.0", lifespan=lifespan)

# CRITICAL: CORS Middleware must be FIRST to handle all responses including errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Custom middleware to ensure CORS headers on ALL responses (including 401, 403, 500)
@app.middleware("http")
async def cors_debug_handler(request: Request, call_next):
    origin = request.headers.get("origin")
    
    # Handle preflight
    if request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin": origin if origin in settings.CORS_ORIGINS else settings.CORS_ORIGINS[0],
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, Origin, X-Requested-With",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        }
        return JSONResponse(content={}, headers=headers)
    
    try:
        response = await call_next(request)
        
        # Add CORS headers to response
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
        else:
            response.headers["Access-Control-Allow-Origin"] = settings.CORS_ORIGINS[0]
        response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response
        
    except Exception as exc:
        # Even on 500 errors, return CORS headers so frontend can see the error
        logger.error(f"Error processing request: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers={
                "Access-Control-Allow-Origin": origin if origin else settings.CORS_ORIGINS[0],
                "Access-Control-Allow-Credentials": "true",
            }
        )

# Security
security = HTTPBearer(auto_error=False)  # auto_error=False prevents 403 without CORS headers

# Models (same as before - fixed for Pydantic v2)
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

class MentorChatMessage(BaseModel):
    message: str = Field(..., min_length=1)
    context: Optional[str] = None

# Database initialization
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
        
        # Create default admin
        admin_exists = await conn.fetchval("SELECT id FROM users WHERE email = $1", settings.ADMIN_EMAIL)
        if not admin_exists:
            hashed = bcrypt.hashpw(settings.ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
            await conn.execute("""
                INSERT INTO users (email, password_hash, full_name, role, subscription_tier, subscription_status, email_verified)
                VALUES ($1, $2, $3, 'admin', 'vip', 'active', TRUE)
            """, settings.ADMIN_EMAIL, hashed, "System Administrator")
            logger.info(f"Default admin created: {settings.ADMIN_EMAIL}")

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

# FIXED: get_current_user now handles missing tokens gracefully with CORS
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

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "moderator"]:
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
            INSERT INTO users (email, password_hash, full_name, subscription_tier, subscription_status)
            VALUES ($1, $2, $3, 'free', 'active')
            RETURNING id
        """, user_data.email, hashed_pw, user_data.full_name)
        
        access_token = create_access_token({"sub": str(user_id)})
        refresh_token = create_refresh_token({"sub": str(user_id)})
        
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": dict(user)
        }

@app.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", credentials.email)
        if not user or not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        await conn.execute("UPDATE users SET last_login = NOW() WHERE id = $1", user["id"])
        
        access_token = create_access_token({"sub": str(user["id"])})
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
            
            new_access = create_access_token({"sub": str(user_id)})
            return {"access_token": new_access, "token_type": "bearer"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

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
    if int(admin["id"]) == user_id and role != "admin":
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
    if int(admin["id"]) == user_id:
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
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        total_signals = await conn.fetchval("SELECT COUNT(*) FROM signals")
        active_signals = await conn.fetchval("SELECT COUNT(*) FROM signals WHERE status = 'active'")
        premium_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE subscription_tier IN ('premium', 'vip')")
        
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
    current_user: Optional[dict] = Depends(get_current_user)
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
        
        # Filter premium signals for non-premium users
        if not current_user or current_user["subscription_tier"] == "free":
            query += " AND is_premium = FALSE"
        
        query += " ORDER BY created_at DESC"
        query += f" LIMIT ${len(params)+1}"
        params.append(limit)
        
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]

@app.post("/signals")
async def create_signal(signal: SignalCreate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        signal_id = await conn.fetchval("""
            INSERT INTO signals (pair, direction, entry_price, stop_loss, take_profit, timeframe, analysis, is_premium, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """, signal.pair, signal.direction, signal.entry_price, signal.stop_loss,
             signal.take_profit, signal.timeframe, signal.analysis, signal.is_premium, admin["id"])
        
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

# AI Analysis
@app.post("/analyze/chart")
async def analyze_chart(
    file: UploadFile = File(...),
    pair: Optional[str] = Form(None),
    timeframe: Optional[str] = Form(None),
    additional_info: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")
    
    import base64
    image_base64 = base64.b64encode(contents).decode()
    
    prompt = f"""Analyze this forex/crypto chart for {pair or 'unknown pair'} on {timeframe or 'unknown timeframe'} timeframe.
    Additional context: {additional_info or 'None'}
    
    Provide analysis in this format:
    - Trend Direction (Bullish/Bearish/Neutral)
    - Key Support Levels
    - Key Resistance Levels
    - Entry Suggestion (if any)
    - Risk Management advice
    - Confidence Level (1-10)"""
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
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
                    ]
                },
                timeout=60.0
            )
            
            result = response.json()
            analysis = result["choices"][0]["message"]["content"]
            
            return {
                "analysis": analysis,
                "pair": pair,
                "timeframe": timeframe,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"AI Analysis error: {str(e)}")
            raise HTTPException(status_code=500, detail="AI analysis failed")

@app.post("/mentor/chat")
async def mentor_chat(
    message: MentorChatMessage,
    current_user: dict = Depends(get_current_user)
):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    async with db_pool.acquire() as conn:
        history = await conn.fetch("""
            SELECT message, response FROM chat_history 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT 5
        """, current_user["id"])
        
        messages = []
        for row in reversed(history):
            messages.extend([
                {"role": "user", "content": row["message"]},
                {"role": "assistant", "content": row["response"]}
            ])
        
        messages.append({
            "role": "user",
            "content": f"{message.message}\n\nContext: {message.context or 'Forex trading'}"
        })
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://pipways.com",
                    "X-Title": "Pipways AI Mentor"
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are an expert forex trading mentor. Provide clear, actionable advice. Be encouraging but realistic about risks."},
                        *messages
                    ]
                },
                timeout=30.0
            )
            
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
            await conn.execute("""
                INSERT INTO chat_history (user_id, message, response, context)
                VALUES ($1, $2, $3, $4)
            """, current_user["id"], message.message, ai_response, message.context)
            
            return {"response": ai_response, "timestamp": datetime.utcnow().isoformat()}

# Content Management
@app.get("/blog/posts")
async def get_blog_posts(
    limit: int = Query(10, le=50),
    current_user: Optional[dict] = Depends(get_current_user)
):
    async with db_pool.acquire() as conn:
        query = "SELECT * FROM blog_posts"
        if not current_user or current_user["subscription_tier"] == "free":
            query += " WHERE is_premium = FALSE"
        query += " ORDER BY created_at DESC LIMIT $1"
        
        rows = await conn.fetch(query, limit)
        return [dict(row) for row in rows]

@app.post("/blog/posts")
async def create_blog_post(post: BlogPostCreate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        post_id = await conn.fetchval("""
            INSERT INTO blog_posts (title, content, excerpt, author_id, is_premium)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, post.title, post.content, post.excerpt or post.content[:200], admin["id"], post.is_premium)
        return {"id": post_id, "message": "Blog post created"}

@app.get("/webinars")
async def get_webinars(current_user: Optional[dict] = Depends(get_current_user)):
    async with db_pool.acquire() as conn:
        query = "SELECT * FROM webinars WHERE scheduled_at > NOW()"
        if not current_user or current_user["subscription_tier"] == "free":
            query += " AND is_premium = FALSE"
        query += " ORDER BY scheduled_at ASC"
        
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]

@app.post("/webinars")
async def create_webinar(webinar: WebinarCreate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        webinar_id = await conn.fetchval("""
            INSERT INTO webinars (title, description, scheduled_at, duration_minutes, meeting_link, is_premium, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """, webinar.title, webinar.description, webinar.scheduled_at, 
             webinar.duration_minutes, webinar.meeting_link, webinar.is_premium, admin["id"])
        return {"id": webinar_id, "message": "Webinar created"}

@app.get("/courses")
async def get_courses(current_user: Optional[dict] = Depends(get_current_user)):
    async with db_pool.acquire() as conn:
        query = "SELECT * FROM courses"
        if not current_user or current_user["subscription_tier"] == "free":
            query += " WHERE is_premium = FALSE"
        query += " ORDER BY created_at DESC"
        
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]

@app.post("/courses")
async def create_course(course: CourseCreate, admin: dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        course_id = await conn.fetchval("""
            INSERT INTO courses (title, description, content, is_premium, created_by)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, course.title, course.description, course.content, course.is_premium, admin["id"])
        return {"id": course_id, "message": "Course created"}

# Config
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
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
