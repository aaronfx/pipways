"""
Main FastAPI application entry point.
Uses RELATIVE imports to work as a Python package.
Run with: uvicorn backend.main:app (from root directory)
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import select

# RELATIVE imports from sibling modules (not via __init__.py)
from .database import database, metadata, users
from .security import get_password_hash, get_current_user

# Import routers DIRECTLY from modules (avoiding __init__.py circular imports)
from .auth import router as auth_router
from .signals import router as signals_router
from .courses import router as courses_router
from .blog import router as blog_router
from .webinars import router as webinars_router
from .media import router as media_router
from .admin import router as admin_router
from .notifications import router as notifications_router
from .payments import router as payments_router
from .risk_calculator import router as risk_router
from .ai_screening import router as ai_screening_router
from .blog_enhanced import router as blog_enhanced_router
from .courses_enhanced import router as courses_enhanced_router

# NEW AI modules - import routers directly
from .ai_mentor import router as ai_mentor_router
from .chart_analysis import router as chart_analysis_router
from .performance_analyzer import router as performance_router

# Create FastAPI app
app = FastAPI(
    title="Pipways Trading Platform API",
    description="Professional trading signals and analysis platform with AI features",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080,https://pipwaysapp.onrender.com").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Determine the correct path to frontend directory
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# Mount static files FIRST (before routes)
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    print(f"✓ Mounted static files from: {FRONTEND_DIR}", flush=True)
else:
    print(f"⚠ Frontend directory not found at: {FRONTEND_DIR}", flush=True)

async def create_default_admin():
    """Create default admin user if no admin exists."""
    try:
        # Check if admin exists
        query = users.select().where(users.c.email == "admin@pipways.com")
        existing = await database.fetch_one(query)
        
        if not existing:
            # Create default admin
            admin_data = {
                "email": "admin@pipways.com",
                "password_hash": get_password_hash("admin123"),
                "full_name": "System Administrator",
                "is_active": True,
                "is_admin": True,
                "created_at": datetime.utcnow()
            }
            
            # Add role column if it exists in schema
            if hasattr(users.c, 'role'):
                admin_data["role"] = "admin"
            
            query = users.insert().values(**admin_data)
            await database.execute(query)
            print("✓ Default admin created: admin@pipways.com / admin123", flush=True)
        else:
            print("✓ Admin user already exists", flush=True)
            
    except Exception as e:
        print(f"⚠ Admin initialization error: {e}", flush=True)

@app.on_event("startup")
async def startup():
    """Connect to database and initialize admin user."""
    await database.connect()
    print("✓ Database connected", flush=True)
    
    # Initialize admin user
    await create_default_admin()

@app.on_event("shutdown")
async def shutdown():
    """Disconnect from database on shutdown."""
    await database.disconnect()
    print("✓ Database disconnected", flush=True)

# Health check endpoint (must be BEFORE root route)
@app.get("/health")
async def health_check():
    """Health check for Render monitoring."""
    return {
        "status": "healthy",
        "service": "pipways-api",
        "version": "2.0.0",
        "timestamp": str(datetime.utcnow())
    }

# API info endpoint
@app.get("/api")
async def api_info():
    """API info and available endpoints."""
    return {
        "message": "Welcome to Pipways Trading Platform API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "features": [
            "Trading Signals",
            "Course Management", 
            "Blog & Content",
            "Webinars",
            "AI Market Analysis",
            "AI Mentor",
            "Chart Pattern Recognition",
            "Performance Analytics",
            "Risk Calculator"
        ],
        "endpoints": {
            "auth": "/auth",
            "signals": "/signals",
            "courses": "/courses",
            "blog": "/blog",
            "webinars": "/webinars",
            "admin": "/admin",
            "notifications": "/notifications",
            "payments": "/payments",
            "risk": "/risk",
            "ai": {
                "market_analysis": "/ai/analyze",
                "batch_screening": "/ai/batch-screen",
                "sentiment": "/ai/sentiment/{symbol}",
                "signal_validation": "/ai/validate-signal",
                "mentor": {
                    "ask": "/ai/mentor/ask",
                    "learning_path": "/ai/mentor/learning-path",
                    "trade_review": "/ai/mentor/review-trade",
                    "daily_wisdom": "/ai/mentor/daily-wisdom"
                },
                "chart": {
                    "analyze_image": "/ai/chart/analyze",
                    "patterns": "/ai/chart/pattern-library",
                    "multichart": "/ai/chart/scan-multichart"
                },
                "performance": {
                    "analyze_journal": "/ai/performance/analyze-journal",
                    "dashboard": "/ai/performance/dashboard-stats"
                }
            }
        }
    }

# Serve frontend files
@app.get("/")
async def serve_index():
    """Serve the login landing page."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        return {
            "error": "Frontend not found",
            "path": str(index_file),
            "api_docs": "/docs",
            "api_endpoints": "/api"
        }

@app.get("/dashboard.html")
async def serve_dashboard():
    """Serve the main dashboard app."""
    dashboard_file = FRONTEND_DIR / "dashboard.html"
    if dashboard_file.exists():
        return FileResponse(str(dashboard_file))
    else:
        return {"error": "Dashboard not found", "path": str(dashboard_file)}

# Include all API routers with explicit prefixes
# Auth router (prefix already included in router)
app.include_router(auth_router)

# Core feature routers
app.include_router(signals_router, prefix="/signals", tags=["signals"])
app.include_router(courses_router, prefix="/courses", tags=["courses"])
app.include_router(blog_router, prefix="/blog", tags=["blog"])
app.include_router(webinars_router, prefix="/webinars", tags=["webinars"])
app.include_router(media_router, prefix="/media", tags=["media"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])

# Utility routers
app.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
app.include_router(payments_router, prefix="/payments", tags=["payments"])
app.include_router(risk_router, prefix="/risk", tags=["risk"])

# Enhanced feature routers
app.include_router(blog_enhanced_router, prefix="/blog-enhanced", tags=["blog-enhanced"])
app.include_router(courses_enhanced_router, prefix="/courses-enhanced", tags=["courses-enhanced"])

# AI Feature routers
app.include_router(ai_screening_router, prefix="/ai", tags=["ai"])
app.include_router(ai_mentor_router, prefix="/ai/mentor", tags=["ai-mentor"])
app.include_router(chart_analysis_router, prefix="/ai/chart", tags=["chart-analysis"])
app.include_router(performance_router, prefix="/ai/performance", tags=["performance"])
