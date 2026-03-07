from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from contextlib import asynccontextmanager
import os

from config import settings
from database import init_db
from auth import router as auth_router
from routers import trades, analysis, mentorship, blog, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    await init_db()
    yield

app = FastAPI(
    title="Pipways API",
    description="Institutional Trader Development Platform",
    version="2.1.0",
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
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "2.1.0",
        "database": "connected" if settings.DATABASE_URL else "not configured",
        "openrouter": "configured" if settings.OPENROUTER_API_KEY else "not configured",
        "features": ["auth", "trades", "analysis", "mentorship", "blog", "admin"]
    }

@app.get("/sitemap.xml")
async def sitemap():
    """Generate XML sitemap"""
    base_url = "https://pipways.com"
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{base_url}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>
  <url><loc>{base_url}/blog</loc><changefreq>daily</changefreq><priority>0.8</priority></url>
</urlset>"""
    return HTMLResponse(content=xml, media_type="application/xml")

@app.get("/robots.txt")
async def robots():
    """Serve robots.txt"""
    content = """User-agent: *
Allow: /
Allow: /blog/
Disallow: /admin/
Disallow: /api/

Sitemap: https://pipways.com/sitemap.xml
"""
    return HTMLResponse(content=content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
