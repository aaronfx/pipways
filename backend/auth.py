"""
Authentication Routes
Handles login, register, and token management
"""
import bcrypt
from fastapi import APIRouter, HTTPException, Depends
from datetime import timedelta
from typing import Optional

# FIXED: Import database module, not the variable
from . import database
from .database import SECRET_KEY, ALGORITHM
from .schemas import UserRegister, UserLogin, Token
from .security import create_access_token, create_refresh_token, get_current_user

router = APIRouter()

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister):
    """Register a new user"""
    # Use database.db_pool to get current value
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        async with database.db_pool.acquire() as conn:
            # Check if user exists
            existing = await conn.fetchval(
                "SELECT id FROM users WHERE email = $1", 
                user_data.email
            )
            if existing:
                raise HTTPException(status_code=400, detail="Email already registered")
            
            # Hash password
            hashed = bcrypt.hashpw(user_data.password.encode(), bcrypt.gensalt()).decode()
            
            # Create user
            user_id = await conn.fetchval("""
                INSERT INTO users (email, password_hash, full_name, role, subscription_tier, subscription_status, email_verified)
                VALUES ($1, $2, $3, 'user', 'free', 'inactive', FALSE) RETURNING id
            """, user_data.email, hashed, user_data.full_name)
            
            # Create tokens
            access_token = create_access_token({"sub": str(user_id)})
            refresh_token = create_refresh_token({"sub": str(user_id)})
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": {
                    "id": user_id,
                    "email": user_data.email,
                    "full_name": user_data.full_name,
                    "role": "user",
                    "subscription_tier": "free"
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login user"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        async with database.db_pool.acquire() as conn:
            # Get user by email
            user = await conn.fetchrow("""
                SELECT id, email, password_hash, full_name, role, subscription_tier, subscription_status 
                FROM users WHERE email = $1
            """, credentials.email)
            
            if not user:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            
            # Verify password
            if not bcrypt.checkpw(credentials.password.encode(), user["password_hash"].encode()):
                raise HTTPException(status_code=401, detail="Invalid email or password")
            
            # Update last login
            await conn.execute("UPDATE users SET last_login = NOW() WHERE id = $1", user["id"])
            
            # Create tokens
            access_token = create_access_token({"sub": str(user["id"])})
            refresh_token = create_refresh_token({"sub": str(user["id"])})
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@router.post("/refresh")
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """Refresh access token"""
    new_token = create_access_token({"sub": str(current_user["id"])})
    return {"access_token": new_token, "token_type": "bearer"}
