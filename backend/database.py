"""
Database Module - Complete Setup for Pipways Trading Platform
PostgreSQL + asyncpg implementation
"""

import asyncpg
import asyncio
import logging
from typing import Optional, List, Dict, Any, Union, AsyncGenerator
from datetime import datetime
import os
import json
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# SECURITY CONFIGURATION (Imported by auth.py)
# ============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production-min-32-chars")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Global connection pool
db_pool: Optional[asyncpg.Pool] = None

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'database': os.getenv('DB_NAME', 'pipways'),
    'min_size': 5,
    'max_size': 20,
    'command_timeout': 60,
    'server_settings': {'jit': 'off'}
}

async def init_db_pool():
    """Initialize database connection pool"""
    global db_pool
    
    if db_pool:
        return db_pool
    
    try:
        dsn = os.getenv('DATABASE_URL')
        if dsn:
            db_pool = await asyncpg.create_pool(dsn, min_size=5, max_size=20, command_timeout=60)
        else:
            db_pool = await asyncpg.create_pool(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database'],
                min_size=DB_CONFIG['min_size'],
                max_size=DB_CONFIG['max_size'],
                command_timeout=DB_CONFIG['command_timeout'],
                server_settings=DB_CONFIG['server_settings']
            )
        
        logger.info("Database pool initialized")
        return db_pool
    except Exception as e:
        logger.error(f"Database pool init failed: {e}")
        raise

async def close_db_pool():
    """Close database pool"""
    global db_pool
    if db_pool:
        await db_pool.close()
        db_pool = None
        logger.info("Database pool closed")

@asynccontextmanager
async def get_connection():
    """Context manager for database connections"""
    if not db_pool:
        await init_db_pool()
    
    conn = await db_pool.acquire()
    try:
        yield conn
    finally:
        await db_pool.release(conn)

async def execute(query: str, *args):
    """Execute query without return"""
    async with get_connection() as conn:
        return await conn.execute(query, *args)

async def fetch(query: str, *args) -> List[asyncpg.Record]:
    """Fetch multiple rows"""
    async with get_connection() as conn:
        return await conn.fetch(query, *args)

async def fetchrow(query: str, *args) -> Optional[asyncpg.Record]:
    """Fetch single row"""
    async with get_connection() as conn:
        return await conn.fetchrow(query, *args)

async def fetchval(query: str, *args):
    """Fetch single value"""
    async with get_connection() as conn:
        return await conn.fetchval(query, *args)

# ============================================================================
# LIFESPAN CONTEXT MANAGER (for FastAPI startup/shutdown)
# ============================================================================

@asynccontextmanager
async def lifespan(app) -> AsyncGenerator:
    """
    FastAPI lifespan context manager.
    Handles database initialization on startup and cleanup on shutdown.
    """
    # Startup
    logger.info("Starting up database...")
    try:
        await init_db_pool()
        await init_db()
        logger.info("Database startup complete")
    except Exception as e:
        logger.error(f"Database startup failed: {e}")
        raise
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down database...")
    await close_db_pool()
    logger.info("Database shutdown complete")

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

async def column_exists(conn, table: str, column: str) -> bool:
    """Check if a column exists in a table"""
    result = await conn.fetchval("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = $1 AND column_name = $2
        )
    """, table, column)
    return result

async def table_exists(conn, table: str) -> bool:
    """Check if a table exists"""
    result = await conn.fetchval("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = $1
        )
    """, table)
    return result

async def init_db():
    """Initialize all database tables with indexes"""
    if not db_pool:
        await init_db_pool()
    
    async with db_pool.acquire() as conn:
        await conn.execute("SET timezone TO 'UTC'")
        
        # 1. USERS TABLE
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'moderator', 'admin')),
                subscription_tier VARCHAR(20) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'vip')),
                is_active BOOLEAN DEFAULT TRUE,
                email_verified BOOLEAN DEFAULT FALSE,
                avatar_url VARCHAR(500),
                phone VARCHAR(20),
                country VARCHAR(100),
                trading_experience VARCHAR(50),
                preferred_pairs TEXT[],
                telegram_username VARCHAR(100),
                notification_settings JSONB DEFAULT '{"email": true, "telegram": false}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
            CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(subscription_tier);
        """)
        
        # 2. SIGNALS TABLE (Enhanced)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id SERIAL PRIMARY KEY,
                pair VARCHAR(20) NOT NULL,
                direction VARCHAR(10) NOT NULL CHECK (direction IN ('buy', 'sell')),
                entry_price DECIMAL(15,5),
                stop_loss DECIMAL(15,5),
                tp1 DECIMAL(15,5),
                tp2 DECIMAL(15,5),
                tp3 DECIMAL(15,5),
                timeframe VARCHAR(10),
                risk_reward_ratio VARCHAR(20),
                analysis TEXT,
                chart_image_url VARCHAR(500),
                is_premium BOOLEAN DEFAULT FALSE,
                status VARCHAR(20) DEFAULT 'active' CHECK (
                    status IN ('active', 'tp1_hit', 'tp2_hit', 'tp3_hit', 'sl_hit', 'closed', 'expired', 'cancelled')
                ),
                tp1_hit BOOLEAN DEFAULT FALSE,
                tp2_hit BOOLEAN DEFAULT FALSE,
                tp3_hit BOOLEAN DEFAULT FALSE,
                sl_hit BOOLEAN DEFAULT FALSE,
                pips_gained DECIMAL(10,2),
                accuracy_rating DECIMAL(3,2),
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                expired_at TIMESTAMP,
                hit_date TIMESTAMP
            )
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_signals_pair ON signals(pair);
            CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
            CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_signals_premium ON signals(is_premium);
        """)
        
        # 3. COURSES TABLE
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                short_description VARCHAR(500),
                thumbnail VARCHAR(500),
                level VARCHAR(20) DEFAULT 'beginner' CHECK (level IN ('beginner', 'intermediate', 'advanced', 'expert')),
                duration_hours DECIMAL(5,2),
                is_premium BOOLEAN DEFAULT FALSE,
                status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
                price DECIMAL(10,2) DEFAULT 0,
                currency VARCHAR(3) DEFAULT 'USD',
                category VARCHAR(50),
                tags TEXT[],
                prerequisites TEXT[],
                learning_outcomes TEXT[],
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                published_at TIMESTAMP
            )
        """)
        
        # 4. COURSE MODULES
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS course_modules (
                id SERIAL PRIMARY KEY,
                course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                sort_order INTEGER DEFAULT 0,
                is_premium BOOLEAN DEFAULT FALSE,
                is_published BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_modules_course ON course_modules(course_id);
            CREATE INDEX IF NOT EXISTS idx_modules_order ON course_modules(sort_order);
        """)
        
        # 5. LESSONS
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id SERIAL PRIMARY KEY,
                module_id INTEGER REFERENCES course_modules(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                content TEXT,
                video_url VARCHAR(500),
                video_type VARCHAR(20) DEFAULT 'upload' CHECK (video_type IN ('upload', 'youtube', 'vimeo', 'embed')),
                video_duration_seconds INTEGER,
                pdf_url VARCHAR(500),
                pdf_pages INTEGER,
                images TEXT[],
                audio_url VARCHAR(500),
                external_links JSONB,
                downloadable_resources JSONB,
                sort_order INTEGER DEFAULT 0,
                duration_minutes INTEGER,
                is_premium BOOLEAN DEFAULT FALSE,
                is_preview BOOLEAN DEFAULT FALSE,
                pass_mcq_required BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_lessons_module ON lessons(module_id);
            CREATE INDEX IF NOT EXISTS idx_lessons_order ON lessons(sort_order);
        """)
        
        # 6. STUDENT PROGRESS
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS student_progress (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                module_id INTEGER REFERENCES course_modules(id) ON DELETE CASCADE,
                lesson_id INTEGER REFERENCES lessons(id) ON DELETE CASCADE,
                completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                progress_percent INTEGER DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
                time_spent_minutes INTEGER DEFAULT 0,
                notes TEXT,
                UNIQUE(user_id, lesson_id)
            )
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_progress_user ON student_progress(user_id);
            CREATE INDEX IF NOT EXISTS idx_progress_course ON student_progress(course_id);
            CREATE INDEX IF NOT EXISTS idx_progress_lesson ON student_progress(lesson_id);
        """)
        
        # 7. ENROLLMENTS
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS enrollments (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                payment_status VARCHAR(20) DEFAULT 'free' CHECK (payment_status IN ('free', 'pending', 'completed', 'failed', 'refunded')),
                payment_method VARCHAR(50),
                transaction_id VARCHAR(255),
                price_paid DECIMAL(10,2),
                UNIQUE(user_id, course_id)
            )
        """)
        
        # 8. QUIZZES
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
                id SERIAL PRIMARY KEY,
                module_id INTEGER REFERENCES course_modules(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                instructions TEXT,
                passing_score INTEGER DEFAULT 70 CHECK (passing_score >= 0 AND passing_score <= 100),
                time_limit_minutes INTEGER,
                max_attempts INTEGER DEFAULT 3,
                shuffle_questions BOOLEAN DEFAULT TRUE,
                show_correct_answers BOOLEAN DEFAULT TRUE,
                is_published BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 9. QUIZ QUESTIONS
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id SERIAL PRIMARY KEY,
                quiz_id INTEGER REFERENCES quizzes(id) ON DELETE CASCADE,
                question_text TEXT NOT NULL,
                question_type VARCHAR(20) DEFAULT 'multiple_choice' CHECK (
                    question_type IN ('multiple_choice', 'true_false', 'fill_blank', 'matching', 'essay')
                ),
                options JSONB,
                correct_answer VARCHAR(255) NOT NULL,
                correct_answers JSONB,
                explanation TEXT,
                hint TEXT,
                points INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                image_url VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 10. QUIZ ATTEMPTS
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id SERIAL PRIMARY KEY,
                quiz_id INTEGER REFERENCES quizzes(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                answers JSONB,
                score INTEGER,
                max_score INTEGER,
                percentage DECIMAL(5,2),
                passed BOOLEAN DEFAULT FALSE,
                attempt_number INTEGER DEFAULT 1,
                time_taken_seconds INTEGER,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                ip_address INET,
                user_agent TEXT
            )
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_attempts_quiz ON quiz_attempts(quiz_id);
            CREATE INDEX IF NOT EXISTS idx_attempts_user ON quiz_attempts(user_id);
        """)
        
        # 11. STUDENT QUESTIONS (Q&A)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS student_questions (
                id SERIAL PRIMARY KEY,
                lesson_id INTEGER REFERENCES lessons(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                question TEXT NOT NULL,
                question_type VARCHAR(20) DEFAULT 'general' CHECK (question_type IN ('general', 'technical', 'clarification', 'error')),
                answer TEXT,
                answered_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                is_answered BOOLEAN DEFAULT FALSE,
                is_public BOOLEAN DEFAULT TRUE,
                upvotes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                answered_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 12. BLOG POSTS
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                excerpt TEXT,
                category VARCHAR(50) DEFAULT 'General',
                tags TEXT[],
                author_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
                is_premium BOOLEAN DEFAULT FALSE,
                featured_image VARCHAR(500),
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                reading_time_minutes INTEGER,
                is_featured BOOLEAN DEFAULT FALSE,
                allow_comments BOOLEAN DEFAULT TRUE,
                meta_keywords TEXT[],
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                published_at TIMESTAMP
            )
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_blog_status ON blog_posts(status);
            CREATE INDEX IF NOT EXISTS idx_blog_category ON blog_posts(category);
            CREATE INDEX IF NOT EXISTS idx_blog_created ON blog_posts(created_at DESC);
        """)
        
        # Add is_featured column to blog_posts if it doesn't exist
        if not await column_exists(conn, 'blog_posts', 'is_featured'):
            await conn.execute("ALTER TABLE blog_posts ADD COLUMN is_featured BOOLEAN DEFAULT FALSE")
            logger.info("Added is_featured column to blog_posts")
        
        # Now create the index (safely)
        try:
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_blog_featured ON blog_posts(is_featured)")
        except Exception as e:
            logger.warning(f"Could not create idx_blog_featured: {e}")
        
        # 13. BLOG MEDIA
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS blog_media (
                id SERIAL PRIMARY KEY,
                post_id INTEGER REFERENCES blog_posts(id) ON DELETE CASCADE,
                filename VARCHAR(255) NOT NULL,
                url VARCHAR(500) NOT NULL,
                caption TEXT,
                alt_text VARCHAR(255),
                mime_type VARCHAR(100),
                file_size_bytes INTEGER,
                dimensions VARCHAR(50),
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add is_featured column to blog_media if it doesn't exist
        if not await column_exists(conn, 'blog_media', 'is_featured'):
            await conn.execute("ALTER TABLE blog_media ADD COLUMN is_featured BOOLEAN DEFAULT FALSE")
            logger.info("Added is_featured column to blog_media")
        
        # 14. BLOG SEO DATA
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS blog_seo_data (
                id SERIAL PRIMARY KEY,
                post_id INTEGER REFERENCES blog_posts(id) ON DELETE CASCADE,
                seo_title VARCHAR(255),
                meta_description TEXT,
                focus_keyword VARCHAR(100),
                secondary_keywords TEXT[],
                slug VARCHAR(255) UNIQUE,
                canonical_url VARCHAR(500),
                schema_markup JSONB,
                seo_score INTEGER DEFAULT 0 CHECK (seo_score >= 0 AND seo_score <= 100),
                keyword_density DECIMAL(5,2),
                readability_score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_seo_slug ON blog_seo_data(slug);
        """)
        
        # 15. WEBINARS
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS webinars (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                scheduled_at TIMESTAMP NOT NULL,
                duration_minutes INTEGER DEFAULT 60,
                meeting_link VARCHAR(500),
                recording_url VARCHAR(500),
                max_participants INTEGER,
                current_participants INTEGER DEFAULT 0,
                reminder_message TEXT,
                reminder_sent BOOLEAN DEFAULT FALSE,
                is_premium BOOLEAN DEFAULT FALSE,
                status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'live', 'completed', 'cancelled')),
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 16. WEBINAR REGISTRATIONS
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS webinar_registrations (
                id SERIAL PRIMARY KEY,
                webinar_id INTEGER REFERENCES webinars(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reminder_sent BOOLEAN DEFAULT FALSE,
                attended BOOLEAN DEFAULT FALSE,
                attended_at TIMESTAMP,
                feedback_rating INTEGER CHECK (feedback_rating >= 1 AND feedback_rating <= 5),
                feedback_comment TEXT,
                UNIQUE(webinar_id, user_id)
            )
        """)
        
        # 17. MEDIA FILES
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS media_files (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                original_name VARCHAR(255),
                url VARCHAR(500) NOT NULL,
                mime_type VARCHAR(100),
                file_size_bytes INTEGER,
                entity_type VARCHAR(50),
                entity_id INTEGER,
                uploaded_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 18. SETTINGS
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id SERIAL PRIMARY KEY,
                key VARCHAR(255) UNIQUE NOT NULL,
                value TEXT,
                data_type VARCHAR(20) DEFAULT 'string' CHECK (data_type IN ('string', 'integer', 'boolean', 'json', 'array')),
                category VARCHAR(50) DEFAULT 'general' CHECK (category IN ('general', 'email', 'payment', 'telegram', 'security')),
                description TEXT,
                is_editable BOOLEAN DEFAULT TRUE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 19. ACTIVITY LOG
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                action VARCHAR(50) NOT NULL,
                entity_type VARCHAR(50),
                entity_id INTEGER,
                old_values JSONB,
                new_values JSONB,
                ip_address INET,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_log(user_id);
            CREATE INDEX IF NOT EXISTS idx_activity_action ON activity_log(action);
            CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_log(created_at DESC);
        """)
        
        # INSERT DEFAULT SETTINGS
        default_settings = [
            ('site_name', 'Pipways', 'string', 'general', 'Platform name', True),
            ('site_url', 'https://pipways.com', 'string', 'general', 'Main site URL', True),
            ('contact_email', 'admin@pipways.com', 'string', 'general', 'Contact email', True),
            ('telegram_free_link', 'https://t.me/pipways_free', 'string', 'telegram', 'Free channel link', True),
            ('telegram_vip_link', 'https://t.me/pipways_vip', 'string', 'telegram', 'VIP channel link', True),
            ('vip_price', '99.00', 'string', 'payment', 'Monthly VIP price', True),
            ('vip_price_currency', 'USD', 'string', 'payment', 'Currency code', True),
            ('enable_registration', 'true', 'boolean', 'general', 'Allow new registrations', True),
            ('maintenance_mode', 'false', 'boolean', 'general', 'Maintenance mode', True),
            ('max_login_attempts', '5', 'integer', 'security', 'Max failed login attempts', True),
            ('signal_expiry_hours', '48', 'integer', 'general', 'Auto-close signals after hours', True),
        ]
        
        for setting in default_settings:
            await conn.execute("""
                INSERT INTO settings (key, value, data_type, category, description, is_editable)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (key) DO NOTHING
            """, *setting)
        
        # CREATE DEFAULT ADMIN IF NONE EXISTS
        admin_exists = await conn.fetchval("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
        if not admin_exists:
            try:
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                hashed = pwd_context.hash('admin123')
                
                await conn.execute("""
                    INSERT INTO users (email, hashed_password, full_name, role, subscription_tier, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, 'admin@pipways.com', hashed, 'System Administrator', 'admin', 'vip', True)
                
                logger.info("Default admin created: admin@pipways.com / admin123")
            except ImportError:
                logger.warning("passlib not installed, skipping default admin creation")
        
        logger.info("Database initialization complete")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def check_connection() -> bool:
    """Check if database connection is alive"""
    try:
        async with get_connection() as conn:
            result = await conn.fetchval("SELECT 1")
            return result == 1
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

async def get_setting(key: str, default: Any = None) -> Any:
    """Get setting value by key"""
    try:
        value = await fetchval("SELECT value FROM settings WHERE key = $1", key)
        if value is None:
            return default
        
        type_row = await fetchrow("SELECT data_type FROM settings WHERE key = $1", key)
        if not type_row:
            return value
            
        data_type = type_row['data_type']
        
        if data_type == 'boolean':
            return value.lower() == 'true'
        elif data_type == 'integer':
            return int(value)
        elif data_type == 'json':
            return json.loads(value)
        elif data_type == 'array':
            return value.split(',') if value else []
        return value
    except Exception as e:
        logger.error(f"Error getting setting {key}: {e}")
        return default

async def update_setting(key: str, value: Any) -> bool:
    """Update setting value"""
    try:
        await execute("""
            UPDATE settings 
            SET value = $1, updated_at = CURRENT_TIMESTAMP 
            WHERE key = $2
        """, str(value), key)
        return True
    except Exception as e:
        logger.error(f"Error updating setting {key}: {e}")
        return False

async def log_activity(
    user_id: Optional[int],
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    old_values: Optional[Dict] = None,
    new_values: Optional[Dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Log activity to audit trail"""
    try:
        await execute("""
            INSERT INTO activity_log 
            (user_id, action, entity_type, entity_id, old_values, new_values, ip_address, user_agent)
            VALUES ($1, $2, $3, $4, $5, $6, $7::inet, $8)
        """, 
            user_id, action, entity_type, entity_id,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
            ip_address, user_agent
        )
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")

class Transaction:
    """Transaction context manager"""
    def __init__(self):
        self.conn = None
        self.transaction = None
    
    async def __aenter__(self):
        if not db_pool:
            await init_db_pool()
        self.conn = await db_pool.acquire()
        self.transaction = self.conn.transaction()
        await self.transaction.start()
        return self.conn
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.transaction.commit()
        else:
            await self.transaction.rollback()
        await db_pool.release(self.conn)
