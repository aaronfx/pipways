
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncpg
import os

from app.config import settings
from app.routers import auth, admin, blog, courses, webinars, ai

# Database pool
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    # Startup
    db_pool = await asyncpg.create_pool(settings.DATABASE_URL)
    app.state.db_pool = db_pool
    yield
    # Shutdown
    if db_pool:
        await db_pool.close()

app = FastAPI(
    title="Pipways Pro API",
    description="Professional Trading Platform API",
    version="3.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(blog.router)
app.include_router(courses.router)
app.include_router(webinars.router)
app.include_router(ai.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "3.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
