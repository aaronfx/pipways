"""
Database configuration and initialization.
"""
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, Text
from databases import Database
from datetime import datetime

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/pipways")

# Convert to async format if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create database instance
database = Database(DATABASE_URL)

# SQLAlchemy metadata
metadata = MetaData()

# Users table definition
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

# Security constants
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

async def init_database():
    """Initialize database and create admin user if not exists."""
    from .security import get_password_hash
    
    try:
        # Check if admin exists
        query = users.select().where(users.c.email == "admin@pipways.com")
        existing = await database.fetch_one(query)
        
        if not existing:
            # Create default admin
            admin_data = {
                "email": "admin@pipways.com",
                "password_hash": get_password_hash("admin123"),
                "full_name": "System Administrator",
                "is_active": True,
                "is_admin": True,
                "role": "admin",
                "created_at": datetime.utcnow(),
                "subscription_tier": "admin"
            }
            
            query = users.insert().values(**admin_data)
            await database.execute(query)
            print("✓ Default admin created: admin@pipways.com / admin123")
        else:
            print("✓ Admin user exists")
            
    except Exception as e:
        print(f"⚠ Database initialization error: {e}")
        # Don't raise - let the app start anyway
