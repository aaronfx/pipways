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


# ══════════════════════════════════════════════════════════════════════════════
# LEARNING ACADEMY TABLES  (used by academy.js + learning.py)
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
]

# ── Default curriculum data ───────────────────────────────────────────────────

_LEVELS = [
    (1, "Beginner",     "Master the basics of Forex trading from scratch.", 1),
    (2, "Intermediate", "Build strategies using technical analysis tools.", 2),
    (3, "Advanced",     "Trade like an institution — market structure and liquidity.", 3),
]

_MODULES = [
    # (level_id, title, description, order_index)
    # BEGINNER
    (1, "Introduction to Forex Trading",   "What Forex is and who trades it.",                        1),
    (1, "Currency Pairs and Price Quotes",  "Majors, minors, exotics, pips, and spreads.",             2),
    (1, "Trading Sessions and Market Timing","When the markets are most active.",                      3),
    (1, "Pips, Lots, and Leverage",         "Position sizing and leverage explained.",                 4),
    (1, "Basic Risk Management",            "Stop loss, take profit, and the 1-2% rule.",              5),
    (1, "Introduction to Trading Charts",   "Candlestick charts and support/resistance basics.",       6),
    # INTERMEDIATE
    (2, "Technical Analysis Fundamentals",  "Trend identification and chart reading.",                 1),
    (2, "Support and Resistance",           "Drawing levels that professionals actually use.",         2),
    (2, "Chart Patterns",                   "Reversals and continuations — flags, H&S, triangles.",    3),
    (2, "Candlestick Patterns",             "Pin bars, engulfing candles, doji patterns.",             4),
    (2, "Trading Indicators",               "MACD, RSI, and Moving Averages used properly.",           5),
    (2, "Trading Strategies",               "Building a complete, rule-based trading strategy.",       6),
    # ADVANCED
    (3, "Market Structure",                 "BOS, CHoCH, order blocks, and fair value gaps.",          1),
    (3, "Liquidity and Institutional Trading","Stop hunts, liquidity pools, and smart money.",         2),
    (3, "Advanced Risk Management",         "Portfolio risk, correlated pairs, drawdown management.",  3),
    (3, "Trading Psychology",               "Emotional control, discipline, and process thinking.",    4),
    (3, "Strategy Development",             "Backtesting, forward testing, and edge calculation.",     5),
    (3, "Building a Complete Trading System","Combining all elements into a professional plan.",       6),
]

# (module_order, lesson_order, title, content_snippet)
_LESSONS = [
    # BEGINNER — Module 1
    (1, 1, "What is Forex?", "Forex (Foreign Exchange) is the global marketplace where currencies are bought and sold — over $7.5 trillion traded every day.\n\n## Why Trade Forex?\n- 24/5 market access\n- High liquidity\n- Low barriers to entry\n- Profit from rising AND falling markets\n\n## How it Works\nCurrencies trade in pairs. EUR/USD = 1.0850 means 1 Euro buys 1.0850 US Dollars. You profit when you correctly predict which direction the rate moves.\n\n**Trade Example**\nPair: EUR/USD | Direction: Buy | Entry: 1.0850 | Stop: 1.0800 | Target: 1.0950\nRisk: 50 pips | Reward: 100 pips | R:R = 1:2"),
    (1, 2, "Who Trades Forex?", "## Market Participants\n\n**Central Banks** — set interest rates, most powerful players.\n**Commercial Banks** — JP Morgan, Goldman Sachs execute trillions daily.\n**Corporations** — convert foreign earnings (Apple, Nike, etc.).\n**Retail Traders** — you. Less than 5% of total volume.\n\n## Key Insight\nTrade WITH institutional flow, not against it. Price moves when large participants need to buy or sell."),
    # BEGINNER — Module 2
    (2, 1, "Major, Minor and Exotic Pairs", "## Major Pairs (Always include USD)\n- EUR/USD — most traded\n- GBP/USD — 'Cable'\n- USD/JPY — dollar vs yen\n- USD/CHF — safe haven\n\n## Minors (No USD)\nEUR/GBP, GBP/JPY, AUD/JPY\n\n## Exotics\nUSD/ZAR, EUR/TRY — wide spreads, not for beginners.\n\n**Rule:** Start with EUR/USD. Tight spreads, abundant analysis."),
    (2, 2, "Reading Pips and Spreads", "## What is a Pip?\nA pip = 0.0001 move on most pairs. EUR/USD from 1.0850 to 1.0860 = 10 pips.\n\n## Pip Value\n- Standard lot (100k units): ~$10/pip\n- Mini lot (10k): ~$1/pip\n- Micro lot (1k): ~$0.10/pip\n\n## Spread\nBid vs Ask difference. Your cost to trade. EUR/USD: 0.1–0.5 pip."),
    # BEGINNER — Module 5
    (5, 1, "The 1-2% Rule", "**Never risk more than 1–2% of your account on a single trade.**\n\n## Example\n$10,000 account × 2% = $200 max risk.\nStop = 50 pips → lot size = 200 ÷ 50 ÷ 10 = 0.4 lots.\n\n## Why This Works\nWith 2% risk you need 50 consecutive losses to blow the account. With 10% risk, only 10 losses wipe you out."),
    (5, 2, "Stop Loss and Take Profit", "Every trade must have BOTH before you click.\n\n## Stop Loss Placement\n- Buys: below support\n- Sells: above resistance\n\n## Take Profit\nMinimum 1:2 R:R — risk $100 to make $200.\n\n**Trade Example**\nEUR/USD Buy at 1.0850 | Stop: 1.0800 | Target: 1.0950\nRisk: 50 pips | Reward: 100 pips ✓"),
    # BEGINNER — Module 6
    (6, 1, "Candlestick Charts Explained", "## Candle Anatomy\n- **Open** — start of period\n- **Close** — end of period\n- **High / Low** — extremes\n- Green = bullish (close > open)\n- Red = bearish (close < open)\n\n## Key Patterns\n- **Doji** — indecision\n- **Pin Bar** — rejection of a level\n- **Engulfing** — potential reversal"),
    (6, 2, "Support and Resistance", "## Support\nA price floor where buyers historically step in. Price falls → hits support → bounces.\n\n## Resistance\nA price ceiling where sellers historically appear. Price rises → hits resistance → falls.\n\n## Role Reversal\nBroken resistance becomes new support. This is one of the most reliable patterns in trading.\n\n**Drawing Rule:** Need 2+ touches to call a level significant."),
    # INTERMEDIATE — Module 7 (index 7 in modules list)
    (7, 1, "Identifying Trends", "## Uptrend\nHigher Highs (HH) + Higher Lows (HL).\n\n## Downtrend\nLower Highs (LH) + Lower Lows (LL).\n\n## Trend Confirmation\n- Price above 200 EMA = bullish bias\n- Price below 200 EMA = bearish bias\n- Trade WITH the higher timeframe trend.\n\n**Rule:** Always check the daily chart trend before entering on H1."),
    (7, 2, "Multi-Timeframe Analysis", "## The Concept\nUse higher timeframes for direction, lower timeframes for entry.\n\n**Process:**\n1. Daily chart: identify trend\n2. H4 chart: find key level (support/resistance)\n3. H1 chart: wait for entry signal\n\nThis is how professional traders time entries with minimal risk."),
    # INTERMEDIATE — Module 11 (indicators)
    (11, 1, "MACD and RSI", "## RSI\nMeasures momentum 0–100.\n- Above 70: overbought\n- Below 30: oversold\n- **Divergence**: price new high but RSI lower high = reversal warning\n\n## MACD\n- MACD line crosses above signal = bullish momentum\n- MACD line crosses below signal = bearish momentum\n- Histogram shows momentum strength\n\n**Rule:** Use divergence signals, not overbought/oversold levels alone."),
    (11, 2, "Moving Averages", "## Types\n- **SMA** — equal weight all periods\n- **EMA** — more weight to recent (faster)\n\n## Key Levels\n20 EMA (short-term) | 50 EMA (medium) | 200 EMA (long-term trend)\n\n## Golden/Death Cross\n50 EMA crosses 200 EMA up = Golden Cross (bullish)\n50 EMA crosses 200 EMA down = Death Cross (bearish)"),
    # ADVANCED — Module 13
    (13, 1, "Market Structure: BOS and CHoCH", "## Break of Structure (BOS)\nPrice breaks a previous swing high (uptrend) or low (downtrend).\nBOS = trend continuation confirmed.\n\n## Change of Character (CHoCH)\nIn an uptrend: price breaks BELOW the last swing low.\nFirst warning of potential reversal.\n\n## Order Blocks\nLast bearish candle before a bullish impulse = institutional order block.\nPrice returns to this zone = high-probability entry."),
    (13, 2, "Fair Value Gaps", "A Fair Value Gap (FVG) is a 3-candle pattern where price moves so fast it leaves a gap between candle 1's high and candle 3's low.\n\nThese gaps are market inefficiencies that price tends to revisit before continuing.\n\n**Setup:** Order Block + FVG fill + BOS confirmation = highest probability entries in institutional trading."),
    # ADVANCED — Module 14 (liquidity)
    (14, 1, "Liquidity Pools and Stop Hunts", "## What is Liquidity?\nInstitutions need liquidity to fill large orders. Stop losses cluster above swing highs and below swing lows.\n\n## The Stop Hunt\nPrice sweeps above equal highs → triggers buy stops → institutions SELL into liquidity.\nPrice sweeps below equal lows → triggers sell stops → institutions BUY.\n\n## How to Use It\nWait for the sweep candle. Enter AFTER the sweep reverses. This is the cleaner entry."),
    # ADVANCED — Module 16 (psychology)
    (16, 1, "The Psychology of Trading", "## The Four Deadly Emotions\n1. **Fear** — cutting winners, missing valid setups\n2. **Greed** — holding past targets, overtrading\n3. **Hope** — not taking stop losses\n4. **Revenge** — trading immediately after a loss\n\n## Solution\n- Max 2 losses per session, then STOP\n- Pre-trade checklist (written)\n- Judge trades by process, not outcome\n- Keep a detailed journal"),
]

_QUIZ_DATA = [
    # (lesson_title, question, A, B, C, D, correct, explanation, topic_slug)
    ("What is Forex?",
     "What does EUR/USD = 1.0850 mean?",
     "1 USD buys 1.0850 Euros", "1 EUR buys 1.0850 USD", "Both currencies cost 1.0850", "EUR is stronger by 8.5%",
     "B", "In Forex quotes the base currency (EUR) is always 1 unit. EUR/USD = 1.0850 means 1 Euro buys 1.0850 US Dollars.", "forex_basics"),

    ("The 1-2% Rule",
     "With a $5,000 account using 2% risk and a 50-pip stop on EUR/USD, what is the correct lot size?",
     "1.0 standard lot", "0.2 mini lots", "5.0 micro lots", "0.02 standard lots",
     "B", "$5,000 × 2% = $100 risk. $100 ÷ 50 pips ÷ $1/pip per mini lot = 2 mini lots. 0.2 standard = 2 mini lots.", "risk_management"),

    ("Stop Loss and Take Profit",
     "What is the minimum risk-to-reward ratio professionals recommend?",
     "1:1", "1:2", "1:3", "2:1",
     "B", "A 1:2 R:R means you risk $1 to make $2. This means you only need to win 35-40% of trades to be profitable over time.", "risk_reward"),

    ("Candlestick Charts Explained",
     "What does a bearish engulfing candle signal?",
     "The trend is continuing upward", "Strong buying pressure has entered", "Sellers have overwhelmed buyers — potential reversal", "Price is consolidating",
     "C", "A bearish engulfing candle has a red body that completely covers the previous green candle. It signals sellers have overwhelmed buyers and a downward reversal may follow.", "candlestick_patterns"),

    ("Support and Resistance",
     "What is 'role reversal' in technical analysis?",
     "When two traders swap positions", "When broken resistance becomes new support", "When the trend reverses completely", "When price gaps through a level",
     "B", "Role reversal is when a previously broken resistance level now acts as support (or vice versa). It's one of the most reliable patterns in all of technical analysis.", "support_resistance"),

    ("Identifying Trends",
     "In a confirmed uptrend using price action, what pattern must you see?",
     "Lower highs and lower lows", "Higher highs and higher lows", "Equal highs and random lows", "Price above the 200 EMA only",
     "B", "An uptrend is technically defined as a series of Higher Highs (HH) AND Higher Lows (HL). Both conditions must be present for a confirmed uptrend.", "trend_analysis"),

    ("MACD and RSI",
     "RSI divergence occurs when:",
     "Price and RSI both make new highs", "Price makes a new high but RSI makes a lower high", "RSI goes above 70", "Price and RSI both go below 30",
     "B", "Bullish divergence: price new low, RSI higher low. Bearish divergence: price new high, RSI lower high. Divergence signals momentum is weakening before price confirms the reversal.", "indicators"),

    ("Market Structure: BOS and CHoCH",
     "What is a Change of Character (CHoCH) in an uptrend?",
     "A new higher high is formed", "Price breaks BELOW the most recent swing low", "The 50 EMA crosses the 200 EMA", "Price reaches a round number",
     "B", "CHoCH in an uptrend = price breaks below the last swing low, breaking the HH/HL structure. It's the first warning that the uptrend may be ending. Not a confirmed reversal until structure flips.", "market_structure"),

    ("Liquidity Pools and Stop Hunts",
     "Why do institutions 'stop hunt' above obvious resistance levels?",
     "To drive price higher for retail traders", "To trigger buy stops and sell into the liquidity created", "To test the strength of resistance", "To confuse technical analysts",
     "B", "Institutions need large order flow to fill their positions. Sweeping above resistance triggers retail buy stops, creating the liquidity institutions need to sell. The apparent 'breakout' is engineered to fill institutional orders.", "liquidity"),

    ("The Psychology of Trading",
     "What is 'revenge trading'?",
     "Trading a currency pair you previously lost on", "Entering a trade immediately after a loss to recover it", "Trading against the trend out of frustration", "Doubling position size after a win",
     "B", "Revenge trading is entering a new trade immediately after a loss driven by the desire to 'make it back.' It is emotional, unplanned, and almost always results in a second larger loss.", "psychology"),
]


async def _seed_curriculum() -> None:
    """Insert the default 3-level curriculum if tables are empty."""
    existing = await database.fetch_val("SELECT COUNT(*) FROM learning_levels")
    if existing and int(existing) > 0:
        print("[LMS INIT] Curriculum already seeded — skipping", flush=True)
        return

    # Insert levels
    level_ids = {}
    for order_id, name, desc, order in _LEVELS:
        lid = await database.execute(
            "INSERT INTO learning_levels (name, description, order_index) VALUES (:n,:d,:o) RETURNING id",
            {"n": name, "d": desc, "o": order}
        )
        level_ids[order_id] = lid
        print(f"[LMS INIT] Level created: {name} (id={lid})", flush=True)

    # Insert modules — store (level_order, module_order) → module_id
    module_ids = {}  # key = (level_order, module_order_within_level)
    level_module_counters = {}
    for level_order, title, desc, global_order in _MODULES:
        lid = level_ids[level_order]
        cnt = level_module_counters.get(level_order, 0) + 1
        level_module_counters[level_order] = cnt
        mid = await database.execute(
            "INSERT INTO learning_modules (level_id, title, description, order_index) VALUES (:l,:t,:d,:o) RETURNING id",
            {"l": lid, "t": title, "d": desc, "o": global_order}
        )
        module_ids[(level_order, cnt)] = mid

    # We need a flat mapping from global module index (1-based) to module_id
    global_module_list = []
    for level_order in [1, 2, 3]:
        for mod_order in range(1, level_module_counters.get(level_order, 0) + 1):
            global_module_list.append(module_ids[(level_order, mod_order)])

    # Insert lessons — _LESSONS use (module_global_index, lesson_order, ...)
    lesson_ids = {}  # key = lesson title
    for mod_global_idx, lesson_order, title, content in _LESSONS:
        if mod_global_idx < 1 or mod_global_idx > len(global_module_list):
            print(f"[LMS INIT] Lesson skip — invalid module index {mod_global_idx}", flush=True)
            continue
        mid = global_module_list[mod_global_idx - 1]
        lid = await database.execute(
            "INSERT INTO learning_lessons (module_id, title, content, order_index) VALUES (:m,:t,:c,:o) RETURNING id",
            {"m": mid, "t": title, "c": content, "o": lesson_order}
        )
        lesson_ids[title] = lid

    # Insert quiz questions
    for lesson_title, question, a, b, c, d, correct, explanation, slug in _QUIZ_DATA:
        lid = lesson_ids.get(lesson_title)
        if not lid:
            continue
        try:
            await database.execute(
                "INSERT INTO lesson_quizzes (lesson_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation, topic_slug) "
                "VALUES (:lid,:q,:a,:b,:c,:d,:correct,:expl,:slug)",
                {"lid": lid, "q": question, "a": a, "b": b, "c": c, "d": d,
                 "correct": correct, "expl": explanation, "slug": slug}
            )
        except Exception as e:
            print(f"[LMS INIT] Quiz insert warn: {e}", flush=True)

    print("[LMS INIT] Academy curriculum seeded — 3 levels, 18 modules, lessons + quizzes", flush=True)


async def init_lms_tables() -> None:
    """
    1. Add missing columns to `courses`.
    2. Create CMS LMS tables (course_modules, lessons, quizzes...).
    3. Create Academy tables (learning_levels, learning_modules...).
    4. Seed default curriculum if empty.
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

    # Step 2 — create CMS LMS tables
    for sql in _TABLE_SQLS:
        try:
            await database.execute(sql.strip())
            ok += 1
        except Exception as e:
            warn += 1
            print(f"[LMS INIT] table warn: {e}", flush=True)

    # Step 3 — create Academy tables
    for sql in _LEARNING_TABLE_SQLS:
        try:
            await database.execute(sql.strip())
            ok += 1
        except Exception as e:
            warn += 1
            print(f"[LMS INIT] learning table warn: {e}", flush=True)

    print(f"[LMS INIT] Done — {ok} ok, {warn} warnings", flush=True)

    # Step 4 — seed curriculum
    try:
        await _seed_curriculum()
    except Exception as e:
        print(f"[LMS INIT] Seed warn: {e}", flush=True)
