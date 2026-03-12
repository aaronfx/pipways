"""
Authentication routes and handlers.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta

# ABSOLUTE imports (not relative)
from backend.database import database, users
from backend.security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_user, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from backend.schemas import UserRegister, UserResponse, Token

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
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
    query = users.insert().values(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name
    )

    try:
        user_id = await database.execute(query)
        return {**user_data.dict(), "id": user_id, "is_active": True, "is_admin": False}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.post("/token", response_model=Token)
async def login(form_data: UserRegister):
    """OAuth2 compatible token login."""
    # Verify user credentials
    query = users.select().where(users.c.email == form_data.email)
    user = await database.fetch_one(query)

    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user
