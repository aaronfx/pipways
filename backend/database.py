"""
Database configuration and connection handling.
"""
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from databases import Database

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/pipways")

# Convert to async format if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# SQLAlchemy components
engine = create_async_engine(DATABASE_URL)
metadata = MetaData()
database = Database(DATABASE_URL)

# Table definitions (simplified)
from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime, Text

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(255), unique=True, index=True),
    Column("password_hash", String(255)),
    Column("is_active", Boolean, default=True),
    Column("is_admin", Boolean, default=False),
    Column("created_at", DateTime),
)

# Security constants
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day
