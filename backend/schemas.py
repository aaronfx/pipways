"""
Pydantic Models for Pipways Platform
All request/response schemas defined here
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field, field_validator

# ============================================================================
# Authentication Models
# ============================================================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain a lowercase letter')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain an uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain a number')
        if not any(c in '@$!%*?&' for c in v):
            raise ValueError('Password must contain a special character (@$!%*?&)')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserUpdate(BaseModel):
    role: Optional[str] = None
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None
    full_name: Optional[str] = None

# ============================================================================
# Blog Models
# ============================================================================

class BlogPostCreate(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = None
    is_premium: bool = False
    status: str = Field(default="published", pattern="^(draft|published|scheduled)$")
    scheduled_at: Optional[datetime] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    slug: Optional[str] = None
    featured_image: Optional[str] = None
    tags: Optional[List[str]] = []
    category: Optional[str] = None

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    is_premium: Optional[bool] = None
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    slug: Optional[str] = None
    featured_image: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None

# ============================================================================
# Webinar Models
# ============================================================================

class WebinarCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=1)
    is_premium: bool = False
    meeting_link: Optional[str] = None
    max_participants: Optional[int] = 100
    reminder_message: Optional[str] = None  # Required field for webinar creation

class WebinarUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    is_premium: Optional[bool] = None
    meeting_link: Optional[str] = None
    max_participants: Optional[int] = None
    reminder_message: Optional[str] = None

# ============================================================================
# Signal Models
# ============================================================================

class SignalCreate(BaseModel):
    pair: str = Field(..., min_length=1)
    direction: str = Field(..., pattern="^(buy|sell)$")
    entry_price: float
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    risk_reward_ratio: Optional[str] = None
    expires_at: Optional[datetime] = None
    timeframe: str = "1H"
    analysis: Optional[str] = None
    is_premium: bool = False

class SignalUpdate(BaseModel):
    pair: Optional[str] = None
    direction: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    risk_reward_ratio: Optional[str] = None
    expires_at: Optional[datetime] = None
    timeframe: Optional[str] = None
    analysis: Optional[str] = None
    is_premium: Optional[bool] = None
    status: Optional[str] = None
    result: Optional[str] = None

class SignalResultUpdate(BaseModel):
    result: str = Field(..., pattern="^(WIN|LOSS|PARTIAL|EXPIRED)$")
    pips_gain_loss: Optional[float] = None

# ============================================================================
# Course Models
# ============================================================================

class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    is_premium: bool = False
    level: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")
    duration_hours: Optional[float] = None
    thumbnail: Optional[str] = None
    modules: Optional[List[Dict]] = None

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    is_premium: Optional[bool] = None
    level: Optional[str] = None
    duration_hours: Optional[float] = None
    thumbnail: Optional[str] = None

class ModuleCreate(BaseModel):
    title: str = Field(..., min_length=1)
    content: Optional[str] = None
    video_url: Optional[str] = None
    sort_order: Optional[int] = 0
    is_premium: bool = False

class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    video_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_premium: Optional[bool] = None

# ============================================================================
# Quiz Models
# ============================================================================

class QuizCreate(BaseModel):
    course_id: int
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    passing_score: int = Field(default=70, ge=0, le=100)
    questions: Optional[List[Dict]] = []

class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    passing_score: Optional[int] = None

class QuizQuestionCreate(BaseModel):
    quiz_id: int
    question_text: str
    question_type: str = Field(default="multiple_choice", pattern="^(multiple_choice|true_false|text)$")
    options: Optional[List[str]] = []
    correct_answer: str
    points: int = Field(default=1, ge=1)
    sort_order: Optional[int] = 0

class QuizAttempt(BaseModel):
    quiz_id: int
    answers: Dict[str, Any]

# ============================================================================
# AI & Performance Models
# ============================================================================

class PerformanceAnalysisRequest(BaseModel):
    trades: Optional[List[Dict[str, Any]]] = []
    account_balance: Optional[float] = None
    trading_period_days: Optional[int] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context: Optional[str] = ""
    history: Optional[List[Dict[str, str]]] = []
    include_knowledge: Optional[bool] = True

# ============================================================================
# Settings Models
# ============================================================================

class SiteSettingsUpdate(BaseModel):
    site_name: Optional[str] = None
    telegram_free_link: Optional[str] = None
    telegram_vip_link: Optional[str] = None
    vip_price: Optional[float] = None
    vip_price_currency: Optional[str] = None
    seo_default_title: Optional[str] = None
    seo_default_description: Optional[str] = None
    contact_email: Optional[str] = None
