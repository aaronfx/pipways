from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, insert, update
from pydantic import BaseModel, EmailStr
from typing import Optional

from .database import database, users, subscriptions
from .security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from .schemas import UserRegister, UserResponse, Token

router = APIRouter(prefix="/auth", tags=["authentication"])

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister):
    query = select(users).where(users.c.email == user_data.email)
    existing_user = await database.fetch_one(query)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    query = select(users).where(users.c.username == user_data.username)
    existing_user = await database.fetch_one(query)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = get_password_hash(user_data.password)

    query = insert(users).values(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        country=user_data.country,
        is_active=True,
        is_admin=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    user_id = await database.execute(query)

    # Create free subscription
    query = insert(subscriptions).values(
        user_id=user_id,
        tier="free",
        status="active",
        created_at=datetime.utcnow()
    )
    await database.execute(query)

    query = select(users).where(users.c.id == user_id)
    user = await database.fetch_one(query)
    return dict(user)

@router.post("/login", response_model=LoginResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    query = select(users).where(
        (users.c.email == form_data.username) | (users.c.username == form_data.username)
    )
    user = await database.fetch_one(query)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    query = update(users).where(users.c.id == user["id"]).values(
        last_login=datetime.utcnow()
    )
    await database.execute(query)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["id"])}, 
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": dict(user)
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: dict = Depends(get_current_user)):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(current_user["id"])}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
