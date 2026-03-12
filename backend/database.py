from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON, ARRAY, Date, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database
import os
from datetime import datetime

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pipways.db")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
metadata = MetaData()
Base = declarative_base()

# Users table
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, unique=True, index=True),
    Column("username", String, unique=True, index=True),
    Column("password_hash", String),
    Column("first_name", String),
    Column("last_name", String),
    Column("phone", String),
    Column("country", String),
    Column("is_active", Boolean, default=True),
    Column("is_admin", Boolean, default=False),
    Column("email_verified", Boolean, default=False),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow),
    Column("last_login", DateTime),
)

# Subscriptions
subscriptions = Table(
    "subscriptions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), unique=True),
    Column("tier", String(20), default="free"),
    Column("status", String(20), default="active"),
    Column("stripe_customer_id", String(100)),
    Column("stripe_subscription_id", String(100)),
    Column("current_period_end", DateTime),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow),
)

# Notification preferences
notification_preferences = Table(
    "notification_preferences",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("channel", String(20)),
    Column("enabled", Boolean, default=True),
    Column("telegram_chat_id", String(100)),
    Column("webhook_url", String(255)),
    Column("phone_number", String(20)),
)

# Signals table
signals = Table(
    "signals",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String),
    Column("description", Text),
    Column("asset", String),
    Column("direction", String),
    Column("entry_price", Float),
    Column("stop_loss", Float),
    Column("take_profit", Float),
    Column("status", String, default="ACTIVE"),
    Column("result", String, default="PENDING"),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow),
    Column("closed_at", DateTime),
)

# Courses table
courses = Table(
    "courses",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String),
    Column("description", Text),
    Column("content", Text),
    Column("category", String),
    Column("level", String),
    Column("price", Float, default=0),
    Column("is_published", Boolean, default=False),
    Column("instructor_id", Integer, ForeignKey("users.id")),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow),
)

# Course quizzes
course_quizzes = Table(
    "course_quizzes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("course_id", Integer, ForeignKey("courses.id")),
    Column("title", String(200)),
    Column("questions", JSON),
    Column("passing_score", Integer, default=70),
    Column("order_index", Integer),
)

# User progress
user_progress = Table(
    "user_progress",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("course_id", Integer, ForeignKey("courses.id")),
    Column("completed_lessons", ARRAY(Integer)),
    Column("quiz_scores", JSON),
    Column("overall_progress", Integer, default=0),
    Column("started_at", DateTime, default=datetime.utcnow),
    Column("completed_at", DateTime),
    Column("certificate_issued", Boolean, default=False),
)

# Blog posts table
blog_posts = Table(
    "blog_posts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String),
    Column("slug", String, unique=True),
    Column("content", Text),
    Column("excerpt", Text),
    Column("featured_image", String),
    Column("category", String),
    Column("tags", JSON),
    Column("author_id", Integer, ForeignKey("users.id")),
    Column("is_published", Boolean, default=False),
    Column("views", Integer, default=0),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow),
)

# Blog SEO metadata
blog_seo_metadata = Table(
    "blog_seo_metadata",
    metadata,
    Column("post_id", Integer, ForeignKey("blog_posts.id"), primary_key=True),
    Column("meta_title", String(70)),
    Column("meta_description", String(160)),
    Column("keywords", ARRAY(String)),
    Column("reading_time_minutes", Integer),
    Column("canonical_url", String(255)),
    Column("featured", Boolean, default=False),
    Column("newsletter_sent", Boolean, default=False),
    Column("unique_view_count", Integer, default=0),
    Column("avg_time_on_page", Float),
)

# Content upgrades
content_upgrades = Table(
    "content_upgrades",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("post_id", Integer, ForeignKey("blog_posts.id")),
    Column("upgrade_type", String(50)),
    Column("title", String(100)),
    Column("file_path", String(255)),
    Column("require_email", Boolean, default=True),
    Column("download_count", Integer, default=0),
    Column("created_at", DateTime, default=datetime.utcnow),
)

# Email captures
email_captures = Table(
    "email_captures",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(255)),
    Column("post_id", Integer, ForeignKey("blog_posts.id")),
    Column("upgrade_id", Integer, ForeignKey("content_upgrades.id")),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=True),
    Column("captured_at", DateTime, default=datetime.utcnow),
    Column("converted_to_paid", Boolean, default=False),
)

# Content calendar
content_calendar = Table(
    "content_calendar",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("post_id", Integer, ForeignKey("blog_posts.id"), nullable=True),
    Column("planned_title", String(200)),
    Column("category", String(50)),
    Column("target_keyword", String(100)),
    Column("assigned_to", Integer, ForeignKey("users.id")),
    Column("status", String(20), default="planned"),
    Column("planned_publish_date", Date),
    Column("newsletter_include", Boolean, default=True),
    Column("social_schedule", JSON),
)

# Webinars table
webinars = Table(
    "webinars",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String),
    Column("description", Text),
    Column("presenter", String),
    Column("scheduled_at", DateTime),
    Column("duration_minutes", Integer),
    Column("meeting_link", String),
    Column("recording_url", String),
    Column("max_participants", Integer),
    Column("is_recorded", Boolean, default=False),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", DateTime, default=datetime.utcnow),
)

# Media files table
media_files = Table(
    "media_files",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("filename", String),
    Column("original_name", String),
    Column("file_path", String),
    Column("file_type", String),
    Column("file_size", Integer),
    Column("mime_type", String),
    Column("uploaded_by", Integer, ForeignKey("users.id")),
    Column("created_at", DateTime, default=datetime.utcnow),
)

# Performance analyses table
performance_analyses = Table(
    "performance_analyses",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("title", String),
    Column("description", Text),
    Column("analysis_data", JSON),
    Column("file_path", String),
    Column("chart_data", JSON),
    Column("metrics", JSON),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow),
)

# Risk calculations
risk_calculations = Table(
    "risk_calculations",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=True),
    Column("signal_id", Integer, ForeignKey("signals.id"), nullable=True),
    Column("account_balance", Float),
    Column("risk_percent", Float),
    Column("entry_price", Float),
    Column("stop_loss", Float),
    Column("position_size", Float),
    Column("max_loss", Float),
    Column("risk_reward_ratio", Float),
    Column("calculated_at", DateTime, default=datetime.utcnow),
)

# AI Screening logs
ai_screening_logs = Table(
    "ai_screening",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("signal_id", Integer, ForeignKey("signals.id")),
    Column("market_condition", String(50)),
    Column("news_sentiment", String(20)),
    Column("volatility_score", Float),
    Column("ai_recommendation", String(20)),
    Column("reasoning", Text),
    Column("screened_at", DateTime, default=datetime.utcnow),
)

# Database connection
database = Database(DATABASE_URL)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Secret key
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
