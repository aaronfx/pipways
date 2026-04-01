from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from pathlib import Path
from backend.auth import router as auth_router
from backend.routes.signals import router as signals_router
from backend.courses import router as courses_router
from backend.courses_enhanced import router as courses_enhanced_router
from backend.webinars import router as webinars_router
from backend.blog import router as blog_router
from backend.blog_enhanced import router as blog_enhanced_router
from backend.admin import router as admin_router
from backend.ai_services import router as ai_router
from backend.chart_analysis import router as chart_analysis_router
from backend.chart_analysis import init_chart_http_client, close_chart_http_client
from backend.performance import router as performance_router
from backend.ai_mentor import router as ai_mentor_router
from backend.ai_insights import router as ai_insights_router
from backend.stock_terminal_backend import router as stock_router
from backend.cms import router as cms_router
from backend.payments import router as payments_router
from backend.email_service import router as email_router
from backend.academy_routes import router as learning_router
from backend.risk_calculator import router as risk_router
from backend.database import database, init_database, run_migrations, run_unique_index_migrations
BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
print(f"[PATH DEBUG] __file__ = {__file__}", flush=True)
print(f"[PATH DEBUG] BASE_DIR = {BASE_DIR}", flush=True)
print(f"[PATH DEBUG] FRONTEND_DIR = {FRONTEND_DIR}", flush=True)

# M7 — single version constant, referenced everywhere
APP_VERSION = "2.5.0"

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database()
    print("✅ Database initialized")
    await run_migrations()
    await run_unique_index_migrations()
    await run_enhanced_signals_migration()
    await init_chart_http_client()
    print("✅ Chart analysis HTTP client initialized")
    from backend.subscriptions import init_subscription_tables
    await init_subscription_tables()
    # M1 — ensure email tables exist (password_reset_tokens, email_logs, preferences)
    from backend.email_service import ensure_email_tables
    await ensure_email_tables()
    # M3 — auto-promote admin via ADMIN_EMAIL env var
    admin_email = os.getenv("ADMIN_EMAIL", "").lower().strip()
    if admin_email:
        try:
            await database.execute(
                "UPDATE users SET is_admin = TRUE WHERE LOWER(email) = :email",
                {"email": admin_email}
            )
            print(f"[ADMIN] Auto-promoted {admin_email}", flush=True)
        except Exception as e:
            print(f"[ADMIN] Auto-promote warning: {e}", flush=True)
    yield
    await close_chart_http_client()
    await database.disconnect()
    print("🔄 Application shutting down")


async def run_enhanced_signals_migration():
    try:
        print("[ENHANCED SIGNALS] Checking migration status...")
        existing_query = """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'signals' AND table_schema = 'public'
        """
        existing_rows = await database.fetch_all(existing_query)
        existing_columns = [row["column_name"] for row in existing_rows]
        new_columns = [
            ('pattern', 'VARCHAR(50)'),
            ('full_name', 'TEXT'),
            ('asset_type', "VARCHAR(50) DEFAULT 'forex'"),
            ('country', "VARCHAR(10) DEFAULT 'all'"),
            ('sentiment_bearish', 'INTEGER DEFAULT 50'),
            ('sentiment_bullish', 'INTEGER DEFAULT 50'),
            ('current_price', 'VARCHAR(20)'),
            ('price_change', 'VARCHAR(20)'),
            ('price_change_percent', 'VARCHAR(20)'),
            ('chart_data', 'TEXT'),
            ('expires_at', 'TIMESTAMPTZ'),
            ('ai_confidence', 'FLOAT DEFAULT 0.5'),
            ('confidence', 'INTEGER DEFAULT 75'),
            ('entry', 'VARCHAR(50)'),
            ('target', 'VARCHAR(50)'),
            ('stop', 'VARCHAR(50)'),
            ('pattern_points', "JSONB DEFAULT '[]'"),
            ('pattern_lines',  "JSONB DEFAULT '[]'"),
            ('is_pattern_idea', 'BOOLEAN DEFAULT FALSE'),
            ('is_published', 'BOOLEAN DEFAULT TRUE'),
            ('technical_summary', 'TEXT'),
            ('volatility_index', 'FLOAT'),
            ('pattern_name',   'TEXT'),
            ('structure',      'TEXT'),
            ('bias_d1',        'TEXT'),
            ('bias_h4',        'TEXT'),
            ('bos_m5',         'TEXT'),
            ('breakout_point', 'JSONB'),
            ('candles',        "JSONB DEFAULT '[]'"),
            ('timeframe',      "TEXT DEFAULT 'M5'"),
            ('rationale',      'TEXT'),
            ('entry_price',    'NUMERIC(20, 8)'),
            ('take_profit',    'NUMERIC(20, 8)'),
            ('stop_loss',      'NUMERIC(20, 8)'),
            ('updated_at',     'TIMESTAMPTZ'),
        ]
        columns_added = 0
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    await database.execute(
                        f"ALTER TABLE signals ADD COLUMN IF NOT EXISTS {column_name} {column_type}"
                    )
                    print(f"[ENHANCED SIGNALS] ✅ Added column: {column_name}")
                    columns_added += 1
                except Exception as e:
                    print(f"[ENHANCED SIGNALS] ⚠️  Error adding column {column_name}: {e}")
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_signals_pattern ON signals(pattern)',
            'CREATE INDEX IF NOT EXISTS idx_signals_asset_type ON signals(asset_type)',
            'CREATE INDEX IF NOT EXISTS idx_signals_confidence ON signals(confidence)',
            'CREATE INDEX IF NOT EXISTS idx_signals_expires_at ON signals(expires_at)',
            'CREATE INDEX IF NOT EXISTS idx_signals_country ON signals(country)',
            'CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status)',
            """CREATE INDEX IF NOT EXISTS idx_signals_enhanced
               ON signals (status, is_published, expires_at, created_at DESC)
               WHERE status = 'active' AND is_published = TRUE""",
        ]
        for index_sql in indexes:
            try:
                await database.execute(index_sql)
            except Exception as e:
                print(f"[ENHANCED SIGNALS] ⚠️  Error adding index: {e}")
        update_queries = [
            "UPDATE signals SET asset_type = 'forex' WHERE asset_type IS NULL",
            "UPDATE signals SET country = 'all' WHERE country IS NULL",
            "UPDATE signals SET sentiment_bearish = 50 WHERE sentiment_bearish IS NULL",
            "UPDATE signals SET sentiment_bullish = 50 WHERE sentiment_bullish IS NULL",
            "UPDATE signals SET ai_confidence = confidence WHERE ai_confidence IS NULL AND confidence IS NOT NULL"
        ]
        for query in update_queries:
            try:
                await database.execute(query)
            except Exception as e:
                print(f"[ENHANCED SIGNALS] ⚠️  Error updating data: {e}")
        print(f"[ENHANCED SIGNALS] 🎉 Migration completed: {columns_added} columns added")
        print("[ENHANCED SIGNALS] ℹ️  No seed data injected — bot is the only signal source")
        return True
    except Exception as e:
        print(f"[ENHANCED SIGNALS] ❌ Migration error: {e}")
        return False


# M4 — rebranded title/description; M7 — use APP_VERSION
app = FastAPI(
    title="Gopipways API",
    description="Gopipways — Nigeria's Trading Education & AI Platform",
    version=APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gopipways.com",
        "https://www.gopipways.com",
        "http://localhost:8000",
        "http://localhost:3000",   # M5 — local frontend dev server
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,             prefix="/auth",           tags=["Authentication"])
app.include_router(signals_router)
app.include_router(courses_router,          prefix="/courses",        tags=["Courses"])
app.include_router(courses_enhanced_router, prefix="/courses",        tags=["Enhanced Courses"])
app.include_router(webinars_router,         prefix="/webinars",       tags=["Webinars"])
app.include_router(blog_router,             prefix="/blog",           tags=["Blog"])
app.include_router(blog_enhanced_router,    prefix="/blog",           tags=["Enhanced Blog"])
app.include_router(admin_router,            prefix="/admin",          tags=["Admin"])
app.include_router(ai_router,               prefix="/ai",             tags=["AI Services"])
app.include_router(chart_analysis_router,   prefix="/ai/chart",       tags=["Chart Analysis"])
app.include_router(performance_router,      prefix="/ai/performance", tags=["Performance Analytics"])
app.include_router(ai_mentor_router,        prefix="/ai/mentor",      tags=["AI Mentor"])
app.include_router(ai_insights_router,      prefix="/ai/insights",    tags=["AI Insights"])
app.include_router(stock_router,            prefix="/api/stock",      tags=["Stock Research"])
app.include_router(cms_router,              prefix="/cms",            tags=["Content Management"])
app.include_router(payments_router,         prefix="/payments",       tags=["Payments"])
app.include_router(email_router,            prefix="/email",          tags=["Email Services"])
app.include_router(learning_router,         prefix="/learning",       tags=["Learning Management"])
app.include_router(risk_router,             prefix="/risk",           tags=["Risk Calculator"])

static_dir = FRONTEND_DIR / "static"
js_dir     = FRONTEND_DIR / "js"
print(f"[STATIC] Looking for frontend at: {FRONTEND_DIR}", flush=True)
print(f"[STATIC] static_dir exists: {static_dir.exists()}", flush=True)
print(f"[STATIC] js_dir exists: {js_dir.exists()}", flush=True)
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    print(f"[STATIC] ✅ Mounted /static from {static_dir}", flush=True)
else:
    print(f"[STATIC] ⚠️ Static directory not found: {static_dir}", flush=True)
if js_dir.exists():
    app.mount("/js", StaticFiles(directory=js_dir), name="js")
    print(f"[STATIC] ✅ Mounted /js from {js_dir}", flush=True)
else:
    print(f"[STATIC] ⚠️ JS directory not found: {js_dir}", flush=True)


def _read_html(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/static/enhanced_signals_content.html")
async def get_enhanced_signals_content():
    try:
        p = FRONTEND_DIR / "static" / "enhanced_signals_content.html"
        if not p.exists():
            raise HTTPException(status_code=404, detail="Enhanced signals content not found")
        return HTMLResponse(content=_read_html(p))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Enhanced signals content not found")
    except Exception as e:
        print(f"Error serving enhanced signals content: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/")
async def read_root():
    try:
        p = FRONTEND_DIR / "static" / "index.html"
        if not p.exists():
            return HTMLResponse(content="<h1>Gopipways API</h1><p>Welcome to Gopipways — Nigeria's Trading Education Platform</p>")
        return HTMLResponse(content=_read_html(p))
    except Exception as e:
        print(f"Error serving index page: {e}")
        return HTMLResponse(content="<h1>Gopipways API</h1><p>Welcome to Gopipways</p>")


async def _serve_html(path: Path, name: str) -> HTMLResponse:
    try:
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"{name} not found")
        return HTMLResponse(content=_read_html(path))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"{name} not found")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error serving {name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/dashboard")
async def get_dashboard():
    return await _serve_html(FRONTEND_DIR / "static" / "dashboard.html", "Dashboard")

@app.get("/dashboard.html")
async def get_dashboard_html():
    return await get_dashboard()

@app.get("/academy")
async def get_academy():
    return await _serve_html(FRONTEND_DIR / "static" / "academy.html", "Academy")

@app.get("/pricing")
async def get_pricing():
    return await _serve_html(FRONTEND_DIR / "static" / "pricing.html", "Pricing")

@app.get("/risk-calculator")
async def get_risk_calculator():
    return await _serve_html(FRONTEND_DIR / "static" / "risk_calculator.html", "Risk Calculator")

@app.get("/stock-terminal")
async def get_stock_terminal():
    return await _serve_html(FRONTEND_DIR / "static" / "stock_terminal.html", "Stock Terminal")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": APP_VERSION,   # M7
        "platform": "Gopipways",  # M4
        "features": [
            "Trading Academy", "AI Chart Analysis", "AI Mentor",
            "Performance Analytics", "Enhanced Market Signals",
            "Risk Calculator", "AI Stock Research", "Blog & Content",
            "Webinars", "Payments (Paystack)"
        ],
        "enhanced_signals": "active",
        "signal_source": "bot_only"
    }


@app.get("/api/info")
async def api_info():
    return {
        "name": "Gopipways API",   # M4
        "version": APP_VERSION,    # M7
        "description": "Gopipways — Nigeria's Trading Education & AI Platform",
        "signal_system": {"source": "trading_bot", "fake_data": False, "endpoint": "/api/signals/enhanced"},
        "features": {
            "authentication": "/auth", "signals": "/api/signals",
            "enhanced_signals": "/api/signals/enhanced", "courses": "/courses",
            "webinars": "/webinars", "blog": "/blog", "admin": "/admin",
            "ai_services": "/ai", "chart_analysis": "/ai/chart",
            "performance": "/ai/performance", "ai_mentor": "/ai/mentor",
            "stock_research": "/api/stock", "cms": "/cms",
            "payments": "/payments", "email": "/email",
            "learning": "/learning", "risk_calculator": "/risk"
        },
        "documentation": "/docs"
    }


@app.get("/favicon.ico")
async def get_favicon():
    favicon_path = FRONTEND_DIR / "static" / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    return HTMLResponse(content="", status_code=204)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    from fastapi.responses import JSONResponse
    path = request.url.path
    # M2 — removed trailing slashes from all prefix checks
    api_prefixes = (
        "/api", "/auth", "/signals", "/courses", "/webinars",
        "/blog", "/admin", "/ai", "/cms", "/payments",
        "/email", "/learning", "/risk", "/health", "/favicon"
    )
    if any(path.startswith(p) for p in api_prefixes):
        return JSONResponse(status_code=404, content={"detail": "Endpoint not found"})
    # M6 — return a proper 404 page instead of redirect loop
    return HTMLResponse(
        content="""<!DOCTYPE html><html>
        <head><title>Page Not Found — Gopipways</title></head>
        <body style="font-family:Arial,sans-serif;text-align:center;padding:80px;background:#0f172a;color:#e2e8f0;">
          <h1 style="font-size:64px;color:#7c3aed;margin:0;">404</h1>
          <h2 style="margin:12px 0;">Page Not Found</h2>
          <p style="color:#94a3b8;">The page you're looking for doesn't exist.</p>
          <a href="/" style="display:inline-block;margin-top:20px;background:#7c3aed;color:white;
             padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;">
            ← Back to Gopipways
          </a>
        </body></html>""",
        status_code=404
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    print(f"Internal server error: {exc}")
    from fastapi.responses import JSONResponse
    if any(request.url.path.startswith(p) for p in ("/api", "/auth")):
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
    return HTMLResponse(
        content="""<!DOCTYPE html><html>
        <head><title>Server Error — Gopipways</title></head>
        <body style="font-family:Arial,sans-serif;text-align:center;padding:80px;background:#0f172a;color:#e2e8f0;">
          <h1 style="color:#ef4444;">Something went wrong</h1>
          <p style="color:#94a3b8;">We're working to fix this. Please try again later.</p>
          <a href="/" style="display:inline-block;margin-top:20px;background:#7c3aed;color:white;
             padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;">
            ← Back to Home
          </a>
        </body></html>""",
        status_code=500
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
