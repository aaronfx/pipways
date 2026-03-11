"""
Pipways Platform - Main Application
Entry point with router aggregation
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import os
import logging

# Import lifespan from database
from .database import lifespan, UPLOAD_DIR

# Import all routers using relative imports
from . import auth
from . import signals
from . import webinars
from . import courses
from . import blog
from . import media
from . import ai_services
from . import performance
from . import admin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app with lifespan
app = FastAPI(
    title="Pipways Platform API",
    description="Trading education and signals platform",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include all routers
app.include_router(auth.router)
app.include_router(signals.router)
app.include_router(webinars.router)
app.include_router(courses.router)
app.include_router(blog.router)
app.include_router(media.router)
app.include_router(ai_services.router)
app.include_router(performance.router)
app.include_router(admin.router)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}

# Serve frontend - Define paths using BASE_DIR for safety
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve main HTML file"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Pipways API</h1><p>Frontend not found</p>")

# Serve static frontend assets with API route protection
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str, request: Request):
    """Serve static files from frontend directory"""
    # Protect API routes from being caught by catch-all
    if full_path.startswith("api/") or full_path.startswith("auth/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    file_path = os.path.join(FRONTEND_DIR, full_path)

    # Security check - ensure we don't serve files outside frontend_dir
    real_file_path = os.path.realpath(file_path)
    real_frontend_dir = os.path.realpath(FRONTEND_DIR)
    if not real_file_path.startswith(real_frontend_dir):
        raise HTTPException(status_code=404, detail="Not found")

    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)

    # Return index.html for SPA routing (client-side routing)
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return HTMLResponse(content=f.read())

    raise HTTPException(status_code=404, detail="Not found")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
