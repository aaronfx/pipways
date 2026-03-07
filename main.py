"""
Pipways Trading Education Platform
Complete FastAPI application with all endpoints for the updated frontend
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
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Form, UploadFile, File, HTTPException, Depends, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
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

    # Trades table - NEW
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            pair VARCHAR(20) NOT NULL,
            direction VARCHAR(10) NOT NULL CHECK (direction IN ('LONG', 'SHORT')),
            pips DECIMAL(10,2) NOT NULL,
            grade VARCHAR(5) DEFAULT 'C' CHECK (grade IN ('A', 'B', 'C', 'D', 'F')),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Chart analyses
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS chart_analyses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            image_data TEXT,
            pair VARCHAR(20),
            timeframe VARCHAR(10),
            analysis_result JSONB,
            grade VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Performance analyses
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS performance_analyses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            file_data TEXT,
            trader_type VARCHAR(100),
            strengths TEXT[],
            weaknesses TEXT[],
            key_mistakes TEXT[],
            recommendations TEXT[],
            overall_score INTEGER,
            risk_management_score INTEGER,
            strategy_effectiveness INTEGER,
            psychology_score INTEGER,
            discipline_score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # AI Mentor sessions
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS mentorship_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            message TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            context JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # User insights (AI-generated profile)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_insights (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
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
            title VARCHAR(255) NOT NULL,
            description TEXT,
            zoom_link VARCHAR(500),
            zoom_meeting_id VARCHAR(100),
            scheduled_at TIMESTAMP NOT NULL,
            max_participants INTEGER DEFAULT 100,
            status VARCHAR(20) DEFAULT 'UPCOMING',
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Webinar registrations
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS webinar_registrations (
            id SERIAL PRIMARY KEY,
            webinar_id INTEGER REFERENCES webinars(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(webinar_id, user_id)
        )
    """)

    # LMS Courses
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
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
            course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            content_type VARCHAR(50),
            content TEXT,
            video_url VARCHAR(500),
            order_index INTEGER DEFAULT 0,
            duration_minutes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # User progress
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            module_id INTEGER REFERENCES course_modules(id) ON DELETE CASCADE,
            completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP,
            UNIQUE(user_id, module_id)
        )
    """)

    # Course enrollments - NEW
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS course_enrollments (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, course_id)
        )
    """)

    # Blog posts (WordPress-style)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS blog_posts (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            slug VARCHAR(255) UNIQUE NOT NULL,
            content TEXT NOT NULL,
            excerpt TEXT,
            featured_image VARCHAR(500),
            meta_title VARCHAR(255),
            meta_description VARCHAR(255),
            meta_keywords VARCHAR(255),
            status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
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
            name VARCHAR(100) UNIQUE NOT NULL,
            slug VARCHAR(100) UNIQUE NOT NULL,
            description TEXT
        )
    """)

    # Blog tags
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS blog_tags (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            slug VARCHAR(100) UNIQUE NOT NULL
        )
    """)

    # Post categories relationship
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS post_categories (
            post_id INTEGER REFERENCES blog_posts(id) ON DELETE CASCADE,
            category_id INTEGER REFERENCES blog_categories(id) ON DELETE CASCADE,
            PRIMARY KEY (post_id, category_id)
        )
    """)

    # Post tags relationship
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS post_tags (
            post_id INTEGER REFERENCES blog_posts(id) ON DELETE CASCADE,
            tag_id INTEGER REFERENCES blog_tags(id) ON DELETE CASCADE,
            PRIMARY KEY (post_id, tag_id)
        )
    """)

    # Media files
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS media_files (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            url VARCHAR(500) UNIQUE NOT NULL,
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
        logger.info(f"Default admin created: {DEFAULT_ADMIN_EMAIL}")

    # Create default blog categories
    categories = [
        ("Strategy", "strategy", "Trading strategies and methodologies"),
        ("Psychology", "psychology", "Trading psychology and mental game"),
        ("Risk Management", "risk-management", "Position sizing and risk control"),
        ("Technical Analysis", "technical-analysis", "Charts, patterns, and indicators"),
        ("Fundamental Analysis", "fundamental-analysis", "Economic events and news trading"),
        ("Education", "education", "General trading education")
    ]
    for name, slug, desc in categories:
        await conn.execute(
            "INSERT INTO blog_categories (name, slug, description) VALUES ($1, $2, $3) ON CONFLICT (slug) DO NOTHING",
            name, slug, desc
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

app = FastAPI(title="Pipways API", version="2.0.0", lifespan=lifespan)
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domains in production
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

# Mount uploads directory
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
    # Validate email format
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    # Validate password length
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

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
# TRADE JOURNAL - NEW ENDPOINTS
# ============================================================================

@app.post("/trades")
async def create_trade(
    pair: str = Form(...),
    direction: str = Form(...),
    pips: float = Form(...),
    grade: str = Form("C"),
    notes: Optional[str] = Form(None),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Create a new trade entry"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    # Validate inputs
    pair = pair.upper().strip()
    if len(pair) != 6 or not pair.isalpha():
        raise HTTPException(status_code=400, detail="Invalid currency pair format (e.g., EURUSD)")

    direction = direction.upper()
    if direction not in ["LONG", "SHORT"]:
        raise HTTPException(status_code=400, detail="Direction must be LONG or SHORT")

    grade = grade.upper()
    if grade not in ["A", "B", "C", "D", "F"]:
        grade = "C"

    trade_id = await conn.fetchval(
        """INSERT INTO trades (user_id, pair, direction, pips, grade, notes) 
           VALUES ($1, $2, $3, $4, $5, $6) RETURNING id""",
        user["id"], pair, direction, pips, grade, notes
    )

    return {
        "success": True,
        "trade_id": trade_id,
        "message": "Trade logged successfully"
    }

@app.get("/trades")
async def get_trades(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Get user's trade history"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    trades = await conn.fetch(
        """SELECT * FROM trades 
           WHERE user_id = $1 
           ORDER BY created_at DESC 
           LIMIT $2 OFFSET $3""",
        user["id"], limit, offset
    )
    return [dict(t) for t in trades]

@app.get("/trades/stats")
async def get_trade_stats(current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    """Get trading statistics"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    stats = await conn.fetchrow(
        """SELECT 
            COUNT(*) as total_trades,
            COUNT(CASE WHEN pips > 0 THEN 1 END) as winning_trades,
            COUNT(CASE WHEN pips < 0 THEN 1 END) as losing_trades,
            SUM(pips) as total_pips,
            AVG(pips) as avg_pips,
            AVG(CASE WHEN pips > 0 THEN pips END) as avg_win,
            AVG(CASE WHEN pips < 0 THEN pips END) as avg_loss
           FROM trades 
           WHERE user_id = $1""",
        user["id"]
    )

    return dict(stats) if stats else {}

# ============================================================================
# AI CHART ANALYSIS
# ============================================================================

@app.post("/analyze/chart")
async def analyze_chart(
    file: UploadFile = File(...),
    pair: Optional[str] = Form("UNKNOWN"),
    timeframe: Optional[str] = Form("1H"),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Analyze trading chart image using AI"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    # Validate file size (10MB max)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max size is 10MB.")

    base64_image = base64.b64encode(contents).decode('utf-8')

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
                        "text": f"Analyze this {pair} {timeframe} trading chart. Provide detailed analysis including: 1) Trade setup quality (A/B/C grade), 2) Entry/exit points with specific prices, 3) Risk/reward ratio, 4) Key support/resistance levels, 5) Suggested improvements. Return as JSON with fields: grade, pair, direction, entry_price, stop_loss, take_profit, risk_reward, analysis, key_levels, recommendations"
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
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions", 
            headers=headers, 
            json=payload, 
            timeout=60
        )

        if response.status_code != 200:
            return {"success": False, "error": f"API error: {response.status_code}"}

        response_data = response.json()
        if "choices" not in response_data or not response_data["choices"]:
            return {"success": False, "error": "Invalid AI response structure"}

        ai_response = response_data["choices"][0]["message"]["content"]

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            try:
                analysis_result = json.loads(json_match.group())
            except json.JSONDecodeError:
                analysis_result = {"raw_analysis": ai_response}
        else:
            analysis_result = {"raw_analysis": ai_response}

        grade = analysis_result.get("grade", "C")

        # Save image to file
        upload_dir = "uploads/images"
        os.makedirs(upload_dir, exist_ok=True)
        timestamp = int(datetime.utcnow().timestamp())
        image_filename = f"chart_{user['id']}_{timestamp}.png"
        image_path = f"{upload_dir}/{image_filename}"

        with open(image_path, "wb") as f:
            f.write(base64.b64decode(base64_image))

        image_url = f"/uploads/images/{image_filename}"

        # Save to database
        await conn.execute(
            """INSERT INTO chart_analyses 
               (user_id, image_data, pair, timeframe, analysis_result, grade) 
               VALUES ($1, $2, $3, $4, $5, $6)""",
            user["id"], image_url, pair, timeframe, json.dumps(analysis_result), grade
        )

        return {"success": True, "analysis": analysis_result, "grade": grade}

    except Exception as e:
        logger.error(f"Chart analysis error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/analyze/chart/history")
async def get_chart_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Get user's chart analysis history"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    analyses = await conn.fetch(
        """SELECT id, pair, timeframe, analysis_result, grade, created_at 
           FROM chart_analyses 
           WHERE user_id = $1 
           ORDER BY created_at DESC 
           LIMIT $2""",
        user["id"], limit
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

    # Validate file size (10MB max)
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max size is 10MB.")

    try:
        text_content = contents.decode('utf-8', errors='ignore')
    except:
        text_content = "[Binary file - content extracted via OCR would go here]"

    # Truncate if too long
    if len(text_content) > 15000:
        text_content = text_content[:15000] + "..."

    if not OPENROUTER_API_KEY:
        return {"success": False, "error": "OpenRouter API key not configured"}

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""Analyze this trading statement and provide a comprehensive trader profile:

Trading Data:
{text_content[:5000]}

Provide analysis in this exact JSON format:
{{
    "trader_type": "e.g., Scalper, Day Trader, Swing Trader, Position Trader, or specific style like Revenge Trader, FOMO Trader",
    "overall_score": 75,
    "risk_management_score": 80,
    "strategy_effectiveness": 70,
    "psychology_score": 75,
    "discipline_score": 65,
    "strengths": ["List 3-5 specific strengths"],
    "weaknesses": ["List 3-5 specific weaknesses"],
    "key_mistakes": ["List 2-4 recurring mistakes"],
    "psychology_profile": "Detailed description of trading psychology and behavioral patterns",
    "recommendations": ["5-7 specific actionable recommendations"],
    "suggested_courses": ["List 3-5 course topics that would help this trader"]
}}

Be specific and actionable. Use real trading terminology."""

    payload = {
        "model": "anthropic/claude-3-opus-20240229",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers, 
            json=payload, 
            timeout=90
        )

        if response.status_code != 200:
            return {"success": False, "error": f"API error: {response.status_code}"}

        response_data = response.json()
        if "choices" not in response_data or not response_data["choices"]:
            return {"success": False, "error": "Invalid AI response structure"}

        ai_response = response_data["choices"][0]["message"]["content"]

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            try:
                analysis = json.loads(json_match.group())
            except json.JSONDecodeError:
                analysis = {"raw_analysis": ai_response}
        else:
            analysis = {"raw_analysis": ai_response}

        # Save to database
        await conn.execute(
            """INSERT INTO performance_analyses 
               (user_id, file_data, trader_type, strengths, weaknesses, key_mistakes, 
                recommendations, overall_score, risk_management_score, strategy_effectiveness,
                psychology_score, discipline_score) 
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)""",
            user["id"],
            text_content[:2000],
            analysis.get("trader_type", "Unknown"),
            analysis.get("strengths", []),
            analysis.get("weaknesses", []),
            analysis.get("key_mistakes", []),
            analysis.get("recommendations", []),
            int(analysis.get("overall_score", 50)),
            int(analysis.get("risk_management_score", 50)),
            int(analysis.get("strategy_effectiveness", 50)),
            int(analysis.get("psychology_score", 50)),
            int(analysis.get("discipline_score", 50))
        )

        # Update or create user insights
        await conn.execute("""
            INSERT INTO user_insights (user_id, trader_type, personality_profile, learning_path)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO UPDATE SET
            trader_type = $2,
            personality_profile = $3,
            learning_path = $4,
            last_updated = CURRENT_TIMESTAMP
        """, 
            user["id"], 
            analysis.get("trader_type"),
            json.dumps({
                "psychology": analysis.get("psychology_profile"),
                "score": analysis.get("overall_score"),
                "risk_score": analysis.get("risk_management_score"),
                "strategy_score": analysis.get("strategy_effectiveness")
            }),
            json.dumps({"suggested_courses": analysis.get("suggested_courses", [])})
        )

        return {"success": True, "analysis": analysis}

    except Exception as e:
        logger.error(f"Performance analysis error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/analyze/performance/history")
async def get_performance_history(
    limit: int = Query(10, ge=1, le=50),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Get performance analysis history"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    analyses = await conn.fetch(
        """SELECT id, trader_type, overall_score, strengths, weaknesses, 
                  risk_management_score, strategy_effectiveness, created_at 
           FROM performance_analyses 
           WHERE user_id = $1 
           ORDER BY created_at DESC 
           LIMIT $2""",
        user["id"], limit
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

    # Get recent chat history (last 10 messages for context)
    history = await conn.fetch(
        """SELECT message, ai_response 
           FROM mentorship_sessions 
           WHERE user_id = $1 
           ORDER BY created_at DESC 
           LIMIT 10""",
        user["id"]
    )

    # Get available courses for recommendations
    courses = await conn.fetch(
        "SELECT id, title, category FROM courses WHERE is_published = TRUE LIMIT 10"
    )

    # Build conversation history
    history_text = ""
    for h in reversed(history):
        history_text += f"\nUser: {h['message']}\nMentor: {h['ai_response']}"

    # Build context
    context = f"""You are a professional trading mentor and psychologist. Be direct, supportive but honest. Your goal is to help traders improve their performance and mindset.

Student: {user['name']}
Trader Type: {insights['trader_type'] if insights else 'Not analyzed yet'}
Profile: {json.dumps(insights['personality_profile']) if insights else 'N/A'}

Available Courses: {json.dumps([dict(c) for c in courses])}

Recent conversation:{history_text}

Instructions:
- Reference their specific weaknesses/strengths if relevant to their question
- Suggest specific courses from the available list when appropriate
- Keep responses concise (2-4 paragraphs max)
- Be encouraging but hold them accountable
- If they ask about their performance, reference their analysis data
- Use trading terminology appropriately
- For psychological issues, provide actionable coping strategies"""

    if not OPENROUTER_API_KEY:
        return {"success": False, "error": "OpenRouter API key not configured"}

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "anthropic/claude-3-opus-20240229",
        "messages": [
            {"role": "system", "content": context},
            {"role": "user", "content": message}
        ],
        "temperature": 0.8,
        "max_tokens": 1000
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers, 
            json=payload, 
            timeout=60
        )

        if response.status_code != 200:
            return {"success": False, "error": f"API error: {response.status_code}"}

        response_data = response.json()
        if "choices" not in response_data or not response_data["choices"]:
            return {"success": False, "error": "Invalid AI response"}

        ai_response = response_data["choices"][0]["message"]["content"]

        # Save conversation
        await conn.execute(
            """INSERT INTO mentorship_sessions (user_id, message, ai_response, context) 
               VALUES ($1, $2, $3, $4)""",
            user["id"], 
            message, 
            ai_response, 
            json.dumps({"trader_type": insights["trader_type"] if insights else None})
        )

        return {"success": True, "response": ai_response}

    except Exception as e:
        logger.error(f"Mentor chat error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/mentor/history")
async def get_mentor_history(
    limit: int = Query(50, ge=1, le=100),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Get mentorship chat history"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    sessions = await conn.fetch(
        """SELECT message, ai_response, created_at 
           FROM mentorship_sessions 
           WHERE user_id = $1 
           ORDER BY created_at DESC 
           LIMIT $2""",
        user["id"], limit
    )
    return [dict(s) for s in sessions]

@app.get("/mentor/insights")
async def get_mentor_insights(current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    """Get AI-generated trader insights"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    insights = await conn.fetchrow("SELECT * FROM user_insights WHERE user_id = $1", user["id"])

    if not insights:
        return {
            "message": "Complete a performance analysis first to get personalized insights",
            "trader_type": None
        }

    return {
        "trader_type": insights["trader_type"],
        "personality_profile": insights["personality_profile"],
        "learning_path": insights["learning_path"],
        "recommended_courses": insights["recommended_courses"],
        "last_updated": insights["last_updated"].isoformat() if insights["last_updated"] else None
    }

# ============================================================================
# WEBINARS
# ============================================================================

@app.post("/admin/webinars")
async def create_webinar(
    title: str = Form(...),
    description: str = Form(...),
    scheduled_at: str = Form(...),  # ISO format datetime
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

            zoom_headers = {
                "Authorization": f"Bearer {zoom_token}",
                "Content-Type": "application/json"
            }
            zoom_payload = {
                "topic": title,
                "type": 2,  # Scheduled meeting
                "start_time": scheduled_at,
                "duration": 60,
                "settings": {
                    "join_before_host": True,
                    "waiting_room": False
                }
            }

            zoom_response = requests.post(
                "https://api.zoom.us/v2/users/me/meetings",
                headers=zoom_headers, 
                json=zoom_payload,
                timeout=30
            )

            if zoom_response.status_code == 201:
                zoom_data = zoom_response.json()
                zoom_link = zoom_data.get("join_url", "")
                zoom_meeting_id = str(zoom_data.get("id", ""))
        except Exception as e:
            logger.error(f"Zoom integration error: {e}")

    webinar_id = await conn.fetchval(
        """INSERT INTO webinars 
           (title, description, zoom_link, zoom_meeting_id, scheduled_at, max_participants, created_by) 
           VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id""",
        title, description, zoom_link, zoom_meeting_id, scheduled_at, max_participants, user["id"]
    )

    return {
        "success": True, 
        "webinar_id": webinar_id, 
        "zoom_link": zoom_link,
        "message": "Webinar created successfully"
    }

@app.get("/webinars")
async def list_webinars(conn=Depends(get_db)):
    """List upcoming webinars with registration counts"""
    webinars = await conn.fetch(
        """SELECT w.*, COUNT(r.id) as registered_count 
           FROM webinars w 
           LEFT JOIN webinar_registrations r ON w.id = r.webinar_id
           WHERE w.scheduled_at > NOW() - INTERVAL '1 hour'
           GROUP BY w.id 
           ORDER BY w.scheduled_at"""
    )
    return [dict(w) for w in webinars]

@app.get("/webinars/my")
async def my_webinars(current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    """Get user's registered webinars"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    webinars = await conn.fetch(
        """SELECT w.*, r.registered_at 
           FROM webinars w
           JOIN webinar_registrations r ON w.id = r.webinar_id
           WHERE r.user_id = $1 
           AND w.scheduled_at > NOW() - INTERVAL '1 hour'
           ORDER BY w.scheduled_at""",
        user["id"]
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

    # Check if webinar exists and has space
    webinar = await conn.fetchrow(
        """SELECT w.*, COUNT(r.id) as registered_count 
           FROM webinars w 
           LEFT JOIN webinar_registrations r ON w.id = r.webinar_id
           WHERE w.id = $1 
           GROUP BY w.id""",
        webinar_id
    )

    if not webinar:
        raise HTTPException(status_code=404, detail="Webinar not found")

    if webinar["registered_count"] >= webinar["max_participants"]:
        return {"success": False, "message": "Webinar is full"}

    try:
        await conn.execute(
            "INSERT INTO webinar_registrations (webinar_id, user_id) VALUES ($1, $2)",
            webinar_id, user["id"]
        )
        return {
            "success": True, 
            "message": "Registered successfully",
            "zoom_link": webinar["zoom_link"]
        }
    except asyncpg.UniqueViolationError:
        return {"success": False, "message": "Already registered"}

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
        """INSERT INTO courses 
           (title, description, difficulty, estimated_hours, category, created_by) 
           VALUES ($1, $2, $3, $4, $5, $6) RETURNING id""",
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
    order_index: int = Form(0),
    duration_minutes: int = Form(0),
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """Add module to course (admin only)"""
    module_id = await conn.fetchval(
        """INSERT INTO course_modules 
           (course_id, title, content_type, content, video_url, order_index, duration_minutes) 
           VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id""",
        course_id, title, content_type, content, video_url, order_index, duration_minutes
    )
    return {"success": True, "module_id": module_id}

@app.get("/courses")
async def list_courses(conn=Depends(get_db)):
    """List all published courses with stats"""
    courses = await conn.fetch(
        """SELECT c.*, 
                  COUNT(DISTINCT cm.id) as module_count,
                  COUNT(DISTINCT ce.user_id) as enrollments,
                  COALESCE(SUM(CASE WHEN up.completed THEN 1 ELSE 0 END), 0) as completions
           FROM courses c
           LEFT JOIN course_modules cm ON c.id = cm.course_id
           LEFT JOIN course_enrollments ce ON c.id = ce.course_id
           LEFT JOIN user_progress up ON cm.id = up.module_id
           WHERE c.is_published = TRUE
           GROUP BY c.id
           ORDER BY c.created_at DESC"""
    )
    return [dict(c) for c in courses]

@app.get("/courses/recommended")
async def get_recommended_courses(current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    """Get AI-recommended courses based on user insights"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
    insights = await conn.fetchrow("SELECT * FROM user_insights WHERE user_id = $1", user["id"])

    if not insights or not insights["recommended_courses"]:
        # Return default recommendations (newest courses)
        courses = await conn.fetch(
            """SELECT c.*, COUNT(cm.id) as module_count
               FROM courses c
               LEFT JOIN course_modules cm ON c.id = cm.course_id
               WHERE c.is_published = TRUE
               GROUP BY c.id
               ORDER BY c.created_at DESC LIMIT 3"""
        )
    else:
        # Return AI-recommended courses
        courses = await conn.fetch(
            """SELECT c.*, COUNT(cm.id) as module_count
               FROM courses c
               LEFT JOIN course_modules cm ON c.id = cm.course_id
               WHERE c.id = ANY($1) AND c.is_published = TRUE
               GROUP BY c.id""",
            insights["recommended_courses"]
        )

    return [dict(c) for c in courses]

@app.get("/courses/{course_id}")
async def get_course(
    course_id: int, 
    current_user: str = Depends(get_current_user), 
    conn=Depends(get_db)
):
    """Get course details with modules and user progress"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    course = await conn.fetchrow(
        """SELECT c.*, COUNT(ce.user_id) as total_enrollments
           FROM courses c
           LEFT JOIN course_enrollments ce ON c.id = ce.course_id
           WHERE c.id = $1 AND c.is_published = TRUE
           GROUP BY c.id""",
        course_id
    )

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check if user is enrolled
    enrollment = await conn.fetchrow(
        "SELECT * FROM course_enrollments WHERE user_id = $1 AND course_id = $2",
        user["id"], course_id
    )

    modules = await conn.fetch(
        """SELECT cm.*, up.completed, up.completed_at 
           FROM course_modules cm
           LEFT JOIN user_progress up ON cm.id = up.module_id AND up.user_id = $1
           WHERE cm.course_id = $2 
           ORDER BY cm.order_index""",
        user["id"], course_id
    )

    return {
        "course": dict(course),
        "is_enrolled": enrollment is not None,
        "modules": [dict(m) for m in modules]
    }

@app.post("/courses/{course_id}/enroll")
async def enroll_course(
    course_id: int,
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Enroll in a course"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    # Check if course exists and is published
    course = await conn.fetchrow(
        "SELECT id FROM courses WHERE id = $1 AND is_published = TRUE",
        course_id
    )

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    try:
        await conn.execute(
            "INSERT INTO course_enrollments (user_id, course_id) VALUES ($1, $2)",
            user["id"], course_id
        )
        return {"success": True, "message": "Enrolled successfully"}
    except asyncpg.UniqueViolationError:
        return {"success": False, "message": "Already enrolled"}

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

    return {"success": True, "message": "Module completed"}

# ============================================================================
# BLOG (WordPress-style with SEO)
# ============================================================================

@app.post("/admin/blog/posts")
async def create_blog_post(
    title: str = Form(...),
    content: str = Form(...),
    excerpt: Optional[str] = Form(None),
    featured_image: Optional[str] = Form(None),
    featured_image_upload: Optional[UploadFile] = File(None),
    meta_title: Optional[str] = Form(None),
    meta_description: Optional[str] = Form(None),
    meta_keywords: Optional[str] = Form(None),
    category: Optional[str] = Form("general"),
    status: str = Form("draft"),
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """Create blog post (admin only)"""
    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    # Handle featured image upload
    if featured_image_upload and not featured_image:
        upload_dir = "uploads/images"
        os.makedirs(upload_dir, exist_ok=True)

        timestamp = int(datetime.utcnow().timestamp())
        safe_filename = re.sub(r'[^\w\.]', '_', featured_image_upload.filename)
        unique_filename = f"blog_{timestamp}_{safe_filename}"
        file_path = f"{upload_dir}/{unique_filename}"

        contents = await featured_image_upload.read()

        # Validate image size (5MB max)
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large. Max 5MB.")

        with open(file_path, "wb") as f:
            f.write(contents)

        featured_image = f"/uploads/images/{unique_filename}"

        # Save to media library
        await conn.execute(
            """INSERT INTO media_files (filename, url, file_type, file_size, uploaded_by) 
               VALUES ($1, $2, $3, $4, $5) 
               ON CONFLICT (url) DO NOTHING""",
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

    # Get category ID
    category_id = None
    if category:
        cat = await conn.fetchrow("SELECT id FROM blog_categories WHERE slug = $1", category)
        if cat:
            category_id = cat["id"]

    post_id = await conn.fetchval(
        """INSERT INTO blog_posts 
           (title, slug, content, excerpt, featured_image, meta_title, meta_description, meta_keywords, 
            status, published_at, author_id, seo_score, seo_suggestions)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13) RETURNING id""",
        title, slug, content, excerpt, featured_image, meta_title or title, 
        meta_description, meta_keywords, status, published_at, user["id"], 
        seo_data["score"], json.dumps(seo_data["suggestions"])
    )

    # Add category relationship
    if category_id:
        await conn.execute(
            "INSERT INTO post_categories (post_id, category_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            post_id, category_id
        )

    return {
        "success": True, 
        "post_id": post_id, 
        "slug": slug, 
        "seo_score": seo_data["score"], 
        "suggestions": seo_data["suggestions"]
    }

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

@app.delete("/admin/blog/posts/{post_id}")
async def delete_blog_post(
    post_id: int,
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """Delete blog post (admin only)"""
    await conn.execute("DELETE FROM blog_posts WHERE id = $1", post_id)
    return {"success": True, "message": "Post deleted"}

@app.get("/blog/posts")
async def list_blog_posts(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    status: str = Query("published"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    conn=Depends(get_db)
):
    """List blog posts with filtering and pagination"""
    where_clauses = ["bp.status = $1"]
    params = [status]

    if category:
        where_clauses.append(f"EXISTS (SELECT 1 FROM post_categories pc JOIN blog_categories bc ON pc.category_id = bc.id WHERE pc.post_id = bp.id AND bc.slug = ${len(params) + 1})")
        params.append(category)

    if tag:
        where_clauses.append(f"EXISTS (SELECT 1 FROM post_tags pt JOIN blog_tags bt ON pt.tag_id = bt.id WHERE pt.post_id = bp.id AND bt.slug = ${len(params) + 1})")
        params.append(tag)

    if search:
        where_clauses.append(f"(bp.title ILIKE ${len(params) + 1} OR bp.content ILIKE ${len(params) + 1})")
        params.append(f"%{search}%")

    where_str = " AND ".join(where_clauses)

    # Get total count
    count_query = f"SELECT COUNT(*) FROM blog_posts bp WHERE {where_str}"
    total = await conn.fetchval(count_query, *params)

    # Get posts
    offset = (page - 1) * per_page
    query = f"""SELECT bp.*, u.name as author_name,
                COALESCE(json_agg(DISTINCT bc.name) FILTER (WHERE bc.name IS NOT NULL), '[]') as categories,
                COALESCE(json_agg(DISTINCT bt.name) FILTER (WHERE bt.name IS NOT NULL), '[]') as tags
                FROM blog_posts bp
                JOIN users u ON bp.author_id = u.id
                LEFT JOIN post_categories pc ON bp.id = pc.post_id
                LEFT JOIN blog_categories bc ON pc.category_id = bc.id
                LEFT JOIN post_tags pt ON bp.id = pt.post_id
                LEFT JOIN blog_tags bt ON pt.tag_id = bt.id
                WHERE {where_str}
                GROUP BY bp.id, u.name
                ORDER BY bp.published_at DESC NULLS LAST
                LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"""

    params.extend([per_page, offset])
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
                                  COALESCE(json_agg(DISTINCT bc.name) FILTER (WHERE bc.name IS NOT NULL), '[]') as categories,
                                  COALESCE(json_agg(DISTINCT bt.name) FILTER (WHERE bt.name IS NOT NULL), '[]') as tags
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
    """List all blog categories with post counts"""
    categories = await conn.fetch("""SELECT bc.*, COUNT(DISTINCT pc.post_id) as post_count 
                                     FROM blog_categories bc
                                     LEFT JOIN post_categories pc ON bc.id = pc.category_id
                                     LEFT JOIN blog_posts bp ON pc.post_id = bp.id AND bp.status = 'published'
                                     GROUP BY bc.id
                                     ORDER BY bc.name""")
    return [dict(c) for c in categories]

@app.get("/blog/tags")
async def list_tags(conn=Depends(get_db)):
    """List all blog tags with post counts"""
    tags = await conn.fetch("""SELECT bt.*, COUNT(DISTINCT pt.post_id) as post_count 
                               FROM blog_tags bt
                               LEFT JOIN post_tags pt ON bt.id = pt.tag_id
                               LEFT JOIN blog_posts bp ON pt.post_id = bp.id AND bp.status = 'published'
                               GROUP BY bt.id
                               ORDER BY bt.name""")
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
        ET.SubElement(url, "lastmod").text = post["updated_at"].isoformat() if post["updated_at"] else datetime.utcnow().isoformat()
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

    # Create uploads directory
    upload_dir = f"uploads/{file_type}s"
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    timestamp = int(datetime.utcnow().timestamp())
    safe_filename = re.sub(r'[^\w\.]', '_', file.filename)
    unique_filename = f"{timestamp}_{safe_filename}"
    file_path = f"{upload_dir}/{unique_filename}"

    # Save file
    contents = await file.read()

    # Validate file size (10MB max for images, 50MB for videos)
    max_size = 50 * 1024 * 1024 if file_type == 'video' else 10 * 1024 * 1024
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail=f"File too large. Max size is {max_size // (1024*1024)}MB.")

    with open(file_path, "wb") as f:
        f.write(contents)

    # Determine URL path
    file_size = len(contents)
    url_path = f"/uploads/{file_type}s/{unique_filename}"

    # Save to database
    media_id = await conn.fetchval(
        """INSERT INTO media_files (filename, url, file_type, file_size, uploaded_by) 
           VALUES ($1, $2, $3, $4, $5) 
           ON CONFLICT (url) DO UPDATE SET
           file_size = $4,
           uploaded_by = $5
           RETURNING id""",
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
    file_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """List all uploaded media files (admin only) with pagination"""
    offset = (page - 1) * per_page

    if file_type:
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM media_files WHERE file_type = $1",
            file_type
        )
        media = await conn.fetch(
            """SELECT m.*, u.name as uploaded_by_name 
               FROM media_files m 
               JOIN users u ON m.uploaded_by = u.id 
               WHERE m.file_type = $1 
               ORDER BY m.created_at DESC 
               LIMIT $2 OFFSET $3""",
            file_type, per_page, offset
        )
    else:
        total = await conn.fetchval("SELECT COUNT(*) FROM media_files")
        media = await conn.fetch(
            """SELECT m.*, u.name as uploaded_by_name 
               FROM media_files m 
               JOIN users u ON m.uploaded_by = u.id 
               ORDER BY m.created_at DESC 
               LIMIT $1 OFFSET $2""",
            per_page, offset
        )

    return {
        "media": [dict(m) for m in media],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

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

# ============================================================================
# ADMIN DASHBOARD
# ============================================================================

@app.get("/admin/stats")
async def admin_stats(current_user: str = Depends(get_current_admin), conn=Depends(get_db)):
    """Get admin dashboard statistics"""
    stats = {
        "users": await conn.fetchval("SELECT COUNT(*) FROM users"),
        "trades": await conn.fetchval("SELECT COUNT(*) FROM trades"),
        "chart_analyses": await conn.fetchval("SELECT COUNT(*) FROM chart_analyses"),
        "performance_analyses": await conn.fetchval("SELECT COUNT(*) FROM performance_analyses"),
        "mentorship_sessions": await conn.fetchval("SELECT COUNT(*) FROM mentorship_sessions"),
        "courses": await conn.fetchval("SELECT COUNT(*) FROM courses"),
        "published_courses": await conn.fetchval("SELECT COUNT(*) FROM courses WHERE is_published = TRUE"),
        "webinars": await conn.fetchval("SELECT COUNT(*) FROM webinars WHERE scheduled_at > NOW() - INTERVAL '1 hour'"),
        "webinar_registrations": await conn.fetchval("SELECT COUNT(*) FROM webinar_registrations"),
        "blog_posts": await conn.fetchval("SELECT COUNT(*) FROM blog_posts"),
        "published_posts": await conn.fetchval("SELECT COUNT(*) FROM blog_posts WHERE status = 'published'"),
        "total_views": await conn.fetchval("SELECT COALESCE(SUM(views), 0) FROM blog_posts"),
        "media_files": await conn.fetchval("SELECT COUNT(*) FROM media_files"),
        "course_enrollments": await conn.fetchval("SELECT COUNT(*) FROM course_enrollments")
    }

    return stats

@app.get("/admin/users")
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """List all users with pagination (admin only)"""
    offset = (page - 1) * per_page

    total = await conn.fetchval("SELECT COUNT(*) FROM users")

    users = await conn.fetch(
        """SELECT id, email, name, is_admin, created_at,
                  (SELECT COUNT(*) FROM trades WHERE user_id = users.id) as trade_count,
                  (SELECT COUNT(*) FROM chart_analyses WHERE user_id = users.id) as analysis_count
           FROM users 
           ORDER BY created_at DESC 
           LIMIT $1 OFFSET $2""",
        per_page, offset
    )

    return {
        "users": [dict(u) for u in users],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

@app.get("/admin/users/{user_id}/activity")
async def get_user_activity(
    user_id: int,
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """Get detailed activity for a specific user (admin only)"""
    user = await conn.fetchrow(
        "SELECT id, email, name, is_admin, created_at FROM users WHERE id = $1",
        user_id
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get recent trades
    trades = await conn.fetch(
        "SELECT * FROM trades WHERE user_id = $1 ORDER BY created_at DESC LIMIT 10",
        user_id
    )

    # Get recent analyses
    analyses = await conn.fetch(
        """SELECT 'chart' as type, id, created_at FROM chart_analyses WHERE user_id = $1
           UNION ALL
           SELECT 'performance' as type, id, created_at FROM performance_analyses WHERE user_id = $1
           ORDER BY created_at DESC LIMIT 10""",
        user_id
    )

    # Get insights
    insights = await conn.fetchrow(
        "SELECT * FROM user_insights WHERE user_id = $1",
        user_id
    )

    return {
        "user": dict(user),
        "recent_trades": [dict(t) for t in trades],
        "recent_analyses": [dict(a) for a in analyses],
        "insights": dict(insights) if insights else None
    }

# ============================================================================
# DEBUG ENDPOINTS
# ============================================================================

@app.get("/debug/admin")
async def debug_admin(conn=Depends(get_db)):
    """Debug endpoint to check admin user status"""
    try:
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """)

        if not table_exists:
            return {"error": "Users table does not exist", "fix": "Restart server to trigger init_db()"}

        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")

        admin = await conn.fetchrow(
            "SELECT id, email, is_admin, created_at FROM users WHERE email = $1",
            DEFAULT_ADMIN_EMAIL
        )

        return {
            "users_table_exists": True,
            "total_users": user_count,
            "admin_configured": DEFAULT_ADMIN_EMAIL,
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

        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1", DEFAULT_ADMIN_EMAIL
        )

        if existing:
            return {"message": "Admin already exists", "email": DEFAULT_ADMIN_EMAIL}

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

@app.get("/")
async def root():
    """Serve frontend from root directory"""
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head><title>Pipways API</title></head>
    <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
        <h1>🚀 Pipways API is running</h1>
        <p>Backend Status: <strong style="color: green;">Operational</strong></p>
        <p>Frontend not detected. Please place index.html in the root folder.</p>
        <hr>
        <h3>Quick Links:</h3>
        <ul>
            <li><a href="/docs">API Documentation (Swagger UI)</a></li>
            <li><a href="/redoc">API Documentation (ReDoc)</a></li>
            <li><a href="/health">Health Check</a></li>
            <li><a href="/debug/admin">Debug Admin Status</a></li>
        </ul>
        <hr>
        <p><small>Version 2.0.0 | Built with FastAPI</small></p>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": [
            "trade_journal",
            "chart_analysis",
            "performance_analysis", 
            "ai_mentor",
            "webinars",
            "lms",
            "blog",
            "media_upload"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
