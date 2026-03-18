"""
LMS Auto-Initialisation — Bulletproof Edition (v3.0 UPSERT)
Changes:
- Uses upsert logic: adds missing curriculum without duplicates
- Safe for production: preserves all user progress
- Fixes missing modules (now 6 per level as per requirements)
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
    """CREATE TABLE IF NOT EXISTS course_modules (...)""",  # Keep existing
    # ... (keep all your existing _TABLE_SQLS here) ...
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
    (3, 2, "Best Times to Trade", "## The Golden Window\n13:00–17:00 UTC (London-NY Overlap):\n- Highest liquidity\n- Tightest spreads\n- Most directional moves\n\n## Worst Times\nFriday evenings (low liquidity), Sunday opens (gaps), major news releases (spikes)."),
    # Module 4 (Pips Lots Leverage)
    (4, 1, "Understanding Leverage", "## What is Leverage?\nControl large positions with small capital. 1:100 leverage = $1,000 controls $100,000.\n\n## Caution\nLeverage amplifies gains AND losses. Never use maximum available leverage.\n\n**Safe Rule:** Use 1:10 to 1:30 for beginners. Never risk more than 2% per trade regardless of leverage.\n\n[VISUAL:LEVERAGE_EXAMPLE]"),
    (4, 2, "Position Sizing Calculation", "## The Formula\nPosition Size = Account Risk ($) ÷ (Stop Loss (pips) × Pip Value ($))\n\n## Example\n$10,000 account, 2% risk ($200), 50 pip stop, $10/pip value:\n200 ÷ (50 × 10) = 0.4 standard lots (or 4 mini lots)"),
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
    (9, 2, "Continuation Patterns", "## Flags and Pennants\nBrief consolidation in strong trend. Trade breakout in trend direction.\n\n## Rectangles\nPrice oscillates between parallel support/resistance. Trade the range or breakout.\n\n## Measured Moves\nFlag pole height projected from breakout point = target.\n\n[CHART:EURUSD]"),
    # Module 10 (Candlesticks)
    (10, 1, "Advanced Candlestick Signals", "## Pin Bar\nLong wick, small body. Rejection of price level. Best at support/resistance.\n\n## Engulfing Pattern\nCurrent candle completely covers previous. Bullish engulfing at support = strong buy.\n\n## Morning/Evening Star\n3-candle reversal pattern. High reliability at key levels.\n\n[VISUAL:CANDLESTICK_PATTERNS]"),
    (10, 2, "Doji and Indecision", "## Doji Types\n- Standard: open ≈ close, indecision\n- Dragonfly: strong rejection of lows (bullish)\n- Gravestone: strong rejection of highs (bearish)\n\n## Context Matters\nDoji at support = potential bounce. Doji in middle of range = ignore."),
    # Module 11 (Indicators)
    (11, 1, "MACD and RSI", "## RSI\nMeasures momentum 0–100.\n- Above 70: overbought\n- Below 30: oversold\n- **Divergence**: price new high but RSI lower high = reversal warning\n\n## MACD\n- MACD line crosses above signal = bullish momentum\n- MACD line crosses below signal = bearish momentum\n- Histogram shows momentum strength\n\n**Rule:** Use divergence signals, not overbought/oversold levels alone.\n\n[CHART:EURUSD_INDICATORS]"),
    (11, 2, "Moving Averages", "## Types\n- **SMA** — equal weight all periods\n- **EMA** — more weight to recent (faster)\n\n## Key Levels\n20 EMA (short-term) | 50 EMA (medium) | 200 EMA (long-term trend)\n\n## Golden/Death Cross\n50 EMA crosses 200 EMA up = Golden Cross (bullish)\n50 EMA crosses 200 EMA down = Death Cross (bearish)\n\n[CHART:EURUSD_MA]"),
    # Module 12 (Strategies)
    (12, 1, "Building Your First Strategy", "## Strategy Template\n1. **Market**: Which pairs? (EUR/USD recommended)\n2. **Timeframe**: H1 for analysis, M15 for entry\n3. **Setup**: What conditions must align?\n4. **Entry**: Exact trigger (e.g., pin bar at support)\n5. **Exit**: Stop loss and take profit rules\n6. **Risk**: 1% per trade, max 3 trades/day\n\n## Backtest First\nTest 50 trades on historical data before risking real money.\n\n[CHART:EURUSD]"),
    (12, 2, "Strategy Examples", "## Trend Following\n- Daily trend: up\n- H4 pullback to 50 EMA\n- H1 bullish engulfing at EMA = entry\n\n## Range Trading\n- Identify support/resistance zone\n- Buy support, sell resistance\n- Tight stops just beyond boundaries\n\n## Breakout Trading\n- Wait for price to close beyond level\n- Enter on retest of broken level (role reversal)\n- Volume confirmation ideal"),
    
    # Advanced: Module 13 (Market Structure)
    (13, 1, "Market Structure: BOS and CHoCH", "## Break of Structure (BOS)\nPrice breaks a previous swing high (uptrend) or low (downtrend).\nBOS = trend continuation confirmed.\n\n## Change of Character (CHoCH)\nIn an uptrend: price breaks BELOW the last swing low.\nFirst warning of potential reversal.\n\n## Order Blocks\nLast bearish candle before a bullish impulse = institutional order block.\nPrice returns to this zone = high-probability entry.\n\n[VISUAL:MARKET_STRUCTURE]\n\n[CHART:EURUSD_SMC]"),
    (13, 2, "Fair Value Gaps", "A Fair Value Gap (FVG) is a 3-candle pattern where price moves so fast it leaves a gap between candle 1's high and candle 3's low.\n\nThese gaps are market inefficiencies that price tends to revisit before continuing.\n\n**Setup:** Order Block + FVG fill + BOS confirmation = highest probability entries in institutional trading.\n\n[VISUAL:FVG_DIAGRAM]\n\n[CHART:EURUSD]"),
    # Module 14 (Liquidity)
    (14, 1, "Liquidity Pools and Stop Hunts", "## What is Liquidity?\nInstitutions need liquidity to fill large orders. Stop losses cluster above swing highs and below swing lows.\n\n## The Stop Hunt\nPrice sweeps above equal highs → triggers buy stops → institutions SELL into liquidity.\nPrice sweeps below equal lows → triggers sell stops → institutions BUY.\n\n## How to Use It\nWait for the sweep candle. Enter AFTER the sweep reverses. This is the cleaner entry.\n\n[VISUAL:LIQUIDITY_SWEEP]\n\n[CHART:EURUSD]"),
    (14, 2, "Smart Money Concepts", "## Institutional Order Flow\n- Accumulation: Smart money building positions\n- Manipulation: Stop hunts to generate liquidity\n- Distribution: Profit taking at retail entries\n\n## Your Edge\nRetail traders try to predict. Smart money traders react to institutional footprints (order blocks, FVGs, liquidity sweeps).\n\n[CHART:EURUSD]"),
    # Module 15 (Advanced Risk)
    (15, 1, "Portfolio Risk Management", "## Correlation Risk\nDon't trade EUR/USD and GBP/USD simultaneously — they're 90% correlated. One loss = two losses.\n\n## Drawdown Rules\n- Daily loss limit: 3% of account\n- Weekly loss limit: 6% of account\n- Hit limit = stop trading for the period\n\n## Asymmetric Risk\nRisk 1% to make 3%. Win rate can be 40% and you'll still profit."),
    (15, 2, "Advanced Position Sizing", "## Kelly Criterion\nf* = (bp - q) / b\nWhere b = odds, p = win probability, q = loss probability\n\n## Practical Application\nWith 50% win rate and 2:1 R:R:\nf* = (2×0.5 - 0.5) / 2 = 0.25 (risk 25% per trade — too high!)\n\n**Use Half-Kelly:** 12.5% max (still aggressive). Most pros use 1-2% regardless."),
    # Module 16 (Psychology)
    (16, 1, "The Psychology of Trading", "## The Four Deadly Emotions\n1. **Fear** — cutting winners, missing valid setups\n2. **Greed** — holding past targets, overtrading\n3. **Hope** — not taking stop losses\n4. **Revenge** — trading immediately after a loss\n\n## Solution\n- Max 2 losses per session, then STOP\n- Pre-trade checklist (written)\n- Judge trades by process, not outcome\n- Keep a detailed journal"),
    (16, 2, "Developing Trader Discipline", "## Process Over Outcome\nA good trade follows your rules regardless of result. A bad trade breaks rules even if profitable.\n\n## The 3 R's\n- **Rules**: Written, specific, unambiguous\n- **Records**: Journal every trade with screenshot\n- **Review**: Weekly analysis of performance\n\n[VISUAL:DISCIPLINE_CYCLE]"),
    # Module 17 (Strategy Development)
    (17, 1, "Backtesting Your Strategy", "## Manual Backtesting\n1. Open chart to past date\n2. Move forward candle by candle\n3. Record every valid setup\n4. Calculate win rate and R:R\n\n## Minimum Viable Sample\nNeed 100+ trades before trusting statistics. 50 wins/50 losses tells you nothing. 60/40 with 1:2 R:R = profitable edge."),
    (17, 2, "Forward Testing", "## Paper Trading\nTrade live markets with demo account for 30 days minimum.\n\n## The Transition to Live\n- Start with micro lots (0.01)\n- Only scale up after 3 consecutive profitable weeks\n- If demo fails, fix strategy before risking capital"),
    # Module 18 (Complete System)
    (18, 1, "Building Your Trading Plan", "## Complete Trading System Checklist\n- [ ] Clear entry rules (5 bullet points max)\n- [ ] Clear exit rules (stop and target)\n- [ ] Risk per trade defined (1%)\n- [ ] Maximum daily trades (3)\n- [ ] Trading schedule (London session only?)\n- [ ] Pre-trade checklist (mental/technical)\n- [ ] Post-trade review process\n\n**Print this and tape it to your monitor.**"),
    (18, 2, "The Trader's Routine", "## Pre-Market (30 mins before)\n1. Check economic calendar\n2. Mark key levels on charts\n3. Set price alerts\n\n## During Session\n1. Wait for your setup (don't force trades)\n2. Execute checklist before entry\n3. Set stop loss immediately\n\n## Post-Session\n1. Review all trades taken\n2. Update journal\n3. Prepare for next day"),
]

_QUIZ_DATA = [
    # Beginner Quizzes (12)
    ("What is Forex?", "What does EUR/USD = 1.0850 mean?", "1 USD buys 1.0850 Euros", "1 EUR buys 1.0850 USD", "Both currencies cost 1.0850", "EUR is stronger by 8.5%", "B", "In Forex quotes the base currency (EUR) is always 1 unit. EUR/USD = 1.0850 means 1 Euro buys 1.0850 US Dollars.", "forex_basics"),
    ("Who Trades Forex?", "Which participant moves the market most?", "Retail traders", "Central Banks", "Your broker", "Social media influencers", "B", "Central banks control interest rates and currency supply. Their decisions create the largest price movements.", "market_participants"),
    ("Major, Minor and Exotic Pairs", "Which is a minor pair?", "EUR/USD", "GBP/JPY", "USD/CHF", "USD/ZAR", "B", "Minors (crosses) don't include USD. GBP/JPY is a minor/cross pair.", "currency_pairs"),
    ("Reading Pips and Spreads", "How much is 1 pip on EUR/USD for 1 standard lot?", "$0.10", "$1", "$10", "$100", "C", "1 standard lot = 100,000 units. 1 pip (0.0001) × 100,000 = $10.", "pips_lots"),
    ("Trading Sessions", "When is the best time to trade?", "Asian session only", "London-NY overlap (13:00-17:00 UTC)", "Weekends", "Holidays", "B", "The London-NY overlap has the highest liquidity and tightest spreads.", "sessions"),
    ("Leverage", "With 1:100 leverage, how much does $1,000 control?", "$1,000", "$10,000", "$100,000", "$1,000,000", "C", "1:100 leverage means $1,000 × 100 = $100,000 position size.", "leverage"),
    ("The 1-2% Rule", "With $5,000 account and 2% risk, what's max $ loss per trade?", "$10", "$50", "$100", "$1,000", "C", "$5,000 × 2% = $100 maximum risk per trade.", "risk_management"),
    ("Stop Loss", "Where should stop loss be placed for a BUY trade?", "Above resistance", "Below support", "At entry price", "Randomly", "B", "For buy trades, stops go below support to invalidate the trade idea if support breaks.", "risk_management"),
    ("Candlesticks", "What does a bearish engulfing candle signal?", "Trend continuation up", "Strong buying", "Sellers overwhelming buyers — potential reversal down", "Consolidation", "C", "Bearish engulfing means sellers took control from buyers. Strong reversal signal at resistance.", "candlestick_patterns"),
    ("Support/Resistance", "What is 'role reversal'?", "Traders swapping positions", "Broken resistance becomes new support", "Trend reversal", "Price gaps", "B", "Role reversal: once resistance is broken, it often becomes support on future pullbacks.", "support_resistance"),
    ("Pips", "EUR/USD moves from 1.0850 to 1.0865. How many pips?", "6.5", "15", "150", "1.5", "B", "1.0865 - 1.0850 = 0.0015 = 15 pips (0.0001 = 1 pip).", "pips_lots"),
    ("Risk Reward", "Minimum recommended Risk:Reward ratio?", "1:1", "1:2", "1:0.5", "2:1", "B", "Minimum 1:2 R:R. Risk $1 to make $2. Allows 40% win rate to be profitable.", "risk_reward"),
    
    # Intermediate Quizzes (12)
    ("Trends", "In a confirmed uptrend, you need:", "Lower highs, lower lows", "Higher highs, higher lows", "Equal highs", "Random price action", "B", "Uptrend = Higher Highs (HH) + Higher Lows (HL). Both conditions required.", "trend_analysis"),
    ("Multi-Timeframe", "Best timeframe for entry timing?", "Monthly", "Weekly", "Daily", "H1 or lower", "D", "Higher timeframes (Daily) for direction, lower timeframes (H1, M15) for precise entry timing.", "timeframe_analysis"),
    ("Support/Resistance", "What creates the strongest S/R level?", "Single touch", "Two touches", "3+ touches + confluence", "Random line", "C", "More touches + confluence (Fibonacci, round numbers) = stronger level.", "advanced_snr"),
    ("Chart Patterns", "Head and Shoulders indicates:", "Continuation", "Reversal", "Consolidation", "Breakout", "B", "Head and Shoulders is a reversal pattern. Neckline break confirms trend change.", "chart_patterns"),
    ("RSI Divergence", "Bearish divergence occurs when:", "Price and RSI both make new highs", "Price makes new high but RSI makes lower high", "RSI above 70", "Price below 30", "B", "Divergence = price and indicator disagree. Signals momentum weakening.", "indicators"),
    ("Moving Averages", "Golden Cross is:", "50 EMA crosses above 200 EMA", "200 EMA crosses above 50", "Price crosses 20 EMA", "Two MAs touch", "A", "50 EMA crossing above 200 EMA = Golden Cross (bullish signal).", "moving_averages"),
    ("Candlesticks", "Pin bar shows:", "Strong trend", "Indecision", "Rejection of a price level", "Consolidation", "C", "Pin bar = long wick, small body. Shows price was rejected from that level.", "candlestick_patterns"),
    ("Indicators", "MACD histogram shows:", "Price direction", "Volume", "Momentum strength", "Support levels", "C", "MACD histogram bars show momentum strength (expanding = strengthening).", "indicators"),
    ("Trend Trading", "In an uptrend, you should:", "Sell rallies", "Buy pullbacks", "Trade both directions", "Avoid trading", "B", "Trend trading rule: buy pullbacks to support in uptrends, sell rallies to resistance in downtrends.", "trend_analysis"),
    ("Range Trading", "In a range, buy at:", "Resistance", "Support", "The middle", "Anywhere", "B", "Range trading: buy support, sell resistance. Stop beyond boundaries.", "support_resistance"),
    ("Strategy", "Before trading live, you should:", "Start with max leverage", "Backtest 100+ trades minimum", "Copy other traders", "Trade news only", "B", "Backtesting validates edge. Need 100+ sample size for statistical significance.", "strategy"),
    ("Timeframes", "Daily chart shows:", "Exact entry points", "Overall trend direction", "Spread values", "News events", "B", "Daily/weekly charts show the 'big picture' trend. Lower timeframes fine-tune entries.", "timeframe_analysis"),
    
    # Advanced Quizzes (12)
    ("Market Structure", "CHoCH in an uptrend means:", "New higher high", "Price breaks below last swing low", "50 EMA crosses 200", "Round number hit", "B", "Change of Character = first sign of trend change (breaks HH/HL structure).", "market_structure"),
    ("Order Blocks", "Bullish order block is:", "Last green candle before move up", "Last red candle before move up", "Doji candle", "Any large candle", "B", "Bullish OB = last bearish (red) candle before strong bullish impulse. Smart money accumulation zone.", "market_structure"),
    ("FVG", "Fair Value Gap is:", "Weekend gap", "3-candle imbalance pattern", "Missing data", "News spike", "B", "FVG = 3-candle pattern with gap between candle 1 high and candle 3 low (or vice versa).", "fair_value_gaps"),
    ("Liquidity", "Stop hunts occur to:", "Help retail traders", "Generate liquidity for institutions", "Test breakout strength", "Signal reversal", "B", "Institutions sweep highs/lows to trigger retail stops, creating liquidity for their positions.", "liquidity"),
    ("Psychology", "Revenge trading is:", "Trading after wins", "Trading immediately after loss to recover", "Following plan", "Taking breaks", "B", "Revenge trading = emotional trading after loss. Leads to second, larger loss.", "psychology"),
    ("Risk", "Correlation between EUR/USD and GBP/USD is roughly:", "0% (none)", "30%", "90%", "Negative", "C", "EUR/USD and GBP/USD are ~90% correlated. Trading both = doubling risk.", "correlation"),
    ("Backtesting", "Minimum viable sample size:", "10 trades", "25 trades", "50 trades", "100+ trades", "D", "Need 100+ trades for statistical significance. Small samples produce random results.", "backtesting"),
    ("Drawdown", "Max recommended daily loss limit:", "10%", "6%", "3%", "No limit", "C", "Daily loss limit of 3% protects capital. Hit limit = stop trading for the day.", "risk_management"),
    ("SMC", "Accumulation phase is when:", "Retail traders are buying", "Institutions are building positions", "Trend is breaking", "Volume is low", "B", "Accumulation = smart money quietly building positions before markup.", "smart_money"),
    ("BOS", "Break of Structure confirms:", "Trend reversal", "Trend continuation", "Range bound", "News event", "B", "BOS = price breaks prior high/low in trend direction. Confirms continuation, not reversal.", "market_structure"),
    ("Discipline", "Good trade is defined by:", "Profit amount", "Following your rules", "Trade frequency", "Market conditions", "B", "Process over outcome. Good trade follows rules; bad trade breaks rules even if profitable.", "psychology"),
    ("Edge", "Trading edge means:", "Winning every trade", "Positive expectancy over time", "Having insider info", "Using indicators", "B", "Edge = positive mathematical expectancy over large sample of trades.", "strategy"),
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
    """Create all tables if they don't exist. Fully idempotent."""
    ok = warn = 0

    for col, definition in _COURSE_COLUMNS:
        sql = f"ALTER TABLE courses ADD COLUMN IF NOT EXISTS {col} {definition}"
        try:
            await database.execute(sql)
            ok += 1
        except Exception as e:
            warn += 1
            print(f"[LMS INIT] courses.{col}: {e}", flush=True)

    for sql in _LEARNING_TABLE_SQLS:
        try:
            await database.execute(sql.strip())
            ok += 1
        except Exception as e:
            warn += 1
            print(f"[LMS INIT] learning table warn: {e}", flush=True)

    print(f"[LMS INIT] Tables done — {ok} ok, {warn} warnings", flush=True)

    # CRITICAL FIX: Use upsert instead of simple seed
    await upsert_curriculum()


async def upsert_curriculum():
    """
    Safely add missing curriculum items without duplicates.
    Preserves existing user progress.
    """
    print("[LMS UPSERT] Checking for missing curriculum...", flush=True)
    
    # Get or create levels
    existing_levels = await database.fetch_all("SELECT id, name FROM learning_levels ORDER BY order_index")
    existing_level_map = {r["name"]: r["id"] for r in existing_levels}
    
    level_id_map = {}  # Maps order_id (1,2,3) to DB id
    
    for order_id, name, desc, order in _LEVELS:
        if name in existing_level_map:
            level_id_map[order_id] = existing_level_map[name]
            print(f"[LMS UPSERT] Level exists: {name}", flush=True)
        else:
            # Insert new level
            new_id = await database.fetch_val(
                "INSERT INTO learning_levels (name, description, order_index) VALUES (:n,:d,:o) RETURNING id",
                {"n": name, "d": desc, "o": order}
            )
            level_id_map[order_id] = new_id
            print(f"[LMS UPSERT] Level created: {name}", flush=True)
    
    # Get or create modules
    existing_modules = await database.fetch_all("SELECT id, title, level_id FROM learning_modules")
    existing_mod_map = {(r["title"], r["level_id"]): r["id"] for r in existing_modules}
    
    module_id_map = {}  # Maps (level_order, title) to DB id
    
    for level_order, title, desc, global_order in _MODULES:
        level_id = level_id_map[level_order]
        key = (title, level_id)
        
        if key in existing_mod_map:
            module_id_map[(level_order, title)] = existing_mod_map[key]
        else:
            new_id = await database.fetch_val(
                "INSERT INTO learning_modules (level_id, title, description, order_index) VALUES (:l,:t,:d,:o) RETURNING id",
                {"l": level_id, "t": title, "d": desc, "o": global_order}
            )
            module_id_map[(level_order, title)] = new_id
            print(f"[LMS UPSERT] Module created: {title}", flush=True)
    
    # Build global module index (1-18) to DB id mapping
    global_idx = 1
    idx_to_db_id = {}
    for level_order in [1, 2, 3]:
        # Get modules for this level in order
        level_mods = [m for m in _MODULES if m[0] == level_order]
        level_mods.sort(key=lambda x: x[3])  # Sort by global_order
        for mod in level_mods:
            title = mod[1]
            db_id = module_id_map[(level_order, title)]
            idx_to_db_id[global_idx] = db_id
            global_idx += 1
    
    # Get existing lessons
    existing_lessons = await database.fetch_all("SELECT id, title, module_id FROM learning_lessons")
    existing_lesson_keys = {(r["title"], r["module_id"]): r["id"] for r in existing_lessons}
    
    lesson_title_to_id = {}
    lessons_added = 0
    
    for mod_global_idx, lesson_order, title, content in _LESSONS:
        if mod_global_idx not in idx_to_db_id:
            continue
            
        module_id = idx_to_db_id[mod_global_idx]
        key = (title, module_id)
        
        if key in existing_lesson_keys:
            lesson_title_to_id[title] = existing_lesson_keys[key]
        else:
            new_id = await database.fetch_val(
                "INSERT INTO learning_lessons (module_id, title, content, order_index) VALUES (:m,:t,:c,:o) RETURNING id",
                {"m": module_id, "t": title, "c": content, "o": lesson_order}
            )
            lesson_title_to_id[title] = new_id
            lessons_added += 1
    
    # Upsert quizzes
    quizzes_added = 0
    for lesson_title, question, a, b, c, d, correct, explanation, slug in _QUIZ_DATA:
        if lesson_title not in lesson_title_to_id:
            continue
            
        lesson_id = lesson_title_to_id[lesson_title]
        
        # Check if this exact quiz exists
        existing = await database.fetch_one(
            "SELECT id FROM lesson_quizzes WHERE lesson_id=:lid AND question=:q",
            {"lid": lesson_id, "q": question}
        )
        
        if not existing:
            await database.execute(
                "INSERT INTO lesson_quizzes (lesson_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation, topic_slug) "
                "VALUES (:lid,:q,:a,:b,:c,:d,:correct,:expl,:slug)",
                {"lid": lesson_id, "q": question, "a": a, "b": b, "c": c, "d": d,
                 "correct": correct, "expl": explanation, "slug": slug}
            )
            quizzes_added += 1
    
    print(f"[LMS UPSERT] Complete: {lessons_added} lessons added, {quizzes_added} quizzes added", flush=True)
    
    # Validate curriculum
    total_lessons = await database.fetch_val("SELECT COUNT(*) FROM learning_lessons")
    total_modules = await database.fetch_val("SELECT COUNT(*) FROM learning_modules")
    print(f"[LMS UPSERT] Curriculum status: {total_modules} modules, {total_lessons} lessons", flush=True)


# Keep old function for backwards compatibility but make it use upsert
async def _seed_curriculum():
    """Legacy wrapper - now uses upsert logic"""
    await upsert_curriculum()
