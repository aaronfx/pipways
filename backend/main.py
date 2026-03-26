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
from . import ai_insights   
from . import cms

# ── Trading Academy ───────────────────────────────────────────────────────────
# academy_routes owns: GET /academy.html, GET /academy, ALL /learning/*
from .academy_routes import router as academy_router
print("[IMPORT] Academy router loaded", flush=True)

# LMS Initialization
try:
    from .lms_init import init_lms_tables, upsert_curriculum
    _HAS_LMS_INIT = True
except ImportError:
    _HAS_LMS_INIT = False
    async def init_lms_tables():
        print("[LMS INIT] lms_init.py not found — skipping LMS table setup", flush=True)
    
    async def upsert_curriculum():
        print("[LMS INIT] Cannot upsert curriculum without lms_init.py", flush=True)

# Subscription & usage enforcement
try:
    from .subscriptions import init_subscription_tables
    _HAS_SUBSCRIPTIONS = True
except ImportError:
    _HAS_SUBSCRIPTIONS = False
    async def init_subscription_tables():
        print("[SUBSCRIPTIONS] subscriptions.py not found — skipping", flush=True)

from . import stock_terminal_backend as stock_module

# Email + Health
try:
    from .email_service import (
        router as email_router,
        ensure_email_tables,
        send_welcome,
    )
    _HAS_EMAIL = True
    print("[INIT] Email service loaded", flush=True)
except Exception as _e:
    _HAS_EMAIL = False
    print(f"[INIT] Email service not loaded: {_e}", flush=True)

try:
    from .health_check import (
        router as health_router,
        ensure_health_tables,
        start_scheduler,
        stop_scheduler,
    )
    _HAS_HEALTH = True
    print("[INIT] Health check module loaded", flush=True)
except Exception as _e:
    _HAS_HEALTH = False
    print(f"[INIT] Health check module not loaded: {_e}", flush=True)
stock_router = stock_module.router

from anthropic import AsyncAnthropic
import httpx

print("[IMPORT] All modules loaded successfully", flush=True)

# ── Usage enforcement map ─────────────────────────────────────────────────────
# Maps URL prefix → feature key in subscriptions.FEATURE_CONFIG
# Middleware intercepts POST requests to these paths and enforces limits.
_USAGE_ENFORCEMENT = {
    "/ai/chart/analyse":          "chart_analysis",
    "/ai/chart/analyze":          "chart_analysis",
    "/ai/performance/analyse":    "performance",
    "/ai/performance/analyze":    "performance",
    "/ai/performance/upload":     "performance",
    "/ai/mentor/ask":             "ai_mentor",
    "/mentor/ask":                "ai_mentor",
    "/api/stock/analyse":         "stock_research",
    "/api/stock/analyze":         "stock_research",
    "/api/stock/research":        "stock_research",
}

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
APP_VERSION = "2.4.0"

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

        try:
            await run_migrations()
        except Exception as e:
            print(f"[DB MIGRATION] Error: {e}", flush=True)

        if _HAS_LMS_INIT:
            try:
                print("[LMS] Initializing tables...", flush=True)
                await init_lms_tables()  # internally calls seed_academy()
                print("[LMS] Tables ready", flush=True)
            except Exception as e:
                print(f"[LMS] Initialization error: {e}", flush=True)

        if _HAS_SUBSCRIPTIONS:
            try:
                await init_subscription_tables()
            except Exception as e:
                print(f"[SUBSCRIPTIONS] Initialization error: {e}", flush=True)

        try:
            chart_analysis._http_client = httpx.AsyncClient(timeout=60.0)
            print("[CHART] HTTP client initialized", flush=True)
        except Exception as e:
            print(f"[CHART] HTTP client init error: {e}", flush=True)

        try:
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if anthropic_key:
                stock_module._anthropic = AsyncAnthropic(api_key=anthropic_key)
                print("[STOCK] Anthropic client initialised", flush=True)
            else:
                print("[STOCK] WARNING: ANTHROPIC_API_KEY not set", flush=True)
        except Exception as e:
            print(f"[STOCK] Client initialisation error: {e}", flush=True)

        try:
            await cms._ensure_settings_table()
            print("[CMS] Settings table ready", flush=True)
        except Exception as e:
            print(f"[CMS] Settings init error: {e}", flush=True)

        if _HAS_EMAIL:
            try:
                await ensure_email_tables()
            except Exception as e:
                print(f"[EMAIL] Init error: {e}", flush=True)

        if _HAS_HEALTH:
            try:
                await ensure_health_tables()
                start_scheduler(interval_seconds=300)  # check every 5 minutes
            except Exception as e:
                print(f"[HEALTH] Init error: {e}", flush=True)

        print("[STARTUP] Database connected", flush=True)

    except Exception as e:
        print(f"[STARTUP ERROR] {e}", flush=True)
        raise

    yield

    if _HAS_HEALTH:
        try:
            stop_scheduler()
        except Exception:
            pass

    try:
        await database.disconnect()
    except Exception as e:
        print(f"[SHUTDOWN] database.disconnect() error: {e}", flush=True)

    try:
        if chart_analysis._http_client:
            await chart_analysis._http_client.aclose()
            print("[CHART] HTTP client closed", flush=True)
    except Exception:
        pass

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Usage enforcement middleware ──────────────────────────────────────────────
# Intercepts POST requests to gated feature endpoints.
# Raises 402 if the user has hit their tier limit.
# This means individual route files don't need to be modified.
@app.middleware("http")
async def enforce_usage_limits(request: Request, call_next):
    if not _HAS_SUBSCRIPTIONS:
        return await call_next(request)

    # Only enforce on POST/PUT to gated paths
    if request.method not in ("POST", "PUT"):
        return await call_next(request)

    path = request.url.path
    feature = None
    for prefix, feat in _USAGE_ENFORCEMENT.items():
        if path.startswith(prefix):
            feature = feat
            break

    if feature is None:
        return await call_next(request)

    # Extract user from Bearer token
    try:
        from jose import jwt, JWTError
        from .security import SECRET_KEY, ALGORITHM
        from .subscriptions import check_and_record_usage

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return await call_next(request)

        token = auth_header[7:]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        if not user_id:
            return await call_next(request)

        # check_and_record_usage raises HTTP 402 if limit hit,
        # records usage event if allowed
        await check_and_record_usage(int(user_id), feature)

    except HTTPException as he:
        # 402 from check_and_record_usage — return as JSON
        return JSONResponse(
            status_code=he.status_code,
            content=he.detail if isinstance(he.detail, dict) else {"error": he.detail}
        )
    except Exception as e:
        # Non-fatal — if middleware errors, allow request through
        print(f"[USAGE MIDDLEWARE] Non-fatal error for {path}: {e}", flush=True)

    return await call_next(request)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "lms_available": _HAS_LMS_INIT,
        "subscriptions_available": _HAS_SUBSCRIPTIONS,
        "academy_router": True,
        "stock_terminal": {
            "anthropic_ready": stock_module._anthropic is not None,
            "data_source": "yfinance (free)",
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
            "trading_academy_lms",
            "subscription_enforcement",
            "usage_tracking",
        ]
    }

@app.post("/admin/init-academy")
async def init_academy():
    """Manually initialize academy curriculum (admin only)"""
    if not _HAS_LMS_INIT:
        raise HTTPException(status_code=503, detail="LMS module not available")
    try:
        await upsert_curriculum()
        return {"status": "success", "message": "Academy curriculum initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/academy/reseed")
async def admin_reseed_academy():
    """Force wipe and reseed the full academy curriculum from v2 seed file."""
    if not _HAS_LMS_INIT:
        raise HTTPException(status_code=503, detail="LMS module not available")
    try:
        from .lms_init import force_reseed_academy
        await force_reseed_academy()
        return {"status": "success", "message": "Academy reseeded from v2 curriculum"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pricing.html")
async def serve_pricing():
    for path in [
        os.path.join(BASE_DIR, "frontend", "static", "pricing.html"),
        os.path.join(BASE_DIR, "frontend", "pricing.html"),
        os.path.join(BASE_DIR, "static", "pricing.html"),
        os.path.join(STATIC_DIR, "pricing.html"),
        "static/pricing.html",
        "pricing.html",
    ]:
        if path and os.path.exists(path):
            return FileResponse(path)
    raise HTTPException(404, "pricing.html not found")

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
app.include_router(stock_router,            prefix="/api/stock",      tags=["Stock Terminal"])

if _HAS_EMAIL:
    app.include_router(email_router, prefix="/email", tags=["Email"])
    print("[ROUTES] Email router mounted (/email)", flush=True)

if _HAS_HEALTH:
    app.include_router(health_router, prefix="/health", tags=["Health"])
    print("[ROUTES] Health check router mounted (/health)", flush=True)

# Academy: no prefix — router owns /academy.html, /academy, /learning/*, /admin/academy/*
app.include_router(academy_router, tags=["Academy"])
print("[ROUTES] Academy router mounted (/academy.html + /academy + /learning/* + /admin/academy/*)", flush=True)

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
    return JSONResponse({
        "message": "Pipways API Server", 
        "status": "running", 
        "version": APP_VERSION, 
        "docs": "/docs",
        "academy_status": "configured"
    })

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
        "blog/", "ai/", "admin/", "cms/", "learning/", "api/",
        "academy", "health", "docs", "openapi.json",
        "static/", "js/",
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
        "version": APP_VERSION, 
        "path": full_path
    })
