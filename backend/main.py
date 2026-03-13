"""
Pipways Trading Platform - Main Application
PRODUCTION READY - With Enhanced Features
"""
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from .database import database, init_database

# Import all routers
from . import auth
from . import signals
from . import courses
from . import webinars
from . import blog
from . import ai_screening
from . import performance
from . import admin
from . import blog_enhanced      # ENHANCED: Blog with comments/tags/SEO
from . import courses_enhanced  # ENHANCED: Progress tracking & certificates

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    print(f"[STARTUP] Environment: {ENVIRONMENT}", flush=True)
    try:
        await init_database()
        print("[STARTUP] Database connected", flush=True)
    except Exception as e:
        print(f"[STARTUP ERROR] Database connection failed: {e}", flush=True)
        # Continue anyway - graceful degradation
    
    yield
    
    # Shutdown
    try:
        await database.disconnect()
        print("[SHUTDOWN] Database disconnected", flush=True)
    except:
        pass

# Create FastAPI app
app = FastAPI(
    title="Pipways Trading Platform",
    description="Professional trading signals and AI analysis platform",
    version="2.1.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL] if FRONTEND_URL != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# API ROUTES - CORE
# ==========================================

@app.get("/health")
async def health_check():
    """System health check endpoint"""
    try:
        await database.fetch_one("SELECT 1")
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "version": "2.1.0",
        "environment": ENVIRONMENT,
        "features": ["core", "enhanced_blog", "enhanced_courses"]
    }

# Core routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(signals.router, prefix="/signals", tags=["Trading Signals"])
app.include_router(courses.router, prefix="/courses", tags=["Courses"])
app.include_router(webinars.router, prefix="/webinars", tags=["Webinars"])
app.include_router(blog.router, prefix="/blog", tags=["Blog"])
app.include_router(ai_screening.router, prefix="/ai", tags=["AI Services"])
app.include_router(performance.router, prefix="/ai/performance", tags=["Performance Analytics"])
app.include_router(admin.router, prefix="/admin", tags=["Administration"])

# ==========================================
# API ROUTES - ENHANCED FEATURES
# ==========================================

# Enhanced Blog (SEO, comments, tags)
app.include_router(blog_enhanced.router, prefix="/blog", tags=["Blog Enhanced"])

# Enhanced Courses (progress tracking, certificates)
app.include_router(courses_enhanced.router, prefix="/courses", tags=["Courses Enhanced"])

# ==========================================
# STATIC FILES & SPA ROUTING
# ==========================================

# Mount static files directory
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    print("[WARNING] Static directory not found, skipping mount", flush=True)

# Serve frontend SPA - catch all routes and serve index.html
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """
    Serve Single Page Application (SPA).
    Returns index.html for all non-API routes.
    """
    # Don't interfere with API routes
    if full_path.startswith(("api/", "auth/", "signals/", "courses/", 
                            "webinars/", "blog/", "ai/", "admin/", "health")):
        raise HTTPException(404, "Not found")
    
    # Check for static file first
    static_file = f"static/{full_path}"
    if os.path.exists(static_file) and os.path.isfile(static_file):
        return FileResponse(static_file)
    
    # Serve index.html for all other routes (SPA routing)
    index_path = "static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # Fallback if no frontend files
    return {
        "message": "Pipways API Server",
        "status": "running",
        "docs": "/docs"
    }
