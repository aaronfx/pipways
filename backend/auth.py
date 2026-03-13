"""
Authentication module - handles user registration and login.
Fixed to work with older database schemas gracefully.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError

from .database import database, users, get_available_columns
from .security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM
)

router = APIRouter(prefix="/auth", tags=["auth"])

# OAuth2 scheme
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

# Cache available columns to avoid repeated inspection
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
        # Only select columns that exist
        cols = get_columns()
        query = users.select().where(users.c.email == email)
        result = await database.fetch_one(query)
        return result
    except Exception as e:
        print(f"DB Error fetching user: {e}", flush=True)
        return None

async def create_user(user_data: dict):
    """Create user with only available columns."""
    try:
        available_cols = get_columns()
        
        # Build insert data with only existing columns
        insert_data = {
            "email": user_data["email"],
            "password_hash": get_password_hash(user_data["password"]),
            "created_at": datetime.utcnow()
        }
        
        # Only add optional columns if they exist in DB
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
        
        # Build query dynamically
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
        print(f"Error creating user: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister):
    """Register a new user account."""
    print(f"Registration attempt for: {user_data.email}", flush=True)
    
    # Check if user exists
    existing = await get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = await create_user({
        "email": user_data.email,
        "password": user_data.password,
        "full_name": user_data.full_name
    })
    
    # Create access token
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
    """Authenticate user and return JWT token."""
    print(f"Login attempt for: {form_data.username}", flush=True)
    
    user = await get_user_by_email(form_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    try:
        stored_hash = user.password_hash if hasattr(user, 'password_hash') else user['password_hash']
        is_valid = verify_password(form_data.password, stored_hash)
    except Exception as e:
        print(f"Password verification error: {e}", flush=True)
        is_valid = False
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check active status safely
    is_active = True
    if hasattr(user, 'is_active'):
        is_active = user.is_active
    elif isinstance(user, dict) and 'is_active' in user:
        is_active = user['is_active']
    
    if not is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")
    
    # Get user ID and email safely
    user_id = user.id if hasattr(user, 'id') else user['id']
    user_email = user.email if hasattr(user, 'email') else user['email']
    is_admin = False
    if hasattr(user, 'is_admin'):
        is_admin = user.is_admin
    elif isinstance(user, dict) and 'is_admin' in user:
        is_admin = user['is_admin']
    
    access_token = create_access_token(
        data={
            "sub": user_email,
            "user_id": user_id,
            "is_admin": is_admin
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    user_response = {
        "id": user_id,
        "email": user_email,
        "full_name": getattr(user, 'full_name', user.get('full_name', '')) if isinstance(user, dict) else getattr(user, 'full_name', ''),
        "is_active": is_active,
        "is_admin": is_admin
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user_response)
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
        id=user.id if hasattr(user, 'id') else user['id'],
        email=user.email if hasattr(user, 'email') else user['email'],
        full_name=getattr(user, 'full_name', user.get('full_name', '')) if isinstance(user, dict) else getattr(user, 'full_name', ''),
        is_active=getattr(user, 'is_active', True) if not isinstance(user, dict) else user.get('is_active', True),
        is_admin=getattr(user, 'is_admin', False) if not isinstance(user, dict) else user.get('is_admin', False)
    )
