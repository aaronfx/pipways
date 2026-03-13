"""
Main FastAPI application entry point.
Uses RELATIVE imports to work as a Python package.
Run with: uvicorn backend.main:app (from root directory)
"""
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select

# RELATIVE imports (from .module)
from .database import database, metadata, users
from .security import get_password_hash, get_current_user

# Import all route modules using RELATIVE imports
from . import auth, signals, courses, blog, webinars, media, admin
from . import notifications, payments, risk_calculator, ai_screening, blog_enhanced, courses_enhanced
from . import ai_mentor, chart_analysis, performance_analyzer

# Create FastAPI app
app = FastAPI(
    title="Pipways Trading Platform API",
    description="Professional trading signals and analysis platform with AI features",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global exception handler to ensure JSON responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Ensure all errors return JSON."""
    print(f"Global error: {str(exc)}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
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
            if hasattr(users.c, 'subscription_tier'):
                admin_data["subscription_tier"] = "admin"
            
            query = users.insert().values(**admin_data)
            await database.execute(query)
            print("✓ Default admin created: admin@pipways.com / admin123", flush=True)
        else:
            print("✓ Admin user already exists", flush=True)
            
    except Exception as e:
        print(f"⚠ Admin initialization error: {e}", flush=True)
        # Don't raise - allow app to continue

@app.on_event("startup")
async def startup():
    """Connect to database and initialize admin user."""
    try:
        await database.connect()
        print("✓ Database connected", flush=True)
        
        # Initialize admin user
        await create_default_admin()
    except Exception as e:
        print(f"⚠ Startup error: {e}", flush=True)
        # Don't crash - let health check handle it

@app.on_event("shutdown")
async def shutdown():
    """Disconnect from database on shutdown."""
    try:
        if database.is_connected:
            await database.disconnect()
            print("✓ Database disconnected", flush=True)
    except Exception as e:
        print(f"⚠ Shutdown error: {e}", flush=True)

# Health check endpoint (must be BEFORE root route)
@app.get("/health")
async def health_check():
    """Health check for Render monitoring."""
    db_status = "connected" if database.is_connected else "disconnected"
    return {
        "status": "healthy" if database.is_connected else "unhealthy",
        "service": "pipways-api",
        "version": "2.0.0",
        "database": db_status,
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
            "ai": "/ai"
        }
    }

# Serve frontend files
@app.get("/")
async def serve_index():
    """Serve the login landing page."""
    try:
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        else:
            return JSONResponse(
                status_code=404,
                content={"error": "Frontend not found", "path": str(index_file)}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to serve frontend", "detail": str(e)}
        )

@app.get("/dashboard.html")
async def serve_dashboard():
    """Serve the main dashboard app."""
    try:
        dashboard_file = FRONTEND_DIR / "dashboard.html"
        if dashboard_file.exists():
            return FileResponse(str(dashboard_file))
        else:
            return JSONResponse(
                status_code=404,
                content={"error": "Dashboard not found", "path": str(dashboard_file)}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to serve dashboard", "detail": str(e)}
        )

# Include all API routers
app.include_router(auth.router)
app.include_router(signals.router, prefix="/signals", tags=["signals"])
app.include_router(courses.router, prefix="/courses", tags=["courses"])
app.include_router(blog.router, prefix="/blog", tags=["blog"])
app.include_router(webinars.router, prefix="/webinars", tags=["webinars"])
app.include_router(media.router, prefix="/media", tags=["media"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
app.include_router(payments.router, prefix="/payments", tags=["payments"])
app.include_router(risk_calculator.router, prefix="/risk", tags=["risk"])
app.include_router(ai_screening.router, prefix="/ai", tags=["ai"])
app.include_router(ai_mentor.router, prefix="/ai/mentor", tags=["ai-mentor"])
app.include_router(chart_analysis.router, prefix="/ai/chart", tags=["chart-analysis"])
app.include_router(performance_analyzer.router, prefix="/ai/performance", tags=["performance"])
app.include_router(blog_enhanced.router, prefix="/blog-enhanced", tags=["blog-enhanced"])
app.include_router(courses_enhanced.router, prefix="/courses-enhanced", tags=["courses-enhanced"])
