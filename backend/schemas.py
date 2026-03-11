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

class TokenData(BaseModel):
    sub: Optional[str] = None
    email: Optional[str] = None

class UserUpdate(BaseModel):
    role: Optional[str] = None
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None
    full_name: Optional[str] = None
    email_verified: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    subscription_tier: str
    subscription_status: str
    email_verified: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================================================
# Blog Models
# ============================================================================

class BlogPostBase(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = None
    category: Optional[str] = None
    featured_image: Optional[str] = None
    is_premium: bool = False
    tags: Optional[List[str]] = []
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

class BlogPostCreate(BlogPostBase):
    status: str = Field(default="published", pattern="^(draft|published|scheduled)$")
    scheduled_at: Optional[datetime] = None

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    category: Optional[str] = None
    featured_image: Optional[str] = None
    is_premium: Optional[bool] = None
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    tags: Optional[List[str]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

class BlogPostResponse(BlogPostBase):
    id: int
    status: str
    slug: Optional[str] = None
    author_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================================================
# Webinar Models
# ============================================================================

class WebinarBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=1)
    is_premium: bool = False
    meeting_link: Optional[str] = None
    max_participants: Optional[int] = Field(default=100, ge=1)
    reminder_message: Optional[str] = None

class WebinarCreate(WebinarBase):
    pass

class WebinarUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    is_premium: Optional[bool] = None
    meeting_link: Optional[str] = None
    max_participants: Optional[int] = None
    reminder_message: Optional[str] = None

class WebinarResponse(WebinarBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# Signal Models
# ============================================================================

class SignalBase(BaseModel):
    pair: str = Field(..., min_length=1)
    direction: str = Field(..., pattern="^(buy|sell)$")
    entry_price: float
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward_ratio: Optional[str] = None
    expires_at: Optional[datetime] = None
    timeframe: str = "1H"
    analysis: Optional[str] = None
    is_premium: bool = False

class SignalCreate(SignalBase):
    pass

class SignalUpdate(BaseModel):
    pair: Optional[str] = None
    direction: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward_ratio: Optional[str] = None
    expires_at: Optional[datetime] = None
    timeframe: Optional[str] = None
    analysis: Optional[str] = None
    is_premium: Optional[bool] = None
    status: Optional[str] = None
    result: Optional[str] = None
    pips_gain: Optional[float] = None

class SignalResultUpdate(BaseModel):
    result: str = Field(..., pattern="^(WIN|LOSS|PARTIAL|EXPIRED)$")
    pips_gain_loss: Optional[float] = None

class SignalResponse(SignalBase):
    id: int
    status: str
    result: Optional[str] = None
    pips_gain: Optional[float] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================================================
# Course Models
# ============================================================================

class CourseBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    content: Optional[str] = None
    is_premium: bool = False
    level: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")
    duration_hours: Optional[float] = None
    thumbnail: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    is_premium: Optional[bool] = None
    level: Optional[str] = None
    duration_hours: Optional[float] = None
    thumbnail: Optional[str] = None

class CourseModuleBase(BaseModel):
    title: str = Field(..., min_length=1)
    content: Optional[str] = None
    video_url: Optional[str] = None
    sort_order: int = 0
    is_premium: bool = False

class CourseModuleCreate(CourseModuleBase):
    pass

class CourseResponse(CourseBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    modules: Optional[List[Dict[str, Any]]] = []

    class Config:
        from_attributes = True

# ============================================================================
# Quiz Models
# ============================================================================

class QuizCreate(BaseModel):
    course_id: int
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    passing_score: int = Field(default=70, ge=0, le=100)

class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    passing_score: Optional[int] = Field(None, ge=0, le=100)

class QuizQuestionCreate(BaseModel):
    quiz_id: int
    question_text: str
    question_type: str = Field(default="multiple_choice", pattern="^(multiple_choice|true_false|text)$")
    options: Optional[List[str]] = []
    correct_answer: str
    points: int = Field(default=1, ge=1)

class QuizAttempt(BaseModel):
    quiz_id: int
    answers: Dict[str, Any]

# ============================================================================
# AI & Performance Models
# ============================================================================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context: Optional[str] = ""
    history: Optional[List[Dict[str, str]]] = []
    use_knowledge: Optional[bool] = True

class ChartAnalysisRequest(BaseModel):
    image: str  # Base64 encoded image
    pair: Optional[str] = "EURUSD"
    timeframe: Optional[str] = "1H"
    context: Optional[str] = ""

class PerformanceAnalysisRequest(BaseModel):
    trades: Optional[List[Dict[str, Any]]] = []
    account_balance: Optional[float] = None
    trading_period_days: Optional[int] = None

class VisionAnalysisRequest(BaseModel):
    image: str  # Base64 encoded image
    account_balance: Optional[float] = None
    trading_period_days: Optional[int] = 30

class PerformanceAnalysisResponse(BaseModel):
    trader_score: int
    total_trades: int
    win_rate: float
    profit_factor: Optional[float] = None
    average_return: Optional[float] = None
    top_mistakes: List[str]
    strengths: List[str]
    improvement_plan: List[str]
    recommended_courses: List[str]
    mentor_advice: str

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

class SiteSettingsResponse(BaseModel):
    id: int
    site_name: str
    telegram_free_link: Optional[str] = None
    telegram_vip_link: Optional[str] = None
    vip_price: float
    vip_price_currency: str
    seo_default_title: Optional[str] = None
    seo_default_description: Optional[str] = None
    contact_email: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================================================
# Admin Dashboard Models
# ============================================================================

class DashboardStats(BaseModel):
    total_users: int
    new_users_30d: int
    vip_users: int
    active_signals: int
    published_posts: int
    upcoming_webinars: int
    total_courses: int

class UserManagementUpdate(BaseModel):
    role: Optional[str] = Field(None, pattern="^(user|moderator|admin)$")
    subscription_tier: Optional[str] = Field(None, pattern="^(free|vip)$")
    subscription_status: Optional[str] = Field(None, pattern="^(active|inactive|cancelled)$")
