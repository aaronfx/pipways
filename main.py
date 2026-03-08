
"""
Pipways Trading API - Complete Production-Ready Backend
Features: Trading Signals, AI Chart Analysis, AI Mentor, Admin Panel, Content Management
"""

import os
import json
import logging
import base64
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

# FastAPI and related
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Database
import asyncpg
from asyncpg import Pool

# HTTP Client
import httpx

# Password hashing
from passlib.context import CryptContext

# JWT
from jose import JWTError, jwt

# Pydantic models
from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================

class Settings:
    def __init__(self):
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "")
        self.REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

        # OpenRouter AI Configuration
        self.OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
        self.OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-opus-20240229")
        self.OPENROUTER_VISION_MODEL: str = os.getenv("OPENROUTER_VISION_MODEL", "anthropic/claude-3-opus-20240229")
        self.OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

        # JWT Configuration
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.ALGORITHM: str = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

        # Telegram Configuration
        self.TELEGRAM_FREE_CHANNEL_LINK: str = os.getenv("TELEGRAM_FREE_CHANNEL_LINK", "https://t.me/pipways_free")
        self.TELEGRAM_PREMIUM_CHANNEL_LINK: str = os.getenv("TELEGRAM_PREMIUM_CHANNEL_LINK", "https://t.me/pipways_vip")
        self.TELEGRAM_BOT_USERNAME: str = os.getenv("TELEGRAM_BOT_USERNAME", "pipways_bot")

        # App Configuration
        self.SUBSCRIPTION_ENABLED: bool = os.getenv("SUBSCRIPTION_ENABLED", "false").lower() == "true"
        self.FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://pipways-web-nhem.onrender.com")

        # CORS Origins - parse from env
        cors_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
        self.CORS_ORIGINS: List[str] = [origin.strip() for origin in cors_env.split(",")]

        # Admin Configuration
        self.ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@pipways.com")
        self.ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")

settings = Settings()

# ==================== PASSWORD & SECURITY ====================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return {"user_id": user_id, "email": payload.get("email"), "role": payload.get("role", "user")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = await get_current_user(credentials)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ==================== DATABASE ====================

db_pool: Optional[Pool] = None

async def init_db():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        logger.info("Database pool created")

        async with db_pool.acquire() as conn:
            # Check if users table exists
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                );
            """)

            if table_exists:
                logger.info("Users table exists, checking for missing columns...")
                # Add columns one by one with individual checks
                columns = [
                    ("full_name", "VARCHAR(255)"),
                    ("subscription_tier", "VARCHAR(50) DEFAULT 'free'"),
                    ("subscription_status", "VARCHAR(50) DEFAULT 'inactive'"),
                    ("telegram_username", "VARCHAR(100)"),
                    ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                    ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                ]

                for col_name, col_type in columns:
                    exists = await conn.fetchval(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'users' AND column_name = '{col_name}'
                        );
                    """)
                    if not exists:
                        await conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};")
                        logger.info(f"Added column: {col_name}")
                    else:
                        logger.info(f"Column already exists: {col_name}")
            else:
                logger.info("Creating users table...")
                await conn.execute("""
                    CREATE TABLE users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        full_name VARCHAR(255),
                        role VARCHAR(50) DEFAULT 'user',
                        subscription_tier VARCHAR(50) DEFAULT 'free',
                        subscription_status VARCHAR(50) DEFAULT 'inactive',
                        telegram_username VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

            # Create other tables if they don't exist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id SERIAL PRIMARY KEY,
                    pair VARCHAR(50) NOT NULL,
                    type VARCHAR(20) NOT NULL,
                    entry_price DECIMAL(15,8),
                    stop_loss DECIMAL(15,8),
                    take_profit DECIMAL(15,8),
                    description TEXT,
                    status VARCHAR(20) DEFAULT 'active',
                    created_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chart_analyses (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    image_url TEXT,
                    analysis_text TEXT,
                    pair VARCHAR(50),
                    timeframe VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS mentor_chats (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS blog_posts (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    excerpt TEXT,
                    author_id INTEGER REFERENCES users(id),
                    status VARCHAR(20) DEFAULT 'draft',
                    featured_image TEXT,
                    tags TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    published_at TIMESTAMP
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS webinars (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    presenter VARCHAR(255),
                    scheduled_at TIMESTAMP,
                    duration_minutes INTEGER,
                    meeting_link TEXT,
                    recording_url TEXT,
                    status VARCHAR(20) DEFAULT 'upcoming',
                    created_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    thumbnail_url TEXT,
                    price DECIMAL(10,2) DEFAULT 0,
                    is_premium BOOLEAN DEFAULT false,
                    content JSONB DEFAULT '[]',
                    status VARCHAR(20) DEFAULT 'draft',
                    created_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Create admin user if not exists
            admin_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM users WHERE email = $1)",
                settings.ADMIN_EMAIL
            )
            if not admin_exists:
                await conn.execute("""
                    INSERT INTO users (email, password_hash, full_name, role, subscription_tier, subscription_status)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                    settings.ADMIN_EMAIL,
                    get_password_hash(settings.ADMIN_PASSWORD),
                    "Administrator",
                    "admin",
                    "premium",
                    "active"
                )
                logger.info("Admin user created")

            logger.info("Database initialization completed")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

async def close_db():
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")

# ==================== AI SERVICE ====================

class AIService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)
        self.headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.FRONTEND_URL,
            "X-Title": "Pipways Trading API"
        }

    async def analyze_chart(self, image_base64: str, pair: str = "", timeframe: str = "", additional_info: str = "") -> Dict[str, Any]:
        if not settings.OPENROUTER_API_KEY:
            raise HTTPException(status_code=503, detail="AI service not configured")

        prompt = f"""You are an expert forex/crypto trading analyst with 20+ years of experience. Analyze this trading chart with extreme precision and professional insight.

**Chart Information:**
- Trading Pair: {pair or "Not specified"}
- Timeframe: {timeframe or "Not specified"}
- Additional Context: {additional_info or "None provided"}

**Your Analysis Must Include:**

1. **Pattern Recognition** (be specific):
   - Identify exact patterns: Head & Shoulders, Double Top/Bottom, Triangles (Ascending/Descending/Symmetrical), Flags, Pennants, Wedges, Channels, Harmonic patterns
   - Pattern completion percentage and reliability score

2. **Support & Resistance Levels**:
   - Key horizontal S/R levels with price points
   - Dynamic S/R (trendlines, moving averages)
   - Psychological levels (round numbers)

3. **Trend Analysis** (Multi-timeframe):
   - Primary trend direction and strength (1-10 scale)
   - Intermediate trend alignment
   - Potential trend exhaustion signals

4. **Entry/Exit Points**:
   - Optimal entry zone with exact price range
   - Stop loss placement with rationale (ATR-based or structure-based)
   - Multiple take profit targets (TP1 conservative, TP2 moderate, TP3 aggressive)
   - Risk:Reward ratio for each setup

5. **Risk Assessment**:
   - Position sizing recommendation (% of account)
   - Key risk events to monitor
   - Invalidation criteria (when to exit early)

6. **Market Context**:
   - Volume analysis if visible
   - Momentum indicator interpretation
   - Correlation considerations

**Output Format (STRICT JSON):**
{{
    "summary": "Brief 2-sentence overview",
    "pattern": "Pattern name and confidence %",
    "trend": "Bullish/Bearish/Neutral - Strength X/10",
    "support_resistance": {{
        "support": ["price1", "price2"],
        "resistance": ["price1", "price2"]
    }},
    "entry_zone": "price range",
    "stop_loss": "price",
    "take_profit": ["tp1", "tp2", "tp3"],
    "risk_reward": "1:X",
    "position_size": "X%",
    "confidence": "High/Medium/Low - X%",
    "invalidation": "Price level that invalidates this setup",
    "timeframe_validity": "How long this setup remains valid"
}}

Provide ONLY the JSON response, no markdown formatting, no additional commentary."""

        try:
            response = await self.client.post(
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                headers=self.headers,
                json={
                    "model": settings.OPENROUTER_VISION_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                                }
                            ]
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.2
                }
            )
            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"]
            # Try to parse JSON from the response
            try:
                # Remove markdown code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                analysis_json = json.loads(content.strip())
            except:
                analysis_json = {"raw_analysis": content}

            return {
                "analysis": analysis_json,
                "pair": pair,
                "timeframe": timeframe,
                "timestamp": datetime.utcnow().isoformat()
            }

        except httpx.HTTPError as e:
            logger.error(f"OpenRouter API error: {e}")
            raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")
        except Exception as e:
            logger.error(f"Chart analysis error: {e}")
            raise HTTPException(status_code=500, detail="Analysis failed")

    async def mentor_chat(self, message: str, chat_history: List[Dict] = None, user_context: Dict = None) -> str:
        if not settings.OPENROUTER_API_KEY:
            raise HTTPException(status_code=503, detail="AI service not configured")

        system_prompt = """You are an elite trading mentor with expertise in:
- Technical Analysis (Price Action, Indicators, Chart Patterns)
- Fundamental Analysis (Macro economics, News impact)
- Risk Management (Position sizing, Portfolio management)
- Trading Psychology (Emotion control, Discipline, Mindset)
- Strategy Development (Backtesting, Optimization)

**Guidelines:**
1. Provide actionable, specific advice - not generic platitudes
2. Always emphasize risk management first
3. Use real trading terminology and concepts
4. Ask clarifying questions when needed
5. Share relevant examples from market history
6. Encourage disciplined, process-oriented trading
7. Never guarantee profits or provide "signals"
8. Keep responses concise but comprehensive (2-4 paragraphs max)
9. If the user asks about a specific trade, ask for their analysis first to guide their thinking
10. Remind them that all trading decisions are their responsibility

**Tone:** Professional, encouraging, realistic, mentor-like."""

        messages = [{"role": "system", "content": system_prompt}]

        if chat_history:
            for chat in chat_history[-5:]:  # Last 5 messages for context
                messages.append({"role": "user", "content": chat.get("message", "")})
                messages.append({"role": "assistant", "content": chat.get("response", "")})

        messages.append({"role": "user", "content": message})

        try:
            response = await self.client.post(
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                headers=self.headers,
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": messages,
                    "max_tokens": 1500,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]

        except httpx.HTTPError as e:
            logger.error(f"OpenRouter API error: {e}")
            raise HTTPException(status_code=502, detail="AI service unavailable")
        except Exception as e:
            logger.error(f"Mentor chat error: {e}")
            raise HTTPException(status_code=500, detail="Chat failed")

ai_service = AIService()

# ==================== PYDANTIC MODELS ====================

class UserRegister(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"email": "user@example.com", "password": "password123", "full_name": "John Doe"}})

    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class SignalCreate(BaseModel):
    pair: str
    type: str = Field(..., pattern="^(buy|sell|neutral)$")
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    description: Optional[str] = None
    expires_at: Optional[datetime] = None

class SignalUpdate(BaseModel):
    pair: Optional[str] = None
    type: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    description: Optional[str] = None
    status: Optional[str] = None

class BlogPostCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    status: str = "draft"
    featured_image: Optional[str] = None
    tags: Optional[List[str]] = None

class WebinarCreate(BaseModel):
    title: str
    description: Optional[str] = None
    presenter: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: Optional[int] = 60
    meeting_link: Optional[str] = None

class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    price: float = 0
    is_premium: bool = False
    content: Optional[List[Dict]] = None
    status: str = "draft"

class ChartAnalysisRequest(BaseModel):
    pair: Optional[str] = None
    timeframe: Optional[str] = None
    additional_info: Optional[str] = None

class MentorChatRequest(BaseModel):
    message: str

# ==================== FASTAPI APP ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()

app = FastAPI(
    title="Pipways Trading API",
    description="Professional trading signals and AI-powered analysis platform",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== AUTH ROUTES ====================

@app.post("/auth/register", response_model=Token)
async def register(user_data: UserRegister):
    async with db_pool.acquire() as conn:
        existing = await conn.fetchval("SELECT id FROM users WHERE email = $1", user_data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        user_id = await conn.fetchval("""
            INSERT INTO users (email, password_hash, full_name, subscription_tier, subscription_status)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, 
            user_data.email,
            get_password_hash(user_data.password),
            user_data.full_name,
            "free",
            "active" if not settings.SUBSCRIPTION_ENABLED else "inactive"
        )

        access_token = create_access_token(data={
            "sub": str(user_id),
            "email": user_data.email,
            "role": "user"
        })

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "role": "user",
                "subscription_tier": "free"
            }
        }

@app.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("""
            SELECT id, email, password_hash, full_name, role, subscription_tier, subscription_status
            FROM users WHERE email = $1
        """, credentials.email)

        if not user or not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = create_access_token(data={
            "sub": str(user["id"]),
            "email": user["email"],
            "role": user["role"]
        })

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "subscription_tier": user["subscription_tier"],
                "subscription_status": user["subscription_status"]
            }
        }

@app.get("/auth/me")
async def get_me(current_user: Dict = Depends(get_current_user)):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("""
            SELECT id, email, full_name, role, subscription_tier, subscription_status, telegram_username, created_at
            FROM users WHERE id = $1
        """, int(current_user["user_id"]))

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return dict(user)

# ==================== TRADING SIGNALS ROUTES ====================

@app.get("/signals")
async def get_signals(
    status: Optional[str] = Query(None),
    pair: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    async with db_pool.acquire() as conn:
        query = "SELECT * FROM trading_signals WHERE 1=1"
        params = []

        if status:
            query += f" AND status = ${len(params)+1}"
            params.append(status)
        if pair:
            query += f" AND pair ILIKE ${len(params)+1}"
            params.append(f"%{pair}%")

        query += f" ORDER BY created_at DESC LIMIT ${len(params)+1}"
        params.append(limit)

        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]

@app.get("/signals/{signal_id}")
async def get_signal(signal_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM trading_signals WHERE id = $1", signal_id)
        if not row:
            raise HTTPException(status_code=404, detail="Signal not found")
        return dict(row)

@app.get("/signals/stats")
async def get_signal_stats():
    async with db_pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'active') as active,
                COUNT(*) FILTER (WHERE status = 'closed') as closed,
                COUNT(*) FILTER (WHERE type = 'buy') as buy_signals,
                COUNT(*) FILTER (WHERE type = 'sell') as sell_signals
            FROM trading_signals
        """)
        return dict(stats)

# ==================== ADMIN SIGNALS ROUTES ====================

@app.post("/admin/signals")
async def create_signal(signal: SignalCreate, admin: Dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        signal_id = await conn.fetchval("""
            INSERT INTO trading_signals 
            (pair, type, entry_price, stop_loss, take_profit, description, created_by, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """,
            signal.pair.upper(),
            signal.type.lower(),
            signal.entry_price,
            signal.stop_loss,
            signal.take_profit,
            signal.description,
            int(admin["user_id"]),
            signal.expires_at
        )

        row = await conn.fetchrow("SELECT * FROM trading_signals WHERE id = $1", signal_id)
        return dict(row)

@app.put("/admin/signals/{signal_id}")
async def update_signal(signal_id: int, signal: SignalUpdate, admin: Dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM trading_signals WHERE id = $1", signal_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Signal not found")

        update_fields = []
        values = []

        if signal.pair is not None:
            update_fields.append(f"pair = ${len(values)+1}")
            values.append(signal.pair.upper())
        if signal.type is not None:
            update_fields.append(f"type = ${len(values)+1}")
            values.append(signal.type.lower())
        if signal.entry_price is not None:
            update_fields.append(f"entry_price = ${len(values)+1}")
            values.append(signal.entry_price)
        if signal.stop_loss is not None:
            update_fields.append(f"stop_loss = ${len(values)+1}")
            values.append(signal.stop_loss)
        if signal.take_profit is not None:
            update_fields.append(f"take_profit = ${len(values)+1}")
            values.append(signal.take_profit)
        if signal.description is not None:
            update_fields.append(f"description = ${len(values)+1}")
            values.append(signal.description)
        if signal.status is not None:
            update_fields.append(f"status = ${len(values)+1}")
            values.append(signal.status)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        update_fields.append(f"updated_at = ${len(values)+1}")
        values.append(datetime.utcnow())
        values.append(signal_id)

        await conn.execute(
            f"UPDATE trading_signals SET {', '.join(update_fields)} WHERE id = ${len(values)}",
            *values
        )

        row = await conn.fetchrow("SELECT * FROM trading_signals WHERE id = $1", signal_id)
        return dict(row)

@app.delete("/admin/signals/{signal_id}")
async def delete_signal(signal_id: int, admin: Dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM trading_signals WHERE id = $1", signal_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Signal not found")
        return {"message": "Signal deleted successfully"}

# ==================== AI ANALYSIS ROUTES ====================

@app.post("/analyze/chart")
async def analyze_chart(
    file: UploadFile = File(...),
    pair: Optional[str] = Form(None),
    timeframe: Optional[str] = Form(None),
    additional_info: Optional[str] = Form(None),
    current_user: Dict = Depends(get_current_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="Image too large (max 10MB)")

    image_base64 = base64.b64encode(contents).decode()

    analysis = await ai_service.analyze_chart(image_base64, pair, timeframe, additional_info)

    # Save to history
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO chart_analyses (user_id, image_url, analysis_text, pair, timeframe)
            VALUES ($1, $2, $3, $4, $5)
        """,
            int(current_user["user_id"]),
            f"data:{file.content_type};base64,{image_base64[:100]}...",  # Store truncated reference
            json.dumps(analysis["analysis"]),
            pair,
            timeframe
        )

    return analysis

@app.get("/analyze/history")
async def get_analysis_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict = Depends(get_current_user)
):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, pair, timeframe, analysis_text, created_at
            FROM chart_analyses
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, int(current_user["user_id"]), limit)

        history = []
        for row in rows:
            item = dict(row)
            try:
                item["analysis"] = json.loads(item["analysis_text"])
            except:
                item["analysis"] = item["analysis_text"]
            del item["analysis_text"]
            history.append(item)

        return history

# ==================== AI MENTOR ROUTES ====================

@app.post("/mentor/chat")
async def mentor_chat(
    request: MentorChatRequest,
    current_user: Dict = Depends(get_current_user)
):
    # Get chat history for context
    async with db_pool.acquire() as conn:
        history = await conn.fetch("""
            SELECT message, response
            FROM mentor_chats
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 5
        """, int(current_user["user_id"]))

        chat_history = [dict(row) for row in history]

        # Get AI response
        response_text = await ai_service.mentor_chat(request.message, chat_history)

        # Save chat
        await conn.execute("""
            INSERT INTO mentor_chats (user_id, message, response)
            VALUES ($1, $2, $3)
        """, int(current_user["user_id"]), request.message, response_text)

        return {
            "response": response_text,
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/mentor/history")
async def get_mentor_history(
    limit: int = Query(50, ge=1, le=100),
    current_user: Dict = Depends(get_current_user)
):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, message, response, created_at
            FROM mentor_chats
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, int(current_user["user_id"]), limit)

        return [dict(row) for row in rows]

# ==================== ADMIN CONTENT ROUTES ====================

@app.post("/admin/blog")
async def create_blog_post(post: BlogPostCreate, admin: Dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        post_id = await conn.fetchval("""
            INSERT INTO blog_posts (title, content, excerpt, author_id, status, featured_image, tags, published_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """,
            post.title,
            post.content,
            post.excerpt or post.content[:200] + "...",
            int(admin["user_id"]),
            post.status,
            post.featured_image,
            post.tags or [],
            datetime.utcnow() if post.status == "published" else None
        )

        row = await conn.fetchrow("SELECT * FROM blog_posts WHERE id = $1", post_id)
        return dict(row)

@app.put("/admin/blog/{post_id}")
async def update_blog_post(post_id: int, post: BlogPostCreate, admin: Dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM blog_posts WHERE id = $1", post_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Post not found")

        await conn.execute("""
            UPDATE blog_posts 
            SET title = $1, content = $2, excerpt = $3, status = $4, 
                featured_image = $5, tags = $6, updated_at = $7,
                published_at = CASE WHEN $4 = 'published' AND published_at IS NULL THEN $8 ELSE published_at END
            WHERE id = $9
        """,
            post.title,
            post.content,
            post.excerpt or post.content[:200] + "...",
            post.status,
            post.featured_image,
            post.tags or [],
            datetime.utcnow(),
            datetime.utcnow(),
            post_id
        )

        row = await conn.fetchrow("SELECT * FROM blog_posts WHERE id = $1", post_id)
        return dict(row)

@app.delete("/admin/blog/{post_id}")
async def delete_blog_post(post_id: int, admin: Dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM blog_posts WHERE id = $1", post_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Post not found")
        return {"message": "Post deleted successfully"}

@app.post("/admin/webinars")
async def create_webinar(webinar: WebinarCreate, admin: Dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        webinar_id = await conn.fetchval("""
            INSERT INTO webinars (title, description, presenter, scheduled_at, duration_minutes, meeting_link, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """,
            webinar.title,
            webinar.description,
            webinar.presenter,
            webinar.scheduled_at,
            webinar.duration_minutes,
            webinar.meeting_link,
            int(admin["user_id"])
        )

        row = await conn.fetchrow("SELECT * FROM webinars WHERE id = $1", webinar_id)
        return dict(row)

@app.put("/admin/webinars/{webinar_id}")
async def update_webinar(webinar_id: int, webinar: WebinarCreate, admin: Dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM webinars WHERE id = $1", webinar_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Webinar not found")

        await conn.execute("""
            UPDATE webinars 
            SET title = $1, description = $2, presenter = $3, scheduled_at = $4,
                duration_minutes = $5, meeting_link = $6
            WHERE id = $7
        """,
            webinar.title,
            webinar.description,
            webinar.presenter,
            webinar.scheduled_at,
            webinar.duration_minutes,
            webinar.meeting_link,
            webinar_id
        )

        row = await conn.fetchrow("SELECT * FROM webinars WHERE id = $1", webinar_id)
        return dict(row)

@app.delete("/admin/webinars/{webinar_id}")
async def delete_webinar(webinar_id: int, admin: Dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM webinars WHERE id = $1", webinar_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Webinar not found")
        return {"message": "Webinar deleted successfully"}

@app.post("/admin/courses")
async def create_course(course: CourseCreate, admin: Dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        course_id = await conn.fetchval("""
            INSERT INTO courses (title, description, thumbnail_url, price, is_premium, content, status, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """,
            course.title,
            course.description,
            course.thumbnail_url,
            course.price,
            course.is_premium,
            json.dumps(course.content or []),
            course.status,
            int(admin["user_id"])
        )

        row = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
        return dict(row)

@app.put("/admin/courses/{course_id}")
async def update_course(course_id: int, course: CourseCreate, admin: Dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Course not found")

        await conn.execute("""
            UPDATE courses 
            SET title = $1, description = $2, thumbnail_url = $3, price = $4,
                is_premium = $5, content = $6, status = $7, updated_at = $8
            WHERE id = $9
        """,
            course.title,
            course.description,
            course.thumbnail_url,
            course.price,
            course.is_premium,
            json.dumps(course.content or []),
            course.status,
            datetime.utcnow(),
            course_id
        )

        row = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
        return dict(row)

@app.delete("/admin/courses/{course_id}")
async def delete_course(course_id: int, admin: Dict = Depends(get_admin_user)):
    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM courses WHERE id = $1", course_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Course not found")
        return {"message": "Course deleted successfully"}

# ==================== PUBLIC CONTENT ROUTES ====================

@app.get("/blog/posts")
async def get_blog_posts(
    status: str = Query("published"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT bp.*, u.full_name as author_name
            FROM blog_posts bp
            LEFT JOIN users u ON bp.author_id = u.id
            WHERE bp.status = $1
            ORDER BY bp.created_at DESC
            LIMIT $2 OFFSET $3
        """, status, limit, offset)

        return [dict(row) for row in rows]

@app.get("/blog/posts/{post_id}")
async def get_blog_post(post_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT bp.*, u.full_name as author_name
            FROM blog_posts bp
            LEFT JOIN users u ON bp.author_id = u.id
            WHERE bp.id = $1
        """, post_id)

        if not row:
            raise HTTPException(status_code=404, detail="Post not found")

        return dict(row)

@app.get("/webinars")
async def get_webinars(
    status: Optional[str] = Query(None),
    upcoming: bool = Query(False)
):
    async with db_pool.acquire() as conn:
        query = "SELECT * FROM webinars WHERE 1=1"
        params = []

        if status:
            query += f" AND status = ${len(params)+1}"
            params.append(status)

        if upcoming:
            query += f" AND scheduled_at > ${len(params)+1}"
            params.append(datetime.utcnow())

        query += " ORDER BY scheduled_at ASC"

        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]

@app.get("/courses")
async def get_courses(
    status: str = Query("published"),
    is_premium: Optional[bool] = Query(None)
):
    async with db_pool.acquire() as conn:
        query = "SELECT * FROM courses WHERE status = $1"
        params = [status]

        if is_premium is not None:
            query += f" AND is_premium = ${len(params)+1}"
            params.append(is_premium)

        query += " ORDER BY created_at DESC"

        rows = await conn.fetch(query, *params)

        courses = []
        for row in rows:
            course = dict(row)
            if course.get("content"):
                try:
                    course["content"] = json.loads(course["content"])
                except:
                    pass
            courses.append(course)

        return courses

@app.get("/courses/{course_id}")
async def get_course(course_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM courses WHERE id = $1 AND status = 'published'", course_id)

        if not row:
            raise HTTPException(status_code=404, detail="Course not found")

        course = dict(row)
        if course.get("content"):
            try:
                course["content"] = json.loads(course["content"])
            except:
                pass

        return course

# ==================== CONFIG ROUTES ====================

@app.get("/config")
async def get_config():
    return {
        "telegram_free_channel": settings.TELEGRAM_FREE_CHANNEL_LINK,
        "telegram_premium_channel": settings.TELEGRAM_PREMIUM_CHANNEL_LINK,
        "telegram_bot_username": settings.TELEGRAM_BOT_USERNAME,
        "subscription_enabled": settings.SUBSCRIPTION_ENABLED,
        "frontend_url": settings.FRONTEND_URL
    }

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }

@app.get("/")
async def root():
    return {
        "message": "Pipways Trading API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# ==================== ERROR HANDLERS ====================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
