"""
Authentication routes and handlers.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import traceback

# RELATIVE imports
from .database import database, users, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from .security import (
    get_password_hash, 
    verify_password, 
    create_access_token
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/register")
async def register(user_data: UserRegister):
    """Register a new user."""
    try:
        # Check if database is connected
        if not database.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available"
            )
        
        # Check if user exists
        query = users.select().where(users.c.email == user_data.email)
        existing = await database.fetch_one(query)
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Prepare user data
        user_values = {
            "email": user_data.email,
            "password_hash": hashed_password,
            "full_name": user_data.full_name or "",
            "is_active": True,
            "is_admin": False,
            "created_at": datetime.utcnow()
        }
        
        # Insert user
        query = users.insert().values(**user_values)
        user_id = await database.execute(query)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_data.email}, 
            expires_delta=access_token_expires
        )
        
        # Return success response
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": user_data.email,
                "full_name": user_data.full_name or "",
                "is_active": True,
                "is_admin": False,
                "role": "user"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/token")
async def login(username: str = Form(...), password: str = Form(...)):
    """
    OAuth2 compatible token login using form data.
    """
    try:
        # Check if database is connected
        if not database.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available"
            )
        
        # Find user by email (username field contains email)
        query = users.select().where(users.c.email == username)
        user = await database.fetch_one(query)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"]}, 
            expires_delta=access_token_expires
        )
        
        # Determine role
        role = "admin" if user.get("is_admin") else user.get("role", "user")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("full_name", ""),
                "is_active": user["is_active"],
                "is_admin": user.get("is_admin", False),
                "role": role
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me")
async def get_current_user_info():
    """Get current user info - requires token in header."""
    from fastapi import Depends
    from .security import get_current_user as security_get_current_user
    
    try:
        user = await security_get_current_user()
        return {
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name", ""),
            "is_active": user["is_active"],
            "is_admin": user.get("is_admin", False),
            "role": "admin" if user.get("is_admin") else user.get("role", "user")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication"
        )
