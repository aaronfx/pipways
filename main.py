"""
Pipways API Service
Separate backend for pipways-api-nhem
"""

import os
import re
import json
import base64
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from asyncpg import Pool
from jose import JWTError, jwt
from passlib.context import CryptContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Settings
class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://pipways-web-nhem.onrender.com")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

settings = Settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)
pool: Optional[Pool] = None

# Database
async def init_db():
    global pool
    if not settings.DATABASE_URL:
        logger.error("DATABASE_URL not set!")
        return
    
    try:
        pool = await asyncpg.create_pool(settings.DATABASE_URL, min_size=5, max_size=20)
        logger.info("Database connected")
        
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255),
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    pair VARCHAR(20) NOT NULL,
                    direction VARCHAR(10) NOT NULL CHECK (direction IN ('LONG', 'SHORT')),
                    pips DECIMAL(10,2) NOT NULL,
                    grade VARCHAR(5) DEFAULT 'C',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS courses (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    level VARCHAR(20) DEFAULT 'beginner',
                    is_published BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS course_enrollments (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, course_id)
                );
                
                CREATE TABLE IF NOT EXISTS webinars (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    presenter VARCHAR(255),
                    scheduled_at TIMESTAMP NOT NULL,
                    zoom_link TEXT,
                    max_attendees INTEGER DEFAULT 100,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS webinar_registrations (
                    id SERIAL PRIMARY KEY,
                    webinar_id INTEGER REFERENCES webinars(id) ON DELETE CASCADE,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(webinar_id, user_id)
                );
                
                CREATE TABLE IF NOT EXISTS blog_posts (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    excerpt TEXT,
                    featured_image TEXT,
                    category VARCHAR(50) DEFAULT 'general',
                    is_published BOOLEAN DEFAULT FALSE,
                    author_id INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS chart_analyses (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    image_url TEXT NOT NULL,
                    analysis_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS mentor_chats (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database error: {e}")

async def get_db():
    if pool is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    async with pool.acquire() as conn:
        yield conn

# Auth
def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)
def get_password_hash(password): return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# FastAPI App
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    if pool:
        await pool.close()

app = FastAPI(title="Pipways API", version="2.0.0", lifespan=lifespan)

# CORS - CRITICAL for separate services
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "database": "connected" if pool else "disconnected"
    }

@app.get("/")
async def root():
    return {
        "message": "Pipways API Server",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.post("/auth/register")
async def register(
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(None),
    conn=Depends(get_db)
):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = get_password_hash(password)
    user_id = await conn.fetchval(
        "INSERT INTO users (email, password_hash, full_name) VALUES ($1, $2, $3) RETURNING id",
        email, hashed, full_name
    )
    
    access_token = create_access_token({"sub": email})
    
    return {
        "success": True,
        "user_id": user_id,
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/auth/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    conn=Depends(get_db)
):
    user = await conn.fetchrow(
        "SELECT id, email, password_hash, full_name, is_admin FROM users WHERE email = $1 AND is_active = TRUE",
        email
    )
    
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    await conn.execute("UPDATE users SET last_login = NOW() WHERE id = $1", user["id"])
    
    access_token = create_access_token({"sub": email})
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "is_admin": user["is_admin"]
        }
    }

@app.get("/auth/me")
async def get_me(current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    user = await conn.fetchrow(
        "SELECT id, email, full_name, is_admin FROM users WHERE email = $1",
        current_user
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user)

# ============================================================================
# TRADE ENDPOINTS
# ============================================================================

@app.post("/trades")
async def create_trade(
    pair: str = Form(...),
    direction: str = Form(...),
    pips: float = Form(...),
    grade: str = Form("C"),
    notes: str = Form(None),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    
    trade_id = await conn.fetchval(
        "INSERT INTO trades (user_id, pair, direction, pips, grade, notes) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id",
        user["id"], pair.upper(), direction.upper(), pips, grade.upper(), notes
    )
    
    return {"success": True, "trade_id": trade_id}

@app.get("/trades")
async def get_trades(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    
    total = await conn.fetchval("SELECT COUNT(*) FROM trades WHERE user_id = $1", user["id"])
    offset = (page - 1) * per_page
    
    trades = await conn.fetch(
        "SELECT * FROM trades WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
        user["id"], per_page, offset
    )
    
    return {
        "trades": [dict(t) for t in trades],
        "total": total,
        "page": page,
        "per_page": per_page
    }

# ============================================================================
# COURSE ENDPOINTS
# ============================================================================

@app.get("/courses")
async def get_courses(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    conn=Depends(get_db)
):
    total = await conn.fetchval("SELECT COUNT(*) FROM courses WHERE is_published = TRUE")
    offset = (page - 1) * per_page
    
    courses = await conn.fetch(
        "SELECT * FROM courses WHERE is_published = TRUE ORDER BY created_at DESC LIMIT $1 OFFSET $2",
        per_page, offset
    )
    
    return {
        "courses": [dict(c) for c in courses],
        "total": total,
        "page": page,
        "per_page": per_page
    }

@app.post("/courses/{course_id}/enroll")
async def enroll_course(
    course_id: int,
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    
    try:
        await conn.execute(
            "INSERT INTO course_enrollments (user_id, course_id) VALUES ($1, $2)",
            user["id"], course_id
        )
        return {"success": True, "message": "Enrolled successfully"}
    except asyncpg.UniqueViolationError:
        return {"success": True, "message": "Already enrolled"}

# ============================================================================
# WEBINAR ENDPOINTS
# ============================================================================

@app.get("/webinars")
async def get_webinars(conn=Depends(get_db)):
    webinars = await conn.fetch(
        "SELECT * FROM webinars WHERE scheduled_at > NOW() ORDER BY scheduled_at ASC"
    )
    return {"webinars": [dict(w) for w in webinars]}

@app.post("/webinars/{webinar_id}/register")
async def register_webinar(
    webinar_id: int,
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    
    try:
        await conn.execute(
            "INSERT INTO webinar_registrations (webinar_id, user_id) VALUES ($1, $2)",
            webinar_id, user["id"]
        )
        return {"success": True, "message": "Registered successfully"}
    except asyncpg.UniqueViolationError:
        return {"success": True, "message": "Already registered"}

# ============================================================================
# BLOG ENDPOINTS
# ============================================================================

@app.get("/blog/posts")
async def get_blog_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    conn=Depends(get_db)
):
    total = await conn.fetchval("SELECT COUNT(*) FROM blog_posts WHERE is_published = TRUE")
    offset = (page - 1) * per_page
    
    posts = await conn.fetch(
        "SELECT id, title, slug, excerpt, featured_image, category, published_at FROM blog_posts WHERE is_published = TRUE ORDER BY published_at DESC LIMIT $1 OFFSET $2",
        per_page, offset
    )
    
    return {
        "posts": [dict(p) for p in posts],
        "total": total,
        "page": page,
        "per_page": per_page
    }

# ============================================================================
# AI ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/analyze/chart")
async def analyze_chart(
    image: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    
    contents = await image.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")
    
    filename = f"chart_{int(datetime.now().timestamp())}.png"
    analysis = "Chart analysis placeholder."
    
    await conn.execute(
        "INSERT INTO chart_analyses (user_id, image_url, analysis_text) VALUES ($1, $2, $3)",
        user["id"], filename, analysis
    )
    
    return {"success": True, "analysis": analysis}

@app.post("/mentor/chat")
async def mentor_chat(
    message: str = Form(...),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    
    response = f"You said: {message}. This is a placeholder."
    
    await conn.execute(
        "INSERT INTO mentor_chats (user_id, message, response) VALUES ($1, $2, $3)",
        user["id"], message, response
    )
    
    return {"success": True, "response": response}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
