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

from .database import database, init_database, metadata
from sqlalchemy import create_engine

# Import all routers - UPDATED with new modules
from . import auth
from . import signals
from . import courses
from . import webinars
from . import blog
from . import admin
from . import blog_enhanced
from . import courses_enhanced

# NEW: Import enhanced AI services (includes mentor, validator, signal saver)
from . import ai_services

# NEW: Import enhanced chart analysis (includes pattern library, vision analysis)
from . import chart_analysis

# NEW: Import enhanced performance (includes upload-journal, psychology insights)
from . import performance

# NEW: Import upgraded AI Mentor (Platform Intelligence System v3.0)
from . import ai_mentor

# NEW: AI Stock Research Terminal
from .stock_terminal_backend import router as stock_router

# Import stock terminal globals for initialization
import httpx
from anthropic import AsyncAnthropic
import stock_terminal_backend as stock_module

# Keep old imports for backwards compatibility if needed
# from . import ai_screening  # Can be removed if fully replaced by ai_services

print("[IMPORT] All modules loaded successfully", flush=True)

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_database()
        # Create tables if they don't exist
        try:
            database_url = os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+psycopg2://").replace("postgresql+asyncpg://", "postgresql+psycopg2://")
            if database_url:
                engine = create_engine(database_url)
                metadata.create_all(engine)
                print("[DB] Tables created/verified", flush=True)
        except Exception as e:
            print(f"[DB] Table creation skipped: {e}", flush=True)
        
        # Initialize Stock Terminal clients
        try:
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if anthropic_key:
                stock_module._anthropic = AsyncAnthropic(api_key=anthropic_key)
                stock_module._http = httpx.AsyncClient(timeout=10.0)
                print("[STOCK] Terminal clients initialized", flush=True)
            else:
                print("[STOCK] WARNING: ANTHROPIC_API_KEY not set", flush=True)
        except Exception as e:
            print(f"[STOCK] Client initialization error: {e}", flush=True)
        
        print("[STARTUP] Database connected", flush=True)
    except Exception as e:
        print(f"[STARTUP ERROR] {e}", flush=True)
    yield
    try:
        await database.disconnect()
    except:
        pass
    # Close stock terminal http client
    try:
        if stock_module._http:
            await stock_module._http.aclose()
    except:
        pass

app = FastAPI(
    title="Pipways Trading Platform",
    version="2.2.0",  # Bumped version for new features
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
    return {
        "status": "healthy",
        "version": "2.2.0",
        "features": [
            "multi_format_journal",
            "ai_trade_validator",
            "signal_generator",
            "ocr_extraction",
            "psychology_profile",
            "ai_stock_research"
        ]
    }

# ==========================================
# API ROUTES - UPDATED WITH NEW ROUTERS
# ==========================================

# Core modules
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(signals.router, prefix="/signals", tags=["Trading Signals"])
app.include_router(courses.router, prefix="/courses", tags=["Courses"])
app.include_router(webinars.router, prefix="/webinars", tags=["Webinars"])
app.include_router(blog.router, prefix="/blog", tags=["Blog"])
app.include_router(admin.router, prefix="/admin", tags=["Administration"])
app.include_router(blog_enhanced.router, prefix="/blog", tags=["Blog Enhanced"])
app.include_router(courses_enhanced.router, prefix="/courses", tags=["Courses Enhanced"])

# UPDATED: AI Services Router (enhanced with validator, signal saver, symbol detection)
# This router includes: /mentor/ask, /trade/validate, /signal/save, /chart/analyze, /performance/analyze-journal
app.include_router(ai_services.router, prefix="/ai", tags=["AI Services"])

# NEW: Chart Analysis Router (pattern library, enhanced analysis)
# Mounted at /ai/chart - provides: /analyze, /pattern-library
app.include_router(chart_analysis.router, prefix="/ai/chart", tags=["Chart Analysis"])

# UPDATED: Performance Router (upload-journal endpoint, psychology insights)
# Mounted at /ai/performance - provides: /upload-journal, /analyze-journal, /dashboard, /equity-curve, /monthly-analysis
app.include_router(performance.router, prefix="/ai/performance", tags=["Performance Analytics"])

# NEW: AI Mentor Router (context-aware coach, insights, recommendations)
# Mounted at /ai/mentor - provides: /ask, /insights, /history, /clear-history
app.include_router(ai_mentor.router, prefix="/ai/mentor", tags=["AI Mentor v3.0"])

# NEW: AI Stock Research Terminal Router
# Mounted at /api/stock - provides: /quote, /overview, /analyze, /portfolio, /compare
app.include_router(stock_router, prefix="/api/stock", tags=["Stock Terminal"])

# NOTE: If you were using ai_screening before, it can be removed since ai_services replaces it
# If keeping for backwards compatibility, uncomment:
# app.include_router(ai_screening.router, prefix="/ai/legacy", tags=["AI Legacy"])

# ==========================================
# STATIC FILES - FIXED PATHS
# ==========================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Mount /js folder for JavaScript files
JS_DIR = os.path.join(BASE_DIR, "frontend", "js")
if os.path.exists(JS_DIR):
    app.mount("/js", StaticFiles(directory=JS_DIR), name="js")
    print(f"[STATIC] Mounted /js from {JS_DIR}", flush=True)
else:
    if os.path.exists("js"):
        app.mount("/js", StaticFiles(directory="js"), name="js")
        print("[STATIC] Mounted /js from js/", flush=True)

# Mount /static folder for HTML and other static files
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print(f"[STATIC] Mounted /static from frontend/static", flush=True)
else:
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    if os.path.exists(STATIC_DIR):
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
        print(f"[STATIC] Mounted /static from root static", flush=True)

# ==========================================
# SPA ROUTING
# ==========================================

@app.get("/")
async def serve_index():
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
        "version": "2.2.0",
        "docs": "/docs",
        "hint": "Frontend not found"
    })

@app.get("/dashboard.html")
async def serve_dashboard():
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
    api_prefixes = (
        "auth/", "signals/", "courses/", "webinars/", 
        "blog/", "ai/", "admin/", "health", "docs", "openapi.json",
        "static/", "js/", "api/"
    )
    if full_path.startswith(api_prefixes):
        raise HTTPException(404, "Not found")

    file_path = os.path.join(STATIC_DIR, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)

    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    return JSONResponse({
        "message": "Pipways API Server",
        "status": "running",
        "version": "2.2.0",
        "path": full_path
    })
