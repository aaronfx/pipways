"""
Authentication Routes - User registration, login, token management
"""

import os
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import Optional

# ABSOLUTE IMPORTS (no dots)
import database
from schemas import UserRegister, UserLogin, UserResponse, TokenResponse, UserUpdate
from security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    get_current_user
)

router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister):
    """Register new user"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Check if registration is enabled
    reg_enabled = await database.get_setting('enable_registration', 'true')
    if reg_enabled == 'false':
        raise HTTPException(status_code=403, detail="Registration is currently disabled")
    
    async with database.db_pool.acquire() as conn:
        # Check if email exists
        existing = await conn.fetchval("SELECT id FROM users WHERE email = $1", user_data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user
        user_id = await conn.fetchval("""
            INSERT INTO users (email, hashed_password, full_name, role, subscription_tier, is_active, created_at)
            VALUES ($1, $2, $3, 'user', 'free', TRUE, CURRENT_TIMESTAMP)
            RETURNING id
        """, user_data.email, hashed_password, user_data.full_name)
        
        # Return user
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return dict(user)

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Authenticate user and return JWT tokens"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        # Get user by email
        user = await conn.fetchrow("""
            SELECT id, email, hashed_password, full_name, role, subscription_tier, is_active 
            FROM users WHERE email = $1
        """, credentials.email)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not user['is_active']:
            raise HTTPException(status_code=403, detail="Account is deactivated")
        
        # Verify password
        if not verify_password(credentials.password, user['hashed_password']):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Update last login
        await conn.execute("""
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1
        """, user['id'])
        
        # Generate tokens
        token_data = {
            "sub": str(user['id']),
            "email": user['email'],
            "role": user['role'],
            "tier": user['subscription_tier']
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Log activity
        await database.log_activity(
            user_id=user['id'],
            action='login',
            entity_type='user',
            entity_id=user['id'],
            ip_address=None,
            user_agent=None
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 60
        }

@router.post("/refresh")
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Refresh access token using refresh token"""
    from jose import jwt as jose_jwt, JWTError
    
    try:
        payload = jose_jwt.decode(credentials.credentials, os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production-min-32-chars"), algorithms=["HS256"])
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("sub")
        
        # Generate new access token
        token_data = {
            "sub": user_id,
            "email": payload.get("email"),
            "role": payload.get("role"),
            "tier": payload.get("tier")
        }
        
        new_token = create_access_token(token_data)
        
        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_in": 60
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info"""
    return current_user

@router.put("/me")
async def update_profile(update_data: UserUpdate, current_user: dict = Depends(get_current_user)):
    """Update current user profile"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        # Build update fields
        updates = []
        values = []
        
        if update_data.full_name:
            updates.append("full_name = $1")
            values.append(update_data.full_name)
        if update_data.phone:
            updates.append(f"phone = ${len(values)+1}")
            values.append(update_data.phone)
        if update_data.country:
            updates.append(f"country = ${len(values)+1}")
            values.append(update_data.country)
        if update_data.telegram_username:
            updates.append(f"telegram_username = ${len(values)+1}")
            values.append(update_data.telegram_username)
        if update_data.preferred_pairs:
            updates.append(f"preferred_pairs = ${len(values)+1}")
            values.append(update_data.preferred_pairs)
        if update_data.notification_settings:
            updates.append(f"notification_settings = ${len(values)+1}")
            values.append(update_data.notification_settings)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(current_user['id'])
        
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ${len(values)} RETURNING *"
        row = await conn.fetchrow(query, *values)
        
        return dict(row)

@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_user)
):
    """Change user password"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        # Get current password hash
        user = await conn.fetchrow(
            "SELECT hashed_password FROM users WHERE id = $1", 
            current_user['id']
        )
        
        if not verify_password(current_password, user['hashed_password']):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Update password
        new_hash = get_password_hash(new_password)
        await conn.execute(
            "UPDATE users SET hashed_password = $1 WHERE id = $2",
            new_hash, current_user['id']
        )
        
        return {"message": "Password updated successfully"}
