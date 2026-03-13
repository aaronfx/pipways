"""
Main FastAPI application entry point.
Uses RELATIVE imports to work as a Python package.
Run with: uvicorn backend.main:app (from root directory)
"""
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy import select

# RELATIVE imports (from .module)
from .database import database, metadata, users
from .security import get_password_hash, get_current_user

# Import all route modules using RELATIVE imports
from . import auth, signals, courses, blog, webinars, media, admin
from . import notifications, payments, risk_calculator, ai_screening, blog_enhanced, courses_enhanced

# Create FastAPI app
app = FastAPI(
    title="Pipways Trading Platform API",
    description="Professional trading signals and analysis platform",
    version="1.0.0",
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

# Mount static files
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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check for Render monitoring."""
    return {
        "status": "healthy",
        "service": "pipways-api",
        "version": "1.0.0",
        "timestamp": str(datetime.utcnow())
    }

# API info endpoint
@app.get("/api")
async def api_info():
    """API info and available endpoints."""
    return {
        "message": "Welcome to Pipways Trading Platform API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
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
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        return {"error": "Frontend not found", "path": str(index_file)}

@app.get("/dashboard.html")
async def serve_dashboard():
    """Serve the main dashboard app."""
    dashboard_file = FRONTEND_DIR / "dashboard.html"
    if dashboard_file.exists():
        return FileResponse(str(dashboard_file))
    else:
        return {"error": "Dashboard not found", "path": str(dashboard_file)}

@app.get("/admin.html")
async def serve_admin():
    """Serve admin page."""
    admin_file = FRONTEND_DIR / "admin.html"
    if admin_file.exists():
        return FileResponse(str(admin_file))
    else:
        # Fallback to dashboard if separate admin.html doesn't exist
        return FileResponse(str(FRONTEND_DIR / "dashboard.html"))

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
app.include_router(blog_enhanced.router, prefix="/blog-enhanced", tags=["blog-enhanced"])
app.include_router(courses_enhanced.router, prefix="/courses-enhanced", tags=["courses-enhanced"])
