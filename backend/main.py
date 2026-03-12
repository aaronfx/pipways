"""
Pipways Trading Platform - Main Application
FastAPI entry point with all modules mounted
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os

# Relative imports as per project requirements
from . import database
from .routes import signals, courses, blog, media, auth
from .schemas import DashboardStats, MessageResponse
from .security import get_admin_user, get_current_user

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
    logger.info("Starting up Pipways Trading Platform...")
    try:
        await database.init_db_pool()
        await database.init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down Pipways Trading Platform...")
    await database.close_db_pool()
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
    allow_origins=["*"],  # Configure for production (e.g., ["https://pipways.com"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("uploads/blog", exist_ok=True)
os.makedirs("uploads/courses", exist_ok=True)
os.makedirs("uploads/signals", exist_ok=True)
os.makedirs("uploads/avatars", exist_ok=True)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers with prefixes
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}}
)

app.include_router(
    signals.router,
    prefix="/api/signals",
    tags=["Trading Signals"],
    dependencies=[]  # Public access with optional auth for premium content
)

app.include_router(
    courses.router,
    prefix="/api/courses",
    tags=["Learning Management System"],
    dependencies=[]  # Public access with auth for enrollment/progress
)

app.include_router(
    blog.router,
    prefix="/api/blog",
    tags=["Blog & SEO CMS"],
    dependencies=[]  # Public access with auth for premium posts
)

app.include_router(
    media.router,
    prefix="/api/media",
    tags=["Media Uploads"],
    dependencies=[]  # Auth handled within routes
)

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

# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """System health check including database connectivity"""
    db_status = await database.check_connection()
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "service": "pipways-api",
        "version": "2.0.0"
    }

# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """API root with available endpoints"""
    return {
        "message": "Welcome to Pipways Trading Platform API",
        "documentation": "/api/docs",
        "version": "2.0.0",
        "modules": ["signals", "courses", "blog", "media", "auth"],
        "health_check": "/health"
    }

# Admin dashboard stats (aggregated from all modules)
@app.get("/api/admin/dashboard", response_model=DashboardStats, tags=["Admin"])
async def admin_dashboard(current_user: dict = Depends(get_admin_user)):
    """Get comprehensive dashboard statistics for admin panel"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
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
        blog_stats = await conn.fetchrow("""
            SELECT COUNT(*) as total FROM blog_posts
        """)
        
        # Webinar stats (if implemented)
        webinar_stats = await conn.fetchrow("""
            SELECT COUNT(*) as total FROM webinars
        """)
        
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
            "total_users": total_users,
            "total_signals": signal_stats['total'],
            "active_signals": signal_stats['active'],
            "total_courses": course_stats['total'],
            "published_courses": course_stats['published'],
            "total_lessons": course_stats['lessons'],
            "total_quizzes": course_stats['quizzes'],
            "total_blog_posts": blog_stats['total'],
            "total_webinars": webinar_stats['total'] if webinar_stats else 0,
            "total_enrollments": total_enrollments,
            "pending_questions": pending_questions,
            "recent_activities": [dict(a) for a in recent_activities]
        }

# Global settings endpoint
@app.get("/api/settings", tags=["System"])
async def get_public_settings():
    """Get public site settings"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    settings = {}
    keys = ['site_name', 'site_url', 'telegram_free_link', 'vip_price', 'vip_price_currency']
    
    for key in keys:
        value = await database.get_setting(key)
        if value:
            settings[key] = value
    
    return settings

# Server startup verification
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server...")
    uvicorn.run(
        "app.main:app",  # Adjust "app" to your package name
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "false").lower() == "true",
        log_level="info"
    )
