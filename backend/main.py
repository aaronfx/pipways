"""
Main FastAPI application entry point.
Uses RELATIVE imports to work as a Python package.
Run with: uvicorn backend.main:app (from root directory)
"""
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# RELATIVE imports (from .module)
from .database import database, metadata
from .security import get_current_user

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
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """Connect to database on startup."""
    await database.connect()
    print("✓ Database connected", flush=True)

@app.on_event("shutdown")
async def shutdown():
    """Disconnect from database on shutdown."""
    await database.disconnect()
    print("✓ Database disconnected", flush=True)

# ROOT ENDPOINT - Fixes "Not Found" error
@app.get("/")
async def root():
    """Root endpoint - API info and health status."""
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

# Include all routers
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
