"""
Pipways Trading Platform - Main Application
"""

import sys
import os
import base64
import json
from pathlib import Path
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import asyncio

# Add backend directory to Python path
backend_dir = Path(__file__).parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Core imports
from database import init_db_pool, close_db_pool, init_db, check_connection, db_pool
from security import get_admin_user, get_current_user, get_current_user_optional, create_access_token, verify_password, get_password_hash

from fastapi import FastAPI, HTTPException, Depends, Request, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
import httpx

# Import routes
try:
    from routes import auth, blog, courses, signals, webinars, media
    from routes.auth import router as auth_router
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import routes: {e}")
    # Create minimal auth router if imports fail
    from fastapi import APIRouter
    auth_router = APIRouter()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Frontend path
frontend_path = os.path.join(os.path.dirname(backend_dir), "frontend")

# OpenAI/Azure OpenAI Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("Starting Pipways Trading Platform v2.0.0")
    logger.info("=" * 60)
    
    try:
        await init_db_pool()
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    yield
    
    logger.info("Shutting down...")
    try:
        await close_db_pool()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

app = FastAPI(
    title="Pipways Trading Platform API",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Create uploads directories
for d in ["uploads", "uploads/blog", "uploads/courses", "uploads/signals", "uploads/avatars", "uploads/webinars", "uploads/analysis"]:
    os.makedirs(d, exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Mount frontend static files
if os.path.exists(frontend_path):
    css_path = os.path.join(frontend_path, "css")
    js_path = os.path.join(frontend_path, "js")
    images_path = os.path.join(frontend_path, "images")
    
    if os.path.exists(css_path):
        app.mount("/css", StaticFiles(directory=css_path), name="css")
    if os.path.exists(js_path):
        app.mount("/js", StaticFiles(directory=js_path), name="js")
    if os.path.exists(images_path):
        app.mount("/images", StaticFiles(directory=images_path), name="images")

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
try:
    app.include_router(signals.router, prefix="/api/signals", tags=["Trading Signals"])
    app.include_router(courses.router, prefix="/api/courses", tags=["Courses"])
    app.include_router(blog.router, prefix="/api/blog", tags=["Blog"])
    app.include_router(webinars.router, prefix="/api/webinars", tags=["Webinars"])
    app.include_router(media.router, prefix="/api/media", tags=["Media"])
except Exception as e:
    logger.error(f"Error including routers: {e}")

# ==========================================
# AI SERVICES ENDPOINTS
# ==========================================

async def call_openai_vision(image_base64: str, prompt: str) -> str:
    """Call OpenAI GPT-4 Vision API for image analysis"""
    if not OPENAI_API_KEY:
        return "AI analysis is currently unavailable. Please configure OPENAI_API_KEY."
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a professional forex trading analyst. Analyze trading charts and provide detailed technical analysis including support/resistance levels, trend direction, entry points, stop loss, and take profit recommendations. Be specific with price levels."
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 1000
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return f"AI analysis error: {response.status_code}. Please try again later."
                
    except Exception as e:
        logger.error(f"Error calling OpenAI: {e}")
        return f"AI service error: {str(e)}. Please ensure OPENAI_API_KEY is configured."

@app.post("/api/ai/analyze-chart", tags=["AI Services"])
async def analyze_chart(
    image: UploadFile = File(...),
    pair: str = Form("EURUSD"),
    timeframe: str = Form("H1"),
    current_user: dict = Depends(get_current_user)
):
    """Analyze trading chart using AI vision"""
    try:
        # Read image and convert to base64
        contents = await image.read()
        image_base64 = base64.b64encode(contents).decode('utf-8')
        
        # Prepare prompt
        prompt = f"""Analyze this {pair} {timeframe} chart. Provide:
1. Current trend direction (Bullish/Bearish/Neutral)
2. Key support and resistance levels with specific prices
3. Recommended entry price
4. Stop Loss price
5. Take Profit targets (2 levels)
6. Brief technical analysis (2-3 sentences)
Format as JSON with keys: trend, support, resistance, entry, stop_loss, take_profit_1, take_profit_2, analysis"""
        
        # Call AI service
        analysis = await call_openai_vision(image_base64, prompt)
        
        return {
            "success": True,
            "pair": pair,
            "timeframe": timeframe,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Chart analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/analyze-performance", tags=["AI Services"])
async def analyze_performance(
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Analyze trading statement/performance using AI vision"""
    try:
        contents = await image.read()
        image_base64 = base64.b64encode(contents).decode('utf-8')
        
        prompt = """Analyze this trading statement/performance report. Extract:
1. Total number of trades
2. Win rate percentage
3. Average win/loss in pips or dollars
4. Largest winning trade
5. Largest losing trade
6. Profit factor
7. Key insights and recommendations for improvement (2-3 sentences)
Format as clear text with these sections."""
        
        analysis = await call_openai_vision(image_base64, prompt)
        
        return {
            "success": True,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/mentor-chat", tags=["AI Services"])
async def mentor_chat(
    request: Dict[str, str],
    current_user: dict = Depends(get_current_user)
):
    """AI Trading Mentor chat endpoint"""
    try:
        message = request.get("message", "")
        context = request.get("context", "general")
        
        if not OPENAI_API_KEY:
            return {
                "response": "I'm currently running in demo mode. In production, I would provide detailed trading advice based on your question: " + message,
                "timestamp": datetime.now().isoformat()
            }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are an expert trading mentor with 20+ years of experience in forex, crypto, and stock trading. 
                            Provide specific, actionable advice on trading strategies, risk management, trading psychology, and market analysis. 
                            Be encouraging but emphasize risk management. Keep responses concise (3-4 sentences max) but informative."""
                        },
                        {
                            "role": "user",
                            "content": f"Context: {context}\n\nQuestion: {message}"
                        }
                    ],
                    "max_tokens": 300
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data['choices'][0]['message']['content']
            else:
                ai_response = "I'm having trouble connecting to my knowledge base. Please try again in a moment."
        
        return {
            "response": ai_response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Mentor chat error: {e}")
        return {
            "response": "I'm experiencing technical difficulties. Please try again later.",
            "error": str(e)
        }

# ==========================================
# FALLBACK DATA ENDPOINTS (if DB fails)
# ==========================================

@app.get("/api/signals", tags=["Trading Signals"])
async def get_signals(
    status: Optional[str] = Query(None),
    pair: Optional[str] = Query(None),
    limit: int = Query(50),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get trading signals"""
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                query = "SELECT * FROM signals WHERE 1=1"
                params = []
                
                if status:
                    query += f" AND status = ${len(params)+1}"
                    params.append(status)
                if pair:
                    query += f" AND pair ILIKE ${len(params)+1}"
                    params.append(f"%{pair}%")
                
                query += " ORDER BY created_at DESC LIMIT $"+str(len(params)+1)
                params.append(limit)
                
                rows = await conn.fetch(query, *params)
                signals = [dict(row) for row in rows]
                return {"signals": signals, "total": len(signals)}
        
        # Fallback mock data
        return {
            "signals": [
                {
                    "id": 1,
                    "pair": "EURUSD",
                    "direction": "buy",
                    "entry_price": "1.0850",
                    "stop_loss": "1.0800",
                    "take_profit_1": "1.0900",
                    "take_profit_2": "1.0950",
                    "status": "active",
                    "timeframe": "H1",
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": 2,
                    "pair": "GBPUSD",
                    "direction": "sell",
                    "entry_price": "1.2650",
                    "stop_loss": "1.2700",
                    "take_profit_1": "1.2600",
                    "take_profit_2": "1.2550",
                    "status": "active",
                    "timeframe": "H4",
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": 3,
                    "pair": "USDJPY",
                    "direction": "buy",
                    "entry_price": "149.50",
                    "stop_loss": "149.00",
                    "take_profit_1": "150.00",
                    "take_profit_2": "150.50",
                    "status": "tp1_hit",
                    "timeframe": "D1",
                    "created_at": datetime.now().isoformat()
                }
            ],
            "total": 3
        }
    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        return {"signals": [], "total": 0, "error": str(e)}

@app.get("/api/courses", tags=["Learning Management System"])
async def get_courses(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get all courses"""
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM courses ORDER BY created_at DESC")
                courses = [dict(row) for row in rows]
                return {"courses": courses}
        
        # Fallback
        return {
            "courses": [
                {
                    "id": 1,
                    "title": "Forex Trading Basics",
                    "description": "Learn the fundamentals of forex trading including currency pairs, pips, and lot sizes",
                    "level": "beginner",
                    "lessons_count": 10,
                    "image_url": "/images/course1.jpg"
                },
                {
                    "id": 2,
                    "title": "Technical Analysis Masterclass",
                    "description": "Master chart patterns, indicators, and price action strategies",
                    "level": "intermediate",
                    "lessons_count": 15,
                    "image_url": "/images/course2.jpg"
                },
                {
                    "id": 3,
                    "title": "Advanced Risk Management",
                    "description": "Professional techniques for managing risk and maximizing returns",
                    "level": "advanced",
                    "lessons_count": 8,
                    "image_url": "/images/course3.jpg"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching courses: {e}")
        return {"courses": []}

@app.get("/api/webinars", tags=["Webinars"])
async def get_webinars(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get upcoming webinars"""
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM webinars WHERE scheduled_at > NOW() ORDER BY scheduled_at ASC"
                )
                webinars = [dict(row) for row in rows]
                return {"webinars": webinars}
        
        # Fallback
        return {
            "webinars": [
                {
                    "id": 1,
                    "title": "Live Trading Session - EURUSD Analysis",
                    "description": "Join our head analyst for a live breakdown of EURUSD setups",
                    "scheduled_at": (datetime.now() + timedelta(days=2)).isoformat(),
                    "presenter": "Senior Analyst",
                    "status": "upcoming"
                },
                {
                    "id": 2,
                    "title": "Risk Management Workshop",
                    "description": "Learn how professionals manage risk in volatile markets",
                    "scheduled_at": (datetime.now() + timedelta(days=5)).isoformat(),
                    "presenter": "Risk Manager",
                    "status": "upcoming"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching webinars: {e}")
        return {"webinars": []}

@app.get("/api/blog", tags=["Blog"])
async def get_blog_posts(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(10)
):
    """Get blog posts"""
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                query = "SELECT * FROM blog_posts WHERE status = 'published'"
                params = []
                
                if category:
                    query += f" AND category = ${len(params)+1}"
                    params.append(category)
                
                query += " ORDER BY created_at DESC"
                rows = await conn.fetch(query, *params)
                posts = [dict(row) for row in rows]
                return {"posts": posts, "total": len(posts)}
        
        # Fallback
        return {
            "posts": [
                {
                    "id": 1,
                    "title": "Welcome to Pipways",
                    "excerpt": "Your journey to becoming a professional trader starts here...",
                    "content": "Welcome to Pipways! We provide professional trading signals...",
                    "category": "General",
                    "author": "Admin",
                    "created_at": datetime.now().isoformat(),
                    "views": 1250
                },
                {
                    "id": 2,
                    "title": "Understanding Support and Resistance",
                    "excerpt": "Learn the most important concepts in technical analysis...",
                    "content": "Support and resistance are key levels...",
                    "category": "Strategy",
                    "author": "Admin",
                    "created_at": datetime.now().isoformat(),
                    "views": 890
                },
                {
                    "id": 3,
                    "title": "Risk Management: The 1% Rule",
                    "excerpt": "Why professional traders never risk more than 1% per trade...",
                    "content": "The 1% rule is essential...",
                    "category": "Risk Management",
                    "author": "Admin",
                    "created_at": datetime.now().isoformat(),
                    "views": 2100
                }
            ],
            "total": 3
        }
    except Exception as e:
        logger.error(f"Error fetching blog: {e}")
        return {"posts": []}

@app.post("/api/blog", tags=["Blog"])
async def create_blog_post(
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form("General"),
    current_user: dict = Depends(get_current_user)
):
    """Create new blog post"""
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """INSERT INTO blog_posts (title, content, category, author_id, status, created_at) 
                       VALUES ($1, $2, $3, $4, 'published', NOW()) RETURNING *""",
                    title, content, category, current_user.get('id', 1)
                )
                return {"success": True, "post": dict(row)}
        
        return {"success": True, "message": "Blog post created (mock)"}
    except Exception as e:
        logger.error(f"Error creating blog post: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/dashboard", tags=["Admin"])
async def admin_dashboard(current_user: dict = Depends(get_admin_user)):
    """Get admin dashboard stats"""
    try:
        stats = {
            "users": {"total": 0, "vip": 0, "new_this_week": 0},
            "signals": {"total_30d": 0, "active": 0, "tp1_hits": 0, "avg_pips": 0},
            "courses": {"total": 3, "lessons": 33, "quizzes": 5, "enrollments": 150},
            "blog": {"total_posts": 3, "total_views": 4240},
            "webinars": {"total": 2, "registrations": 45},
            "recent_activities": []
        }
        
        if db_pool:
            async with db_pool.acquire() as conn:
                # User stats
                user_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN subscription_tier = 'vip' THEN 1 END) as vip,
                        COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as new_this_week
                    FROM users
                """)
                if user_stats:
                    stats["users"] = {
                        "total": user_stats['total'],
                        "vip": user_stats['vip'],
                        "new_this_week": user_stats['new_this_week']
                    }
                
                # Signal stats
                signal_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_30d,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                        COUNT(CASE WHEN tp1_hit = TRUE THEN 1 END) as tp1_hits
                    FROM signals 
                    WHERE created_at > NOW() - INTERVAL '30 days'
                """)
                if signal_stats:
                    stats["signals"] = {
                        "total_30d": signal_stats['total_30d'],
                        "active": signal_stats['active'],
                        "tp1_hits": signal_stats['tp1_hits'],
                        "avg_pips": 0
                    }
        
        return stats
        
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/signals", tags=["Admin"])
async def create_signal(
    pair: str = Form(...),
    direction: str = Form(...),
    entry_price: str = Form(...),
    stop_loss: str = Form(...),
    take_profit_1: str = Form(...),
    take_profit_2: Optional[str] = Form(None),
    timeframe: str = Form("H1"),
    analysis: Optional[str] = Form(""),
    current_user: dict = Depends(get_admin_user)
):
    """Create new trading signal (Admin only)"""
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """INSERT INTO signals 
                       (pair, direction, entry_price, stop_loss, take_profit_1, take_profit_2, 
                        timeframe, analysis, status, created_at, created_by) 
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'active', NOW(), $9) 
                       RETURNING *""",
                    pair, direction, entry_price, stop_loss, take_profit_1, take_profit_2,
                    timeframe, analysis, current_user.get('id')
                )
                return {"success": True, "signal": dict(row)}
        
        return {"success": True, "message": "Signal created (mock)"}
    except Exception as e:
        logger.error(f"Error creating signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# SPA Catch-all
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def spa_catch_all(full_path: str):
    if full_path.startswith(("api/", "docs", "redoc", "openapi", "css/", "js/", "images/", "uploads/")):
        raise HTTPException(status_code=404)
    
    dashboard_path = os.path.join(frontend_path, "dashboard.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return f.read()
    
    return JSONResponse(status_code=404, content={"detail": "Dashboard not found"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=False)
