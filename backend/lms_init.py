"""
LMS Auto-Initialisation — Bulletproof Edition
=============================================
Adds every required column to the existing `courses` table
and creates all LMS tables. Every statement is idempotent.
Runs at startup via main.py lifespan.
"""
from .database import database


# Columns to ADD to the existing `courses` table.
# Each tuple: (column_name, sql_type_and_default)
_COURSE_COLUMNS = [
    ("price",               "FLOAT        NOT NULL DEFAULT 0"),
    ("thumbnail",           "VARCHAR(500) NOT NULL DEFAULT ''"),
    ("thumbnail_url",       "VARCHAR(500) NOT NULL DEFAULT ''"),
    ("preview_video",       "VARCHAR(500) NOT NULL DEFAULT ''"),
    ("is_published",        "BOOLEAN      NOT NULL DEFAULT FALSE"),
    ("is_active",           "BOOLEAN      NOT NULL DEFAULT TRUE"),
    ("certificate_enabled", "BOOLEAN      NOT NULL DEFAULT FALSE"),
    ("pass_percentage",     "INTEGER      NOT NULL DEFAULT 70"),
    ("instructor",          "VARCHAR(255) NOT NULL DEFAULT ''"),
]

# Full CREATE TABLE statements for LMS tables (all idempotent).
_TABLE_SQLS = [
    """
    CREATE TABLE IF NOT EXISTS course_modules (
        id          SERIAL  PRIMARY KEY,
        course_id   INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        title       VARCHAR(255) NOT NULL,
        description TEXT         NOT NULL DEFAULT '',
        order_index INTEGER      NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS lessons (
        id               SERIAL  PRIMARY KEY,
        course_id        INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        module_id        INTEGER REFERENCES course_modules(id) ON DELETE SET NULL,
        title            VARCHAR(255) NOT NULL,
        content          TEXT         NOT NULL DEFAULT '',
        video_url        VARCHAR(500) NOT NULL DEFAULT '',
        attachment_url   VARCHAR(500) NOT NULL DEFAULT '',
        duration_minutes INTEGER      NOT NULL DEFAULT 0,
        order_index      INTEGER      NOT NULL DEFAULT 0,
        is_free_preview  BOOLEAN      NOT NULL DEFAULT FALSE,
        is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
        created_at       TIMESTAMP    NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS quizzes (
        id              SERIAL  PRIMARY KEY,
        module_id       INTEGER NOT NULL REFERENCES course_modules(id) ON DELETE CASCADE,
        title           VARCHAR(255) NOT NULL,
        pass_percentage INTEGER      NOT NULL DEFAULT 70,
        max_attempts    INTEGER      NOT NULL DEFAULT 3,
        created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS quiz_questions (
        id             SERIAL  PRIMARY KEY,
        quiz_id        INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
        question       TEXT         NOT NULL,
        option_a       TEXT         NOT NULL,
        option_b       TEXT         NOT NULL,
        option_c       TEXT         NOT NULL DEFAULT '',
        option_d       TEXT         NOT NULL DEFAULT '',
        correct_option VARCHAR(1)   NOT NULL,
        explanation    TEXT         NOT NULL DEFAULT '',
        order_index    INTEGER      NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_progress (
        id                SERIAL  PRIMARY KEY,
        user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id         INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        progress_percent  INTEGER NOT NULL DEFAULT 0,
        completed_lessons INTEGER NOT NULL DEFAULT 0,
        last_accessed     TIMESTAMP NOT NULL DEFAULT NOW(),
        completed_at      TIMESTAMP,
        UNIQUE(user_id, course_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_lesson_progress (
        id                 SERIAL  PRIMARY KEY,
        user_id            INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        lesson_id          INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
        completed_at       TIMESTAMP NOT NULL DEFAULT NOW(),
        time_spent_seconds INTEGER   NOT NULL DEFAULT 0,
        UNIQUE(user_id, lesson_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS certificates (
        id                 SERIAL  PRIMARY KEY,
        user_id            INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id          INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        certificate_number VARCHAR(100) UNIQUE NOT NULL,
        issued_at          TIMESTAMP NOT NULL DEFAULT NOW(),
        pdf_url            VARCHAR(500) NOT NULL DEFAULT '',
        UNIQUE(user_id, course_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id           SERIAL  PRIMARY KEY,
        user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        quiz_id      INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
        score        FLOAT   NOT NULL DEFAULT 0,
        passed       BOOLEAN NOT NULL DEFAULT FALSE,
        answers      TEXT    NOT NULL DEFAULT '{}',
        attempted_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """,
]


async def init_lms_tables() -> None:
    """
    1. Add missing columns to `courses`.
    2. Create all LMS tables.
    Fully idempotent — safe on every deploy.
    """
    ok = warn = 0

    # Step 1 — add columns to courses
    for col, definition in _COURSE_COLUMNS:
        sql = f"ALTER TABLE courses ADD COLUMN IF NOT EXISTS {col} {definition}"
        try:
            await database.execute(sql)
            ok += 1
        except Exception as e:
            warn += 1
            print(f"[LMS INIT] courses.{col}: {e}", flush=True)

    # Step 2 — create LMS tables
    for sql in _TABLE_SQLS:
        try:
            await database.execute(sql.strip())
            ok += 1
        except Exception as e:
            warn += 1
            print(f"[LMS INIT] table warn: {e}", flush=True)

    print(f"[LMS INIT] Done — {ok} ok, {warn} warnings", flush=True)
