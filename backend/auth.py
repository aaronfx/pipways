"""
Authentication module - Production Grade OAuth2 Implementation
"""
from fastapi import APIRouter, HTTPException, status, Depends, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError
import os

from .database import database, users, get_available_columns
from .security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM
)

# FIXED: Removed prefix="/auth" to prevent double prefixing (main.py already adds /auth)
router = APIRouter(tags=["auth"])

# OAuth2 scheme for token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool = True
    is_admin: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

_available_columns_cache = None

def get_columns():
    """Get available columns with caching."""
    global _available_columns_cache
    if _available_columns_cache is None:
        _available_columns_cache = get_available_columns()
    return _available_columns_cache

async def get_user_by_email(email: str):
    """Fetch user by email safely."""
    try:
        query = users.select().where(users.c.email == email)
        result = await database.fetch_one(query)
        return result
    except Exception as e:
        print(f"[DB Error] fetching user: {e}", flush=True)
        return None

async def create_user(user_data: dict):
    """Create user with only available columns."""
    try:
        available_cols = get_columns()
        
        insert_data = {
            "email": user_data["email"],
            "password_hash": get_password_hash(user_data["password"]),
            "created_at": datetime.utcnow()
        }
        
        if "full_name" in available_cols:
            insert_data["full_name"] = user_data.get("full_name", "")
        if "is_active" in available_cols:
            insert_data["is_active"] = True
        if "is_admin" in available_cols:
            insert_data["is_admin"] = False
        if "role" in available_cols:
            insert_data["role"] = "user"
        if "subscription_tier" in available_cols:
            insert_data["subscription_tier"] = "free"
        
        query = users.insert().values(**insert_data)
        user_id = await database.execute(query)
        
        return {
            "id": user_id,
            "email": user_data["email"],
            "full_name": insert_data.get("full_name", ""),
            "is_active": insert_data.get("is_active", True),
            "is_admin": insert_data.get("is_admin", False)
        }
    except Exception as e:
        print(f"[Error] creating user: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister):
    """Register a new user account."""
    print(f"[Auth] Registration attempt: {user_data.email}", flush=True)
    
    existing = await get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = await create_user({
        "email": user_data.email,
        "password": user_data.password,
        "full_name": user_data.full_name
    })
    
    access_token = create_access_token(
        data={"sub": user_data.email, "user_id": user["id"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user)
    }

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login endpoint.
    Expects: application/x-www-form-urlencoded with username and password fields.
    """
    print(f"[Auth] Login attempt: {form_data.username}", flush=True)
    
    user = await get_user_by_email(form_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        stored_hash = user.password_hash if hasattr(user, 'password_hash') else user['password_hash']
        is_valid = verify_password(form_data.password, stored_hash)
    except Exception as e:
        print(f"[Error] Password verification: {e}", flush=True)
        is_valid = False
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Safely extract user properties
    is_active = getattr(user, 'is_active', True) if not isinstance(user, dict) else user.get('is_active', True)
    if not is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")
    
    user_id = getattr(user, 'id', None) or user.get('id')
    user_email = getattr(user, 'email', None) or user.get('email')
    is_admin = getattr(user, 'is_admin', False) if not isinstance(user, dict) else user.get('is_admin', False)
    full_name = getattr(user, 'full_name', '') if not isinstance(user, dict) else user.get('full_name', '')
    
    access_token = create_access_token(
        data={
            "sub": user_email,
            "user_id": user_id,
            "is_admin": is_admin
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user_id,
            email=user_email,
            full_name=full_name,
            is_active=is_active,
            is_admin=is_admin
        )
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user info."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(email)
    if user is None:
        raise credentials_exception
    
    return UserResponse(
        id=getattr(user, 'id', None) or user.get('id'),
        email=getattr(user, 'email', None) or user.get('email'),
        full_name=getattr(user, 'full_name', '') if not isinstance(user, dict) else user.get('full_name', ''),
        is_active=getattr(user, 'is_active', True) if not isinstance(user, dict) else user.get('is_active', True),
        is_admin=getattr(user, 'is_admin', False) if not isinstance(user, dict) else user.get('is_admin', False)
    )
