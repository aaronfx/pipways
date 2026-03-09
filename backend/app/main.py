from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from contextlib import asynccontextmanager

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
    version="3.0.0",
    lifespan=lifespan
)

# FIXED: Explicitly allow your frontend domain
origins = [
    "https://pipways-web-nhem.onrender.com",  # Your frontend
    "https://pipways-pro.onrender.com",       # Alternative domain if you have one
    "http://localhost:8000",                   # Local development
    "http://127.0.0.1:5500",                   # Local live server
]

# If CORS_ORIGINS env var is set, parse it too
if settings.CORS_ORIGINS and settings.CORS_ORIGINS != ["*"]:
    origins.extend(settings.CORS_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Pipways Pro API", "version": "3.0.0", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "ok", "version": "3.0.0"}

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(blog.router)
app.include_router(courses.router)
app.include_router(webinars.router)
app.include_router(ai.router)
