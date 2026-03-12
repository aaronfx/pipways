from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ... existing schemas ...

# Course Schemas
class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    level: str = "beginner"
    duration_hours: Optional[float] = None
    is_premium: bool = False
    status: str = "draft"
    thumbnail: Optional[str] = None

class ModuleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    is_premium: bool = False

class LessonCreate(BaseModel):
    title: str
    content: Optional[str] = None
    video_url: Optional[str] = None
    video_type: str = "upload"  # upload, youtube, vimeo
    pdf_url: Optional[str] = None
    images: Optional[List[str]] = []
    duration_minutes: Optional[int] = None
    is_premium: bool = False

# Quiz Schemas
class QuestionCreate(BaseModel):
    question_text: str
    question_type: str = "multiple_choice"
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None
    points: int = 1

class QuizCreate(BaseModel):
    title: str
    description: Optional[str] = None
    passing_score: int = 70
    time_limit_minutes: Optional[int] = None
    max_attempts: int = 3
    questions: List[QuestionCreate]

# Signal Schemas (updated)
class SignalCreate(BaseModel):
    pair: str
    direction: str
    entry_price: float
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    tp3: Optional[float] = None
    timeframe: Optional[str] = None
    analysis: Optional[str] = None
    is_premium: bool = False
    status: str = "active"
