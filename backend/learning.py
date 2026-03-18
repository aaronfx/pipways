"""
LMS Auto-Initialisation — Bulletproof Edition v3.0
=============================================
Adds user_badges table and enhanced curriculum.
Fully idempotent — safe on every deploy.
"""
from .database import database


# Columns to ADD to the existing `courses` table.
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

# CMS LMS Tables (unchanged)
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


# ══════════════════════════════════════════════════════════════════════════════
# TRADING ACADEMY TABLES (Enhanced with Badges)
# ══════════════════════════════════════════════════════════════════════════════

_LEARNING_TABLE_SQLS = [
    """
    CREATE TABLE IF NOT EXISTS learning_levels (
        id          SERIAL  PRIMARY KEY,
        name        VARCHAR(100) NOT NULL,
        description TEXT         NOT NULL DEFAULT '',
        order_index INTEGER      NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS learning_modules (
        id          SERIAL  PRIMARY KEY,
        level_id    INTEGER NOT NULL REFERENCES learning_levels(id) ON DELETE CASCADE,
        title       VARCHAR(255) NOT NULL,
        description TEXT         NOT NULL DEFAULT '',
        order_index INTEGER      NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS learning_lessons (
        id          SERIAL  PRIMARY KEY,
        module_id   INTEGER NOT NULL REFERENCES learning_modules(id) ON DELETE CASCADE,
        title       VARCHAR(255) NOT NULL,
        content     TEXT         NOT NULL DEFAULT '',
        order_index INTEGER      NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS lesson_quizzes (
        id             SERIAL  PRIMARY KEY,
        lesson_id      INTEGER NOT NULL REFERENCES learning_lessons(id) ON DELETE CASCADE,
        question       TEXT    NOT NULL,
        option_a       TEXT    NOT NULL,
        option_b       TEXT    NOT NULL,
        option_c       TEXT    NOT NULL DEFAULT '',
        option_d       TEXT    NOT NULL DEFAULT '',
        correct_answer VARCHAR(1) NOT NULL,
        explanation    TEXT    NOT NULL DEFAULT '',
        topic_slug     VARCHAR(100) NOT NULL DEFAULT ''
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_learning_progress (
        id           SERIAL  PRIMARY KEY,
        user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        level_id     INTEGER NOT NULL DEFAULT 0,
        module_id    INTEGER NOT NULL DEFAULT 0,
        lesson_id    INTEGER NOT NULL REFERENCES learning_lessons(id) ON DELETE CASCADE,
        completed    BOOLEAN NOT NULL DEFAULT FALSE,
        quiz_score   FLOAT,
        completed_at TIMESTAMP,
        UNIQUE(user_id, lesson_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_quiz_results (
        id              SERIAL  PRIMARY KEY,
        user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        lesson_id       INTEGER NOT NULL DEFAULT 0,
        question_id     INTEGER NOT NULL DEFAULT 0,
        selected_answer VARCHAR(1) NOT NULL,
        is_correct      BOOLEAN NOT NULL DEFAULT FALSE,
        answered_at     TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_learning_profile (
        id            SERIAL  PRIMARY KEY,
        user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
        weak_topics   TEXT    NOT NULL DEFAULT '[]',
        strong_topics TEXT    NOT NULL DEFAULT '[]',
        last_updated  TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_badges (
        id          SERIAL  PRIMARY KEY,
        user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        badge_type  VARCHAR(50) NOT NULL,
        earned_at   TIMESTAMP NOT NULL DEFAULT NOW(),
        UNIQUE(user_id, badge_type)
    )
    """,
]

# ── Enhanced Curriculum Data ─────────────────────────────────────────────────

_LEVELS = [
    (1, "Beginner",     "Master the basics of Forex trading from scratch. Learn market structure, pips, leverage, and essential risk management.", 1),
    (2, "Intermediate", "Build professional trading strategies using technical analysis. Master trends, support/resistance, patterns, and indicators.", 2),
    (3, "Advanced",     "Trade like an institution. Learn market structure, liquidity, smart money concepts, and build complete trading systems.", 3),
]

_MODULES = [
    # BEGINNER LEVEL
    (1, "Introduction to Forex Trading",      "What Forex is, how it works, and who the major players are in the global currency market.", 1),
    (1, "Currency Pairs and Price Quotes",    "Understanding majors, minors, and exotics. Reading pips, spreads, and calculating profit.", 2),
    (1, "Trading Sessions and Market Timing",  "When the major markets open and close. Best times to trade for maximum opportunity.", 3),
    (1, "Pips, Lots, and Leverage",           "Position sizing, margin requirements, and the power (and danger) of leverage.", 4),
    (1, "Basic Risk Management",              "The 1-2% rule, stop losses, take profits, and protecting your trading capital.", 5),
    (1, "Introduction to Trading Charts",       "Reading candlesticks, identifying trends, and drawing support/resistance levels.", 6),
    (1, "Your First Trading Strategy",        "Putting it all together: a simple, rule-based strategy for beginners.", 7),
    
    # INTERMEDIATE LEVEL
    (2, "Technical Analysis Fundamentals",    "The framework for analyzing price action and predicting future movements.", 1),
    (2, "Trend Identification and Analysis",  "Using swing highs/lows, moving averages, and multi-timeframe analysis.", 2),
    (2, "Advanced Support and Resistance",    "Dynamic levels, trendlines, channels, and Fibonacci retracements.", 3),
    (2, "Chart Patterns Recognition",         "Reversal and continuation patterns: Head & Shoulders, Triangles, Flags.", 4),
    (2, "Candlestick Patterns",               "Reading price action: Pin bars, Engulfing patterns, Doji, and Morning Star.", 5),
    (2, "Trading Indicators",                 "MACD, RSI, Stochastic, and Moving Averages. Using indicators properly.", 6),
    (2, "Building Trading Strategies",        "Creating rule-based systems with clear entry, exit, and risk parameters.", 7),
    
    # ADVANCED LEVEL
    (3, "Market Structure Analysis",          "BOS, CHoCH, order blocks, fair value gaps, and institutional footprints.", 1),
    (3, "Liquidity and Institutional Trading", "Understanding how smart money operates: Liquidity sweeps, stop hunts, mitigation.", 2),
    (3, "Advanced Risk Management",           "Portfolio heat, correlated pairs, drawdown management, and position sizing.", 3),
    (3, "Trading Psychology Mastery",         "Emotional control, discipline, FOMO management, and developing trader mindset.", 4),
    (3, "Strategy Development and Backtesting", "Building robust systems, forward testing, and measuring statistical edge.", 5),
    (3, "Creating Your Trading Plan",         "Combining all elements into a professional trading business plan.", 6),
]

_LESSONS = [
    # ═════════════════════════════════════════════════════════════════════════
    # BEGINNER LEVEL - Module 1: Introduction to Forex Trading
    # ═════════════════════════════════════════════════════════════════════════
    (1, 1, "What is Forex Trading?", 
     """Forex (Foreign Exchange) is the global decentralized marketplace where currencies are traded. With over $7.5 trillion traded daily, it's the largest and most liquid financial market in the world.

## Why Trade Forex?

**24-Hour Market:** Trade from Sunday evening to Friday evening, following the sun across major financial centers (Sydney, Tokyo, London, New York).

**High Liquidity:** Enter and exit positions easily, even with large amounts. The market is so large that no single entity can control it.

**Low Barriers to Entry:** Start with as little as $100 and trade from anywhere with an internet connection.

**Profit Potential:** Unlike stocks, you can profit from both rising AND falling markets by going long or short.

## How Currency Trading Works

Currencies are quoted in pairs. The first currency (EUR) is the **base**, the second (USD) is the **quote**.
