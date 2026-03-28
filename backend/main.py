from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import os
from pathlib import Path

# Import all route modules
from backend.auth import router as auth_router, get_current_user
from backend.routes.signals import router as signals_router  # GreenXTrades signals (routes/signals.py)
from backend.courses import router as courses_router
from backend.courses_enhanced import router as courses_enhanced_router
from backend.webinars import router as webinars_router
from backend.blog import router as blog_router
from backend.blog_enhanced import router as blog_enhanced_router
from backend.admin import router as admin_router
from backend.ai_services import router as ai_router
from backend.chart_analysis import router as chart_analysis_router
from backend.performance import router as performance_router
from backend.ai_mentor import router as ai_mentor_router
from backend.ai_insights import router as ai_insights_router
from backend.stock_terminal_backend import router as stock_router
from backend.cms import router as cms_router
from backend.payments import router as payments_router
from backend.email_service import router as email_router
from backend.academy_routes import router as learning_router
from backend.risk_calculator import router as risk_router

# Import database (databases library pattern - no get_database needed)
from backend.database import database, init_database, run_migrations, run_unique_index_migrations

# Define BASE_DIR before any route handlers
BASE_DIR = Path(__file__).parent  # /app/backend
FRONTEND_DIR = BASE_DIR.parent / "frontend"  # /app/frontend

# Debug: Print paths at import time
print(f"[PATH DEBUG] __file__ = {__file__}", flush=True)
print(f"[PATH DEBUG] BASE_DIR = {BASE_DIR}", flush=True)
print(f"[PATH DEBUG] FRONTEND_DIR = {FRONTEND_DIR}", flush=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    await init_database()
    print("✅ Database initialized")
    
    # Run schema migrations (from database.py)
    await run_migrations()
    await run_unique_index_migrations()
    
    # Enhanced Signals column migration (NO seed data)
    await run_enhanced_signals_migration()
    
    yield
    # Cleanup on shutdown
    await database.disconnect()
    print("🔄 Application shutting down")

async def run_enhanced_signals_migration():
    """
    Run enhanced signals migration after existing database initialization.
    
    ⚠️ NO SEED DATA — Only schema changes
    Bot is the ONLY source of real signals.
    """
    
    try:
        print("[ENHANCED SIGNALS] Checking migration status...")
        
        # Get existing columns
        existing_query = """
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'signals' AND table_schema = 'public'
        """
        existing_rows = await database.fetch_all(existing_query)
        existing_columns = [row["column_name"] for row in existing_rows]
        
        # All columns we need
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
            ('expires_at', 'TIMESTAMP'),
            ('ai_confidence', 'INTEGER'),
            ('confidence', 'INTEGER DEFAULT 75'),
            ('entry', 'VARCHAR(50)'),
            ('target', 'VARCHAR(50)'),
            ('stop', 'VARCHAR(50)'),
            ('pattern_points', 'TEXT'),  # JSON: [{time, price}, ...]
            ('pattern_lines', 'TEXT'),   # JSON: [{start: {time, price}, end: {time, price}}, ...]
            ('is_pattern_idea', 'BOOLEAN DEFAULT FALSE'),
            ('is_published', 'BOOLEAN DEFAULT TRUE'),
            ('technical_summary', 'TEXT'),
            ('volatility_index', 'FLOAT'),
        ]
        
        # Add missing columns
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
        
        # Add performance indexes
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_signals_pattern ON signals(pattern)',
            'CREATE INDEX IF NOT EXISTS idx_signals_asset_type ON signals(asset_type)',
            'CREATE INDEX IF NOT EXISTS idx_signals_confidence ON signals(confidence)',
            'CREATE INDEX IF NOT EXISTS idx_signals_expires_at ON signals(expires_at)',
            'CREATE INDEX IF NOT EXISTS idx_signals_country ON signals(country)',
            'CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status)',
        ]
        
        for index_sql in indexes:
            try:
                await database.execute(index_sql)
            except Exception as e:
                print(f"[ENHANCED SIGNALS] ⚠️  Error adding index: {e}")
        
        # Update existing records with defaults (NOT inserting new records)
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
        
        # ⚠️ NO SEED DATA — Bot is the only source of signals
        # add_sample_enhanced_signals() REMOVED
        
        print(f"[ENHANCED SIGNALS] 🎉 Migration completed: {columns_added} columns added")
        print("[ENHANCED SIGNALS] ℹ️  No seed data injected — bot is the only signal source")
        return True
            
    except Exception as e:
        print(f"[ENHANCED SIGNALS] ❌ Migration error: {e}")
        return False

# Create FastAPI app with lifespan
app = FastAPI(
    title="Pipways API",
    description="Nigerian Forex Trading Education & AI Tools Platform",
    version="2.5.0",  # Version bump for clean signal system
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Include all routers with their prefixes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(signals_router)  # No prefix — full paths declared in routes/signals.py as /api/signals/*
app.include_router(courses_router, prefix="/courses", tags=["Courses"])
app.include_router(courses_enhanced_router, prefix="/courses", tags=["Enhanced Courses"])
app.include_router(webinars_router, prefix="/webinars", tags=["Webinars"])
app.include_router(blog_router, prefix="/blog", tags=["Blog"])
app.include_router(blog_enhanced_router, prefix="/blog", tags=["Enhanced Blog"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(ai_router, prefix="/ai", tags=["AI Services"])
app.include_router(chart_analysis_router, prefix="/ai/chart", tags=["Chart Analysis"])
app.include_router(performance_router, prefix="/ai/performance", tags=["Performance Analytics"])
app.include_router(ai_mentor_router, prefix="/ai/mentor", tags=["AI Mentor"])
app.include_router(ai_insights_router, prefix="/ai/insights", tags=["AI Insights"])
app.include_router(stock_router, prefix="/api/stock", tags=["Stock Research"])
app.include_router(cms_router, prefix="/cms", tags=["Content Management"])
app.include_router(payments_router, prefix="/payments", tags=["Payments"])
app.include_router(email_router, prefix="/email", tags=["Email Services"])
app.include_router(learning_router, prefix="/learning", tags=["Learning Management"])
app.include_router(risk_router, prefix="/risk", tags=["Risk Calculator"])

# Mount static files (with existence check to prevent crash)
static_dir = FRONTEND_DIR / "static"
js_dir = FRONTEND_DIR / "js"

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

# Enhanced signals content endpoint
@app.get("/static/enhanced_signals_content.html")
async def get_enhanced_signals_content():
    """Serve the enhanced signals page content"""
    try:
        content_path = FRONTEND_DIR / "static" / "enhanced_signals_content.html"
        if not content_path.exists():
            raise HTTPException(status_code=404, detail="Enhanced signals content not found")
        
        with open(content_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Enhanced signals content not found")
    except Exception as e:
        print(f"Error serving enhanced signals content: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# NOTE: /signals/active legacy route removed.
# Use /api/signals/active or /api/signals/enhanced instead.

# Root endpoint
@app.get("/")
async def read_root():
    """Serve the landing page"""
    try:
        index_path = FRONTEND_DIR / "static" / "index.html"
        if not index_path.exists():
            return HTMLResponse(content="<h1>Pipways API</h1><p>Welcome to Pipways - Nigeria's Trading Education Platform</p>")
        
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        print(f"Error serving index page: {e}")
        return HTMLResponse(content="<h1>Pipways API</h1><p>Welcome to Pipways</p>")

# Dashboard endpoint
@app.get("/dashboard")
async def get_dashboard():
    """Serve the main dashboard"""
    try:
        dashboard_path = FRONTEND_DIR / "static" / "dashboard.html"
        if not dashboard_path.exists():
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        with open(dashboard_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    except Exception as e:
        print(f"Error serving dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Dashboard with .html extension (common request pattern)
@app.get("/dashboard.html")
async def get_dashboard_html():
    """Serve the dashboard (with .html extension)"""
    return await get_dashboard()

# Academy endpoint
@app.get("/academy")
async def get_academy():
    """Serve the trading academy"""
    try:
        academy_path = FRONTEND_DIR / "static" / "academy.html"
        if not academy_path.exists():
            raise HTTPException(status_code=404, detail="Academy not found")
        
        with open(academy_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Academy not found")
    except Exception as e:
        print(f"Error serving academy: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Pricing endpoint
@app.get("/pricing")
async def get_pricing():
    """Serve the pricing page"""
    try:
        pricing_path = FRONTEND_DIR / "static" / "pricing.html"
        if not pricing_path.exists():
            raise HTTPException(status_code=404, detail="Pricing page not found")
        
        with open(pricing_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Pricing page not found")
    except Exception as e:
        print(f"Error serving pricing page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Risk calculator endpoint (public)
@app.get("/risk-calculator")
async def get_risk_calculator():
    """Serve the public risk calculator"""
    try:
        risk_calc_path = FRONTEND_DIR / "static" / "risk_calculator.html"
        if not risk_calc_path.exists():
            raise HTTPException(status_code=404, detail="Risk calculator not found")
        
        with open(risk_calc_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Risk calculator not found")
    except Exception as e:
        print(f"Error serving risk calculator: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Stock terminal endpoint
@app.get("/stock-terminal")
async def get_stock_terminal():
    """Serve the stock research terminal"""
    try:
        stock_terminal_path = FRONTEND_DIR / "static" / "stock_terminal.html"
        if not stock_terminal_path.exists():
            raise HTTPException(status_code=404, detail="Stock terminal not found")
        
        with open(stock_terminal_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Stock terminal not found")
    except Exception as e:
        print(f"Error serving stock terminal: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.5.0",
        "platform": "Pipways",
        "features": [
            "Trading Academy",
            "AI Chart Analysis", 
            "AI Mentor",
            "Performance Analytics",
            "Enhanced Market Signals",
            "Risk Calculator",
            "AI Stock Research",
            "Blog & Content",
            "Webinars",
            "Payments (Paystack)"
        ],
        "enhanced_signals": "active",
        "signal_source": "bot_only"  # Indicates no fake data
    }

# API info endpoint
@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "name": "Pipways API",
        "version": "2.5.0",
        "description": "Nigerian Forex Trading Education & AI Tools Platform",
        "signal_system": {
            "source": "trading_bot",
            "fake_data": False,
            "endpoint": "/api/signals/enhanced"
        },
        "features": {
            "authentication": "/auth",
            "signals": "/api/signals",
            "enhanced_signals": "/api/signals/enhanced",
            "courses": "/courses", 
            "webinars": "/webinars",
            "blog": "/blog",
            "admin": "/admin",
            "ai_services": "/ai",
            "chart_analysis": "/ai/chart",
            "performance": "/ai/performance", 
            "ai_mentor": "/ai/mentor",
            "stock_research": "/api/stock",
            "cms": "/cms",
            "payments": "/payments",
            "email": "/email",
            "learning": "/learning",
            "risk_calculator": "/risk"
        },
        "documentation": "/docs"
    }

# Favicon endpoint
@app.get("/favicon.ico")
async def get_favicon():
    """Serve favicon"""
    favicon_path = FRONTEND_DIR / "static" / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    else:
        return HTMLResponse(content="", status_code=204)

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler — API paths return JSON; everything else redirects to SPA root."""
    from fastapi.responses import JSONResponse
    path = request.url.path
    is_api = (
        path.startswith("/api/")
        or path.startswith("/auth/")
        or path.startswith("/signals/")
        or path.startswith("/courses/")
        or path.startswith("/webinars/")
        or path.startswith("/blog/")
        or path.startswith("/admin/")
        or path.startswith("/ai/")
        or path.startswith("/cms/")
        or path.startswith("/payments/")
        or path.startswith("/email/")
        or path.startswith("/learning/")
        or path.startswith("/risk/")
    )
    if is_api:
        return JSONResponse(status_code=404, content={"detail": "Endpoint not found"})
    return RedirectResponse(url="/", status_code=302)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler"""
    print(f"Internal server error: {exc}")
    
    if request.url.path.startswith("/api/") or request.url.path.startswith("/auth/"):
        return {"detail": "Internal server error"}
    else:
        return HTMLResponse(
            content="""
            <html>
                <head><title>Server Error - Pipways</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1>Something went wrong</h1>
                    <p>We're working to fix this issue. Please try again later.</p>
                    <a href="/" style="color: #007bff;">← Back to Home</a>
                </body>
            </html>
            """,
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
