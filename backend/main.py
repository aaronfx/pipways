from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import os
from pathlib import Path
from sqlalchemy import text

# Import all route modules
from backend.auth import router as auth_router
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

# Import database and auth dependencies
from backend.database import init_database, get_database
from backend.auth import get_current_user

# Define BASE_DIR before any route handlers
BASE_DIR = Path(__file__).parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    await init_database()
    print("✅ Database initialized")
    
    # Railway Auto-Migration: Run enhanced signals migration
    if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('DATABASE_URL'):
        print("🚄 Railway deployment detected, running enhanced signals auto-migration...")
        
        try:
            # Run enhanced signals migration
            await railway_auto_migrate_enhanced_signals()
        except Exception as e:
            print(f"⚠️  Railway auto-migration error: {e}")
            # Don't fail startup for migration errors
    
    print("✨ Enhanced signals features are now active!")
    yield
    # Cleanup on shutdown
    print("🔄 Application shutting down")

async def railway_auto_migrate_enhanced_signals():
    """Auto-migrate enhanced signals on Railway"""
    
    try:
        async with get_database() as db:
            print("🔍 Checking enhanced signals migration status...")
            
            # Check if migration is needed
            result = await db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'signals' 
                AND table_schema = 'public'
                AND column_name IN ('pattern', 'full_name', 'asset_type');
            """))
            
            enhanced_columns = [row[0] for row in result.fetchall()]
            
            if len(enhanced_columns) >= 3:
                print("✅ Enhanced signals migration already applied")
                return True
                
            print("🔄 Running enhanced signals migration...")
            
            # Add new columns
            new_columns = [
                ('pattern', 'VARCHAR(50)'),
                ('full_name', 'TEXT'),
                ('asset_type', 'VARCHAR(50) DEFAULT \'forex\''),
                ('country', 'VARCHAR(10) DEFAULT \'all\''),
                ('sentiment_bearish', 'INTEGER DEFAULT 50'),
                ('sentiment_bullish', 'INTEGER DEFAULT 50'),
                ('current_price', 'VARCHAR(20)'),
                ('price_change', 'VARCHAR(20)'),
                ('price_change_percent', 'VARCHAR(20)'),
                ('chart_data', 'TEXT'),
                ('expires_at', 'TIMESTAMP'),
                ('ai_confidence', 'INTEGER')
            ]
            
            # Get existing columns
            result = await db.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'signals' AND table_schema = 'public';
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            
            # Add missing columns
            columns_added = 0
            for column_name, column_type in new_columns:
                if column_name not in existing_columns:
                    try:
                        await db.execute(
                            text(f"ALTER TABLE signals ADD COLUMN {column_name} {column_type};")
                        )
                        print(f"✅ Added column: {column_name}")
                        columns_added += 1
                    except Exception as e:
                        print(f"⚠️  Error adding column {column_name}: {e}")
            
            # Add performance indexes
            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_signals_pattern ON signals(pattern);',
                'CREATE INDEX IF NOT EXISTS idx_signals_asset_type ON signals(asset_type);',
                'CREATE INDEX IF NOT EXISTS idx_signals_confidence ON signals(confidence);',
                'CREATE INDEX IF NOT EXISTS idx_signals_expires_at ON signals(expires_at);',
                'CREATE INDEX IF NOT EXISTS idx_signals_country ON signals(country);'
            ]
            
            for index_sql in indexes:
                try:
                    await db.execute(text(index_sql))
                except Exception as e:
                    print(f"⚠️  Error adding index: {e}")
            
            # Update existing records with defaults
            update_queries = [
                "UPDATE signals SET asset_type = 'forex' WHERE asset_type IS NULL;",
                "UPDATE signals SET country = 'all' WHERE country IS NULL;",
                "UPDATE signals SET sentiment_bearish = 50 WHERE sentiment_bearish IS NULL;",
                "UPDATE signals SET sentiment_bullish = 50 WHERE sentiment_bullish IS NULL;",
                "UPDATE signals SET ai_confidence = confidence WHERE ai_confidence IS NULL AND confidence IS NOT NULL;"
            ]
            
            for query in update_queries:
                try:
                    await db.execute(text(query))
                except Exception as e:
                    print(f"⚠️  Error updating data: {e}")
            
            # Add sample data if needed
            await add_railway_sample_signals(db)
            
            # Add site settings for enhanced signals
            await add_railway_site_settings(db)
            
            await db.commit()
            
            print(f"🎉 Railway enhanced signals migration completed: {columns_added} columns added")
            return True
            
    except Exception as e:
        print(f"❌ Railway migration error: {e}")
        return False

async def add_railway_sample_signals(db):
    """Add sample enhanced signals for Railway deployment"""
    
    try:
        # Check if we have enhanced signals
        result = await db.execute(text("SELECT COUNT(*) FROM signals WHERE pattern IS NOT NULL;"))
        enhanced_count = result.scalar()
        
        if enhanced_count > 0:
            print(f"⏭️  Found {enhanced_count} existing enhanced signals")
            return
        
        print("🧪 Adding sample enhanced signals...")
        
        # Add sample signals
        sample_signals = [
            {
                'symbol': 'AUDCAD',
                'full_name': 'Australian Dollar vs Canadian Dollar',
                'direction': 'BUY STOP',
                'pattern': 'FLAG',
                'timeframe': '1H',
                'entry': '0.95426',
                'target': '0.95800',
                'stop': '0.95200',
                'confidence': 78,
                'asset_type': 'forex',
                'country': 'AU',
                'sentiment_bearish': 35,
                'sentiment_bullish': 65,
                'current_price': '0.95523',
                'price_change': '+0.00096',
                'price_change_percent': '+0.10%',
                'status': 'active',
                'ai_confidence': 78
            },
            {
                'symbol': 'EUR/SEK',
                'full_name': 'Euro vs Swedish Krona',
                'direction': 'SELL STOP',
                'pattern': 'WEDGE',
                'timeframe': '4H',
                'entry': '10.8830',
                'target': '10.8400',
                'stop': '10.9100',
                'confidence': 72,
                'asset_type': 'forex',
                'country': 'EU',
                'sentiment_bearish': 68,
                'sentiment_bullish': 32,
                'current_price': '10.8795',
                'price_change': '-0.0035',
                'price_change_percent': '-0.03%',
                'status': 'active',
                'ai_confidence': 72
            },
            {
                'symbol': 'CHINA50',
                'full_name': 'China A50 Index',
                'direction': 'BUY STOP',
                'pattern': 'PENNANT',
                'timeframe': '1H',
                'entry': '14495',
                'target': '14650',
                'stop': '14380',
                'confidence': 81,
                'asset_type': 'indices',
                'country': 'CN',
                'sentiment_bearish': 28,
                'sentiment_bullish': 72,
                'current_price': '14512',
                'price_change': '+17',
                'price_change_percent': '+0.12%',
                'status': 'active',
                'ai_confidence': 81
            }
        ]
        
        for signal in sample_signals:
            columns = ', '.join(signal.keys())
            placeholders = ', '.join([f":{key}" for key in signal.keys()])
            
            insert_sql = f"""
            INSERT INTO signals ({columns}, created_at, updated_at)
            VALUES ({placeholders}, NOW(), NOW());
            """
            
            await db.execute(text(insert_sql), signal)
            print(f"✅ Added sample signal: {signal['symbol']} ({signal['pattern']})")
            
    except Exception as e:
        print(f"⚠️  Error adding sample signals: {e}")

async def add_railway_site_settings(db):
    """Add site settings for enhanced signals features"""
    
    try:
        # Check if site_settings table exists
        result = await db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'site_settings'
            );
        """))
        
        if not result.scalar():
            print("⚠️  site_settings table not found, skipping settings")
            return
        
        settings = [
            ('signals_visible_free', '3', 'Signals visible to free users'),
            ('signals_visible_pro', 'none', 'Signals visible to pro users'),
            ('signals_detailed_analysis_free', '1', 'Detailed analysis for free users per day'),
            ('signals_detailed_analysis_pro', 'none', 'Detailed analysis for pro users'),
            ('signals_chart_access_free', 'false', 'Chart access for free users'),
            ('signals_chart_access_pro', 'true', 'Chart access for pro users'),
            ('signals_pattern_filtering_free', 'false', 'Pattern filtering for free users'),
            ('signals_pattern_filtering_pro', 'true', 'Pattern filtering for pro users'),
            ('signals_email_alerts_free', 'false', 'Email alerts for free users'),
            ('signals_email_alerts_pro', 'true', 'Email alerts for pro users')
        ]
        
        settings_added = 0
        for key, value, description in settings:
            try:
                # Check if setting exists
                result = await db.execute(
                    text("SELECT COUNT(*) FROM site_settings WHERE key = :key"),
                    {'key': key}
                )
                
                if result.scalar() == 0:
                    # Add new setting
                    await db.execute(text("""
                        INSERT INTO site_settings (key, value, description, created_at, updated_at)
                        VALUES (:key, :value, :description, NOW(), NOW())
                    """), {'key': key, 'value': value, 'description': description})
                    settings_added += 1
                    
            except Exception as e:
                print(f"⚠️  Error adding setting {key}: {e}")
        
        if settings_added > 0:
            print(f"✅ Added {settings_added} enhanced signals site settings")
                
    except Exception as e:
        print(f"⚠️  Error updating site settings: {e}")

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

# Mount static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend" / "static"), name="static")
app.mount("/js", StaticFiles(directory=BASE_DIR / "frontend" / "js"), name="js")

# Enhanced signals content endpoint
@app.get("/static/enhanced_signals_content.html")
async def get_enhanced_signals_content():
    """Serve the enhanced signals page content"""
    try:
        content_path = BASE_DIR / "frontend" / "static" / "enhanced_signals_content.html"
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
        index_path = BASE_DIR / "frontend" / "static" / "index.html"
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
        dashboard_path = BASE_DIR / "frontend" / "static" / "dashboard.html"
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

# Academy endpoint
@app.get("/academy")
async def get_academy():
    """Serve the trading academy"""
    try:
        academy_path = BASE_DIR / "frontend" / "static" / "academy.html"
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
        pricing_path = BASE_DIR / "frontend" / "static" / "pricing.html"
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
        risk_calc_path = BASE_DIR / "frontend" / "static" / "risk_calculator.html"
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
        stock_terminal_path = BASE_DIR / "frontend" / "static" / "stock_terminal.html"
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
            "Enhanced Market Signals",  # New feature
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
            "signals": "/signals",  # Enhanced signals
            "enhanced_signals": "/signals/enhanced",  # New enhanced endpoint
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
    favicon_path = BASE_DIR / "frontend" / "static" / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    else:
        # Return a basic response if no favicon exists
        return HTMLResponse(content="", status_code=204)

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler"""
    if request.url.path.startswith("/api/") or request.url.path.startswith("/auth/"):
        # Return JSON for API endpoints
        return {"detail": "Endpoint not found"}
    else:
        # Return HTML for web pages - redirect to home
        return RedirectResponse(url="/", status_code=302)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler"""
    print(f"Internal server error: {exc}")
    
    if request.url.path.startswith("/api/") or request.url.path.startswith("/auth/"):
        # Return JSON for API endpoints
        return {"detail": "Internal server error"}
    else:
        # Return HTML error page
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

# Startup message
@app.on_event("startup")
async def startup_event():
    """Print startup information"""
    print("🚀 Pipways API starting up...")
    print(f"📂 BASE_DIR: {BASE_DIR}")
    print("🔗 Routes mounted:")
    print("   • /auth - Authentication")
    print("   • /signals - Enhanced Trading Signals")
    print("   • /signals/enhanced - Enhanced Signals API")
    print("   • /courses - Course Management")
    print("   • /webinars - Webinar System")
    print("   • /blog - Blog & Content")
    print("   • /admin - Admin Panel")
    print("   • /ai - AI Services")
    print("   • /ai/chart - Chart Analysis")
    print("   • /ai/performance - Performance Analytics")
    print("   • /ai/mentor - AI Mentor")
    print("   • /api/stock - Stock Research")
    print("   • /cms - Content Management")
    print("   • /payments - Paystack Integration")
    print("   • /email - Email Services")
    print("   • /learning - Learning Management")
    print("   • /risk - Risk Calculator")
    print("📱 Frontend pages:")
    print("   • / - Landing Page")
    print("   • /dashboard - Main Dashboard")
    print("   • /dashboard#enhanced-signals - Enhanced Signals Interface")
    print("   • /academy - Trading Academy")
    print("   • /pricing - Pricing Plans")
    print("   • /risk-calculator - Public Risk Calculator")
    print("   • /stock-terminal - Stock Research")
    print("✨ Enhanced Market Signals with Railway auto-migration is now active!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
