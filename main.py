"""
Pipways API - Emergency Fix
Handles all edge cases and CORS properly
"""

import os
import sys
import traceback
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import with error handling
try:
    from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Query, Request
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.exceptions import RequestValidationError
    logger.info("✅ FastAPI imports successful")
except ImportError as e:
    logger.error(f"❌ Failed to import FastAPI: {e}")
    raise

try:
    import asyncpg
    from asyncpg import Pool
    logger.info("✅ asyncpg import successful")
except ImportError as e:
    logger.error(f"❌ Failed to import asyncpg: {e}")
    asyncpg = None
    Pool = None

try:
    from jose import JWTError, jwt
    logger.info("✅ python-jose import successful")
except ImportError as e:
    logger.error(f"❌ Failed to import python-jose: {e}")
    jwt = None
    JWTError = Exception

try:
    from passlib.context import CryptContext
    logger.info("✅ passlib import successful")
except ImportError as e:
    logger.error(f"❌ Failed to import passlib: {e}")
    CryptContext = None

# Settings with fallbacks
class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "emergency-secret-key-change-in-production")
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://pipways-web-nhem.onrender.com")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "https://pipways-web-nhem.onrender.com,http://localhost:3000,http://localhost:5173").split(",")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    PORT = int(os.environ.get("PORT", "8000"))

settings = Settings()
logger.info(f"🔧 Settings loaded. FRONTEND_URL: {settings.FRONTEND_URL}")
logger.info(f"🔧 CORS_ORIGINS: {settings.CORS_ORIGINS}")

# Initialize password hashing
if CryptContext:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
else:
    pwd_context = None
    logger.warning("⚠️ Password hashing not available")

security = HTTPBearer(auto_error=False)
pool: Optional[Any] = None

# Database functions
async def init_db():
    global pool
    if not settings.DATABASE_URL:
        logger.error("❌ DATABASE_URL not set!")
        return
    
    if asyncpg is None:
        logger.error("❌ asyncpg not available")
        return
    
    try:
        logger.info("🔄 Connecting to database...")
        pool = await asyncpg.create_pool(
            settings.DATABASE_URL, 
            min_size=1, 
            max_size=10,
            command_timeout=60,
            server_settings={
                'jit': 'off'
            }
        )
        logger.info("✅ Database connected")
        
        async with pool.acquire() as conn:
            logger.info("🔄 Creating tables...")
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
            logger.info("✅ Database tables created")
            
            # Insert sample data if empty
            course_count = await conn.fetchval("SELECT COUNT(*) FROM courses")
            if course_count == 0:
                logger.info("🔄 Inserting sample courses...")
                await conn.execute("""
                    INSERT INTO courses (title, description, level, is_published) VALUES
                    ('Forex Fundamentals', 'Master the basics of currency trading', 'beginner', TRUE),
                    ('Technical Analysis', 'Chart patterns and indicators', 'intermediate', TRUE),
                    ('Risk Management', 'Professional position sizing', 'advanced', TRUE)
                """)
            
            webinar_count = await conn.fetchval("SELECT COUNT(*) FROM webinars")
            if webinar_count == 0:
                logger.info("🔄 Inserting sample webinars...")
                await conn.execute("""
                    INSERT INTO webinars (title, description, presenter, scheduled_at, max_attendees) VALUES
                    ('Live Trading Session', 'Watch and learn in real-time', 'Master Trader', NOW() + INTERVAL '2 days', 100),
                    ('Q&A with Pros', 'Ask anything about trading', 'Expert Panel', NOW() + INTERVAL '5 days', 50)
                """)
            
            blog_count = await conn.fetchval("SELECT COUNT(*) FROM blog_posts")
            if blog_count == 0:
                logger.info("🔄 Inserting sample blog posts...")
                await conn.execute("""
                    INSERT INTO blog_posts (title, slug, content, excerpt, category, is_published) VALUES
                    ('Getting Started with Forex', 'getting-started', 'Full content here...', 'Learn the basics', 'education', TRUE),
                    ('Top 5 Trading Mistakes', 'top-mistakes', 'Full content here...', 'Avoid these errors', 'tips', TRUE)
                """)
                
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        logger.error(traceback.format_exc())
        pool = None

async def get_db():
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        async with pool.acquire() as conn:
            yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")

# Auth functions
def verify_password(plain, hashed):
    if pwd_context is None:
        return plain == hashed  # Fallback (INSECURE - for testing only)
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    if pwd_context is None:
        return password  # Fallback (INSECURE - for testing only)
    return pwd_context.hash(password)

def create_access_token(data: dict):
    if jwt is None:
        return "fake-token"
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if jwt is None:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
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
    logger.info("🚀 Application starting...")
    await init_db()
    logger.info("✅ Application startup complete")
    yield
    logger.info("🛑 Application shutting down...")
    if pool:
        await pool.close()
        logger.info("✅ Database pool closed")

app = FastAPI(
    title="Pipways API",
    version="2.0.1",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# ==========================================
# CORS - MUST BE FIRST, BEFORE ANY ROUTES
# ==========================================
logger.info("🔧 Setting up CORS middleware...")

# Add CORS middleware with explicit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

logger.info(f"✅ CORS configured for origins: {settings.CORS_ORIGINS}")

# ==========================================
# GLOBAL EXCEPTION HANDLERS
# ==========================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "success": False}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"❌ Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "success": False}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"❌ HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "success": False}
    )

# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.1",
        "database": "connected" if pool else "disconnected",
        "cors": "enabled",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    return {
        "message": "Pipways API Server",
        "version": "2.0.1",
        "docs": "/docs",
        "health": "/health",
        "cors_origins": settings.CORS_ORIGINS
    }

# Test CORS endpoint
@app.options("/{path:path}")
async def options_handler(path: str):
    return {"detail": "OK"}

# ==========================================
# AUTH ENDPOINTS
# ==========================================

@app.post("/auth/register")
async def register(
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(""),
    conn=Depends(get_db)
):
    try:
        logger.info(f"📝 Registration attempt for: {email}")
        
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        # Check if user exists
        existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        hashed = get_password_hash(password)
        user_id = await conn.fetchval(
            "INSERT INTO users (email, password_hash, full_name) VALUES ($1, $2, $3) RETURNING id",
            email, hashed, full_name
        )
        
        # Generate token
        access_token = create_access_token({"sub": email})
        
        logger.info(f"✅ User registered: {email}")
        
        return {
            "success": True,
            "user_id": user_id,
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "is_admin": False
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/auth/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    conn=Depends(get_db)
):
    try:
        logger.info(f"🔑 Login attempt for: {email}")
        
        # Get user
        user = await conn.fetchrow(
            "SELECT id, email, password_hash, full_name, is_admin FROM users WHERE email = $1 AND is_active = TRUE",
            email
        )
        
        if not user:
            logger.warning(f"⚠️ User not found: {email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not verify_password(password, user["password_hash"]):
            logger.warning(f"⚠️ Invalid password for: {email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Update last login
        await conn.execute("UPDATE users SET last_login = NOW() WHERE id = $1", user["id"])
        
        # Generate token
        access_token = create_access_token({"sub": email})
        
        logger.info(f"✅ Login successful: {email}")
        
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/auth/me")
async def get_me(current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    try:
        user = await conn.fetchrow(
            "SELECT id, email, full_name, is_admin FROM users WHERE email = $1",
            current_user
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "user": dict(user)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get user error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user")

# ==========================================
# TRADE ENDPOINTS
# ==========================================

@app.post("/trades")
async def create_trade(
    pair: str = Form(...),
    direction: str = Form(...),
    pips: float = Form(...),
    grade: str = Form("C"),
    notes: str = Form(""),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    try:
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
        
        trade_id = await conn.fetchval(
            "INSERT INTO trades (user_id, pair, direction, pips, grade, notes) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id",
            user["id"], pair.upper(), direction.upper(), pips, grade.upper(), notes
        )
        
        return {"success": True, "trade_id": trade_id}
    except Exception as e:
        logger.error(f"❌ Create trade error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create trade")

@app.get("/trades")
async def get_trades(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    try:
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
        
        total = await conn.fetchval("SELECT COUNT(*) FROM trades WHERE user_id = $1", user["id"])
        offset = (page - 1) * per_page
        
        trades = await conn.fetch(
            "SELECT * FROM trades WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
            user["id"], per_page, offset
        )
        
        return {
            "success": True,
            "trades": [dict(t) for t in trades],
            "total": total,
            "page": page,
            "per_page": per_page
        }
    except Exception as e:
        logger.error(f"❌ Get trades error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trades")

# ==========================================
# COURSE ENDPOINTS
# ==========================================

@app.get("/courses")
async def get_courses(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    conn=Depends(get_db)
):
    try:
        total = await conn.fetchval("SELECT COUNT(*) FROM courses WHERE is_published = TRUE")
        offset = (page - 1) * per_page
        
        courses = await conn.fetch(
            "SELECT * FROM courses WHERE is_published = TRUE ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            per_page, offset
        )
        
        return {
            "success": True,
            "courses": [dict(c) for c in courses],
            "total": total,
            "page": page,
            "per_page": per_page
        }
    except Exception as e:
        logger.error(f"❌ Get courses error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get courses")

@app.post("/courses/{course_id}/enroll")
async def enroll_course(
    course_id: int,
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    try:
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
        
        try:
            await conn.execute(
                "INSERT INTO course_enrollments (user_id, course_id) VALUES ($1, $2)",
                user["id"], course_id
            )
            return {"success": True, "message": "Enrolled successfully"}
        except asyncpg.UniqueViolationError:
            return {"success": True, "message": "Already enrolled"}
    except Exception as e:
        logger.error(f"❌ Enroll course error: {e}")
        raise HTTPException(status_code=500, detail="Failed to enroll")

# ==========================================
# WEBINAR ENDPOINTS
# ==========================================

@app.get("/webinars")
async def get_webinars(conn=Depends(get_db)):
    try:
        webinars = await conn.fetch(
            "SELECT * FROM webinars WHERE scheduled_at > NOW() ORDER BY scheduled_at ASC"
        )
        return {"success": True, "webinars": [dict(w) for w in webinars]}
    except Exception as e:
        logger.error(f"❌ Get webinars error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get webinars")

@app.post("/webinars/{webinar_id}/register")
async def register_webinar(
    webinar_id: int,
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    try:
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
        
        try:
            await conn.execute(
                "INSERT INTO webinar_registrations (webinar_id, user_id) VALUES ($1, $2)",
                webinar_id, user["id"]
            )
            return {"success": True, "message": "Registered successfully"}
        except asyncpg.UniqueViolationError:
            return {"success": True, "message": "Already registered"}
    except Exception as e:
        logger.error(f"❌ Register webinar error: {e}")
        raise HTTPException(status_code=500, detail="Failed to register")

# ==========================================
# BLOG ENDPOINTS
# ==========================================

@app.get("/blog/posts")
async def get_blog_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    conn=Depends(get_db)
):
    try:
        total = await conn.fetchval("SELECT COUNT(*) FROM blog_posts WHERE is_published = TRUE")
        offset = (page - 1) * per_page
        
        posts = await conn.fetch(
            "SELECT id, title, slug, excerpt, featured_image, category, created_at FROM blog_posts WHERE is_published = TRUE ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            per_page, offset
        )
        
        return {
            "success": True,
            "posts": [dict(p) for p in posts],
            "total": total,
            "page": page,
            "per_page": per_page
        }
    except Exception as e:
        logger.error(f"❌ Get blog posts error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get blog posts")

# ==========================================
# AI ANALYSIS ENDPOINTS
# ==========================================

@app.post("/analyze/chart")
async def analyze_chart(
    image: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    try:
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
        
        contents = await image.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        filename = f"chart_{int(datetime.now().timestamp())}.png"
        
        # Simple analysis (replace with actual AI logic)
        analysis = f"Chart analysis for {image.filename}. Pattern detected: Bullish trend with support at key level."
        
        await conn.execute(
            "INSERT INTO chart_analyses (user_id, image_url, analysis_text) VALUES ($1, $2, $3)",
            user["id"], filename, analysis
        )
        
        return {
            "success": True,
            "analysis": analysis,
            "filename": filename
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Chart analysis error: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze chart")

@app.post("/mentor/chat")
async def mentor_chat(
    message: str = Form(...),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    try:
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
        
        # Simple response (replace with actual AI logic)
        response = f"You asked: '{message}'. As a trading mentor, I recommend focusing on risk management and following your trading plan."
        
        await conn.execute(
            "INSERT INTO mentor_chats (user_id, message, response) VALUES ($1, $2, $3)",
            user["id"], message, response
        )
        
        return {"success": True, "response": response}
    except Exception as e:
        logger.error(f"❌ Mentor chat error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get response")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"🚀 Starting server on port {settings.PORT}")
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
