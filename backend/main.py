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
from typing import Optional, List, Dict, Any

# Add backend directory to Python path
backend_dir = Path(__file__).parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Core imports
from database import init_db_pool, close_db_pool, init_db, check_connection, get_setting, db_pool
from security import get_admin_user, get_current_user, get_current_user_optional

from fastapi import FastAPI, HTTPException, Depends, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse

# Import routes using absolute imports
try:
    from routes import auth, blog, courses, signals, webinars, media
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import routes: {e}")
    # Create dummy routers if imports fail
    from fastapi import APIRouter
    auth = type('obj', (object,), {'router': APIRouter()})()
    blog = type('obj', (object,), {'router': APIRouter()})()
    courses = type('obj', (object,), {'router': APIRouter()})()
    signals = type('obj', (object,), {'router': APIRouter()})()
    webinars = type('obj', (object,), {'router': APIRouter()})()
    media = type('obj', (object,), {'router': APIRouter()})()

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

# CORS - Permissive for debugging
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

# Mount uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Mount frontend static files
if os.path.exists(frontend_path):
    logger.info(f"Mounting frontend from: {frontend_path}")
    
    css_path = os.path.join(frontend_path, "css")
    js_path = os.path.join(frontend_path, "js")
    images_path = os.path.join(frontend_path, "images")
    
    if os.path.exists(css_path):
        app.mount("/css", StaticFiles(directory=css_path), name="css")
    if os.path.exists(js_path):
        app.mount("/js", StaticFiles(directory=js_path), name="js")
    if os.path.exists(images_path):
        app.mount("/images", StaticFiles(directory=images_path), name="images")
else:
    logger.warning(f"Frontend path not found: {frontend_path}")

# Include all API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(signals.router, prefix="/api/signals", tags=["Trading Signals"])
app.include_router(courses.router, prefix="/api/courses", tags=["Learning Management System"])
app.include_router(blog.router, prefix="/api/blog", tags=["Blog & SEO CMS"])
app.include_router(webinars.router, prefix="/api/webinars", tags=["Webinars & Live Sessions"])
app.include_router(media.router, prefix="/api/media", tags=["Media Uploads"])

# Debug endpoint to check routes
@app.get("/api/debug/routes", tags=["Debug"])
async def debug_routes():
    """List all registered API routes for debugging"""
    routes = []
    for route in app.routes:
        if hasattr(route, "path") and route.path.startswith("/api"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if hasattr(route, "methods") else [],
                "name": route.name if hasattr(route, "name") else None
            })
    return {"routes": routes, "total": len(routes)}

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

# Health check
@app.get("/health", tags=["System"])
async def health_check():
    """System health check"""
    db_status = await check_connection()
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "service": "pipways-api",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

# Fallback data endpoints in case database tables don't exist yet
@app.get("/api/signals", tags=["Trading Signals"])
async def get_signals(
    status: Optional[str] = Query(None),
    timeframe: Optional[str] = Query(None),
    pair: Optional[str] = Query(None),
    limit: int = Query(50)
):
    """Get trading signals with optional filters"""
    try:
        if not db_pool:
            # Return mock data if no database
            return {
                "signals": [
                    {
                        "id": 1,
                        "pair": "EURUSD",
                        "direction": "buy",
                        "entry_price": "1.0850",
                        "stop_loss": "1.0800",
                        "take_profit_1": "1.0900",
                        "take_profit_2": "1.0950",
                        "status": "active",
                        "timeframe": "H1",
                        "created_at": datetime.now().isoformat()
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": limit
            }
        
        async with db_pool.acquire() as conn:
            query = "SELECT * FROM signals WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = $1"
                params.append(status)
            if pair:
                query += f" AND pair ILIKE ${len(params)+1}"
                params.append(f"%{pair}%")
            if timeframe:
                query += f" AND timeframe = ${len(params)+1}"
                params.append(timeframe)
            
            query += " ORDER BY created_at DESC LIMIT $"+str(len(params)+1)
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            signals = [dict(row) for row in rows]
            
            return {
                "signals": signals,
                "total": len(signals),
                "page": 1,
                "page_size": limit
            }
    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        return {"signals": [], "total": 0, "error": str(e)}

@app.get("/api/courses", tags=["Learning Management System"])
async def get_courses():
    """Get all courses"""
    try:
        if not db_pool:
            return {
                "courses": [
                    {
                        "id": 1,
                        "title": "Forex Trading Basics",
                        "description": "Learn the fundamentals of forex trading",
                        "level": "beginner",
                        "lessons_count": 10,
                        "image_url": "/images/course1.jpg"
                    }
                ]
            }
        
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM courses ORDER BY created_at DESC")
            courses = [dict(row) for row in rows]
            return {"courses": courses}
    except Exception as e:
        logger.error(f"Error fetching courses: {e}")
        return {"courses": [], "error": str(e)}

@app.get("/api/webinars", tags=["Webinars & Live Sessions"])
async def get_webinars():
    """Get upcoming webinars"""
    try:
        if not db_pool:
            return {
                "webinars": [
                    {
                        "id": 1,
                        "title": "Live Trading Session",
                        "description": "Join us for a live trading session",
                        "scheduled_at": datetime.now().isoformat(),
                        "presenter": "Admin",
                        "status": "upcoming"
                    }
                ]
            }
        
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM webinars WHERE scheduled_at > NOW() ORDER BY scheduled_at ASC"
            )
            webinars = [dict(row) for row in rows]
            return {"webinars": webinars}
    except Exception as e:
        logger.error(f"Error fetching webinars: {e}")
        return {"webinars": [], "error": str(e)}

@app.get("/api/blog", tags=["Blog & SEO CMS"])
async def get_blog_posts(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(10)
):
    """Get blog posts with filters"""
    try:
        if not db_pool:
            return {
                "posts": [
                    {
                        "id": 1,
                        "title": "Welcome to Pipways",
                        "excerpt": "Your journey starts here",
                        "content": "Welcome content...",
                        "category": "General",
                        "author": "Admin",
                        "created_at": datetime.now().isoformat(),
                        "views": 0
                    }
                ],
                "total": 1,
                "page": page,
                "page_size": page_size
            }
        
        async with db_pool.acquire() as conn:
            query = "SELECT * FROM blog_posts WHERE status = 'published'"
            params = []
            
            if category:
                query += f" AND category = ${len(params)+1}"
                params.append(category)
            if search:
                query += f" AND (title ILIKE ${len(params)+1} OR content ILIKE ${len(params)+1})"
                params.append(f"%{search}%")
            
            count_query = query.replace("SELECT *", "SELECT COUNT(*)")
            total = await conn.fetchval(count_query, *params)
            
            query += f" ORDER BY created_at DESC OFFSET ${len(params)+1} LIMIT ${len(params)+2}"
            params.extend([(page-1)*page_size, page_size])
            
            rows = await conn.fetch(query, *params)
            posts = [dict(row) for row in rows]
            
            return {
                "posts": posts,
                "total": total,
                "page": page,
                "page_size": page_size
            }
    except Exception as e:
        logger.error(f"Error fetching blog posts: {e}")
        return {"posts": [], "total": 0, "error": str(e)}

@app.get("/api/admin/dashboard", tags=["Admin"])
async def admin_dashboard(current_user: dict = Depends(get_admin_user)):
    """Get admin dashboard stats"""
    try:
        if not db_pool:
            return {
                "users": {"total": 0, "vip": 0, "new_this_week": 0},
                "signals": {"total_30d": 0, "active": 0, "tp1_hits": 0, "avg_pips": 0},
                "courses": {"total": 0, "lessons": 0, "quizzes": 0, "enrollments": 0},
                "blog": {"total_posts": 0, "total_views": 0},
                "webinars": {"total": 0, "registrations": 0},
                "recent_activities": []
            }
        
        async with db_pool.acquire() as conn:
            # Get user stats
            user_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN subscription_tier = 'vip' THEN 1 END) as vip,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as new_this_week
                FROM users
            """)
            
            # Get signal stats
            signal_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_30d,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                    COUNT(CASE WHEN tp1_hit = TRUE THEN 1 END) as tp1_hits
                FROM signals 
                WHERE created_at > NOW() - INTERVAL '30 days'
            """)
            
            return {
                "users": {
                    "total": user_stats['total'] if user_stats else 0,
                    "vip": user_stats['vip'] if user_stats else 0,
                    "new_this_week": user_stats['new_this_week'] if user_stats else 0
                },
                "signals": {
                    "total_30d": signal_stats['total_30d'] if signal_stats else 0,
                    "active": signal_stats['active'] if signal_stats else 0,
                    "tp1_hits": signal_stats['tp1_hits'] if signal_stats else 0,
                    "avg_pips": 0
                },
                "courses": {"total": 0, "lessons": 0, "quizzes": 0, "enrollments": 0},
                "blog": {"total_posts": 0, "total_views": 0},
                "webinars": {"total": 0, "registrations": 0},
                "recent_activities": []
            }
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# SPA Catch-all - MUST BE LAST
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def spa_catch_all(full_path: str):
    """Catch-all route for SPA"""
    
    # Skip API routes
    if full_path.startswith(("api/", "docs", "redoc", "openapi")):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Skip static files
    if full_path.startswith(("css/", "js/", "images/", "assets/", "uploads/")):
        raise HTTPException(status_code=404, detail="Static file not found")
    
    # Serve dashboard.html for all other routes
    html = get_dashboard_html()
    if html:
        return html
    
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
