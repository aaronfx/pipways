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
db_pool: Optional[asyncpg.Pool] = None

# Config
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-min-32-chars-long")

async def init_database_pool():
    global db_pool
    try:
        dsn = DATABASE_URL
        if dsn and "render.com" in dsn and "sslmode" not in dsn:
            dsn += "?sslmode=require"
        
        if not dsn:
            raise ValueError("DATABASE_URL not set")
        
        db_pool = await asyncpg.create_pool(
            dsn,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info("Database pool initialized")
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise

async def close_database_pool():
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")

async def init_db():
    """Initialize database tables"""
    import bcrypt
    
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
        
        # Create default admin if not exists
        try:
            admin_exists = await conn.fetchval("SELECT id FROM users WHERE email = $1", 
                os.getenv("ADMIN_EMAIL", "admin@pipways.com"))
            if not admin_exists:
                hashed = bcrypt.hashpw(
                    os.getenv("ADMIN_PASSWORD", "admin123").encode(), 
                    bcrypt.gensalt()
                ).decode()
                await conn.execute("""
                    INSERT INTO users (email, password_hash, full_name, role, subscription_tier, subscription_status, email_verified)
                    VALUES ($1, $2, 'System Administrator', 'admin', 'vip', 'active', TRUE)
                """, os.getenv("ADMIN_EMAIL", "admin@pipways.com"), hashed)
                logger.info("Default admin created")
        except Exception as e:
            logger.error(f"Admin creation error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database_pool()
    await init_db()
    yield
    await close_database_pool()
