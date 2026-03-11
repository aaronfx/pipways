"""
Authentication Routes
"""
import os
import bcrypt
import jwt
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from .database import db_pool, SECRET_KEY, ALGORITHM
from .schemas import UserRegister, UserLogin

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, full_name, role, subscription_tier, subscription_status FROM users WHERE id = $1",
                int(user_id)
            )
            if user is None:
                raise HTTPException(status_code=401, detail="User not found")
            return dict(user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

@router.post("/register")
async def register(user_data: UserRegister):
    """Register a new user"""
    logger.info(f"Registration attempt for: {user_data.email}")
    
    if not db_pool:
        logger.error("Database pool not initialized")
        raise HTTPException(status_code=500, detail="Database not connected")
    
    try:
        async with db_pool.acquire() as conn:
            # Check if user exists
            existing = await conn.fetchval("SELECT id FROM users WHERE email = $1", user_data.email)
            if existing:
                logger.warning(f"Email already exists: {user_data.email}")
                raise HTTPException(status_code=400, detail="Email already registered")
            
            # Hash password
            hashed = bcrypt.hashpw(user_data.password.encode(), bcrypt.gensalt()).decode()
            logger.info(f"Password hashed successfully")
            
            # Create user
            user_id = await conn.fetchval(
                """INSERT INTO users (email, password_hash, full_name, role, subscription_tier, subscription_status, email_verified)
                   VALUES ($1, $2, $3, 'user', 'free', 'inactive', FALSE) RETURNING id""",
                user_data.email, hashed, user_data.full_name
            )
            
            logger.info(f"User created with ID: {user_id}")
            
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
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login")
async def login(credentials: UserLogin):
    """Login user"""
    logger.info(f"Login attempt for: {credentials.email}")
    
    if not db_pool:
        logger.error("Database pool not initialized")
        raise HTTPException(status_code=500, detail="Database not connected")
    
    try:
        async with db_pool.acquire() as conn:
            # Get user by email
            user = await conn.fetchrow(
                "SELECT id, email, password_hash, full_name, role, subscription_tier, subscription_status FROM users WHERE email = $1",
                credentials.email
            )
            
            if not user:
                logger.warning(f"User not found: {credentials.email}")
                raise HTTPException(status_code=401, detail="Invalid email or password")
            
            logger.info(f"User found: {user['email']}, checking password...")
            
            # Verify password
            try:
                password_valid = bcrypt.checkpw(
                    credentials.password.encode(), 
                    user["password_hash"].encode()
                )
            except Exception as e:
                logger.error(f"Password verification error: {e}")
                raise HTTPException(status_code=500, detail="Password verification failed")
            
            if not password_valid:
                logger.warning(f"Invalid password for: {credentials.email}")
                raise HTTPException(status_code=401, detail="Invalid email or password")
            
            logger.info(f"Password valid, updating last login...")
            
            # Update last login
            await conn.execute("UPDATE users SET last_login = NOW() WHERE id = $1", user["id"])
            
            # Create tokens
            access_token = create_access_token({"sub": str(user["id"])})
            refresh_token = create_refresh_token({"sub": str(user["id"])})
            
            logger.info(f"Login successful for: {user['email']}")
            
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
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@router.post("/refresh")
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Refresh access token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, email FROM users WHERE id = $1",
                int(user_id)
            )
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            
            new_token = create_access_token({"sub": str(user_id)})
            return {"access_token": new_token, "token_type": "bearer"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
