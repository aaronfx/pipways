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
from backend.signals import router as signals_router  # Enhanced signals
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
print(f"[PATH DEBUG] BASE_DIR.parent = {BASE_DIR.parent}", flush=True)
print(f"[PATH DEBUG] FRONTEND_DIR = {FRONTEND_DIR}", flush=True)
print(f"[PATH DEBUG] FRONTEND_DIR exists = {FRONTEND_DIR.exists()}", flush=True)

# List what's in the parent directory
try:
    parent_contents = list(BASE_DIR.parent.iterdir())
    print(f"[PATH DEBUG] Contents of {BASE_DIR.parent}: {[p.name for p in parent_contents]}", flush=True)
except Exception as e:
    print(f"[PATH DEBUG] Could not list parent dir: {e}", flush=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    await init_database()
    print("✅ Database initialized")
    
    # Run schema migrations (from database.py)
    await run_migrations()
    await run_unique_index_migrations()
    
    # Enhanced Signals Auto-Migration
    await run_enhanced_signals_migration()
    
    yield
    # Cleanup on shutdown
    await database.disconnect()
    print("🔄 Application shutting down")

async def run_enhanced_signals_migration():
    """Run enhanced signals migration after existing database initialization"""
    
    try:
        print("[ENHANCED SIGNALS] Checking migration status...")
        
        # Check if migration is needed - using databases library pattern
        check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'signals' 
            AND table_schema = 'public'
            AND column_name IN ('pattern', 'full_name', 'asset_type')
        """
        rows = await database.fetch_all(check_query)
        enhanced_columns = [row["column_name"] for row in rows]
        
        if len(enhanced_columns) >= 3:
            print("[ENHANCED SIGNALS] ✅ Migration already applied")
            return True
            
        print("[ENHANCED SIGNALS] 🔄 Running migration...")
        
        # Add new columns
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
        ]
        
        # Get existing columns
        existing_query = """
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'signals' AND table_schema = 'public'
        """
        existing_rows = await database.fetch_all(existing_query)
        existing_columns = [row["column_name"] for row in existing_rows]
        
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
            'CREATE INDEX IF NOT EXISTS idx_signals_country ON signals(country)'
        ]
        
        for index_sql in indexes:
            try:
                await database.execute(index_sql)
            except Exception as e:
                print(f"[ENHANCED SIGNALS] ⚠️  Error adding index: {e}")
        
        # Update existing records with defaults
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
        
        # Add sample data if needed
        await add_sample_enhanced_signals()
        
        # Add site settings for enhanced signals
        await add_enhanced_signals_site_settings()
        
        print(f"[ENHANCED SIGNALS] 🎉 Migration completed: {columns_added} columns added")
        return True
            
    except Exception as e:
        print(f"[ENHANCED SIGNALS] ❌ Migration error: {e}")
        return False

async def add_sample_enhanced_signals():
    """Add sample enhanced signals if none exist — includes AI-Driven + AnalysisIQ signals"""
    
    try:
        # Check if we have any active signals
        result = await database.fetch_val("SELECT COUNT(*) FROM signals WHERE status = 'active'")
        
        if result and result > 0:
            print(f"[ENHANCED SIGNALS] ⏭️  Found {result} existing active signals, skipping seed")
            return
        
        print("[ENHANCED SIGNALS] 🧪 Seeding 15 sample signals (7 AI-Driven + 8 AnalysisIQ)...")
        
        # Complete seed data: 7 AI-Driven (confidence >= 75) + 8 AnalysisIQ (is_pattern_idea = True)
        sample_signals = [
            # ══════════════════════════════════════════════════════════════════════
            # AI-DRIVEN SIGNALS (confidence >= 75, is_pattern_idea = False)
            # ══════════════════════════════════════════════════════════════════════
            {'symbol': 'EURUSD', 'full_name': 'Euro vs US Dollar', 'direction': 'BUY', 'pattern': 'BREAKOUT', 'timeframe': '4H', 'entry': '1.08250', 'target': '1.08850', 'stop': '1.07850', 'entry_price': 1.08250, 'take_profit': 1.08850, 'stop_loss': 1.07850, 'confidence': 88, 'ai_confidence': 88, 'asset_type': 'forex', 'country': 'EU', 'sentiment_bearish': 25, 'sentiment_bullish': 75, 'status': 'active', 'is_published': True, 'is_pattern_idea': False, 'expires_hours': 24},
            {'symbol': 'GBPUSD', 'full_name': 'British Pound vs US Dollar', 'direction': 'BUY', 'pattern': 'FLAG', 'timeframe': '1H', 'entry': '1.26750', 'target': '1.27350', 'stop': '1.26350', 'entry_price': 1.26750, 'take_profit': 1.27350, 'stop_loss': 1.26350, 'confidence': 82, 'ai_confidence': 82, 'asset_type': 'forex', 'country': 'UK', 'sentiment_bearish': 30, 'sentiment_bullish': 70, 'status': 'active', 'is_published': True, 'is_pattern_idea': False, 'expires_hours': 36},
            {'symbol': 'USDJPY', 'full_name': 'US Dollar vs Japanese Yen', 'direction': 'SELL', 'pattern': 'REVERSAL', 'timeframe': '4H', 'entry': '149.850', 'target': '148.850', 'stop': '150.350', 'entry_price': 149.850, 'take_profit': 148.850, 'stop_loss': 150.350, 'confidence': 79, 'ai_confidence': 79, 'asset_type': 'forex', 'country': 'JP', 'sentiment_bearish': 65, 'sentiment_bullish': 35, 'status': 'active', 'is_published': True, 'is_pattern_idea': False, 'expires_hours': 48},
            {'symbol': 'AUDUSD', 'full_name': 'Australian Dollar vs US Dollar', 'direction': 'BUY', 'pattern': 'SUPPORT', 'timeframe': '1H', 'entry': '0.67850', 'target': '0.68450', 'stop': '0.67450', 'entry_price': 0.67850, 'take_profit': 0.68450, 'stop_loss': 0.67450, 'confidence': 85, 'ai_confidence': 85, 'asset_type': 'forex', 'country': 'AU', 'sentiment_bearish': 28, 'sentiment_bullish': 72, 'status': 'active', 'is_published': True, 'is_pattern_idea': False, 'expires_hours': 72},
            {'symbol': 'US30', 'full_name': 'Dow Jones Industrial Average', 'direction': 'BUY', 'pattern': 'BREAKOUT', 'timeframe': '1H', 'entry': '38950', 'target': '39250', 'stop': '38700', 'entry_price': 38950, 'take_profit': 39250, 'stop_loss': 38700, 'confidence': 84, 'ai_confidence': 84, 'asset_type': 'indices', 'country': 'US', 'sentiment_bearish': 22, 'sentiment_bullish': 78, 'status': 'active', 'is_published': True, 'is_pattern_idea': False, 'expires_hours': 24},
            {'symbol': 'XAUUSD', 'full_name': 'Gold vs US Dollar', 'direction': 'BUY', 'pattern': 'SUPPORT', 'timeframe': '4H', 'entry': '2345.50', 'target': '2385.00', 'stop': '2320.00', 'entry_price': 2345.50, 'take_profit': 2385.00, 'stop_loss': 2320.00, 'confidence': 86, 'ai_confidence': 86, 'asset_type': 'commodities', 'country': 'all', 'sentiment_bearish': 20, 'sentiment_bullish': 80, 'status': 'active', 'is_published': True, 'is_pattern_idea': False, 'expires_hours': 36},
            {'symbol': 'BTCUSD', 'full_name': 'Bitcoin vs US Dollar', 'direction': 'BUY', 'pattern': 'BREAKOUT', 'timeframe': '4H', 'entry': '67500', 'target': '72000', 'stop': '64500', 'entry_price': 67500, 'take_profit': 72000, 'stop_loss': 64500, 'confidence': 77, 'ai_confidence': 77, 'asset_type': 'crypto', 'country': 'all', 'sentiment_bearish': 32, 'sentiment_bullish': 68, 'status': 'active', 'is_published': True, 'is_pattern_idea': False, 'expires_hours': 48},

            # ══════════════════════════════════════════════════════════════════════
            # ANALYSISIQ / PATTERN IDEAS (is_pattern_idea = True)
            # ══════════════════════════════════════════════════════════════════════
            {'symbol': 'AUDCAD', 'full_name': 'Australian Dollar vs Canadian Dollar', 'direction': 'BUY', 'pattern': 'FLAG', 'timeframe': '1H', 'entry': '0.95426', 'target': '0.95800', 'stop': '0.95200', 'entry_price': 0.95426, 'take_profit': 0.95800, 'stop_loss': 0.95200, 'confidence': 72, 'ai_confidence': 72, 'asset_type': 'forex', 'country': 'AU', 'sentiment_bearish': 35, 'sentiment_bullish': 65, 'status': 'active', 'is_published': True, 'is_pattern_idea': True, 'expires_hours': 72},
            {'symbol': 'NZDUSD', 'full_name': 'New Zealand Dollar vs US Dollar', 'direction': 'BUY', 'pattern': 'FLAG', 'timeframe': '4H', 'entry': '0.61250', 'target': '0.61750', 'stop': '0.60900', 'entry_price': 0.61250, 'take_profit': 0.61750, 'stop_loss': 0.60900, 'confidence': 68, 'ai_confidence': 68, 'asset_type': 'forex', 'country': 'NZ', 'sentiment_bearish': 38, 'sentiment_bullish': 62, 'status': 'active', 'is_published': True, 'is_pattern_idea': True, 'expires_hours': 24},
            {'symbol': 'EURSEEK', 'full_name': 'Euro vs Swedish Krona', 'direction': 'SELL', 'pattern': 'WEDGE', 'timeframe': '4H', 'entry': '10.8830', 'target': '10.8400', 'stop': '10.9100', 'entry_price': 10.8830, 'take_profit': 10.8400, 'stop_loss': 10.9100, 'confidence': 70, 'ai_confidence': 70, 'asset_type': 'forex', 'country': 'EU', 'sentiment_bearish': 58, 'sentiment_bullish': 42, 'status': 'active', 'is_published': True, 'is_pattern_idea': True, 'expires_hours': 36},
            {'symbol': 'GBPJPY', 'full_name': 'British Pound vs Japanese Yen', 'direction': 'BUY', 'pattern': 'WEDGE', 'timeframe': '1H', 'entry': '189.450', 'target': '190.450', 'stop': '188.750', 'entry_price': 189.450, 'take_profit': 190.450, 'stop_loss': 188.750, 'confidence': 74, 'ai_confidence': 74, 'asset_type': 'forex', 'country': 'UK', 'sentiment_bearish': 32, 'sentiment_bullish': 68, 'status': 'active', 'is_published': True, 'is_pattern_idea': True, 'expires_hours': 48},
            {'symbol': 'CHINA50', 'full_name': 'China A50 Index', 'direction': 'BUY', 'pattern': 'PENNANT', 'timeframe': '1H', 'entry': '14495', 'target': '14650', 'stop': '14380', 'entry_price': 14495, 'take_profit': 14650, 'stop_loss': 14380, 'confidence': 78, 'ai_confidence': 78, 'asset_type': 'indices', 'country': 'CN', 'sentiment_bearish': 28, 'sentiment_bullish': 72, 'status': 'active', 'is_published': True, 'is_pattern_idea': True, 'expires_hours': 72},
            {'symbol': 'XAGUSD', 'full_name': 'Silver vs US Dollar', 'direction': 'BUY', 'pattern': 'TRIANGLE', 'timeframe': '4H', 'entry': '27.850', 'target': '28.550', 'stop': '27.350', 'entry_price': 27.850, 'take_profit': 28.550, 'stop_loss': 27.350, 'confidence': 71, 'ai_confidence': 71, 'asset_type': 'commodities', 'country': 'all', 'sentiment_bearish': 40, 'sentiment_bullish': 60, 'status': 'active', 'is_published': True, 'is_pattern_idea': True, 'expires_hours': 24},
            {'symbol': 'ETHUSD', 'full_name': 'Ethereum vs US Dollar', 'direction': 'BUY', 'pattern': 'DOUBLE_BOTTOM', 'timeframe': '4H', 'entry': '3450', 'target': '3650', 'stop': '3300', 'entry_price': 3450, 'take_profit': 3650, 'stop_loss': 3300, 'confidence': 69, 'ai_confidence': 69, 'asset_type': 'crypto', 'country': 'all', 'sentiment_bearish': 42, 'sentiment_bullish': 58, 'status': 'active', 'is_published': True, 'is_pattern_idea': True, 'expires_hours': 36},
            {'symbol': 'GER40', 'full_name': 'DAX 40 Index', 'direction': 'SELL', 'pattern': 'DOUBLE_TOP', 'timeframe': '1H', 'entry': '18250', 'target': '17950', 'stop': '18450', 'entry_price': 18250, 'take_profit': 17950, 'stop_loss': 18450, 'confidence': 66, 'ai_confidence': 66, 'asset_type': 'indices', 'country': 'DE', 'sentiment_bearish': 58, 'sentiment_bullish': 42, 'status': 'active', 'is_published': True, 'is_pattern_idea': True, 'expires_hours': 48},
        ]
        
        seeded = 0
        for signal in sample_signals:
            try:
                # Extract expires_hours and remove from dict (not a DB column)
                expires_hours = signal.pop('expires_hours', 24)
                
                # Build raw SQL INSERT (avoids SQLAlchemy column validation issues)
                insert_sql = """
                INSERT INTO signals (
                    symbol, full_name, direction, pattern, timeframe,
                    entry, target, stop, entry_price, take_profit, stop_loss,
                    confidence, ai_confidence, asset_type, country,
                    sentiment_bearish, sentiment_bullish, status,
                    is_published, is_pattern_idea, created_at, expires_at
                ) VALUES (
                    :symbol, :full_name, :direction, :pattern, :timeframe,
                    :entry, :target, :stop, :entry_price, :take_profit, :stop_loss,
                    :confidence, :ai_confidence, :asset_type, :country,
                    :sentiment_bearish, :sentiment_bullish, :status,
                    :is_published, :is_pattern_idea, NOW(), NOW() + INTERVAL '%s hours'
                )
                """ % expires_hours
                
                await database.execute(insert_sql, signal)
                tag = "AnalysisIQ" if signal.get('is_pattern_idea') else "AI-Driven"
                print(f"[ENHANCED SIGNALS] ✅ Seeded [{tag}]: {signal['symbol']} ({signal['pattern']})")
                seeded += 1
            except Exception as e:
                print(f"[ENHANCED SIGNALS] ⚠️  Error seeding {signal.get('symbol', '?')}: {e}")
        
        print(f"[ENHANCED SIGNALS] 🎉 Seeded {seeded}/15 signals")
            
    except Exception as e:
        print(f"[ENHANCED SIGNALS] ⚠️  Error in auto-seed: {e}")

async def add_enhanced_signals_site_settings():
    """Add site settings for enhanced signals features"""
    
    try:
        # Check if site_settings table exists
        result = await database.fetch_val("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'site_settings'
            )
        """)
        
        if not result:
            print("[ENHANCED SIGNALS] ⚠️  site_settings table not found, skipping settings")
            return
        
        settings = [
            ('signals_visible_free', '3'),
            ('signals_visible_pro', 'none'),
            ('signals_detailed_analysis_free', '1'),
            ('signals_detailed_analysis_pro', 'none'),
            ('signals_chart_access_free', 'false'),
            ('signals_chart_access_pro', 'true'),
            ('signals_pattern_filtering_free', 'false'),
            ('signals_pattern_filtering_pro', 'true'),
            ('signals_email_alerts_free', 'false'),
            ('signals_email_alerts_pro', 'true')
        ]
        
        settings_added = 0
        for key, value in settings:
            try:
                # Check if setting exists
                exists = await database.fetch_val(
                    "SELECT COUNT(*) FROM site_settings WHERE key = :key",
                    {'key': key}
                )
                
                if not exists or exists == 0:
                    # Add new setting (site_settings has key, value, updated_at columns)
                    await database.execute(
                        "INSERT INTO site_settings (key, value, updated_at) VALUES (:key, :value, NOW())",
                        {'key': key, 'value': value}
                    )
                    settings_added += 1
                    
            except Exception as e:
                print(f"[ENHANCED SIGNALS] ⚠️  Error adding setting {key}: {e}")
        
        if settings_added > 0:
            print(f"[ENHANCED SIGNALS] ✅ Added {settings_added} site settings")
                
    except Exception as e:
        print(f"[ENHANCED SIGNALS] ⚠️  Error updating site settings: {e}")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Pipways API",
    description="Nigerian Forex Trading Education & AI Tools Platform",
    version="2.4.0",
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
app.include_router(signals_router, prefix="/signals", tags=["Trading Signals"])  # Enhanced signals
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

# Legacy signals route compatibility
@app.get("/signals/active")
async def get_active_signals_legacy(current_user: dict = Depends(get_current_user)):
    """Legacy endpoint - redirect to enhanced signals"""
    return RedirectResponse(url="/signals/enhanced", status_code=301)

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
        "version": "2.4.0",
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
        "enhanced_signals": "active"
    }

# API info endpoint
@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "name": "Pipways API",
        "version": "2.4.0",
        "description": "Nigerian Forex Trading Education & AI Tools Platform",
        "features": {
            "authentication": "/auth",
            "signals": "/signals",
            "enhanced_signals": "/signals/enhanced",
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
    """Custom 404 handler"""
    if request.url.path.startswith("/api/") or request.url.path.startswith("/auth/"):
        return {"detail": "Endpoint not found"}
    else:
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
