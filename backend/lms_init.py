"""
LMS Auto-Initialisation — Bulletproof Edition (PATCHED v2.1)
Changes:
- Added first_academy_visit column to user_learning_profile
- init_lms_tables() now auto-seeds curriculum if empty (idempotent)
"""
from .database import database

_COURSE_COLUMNS = [
    ("price", "FLOAT NOT NULL DEFAULT 0"),
    ("thumbnail", "VARCHAR(500) NOT NULL DEFAULT ''"),
    ("thumbnail_url", "VARCHAR(500) NOT NULL DEFAULT ''"),
    ("preview_video", "VARCHAR(500) NOT NULL DEFAULT ''"),
    ("is_published", "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("is_active", "BOOLEAN NOT NULL DEFAULT TRUE"),
    ("certificate_enabled", "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("pass_percentage", "INTEGER NOT NULL DEFAULT 70"),
    ("instructor", "VARCHAR(255) NOT NULL DEFAULT ''"),
]

_TABLE_SQLS = [
    """CREATE TABLE IF NOT EXISTS course_modules (
        id SERIAL PRIMARY KEY,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        order_index INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS lessons (
        id SERIAL PRIMARY KEY,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        module_id INTEGER REFERENCES course_modules(id) ON DELETE SET NULL,
        title VARCHAR(255) NOT NULL,
        content TEXT NOT NULL DEFAULT '',
        video_url VARCHAR(500) NOT NULL DEFAULT '',
        attachment_url VARCHAR(500) NOT NULL DEFAULT '',
        duration_minutes INTEGER NOT NULL DEFAULT 0,
        order_index INTEGER NOT NULL DEFAULT 0,
        is_free_preview BOOLEAN NOT NULL DEFAULT FALSE,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS quizzes (
        id SERIAL PRIMARY KEY,
        module_id INTEGER NOT NULL REFERENCES course_modules(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        pass_percentage INTEGER NOT NULL DEFAULT 70,
        max_attempts INTEGER NOT NULL DEFAULT 3,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS quiz_questions (
        id SERIAL PRIMARY KEY,
        quiz_id INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
        question TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL DEFAULT '',
        option_d TEXT NOT NULL DEFAULT '',
        correct_option VARCHAR(1) NOT NULL,
        explanation TEXT NOT NULL DEFAULT '',
        order_index INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS user_progress (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        progress_percent INTEGER NOT NULL DEFAULT 0,
        completed_lessons INTEGER NOT NULL DEFAULT 0,
        last_accessed TIMESTAMP NOT NULL DEFAULT NOW(),
        completed_at TIMESTAMP,
        UNIQUE(user_id, course_id)
    )""",
    """CREATE TABLE IF NOT EXISTS user_lesson_progress (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
        completed_at TIMESTAMP NOT NULL DEFAULT NOW(),
        time_spent_seconds INTEGER NOT NULL DEFAULT 0,
        UNIQUE(user_id, lesson_id)
    )""",
    """CREATE TABLE IF NOT EXISTS certificates (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        certificate_number VARCHAR(100) UNIQUE NOT NULL,
        issued_at TIMESTAMP NOT NULL DEFAULT NOW(),
        pdf_url VARCHAR(500) NOT NULL DEFAULT '',
        UNIQUE(user_id, course_id)
    )""",
    """CREATE TABLE IF NOT EXISTS quiz_attempts (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        quiz_id INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
        score FLOAT NOT NULL DEFAULT 0,
        passed BOOLEAN NOT NULL DEFAULT FALSE,
        answers TEXT NOT NULL DEFAULT '{}',
        attempted_at TIMESTAMP NOT NULL DEFAULT NOW()
    )""",
]

_LEARNING_TABLE_SQLS = [
    """CREATE TABLE IF NOT EXISTS learning_levels (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        order_index INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS learning_modules (
        id SERIAL PRIMARY KEY,
        level_id INTEGER NOT NULL REFERENCES learning_levels(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        order_index INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS learning_lessons (
        id SERIAL PRIMARY KEY,
        module_id INTEGER NOT NULL REFERENCES learning_modules(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        content TEXT NOT NULL DEFAULT '',
        order_index INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS lesson_quizzes (
        id SERIAL PRIMARY KEY,
        lesson_id INTEGER NOT NULL REFERENCES learning_lessons(id) ON DELETE CASCADE,
        question TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL DEFAULT '',
        option_d TEXT NOT NULL DEFAULT '',
        correct_answer VARCHAR(1) NOT NULL,
        explanation TEXT NOT NULL DEFAULT '',
        topic_slug VARCHAR(100) NOT NULL DEFAULT ''
    )""",
    """CREATE TABLE IF NOT EXISTS user_learning_progress (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        level_id INTEGER NOT NULL DEFAULT 0,
        module_id INTEGER NOT NULL DEFAULT 0,
        lesson_id INTEGER NOT NULL REFERENCES learning_lessons(id) ON DELETE CASCADE,
        completed BOOLEAN NOT NULL DEFAULT FALSE,
        quiz_score FLOAT,
        completed_at TIMESTAMP,
        UNIQUE(user_id, lesson_id)
    )""",
    """CREATE TABLE IF NOT EXISTS user_quiz_results (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        lesson_id INTEGER NOT NULL DEFAULT 0,
        question_id INTEGER NOT NULL DEFAULT 0,
        selected_answer VARCHAR(1) NOT NULL,
        is_correct BOOLEAN NOT NULL DEFAULT FALSE,
        answered_at TIMESTAMP NOT NULL DEFAULT NOW()
    )""",
    # PATCH: Added first_academy_visit column
    """CREATE TABLE IF NOT EXISTS user_learning_profile (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
        weak_topics TEXT NOT NULL DEFAULT '[]',
        strong_topics TEXT NOT NULL DEFAULT '[]',
        first_academy_visit BOOLEAN NOT NULL DEFAULT TRUE,
        last_updated TIMESTAMP NOT NULL DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS user_badges (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        badge_type VARCHAR(50) NOT NULL,
        earned_at TIMESTAMP NOT NULL DEFAULT NOW(),
        UNIQUE(user_id, badge_type)
    )""",
]

_LEVELS = [
    (1, "Beginner", "Master the basics of Forex trading from scratch.", 1),
    (2, "Intermediate", "Build strategies using technical analysis tools.", 2),
    (3, "Advanced", "Trade like an institution — market structure and liquidity.", 3),
]

_MODULES = [
    # Beginner (Level 1)
    (1, "Introduction to Forex Trading", "What Forex is and who trades it.", 1),
    (1, "Currency Pairs and Price Quotes", "Majors, minors, exotics, pips, and spreads.", 2),
    (1, "Trading Sessions and Market Timing", "When the markets are most active.", 3),
    (1, "Pips, Lots, and Leverage", "Position sizing and leverage explained.", 4),
    (1, "Basic Risk Management", "Stop loss, take profit, and the 1-2% rule.", 5),
    (1, "Introduction to Trading Charts", "Candlestick charts and support/resistance basics.", 6),
    # Intermediate (Level 2)
    (2, "Technical Analysis Fundamentals", "Trend identification and chart reading.", 1),
    (2, "Support and Resistance", "Drawing levels that professionals actually use.", 2),
    (2, "Chart Patterns", "Reversals and continuations — flags, H&S, triangles.", 3),
    (2, "Candlestick Patterns", "Pin bars, engulfing candles, doji patterns.", 4),
    (2, "Trading Indicators", "MACD, RSI, and Moving Averages used properly.", 5),
    (2, "Trading Strategies", "Building a complete, rule-based trading strategy.", 6),
    # Advanced (Level 3)
    (3, "Market Structure", "BOS, CHoCH, order blocks, and fair value gaps.", 1),
    (3, "Liquidity and Institutional Trading", "Stop hunts, liquidity pools, and smart money.", 2),
    (3, "Advanced Risk Management", "Portfolio risk, correlated pairs, drawdown management.", 3),
    (3, "Trading Psychology", "Emotional control, discipline, and process thinking.", 4),
    (3, "Strategy Development", "Backtesting, forward testing, and edge calculation.", 5),
    (3, "Building a Complete Trading System", "Combining all elements into a professional plan.", 6),
]

_LESSONS = [
    # Beginner: Module 1 (Introduction to Forex)
    (1, 1, "What is Forex?", "Forex (Foreign Exchange) is the global marketplace where currencies are bought and sold — over $7.5 trillion traded every day.\n\n## Why Trade Forex?\n- 24/5 market access\n- High liquidity\n- Low barriers to entry\n- Profit from rising AND falling markets\n\n## How it Works\nCurrencies trade in pairs. EUR/USD = 1.0850 means 1 Euro buys 1.0850 US Dollars. You profit when you correctly predict which direction the rate moves.\n\n**Trade Example**\nPair: EUR/USD | Direction: Buy | Entry: 1.0850 | Stop: 1.0800 | Target: 1.0950\nRisk: 50 pips | Reward: 100 pips | R:R = 1:2\n\n[CHART:EURUSD]"),
    (1, 2, "Who Trades Forex?", "## Market Participants\n\n**Central Banks** — set interest rates, most powerful players.\n**Commercial Banks** — JP Morgan, Goldman Sachs execute trillions daily.\n**Corporations** — convert foreign earnings (Apple, Nike, etc.).\n**Retail Traders** — you. Less than 5% of total volume.\n\n## Key Insight\nTrade WITH institutional flow, not against it. Price moves when large participants need to buy or sell.\n\n[VISUAL:MARKET_PARTICIPANTS]"),
    # Module 2 (Currency Pairs)
    (2, 1, "Major, Minor and Exotic Pairs", "## Major Pairs (Always include USD)\n- EUR/USD — most traded\n- GBP/USD — 'Cable'\n- USD/JPY — dollar vs yen\n- USD/CHF — safe haven\n\n## Minors (No USD)\nEUR/GBP, GBP/JPY, AUD/JPY\n\n## Exotics\nUSD/ZAR, EUR/TRY — wide spreads, not for beginners.\n\n**Rule:** Start with EUR/USD. Tight spreads, abundant analysis."),
    (2, 2, "Reading Pips and Spreads", "## What is a Pip?\nA pip = 0.0001 move on most pairs. EUR/USD from 1.0850 to 1.0860 = 10 pips.\n\n## Pip Value\n- Standard lot (100k units): ~$10/pip\n- Mini lot (10k): ~$1/pip\n- Micro lot (1k): ~$0.10/pip\n\n## Spread\nBid vs Ask difference. Your cost to trade. EUR/USD: 0.1–0.5 pip.\n\n[VISUAL:PIP_SPREAD]"),
    # Module 3 (Trading Sessions)
    (3, 1, "Trading Sessions Explained", "## Asian Session (Tokyo)\n20:00–05:00 UTC. Slower moves, JPY pairs most active.\n\n## London Session\n08:00–17:00 UTC. Highest liquidity. EUR, GBP, CHF active.\n\n## New York Session\n13:00–22:00 UTC. USD pairs volatile. Overlap with London (13:00–17:00) = best trading hours.\n\n[VISUAL:SESSIONS_CLOCK]"),
    # Module 4 (Pips Lots Leverage)
    (4, 1, "Understanding Leverage", "## What is Leverage?\nControl large positions with small capital. 1:100 leverage = $1,000 controls $100,000.\n\n## Caution\nLeverage amplifies gains AND losses. Never use maximum available leverage.\n\n**Safe Rule:** Use 1:10 to 1:30 for beginners. Never risk more than 2% per trade regardless of leverage.\n\n[VISUAL:LEVERAGE_EXAMPLE]"),
    # Module 5 (Risk Management)
    (5, 1, "The 1-2% Rule", "**Never risk more than 1–2% of your account on a single trade.**\n\n## Example\n$10,000 account × 2% = $200 max risk.\nStop = 50 pips → lot size = 200 ÷ 50 ÷ 10 = 0.4 lots.\n\n## Why This Works\nWith 2% risk you need 50 consecutive losses to blow the account. With 10% risk, only 10 losses wipe you out.\n\n[VISUAL:RISK_2PERCENT]"),
    (5, 2, "Stop Loss and Take Profit", "Every trade must have BOTH before you click.\n\n## Stop Loss Placement\n- Buys: below support\n- Sells: above resistance\n\n## Take Profit\nMinimum 1:2 R:R — risk $100 to make $200.\n\n**Trade Example**\nEUR/USD Buy at 1.0850 | Stop: 1.0800 | Target: 1.0950\nRisk: 50 pips | Reward: 100 pips ✓"),
    # Module 6 (Charts)
    (6, 1, "Candlestick Charts Explained", "## Candle Anatomy\n- **Open** — start of period\n- **Close** — end of period\n- **High / Low** — extremes\n- Green = bullish (close > open)\n- Red = bearish (close < open)\n\n## Key Patterns\n- **Doji** — indecision\n- **Pin Bar** — rejection of a level\n- **Engulfing** — potential reversal\n\n[VISUAL:CANDLESTICK_ANATOMY]\n\n[CHART:EURUSD]"),
    (6, 2, "Support and Resistance Basics", "## Support\nA price floor where buyers historically step in. Price falls → hits support → bounces.\n\n## Resistance\nA price ceiling where sellers historically appear. Price rises → hits resistance → falls.\n\n## Role Reversal\nBroken resistance becomes new support. This is one of the most reliable patterns in trading.\n\n**Drawing Rule:** Need 2+ touches to call a level significant.\n\n[VISUAL:SUPPORT_RESISTANCE]\n\n[CHART:EURUSD]"),
    
    # Intermediate: Module 7 (Technical Analysis)
    (7, 1, "Identifying Trends", "## Uptrend\nHigher Highs (HH) + Higher Lows (HL).\n\n## Downtrend\nLower Highs (LH) + Lower Lows (LL).\n\n## Trend Confirmation\n- Price above 200 EMA = bullish bias\n- Price below 200 EMA = bearish bias\n- Trade WITH the higher timeframe trend.\n\n**Rule:** Always check the daily chart trend before entering on H1.\n\n[VISUAL:TREND_STRUCTURE]\n\n[CHART:GBPUSD]"),
    (7, 2, "Multi-Timeframe Analysis", "## The Concept\nUse higher timeframes for direction, lower timeframes for entry.\n\n**Process:**\n1. Daily chart: identify trend\n2. H4 chart: find key level (support/resistance)\n3. H1 chart: wait for entry signal\n\nThis is how professional traders time entries with minimal risk.\n\n[CHART:EURUSD]"),
    # Module 8 (Support/Resistance Advanced)
    (8, 1, "Drawing Professional Levels", "## Clean Levels Only\n- Remove lines with only 1 touch\n- Focus on zones (areas), not exact prices\n- Weekly/monthly levels strongest\n\n## Confluence\nWhen support/resistance aligns with:\n- Fibonacci retracement\n- Round numbers (1.1000)\n- Moving averages\n= Higher probability trades\n\n[CHART:USDJPY]"),
    (8, 2, "Dynamic Support with Moving Averages", "## Live Levels\nUnlike horizontal lines, moving averages act as dynamic support/resistance that updates every candle.\n\n## EMA Strategy\n- Price pulls back to 20 EMA in uptrend = buy\n- Price rejects 20 EMA in downtrend = sell\n\nCombine with horizontal levels for double confirmation.\n\n[CHART:EURUSD]"),
    # Module 9 (Chart Patterns)
    (9, 1, "Reversal Patterns", "## Head and Shoulders\nThree peaks, middle highest. Break of neckline = trend reversal.\n\n## Double Top/Bottom\nTwo equal highs/lows. Second rejection confirms reversal.\n\n## Triangles\n- Ascending: bullish breakout\n- Descending: bearish breakout\n- Symmetrical: breakout direction follows prior trend\n\n[VISUAL:CHART_PATTERNS]\n\n[CHART:EURUSD]"),
    # Module 10 (Candlesticks)
    (10, 1, "Advanced Candlestick Signals", "## Pin Bar\nLong wick, small body. Rejection of price level. Best at support/resistance.\n\n## Engulfing Pattern\nCurrent candle completely covers previous. Bullish engulfing at support = strong buy.\n\n## Morning/Evening Star\n3-candle reversal pattern. High reliability at key levels.\n\n[VISUAL:CANDLESTICK_PATTERNS]"),
    # Module 11 (Indicators)
    (11, 1, "MACD and RSI", "## RSI\nMeasures momentum 0–100.\n- Above 70: overbought\n- Below 30: oversold\n- **Divergence**: price new high but RSI lower high = reversal warning\n\n## MACD\n- MACD line crosses above signal = bullish momentum\n- MACD line crosses below signal = bearish momentum\n- Histogram shows momentum strength\n\n**Rule:** Use divergence signals, not overbought/oversold levels alone.\n\n[CHART:EURUSD_INDICATORS]"),
    (11, 2, "Moving Averages", "## Types\n- **SMA** — equal weight all periods\n- **EMA** — more weight to recent (faster)\n\n## Key Levels\n20 EMA (short-term) | 50 EMA (medium) | 200 EMA (long-term trend)\n\n## Golden/Death Cross\n50 EMA crosses 200 EMA up = Golden Cross (bullish)\n50 EMA crosses 200 EMA down = Death Cross (bearish)\n\n[CHART:EURUSD_MA]"),
    # Module 12 (Strategies)
    (12, 1, "Building Your First Strategy", "## Strategy Template\n1. **Market**: Which pairs? (EUR/USD recommended)\n2. **Timeframe**: H1 for analysis, M15 for entry\n3. **Setup**: What conditions must align?\n4. **Entry**: Exact trigger (e.g., pin bar at support)\n5. **Exit**: Stop loss and take profit rules\n6. **Risk**: 1% per trade, max 3 trades/day\n\n## Backtest First\nTest 50 trades on historical data before risking real money.\n\n[CHART:EURUSD]"),
    
    # Advanced: Module 13 (Market Structure)
    (13, 1, "Market Structure: BOS and CHoCH", "## Break of Structure (BOS)\nPrice breaks a previous swing high (uptrend) or low (downtrend).\nBOS = trend continuation confirmed.\n\n## Change of Character (CHoCH)\nIn an uptrend: price breaks BELOW the last swing low.\nFirst warning of potential reversal.\n\n## Order Blocks\nLast bearish candle before a bullish impulse = institutional order block.\nPrice returns to this zone = high-probability entry.\n\n[VISUAL:MARKET_STRUCTURE]\n\n[CHART:EURUSD_SMC]"),
    (13, 2, "Fair Value Gaps", "A Fair Value Gap (FVG) is a 3-candle pattern where price moves so fast it leaves a gap between candle 1's high and candle 3's low.\n\nThese gaps are market inefficiencies that price tends to revisit before continuing.\n\n**Setup:** Order Block + FVG fill + BOS confirmation = highest probability entries in institutional trading.\n\n[VISUAL:FVG_DIAGRAM]\n\n[CHART:EURUSD]"),
    # Module 14 (Liquidity)
    (14, 1, "Liquidity Pools and Stop Hunts", "## What is Liquidity?\nInstitutions need liquidity to fill large orders. Stop losses cluster above swing highs and below swing lows.\n\n## The Stop Hunt\nPrice sweeps above equal highs → triggers buy stops → institutions SELL into liquidity.\nPrice sweeps below equal lows → triggers sell stops → institutions BUY.\n\n## How to Use It\nWait for the sweep candle. Enter AFTER the sweep reverses. This is the cleaner entry.\n\n[VISUAL:LIQUIDITY_SWEEP]\n\n[CHART:EURUSD]"),
    (14, 2, "Smart Money Concepts", "## Institutional Order Flow\n- Accumulation: Smart money building positions\n- Manipulation: Stop hunts to generate liquidity\n- Distribution: Profit taking at retail entries\n\n## Your Edge\nRetail traders try to predict. Smart money traders react to institutional footprints (order blocks, FVGs, liquidity sweeps).\n\n[CHART:EURUSD]"),
    # Module 15 (Advanced Risk)
    (15, 1, "Portfolio Risk Management", "## Correlation Risk\nDon't trade EUR/USD and GBP/USD simultaneously — they're 90% correlated. One loss = two losses.\n\n## Drawdown Rules\n- Daily loss limit: 3% of account\n- Weekly loss limit: 6% of account\n- Hit limit = stop trading for the period\n\n## Asymmetric Risk\nRisk 1% to make 3%. Win rate can be 40% and you'll still profit."),
    # Module 16 (Psychology)
    (16, 1, "The Psychology of Trading", "## The Four Deadly Emotions\n1. **Fear** — cutting winners, missing valid setups\n2. **Greed** — holding past targets, overtrading\n3. **Hope** — not taking stop losses\n4. **Revenge** — trading immediately after a loss\n\n## Solution\n- Max 2 losses per session, then STOP\n- Pre-trade checklist (written)\n- Judge trades by process, not outcome\n- Keep a detailed journal"),
    (16, 2, "Developing Trader Discipline", "## Process Over Outcome\nA good trade follows your rules regardless of result. A bad trade breaks rules even if profitable.\n\n## The 3 R's\n- **Rules**: Written, specific, unambiguous\n- **Records**: Journal every trade with screenshot\n- **Review**: Weekly analysis of performance\n\n[VISUAL:DISCIPLINE_CYCLE]"),
    # Module 17 (Strategy Development)
    (17, 1, "Backtesting Your Strategy", "## Manual Backtesting\n1. Open chart to past date\n2. Move forward candle by candle\n3. Record every valid setup\n4. Calculate win rate and R:R\n\n## Minimum Viable Sample\nNeed 100+ trades before trusting statistics. 50 wins/50 losses tells you nothing. 60/40 with 1:2 R:R = profitable edge."),
    # Module 18 (Complete System)
    (18, 1, "Building Your Trading Plan", "## Complete Trading System Checklist\n- [ ] Clear entry rules (5 bullet points max)\n- [ ] Clear exit rules (stop and target)\n- [ ] Risk per trade defined (1%)\n- [ ] Maximum daily trades (3)\n- [ ] Trading schedule (London session only?)\n- [ ] Pre-trade checklist (mental/technical)\n- [ ] Post-trade review process\n\n**Print this and tape it to your monitor.**"),
]

_QUIZ_DATA = [
    # Beginner Quizzes
    ("What is Forex?", "What does EUR/USD = 1.0850 mean?", "1 USD buys 1.0850 Euros", "1 EUR buys 1.0850 USD", "Both currencies cost 1.0850", "EUR is stronger by 8.5%", "B", "In Forex quotes the base currency (EUR) is always 1 unit. EUR/USD = 1.0850 means 1 Euro buys 1.0850 US Dollars.", "forex_basics"),
    ("Who Trades Forex?", "Which participant moves the market most?", "Retail traders", "Central Banks", "Your broker", "Social media influencers", "B", "Central banks control interest rates and currency supply. Their decisions create the largest price movements.", "market_participants"),
    ("Major, Minor and Exotic Pairs", "Which is a minor pair?", "EUR/USD", "GBP/JPY", "USD/CHF", "USD/ZAR", "B", "Minors (crosses) don't include USD. GBP/JPY is a minor/cross pair.", "currency_pairs"),
    ("Reading Pips and Spreads", "How much is 1 pip on EUR/USD for 1 standard lot?", "$0.10", "$1", "$10", "$100", "C", "1 standard lot = 100,000 units. 1 pip (0.0001) × 100,000 = $10.", "pips_lots"),
    ("The 1-2% Rule", "With $5,000 account and 2% risk, what's max $ loss per trade?", "$10", "$50", "$100", "$1,000", "C", "$5,000 × 2% = $100 maximum risk per trade.", "risk_management"),
    ("Stop Loss and Take Profit", "What is minimum recommended Risk:Reward ratio?", "1:1", "1:2", "1:0.5", "2:1", "B", "Minimum 1:2 R:R recommended. Risk $1 to make $2. Allows 40% win rate to be profitable.", "risk_reward"),
    ("Candlestick Charts Explained", "What does a bearish engulfing candle signal?", "The trend is continuing upward", "Strong buying pressure has entered", "Sellers have overwhelmed buyers — potential reversal", "Price is consolidating", "C", "A bearish engulfing candle has a red body that completely covers the previous green candle. It signals sellers have overwhelmed buyers and a downward reversal may follow.", "candlestick_patterns"),
    ("Support and Resistance Basics", "What is 'role reversal'?", "When two traders swap positions", "When broken resistance becomes new support", "When the trend reverses completely", "When price gaps through a level", "B", "Role reversal is when a previously broken resistance level now acts as support (or vice versa). It's one of the most reliable patterns in all of technical analysis.", "support_resistance"),
    
    # Intermediate Quizzes
    ("Identifying Trends", "In a confirmed uptrend using price action, what pattern must you see?", "Lower highs and lower lows", "Higher highs and higher lows", "Equal highs and random lows", "Price above the 200 EMA only", "B", "An uptrend is technically defined as a series of Higher Highs (HH) AND Higher Lows (HL). Both conditions must be present for a confirmed uptrend.", "trend_analysis"),
    ("Multi-Timeframe Analysis", "Best timeframe for entry timing?", "Monthly", "Weekly", "Daily", "H1 or lower", "D", "Higher timeframes (Daily) for direction, lower timeframes (H1, M15) for precise entry timing and tight stops.", "timeframe_analysis"),
    ("Support and Resistance Advanced", "What creates the strongest support/resistance level?", "Single touch", "Two touches", "Three or more touches + confluence", "Random line on chart", "C", "The more touches a level has, and the more confluence (Fibonacci, round numbers, moving averages), the stronger the level becomes.", "advanced_snr"),
    ("Chart Patterns", "What does Head and Shoulders pattern indicate?", "Trend continuation", "Trend reversal", "Consolidation", "Breakout imminent", "B", "Head and Shoulders is a reversal pattern. The break of the neckline confirms the previous trend is reversing.", "chart_patterns"),
    ("MACD and RSI", "RSI divergence occurs when:", "Price and RSI both make new highs", "Price makes a new high but RSI makes a lower high", "RSI goes above 70", "Price and RSI both go below 30", "B", "Bearish divergence: price new high, RSI lower high. Bullish divergence: price new low, RSI higher low. Divergence signals momentum is weakening before price confirms the reversal.", "indicators"),
    ("Moving Averages", "Golden Cross occurs when:", "50 EMA crosses above 200 EMA", "200 EMA crosses above 50 EMA", "Price crosses above 20 EMA", "Two moving averages touch", "A", "50 EMA crossing above 200 EMA is called a Golden Cross and is a long-term bullish signal.", "moving_averages"),
    
    # Advanced Quizzes
    ("Market Structure: BOS and CHoCH", "What is a Change of Character (CHoCH) in an uptrend?", "A new higher high is formed", "Price breaks BELOW the most recent swing low", "The 50 EMA crosses the 200 EMA", "Price reaches a round number", "B", "CHoCH in an uptrend = price breaks below the last swing low, breaking the HH/HL structure. It's the first warning that the uptrend may be ending. Not a confirmed reversal until structure flips.", "market_structure"),
    ("Fair Value Gaps", "What defines a Fair Value Gap (FVG)?", "Price gap between Friday close and Sunday open", "3-candle pattern with gap between candle 1 and candle 3", "Missing data on chart", "News event gap", "B", "FVG is a 3-candle pattern where candle 3's low is above candle 1's high (bullish FVG) or candle 3's high is below candle 1's low (bearish FVG). Price often returns to fill this inefficiency.", "fair_value_gaps"),
    ("Liquidity and Stop Hunts", "Why do institutions 'stop hunt' above obvious resistance?", "To drive price higher for retail traders", "To trigger buy stops and sell into the liquidity created", "To test the strength of resistance", "To confuse technical analysts", "B", "Institutions need large order flow to fill their positions. Sweeping above resistance triggers retail buy stops, creating the liquidity institutions need to sell. The apparent 'breakout' is engineered to fill institutional orders.", "liquidity"),
    ("Trading Psychology", "What is 'revenge trading'?", "Trading a currency pair you previously lost on", "Entering a trade immediately after a loss to recover it", "Trading against the trend out of frustration", "Doubling position size after a win", "B", "Revenge trading is entering a new trade immediately after a loss driven by the desire to 'make it back.' It is emotional, unplanned, and almost always results in a second larger loss.", "psychology"),
    ("Portfolio Risk", "Max recommended correlation between two open trades?", "0% (uncorrelated)", "50%", "90%", "100%", "A", "Avoid correlated pairs (EUR/USD and GBP/USD move together ~90%). A loss on one likely means loss on both. Choose uncorrelated opportunities or reduce size.", "correlation"),
    ("Strategy Development", "Minimum backtest sample size before trusting statistics?", "10 trades", "25 trades", "50 trades", "100+ trades", "D", "Need 100+ trades for statistical significance. Win rates vary wildly in small samples. 100 trades with 60% win rate and 1:2 R:R indicates a probable edge.", "backtesting"),
]

# Badge definitions
BADGE_DEFINITIONS = {
    "beginner_trader": {"name": "Beginner Trader", "icon": "fa-seedling", "color": "#34d399", "desc": "Completed Beginner level"},
    "technical_analyst": {"name": "Technical Analyst", "icon": "fa-chart-line", "color": "#60a5fa", "desc": "Completed Intermediate level"},
    "strategy_builder": {"name": "Strategy Builder", "icon": "fa-chess-knight", "color": "#a78bfa", "desc": "Completed Advanced level"},
    "pipways_certified": {"name": "Pipways Certified", "icon": "fa-certificate", "color": "#f59e0b", "desc": "Completed entire Academy curriculum"},
    "quiz_master": {"name": "Quiz Master", "icon": "fa-brain", "color": "#f472b6", "desc": "Passed 10 quizzes with 80%+"},
    "perfect_score": {"name": "Perfect Score", "icon": "fa-star", "color": "#fbbf24", "desc": "Scored 100% on any quiz"},
    "risk_manager": {"name": "Risk Manager", "icon": "fa-shield-alt", "color": "#22d3ee", "desc": "Mastered Risk Management modules"},
    "psychology_pro": {"name": "Psychology Pro", "icon": "fa-brain", "color": "#e879f9", "desc": "Completed Trading Psychology module"},
}


async def init_lms_tables():
    """Create all tables if they don't exist. Fully idempotent. Auto-seeds if empty."""
    ok = warn = 0

    for col, definition in _COURSE_COLUMNS:
        sql = f"ALTER TABLE courses ADD COLUMN IF NOT EXISTS {col} {definition}"
        try:
            await database.execute(sql)
            ok += 1
        except Exception as e:
            warn += 1
            print(f"[LMS INIT] courses.{col}: {e}", flush=True)

    for sql in _TABLE_SQLS:
        try:
            await database.execute(sql.strip())
            ok += 1
        except Exception as e:
            warn += 1
            print(f"[LMS INIT] table warn: {e}", flush=True)

    for sql in _LEARNING_TABLE_SQLS:
        try:
            await database.execute(sql.strip())
            ok += 1
        except Exception as e:
            warn += 1
            print(f"[LMS INIT] learning table warn: {e}", flush=True)

    print(f"[LMS INIT] Tables done — {ok} ok, {warn} warnings", flush=True)

    # CRITICAL FIX: Auto-seed curriculum if empty (idempotent check)
    try:
        count = await database.fetch_val("SELECT COUNT(*) FROM learning_levels")
        if not count or int(count) == 0:
            print("[LMS INIT] Curriculum empty — seeding default content...", flush=True)
            await _seed_curriculum()
        else:
            print(f"[LMS INIT] Curriculum exists ({count} levels) — skipping seed", flush=True)
    except Exception as e:
        print(f"[LMS INIT] Seed check error: {e}", flush=True)


async def _seed_curriculum():
    """Insert the default curriculum if tables are empty."""
    existing = await database.fetch_val("SELECT COUNT(*) FROM learning_levels")
    if existing and int(existing) > 0:
        print("[LMS INIT] Curriculum already seeded — skipping", flush=True)
        return

    level_ids = {}
    for order_id, name, desc, order in _LEVELS:
        lid = await database.execute(
            "INSERT INTO learning_levels (name, description, order_index) VALUES (:n,:d,:o) RETURNING id",
            {"n": name, "d": desc, "o": order}
        )
        level_ids[order_id] = lid
        print(f"[LMS INIT] Level created: {name} (id={lid})", flush=True)

    module_ids = {}
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

    # Map global module index to actual ID
    global_module_list = []
    for level_order in [1, 2, 3]:
        for mod_order in range(1, level_module_counters.get(level_order, 0) + 1):
            global_module_list.append(module_ids[(level_order, mod_order)])

    lesson_ids = {}
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

    print("[LMS INIT] Academy curriculum seeded successfully", flush=True)
