from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncpg
import os

from app.config import settings
from app.routers import auth, admin, blog, courses, webinars, ai

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create connection pool
    app.state.db_pool = await asyncpg.create_pool(settings.DATABASE_URL)
    yield
    # Shutdown: Close pool
    await app.state.db_pool.close()

app = FastAPI(
    title="Pipways Pro API",
    description="Professional Trading Platform API",
    version="3.0.0",
    lifespan=lifespan
)

# CRITICAL FIX: CORS MUST be added BEFORE including routers
# Hardcoded to allow your frontend - bypasses any environment variable issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pipways-web-nhem.onrender.com",  # Your frontend
        "http://localhost:8000",                    # Local development
        "http://127.0.0.1:5500",                    # Local live server
        "*"                                          # Fallback - allow all
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers AFTER CORS middleware
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(blog.router)
app.include_router(courses.router)
app.include_router(webinars.router)
app.include_router(ai.router)

@app.get("/")
async def root():
    return {
        "message": "Pipways Pro API", 
        "version": "3.0.0", 
        "status": "running",
        "cors": "enabled"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "3.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
