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
    Column("lesson_id", Integer, nullable=False),  # FIX: was FK to course_lessons (old table); plain Integer avoids FK ordering issues
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


# ══════════════════════════════════════════════════════════════════════════════
# DATABASE MIGRATIONS  ─  added for CMS v2
# Safe to call every startup: every statement is fully idempotent.
# ══════════════════════════════════════════════════════════════════════════════

# (table, column, pg_type, default_clause)
# Each row becomes:  ALTER TABLE <table> ADD COLUMN IF NOT EXISTS <col> <type> <default>
_COLUMN_MIGRATIONS = [
    # ── blog_posts ────────────────────────────────────────────────────────────
    # The live table was created with status/featured only; CMS v2 needs these:
    ("blog_posts", "is_published",    "BOOLEAN",      "DEFAULT FALSE"),
    ("blog_posts", "featured",        "BOOLEAN",      "DEFAULT FALSE"),  # was missing — caused all queries to fail
    ("blog_posts", "read_time",       "VARCHAR(20)",  "DEFAULT '5 min'"),  # was missing
    ("blog_posts", "tags",            "TEXT",         "DEFAULT '[]'"),
    ("blog_posts", "featured_image",  "VARCHAR(500)", "DEFAULT ''"),
    ("blog_posts", "views",           "INTEGER",      "DEFAULT 0"),
    ("blog_posts", "focus_keyword",   "VARCHAR(255)", "DEFAULT ''"),
    ("blog_posts", "seo_title",       "VARCHAR(255)", "DEFAULT ''"),
    ("blog_posts", "seo_description", "TEXT",         "DEFAULT ''"),   # may already exist
    ("blog_posts", "seo_keywords",    "VARCHAR(500)", "DEFAULT ''"),   # may already exist
    ("blog_posts", "og_image_url",    "VARCHAR(500)", "DEFAULT ''"),   # may already exist

    # ── signals ───────────────────────────────────────────────────────────────
    # Production signals table may have been created with a minimal schema
    # (id, title, status …) before the trading-specific columns were added.
    ("signals", "symbol",        "VARCHAR(20)",  "DEFAULT ''"),
    ("signals", "direction",     "VARCHAR(10)",  "DEFAULT 'BUY'"),
    ("signals", "entry_price",   "FLOAT",        "DEFAULT 0"),
    ("signals", "stop_loss",     "FLOAT",        "DEFAULT 0"),
    ("signals", "take_profit",   "FLOAT",        "DEFAULT 0"),
    ("signals", "timeframe",     "VARCHAR(10)",  "DEFAULT '1H'"),
    ("signals", "analysis",      "TEXT",         "DEFAULT ''"),
    ("signals", "outcome",       "VARCHAR(20)",  ""),
    ("signals", "ai_confidence", "FLOAT",        ""),
    ("signals", "is_published",  "BOOLEAN",      "DEFAULT FALSE"),  # was missing — caused COALESCE to fail
    ("signals", "created_by",    "INTEGER",      ""),
    ("signals", "result_pips",   "FLOAT",        ""),
    # status / closed_at already exist per the ORM definition

    # ── webinars ──────────────────────────────────────────────────────────────
    # presenter + recording_url are in the ORM but missing from some live DBs
    ("webinars", "presenter",        "VARCHAR(255)", "DEFAULT ''"),
    ("webinars", "meeting_link",     "VARCHAR(500)", "DEFAULT ''"),
    ("webinars", "recording_url",    "VARCHAR(500)", "DEFAULT ''"),   # may already exist
    ("webinars", "thumbnail",        "VARCHAR(500)", "DEFAULT ''"),
    ("webinars", "max_attendees",    "INTEGER",      "DEFAULT 100"),
    ("webinars", "is_published",     "BOOLEAN",      "DEFAULT FALSE"),
    ("webinars", "status",           "VARCHAR(50)",  "DEFAULT 'scheduled'"),  # was missing → CMS INSERT failed

    # ── courses ───────────────────────────────────────────────────────────────
    ("courses", "price",               "FLOAT",        "DEFAULT 0"),
    ("courses", "thumbnail",           "VARCHAR(500)", "DEFAULT ''"),
    ("courses", "preview_video",       "VARCHAR(500)", "DEFAULT ''"),
    ("courses", "is_active",           "BOOLEAN",      "DEFAULT TRUE"),   # was missing — caused INSERT 500
    ("courses", "is_published",        "BOOLEAN",      "DEFAULT FALSE"),
    ("courses", "certificate_enabled", "BOOLEAN",      "DEFAULT FALSE"),
    ("courses", "pass_percentage",     "INTEGER",      "DEFAULT 70"),
    # BUG FIX: instructor & thumbnail_url are in the ORM courses_table definition
    # but were missing from _COLUMN_MIGRATIONS, so older live DBs that pre-date
    # the ORM column addition would not have them added on startup.
    ("courses", "instructor",          "VARCHAR(255)", "DEFAULT ''"),
    ("courses", "thumbnail_url",       "VARCHAR(500)", "DEFAULT ''"),


    # ── course_modules ────────────────────────────────────────────────────────
    # BUG FIX: The live table may have been created by an older migration that
    # lacked these columns.  CREATE TABLE IF NOT EXISTS never patches existing
    # tables, so every column that can be missing needs its own ADD COLUMN.
    ("course_modules", "description",  "TEXT",    "DEFAULT ''"),
    ("course_modules", "order_index",  "INTEGER", "DEFAULT 0"),
    ("course_modules", "is_published", "BOOLEAN", "DEFAULT TRUE"),
    ("course_modules", "course_id",    "INTEGER", "REFERENCES courses(id) ON DELETE CASCADE"),
    # ── lessons ───────────────────────────────────────────────────────────────
    # Core FK columns — may be missing if table was created from old schema
    ("lessons", "course_id",        "INTEGER",      "REFERENCES courses(id) ON DELETE CASCADE"),
    ("lessons", "module_id",        "INTEGER",      ""),
    ("lessons", "content",          "TEXT",         "DEFAULT ''"),
    ("lessons", "video_url",        "VARCHAR(500)", "DEFAULT ''"),
    ("lessons", "attachment_url",   "VARCHAR(500)", "DEFAULT ''"),
    ("lessons", "duration_minutes", "INTEGER",      "DEFAULT 0"),
    ("lessons", "order_index",      "INTEGER",      "DEFAULT 0"),
    ("lessons", "is_free_preview",  "BOOLEAN",      "DEFAULT FALSE"),
    ("lessons", "is_active",        "BOOLEAN",      "DEFAULT TRUE"),
    ("lessons", "is_published",     "BOOLEAN",      "DEFAULT TRUE"),

    # ── users ─────────────────────────────────────────────────────────────────
    ("users", "last_login",        "TIMESTAMP",   ""),
    # role / subscription_tier already exist in the ORM, guard anyway
    ("users", "role",              "VARCHAR(50)", "DEFAULT 'user'"),
    # ── ai_mentor_logs — add message/role columns for persistent history ──────
    ("ai_mentor_logs", "role",    "VARCHAR(20)", "DEFAULT 'user'"),
    ("ai_mentor_logs", "message", "TEXT",        "DEFAULT ''"),
]

# New tables required by CMS v2 — all CREATE … IF NOT EXISTS so safe to re-run.
_TABLE_MIGRATIONS = [
    """CREATE TABLE IF NOT EXISTS course_modules (
        id          SERIAL PRIMARY KEY,
        course_id   INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        title       VARCHAR(255) NOT NULL,
        description TEXT DEFAULT '',
        order_index INTEGER DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS lessons (
        id               SERIAL PRIMARY KEY,
        course_id        INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        module_id        INTEGER,
        title            VARCHAR(255) NOT NULL,
        content          TEXT DEFAULT '',
        video_url        VARCHAR(500) DEFAULT '',
        attachment_url   VARCHAR(500) DEFAULT '',
        duration_minutes INTEGER DEFAULT 0,
        order_index      INTEGER DEFAULT 0,
        is_free_preview  BOOLEAN DEFAULT FALSE,
        is_active        BOOLEAN DEFAULT TRUE,
        created_at       TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS quizzes (
        id              SERIAL PRIMARY KEY,
        module_id       INTEGER NOT NULL REFERENCES course_modules(id) ON DELETE CASCADE,
        title           VARCHAR(255) NOT NULL,
        pass_percentage INTEGER DEFAULT 70,
        max_attempts    INTEGER DEFAULT 3,
        created_at      TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS quiz_questions (
        id             SERIAL PRIMARY KEY,
        quiz_id        INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
        question       TEXT NOT NULL,
        option_a       TEXT NOT NULL,
        option_b       TEXT NOT NULL,
        option_c       TEXT DEFAULT '',
        option_d       TEXT DEFAULT '',
        correct_option VARCHAR(1) NOT NULL,
        explanation    TEXT DEFAULT '',
        order_index    INTEGER DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS media_library (
        id            SERIAL PRIMARY KEY,
        filename      VARCHAR(500) NOT NULL,
        original_name VARCHAR(255) DEFAULT '',
        url           VARCHAR(500) NOT NULL,
        mime_type     VARCHAR(100) DEFAULT '',
        size_bytes    BIGINT DEFAULT 0,
        folder        VARCHAR(100) DEFAULT 'general',
        created_at    TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS site_settings (
        key        VARCHAR(120) PRIMARY KEY,
        value      TEXT NOT NULL DEFAULT '',
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS announcements (
        id         SERIAL PRIMARY KEY,
        message    TEXT NOT NULL,
        type       VARCHAR(20) DEFAULT 'info',
        is_active  BOOLEAN DEFAULT TRUE,
        expires_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS coupons (
        id             SERIAL PRIMARY KEY,
        code           VARCHAR(50) UNIQUE NOT NULL,
        discount_type  VARCHAR(20) DEFAULT 'percent',
        discount_value FLOAT NOT NULL,
        max_uses       INTEGER DEFAULT 100,
        uses           INTEGER DEFAULT 0,
        expires_at     TIMESTAMP,
        is_active      BOOLEAN DEFAULT TRUE,
        created_at     TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS login_logs (
        id         SERIAL PRIMARY KEY,
        user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS ai_mentor_logs (
        id             SERIAL PRIMARY KEY,
        user_id        INTEGER,
        question_topic VARCHAR(255) DEFAULT '',
        role           VARCHAR(20)  DEFAULT 'user',
        message        TEXT         DEFAULT '',
        created_at     TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS chart_analysis_logs (
        id         SERIAL PRIMARY KEY,
        user_id    INTEGER,
        symbol     VARCHAR(20) DEFAULT '',
        created_at TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS journal_uploads (
        id         SERIAL PRIMARY KEY,
        user_id    INTEGER,
        created_at TIMESTAMP DEFAULT NOW()
    )""",
]


async def run_migrations():
    """
    Idempotent migration runner — call once from main.py lifespan startup.

    Phase 1: CREATE new tables (IF NOT EXISTS).
    Phase 2: ADD missing columns (IF NOT EXISTS).
    Phase 3: Back-fill is_published from legacy status/is_active columns.
    """
    print("[DB MIGRATION] Starting schema migration…", flush=True)
    ok = warn = 0

    # ── Phase 1: new tables ──────────────────────────────────────────────────
    for sql in _TABLE_MIGRATIONS:
        try:
            await database.execute(sql.strip())
            ok += 1
        except Exception as e:
            print(f"[DB MIGRATION] table warn: {e}", flush=True)
            warn += 1

    # ── Phase 2: missing columns ─────────────────────────────────────────────
    for table, col, col_type, default_clause in _COLUMN_MIGRATIONS:
        try:
            ddl = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type}"
            if default_clause:
                ddl += f" {default_clause}"
            await database.execute(ddl)
            ok += 1
        except Exception as e:
            print(f"[DB MIGRATION] col {table}.{col} warn: {e}", flush=True)
            warn += 1

    # ── Phase 3: fix legacy NOT NULL constraints & sync dual-column data ─────

    # The live signals table may have a "pair" column (older schema) that is NOT NULL.
    # Make it nullable so CMS inserts (which use symbol/direction) don't fail.
    for sql in [
        "ALTER TABLE signals ALTER COLUMN pair DROP NOT NULL",
        "ALTER TABLE signals ALTER COLUMN pair SET DEFAULT ''",
    ]:
        try: await database.execute(sql)
        except Exception: pass  # column may not exist — safe to ignore

    # Backfill pair = symbol for any rows where pair is null/empty
    try:
        await database.execute(
            "UPDATE signals SET pair = symbol WHERE (pair IS NULL OR pair = '') AND symbol IS NOT NULL"
        )
    except Exception: pass

    # Sync is_active with is_published for courses
    # (public /courses/list filters by is_active, CMS sets is_published)
    try:
        await database.execute(
            "UPDATE courses SET is_active = TRUE WHERE is_published = TRUE"
        )
    except Exception: pass

    # Sync is_published with is_active for courses (reverse direction for old data)
    try:
        await database.execute(
            "UPDATE courses SET is_published = TRUE WHERE is_active = TRUE AND (is_published IS NULL OR is_published = FALSE)"
        )
    except Exception: pass

    # Sync webinar status = 'scheduled' for all published webinars
    try:
        await database.execute(
            "UPDATE webinars SET status = 'scheduled' "
            "WHERE is_published = TRUE AND (status IS NULL OR status = '' OR status = 'draft')"
        )
    except Exception: pass

    # Sync is_published from status for webinars (old data)
    try:
        await database.execute(
            "UPDATE webinars SET is_published = TRUE "
            "WHERE status NOT IN ('cancelled', 'draft', '') AND (is_published IS NULL OR is_published = FALSE)"
        )
    except Exception: pass

    # Sync blog status = 'published' for all posts with is_published = TRUE
    try:
        await database.execute(
            "UPDATE blog_posts SET status = 'published' WHERE is_published = TRUE"
        )
    except Exception: pass

    # Sync is_published from status for blog posts (old data)
    try:
        await database.execute(
            "UPDATE blog_posts SET is_published = TRUE "
            "WHERE status = 'published' AND (is_published IS NULL OR is_published = FALSE)"
        )
    except Exception: pass

    print(f"[DB MIGRATION] Complete — {ok} statements ok, {warn} warnings", flush=True)

# ── Phase 4: Ensure UNIQUE constraints that ON CONFLICT clauses depend on ────
# BUG: `user_progress` was created by metadata.create_all() WITHOUT a UNIQUE
# constraint on (user_id, course_id). The ON CONFLICT upsert in complete_lesson
# (courses.py) requires this constraint — without it PostgreSQL raises:
#   "there is no unique or exclusion constraint matching the ON CONFLICT specification"
# CREATE UNIQUE INDEX IF NOT EXISTS is idempotent and safe on existing tables.

# Also: `user_lesson_progress` needs UNIQUE(user_id, lesson_id) for its
# ON CONFLICT DO NOTHING clause.

# Also: `certificates` needs UNIQUE(user_id, course_id) for its
# ON CONFLICT DO NOTHING clause.

_UNIQUE_INDEX_MIGRATIONS = [
    (
        "idx_user_progress_user_course",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_user_progress_user_course "
        "ON user_progress (user_id, course_id)"
    ),
    (
        "idx_user_lesson_progress_user_lesson",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_user_lesson_progress_user_lesson "
        "ON user_lesson_progress (user_id, lesson_id)"
    ),
    (
        "idx_certificates_user_course",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_certificates_user_course "
        "ON certificates (user_id, course_id)"
    ),
]

async def run_unique_index_migrations():
    """
    Add missing UNIQUE indexes that ON CONFLICT clauses depend on.
    Called from main.py lifespan AFTER run_migrations().
    Idempotent — safe to call on every deploy.
    """
    ok = warn = 0
    for name, sql in _UNIQUE_INDEX_MIGRATIONS:
        try:
            await database.execute(sql)
            ok += 1
            print(f"[DB INDEX] {name}: ok", flush=True)
        except Exception as e:
            warn += 1
            print(f"[DB INDEX] {name} warn: {e}", flush=True)
    print(f"[DB INDEX] Done — {ok} ok, {warn} warnings", flush=True)
