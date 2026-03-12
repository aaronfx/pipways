"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class SignalCreate(BaseModel):
    symbol: str
    action: str  # BUY or SELL
    price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class SignalResponse(SignalCreate):
    id: int
    created_at: datetime
    status: str
