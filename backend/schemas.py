"""
Pydantic Schemas for Pipways Trading Platform
Complete request/response models for all API endpoints
"""

from pydantic import BaseModel, EmailStr, Field, validator, root_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

# ============================================================================
# ENUMERATIONS
# ============================================================================

class UserRole(str, Enum):
    user = "user"
    moderator = "moderator"
    admin = "admin"

class SubscriptionTier(str, Enum):
    free = "free"
    vip = "vip"

class SignalDirection(str, Enum):
    buy = "buy"
    sell = "sell"

class SignalStatus(str, Enum):
    active = "active"
    tp1_hit = "tp1_hit"
    tp2_hit = "tp2_hit"
    tp3_hit = "tp3_hit"
    sl_hit = "sl_hit"
    closed = "closed"
    expired = "expired"
    cancelled = "cancelled"

class CourseLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"

class CourseStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"

class VideoType(str, Enum):
    upload = "upload"
    youtube = "youtube"
    vimeo = "vimeo"
    embed = "embed"

class QuestionType(str, Enum):
    multiple_choice = "multiple_choice"
    true_false = "true_false"
    fill_blank = "fill_blank"
    matching = "matching"
    essay = "essay"

class BlogStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"

class WebinarStatus(str, Enum):
    scheduled = "scheduled"
    live = "live"
    completed = "completed"
    cancelled = "cancelled"

class PaymentStatus(str, Enum):
    free = "free"
    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"

class QuestionCategory(str, Enum):
    general = "general"
    technical = "technical"
    clarification = "clarification"
    error = "error"

# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserRegister(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    trading_experience: Optional[str] = None
    preferred_pairs: Optional[List[str]] = []
    telegram_username: Optional[str] = Field(None, max_length=100)
    notification_settings: Optional[Dict[str, bool]] = None
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    id: int
    role: UserRole
    subscription_tier: SubscriptionTier
    is_active: bool
    email_verified: bool
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    trading_experience: Optional[str] = None
    preferred_pairs: List[str] = []
    telegram_username: Optional[str] = None
    notification_settings: Dict[str, Any] = {}
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class UserMinimal(BaseModel):
    id: int
    full_name: Optional[str] = None
    email: EmailStr
    
    class Config:
        orm_mode = True

# ============================================================================
# SIGNAL SCHEMAS
# ============================================================================

class SignalBase(BaseModel):
    pair: str = Field(..., max_length=20)
    direction: SignalDirection
    entry_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    tp1: Optional[Decimal] = None
    tp2: Optional[Decimal] = None
    tp3: Optional[Decimal] = None
    timeframe: Optional[str] = Field(None, max_length=10)
    analysis: Optional[str] = None
    chart_image_url: Optional[str] = None
    is_premium: bool = False

class SignalCreate(SignalBase):
    pass

class SignalUpdate(BaseModel):
    pair: Optional[str] = None
    direction: Optional[SignalDirection] = None
    entry_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    tp1: Optional[Decimal] = None
    tp2: Optional[Decimal] = None
    tp3: Optional[Decimal] = None
    timeframe: Optional[str] = None
    analysis: Optional[str] = None
    chart_image_url: Optional[str] = None
    is_premium: Optional[bool] = None
    status: Optional[SignalStatus] = None
    tp1_hit: Optional[bool] = None
    tp2_hit: Optional[bool] = None
    tp3_hit: Optional[bool] = None
    sl_hit: Optional[bool] = None
    pips_gained: Optional[Decimal] = None

class SignalResponse(SignalBase):
    id: int
    risk_reward_ratio: Optional[str] = None
    status: SignalStatus
    tp1_hit: bool
    tp2_hit: bool
    tp3_hit: bool
    sl_hit: bool
    pips_gained: Optional[Decimal] = None
    accuracy_rating: Optional[Decimal] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    hit_date: Optional[datetime] = None
    author: Optional[UserMinimal] = None
    
    class Config:
        orm_mode = True

class SignalListResponse(BaseModel):
    signals: List[SignalResponse]
    total: int
    page: int
    pages: int

# ============================================================================
# COURSE SCHEMAS
# ============================================================================

class CourseBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    thumbnail: Optional[str] = None
    level: CourseLevel = CourseLevel.beginner
    duration_hours: Optional[Decimal] = None
    is_premium: bool = False
    status: CourseStatus = CourseStatus.draft
    price: Decimal = Decimal('0.00')
    currency: str = Field(default='USD', max_length=3)
    category: Optional[str] = None
    tags: List[str] = []
    prerequisites: List[str] = []
    learning_outcomes: List[str] = []

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    thumbnail: Optional[str] = None
    level: Optional[CourseLevel] = None
    duration_hours: Optional[Decimal] = None
    is_premium: Optional[bool] = None
    status: Optional[CourseStatus] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    learning_outcomes: Optional[List[str]] = None

class CourseResponse(CourseBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    author: Optional[UserMinimal] = None
    total_lessons: Optional[int] = 0
    total_modules: Optional[int] = 0
    enrolled_count: Optional[int] = 0
    
    class Config:
        orm_mode = True

class CourseDetailResponse(CourseResponse):
    modules: List['ModuleResponse'] = []
    is_enrolled: Optional[bool] = False
    progress_percent: Optional[int] = 0
    completed_lessons: Optional[int] = 0

# ============================================================================
# MODULE SCHEMAS
# ============================================================================

class ModuleBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    sort_order: int = 0
    is_premium: bool = False
    is_published: bool = True

class ModuleCreate(ModuleBase):
    pass

class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_premium: Optional[bool] = None
    is_published: Optional[bool] = None

class ModuleResponse(ModuleBase):
    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime
    lesson_count: Optional[int] = 0
    total_duration: Optional[int] = 0
    lessons: Optional[List['LessonMinimal']] = []
    quiz: Optional['QuizMinimal'] = None
    
    class Config:
        orm_mode = True

class ModuleMinimal(BaseModel):
    id: int
    title: str
    sort_order: int
    
    class Config:
        orm_mode = True

# ============================================================================
# LESSON SCHEMAS
# ============================================================================

class LessonBase(BaseModel):
    title: str = Field(..., max_length=255)
    content: Optional[str] = None
    video_url: Optional[str] = None
    video_type: VideoType = VideoType.upload
    video_duration_seconds: Optional[int] = None
    pdf_url: Optional[str] = None
    pdf_pages: Optional[int] = None
    images: List[str] = []
    audio_url: Optional[str] = None
    external_links: Optional[Dict[str, Any]] = None
    downloadable_resources: Optional[Dict[str, Any]] = None
    sort_order: int = 0
    duration_minutes: Optional[int] = None
    is_premium: bool = False
    is_preview: bool = False
    pass_mcq_required: bool = False

class LessonCreate(LessonBase):
    pass

class LessonUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    video_url: Optional[str] = None
    video_type: Optional[VideoType] = None
    video_duration_seconds: Optional[int] = None
    pdf_url: Optional[str] = None
    pdf_pages: Optional[int] = None
    images: Optional[List[str]] = None
    audio_url: Optional[str] = None
    external_links: Optional[Dict[str, Any]] = None
    downloadable_resources: Optional[Dict[str, Any]] = None
    sort_order: Optional[int] = None
    duration_minutes: Optional[int] = None
    is_premium: Optional[bool] = None
    is_preview: Optional[bool] = None
    pass_mcq_required: Optional[bool] = None

class LessonMinimal(BaseModel):
    id: int
    title: str
    sort_order: int
    duration_minutes: Optional[int] = None
    is_premium: bool
    is_preview: bool
    is_completed: Optional[bool] = False
    
    class Config:
        orm_mode = True

class LessonResponse(LessonBase):
    id: int
    module_id: int
    created_at: datetime
    updated_at: datetime
    is_completed: Optional[bool] = False
    prev_lesson: Optional[int] = None
    next_lesson: Optional[int] = None
    questions: List['StudentQuestionResponse'] = []
    
    class Config:
        orm_mode = True

# ============================================================================
# QUIZ SCHEMAS
# ============================================================================

class QuestionCreate(BaseModel):
    question_text: str
    question_type: QuestionType = QuestionType.multiple_choice
    options: Optional[Dict[str, Any]] = None
    correct_answer: str
    correct_answers: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    hint: Optional[str] = None
    points: int = 1
    sort_order: int = 0
    image_url: Optional[str] = None

class QuestionResponse(QuestionCreate):
    id: int
    quiz_id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class QuizBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    passing_score: int = Field(default=70, ge=0, le=100)
    time_limit_minutes: Optional[int] = None
    max_attempts: int = 3
    shuffle_questions: bool = True
    show_correct_answers: bool = True
    is_published: bool = False

class QuizCreate(QuizBase):
    questions: List[QuestionCreate] = []

class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    passing_score: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    max_attempts: Optional[int] = None
    shuffle_questions: Optional[bool] = None
    show_correct_answers: Optional[bool] = None
    is_published: Optional[bool] = None

class QuizMinimal(BaseModel):
    id: int
    title: str
    passing_score: int
    time_limit_minutes: Optional[int] = None
    max_attempts: int
    
    class Config:
        orm_mode = True

class QuizResponse(QuizBase):
    id: int
    module_id: int
    created_at: datetime
    updated_at: datetime
    questions: List[QuestionResponse] = []
    attempts: List['QuizAttemptResponse'] = []
    
    class Config:
        orm_mode = True

class QuizSubmit(BaseModel):
    answers: Dict[str, str]  # {question_id: answer}
    time_taken: int = 0  # seconds

class QuizAttemptResponse(BaseModel):
    id: int
    quiz_id: int
    user_id: int
    answers: Optional[Dict[str, Any]] = None
    score: Optional[int] = None
    max_score: Optional[int] = None
    percentage: Optional[Decimal] = None
    passed: bool
    attempt_number: int
    time_taken_seconds: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class QuizResult(BaseModel):
    attempt_id: int
    score: int
    max_score: int
    percentage: float
    passed: bool
    attempt_number: int

# ============================================================================
# STUDENT PROGRESS SCHEMAS
# ============================================================================

class ProgressUpdate(BaseModel):
    progress_percent: int = Field(..., ge=0, le=100)
    time_spent_minutes: Optional[int] = None
    notes: Optional[str] = None

class ProgressResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    module_id: int
    lesson_id: int
    completed: bool
    completed_at: Optional[datetime] = None
    last_accessed: datetime
    progress_percent: int
    time_spent_minutes: int
    notes: Optional[str] = None
    
    class Config:
        orm_mode = True

# ============================================================================
# ENROLLMENT SCHEMAS
# ============================================================================

class EnrollmentCreate(BaseModel):
    course_id: int

class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    enrolled_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    payment_status: PaymentStatus
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    price_paid: Optional[Decimal] = None
    
    class Config:
        orm_mode = True

# ============================================================================
# STUDENT QUESTION SCHEMAS
# ============================================================================

class StudentQuestionCreate(BaseModel):
    question: str
    question_type: QuestionCategory = QuestionCategory.general

class StudentQuestionUpdate(BaseModel):
    answer: str

class StudentQuestionResponse(BaseModel):
    id: int
    lesson_id: int
    user_id: int
    question: str
    question_type: QuestionCategory
    answer: Optional[str] = None
    answered_by: Optional[int] = None
    is_answered: bool
    is_public: bool
    upvotes: int
    created_at: datetime
    answered_at: Optional[datetime] = None
    updated_at: datetime
    student_name: Optional[str] = None
    answered_by_name: Optional[str] = None
    
    class Config:
        orm_mode = True

# ============================================================================
# BLOG SCHEMAS
# ============================================================================

class BlogMediaBase(BaseModel):
    filename: str
    url: str
    caption: Optional[str] = None
    alt_text: Optional[str] = None
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    dimensions: Optional[str] = None
    sort_order: int = 0
    is_featured: bool = False

class BlogMediaResponse(BlogMediaBase):
    id: int
    post_id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class BlogSEOBase(BaseModel):
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    focus_keyword: Optional[str] = None
    secondary_keywords: List[str] = []
    slug: Optional[str] = None
    canonical_url: Optional[str] = None
    schema_markup: Optional[Dict[str, Any]] = None
    seo_score: int = 0
    keyword_density: Optional[Decimal] = None
    readability_score: Optional[int] = None

class BlogSEOResponse(BlogSEOBase):
    id: int
    post_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class BlogPostBase(BaseModel):
    title: str = Field(..., max_length=255)
    content: str
    excerpt: Optional[str] = None
    category: str = Field(default='General', max_length=50)
    tags: List[str] = []
    is_premium: bool = False
    featured_image: Optional[str] = None
    reading_time_minutes: Optional[int] = None
    is_featured: bool = False
    allow_comments: bool = True
    meta_keywords: List[str] = []

class BlogPostCreate(BlogPostBase):
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    focus_keyword: Optional[str] = None
    secondary_keywords: List[str] = []
    slug: Optional[str] = None
    canonical_url: Optional[str] = None
    schema_markup: Optional[Dict[str, Any]] = None
    status: BlogStatus = BlogStatus.draft

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[BlogStatus] = None
    is_premium: Optional[bool] = None
    featured_image: Optional[str] = None
    reading_time_minutes: Optional[int] = None
    is_featured: Optional[bool] = None
    allow_comments: Optional[bool] = None
    meta_keywords: Optional[List[str]] = None

class BlogPostMinimal(BaseModel):
    id: int
    title: str
    excerpt: Optional[str] = None
    category: str
    featured_image: Optional[str] = None
    views: int
    likes: int
    created_at: datetime
    author_name: Optional[str] = None
    slug: Optional[str] = None
    
    class Config:
        orm_mode = True

class BlogPostResponse(BlogPostBase):
    id: int
    author_id: Optional[int] = None
    status: BlogStatus
    views: int
    likes: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    author_name: Optional[str] = None
    media: List[BlogMediaResponse] = []
    seo: Optional[BlogSEOResponse] = None
    related_posts: List[BlogPostMinimal] = []
    
    class Config:
        orm_mode = True

class BlogListResponse(BaseModel):
    posts: List[BlogPostMinimal]
    total: int
    page: int
    pages: int

# ============================================================================
# WEBINAR SCHEMAS
# ============================================================================

class WebinarBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int = 60
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
    status: Optional[WebinarStatus] = None
    recording_url: Optional[str] = None

class WebinarResponse(WebinarBase):
    id: int
    recording_url: Optional[str] = None
    current_participants: int
    reminder_sent: bool
    status: WebinarStatus
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_registered: Optional[bool] = False
    
    class Config:
        orm_mode = True

class WebinarRegistrationResponse(BaseModel):
    id: int
    webinar_id: int
    user_id: int
    registered_at: datetime
    reminder_sent: bool
    attended: bool
    attended_at: Optional[datetime] = None
    feedback_rating: Optional[int] = None
    feedback_comment: Optional[str] = None
    
    class Config:
        orm_mode = True

# ============================================================================
# SETTINGS SCHEMAS
# ============================================================================

class SettingBase(BaseModel):
    key: str = Field(..., max_length=255)
    value: str
    data_type: str = Field(default='string', regex='^(string|integer|boolean|json|array)$')
    category: str = Field(default='general', regex='^(general|email|payment|telegram|security)$')
    description: Optional[str] = None
    is_editable: bool = True

class SettingUpdate(BaseModel):
    value: str

class SettingResponse(SettingBase):
    id: int
    updated_at: datetime
    
    class Config:
        orm_mode = True

# ============================================================================
# ACTIVITY LOG SCHEMAS
# ============================================================================

class ActivityLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

# ============================================================================
# GENERIC RESPONSE SCHEMAS
# ============================================================================

class MessageResponse(BaseModel):
    message: str
    success: bool = True

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    pages: int
    per_page: int

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # minutes

class DashboardStats(BaseModel):
    total_users: int
    total_signals: int
    active_signals: int
    total_courses: int
    published_courses: int
    total_lessons: int
    total_quizzes: int
    total_blog_posts: int
    total_webinars: int
    total_enrollments: int
    pending_questions: int
    recent_activities: List[ActivityLogResponse] = []

# Forward references for nested models
CourseDetailResponse.update_forward_refs()
ModuleResponse.update_forward_refs()
LessonResponse.update_forward_refs()
QuizResponse.update_forward_refs()
