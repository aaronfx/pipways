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

# CORS Configuration - MUST be before routers
# Option 1: Allow all origins (easiest for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False with ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Option 2: Specific origins (more secure - uncomment to use)
# origins = [
#     "https://pipways-web-nhem.onrender.com",
#     "http://localhost:8000",
#     "http://127.0.0.1:5500"
# ]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

@app.get("/")
async def root():
    return {"message": "Pipways Pro API", "version": "3.0.0", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "ok", "version": "3.0.0"}

# Include routers - MUST be after CORS middleware
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(blog.router)
app.include_router(courses.router)
app.include_router(webinars.router)
app.include_router(ai.router)
