"""
Pipways Trading Platform - Main Application
Serves both API and Frontend SPA
"""

import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager
import logging
from datetime import datetime

# Add backend directory to Python path
backend_dir = Path(__file__).parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Core imports
from database import init_db_pool, close_db_pool, init_db, check_connection, get_setting, db_pool
from security import get_admin_user, get_current_user, get_current_user_optional

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse

# Import routes using absolute imports (for Render deployment)
import auth
import blog
import courses
import signals
import webinars
import media

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Frontend path (one level up from backend)
frontend_path = os.path.join(os.path.dirname(backend_dir), "frontend")

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
    
    yield
    
    logger.info("Shutting down Pipways Trading Platform...")
    try:
        await close_db_pool()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

app = FastAPI(
    title="Pipways Trading Platform API",
    description="Professional trading signals, LMS, and SEO-optimized blog system",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Create uploads directories
for d in ["uploads", "uploads/blog", "uploads/courses", "uploads/signals", "uploads/avatars", "uploads/webinars"]:
    os.makedirs(d, exist_ok=True)

# Mount uploads directory (must be before static files to avoid conflicts)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Mount frontend static files (CSS, JS, images) - must be before HTML routes
if os.path.exists(frontend_path):
    logger.info(f"Mounting frontend from: {frontend_path}")
    
    css_path = os.path.join(frontend_path, "css")
    js_path = os.path.join(frontend_path, "js")
    images_path = os.path.join(frontend_path, "images")
    assets_path = os.path.join(frontend_path, "assets")
    
    if os.path.exists(css_path):
        app.mount("/css", StaticFiles(directory=css_path), name="css")
    if os.path.exists(js_path):
        app.mount("/js", StaticFiles(directory=js_path), name="js")
    if os.path.exists(images_path):
        app.mount("/images", StaticFiles(directory=images_path), name="images")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
else:
    logger.warning(f"Frontend path not found: {frontend_path}")

# Include all API routers with prefixes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(signals.router, prefix="/api/signals", tags=["Trading Signals"])
app.include_router(courses.router, prefix="/api/courses", tags=["Learning Management System"])
app.include_router(blog.router, prefix="/api/blog", tags=["Blog & SEO CMS"])
app.include_router(webinars.router, prefix="/api/webinars", tags=["Webinars & Live Sessions"])
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

# SPA Serving Logic
def get_dashboard_html():
    """Read and return the dashboard HTML file"""
    dashboard_path = os.path.join(frontend_path, "dashboard.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return f.read()
    return None

# Root route serves dashboard
@app.get("/", response_class=HTMLResponse)
async def serve_root():
    """Serve the main dashboard SPA"""
    html = get_dashboard_html()
    if html:
        return html
    return JSONResponse(
        status_code=404,
        content={"detail": "Dashboard not found. Please ensure frontend/dashboard.html exists."}
    )

# Explicit dashboard route
@app.get("/dashboard.html", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve dashboard explicitly"""
    return await serve_root()

# Health check endpoint
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

# API Admin Dashboard endpoint (used by frontend)
@app.get("/api/admin/dashboard", tags=["Admin"])
async def admin_dashboard(current_user: dict = Depends(get_admin_user)):
    """Get comprehensive dashboard statistics for admin panel"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        async with db_pool.acquire() as conn:
            user_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN subscription_tier = 'vip' THEN 1 END) as vip_users,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as new_this_week
                FROM users
            """)
            
            signal_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                    COUNT(CASE WHEN tp1_hit = TRUE THEN 1 END) as tp1_hits,
                    COALESCE(AVG(pips_gained), 0) as avg_pips
                FROM signals
                WHERE created_at > NOW() - INTERVAL '30 days'
            """)
            
            course_stats = await conn.fetchrow("""
                SELECT 
                    (SELECT COUNT(*) FROM courses) as total_courses,
                    (SELECT COUNT(*) FROM lessons) as total_lessons,
                    (SELECT COUNT(*) FROM quizzes) as total_quizzes,
                    (SELECT COUNT(*) FROM enrollments) as total_enrollments
            """)
            
            blog_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_posts,
                    COALESCE(SUM(views), 0) as total_views
                FROM blog_posts
            """)
            
            webinar_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_webinars,
                    (SELECT COUNT(*) FROM webinar_registrations) as total_registrations
                FROM webinars
            """)
            
            pending_questions = await conn.fetchval("""
                SELECT COUNT(*) FROM student_questions WHERE is_answered = FALSE
            """)
            
            recent_activities = await conn.fetch("""
                SELECT a.*, u.full_name as user_name 
                FROM activity_log a 
                LEFT JOIN users u ON a.user_id = u.id 
                ORDER BY a.created_at DESC LIMIT 10
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
                    "avg_pips": round(float(signal_stats['avg_pips'] or 0), 2)
                },
                "courses": {
                    "total": course_stats['total_courses'] or 0,
                    "lessons": course_stats['total_lessons'] or 0,
                    "quizzes": course_stats['total_quizzes'] or 0,
                    "enrollments": course_stats['total_enrollments'] or 0
                },
                "blog": {
                    "total_posts": blog_stats['total_posts'] or 0,
                    "total_views": int(blog_stats['total_views'] or 0)
                },
                "webinars": {
                    "total": webinar_stats['total_webinars'] or 0,
                    "registrations": webinar_stats['total_registrations'] or 0
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

# Public settings endpoint
@app.get("/api/settings", tags=["System"])
async def get_public_settings():
    """Get public site settings"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    keys = ['site_name', 'site_url', 'telegram_free_link', 'vip_price', 'vip_price_currency']
    settings = {}
    for key in keys:
        try:
            value = await get_setting(key)
            if value is not None:
                settings[key] = value
        except Exception as e:
            logger.warning(f"Failed to get setting {key}: {e}")
    
    return settings

# SPA Catch-all - MUST BE LAST
# This serves dashboard.html for all non-API, non-static routes
# allowing the React/Vue-like router in dashboard.html to handle client-side routing
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def spa_catch_all(full_path: str):
    """Catch-all route for SPA - serves dashboard.html for all frontend routes"""
    
    # Skip API routes
    if full_path.startswith(("api/", "docs", "redoc", "openapi")):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Skip static files (should be caught by mounted StaticFiles, but just in case)
    if full_path.startswith(("css/", "js/", "images/", "assets/", "uploads/")):
        raise HTTPException(status_code=404, detail="Static file not found")
    
    # Serve dashboard.html for all other routes (signals, blog, admin, etc.)
    # The frontend router will handle showing the correct section
    html = get_dashboard_html()
    if html:
        return html
    
    # Fallback if no dashboard.html
    return JSONResponse(
        status_code=404,
        content={"detail": "Page not found", "error_code": "HTTP_404"}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=False, log_level="info")
