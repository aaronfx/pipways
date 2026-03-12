"""
Pipways Trading Platform - Main Application
Serves both API and Frontend
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
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse

# Import routes using absolute imports (for Render deployment)
from routes import auth, blog, courses, signals, webinars, media

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

# Mount uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Mount frontend static files (CSS, JS, images) - MUST be before HTML routes
if os.path.exists(frontend_path):
    logger.info(f"Mounting frontend from: {frontend_path}")
    
    # Mount static subdirectories
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

# Include all API routers - prefixes defined here ONLY
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

# Serve specific HTML pages
@app.get("/{page}.html", response_class=HTMLResponse)
async def serve_html_page(page: str):
    """Serve HTML pages from frontend folder"""
    page_path = os.path.join(frontend_path, f"{page}.html")
    
    if os.path.exists(page_path):
        with open(page_path, "r", encoding="utf-8") as f:
            return f.read()
    
    raise HTTPException(status_code=404, detail="Page not found")

# Serve index.html at root
@app.get("/", response_class=HTMLResponse)
async def serve_root():
    """Serve the frontend application at root"""
    index_path = os.path.join(frontend_path, "index.html")
    
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    
    # Fallback to API docs if no frontend
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pipways Trading Platform API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #0f172a; color: #e2e8f0; }
            h1 { color: #60a5fa; }
            .endpoint { background: #1e293b; padding: 10px; margin: 10px 0; border-radius: 5px; }
            a { color: #60a5fa; text-decoration: none; }
        </style>
    </head>
    <body>
        <h1>🚀 Pipways Trading Platform API</h1>
        <p>Version 2.0.0 - Professional trading education platform</p>
        
        <h2>📚 Documentation</h2>
        <div class="endpoint">
            <strong>Swagger UI:</strong> <a href="/api/docs">/api/docs</a>
        </div>
        <div class="endpoint">
            <strong>ReDoc:</strong> <a href="/api/redoc">/api/redoc</a>
        </div>
    </body>
    </html>
    """

# Catch-all for frontend routes (SPA support) - MUST be last
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def catch_all(full_path: str):
    """Catch-all route for frontend SPA routing"""
    # Skip API routes
    if full_path.startswith(("api/", "docs", "redoc", "openapi")):
        raise HTTPException(status_code=404)
    
    # Skip static files
    if full_path.startswith(("css/", "js/", "images/", "uploads/")):
        raise HTTPException(status_code=404)
    
    # Try to serve the specific HTML file first
    file_path = os.path.join(frontend_path, full_path)
    if os.path.exists(file_path) and file_path.endswith('.html'):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    # Default to index.html for SPA routing (client-side routing)
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    
    raise HTTPException(status_code=404, detail="Not found")

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

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=False, log_level="info")
