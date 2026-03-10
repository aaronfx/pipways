from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncpg
import os
import logging

from app.config import settings
from app.database import Database

# Import all routers
from app.routes import auth, blog, courses, webinars, signals, journal, ai, payments, admin, media

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await Database.connect(settings.DATABASE_URL)
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    yield
    # Shutdown
    await Database.close()
    logger.info("Database disconnected")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Professional Forex Trading Academy Platform",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# =============================================================================
# CORS CONFIGURATION - Express.js Equivalent
# =============================================================================
# This is the exact FastAPI equivalent of:
# app.use(cors({
#   origin: 'https://pipways-web-nhem.onrender.com',
#   methods: ['GET', 'POST', 'PUT', 'DELETE'],
#   credentials: true
# }))

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pipways-web-nhem.onrender.com",  # Your frontend domain
        "http://localhost:8000",                   # Local development
        "http://127.0.0.1:5500",                   # Live server local
        "http://localhost:3000"                    # React/Vite default
    ],
    allow_credentials=True,  # Allow cookies/auth headers
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # HTTP methods
    allow_headers=[
        "Content-Type",
        "Authorization", 
        "Accept",
        "Origin",
        "X-Requested-With",
        "*"
    ],  # Allowed headers
    expose_headers=["*"],  # Expose headers to frontend
    max_age=3600,  # Preflight cache duration (1 hour)
)

# =============================================================================
# STATIC FILES
# =============================================================================
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# =============================================================================
# GLOBAL EXCEPTION HANDLER
# =============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc), 
            "type": "internal_error",
            "path": str(request.url)
        }
    )

# =============================================================================
# HEALTH CHECK
# =============================================================================
@app.get("/health")
async def health_check():
    try:
        # Test database connection
        await Database.fetchval("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "database": db_status,
        "cors": "enabled",
        "timestamp": str(datetime.utcnow())
    }

# =============================================================================
# ROUTES - MUST BE AFTER CORS MIDDLEWARE
# =============================================================================
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(blog.router, prefix="/blog", tags=["Blog"])
app.include_router(courses.router, prefix="/courses", tags=["Courses"])
app.include_router(webinars.router, prefix="/webinars", tags=["Webinars"])
app.include_router(signals.router, prefix="/signals", tags=["Signals"])
app.include_router(journal.router, prefix="/journal", tags=["Trade Journal"])
app.include_router(ai.router, prefix="/ai", tags=["AI Services"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(media.router, prefix="/media", tags=["Media Library"])

# =============================================================================
# ROOT ENDPOINT
# =============================================================================
@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running",
        "cors_origins": [
            "https://pipways-web-nhem.onrender.com",
            "http://localhost:8000"
        ],
        "endpoints": {
            "auth": "/auth",
            "blog": "/blog",
            "courses": "/courses",
            "webinars": "/webinars",
            "signals": "/signals",
            "journal": "/journal",
            "ai": "/ai",
            "payments": "/payments",
            "admin": "/admin",
            "media": "/media",
            "health": "/health"
        }
    }

# =============================================================================
# IMPORT DATETIME FOR HEALTH CHECK
# =============================================================================
from datetime import datetime

# =============================================================================
# MAIN ENTRY POINT (for local development)
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=port,
        reload=settings.DEBUG,
        log_level="info"
    )
