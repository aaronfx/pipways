"""
Security Utilities
Authentication and authorization dependencies
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from typing import Optional

# FIXED: Import database module, not the variable
from . import database
from .database import SECRET_KEY, ALGORITHM

security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return current user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Get user from database
    async with database.db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, email, full_name, role, subscription_tier, subscription_status FROM users WHERE id = $1",
            int(user_id)
        )
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    return dict(user)

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Optional authentication - returns user if token valid, None if no token or invalid.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            return None
            
        if not database.db_pool:
            return None
            
        async with database.db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, full_name, role, subscription_tier, subscription_status FROM users WHERE id = $1",
                int(user_id)
            )
            return dict(user) if user else None
            
    except (jwt.ExpiredSignatureError, jwt.JWTError, Exception):
        return None

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Verify user is admin or moderator"""
    if current_user["role"] not in ["admin", "moderator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def create_access_token(data: dict, expires_delta: Optional[int] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    """Create JWT refresh token"""
    expire = datetime.utcnow() + timedelta(days=7)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
