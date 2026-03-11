"""
Pipways Trading Platform - Main Application
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import lifespan
from .auth import router as auth_router
from .admin import router as admin_router
from .signals import router as signals_router
from .webinars import router as webinars_router
from .courses import router as courses_router
from .blog import router as blog_router
from .ai_services import router as ai_router
from .performance import router as performance_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pipways API",
    version="3.5",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(signals_router, prefix="/api/signals", tags=["signals"])
app.include_router(webinars_router, prefix="/api/webinars", tags=["webinars"])
app.include_router(courses_router, prefix="/api/courses", tags=["courses"])
app.include_router(blog_router, prefix="/api/blog", tags=["blog"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
app.include_router(performance_router, prefix="/api/performance", tags=["performance"])

# Frontend serving setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.exists(FRONTEND_DIR):
    css_dir = os.path.join(FRONTEND_DIR, "css")
    js_dir = os.path.join(FRONTEND_DIR, "js")
    
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")
    
    os.makedirs(os.path.join(BASE_DIR, "uploads"), exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=os.path.join(BASE_DIR, "uploads")), name="uploads")
    
    logger.info(f"Frontend mounted from: {FRONTEND_DIR}")

@app.get("/")
async def serve_index():
    """Serve the main index.html file"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Pipways API v3.5", "status": "running", "frontend": "not found"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "3.5"}

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve index.html for all non-API routes"""
    # Skip API routes
    if any(full_path.startswith(prefix) for prefix in [
        "api/", "auth/", "css/", "js/", "uploads/", "health"
    ]):
        return {"detail": "Not Found"}
    
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Pipways API v3.5", "status": "running"}
