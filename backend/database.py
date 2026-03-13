"""
Database configuration - PRODUCTION READY
"""
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from databases import Database
from datetime import datetime

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/pipways")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

database = Database(DATABASE_URL, min_size=5, max_size=20)
metadata = MetaData()

# ==========================================
# ALL TABLE DEFINITIONS
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

# THIS WAS MISSING - NOW ADDED
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
    Column("instructor", String(255), default="")
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
    Column("author_id", Integer, ForeignKey("users.id"), nullable=True)
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
    Column("created_at", DateTime, default=datetime.utcnow)
)

user_progress = Table(
    "user_progress",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("course_id", Integer, ForeignKey("courses.id"), nullable=False),
    Column("progress_percent", Integer, default=0),
    Column("completed_lessons", Integer, default=0),
    Column("last_accessed", DateTime, default=datetime.utcnow)
)

# Security constants
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
