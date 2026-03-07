"""
Pipways Trading Platform API v2.0
Production-ready FastAPI backend with integrated frontend serving
"""

import os
import re
import json
import base64
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from asyncpg import Pool
from jose import JWTError, jwt
from passlib.context import CryptContext
import requests

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Settings
class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")
    STATIC_DIR = os.environ.get("STATIC_DIR", "static")
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
                    grade VARCHAR(5) DEFAULT 'C' CHECK (grade IN ('A', 'B', 'C', 'D', 'F')),
                    notes TEXT,
                    entry_price DECIMAL(15,5),
                    exit_price DECIMAL(15,5),
                    trade_date DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS courses (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    level VARCHAR(20) DEFAULT 'beginner',
                    duration_hours INTEGER,
                    image_url TEXT,
                    is_published BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS course_modules (
                    id SERIAL PRIMARY KEY,
                    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    video_url TEXT,
                    order_index INTEGER DEFAULT 0,
                    duration_minutes INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS course_enrollments (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    progress_percent INTEGER DEFAULT 0,
                    UNIQUE(user_id, course_id)
                );

                CREATE TABLE IF NOT EXISTS webinars (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    presenter VARCHAR(255),
                    scheduled_at TIMESTAMP NOT NULL,
                    duration_minutes INTEGER DEFAULT 60,
                    zoom_link TEXT,
                    max_attendees INTEGER DEFAULT 100,
                    is_recorded BOOLEAN DEFAULT FALSE,
                    recording_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS webinar_registrations (
                    id SERIAL PRIMARY KEY,
                    webinar_id INTEGER REFERENCES webinars(id) ON DELETE CASCADE,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    attended BOOLEAN DEFAULT FALSE,
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
                    tags TEXT[],
                    author_id INTEGER REFERENCES users(id),
                    is_published BOOLEAN DEFAULT FALSE,
                    published_at TIMESTAMP,
                    view_count INTEGER DEFAULT 0,
                    seo_score INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS chart_analyses (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    image_url TEXT NOT NULL,
                    analysis_text TEXT NOT NULL,
                    pair VARCHAR(20),
                    timeframe VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS performance_analyses (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    statement_data JSONB,
                    analysis_text TEXT NOT NULL,
                    metrics JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS mentor_chats (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    context JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS media_files (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    original_name VARCHAR(255),
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    mime_type VARCHAR(100),
                    uploaded_by INTEGER REFERENCES users(id),
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

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security), conn=Depends(get_db)):
    email = await get_current_user(credentials)
    user = await conn.fetchrow("SELECT is_admin FROM users WHERE email = $1", email)
    if not user or not user["is_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return email

# FastAPI App
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    if pool:
        await pool.close()

app = FastAPI(title="Pipways API", version="2.0.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
os.makedirs(settings.STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.STATIC_DIR, "uploads"), exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=os.path.join(settings.STATIC_DIR, "uploads")), name="uploads")

# Serve frontend at root
@app.get("/")
async def serve_frontend():
    index_path = os.path.join(settings.STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse(content="""
    <h1>Pipways API Server</h1>
    <p>Frontend not found. Please place index.html in the static folder.</p>
    <p><a href="/docs">API Documentation</a></p>
    <p><a href="/health">Health Check</a></p>
    """)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if pool else "disconnected"
    }

@app.get("/api/version")
async def get_version():
    return {"version": "2.0.0", "environment": settings.ENVIRONMENT}

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.post("/api/auth/register")
async def register(
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(None),
    conn=Depends(get_db)
):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=400, detail="Invalid email format")

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

@app.post("/api/auth/login")
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

@app.get("/api/auth/me")
async def get_me(current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    user = await conn.fetchrow(
        "SELECT id, email, full_name, is_admin, created_at FROM users WHERE email = $1",
        current_user
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user)

# ============================================================================
# TRADE ENDPOINTS
# ============================================================================

@app.post("/api/trades")
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

    direction = direction.upper()
    if direction not in ["LONG", "SHORT"]:
        raise HTTPException(status_code=400, detail="Direction must be LONG or SHORT")

    trade_id = await conn.fetchval(
        "INSERT INTO trades (user_id, pair, direction, pips, grade, notes) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id",
        user["id"], pair.upper(), direction, pips, grade.upper(), notes
    )

    return {"success": True, "trade_id": trade_id, "message": "Trade logged successfully"}

@app.get("/api/trades")
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
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

# ============================================================================
# COURSE ENDPOINTS
# ============================================================================

@app.get("/api/courses")
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

@app.get("/api/courses/{course_id}")
async def get_course(course_id: int, conn=Depends(get_db)):
    course = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    modules = await conn.fetch(
        "SELECT id, title, content, video_url, order_index, duration_minutes FROM course_modules WHERE course_id = $1 ORDER BY order_index",
        course_id
    )

    return {"course": dict(course), "modules": [dict(m) for m in modules]}

@app.post("/api/courses/{course_id}/enroll")
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

@app.get("/api/webinars")
async def get_webinars(
    upcoming: bool = Query(True),
    conn=Depends(get_db)
):
    if upcoming:
        webinars = await conn.fetch(
            "SELECT * FROM webinars WHERE scheduled_at > NOW() ORDER BY scheduled_at ASC"
        )
    else:
        webinars = await conn.fetch("SELECT * FROM webinars ORDER BY scheduled_at DESC")

    return {"webinars": [dict(w) for w in webinars]}

@app.get("/api/webinars/my")
async def get_my_webinars(
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    webinars = await conn.fetch(
        """SELECT w.*, wr.registered_at, wr.attended
           FROM webinars w
           JOIN webinar_registrations wr ON w.id = wr.webinar_id
           WHERE wr.user_id = $1
           ORDER BY w.scheduled_at DESC""",
        user["id"]
    )

    return {"webinars": [dict(w) for w in webinars]}

@app.post("/api/webinars/{webinar_id}/register")
async def register_webinar(
    webinar_id: int,
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    webinar = await conn.fetchrow(
        "SELECT max_attendees FROM webinars WHERE id = $1 AND scheduled_at > NOW()",
        webinar_id
    )

    if not webinar:
        raise HTTPException(status_code=404, detail="Webinar not found or already started")

    current_count = await conn.fetchval(
        "SELECT COUNT(*) FROM webinar_registrations WHERE webinar_id = $1",
        webinar_id
    )

    if current_count >= webinar["max_attendees"]:
        raise HTTPException(status_code=400, detail="Webinar is full")

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

@app.get("/api/blog/posts")
async def get_blog_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    conn=Depends(get_db)
):
    total = await conn.fetchval("SELECT COUNT(*) FROM blog_posts WHERE is_published = TRUE")
    offset = (page - 1) * per_page

    posts = await conn.fetch(
        """SELECT id, title, slug, excerpt, featured_image, category, tags,
                  author_id, published_at, view_count, seo_score
           FROM blog_posts 
           WHERE is_published = TRUE 
           ORDER BY published_at DESC 
           LIMIT $1 OFFSET $2""",
        per_page, offset
    )

    return {
        "posts": [dict(p) for p in posts],
        "total": total,
        "page": page,
        "per_page": per_page
    }

@app.get("/api/blog/post/{slug}")
async def get_blog_post(slug: str, conn=Depends(get_db)):
    post = await conn.fetchrow(
        "SELECT * FROM blog_posts WHERE slug = $1 AND is_published = TRUE",
        slug
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    await conn.execute(
        "UPDATE blog_posts SET view_count = view_count + 1 WHERE id = $1",
        post["id"]
    )

    return dict(post)

# ============================================================================
# AI ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/analyze/chart")
async def analyze_chart(
    image: UploadFile = File(...),
    pair: str = Form(None),
    timeframe: str = Form(None),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    contents = await image.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    filename = f"chart_{int(datetime.now().timestamp())}_{image.filename}"
    file_path = os.path.join(settings.STATIC_DIR, "uploads", filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    # Placeholder analysis - replace with actual AI call
    analysis = f"Chart analysis for {pair or 'unknown pair'} on {timeframe or 'unknown timeframe'}."

    await conn.execute(
        "INSERT INTO chart_analyses (user_id, image_url, analysis_text, pair, timeframe) VALUES ($1, $2, $3, $4, $5)",
        user["id"], f"/uploads/{filename}", analysis, pair, timeframe
    )

    return {"success": True, "analysis": analysis, "image_url": f"/uploads/{filename}"}

@app.get("/api/analyze/chart/history")
async def get_chart_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    total = await conn.fetchval(
        "SELECT COUNT(*) FROM chart_analyses WHERE user_id = $1", user["id"]
    )

    offset = (page - 1) * per_page
    analyses = await conn.fetch(
        """SELECT id, image_url, analysis_text, pair, timeframe, created_at 
           FROM chart_analyses 
           WHERE user_id = $1 
           ORDER BY created_at DESC 
           LIMIT $2 OFFSET $3""",
        user["id"], per_page, offset
    )

    return {
        "analyses": [dict(a) for a in analyses],
        "total": total,
        "page": page,
        "per_page": per_page
    }

@app.post("/api/mentor/chat")
async def mentor_chat(
    message: str = Form(...),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    # Placeholder - replace with actual AI
    response = f"You asked: {message}. This is a placeholder response from your AI mentor."

    await conn.execute(
        "INSERT INTO mentor_chats (user_id, message, response) VALUES ($1, $2, $3)",
        user["id"], message, response
    )

    return {"success": True, "response": response}

@app.get("/api/mentor/history")
async def get_mentor_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    total = await conn.fetchval(
        "SELECT COUNT(*) FROM mentor_chats WHERE user_id = $1", user["id"]
    )

    offset = (page - 1) * per_page
    chats = await conn.fetch(
        """SELECT id, message, response, created_at 
           FROM mentor_chats 
           WHERE user_id = $1 
           ORDER BY created_at DESC 
           LIMIT $2 OFFSET $3""",
        user["id"], per_page, offset
    )

    return {
        "chats": [dict(c) for c in chats],
        "total": total,
        "page": page,
        "per_page": per_page
    }

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@app.get("/api/admin/stats")
async def get_admin_stats(
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    stats = await conn.fetchrow("""
        SELECT 
            (SELECT COUNT(*) FROM users) as total_users,
            (SELECT COUNT(*) FROM users WHERE last_login > NOW() - INTERVAL '7 days') as active_users_7d,
            (SELECT COUNT(*) FROM trades) as total_trades,
            (SELECT COUNT(*) FROM courses) as total_courses,
            (SELECT COUNT(*) FROM webinars) as total_webinars,
            (SELECT COUNT(*) FROM blog_posts) as total_posts
    """)

    return dict(stats)

@app.post("/api/admin/blog/posts")
async def create_blog_post(
    title: str = Form(...),
    content: str = Form(...),
    excerpt: str = Form(None),
    category: str = Form("general"),
    tags: str = Form(None),
    featured_image: str = Form(None),
    is_published: bool = Form(False),
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    slug = re.sub(r'[^\w]+', '-', title.lower()).strip('-')

    existing = await conn.fetchrow("SELECT id FROM blog_posts WHERE slug = $1", slug)
    if existing:
        slug = f"{slug}-{int(datetime.now().timestamp())}"

    # Simple SEO scoring
    seo_score = 50
    if 30 < len(title) < 60: seo_score += 10
    if excerpt and len(excerpt) > 100: seo_score += 10
    if featured_image: seo_score += 10
    if tags: seo_score += 10
    if len(content) > 500: seo_score += 10

    author = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    post_id = await conn.fetchval(
        """INSERT INTO blog_posts 
           (title, slug, content, excerpt, category, tags, featured_image, 
            is_published, published_at, author_id, seo_score)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) RETURNING id""",
        title, slug, content, excerpt, category,
        tags.split(',') if tags else [],
        featured_image, is_published,
        datetime.now() if is_published else None,
        author["id"], seo_score
    )

    return {
        "success": True,
        "post_id": post_id,
        "slug": slug,
        "seo_score": seo_score
    }

# ============================================================================
# SPA FALLBACK - Must be last
# ============================================================================

@app.get("/{path:path}")
async def spa_fallback(path: str):
    """Serve index.html for all non-API routes (SPA support)"""
    if path.startswith("api/") or path.startswith("static/") or path.startswith("uploads/"):
        raise HTTPException(status_code=404)

    index_path = os.path.join(settings.STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
