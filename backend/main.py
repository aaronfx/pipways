"""
Pipways Trading Platform - Main Application
FastAPI entry point with all modules mounted
"""

import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager
import logging
from datetime import datetime

# Add backend directory to Python path (critical for Render)
backend_dir = Path(__file__).parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Core imports (absolute only - no dots)
from database import init_db_pool, close_db_pool, init_db, check_connection, get_setting, db_pool
from schemas import DashboardStats
from security import get_admin_user, get_current_user, get_current_user_optional

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse

# Import routes directly (absolute imports)
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
    """Application lifespan manager"""
    logger.info("=" * 60)
    logger.info("Starting Pipways Trading Platform v2.0.0")
    logger.info("=" * 60)
    
    try:
        await init_db_pool()
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        # Continue anyway - health check will show degraded status
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down Pipways Trading Platform...")
    try:
        await close_db_pool()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="Pipways Trading Platform API",
    description="""
    Professional trading platform with:
    - Real-time trading signals with TP/SL tracking
    - Complete LMS with courses, modules, quizzes
    - SEO-optimized blog with Yoast-style scoring
    - Live webinars with registration management
    - Secure media uploads
    """,
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Create uploads directories
upload_dirs = [
    "uploads", 
    "uploads/blog", 
    "uploads/courses", 
    "uploads/signals", 
    "uploads/avatars", 
    "uploads/webinars"
]
for directory in upload_dirs:
    os.makedirs(directory, exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include all routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(signals.router, prefix="/api/signals", tags=["Trading Signals"])
app.include_router(courses.router, prefix="/api/courses", tags=["Learning Management System"])
app.include_router(blog.router, prefix="/api/blog", tags=["Blog & SEO CMS"])
app.include_router(webinars.router, prefix="/api/webinars", tags=["Webinars & Live Sessions"])
app.include_router(media.router, prefix="/api/media", tags=["Media Uploads"])

# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

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

# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@app.get("/health", tags=["System"])
async def health_check():
    """System health check including database connectivity"""
    db_status = await check_connection()
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "service": "pipways-api",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/", tags=["System"], response_class=HTMLResponse)
async def root():
    """API root with HTML documentation"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pipways Trading Platform API</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                max-width: 800px; 
                margin: 50px auto; 
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }
            h1 { margin-top: 0; }
            .endpoint { 
                background: rgba(255,255,255,0.2); 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 8px;
                border-left: 4px solid #fff;
            }
            a { color: #ffd700; text-decoration: none; font-weight: bold; }
            a:hover { text-decoration: underline; }
            .status { display: inline-block; width: 10px; height: 10px; background: #00ff88; border-radius: 50%; margin-right: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1><span class="status"></span>Pipways Trading Platform API</h1>
            <p>Version 2.0.0 - Professional trading education platform</p>
            
            <h2>📚 Documentation</h2>
            <div class="endpoint">
                <strong>Swagger UI:</strong> <a href="/api/docs">/api/docs</a>
            </div>
            <div class="endpoint">
                <strong>ReDoc:</strong> <a href="/api/redoc">/api/redoc</a>
            </div>
            <div class="endpoint">
                <strong>Health Check:</strong> <a href="/health">/health</a>
            </div>
            
            <h2>🔧 Modules</h2>
            <ul>
                <li><strong>Auth:</strong> /api/auth/* - Authentication & user management</li>
                <li><strong>Signals:</strong> /api/signals/* - Trading signals with TP/SL tracking</li>
                <li><strong>Courses:</strong> /api/courses/* - LMS with modules, lessons, quizzes</li>
                <li><strong>Blog:</strong> /api/blog/* - SEO-optimized content management</li>
                <li><strong>Webinars:</strong> /api/webinars/* - Live sessions & recordings</li>
                <li><strong>Media:</strong> /api/media/* - File uploads</li>
            </ul>
            
            <h2>👨‍💼 Admin</h2>
            <div class="endpoint">
                <strong>Dashboard:</strong> /api/admin/dashboard
            </div>
        </div>
    </body>
    </html>
    """

# ============================================================================
# ADMIN DASHBOARD
# ============================================================================

@app.get("/api/admin/dashboard", tags=["Admin"])
async def admin_dashboard(current_user: dict = Depends(get_admin_user)):
    """Get comprehensive dashboard statistics for admin panel"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        async with db_pool.acquire() as conn:
            # User statistics
            user_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN subscription_tier = 'vip' THEN 1 END) as vip_users,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as new_this_week
                FROM users
            """)
            
            # Signal statistics (last 30 days)
            signal_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                    COUNT(CASE WHEN tp1_hit = TRUE THEN 1 END) as tp1_hits,
                    COUNT(CASE WHEN sl_hit = TRUE THEN 1 END) as sl_hits,
                    COALESCE(AVG(pips_gained), 0) as avg_pips
                FROM signals
                WHERE created_at > NOW() - INTERVAL '30 days'
            """)
            
            # Course statistics
            course_stats = await conn.fetchrow("""
                SELECT 
                    (SELECT COUNT(*) FROM courses) as total_courses,
                    (SELECT COUNT(*) FROM courses WHERE status = 'published') as published_courses,
                    (SELECT COUNT(*) FROM lessons) as total_lessons,
                    (SELECT COUNT(*) FROM quizzes) as total_quizzes,
                    (SELECT COUNT(*) FROM enrollments) as total_enrollments,
                    (SELECT COUNT(*) FROM enrollments WHERE enrolled_at > NOW() - INTERVAL '7 days') as new_enrollments
            """)
            
            # Blog statistics
            blog_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_posts,
                    COUNT(CASE WHEN status = 'published' THEN 1 END) as published,
                    COUNT(CASE WHEN is_featured = TRUE THEN 1 END) as featured,
                    COALESCE(SUM(views), 0) as total_views
                FROM blog_posts
            """)
            
            # Webinar statistics
            webinar_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_webinars,
                    COUNT(CASE WHEN status = 'scheduled' THEN 1 END) as upcoming,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    (SELECT COUNT(*) FROM webinar_registrations) as total_registrations,
                    (SELECT AVG(feedback_rating) FROM webinar_registrations WHERE feedback_rating IS NOT NULL) as avg_rating
                FROM webinars
            """)
            
            # Support statistics
            pending_questions = await conn.fetchval("""
                SELECT COUNT(*) FROM student_questions WHERE is_answered = FALSE
            """)
            
            # Recent activity (last 10)
            recent_activities = await conn.fetch("""
                SELECT 
                    a.id, a.action, a.entity_type, a.entity_id, a.created_at,
                    u.full_name as user_name
                FROM activity_log a
                LEFT JOIN users u ON a.user_id = u.id
                ORDER BY a.created_at DESC
                LIMIT 10
            """)
            
            return {
                "users": {
                    "total": user_stats['total_users'] or 0,
                    "vip": user_stats['vip_users'] or 0,
                    "new_this_week": user_stats['new_this_week'] or 0
                },
                "signals": {
                    "total_30d": signal_stats['total'] or 0,
                    "active": signal_stats['active'] or 0,
                    "tp1_hits": signal_stats['tp1_hits'] or 0,
                    "sl_hits": signal_stats['sl_hits'] or 0,
                    "avg_pips": round(float(signal_stats['avg_pips'] or 0), 2)
                },
                "courses": {
                    "total": course_stats['total_courses'] or 0,
                    "published": course_stats['published_courses'] or 0,
                    "lessons": course_stats['total_lessons'] or 0,
                    "quizzes": course_stats['total_quizzes'] or 0,
                    "enrollments": course_stats['total_enrollments'] or 0,
                    "new_enrollments": course_stats['new_enrollments'] or 0
                },
                "blog": {
                    "total_posts": blog_stats['total_posts'] or 0,
                    "published": blog_stats['published'] or 0,
                    "featured": blog_stats['featured'] or 0,
                    "total_views": int(blog_stats['total_views'] or 0)
                },
                "webinars": {
                    "total": webinar_stats['total_webinars'] or 0,
                    "upcoming": webinar_stats['upcoming'] or 0,
                    "completed": webinar_stats['completed'] or 0,
                    "registrations": webinar_stats['total_registrations'] or 0,
                    "avg_rating": round(float(webinar_stats['avg_rating'] or 0), 1)
                },
                "support": {
                    "pending_questions": pending_questions or 0
                },
                "recent_activities": [
                    {
                        "id": a['id'],
                        "action": a['action'],
                        "entity_type": a['entity_type'],
                        "user": a['user_name'],
                        "time": a['created_at'].isoformat() if a['created_at'] else None
                    }
                    for a in recent_activities
                ] if recent_activities else []
            }
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load dashboard: {str(e)}")

@app.get("/api/settings", tags=["System"])
async def get_public_settings():
    """Get public site settings"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    keys = [
        'site_name', 'site_url', 'contact_email',
        'telegram_free_link', 'telegram_vip_link',
        'vip_price', 'vip_price_currency', 'enable_registration'
    ]
    
    settings = {}
    for key in keys:
        try:
            value = await get_setting(key)
            if value is not None:
                settings[key] = value
        except Exception as e:
            logger.warning(f"Failed to get setting {key}: {e}")
    
    return settings

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=False, log_level="info")
