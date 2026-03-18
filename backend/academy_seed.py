"""
Pipways Trading Academy — Curriculum Seed
==========================================
POST /courses/seed   (admin-only)

Creates the full 3-level, 21-module curriculum if it doesn't exist yet.
Each lesson includes professional Babypips-quality content with:
  • structured sections, real examples, tip/warning/example boxes

Safe to call repeatedly — checks for existing courses by title first.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from .database import database
from .admin import get_admin_user

router = APIRouter()


# ── DB helpers ────────────────────────────────────────────────────────────────

async def _x(q, v=None):
    try:
        return await database.execute(q, v or {})
    except Exception as e:
        print(f"[SEED] exec error: {e}", flush=True)
        raise


async def _one(q, v=None):
    try:
        r = await database.fetch_one(q, v or {})
        return dict(r) if r else None
    except Exception:
        return None


# ── Curriculum data ───────────────────────────────────────────────────────────

CURRICULUM = [
    # ── BEGINNER ──────────────────────────────────────────────────────────────
    {
        "title":       "Beginner",
        "description": "Master the basics of Forex trading from scratch. No prior experience needed.",
        "level":       "Beginner",
        "price":       0,
        "is_published": True,
        "modules": [
            {
                "title":       "Module 1: Introduction to Forex Trading",
                "order_index": 1,
                "lessons": [
                    {
                        "title":   "What is Forex?",
                        "order":   1,
                        "minutes": 8,
                        "content": """<h2>What is Forex?</h2>
<p>Forex (Foreign Exchange) is the global marketplace where currencies are bought and sold — over <strong>$7.5 trillion</strong> traded every single day. It is the largest and most liquid financial market in the world.</p>

<h3>Simple Explanation</h3>
<p>Think of it this way: every time you travel abroad and exchange your home currency for another, you are participating in the Forex market. Professional traders do the same thing — but with the goal of profiting from exchange rate movements.</p>

<h3>How Currency Pairs Work</h3>
<p>Currencies always trade in pairs. The first currency is called the <strong>base currency</strong> and the second is the <strong>quote currency</strong>.</p>
<p>Example: <code>EUR/USD = 1.0850</code> means 1 Euro buys 1.0850 US Dollars.</p>

<div class="example-box">
<strong>Trade Example</strong><br>
Pair: EUR/USD<br>
Direction: Buy (you expect EUR to strengthen against USD)<br>
Entry: 1.0850 · Stop Loss: 1.0800 · Take Profit: 1.0950<br>
Risk: 50 pips · Reward: 100 pips · R:R = 1:2 ✓
</div>

<h3>Key Facts</h3>
<ul>
<li>Market is open 24 hours a day, 5 days a week</li>
<li>No central exchange — trades happen electronically (OTC)</li>
<li>Four major trading sessions: Sydney, Tokyo, London, New York</li>
<li>Most liquid pairs: EUR/USD, GBP/USD, USD/JPY, USD/CHF</li>
</ul>

<div class="tip-box">
<strong>💡 Beginner Tip:</strong> Start with EUR/USD. It has the tightest spreads, the most analysis available, and moves predictably during London and New York sessions.
</div>

<h3>Common Mistakes to Avoid</h3>
<ul>
<li>Trading too many pairs at once — focus on 1–2 to start</li>
<li>Confusing the market being "open" with it being active (volume matters)</li>
<li>Ignoring the spread — the difference between buy and sell price is a cost</li>
</ul>

<h3>Summary</h3>
<p>Forex is simply the exchange of one currency for another. Your goal as a trader is to correctly predict which direction a currency pair will move — and manage risk carefully when you are wrong.</p>""",
                    },
                    {
                        "title":   "Who Trades Forex and Why?",
                        "order":   2,
                        "minutes": 7,
                        "content": """<h2>Who Trades Forex?</h2>
<p>Understanding the major market participants helps you predict price movements more accurately.</p>

<h3>1. Central Banks</h3>
<p>The most powerful players. Central banks (like the US Federal Reserve, European Central Bank) set interest rates and intervene in currency markets to stabilize their economies.</p>
<div class="tip-box"><strong>Why it matters:</strong> When the Fed raises interest rates, USD typically strengthens — capital flows into the US for higher returns.</div>

<h3>2. Commercial Banks</h3>
<p>Banks like JP Morgan, Goldman Sachs, Deutsche Bank execute enormous orders on behalf of clients and for their own profit. They see order flow data retail traders cannot access.</p>

<h3>3. Corporations</h3>
<p>A company like Apple earning billions in Euros must convert those earnings to USD. This creates predictable, large-volume flows at certain times of the month.</p>

<h3>4. Retail Traders (You)</h3>
<p>Individual traders accessing the market through brokers. We represent less than 5% of total volume, which is why trading against the institutional trend is dangerous.</p>

<div class="warning-box">
<strong>⚠ Important:</strong> Retail traders are at an information disadvantage. Your edge comes from discipline, risk management, and reading the market structure that institutions create — not from outsmarting them.
</div>

<h3>Summary</h3>
<p>The hierarchy is: Central Banks → Commercial Banks → Corporations → Retail Traders. Price moves when large participants need to buy or sell. Your job is to identify these movements and trade with them — not against them.</p>""",
                    },
                ]
            },
            {
                "title":       "Module 2: Currency Pairs and Price Quotes",
                "order_index": 2,
                "lessons": [
                    {
                        "title":   "Major, Minor, and Exotic Pairs",
                        "order":   1,
                        "minutes": 9,
                        "content": """<h2>Currency Pairs Explained</h2>
<p>All Forex trades involve two currencies. Understanding the three categories helps you choose the right pairs to trade.</p>

<h3>Major Pairs (Always include USD)</h3>
<ul>
<li><strong>EUR/USD</strong> — Euro / US Dollar (most traded pair in the world)</li>
<li><strong>GBP/USD</strong> — British Pound / US Dollar (known as "Cable")</li>
<li><strong>USD/JPY</strong> — US Dollar / Japanese Yen</li>
<li><strong>USD/CHF</strong> — US Dollar / Swiss Franc (safe-haven pair)</li>
<li><strong>AUD/USD</strong> — Australian Dollar / US Dollar (commodity-linked)</li>
<li><strong>USD/CAD</strong> — US Dollar / Canadian Dollar (oil-correlated)</li>
</ul>
<div class="tip-box"><strong>Majors advantage:</strong> Tight spreads (0.1–1 pip), high liquidity, abundant analysis available online.</div>

<h3>Minor / Cross Pairs (No USD)</h3>
<ul>
<li>EUR/GBP · EUR/JPY · GBP/JPY · AUD/JPY</li>
<li>Wider spreads than majors but still good liquidity</li>
<li>GBP/JPY is nicknamed "the Dragon" — extremely volatile</li>
</ul>

<h3>Exotic Pairs</h3>
<p>One major currency + one emerging market currency (USD/ZAR, EUR/TRY, USD/MXN). Very wide spreads, news-sensitive, not recommended for beginners.</p>

<div class="example-box">
<strong>Spread Comparison:</strong><br>
EUR/USD: 0.1–0.5 pip spread<br>
GBP/JPY: 1–3 pip spread<br>
USD/ZAR: 30–80 pip spread<br>
<em>Wider spread = more expensive to trade</em>
</div>

<h3>Summary</h3>
<p>Beginners should start with EUR/USD or GBP/USD. Once consistent, expand to other majors. Avoid exotics until you are highly experienced.</p>""",
                    },
                    {
                        "title":   "Reading Price Quotes and Pips",
                        "order":   2,
                        "minutes": 8,
                        "content": """<h2>Reading Forex Prices</h2>
<p>Understanding how prices are quoted and measured is fundamental to every trade you will ever make.</p>

<h3>Bid vs Ask</h3>
<p>Every price has two sides:</p>
<ul>
<li><strong>Bid</strong> — the price brokers will buy from you (you sell at this price)</li>
<li><strong>Ask</strong> — the price brokers will sell to you (you buy at this price)</li>
<li><strong>Spread</strong> = Ask − Bid. This is the broker's fee.</li>
</ul>

<h3>What is a Pip?</h3>
<p>A <strong>pip</strong> (Percentage In Point) is the smallest standard price movement. For most pairs (4 decimal places), 1 pip = 0.0001.</p>
<div class="example-box">
EUR/USD moves from 1.0850 to 1.0860 = <strong>10 pip move</strong><br>
USD/JPY moves from 149.50 to 150.00 = <strong>50 pip move</strong><br>
(JPY pairs: 1 pip = 0.01 because only 2 decimal places)
</div>

<h3>Pip Value Calculation</h3>
<p>Pip value depends on your lot size and the currency pair:</p>
<ul>
<li>Standard Lot (100,000 units): ~$10 per pip on EUR/USD</li>
<li>Mini Lot (10,000 units): ~$1 per pip</li>
<li>Micro Lot (1,000 units): ~$0.10 per pip</li>
</ul>

<div class="warning-box">
<strong>⚠ Critical for Risk Management:</strong> Always calculate your pip value before entering a trade. A 50-pip stop loss on a standard lot costs $500 — know your risk before you click.
</div>

<h3>Summary</h3>
<p>Pips measure profit and loss. Lot size controls how much each pip is worth. Always calculate: lot size × pips × pip value = dollar risk.</p>""",
                    },
                ]
            },
            {
                "title":       "Module 3: Basic Risk Management",
                "order_index": 3,
                "lessons": [
                    {
                        "title":   "The 1-2% Rule",
                        "order":   1,
                        "minutes": 10,
                        "content": """<h2>The Most Important Rule in Trading</h2>
<p>Professional traders protect their capital above all else. The <strong>1–2% rule</strong> is the foundation of surviving the market long enough to become consistently profitable.</p>

<h3>The Rule</h3>
<p><strong>Never risk more than 1–2% of your account on any single trade.</strong></p>

<div class="example-box">
<strong>Example — $10,000 account:</strong><br>
Maximum risk per trade (2%) = $200<br>
Stop loss = 50 pips on EUR/USD<br>
Required lot size = 200 ÷ 50 ÷ 10 = 0.4 lots (mini lots)<br>
This keeps your risk at exactly $200 regardless of the trade outcome.
</div>

<h3>Why This Rule Saves You</h3>
<p>With 2% risk, you need 50 consecutive losing trades to lose your entire account. In practice, no sound strategy loses 50 times in a row.</p>
<p>Compare: With 10% risk, just 10 losses wipe you out. Most beginners lose 10 trades early on while learning.</p>

<h3>Risk-to-Reward Ratio</h3>
<p>Every trade must have a defined risk:reward (R:R). Aim for minimum <strong>1:2</strong> — risking $100 to make $200.</p>
<ul>
<li>With 1:2 R:R you can be profitable even if you only win 40% of trades</li>
<li>1:1 R:R requires >50% win rate just to break even</li>
<li>1:3 or better R:R allows profitability with only 35% win rate</li>
</ul>

<div class="tip-box">
<strong>💡 The Math of Survival:</strong> A trader with a 45% win rate and 1:2 R:R is MORE profitable than a trader with a 60% win rate and 1:1 R:R. It's not about being right — it's about how much you make when you're right vs. how much you lose when you're wrong.
</div>

<h3>Summary</h3>
<p>Define your risk before every trade. Use 1–2% max. Seek 1:2 minimum reward-to-risk. These two rules will keep you in the game long enough to develop real skill.</p>""",
                    },
                    {
                        "title":   "Stop Loss and Take Profit",
                        "order":   2,
                        "minutes": 9,
                        "content": """<h2>Stop Loss and Take Profit</h2>
<p>Every trade needs both a stop loss and a take profit before you click "Buy" or "Sell". No exceptions.</p>

<h3>Stop Loss</h3>
<p>A stop loss is an automatic order that closes your trade at a predefined loss level. It exists to protect you when you are wrong.</p>
<div class="warning-box">
<strong>Never trade without a stop loss.</strong> The market can move hundreds of pips against you in minutes during news events. A trade without a stop loss is gambling, not trading.
</div>

<h3>Where to Place Your Stop Loss</h3>
<ul>
<li><strong>Below support</strong> for buy trades — place stop just below the swing low</li>
<li><strong>Above resistance</strong> for sell trades — place stop just above the swing high</li>
<li>Give enough room for normal price fluctuation (avoid placing stops too tight)</li>
</ul>

<h3>Take Profit</h3>
<p>A take profit automatically closes your trade when it reaches your profit target. This prevents greed from turning winners into losers.</p>

<div class="example-box">
<strong>Complete Trade Setup — EUR/USD:</strong><br>
Entry: 1.0850 (Buy)<br>
Stop Loss: 1.0800 (50 pip risk)<br>
Take Profit: 1.0950 (100 pip reward)<br>
R:R = 1:2 ✓<br>
Account: $10,000 · Risk: 2% = $200<br>
Lot size: 0.4 (mini lots)<br>
<em>Everything defined before the trade is entered.</em>
</div>

<h3>Trailing Stops</h3>
<p>A trailing stop moves with price as your trade moves into profit, locking in gains while leaving room to run. Useful for trend-following strategies.</p>

<h3>Summary</h3>
<p>Stop loss placement is a skill developed over time. Always place it at a logical technical level — not at an arbitrary pip number. Your stop loss is your insurance policy: pay for it on every trade.</p>""",
                    },
                ]
            },
            {
                "title":       "Module 4: Introduction to Trading Charts",
                "order_index": 4,
                "lessons": [
                    {
                        "title":   "Candlestick Charts Explained",
                        "order":   1,
                        "minutes": 10,
                        "content": """<h2>Reading Candlestick Charts</h2>
<p>Candlestick charts originated in 18th-century Japan and remain the most popular chart type for traders because they display four key data points in one visual element.</p>

<h3>Anatomy of a Candle</h3>
<p>Each candle represents a specific time period (1 minute, 1 hour, 1 day, etc.):</p>
<ul>
<li><strong>Open</strong> — price at the start of the period</li>
<li><strong>High</strong> — highest price reached</li>
<li><strong>Low</strong> — lowest price reached</li>
<li><strong>Close</strong> — price at the end of the period</li>
</ul>
<p>The <strong>body</strong> (rectangle) shows the range between open and close. The <strong>wicks/shadows</strong> show the high and low.</p>
<p>🟢 <strong>Green (bullish) candle</strong> — close is above open (price went up)<br>
🔴 <strong>Red (bearish) candle</strong> — close is below open (price went down)</p>

<h3>Timeframes</h3>
<ul>
<li><strong>M1/M5/M15</strong> — scalping, very noisy, requires experience</li>
<li><strong>H1/H4</strong> — intraday trading, good balance of signals and noise</li>
<li><strong>D1/W1</strong> — swing trading, cleaner signals, less time commitment</li>
</ul>
<div class="tip-box">
<strong>Multi-timeframe analysis:</strong> Always check the daily chart for trend direction before entering on the H1. Trade in the direction of the higher timeframe trend.
</div>

<h3>Key Candlestick Patterns</h3>
<ul>
<li><strong>Doji</strong> — open and close are almost equal; signals indecision</li>
<li><strong>Engulfing</strong> — large candle completely covers the previous candle; signals reversal</li>
<li><strong>Hammer/Pin Bar</strong> — long wick with small body; signals rejection of a level</li>
</ul>

<h3>Summary</h3>
<p>Candlestick charts tell a story about the battle between buyers and sellers in each time period. Learning to read this story is the foundation of all technical analysis.</p>""",
                    },
                    {
                        "title":   "Support and Resistance Basics",
                        "order":   2,
                        "minutes": 12,
                        "content": """<h2>Support and Resistance</h2>
<p>Support and resistance are the most fundamental concepts in technical analysis. They represent price levels where the market has historically reversed or paused — creating high-probability trade locations.</p>

<h3>What is Support?</h3>
<p>Support is a price level where buying pressure has historically been strong enough to stop price from falling further. Think of it as a "floor" under price.</p>
<p>Price falls → hits support → buyers enter → price bounces up.</p>

<h3>What is Resistance?</h3>
<p>Resistance is a price level where selling pressure has historically been strong enough to stop price from rising further. Think of it as a "ceiling" above price.</p>
<p>Price rises → hits resistance → sellers enter → price falls.</p>

<h3>Why These Levels Form</h3>
<p>Psychological levels form because traders remember significant price points:</p>
<ul>
<li>Previous highs and lows attract fresh orders</li>
<li>Round numbers (1.1000, 1.0500) create supply and demand clusters</li>
<li>Broken resistance becomes new support (and vice versa)</li>
</ul>

<div class="example-box">
<strong>Role Reversal Example:</strong><br>
EUR/USD resistance at 1.0900 (price failed here 3 times)<br>
Price eventually breaks ABOVE 1.0900<br>
1.0900 is now SUPPORT — buyers defend it on pullbacks<br>
This is called <em>role reversal</em> — a key concept in price action trading.
</div>

<h3>How to Draw Levels</h3>
<ul>
<li>Use the <strong>body</strong> of candles to identify major levels (not always wicks)</li>
<li>Zones (areas) are more reliable than single price lines</li>
<li>More touches = stronger level (2+ touches required to call it significant)</li>
<li>Recent levels matter more than ancient history</li>
</ul>

<div class="warning-box">
<strong>⚠ Common Mistake:</strong> Beginners draw too many support/resistance lines and see "levels" everywhere. Identify only the 2–3 most significant levels on each chart. Quality over quantity.
</div>

<h3>Summary</h3>
<p>Support and resistance are the skeleton of every chart. Every valid trading strategy uses these levels for entries, stop losses, and take profits. Master this concept before anything else.</p>""",
                    },
                ]
            },
        ]
    },

    # ── INTERMEDIATE ──────────────────────────────────────────────────────────
    {
        "title":       "Intermediate",
        "description": "Build strategies using technical analysis, chart patterns, and trading indicators.",
        "level":       "Intermediate",
        "price":       0,
        "is_published": True,
        "modules": [
            {
                "title":       "Module 1: Technical Analysis Fundamentals",
                "order_index": 1,
                "lessons": [
                    {
                        "title":   "Trend Identification",
                        "order":   1,
                        "minutes": 12,
                        "content": """<h2>Identifying Market Trends</h2>
<p>The most powerful concept in trading: <strong>"The trend is your friend."</strong> Trading with the trend dramatically increases your probability of success.</p>

<h3>Defining a Trend</h3>
<ul>
<li><strong>Uptrend</strong> — series of Higher Highs (HH) and Higher Lows (HL)</li>
<li><strong>Downtrend</strong> — series of Lower Highs (LH) and Lower Lows (LL)</li>
<li><strong>Ranging / Sideways</strong> — price oscillates between two horizontal levels</li>
</ul>

<h3>Trend Confirmation Methods</h3>
<p><strong>1. Moving Averages:</strong></p>
<ul>
<li>Price above 50 EMA and 200 EMA → bullish bias</li>
<li>Price below both EMAs → bearish bias</li>
<li>50 EMA crossing above 200 EMA → "Golden Cross" (bullish signal)</li>
<li>50 EMA crossing below 200 EMA → "Death Cross" (bearish signal)</li>
</ul>

<div class="example-box">
<strong>Multi-Timeframe Trend Example:</strong><br>
Daily chart: EUR/USD is in an uptrend (HH/HL structure, above 200 EMA)<br>
H4 chart: Price pulls back to 50 EMA support<br>
H1 chart: Bullish engulfing candle forms at support<br>
<strong>Trade: Buy at H4 support, with daily trend. Confluence = high probability.</strong>
</div>

<h3>Trendlines</h3>
<p>Draw trendlines by connecting swing lows in an uptrend (or swing highs in a downtrend). Requires minimum 2 points, confirmed by a 3rd touch.</p>

<div class="tip-box">
<strong>💡 Professional Approach:</strong> Don't fight the trend. If the daily chart is in a downtrend, do not look for buy signals on the H1 — regardless of how "good" they look. Trade in the direction of the highest timeframe trend you can identify.
</div>

<h3>Trend Strength</h3>
<p>Strong trends: small pullbacks, candles mostly one color, clean structure<br>
Weak trends: deep pullbacks (>50%), choppy price action, mixed signals</p>

<h3>Summary</h3>
<p>Identify the trend on the daily chart. Use lower timeframes only to time entries in the direction of the daily trend. Never fight a strong trend — it is the single biggest mistake intermediate traders make.</p>""",
                    },
                    {
                        "title":   "Trading Indicators: MACD, RSI, Moving Averages",
                        "order":   2,
                        "minutes": 14,
                        "content": """<h2>Trading Indicators</h2>
<p>Indicators are mathematical calculations based on price history. They help confirm trends, identify momentum, and time entries — but should never replace price action analysis.</p>

<h3>Moving Averages (MA)</h3>
<p><strong>Simple MA (SMA)</strong> — equal weight to all periods<br>
<strong>Exponential MA (EMA)</strong> — more weight to recent prices; faster reaction</p>
<p>Key levels used by professionals: <strong>20 EMA, 50 EMA, 200 EMA</strong></p>
<div class="tip-box">The 200 EMA on the daily chart is watched by banks and institutional traders. Price bouncing off the 200 EMA is a significant event.</div>

<h3>RSI — Relative Strength Index</h3>
<p>Measures momentum on a 0–100 scale.</p>
<ul>
<li>RSI above 70 → overbought (potential sell signal)</li>
<li>RSI below 30 → oversold (potential buy signal)</li>
<li><strong>RSI divergence</strong> — price makes new high but RSI makes lower high → momentum weakening → reversal warning</li>
</ul>

<div class="warning-box">
<strong>⚠ RSI Mistake:</strong> Overbought does NOT mean "sell now." In a strong uptrend, RSI can stay above 70 for weeks. Use RSI divergence, not overbought/oversold levels alone, for reversal signals.
</div>

<h3>MACD — Moving Average Convergence Divergence</h3>
<p>Components: MACD Line · Signal Line · Histogram</p>
<ul>
<li>MACD line crosses above signal line → bullish momentum</li>
<li>MACD line crosses below signal line → bearish momentum</li>
<li>Histogram above zero → bullish · Below zero → bearish</li>
<li>MACD divergence → same as RSI divergence, very reliable signal</li>
</ul>

<div class="example-box">
<strong>High-Probability Setup Using Confluence:</strong><br>
1. Daily trend: Uptrend (price above 200 EMA)<br>
2. H4 price at support level<br>
3. RSI on H4 at 35 (oversold in context of uptrend)<br>
4. MACD bullish crossover on H4<br>
5. Bullish pin bar forms at support<br>
<strong>All 5 factors confirm → strong buy signal</strong>
</div>

<h3>Summary</h3>
<p>Use maximum 2–3 indicators. More indicators = more confusion and conflicting signals. Combine price action + 1 trend indicator + 1 momentum indicator for your best setups.</p>""",
                    },
                ]
            },
            {
                "title":       "Module 2: Chart Patterns",
                "order_index": 2,
                "lessons": [
                    {
                        "title":   "Head and Shoulders, Double Top/Bottom",
                        "order":   1,
                        "minutes": 13,
                        "content": """<h2>Reversal Chart Patterns</h2>
<p>Reversal patterns signal that the current trend is losing momentum and a directional change is likely. These are among the most reliable patterns in technical analysis.</p>

<h3>Head and Shoulders (H&S)</h3>
<p>Appears at the end of an uptrend. Structure:</p>
<ul>
<li>Left Shoulder — price rallies, then pulls back</li>
<li>Head — price rallies to a new high, then pulls back</li>
<li>Right Shoulder — price rallies to the same level as the left shoulder, then falls</li>
<li>Neckline — the support level connecting the two pullback lows</li>
</ul>
<p><strong>Entry:</strong> Sell when price breaks below the neckline<br>
<strong>Target:</strong> Measure the distance from head to neckline — project down from breakout<br>
<strong>Stop:</strong> Above the right shoulder</p>

<div class="example-box">
<strong>EUR/USD Example:</strong><br>
Left shoulder high: 1.1200 · Head high: 1.1350 · Right shoulder high: 1.1210<br>
Neckline: 1.1050<br>
Head to neckline distance: 300 pips<br>
Target after neckline break: 1.1050 − 300 = 0.7750<br>
<em>Risk is well-defined, target is measurable.</em>
</div>

<h3>Double Top</h3>
<p>Two peaks at approximately the same price level. Confirms when price breaks below the "valley" between the two peaks.</p>
<div class="tip-box"><strong>Key rule:</strong> Wait for the break. Do NOT sell just because you see two tops — the pattern only confirms on the break of support.</div>

<h3>Double Bottom</h3>
<p>Mirror image of double top. Two lows at the same level, confirms on break above resistance between the two lows. Bullish reversal pattern.</p>

<h3>Summary</h3>
<p>Reversal patterns are powerful but require patience. Always wait for the confirmation break before entering. False breaks happen — stop placement is critical.</p>""",
                    },
                    {
                        "title":   "Flags, Pennants, and Continuation Patterns",
                        "order":   2,
                        "minutes": 11,
                        "content": """<h2>Continuation Patterns</h2>
<p>Continuation patterns form when the market pauses during a trend before continuing in the original direction. They represent areas where price consolidates before the next move.</p>

<h3>Bull/Bear Flag</h3>
<p>The most common and reliable continuation pattern.</p>
<ul>
<li><strong>Flagpole</strong> — sharp move in the trend direction (strong momentum)</li>
<li><strong>Flag</strong> — sideways or slight counter-trend consolidation (low volume, tight range)</li>
<li><strong>Breakout</strong> — price breaks in the original trend direction with volume</li>
</ul>
<p>Target = flagpole length projected from breakout point.</p>

<div class="example-box">
<strong>Bull Flag Setup:</strong><br>
GBP/USD moves from 1.2500 to 1.2600 in one session (flagpole = 100 pips)<br>
Price consolidates between 1.2560–1.2590 for 4 hours (flag)<br>
Price breaks above 1.2590 (flag upper boundary)<br>
Target: 1.2590 + 100 pips = 1.2690<br>
Stop: Below 1.2560 (flag lower boundary)
</div>

<h3>Pennant</h3>
<p>Similar to a flag but the consolidation forms converging trendlines (triangle shape). Slightly shorter timeframe than a flag. Same entry and measurement rules apply.</p>

<h3>Ascending/Descending Triangle</h3>
<ul>
<li><strong>Ascending:</strong> flat resistance + rising lows → buyers more aggressive → bullish bias</li>
<li><strong>Descending:</strong> flat support + falling highs → sellers more aggressive → bearish bias</li>
</ul>

<div class="warning-box">
<strong>⚠ Pattern Failure:</strong> No pattern works 100% of the time. Always define your stop loss before entry. Pattern failures often create strong moves in the opposite direction — don't add to a losing pattern trade.
</div>

<h3>Summary</h3>
<p>Continuation patterns give you high-probability entries in established trends. The key: identify the trend first, then look for the pattern as a low-risk entry opportunity.</p>""",
                    },
                ]
            },
            {
                "title":       "Module 3: Trading Strategies",
                "order_index": 3,
                "lessons": [
                    {
                        "title":   "Building a Trading Strategy",
                        "order":   1,
                        "minutes": 15,
                        "content": """<h2>Building a Complete Trading Strategy</h2>
<p>A trading strategy is a defined set of rules for entering and exiting trades. Without rules, you are reacting emotionally. With rules, you can measure, improve, and trust your process.</p>

<h3>The 5 Elements of Every Strategy</h3>
<ol>
<li><strong>Market Selection</strong> — which pairs/assets and which sessions</li>
<li><strong>Trend Filter</strong> — which direction are you allowed to trade?</li>
<li><strong>Entry Trigger</strong> — what exactly signals an entry?</li>
<li><strong>Risk Management</strong> — position size, stop loss placement</li>
<li><strong>Exit Rules</strong> — take profit targets, trailing stop, or time-based exit</li>
</ol>

<h3>Example Strategy: Trend Pullback</h3>
<div class="example-box">
<strong>The 50 EMA Pullback Strategy:</strong><br>
1. Market: EUR/USD, GBP/USD<br>
2. Session: London open (08:00–11:00 GMT)<br>
3. Trend filter: Daily trend must be bullish (HH/HL + above 200 EMA)<br>
4. Setup: H1 price pulls back to 50 EMA<br>
5. Entry trigger: Bullish pin bar or engulfing candle at the 50 EMA<br>
6. Stop loss: 10 pips below the pin bar low<br>
7. Take profit: 1:2 R:R (2× stop loss distance)<br>
<br>
<em>All 5 elements defined. Rules are objective — no discretion needed.</em>
</div>

<h3>Why Most Traders Lose</h3>
<ul>
<li>No defined strategy — trade on impulse</li>
<li>Changing strategy after every losing trade</li>
<li>Not accounting for spread and slippage in planning</li>
<li>Risking too much per trade (emotional decisions follow)</li>
<li>Not keeping a trade journal to track results</li>
</ul>

<div class="tip-box">
<strong>💡 The 20-Trade Rule:</strong> Any strategy needs at least 20–50 trades to evaluate properly. A strategy with 3 losing trades is NOT proven to be bad. Run it consistently for a sample size before judging.
</div>

<h3>Summary</h3>
<p>Write your strategy down. Every rule. Test it on past data (backtesting). Then forward test in a demo account. Only trade it live when you have 50+ documented demo trades proving edge. This discipline separates profitable traders from the 75% who lose.</p>""",
                    },
                ]
            },
        ]
    },

    # ── ADVANCED ──────────────────────────────────────────────────────────────
    {
        "title":       "Advanced",
        "description": "Trade like an institution. Master market structure, liquidity, and advanced psychology.",
        "level":       "Advanced",
        "price":       0,
        "is_published": True,
        "modules": [
            {
                "title":       "Module 1: Market Structure",
                "order_index": 1,
                "lessons": [
                    {
                        "title":   "Institutional Market Structure",
                        "order":   1,
                        "minutes": 18,
                        "content": """<h2>Institutional Market Structure (IMS / SMC)</h2>
<p>Market structure analysis focuses on understanding how large institutional participants (banks, hedge funds) move price. Unlike retail technical analysis, IMS looks at the WHY behind price movements.</p>

<h3>Break of Structure (BOS)</h3>
<p>A BOS occurs when price breaks a significant swing high (in uptrend) or swing low (in downtrend). BOS confirms the current trend is continuing.</p>
<ul>
<li><strong>Bullish BOS</strong> — price breaks above a previous swing high → uptrend confirmation</li>
<li><strong>Bearish BOS</strong> — price breaks below a previous swing low → downtrend confirmation</li>
</ul>

<h3>Change of Character (CHOCH)</h3>
<p>A CHoCH signals a potential trend reversal:</p>
<ul>
<li>In an uptrend: price breaks below the most recent swing LOW (HH/HL structure breaks down)</li>
<li>This is the first warning of trend change — not a confirmed reversal until structure flips on higher TF</li>
</ul>

<h3>Order Blocks</h3>
<p>An order block is the last bearish candle before a bullish impulse (or last bullish candle before bearish impulse). Institutions leave unfilled orders at these levels, creating strong support/resistance.</p>

<div class="example-box">
<strong>Identifying a Bullish Order Block:</strong><br>
1. Daily chart: EUR/USD in uptrend<br>
2. Pullback occurs on H4<br>
3. Find the last red candle before the most recent bullish impulse move<br>
4. Mark its high and low as the order block zone<br>
5. When price returns to this zone: look for H1 bullish entries<br>
<em>Institutions defending their position = high-probability bounce</em>
</div>

<h3>Fair Value Gaps (FVG / Imbalance)</h3>
<p>A Fair Value Gap is a three-candle pattern where the middle candle moves so fast that price leaves a gap between candle 1's high and candle 3's low. These gaps are "inefficiencies" that price tends to revisit before continuing.</p>

<div class="tip-box">
<strong>Combine for High Probability:</strong> Order Block + FVG filling + BOS = one of the strongest setups in institutional trading. Price often fills the FVG before continuing in the trend direction.
</div>

<h3>Summary</h3>
<p>Institutional market structure shifts your perspective from "price is random" to "price moves purposefully to engineer liquidity." Once you see the structure, you cannot unsee it — and your entries become far more precise.</p>""",
                    },
                    {
                        "title":   "Liquidity and Stop Hunts",
                        "order":   2,
                        "minutes": 16,
                        "content": """<h2>Liquidity: The Institutional Perspective</h2>
<p>Banks and large institutions need liquidity — the ability to fill enormous orders without moving the market against themselves. This need for liquidity explains price movements that appear irrational to retail traders.</p>

<h3>What is Liquidity?</h3>
<p>Liquidity pools are areas where large numbers of orders cluster. Two main types:</p>
<ul>
<li><strong>Buy-side liquidity</strong> — stop losses of sell trades + pending buy stops, sitting ABOVE recent highs</li>
<li><strong>Sell-side liquidity</strong> — stop losses of buy trades + pending sell limits, sitting BELOW recent lows</li>
</ul>

<h3>The Stop Hunt</h3>
<p>Institutions move price into liquidity pools to fill their opposite orders:</p>
<ul>
<li>Price sweeps above equal highs → triggers retail buy stops → institution SELLS into this liquidity</li>
<li>Price sweeps below equal lows → triggers retail sell stops → institution BUYS into this liquidity</li>
</ul>

<div class="example-box">
<strong>Classic Stop Hunt Pattern:</strong><br>
1. GBP/USD forms equal highs at 1.2600 (obvious resistance)<br>
2. Price sweeps ABOVE 1.2600 briefly (stop hunt — triggers retail sellers' stops)<br>
3. Price quickly reverses below 1.2600<br>
4. Retail traders who were long: stopped out just above 1.2600<br>
5. Institutional players: sold into the liquidity spike<br>
6. Price drops 150 pips after the sweep<br>
<br>
<em>The "fake breakout" you've seen countless times = a stop hunt.</em>
</div>

<h3>How to Use This</h3>
<ul>
<li>Stop placing stops at obvious levels (equal highs/lows, round numbers)</li>
<li>Wait for the sweep to complete before entering (patience!)</li>
<li>Look for pin bars or engulfing candles AFTER the sweep as confirmation</li>
<li>The sweep + reversal candle = one of the highest-probability entries available</li>
</ul>

<div class="warning-box">
<strong>⚠ Trap:</strong> Not every sweep leads to a strong reversal. Always confirm with market structure: if the higher timeframe trend is strongly bullish, a brief sweep below a low is likely a hunt — a true break changes the structure.
</div>

<h3>Summary</h3>
<p>Stop hunts are engineered moves designed to trigger retail orders and provide institutional liquidity. Once you recognize them, you stop being the victim and start being the beneficiary. Patience and discipline are required — wait for the sweep, confirm the reversal, then enter.</p>""",
                    },
                ]
            },
            {
                "title":       "Module 2: Trading Psychology",
                "order_index": 2,
                "lessons": [
                    {
                        "title":   "The Psychology of a Profitable Trader",
                        "order":   1,
                        "minutes": 14,
                        "content": """<h2>Trading Psychology</h2>
<p>Studies consistently show that 75–80% of retail Forex traders lose money. The primary reason is not lack of strategy — it is failure to control psychology and emotions.</p>

<h3>The Four Deadly Emotions</h3>
<p><strong>1. Fear of Loss</strong><br>
Causes: cutting winners short, not taking valid setups, moving stop losses tighter (opposite of correct).</p>
<p><strong>2. Greed</strong><br>
Causes: holding trades beyond targets, adding to losing positions, overtrading after wins ("now I can't lose").</p>
<p><strong>3. Hope</strong><br>
Causes: not taking stop losses, hoping the market will "come back." It usually doesn't.</p>
<p><strong>4. Revenge Trading</strong><br>
After a loss: entering a new trade immediately to "get it back." Emotional, unplanned, almost always creates a second (larger) loss.</p>

<div class="warning-box">
<strong>⚠ The Revenge Trading Trap:</strong> You lose $200 on EUR/USD. You feel angry. You immediately enter a GBP/USD trade with $500 risk to "make it back fast." You lose again. Now you're down $700 and your emotions are controlling the account. This is how accounts are blown in one afternoon.
</div>

<h3>Process vs Outcome Thinking</h3>
<p>Beginners focus on outcomes: "Did this trade win?" Professionals focus on process: "Did I follow my rules?"</p>
<p>A trade can follow all rules perfectly and still lose. That is NOT a bad trade — it is the correct process losing to market randomness. Over 100 trades, the correct process generates profit.</p>

<h3>Building Mental Discipline</h3>
<ul>
<li><strong>Daily limits:</strong> Maximum 2 losses per session. Stop trading after 2 losses, no exceptions.</li>
<li><strong>Pre-trade checklist:</strong> Write down your setup, entry, stop, target before clicking. Forces rational thinking.</li>
<li><strong>Post-trade review:</strong> Did you follow your rules? The P&L doesn't matter for evaluation — rule adherence does.</li>
<li><strong>Journal everything:</strong> Screenshots, notes, emotions. Patterns in losing trades become visible within weeks.</li>
</ul>

<div class="tip-box">
<strong>💡 The Best Traders:</strong> Don't feel excited when they win or devastated when they lose. They feel the same after both — because they know the outcome of one trade is irrelevant to the long-term edge. Emotional neutrality is the goal.
</div>

<h3>Summary</h3>
<p>Your greatest trading enemy lives between your ears. Technical skill without psychological discipline is worthless. Build the habit of following your rules first — profitability will follow. It is not possible to be consistently profitable without consistent emotional control.</p>""",
                    },
                ]
            },
        ]
    },
]


# ── Seed endpoint ─────────────────────────────────────────────────────────────

@router.post("/seed")
async def seed_academy(_=Depends(get_admin_user)):
    """
    Seed the full Pipways Trading Academy curriculum.
    Safe to call multiple times — skips courses that already exist (by title).
    """
    created_courses = 0
    created_modules = 0
    created_lessons = 0

    for course_data in CURRICULUM:
        # Check if course already exists
        existing = await _one(
            "SELECT id FROM courses WHERE title = :t",
            {"t": course_data["title"]}
        )
        if existing:
            print(f"[SEED] Course '{course_data['title']}' already exists — skipping", flush=True)
            continue

        # ── Create the course (minimal guaranteed columns first) ──────────────
        now = datetime.utcnow()
        try:
            cid = await _x(
                "INSERT INTO courses (title, description, level, created_at)"
                " VALUES (:title, :desc, :level, :now) RETURNING id",
                {"title": course_data["title"],
                 "desc":  course_data["description"],
                 "level": course_data["level"],
                 "now":   now}
            )
        except Exception as e:
            print(f"[SEED] Course insert failed: {e}", flush=True)
            raise HTTPException(500, f"Failed to create course '{course_data['title']}': {e}")

        # Patch extra columns individually (safe if not yet migrated)
        for col, val in [
            ("is_published", course_data.get("is_published", True)),
            ("is_active",    course_data.get("is_published", True)),
            ("price",        course_data.get("price", 0)),
        ]:
            try:
                await database.execute(
                    f"UPDATE courses SET {col} = :v WHERE id = :id",
                    {"v": val, "id": cid}
                )
            except Exception:
                pass

        created_courses += 1
        print(f"[SEED] Created course id={cid}: {course_data['title']}", flush=True)

        # ── Create modules ────────────────────────────────────────────────────
        for mod_data in course_data.get("modules", []):
            try:
                mid = await _x(
                    "INSERT INTO course_modules (course_id, title, description, order_index)"
                    " VALUES (:cid, :title, :desc, :ord) RETURNING id",
                    {"cid":   cid,
                     "title": mod_data["title"],
                     "desc":  mod_data.get("description", ""),
                     "ord":   mod_data.get("order_index", 0)}
                )
            except Exception as e:
                print(f"[SEED] Module insert failed: {e}", flush=True)
                continue

            created_modules += 1

            # ── Create lessons ────────────────────────────────────────────────
            for lesson in mod_data.get("lessons", []):
                try:
                    await _x(
                        "INSERT INTO lessons"
                        " (course_id, module_id, title, content,"
                        "  duration_minutes, order_index, is_free_preview, created_at)"
                        " VALUES (:cid, :mid, :title, :content,"
                        "         :dur, :ord, :preview, :now) RETURNING id",
                        {"cid":     cid,
                         "mid":     mid,
                         "title":   lesson["title"],
                         "content": lesson.get("content", ""),
                         "dur":     lesson.get("minutes", 10),
                         "ord":     lesson.get("order", 0),
                         "preview": True,   # all lessons free for now
                         "now":     now}
                    )
                    created_lessons += 1
                except Exception as e:
                    print(f"[SEED] Lesson insert failed '{lesson['title']}': {e}", flush=True)

        # Update lesson_count on the course
        try:
            await database.execute(
                "UPDATE courses SET lesson_count = "
                "(SELECT COUNT(*) FROM lessons WHERE course_id = :id) WHERE id = :id",
                {"id": cid}
            )
        except Exception:
            pass

    return {
        "message":         "Academy seeded successfully",
        "courses_created": created_courses,
        "modules_created": created_modules,
        "lessons_created": created_lessons,
    }


@router.get("/seed/status")
async def seed_status(_=Depends(get_admin_user)):
    """Check current academy content counts."""
    try:
        courses = await database.fetch_one("SELECT COUNT(*) AS c FROM courses")
        modules = await database.fetch_one("SELECT COUNT(*) AS c FROM course_modules")
        lessons = await database.fetch_one("SELECT COUNT(*) AS c FROM lessons")
        return {
            "courses": dict(courses).get("c", 0) if courses else 0,
            "modules": dict(modules).get("c", 0) if modules else 0,
            "lessons": dict(lessons).get("c", 0) if lessons else 0,
        }
    except Exception as e:
        return {"error": str(e)}
