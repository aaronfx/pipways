"""
Database Configuration
"""
import os
import logging
import asyncpg
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI

logger = logging.getLogger(__name__)

# Global database pool
db_pool: Optional[asyncpg.Pool] = None

# Config
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-min-32-chars-long")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@pipways.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

async def init_database_pool():
    """Initialize the database connection pool"""
    global db_pool
    
    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable not set!")
        raise ValueError("DATABASE_URL not configured")
    
    try:
        dsn = DATABASE_URL
        if "render.com" in dsn and "sslmode" not in dsn:
            dsn += "?sslmode=require"
        
        logger.info(f"Connecting to database...")
        db_pool = await asyncpg.create_pool(
            dsn, 
            min_size=2, 
            max_size=10,
            command_timeout=60,
            server_settings={'jit': 'off'}
        )
        logger.info("Database pool initialized successfully")
    except Exception as e:
        logger.error(f"Database pool initialization error: {e}")
        raise

async def close_database_pool():
    """Close the database connection pool"""
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")

async def init_db():
    """Initialize database tables"""
    import bcrypt
    
    if not db_pool:
        raise RuntimeError("Database pool not initialized")
    
    async with db_pool.acquire() as conn:
        # Users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                subscription_tier VARCHAR(20) DEFAULT 'free',
                subscription_status VARCHAR(20) DEFAULT 'inactive',
                email_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                reset_token VARCHAR(255),
                reset_token_expires TIMESTAMP
            )
        """)
        
        # Create default admin
        try:
            admin_exists = await conn.fetchval("SELECT id FROM users WHERE email = $1", ADMIN_EMAIL)
            if not admin_exists:
                logger.info(f"Creating default admin user: {ADMIN_EMAIL}")
                hashed = bcrypt.hashpw(ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
                await conn.execute("""
                    INSERT INTO users (email, password_hash, full_name, role, subscription_tier, subscription_status, email_verified)
                    VALUES ($1, $2, 'System Administrator', 'admin', 'vip', 'active', TRUE)
                """, ADMIN_EMAIL, hashed)
                logger.info("Default admin created")
        except Exception as e:
            logger.error(f"Error creating admin: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    try:
        await init_database_pool()
        await init_db()
        yield
    except Exception as e:
        logger.error(f"Lifespan error: {e}")
        raise
    finally:
        await close_database_pool()
