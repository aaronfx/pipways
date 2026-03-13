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
# STATIC FILES - FIXED PATH
# ==========================================

# Get absolute path to static directory (inside frontend folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")

print(f"[STATIC] Looking for static files at: {STATIC_DIR}", flush=True)
print(f"[STATIC] Directory exists: {os.path.exists(STATIC_DIR)}", flush=True)

# Mount static files if directory exists
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print(f"[STATIC] Mounted successfully from frontend/static", flush=True)
else:
    # Fallback: try root static folder
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    if os.path.exists(STATIC_DIR):
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
        print(f"[STATIC] Mounted successfully from root static", flush=True)
    else:
        print(f"[WARNING] Static directory not found", flush=True)

# ==========================================
# SPA ROUTING
# ==========================================

@app.get("/")
async def serve_index():
    """Serve index.html for root path"""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({
        "message": "Pipways API Server",
        "status": "running",
        "docs": "/docs",
        "hint": "Frontend not found"
    })

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """
    Serve Single Page Application.
    Returns index.html for all non-API routes.
    """
    # Skip API routes
    api_prefixes = (
        "auth/", "signals/", "courses/", "webinars/", 
        "blog/", "ai/", "admin/", "health", "docs", "openapi.json",
        "static/"
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
