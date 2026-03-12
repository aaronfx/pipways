"""
Pipways Trading Platform - Main Application
FastAPI entry point with all modules mounted
"""

import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager
import logging

# Add parent directory to path for imports (Render compatibility)
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import from current directory (backend)
from database import init_db_pool, close_db_pool, init_db, check_connection, get_setting, db_pool
from schemas import DashboardStats
from security import get_admin_user, get_current_user, get_current_user_optional

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# Import routes directly from files (avoiding package issues)
try:
    from routes import signals, courses, blog, media, auth
except ImportError:
    # Fallback to direct import for Render
    import routes.signals as signals
    import routes.courses as courses
    import routes.blog as blog
    import routes.media as media
    import routes.auth as auth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles database initialization on startup and cleanup on shutdown
    """
    # Startup
    logger.info("=" * 50)
    logger.info("Starting up Pipways Trading Platform...")
    logger.info("=" * 50)
    
    try:
        await init_db_pool()
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        # Don't raise - let app start but show degraded status
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down Pipways Trading Platform...")
    await close_db_pool()
    logger.info("✅ Database connections closed")

# Initialize FastAPI app
app = FastAPI(
    title="Pipways Trading Platform API",
    description="Professional trading signals, LMS, and SEO-optimized blog system",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Create uploads directories
for directory in ["uploads", "uploads/blog", "uploads/courses", "uploads/signals", "uploads/avatars"]:
    os.makedirs(directory, exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(signals.router, prefix="/api/signals", tags=["Trading Signals"])
app.include_router(courses.router, prefix="/api/courses", tags=["Learning Management System"])
app.include_router(blog.router, prefix="/api/blog", tags=["Blog & SEO CMS"])
app.include_router(media.router, prefix="/api/media", tags=["Media Uploads"])

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": f"HTTP_{exc.status_code}"}
    )

# Health check
@app.get("/health", tags=["System"])
async def health_check():
    db_status = await check_connection()
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "service": "pipways-api",
        "version": "2.0.0"
    }

# Root endpoint
@app.get("/", tags=["System"])
async def root():
    return {
        "message": "Welcome to Pipways Trading Platform API",
        "documentation": "/api/docs",
        "version": "2.0.0",
        "health_check": "/health"
    }

# Admin dashboard
@app.get("/api/admin/dashboard", tags=["Admin"])
async def admin_dashboard(current_user: dict = Depends(get_admin_user)):
    """Get comprehensive dashboard statistics"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    import asyncpg
    
    async with db_pool.acquire() as conn:
        # User stats
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        
        # Signal stats
        signal_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active
            FROM signals
        """)
        
        # Course stats
        course_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'published' THEN 1 END) as published,
                (SELECT COUNT(*) FROM lessons) as lessons,
                (SELECT COUNT(*) FROM quizzes) as quizzes
            FROM courses
        """)
        
        # Blog stats
        blog_stats = await conn.fetchrow("SELECT COUNT(*) as total FROM blog_posts")
        
        # Webinar stats
        webinar_stats = await conn.fetchrow("SELECT COUNT(*) as total FROM webinars")
        
        # Enrollment stats
        total_enrollments = await conn.fetchval("SELECT COUNT(*) FROM enrollments")
        
        # Pending questions
        pending_questions = await conn.fetchval("""
            SELECT COUNT(*) FROM student_questions WHERE is_answered = FALSE
        """)
        
        # Recent activity
        recent_activities = await conn.fetch("""
            SELECT * FROM activity_log 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        return {
            "total_users": total_users or 0,
            "total_signals": signal_stats['total'] if signal_stats else 0,
            "active_signals": signal_stats['active'] if signal_stats else 0,
            "total_courses": course_stats['total'] if course_stats else 0,
            "published_courses": course_stats['published'] if course_stats else 0,
            "total_lessons": course_stats['lessons'] if course_stats else 0,
            "total_quizzes": course_stats['quizzes'] if course_stats else 0,
            "total_blog_posts": blog_stats['total'] if blog_stats else 0,
            "total_webinars": webinar_stats['total'] if webinar_stats else 0,
            "total_enrollments": total_enrollments or 0,
            "pending_questions": pending_questions or 0,
            "recent_activities": [dict(a) for a in recent_activities] if recent_activities else []
        }

# Public settings
@app.get("/api/settings", tags=["System"])
async def get_public_settings():
    """Get public site settings"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    settings = {}
    keys = ['site_name', 'site_url', 'telegram_free_link', 'vip_price', 'vip_price_currency']
    
    for key in keys:
        value = await get_setting(key)
        if value:
            settings[key] = value
    
    return settings

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
