"""
LMS Auto-Initialisation
=======================
Run init_lms_tables() during FastAPI startup.
Every statement is idempotent — safe to call on every deploy.

Usage in main.py:
    from .lms_init import init_lms_tables

    @asynccontextmanager
    async def lifespan(app):
        await init_database()
        await init_lms_tables()
        ...
        yield
"""
from .database import database

# ── New columns to ADD to the existing `courses` table ───────────────────────
_COURSE_COLUMNS = [
    ("price",               "FLOAT",        "DEFAULT 0"),
    ("thumbnail",           "VARCHAR(500)", "DEFAULT ''"),
    ("thumbnail_url",       "VARCHAR(500)", "DEFAULT ''"),
    ("preview_video",       "VARCHAR(500)", "DEFAULT ''"),
    ("is_active",           "BOOLEAN",      "DEFAULT TRUE"),
    ("is_published",        "BOOLEAN",      "DEFAULT FALSE"),
    ("certificate_enabled", "BOOLEAN",      "DEFAULT FALSE"),
    ("pass_percentage",     "INTEGER",      "DEFAULT 70"),
    ("instructor",          "VARCHAR(255)", "DEFAULT ''"),
]

# ── Tables to CREATE IF NOT EXISTS ───────────────────────────────────────────
_TABLE_SQLS = [
    """
    CREATE TABLE IF NOT EXISTS course_modules (
        id          SERIAL PRIMARY KEY,
        course_id   INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        title       VARCHAR(255) NOT NULL,
        description TEXT    DEFAULT '',
        order_index INTEGER DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS lessons (
        id               SERIAL PRIMARY KEY,
        course_id        INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        module_id        INTEGER,
        title            VARCHAR(255) NOT NULL,
        content          TEXT    DEFAULT '',
        video_url        VARCHAR(500) DEFAULT '',
        attachment_url   VARCHAR(500) DEFAULT '',
        duration_minutes INTEGER DEFAULT 0,
        order_index      INTEGER DEFAULT 0,
        is_free_preview  BOOLEAN DEFAULT FALSE,
        is_active        BOOLEAN DEFAULT TRUE,
        created_at       TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS quizzes (
        id              SERIAL PRIMARY KEY,
        module_id       INTEGER NOT NULL REFERENCES course_modules(id) ON DELETE CASCADE,
        title           VARCHAR(255) NOT NULL,
        pass_percentage INTEGER DEFAULT 70,
        max_attempts    INTEGER DEFAULT 3,
        created_at      TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS quiz_questions (
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
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_progress (
        id                SERIAL PRIMARY KEY,
        user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id         INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        progress_percent  INTEGER DEFAULT 0,
        completed_lessons INTEGER DEFAULT 0,
        last_accessed     TIMESTAMP DEFAULT NOW(),
        completed_at      TIMESTAMP,
        UNIQUE(user_id, course_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_lesson_progress (
        id                   SERIAL PRIMARY KEY,
        user_id              INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        lesson_id            INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
        completed_at         TIMESTAMP DEFAULT NOW(),
        time_spent_seconds   INTEGER DEFAULT 0,
        UNIQUE(user_id, lesson_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS certificates (
        id                 SERIAL PRIMARY KEY,
        user_id            INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id          INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        certificate_number VARCHAR(100) UNIQUE NOT NULL,
        issued_at          TIMESTAMP DEFAULT NOW(),
        pdf_url            VARCHAR(500) DEFAULT '',
        UNIQUE(user_id, course_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id           SERIAL PRIMARY KEY,
        user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        quiz_id      INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
        score        FLOAT NOT NULL DEFAULT 0,
        passed       BOOLEAN DEFAULT FALSE,
        answers      TEXT DEFAULT '{}',
        attempted_at TIMESTAMP DEFAULT NOW()
    )
    """,
]


async def init_lms_tables() -> None:
    """
    Create all LMS tables and add missing columns to courses.
    Fully idempotent — safe to call on every startup.
    """
    ok = warn = 0

    # 1. Add missing columns to courses
    for col, col_type, default in _COURSE_COLUMNS:
        try:
            await database.execute(
                f"ALTER TABLE courses ADD COLUMN IF NOT EXISTS {col} {col_type} {default}"
            )
            ok += 1
        except Exception as e:
            print(f"[LMS INIT] courses.{col} warn: {e}", flush=True)
            warn += 1

    # 2. Create LMS tables
    for sql in _TABLE_SQLS:
        try:
            await database.execute(sql.strip())
            ok += 1
        except Exception as e:
            print(f"[LMS INIT] table warn: {e}", flush=True)
            warn += 1

    print(f"[LMS INIT] Complete — {ok} ok, {warn} warnings", flush=True)
