"""Pipways Trading Platform - Main Application"""
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .database import database, init_database

# Import all routers
try:
    from . import auth
    from . import signals
    from . import courses
    from . import webinars
    from . import blog
    from . import ai_screening
    from . import performance
    from . import admin
    from . import blog_enhanced
    from . import courses_enhanced
    print("[IMPORT] All modules loaded successfully", flush=True)
except ImportError as e:
    print(f"[IMPORT ERROR] {e}", flush=True)
    raise

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_database()
        print("[STARTUP] Database connected", flush=True)
    except Exception as e:
        print(f"[STARTUP ERROR] {e}", flush=True)
    yield
    try:
        await database.disconnect()
    except:
        pass

app = FastAPI(
    title="Pipways Trading Platform",
    version="2.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.1.0"}

# API Routes
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(signals.router, prefix="/signals", tags=["Trading Signals"])
app.include_router(courses.router, prefix="/courses", tags=["Courses"])
app.include_router(webinars.router, prefix="/webinars", tags=["Webinars"])
app.include_router(blog.router, prefix="/blog", tags=["Blog"])
app.include_router(ai_screening.router, prefix="/ai", tags=["AI Services"])
app.include_router(performance.router, prefix="/ai/performance", tags=["Performance"])
app.include_router(admin.router, prefix="/admin", tags=["Administration"])
app.include_router(blog_enhanced.router, prefix="/blog", tags=["Blog Enhanced"])
app.include_router(courses_enhanced.router, prefix="/courses", tags=["Courses Enhanced"])

# ==========================================
# STATIC FILES - FIXED PATHS
# ==========================================

# Get absolute path to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. Mount /js folder for JavaScript files (FIXED: points to frontend/js)
JS_DIR = os.path.join(BASE_DIR, "frontend", "js")
if os.path.exists(JS_DIR):
    app.mount("/js", StaticFiles(directory=JS_DIR), name="js")
    print(f"[STATIC] Mounted /js from {JS_DIR}", flush=True)
else:
    # Fallback: try js folder in current directory
    if os.path.exists("js"):
        app.mount("/js", StaticFiles(directory="js"), name="js")
        print("[STATIC] Mounted /js from js/", flush=True)

# 2. Mount /static folder for HTML and other static files
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print(f"[STATIC] Mounted /static from frontend/static", flush=True)
else:
    # Fallback: try root static folder
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    if os.path.exists(STATIC_DIR):
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
        print(f"[STATIC] Mounted /static from root static", flush=True)
    else:
        print(f"[WARNING] Static directory not found", flush=True)

# ==========================================
# SPA ROUTING - Serve index.html for all non-API routes
# ==========================================

@app.get("/")
async def serve_index():
    """Serve index.html for root path"""
    # Try multiple locations for index.html
    possible_paths = [
        os.path.join(BASE_DIR, "frontend", "static", "index.html"),
        os.path.join(BASE_DIR, "static", "index.html"),
        os.path.join(STATIC_DIR, "index.html") if 'STATIC_DIR' in locals() else "",
        "static/index.html"
    ]
    
    for index_path in possible_paths:
        if index_path and os.path.exists(index_path):
            return FileResponse(index_path)
    
    return JSONResponse({
        "message": "Pipways API Server",
        "status": "running",
        "docs": "/docs",
        "hint": "Frontend not found"
    })

@app.get("/dashboard.html")
async def serve_dashboard():
    """Serve dashboard.html"""
    possible_paths = [
        os.path.join(BASE_DIR, "frontend", "static", "dashboard.html"),
        os.path.join(BASE_DIR, "static", "dashboard.html"),
        os.path.join(STATIC_DIR, "dashboard.html") if 'STATIC_DIR' in locals() else "",
        "static/dashboard.html"
    ]
    
    for dashboard_path in possible_paths:
        if dashboard_path and os.path.exists(dashboard_path):
            return FileResponse(dashboard_path)
    
    raise HTTPException(404, "dashboard.html not found")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """
    Serve Single Page Application.
    Returns index.html for all non-API routes.
    """
    # Skip API routes (FIXED: Added "js/" to prevent SPA routing from catching JS files)
    api_prefixes = (
        "auth/", "signals/", "courses/", "webinars/", 
        "blog/", "ai/", "admin/", "health", "docs", "openapi.json",
        "static/", "js/"
    )
    if full_path.startswith(api_prefixes):
        raise HTTPException(404, "Not found")
    
    # Try to serve specific file first
    file_path = os.path.join(STATIC_DIR, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Serve index.html for SPA routing
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # Fallback
    return JSONResponse({
        "message": "Pipways API Server",
        "status": "running",
        "path": full_path
    })
