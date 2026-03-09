
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"

class SubscriptionTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    PRO = "pro"

# Auth Models
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

# Blog Models
class BlogPostCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    category: Optional[str] = "general"
    status: str = "draft"  # draft, published, scheduled
    scheduled_at: Optional[datetime] = None
    featured_image: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    tags: List[str] = []
    is_premium: bool = False
    slug: Optional[str] = None

class BlogPostResponse(BlogPostCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    author_id: int
    views: int = 0

# Course Models
class CourseModule(BaseModel):
    title: str
    content: str
    order: int = 0
    video_url: Optional[str] = None
    duration_minutes: Optional[int] = None

class CourseCreate(BaseModel):
    title: str
    description: str
    content: Optional[str] = None
    level: str = "beginner"  # beginner, intermediate, advanced
    duration_hours: Optional[float] = None
    thumbnail: Optional[str] = None
    is_premium: bool = False
    modules: List[CourseModule] = []

class CourseResponse(CourseCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    instructor_id: int

# Webinar Models
class WebinarCreate(BaseModel):
    title: str
    description: str
    scheduled_at: datetime
    duration_minutes: int = 60
    max_participants: int = 100
    meeting_link: Optional[str] = None
    is_premium: bool = False
    is_recorded: bool = False
    recording_url: Optional[str] = None

class WebinarResponse(WebinarCreate):
    id: int
    created_at: datetime
    host_id: int
    current_participants: int = 0

# Signal Models
class SignalCreate(BaseModel):
    pair: str
    direction: str  # BUY, SELL
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timeframe: str = "1H"
    analysis: Optional[str] = None
    is_premium: bool = False

# AI Models
class PerformanceAnalysisRequest(BaseModel):
    trades: List[dict]
    account_balance: Optional[float] = None
    trading_period_days: int = 30

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1)
    context: str = "trading"  # trading, psychology, risk_management, etc.

class ChartAnalysisRequest(BaseModel):
    pair: str = "EURUSD"
    timeframe: str = "1H"
    additional_info: Optional[str] = ""
