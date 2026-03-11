"""
Pydantic Models for Request/Response Validation
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class BlogPostCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    category: Optional[str] = None
    featured_image: Optional[str] = None
    is_premium: bool = False
    status: str = "published"

class CourseCreate(BaseModel):
    title: str
    description: str
    content: Optional[str] = None
    level: str = "beginner"
    duration_hours: Optional[float] = None
    thumbnail: Optional[str] = None
    is_premium: bool = False

class CourseModuleCreate(BaseModel):
    title: str
    content: Optional[str] = None
    video_url: Optional[str] = None
    is_premium: bool = False
    sort_order: int = 0

class WebinarCreate(BaseModel):
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int = 60
    meeting_link: Optional[str] = None
    is_premium: bool = False
    max_participants: int = 100
    reminder_message: Optional[str] = None

class SignalCreate(BaseModel):
    pair: str
    direction: str
    entry_price: float
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    analysis: Optional[str] = None
    is_premium: bool = False
    status: str = "active"

class UserUpdate(BaseModel):
    role: Optional[str] = None
    subscription_tier: Optional[str] = None

class AIAnalyzeRequest(BaseModel):
    pair: str
    timeframe: str
    context: Optional[str] = None

class AIMentorRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    use_knowledge: bool = True

# FIXED: Added missing schema
class PerformanceAnalysisRequest(BaseModel):
    image: str  # base64 encoded image
    account_balance: float
    trading_period_days: int
