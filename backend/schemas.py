"""
Pydantic Schemas for Pipways Trading Platform
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    
class UserRegister(UserBase):
    password: str = Field(..., min_length=6)
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    telegram_username: Optional[str] = None
    preferred_pairs: Optional[List[str]] = None
    notification_settings: Optional[Dict[str, Any]] = None
    
class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: str
    subscription_tier: str
    is_active: bool
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
    
class Token(BaseModel):
    """Token response with user data - Used by auth routes"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict  # Contains id, email, full_name, role, subscription_tier
    
class TokenResponse(BaseModel):
    """Alternative token response format"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserMinimal(BaseModel):
    id: int
    full_name: str


# ============================================================================
# SIGNAL SCHEMAS
# ============================================================================

class SignalBase(BaseModel):
    pair: str
    direction: str
    entry_price: Decimal
    stop_loss: Decimal
    take_profit_1: Decimal
    take_profit_2: Optional[Decimal] = None
    take_profit_3: Optional[Decimal] = None
    analysis: Optional[str] = None

class SignalCreate(SignalBase):
    status: Optional[str] = "active"
    
class SignalUpdate(BaseModel):
    pair: Optional[str] = None
    direction: Optional[str] = None
    entry_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit_1: Optional[Decimal] = None
    take_profit_2: Optional[Decimal] = None
    take_profit_3: Optional[Decimal] = None
    analysis: Optional[str] = None
    status: Optional[str] = None
    tp1_hit: Optional[bool] = None
    tp2_hit: Optional[bool] = None
    tp3_hit: Optional[bool] = None
    sl_hit: Optional[bool] = None
    pips_gained: Optional[float] = None

class SignalResponse(SignalBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    risk_reward_ratio: Optional[str] = None
    status: str
    tp1_hit: bool = False
    tp2_hit: bool = False
    tp3_hit: bool = False
    sl_hit: bool = False
    pips_gained: Optional[float] = None
    created_by: Optional[int] = None
    author_name: Optional[str] = None
    created_at: Optional[datetime] = None
    
class SignalListResponse(BaseModel):
    signals: List[SignalResponse]
    total: int


# ============================================================================
# COURSE SCHEMAS (FIXED - All missing classes added)
# ============================================================================

class CourseBase(BaseModel):
    title: str
    description: str
    short_description: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = "beginner"
    duration_minutes: Optional[int] = None
    thumbnail_url: Optional[str] = None

class CourseCreate(CourseBase):
    status: Optional[str] = "draft"
    
class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    duration_minutes: Optional[int] = None
    thumbnail_url: Optional[str] = None
    status: Optional[str] = None

class CourseResponse(CourseBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    status: str
    lessons_count: Optional[int] = 0
    created_at: Optional[datetime] = None

class LessonBase(BaseModel):
    title: str
    content: Optional[str] = None
    video_url: Optional[str] = None
    order_index: int = 0
    duration_minutes: Optional[int] = None
    is_preview: bool = False

class LessonCreate(LessonBase):
    pass

class LessonUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    video_url: Optional[str] = None
    order_index: Optional[int] = None
    duration_minutes: Optional[int] = None
    is_preview: Optional[bool] = None

class LessonResponse(LessonBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    course_id: int
    created_at: Optional[datetime] = None

class QuizCreate(BaseModel):
    lesson_id: Optional[int] = None
    question: str
    options: List[str]
    correct_answer: str

class QuizSubmit(BaseModel):
    answer: str

class QuestionCreate(BaseModel):
    lesson_id: Optional[int] = None
    question: str

class AnswerCreate(BaseModel):
    question_id: int
    answer: str

class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    course_id: int
    lesson_id: Optional[int] = None
    user_id: int
    question: str
    is_answered: bool = False
    created_at: Optional[datetime] = None

class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    course_id: int
    progress_percent: int = 0
    enrolled_at: Optional[datetime] = None

class ProgressResponse(BaseModel):
    lesson_id: int
    completed: bool
    progress_percent: int


# ============================================================================
# BLOG SCHEMAS
# ============================================================================

class SEOMetadata(BaseModel):
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    focus_keyword: Optional[str] = None

class BlogPostBase(BaseModel):
    title: str
    slug: Optional[str] = None
    content: str
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    focus_keyword: Optional[str] = None

class BlogPostCreate(BlogPostBase):
    status: Optional[str] = "draft"
    is_featured: bool = False

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    focus_keyword: Optional[str] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None

class BlogPostResponse(BlogPostBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    status: str
    is_featured: bool = False
    views: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class BlogCommentCreate(BaseModel):
    content: str

class BlogCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    post_id: int
    user_id: int
    content: str
    is_approved: bool = False
    created_at: Optional[datetime] = None


# ============================================================================
# WEBINAR SCHEMAS
# ============================================================================

class WebinarBase(BaseModel):
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: Optional[int] = 60
    meeting_link: Optional[str] = None
    max_participants: Optional[int] = None
    reminder_message: Optional[str] = None
    is_premium: bool = False

class WebinarCreate(WebinarBase):
    pass

class WebinarUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    meeting_link: Optional[str] = None
    max_participants: Optional[int] = None
    reminder_message: Optional[str] = None
    is_premium: Optional[bool] = None
    status: Optional[str] = None
    recording_url: Optional[str] = None

class WebinarResponse(WebinarBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    current_participants: int = 0
    created_by: Optional[int] = None
    author_name: Optional[str] = None
    is_registered: Optional[bool] = False
    created_at: Optional[datetime] = None

class WebinarRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    webinar_id: int
    user_id: int
    registered_at: Optional[datetime] = None
    attended: bool = False
    feedback_rating: Optional[int] = None
    feedback_comment: Optional[str] = None


# ============================================================================
# MEDIA SCHEMAS
# ============================================================================

class MediaUploadResponse(BaseModel):
    filename: str
    original_name: str
    url: str
    size: int
    folder: str


# ============================================================================
# ADMIN/DASHBOARD SCHEMAS
# ============================================================================

class DashboardStats(BaseModel):
    total_users: int = 0
    total_signals: int = 0
    active_signals: int = 0
    total_courses: int = 0
    published_courses: int = 0
    total_lessons: int = 0
    total_quizzes: int = 0
    total_blog_posts: int = 0
    total_webinars: int = 0
    total_enrollments: int = 0
    pending_questions: int = 0
    recent_activities: Optional[List[Dict[str, Any]]] = None

class MessageResponse(BaseModel):
    message: str
    success: bool = True
