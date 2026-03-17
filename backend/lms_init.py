"""
LMS Table Initialisation — Pipways Learning Management System  v2
Creates all learning-related tables idempotently.
Called from main.py lifespan — safe to run multiple times.
Does NOT touch any existing tables.

v2 changes vs v1:
  • lesson_quizzes includes topic_slug column
  • Idempotent ALTER TABLE adds topic_slug to existing tables (v1 → v2 upgrade)
  • Richer default curriculum with more lessons
"""
from .database import database


async def init_lms_tables() -> None:
    statements = [
        """CREATE TABLE IF NOT EXISTS learning_levels (
            id          SERIAL PRIMARY KEY,
            name        VARCHAR(100) NOT NULL UNIQUE,
            description TEXT         DEFAULT '',
            order_index INTEGER      DEFAULT 0,
            created_at  TIMESTAMP    DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS learning_modules (
            id          SERIAL PRIMARY KEY,
            level_id    INTEGER      NOT NULL REFERENCES learning_levels(id) ON DELETE CASCADE,
            title       VARCHAR(255) NOT NULL,
            description TEXT         DEFAULT '',
            order_index INTEGER      DEFAULT 0,
            created_at  TIMESTAMP    DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS learning_lessons (
            id          SERIAL PRIMARY KEY,
            module_id   INTEGER      NOT NULL REFERENCES learning_modules(id) ON DELETE CASCADE,
            title       VARCHAR(255) NOT NULL,
            content     TEXT         DEFAULT '',
            order_index INTEGER      DEFAULT 0,
            created_at  TIMESTAMP    DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS lesson_quizzes (
            id             SERIAL PRIMARY KEY,
            lesson_id      INTEGER     NOT NULL REFERENCES learning_lessons(id) ON DELETE CASCADE,
            question       TEXT        NOT NULL,
            option_a       TEXT        NOT NULL,
            option_b       TEXT        NOT NULL,
            option_c       TEXT        NOT NULL,
            option_d       TEXT        NOT NULL,
            correct_answer VARCHAR(1)  NOT NULL CHECK (correct_answer IN ('A','B','C','D')),
            explanation    TEXT        DEFAULT '',
            topic_slug     VARCHAR(100) DEFAULT 'general'
        )""",
        """CREATE TABLE IF NOT EXISTS user_learning_progress (
            id           SERIAL PRIMARY KEY,
            user_id      INTEGER   NOT NULL,
            level_id     INTEGER   REFERENCES learning_levels(id),
            module_id    INTEGER   REFERENCES learning_modules(id),
            lesson_id    INTEGER   REFERENCES learning_lessons(id),
            completed    BOOLEAN   DEFAULT FALSE,
            quiz_score   FLOAT     DEFAULT 0,
            completed_at TIMESTAMP,
            UNIQUE (user_id, lesson_id)
        )""",
        """CREATE TABLE IF NOT EXISTS user_quiz_results (
            id              SERIAL PRIMARY KEY,
            user_id         INTEGER   NOT NULL,
            lesson_id       INTEGER   REFERENCES learning_lessons(id),
            question_id     INTEGER   REFERENCES lesson_quizzes(id),
            selected_answer VARCHAR(1),
            is_correct      BOOLEAN   DEFAULT FALSE,
            answered_at     TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS user_learning_profile (
            id            SERIAL PRIMARY KEY,
            user_id       INTEGER   NOT NULL UNIQUE,
            weak_topics   JSONB     DEFAULT '[]',
            strong_topics JSONB     DEFAULT '[]',
            last_updated  TIMESTAMP DEFAULT NOW()
        )""",
    ]

    for sql in statements:
        try:
            await database.execute(sql.strip())
        except Exception as e:
            print(f"[LMS INIT] Table note: {e}", flush=True)

    # Idempotent v1→v2 migration: add topic_slug if missing
    try:
        await database.execute(
            "ALTER TABLE lesson_quizzes ADD COLUMN IF NOT EXISTS topic_slug VARCHAR(100) DEFAULT 'general'"
        )
    except Exception as e:
        print(f"[LMS INIT] topic_slug migration: {e}", flush=True)

    try:
        count = await database.fetch_val("SELECT COUNT(*) FROM learning_levels")
        if count == 0:
            await _seed_curriculum()
    except Exception as e:
        print(f"[LMS INIT] Seed error: {e}", flush=True)

    print("[LMS INIT] All LMS tables ready", flush=True)


async def _insert_quiz(lesson_id: int, questions: list) -> None:
    for q in questions:
        await database.execute(
            "INSERT INTO lesson_quizzes "
            "(lesson_id,question,option_a,option_b,option_c,option_d,correct_answer,explanation,topic_slug) "
            "VALUES (:lid,:q,:a,:b,:c,:d,:ca,:ex,:ts)",
            {"lid": lesson_id, "q": q["question"],
             "a": q["a"], "b": q["b"], "c": q["c"], "d": q["d"],
             "ca": q["correct"], "ex": q["explanation"], "ts": q.get("slug", "general")}
        )


async def _seed_curriculum() -> None:
    print("[LMS INIT] Seeding default curriculum…", flush=True)

    levels = [
        ("Beginner",     "Master the basics of Forex trading from scratch.", 1),
        ("Intermediate", "Build strategies using technical analysis tools.",  2),
        ("Advanced",     "Trade like an institution — market structure and liquidity.", 3),
    ]
    level_ids = {}
    for name, desc, order in levels:
        lid = await database.fetch_val(
            "INSERT INTO learning_levels (name,description,order_index) VALUES (:n,:d,:o) RETURNING id",
            {"n": name, "d": desc, "o": order}
        )
        level_ids[name] = lid

    # ── BEGINNER ──────────────────────────────────────────────────────────
    b = level_ids["Beginner"]

    m1 = await database.fetch_val(
        "INSERT INTO learning_modules (level_id,title,description,order_index) VALUES (:l,:t,:d,1) RETURNING id",
        {"l": b, "t": "Forex Foundations", "d": "Understand what Forex is and how the market works."}
    )

    l1 = await database.fetch_val(
        "INSERT INTO learning_lessons (module_id,title,content,order_index) VALUES (:m,:t,:c,1) RETURNING id",
        {"m": m1, "t": "What is Forex?", "c": _content_what_is_forex()}
    )
    await _insert_quiz(l1, [
        {"question": "What does Forex stand for?",
         "a": "Foreign Exchange", "b": "Forward Exchange", "c": "Financial Exchange", "d": "Future Exchange",
         "correct": "A", "explanation": "Forex = Foreign Exchange — the global currency market.", "slug": "forex_basics"},
        {"question": "In EUR/USD, which is the base currency?",
         "a": "USD", "b": "EUR", "c": "Both", "d": "Neither",
         "correct": "B", "explanation": "The base currency is always listed first in a pair.", "slug": "currency_pairs"},
        {"question": "Approximately how much is traded in Forex daily?",
         "a": "$100 million", "b": "$1 billion", "c": "$7 trillion", "d": "$500 billion",
         "correct": "C", "explanation": "Forex trades over $7 trillion per day — the world's largest market.", "slug": "forex_basics"},
    ])

    l2 = await database.fetch_val(
        "INSERT INTO learning_lessons (module_id,title,content,order_index) VALUES (:m,:t,:c,2) RETURNING id",
        {"m": m1, "t": "Understanding Pips", "c": _content_pips()}
    )
    await _insert_quiz(l2, [
        {"question": "For EUR/USD, where is 1 pip measured?",
         "a": "1st decimal", "b": "2nd decimal", "c": "4th decimal", "d": "5th decimal",
         "correct": "C", "explanation": "1 pip = 0.0001 for most major pairs — the 4th decimal place.", "slug": "pips"},
        {"question": "EUR/USD moves 1.1000 → 1.1050. How many pips?",
         "a": "5 pips", "b": "50 pips", "c": "500 pips", "d": "0.5 pips",
         "correct": "B", "explanation": "0.0050 ÷ 0.0001 = 50 pips.", "slug": "pips"},
        {"question": "For JPY pairs, 1 pip is at which decimal?",
         "a": "4th", "b": "3rd", "c": "2nd", "d": "1st",
         "correct": "C", "explanation": "JPY pairs use the 2nd decimal place for pips (0.01).", "slug": "pips"},
    ])

    m2 = await database.fetch_val(
        "INSERT INTO learning_modules (level_id,title,description,order_index) VALUES (:l,:t,:d,2) RETURNING id",
        {"l": b, "t": "Risk Management Basics", "d": "Protect your capital before growing it."}
    )

    l3 = await database.fetch_val(
        "INSERT INTO learning_lessons (module_id,title,content,order_index) VALUES (:m,:t,:c,1) RETURNING id",
        {"m": m2, "t": "What is Risk Management?", "c": _content_risk()}
    )
    await _insert_quiz(l3, [
        {"question": "What is the recommended max risk per trade for beginners?",
         "a": "10%", "b": "5%", "c": "1–2%", "d": "50%",
         "correct": "C", "explanation": "Never risk more than 1–2% per trade to survive losing streaks.", "slug": "risk_management"},
        {"question": "What should you NEVER do when a trade moves against you?",
         "a": "Close the trade", "b": "Move stop loss further away", "c": "Accept the loss", "d": "Review entry",
         "correct": "B", "explanation": "Moving your stop loss away increases risk and breaks discipline.", "slug": "risk_management"},
        {"question": "On a $1,000 account with 1% risk, how much per trade?",
         "a": "$100", "b": "$1", "c": "$10", "d": "$50",
         "correct": "C", "explanation": "1% of $1,000 = $10. This is your maximum per-trade loss.", "slug": "risk_management"},
    ])

    l4 = await database.fetch_val(
        "INSERT INTO learning_lessons (module_id,title,content,order_index) VALUES (:m,:t,:c,2) RETURNING id",
        {"m": m2, "t": "Lot Sizes and Position Sizing", "c": _content_lots()}
    )
    await _insert_quiz(l4, [
        {"question": "How many units is a Standard Lot?",
         "a": "1,000", "b": "10,000", "c": "100,000", "d": "1,000,000",
         "correct": "C", "explanation": "Standard Lot = 100,000 units of the base currency.", "slug": "position_sizing"},
        {"question": "A Mini Lot represents how many units?",
         "a": "1,000", "b": "10,000", "c": "100,000", "d": "100",
         "correct": "B", "explanation": "Mini Lot = 10,000 units — 1/10th of a Standard Lot.", "slug": "position_sizing"},
    ])

    # ── INTERMEDIATE ──────────────────────────────────────────────────────
    i = level_ids["Intermediate"]

    m3 = await database.fetch_val(
        "INSERT INTO learning_modules (level_id,title,description,order_index) VALUES (:l,:t,:d,1) RETURNING id",
        {"l": i, "t": "Technical Analysis", "d": "Read charts using key indicators and concepts."}
    )

    l5 = await database.fetch_val(
        "INSERT INTO learning_lessons (module_id,title,content,order_index) VALUES (:m,:t,:c,1) RETURNING id",
        {"m": m3, "t": "Support and Resistance", "c": _content_sr()}
    )
    await _insert_quiz(l5, [
        {"question": "Support is best described as:",
         "a": "A price ceiling where sellers dominate", "b": "A price floor where buyers prevent decline",
         "c": "Market volatility", "d": "Trading volume",
         "correct": "B", "explanation": "Support is where buying pressure stops price from falling further.", "slug": "support_resistance"},
        {"question": "A strong S/R level has been:",
         "a": "Touched once", "b": "Tested and respected multiple times",
         "c": "Broken and never revisited", "d": "Only on the 1-minute chart",
         "correct": "B", "explanation": "Multiple touches confirm a level's significance — price has memory.", "slug": "support_resistance"},
        {"question": "When resistance is broken, it often becomes:",
         "a": "Irrelevant", "b": "New support", "c": "Immediate reversal", "d": "Unchanged",
         "correct": "B", "explanation": "Role reversal: broken resistance becomes new support.", "slug": "support_resistance"},
    ])

    l6 = await database.fetch_val(
        "INSERT INTO learning_lessons (module_id,title,content,order_index) VALUES (:m,:t,:c,2) RETURNING id",
        {"m": m3, "t": "Trend Analysis", "c": _content_trend()}
    )
    await _insert_quiz(l6, [
        {"question": "What defines an uptrend?",
         "a": "Lower highs and lower lows", "b": "Higher highs and higher lows",
         "c": "Sideways price", "d": "High volume",
         "correct": "B", "explanation": "Uptrend = series of higher highs and higher lows.", "slug": "trend_analysis"},
        {"question": "Which timeframe identifies the primary trend?",
         "a": "1-minute", "b": "5-minute", "c": "H4 or Daily", "d": "All equally",
         "correct": "C", "explanation": "Higher timeframes give the macro picture — always start there.", "slug": "trend_analysis"},
        {"question": "Counter-trend trading is best described as:",
         "a": "Recommended for beginners", "b": "Always profitable", "c": "High risk requiring advanced skill", "d": "Easier than trend trading",
         "correct": "C", "explanation": "Trading against the trend requires advanced skills — beginners should trade with it.", "slug": "trend_analysis"},
    ])

    l7 = await database.fetch_val(
        "INSERT INTO learning_lessons (module_id,title,content,order_index) VALUES (:m,:t,:c,3) RETURNING id",
        {"m": m3, "t": "Risk/Reward Ratios", "c": _content_rr()}
    )
    await _insert_quiz(l7, [
        {"question": "A 1:2 risk/reward ratio means:",
         "a": "Risk $2 to make $1", "b": "Risk $1 to make $2", "c": "Equal risk and reward", "d": "No losses",
         "correct": "B", "explanation": "1:2 = risk $1 to potentially gain $2.", "slug": "risk_reward"},
        {"question": "With a 40% win rate and 1:3 RR, are you profitable?",
         "a": "No, need 50% wins", "b": "Yes, winners outsize losers", "c": "Only with more trades", "d": "No",
         "correct": "B", "explanation": "40% × 3 = 1.2 vs 60% × 1 = 0.6. Net profit: 0.6 per trade.", "slug": "risk_reward"},
    ])

    # ── ADVANCED ──────────────────────────────────────────────────────────
    a = level_ids["Advanced"]

    m4 = await database.fetch_val(
        "INSERT INTO learning_modules (level_id,title,description,order_index) VALUES (:l,:t,:d,1) RETURNING id",
        {"l": a, "t": "Market Structure & Liquidity", "d": "Trade like institutions — order flow and smart money."}
    )

    l8 = await database.fetch_val(
        "INSERT INTO learning_lessons (module_id,title,content,order_index) VALUES (:m,:t,:c,1) RETURNING id",
        {"m": m4, "t": "Market Structure", "c": _content_structure()}
    )
    await _insert_quiz(l8, [
        {"question": "CHoCH stands for:",
         "a": "Continuation of Higher Chart Highs", "b": "Change of Character",
         "c": "Chart of Currency Highs", "d": "Consolidation at Higher Close",
         "correct": "B", "explanation": "CHoCH = Change of Character — a structural shift signalling potential reversal.", "slug": "market_structure"},
        {"question": "A bullish BOS means price has broken:",
         "a": "A previous low", "b": "A previous high", "c": "A support zone", "d": "A moving average",
         "correct": "B", "explanation": "Bullish BOS = price breaks above a prior swing high, confirming bullish trend continuation.", "slug": "market_structure"},
        {"question": "In a downtrend, what signals a possible reversal?",
         "a": "Another BOS lower", "b": "New lower low", "c": "Breaking a recent swing high (CHoCH)", "d": "Volume drop",
         "correct": "C", "explanation": "CHoCH in a downtrend = price breaks above a recent swing high for the first time.", "slug": "market_structure"},
    ])

    l9 = await database.fetch_val(
        "INSERT INTO learning_lessons (module_id,title,content,order_index) VALUES (:m,:t,:c,2) RETURNING id",
        {"m": m4, "t": "Liquidity and Order Blocks", "c": _content_liquidity()}
    )
    await _insert_quiz(l9, [
        {"question": "A liquidity pool is:",
         "a": "A savings account", "b": "A cluster of stop-loss orders institutions target",
         "c": "High volume on one candle", "d": "A support level",
         "correct": "B", "explanation": "Liquidity pools = clusters of stop-losses that institutions sweep to fill large orders.", "slug": "liquidity"},
        {"question": "An order block is best described as:",
         "a": "A blocked trade", "b": "The last opposing candle before a significant move",
         "c": "A chart gap", "d": "A lower-timeframe support",
         "correct": "B", "explanation": "Order block = last bearish candle before a bullish impulse (or vice versa) — where institutions placed orders.", "slug": "order_blocks"},
    ])

    print("[LMS INIT] Curriculum seeded successfully", flush=True)


# ── Lesson content ────────────────────────────────────────────────────────────

def _content_what_is_forex() -> str:
    return """## What is Forex?

**Simple Explanation**
Forex (Foreign Exchange) is the global marketplace where currencies are bought and sold — over $7 trillion traded every day.

**Step-by-Step Guide**
1. Currencies trade in pairs: EUR/USD, GBP/USD, USD/JPY.
2. The first currency = base. The second = quote.
3. EUR/USD = 1.0850 means 1 Euro buys 1.0850 US Dollars.
4. You profit by correctly predicting which direction the rate moves.
5. The market is open 24 hours, 5 days a week.

**Trade Example**
```
Pair:        EUR/USD
Direction:   Buy (expecting EUR to strengthen)
Entry:       1.0850
Stop Loss:   1.0820
Take Profit: 1.0910
```

**Common Mistakes**
- Trading without understanding what drives currency movements.
- Ignoring the base/quote relationship.
- Over-trading — start with one or two pairs only.

**Quick Summary**
Forex is the exchange of currencies. Currencies trade in pairs. The rate tells you how much quote currency buys one unit of base currency."""


def _content_pips() -> str:
    return """## Understanding Pips

**Simple Explanation**
A pip is the smallest standard price movement. For most pairs, 1 pip = 0.0001.

**Step-by-Step Guide**
1. Look at the 4th decimal place of a price.
2. EUR/USD: 1.0850 → 1.0851 = 1 pip.
3. JPY pairs: 1 pip = 0.01 (2nd decimal).
4. Pip value depends on your lot size.
5. A pipette (0.1 pip) is the 5th decimal on most platforms.

**Trade Example**
```
EUR/USD: 1.0850 → 1.0910 = 60 pips
0.1 lot (mini) @ $1/pip = $60 profit
```

**Common Mistakes**
- Confusing pips with pipettes.
- Not accounting for spread (broker fee in pips).

**Quick Summary**
Pips measure price movement. 4th decimal for most pairs, 2nd decimal for JPY. Know your pip value before trading."""


def _content_risk() -> str:
    return """## What is Risk Management?

**Simple Explanation**
Risk management controls how much you can lose on any trade. Protect capital first — profits follow.

**Step-by-Step Guide**
1. Set maximum risk: 1% of account per trade.
2. Place stop loss at a logical market level.
3. Calculate pip distance to stop loss.
4. Size your position so dollar risk = 1%.
5. Never move stop loss further once in a trade.

**Trade Example**
```
Account:    $1,000
Risk 1%:    $10
Stop Loss:  20 pips
Pip value:  $0.10 (micro lot)
Max lots:   5 micro lots (0.05)
```

**Common Mistakes**
- Risking >2% — a 10-loss streak wipes 20% of account.
- No stop loss — "I'll watch it" destroys accounts.
- Moving stop loss away when losing.

**Quick Summary**
Max 1–2% risk per trade. Always use a stop loss. Capital preservation is job one."""


def _content_lots() -> str:
    return """## Lot Sizes and Position Sizing

**Simple Explanation**
A lot is how much currency you trade. Correct lot sizing is critical to risk control.

**Lot Types**
- Standard Lot = 100,000 units → ~$10/pip
- Mini Lot = 10,000 units → ~$1/pip
- Micro Lot = 1,000 units → ~$0.10/pip
- Nano Lot = 100 units → ~$0.01/pip

**Position Sizing Formula**
```
Lot Size = Risk ($) ÷ (Stop Pips × Pip Value)

$10 risk ÷ (20 pips × $0.10) = 5 micro lots
```

**Common Mistakes**
- Same lot every trade regardless of stop distance.
- Trading standards on small accounts.

**Quick Summary**
Always calculate lot size from your risk amount. Never guess it."""


def _content_sr() -> str:
    return """## Support and Resistance

**Simple Explanation**
Support = price floor. Resistance = price ceiling.

**Step-by-Step Guide**
1. Find levels where price bounced at least twice.
2. Draw a horizontal line through those areas.
3. More touches = stronger level.
4. Look for price action signals (pin bars, engulfing candles) AT the level.
5. Treat levels as zones, not single lines.

**Trade Example**
```
Pair:      EUR/USD
Resistance: 1.1000 (3 previous rejections)
Action:    Bearish pin bar forms at 1.1000
Entry:     1.0995 sell
Stop:      1.1020
Target:    1.0930
```

**Common Mistakes**
- Drawing too many lines — keep only the 3–5 most significant.
- Expecting exact pip touches.

**Quick Summary**
Support and resistance are the foundation of TA. Strong levels have multiple touches. Broken resistance often becomes support."""


def _content_trend() -> str:
    return """## Trend Analysis

**Simple Explanation**
The trend is your friend. Trading with it maximises probability.

**Step-by-Step Guide**
1. Uptrend = higher highs + higher lows.
2. Downtrend = lower highs + lower lows.
3. Sideways = range — trade the range or stay out.
4. Identify primary trend on Daily chart.
5. Find entries on H4/H1 in the trend direction.

**Trade Example**
```
Daily:  Uptrend confirmed
H1:     Price pulls back to 1.0800 support
Entry:  Buy 1.0805
Stop:   1.0770
Target: 1.0900
```

**Common Mistakes**
- Counter-trend trading without advanced skills.
- Entering too late near key resistance.

**Quick Summary**
Identify higher-TF trend first. Enter on pullbacks. Never fight the trend."""


def _content_rr() -> str:
    return """## Risk/Reward Ratios

**Simple Explanation**
R:R ratio = what you stand to gain vs what you risk. Minimum target: 1:2.

**Step-by-Step Guide**
1. Risk = entry to stop loss in pips.
2. Reward = entry to target in pips.
3. R:R = reward ÷ risk.
4. Only trade if R:R ≥ 1:2.
5. Good R:R = profitable even with a low win rate.

**Trade Example**
```
Entry:  1.0850
Stop:   1.0820  →  Risk = 30 pips
Target: 1.0920  →  Reward = 70 pips
R:R:    1:2.3
```

**Common Mistakes**
- Taking 1:1 or worse trades — requires >50% win rate just to break even.
- Moving TP closer and ruining the R:R.

**Quick Summary**
Always calculate R:R before entering. Aim for 1:2 minimum."""


def _content_structure() -> str:
    return """## Market Structure

**Simple Explanation**
Market structure = the pattern of highs and lows revealing who controls the market.

**Key Concepts**
- BOS (Break of Structure): price breaks a prior swing high/low → trend continuation.
- CHoCH (Change of Character): price breaks structure IN THE OPPOSITE DIRECTION → potential reversal.
- Internal vs External structure.

**Step-by-Step Guide**
1. Mark swing highs and lows on H4/Daily.
2. BOS = expect continuation.
3. CHoCH = watch for reversal setup.
4. Wait for confirmed candle close beyond the level.

**Trade Example**
```
Downtrend → CHoCH forms (price breaks swing high)
Bias:  Bullish
Entry: Buy pullback to demand zone
Stop:  Below last swing low
Target: Next swing high (liquidity)
```

**Common Mistakes**
- Treating every bounce as a CHoCH.
- Not waiting for candle confirmation.

**Quick Summary**
BOS = continue. CHoCH = reversal signal. Trade with structure, not against it."""


def _content_liquidity() -> str:
    return """## Liquidity and Order Blocks

**Simple Explanation**
Institutions need massive volume. They target retail stop-loss clusters (liquidity pools) to fill their own orders. Understanding this gives a real edge.

**Key Concepts**
- Liquidity Pool: cluster of stops above swing highs / below swing lows.
- Order Block: last opposing candle before an impulse — where institutions entered.
- Fair Value Gap (FVG): imbalance left by rapid institutional moves — price often returns.

**Step-by-Step Guide**
1. Identify swing highs/lows → liquidity pools sit just beyond them.
2. When price sweeps above highs then reverses — institutions hunted stops.
3. Find the order block (last bullish candle before a bearish drop, or vice versa).
4. Wait for price to return to the OB.
5. Enter at the OB with stop beyond it.

**Trade Example**
```
EUR/USD sweeps above equal highs (1.1010) then drops sharply
Order Block: 1.0900–1.0910
Entry:  Sell at 1.0905 on OB return
Stop:   1.0925
Target: 1.0820 (liquidity below equal lows)
```

**Common Mistakes**
- Trading every candle as an OB — be selective.
- Ignoring the higher-timeframe bias.

**Quick Summary**
Institutions move markets. Follow their footprint via liquidity sweeps and order blocks."""
