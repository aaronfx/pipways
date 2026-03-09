from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from contextlib import asynccontextmanager

from app.config import settings
from app.routers import auth, admin, blog, courses, webinars, ai

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = await asyncpg.create_pool(settings.DATABASE_URL)
    yield
    await app.state.db_pool.close()

app = FastAPI(
    title="Pipways Pro API",
    version="3.0.0",
    lifespan=lifespan
)

# CRITICAL FIX: Hardcode your frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pipways-web-nhem.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Pipways Pro API", "version": "3.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok", "version": "3.0.0"}

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(blog.router)
app.include_router(courses.router)
app.include_router(webinars.router)
app.include_router(ai.router)
