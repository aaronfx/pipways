"""
Pipways Trading Education Platform
Single-file FastAPI application with:
- AI Chart Analysis (image upload)
- AI Performance Analysis (statement upload)
- AI Mentor (personalized coaching with LMS integration)
- Webinars (Zoom integration)
- LMS (Learning Management System)
- Blog (WordPress-style editor with SEO)
- Admin Dashboard
"""

import os
import logging
import re
import json
import base64
import asyncpg
import bcrypt
import requests
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, Form, UploadFile, File, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from jose import JWTError, jwt
from contextlib import asynccontextmanager
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
DATABASE_URL = os.getenv("DATABASE_URL", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
ZOOM_API_KEY = os.getenv("ZOOM_API_KEY", "")
ZOOM_API_SECRET = os.getenv("ZOOM_API_SECRET", "")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30
DEFAULT_ADMIN_EMAIL = "admin@pipways.com"
DEFAULT_ADMIN_PASSWORD = "admin123"

# ============================================================================
# UTILITIES
# ============================================================================

def get_password_hash(password: str) -> str:
    """Hash password with bcrypt (72 char limit)"""
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def create_access_token(data: dict) -> str:
    """Create JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def generate_slug(title: str) -> str:
    """Generate URL-friendly slug from title"""
    slug = re.sub(r"[^\w\s-]", "", title.lower()).strip()
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug

def calculate_seo_score(title: str, content: str, meta_desc: str) -> dict:
    """Calculate SEO score for blog post"""
    score = 0
    suggestions = []

    # Title checks
    if len(title) >= 50 and len(title) <= 60:
        score += 20
    else:
        suggestions.append("Title should be 50-60 characters")

    # Content length
    word_count = len(content.split())
    if word_count >= 300:
        score += 20
    else:
        suggestions.append("Content should be at least 300 words")

    # Meta description
    if len(meta_desc) >= 150 and len(meta_desc) <= 160:
        score += 20
    else:
        suggestions.append("Meta description should be 150-160 characters")

    # Keyword density (simplified)
    if len(content) > 0:
        paragraphs = content.count('<p>')
        if paragraphs >= 3:
            score += 20
        else:
            suggestions.append("Use more paragraphs for readability")

    # Headers
    if '<h2>' in content or '<h3>' in content:
        score += 20
    else:
        suggestions.append("Add subheadings (H2, H3) to structure content")

    return {"score": min(score, 100), "suggestions": suggestions}

# ============================================================================
# DATABASE SETUP
# ============================================================================

async def get_db():
    """Database dependency"""
    conn = await asyncpg.connect(DATABASE_URL, ssl="require")
    try:
        yield conn
    finally:
        await conn.close()

async def init_db():
    """Initialize database tables"""
    logger.info("Initializing database...")

    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable is not set")
        raise ValueError("DATABASE_URL environment variable is not set")

    try:
        conn = await asyncpg.connect(DATABASE_URL, ssl="require")
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

    # Users table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(100),
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Chart analyses
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS chart_analyses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            image_data TEXT,
            analysis_result JSONB,
            grade VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Performance analyses
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS performance_analyses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            file_data TEXT,
            trader_type VARCHAR(100),
            strengths TEXT[],
            weaknesses TEXT[],
            recommendations TEXT[],
            overall_score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # AI Mentor sessions
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS mentorship_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            message TEXT,
            ai_response TEXT,
            context JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # User insights (AI-generated profile)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_insights (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) UNIQUE,
            trader_type VARCHAR(100),
            personality_profile JSONB,
            learning_path JSONB,
            recommended_courses INTEGER[],
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Webinars
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS webinars (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255),
            description TEXT,
            zoom_link VARCHAR(500),
            zoom_meeting_id VARCHAR(100),
            scheduled_at TIMESTAMP,
            max_participants INTEGER DEFAULT 100,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Webinar registrations
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS webinar_registrations (
            id SERIAL PRIMARY KEY,
            webinar_id INTEGER REFERENCES webinars(id),
            user_id INTEGER REFERENCES users(id),
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(webinar_id, user_id)
        )
    """)

    # LMS Courses
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255),
            description TEXT,
            thumbnail VARCHAR(500),
            difficulty VARCHAR(50),
            estimated_hours INTEGER,
            category VARCHAR(100),
            is_published BOOLEAN DEFAULT FALSE,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Course modules
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS course_modules (
            id SERIAL PRIMARY KEY,
            course_id INTEGER REFERENCES courses(id),
            title VARCHAR(255),
            content_type VARCHAR(50),
            content TEXT,
            video_url VARCHAR(500),
            order_index INTEGER,
            duration_minutes INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # User progress
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            module_id INTEGER REFERENCES course_modules(id),
            completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP,
            UNIQUE(user_id, module_id)
        )
    """)

    # Blog posts (WordPress-style)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS blog_posts (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255),
            slug VARCHAR(255) UNIQUE,
            content TEXT,
            excerpt TEXT,
            featured_image VARCHAR(500),
            meta_title VARCHAR(255),
            meta_description VARCHAR(255),
            meta_keywords VARCHAR(255),
            status VARCHAR(20) DEFAULT 'draft',
            published_at TIMESTAMP,
            author_id INTEGER REFERENCES users(id),
            seo_score INTEGER,
            seo_suggestions JSONB,
            views INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Blog categories
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS blog_categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            slug VARCHAR(100) UNIQUE,
            description TEXT
        )
    """)

    # Blog tags
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS blog_tags (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            slug VARCHAR(100) UNIQUE
        )
    """)

    # Post categories relationship
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS post_categories (
            post_id INTEGER REFERENCES blog_posts(id),
            category_id INTEGER REFERENCES blog_categories(id),
            PRIMARY KEY (post_id, category_id)
        )
    """)

    # Post tags relationship
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS post_tags (
            post_id INTEGER REFERENCES blog_posts(id),
            tag_id INTEGER REFERENCES blog_tags(id),
            PRIMARY KEY (post_id, tag_id)
        )
    """)

    # Media files
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS media_files (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255),
            url VARCHAR(500),
            file_type VARCHAR(50),
            file_size INTEGER,
            uploaded_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create default admin
    existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", DEFAULT_ADMIN_EMAIL)
    if not existing:
        hashed = get_password_hash(DEFAULT_ADMIN_PASSWORD)
        await conn.execute(
            "INSERT INTO users (email, password_hash, name, is_admin) VALUES ($1, $2, $3, $4)",
            DEFAULT_ADMIN_EMAIL, hashed, "Admin", True
        )

    # Create default blog categories
    categories = ["Strategy", "Psychology", "Risk Management", "Technical Analysis", "Fundamental Analysis"]
    for cat in categories:
        slug = generate_slug(cat)
        await conn.execute(
            "INSERT INTO blog_categories (name, slug, description) VALUES ($1, $2, $3) ON CONFLICT (slug) DO NOTHING",
            cat, slug, f"Articles about {cat.lower()}"
        )

    await conn.close()
    logger.info("Database initialization complete")

# ============================================================================
# FASTAPI SETUP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Pipways API", lifespan=lifespan)
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = datetime.utcnow()
    response = await call_next(request)
    duration = (datetime.utcnow() - start_time).total_seconds()
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s")
    return response

# Mount uploads directory for serving media files
from fastapi.staticfiles import StaticFiles
os.makedirs("uploads/images", exist_ok=True)
os.makedirs("uploads/videos", exist_ok=True)
os.makedirs("uploads/documents", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ============================================================================
# AUTHENTICATION
# ============================================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and return user email"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security), conn=Depends(get_db)):
    """Validate admin access"""
    email = await get_current_user(credentials)
    user = await conn.fetchrow("SELECT is_admin FROM users WHERE email = $1", email)
    if not user or not user["is_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return email

@app.post("/auth/register")
async def register(
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    conn=Depends(get_db)
):
    """Register new user"""
    existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = get_password_hash(password)
    user_id = await conn.fetchval(
        "INSERT INTO users (email, password_hash, name) VALUES ($1, $2, $3) RETURNING id",
        email, hashed, name
    )

    token = create_access_token({"sub": email})
    return {
        "access_token": token,
        "user_id": user_id,
        "email": email,
        "name": name,
        "is_admin": False
    }

@app.post("/auth/login")
async def login(email: str = Form(...), password: str = Form(...), conn=Depends(get_db)):
    """Login user"""
    user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": email})
    return {
        "access_token": token,
        "user_id": user["id"],
        "name": user["name"],
        "email": email,
        "is_admin": user["is_admin"]
    }

# ============================================================================
# AI CHART ANALYSIS
# ============================================================================

@app.post("/analyze/chart")
async def analyze_chart(
    file: UploadFile = File(...),
    pair: str = Form(...),
    timeframe: str = Form(...),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Analyze trading chart image using AI"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    # Read and encode image
    contents = await file.read()
    base64_image = base64.b64encode(contents).decode('utf-8')

    # Validate API key
    if not OPENROUTER_API_KEY:
        return {"success": False, "error": "OpenRouter API key not configured"}

    # Call OpenRouter API
    # Validate API key
    if not OPENROUTER_API_KEY:
        return {"success": False, "error": "OpenRouter API key not configured"}

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "anthropic/claude-3-opus-20240229",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Analyze this {pair} {timeframe} trading chart. Provide: 1) Trade setup quality (A/B/C grade), 2) Entry/exit points, 3) Risk/reward ratio, 4) Key support/resistance, 5) Suggested improvements. Return as JSON with fields: grade, entry_price, exit_price, stop_loss, take_profit, risk_reward, analysis, key_levels, improvements"
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                headers=headers, json=payload, timeout=30)

        # Validate response structure
        if response.status_code != 200:
            return {"success": False, "error": f"API error: {response.status_code}"}

        response_data = response.json()
        if "choices" not in response_data or not response_data["choices"]:
            return {"success": False, "error": "Invalid AI response structure"}

        ai_response = response_data["choices"][0]["message"]["content"]

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            analysis_result = json.loads(json_match.group())
        else:
            analysis_result = {"raw_analysis": ai_response}

        grade = analysis_result.get("grade", "C")

        # Save image to file instead of database
        upload_dir = "uploads/images"
        os.makedirs(upload_dir, exist_ok=True)
        timestamp = int(datetime.utcnow().timestamp())
        image_filename = f"chart_{user['id']}_{timestamp}.png"
        image_path = f"{upload_dir}/{image_filename}"

        with open(image_path, "wb") as f:
            f.write(base64.b64decode(base64_image))

        image_url = f"/uploads/images/{image_filename}"

        # Save to database (only URL, not base64)
        await conn.execute(
            "INSERT INTO chart_analyses (user_id, image_data, analysis_result, grade) VALUES ($1, $2, $3, $4)",
            user["id"], image_url, json.dumps(analysis_result), grade
        )

        return {"success": True, "analysis": analysis_result, "grade": grade}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/analyze/chart/history")
async def get_chart_history(current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    """Get user's chart analysis history"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    analyses = await conn.fetch(
        "SELECT id, analysis_result, grade, created_at FROM chart_analyses WHERE user_id = $1 ORDER BY created_at DESC",
        user["id"]
    )
    return [dict(a) for a in analyses]

# ============================================================================
# AI PERFORMANCE ANALYSIS
# ============================================================================

@app.post("/analyze/performance")
async def analyze_performance(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Analyze trading statement and generate trader profile"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    contents = await file.read()
    text_content = contents.decode('utf-8', errors='ignore')

    # Truncate if too long
    if len(text_content) > 10000:
        text_content = text_content[:10000]

    # Validate API key
    if not OPENROUTER_API_KEY:
        return {"success": False, "error": "OpenRouter API key not configured"}

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""Analyze this trading statement and provide a detailed trader profile:

    Trading Data:
    {text_content}

    Provide analysis in this JSON format:
    {{
        "trader_type": "e.g., Scalper, Day Trader, Swing Trader, Revenge Trader, FOMO Trader",
        "overall_score": "1-100",
        "strengths": ["list 3-5 strengths"],
        "weaknesses": ["list 3-5 weaknesses"],
        "key_mistakes": ["list recurring mistakes"],
        "psychology_profile": "description of trading psychology",
        "risk_management_score": "1-100",
        "strategy_effectiveness": "1-100",
        "recommendations": ["specific actionable recommendations"],
        "suggested_courses": ["course topics that would help"]
    }}
    """

    payload = {
        "model": "anthropic/claude-3-opus-20240229",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                headers=headers, json=payload, timeout=30)

        # Validate response structure
        if response.status_code != 200:
            return {"success": False, "error": f"API error: {response.status_code}"}

        response_data = response.json()
        if "choices" not in response_data or not response_data["choices"]:
            return {"success": False, "error": "Invalid AI response structure"}

        ai_response = response_data["choices"][0]["message"]["content"]

        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group())
        else:
            analysis = {"raw_analysis": ai_response}

        # Save to database
        await conn.execute(
            """INSERT INTO performance_analyses 
               (user_id, file_data, trader_type, strengths, weaknesses, recommendations, overall_score)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            user["id"],
            text_content[:2000],
            analysis.get("trader_type", "Unknown"),
            analysis.get("strengths", []),
            analysis.get("weaknesses", []),
            analysis.get("recommendations", []),
            int(analysis.get("overall_score", 50))
        )

        # Update or create user insights
        await conn.execute("""
            INSERT INTO user_insights (user_id, trader_type, personality_profile, learning_path)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO UPDATE SET
            trader_type = $2,
            personality_profile = $3,
            last_updated = CURRENT_TIMESTAMP
        """, user["id"], analysis.get("trader_type"), 
            json.dumps({"psychology": analysis.get("psychology_profile"), "score": analysis.get("overall_score")}),
            json.dumps({"suggested_courses": analysis.get("suggested_courses", [])}))

        return {"success": True, "analysis": analysis}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/analyze/performance/history")
async def get_performance_history(current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    """Get performance analysis history"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    analyses = await conn.fetch(
        "SELECT id, trader_type, overall_score, strengths, weaknesses, created_at FROM performance_analyses WHERE user_id = $1 ORDER BY created_at DESC",
        user["id"]
    )
    return [dict(a) for a in analyses]

# ============================================================================
# AI MENTOR (with LMS Integration)
# ============================================================================

@app.post("/mentor/chat")
async def mentor_chat(
    message: str = Form(...),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """AI Mentor chat with context from performance analysis"""
    user = await conn.fetchrow("SELECT id, name FROM users WHERE email = $1", current_user)

    # Get user insights
    insights = await conn.fetchrow("SELECT * FROM user_insights WHERE user_id = $1", user["id"])

    # Get recent chat history
    history = await conn.fetch(
        "SELECT message, ai_response FROM mentorship_sessions WHERE user_id = $1 ORDER BY created_at DESC LIMIT 5",
        user["id"]
    )

    # Get available courses for recommendations
    courses = await conn.fetch("SELECT id, title, category FROM courses WHERE is_published = TRUE LIMIT 10")

    # Build history text separately to avoid f-string backslash issue
    history_lines = []
    for h in reversed(history):
        history_lines.append(f"User: {h['message']}")
        history_lines.append(f"Mentor: {h['ai_response']}")
    history_text = "\n".join(history_lines)

    # Build context
    context = f"""You are a professional trading mentor. Be direct, supportive but honest.

    Student: {user['name']}
    Trader Type: {insights['trader_type'] if insights else 'Not analyzed yet'}
    Profile: {json.dumps(insights['personality_profile']) if insights else 'N/A'}

    Available Courses: {json.dumps([dict(c) for c in courses])}

    Recent conversation:
    {history_text}

    Instructions:
    - Reference their specific weaknesses/strengths if relevant
    - Suggest specific courses from the available list when appropriate
    - Keep responses concise (2-3 paragraphs max)
    - Be encouraging but hold them accountable
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "anthropic/claude-3-opus-20240229",
        "messages": [
            {"role": "system", "content": context},
            {"role": "user", "content": message}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                headers=headers, json=payload, timeout=30)

        # Validate response structure
        if response.status_code != 200:
            return {"success": False, "error": f"API error: {response.status_code}"}

        response_data = response.json()
        if "choices" not in response_data or not response_data["choices"]:
            return {"success": False, "error": "Invalid AI response structure"}

        ai_response = response_data["choices"][0]["message"]["content"]

        # Save conversation
        await conn.execute(
            "INSERT INTO mentorship_sessions (user_id, message, ai_response, context) VALUES ($1, $2, $3, $4)",
            user["id"], message, ai_response, json.dumps({"trader_type": insights["trader_type"] if insights else None})
        )

        return {"success": True, "response": ai_response}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/mentor/history")
async def get_mentor_history(current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    """Get mentorship chat history"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    sessions = await conn.fetch(
        "SELECT message, ai_response, created_at FROM mentorship_sessions WHERE user_id = $1 ORDER BY created_at DESC LIMIT 50",
        user["id"]
    )
    return [dict(s) for s in sessions]

@app.get("/mentor/insights")
async def get_mentor_insights(current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    """Get AI-generated trader insights"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    insights = await conn.fetchrow("SELECT * FROM user_insights WHERE user_id = $1", user["id"])

    if not insights:
        return {"message": "Complete a performance analysis first to get insights"}

    return {
        "trader_type": insights["trader_type"],
        "personality_profile": insights["personality_profile"],
        "learning_path": insights["learning_path"],
        "recommended_courses": insights["recommended_courses"]
    }

# ============================================================================
# WEBINARS
# ============================================================================

@app.post("/admin/webinars")
async def create_webinar(
    title: str = Form(...),
    description: str = Form(...),
    scheduled_at: str = Form(...),
    max_participants: int = Form(100),
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """Create new webinar (admin only)"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    # Create Zoom meeting if credentials available
    zoom_link = ""
    zoom_meeting_id = ""

    if ZOOM_API_KEY and ZOOM_API_SECRET:
        try:
            import jwt as zoom_jwt
            zoom_token = zoom_jwt.encode(
                {"iss": ZOOM_API_KEY, "exp": datetime.utcnow() + timedelta(hours=1)},
                ZOOM_API_SECRET,
                algorithm="HS256"
            )

            zoom_headers = {"Authorization": f"Bearer {zoom_token}", "Content-Type": "application/json"}
            zoom_payload = {
                "topic": title,
                "type": 2,
                "start_time": scheduled_at,
                "duration": 60,
                "settings": {"join_before_host": True}
            }

            zoom_response = requests.post("https://api.zoom.us/v2/users/me/meetings",
                                         headers=zoom_headers, json=zoom_payload)
            zoom_data = zoom_response.json()
            zoom_link = zoom_data.get("join_url", "")
            zoom_meeting_id = str(zoom_data.get("id", ""))
        except:
            pass

    webinar_id = await conn.fetchval(
        """INSERT INTO webinars (title, description, zoom_link, zoom_meeting_id, scheduled_at, max_participants, created_by)
           VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id""",
        title, description, zoom_link, zoom_meeting_id, scheduled_at, max_participants, user["id"]
    )

    return {"success": True, "webinar_id": webinar_id, "zoom_link": zoom_link}

@app.get("/webinars")
async def list_webinars(conn=Depends(get_db)):
    """List upcoming webinars"""
    webinars = await conn.fetch(
        """SELECT w.*, COUNT(r.id) as registered_count 
           FROM webinars w 
           LEFT JOIN webinar_registrations r ON w.id = r.webinar_id
           WHERE w.scheduled_at > NOW()
           GROUP BY w.id 
           ORDER BY w.scheduled_at"""
    )
    return [dict(w) for w in webinars]

@app.post("/webinars/{webinar_id}/register")
async def register_webinar(
    webinar_id: int,
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Register for webinar"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    try:
        await conn.execute(
            "INSERT INTO webinar_registrations (webinar_id, user_id) VALUES ($1, $2)",
            webinar_id, user["id"]
        )
        return {"success": True, "message": "Registered successfully"}
    except asyncpg.UniqueViolationError:
        return {"success": False, "message": "Already registered"}

@app.get("/webinars/my")
async def my_webinars(current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    """Get user's registered webinars"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    webinars = await conn.fetch(
        """SELECT w.* FROM webinars w
           JOIN webinar_registrations r ON w.id = r.webinar_id
           WHERE r.user_id = $1 ORDER BY w.scheduled_at""",
        user["id"]
    )
    return [dict(w) for w in webinars]

# ============================================================================
# LMS (Learning Management System)
# ============================================================================

@app.post("/admin/courses")
async def create_course(
    title: str = Form(...),
    description: str = Form(...),
    difficulty: str = Form(...),
    estimated_hours: int = Form(...),
    category: str = Form(...),
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """Create new course (admin only)"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    course_id = await conn.fetchval(
        "INSERT INTO courses (title, description, difficulty, estimated_hours, category, created_by) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id",
        title, description, difficulty, estimated_hours, category, user["id"]
    )

    return {"success": True, "course_id": course_id}

@app.post("/admin/courses/{course_id}/modules")
async def create_module(
    course_id: int,
    title: str = Form(...),
    content_type: str = Form(...),
    content: str = Form(...),
    video_url: Optional[str] = Form(None),
    order_index: int = Form(...),
    duration_minutes: int = Form(...),
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """Add module to course (admin only)"""
    module_id = await conn.fetchval(
        "INSERT INTO course_modules (course_id, title, content_type, content, video_url, order_index, duration_minutes) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id",
        course_id, title, content_type, content, video_url, order_index, duration_minutes
    )
    return {"success": True, "module_id": module_id}

@app.get("/courses")
async def list_courses(conn=Depends(get_db)):
    """List all published courses"""
    courses = await conn.fetch(
        """SELECT c.*, COUNT(cm.id) as module_count,
           (SELECT COUNT(*) FROM course_modules cm2 
            JOIN user_progress up ON cm2.id = up.module_id 
            WHERE cm2.course_id = c.id AND up.completed = TRUE) as completions
           FROM courses c
           LEFT JOIN course_modules cm ON c.id = cm.course_id
           WHERE c.is_published = TRUE
           GROUP BY c.id"""
    )
    return [dict(c) for c in courses]

@app.get("/courses/{course_id}")
async def get_course(course_id: int, current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    """Get course details with modules"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    course = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    modules = await conn.fetch(
        """SELECT cm.*, up.completed, up.completed_at 
           FROM course_modules cm
           LEFT JOIN user_progress up ON cm.id = up.module_id AND up.user_id = $1
           WHERE cm.course_id = $2 ORDER BY cm.order_index""",
        user["id"], course_id
    )

    return {
        "course": dict(course),
        "modules": [dict(m) for m in modules]
    }

@app.post("/courses/{course_id}/modules/{module_id}/complete")
async def complete_module(
    course_id: int,
    module_id: int,
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Mark module as complete"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    await conn.execute("""
        INSERT INTO user_progress (user_id, module_id, completed, completed_at)
        VALUES ($1, $2, TRUE, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id, module_id) DO UPDATE SET
        completed = TRUE, completed_at = CURRENT_TIMESTAMP
    """, user["id"], module_id)

    return {"success": True}

@app.get("/courses/recommended")
async def get_recommended_courses(current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    """Get AI-recommended courses based on user insights"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    insights = await conn.fetchrow("SELECT * FROM user_insights WHERE user_id = $1", user["id"])

    if not insights or not insights["recommended_courses"]:
        # Return default recommendations
        courses = await conn.fetch(
            "SELECT * FROM courses WHERE is_published = TRUE ORDER BY created_at DESC LIMIT 3"
        )
    else:
        courses = await conn.fetch(
            "SELECT * FROM courses WHERE id = ANY($1) AND is_published = TRUE",
            insights["recommended_courses"]
        )

    return [dict(c) for c in courses]

# ============================================================================
# BLOG (WordPress-style with SEO)
# ============================================================================

@app.post("/admin/blog/posts")
async def create_blog_post(
    title: str = Form(...),
    content: str = Form(...),
    excerpt: Optional[str] = Form(None),
    featured_image: Optional[str] = Form(None),
    featured_image_upload: Optional[UploadFile] = File(None),  # Allow direct upload
    meta_title: Optional[str] = Form(None),
    meta_description: Optional[str] = Form(None),
    meta_keywords: Optional[str] = Form(None),
    category_ids: Optional[str] = Form(""),
    tag_ids: Optional[str] = Form(""),
    status: str = Form("draft"),
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """Create blog post (admin only)"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    # Handle featured image upload
    if featured_image_upload and not featured_image:
        # Save uploaded image
        upload_dir = "uploads/images"
        os.makedirs(upload_dir, exist_ok=True)

        timestamp = int(datetime.utcnow().timestamp())
        safe_filename = re.sub(r'[^\w\.]', '_', featured_image_upload.filename)
        unique_filename = f"blog_{timestamp}_{safe_filename}"
        file_path = f"{upload_dir}/{unique_filename}"

        contents = await featured_image_upload.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        featured_image = f"/uploads/images/{unique_filename}"

        # Save to media library
        await conn.execute(
            "INSERT INTO media_files (filename, url, file_type, file_size, uploaded_by) VALUES ($1, $2, $3, $4, $5) ON CONFLICT (url) DO NOTHING",
            unique_filename, featured_image, "image", len(contents), user["id"]
        )

    slug = generate_slug(title)

    # Calculate SEO score
    seo_data = calculate_seo_score(title, content, meta_description or "")

    # Check for unique slug
    existing = await conn.fetchrow("SELECT id FROM blog_posts WHERE slug = $1", slug)
    if existing:
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

    published_at = None
    if status == "published":
        published_at = datetime.utcnow()

    post_id = await conn.fetchval(
        """INSERT INTO blog_posts 
           (title, slug, content, excerpt, featured_image, meta_title, meta_description, meta_keywords, 
            status, published_at, author_id, seo_score, seo_suggestions)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13) RETURNING id""",
        title, slug, content, excerpt, featured_image, meta_title or title, 
        meta_description, meta_keywords, status, published_at, user["id"], seo_data["score"], 
        json.dumps(seo_data["suggestions"])
    )

    # Add categories
    if category_ids:
        cat_ids = [int(x) for x in category_ids.split(",") if x]
        for cat_id in cat_ids:
            await conn.execute("INSERT INTO post_categories (post_id, category_id) VALUES ($1, $2) ON CONFLICT (post_id, category_id) DO NOTHING",
                             post_id, cat_id)

    # Add tags
    if tag_ids:
        t_ids = [int(x) for x in tag_ids.split(",") if x]
        for t_id in t_ids:
            await conn.execute("INSERT INTO post_tags (post_id, tag_id) VALUES ($1, $2) ON CONFLICT (post_id, tag_id) DO NOTHING",
                             post_id, t_id)

    return {"success": True, "post_id": post_id, "slug": slug, "seo_score": seo_data["score"], "suggestions": seo_data["suggestions"]}

@app.put("/admin/blog/posts/{post_id}")
async def update_blog_post(
    post_id: int,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    excerpt: Optional[str] = Form(None),
    featured_image: Optional[str] = Form(None),
    meta_title: Optional[str] = Form(None),
    meta_description: Optional[str] = Form(None),
    meta_keywords: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """Update blog post (admin only)"""

    updates = []
    values = []

    if title:
        updates.append("title = $" + str(len(values) + 1))
        values.append(title)
        updates.append("slug = $" + str(len(values) + 1))
        values.append(generate_slug(title))
    if content:
        updates.append("content = $" + str(len(values) + 1))
        values.append(content)
    if excerpt is not None:
        updates.append("excerpt = $" + str(len(values) + 1))
        values.append(excerpt)
    if featured_image is not None:
        updates.append("featured_image = $" + str(len(values) + 1))
        values.append(featured_image)
    if meta_title:
        updates.append("meta_title = $" + str(len(values) + 1))
        values.append(meta_title)
    if meta_description is not None:
        updates.append("meta_description = $" + str(len(values) + 1))
        values.append(meta_description)
    if meta_keywords is not None:
        updates.append("meta_keywords = $" + str(len(values) + 1))
        values.append(meta_keywords)
    if status:
        updates.append("status = $" + str(len(values) + 1))
        values.append(status)
        if status == "published":
            updates.append("published_at = $" + str(len(values) + 1))
            values.append(datetime.utcnow())

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE blog_posts SET {', '.join(updates)} WHERE id = ${len(values) + 1}"
        values.append(post_id)
        await conn.execute(query, *values)

    return {"success": True}

@app.get("/blog/posts")
async def list_blog_posts(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
    conn=Depends(get_db)
):
    """List published blog posts with filtering"""

    where_clauses = ["status = 'published'"]
    params = []

    if category:
        where_clauses.append(f"id IN (SELECT post_id FROM post_categories pc JOIN blog_categories bc ON pc.category_id = bc.id WHERE bc.slug = ${len(params) + 1})")
        params.append(category)

    if tag:
        where_clauses.append(f"id IN (SELECT post_id FROM post_tags pt JOIN blog_tags bt ON pt.tag_id = bt.id WHERE bt.slug = ${len(params) + 1})")
        params.append(tag)

    if search:
        where_clauses.append(f"(title ILIKE ${len(params) + 1} OR content ILIKE ${len(params) + 1})")
        params.append(f"%{search}%")

    where_str = " AND ".join(where_clauses)

    # Get total count
    count_query = f"SELECT COUNT(*) FROM blog_posts WHERE {where_str}"
    total = await conn.fetchval(count_query, *params)

    # Get posts
    query = f"""SELECT bp.*, u.name as author_name,
                ARRAY_AGG(DISTINCT bc.name) as categories,
                ARRAY_AGG(DISTINCT bt.name) as tags
                FROM blog_posts bp
                JOIN users u ON bp.author_id = u.id
                LEFT JOIN post_categories pc ON bp.id = pc.post_id
                LEFT JOIN blog_categories bc ON pc.category_id = bc.id
                LEFT JOIN post_tags pt ON bp.id = pt.post_id
                LEFT JOIN blog_tags bt ON pt.tag_id = bt.id
                WHERE {where_str}
                GROUP BY bp.id, u.name
                ORDER BY bp.published_at DESC
                LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"""

    params.extend([per_page, (page - 1) * per_page])
    posts = await conn.fetch(query, *params)

    return {
        "posts": [dict(p) for p in posts],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

@app.get("/blog/posts/{slug}")
async def get_blog_post(slug: str, conn=Depends(get_db)):
    """Get single blog post by slug"""

    # Increment views
    await conn.execute("UPDATE blog_posts SET views = views + 1 WHERE slug = $1", slug)

    post = await conn.fetchrow("""SELECT bp.*, u.name as author_name,
                                  ARRAY_AGG(DISTINCT bc.name) as categories,
                                  ARRAY_AGG(DISTINCT bt.name) as tags
                                  FROM blog_posts bp
                                  JOIN users u ON bp.author_id = u.id
                                  LEFT JOIN post_categories pc ON bp.id = pc.post_id
                                  LEFT JOIN blog_categories bc ON pc.category_id = bc.id
                                  LEFT JOIN post_tags pt ON bp.id = pt.post_id
                                  LEFT JOIN blog_tags bt ON pt.tag_id = bt.id
                                  WHERE bp.slug = $1 AND bp.status = 'published'
                                  GROUP BY bp.id, u.name""", slug)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return dict(post)

@app.get("/blog/categories")
async def list_categories(conn=Depends(get_db)):
    """List all blog categories"""
    categories = await conn.fetch("""SELECT bc.*, COUNT(pc.post_id) as post_count 
                                     FROM blog_categories bc
                                     LEFT JOIN post_categories pc ON bc.id = pc.category_id
                                     LEFT JOIN blog_posts bp ON pc.post_id = bp.id AND bp.status = 'published'
                                     GROUP BY bc.id""")
    return [dict(c) for c in categories]

@app.get("/blog/tags")
async def list_tags(conn=Depends(get_db)):
    """List all blog tags"""
    tags = await conn.fetch("""SELECT bt.*, COUNT(pt.post_id) as post_count 
                               FROM blog_tags bt
                               LEFT JOIN post_tags pt ON bt.id = pt.tag_id
                               LEFT JOIN blog_posts bp ON pt.post_id = bp.id AND bp.status = 'published'
                               GROUP BY bt.id""")
    return [dict(t) for t in tags]

@app.get("/blog/sitemap.xml")
async def generate_sitemap(conn=Depends(get_db)):
    """Generate XML sitemap for SEO"""
    posts = await conn.fetch("SELECT slug, updated_at FROM blog_posts WHERE status = 'published'")

    root = ET.Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    # Homepage
    url = ET.SubElement(root, "url")
    ET.SubElement(url, "loc").text = "https://pipways.com/"
    ET.SubElement(url, "changefreq").text = "daily"
    ET.SubElement(url, "priority").text = "1.0"

    # Blog posts
    for post in posts:
        url = ET.SubElement(root, "url")
        ET.SubElement(url, "loc").text = f"https://pipways.com/blog/{post['slug']}"
        ET.SubElement(url, "lastmod").text = post["updated_at"].isoformat()
        ET.SubElement(url, "changefreq").text = "weekly"
        ET.SubElement(url, "priority").text = "0.8"

    xml_str = ET.tostring(root, encoding='unicode')
    return HTMLResponse(content=xml_str, media_type="application/xml")


# ============================================================================
# MEDIA UPLOADS (for Blog and Content)
# ============================================================================

@app.post("/admin/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """Upload media file (images, videos, documents) for blog/content"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    # Validate file type
    allowed_types = {
        'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'],
        'video': ['video/mp4', 'video/webm', 'video/ogg'],
        'document': ['application/pdf', 'text/plain', 'application/msword', 
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    }

    file_type = None
    for category, types in allowed_types.items():
        if file.content_type in types:
            file_type = category
            break

    if not file_type:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed")

    # Create uploads directory if not exists
    upload_dir = f"uploads/{file_type}s"
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    timestamp = int(datetime.utcnow().timestamp())
    safe_filename = re.sub(r'[^\w\.]', '_', file.filename)
    unique_filename = f"{timestamp}_{safe_filename}"
    file_path = f"{upload_dir}/{unique_filename}"

    # Save file
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    # Determine URL path
    file_size = len(contents)
    url_path = f"/uploads/{file_type}s/{unique_filename}"

    # Save to database
    media_id = await conn.fetchval(
        "INSERT INTO media_files (filename, url, file_type, file_size, uploaded_by) VALUES ($1, $2, $3, $4, $5) ON CONFLICT (url) DO NOTHING RETURNING id",
        unique_filename, url_path, file_type, file_size, user["id"]
    )

    return {
        "success": True,
        "media_id": media_id,
        "url": url_path,
        "filename": unique_filename,
        "type": file_type,
        "size": file_size
    }

@app.get("/admin/media")
async def list_media(
    file_type: Optional[str] = None,
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """List all uploaded media files (admin only)"""
    if file_type:
        media = await conn.fetch(
            "SELECT m.*, u.name as uploaded_by_name FROM media_files m JOIN users u ON m.uploaded_by = u.id WHERE m.file_type = $1 ORDER BY m.created_at DESC",
            file_type
        )
    else:
        media = await conn.fetch(
            "SELECT m.*, u.name as uploaded_by_name FROM media_files m JOIN users u ON m.uploaded_by = u.id ORDER BY m.created_at DESC"
        )
    return [dict(m) for m in media]

@app.delete("/admin/media/{media_id}")
async def delete_media(
    media_id: int,
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """Delete media file (admin only)"""
    media = await conn.fetchrow("SELECT * FROM media_files WHERE id = $1", media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    # Delete physical file
    file_path = media["url"].lstrip("/")
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete from database
    await conn.execute("DELETE FROM media_files WHERE id = $1", media_id)

    return {"success": True, "message": "Media deleted"}

@app.get("/uploads/{file_type}/{filename}")
async def serve_media(file_type: str, filename: str):
    """Serve uploaded media files"""
    file_path = f"uploads/{file_type}s/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Determine content type
    content_types = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.png': 'image/png', '.gif': 'image/gif',
        '.webp': 'image/webp', '.svg': 'image/svg+xml',
        '.mp4': 'video/mp4', '.webm': 'video/webm',
        '.pdf': 'application/pdf'
    }

    ext = os.path.splitext(filename)[1].lower()
    content_type = content_types.get(ext, 'application/octet-stream')

    return FileResponse(file_path, media_type=content_type)


@app.get("/admin/media/browser")
async def media_browser(
    type: Optional[str] = "image",
    page: int = 1,
    per_page: int = 20,
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """Media browser for frontend editor (paginated)"""
    offset = (page - 1) * per_page

    total = await conn.fetchval(
        "SELECT COUNT(*) FROM media_files WHERE file_type = $1",
        type
    )

    media = await conn.fetch(
        """SELECT id, url, filename, file_type, file_size, created_at 
           FROM media_files 
           WHERE file_type = $1 
           ORDER BY created_at DESC 
           LIMIT $2 OFFSET $3""",
        type, per_page, offset
    )

    return {
        "media": [dict(m) for m in media],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

# ============================================================================
# ADMIN DASHBOARD
# ============================================================================

@app.get("/admin/stats")
async def admin_stats(current_user: str = Depends(get_current_admin), conn=Depends(get_db)):
    """Get admin dashboard statistics"""

    stats = {
        "users": await conn.fetchval("SELECT COUNT(*) FROM users"),
        "chart_analyses": await conn.fetchval("SELECT COUNT(*) FROM chart_analyses"),
        "performance_analyses": await conn.fetchval("SELECT COUNT(*) FROM performance_analyses"),
        "courses": await conn.fetchval("SELECT COUNT(*) FROM courses"),
        "published_courses": await conn.fetchval("SELECT COUNT(*) FROM courses WHERE is_published = TRUE"),
        "webinars": await conn.fetchval("SELECT COUNT(*) FROM webinars WHERE scheduled_at > NOW()"),
        "blog_posts": await conn.fetchval("SELECT COUNT(*) FROM blog_posts"),
        "published_posts": await conn.fetchval("SELECT COUNT(*) FROM blog_posts WHERE status = 'published'"),
        "total_views": await conn.fetchval("SELECT COALESCE(SUM(views), 0) FROM blog_posts")
    }

    return stats

@app.get("/admin/users")
async def list_users(current_user: str = Depends(get_current_admin), conn=Depends(get_db)):
    """List all users (admin only)"""
    users = await conn.fetch("SELECT id, email, name, is_admin, created_at FROM users ORDER BY created_at DESC")
    return [dict(u) for u in users]


@app.get("/debug/admin")
async def debug_admin(conn=Depends(get_db)):
    """Debug endpoint to check admin user status"""
    try:
        # Check users table
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """)

        if not table_exists:
            return {"error": "Users table does not exist", "fix": "Restart server to trigger init_db()"}

        # Count users
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")

        # Check admin
        admin = await conn.fetchrow(
            "SELECT id, email, is_admin, created_at FROM users WHERE email = $1",
            DEFAULT_ADMIN_EMAIL
        )

        return {
            "users_table_exists": True,
            "total_users": user_count,
            "admin_configured": DEFAULT_ADMIN_EMAIL,
            "admin_password_configured": DEFAULT_ADMIN_PASSWORD,
            "admin_found_in_db": dict(admin) if admin else None,
            "login_credentials": {
                "email": DEFAULT_ADMIN_EMAIL,
                "password": DEFAULT_ADMIN_PASSWORD
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/debug/fix-admin")
async def debug_fix_admin(conn=Depends(get_db)):
    """Emergency admin creation"""
    try:
        # Ensure table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(100),
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Check existing
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1", DEFAULT_ADMIN_EMAIL
        )

        if existing:
            return {"message": "Admin already exists", "email": DEFAULT_ADMIN_EMAIL}

        # Create admin
        hashed = get_password_hash(DEFAULT_ADMIN_PASSWORD)
        await conn.execute(
            "INSERT INTO users (email, password_hash, name, is_admin) VALUES ($1, $2, $3, $4)",
            DEFAULT_ADMIN_EMAIL, hashed, "Admin", True
        )

        return {
            "message": "Admin created successfully",
            "email": DEFAULT_ADMIN_EMAIL,
            "password": DEFAULT_ADMIN_PASSWORD
        }
    except Exception as e:
        return {"error": str(e)}

# ============================================================================
# FRONTEND SERVING
# ============================================================================
# FRONTEND SERVING
# ============================================================================

@app.get("/")
async def root():
    """Serve frontend from root directory"""
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head><title>Pipways</title></head>
    <body>
        <h1>Pipways API is running</h1>
        <p>Frontend not found. Please place index.html in the root folder.</p>
        <p>API Documentation: <a href="/docs">/docs</a></p>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": ["chart_analysis", "performance_analysis", "ai_mentor", "webinars", "lms", "blog"],
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
