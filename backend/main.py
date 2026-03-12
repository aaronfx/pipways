"""
Main FastAPI application entry point.
All imports use absolute paths (backend.module) to work with uvicorn.
"""
import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ABSOLUTE imports (not relative) - this is key for Render deployment
from backend.database import database, engine, metadata
from backend.security import get_current_user

# Import all route modules
from backend import auth, signals, courses, blog, webinars, media, admin

# Create FastAPI app
app = FastAPI(
    title="Pipways Trading Platform API",
    description="Professional trading signals and analysis platform",
    version="1.0.0"
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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check for Render monitoring."""
    return {
        "status": "healthy",
        "service": "pipways-api",
        "version": "1.0.0"
    }

# Include all routers
app.include_router(auth.router)
app.include_router(signals.router, prefix="/signals", tags=["signals"])
app.include_router(courses.router, prefix="/courses", tags=["courses"])
app.include_router(blog.router, prefix="/blog", tags=["blog"])
app.include_router(webinars.router, prefix="/webinars", tags=["webinars"])
app.include_router(media.router, prefix="/media", tags=["media"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
