from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from app.models.schemas import UserCreate, UserLogin, TokenResponse
from app.config import settings
import asyncpg

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RefreshRequest(BaseModel):
    refresh_token: str

# Database connection
async def get_db():
    return await asyncpg.create_pool(settings.DATABASE_URL)

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@router.post("/register", response_model=TokenResponse)
async def register(user: UserCreate):
    pool = await get_db()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", user.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed = pwd_context.hash(user.password)
        user_id = await conn.fetchval("""
            INSERT INTO users (email, password_hash, full_name, role, subscription_tier)
            VALUES ($1, $2, $3, $4, $5) RETURNING id
        """, user.email, hashed, user.full_name, "user", "free")

        access_token = create_token(
            {"sub": str(user_id), "email": user.email, "role": "user"},
            timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_token(
            {"sub": str(user_id), "type": "refresh"},
            timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {"id": user_id, "email": user.email, "role": "user", "full_name": user.full_name}
        }

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    pool = await get_db()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", credentials.email)
        if not user or not pwd_context.verify(credentials.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = create_token(
            {"sub": str(user["id"]), "email": user["email"], "role": user["role"]},
            timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_token(
            {"sub": str(user["id"]), "type": "refresh"},
            timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "role": user["role"],
                "full_name": user["full_name"],
                "subscription_tier": user["subscription_tier"]
            }
        }

@router.post("/refresh")
async def refresh_token(request: RefreshRequest):  # Changed to accept JSON body
    try:
        payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        pool = await get_db()
        async with pool.acquire() as conn:
            user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", int(user_id))
            if not user:
                raise HTTPException(status_code=401, detail="User not found")

            new_access = create_token(
                {"sub": str(user_id), "email": user["email"], "role": user["role"]},
                timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            new_refresh = create_token(
                {"sub": str(user_id), "type": "refresh"},
                timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            )

            return {"access_token": new_access, "refresh_token": new_refresh}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
