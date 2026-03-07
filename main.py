from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from contextlib import asynccontextmanager
import os
import asyncpg

from config import settings
from database import init_db
from auth import router as auth_router
from routers import trades, analysis, mentorship, blog, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    try:
        await init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise
    yield

app = FastAPI(
    title="Pipways API",
    description="Institutional Trader Development Platform",
    version="2.1.0",
    lifespan=lifespan
)

# CORS middleware - Fix #6: More restrictive in production
# Allow all for now, but restrict to specific origin when deploying
cors_origins = ["*"]
if os.getenv("ENVIRONMENT") == "production":
    cors_origins = ["https://pipways-web-nhem.onrender.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler for debugging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Global error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__}
    )

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(trades.router, prefix="/trades", tags=["Trading Journal"])
app.include_router(analysis.router, prefix="/analyze", tags=["AI Analysis"])
app.include_router(mentorship.router, prefix="/mentorship", tags=["AI Mentor"])
app.include_router(blog.router, prefix="/blog", tags=["Blog"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

@app.get("/")
async def root():
    """Serve frontend"""
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head><title>Pipways API</title></head>
    <body>
        <h1>Pipways API is running</h1>
        <p>Frontend not found. Please place index.html in static/ folder.</p>
        <p><a href="/health">Health Check</a></p>
    </body>
    </html>
    """)

@app.get("/health")
async def health():
    """Health check endpoint - Fix #5: Show env var status"""
    return {
        "status": "ok",
        "version": "2.1.0",
        "environment": {
            "database_configured": bool(settings.DATABASE_URL),
            "secret_key_configured": bool(settings.SECRET_KEY) and settings.SECRET_KEY != "your-secret-key-change-in-production",
            "openrouter_configured": bool(settings.OPENROUTER_API_KEY)
        },
        "features": ["auth", "trades", "analysis", "mentorship", "blog", "admin"]
    }

# Debug endpoint to check database
@app.get("/debug/db")
async def debug_db():
    """Debug database connection"""
    try:
        from database import get_db
        conn = await asyncpg.connect(settings.DATABASE_URL, ssl="require")
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        await conn.close()
        return {"status": "ok", "user_count": user_count}
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
