from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from datetime import datetime
import os
import logging

from .database import database, engine, metadata
from . import auth, signals, courses, blog, webinars, media, admin, security
from . import notifications, payments, risk_calculator, ai_screening, blog_enhanced, courses_enhanced

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    await database.connect()
    metadata.create_all(engine)
    logger.info("Database connected and tables created")

    # Setup Telegram webhook
    await notifications.setup_telegram_webhook()

    yield

    logger.info("Shutting down...")
    await database.disconnect()

app = FastAPI(
    title="Pipways Trading Platform",
    description="Professional trading education and signals platform",
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", 
    "http://localhost:3000,http://localhost:8080,http://localhost:5500"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.get("/health")
@limiter.limit("10/minute")
async def health_check(request: Request):
    return {
        "status": "healthy",
        "timestamp": str(datetime.utcnow()),
        "version": "1.0.0"
    }

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(signals.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(blog.router, prefix="/api")
app.include_router(webinars.router, prefix="/api")
app.include_router(media.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(risk_calculator.router, prefix="/api")
app.include_router(ai_screening.router, prefix="/api")
app.include_router(blog_enhanced.router, prefix="/api")
app.include_router(courses_enhanced.router, prefix="/api")

# WebSocket endpoint
@app.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return

    try:
        payload = security.decode_token(token)
        user_id = int(payload.get("sub"))

        await notifications.manager.connect(websocket, user_id)
        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            notifications.manager.disconnect(websocket, user_id)
    except Exception:
        await websocket.close(code=4002)

# Static files
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    return {
        "message": "Welcome to Pipways Trading Platform API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
