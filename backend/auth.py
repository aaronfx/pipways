"""
Authentication routes and handlers.
"""
from datetime import datetime  # ← ADD THIS LINE
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
from pydantic import BaseModel, EmailStr
from typing import Optional

# RELATIVE imports (from .module)
from .database import database, users, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from .security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_user
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    role: Optional[str] = "user"
    created_at: Optional[datetime] = None  # ← This now works

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[dict] = None

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister):
    """Register a new user."""
    # Check if user exists
    query = users.select().where(users.c.email == user_data.email)
    existing = await database.fetch_one(query)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = get_password_hash(user_data.password)
    
    # Prepare user data
    user_values = {
        "email": user_data.email,
        "password_hash": hashed_password,
        "full_name": user_data.full_name,
        "is_active": True,
        "is_admin": False,
        "created_at": datetime.utcnow()
    }
    
    # Add role if column exists
    if hasattr(users.c, 'role'):
        user_values["role"] = "user"
    
    try:
        query = users.insert().values(**user_values)
        user_id = await database.execute(query)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_data.email}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "is_active": True,
                "is_admin": False,
                "role": "user"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.post("/token", response_model=Token)
async def login(form_data: dict = None, username: str = None, password: str = None):
    """
    OAuth2 compatible token login.
    Accepts both form data and JSON.
    """
    # Handle form data (OAuth2 standard)
    if form_data and isinstance(form_data, dict):
        username = form_data.get('username')
        password = form_data.get('password')
    
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password required"
        )
    
    # Verify user credentials
    query = users.select().where(users.c.email == username)
    user = await database.fetch_one(query)
    
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "is_active": user["is_active"],
            "is_admin": user.get("is_admin", False),
            "role": user.get("role", "user")
        }
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user

@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token removal)."""
    return {"message": "Successfully logged out"}
