"""Pipways Trading Platform - Main Application"""
import os
import sys
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .database import database, init_database, metadata, run_migrations
from sqlalchemy import create_engine

# Import all routers
from . import auth
from . import signals
from . import courses
from . import webinars
from . import blog
from . import admin
from . import blog_enhanced
from . import courses_enhanced
from . import ai_services
from . import chart_analysis
from . import performance
from . import ai_mentor
from . import ai_insights   # Proactive AI Insight Engine
from . import cms
from . import learning              # ← Trading Academy LMS
try:
    from .lms_init import init_lms_tables
    _HAS_LMS_INIT = True
except ImportError:
    _HAS_LMS_INIT = False
    async def init_lms_tables():
        print("[LMS INIT] lms_init.py not found — skipping LMS table setup", flush=True)

# ── FIX 1 (CRITICAL): Use a SINGLE relative import for stock_terminal_backend.
#
#    The previous code had TWO separate import statements:
#
#       from .stock_terminal_backend import router as stock_router   ← package module
#       import stock_terminal_backend as stock_module                ← TOP-LEVEL module
#
#    Python treats these as DIFFERENT module objects with DIFFERENT global variables.
#    The lifespan set  stock_module._anthropic = ...  on the top-level copy,
#    but the router ran inside the package copy where _anthropic was still None.
#    This caused AttributeError → FastAPI returned plain-text "Internal Server Error"
#    → frontend JSON.parse() crashed with "Unexpected token 'I'...".
#
#    Fix: use ONE relative import for both the module reference and the router.
from . import stock_terminal_backend as stock_module
stock_router = stock_module.router          # same object, same globals

from anthropic import AsyncAnthropic
import httpx  # Required for chart analysis HTTP client

print("[IMPORT] All modules loaded successfully", flush=True)

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Single source of truth for the application version.
# Update this constant only; all references below use it automatically.
APP_VERSION = "2.3.0"

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_database()
        try:
            database_url = os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+psycopg2://").replace("postgresql+asyncpg://", "postgresql+psycopg2://")
            if database_url:
                engine = create_engine(database_url)
                metadata.create_all(engine)
                print("[DB] Tables created/verified", flush=True)
        except Exception as e:
            print(f"[DB] Table creation skipped: {e}", flush=True)

        # ── Run column migrations (ADD COLUMN IF NOT EXISTS — fully idempotent) ─
        try:
            await run_migrations()
        except Exception as e:
            print(f"[DB MIGRATION] Error: {e}", flush=True)

        # ── Run LMS table initialisation (idempotent) ──────────────────────
        try:
            await init_lms_tables()
        except Exception as e:
            print(f"[LMS INIT] Error: {e}", flush=True)

        # ── Initialise Chart Analysis HTTP client (connection pooling) ──────────
        try:
            chart_analysis._http_client = httpx.AsyncClient(timeout=60.0)
            print("[CHART] HTTP client initialized", flush=True)
        except Exception as e:
            print(f"[CHART] HTTP client init error: {e}", flush=True)

        # ── Initialise Stock Terminal Anthropic client ─────────────────────
        # httpx removed — data is now fetched via yfinance (no HTTP client needed).
        try:
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if anthropic_key:
                stock_module._anthropic = AsyncAnthropic(api_key=anthropic_key)
                print("[STOCK] Anthropic client initialised", flush=True)
            else:
                print("[STOCK] WARNING: ANTHROPIC_API_KEY not set — stock terminal disabled", flush=True)
        except Exception as e:
            print(f"[STOCK] Client initialisation error: {e}", flush=True)

        print("[STARTUP] Database connected", flush=True)

        # ── Initialise CMS settings table (idempotent) ────────────────────
        try:
            await cms._ensure_settings_table()
            print("[CMS] Settings table ready", flush=True)
        except Exception as e:
            print(f"[CMS] Settings table init skipped: {e}", flush=True)
    except Exception as e:
        print(f"[STARTUP ERROR] {e}", flush=True)

    yield

    # ── Cleanup ────────────────────────────────────────────────────────────
    try:
        await database.disconnect()
    except Exception as e:
        # FIX: was bare `except: pass` — errors are now logged so they are not
        # silently swallowed during shutdown, aiding post-mortem debugging.
        print(f"[SHUTDOWN] database.disconnect() error: {e}", flush=True)

    # Close chart analysis HTTP client
    try:
        if chart_analysis._http_client:
            await chart_analysis._http_client.aclose()
            print("[CHART] HTTP client closed", flush=True)
    except Exception:
        pass

    # Close stock terminal HTTP client if it was lazy-initialized
    try:
        if stock_module._http is not None:
            await stock_module._http.aclose()
            print("[STOCK] HTTP client closed", flush=True)
    except Exception:
        pass


app = FastAPI(
    title="Pipways Trading Platform",
    version=APP_VERSION,
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
        "version": APP_VERSION,
        "stock_terminal": {
            "anthropic_ready": stock_module._anthropic is not None,
            "data_source":     "yfinance (free)",
        },
        "chart_analysis": {
            "http_pooling": chart_analysis._http_client is not None
        },
        "features": [
            "multi_format_journal",
            "ai_trade_validator",
            "signal_generator",
            "ocr_extraction",
            "psychology_profile",
            "ai_stock_research",
            "chart_analysis_caching",
            "proactive_ai_insights",
            "trading_academy_lms"
        ]
    }

# ==========================================
# API ROUTES
# ==========================================

app.include_router(auth.router,             prefix="/auth",           tags=["Authentication"])
app.include_router(signals.router,          prefix="/signals",        tags=["Trading Signals"])
app.include_router(courses.router,          prefix="/courses",        tags=["Courses"])
app.include_router(webinars.router,         prefix="/webinars",       tags=["Webinars"])
app.include_router(blog.router,             prefix="/blog",           tags=["Blog"])
app.include_router(admin.router,            prefix="/admin",          tags=["Administration"])
app.include_router(blog_enhanced.router,    prefix="/blog",           tags=["Blog Enhanced"])
app.include_router(courses_enhanced.router, prefix="/courses",        tags=["Courses Enhanced"])
app.include_router(ai_services.router,      prefix="/ai",             tags=["AI Services"])
app.include_router(chart_analysis.router,   prefix="/ai/chart",       tags=["Chart Analysis"])
app.include_router(performance.router,      prefix="/ai/performance", tags=["Performance Analytics"])
app.include_router(ai_insights.router,      prefix="/ai/mentor",      tags=["AI Insights Engine"])
app.include_router(ai_mentor.router,        prefix="/ai/mentor",      tags=["AI Mentor v3.0"])
app.include_router(cms.router,              prefix="/cms",            tags=["CMS"])
app.include_router(learning.router,         prefix="/learning",       tags=["Learning"])    # ← Trading Academy LMS

# Stock Terminal — uses the corrected single-import router reference
app.include_router(stock_router,            prefix="/api/stock",      tags=["Stock Terminal"])

# ==========================================
# STATIC FILES
# ==========================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JS_DIR = os.path.join(BASE_DIR, "frontend", "js")
if os.path.exists(JS_DIR):
    app.mount("/js", StaticFiles(directory=JS_DIR), name="js")
    print(f"[STATIC] Mounted /js from {JS_DIR}", flush=True)
elif os.path.exists("js"):
    app.mount("/js", StaticFiles(directory="js"), name="js")
    print("[STATIC] Mounted /js from js/", flush=True)

STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
if not os.path.exists(STATIC_DIR):
    STATIC_DIR = os.path.join(BASE_DIR, "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print(f"[STATIC] Mounted /static from {STATIC_DIR}", flush=True)

# ==========================================
# SPA ROUTING
# ==========================================

@app.get("/")
async def serve_index():
    for path in [
        os.path.join(BASE_DIR, "frontend", "static", "index.html"),
        os.path.join(BASE_DIR, "static", "index.html"),
        os.path.join(STATIC_DIR, "index.html"),
        "static/index.html",
    ]:
        if path and os.path.exists(path):
            return FileResponse(path)
    return JSONResponse({"message": "Pipways API Server", "status": "running", "version": APP_VERSION, "docs": "/docs"})


@app.get("/dashboard.html")
async def serve_dashboard():
    for path in [
        os.path.join(BASE_DIR, "frontend", "static", "dashboard.html"),
        os.path.join(BASE_DIR, "static", "dashboard.html"),
        os.path.join(STATIC_DIR, "dashboard.html"),
        "static/dashboard.html",
    ]:
        if path and os.path.exists(path):
            return FileResponse(path)
    raise HTTPException(404, "dashboard.html not found")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    api_prefixes = (
        "auth/", "signals/", "courses/", "webinars/",
        "blog/", "ai/", "admin/", "cms/", "learning/", "health", "docs", "openapi.json",
        "static/", "js/", "api/",
    )
    if full_path.startswith(api_prefixes):
        raise HTTPException(404, "Not found")

    file_path = os.path.join(STATIC_DIR, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)

    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    return JSONResponse({"message": "Pipways API Server", "status": "running", "version": APP_VERSION, "path": full_path})
