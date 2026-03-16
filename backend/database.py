"""
Database configuration and connection management for Pipways Trading Platform.
Includes automatic schema migrations for LMS tables.
"""
import os
import logging
from databases import Database
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import expression
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/pipways")

# Initialize Database connection (async)
database = Database(DATABASE_URL)

# SQLAlchemy setup for migrations (sync)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
metadata = MetaData()

# ═══════════════════════════════════════════════════════════════════════════════
# TABLE DEFINITIONS (SQLAlchemy)
# ═══════════════════════════════════════════════════════════════════════════════

# Users table
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(255), unique=True, nullable=False),
    Column("password", String(255), nullable=False),
    Column("full_name", String(255)),
    Column("is_active", Boolean, default=True),
    Column("is_admin", Boolean, default=False),
    Column("role", String(50), default="user"),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("last_login", DateTime),
)

# Blog posts table
blog_posts = Table(
    "blog_posts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(255), nullable=False),
    Column("slug", String(255), unique=True, nullable=False),
    Column("content", Text),
    Column("excerpt", Text),
    Column("category", String(100)),
    Column("featured_image", String(500)),
    Column("views", Integer, default=0),
    Column("tags", String(500)),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime),
    Column("featured", Boolean, default=False),
    Column("read_time", String(50)),
    Column("is_published", Boolean, default=False),
    Column("status", String(50), default="draft"),
)

# Courses table (basic)
courses_table = Table(
    "courses",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(255), nullable=False),
    Column("description", Text),
    Column("level", String(50)),
    Column("is_active", Boolean, default=True),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("price", Float, default=0),
    Column("thumbnail", String(500)),
    Column("preview_video", String(500)),
    Column("is_published", Boolean, default=False),
    Column("certificate_enabled", Boolean, default=False),
    Column("pass_percentage", Integer, default=70),
    Column("lesson_count", Integer, default=0),
)

# ═══════════════════════════════════════════════════════════════════════════════
# AUTOMATIC MIGRATIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Legacy column migrations (existing tables)
_COLUMN_MIGRATIONS = [
    ("blog_posts", "featured_image", "VARCHAR(500)", "DEFAULT ''"),
    ("blog_posts", "views", "INTEGER", "DEFAULT 0"),
    ("blog_posts", "tags", "VARCHAR(500)", "DEFAULT '[]'"),
    ("blog_posts", "featured", "BOOLEAN", "DEFAULT FALSE"),
    ("blog_posts", "read_time", "VARCHAR(50)", "DEFAULT '5 min'"),
    ("blog_posts", "is_published", "BOOLEAN", "DEFAULT FALSE"),
    ("blog_posts", "status", "VARCHAR(50)", "DEFAULT 'published'"),
]

# LMS Column migrations (adds columns to existing courses table)
_LMS_COLUMN_MIGRATIONS = [
    ("courses", "price", "FLOAT", "DEFAULT 0"),
    ("courses", "thumbnail", "VARCHAR(500)", "DEFAULT ''"),
    ("courses", "preview_video", "VARCHAR(500)", "DEFAULT ''"),
    ("courses", "is_published", "BOOLEAN", "DEFAULT FALSE"),
    ("courses", "is_active", "BOOLEAN", "DEFAULT TRUE"),
    ("courses", "certificate_enabled", "BOOLEAN", "DEFAULT FALSE"),
    ("courses", "pass_percentage", "INTEGER", "DEFAULT 70"),
    ("courses", "lesson_count", "INTEGER", "DEFAULT 0"),
    ("courses", "level", "VARCHAR(50)", "DEFAULT 'Beginner'"),
]

# LMS Table migrations (creates new tables if not exist)
_LMS_TABLE_MIGRATIONS = [
    # Course Modules
    """CREATE TABLE IF NOT EXISTS course_modules (
        id SERIAL PRIMARY KEY,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        description TEXT DEFAULT '',
        order_index INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW()
    )""",
    
    # Lessons
    """CREATE TABLE IF NOT EXISTS lessons (
        id SERIAL PRIMARY KEY,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        module_id INTEGER REFERENCES course_modules(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        content TEXT DEFAULT '',
        video_url VARCHAR(500) DEFAULT '',
        attachment_url VARCHAR(500) DEFAULT '',
        duration_minutes INTEGER DEFAULT 0,
        order_index INTEGER DEFAULT 0,
        is_free_preview BOOLEAN DEFAULT FALSE,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT NOW()
    )""",
    
    # Quizzes
    """CREATE TABLE IF NOT EXISTS quizzes (
        id SERIAL PRIMARY KEY,
        module_id INTEGER NOT NULL REFERENCES course_modules(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        pass_percentage INTEGER DEFAULT 70,
        max_attempts INTEGER DEFAULT 3,
        created_at TIMESTAMP DEFAULT NOW()
    )""",
    
    # Quiz Questions
    """CREATE TABLE IF NOT EXISTS quiz_questions (
        id SERIAL PRIMARY KEY,
        quiz_id INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
        question TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT DEFAULT '',
        option_d TEXT DEFAULT '',
        correct_option VARCHAR(1) NOT NULL CHECK (correct_option IN ('a', 'b', 'c', 'd')),
        explanation TEXT DEFAULT '',
        order_index INTEGER DEFAULT 0
    )""",
    
    # User Progress
    """CREATE TABLE IF NOT EXISTS user_progress (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        progress_percent INTEGER DEFAULT 0,
        completed_lessons INTEGER DEFAULT 0,
        last_accessed TIMESTAMP,
        completed_at TIMESTAMP,
        UNIQUE(user_id, course_id)
    )""",
    
    # User Lesson Progress
    """CREATE TABLE IF NOT EXISTS user_lesson_progress (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
        completed_at TIMESTAMP DEFAULT NOW(),
        time_spent_seconds INTEGER DEFAULT 0,
        UNIQUE(user_id, lesson_id)
    )""",
    
    # Certificates
    """CREATE TABLE IF NOT EXISTS certificates (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        certificate_number VARCHAR(100) UNIQUE NOT NULL,
        issued_at TIMESTAMP DEFAULT NOW(),
        pdf_url VARCHAR(500) DEFAULT '',
        UNIQUE(user_id, course_id)
    )""",
    
    # Media Library for file uploads
    """CREATE TABLE IF NOT EXISTS media_library (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(500) NOT NULL,
        original_name VARCHAR(255) DEFAULT '',
        url VARCHAR(500) NOT NULL,
        mime_type VARCHAR(100) DEFAULT '',
        size_bytes BIGINT DEFAULT 0,
        folder VARCHAR(100) DEFAULT 'general',
        created_at TIMESTAMP DEFAULT NOW()
    )""",
]

# Indexes for performance
_LMS_INDEX_MIGRATIONS = [
    "CREATE INDEX IF NOT EXISTS idx_lessons_module ON lessons(module_id)",
    "CREATE INDEX IF NOT EXISTS idx_lessons_course ON lessons(course_id)",
    "CREATE INDEX IF NOT EXISTS idx_modules_course ON course_modules(course_id)",
    "CREATE INDEX IF NOT EXISTS idx_quizzes_module ON quizzes(module_id)",
    "CREATE INDEX IF NOT EXISTS idx_questions_quiz ON quiz_questions(quiz_id)",
    "CREATE INDEX IF NOT EXISTS idx_progress_user ON user_progress(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_progress_course ON user_progress(course_id)",
    "CREATE INDEX IF NOT EXISTS idx_cert_user ON certificates(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_cert_course ON certificates(course_id)",
    "CREATE INDEX IF NOT EXISTS idx_lesson_progress_user ON user_lesson_progress(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_lesson_progress_lesson ON user_lesson_progress(lesson_id)",
]

# Data fixes
_LMS_DATA_FIXES = [
    "UPDATE courses SET is_active = TRUE, is_published = TRUE WHERE is_active IS NULL AND is_published IS NULL",
    "UPDATE courses SET level = 'Beginner' WHERE level IS NULL",
]

# ═══════════════════════════════════════════════════════════════════════════════
# MIGRATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def run_column_migrations():
    """Add missing columns to existing tables"""
    all_migrations = _COLUMN_MIGRATIONS + _LMS_COLUMN_MIGRATIONS
    
    for table, column, col_type, default in all_migrations:
        try:
            # Check if column exists
            query = f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = '{column}'
            """
            result = await database.fetch_one(query)
            
            if not result:
                await database.execute(f"""
                    ALTER TABLE {table} 
                    ADD COLUMN {column} {col_type} {default}
                """)
                logger.info(f"[Migration] Added column {table}.{column}")
        except Exception as e:
            logger.warning(f"[Migration] Column {table}.{column}: {e}")

async def run_table_migrations():
    """Create new tables if they don't exist"""
    all_table_sqls = _LMS_TABLE_MIGRATIONS
    
    for sql in all_table_sqls:
        try:
            await database.execute(sql)
            logger.info("[Migration] Ensured table exists")
        except Exception as e:
            logger.error(f"[Migration] Table creation failed: {e}")

async def run_index_migrations():
    """Create indexes for performance"""
    for sql in _LMS_INDEX_MIGRATIONS:
        try:
            await database.execute(sql)
        except Exception as e:
            logger.warning(f"[Migration] Index creation: {e}")

async def run_data_fixes():
    """Fix existing data"""
    for sql in _LMS_DATA_FIXES:
        try:
            result = await database.execute(sql)
            logger.info(f"[Migration] Data fix applied")
        except Exception as e:
            logger.warning(f"[Migration] Data fix: {e}")

async def run_migrations():
    """
    Run all database migrations automatically.
    Called on application startup.
    """
    logger.info("[DB] Starting database migrations...")
    
    try:
        # 1. Add missing columns to existing tables
        await run_column_migrations()
        
        # 2. Create new LMS tables
        await run_table_migrations()
        
        # 3. Create indexes
        await run_index_migrations()
        
        # 4. Fix existing data
        await run_data_fixes()
        
        logger.info("[DB] All migrations completed successfully")
    except Exception as e:
        logger.error(f"[DB] Migration error: {e}")
        # Don't raise - allow app to start even if some migrations fail

# ═══════════════════════════════════════════════════════════════════════════════
# CONNECTION MANAGEMENT (for main.py compatibility)
# ═══════════════════════════════════════════════════════════════════════════════

async def init_database():
    """
    Initialize database connection and run migrations.
    This is the main entry point called by main.py on startup.
    """
    logger.info("[DB] Initializing database...")
    try:
        await connect()
        await run_migrations()
        logger.info("[DB] Database initialization complete")
    except Exception as e:
        logger.error(f"[DB] Initialization failed: {e}")
        raise

async def connect():
    """Connect to database"""
    if not database.is_connected:
        await database.connect()
        logger.info("[DB] Database connected")

async def disconnect():
    """Disconnect from database"""
    if database.is_connected:
        await database.disconnect()
        logger.info("[DB] Database disconnected")

# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY CONSTANTS (imported by security.py)
# ═══════════════════════════════════════════════════════════════════════════════

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════════════════

# Ensure 'courses' table reference exists for imports
courses = courses_table
