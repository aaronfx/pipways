"""
Database configuration - PRODUCTION READY
Contains all table definitions needed by the application
"""
import os
import sys
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, Text, Float, inspect, ForeignKey
from databases import Database
from datetime import datetime

# Database URL handling
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("[WARNING] DATABASE_URL not set, using default", flush=True)
    DATABASE_URL = "postgresql://user:pass@localhost/pipways"

# Convert to async format
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

print(f"[DB] Using database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}", flush=True)

# Create database instance with connection pooling
database = Database(
    DATABASE_URL, 
    min_size=5,
    max_size=20,
    command_timeout=60
)

# SQLAlchemy metadata
metadata = MetaData()

# ==========================================
# TABLE DEFINITIONS
# ==========================================

# Users table
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(255), unique=True, index=True, nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("full_name", String(255), default=""),
    Column("is_active", Boolean, default=True),
    Column("is_admin", Boolean, default=False),
    Column("role", String(50), default="user"),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("subscription_tier", String(50), default="free")
)

# Courses table - THIS WAS MISSING
courses_table = Table(
    "courses",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(255), nullable=False),
    Column("description", Text, default=""),
    Column("level", String(50), default="beginner"),  # beginner, intermediate, advanced
    Column("lesson_count", Integer, default=0),
    Column("is_active", Boolean, default=True),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column("instructor", String(255), default=""),
    Column("thumbnail_url", String(500), default="")
)

# Webinars table
webinars_table = Table(
    "webinars",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(255), nullable=False),
    Column("description", Text, default=""),
    Column("scheduled_at", DateTime),
    Column("status", String(50), default="scheduled"),  # scheduled, live, recorded, cancelled
    Column("duration_minutes", Integer, default=60),
    Column("recording_url", String(500), default=""),
    Column("presenter", String(255), default=""),
    Column("created_at", DateTime, default=datetime.utcnow)
)

# Blog posts table
blog_posts = Table(
    "blog_posts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(255), nullable=False),
    Column("slug", String(255), unique=True, index=True, nullable=False),
    Column("content", Text, default=""),
    Column("excerpt", String(500), default=""),
    Column("category", String(100), default="General"),
    Column("featured", Boolean, default=False),
    Column("status", String(50), default="draft"),  # draft, published, archived
    Column("read_time", String(20), default="5 min"),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column("author_id", Integer, ForeignKey("users.id"), nullable=True)
)

# Trading signals table
signals = Table(
    "signals",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("symbol", String(20), nullable=False),
    Column("direction", String(10), nullable=False),  # BUY or SELL
    Column("entry_price", Float, nullable=False),
    Column("stop_loss", Float, nullable=False),
    Column("take_profit", Float, nullable=False),
    Column("timeframe", String(10), default="1H"),
    Column("status", String(20), default="active"),  # active, closed, cancelled
    Column("ai_confidence", Float, default=None),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("closed_at", DateTime, nullable=True),
    Column("result_pips", Float, nullable=True)
)

# User progress table (for courses)
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

# Security constants
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    print("[SECURITY WARNING] SECRET_KEY not set, using default. CHANGE IN PRODUCTION!", flush=True)
    SECRET_KEY = "your-secret-key-change-in-production-immediately"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

_cached_columns = None

def get_available_columns(table_name='users'):
    """
    Get list of actually available columns in the database table.
    """
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
        print("[DB] Database initialized", flush=True)
    except Exception as e:
        print(f"[DB FATAL] Could not connect: {e}", flush=True)
        raise
