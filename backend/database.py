"""
Database Configuration and Connection Pool Management
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

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-min-32-chars-long")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@pipways.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

async def init_database_pool():
    """Initialize the database connection pool"""
    global db_pool
    try:
        if not DATABASE_URL:
            logger.error("DATABASE_URL environment variable is not set!")
            raise ValueError("DATABASE_URL is required - check Render environment variables")
        
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
        logger.error(f"Failed to initialize database pool: {e}")
        db_pool = None
        raise

async def close_database_pool():
    """Close the database connection pool"""
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")
        db_pool = None

async def init_db():
    """Initialize database tables"""
    import bcrypt
    
    if not db_pool:
        logger.error("Cannot initialize DB - pool is None")
        return
    
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
        
        # Blog posts
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                excerpt TEXT,
                author_id INTEGER REFERENCES users(id),
                is_premium BOOLEAN DEFAULT FALSE,
                status VARCHAR(20) DEFAULT 'published',
                scheduled_at TIMESTAMP,
                slug VARCHAR(255) UNIQUE,
                featured_image VARCHAR(500),
                tags TEXT[],
                category VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                published_at TIMESTAMP
            )
        """)
        
        # Signals
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id SERIAL PRIMARY KEY,
                pair VARCHAR(20) NOT NULL,
                direction VARCHAR(10) NOT NULL,
                entry_price DECIMAL(10,5),
                stop_loss DECIMAL(10,5),
                tp1 DECIMAL(10,5),
                tp2 DECIMAL(10,5),
                risk_reward_ratio TEXT,
                expires_at TIMESTAMP,
                timeframe VARCHAR(20),
                analysis TEXT,
                status VARCHAR(20) DEFAULT 'active',
                result VARCHAR(20),
                pips_gain DECIMAL(10,2),
                is_premium BOOLEAN DEFAULT FALSE,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP
            )
        """)
        
        # Webinars
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS webinars (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                scheduled_at TIMESTAMP NOT NULL,
                duration_minutes INTEGER DEFAULT 60,
                meeting_link VARCHAR(500),
                is_premium BOOLEAN DEFAULT FALSE,
                max_participants INTEGER DEFAULT 100,
                reminder_message TEXT,
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Courses
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                content TEXT,
                level VARCHAR(20) DEFAULT 'beginner',
                duration_hours DECIMAL(5,2),
                thumbnail VARCHAR(500),
                is_premium BOOLEAN DEFAULT FALSE,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Course modules
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS course_modules (
                id SERIAL PRIMARY KEY,
                course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                content TEXT,
                video_url VARCHAR(500),
                sort_order INTEGER DEFAULT 0,
                is_premium BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Course quizzes
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS course_quizzes (
                id SERIAL PRIMARY KEY,
                course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                passing_score INTEGER DEFAULT 70,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Quiz questions
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id SERIAL PRIMARY KEY,
                quiz_id INTEGER REFERENCES course_quizzes(id) ON DELETE CASCADE,
                question_text TEXT NOT NULL,
                question_type VARCHAR(20) DEFAULT 'multiple_choice',
                options JSONB,
                correct_answer TEXT NOT NULL,
                points INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Quiz attempts
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id SERIAL PRIMARY KEY,
                quiz_id INTEGER REFERENCES course_quizzes(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                answers JSONB,
                score INTEGER,
                max_score INTEGER,
                percentage DECIMAL(5,2),
                passed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User course progress
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_course_progress (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                module_id INTEGER REFERENCES course_modules(id) ON DELETE CASCADE,
                completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                UNIQUE(user_id, module_id)
            )
        """)
        
        # Chat history - FIXED: Added missing table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Media files - FIXED: Added missing table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS media_files (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                url VARCHAR(500) NOT NULL,
                file_type VARCHAR(50),
                size_bytes INTEGER,
                uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Performance analyses - FIXED: Added missing table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_analyses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                analysis_data JSONB NOT NULL,
                raw_trades JSONB,
                trader_score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Site settings
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS site_settings (
                id SERIAL PRIMARY KEY,
                site_name VARCHAR(255) DEFAULT 'Pipways',
                telegram_free_link VARCHAR(500),
                telegram_vip_link VARCHAR(500),
                vip_price DECIMAL(10,2) DEFAULT 99.00,
                vip_price_currency VARCHAR(3) DEFAULT 'USD',
                seo_default_title VARCHAR(255),
                seo_default_description TEXT,
                contact_email VARCHAR(255),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default settings
        await conn.execute("""
            INSERT INTO site_settings (id, site_name, telegram_free_link, telegram_vip_link, vip_price)
            SELECT 1, 'Pipways', 'https://t.me/pipways_free', 'https://t.me/pipways_vip', 99.00
            WHERE NOT EXISTS (SELECT 1 FROM site_settings WHERE id = 1)
        """)
        
        # Create default admin
        try:
            admin_exists = await conn.fetchval("SELECT id FROM users WHERE email = $1", ADMIN_EMAIL)
            if not admin_exists:
                hashed = bcrypt.hashpw(ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
                await conn.execute("""
                    INSERT INTO users (email, password_hash, full_name, role, subscription_tier, subscription_status, email_verified)
                    VALUES ($1, $2, $3, 'admin', 'vip', 'active', TRUE)
                """, ADMIN_EMAIL, hashed, "System Administrator")
                logger.info(f"Default admin created: {ADMIN_EMAIL}")
        except Exception as e:
            logger.error(f"Error creating admin: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    try:
        await init_database_pool()
        await init_db()
        yield
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    finally:
        await close_database_pool()
