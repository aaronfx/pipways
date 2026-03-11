"""
Pipways Trading Platform - Main Application
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# Create FastAPI app
app = FastAPI(
    title="Pipways API",
    version="3.5",
    lifespan=lifespan
)

# CORS - Allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(signals_router, prefix="/api/signals", tags=["signals"])
app.include_router(signals_router, prefix="/api/admin/signals", tags=["admin-signals"])
app.include_router(webinars_router, prefix="/webinars", tags=["webinars"])
app.include_router(courses_router, prefix="/courses", tags=["courses"])
app.include_router(blog_router, prefix="/blog", tags=["blog"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
app.include_router(performance_router, prefix="/api/performance", tags=["performance"])

# Determine the correct path for frontend files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

# Create uploads directory if it doesn't exist
os.makedirs(UPLOADS_DIR, exist_ok=True)
logger.info(f"Uploads directory ensured at: {UPLOADS_DIR}")

# Mount static files
if os.path.exists(FRONTEND_DIR):
    # Mount CSS and JS directories if they exist
    css_dir = os.path.join(FRONTEND_DIR, "css")
    js_dir = os.path.join(FRONTEND_DIR, "js")
    
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")
    
    logger.info(f"Frontend static files mounted from: {FRONTEND_DIR}")
else:
    logger.warning(f"Frontend directory not found at: {FRONTEND_DIR}")

# Mount uploads directory (now it exists)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

@app.get("/")
async def serve_index():
    """Serve the main index.html file"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        # If no frontend, return API info
        return {"message": "Pipways API v3.5", "status": "running", "frontend": "not found"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Catch-all route for SPA (Single Page Application) routing
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve index.html for all non-API routes (SPA behavior)"""
    # Skip API routes
    if full_path.startswith(("api/", "auth/", "blog/", "courses/", "webinars/")):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not Found")
    
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"message": "Pipways API v3.5", "status": "running"}
