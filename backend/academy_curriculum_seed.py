"""
Pipways Trading Academy — Complete Curriculum Seed Data
Contains all 36 lessons (3 Levels × 6 Modules × 2 Lessons)
Each lesson includes: content, 5 quiz questions, SVG diagrams, TradingView widgets
"""

ACADEMY_CURRICULUM = [
    {
        "level_name": "Beginner",
        "description": "Master the basics of Forex trading from scratch. Learn what moves the market, how to read charts, and the fundamental mathematics of position sizing and risk management.",
        "modules": [
            {
                "title": "Introduction to Forex Trading",
                "description": "What Forex is, who trades it, and why the market moves.",
                "lessons": [
                    {
                        "title": "What is Forex Trading?",
                        "content": """## Simple Definition
Forex (Foreign Exchange) is the global marketplace where currencies are traded. It is the largest financial market in the world with over $7.5 trillion traded daily.

## Concept Explanation
Unlike stock markets that have centralized exchanges, Forex is decentralized. It operates 24 hours a day, 5 days a week, across major financial centers: Sydney, Tokyo, London, and New York.

## Step-by-Step Breakdown
1. **Currency Pairs**: Forex trades in pairs (EUR/USD). The first currency is the "base," the second is the "quote."
2. **Price Movement**: If EUR/USD moves from 1.0850 to 1.0860, the Euro strengthened against the Dollar by 10 pips.
3. **Profit Mechanism**: Buy low, sell high (or sell high, buy low for short positions).

## Real Trading Example
**Scenario**: You analyze EUR/USD and expect the Euro to strengthen.
- **Entry**: Buy at 1.0850
- **Position Size**: 0.1 lots ($1 per pip)
- **Stop Loss**: 1.0830 (20 pips risk = $20)
- **Take Profit**: 1.0890 (40 pips reward = $40)
- **Risk:Reward Ratio**: 1:2

<div class="ac-tradingview-widget" data-symbol="FX:EURUSD"></div>

## Common Beginner Mistake
**Overtrading**: New traders think more trades = more profit. Reality: Quality over quantity.

## Key Takeaway
Forex trading is about probability and risk management, not prediction.

## Practice Question
If EUR/USD rises from 1.0500 to 1.0550, how many pips did it move?""",
                        "quiz": [
                            {"question": "What does EUR/USD represent?", "option_a": "Euros per US Dollar", "option_b": "US Dollars per Euro", "option_c": "Exchange rate index", "option_d": "Stock price", "correct_answer": "B", "explanation": "EUR/USD shows how many USD one Euro buys.", "topic_slug": "forex_basics"},
                            {"question": "What is a pip in most currency pairs?", "option_a": "0.01", "option_b": "0.001", "option_c": "0.0001", "option_d": "1.0", "correct_answer": "C", "explanation": "For most pairs, 1 pip = 0.0001 (4th decimal).", "topic_slug": "forex_basics"},
                            {"question": "Calculate: EUR/USD moves from 1.0500 to 1.0550. How many pips?", "option_a": "5 pips", "option_b": "50 pips", "option_c": "500 pips", "option_d": "0.5 pips", "correct_answer": "B", "explanation": "1.0550 - 1.0500 = 0.0050 = 50 pips.", "topic_slug": "forex_basics"},
                            {"question": "Scenario: You buy EUR/USD at 1.0850. Price drops to 1.0800 with 0.1 lots. Loss?", "option_a": "$5", "option_b": "$50", "option_c": "$500", "option_d": "$5,000", "correct_answer": "B", "explanation": "50 pips × $1/pip = $50 loss.", "topic_slug": "forex_basics"},
                            {"question": "Mistake: Using 1:500 leverage on first trade. Risk?", "option_a": "Lower risk", "option_b": "Normal risk", "option_c": "Extreme risk of quick loss", "option_d": "Guaranteed profit", "correct_answer": "C", "explanation": "High leverage amplifies losses significantly.", "topic_slug": "forex_basics"}
                        ]
                    },
                    {
                        "title": "Who Trades Forex and Why?",
                        "content": """## Simple Definition
Forex participants range from central banks to individual retail traders, each with different goals and market impact.

## Concept Explanation
**Market Hierarchy**:
1. **Tier 1**: Central Banks and Major Commercial Banks — 50%+ of volume
2. **Tier 2**: Hedge Funds, Corporations — 40% of volume
3. **Tier 3**: Retail Traders — less than 10% of volume

## Step-by-Step Breakdown
1. **Central Banks**: Control monetary policy, creating the biggest moves.
2. **Commercial Banks**: Facilitate international transactions.
3. **Corporations**: Convert foreign earnings back to home currency.
4. **Retail Traders**: Speculate on price movements for profit.

## Real Trading Example
**The SNB Shock (2015)**: Swiss National Bank removed the EUR/CHF peg. The franc surged 30% in minutes. Retail traders with stops below 1.20 were wiped out.

<svg class="ac-svg-diagram" viewBox="0 0 400 200">
  <rect x="50" y="20" width="300" height="40" fill="rgba(245,158,11,0.2)" stroke="#f59e0b" rx="5"/>
  <text x="200" y="45" text-anchor="middle" fill="#f59e0b" font-size="14">Central Banks (Biggest Impact)</text>
  <line x1="200" y1="60" x2="200" y2="80" stroke="#60a5fa" stroke-width="2"/>
  <rect x="50" y="80" width="300" height="40" fill="rgba(96,165,250,0.2)" stroke="#60a5fa" rx="5"/>
  <text x="200" y="105" text-anchor="middle" fill="#60a5fa" font-size="14">Banks & Institutions</text>
  <line x1="200" y1="120" x2="200" y2="140" stroke="#60a5fa" stroke-width="2"/>
  <rect x="50" y="140" width="300" height="40" fill="rgba(167,139,250,0.2)" stroke="#a78bfa" rx="5"/>
  <text x="200" y="165" text-anchor="middle" fill="#a78bfa" font-size="14">Retail Traders (You)</text>
</svg>

## Common Beginner Mistake
**Fighting the Banks**: Retail traders try to catch falling knives against major bank flows. Trade WITH institutional flow, not against it.

## Key Takeaway
Understand you're a small fish in a big ocean. Your advantage is agility, not size.

## Practice Question
Which market participant creates the largest price movements?""",
                        "quiz": [
                            {"question": "Which participant moves markets most?", "option_a": "Retail traders", "option_b": "Central banks", "option_c": "Your broker", "option_d": "Influencers", "correct_answer": "B", "explanation": "Central banks control interest rates, creating largest moves.", "topic_slug": "market_participants"},
                            {"question": "Why do corporations trade forex?", "option_a": "To speculate", "option_b": "To convert foreign earnings", "option_c": "To manipulate prices", "option_d": "For entertainment", "correct_answer": "B", "explanation": "Corporations convert foreign revenue to home currency.", "topic_slug": "market_participants"},
                            {"question": "Retail trader volume percentage?", "option_a": "50%", "option_b": "25%", "option_c": "10%", "option_d": "Less than 10%", "correct_answer": "D", "explanation": "Retail traders are <10% of $7.5 trillion daily volume.", "topic_slug": "market_participants"},
                            {"question": "Scenario: Deutsche Bank sells $2B EUR/USD. You buy 1 micro lot. Effect?", "option_a": "You reverse the trend", "option_b": "Price ignores your trade", "option_c": "You profit immediately", "option_d": "Bank follows you", "correct_answer": "B", "explanation": "Institutional volume dwarfs retail. Your trade doesn't impact price.", "topic_slug": "market_participants"},
                            {"question": "Mistake: Fighting central bank intervention. Result?", "option_a": "Profit", "option_b": "Losses", "option_c": "Neutral", "option_d": "Guaranteed win", "correct_answer": "B", "explanation": "Never fight central banks. Trade with their flow or stay out.", "topic_slug": "market_participants"}
                        ]
                    }
                ]
            },
            {
                "title": "Currency Pairs and Price Quotes",
                "description": "Majors, minors, exotics, pips, and spreads.",
                "lessons": [
                    {
                        "title": "Major, Minor and Exotic Pairs",
                        "content": """## Simple Definition
Currency pairs are categorized by liquidity: Majors (most traded), Minors (crosses), and Exotics (emerging markets).

## Concept Explanation
**Major Pairs** (All include USD):
- EUR/USD: 28% of daily volume, tightest spreads
- USD/JPY: 13%, "safe haven"
- GBP/USD: 11%, volatile
- USD/CHF, USD/CAD, AUD/USD, NZD/USD

**Minor Pairs**: EUR/GBP, EUR/JPY, GBP/JPY — wider spreads, still liquid.
**Exotics**: USD/ZAR, USD/TRY — huge spreads, dangerous for beginners.

## Step-by-Step Breakdown
1. **Spread Costs**: EUR/USD spread = 0.1-0.3 pips. USD/TRY = 50-200 pips.
2. **Volatility**: GBP/JPY moves 100+ pips daily. EUR/CHF moves 30 pips.
3. **Correlation**: EUR/USD and GBP/USD move together ~90% of time.

## Real Trading Example
**Beginner Account**: $1,000
- **Bad**: USD/ZAR with 50-pip spread = $50 cost (5% of account)
- **Good**: EUR/USD with 0.2-pip spread = $0.20 cost

<div class="ac-tradingview-widget" data-symbol="FX:EURUSD"></div>

## Common Beginner Mistake
**Trading Exotics for "Excitement"**: Beginners see USD/TRY moving 500 pips but ignore 200-pip spread and $20/night swap fees.

## Key Takeaway
Start with EUR/USD only. Master one pair before adding others.

## Practice Question
Which pair is generally best for beginners and why?""",
                        "quiz": [
                            {"question": "Which is a major pair?", "option_a": "EUR/GBP", "option_b": "EUR/USD", "option_c": "USD/ZAR", "option_d": "GBP/JPY", "correct_answer": "B", "explanation": "Majors always include USD. EUR/USD is most traded.", "topic_slug": "currency_pairs"},
                            {"question": "Which has widest spreads?", "option_a": "Majors", "option_b": "Minors", "option_c": "Exotics", "option_d": "All equal", "correct_answer": "C", "explanation": "Exotics like USD/TRY have 50-200 pip spreads.", "topic_slug": "currency_pairs"},
                            {"question": "Calculate: 0.1 lots USD/ZAR with 50-pip spread. Cost?", "option_a": "$0.50", "option_b": "$5", "option_c": "$50", "option_d": "$500", "correct_answer": "C", "explanation": "0.1 lots = $1/pip. 50 pips × $1 = $50.", "topic_slug": "currency_pairs"},
                            {"question": "EUR/USD and GBP/USD correlation?", "option_a": "Opposite", "option_b": "90% same direction", "option_c": "No correlation", "option_d": "Random", "correct_answer": "B", "explanation": "Both move with USD direction, highly correlated.", "topic_slug": "currency_pairs"},
                            {"question": "Mistake: Trading exotics as beginner. Cost?", "option_a": "No cost", "option_b": "High spreads and swap fees", "option_c": "Lower volatility", "option_d": "Better liquidity", "correct_answer": "B", "explanation": "Exotics have massive spreads and overnight fees.", "topic_slug": "currency_pairs"}
                        ]
                    },
                    {
                        "title": "Reading Pips and Spreads",
                        "content": """## Simple Definition
A "pip" is the smallest price move. For most pairs, it's 0.0001. The "spread" is the difference between buy (ask) and sell (bid) prices.

## Concept Explanation
**Pip Values**:
- Most pairs: 0.0001 = 1 pip
- JPY pairs: 0.01 = 1 pip

**Lot Sizes**:
- Standard (1.0): $10/pip
- Mini (0.1): $1/pip
- Micro (0.01): $0.10/pip

## Step-by-Step Breakdown
1. **Calculate Trade Value**: 0.5 lots EUR/USD at 1.0850 = $54,250 exposure
2. **Pip Value**: 0.5 lots = $5 per pip
3. **Spread Cost**: 2-pip spread × $5 = $10 entry cost

## Real Trading Example
**Account**: $5,000, 2% risk = $100
- **Setup**: EUR/USD buy at 1.0850, stop at 1.0830 (20 pips)
- **Calculation**: $100 ÷ 20 pips = $5/pip needed = 0.5 lots

<svg class="ac-svg-diagram" viewBox="0 0 400 120">
  <rect x="20" y="30" width="150" height="40" fill="rgba(239,68,68,0.2)" stroke="#ef4444" rx="5"/>
  <text x="95" y="55" text-anchor="middle" fill="#ef4444" font-size="12">Bid: 1.08498</text>
  <line x1="170" y1="50" x2="230" y2="50" stroke="#f59e0b" stroke-width="2"/>
  <text x="200" y="45" text-anchor="middle" fill="#f59e0b" font-size="12">2 pips</text>
  <rect x="230" y="30" width="150" height="40" fill="rgba(34,197,94,0.2)" stroke="#22c55e" rx="5"/>
  <text x="305" y="55" text-anchor="middle" fill="#22c55e" font-size="12">Ask: 1.08502</text>
</svg>

## Common Beginner Mistake
**Ignoring Spread in Stop Loss**: You set 10-pip stop, spread is 3 pips. Actual stop is 7 pips away—30% risk increase.

## Key Takeaway
Pips measure movement. Spreads measure cost. Calculate both before trading.

## Practice Question
If you trade 0.3 lots with 1.5-pip spread, what is entry cost?""",
                        "quiz": [
                            {"question": "1 pip on EUR/USD standard lot?", "option_a": "$0.10", "option_b": "$1", "option_c": "$10", "option_d": "$100", "correct_answer": "C", "explanation": "1 standard lot = 100,000 units. 1 pip = $10.", "topic_slug": "pips_lots"},
                            {"question": "What is the spread?", "option_a": "Trend direction", "option_b": "Difference between bid and ask", "option_c": "Commission fee", "option_d": "Swap rate", "correct_answer": "B", "explanation": "Spread is buy price minus sell price—your entry cost.", "topic_slug": "pips_lots"},
                            {"question": "Calculate: 0.3 lots, 1.5-pip spread. Cost?", "option_a": "$0.45", "option_b": "$4.50", "option_c": "$45", "option_d": "$450", "correct_answer": "B", "explanation": "0.3 lots = $3/pip. 1.5 × $3 = $4.50.", "topic_slug": "pips_lots"},
                            {"question": "You set 15-pip stop, spread is 2 pips. Actual risk?", "option_a": "15 pips", "option_b": "17 pips", "option_c": "13 pips", "option_d": "30 pips", "correct_answer": "C", "explanation": "Price must move spread + stop. 15 - 2 = 13 pips actual.", "topic_slug": "pips_lots"},
                            {"question": "Mistake: Maximum leverage without pip calculation. Risk?", "option_a": "Lower risk", "option_b": "Cannot size positions correctly", "option_c": "Guaranteed profits", "option_d": "No effect", "correct_answer": "B", "explanation": "Without pip value, you cannot calculate proper position size.", "topic_slug": "pips_lots"}
                        ]
                    }
                ]
            },
            {
                "title": "Trading Sessions and Market Timing",
                "description": "When markets are most active.",
                "lessons": [
                    {
                        "title": "Trading Sessions Explained",
                        "content": """## Simple Definition
The Forex market operates 24/5, divided into three sessions: Asian, London, and New York. Each has unique characteristics.

## Concept Explanation
**Asian Session (Tokyo)**: 00:00–09:00 UTC
- Lower volatility, range-bound
- JPY pairs most active
- Best for: Range trading

**London Session**: 08:00–17:00 UTC
- Highest liquidity
- EUR, GBP, CHF active
- Best for: Trend following

**New York Session**: 13:00–22:00 UTC
- USD pairs volatile
- Overlap with London (13:00–17:00) = Golden Hours

## Step-by-Step Breakdown
1. **Identify Your Session**: Trade when you're sharp and market is active.
2. **Golden Window**: 13:00–17:00 UTC = 70% of daily volume.
3. **Avoid**: Friday evenings, Sunday opens, holidays.

## Real Trading Example
**London Breakout Strategy**:
- Wait for Asian range formation (20:00–08:00 UTC)
- Place buy stop above range high, sell stop below
- London open (08:00 UTC) triggers breakout

<svg class="ac-svg-diagram" viewBox="0 0 600 150">
  <rect x="20" y="50" width="160" height="50" fill="rgba(251,191,36,0.2)" stroke="#fbbf24" rx="5"/>
  <text x="100" y="78" text-anchor="middle" fill="#fbbf24" font-size="12">Asian (00-09 UTC)</text>
  <rect x="200" y="50" width="180" height="50" fill="rgba(96,165,250,0.3)" stroke="#60a5fa" rx="5"/>
  <text x="290" y="78" text-anchor="middle" fill="#60a5fa" font-size="12">London (08-17 UTC)</text>
  <rect x="340" y="50" width="180" height="50" fill="rgba(52,211,153,0.3)" stroke="#34d399" rx="5"/>
  <text x="430" y="78" text-anchor="middle" fill="#34d399" font-size="12">New York (13-22 UTC)</text>
  <rect x="380" y="30" width="140" height="15" fill="rgba(167,139,250,0.5)" rx="3"/>
  <text x="450" y="42" text-anchor="middle" fill="#fff" font-size="10">GOLDEN OVERLAP</text>
</svg>

## Common Beginner Mistake
**Trading Asian Session**: Beginners trade at midnight wondering why nothing moves. Trade during high-liquidity hours only.

## Key Takeaway
Quality trading happens during specific hours. The London-NY overlap offers best opportunities.

## Practice Question
When does highest liquidity occur?""",
                        "quiz": [
                            {"question": "Three major sessions?", "option_a": "Morning, Afternoon, Evening", "option_b": "Asian, London, New York", "option_c": "Open, High, Close", "option_d": "Bull, Bear, Sideways", "correct_answer": "B", "explanation": "Three major sessions: Asian (Tokyo), London, New York.", "topic_slug": "sessions"},
                            {"question": "Which pairs active during Asian?", "option_a": "EUR/USD", "option_b": "USD/CAD", "option_c": "JPY pairs", "option_d": "GBP pairs", "correct_answer": "C", "explanation": "JPY pairs most active during Tokyo hours.", "topic_slug": "sessions"},
                            {"question": "London-New York overlap (UTC)?", "option_a": "08:00-12:00", "option_b": "13:00-17:00", "option_c": "20:00-00:00", "option_d": "00:00-04:00", "correct_answer": "B", "explanation": "13:00-17:00 UTC = highest liquidity period.", "topic_slug": "sessions"},
                            {"question": "Trading GBP/USD at 03:00 UTC?", "option_a": "High volatility", "option_b": "Tight spreads", "option_c": "Low liquidity, whipsaws", "option_d": "Major breakouts", "correct_answer": "C", "explanation": "03:00 UTC is deep Asian session—low liquidity for GBP.", "topic_slug": "sessions"},
                            {"question": "Sunday evening trading risk?", "option_a": "Guaranteed trends", "option_b": "Gaps from weekend news", "option_c": "Low spreads", "option_d": "High liquidity", "correct_answer": "B", "explanation": "Sunday opens have gaps from weekend events.", "topic_slug": "sessions"}
                        ]
                    },
                    {
                        "title": "Best Times to Trade",
                        "content": """## Simple Definition
Not all hours are profitable. The "Golden Window" offers the best combination of liquidity, volatility, and patterns.

## Concept Explanation
**The Golden Window**: 13:00–17:00 UTC
- 70% of daily volume
- Tightest spreads
- Most directional moves

**Avoid**:
- Friday after 18:00 UTC (weekend gap risk)
- Sunday 21:00–23:00 UTC (erratic)
- Major news releases (unless news trader)

## Step-by-Step Breakdown
1. **Pre-Market**: Check economic calendar, mark key levels
2. **Golden Window**: Execute high-probability setups
3. **Afternoon**: Manage existing positions only
4. **Evening**: Journal trades

## Real Trading Example
**2-Hour Trader Schedule**:
- 12:30 UTC: Analyze charts
- 13:00 UTC: Wait for setup
- 14:30 UTC: Enter valid setup
- 16:00 UTC: Close positions

## Common Beginner Mistake
**All-Day Trading**: 8+ hours leads to fatigue, revenge trading, and losses during choppy sessions.

## Key Takeaway
Quality over quantity. Trading 2 hours during Golden Window beats 8 random hours.

## Practice Question
Why avoid holding trades over weekend?""",
                        "quiz": [
                            {"question": "The 'Golden Window'?", "option_a": "Any profitable time", "option_b": "London-NY overlap 13:00-17:00 UTC", "option_c": "Weekend trading", "option_d": "Holidays", "correct_answer": "B", "explanation": "13:00-17:00 UTC offers best liquidity and moves.", "topic_slug": "sessions"},
                            {"question": "Avoid trading when?", "option_a": "Tuesday 14:00 UTC", "option_b": "Friday evening", "option_c": "Thursday 10:00 UTC", "option_d": "Wednesday overlap", "correct_answer": "B", "explanation": "Friday evening has low liquidity and weekend gap risk.", "topic_slug": "sessions"},
                            {"question": "Cost difference: Friday 21:00 (5-pip spread) vs Wednesday 14:00 (0.5-pip), 1 lot?", "option_a": "$5", "option_b": "$45", "option_c": "$50", "option_d": "$500", "correct_answer": "B", "explanation": "4.5 pip difference × $10 = $45 extra cost.", "topic_slug": "sessions"},
                            {"question": "Perfect setup at 22:00 UTC Sunday?", "option_a": "Enter immediately", "option_b": "Wait for Monday liquidity", "option_c": "Increase size", "option_d": "Market order", "correct_answer": "B", "explanation": "Sunday 22:00 has gap risk. Wait for Monday.", "topic_slug": "sessions"},
                            {"question": "8 hours straight trading consequence?", "option_a": "More profit", "option_b": "Fatigue and overtrading", "option_c": "Better focus", "option_d": "Guaranteed success", "correct_answer": "B", "explanation": "Long sessions cause fatigue and poor decisions.", "topic_slug": "sessions"}
                        ]
                    }
                ]
            },
            {
                "title": "Pips, Lots, and Leverage",
                "description": "Position sizing and leverage explained.",
                "lessons": [
                    {
                        "title": "Understanding Leverage",
                        "content": """## Simple Definition
Leverage allows controlling large positions with small capital. Expressed as ratio (1:100), meaning $1,000 controls $100,000.

## Concept Explanation
**How It Works**:
- 1:100 leverage: $1,000 margin controls $100,000 position
- 1:50 leverage: $1,000 controls $50,000

**Double-Edged Sword**:
- 1% move with 1:100 leverage = 100% gain or loss on margin

## Step-by-Step Breakdown
1. **Calculate Margin**: Position Size ÷ Leverage = Margin Required
2. **Margin Call**: Equity drops below required margin = positions closed
3. **Free Margin**: Keep >50% to avoid margin calls

## Real Trading Example
**Account**: $5,000 with 1:100 leverage
- **Trade**: Buy 0.5 lots ($50k position)
- **Margin Used**: $500
- **Free Margin**: $4,500 buffer

<svg class="ac-svg-diagram" viewBox="0 0 400 150">
  <rect x="20" y="60" width="80" height="40" fill="rgba(245,158,11,0.3)" stroke="#f59e0b" rx="5"/>
  <text x="60" y="85" text-anchor="middle" fill="#f59e0b" font-size="12">$1,000</text>
  <line x1="100" y1="80" x2="140" y2="80" stroke="#60a5fa" stroke-width="2"/>
  <text x="120" y="70" text-anchor="middle" fill="#60a5fa" font-size="10">1:100</text>
  <rect x="140" y="40" width="240" height="80" fill="rgba(34,197,94,0.2)" stroke="#22c55e" rx="5"/>
  <text x="260" y="80" text-anchor="middle" fill="#22c55e" font-size="16">$100,000 Position</text>
  <text x="200" y="130" text-anchor="middle" fill="#ef4444" font-size="12">1% move = ±$1,000</text>
</svg>

## Common Beginner Mistake
**Maximum Leverage**: Using 1:500 with $1,000 account. A 20-pip move wipes out the account.

## Key Takeaway
Use 1:10 to 1:30 leverage. Never risk >2% per trade regardless of available leverage.

## Practice Question
With 1:200 leverage and $2,000 account, maximum theoretical position size?""",
                        "quiz": [
                            {"question": "1:100 leverage, $1,000 controls?", "option_a": "$1,000", "option_b": "$10,000", "option_c": "$100,000", "option_d": "$1,000,000", "correct_answer": "C", "explanation": "$1,000 × 100 = $100,000 position size.", "topic_slug": "leverage"},
                            {"question": "What happens to losses with leverage?", "option_a": "Decrease", "option_b": "Stay same", "option_c": "Amplify equally with gains", "option_d": "Disappear", "correct_answer": "C", "explanation": "Leverage amplifies both gains AND losses equally.", "topic_slug": "leverage"},
                            {"question": "Calculate: $10,000 account, 1:50 leverage. Position size?", "option_a": "$5,000", "option_b": "$50,000", "option_c": "$500,000", "option_d": "$20,000", "correct_answer": "C", "explanation": "$10,000 × 50 = $500,000 maximum position.", "topic_slug": "leverage"},
                            {"question": "1:500 leverage, $1,000 account, 1 lot. Pips to margin call?", "option_a": "1,000", "option_b": "100", "option_c": "~20", "option_d": "200", "correct_answer": "C", "explanation": "High leverage means small moves trigger margin calls.", "topic_slug": "leverage"},
                            {"question": "Mistake: Using maximum broker leverage. Why dangerous?", "option_a": "Higher profits", "option_b": "Small moves cause large losses", "option_c": "Lower spreads", "option_d": "Better execution", "correct_answer": "B", "explanation": "Small adverse moves can wipe out entire account.", "topic_slug": "leverage"}
                        ]
                    },
                    {
                        "title": "Position Sizing Calculation",
                        "content": """## Simple Definition
Position sizing determines lot size based on account size, risk percentage, and stop loss distance.

## Concept Explanation
**Formula**: Position Size = Account Risk ($) ÷ (Stop Loss (pips) × Pip Value ($))

**Variables**:
- Account Risk: 1-2% of balance
- Stop Loss: Technical invalidation point
- Pip Value: $10/standard lot

## Step-by-Step Breakdown
**Example**: $10,000 account, 2% risk, 50-pip stop
1. Risk Amount: $10,000 × 2% = $200
2. Pip Value Needed: $200 ÷ 50 = $4/pip
3. Lot Size: $4 ÷ $10 = 0.4 lots

## Real Trading Example
**Account**: $3,000, 1% risk ($30), 30-pip stop
- $30 ÷ 30 pips = $1/pip needed
- $1/pip = 0.1 lots (1 mini lot)

## Common Beginner Mistake
**Fixed Lot Sizes**: Trading 1.0 lot every trade regardless of account or stop distance leads to random risk (0.5% to 20% per trade).

## Key Takeaway
Position sizing is the only "holy grail." Calculate size before entering; never adjust stop to fit desired size.

## Practice Question
$5,000 account, 2% risk, 25-pip stop. What lot size?""",
                        "quiz": [
                            {"question": "Position sizing formula?", "option_a": "Account × leverage", "option_b": "Risk ÷ (stop × pip value)", "option_c": "Maximum lots", "option_d": "Random", "correct_answer": "B", "explanation": "Size = Account Risk ($) ÷ (Stop (pips) × Pip Value ($)).", "topic_slug": "position_sizing"},
                            {"question": "$10,000 account, 2% risk. Risk amount?", "option_a": "$20", "option_b": "$200", "option_c": "$2,000", "option_d": "$200,000", "correct_answer": "B", "explanation": "$10,000 × 2% = $200 maximum risk.", "topic_slug": "position_sizing"},
                            {"question": "Calculate: $5,000, 1% risk, 40-pip stop. Pip value?", "option_a": "$1.25", "option_b": "$12.50", "option_c": "$125", "option_d": "$1,250", "correct_answer": "A", "explanation": "$5,000 × 1% = $50. $50 ÷ 40 = $1.25/pip.", "topic_slug": "position_sizing"},
                            {"question": "Need $2/pip. Lot size?", "option_a": "0.02 lots", "option_b": "0.2 lots", "option_c": "2.0 lots", "option_d": "20 lots", "correct_answer": "B", "explanation": "0.2 lots = $2/pip (0.2 × $10).", "topic_slug": "position_sizing"},
                            {"question": "Mistake: Fixed 0.5 lots every trade. Result?", "option_a": "Consistent risk", "option_b": "Variable risk, potential blowup", "option_c": "Guaranteed profits", "option_d": "Lower spreads", "correct_answer": "B", "explanation": "Fixed lots = variable dollar risk on different stop distances.", "topic_slug": "position_sizing"}
                        ]
                    }
                ]
            },
            {
                "title": "Basic Risk Management",
                "description": "Stop loss, take profit, and the 1-2% rule.",
                "lessons": [
                    {
                        "title": "The 1-2% Rule",
                        "content": """## Simple Definition
Never risk more than 1-2% of total account equity on any single trade. This ensures survival through losing streaks.

## Concept Explanation
**Survival Math**:
- 2% risk: 50 losses to blow account (statistically impossible with edge)
- 5% risk: 20 losses to blow account (happens every few months)
- 10% risk: 10 losses to blow account (happens weekly to beginners)

## Step-by-Step Breakdown
1. Calculate 2%: Balance × 0.02 = Max Risk ($)
2. Determine Stop Distance: Technical level minus entry
3. Size Accordingly: (Pips × Pip Value) ≤ Max Risk
4. Hard Stop: Set immediately upon entry

## Real Trading Example
**Month 1**: $10,000, 2% risk ($200/trade)
- Week 1: 5 wins, 3 losses = +$400
- Week 2: 4 wins, 4 losses = $0
- Week 3: 3 wins, 5 losses = -$400
- **Net**: Break even despite losing more trades

**Month 2**: Same trader, 10% risk ($1,000/trade)
- Week 1: 3 losses = -$3,000 (30% drawdown, quits)

<svg class="ac-svg-diagram" viewBox="0 0 500 120">
  <rect x="20" y="30" width="460" height="40" fill="rgba(34,197,94,0.2)" stroke="#22c55e" rx="5"/>
  <rect x="20" y="30" width="46" height="40" fill="#22c55e" opacity="0.6"/>
  <text x="43" y="55" fill="white" font-size="12" font-weight="bold">2%</text>
  <text x="100" y="90" fill="#9ca3af" font-size="10">50 losses to ruin</text>
  
  <rect x="20" y="30" width="230" height="40" fill="rgba(245,158,11,0.3)" stroke="#f59e0b" opacity="0.5"/>
  <text x="140" y="55" fill="white" font-size="12" font-weight="bold">5%</text>
  <text x="200" y="90" fill="#9ca3af" font-size="10">20 losses</text>
  
  <rect x="20" y="30" width="460" height="40" fill="rgba(239,68,68,0.2)" stroke="#ef4444" opacity="0.3"/>
  <text x="350" y="55" fill="white" font-size="12" font-weight="bold">10%</text>
  <text x="400" y="90" fill="#9ca3af" font-size="10">10 losses</text>
</svg>

## Common Beginner Mistake
**"I only have $500, so I need 20% risk"**: This guarantees failure. Small accounts should trade micro lots with 1% risk, building consistency before sizing up.

## Key Takeaway
The 1-2% rule is survival. You must survive losing streaks to reach winning streaks. Capital preservation is priority #1.

## Practice Question
$5,000 account, 2% risk. Maximum dollar risk per trade?""",
                        "quiz": [
                            {"question": "Maximum recommended risk per trade?", "option_a": "10%", "option_b": "5%", "option_c": "1-2%", "option_d": "25%", "correct_answer": "C", "explanation": "Never risk more than 1-2% per trade to survive streaks.", "topic_slug": "risk_management"},
                            {"question": "With 2% risk, losses to blow account?", "option_a": "10", "option_b": "20", "option_c": "50", "option_d": "5", "correct_answer": "C", "explanation": "2% × 50 = 100%. Requires 50 consecutive losses.", "topic_slug": "risk_management"},
                            {"question": "Calculate: $5,000 account, 2% risk. Max loss?", "option_a": "$10", "option_b": "$100", "option_c": "$1,000", "option_d": "$10,000", "correct_answer": "B", "explanation": "$5,000 × 2% = $100 maximum risk per trade.", "topic_slug": "risk_management"},
                            {"question": "3 losses in a row. Action?", "option_a": "Increase size to recover", "option_b": "Stop trading for the day", "option_c": "Trade different pair", "option_d": "Remove stops", "correct_answer": "B", "explanation": "After 3 losses, stop. You're likely emotional.", "topic_slug": "risk_management"},
                            {"question": "Risking 10% to 'make back' losses. Result?", "option_a": "Faster recovery", "option_b": "Revenge trading spiral", "option_c": "Guaranteed success", "option_d": "Lower stress", "correct_answer": "B", "explanation": "Increasing risk after losses leads to blowup.", "topic_slug": "risk_management"}
                        ]
                    },
                    {
                        "title": "Stop Loss and Take Profit",
                        "content": """## Simple Definition
Every trade must have predetermined exit points: Stop Loss (max loss accepted) and Take Profit (target where reward justifies risk).

## Concept Explanation
**Stop Loss (SL)**:
- Long trades: SL below support
- Short trades: SL above resistance
- Volatility buffer: Add 1-2x ATR to avoid noise

**Take Profit (TP)**:
- Minimum 1:2 Risk:Reward
- Previous swing highs/lows
- Trail stops: Move SL to breakeven at 1R

## Step-by-Step Breakdown
**Trade Setup**: EUR/USD Long
1. Entry: 1.0850 (break of resistance)
2. Stop: 1.0830 (below support, 20 pips)
3. Take Profit: 1.0890 (next resistance, 40 pips)
4. Risk: $200 (2% of $10k)
5. Reward: $400
6. R:R: 1:2 (minimum acceptable)

## Real Trading Example
**Perfect Setup**:
- EUR/USD bounces off 1.0850 support (3rd touch)
- Bullish engulfing confirms
- Entry: 1.0852
- SL: 1.0840 (12 pips)
- TP: 1.0872 (20 pips)
- Position: 0.16 lots ($1.60/pip × 12 = $192 risk)
- Result: 1.67 R:R, target hit in 4 hours

<svg class="ac-svg-diagram" viewBox="0 0 400 150">
  <line x1="50" y1="100" x2="350" y2="100" stroke="#9ca3af" stroke-width="1"/>
  <text x="200" y="115" text-anchor="middle" fill="#9ca3af" font-size="10">Support/Resistance</text>
  <circle cx="100" cy="100" r="5" fill="#ef4444"/>
  <text x="100" y="130" text-anchor="middle" fill="#ef4444" font-size="12">SL: 1.0830</text>
  <circle cx="200" cy="80" r="5" fill="#60a5fa"/>
  <text x="200" y="70" text-anchor="middle" fill="#60a5fa" font-size="12">Entry: 1.0850</text>
  <circle cx="300" cy="60" r="5" fill="#22c55e"/>
  <text x="300" y="50" text-anchor="middle" fill="#22c55e" font-size="12">TP: 1.0870</text>
  <line x1="200" y1="80" x2="300" y2="60" stroke="#22c55e" stroke-width="2" stroke-dasharray="5,5"/>
</svg>

## Common Beginner Mistake
**Moving Stop Losses**: Price approaches SL, trader moves it "just a bit lower" to avoid loss. Turns planned $100 loss into unplanned $300 loss.

## Key Takeaway
Set SL and TP before clicking buy/sell. Once entered, only move SL in direction of profit (trailing), never against it.

## Practice Question
You enter EUR/USD at 1.1000, SL at 1.0980, TP at 1.1040. Risk:Reward ratio?""",
                        "quiz": [
                            {"question": "Where is SL for BUY trade?", "option_a": "Above resistance", "option_b": "Below support", "option_c": "At entry", "option_d": "Random", "correct_answer": "B", "explanation": "Buy stops go below support to invalidate the trade idea.", "topic_slug": "risk_management"},
                            {"question": "Minimum recommended R:R ratio?", "option_a": "1:1", "option_b": "1:2", "option_c": "1:0.5", "option_d": "2:1", "correct_answer": "B", "explanation": "Minimum 1:2 R:R. Allows 40% win rate to be profitable.", "topic_slug": "risk_management"},
                            {"question": "Calculate: Entry 1.1000, SL 1.0980, TP 1.1040. R:R?", "option_a": "1:1", "option_b": "1:2", "option_c": "2:1", "option_d": "4:1", "correct_answer": "B", "explanation": "20 pip risk, 40 pip reward = 1:2 ratio.", "topic_slug": "risk_management"},
                            {"question": "Price nears SL. You move it 10 pips lower. Result?", "option_a": "Saved trade", "option_b": "Usually larger loss", "option_c": "Guaranteed reversal", "option_d": "No effect", "correct_answer": "B", "explanation": "Moving stops to avoid loss usually creates larger losses.", "topic_slug": "risk_management"},
                            {"question": "Trade without stop loss. Danger?", "option_a": "Unlimited downside", "option_b": "Lower spreads", "option_c": "Better fills", "option_d": "More time to decide", "correct_answer": "A", "explanation": "No SL = potential unlimited loss. One event wipes account.", "topic_slug": "risk_management"}
                        ]
                    }
                ]
            },
            {
                "title": "Introduction to Trading Charts",
                "description": "Candlestick charts and support/resistance basics.",
                "lessons": [
                    {
                        "title": "Candlestick Charts Explained",
                        "content": """## Simple Definition
Candlestick charts display price using "candles" showing open, high, low, close (OHLC) for specific periods. Each candle tells who won—buyers or sellers.

## Concept Explanation
**Candle Anatomy**:
- **Body**: Area between open and close
  - Green: Close > Open (Bullish)
  - Red: Close < Open (Bearish)
- **Wicks**: Lines showing high and low
  - Upper Wick: High reached
  - Lower Wick: Low reached

**Timeframes**:
- M1, M5, M15: Scalping
- H1, H4: Day trading
- D1, W1: Position trading

## Step-by-Step Breakdown
**Reading a Candle**:
1. **Body size**: Large = strong conviction. Small = indecision.
2. **Wick length**: Long upper wick = rejection of higher prices.
3. **Color sequence**: Green after red = potential reversal.
4. **Context**: Single candle means nothing. Three candles = pattern.

## Real Trading Example
**The Hammer Pattern** (Bullish Reversal):
- **Appearance**: Small body at top, long lower wick (2-3x body)
- **Location**: Bottom of downtrend
- **Meaning**: Sellers pushed down, buyers regained control
- **Entry**: Buy above hammer high
- **Stop**: Below hammer low

<svg class="ac-svg-diagram" viewBox="0 0 200 300">
  <line x1="100" y1="50" x2="100" y2="250" stroke="#60a5fa" stroke-width="2"/>
  <rect x="85" y="80" width="30" height="20" fill="#22c55e" opacity="0.8"/>
  <line x1="100" y1="80" x2="100" y2="40" stroke="#22c55e" stroke-width="2"/>
  <text x="120" y="70" fill="#22c55e" font-size="10">Upper Wick</text>
  <line x1="100" y1="100" x2="100" y2="260" stroke="#22c55e" stroke-width="2"/>
  <text x="120" y="180" fill="#22c55e" font-size="10">Long Lower Wick</text>
</svg>

## Common Beginner Mistake
**Candlestick Trading Without Context**: "Perfect" bullish engulfing at top of 6-month uptrend against resistance. Beginners buy, get crushed by reversal.

## Key Takeaway
Candles show sentiment. Wicks show rejection. Bodies show conviction. Always read within context of trend and levels.

## Practice Question
What does long upper wick indicate?""",
                        "quiz": [
                            {"question": "Green candle indicates?", "option_a": "Closed lower than open", "option_b": "Closed higher than open", "option_c": "No movement", "option_d": "Market closed", "correct_answer": "B", "explanation": "Green = Close > Open (Bullish).", "topic_slug": "candlestick_patterns"},
                            {"question": "Long upper wick shows?", "option_a": "Strong buying", "option_b": "Rejection of higher prices", "option_c": "Closed high", "option_d": "Low volatility", "correct_answer": "B", "explanation": "Long upper wick = price rejected from higher levels.", "topic_slug": "candlestick_patterns"},
                            {"question": "Calculate: Open 1.1000, Close 1.1020, High 1.1030, Low 1.0990. Body size?", "option_a": "10 pips", "option_b": "20 pips", "option_c": "40 pips", "option_d": "30 pips", "correct_answer": "B", "explanation": "Body = Close - Open = 1.1020 - 1.1000 = 20 pips.", "topic_slug": "candlestick_patterns"},
                            {"question": "Bullish engulfing at all-time high resistance?", "option_a": "Buy immediately", "option_b": "Wait for breakout confirmation", "option_c": "Sell short", "option_d": "Increase leverage", "correct_answer": "B", "explanation": "Patterns at resistance need confirmation.", "topic_slug": "candlestick_patterns"},
                            {"question": "Trading single candle without trend context?", "option_a": "High win rate", "option_b": "False signals against trend", "option_c": "Better entries", "option_d": "Lower spreads", "correct_answer": "B", "explanation": "Single candles without context generate false signals.", "topic_slug": "candlestick_patterns"}
                        ]
                    },
                    {
                        "title": "Support and Resistance Basics",
                        "content": """## Simple Definition
**Support**: Price level where buying overcomes selling, causing bounces.
**Resistance**: Price level where selling overcomes buying, causing rejections.

## Concept Explanation
**Why These Levels Exist**:
- **Psychological**: Round numbers (1.1000, 1.2000)
- **Historical**: Previous highs/lows leave unfilled orders
- **Institutional**: Banks place large orders at specific prices

**Role Reversal**: Once support breaks, it often becomes resistance (and vice versa).

## Step-by-Step Breakdown
**Drawing Support**:
1. Find 2+ price lows at similar level
2. Connect lows with line
3. Extend into future
4. More touches = stronger support

## Real Trading Example
**Triple Top**:
- EUR/USD tests 1.1000 three times over 2 months
- Each test produces long upper wicks
- **Setup**: Short at 1.0990, SL at 1.1020, TP at 1.0850
- **Risk**: 30 pips. **Reward**: 140 pips. **R:R**: 1:4.7

<svg class="ac-svg-diagram" viewBox="0 0 400 150">
  <line x1="50" y1="100" x2="350" y2="100" stroke="#ef4444" stroke-width="2" stroke-dasharray="5,5"/>
  <text x="200" y="90" text-anchor="middle" fill="#ef4444" font-size="14">Resistance</text>
  <path d="M 80 100 Q 100 60 120 100" fill="none" stroke="#60a5fa" stroke-width="2"/>
  <path d="M 180 100 Q 200 50 220 100" fill="none" stroke="#60a5fa" stroke-width="2"/>
  <path d="M 280 100 Q 300 40 320 100" fill="none" stroke="#60a5fa" stroke-width="2"/>
  <text x="200" y="130" text-anchor="middle" fill="#fbbf24" font-size="12">Triple Top - Rejection Pattern</text>
</svg>

## Common Beginner Mistake
**Exact Price Levels**: Drawing lines at exact prices (1.0850) instead of zones (1.0840–1.0860). Markets are messy—use 10-20 pip zones.

## Key Takeaway
Support and resistance are zones, not lines. The more times tested, the weaker they become. Trade bounces at support, rejections at resistance.

## Practice Question
What happens to support once clearly broken?""",
                        "quiz": [
                            {"question": "Support represents?", "option_a": "Selling pressure", "option_b": "Buying overcoming selling", "option_c": "Market top", "option_d": "Random price", "correct_answer": "B", "explanation": "Support is where buyers step in and overcome selling.", "topic_slug": "support_resistance"},
                            {"question": "What is 'role reversal'?", "option_a": "Traders swapping", "option_b": "Broken resistance becomes support", "option_c": "Trend reversal", "option_d": "Price gaps", "correct_answer": "B", "explanation": "Once resistance breaks, it often becomes support on retests.", "topic_slug": "support_resistance"},
                            {"question": "Touches needed to validate level?", "option_a": "1", "option_b": "2 or more", "option_c": "10", "option_d": "None", "correct_answer": "B", "explanation": "Need at least 2 clear touches with reversals.", "topic_slug": "support_resistance"},
                            {"question": "Price breaks below support on high volume?", "option_a": "Buy the dip", "option_b": "Wait for retest as resistance", "option_c": "Hold longs", "option_d": "Remove stops", "correct_answer": "B", "explanation": "Wait for broken support to be retested as resistance.", "topic_slug": "support_resistance"},
                            {"question": "Drawing exact single-price lines vs zones?", "option_a": "Better precision", "option_b": "Missed entries or false breaks", "option_c": "Lower risk", "option_d": "Guaranteed fills", "correct_answer": "B", "explanation": "Exact lines cause missed trades. Use 10-20 pip zones.", "topic_slug": "support_resistance"}
                        ]
                    }
                ]
            }
        ]
    },
    {
        "level_name": "Intermediate",
        "description": "Build strategies using technical analysis tools. Master trend identification, chart patterns, and indicator confluence.",
        "modules": [
            {
                "title": "Technical Analysis Fundamentals",
                "description": "Trend identification and chart reading.",
                "lessons": [
                    {
                        "title": "Identifying Trends",
                        "content": """## Simple Definition
**Uptrend**: Series of Higher Highs (HH) and Higher Lows (HL).
**Downtrend**: Series of Lower Highs (LH) and Lower Lows (LL).
**Range**: Price oscillates between horizontal support/resistance.

## Concept Explanation
**Uptrend Characteristics**:
- Each peak higher than previous (HH)
- Each trough higher than previous (HL)
- 20 EMA > 50 EMA > 200 EMA
- Strategy: Buy pullbacks

**Downtrend Characteristics**:
- Each peak lower (LH)
- Each trough lower (LL)
- Moving averages slope down
- Strategy: Sell rallies

## Step-by-Step Breakdown
**Trend Analysis**:
1. **Zoom Out**: Check daily chart—what's major trend?
2. **Mark Swings**: Identify last 3 swing highs/lows
3. **Compare**: Are highs/lows getting higher?
4. **Moving Averages**: Price above 200 EMA?
5. **Trend Strength**: Steep angle = strong but risky

## Real Trading Example
**Trend Follower**:
- Daily: EUR/USD above 200 EMA, making HH/HL
- H4: Price pulls back to 50 EMA
- H1: Bullish engulfing at 50 EMA
- Entry: Buy at 1.0850
- Stop: 1.0820
- Target: 1.0920 (70 pips)

## Common Beginner Mistake
**Bottom Fishing**: Trying to buy absolute bottom of downtrend because "it can't go lower." Trends persist longer than intuition suggests.

## Key Takeaway
"The trend is your friend until the end when it bends." Never fight clear daily trend.

## Practice Question
In confirmed uptrend, what pattern must you see in swing points?""",
                        "quiz": [
                            {"question": "Uptrend requires?", "option_a": "Lower highs and lower lows", "option_b": "Higher highs and higher lows", "option_c": "Equal highs", "option_d": "Random", "correct_answer": "B", "explanation": "Uptrend = HH + HL required.", "topic_slug": "trend_analysis"},
                            {"question": "Price above 200 EMA indicates?", "option_a": "Bearish", "option_b": "Bullish bias", "option_c": "Range bound", "option_d": "Reversal imminent", "correct_answer": "B", "explanation": "Above 200 EMA = long-term bullish bias.", "topic_slug": "trend_analysis"},
                            {"question": "Trend lasted 6 months. You catch bottom 5 times. Result?", "option_a": "Profit", "option_b": "5 losses", "option_c": "Break even", "option_d": "Guaranteed reversal", "correct_answer": "B", "explanation": "Trends persist. Counter-trend trading loses.", "topic_slug": "trend_analysis"},
                            {"question": "Daily trend up, H1 shows downtrend. Trade?", "option_a": "Sell short on H1", "option_b": "Buy pullbacks on H1", "option_c": "Trade both", "option_d": "Avoid", "correct_answer": "B", "explanation": "Trade in direction of higher timeframe trend.", "topic_slug": "trend_analysis"},
                            {"question": "Selling because price 'too high' in uptrend?", "option_a": "Missing continued trend", "option_b": "Immediate profit", "option_c": "Lower risk", "option_d": "Better fills", "correct_answer": "A", "explanation": "Markets stay 'expensive' longer than you can stay solvent.", "topic_slug": "trend_analysis"}
                        ]
                    },
                    {
                        "title": "Multi-Timeframe Analysis",
                        "content": """## Simple Definition
Use higher timeframes for trend direction (the "road"), lower timeframes for entry timing (the "vehicle").

## Concept Explanation
**Top-Down Approach**:
1. **Daily Chart**: Are we driving north or south? (Trend)
2. **H4 Chart**: Where are the exits? (Key levels)
3. **H1 Chart**: When to press gas? (Entry trigger)

**Why It Works**:
- Daily trends persist weeks
- H4 levels respected by institutions
- H1 provides tight stops

## Step-by-Step Breakdown
**Triple Screen**:
1. Daily: Mark major trend and key zones
2. H4: Identify pullback areas (20/50 EMA)
3. H1: Wait for candlestick confirmation
4. Execute: Only when all three align

## Real Trading Example
**Perfect Alignment**:
- Daily: GBP/USD uptrend, above 200 EMA
- H4: Pullback to 50 EMA at 1.2750
- H1: Bullish pin bar at 1.2750
- Entry: 1.2755
- Stop: 1.2725
- Target: 1.2850
- R:R: 1:3.2

## Common Beginner Mistake
**Timeframe Confusion**: Analyzing H1 for trend, then trading daily charts. Backwards—H1 trends change every few hours.

## Key Takeaway
Higher timeframes for direction, lower for execution. If Daily and H4 disagree, wait.

## Practice Question
Which timeframe for major trend direction?""",
                        "quiz": [
                            {"question": "Best timeframe for major trend?", "option_a": "M5", "option_b": "H1", "option_c": "Daily", "option_d": "Monthly", "correct_answer": "C", "explanation": "Daily shows major trend persisting weeks.", "topic_slug": "timeframe_analysis"},
                            {"question": "Timeframe for entry timing?", "option_a": "Monthly", "option_b": "Weekly", "option_c": "Daily", "option_d": "H1 or H4", "correct_answer": "D", "explanation": "H1/H4 provide precise entries with tight stops.", "topic_slug": "timeframe_analysis"},
                            {"question": "Daily up, H1 down. Trade direction?", "option_a": "Short H1", "option_b": "Long with daily", "option_c": "Avoid", "option_d": "Trade both", "correct_answer": "B", "explanation": "Prioritize higher timeframe. H1 pullback = buy.", "topic_slug": "timeframe_analysis"},
                            {"question": "Daily and H4 disagree on trend?", "option_a": "Trade H4", "option_b": "Wait for alignment", "option_c": "Trade daily only", "option_d": "Increase size", "correct_answer": "B", "explanation": "When timeframes conflict, stay flat.", "topic_slug": "timeframe_analysis"},
                            {"question": "Using H1 trend to trade daily charts?", "option_a": "Better entries", "option_b": "Choppy, inconsistent signals", "option_c": "Lower risk", "option_d": "More profit", "correct_answer": "B", "explanation": "H1 trends change hourly. Using for daily causes whipsaws.", "topic_slug": "timeframe_analysis"}
                        ]
                    }
                ]
            },
            {
                "title": "Support and Resistance Advanced",
                "description": "Drawing levels professionals actually use.",
                "lessons": [
                    {
                        "title": "Drawing Professional Levels",
                        "content": """## Simple Definition
Clean levels have 3+ touches, visible on multiple timeframes, aligned with confluence (moving averages, round numbers, Fibonacci).

## Concept Explanation
**3-Touch Rule**:
- 1 touch = random
- 2 touches = possible, wait for 3rd
- 3+ touches = valid support/resistance
- 5+ touches = strong (but likely to break soon)

**Zone vs Line**:
- Lines: Exact prices (too precise)
- Zones: 10-20 pip ranges (realistic)

**Confluence Factors**:
- Round numbers (1.1000)
- Moving averages (50 EMA)
- Fibonacci (61.8%)
- Previous breakouts

## Step-by-Step Breakdown
**Drawing Clean Support**:
1. Find 3+ lows at similar area (±15 pips)
2. Extend line 20 candles forward/back
3. Check H4 and Daily—does level appear?
4. Mark zone with rectangle
5. Delete old levels (50+ candles untouched)

## Real Trading Example
**Confluence Zone**:
- EUR/USD pulls back to 1.0850
- Factors: Round number, previous resistance (role reversal), 50 EMA at 1.0848, 61.8% Fib at 1.0852
- Zone: 1.0845–1.0855
- Entry: Buy at 1.0850
- Stop: 1.0835
- Probability: 4 factors = high probability

## Common Beginner Mistake
**Spaghetti Charts**: 20+ lines covering every tiny high/low. Analysis paralysis. Professional charts have 3-5 clean levels maximum.

## Key Takeaway
Quality over quantity. One level with 4 touches and confluence beats 10 random lines.

## Practice Question
How many touches to validate significant level?""",
                        "quiz": [
                            {"question": "Touches to validate level?", "option_a": "1", "option_b": "2", "option_c": "3 or more", "option_d": "10", "correct_answer": "C", "explanation": "Need 3+ touches to validate significance.", "topic_slug": "advanced_snr"},
                            {"question": "What creates strongest levels?", "option_a": "Single touch", "option_b": "Two touches", "option_c": "3+ touches + confluence", "option_d": "Random lines", "correct_answer": "C", "explanation": "More touches + confluence = stronger level.", "topic_slug": "advanced_snr"},
                            {"question": "Why use zones vs exact lines?", "option_a": "Less precise", "option_b": "Markets are messy, zones catch wicks", "option_c": "Easier to draw", "option_d": "No difference", "correct_answer": "B", "explanation": "Exact lines cause missed trades. Zones account for noise.", "topic_slug": "advanced_snr"},
                            {"question": "Level has 5 touches over 6 months, none recently?", "option_a": "Keep active", "option_b": "Delete or mark inactive", "option_c": "Trade aggressively", "option_d": "Increase size", "correct_answer": "B", "explanation": "Untouched levels for 50+ candles lose relevance.", "topic_slug": "advanced_snr"},
                            {"question": "Drawing 20+ lines on chart?", "option_a": "Better analysis", "option_b": "Analysis paralysis", "option_c": "More profits", "option_d": "Clearer signals", "correct_answer": "B", "explanation": "Too many lines cause confusion. Use 3-5 maximum.", "topic_slug": "advanced_snr"}
                        ]
                    },
                    {
                        "title": "Dynamic Support with Moving Averages",
                        "content": """## Simple Definition
Moving averages act as dynamic support/resistance updating every candle. Unlike static lines, they follow price and indicate trend strength.

## Concept Explanation
**The Three Amigos**:
- **20 EMA**: Short-term, immediate support/resistance
- **50 EMA**: Medium-term, deeper pullback level
- **200 EMA**: Long-term trend separator

**Golden Cross / Death Cross**:
- Golden: 50 crosses above 200 (bullish)
- Death: 50 crosses below 200 (bearish)

## Step-by-Step Breakdown
**Trading EMA Bounce**:
1. Identify trend (price vs 200 EMA)
2. Wait for pullback to 20 or 50 EMA
3. Look for candlestick confirmation at EMA
4. Enter in trend direction
5. Stop loss below EMA (plus buffer)

## Real Trading Example
**EMA Trio Trade**:
- Daily: Price above 200 EMA (bullish)
- H4: Pullback to 50 EMA at 1.2500
- H1: Bullish hammer at 50 EMA
- Entry: Buy 1.2510
- Stop: 1.2480
- Logic: Triple confluence

## Common Beginner Mistake
**EMA Abuse**: Using 10 EMAs (8, 13, 21, 34, 55, 89...) on one chart. Creates confusion. Stick to 20/50/200.

## Key Takeaway
Moving averages show trend health. Price above 20 EMA = strong trend. Respect these levels like horizontal support.

## Practice Question
What does Golden Cross indicate?""",
                        "quiz": [
                            {"question": "Golden Cross is?", "option_a": "50 EMA crosses above 200", "option_b": "200 crosses above 50", "option_c": "Price crosses 20", "option_d": "Two MAs touch", "correct_answer": "A", "explanation": "50 above 200 = Golden Cross (bullish).", "topic_slug": "moving_averages"},
                            {"question": "Which EMA is immediate support?", "option_a": "200", "option_b": "50", "option_c": "20", "option_d": "All equal", "correct_answer": "C", "explanation": "20 EMA is short-term dynamic support.", "topic_slug": "moving_averages"},
                            {"question": "Price 50 pips above 200 EMA means?", "option_a": "Weak", "option_b": "Extended (possible pullback)", "option_c": "Bearish", "option_d": "No trend", "correct_answer": "B", "explanation": "Far above 200 EMA often indicates overbought.", "topic_slug": "moving_averages"},
                            {"question": "Price below 50 EMA but above 200?", "option_a": "Trend reversal", "option_b": "Medium-term weakness, long-term bullish", "option_c": "Buy immediately", "option_d": "Strong uptrend", "correct_answer": "B", "explanation": "Below 50 = medium weakness. Above 200 = long-term bullish.", "topic_slug": "moving_averages"},
                            {"question": "Using 8 EMAs on one chart?", "option_a": "Better signals", "option_b": "Conflicting signals", "option_c": "Higher win rate", "option_d": "Simpler analysis", "correct_answer": "B", "explanation": "Too many EMAs cause whipsaws. Use 20, 50, 200 only.", "topic_slug": "moving_averages"}
                        ]
                    }
                ]
            },
            {
                "title": "Chart Patterns",
                "description": "Reversals and continuations—flags, H&S, triangles.",
                "lessons": [
                    {
                        "title": "Reversal Patterns",
                        "content": """## Simple Definition
Reversal patterns signal existing trend ending, price likely moving opposite direction. Most reliable at major support/resistance.

## Concept Explanation
**Head and Shoulders**:
- Structure: Three peaks, middle (Head) highest, outer (Shoulders) equal
- Neckline: Support connecting troughs between peaks
- Signal: Break below neckline confirms reversal
- Target: Head-to-neckline distance projected down

**Double Top/Bottom**:
- Double Top: Two peaks at resistance (M pattern, bearish)
- Double Bottom: Two troughs at support (W pattern, bullish)
- Confirmation: Break of middle trough/neckline

## Step-by-Step Breakdown
**Trading Head and Shoulders**:
1. Identify three peaks with center highest
2. Draw neckline connecting lows between shoulders
3. Wait for neckline break (don't short head formation)
4. Enter on break with momentum
5. Stop above right shoulder
6. Target: Head-to-neckline distance down

## Real Trading Example
**EUR/USD Bearish Reversal**:
- Left Shoulder: 1.1200 (support 1.1050)
- Head: 1.1300 (support 1.1050)
- Right Shoulder: 1.1180
- Neckline: 1.1050
- Entry: 1.1040 (neckline break)
- Stop: 1.1200
- Target: 1.0800 (250 pips down)
- Result: Hits 1.0750 in 3 weeks

<svg class="ac-svg-diagram" viewBox="0 0 400 250">
  <path d="M 50 180 L 120 100 L 180 60 L 240 100 L 300 180" fill="none" stroke="#60a5fa" stroke-width="3"/>
  <line x1="50" y1="180" x2="300" y2="180" stroke="#ef4444" stroke-width="2" stroke-dasharray="5,5"/>
  <text x="180" y="195" text-anchor="middle" fill="#ef4444" font-size="12">Neckline (Break = Sell)</text>
  <text x="180" y="50" text-anchor="middle" fill="#fbbf24" font-size="14">HEAD</text>
  <text x="85" y="90" text-anchor="middle" fill="#9ca3af" font-size="12">Left Shoulder</text>
  <text x="275" y="90" text-anchor="middle" fill="#9ca3af" font-size="12">Right Shoulder</text>
  <line x1="180" y1="60" x2="180" y2="180" stroke="#fbbf24" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="180" y1="180" x2="180" y2="240" stroke="#22c55e" stroke-width="2"/>
  <text x="200" y="220" fill="#22c55e" font-size="12">Target</text>
</svg>

## Common Beginner Mistake
**Anticipating Pattern**: Selling the "head" before neckline breaks. Patterns fail frequently—always wait for neckline break with close confirmation.

## Key Takeaway
Reversal patterns complete only after neckline breaks. H&S has 70-75% success rate at major resistance after extended trends.

## Practice Question
Where is stop loss placed in Head and Shoulders pattern?""",
                        "quiz": [
                            {"question": "What confirms H&S pattern?", "option_a": "Three peaks", "option_b": "Break below neckline", "option_c": "High volume on head", "option_d": "Long wicks", "correct_answer": "B", "explanation": "Pattern confirmed when price breaks below neckline.", "topic_slug": "chart_patterns"},
                            {"question": "How is profit target measured?", "option_a": "Head to right shoulder", "option_b": "Head to neckline, projected down", "option_c": "Left shoulder to head", "option_d": "Random Fibonacci", "correct_answer": "B", "explanation": "Measure head-to-neckline, project down from break.", "topic_slug": "chart_patterns"},
                            {"question": "Calculate: Head 1.2000, Neckline 1.1800. Breaks 1.1790. Target?", "option_a": "1.1600", "option_b": "1.1590", "option_c": "1.1790", "option_d": "1.2200", "correct_answer": "B", "explanation": "200 pips down from 1.1790 = 1.1590.", "topic_slug": "chart_patterns"},
                            {"question": "Price forms head and right shoulder but reverses up before neckline break?", "option_a": "Pattern failed", "option_b": "Enter early", "option_c": "Increase size", "option_d": "Pattern still valid", "correct_answer": "A", "explanation": "No neckline break = invalid pattern.", "topic_slug": "chart_patterns"},
                            {"question": "Selling at head before neckline break?", "option_a": "Missing profit", "option_b": "Pattern may never complete", "option_c": "Better fills", "option_d": "Lower risk", "correct_answer": "B", "explanation": "Selling formation early assumes completion.", "topic_slug": "chart_patterns"}
                        ]
                    },
                    {
                        "title": "Continuation Patterns",
                        "content": """## Simple Definition
Continuation patterns are consolidation zones within trends where price pauses before resuming original direction.

## Concept Explanation
**Bull/Bear Flags**:
- Structure: Strong pole followed by small channel against trend
- Bull Flag: Steep rise, then downward sloping channel
- Bear Flag: Sharp drop, then upward channel
- Entry: Break in original trend direction

**Triangles**:
- Ascending: Flat top, rising bottom (bullish)
- Descending: Flat bottom, falling top (bearish)
- Symmetrical: Converging, breakout direction determines trade

## Step-by-Step Breakdown
**Trading Bull Flag**:
1. Identify pole: Strong bullish candles (200+ pips)
2. Mark channel: Two parallel lines containing pullback
3. Wait: Price touches lower channel twice
4. Enter: Buy break above upper channel
5. Stop: Below lowest point of flag
6. Target: Pole length projected up

## Real Trading Example
**GBP/JPY Bear Flag**:
- Pole: 185.00 to 182.00 (300 pips) in 2 days
- Flag: 182.00-183.00 for 3 days (upward channel)
- Entry: 181.90 (break below support)
- Stop: 183.20
- Target: 179.00 (300 pips)
- Result: Hits 179.00 in 48 hours

<svg class="ac-svg-diagram" viewBox="0 0 400 200">
  <line x1="50" y1="150" x2="150" y2="50" stroke="#ef4444" stroke-width="3"/>
  <text x="100" y="80" fill="#ef4444" font-size="12">Pole</text>
  <path d="M 150 50 L 200 80 L 250 60 L 300 70" fill="none" stroke="#fbbf24" stroke-width="2"/>
  <line x1="150" y1="85" x2="300" y2="55" stroke="#9ca3af" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="170" y1="95" x2="320" y2="65" stroke="#9ca3af" stroke-width="1" stroke-dasharray="3,3"/>
  <text x="225" y="45" fill="#fbbf24" font-size="12">Flag Channel</text>
  <line x1="300" y1="70" x2="350" y2="20" stroke="#ef4444" stroke-width="3"/>
  <text x="330" y="50" fill="#ef4444" font-size="12">Breakout</text>
</svg>

## Common Beginner Mistake
**Counter-Trend Trading Consolidation**: Seeing flag in downtrend and thinking "it's going up, I'll buy!" Trade WITH pole direction.

## Key Takeaway
Flags are rest stops for trends. Pole direction tells you which way to trade. Never trade inside pattern—wait for breakout.

## Practice Question
When trading bear flag, which direction for breakout?""",
                        "quiz": [
                            {"question": "Flag pattern indicates?", "option_a": "Trend reversal", "option_b": "Trend continuation", "option_c": "Market top", "option_d": "Low volatility", "correct_answer": "B", "explanation": "Flags = temporary consolidation before trend resumes.", "topic_slug": "chart_patterns"},
                            {"question": "Bull flag consolidation slopes?", "option_a": "Upward", "option_b": "Downward", "option_c": "Flat", "option_d": "Vertical", "correct_answer": "B", "explanation": "Bull flags slope down against trend.", "topic_slug": "chart_patterns"},
                            {"question": "Calculate: Pole 150 pips up. Breakout 1.2000. Target?", "option_a": "1.1850", "option_b": "1.2000", "option_c": "1.2150", "option_d": "1.3500", "correct_answer": "C", "explanation": "Project pole length: 1.2000 + 0.0150 = 1.2150.", "topic_slug": "chart_patterns"},
                            {"question": "Bullish candle inside flag?", "option_a": "Buy immediately", "option_b": "Wait for upper channel breakout", "option_c": "Sell short", "option_d": "Double position", "correct_answer": "B", "explanation": "Don't trade inside patterns. Wait for confirmed breakout.", "topic_slug": "chart_patterns"},
                            {"question": "Buying bear flag because 'it looks bullish'?", "option_a": "Profit when trend reverses", "option_b": "Loss when trend continues", "option_c": "Guaranteed win", "option_d": "No effect", "correct_answer": "B", "explanation": "Bear flags resolve downward.", "topic_slug": "chart_patterns"}
                        ]
                    }
                ]
            },
            {
                "title": "Candlestick Patterns",
                "description": "Pin bars, engulfing candles, doji patterns.",
                "lessons": [
                    {
                        "title": "Pin Bars and Rejection Signals",
                        "content": """## Simple Definition
Pin Bar (Pinocchio bar) has long wick and small body, showing sharp price rejection. The wick "lies" about direction.

## Concept Explanation
**Bullish Pin Bar**:
- Long lower wick (2-3x body), small body at top
- Meaning: Sellers pushed down, buyers rejected
- Location: Best at support or bottom of downtrend

**Bearish Pin Bar**:
- Long upper wick, small body at bottom
- Meaning: Buyers pushed up, sellers rejected
- Location: Best at resistance

## Step-by-Step Breakdown
**Trading Pin Bar**:
1. Locate context: Support/resistance or trend extreme
2. Spot pattern: Long wick (3x body minimum)
3. Confirm: Next candle closes in signal direction
4. Enter: Break of pin bar high/low
5. Manage: 50% at 1R, move stop to breakeven

## Real Trading Example
**EUR/USD Support Bounce**:
- Context: Triple touch support at 1.0850
- Pin Bar: H4, Open 1.0850, Low 1.0820 (30-pip wick), Close 1.0855
- Entry: Buy 1.0860
- Stop: 1.0815
- Target: 1.0900
- Adjustment: Wait for better R:R or take 50% at 1.0880

## Common Beginner Mistake
**Trading Every Pin Bar**: Pins appear constantly. Only trade at clear support/resistance with confluence (trendline, MA, Fibonacci).

## Key Takeaway
Wick tells story of rejection. Trade pin bars only at significant levels where institutions defend prices.

## Practice Question
Minimum wick-to-body ratio for valid pin bar?""",
                        "quiz": [
                            {"question": "Bullish pin bar characteristic?", "option_a": "Long upper wick", "option_b": "Long lower wick, body at top", "option_c": "No wicks", "option_d": "Equal wicks", "correct_answer": "B", "explanation": "Bullish pin has long lower wick, small body near high.", "topic_slug": "candlestick_patterns"},
                            {"question": "Where do pin bars work best?", "option_a": "Middle of range", "option_b": "Strong support/resistance only", "option_c": "During news", "option_d": "Anywhere", "correct_answer": "B", "explanation": "Pin bars need context at key technical levels.", "topic_slug": "candlestick_patterns"},
                            {"question": "Body 5 pips, lower wick 15 pips. Ratio?", "option_a": "1:1", "option_b": "2:1", "option_c": "3:1", "option_d": "4:1", "correct_answer": "C", "explanation": "15 ÷ 5 = 3:1 ratio. Minimum 2:1 required.", "topic_slug": "candlestick_patterns"},
                            {"question": "Bearish pin bar at all-time high resistance?", "option_a": "Ignore", "option_b": "Sell break below low", "option_c": "Buy immediately", "option_d": "Remove stops", "correct_answer": "B", "explanation": "Bearish pin at resistance = high-probability short.", "topic_slug": "candlestick_patterns"},
                            {"question": "Trading pin bar mid-trend without level?", "option_a": "High probability", "option_b": "No confluence, likely continuation", "option_c": "Guaranteed profit", "option_d": "Lower spreads", "correct_answer": "B", "explanation": "Pins without support/resistance often fail.", "topic_slug": "candlestick_patterns"}
                        ]
                    },
                    {
                        "title": "Engulfing Patterns and Doji",
                        "content": """## Simple Definition
Engulfing patterns: One candle completely engulfs previous candle's body, showing momentum shift. Doji shows indecision with equal open and close.

## Concept Explanation
**Bullish Engulfing**:
- Green candle body completely covers previous red body
- Psychology: Buyers overwhelmed sellers
- Location: Bottom of downtrend or support

**Bearish Engulfing**:
- Red candle body completely covers previous green body
- Psychology: Sellers took control
- Location: Top of uptrend or resistance

**Doji Types**:
- Standard: Open = Close, small wicks
- Dragonfly: Long lower wick (bullish at support)
- Gravestone: Long upper wick (bearish at resistance)

## Step-by-Step Breakdown
**Trading Engulfing**:
1. Identify trend (end of extended move, not middle)
2. Spot pattern: Second candle body fully engulfs first
3. Check size: Engulfing candle larger than average
4. Enter: Break above engulfing high (bullish)
5. Stop: Beyond pattern extreme

## Real Trading Example
**USD/JPY Bearish Engulfing**:
- Context: Approaches 147.00 resistance
- Day 1: Green candle 146.50-147.00
- Day 2: Red candle 147.00-145.80 (engulfs completely)
- Entry: Sell 145.75
- Stop: 147.10
- Target: 144.00
- R:R: 1:1.3 (acceptable with strong signal)

## Common Beginner Mistake
**Trading Small Engulfing Patterns**: Small engulfing in quiet markets is noise, not trend change. Look for conviction—significantly larger candles.

## Key Takeaway
Engulfing shows conviction shifts. Doji shows exhaustion—prepare for breakout direction next candle.

## Practice Question
What must be true about second candle in bullish engulfing?""",
                        "quiz": [
                            {"question": "Bullish engulfing requires?", "option_a": "Green bigger than previous red body", "option_b": "Any green after red", "option_c": "Long upper wick", "option_d": "Small body", "correct_answer": "A", "explanation": "Current green body must completely cover previous red body.", "topic_slug": "candlestick_patterns"},
                            {"question": "Gravestone Doji indicates?", "option_a": "Strong buying", "option_b": "Bullish continuation", "option_c": "Rejection of higher prices", "option_d": "Low volatility", "correct_answer": "C", "explanation": "Gravestone has long upper wick showing rejection.", "topic_slug": "candlestick_patterns"},
                            {"question": "Calculate: Up 1R. Stop placement?", "option_a": "Original stop", "option_b": "Move to breakeven", "option_c": "Remove stop", "option_d": "Tighten to 0.5R", "correct_answer": "B", "explanation": "At 1R profit, move stop to entry for risk-free trade.", "topic_slug": "candlestick_patterns"},
                            {"question": "Doji after strong 200-pip uptrend?", "option_a": "Buy more", "option_b": "Trend exhaustion", "option_c": "Sell immediately", "option_d": "Ignore", "correct_answer": "B", "explanation": "Doji after extended move shows exhaustion.", "topic_slug": "candlestick_patterns"},
                            {"question": "Trading engulfing in middle of range?", "option_a": "Better analysis", "option_b": "No trend context, just noise", "option_c": "Higher win rate", "option_d": "Clearer signals", "correct_answer": "B", "explanation": "Engulfing needs trend context. In ranges, it's noise.", "topic_slug": "candlestick_patterns"}
                        ]
                    }
                ]
            },
            {
                "title": "Trading Indicators",
                "description": "MACD, RSI, and Moving Averages used properly.",
                "lessons": [
                    {
                        "title": "RSI and Momentum",
                        "content": """## Simple Definition
RSI (Relative Strength Index) measures momentum on 0-100 scale. Identifies overbought (potential sells) and oversold (potential buys), plus divergence.

## Concept Explanation
**RSI Levels**:
- Above 70: Overbought (may fall, but can stay overbought in trends)
- Below 30: Oversold (may rise, but can stay oversold in crashes)
- 50 Level: Bullish above, Bearish below

**Divergence** (Most Reliable):
- Bullish Divergence: Price lower low, RSI higher low (buy)
- Bearish Divergence: Price higher high, RSI lower high (sell)

## Step-by-Step Breakdown
**Trading RSI Divergence**:
1. Identify trend, mark swing highs/lows
2. Compare RSI at same points
3. Spot divergence: Price and RSI moving opposite?
4. Confirm: Wait for reversal candle
5. Enter: Trade reversal direction
6. Manage: Divergence can persist—tight risk

## Real Trading Example
**EUR/USD Bullish Divergence**:
- Price: Drops to 1.0800 (lower low)
- RSI: First low 28, second low 35 (higher low)
- Divergence: Price lower, RSI higher
- Confirmation: Bullish engulfing at 1.0800
- Entry: Buy 1.0810
- Stop: 1.0780
- Target: 1.0900

<svg class="ac-svg-diagram" viewBox="0 0 400 200">
  <path d="M 50 150 L 100 120 L 150 140 L 200 80" fill="none" stroke="#ef4444" stroke-width="2"/>
  <text x="220" y="80" fill="#ef4444" font-size="12">Price Lower Low</text>
  <path d="M 50 150 L 100 130 L 150 145 L 200 100" fill="none" stroke="#22c55e" stroke-width="2" stroke-dasharray="5,5"/>
  <text x="220" y="100" fill="#22c55e" font-size="12">RSI Higher Low</text>
  <text x="200" y="180" text-anchor="middle" fill="#fbbf24" font-size="14">BULLISH DIVERGENCE</text>
</svg>

## Common Beginner Mistake
**RSI Overbought = Immediate Short**: In strong uptrends, RSI stays overbought for weeks. Always confirm with price action.

## Key Takeaway
RSI measures momentum. Divergence between price and RSI is highest-probability signal. Never trade RSI alone.

## Practice Question
What does bullish divergence indicate?""",
                        "quiz": [
                            {"question": "RSI above 70 indicates?", "option_a": "Guaranteed reversal", "option_b": "Overbought, potential reversal", "option_c": "Strong bearish", "option_d": "Low volatility", "correct_answer": "B", "explanation": "RSI >70 shows overbought, but can persist in trends.", "topic_slug": "indicators"},
                            {"question": "Bullish divergence is?", "option_a": "Price and RSI both rising", "option_b": "Price lower low, RSI higher low", "option_c": "Price higher high, RSI higher high", "option_d": "RSI above 70", "correct_answer": "B", "explanation": "Price drops but RSI forms higher low = momentum strengthening.", "topic_slug": "indicators"},
                            {"question": "Calculate: RSI 75, price at resistance with bearish pin bar. Signal?", "option_a": "Strong buy", "option_b": "Overbought + rejection = sell", "option_c": "Hold longs", "option_d": "Add to longs", "correct_answer": "B", "explanation": "Overbought + price rejection = high-probability short.", "topic_slug": "indicators"},
                            {"question": "Strong uptrend, RSI 85 for 5 days. Action?", "option_a": "Sell immediately", "option_b": "Wait for price reversal", "option_c": "Buy more", "option_d": "Double position", "correct_answer": "B", "explanation": "RSI can stay overbought in trends. Wait for bearish price action.", "topic_slug": "indicators"},
                            {"question": "Trading RSI overbought without price confirmation?", "option_a": "High win rate", "option_b": "Selling into strong trend, stopped out", "option_c": "Guaranteed profit", "option_d": "Lower risk", "correct_answer": "B", "explanation": "Without price confirmation, RSI signals fail in trends.", "topic_slug": "indicators"}
                        ]
                    },
                    {
                        "title": "MACD and Moving Averages",
                        "content": """## Simple Definition
MACD shows relationship between two moving averages (12 and 26 EMA). Consists of MACD line, Signal line (9 EMA of MACD), and Histogram.

## Concept Explanation
**MACD Components**:
- MACD Line: 12 EMA minus 26 EMA
- Signal Line: 9 EMA of MACD Line
- Histogram: MACD minus Signal (momentum)
- Zero Line: Separates bullish/bearish

**Signals**:
- Crossover: MACD above Signal = Buy
- Zero Line Cross: Above 0 = bullish trend shift
- Divergence: Price high, MACD lower high = bearish

## Step-by-Step Breakdown
**Trading MACD Crossovers**:
1. Check trend: Price above/below 200 EMA for bias
2. Wait for cross: MACD crosses Signal in trend direction
3. Histogram: Bars should expand
4. Entry: Price pullback to MA + MACD alignment
5. Stop: Beyond recent swing

## Real Trading Example
**Trend Following**:
- Daily: Price above 200 EMA (bullish bias)
- H4: Pullback to 50 EMA, MACD histogram shrinking
- H1: MACD crosses above Signal at 50 EMA
- Entry: Buy at 50 EMA
- Stop: Below 50 EMA and recent low

## Common Beginner Mistake
**MACD Lag Trading**: MACD is lagging. Trading every cross causes late entries. Use for trend confirmation and divergence only.

## Key Takeaway
MACD confirms trend and momentum but lags price. Use to confirm direction, identify divergence warnings, time entries in established trends.

## Practice Question
What does MACD line crossing above Signal line above zero indicate?""",
                        "quiz": [
                            {"question": "MACD crossing above Signal indicates?", "option_a": "Bearish", "option_b": "Bullish momentum shift", "option_c": "No change", "option_d": "Market closed", "correct_answer": "B", "explanation": "MACD above Signal = bullish acceleration.", "topic_slug": "indicators"},
                            {"question": "Histogram shrinking while price rising?", "option_a": "Increasing momentum", "option_b": "Momentum deceleration", "option_c": "Strong trend", "option_d": "Low volatility", "correct_answer": "B", "explanation": "Shrinking histogram = slowing momentum, potential reversal warning.", "topic_slug": "indicators"},
                            {"question": "Price 100 pips above 200 EMA, MACD crosses below signal?", "option_a": "Trend continuation buy", "option_b": "Overextended, potential pullback", "option_c": "Golden cross", "option_d": "No significance", "correct_answer": "B", "explanation": "Extended + bearish cross suggests overbought pullback.", "topic_slug": "indicators"},
                            {"question": "MACD bullish cross but price below 200 EMA?", "option_a": "Buy full position", "option_b": "Avoid or small size", "option_c": "Sell short", "option_d": "Double leverage", "correct_answer": "B", "explanation": "Crosses against major trend are lower probability.", "topic_slug": "indicators"},
                            {"question": "Trading every MACD cross regardless of trend?", "option_a": "High win rate", "option_b": "Many false signals in ranges", "option_c": "Guaranteed profits", "option_d": "Better execution", "correct_answer": "B", "explanation": "MACD generates false signals in ranges. Filter by trend.", "topic_slug": "indicators"}
                        ]
                    }
                ]
            },
            {
                "title": "Trading Strategies",
                "description": "Building complete, rule-based trading strategies.",
                "lessons": [
                    {
                        "title": "Strategy Components",
                        "content": """## Simple Definition
Trading strategy is complete set of rules: when to enter, when to exit (profit/loss), how much to trade, and which markets.

## Concept Explanation
**Strategy Framework**:
1. Market Selection: Which pairs, timeframes, sessions?
2. Setup Criteria: Conditions before considering trade
3. Entry Rules: Exact trigger
4. Exit Rules: Stop loss and take profit
5. Risk Management: Position sizing, max daily loss
6. Review Process: Weekly performance analysis

**Example Strategy (Trend Pullback)**:
- Market: EUR/USD, GBP/USD
- Timeframe: H4 trend, H1 entry
- Setup: Price above 200 EMA, pulling back to 50 EMA
- Entry: Bullish pin bar or engulfing at 50 EMA
- Stop: Below pullback low
- Target: Previous swing high (1:2 minimum)
- Risk: 1% per trade, max 3/day

## Step-by-Step Breakdown
**Building Your Strategy**:
1. Choose style: Scalping, Day trading, Swing
2. Select tools: Price action, indicators, or combination
3. Define edge: What market condition does it exploit?
4. Backtest: 100+ historical trades
5. Demo trade: 3 months forward testing
6. Journal: Record every trade with emotions

## Real Trading Example
**London Open Breakout**:
- Market: GBP/USD
- Time: 08:00-09:00 GMT
- Setup: Asian session range established
- Entry: Buy stop 5 pips above Asian high
- Stop: Opposite side of range
- Target: 1:1.5 R:R minimum
- Filter: Only if ADR > 80 pips

## Common Beginner Mistake
**Strategy Hopping**: Trying strategy for 3 losses, abandoning for "better" system. No strategy wins every trade. Edge appears over 20+ trades.

## Key Takeaway
Consistency comes from rules, not intuition. Write strategy rules. If you can't explain to 10-year-old, it's too complicated.

## Practice Question
Minimum Risk:Reward ratio for sustainable strategy?""",
                        "quiz": [
                            {"question": "Complete strategy must include?", "option_a": "Only entries", "option_b": "Entries, exits, sizing, markets", "option_c": "Only stops", "option_d": "Lucky charm", "correct_answer": "B", "explanation": "Complete strategies define all components.", "topic_slug": "strategy"},
                            {"question": "Trades minimum to evaluate strategy?", "option_a": "3", "option_b": "10", "option_c": "100", "option_d": "1", "correct_answer": "C", "explanation": "Need 100+ trades for statistical significance.", "topic_slug": "strategy"},
                            {"question": "Calculate: 40% win rate, 1:2 R:R. Profitability?", "option_a": "Losing", "option_b": "Breakeven", "option_c": "Profitable", "option_d": "Cannot determine", "correct_answer": "C", "explanation": "(40×2) - (60×1) = +20 per 100 trades.", "topic_slug": "strategy"},
                            {"question": "3 losses in a row with new strategy?", "option_a": "Change immediately", "option_b": "Continue if rules followed", "option_c": "Increase size", "option_d": "Trade random pairs", "correct_answer": "B", "explanation": "3 losses is normal variance. Review larger sample.", "topic_slug": "strategy"},
                            {"question": "Adding new indicators every week?", "option_a": "Better edge", "option_b": "Curve-fitting, no consistency", "option_c": "Guaranteed profits", "option_d": "Lower risk", "correct_answer": "B", "explanation": "Constant changes lead to curve-fitting past data.", "topic_slug": "strategy"}
                        ]
                    },
                    {
                        "title": "Backtesting and Forward Testing",
                        "content": """## Simple Definition
Backtesting applies strategy to historical data to verify profitability. Forward testing validates with real-time data without risking capital.

## Concept Explanation
**Backtesting Process**:
1. Manual backtest: 2+ years of charts, mark every setup
2. Record: Entry, exit, R:R, win rate, max drawdown
3. Statistics:
   - Win Rate %
   - Average R:R
   - Expectancy (mathematical edge)
   - Max consecutive losses
   - Worst drawdown

**Expectancy Formula**: (Win% × AvgWin) - (Loss% × AvgLoss)

**Forward Testing**: Demo account for 3 months. Must match live conditions (spreads, slippage).

## Step-by-Step Breakdown
**Validating Strategy**:
1. Historical test: 100+ trades over different conditions
2. Analyze metrics: Expectancy > 0.2R per trade
3. Demo phase: 50+ forward test trades
4. Micro live: 0.01 lots for 20 trades
5. Scale up: Only after proven consistency

## Real Trading Example
**Backtest Results - Pin Bar Strategy**:
- Period: 2022-2024, 500 trades
- Win Rate: 48%
- Avg Win: 2.5R, Avg Loss: 1R
- Expectancy: (0.48×2.5) - (0.52×1) = +0.68R
- Max consecutive losses: 6
- Forward test: 3 months confirmed 46% win rate

## Common Beginner Mistake
**Curve Fitting**: Adding filters until backtest shows 90% win rate. Fails on new data because optimized for noise, not signal.

## Key Takeaway
Backtesting proves edge in past. Forward testing proves edge continues. Never risk real money until both show positive expectancy.

## Practice Question
Minimum sample size for statistically significant backtest?""",
                        "quiz": [
                            {"question": "Purpose of backtesting?", "option_a": "Predict exact prices", "option_b": "Verify strategy edge historically", "option_c": "Avoid losses", "option_d": "Impress friends", "correct_answer": "B", "explanation": "Backtesting verifies positive expectancy over history.", "topic_slug": "strategy_dev"},
                            {"question": "Curve-fitting means?", "option_a": "Perfect fit to future", "option_b": "Over-optimized to historical noise", "option_c": "Robust design", "option_d": "Risk management", "correct_answer": "B", "explanation": "Curve-fitting creates false excellence on past data.", "topic_slug": "strategy_dev"},
                            {"question": "Robust strategy survives?", "option_a": "Parameter changes", "option_b": "Different pairs", "option_c": "Spread variations", "option_d": "All of above", "correct_answer": "D", "explanation": "True edge persists across variations and conditions.", "topic_slug": "strategy_dev"},
                            {"question": "Strategy works on EUR/USD but fails on GBP/USD?", "option_a": "GBP random", "option_b": "Curve-fitted to EUR specifics", "option_c": "Different timezones", "option_d": "Better on EUR", "correct_answer": "B", "explanation": "Robust edges work across similar instruments.", "topic_slug": "strategy_dev"},
                            {"question": "Optimizing until 90% win rate?", "option_a": "Future success", "option_b": "Curve-fitted, fails on new data", "option_c": "Guaranteed profits", "option_d": "Lower drawdown", "correct_answer": "B", "explanation": "90% win rates usually mean fitting to historical quirks.", "topic_slug": "strategy_dev"}
                        ]
                    }
                ]
            }
        ]
    },
    {
        "level_name": "Advanced",
        "description": "Trade like an institution—master market structure, liquidity concepts, and professional risk management.",
        "modules": [
            {
                "title": "Market Structure",
                "description": "BOS, CHoCH, order blocks, and fair value gaps.",
                "lessons": [
                    {
                        "title": "Break of Structure (BOS) and CHoCH",
                        "content": """## Simple Definition
**BOS**: Price breaks above previous high in uptrend (or below low in downtrend), confirming continuation.
**CHoCH**: Price breaks below previous low in uptrend (or above high in downtrend), signaling potential reversal.

## Concept Explanation
**Market Structure**:
- Uptrend: Higher Highs (HH) and Higher Lows (HL)
- Downtrend: Lower Highs (LH) and Lower Lows (LL)
- Bullish BOS: Break above last HH
- Bearish BOS: Break below last LL
- Bullish CHoCH: Break above last LH in downtrend
- Bearish CHoCH: Break below last HL in uptrend

## Step-by-Step Breakdown
**Trading CHoCH**:
1. Identify trend (HH/HL or LH/LL sequence)
2. Watch for break of last HL (uptrend) or LH (downtrend)
3. Confirm: Close beyond structure point
4. Enter: Retest of broken level (now support/resistance flip)
5. Manage: Stop beyond new extreme

## Real Trading Example
**Bearish CHoCH on EUR/USD**:
- Trend: Uptrend with HH at 1.1000, HL at 1.0900, new HH at 1.1050
- Change: Price drops below 1.0900 with momentum
- CHoCH Confirmed: Uptrend broken
- Entry: Retest of 1.0900 (now resistance)
- Stop: Above 1.1050
- Target: 1.0800

<svg class="ac-svg-diagram" viewBox="0 0 400 250">
  <text x="200" y="20" text-anchor="middle" fill="#fbbf24" font-size="14">BEARISH CHoCH</text>
  <path d="M 50 200 L 100 150 L 150 180 L 200 100" fill="none" stroke="#22c55e" stroke-width="2"/>
  <text x="210" y="100" fill="#22c55e" font-size="12">HH</text>
  <path d="M 200 100 L 250 140" fill="none" stroke="#22c55e" stroke-width="2"/>
  <text x="260" y="130" fill="#22c55e" font-size="12">HL</text>
  <path d="M 250 140 L 300 80" fill="none" stroke="#22c55e" stroke-width="2"/>
  <text x="310" y="80" fill="#22c55e" font-size="12">HH</text>
  <path d="M 300 80 L 350 200" fill="none" stroke="#ef4444" stroke-width="3"/>
  <line x1="250" y1="140" x2="350" y2="140" stroke="#ef4444" stroke-width="1" stroke-dasharray="5,5"/>
  <text x="300" y="155" fill="#ef4444" font-size="12">CHoCH Break</text>
</svg>

## Common Beginner Mistake
**CHoCH Hunting**: Taking every internal CHoCH on M15 as reversal. Minor breaks constantly. Only trade CHoCH when external structure aligns.

## Key Takeaway
Structure tells who controls market. BOS = Trend continues. CHoCH = Control shifting. Always know where you are in structure sequence.

## Practice Question
What does BOS indicate in established uptrend?""",
                        "quiz": [
                            {"question": "BOS in uptrend means?", "option_a": "Trend reversal", "option_b": "Trend continuation (new HH)", "option_c": "Market crash", "option_d": "No significance", "correct_answer": "B", "explanation": "Break above previous high confirms continuation.", "topic_slug": "market_structure"},
                            {"question": "CHoCH indicates?", "option_a": "Trend continuation", "option_b": "Potential trend reversal", "option_c": "Low volatility", "option_d": "Gap fill", "correct_answer": "B", "explanation": "Breaking previous HL/LH signals possible trend change.", "topic_slug": "market_structure"},
                            {"question": "Structure matters most for swing trading?", "option_a": "M5 internal", "option_b": "H4/Daily external", "option_c": "Tick chart", "option_d": "All equal", "correct_answer": "B", "explanation": "External structure on higher timeframes determines major trend.", "topic_slug": "market_structure"},
                            {"question": "Price breaks below HL in strong uptrend?", "option_a": "Immediately sell", "option_b": "Wait for retest and confirmation", "option_c": "Double longs", "option_d": "Remove stops", "correct_answer": "B", "explanation": "Wait for retest of broken structure as resistance.", "topic_slug": "market_structure"},
                            {"question": "Trading M15 CHoCH against H4 trend?", "option_a": "High probability reversal", "option_b": "Minor pullback in major trend", "option_c": "Guaranteed profit", "option_d": "Lower risk", "correct_answer": "B", "explanation": "Low timeframe breaks are often pullbacks in higher trends.", "topic_slug": "market_structure"}
                        ]
                    },
                    {
                        "title": "Order Blocks and Fair Value Gaps",
                        "content": """## Simple Definition
**Order Block**: Last opposing candle before significant move, representing institutional orders.
**Fair Value Gap**: Imbalance zone where price moved rapidly without filling orders.

## Concept Explanation
**Bullish Order Block**:
- Last bearish candle before aggressive bullish move
- Shows where institutions placed buy orders
- Price often returns to "mitigate" these orders

**Bearish Order Block**:
- Last bullish candle before aggressive bearish move
- Institutional sell zone

**Fair Value Gaps**:
- Three-candle pattern with no overlap between neighbors
- Price usually returns to fill gap before continuing

## Step-by-Step Breakdown
**Trading Order Blocks**:
1. Identify move creating structure break
2. Mark OB: Last opposing candle before move
3. Wait: Price returns to OB zone (mitigation)
4. Confirm: Reaction at OB (pin bar, engulfing)
5. Enter: In direction of original impulse
6. Stop: Beyond OB extreme

## Real Trading Example
**Bullish Order Block Trade**:
- Move: GBP/USD rallies 150 pips from 1.2500, breaking above high
- OB: Last red candle before rally: 1.2510-1.2530
- Wait: Price pulls back to 1.2520
- Confirm: Bullish engulfing at 1.2520
- Entry: Buy 1.2525
- Stop: 1.2490
- Target: 1.2650

## Common Beginner Mistake
**Trading Every OB**: Not all order blocks equal. Only trade OBs that preceded significant structure breaks on H4+.

## Key Takeaway
Order blocks show where smart money entered. FVGs show where price likely returns for "cleanup." Trade only with higher timeframe confirmation.

## Practice Question
What qualifies as valid Bullish Order Block?""",
                        "quiz": [
                            {"question": "Order Block is?", "option_a": "Any candle", "option_b": "Last opposing candle before significant move", "option_c": "Moving average", "option_d": "Random support", "correct_answer": "B", "explanation": "OB is last opposing candle before impulsive structure-breaking move.", "topic_slug": "market_structure"},
                            {"question": "Fair Value Gap represents?", "option_a": "Balanced market", "option_b": "Price imbalance likely to be filled", "option_c": "Trend continuation only", "option_d": "Low volatility", "correct_answer": "B", "explanation": "FVG is inefficiency market usually returns to fill.", "topic_slug": "market_structure"},
                            {"question": "OB high 1.2500, OB low 1.2480. Entry at 50% zone?", "option_a": "1.2490", "option_b": "1.2500", "option_c": "1.2480", "option_d": "1.2600", "correct_answer": "A", "explanation": "50% of 1.2480-1.2500 = 1.2490. Common entry point.", "topic_slug": "market_structure"},
                            {"question": "Price hits OB but immediately breaks through?", "option_a": "Hold position", "option_b": "OB failed, exit immediately", "option_c": "Double position", "option_d": "Move stop away", "correct_answer": "B", "explanation": "If price slices through OB without reaction, level invalid.", "topic_slug": "market_structure"},
                            {"question": "Trading OB on M5 without H4 context?", "option_a": "High probability", "option_b": "OB may be minor in larger trend", "option_c": "Guaranteed fills", "option_d": "Better spreads", "correct_answer": "B", "explanation": "Low timeframe OBs lack institutional significance.", "topic_slug": "market_structure"}
                        ]
                    }
                ]
            },
            {
                "title": "Liquidity and Institutional Trading",
                "description": "Stop hunts, liquidity pools, and smart money concepts.",
                "lessons": [
                    {
                        "title": "Liquidity Pools and Stop Hunts",
                        "content": """## Simple Definition
**Liquidity Pools**: Clusters of stop orders above/below key levels where institutions fill large positions.
**Stop Hunt**: Price briefly breaks level to trigger retail stops before reversing sharply.

## Concept Explanation
**Where is Liquidity?**
- Above Swing Highs: Retail buy stops and breakout traders
- Below Swing Lows: Retail sell stops
- Equal Highs/Lows: Concentrated orders
- Round Numbers: 1.1000, 1.2000

**Stop Hunt Pattern**:
1. Market approaches obvious level (previous high)
2. Retail place buy stop above high
3. Institutions push price slightly above, triggering stops
4. Institutions sell into liquidity (filling shorts)
5. Price collapses back below level

## Step-by-Step Breakdown
**Avoiding Stop Hunts**:
1. Identify liquidity: Mark obvious swing highs/lows
2. Expect hunt: Assume price takes stops before real move
3. Entry: Place entries 10-15 pips beyond obvious level
4. Stop placement: Don't place at obvious levels (1.1000, exact swing high)
5. Confirmation: Wait for return inside range after sweep

## Real Trading Example
**The Liquidity Grab**:
- Setup: EUR/USD double top at 1.1000
- Retail action: Buy stops at 1.1005
- Smart money: See cluster of stops
- Execution: Price spikes to 1.1010, institutions sell heavily
- Result: Collapses to 1.0950 in 2 hours
- Lesson: Place sell limits at 1.1010, not buy stops

<svg class="ac-svg-diagram" viewBox="0 0 400 200">
  <rect x="150" y="40" width="100" height="20" fill="rgba(167,139,250,0.3)" stroke="#a78bfa" rx="5"/>
  <text x="200" y="55" text-anchor="middle" fill="#a78bfa" font-size="12">Liquidity Pool</text>
  <line x1="200" y1="60" x2="200" y2="100" stroke="#60a5fa" stroke-width="2"/>
  <path d="M 50 150 L 150 100 L 200 100" fill="none" stroke="#22c55e" stroke-width="2"/>
  <path d="M 200 100 L 220 70 L 200 150" fill="none" stroke="#ef4444" stroke-width="3"/>
  <text x="230" y="70" fill="#ef4444" font-size="12">Stop Hunt</text>
  <text x="200" y="170" text-anchor="middle" fill="#ef4444" font-size="14">Sharp Reversal</text>
</svg>

## Common Beginner Mistake
**Obvious Stop Placement**: Placing stop exactly below swing low or at round number. Algorithms hunt these levels. Use buffer (ATR or 1.5x spread).

## Key Takeaway
Markets move to take liquidity. Before major reversals, price often takes obvious highs/lows. Don't place stops at obvious levels.

## Practice Question
Why do institutions push price above previous highs before reversing down?""",
                        "quiz": [
                            {"question": "Liquidity pools found?", "option_a": "Randomly", "option_b": "Above highs/below lows where stops cluster", "option_c": "Only at round numbers", "option_d": "Inside ranges", "correct_answer": "B", "explanation": "Liquidity concentrates above highs (buy stops) and below lows (sell stops).", "topic_slug": "liquidity"},
                            {"question": "Stop hunt purpose?", "option_a": "Help retail", "option_b": "Trigger stops so institutions fill orders", "option_c": "Break support permanently", "option_d": "Create volatility for fun", "correct_answer": "B", "explanation": "Institutions hunt stops to generate liquidity for large orders.", "topic_slug": "liquidity"},
                            {"question": "Where NOT to place stop losses?", "option_a": "Below swing low", "option_b": "At exact round numbers", "option_c": "Behind strong structure", "option_d": "Both A and B", "correct_answer": "D", "explanation": "Never at exact lows or round numbers—most hunted levels.", "topic_slug": "liquidity"},
                            {"question": "Price breaks above resistance, triggers your stop, then reverses sharply?", "option_a": "Bad luck", "option_b": "Stop hunt/liquidity grab", "option_c": "Trend continuation", "option_d": "Gap fill", "correct_answer": "B", "explanation": "Classic stop hunt—break above takes buy stops, then reverses.", "topic_slug": "liquidity"},
                            {"question": "Buy stop 5 pips above obvious resistance?", "option_a": "Perfect entry", "option_b": "Stop hunted immediately", "option_c": "Guaranteed breakout", "option_d": "Lower risk", "correct_answer": "B", "explanation": "Buy stops above obvious levels are liquidity targets.", "topic_slug": "liquidity"}
                        ]
                    },
                    {
                        "title": "Smart Money Concepts",
                        "content": """## Simple Definition
Smart Money refers to institutional traders whose large orders move markets. SMC involves reading their footprints: order blocks, liquidity grabs, accumulation/distribution.

## Concept Explanation
**Accumulation/Markup/Distribution/Markdown**:
- **Accumulation**: Smart money buying at lows (consolidation)
- **Markup**: Aggressive move up as retail FOMO joins
- **Distribution**: Smart money selling to retail at highs
- **Markdown**: Aggressive move down

**Displacement**: Large impulsive candle showing institutional order flow.
**Inducement**: Minor structure break designed to trap retail before major move opposite.

## Step-by-Step Breakdown
**Trading with Smart Money**:
1. Identify trend (external structure on H4/Daily)
2. Find OB in trend direction
3. Wait for inducement (counter-trend liquidity grab)
4. Displacement: Strong candle breaking internal structure
5. Entry: FVG or OB retest after displacement
6. Stop: Beyond inducement level

## Real Trading Example
**Smart Money Short Setup**:
- Trend: Daily bearish (lower lows)
- Inducement: Price rallies to take previous H1 high
- Displacement: Sharp H1 candle down breaking last H1 low
- OB: Bearish order block at top of inducement
- Entry: Retest of OB or FVG below displacement
- Stop: Above inducement high
- Target: Next liquidity pool

## Common Beginner Mistake
**Labeling Every Level as SMC**: Not every support is order block. SMC requires: displacement, structure break, mitigation.

## Key Takeaway
Trade with institutions, not against them. Wait for them to show hand via displacement. Don't fight inducement—wait for it to complete, then trade real move.

## Practice Question
What does "inducement" mean in SMC?""",
                        "quiz": [
                            {"question": "Inducement is?", "option_a": "Trend continuation", "option_b": "Minor structure break to trap retail before major move", "option_c": "Breakout pattern", "option_d": "MA cross", "correct_answer": "B", "explanation": "Inducement takes retail liquidity before smart money reverses price.", "topic_slug": "liquidity"},
                            {"question": "Displacement shows?", "option_a": "Low volatility", "option_b": "Institutional order flow (large candles)", "option_c": "Market close", "option_d": "Random noise", "correct_answer": "B", "explanation": "Displacement is large impulsive candle showing institutional participation.", "topic_slug": "liquidity"},
                            {"question": "Bullish OB fails and becomes resistance?", "option_a": "Order block", "option_b": "Breaker block", "option_c": "Fair value gap", "option_d": "Support", "correct_answer": "B", "explanation": "Breaker block is failed OB that flips to opposite role.", "topic_slug": "liquidity"},
                            {"question": "Price takes H1 high, then collapses breaking H1 low sharply?", "option_a": "Trend up", "option_b": "Inducement then displacement down", "option_c": "Accumulation", "option_d": "Random volatility", "correct_answer": "B", "explanation": "Taking highs (inducement) followed by strong move down (displacement).", "topic_slug": "liquidity"},
                            {"question": "Fighting displacement candles?", "option_a": "Catching bottom", "option_b": "Runaway losses against institutional flow", "option_c": "Guaranteed reversal", "option_d": "Better fills", "correct_answer": "B", "explanation": "Displacement shows institutional commitment. Counter-trading it loses.", "topic_slug": "liquidity"}
                        ]
                    }
                ]
            },
            {
                "title": "Advanced Risk Management",
                "description": "Portfolio risk, correlated pairs, drawdown management.",
                "lessons": [
                    {
                        "title": "Portfolio and Correlation Risk",
                        "content": """## Simple Definition
Portfolio risk considers total exposure across all trades, including correlations. Trading EUR/USD and GBP/USD simultaneously is nearly same trade due to 90%+ correlation.

## Concept Explanation
**Correlation Coefficient (-1 to +1)**:
- +0.9+: Pairs move together (EUR/USD & GBP/USD)
- -0.9+: Pairs move opposite (EUR/USD & USD/CHF)
- 0: No correlation

**Risk Implications**:
- Long EUR/USD + Long GBP/USD = 2x risk on same bet
- If correlation is +0.9, you're risking 1.9% instead of perceived 2%

**Basket Risk**:
- USD pairs: If long EUR/USD, GBP/USD, AUD/USD, you're massively short USD

## Step-by-Step Breakdown
**Calculating Portfolio Heat**:
1. List positions with directions
2. Check correlations (30-day matrix)
3. Adjust risk: If 2 pairs at 0.9 correlation with 1% each, actual risk ~1.9%
4. Limit exposure: Max 3% total portfolio risk across correlated positions
5. Hedge check: Are you accidentally neutral?

## Real Trading Example
**Correlation Disaster**:
- Trader: Long EUR/USD (1%), Long GBP/USD (1%), Long AUD/USD (1%), Long NZD/USD (1%)
- Perceived risk: 4%
- Actual risk: ~3.8% (all +0.85 correlated)
- Event: Fed hawkish policy, USD strengthens
- Result: All 4 lose simultaneously, -3.5% in 2 hours

<svg class="ac-svg-diagram" viewBox="0 0 400 150">
  <rect x="50" y="50" width="80" height="40" fill="rgba(34,197,94,0.3)" stroke="#22c55e" rx="5"/>
  <text x="90" y="75" text-anchor="middle" fill="#22c55e" font-size="10">EUR/USD Long</text>
  <rect x="150" y="50" width="80" height="40" fill="rgba(34,197,94,0.3)" stroke="#22c55e" rx="5"/>
  <text x="190" y="75" text-anchor="middle" fill="#22c55e" font-size="10">GBP/USD Long</text>
  <rect x="250" y="50" width="80" height="40" fill="rgba(34,197,94,0.3)" stroke="#22c55e" rx="5"/>
  <text x="290" y="75" text-anchor="middle" fill="#22c55e" font-size="10">AUD/USD Long</text>
  <text x="200" y="120" text-anchor="middle" fill="#ef4444" font-size="14">90% Correlated = 3x Risk on USD Weakness</text>
</svg>

## Common Beginner Mistake
**Diversification Illusion**: Opening 5 different pairs thinking diversified when 4 are USD pairs. When USD moves, all act as one large bet.

## Key Takeaway
Check correlation before adding positions. Max 2 high-correlation trades at reduced size. True diversification requires uncorrelated instruments.

## Practice Question
What happens to portfolio risk if you trade EUR/USD and GBP/USD long with 1% each?""",
                        "quiz": [
                            {"question": "EUR/USD and GBP/USD correlation?", "option_a": "-0.9", "option_b": "0", "option_c": "+0.9", "option_d": "Random", "correct_answer": "C", "explanation": "EUR/USD and GBP/USD move together ~90% due to European ties and USD component.", "topic_slug": "advanced_risk"},
                            {"question": "Trading 3 correlated pairs at 1% risk each equals?", "option_a": "1%", "option_b": "2%", "option_c": "3%", "option_d": "0.5%", "correct_answer": "C", "explanation": "High correlation means positions move together. Risk approaches sum.", "topic_slug": "advanced_risk"},
                            {"question": "Which pairs move opposite to EUR/USD?", "option_a": "GBP/USD", "option_b": "USD/CHF", "option_c": "AUD/USD", "option_d": "EUR/GBP", "correct_answer": "B", "explanation": "USD/CHF moves inverse to EUR/USD ~90% (USD base vs quote).", "topic_slug": "advanced_risk"},
                            {"question": "Long EUR/USD and Short USD/CHF simultaneously?", "option_a": "Diversified", "option_b": "Nearly same trade twice", "option_c": "Hedged", "option_d": "Risk-free", "correct_answer": "B", "explanation": "Both are anti-USD bets. Same directional exposure.", "topic_slug": "advanced_risk"},
                            {"question": "5 positions all USD-pairs same direction during NFP?", "option_a": "Diversified safety", "option_b": "Concentrated explosion risk", "option_c": "Guaranteed profit", "option_d": "No correlation", "correct_answer": "B", "explanation": "USD events affect all USD pairs simultaneously. Compounded risk.", "topic_slug": "advanced_risk"}
                        ]
                    },
                    {
                        "title": "Drawdown Recovery and Psychology",
                        "content": """## Simple Definition
Drawdown is peak-to-trough decline in account. Recovery is mathematical and psychological process of returning to breakeven. 50% drawdown requires 100% gain to recover.

## Concept Explanation
**Drawdown Mathematics**:
- 10% Loss: Requires 11% gain
- 20% Loss: Requires 25% gain
- 50% Loss: Requires 100% gain
- 80% Loss: Requires 400% gain (nearly impossible)

**Recovery Rules**:
- Never increase risk to "make it back faster"
- Reduce size 50% during recovery
- Focus on process, not P&L
- Return to breakeven on reduced size before scaling up

## Step-by-Step Breakdown
**Surviving Drawdowns**:
1. Accept: Drawdowns are inevitable
2. Analyze: Normal variance or broken edge?
3. Adjust: Reduce risk 50% until 3 consecutive wins
4. Review: Journal emotional vs mechanical decisions
5. Resume: Only return to normal size after new equity high

## Real Trading Example
**The Recovery Trap**:
- Trader: Down 25% ($7,500 from $10,000)
- Mistake: Increases risk to 4% to "recover faster"
- Result: Next 3 losses = -12% additional ($900 remaining)
- Mathematical reality: Now needs 1000%+ gain (impossible)
- Proper approach: Reduce to 0.5% risk, accept 150 trades to recover

<svg class="ac-svg-diagram" viewBox="0 0 400 200">
  <line x1="50" y1="180" x2="350" y2="180" stroke="#9ca3af" stroke-width="1"/>
  <text x="200" y="195" text-anchor="middle" fill="#9ca3af" font-size="12">Starting Equity</text>
  <line x1="50" y1="180" x2="200" y2="120" stroke="#ef4444" stroke-width="2"/>
  <text x="125" y="140" fill="#ef4444" font-size="12">50% Drawdown</text>
  <path d="M 200 120 Q 250 120 350 60" fill="none" stroke="#22c55e" stroke-width="2" stroke-dasharray="5,5"/>
  <text x="275" y="90" fill="#22c55e" font-size="12">Requires 100% Gain</text>
  <text x="200" y="40" text-anchor="middle" fill="#fbbf24" font-size="14">Recovery is Exponentially Harder</text>
</svg>

## Common Beginner Mistake
**Revenge Trading**: After 3 losses, doubling position size on "sure thing" to recover. Emotional decision-making creates catastrophic drawdowns.

## Key Takeaway
Preserve capital at all costs. 20% drawdown requires 25% gain—difficult but doable. 50% requires doubling—nearly impossible under pressure. Never risk >2%, never increase size in drawdown.

## Practice Question
If account drops 50%, what percentage gain required to breakeven?""",
                        "quiz": [
                            {"question": "10% drawdown requires what gain?", "option_a": "10%", "option_b": "11%", "option_c": "20%", "option_d": "5%", "correct_answer": "B", "explanation": "After 10% loss, you have 90% left. Need 11% of that to recover.", "topic_slug": "advanced_risk"},
                            {"question": "50% drawdown requires what gain?", "option_a": "50%", "option_b": "75%", "option_c": "100%", "option_d": "25%", "correct_answer": "C", "explanation": "50% drawdown leaves half account. Need 100% gain on remaining half.", "topic_slug": "advanced_risk"},
                            {"question": "During drawdown, proper action?", "option_a": "Increase size to recover", "option_b": "Reduce size 50%, focus on process", "option_c": "Trade more pairs", "option_d": "Remove stops", "correct_answer": "B", "explanation": "Reduce risk during drawdown. Focus on execution quality.", "topic_slug": "advanced_risk"},
                            {"question": "Down 20%, next trade looks perfect?", "option_a": "Triple size to recover", "option_b": "Trade normal or reduced size", "option_c": "Skip trade", "option_d": "Use max leverage", "correct_answer": "B", "explanation": "Never increase size in drawdown. Trade normal until consistent.", "topic_slug": "advanced_risk"},
                            {"question": "Checking P&L every 5 minutes during drawdown?", "option_a": "Better decisions", "option_b": "Emotional trading, revenge trades", "option_c": "Faster recovery", "option_d": "No effect", "correct_answer": "B", "explanation": "Obsessing over P&L creates pressure leading to revenge trading.", "topic_slug": "advanced_risk"}
                        ]
                    }
                ]
            },
            {
                "title": "Trading Psychology",
                "description": "Emotional control, discipline, and process thinking.",
                "lessons": [
                    {
                        "title": "The Psychology of Winning and Losing",
                        "content": """## Simple Definition
Trading is 80% psychology, 20% strategy. Ability to execute consistently under stress distinguishes professionals from amateurs.

## Concept Explanation
**Loss Aversion**:
- Losses feel 2.5x stronger than equivalent gains
- Causes holding losers too long and cutting winners early
- Solution: Pre-define exits, focus on process over outcome

**Overconfidence Bias**:
- After 3 wins, traders increase size and deviate from rules
- Solution: Maintain consistent risk regardless of recent performance

**Recency Bias**:
- Placing too much weight on recent trades vs long-term stats
- Solution: Trade probabilities, not feelings

## Step-by-Step Breakdown
**Mental State Management**:
1. Pre-trading routine: Review rules, check calendar
2. During trade: Focus on execution quality, not P&L
3. Post-trade review: Log emotions with trade data
4. Breaks: Mandatory 24-hour break after 3 consecutive losses
5. Peak performance: Trade only when rested and sharp

## Real Trading Example
**The Tilt Spiral**:
- 08:00: Loses trade 1 (-1%), annoyed
- 08:30: Takes sub-par setup to "make it back" (revenge trade)
- 09:00: Loses trade 2 (-2%), anger increases
- 09:15: Removes stop on trade 3 "to give it room"
- 10:00: Trade 3 hits -8% (blow up)
- Analysis: 3R loss became 8R disaster due to emotion

<svg class="ac-svg-diagram" viewBox="0 0 400 150">
  <text x="200" y="30" text-anchor="middle" fill="#ef4444" font-size="16">The Emotional Spiral</text>
  <circle cx="80" cy="100" r="30" fill="rgba(245,158,11,0.3)" stroke="#f59e0b"/>
  <text x="80" y="105" text-anchor="middle" fill="#f59e0b" font-size="10">Loss 1</text>
  <text x="80" y="145" text-anchor="middle" fill="#9ca3af" font-size="10">Annoyed</text>
  <line x1="110" y1="100" x2="150" y2="100" stroke="#60a5fa" stroke-width="2"/>
  <circle cx="180" cy="100" r="30" fill="rgba(245,158,11,0.5)" stroke="#f59e0b"/>
  <text x="180" y="105" text-anchor="middle" fill="#f59e0b" font-size="10">Loss 2</text>
  <text x="180" y="145" text-anchor="middle" fill="#9ca3af" font-size="10">Angry</text>
  <line x1="210" y1="100" x2="250" y2="100" stroke="#60a5fa" stroke-width="2"/>
  <circle cx="320" cy="100" r="50" fill="rgba(239,68,68,0.3)" stroke="#ef4444"/>
  <text x="320" y="105" text-anchor="middle" fill="#ef4444" font-size="12">BLOW UP</text>
  <text x="320" y="165" text-anchor="middle" fill="#ef4444" font-size="10">Rage/Despair</text>
</svg>

## Common Beginner Mistake
**Outcome Attachment**: Defining self-worth by daily P&L. Two winning days = "I'm genius." Two losing days = "I'm terrible." This volatility destroys consistency.

## Key Takeaway
Separate identity from trading results. You are not your P&L. Focus on process execution. Outcome of single trade is random; edge appears over 100 trades.

## Practice Question
What is "loss aversion" and how does it affect trading?""",
                        "quiz": [
                            {"question": "Loss aversion causes traders to?", "option_a": "Take profits quickly, hold losers", "option_b": "Trade perfectly", "option_c": "Avoid all risk", "option_d": "Increase size after wins", "correct_answer": "A", "explanation": "Losses feel 2.5x worse, causing premature profit-taking and reluctant loss realization.", "topic_slug": "psychology"},
                            {"question": "After 3 consecutive wins, traders become?", "option_a": "More careful", "option_b": "Overconfident, increase size", "option_c": "Stop trading", "option_d": "Less emotional", "correct_answer": "B", "explanation": "Recency bias leads to size increases and rule deviation after wins.", "topic_slug": "psychology"},
                            {"question": "Best practice after 3 consecutive losses?", "option_a": "Trade larger to recover", "option_b": "Mandatory 24-hour break", "option_c": "Trade different pairs", "option_d": "Remove stops", "correct_answer": "B", "explanation": "3 losses indicate emotional involvement. Break prevents tilt spiral.", "topic_slug": "psychology"},
                            {"question": "Up 5% this week. Proper action?", "option_a": "Increase size", "option_b": "Maintain consistent risk, withdraw profits", "option_c": "Trade more hours", "option_d": "Risk all profit on one trade", "correct_answer": "B", "explanation": "Maintain consistency. Withdraw profits periodically.", "topic_slug": "psychology"},
                            {"question": "Defining self-worth by daily P&L?", "option_a": "Consistent performance", "option_b": "Emotional volatility, inconsistent execution", "option_c": "Better focus", "option_d": "Higher profits", "correct_answer": "B", "explanation": "Attaching identity to results creates swings that destroy execution.", "topic_slug": "psychology"}
                        ]
                    },
                    {
                        "title": "Building Mental Toughness",
                        "content": """## Simple Definition
Mental toughness is maintaining strategic discipline under financial and emotional pressure. Developed through deliberate practice, routine, and acceptance of variance.

## Concept Explanation
**Performance Arc**:
- Amateur: Results dictate emotions → emotions dictate next trade
- Professional: Process dictates action → results accumulate over time

**Acceptance of Variance**:
- Even 60% win rate means 40% losses
- 40% win rate with 1:2 R:R is profitable
- "Right" trades lose often; "wrong" trades win sometimes
- Focus on decision quality, not outcome

**Routine Architecture**:
- Pre-market: 30 minutes analysis without trading
- Trading hours: Maximum 4 hours (fatigue management)
- Post-market: Journal, review, exercise
- Weekend: Strategy review, no live trading

## Step-by-Step Breakdown
**Developing Discipline**:
1. Mechanical execution: Follow strategy exactly for 100 trades
2. Emotion labeling: "I'm feeling FOMO" (recognizing reduces power)
3. Small commitments: Win morning routine, win trading day
4. Identity shift: "I am professional who follows process"

## Real Trading Example
**Professional vs Amateur Execution**:
- Setup: GBP/USD bullish pin bar at support
- Amateur: Market buy at 1.2550, stop 1.2520
- Professional: Limit buy at 1.2545, stop 1.2515 (5 pips better)
- Difference: 5 pips better entry = $50/lot savings over 1000 trades

## Common Beginner Mistake
**System Hopping**: Abandoning strategy after 5 losses because "it doesn't work." No strategy works every week. Edge appears over series of trades.

## Key Takeaway
Mental toughness isn't eliminating emotions—it's executing despite them. Build routines removing decision fatigue. Accept 40% of trades lose even when executed perfectly.

## Practice Question
Why do professionals focus on process rather than individual outcomes?""",
                        "quiz": [
                            {"question": "Mental toughness means?", "option_a": "Having no emotions", "option_b": "Executing strategy despite emotions", "option_c": "Winning every trade", "option_d": "Avoiding losses", "correct_answer": "B", "explanation": "Mental toughness is following process when feeling fear or greed.", "topic_slug": "psychology"},
                            {"question": "40% win rate, 1:2 R:R. Expectancy per 10 trades?", "option_a": "Loss", "option_b": "Break even", "option_c": "Profit (+2R)", "option_d": "Cannot calculate", "correct_answer": "C", "explanation": "(4×2R) - (6×1R) = 8R - 6R = +2R profit per 10 trades.", "topic_slug": "psychology"},
                            {"question": "Best pre-trading routine includes?", "option_a": "Social media", "option_b": "30 minutes analysis, breathing", "option_c": "Trading immediately", "option_d": "Large coffee only", "correct_answer": "B", "explanation": "Preparation and calm state reduce emotional errors.", "topic_slug": "psychology"},
                            {"question": "Perfect setup but fearful after 2 losses?", "option_a": "Skip trade", "option_b": "Take trade with reduced size", "option_c": "Trade double size", "option_d": "Change strategy", "correct_answer": "B", "explanation": "Fear is data, not directive. Reduce size to manage emotion.", "topic_slug": "psychology"},
                            {"question": "Changing strategy after 5 losses?", "option_a": "Strategy improvement", "option_b": "No statistical significance", "option_c": "Better results", "option_d": "Lower risk", "correct_answer": "B", "explanation": "5 trades is variance. Changing constantly prevents mastery.", "topic_slug": "psychology"}
                        ]
                    }
                ]
            },
            {
                "title": "Strategy Development",
                "description": "Backtesting, forward testing, and edge calculation.",
                "lessons": [
                    {
                        "title": "Advanced Backtesting Methods",
                        "content": """## Simple Definition
Systematic backtesting tests strategy over multiple market conditions (trending, ranging, high/low volatility) with walk-forward analysis to prevent curve-fitting.

## Concept Explanation
**Walk-Forward Analysis**:
1. Optimize on period A (2020-2022)
2. Test on "unseen" period B (2022-2024) without changes
3. If period B profitable, strategy has real edge
4. If period B fails, strategy optimized for noise

**Market Regimes**:
- Trending: ADR > 100 pips
- Ranging: ADR < 60 pips
- Volatile: Expansion in ATR

**Robustness Tests**:
- Works on multiple pairs?
- Parameter change from 20 to 25 EMA destroy results?
- Survives spread widening by 2 pips?

## Step-by-Step Breakdown
**Professional Backtest**:
1. Data: 5+ years tick data, include spreads
2. In-sample: Optimize on 60% of data
3. Out-of-sample: Validate on remaining 40%
4. Monte Carlo: Randomize trade sequence 1000x
5. Sensitivity: Change parameters ±20%, results remain profitable?

## Real Trading Example
**Robust vs Curve-Fitted**:
- Curve-fitted: RSI(14), MA(20), MACD on EUR/USD only, 2023
- Result: 90% win rate backtest, 35% forward (failed)
- Robust: Pin bar at support/resistance, 2:1 R:R, any major pair
- Result: 48% win rate consistently across 5 pairs, 5 years

## Common Beginner Mistake
**Optimization Bias**: Adding filters until backtest shows 80%+ win rate. Creates "perfect" historical performance that fails on new data.

## Key Takeaway
Simple strategies with slight edge, executed consistently, outperform complex optimized systems. If strategy breaks when changing EMA from 20 to 21, it's not robust.

## Practice Question
What is walk-forward analysis and why critical?""",
                        "quiz": [
                            {"question": "Walk-forward analysis tests?", "option_a": "Past data only", "option_b": "Strategy on unseen data after optimization", "option_c": "Demo trading", "option_d": "Spreads only", "correct_answer": "B", "explanation": "Optimize on one period, test on different period to verify edge.", "topic_slug": "strategy_dev"},
                            {"question": "Curve-fitting means?", "option_a": "Perfect fit to future", "option_b": "Over-optimized to historical noise", "option_c": "Robust design", "option_d": "Risk management", "correct_answer": "B", "explanation": "Curve-fitting creates false excellence by fitting randomness.", "topic_slug": "strategy_dev"},
                            {"question": "Robust strategy survives?", "option_a": "Parameter changes", "option_b": "Different pairs", "option_c": "Spread variations", "option_d": "All of above", "correct_answer": "D", "explanation": "True edge persists across variations and conditions.", "topic_slug": "strategy_dev"},
                            {"question": "Works on EUR/USD but fails on GBP/USD?", "option_a": "GBP random", "option_b": "Curve-fitted to EUR specifics", "option_c": "Different timezones", "option_d": "Better on EUR", "correct_answer": "B", "explanation": "Robust edges work across similar instruments.", "topic_slug": "strategy_dev"},
                            {"question": "Optimizing until 90% win rate?", "option_a": "Future success", "option_b": "Curve-fitted, fails on new data", "option_c": "Guaranteed profits", "option_d": "Lower drawdown", "correct_answer": "B", "explanation": "90% win rates usually mean fitting to historical quirks.", "topic_slug": "strategy_dev"}
                        ]
                    },
                    {
                        "title": "Edge and Expectancy",
                        "content": """## Simple Definition
**Edge**: Mathematical advantage strategy has over random chance.
**Expectancy**: Quantifies edge per trade: (Win% × AvgWin) - (Loss% × AvgLoss).

## Concept Explanation
**Calculating Edge**:
- Win Rate: 45%
- Average Win: 2.2R
- Average Loss: 1.0R
- Expectancy: (0.45 × 2.2) - (0.55 × 1.0) = +0.44R per trade

**Law of Large Numbers**:
- Edge appears over 100+ trades
- 10 trades = variance dominates
- 100 trades = edge emerging
- 1000 trades = deterministic results

**R-Multiple Thinking**:
- Measure outcomes in units of risk (R), not dollars
- +2R win = twice risked amount
- Allows comparison across trade sizes

## Step-by-Step Breakdown
**Verifying Edge**:
1. Record: Minimum 100 live or forward-test trades
2. Calculate: Win rate and average R-multiple
3. Expectancy: Must be > 0.2R per trade
4. Distribution: Check for fat tails (rare huge losses)
5. Consecutive losses: Prepare mentally for worst streak

## Real Trading Example
**Edge Reality**:
- Strategy: Support/Resistance bounces, 1:2 R:R minimum
- Backtest: 500 trades, 42% win, +1.8R avg win, -1R avg loss
- Expectancy: (0.42×1.8) - (0.58×1) = +0.176R
- Monthly: 20 trades × 0.176R = +3.5R per month
- Capital: $10k, 1% risk ($100), 3.5R = $350/month (3.5%)

<svg class="ac-svg-diagram" viewBox="0 0 400 120">
  <rect x="50" y="30" width="300" height="60" fill="rgba(34,197,94,0.2)" stroke="#22c55e" rx="5"/>
  <text x="200" y="55" text-anchor="middle" fill="#22c55e" font-size="14">Expectancy = (Win% × AvgWin) - (Loss% × AvgLoss)</text>
  <text x="200" y="80" text-anchor="middle" fill="#9ca3af" font-size="12">Example: (40% × 2R) - (60% × 1R) = +0.2R per trade</text>
</svg>

## Common Beginner Mistake
**Win Rate Obsession**: Believing 70% win rate necessary. 40% win rate with 1:3 R:R is highly profitable (+0.6R expectancy).

## Key Takeaway
Trading is probability business, not prediction. 40% win rate with proper R:R outperforms 60% with poor R:R. Calculate expectancy, trust math, execute 1000 times.

## Practice Question
Strategy wins 35% with avg win 3R and avg loss 1R. Expectancy?""",
                        "quiz": [
                            {"question": "Expectancy formula?", "option_a": "Win% + Loss%", "option_b": "(Win% × AvgWin) - (Loss% × AvgLoss)", "option_c": "Total profit only", "option_d": "Random", "correct_answer": "B", "explanation": "Expectancy = (Prob Win × Avg Win) - (Prob Loss × Avg Loss).", "topic_slug": "strategy_dev"},
                            {"question": "Calculate: 35% win, 3R avg win, 1R avg loss?", "option_a": "0", "option_b": "0.05R", "option_c": "+0.40R", "option_d": "+0.5R", "correct_answer": "C", "explanation": "(0.35×3) - (0.65×1) = 1.05 - 0.65 = +0.40R per trade.", "topic_slug": "strategy_dev"},
                            {"question": "More important for profitability?", "option_a": "High win rate only", "option_b": "Positive expectancy", "option_c": "Number of trades", "option_d": "Low win rate", "correct_answer": "B", "explanation": "Positive expectancy (win rate + R:R combination) determines profitability.", "topic_slug": "strategy_dev"},
                            {"question": "60% win rate, 0.8R avg win, 1R avg loss?", "option_a": "+0.28R", "option_b": "0", "option_c": "-0.08R (losing)", "option_d": "+1R", "correct_answer": "C", "explanation": "(0.6×0.8) - (0.4×1) = 0.48 - 0.40 = -0.08R. Losing despite 60% wins!", "topic_slug": "strategy_dev"},
                            {"question": "Focusing only on win rate, ignoring R:R?", "option_a": "Profitable system", "option_b": "High win rate but negative expectancy", "option_c": "Better psychology", "option_d": "Lower drawdown", "correct_answer": "B", "explanation": "Many high win-rate systems have poor R:R, creating negative expectancy.", "topic_slug": "strategy_dev"}
                        ]
                    }
                ]
            },
            {
                "title": "Building a Complete Trading System",
                "description": "Combining all elements into a professional plan.",
                "lessons": [
                    {
                        "title": "System Integration",
                        "content": """## Simple Definition
Trading system integrates strategy (entries/exits), risk management (sizing, drawdown limits), psychology (emotional controls), and routine (execution consistency) into repeatable business model.

## Concept Explanation
**Trading Business Plan**:
1. Operations: When, what, how long to trade
2. Strategy: Specific entry/exit rules with backtested edge
3. Risk Protocols: Max risk per trade, day, week, drawdown halt
4. Capital Allocation: Percentage of total wealth as risk capital
5. Review Cycles: Weekly performance, monthly strategy audit
6. Infrastructure: Platform, data feeds, backup

**Redundancy**:
- Two brokers (if one fails)
- Cloud-based journaling
- Pre-written contingency plans

**Scalability**:
- System works with $1k or $100k (just add zeros)
- Can you execute 10x size without emotional breakdown?

## Step-by-Step Breakdown
**System Checklist**:
- [ ] Strategy positive expectancy over 100+ trades
- [ ] Risk per trade capped at 2%
- [ ] Maximum 6% daily loss limit (halt)
- [ ] Maximum 12% monthly drawdown (break)
- [ ] Pre-market routine defined
- [ ] Trade journal with screenshots
- [ ] Weekly review process
- [ ] Broker funds segregated

## Real Trading Example
**Professional System**:
- Capital: $50,000 (2% of net worth)
- Strategy: SMC (OB + FVG) on EUR/USD, GBP/USD
- Risk: 1% per trade ($500), max 3/day
- Schedule: London/NY overlap only
- Daily limit: -3% ($1,500) = stop
- Review: Sunday backtest review, Wednesday check
- Growth: After 3 profitable months, increase 25%

<svg class="ac-svg-diagram" viewBox="0 0 400 200">
  <rect x="50" y="50" width="100" height="100" fill="rgba(96,165,250,0.3)" stroke="#60a5fa" rx="5"/>
  <text x="100" y="105" text-anchor="middle" fill="#60a5fa" font-size="12">Strategy</text>
  <rect x="170" y="50" width="100" height="100" fill="rgba(245,158,11,0.3)" stroke="#f59e0b" rx="5"/>
  <text x="220" y="105" text-anchor="middle" fill="#f59e0b" font-size="12">Risk Mgmt</text>
  <rect x="290" y="50" width="100" height="100" fill="rgba(34,197,94,0.3)" stroke="#22c55e" rx="5"/>
  <text x="340" y="105" text-anchor="middle" fill="#22c55e" font-size="12">Psychology</text>
  <text x="200" y="180" text-anchor="middle" fill="#fbbf24" font-size="16">INTEGRATED SYSTEM</text>
</svg>

## Common Beginner Mistake
**Incomplete System**: Having entry rules but no daily loss limits. Strategy works but trader loses account to tilt.

## Key Takeaway
Treat trading as business, not hobby. Businesses have operating procedures, risk management, quality control. Your system is your franchise—document it, follow it, refine it.

## Practice Question
Purpose of maximum daily loss limit in trading system?""",
                        "quiz": [
                            {"question": "Trading system includes?", "option_a": "Only entries", "option_b": "Strategy, risk, psychology, routine", "option_c": "Only indicators", "option_d": "Only capital", "correct_answer": "B", "explanation": "Complete systems integrate all elements.", "topic_slug": "system"},
                            {"question": "Daily loss limit purpose?", "option_a": "Make back losses faster", "option_b": "Prevent tilt spiral and large drawdowns", "option_c": "Increase size", "option_d": "Guarantee profits", "correct_answer": "B", "explanation": "Daily limits halt trading before emotional decisions.", "topic_slug": "system"},
                            {"question": "Scalability means system works?", "option_a": "Only with large accounts", "option_b": "With any account size proportionally", "option_c": "Only in bull markets", "option_d": "Only once", "correct_answer": "B", "explanation": "True systems scale—same rules, different dollar amounts.", "topic_slug": "system"},
                            {"question": "Strategy profitable but no daily limit?", "option_a": "Safe trading", "option_b": "Single bad day can destroy months", "option_c": "Better performance", "option_d": "Lower risk", "correct_answer": "B", "explanation": "Without daily limits, tilt sessions erase weeks of profits.", "topic_slug": "system"},
                            {"question": "Trading without written business plan?", "option_a": "Consistency", "option_b": "Inconsistent execution, no improvement", "option_c": "Higher profits", "option_d": "Better focus", "correct_answer": "B", "explanation": "Without documented system, cannot identify failures or measure improvement.", "topic_slug": "system"}
                        ]
                    },
                    {
                        "title": "Professional Execution Plan",
                        "content": """## Simple Definition
Execution excellence is bridge between strategy theory and realized profits. Involves precise order placement, timing optimization, and post-trade analysis.

## Concept Explanation
**Order Types**:
- Limit Orders: Your price or better (avoids spread)
- Stop Orders: Market order when price reached (guaranteed fill, slippage risk)
- Stop-Limit: Hybrid

**Execution Timing**:
- Avoid: First 5 minutes of session (wide spreads)
- Avoid: High-impact news releases (unless news strategy)
- Optimal: 15-30 minutes after session open
- Avoid: Friday after 4 PM EST (weekend gap risk)

**Trade Management**:
- Scale Out: Close 50% at 1R, 25% at 2R, 25% runner
- Breakeven Stops: Move to entry after 1R profit
- Time Stops: Exit if not working within expected timeframe

**Review Framework**:
- Immediate: Log trade within 5 minutes
- End of Day: Review all trades, patterns
- Weekend: Statistical analysis
- Monthly: Equity curve analysis

## Step-by-Step Breakdown
**Execution Checklist**:
1. Pre-trade: Check correlation with existing positions
2. Entry: Limit order at technical level
3. Stop: Set immediately
4. Target: Pre-set or manual at level
5. Management: Scale out per plan
6. Post-trade: Screenshot, log R-multiple, emotion

## Real Trading Example
**Professional vs Amateur**:
- Setup: GBP/USD bullish pin bar at support
- Amateur: Market buy at 1.2550, stop 1.2520
- Professional: Limit buy at 1.2545, stop 1.2515
- Difference: 5 pips better entry = $50/lot over 1000 trades

## Common Beginner Mistake
**Market Orders**: Always using market orders creates slippage (2-5 pips/trade). On 1000 trades/year, 3-pip slippage = 3000 pips lost—often difference between profit and loss.

## Key Takeaway
Edge is thin. Execution excellence preserves that edge. Use limit orders, manage with scale-out techniques, review every trade. Trading is business of basis points—optimize every component.

## Practice Question
Why use limit orders instead of market orders for entries?""",
                        "quiz": [
                            {"question": "Limit orders vs market orders?", "option_a": "Market always better", "option_b": "Limit orders avoid spread costs, better fills", "option_c": "No difference", "option_d": "Limit slower", "correct_answer": "B", "explanation": "Limit orders at your price avoid spread markup and often get better fills.", "topic_slug": "system"},
                            {"question": "Scale out technique means?", "option_a": "All or nothing exit", "option_b": "Closing partial positions at different targets", "option_c": "Adding to losers", "option_d": "Removing stops", "correct_answer": "B", "explanation": "Scale out: 50% at 1R, 25% at 2R, 25% runner.", "topic_slug": "system"},
                            {"question": "Best time to avoid trading?", "option_a": "London open", "option_b": "NFP release", "option_c": "NY overlap", "option_d": "Tuesday afternoon", "correct_answer": "B", "explanation": "High impact news creates spread widening and slippage.", "topic_slug": "system"},
                            {"question": "Up 1R on trade. Stop placement?", "option_a": "Original stop", "option_b": "Move to breakeven", "option_c": "Remove stop", "option_d": "Tighten to 0.5R", "correct_answer": "B", "explanation": "At 1R profit, move stop to entry for risk-free trade.", "topic_slug": "system"},
                            {"question": "Not logging trades immediately?", "option_a": "Better memory", "option_b": "Forgotten details, missed improvement", "option_c": "Faster trading", "option_d": "Lower stress", "correct_answer": "B", "explanation": "Delaying journaling leads to forgotten emotions and errors.", "topic_slug": "system"}
                        ]
                    }
                ]
            }
        ]
    }
]
