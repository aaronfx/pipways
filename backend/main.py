"""
Pipways Trading Platform - Main Application
"""

import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager
import logging

# Add backend directory to Python path (critical for Render)
backend_dir = Path(__file__).parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Now imports work without dots
from database import init_db_pool, close_db_pool, init_db, check_connection, get_setting, db_pool
from schemas import DashboardStats
from security import get_admin_user, get_current_user, get_current_user_optional

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse

# Import routes directly (no package imports to avoid conflicts)
import routes.auth as auth
import routes.signals as signals
import routes.courses as courses
import routes.blog as blog
import routes.media as media
import routes.webinars as webinars

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    logger.info("Starting Pipways Trading Platform...")
    try:
        await init_db_pool()
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")
    
    yield
    
    logger.info("Shutting down...")
    await close_db_pool()

app = FastAPI(
    title="Pipways Trading Platform",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Uploads directories
for d in ["uploads", "uploads/blog", "uploads/courses", "uploads/signals", "uploads/avatars", "uploads/webinars"]:
    os.makedirs(d, exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(signals.router, prefix="/api/signals", tags=["Signals"])
app.include_router(courses.router, prefix="/api/courses", tags=["Courses"])
app.include_router(blog.router, prefix="/api/blog", tags=["Blog"])
app.include_router(webinars.router, prefix="/api/webinars", tags=["Webinars"])
app.include_router(media.router, prefix="/api/media", tags=["Media"])

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal error"})

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.get("/health", tags=["System"])
async def health_check():
    db_status = await check_connection()
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected"
    }

@app.get("/", tags=["System"], response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Pipways API</title></head>
    <body>
        <h1>Pipways Trading Platform API</h1>
        <p>Version 2.0.0</p>
        <ul>
            <li><a href="/api/docs">API Documentation (Swagger)</a></li>
            <li><a href="/health">Health Check</a></li>
        </ul>
    </body>
    </html>
    """

@app.get("/api/admin/dashboard", tags=["Admin"])
async def admin_dashboard(current_user: dict = Depends(get_admin_user)):
    """Admin dashboard stats"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    from datetime import datetime
    import asyncpg
    
    async with db_pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM signals WHERE status='active') as active_signals,
                (SELECT COUNT(*) FROM courses) as total_courses,
                (SELECT COUNT(*) FROM blog_posts) as total_posts,
                (SELECT COUNT(*) FROM webinars) as total_webinars,
                (SELECT COUNT(*) FROM enrollments) as total_enrollments,
                (SELECT COUNT(*) FROM student_questions WHERE is_answered=FALSE) as pending_questions
        """)
        
        recent = await conn.fetch("""
            SELECT a.*, u.full_name 
            FROM activity_log a 
            LEFT JOIN users u ON a.user_id=u.id 
            ORDER BY a.created_at DESC LIMIT 10
        """)
        
        return {
            "total_users": stats['total_users'] or 0,
            "active_signals": stats['active_signals'] or 0,
            "total_courses": stats['total_courses'] or 0,
            "total_blog_posts": stats['total_posts'] or 0,
            "total_webinars": stats['total_webinars'] or 0,
            "total_enrollments": stats['total_enrollments'] or 0,
            "pending_questions": stats['pending_questions'] or 0,
            "recent_activities": [dict(r) for r in recent] if recent else []
        }

@app.get("/api/settings", tags=["System"])
async def get_public_settings():
    """Public settings"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    keys = ['site_name', 'site_url', 'telegram_free_link', 'vip_price']
    settings = {}
    for key in keys:
        val = await get_setting(key)
        if val:
            settings[key] = val
    return settings

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
