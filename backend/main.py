"""
Pipways Trading Platform - Main Application
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .database import lifespan
from .auth import router as auth_router
from .admin import router as admin_router
from .signals import router as signals_router
from .webinars import router as webinars_router
from .courses import router as courses_router
from .blog import router as blog_router
from .ai_services import router as ai_router
from .performance import router as performance_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app with lifespan
app = FastAPI(
    title="Pipways API",
    version="3.5",
    lifespan=lifespan
)

# CORS - Allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(signals_router, prefix="/api/signals", tags=["signals"])
app.include_router(signals_router, prefix="/api/admin/signals", tags=["admin-signals"])  # Admin signals
app.include_router(webinars_router, prefix="/webinars", tags=["webinars"])
app.include_router(courses_router, prefix="/courses", tags=["courses"])
app.include_router(blog_router, prefix="/blog", tags=["blog"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
app.include_router(performance_router, prefix="/api/performance", tags=["performance"])

# Static files for uploads
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    return {"message": "Pipways API v3.5", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
