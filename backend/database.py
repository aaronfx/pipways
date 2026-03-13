"""
Database configuration - PRODUCTION READY
Contains all table definitions for core + enhanced features
"""
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, inspect
from databases import Database
from datetime import datetime

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/pipways")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

print(f"[DB] Connecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}", flush=True)

database = Database(DATABASE_URL, min_size=5, max_size=20, command_timeout=60)
metadata = MetaData()

# ==========================================
# CORE TABLES
# ==========================================

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(255), unique=True, nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("full_name", String(255), default=""),
    Column("is_active", Boolean, default=True),
    Column("is_admin", Boolean, default=False),
    Column("role", String(50), default="user"),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("subscription_tier", String(50), default="free")
)

courses_table = Table(
    "courses",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(255), nullable=False),
    Column("description", Text, default=""),
    Column("level", String(50), default="beginner"),
    Column("lesson_count", Integer, default=0),
    Column("is_active", Boolean, default=True),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column("instructor", String(255), default=""),
    Column("thumbnail_url", String(500), default="")
)

webinars_table = Table(
    "webinars",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(255), nullable=False),
    Column("description", Text, default=""),
    Column("scheduled_at", DateTime),
    Column("status", String(50), default="scheduled"),
    Column("duration_minutes", Integer, default=60),
    Column("recording_url", String(500), default=""),
    Column("presenter", String(255), default=""),
    Column("created_at", DateTime, default=datetime.utcnow)
)

blog_posts = Table(
    "blog_posts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(255), nullable=False),
    Column("slug", String(255), unique=True, nullable=False),
    Column("content", Text, default=""),
    Column("excerpt", String(500), default=""),
    Column("category", String(100), default="General"),
    Column("featured", Boolean, default=False),
    Column("status", String(50), default="published"),
    Column("read_time", String(20), default="5 min"),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column("author_id", Integer, ForeignKey("users.id"), nullable=True),
    # SEO fields for enhanced blog
    Column("seo_description", Text, default=""),
    Column("seo_keywords", String(500), default=""),
    Column("og_image_url", String(500), default="")
)

signals = Table(
    "signals",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("symbol", String(20), nullable=False),
    Column("direction", String(10), nullable=False),
    Column("entry_price", Float, nullable=False),
    Column("stop_loss", Float, nullable=False),
    Column("take_profit", Float, nullable=False),
    Column("timeframe", String(10), default="1H"),
    Column("status", String(20), default="active"),
    Column("ai_confidence", Float, default=None),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("closed_at", DateTime, nullable=True),
    Column("result_pips", Float, nullable=True)
)

user_progress = Table(
    "user_progress",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("course_id", Integer, ForeignKey("courses.id"), nullable=False),
    Column("progress_percent", Integer, default=0),
    Column("completed_lessons", Integer, default=0),
    Column("last_accessed", DateTime, default=datetime.utcnow),
    Column("completed_at", DateTime, nullable=True)
)

# ==========================================
# ENHANCED BLOG TABLES
# ==========================================

blog_comments = Table(
    "blog_comments",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("post_id", Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("content", Text, nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column("status", String(20), default="published")  # published, deleted, flagged
)

blog_tags = Table(
    "blog_tags",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(50), unique=True, nullable=False),
    Column("slug", String(50), unique=True, nullable=False),
    Column("description", String(255), default="")
)

blog_post_tags = Table(
    "blog_post_tags",
    metadata,
    Column("post_id", Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False),
    Column("tag_id", Integer, ForeignKey("blog_tags.id", ondelete="CASCADE"), nullable=False)
)

# ==========================================
# ENHANCED COURSES TABLES
# ==========================================

course_lessons = Table(
    "course_lessons",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("course_id", Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
    Column("title", String(255), nullable=False),
    Column("content", Text, default=""),
    Column("video_url", String(500), default=""),
    Column("duration_minutes", Integer, default=0),
    Column("sort_order", Integer, default=0),
    Column("is_active", Boolean, default=True)
)

user_lesson_progress = Table(
    "user_lesson_progress",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("lesson_id", Integer, ForeignKey("course_lessons.id"), nullable=False),
    Column("completed_at", DateTime, default=datetime.utcnow),
    Column("time_spent_seconds", Integer, default=0)
)

certificates = Table(
    "certificates",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("course_id", Integer, ForeignKey("courses.id"), nullable=False),
    Column("certificate_number", String(100), unique=True, nullable=False),
    Column("issued_at", DateTime, default=datetime.utcnow),
    Column("pdf_url", String(500), default="")
)

# ==========================================
# SECURITY & UTILITIES
# ==========================================

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

_cached_columns = None

def get_available_columns(table_name='users'):
    """Get list of actually available columns in the database table."""
    global _cached_columns
    
    if _cached_columns is not None:
        return _cached_columns
    
    try:
        sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        engine = create_engine(sync_url, pool_pre_ping=True)
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        _cached_columns = [col['name'] for col in columns]
        print(f"[DB] Discovered columns: {_cached_columns}", flush=True)
        return _cached_columns
    except Exception as e:
        print(f"[DB ERROR] Could not inspect columns: {e}", flush=True)
        return [col.name for col in users.columns]

async def init_database():
    """Initialize database connection."""
    try:
        await database.connect()
        print("[DB] Database initialized successfully", flush=True)
    except Exception as e:
        print(f"[DB FATAL] Could not connect: {e}", flush=True)
        raise
