"""
Pipways Trading Academy — Curriculum Seed Data
Contains the complete 36-lesson curriculum (3 Levels, 6 Modules per Level, 2 Lessons per Module)
Format: Hierarchical JSON structure for ACADEMY_CURRICULUM
Each lesson includes: 400-700 word content, SVG diagrams, TradingView widgets, and 5 quiz questions
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
Unlike stock markets that have centralized exchanges, Forex is decentralized. It operates 24 hours a day, 5 days a week, across major financial centers: Sydney, Tokyo, London, and New York. When one market closes, another opens, creating continuous trading opportunities.

## Step-by-Step Breakdown
1. **Currency Pairs**: Forex trades in pairs (EUR/USD). The first currency is the "base," the second is the "quote."
2. **Price Movement**: If EUR/USD moves from 1.0850 to 1.0860, the Euro strengthened against the Dollar by 10 pips.
3. **Profit Mechanism**: Buy low, sell high (or sell high, buy low for short positions).
4. **Leverage**: Control large positions with small capital (e.g., 1:100 leverage means $1,000 controls $100,000).

## Real Trading Example
**Scenario**: You analyze EUR/USD and expect the Euro to strengthen.
- **Entry**: Buy at 1.0850
- **Position Size**: 0.1 lots ($1 per pip)
- **Stop Loss**: 1.0830 (20 pips risk = $20)
- **Take Profit**: 1.0890 (40 pips reward = $40)
- **Risk:Reward Ratio**: 1:2

<div class="ac-tradingview-widget" data-symbol="FX:EURUSD"></div>

## Common Beginner Mistake
**Overtrading**: New traders think more trades = more profit. Reality: Quality over quantity. Taking 3 high-probability setups beats taking 20 random trades.

## Key Takeaway
Forex trading is about probability and risk management, not prediction. Your edge comes from managing losses and letting winners run.

## Practice Question
If EUR/USD rises from 1.0500 to 1.0550, how many pips did it move?""",
                        "quiz": [
                            {
                                "question": "What does EUR/USD represent?",
                                "option_a": "Euros per US Dollar",
                                "option_b": "US Dollars per Euro",
                                "option_c": "Exchange rate index",
                                "option_d": "Stock price",
                                "correct_answer": "B",
                                "explanation": "EUR/USD shows how many USD one Euro buys. If 1.0850, 1 EUR = 1.0850 USD.",
                                "topic_slug": "forex_basics"
                            },
                            {
                                "question": "What is a pip in most currency pairs?",
                                "option_a": "0.01",
                                "option_b": "0.001",
                                "option_c": "0.0001",
                                "option_d": "1.0",
                                "correct_answer": "C",
                                "explanation": "For most pairs, 1 pip = 0.0001 (4th decimal). For JPY pairs, it's 0.01.",
                                "topic_slug": "forex_basics"
                            },
                            {
                                "question": "Calculate: EUR/USD moves from 1.0500 to 1.0550. How many pips?",
                                "option_a": "5 pips",
                                "option_b": "50 pips",
                                "option_c": "500 pips",
                                "option_d": "0.5 pips",
                                "correct_answer": "B",
                                "explanation": "1.0550 - 1.0500 = 0.0050 = 50 pips (0.0001 × 50 = 0.0050).",
                                "topic_slug": "forex_basics"
                            },
                            {
                                "question": "Scenario: You buy EUR/USD at 1.0850 with $100 risk. Price drops to 1.0800. What happened?",
                                "option_a": "Made $50 profit",
                                "option_b": "Lost $500",
                                "option_c": "Lost $50",
                                "option_d": "Broke even",
                                "correct_answer": "C",
                                "explanation": "1.0850 to 1.0800 = 50 pips. At $1/pip (0.1 lots), 50 pips = $50 loss.",
                                "topic_slug": "forex_basics"
                            },
                            {
                                "question": "Common mistake: New trader uses 1:500 leverage on first trade. What's the risk?",
                                "option_a": "Lower risk",
                                "option_b": "Normal risk",
                                "option_c": "Extreme risk of quick loss",
                                "option_d": "Guaranteed profit",
                                "correct_answer": "C",
                                "explanation": "High leverage amplifies losses. A 0.2% move against you wipes out the account.",
                                "topic_slug": "forex_basics"
                            }
                        ]
                    },
                    {
                        "title": "Who Trades Forex and Why?",
                        "content": """## Simple Definition
Forex participants range from central banks to individual retail traders, each with different goals and market impact.

## Concept Explanation
**Market Hierarchy**:
1. **Tier 1**: Central Banks and Major Commercial Banks (JP Morgan, Deutsche Bank) — 50%+ of volume
2. **Tier 2**: Hedge Funds, Corporations, Investment Managers — 40% of volume  
3. **Tier 3**: Retail Traders (you and me) — less than 10% of volume

## Step-by-Step Breakdown
1. **Central Banks**: Control monetary policy, interest rates, and currency supply. Their decisions create the biggest moves.
2. **Commercial Banks**: Facilitate international business transactions and speculative trading.
3. **Corporations**: Apple, Toyota, etc., convert foreign earnings back to home currency.
4. **Retail Traders**: Speculate on price movements for profit.

## Real Trading Example
**The SNB Shock (2015)**: Swiss National Bank removed the EUR/CHF peg without warning. The franc surged 30% in minutes. Retail traders with stop losses below 1.20 were wiped out. Lesson: Even "safe" trades can fail catastrophically—always use proper position sizing.

<svg class="ac-svg-diagram" viewBox="0 0 400 200">
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#60a5fa"/>
    </marker>
  </defs>
  <rect x="50" y="20" width="300" height="40" fill="rgba(245,158,11,0.2)" stroke="#f59e0b" rx="5"/>
  <text x="200" y="45" text-anchor="middle" fill="#f59e0b" font-size="14">Central Banks (Biggest Impact)</text>
  <line x1="200" y1="60" x2="200" y2="80" stroke="#60a5fa" stroke-width="2" marker-end="url(#arrowhead)"/>
  
  <rect x="50" y="80" width="300" height="40" fill="rgba(96,165,250,0.2)" stroke="#60a5fa" rx="5"/>
  <text x="200" y="105" text-anchor="middle" fill="#60a5fa" font-size="14">Banks & Institutions</text>
  <line x1="200" y1="120" x2="200" y2="140" stroke="#60a5fa" stroke-width="2" marker-end="url(#arrowhead)"/>
  
  <rect x="50" y="140" width="300" height="40" fill="rgba(167,139,250,0.2)" stroke="#a78bfa" rx="5"/>
  <text x="200" y="165" text-anchor="middle" fill="#a78bfa" font-size="14">Retail Traders (You)</text>
</svg>

## Common Beginner Mistake
**Fighting the Banks**: Retail traders often try to "catch falling knives" against major bank flows. If Deutsche Bank is selling EUR/USD with billions in volume, your $1,000 buy order won't turn the tide. Trade WITH institutional flow, not against it.

## Key Takeaway
Understand that you're a small fish in a big ocean. Your advantage isn't size—it's agility. You can enter and exit quickly while institutions need days to build positions.

## Practice Question
Which market participant typically creates the largest price movements?""",
                        "quiz": [
                            {
                                "question": "Which participant moves markets most?",
                                "option_a": "Retail traders",
                                "option_b": "Central banks",
                                "option_c": "Your broker",
                                "option_d": "Social media influencers",
                                "correct_answer": "B",
                                "explanation": "Central banks control interest rates and currency supply, creating largest moves.",
                                "topic_slug": "market_participants"
                            },
                            {
                                "question": "Why do corporations trade forex?",
                                "option_a": "To speculate",
                                "option_b": "To convert foreign earnings",
                                "option_c": "To manipulate prices",
                                "option_d": "For entertainment",
                                "correct_answer": "B",
                                "explanation": "Apple, Toyota, etc. convert foreign revenue back to home currency.",
                                "topic_slug": "market_participants"
                            },
                            {
                                "question": "What percentage of volume do retail traders represent?",
                                "option_a": "50%",
                                "option_b": "25%",
                                "option_c": "10%",
                                "option_d": "Less than 10%",
                                "correct_answer": "D",
                                "explanation": "Retail traders are less than 10% of the $7.5 trillion daily volume.",
                                "topic_slug": "market_participants"
                            },
                            {
                                "question": "Scenario: Deutsche Bank is selling $2 billion EUR/USD. You buy 1 micro lot. What happens?",
                                "option_a": "You reverse the trend",
                                "option_b": "Price ignores your trade",
                                "option_c": "You profit immediately",
                                "option_d": "The bank follows you",
                                "correct_answer": "B",
                                "explanation": "Institutional volume dwarfs retail. Your $0.10/pip trade doesn't impact price.",
                                "topic_slug": "market_participants"
                            },
                            {
                                "question": "Mistake: Fighting central bank intervention. If SNB is selling CHF heavily, you should?",
                                "option_a": "Buy CHF against them",
                                "option_b": "Sell CHF with them",
                                "option_c": "Ignore the news",
                                "option_d": "Trade exotics instead",
                                "correct_answer": "B",
                                "explanation": "Never fight central banks. Trade in the direction of their flow or stay out.",
                                "topic_slug": "market_participants"
                            }
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
Currency pairs are categorized by liquidity and trading volume: Majors (most traded), Minors (crosses), and Exotics (emerging markets).

## Concept Explanation
**Major Pairs** (All include USD):
- EUR/USD: 28% of daily volume — tightest spreads, most predictable
- USD/JPY: 13% — "safe haven" during uncertainty
- GBP/USD: 11% — volatile, good for scalping
- USD/CHF: 5% — often moves inverse to EUR/USD
- USD/CAD: 4% — oil-correlated
- AUD/USD: 5% — China-correlated, commodity currency
- NZD/USD: 2% — highest interest rate sensitivity

**Minor Pairs** (No USD): EUR/GBP, EUR/JPY, GBP/JPY — wider spreads, still liquid.

**Exotics** (Emerging markets): USD/ZAR, USD/TRY, USD/MXN — huge spreads, dangerous for beginners.

## Step-by-Step Breakdown
1. **Spread Costs**: EUR/USD spread = 0.1-0.3 pips. USD/TRY spread = 50-200 pips.
2. **Volatility**: GBP/JPY moves 100+ pips daily. EUR/CHF might move 30 pips.
3. **Correlation**: EUR/USD and GBP/USD move together ~90% of the time. Don't trade both simultaneously.

## Real Trading Example
**Beginner Account**: $1,000
- **Bad Choice**: Trading USD/ZAR with 50-pip spread. You start 50 pips underwater immediately.
- **Good Choice**: Trading EUR/USD with 0.2-pip spread. Minimal cost to enter.

**Calculation**:
0.1 lots on USD/ZAR (50-pip spread) = $50 cost (5% of account gone instantly).
0.1 lots on EUR/USD (0.2-pip spread) = $0.20 cost (0.02% of account).

<div class="ac-tradingview-widget" data-symbol="FX:EURUSD"></div>

## Common Beginner Mistake
**Trading Exotics for "Excitement"**: Beginners see USD/TRY moving 500 pips and think "more pips = more profit." They ignore that the spread eats 200 pips and the swap fees are $20/night. Stick to majors until consistently profitable.

## Key Takeaway
Start with EUR/USD only. Master one pair before adding others. EUR/USD has:
- Tightest spreads (lowest cost)
- Most analysis available
- Predictable patterns
- Best for learning

## Practice Question
Which pair is generally best for beginners and why?""",
                        "quiz": [
                            {
                                "question": "Which is a major pair?",
                                "option_a": "EUR/GBP",
                                "option_b": "EUR/USD",
                                "option_c": "USD/ZAR",
                                "option_d": "GBP/JPY",
                                "correct_answer": "B",
                                "explanation": "Majors always include USD. EUR/USD is the most traded pair.",
                                "topic_slug": "currency_pairs"
                            },
                            {
                                "question": "Which pair type typically has the widest spreads?",
                                "option_a": "Majors",
                                "option_b": "Minors",
                                "option_c": "Exotics",
                                "option_d": "All equal",
                                "correct_answer": "C",
                                "explanation": "Exotics like USD/TRY have spreads of 50-200 pips vs 0.1-0.3 for majors.",
                                "topic_slug": "currency_pairs"
                            },
                            {
                                "question": "Calculate cost: 0.1 lots USD/ZAR with 50-pip spread.",
                                "option_a": "$0.50",
                                "option_b": "$5.00",
                                "option_c": "$50.00",
                                "option_d": "$500",
                                "correct_answer": "C",
                                "explanation": "0.1 lots = $1/pip on most pairs. 50 pips × $1 = $50 entry cost.",
                                "topic_slug": "currency_pairs"
                            },
                            {
                                "question": "Scenario: You trade both EUR/USD and GBP/USD long. What happens?",
                                "option_a": "Diversified risk",
                                "option_b": "Double risk on same move",
                                "option_c": "Guaranteed profit",
                                "option_d": "Hedge position",
                                "correct_answer": "B",
                                "explanation": "EUR/USD and GBP/USD are ~90% correlated. One move affects both equally.",
                                "topic_slug": "currency_pairs"
                            },
                            {
                                "question": "Mistake: Trading exotics as a beginner. What's the hidden cost?",
                                "option_a": "No cost",
                                "option_b": "High spreads and swap fees",
                                "option_c": "Lower volatility",
                                "option_d": "Better liquidity",
                                "correct_answer": "B",
                                "explanation": "Exotics have 50-200 pip spreads and overnight fees that drain accounts.",
                                "topic_slug": "currency_pairs"
                            }
                        ]
                    },
                    {
                        "title": "Reading Pips and Spreads",
                        "content": """## Simple Definition
A "pip" is the smallest price move in forex. For most pairs, it's the 4th decimal place (0.0001). The "spread" is the difference between buy (ask) and sell (bid) prices—your cost to trade.

## Concept Explanation
**Pip Values**:
- Most pairs: 0.0001 = 1 pip
- JPY pairs: 0.01 = 1 pip (USD/JPY 109.50 to 109.51 = 1 pip)

**Lot Sizes & Pip Values**:
- Standard lot (1.0): 100,000 units = $10/pip
- Mini lot (0.1): 10,000 units = $1/pip  
- Micro lot (0.01): 1,000 units = $0.10/pip
- Nano lot (0.001): 100 units = $0.01/pip

## Step-by-Step Breakdown
1. **Calculate Trade Value**: 0.5 lots EUR/USD at 1.0850 = 50,000 EUR = $54,250 USD exposure
2. **Determine Pip Value**: 0.5 lots = $5 per pip (half of standard lot)
3. **Calculate Spread Cost**: 2-pip spread × $5 = $10 cost to enter trade
4. **Breakeven Calculation**: Price must move 2 pips in your favor just to break even.

## Real Trading Example
**Account**: $5,000
**Risk per trade**: 2% = $100
**Trade Setup**: EUR/USD buy at 1.0850, stop at 1.0830 (20 pips risk)

**Position Sizing Calculation**:
- Risk amount: $100
- Risk in pips: 20
- Pip value needed: $100 ÷ 20 = $5 per pip
- Lot size: 0.5 lots (mini lots)

**Verification**: 20 pips × $5/pip = $100 risk ✓

<svg class="ac-svg-diagram" viewBox="0 0 400 120">
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#f59e0b"/>
    </marker>
  </defs>
  <rect x="20" y="30" width="150" height="40" fill="rgba(239,68,68,0.2)" stroke="#ef4444" rx="5"/>
  <text x="95" y="55" text-anchor="middle" fill="#ef4444" font-size="12">Bid: 1.08498</text>
  <text x="95" y="75" text-anchor="middle" fill="#9ca3af" font-size="10">Sell Price</text>
  
  <line x1="170" y1="50" x2="230" y2="50" stroke="#f59e0b" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="200" y="45" text-anchor="middle" fill="#f59e0b" font-size="12" font-weight="bold">2 pips</text>
  <text x="200" y="80" text-anchor="middle" fill="#9ca3af" font-size="10">Spread = Cost</text>
  
  <rect x="230" y="30" width="150" height="40" fill="rgba(34,197,94,0.2)" stroke="#22c55e" rx="5"/>
  <text x="305" y="55" text-anchor="middle" fill="#22c55e" font-size="12">Ask: 1.08502</text>
  <text x="305" y="75" text-anchor="middle" fill="#9ca3af" font-size="10">Buy Price</text>
</svg>

## Common Beginner Mistake
**Ignoring Spread in Stop Loss Placement**: You set a 10-pip stop loss, but the spread is 3 pips. Your actual stop is only 7 pips away, increasing risk by 30%. Always add spread to your stop distance calculation.

## Key Takeaway
Pips measure movement. Spreads measure cost. Calculate both before every trade. A "free" trade with a 5-pip spread costs $50 on 1 standard lot.

## Practice Question
If you trade 0.3 lots with a 1.5-pip spread, what is your entry cost in dollars?""",
                        "quiz": [
                            {
                                "question": "How much is 1 pip on EUR/USD for 1 standard lot?",
                                "option_a": "$0.10",
                                "option_b": "$1",
                                "option_c": "$10",
                                "option_d": "$100",
                                "correct_answer": "C",
                                "explanation": "1 standard lot = 100,000 units. 1 pip (0.0001) × 100,000 = $10.",
                                "topic_slug": "pips_lots"
                            },
                            {
                                "question": "What is the spread?",
                                "option_a": "The trend direction",
                                "option_b": "Difference between bid and ask",
                                "option_c": "The commission fee",
                                "option_d": "The swap rate",
                                "correct_answer": "B",
                                "explanation": "Spread is the difference between buy (ask) and sell (bid) price—your entry cost.",
                                "topic_slug": "pips_lots"
                            },
                            {
                                "question": "Calculate: 0.3 lots with 1.5-pip spread. Cost in dollars?",
                                "option_a": "$0.45",
                                "option_b": "$4.50",
                                "option_c": "$45",
                                "option_d": "$450",
                                "correct_answer": "B",
                                "explanation": "0.3 lots = $3/pip. 1.5 pips × $3 = $4.50 cost to enter.",
                                "topic_slug": "pips_lots"
                            },
                            {
                                "question": "Scenario: You set a 15-pip stop but spread is 2 pips. Actual risk distance?",
                                "option_a": "15 pips",
                                "option_b": "17 pips",
                                "option_c": "13 pips",
                                "option_d": "30 pips",
                                "correct_answer": "C",
                                "explanation": "Price must move spread + stop distance. 15 - 2 = 13 pips actual protection.",
                                "topic_slug": "pips_lots"
                            },
                            {
                                "question": "Mistake: Using maximum leverage without calculating pip value. Risk?",
                                "option_a": "Lower risk",
                                "option_b": "Precise position sizing impossible",
                                "option_c": "Guaranteed profits",
                                "option_d": "No effect",
                                "correct_answer": "B",
                                "explanation": "Without pip value calculation, you cannot size positions correctly for your risk amount.",
                                "topic_slug": "pips_lots"
                            }
                        ]
                    }
                ]
            },
            {
                "title": "Trading Sessions and Market Timing",
                "description": "When the markets are most active.",
                "lessons": [
                    {
                        "title": "Trading Sessions Explained",
                        "content": """## Simple Definition
The Forex market operates 24/5, divided into three major sessions: Asian, London, and New York. Each session has unique characteristics, volatility patterns, and optimal trading windows.

## Concept Explanation
**Asian Session (Tokyo)**: 20:00–05:00 UTC
- Lower volatility
- JPY pairs most active
- Range-bound markets common
- Best for: Grid trading, range strategies

**London Session**: 08:00–17:00 UTC
- Highest liquidity
- EUR, GBP, CHF pairs most active
- Major trend beginnings
- Best for: Breakout trading, trend following

**New York Session**: 13:00–22:00 UTC
- USD pairs volatile
- Overlap with London (13:00–17:00) = best trading hours
- Economic news releases
- Best for: News trading, momentum strategies

## Step-by-Step Breakdown
1. **Session Open**: Increased volatility as institutional orders hit the market
2. **Mid-Session**: Established trends continue, volume stabilizes
3. **Session Close**: Profit-taking, position squaring, potential reversals
4. **Overlap Periods**: London-NY overlap (13:00–17:00 UTC) offers highest liquidity and tightest spreads

## Real Trading Example
**The London Breakout Strategy**:
- Wait for Asian session range formation (02:00–08:00 UTC)
- Place buy stop above range high, sell stop below range low
- London open (08:00 UTC) triggers breakout
- Target 1.5× the range width
- Stop loss on opposite side of breakout

<div class="ac-tradingview-widget" data-symbol="FX:EURUSD"></div>

## Common Beginner Mistake
**Trading the Asian Session as a Beginner**: While it seems "calmer," the lack of liquidity creates false breakouts and whipsaws. Beginners mistake low volatility for "safety," then get chopped up in range-bound markets.

## Key Takeaway
Trade during the London-NY overlap (13:00–17:00 UTC) for the best combination of liquidity, volatility, and trend clarity. Avoid Friday afternoons and Sunday opens.

## Practice Question
Which session typically offers the highest liquidity and best trading conditions?""",
                        "quiz": [
                            {
                                "question": "What are the three major trading sessions?",
                                "option_a": "Morning, Afternoon, Evening",
                                "option_b": "Asian, London, New York",
                                "option_c": "Open, High, Close",
                                "option_d": "Bull, Bear, Sideways",
                                "correct_answer": "B",
                                "explanation": "The three major sessions are Asian (Tokyo), London, and New York.",
                                "topic_slug": "sessions"
                            },
                            {
                                "question": "Which pairs are most active during the Asian session?",
                                "option_a": "EUR/USD",
                                "option_b": "USD/CAD",
                                "option_c": "JPY pairs",
                                "option_d": "GBP pairs",
                                "correct_answer": "C",
                                "explanation": "Japanese Yen pairs (USD/JPY, EUR/JPY) are most active during Tokyo hours.",
                                "topic_slug": "sessions"
                            },
                            {
                                "question": "When is the London-New York overlap (in UTC)?",
                                "option_a": "08:00-12:00",
                                "option_b": "13:00-17:00",
                                "option_c": "20:00-00:00",
                                "option_d": "00:00-04:00",
                                "correct_answer": "B",
                                "explanation": "13:00-17:00 UTC is when both London and NY markets are open—highest liquidity.",
                                "topic_slug": "sessions"
                            },
                            {
                                "question": "Scenario: You trade GBP/USD at 03:00 UTC. What should you expect?",
                                "option_a": "High volatility",
                                "option_b": "Tight spreads",
                                "option_c": "Low liquidity, possible whipsaws",
                                "option_d": "Major breakouts",
                                "correct_answer": "C",
                                "explanation": "03:00 UTC is deep Asian session—low liquidity for GBP pairs, choppy price action.",
                                "topic_slug": "sessions"
                            },
                            {
                                "question": "Mistake: Trading Sunday evening immediately after market open. Risk?",
                                "option_a": "Guaranteed trends",
                                "option_b": "Gaps from weekend news",
                                "option_c": "Low spreads",
                                "option_d": "High liquidity",
                                "correct_answer": "B",
                                "explanation": "Sunday opens often have gaps from weekend events, causing slippage and false signals.",
                                "topic_slug": "sessions"
                            }
                        ]
                    },
                    {
                        "title": "Best Times to Trade",
                        "content": """## Simple Definition
Not all trading hours are equal. The "Golden Window" offers the best combination of liquidity, volatility, and predictable patterns for retail traders.

## Concept Explanation
**The Golden Window**: 13:00–17:00 UTC (London-NY Overlap)
- Highest liquidity of the day
- Tightest spreads (0.1-0.3 pips on majors)
- Most directional moves
- Best for: Day trading, scalping, momentum strategies

**Good Hours**:
- 08:00–13:00 UTC (London morning, trends establish)
- Volatile but directional movement

**Avoid**:
- 20:00–00:00 UTC (Asian start, choppy)
- Friday 20:00–24:00 UTC (low liquidity, spreads widen)
- Sunday 22:00–23:00 UTC (weekend gap fills, unpredictable)
- Major news releases (unless news trading specialist)

## Step-by-Step Breakdown
1. **Pre-Market Analysis** (30 mins before): Check economic calendar, mark key levels
2. **Golden Window Entry** (13:00–17:00 UTC): Execute high-probability setups only
3. **Afternoon Session** (17:00–20:00 UTC): Manage existing positions, no new entries
4. **Evening Review** (20:00+ UTC): Journal trades, prepare for next day

## Real Trading Example
**The 2-Hour Trader Schedule**:
- **12:30 UTC**: Analyze charts, identify support/resistance
- **13:00 UTC**: London-NY overlap begins, wait for setup
- **14:30 UTC**: Valid setup appears—enter trade
- **16:00 UTC**: Close position before volatility drops
- **Result**: 2 hours of focused trading, 40 pips profit, minimal stress

<svg class="ac-svg-diagram" viewBox="0 0 400 100">
  <rect x="20" y="20" width="80" height="60" fill="rgba(167,139,250,0.3)" stroke="#a78bfa" rx="5"/>
  <text x="60" y="55" text-anchor="middle" fill="#a78bfa" font-size="12">Asian</text>
  
  <rect x="110" y="20" width="90" height="60" fill="rgba(96,165,250,0.3)" stroke="#60a5fa" rx="5"/>
  <text x="155" y="55" text-anchor="middle" fill="#60a5fa" font-size="12">London</text>
  
  <rect x="210" y="20" width="90" height="60" fill="rgba(34,197,94,0.3)" stroke="#22c55e" rx="5"/>
  <text x="255" y="55" text-anchor="middle" fill="#22c55e" font-size="12">NY</text>
  <text x="255" y="75" text-anchor="middle" fill="#fbbf24" font-size="10" font-weight="bold">GOLDEN</text>
  
  <rect x="310" y="20" width="70" height="60" fill="rgba(107,114,128,0.2)" stroke="#6b7280" rx="5"/>
  <text x="345" y="55" text-anchor="middle" fill="#6b7280" font-size="12">Avoid</text>
  
  <text x="200" y="95" text-anchor="middle" fill="#9ca3af" font-size="10">Time Progression →</text>
</svg>

## Common Beginner Mistake
**All-Day Trading**: Beginners sit in front of charts for 8+ hours, overtrading during low-quality hours. This leads to fatigue, revenge trading, and losses during choppy Asian session price action.

## Key Takeaway
Quality over quantity. Trading 2 hours during the Golden Window beats trading 8 hours during random sessions. Protect your mental capital as fiercely as your financial capital.

## Practice Question
Why should beginners avoid trading during the first hour of the Asian session?""",
                        "quiz": [
                            {
                                "question": "What is the 'Golden Window' for trading?",
                                "option_a": "Any profitable time",
                                "option_b": "London-NY overlap 13:00-17:00 UTC",
                                "option_c": "Weekend trading",
                                "option_d": "Holiday sessions",
                                "correct_answer": "B",
                                "explanation": "13:00-17:00 UTC offers highest liquidity, tightest spreads, and most predictable moves.",
                                "topic_slug": "sessions"
                            },
                            {
                                "question": "Which time should beginners avoid?",
                                "option_a": "Tuesday 14:00 UTC",
                                "option_b": "Friday evening",
                                "option_c": "Thursday 10:00 UTC",
                                "option_d": "Wednesday overlap",
                                "correct_answer": "B",
                                "explanation": "Friday evening has low liquidity, wide spreads, and unpredictable weekend risk.",
                                "topic_slug": "sessions"
                            },
                            {
                                "question": "Calculate: You trade 1 standard lot at Friday 21:00 UTC with 5-pip spread vs Wednesday 14:00 UTC with 0.5-pip spread. Difference in cost?",
                                "option_a": "$5",
                                "option_b": "$45",
                                "option_c": "$50",
                                "option_d": "$500",
                                "correct_answer": "B",
                                "explanation": "Difference is 4.5 pips. 1 lot = $10/pip. 4.5 × $10 = $45 extra cost Friday evening.",
                                "topic_slug": "sessions"
                            },
                            {
                                "question": "Scenario: You see a perfect setup at 22:00 UTC Sunday. Action?",
                                "option_a": "Enter immediately",
                                "option_b": "Wait for Monday liquidity",
                                "option_c": "Increase position size",
                                "option_d": "Use market order",
                                "correct_answer": "B",
                                "explanation": "Sunday 22:00 has weekend gap risk and low liquidity. Wait for Monday session.",
                                "topic_slug": "sessions"
                            },
                            {
                                "question": "Mistake: Trading 8 hours straight. Consequence?",
                                "option_a": "More profit",
                                "option_b": "Fatigue and overtrading",
                                "option_c": "Better focus",
                                "option_d": "Guaranteed success",
                                "correct_answer": "B",
                                "explanation": "Long sessions cause fatigue, leading to revenge trading and poor decisions.",
                                "topic_slug": "sessions"
                            }
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
Leverage allows you to control a large position with a small amount of capital. It's expressed as a ratio (1:100), showing how much your position is magnified compared to your margin.

## Concept Explanation
**How It Works**:
- 1:100 leverage = $1,000 margin controls $100,000 position
- 1:50 leverage = $1,000 margin controls $50,000 position
- 1:500 leverage = $1,000 margin controls $500,000 position

**The Double-Edged Sword**:
- **For you**: 1% market move = 100% account gain (with 1:100 leverage)
- **Against you**: 1% market move = 100% account loss (with 1:100 leverage)

## Step-by-Step Breakdown
1. **Account Balance**: $10,000
2. **Leverage Chosen**: 1:100
3. **Position Size Desired**: 1 lot ($100,000)
4. **Margin Required**: $100,000 ÷ 100 = $1,000
5. **Free Margin**: $9,000 (available for other trades or losses)
6. **Margin Call Level**: When losses exceed $9,000, broker closes positions

## Real Trading Example
**Conservative Trader (1:10 leverage)**:
- Account: $10,000
- Position: 0.1 lots ($10,000)
- Margin used: $1,000
- 100 pip loss = $100 (1% of account) — Survived to trade again

**Aggressive Trader (1:500 leverage)**:
- Account: $10,000
- Position: 5 lots ($500,000)
- Margin used: $1,000
- 20 pip loss = $1,000 (10% of account) — Devastating

<svg class="ac-svg-diagram" viewBox="0 0 400 80">
  <rect x="10" y="30" width="40" height="20" fill="#f59e0b" opacity="0.5"/>
  <text x="15" y="44" fill="#fff" font-size="8">$1,000</text>
  <line x1="50" y1="40" x2="150" y2="40" stroke="#9ca3af" stroke-width="1" stroke-dasharray="3,3"/>
  <text x="75" y="35" fill="#9ca3af" font-size="8">1:100</text>
  <text x="70" y="70" fill="#ef4444" font-size="8">Amplifies gains AND losses</text>
  <rect x="150" y="20" width="40" height="40" fill="#22c55e" opacity="0.3"/>
  <text x="155" y="44" fill="#fff" font-size="8">$100k</text>
</svg>

## Common Beginner Mistake
**Maximum Leverage**: Brokers offer 1:500 to 1:1000 leverage. Beginners use it all, thinking "more power." In reality, with 1:500 leverage, a 0.2% move against you wipes out your account. Professional traders rarely use more than 1:20.

## Key Takeaway
Use 1:10 to 1:30 leverage as a beginner. Never risk more than 2% per trade regardless of leverage available. Leverage is a tool, not a weapon.

## Practice Question
With $5,000 account and 1:100 leverage, what is the maximum position size you could theoretically control?""",
                        "quiz": [
                            {
                                "question": "With 1:100 leverage, how much does $1,000 control?",
                                "option_a": "$1,000",
                                "option_b": "$10,000",
                                "option_c": "$100,000",
                                "option_d": "$1,000,000",
                                "correct_answer": "C",
                                "explanation": "1:100 leverage means $1,000 × 100 = $100,000 position size.",
                                "topic_slug": "leverage"
                            },
                            {
                                "question": "What happens to losses with high leverage?",
                                "option_a": "They decrease",
                                "option_b": "They stay the same",
                                "option_c": "They amplify equally with gains",
                                "option_d": "They disappear",
                                "correct_answer": "C",
                                "explanation": "Leverage amplifies both gains AND losses equally. It's a double-edged sword.",
                                "topic_slug": "leverage"
                            },
                            {
                                "question": "Calculate: $10,000 account, 1:50 leverage, 2% account risk. Position size?",
                                "option_a": "$5,000",
                                "option_b": "$50,000",
                                "option_c": "$500,000",
                                "option_d": "$20,000",
                                "correct_answer": "C",
                                "explanation": "1:50 leverage × $10,000 = $500,000 maximum theoretical position.",
                                "topic_slug": "leverage"
                            },
                            {
                                "question": "Scenario: 1:500 leverage, $1,000 account. How many pips to wipe out with 1 lot?",
                                "option_a": "1,000 pips",
                                "option_b": "100 pips",
                                "option_c": "20 pips",
                                "option_d": "200 pips",
                                "correct_answer": "C",
                                "explanation": "1 lot = $10/pip. $1,000 ÷ $10 = 100 pips, but with 1:500, margin is thin. Actually ~20 pips moves trigger margin call.",
                                "topic_slug": "leverage"
                            },
                            {
                                "question": "Mistake: Using maximum broker leverage. Why dangerous?",
                                "option_a": "Higher profits guaranteed",
                                "option_b": "Small moves cause large losses",
                                "option_c": "Lower spreads",
                                "option_d": "Better execution",
                                "correct_answer": "B",
                                "explanation": "High leverage means small adverse moves (0.2%) can wipe out your entire account.",
                                "topic_slug": "leverage"
                            }
                        ]
                    },
                    {
                        "title": "Position Sizing Calculation",
                        "content": """## Simple Definition
Position sizing determines how many lots to trade based on your account risk, stop loss distance, and pip value. It's the most critical skill in risk management.

## Concept Explanation
**The Formula**:

**Variables**:
- **Account Risk**: Fixed percentage (1-2%) of account balance
- **Stop Loss**: Technical level where trade idea is invalidated
- **Pip Value**: Determined by lot size ($10/pip for 1.0 lot)

## Step-by-Step Breakdown
**Example**: $10,000 account, 2% risk, 50-pip stop, trading EUR/USD

1. **Calculate Risk Amount**: $10,000 × 2% = $200 maximum risk
2. **Determine Pip Value Needed**: $200 ÷ 50 pips = $4 per pip
3. **Convert to Lots**: $4 per pip ÷ $10 per pip (standard lot) = 0.4 lots
4. **Verification**: 50 pips × $4/pip = $200 risk ✓

## Real Trading Example
**Account**: $5,000
**Setup**: GBP/JPY short at 185.00, stop at 185.50 (50 pips)
**Risk**: 1% = $50

**Calculation**:
- $50 ÷ 50 pips = $1 per pip needed
- $1 per pip = 0.1 lots (mini lot)
- **Action**: Sell 0.1 lots GBP/JPY

**Outcome**: Price drops to 184.00 (100 pips profit = $100). Risk was $50, reward was $100. 1:2 R:R achieved.

<div class="ac-tradingview-widget" data-symbol="OANDA:GBPJPY"></div>

## Common Beginner Mistake
**Fixed Lot Sizes**: Beginners trade 0.1 lots on every trade regardless of account size or stop distance. On a $500 account with 50-pip stop, this risks $50 (10%!) per trade. After 2 losses, account is down 20%.

## Key Takeaway
Never trade fixed lot sizes. Always calculate: Risk Amount ÷ Stop Distance = Pip Value → Lot Size. This ensures consistent 1-2% risk per trade regardless of setup.

## Practice Question
Account: $2,000. Risk: 2%. Stop loss: 25 pips. What is the correct lot size?""",
                        "quiz": [
                            {
                                "question": "What is the position sizing formula?",
                                "option_a": "Account balance × leverage",
                                "option_b": "Risk amount ÷ (stop pips × pip value)",
                                "option_c": "Maximum lots available",
                                "option_d": "Random selection",
                                "correct_answer": "B",
                                "explanation": "Position Size = Account Risk ($) ÷ (Stop Loss (pips) × Pip Value ($)).",
                                "topic_slug": "position_sizing"
                            },
                            {
                                "question": "With $10,000 account and 2% risk, what is risk amount?",
                                "option_a": "$20",
                                "option_b": "$200",
                                "option_c": "$2,000",
                                "option_d": "$200,000",
                                "correct_answer": "B",
                                "explanation": "$10,000 × 2% = $200 maximum risk per trade.",
                                "topic_slug": "position_sizing"
                            },
                            {
                                "question": "Calculate: $5,000 account, 1% risk, 40-pip stop. Pip value needed?",
                                "option_a": "$1.25",
                                "option_b": "$12.50",
                                "option_c": "$125",
                                "option_d": "$1,250",
                                "correct_answer": "A",
                                "explanation": "$5,000 × 1% = $50 risk. $50 ÷ 40 pips = $1.25 per pip.",
                                "topic_slug": "position_sizing"
                            },
                            {
                                "question": "Scenario: You need $2/pip. What lot size?",
                                "option_a": "0.02 lots",
                                "option_b": "0.2 lots",
                                "option_c": "2.0 lots",
                                "option_d": "20 lots",
                                "correct_answer": "B",
                                "explanation": "0.2 lots = $2/pip (0.2 × $10/pip standard).",
                                "topic_slug": "position_sizing"
                            },
                            {
                                "question": "Mistake: Trading 0.5 lots on every trade regardless of stop. Consequence?",
                                "option_a": "Consistent risk",
                                "option_b": "Variable risk, potential blowup",
                                "option_c": "Guaranteed profits",
                                "option_d": "Lower spreads",
                                "correct_answer": "B",
                                "explanation": "Fixed lots = variable dollar risk. Wide stops with fixed lots = massive losses.",
                                "topic_slug": "position_sizing"
                            }
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
Never risk more than 1–2% of your total account balance on any single trade. This ensures that even a string of losses cannot devastate your capital.

## Concept Explanation
**The Math of Survival**:
- **2% risk**: 50 consecutive losses needed to blow account
- **5% risk**: 20 consecutive losses to blow account  
- **10% risk**: 10 consecutive losses to blow account
- **25% risk**: 4 consecutive losses to blow account

**Probability Reality**: Even profitable traders (60% win rate) experience 5-10 loss streaks regularly. With 2% risk, a 10-loss streak = 20% drawdown (recoverable). With 10% risk, same streak = 100% drawdown (ruined).

## Step-by-Step Breakdown
**Account**: $10,000

1. **Daily Risk Budget**: 6% of account = $600 maximum daily loss
2. **Per Trade Risk**: 2% = $200 maximum per trade
3. **Consecutive Loss Rule**: After 3 losses in a row, stop trading for the day
4. **Weekly Limit**: 12% maximum weekly drawdown before mandatory break

## Real Trading Example
**Trader A (2% rule)**:
- Account: $10,000
- 10 bad trades in a row (rare but happens)
- Loss: $200 × 10 = $2,000 (20% drawdown)
- **Result**: Account at $8,000. Three good weeks of 2% gains recovers to $10,500.

**Trader B (10% rule)**:
- Account: $10,000  
- Same 10 bad trades
- Loss: $1,000 × 10 = $10,000 (100% drawdown)
- **Result**: Account blown. Needs to deposit new funds.

<svg class="ac-svg-diagram" viewBox="0 0 200 60">
  <rect x="10" y="20" width="180" height="20" fill="#1f2937"/>
  <rect x="10" y="20" width="3.6" height="20" fill="#ef4444"/>
  <text x="15" y="55" fill="#ef4444" font-size="8">2% Risk</text>
  <rect x="13.6" y="20" width="176.4" height="20" fill="#22c55e" opacity="0.3"/>
  <text x="100" y="35" fill="#9ca3af" font-size="10">Account Balance Protected</text>
</svg>

## Common Beginner Mistake
**"I only have $500, so I need to risk 20% to make it worth it"**: This guarantees failure. With 20% risk, just 5 losses in a row (common for beginners) wipes out the account. Small accounts should trade micro lots (0.01) with 1% risk ($5), building consistency before sizing up.

## Key Takeaway
The 1-2% rule isn't optional—it's survival. Trading is a game of probabilities. You must survive the inevitable losing streaks to reach the winning streaks. Capital preservation is priority #1.

## Practice Question
If you have a $5,000 account and risk 2% per trade, what is your maximum dollar risk per trade?""",
                        "quiz": [
                            {
                                "question": "What is the maximum recommended risk per trade?",
                                "option_a": "10%",
                                "option_b": "5%",
                                "option_c": "1-2%",
                                "option_d": "25%",
                                "correct_answer": "C",
                                "explanation": "Never risk more than 1-2% of account per trade to survive losing streaks.",
                                "topic_slug": "risk_management"
                            },
                            {
                                "question": "With 2% risk, how many losses to blow account?",
                                "option_a": "10",
                                "option_b": "20",
                                "option_c": "50",
                                "option_d": "5",
                                "correct_answer": "C",
                                "explanation": "With 2% risk, you need 50 consecutive losses to wipe out (2% × 50 = 100%).",
                                "topic_slug": "risk_management"
                            },
                            {
                                "question": "Calculate: $5,000 account, 2% risk. Max dollar loss?",
                                "option_a": "$10",
                                "option_b": "$100",
                                "option_c": "$1,000",
                                "option_d": "$10,000",
                                "correct_answer": "B",
                                "explanation": "$5,000 × 2% = $100 maximum risk per trade.",
                                "topic_slug": "risk_management"
                            },
                            {
                                "question": "Scenario: You've lost 3 trades in a row. Action?",
                                "option_a": "Increase size to recover",
                                "option_b": "Stop trading for the day",
                                "option_c": "Trade different pair",
                                "option_d": "Remove stop losses",
                                "correct_answer": "B",
                                "explanation": "After 3 consecutive losses, stop trading. You're likely emotional or market conditions changed.",
                                "topic_slug": "risk_management"
                            },
                            {
                                "question": "Mistake: Risking 10% to 'make back' previous losses. Risk?",
                                "option_a": "Faster recovery",
                                "option_b": "Revenge trading spiral",
                                "option_c": "Guaranteed success",
                                "option_d": "Lower stress",
                                "correct_answer": "B",
                                "explanation": "Increasing risk after losses leads to revenge trading and account blowup.",
                                "topic_slug": "risk_management"
                            }
                        ]
                    },
                    {
                        "title": "Stop Loss and Take Profit",
                        "content": """## Simple Definition
Every trade must have a predetermined exit point for both losses (stop loss) and gains (take profit) before entry. No exceptions.

## Concept Explanation
**Stop Loss (SL)**: The price level where your trade thesis is proven wrong. Not a suggestion—a mandatory exit.
- **Long trades**: SL below support
- **Short trades**: SL above resistance
- **Volatility buffer**: Add 1-2x ATR to avoid noise

**Take Profit (TP)**: The logical target where reward justifies the risk.
- **Minimum 1:2 Risk:Reward**: Risk $100 to make $200
- **Support/Resistance targets**: Previous swing highs/lows
- **Trail stops**: Move SL to breakeven once 1R reached

## Step-by-Step Breakdown
**Trade Setup**: EUR/USD Long
1. **Entry**: 1.0850 (break of resistance)
2. **Stop Loss**: 1.0830 (below support, 20 pips)
3. **Take Profit**: 1.0890 (next resistance, 40 pips)
4. **Risk**: $200 (2% of $10k account)
5. **Reward**: $400 (4% of account)
6. **R:R Ratio**: 1:2 (minimum acceptable)

## Real Trading Example
**The Perfect Setup**:
- EUR/USD bounces off 1.0850 support (3rd touch)
- Bullish engulfing candle confirms
- **Entry**: 1.0852
- **SL**: 1.0840 (12 pips, below wick)
- **TP**: 1.0872 (20 pips, next resistance)
- **Position**: 0.16 lots ($1.60/pip × 12 pips = $192 risk)
- **Outcome**: Price hits TP in 4 hours. $320 profit vs $192 risk = 1.67 R:R

<svg class="ac-svg-diagram" viewBox="0 0 200 100">
  <line x1="20" y1="30" x2="180" y2="30" stroke="#ef4444" stroke-width="2" stroke-dasharray="5,5"/>
  <text x="30" y="25" fill="#ef4444" font-size="8">SL: 1.0830</text>
  <line x1="20" y1="50" x2="180" y2="50" stroke="#22c55e" stroke-width="2"/>
  <text x="30" y="55" fill="#22c55e" font-size="8">Entry: 1.0850</text>
  <line x1="20" y1="70" x2="180" y2="70" stroke="#60a5fa" stroke-width="2" stroke-dasharray="5,5"/>
  <text x="30" y="75" fill="#60a5fa" font-size="8">TP: 1.0870</text>
  <path d="M 50 50 L 100 40 L 150 65" fill="none" stroke="#f59e0b" stroke-width="2"/>
</svg>

## Common Beginner Mistake
**Moving Stop Losses**: Price approaches SL, trader moves it "just a bit lower" to avoid loss. This turns a planned $100 loss into an unplanned $300 loss. The market doesn't care about your pain tolerance—stick to the plan.

## Key Takeaway
Set SL and TP before clicking buy/sell. Once entered, only move SL in direction of profit (trailing), never against it. A trade without SL is a donation to the market.

## Practice Question
You enter EUR/USD at 1.1000 with SL at 1.0980 and TP at 1.1040. What is your Risk:Reward ratio?""",
                        "quiz": [
                            {
                                "question": "Where should stop loss be placed for a BUY trade?",
                                "option_a": "Above resistance",
                                "option_b": "Below support",
                                "option_c": "At entry price",
                                "option_d": "Randomly",
                                "correct_answer": "B",
                                "explanation": "For buy trades, stops go below support to invalidate the trade idea if support breaks.",
                                "topic_slug": "risk_management"
                            },
                            {
                                "question": "What is minimum recommended Risk:Reward ratio?",
                                "option_a": "1:1",
                                "option_b": "1:2",
                                "option_c": "1:0.5",
                                "option_d": "2:1",
                                "correct_answer": "B",
                                "explanation": "Minimum 1:2 R:R. Risk $1 to make $2. Allows 40% win rate to be profitable.",
                                "topic_slug": "risk_management"
                            },
                            {
                                "question": "Calculate: Entry 1.1000, SL 1.0980, TP 1.1040. Risk:Reward?",
                                "option_a": "1:1",
                                "option_b": "1:2",
                                "option_c": "2:1",
                                "option_d": "4:1",
                                "correct_answer": "B",
                                "explanation": "20 pip risk, 40 pip reward. 40/20 = 1:2 Risk:Reward ratio.",
                                "topic_slug": "risk_management"
                            },
                            {
                                "question": "Scenario: Price nears your SL. You move it 10 pips lower. Result?",
                                "option_a": "Saved the trade",
                                "option_b": "Usually larger loss",
                                "option_c": "Guaranteed reversal",
                                "option_d": "No effect",
                                "correct_answer": "B",
                                "explanation": "Moving stops to avoid loss usually results in larger losses. Trust your analysis.",
                                "topic_slug": "risk_management"
                            },
                            {
                                "question": "Mistake: Entering without stop loss. Why dangerous?",
                                "option_a": "Unlimited downside",
                                "option_b": "Lower spreads",
                                "option_c": "Better fills",
                                "option_d": "More time to decide",
                                "correct_answer": "A",
                                "explanation": "No stop loss = potential unlimited loss. One black swan event wipes account.",
                                "topic_slug": "risk_management"
                            }
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
Candlestick charts display price movement using "candles" that show open, high, low, and close (OHLC) for a specific time period. Each candle tells the story of who won—buyers or sellers—during that period.

## Concept Explanation
**Candle Anatomy**:
- **Body**: Area between open and close
  - Green/White: Close > Open (Bullish)
  - Red/Black: Close < Open (Bearish)
- **Wicks (Shadows)**: Lines extending from body showing high and low
  - **Upper Wick**: High price reached
  - **Lower Wick**: Low price reached

**Timeframes**:
- **M1, M5, M15**: Scalping, quick decisions
- **H1, H4**: Day trading, swing setups
- **D1, W1**: Position trading, major trends

## Step-by-Step Breakdown
**Reading a Daily Candle**:
1. **Body size**: Large body = strong conviction. Small body = indecision.
2. **Wick length**: Long upper wick = rejection of higher prices (selling pressure). Long lower wick = rejection of lower prices (buying pressure).
3. **Color sequence**: Green after red = potential reversal. Red after green = potential pullback.
4. **Context**: Single candle means nothing. Three candles = pattern. Ten candles = trend.

## Real Trading Example
**The Hammer Pattern** (Bullish Reversal):
- **Appearance**: Small body at top, long lower wick (2-3x body length)
- **Location**: Bottom of downtrend
- **Meaning**: Sellers pushed price down, but buyers regained control by close.
- **Entry**: Buy above hammer high
- **Stop**: Below hammer low
- **Confirmation**: Next candle closes green

<div class="ac-tradingview-widget" data-symbol="FX:EURUSD"></div>

## Common Beginner Mistake
**Candlestick Trading Without Context**: A "perfect" bullish engulfing pattern appears, but it's at the top of a 6-month uptrend against major resistance. Beginners buy and get crushed by the reversal. Always check higher timeframes and key levels.

## Key Takeaway
Candles show market sentiment. Wicks show rejection. Bodies show conviction. Always read candles within the context of trend, support/resistance, and volume (if available).

## Practice Question
What does a long upper wick on a candle indicate?""",
                        "quiz": [
                            {
                                "question": "What does a green candle indicate?",
                                "option_a": "Price closed lower than open",
                                "option_b": "Price closed higher than open",
                                "option_c": "No price movement",
                                "option_d": "Market closed",
                                "correct_answer": "B",
                                "explanation": "Green/white candle = Close > Open (Bullish session).",
                                "topic_slug": "candlestick_patterns"
                            },
                            {
                                "question": "What does a long upper wick show?",
                                "option_a": "Strong buying",
                                "option_b": "Rejection of higher prices",
                                "option_c": "Market closed high",
                                "option_d": "Low volatility",
                                "correct_answer": "B",
                                "explanation": "Long upper wick means price was rejected from higher levels—selling pressure.",
                                "topic_slug": "candlestick_patterns"
                            },
                            {
                                "question": "Calculate: Candle opens at 1.1000, closes at 1.1020, high 1.1030, low 1.0990. Body size?",
                                "option_a": "10 pips",
                                "option_b": "20 pips",
                                "option_c": "40 pips",
                                "option_d": "30 pips",
                                "correct_answer": "B",
                                "explanation": "Body = Close - Open = 1.1020 - 1.1000 = 20 pips.",
                                "topic_slug": "candlestick_patterns"
                            },
                            {
                                "question": "Scenario: Bullish engulfing appears at all-time high resistance. Action?",
                                "option_a": "Buy immediately",
                                "option_b": "Wait for breakout confirmation",
                                "option_c": "Sell short",
                                "option_d": "Increase leverage",
                                "correct_answer": "B",
                                "explanation": "Patterns at key resistance need confirmation. False breakouts common at highs.",
                                "topic_slug": "candlestick_patterns"
                            },
                            {
                                "question": "Mistake: Trading single candle patterns without trend context. Risk?",
                                "option_a": "Higher win rate",
                                "option_b": "False signals against trend",
                                "option_c": "Better entries",
                                "option_d": "Lower spreads",
                                "correct_answer": "B",
                                "explanation": "Single candles without trend context generate many false reversal signals.",
                                "topic_slug": "candlestick_patterns"
                            }
                        ]
                    },
                    {
                        "title": "Support and Resistance Basics",
                        "content": """## Simple Definition
**Support**: A price level where buying interest overcomes selling pressure, causing price to bounce upward.
**Resistance**: A price level where selling interest overcomes buying pressure, causing price to fall back.

## Concept Explanation
**Why These Levels Exist**:
- **Psychological**: Round numbers (1.1000, 1.2000) attract orders
- **Historical**: Previous highs/lows leave unfilled orders
- **Institutional**: Banks place large orders at specific prices
- **Technical**: Moving averages, trendlines create dynamic S/R

**Role Reversal**: Once support is broken, it often becomes resistance (and vice versa). This is one of the most reliable patterns in trading.

## Step-by-Step Breakdown
**Drawing Support**:
1. Find 2+ price lows at similar horizontal level
2. Connect the lows with a line
3. Extend line forward into future price action
4. The more touches, the stronger the support

**Validating Resistance**:
1. Price must test level and reverse at least twice
2. Reversals should be visible on multiple timeframes
3. Volume (if available) should increase at test
4. Recent touches carry more weight than ancient history

## Real Trading Example
**The Triple Top**:
- EUR/USD tests 1.1000 three times over 2 months
- Each test produces long upper wicks
- **Trade Setup**: Short at 1.0990, SL at 1.1020 (above resistance), TP at 1.0850 (next support)
- **Risk**: 30 pips
- **Reward**: 140 pips
- **R:R**: 1:4.7
- **Outcome**: Support breaks on 4th test, price falls to 1.0800

<svg class="ac-svg-diagram" viewBox="0 0 200 100">
  <path d="M 10 70 Q 50 70 70 50 T 130 50 T 190 30" fill="none" stroke="#60a5fa" stroke-width="2"/>
  <line x1="0" y1="70" x2="200" y2="70" stroke="#22c55e" stroke-width="2" stroke-dasharray="5,5"/>
  <text x="10" y="85" fill="#22c55e" font-size="8">Support - Price bounces up</text>
  <line x1="0" y1="30" x2="200" y2="30" stroke="#ef4444" stroke-width="2" stroke-dasharray="5,5"/>
  <text x="10" y="25" fill="#ef4444" font-size="8">Resistance - Price rejected</text>
  <circle cx="70" cy="70" r="3" fill="#22c55e"/>
  <circle cx="130" cy="30" r="3" fill="#ef4444"/>
</svg>

## Common Beginner Mistake
**Exact Price Levels**: Beginners draw lines at exact prices (1.0850) instead of zones (1.0840–1.0860). Markets are messy—price rarely hits exact levels. Use zones 10-20 pips wide for better entries.

## Key Takeaway
Support and resistance are zones, not lines. The more times a level is tested, the weaker it becomes (like bending metal). Trade bounces at support and rejections at resistance until the level breaks.

## Practice Question
What happens to support once it is clearly broken by price moving below it?""",
                        "quiz": [
                            {
                                "question": "What does support represent?",
                                "option_a": "Selling pressure",
                                "option_b": "Buying interest overcoming selling",
                                "option_c": "Market top",
                                "option_d": "Random price",
                                "correct_answer": "B",
                                "explanation": "Support is where buyers step in and overcome selling pressure, bouncing price up.",
                                "topic_slug": "support_resistance"
                            },
                            {
                                "question": "What is 'role reversal'?",
                                "option_a": "Traders swapping positions",
                                "option_b": "Broken resistance becomes new support",
                                "option_c": "Trend reversal",
                                "option_d": "Price gaps",
                                "correct_answer": "B",
                                "explanation": "Role reversal: once resistance is broken, it often becomes support on future pullbacks.",
                                "topic_slug": "support_resistance"
                            },
                            {
                                "question": "How many touches needed to validate a level?",
                                "option_a": "1",
                                "option_b": "2 or more",
                                "option_c": "10",
                                "option_d": "None",
                                "correct_answer": "B",
                                "explanation": "Need at least 2 clear touches where price reversed to validate support/resistance.",
                                "topic_slug": "support_resistance"
                            },
                            {
                                "question": "Scenario: Price breaks below support on high volume. Action?",
                                "option_a": "Buy the dip",
                                "option_b": "Wait for retest of broken level as resistance",
                                "option_c": "Hold longs",
                                "option_d": "Remove stops",
                                "correct_answer": "B",
                                "explanation": "Wait for broken support to be retested as resistance for short entry confirmation.",
                                "topic_slug": "support_resistance"
                            },
                            {
                                "question": "Mistake: Drawing exact single-price lines instead of zones. Risk?",
                                "option_a": "Better precision",
                                "option_b": "Missed entries or false breaks",
                                "option_c": "Lower risk",
                                "option_d": "Guaranteed fills",
                                "correct_answer": "B",
                                "explanation": "Exact lines cause missed trades or stops hit by wicks. Use 10-20 pip zones.",
                                "topic_slug": "support_resistance"
                            }
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
An **uptrend** is a series of Higher Highs (HH) and Higher Lows (HL). A **downtrend** is a series of Lower Highs (LH) and Lower Lows (LL). A **range** is when price oscillates between horizontal support and resistance without making new highs or lows.

## Concept Explanation
**Uptrend Characteristics**:
- Each peak is higher than the previous (HH)
- Each trough is higher than the previous (HL)
- Moving averages slope upward (20 EMA > 50 EMA > 200 EMA)
- Best strategy: Buy pullbacks to support

**Downtrend Characteristics**:
- Each peak is lower than the previous (LH)
- Each trough is lower than the previous (LL)
- Moving averages slope downward
- Best strategy: Sell rallies to resistance

## Step-by-Step Breakdown
**Trend Analysis Checklist**:
1. **Zoom Out**: Check daily chart first—what's the major trend?
2. **Mark Swings**: Identify last 3 swing highs and lows
3. **Compare**: Are highs getting higher? Are lows getting higher?
4. **Moving Averages**: Is price above 200 EMA? (Bullish bias)
5. **Trend Strength**: Steep angle = strong but risky. Gentle slope = sustainable.

## Real Trading Example
**The Trend Follower**:
- Daily chart: EUR/USD clearly above 200 EMA, making HH/HL
- H4 chart: Price pulls back to 50 EMA (dynamic support)
- H1 chart: Bullish engulfing candle at 50 EMA
- **Entry**: Buy at 1.0850
- **Stop**: 1.0820 (below EMA and recent low)
- **Target**: 1.0920 (next daily resistance)
- **Result**: Trend continues, target hit in 3 days for 70 pips

<div class="ac-tradingview-widget" data-symbol="FX:EURUSD"></div>

## Common Beginner Mistake
**Bottom Fishing**: Trying to buy at the absolute bottom of a downtrend because "it can't go lower." Trends persist longer than intuition suggests. Trade with the trend until proven otherwise.

## Key Takeaway
"The trend is your friend until the end when it bends." Never fight a clear daily trend. Even if you think it's "too high" or "too low," the market decides what's expensive or cheap.

## Practice Question
In a confirmed uptrend, what pattern must you see in the swing points?""",
                        "quiz": [
                            {
                                "question": "In an uptrend, you need:",
                                "option_a": "Lower highs and lower lows",
                                "option_b": "Higher highs and higher lows",
                                "option_c": "Equal highs",
                                "option_d": "Random price action",
                                "correct_answer": "B",
                                "explanation": "Uptrend = Higher Highs (HH) + Higher Lows (HL). Both conditions required.",
                                "topic_slug": "trend_analysis"
                            },
                            {
                                "question": "What does price above 200 EMA indicate?",
                                "option_a": "Bearish trend",
                                "option_b": "Bullish bias",
                                "option_c": "Range bound",
                                "option_d": "Reversal imminent",
                                "correct_answer": "B",
                                "explanation": "Price above 200 EMA indicates long-term bullish trend bias.",
                                "topic_slug": "trend_analysis"
                            },
                            {
                                "question": "Calculate: Trend lasted 6 months. You try to catch a bottom 5 times. Likely result?",
                                "option_a": "Profit",
                                "option_b": "5 losses",
                                "option_c": "Break even",
                                "option_d": "Guaranteed reversal",
                                "correct_answer": "B",
                                "explanation": "Trends persist. Counter-trend trading leads to multiple losses until trend actually ends.",
                                "topic_slug": "trend_analysis"
                            },
                            {
                                "question": "Scenario: Daily trend is up, H1 shows downtrend. Action?",
                                "option_a": "Sell short on H1",
                                "option_b": "Buy pullbacks on H1 with trend",
                                "option_c": "Trade both directions",
                                "option_d": "Avoid trading",
                                "correct_answer": "B",
                                "explanation": "Trade in direction of higher timeframe trend. H1 pullback in daily uptrend = buying opportunity.",
                                "topic_slug": "trend_analysis"
                            },
                            {
                                "question": "Mistake: Selling because price is 'too high' in uptrend. Risk?",
                                "option_a": "Missing continued trend",
                                "option_b": "Immediate profit",
                                "option_c": "Lower risk",
                                "option_d": "Better fills",
                                "correct_answer": "A",
                                "explanation": "Markets can stay 'expensive' longer than you can stay solvent. Trend trade until structure breaks.",
                                "topic_slug": "trend_analysis"
                            }
                        ]
                    },
                    {
                        "title": "Multi-Timeframe Analysis",
                        "content": """## Simple Definition
Use higher timeframes to identify the major trend direction (the "road"), then use lower timeframes to time your entry (the "vehicle").

## Concept Explanation
**The Top-Down Approach**:
1. **Daily Chart (The Road)**: Are we driving north or south? (Trend direction)
2. **H4 Chart (The Highway)**: Where are the exits? (Key levels)
3. **H1 Chart (The Vehicle)**: When do I press the gas? (Entry trigger)

**Why It Works**:
- Daily trends persist for weeks. Trading against them is swimming upstream.
- H4 levels are respected by institutions. These are your targets.
- H1 provides tight stops and precise risk management.

## Step-by-Step Breakdown
**Triple Screen Analysis**:
1. **Screen 1 (Daily)**: Mark major trend and key support/resistance zones
2. **Screen 2 (H4)**: Identify pullback areas (20/50 EMA confluence)
3. **Screen 3 (H1)**: Wait for candlestick confirmation (engulfing, pin bar)
4. **Execute**: Only trade when all three timeframes align

## Real Trading Example
**The Perfect Alignment**:
- **Daily**: GBP/USD in clear uptrend, above 200 EMA
- **H4**: Pullback to 50 EMA at 1.2750 (dynamic support)
- **H1**: Bullish pin bar with long lower wick at 1.2750
- **Entry**: 1.2755 (break of pin bar high)
- **Stop**: 1.2725 (below pin bar low and H4 support)
- **Target**: 1.2850 (previous daily high)
- **Risk**: 30 pips. **Reward**: 95 pips. **R:R**: 1:3.2

<div class="ac-tradingview-widget" data-symbol="FX:GBPUSD"></div>

## Common Beginner Mistake
**Timeframe Confusion**: Analyzing H1 for trend direction, then trying to trade daily charts for entries. This is backwards—H1 trends change every few hours. Daily trends change every few weeks.

## Key Takeaway
Higher timeframes for direction, lower timeframes for execution. If Daily and H4 disagree, wait. When they agree, strike with confidence.

## Practice Question
Which timeframe should you use to determine the major trend direction?""",
                        "quiz": [
                            {
                                "question": "Best timeframe for major trend direction?",
                                "option_a": "M5",
                                "option_b": "H1",
                                "option_c": "Daily",
                                "option_d": "Monthly",
                                "correct_answer": "C",
                                "explanation": "Daily chart shows the major trend that persists for weeks. Trade in this direction.",
                                "topic_slug": "timeframe_analysis"
                            },
                            {
                                "question": "Which timeframe for entry timing?",
                                "option_a": "Monthly",
                                "option_b": "Weekly",
                                "option_c": "Daily",
                                "option_d": "H1 or H4",
                                "correct_answer": "D",
                                "explanation": "H1/H4 provide precise entry points with tight stops while respecting daily trend.",
                                "topic_slug": "timeframe_analysis"
                            },
                            {
                                "question": "Daily shows uptrend, H1 shows downtrend. Trade direction?",
                                "option_a": "Short on H1",
                                "option_b": "Long with daily trend",
                                "option_c": "Avoid trading",
                                "option_d": "Trade both",
                                "correct_answer": "B",
                                "explanation": "Always prioritize higher timeframe. H1 pullback in daily uptrend = buy opportunity.",
                                "topic_slug": "timeframe_analysis"
                            },
                            {
                                "question": "Scenario: Daily and H4 disagree on trend. Action?",
                                "option_a": "Trade H4 direction",
                                "option_b": "Wait for alignment",
                                "option_c": "Trade daily direction only",
                                "option_d": "Increase size",
                                "correct_answer": "B",
                                "explanation": "When timeframes conflict, stay flat. Wait for alignment to increase probability.",
                                "topic_slug": "timeframe_analysis"
                            },
                            {
                                "question": "Mistake: Using H1 trend to trade daily charts. Risk?",
                                "option_a": "Better entries",
                                "option_b": "Choppy, inconsistent signals",
                                "option_c": "Lower risk",
                                "option_d": "More profit",
                                "correct_answer": "B",
                                "explanation": "H1 trends change every few hours. Using them for daily trades causes whipsaws.",
                                "topic_slug": "timeframe_analysis"
                            }
                        ]
                    }
                ]
            },
            {
                "title": "Support and Resistance Advanced",
                "description": "Drawing levels that professionals actually use.",
                "lessons": [
                    {
                        "title": "Drawing Professional Levels",
                        "content": """## Simple Definition
Clean levels are those with 3+ touches, visible on multiple timeframes, and aligned with other technical confluence factors (moving averages, round numbers, Fibonacci).

## Concept Explanation
**The 3-Touch Rule**:
- 1 touch = random price action
- 2 touches = possible level, wait for 3rd
- 3+ touches = valid support/resistance
- 5+ touches = strong level (but likely to break soon)

**Zone vs Line**:
- **Lines**: Exact prices (1.0850) — too precise, markets are messy
- **Zones**: 10-20 pip ranges (1.0840–1.0860) — realistic, allows for wicks

**Confluence Factors**:
- Round numbers (1.1000) — psychological
- Moving averages (50 EMA) — dynamic support
- Fibonacci retracements (61.8%) — mathematical support
- Previous breakout points — role reversal levels

## Step-by-Step Breakdown
**Drawing Clean Support**:
1. Find 3+ lows at similar horizontal area (±15 pips)
2. Extend line 20 candles into the past and future
3. Check H4 and Daily — does level appear there too?
4. Mark zone with rectangle, not single line
5. Delete old levels that haven't been touched in 50+ candles

## Real Trading Example
**The Confluence Zone**:
- EUR/USD pulls back to 1.0850
- **Confluence Factors**:
  - Round number (1.0850)
  - Previous resistance now support (role reversal)
  - 50 EMA at 1.0848
  - 61.8% Fibonacci at 1.0852
- **Zone**: 1.0845–1.0855 (10 pips)
- **Entry**: Buy at 1.0850
- **Stop**: 1.0835 (below zone)
- **Probability**: 4 factors align = high probability bounce

<svg class="ac-svg-diagram" viewBox="0 0 200 100">
  <rect x="20" y="30" width="160" height="20" fill="rgba(34,197,94,0.1)" stroke="#22c55e" stroke-dasharray="3,3"/>
  <text x="100" y="25" text-anchor="middle" fill="#22c55e" font-size="8">Support Zone (10 pips)</text>
  <line x1="20" y1="40" x2="180" y2="40" stroke="#22c55e" stroke-width="2"/>
  <circle cx="40" cy="50" r="2" fill="#60a5fa"/>
  <circle cx="80" cy="48" r="2" fill="#60a5fa"/>
  <circle cx="120" cy="52" r="2" fill="#60a5fa"/>
  <circle cx="160" cy="50" r="2" fill="#60a5fa"/>
  <path d="M 40 50 Q 60 30 80 48 T 120 52 T 160 50" fill="none" stroke="#60a5fa" stroke-width="1"/>
</svg>

## Common Beginner Mistake
**Spaghetti Charts**: Beginners draw 20+ lines covering every tiny high and low. This creates analysis paralysis. Professional charts have 3-5 clean levels maximum.

## Key Takeaway
Quality over quantity. One level with 4 touches and confluence beats 10 random lines. Delete levels that haven't been relevant in weeks.

## Practice Question
How many touches are typically required to validate a support or resistance level as significant?""",
                        "quiz": [
                            {
                                "question": "How many touches to validate a level?",
                                "option_a": "1",
                                "option_b": "2",
                                "option_c": "3 or more",
                                "option_d": "10",
                                "correct_answer": "C",
                                "explanation": "Need 3+ touches to validate level as significant support/resistance.",
                                "topic_slug": "advanced_snr"
                            },
                            {
                                "question": "What creates the strongest levels?",
                                "option_a": "Single touch",
                                "option_b": "Two touches",
                                "option_c": "3+ touches + confluence",
                                "option_d": "Random lines",
                                "correct_answer": "C",
                                "explanation": "More touches + confluence (Fibonacci, round numbers) = stronger level.",
                                "topic_slug": "advanced_snr"
                            },
                            {
                                "question": "Why use zones (10-20 pips) vs exact lines?",
                                "option_a": "Less precise",
                                "option_b": "Markets are messy, zones catch wicks",
                                "option_c": "Easier to draw",
                                "option_d": "No difference",
                                "correct_answer": "B",
                                "explanation": "Exact lines cause missed trades. Zones account for market noise and wicks.",
                                "topic_slug": "advanced_snr"
                            },
                            {
                                "question": "Scenario: Level has 5 touches over 6 months but none recently. Action?",
                                "option_a": "Keep it active",
                                "option_b": "Delete or mark as inactive",
                                "option_c": "Trade it aggressively",
                                "option_d": "Increase position size",
                                "correct_answer": "B",
                                "explanation": "Untouched levels for 50+ candles lose relevance. Focus on recent price action.",
                                "topic_slug": "advanced_snr"
                            },
                            {
                                "question": "Mistake: Drawing 20+ lines on chart. Result?",
                                "option_a": "Better analysis",
                                "option_b": "Analysis paralysis",
                                "option_c": "More profits",
                                "option_d": "Clearer signals",
                                "correct_answer": "B",
                                "explanation": "Too many lines cause confusion. Use 3-5 clean levels maximum.",
                                "topic_slug": "advanced_snr"
                            }
                        ]
                    },
                    {
                        "title": "Dynamic Support with Moving Averages",
                        "content": """## Simple Definition
Moving averages act as dynamic support and resistance that update every candle. Unlike static horizontal lines, they follow price and indicate trend strength.

## Concept Explanation
**The Three Amigos**:
- **20 EMA**: Short-term trend, immediate support/resistance. Price respects this on H1/H4.
- **50 EMA**: Medium-term trend, deeper pullback level. Major institutions watch this.
- **200 EMA**: Long-term trend separator. Above = bullish bias, below = bearish bias.

**Golden Cross / Death Cross**:
- **Golden**: 50 EMA crosses above 200 EMA = long-term bullish signal
- **Death**: 50 EMA crosses below 200 EMA = long-term bearish signal

## Step-by-Step Breakdown
**Trading the EMA Bounce**:
1. Identify trend direction (price vs 200 EMA)
2. Wait for pullback to 20 or 50 EMA
3. Look for candlestick confirmation at EMA (pin bar, engulfing)
4. Enter in direction of major trend
5. Stop loss below the EMA (plus buffer)

## Real Trading Example
**The EMA Trio Trade**:
- **Daily**: Price above 200 EMA (bullish bias)
- **H4**: Pullback to 50 EMA at 1.2500
- **H1**: Bullish hammer forms at 50 EMA
- **Entry**: Buy 1.2510
- **Stop**: 1.2480 (below EMA and hammer low)
- **Target**: 1.2600 (previous high)
- **Logic**: Triple confluence (trend + level + candle)

<div class="ac-tradingview-widget" data-symbol="FX:EURUSD"></div>

## Common Beginner Mistake
**EMA Abuse**: Using 10 EMAs on one chart (8 EMA, 13 EMA, 21 EMA, etc.). This creates confusion as price constantly crosses different lines. Stick to 20/50/200.

## Key Takeaway
Moving averages show trend health. Price staying above 20 EMA = strong trend. Price crossing below 50 EMA = trend weakening. Respect these levels like horizontal support.

## Practice Question
What does the Golden Cross indicate?""",
                        "quiz": [
                            {
                                "question": "Golden Cross is when:",
                                "option_a": "50 EMA crosses above 200 EMA",
                                "option_b": "200 EMA crosses above 50",
                                "option_c": "Price crosses 20 EMA",
                                "option_d": "Two moving averages touch",
                                "correct_answer": "A",
                                "explanation": "50 EMA crossing above 200 EMA = Golden Cross (bullish signal).",
                                "topic_slug": "moving_averages"
                            },
                            {
                                "question": "Which EMA acts as immediate support/resistance?",
                                "option_a": "200 EMA",
                                "option_b": "50 EMA",
                                "option_c": "20 EMA",
                                "option_d": "All equal",
                                "correct_answer": "C",
                                "explanation": "20 EMA is short-term dynamic support/resistance on H1/H4 timeframes.",
                                "topic_slug": "moving_averages"
                            },
                            {
                                "question": "Calculate: Price 50 pips above 200 EMA. Trend strength?",
                                "option_a": "Weak",
                                "option_b": "Extended (possible pullback)",
                                "option_c": "Bearish",
                                "option_d": "No trend",
                                "correct_answer": "B",
                                "explanation": "Extended far above 200 EMA often indicates overbought conditions due for pullback.",
                                "topic_slug": "moving_averages"
                            },
                            {
                                "question": "Scenario: Price crosses below 50 EMA but above 200. Interpretation?",
                                "option_a": "Trend reversal",
                                "option_b": "Medium-term weakness, long-term bullish",
                                "option_c": "Buy immediately",
                                "option_d": "Strong uptrend",
                                "correct_answer": "B",
                                "explanation": "Below 50 EMA = medium-term weakening. Above 200 EMA = long-term still bullish (pullback, not reversal).",
                                "topic_slug": "moving_averages"
                            },
                            {
                                "question": "Mistake: Using 8 EMAs on one chart. Result?",
                                "option_a": "Better signals",
                                "option_b": "Conflicting signals and confusion",
                                "option_c": "Higher win rate",
                                "option_d": "Simpler analysis",
                                "correct_answer": "B",
                                "explanation": "Too many EMAs cause whipsaws and confusion. Use 20, 50, 200 only.",
                                "topic_slug": "moving_averages"
                            }
                        ]
                    }
                ]
            },
            {
                "title": "Chart Patterns",
                "description": "Reversals and continuations — flags, H&S, triangles.",
                "lessons": [
                    {
                        "title": "Reversal Patterns",
                                             "content": """## Simple Definition
Reversal patterns signal that an existing trend is ending and price is likely to move in the opposite direction. The most reliable patterns occur at major support/resistance with volume confirmation.

## Concept Explanation
**Head and Shoulders**:
- **Structure**: Three peaks with the middle peak (Head) highest and two outer peaks (Shoulders) roughly equal height
- **Neckline**: Support line connecting the two troughs between peaks
- **Signal**: Break below neckline confirms trend reversal from bullish to bearish
- **Target**: Measure distance from head to neckline, project downward from breakout point
- **Inverse H&S**: Same pattern upside down for bearish-to-bullish reversals

**Double Top / Double Bottom**:
- **Double Top**: Two peaks at similar resistance, signaling bearish reversal (M pattern)
- **Double Bottom**: Two troughs at similar support, signaling bullish reversal (W pattern)
- **Confirmation**: Break of the middle trough/neckline validates the pattern
- **Reliability**: More reliable on higher timeframes (H4, Daily)

## Step-by-Step Breakdown
**Trading Head and Shoulders**:
1. **Identify**: Locate three peaks with center highest
2. **Draw Neckline**: Connect the two lows between shoulders (support level)
3. **Wait**: Don't short the head formation—wait for neckline break
4. **Enter**: Sell break below neckline with momentum candle
5. **Stop**: Place above right shoulder (pattern invalidation point)
6. **Target**: Head-to-neckline distance projected downward

## Real Trading Example
**EUR/USD Daily Bearish Reversal**:
- **Left Shoulder**: 1.1200 (forms support at 1.1050)
- **Head**: 1.1300 (highest peak, support holds at 1.1050)
- **Right Shoulder**: 1.1180 (lower high, weakness showing)
- **Neckline**: 1.1050 (critical support)
- **Entry**: 1.1040 (break of neckline)
- **Stop**: 1.1200 (above right shoulder)
- **Target**: 1.0800 (1.1300 - 1.1050 = 250 pips down from 1.1050)
- **Result**: Price hits 1.0750 over next 3 weeks (350 pips profit)

<svg class="ac-svg-diagram" viewBox="0 0 400 250">
  <path d="M 50 180 L 120 100 L 180 60 L 240 100 L 300 180" fill="none" stroke="#60a5fa" stroke-width="3"/>
  <line x1="50" y1="180" x2="300" y2="180" stroke="#ef4444" stroke-width="2" stroke-dasharray="5,5"/>
  <text x="180" y="195" text-anchor="middle" fill="#ef4444" font-size="12">Neckline (Break = Sell)</text>
  <text x="180" y="50" text-anchor="middle" fill="#fbbf24" font-size="14" font-weight="bold">HEAD</text>
  <text x="85" y="90" text-anchor="middle" fill="#9ca3af" font-size="12">Left Shoulder</text>
  <text x="275" y="90" text-anchor="middle" fill="#9ca3af" font-size="12">Right Shoulder</text>
  <line x1="180" y1="60" x2="180" y2="180" stroke="#fbbf24" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="180" y1="180" x2="180" y2="240" stroke="#22c55e" stroke-width="2" marker-end="url(#arrowhead)"/>
  <text x="200" y="220" fill="#22c55e" font-size="12">Target</text>
</svg>

## Common Beginner Mistake
**Anticipating the Pattern**: Traders try to sell the "head" formation before the neckline breaks, assuming the pattern will complete. Patterns fail frequently—always wait for neckline break with candle close confirmation. Premature entries lead to losses when price continues higher instead.

## Key Takeaway
Reversal patterns are complete only after neckline breaks with momentum. The Head and Shoulders has a 70-75% success rate when formed at major resistance after extended uptrends. Measure targets conservatively—take partial profits at 100% projection and move stop to breakeven.

## Practice Question
Where should the stop loss be placed when trading a confirmed Head and Shoulders pattern?""",
                        "quiz": [
                            {
                                "question": "What confirms a Head and Shoulders pattern?",
                                "option_a": "Formation of three peaks",
                                "option_b": "Break below the neckline",
                                "option_c": "High volume on head formation",
                                "option_d": "Long upper wicks",
                                "correct_answer": "B",
                                "explanation": "The pattern is only confirmed when price breaks below the neckline support, validating the reversal.",
                                "topic_slug": "chart_patterns"
                            },
                            {
                                "question": "How is the profit target measured in H&S patterns?",
                                "option_a": "Head to right shoulder distance",
                                "option_b": "Head to neckline distance, projected down",
                                "option_c": "Left shoulder to head distance",
                                "option_d": "Random Fibonacci level",
                                "correct_answer": "B",
                                "explanation": "Measure vertical distance from head peak to neckline, then project that distance downward from neckline break point.",
                                "topic_slug": "chart_patterns"
                            },
                            {
                                "question": "Calculate: Head at 1.2000, Neckline at 1.1800. Breaks at 1.1790. Target?",
                                "option_a": "1.1600",
                                "option_b": "1.1590",
                                "option_c": "1.1790",
                                "option_d": "1.2200",
                                "correct_answer": "B",
                                "explanation": "Head-neckline = 200 pips. 1.1790 - 0.0200 = 1.1590 target.",
                                "topic_slug": "chart_patterns"
                            },
                            {
                                "question": "Scenario: Price forms head and right shoulder but reverses up before breaking neckline.",
                                "option_a": "Pattern failed, pattern invalidated",
                                "option_b": "Enter early",
                                "option_c": "Increase position size",
                                "option_d": "Pattern still valid",
                                "correct_answer": "A",
                                "explanation": "If neckline doesn't break, the pattern is invalid. Don't assume it will complete later.",
                                "topic_slug": "chart_patterns"
                            },
                            {
                                "question": "Mistake: Selling at the head formation before neckline break. Risk?",
                                "option_a": "Missing profit",
                                "option_b": "Pattern may never complete, premature entry",
                                "option_c": "Better fills",
                                "option_d": "Lower risk",
                                "correct_answer": "B",
                                "explanation": "Selling the formation early assumes pattern completion. Price may continue higher, causing losses.",
                                "topic_slug": "chart_patterns"
                            }
                        ]
                    },
                    {
                        "title": "Continuation Patterns",
                        "content": """## Simple Definition
Continuation patterns are consolidation zones within trending markets where price pauses before resuming the original trend. Unlike reversals, these suggest temporary rest, not trend change.

## Concept Explanation
**Bull Flag / Bear Flag**:
- **Structure**: Strong trending pole followed by small parallel channel against trend
- **Bull Flag**: Steep rise (pole) followed by downward sloping channel (consolidation)
- **Bear Flag**: Sharp drop (pole) followed by upward sloping channel
- **Entry**: Break in direction of original trend
- ** psychology**: Profit-taking after strong move, then continuation

**Triangles (Ascending, Descending, Symmetrical)**:
- **Ascending**: Flat top, rising bottom (bullish bias)
- **Descending**: Flat bottom, falling top (bearish bias)  
- **Symmetrical**: Conginging trendlines, breakout direction determines trade
- **Breakout**: Usually occurs 60-75% through triangle formation

**Pennants**:
- Similar to flags but consolidation is triangular (converging) rather than rectangular
- Smaller than flags, usually 1-2 weeks duration
- Breakout often explosive due to compression

## Step-by-Step Breakdown
**Trading the Bull Flag**:
1. **Identify Pole**: Strong bullish candle series (200+ pips), high volume
2. **Mark Channel**: Two parallel lines containing pullback/consolidation
3. **Wait**: Price must touch lower channel at least twice
4. **Enter**: Buy break above upper channel line
5. **Stop**: Below lowest point of flag formation (pole base)
6. **Target**: Length of pole projected upward from breakout

## Real Trading Example
**GBP/JPY Bear Flag Continuation**:
- **Pole**: Drops from 185.00 to 182.00 (300 pips) in 2 days
- **Flag**: Consolidates 182.00-183.00 for 3 days (upward channel)
- **Entry**: 181.90 (break below flag support)
- **Stop**: 183.20 (above flag high)
- **Target**: 179.00 (300 pips down from breakout)
- **Logic**: Sellers took profit at 182, new shorts enter on break
- **Result**: Hits 179.00 in 48 hours

<svg class="ac-svg-diagram" viewBox="0 0 400 200">
  <line x1="50" y1="150" x2="150" y2="50" stroke="#ef4444" stroke-width="3"/>
  <text x="100" y="80" fill="#ef4444" font-size="12">Pole (Strong Trend)</text>
  <path d="M 150 50 L 200 80 L 250 60 L 300 70" fill="none" stroke="#fbbf24" stroke-width="2"/>
  <line x1="150" y1="85" x2="300" y2="55" stroke="#9ca3af" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="170" y1="95" x2="320" y2="65" stroke="#9ca3af" stroke-width="1" stroke-dasharray="3,3"/>
  <text x="225" y="45" fill="#fbbf24" font-size="12">Flag Channel</text>
  <line x1="300" y1="70" x2="350" y2="20" stroke="#ef4444" stroke-width="3" marker-end="url(#arrow)"/>
  <text x="330" y="50" fill="#ef4444" font-size="12">Breakout</text>
</svg>

## Common Beginner Mistake
**Counter-Trend Trading the Consolidation**: Beginners see flag forming and think "it's going up in a downtrend, I'll buy!" They trade against the pole direction. Flags are continuation patterns—trade WITH the pole direction, not against it.

## Key Takeaway
Flags and pennants are rest stops for trending markets. The pole direction tells you which way to trade. Never trade inside the pattern—wait for breakout in trend direction with volume confirmation.

## Practice Question
When trading a bear flag pattern, which direction should you trade the breakout?""",
                        "quiz": [
                            {
                                "question": "What does a flag pattern indicate?",
                                "option_a": "Trend reversal",
                                "option_b": "Trend continuation after consolidation",
                                "option_c": "Market top",
                                "option_d": "Low volatility permanently",
                                "correct_answer": "B",
                                "explanation": "Flags are continuation patterns—temporary consolidation before trend resumes.",
                                "topic_slug": "chart_patterns"
                            },
                            {
                                "question": "In a bull flag, the consolidation channel slopes:",
                                "option_a": "Upward",
                                "option_b": "Downward",
                                "option_c": "Flat horizontal",
                                "option_d": "Vertically",
                                "correct_answer": "B",
                                "explanation": "Bull flags slope downward against trend as traders take profits, then buyers step back in.",
                                "topic_slug": "chart_patterns"
                            },
                            {
                                "question": "Calculate: Pole is 150 pips up. Flag forms. Breakout at 1.2000. Target?",
                                "option_a": "1.1850",
                                "option_b": "1.2000",
                                "option_c": "1.2150",
                                "option_d": "1.3500",
                                "correct_answer": "C",
                                "explanation": "Project pole length from breakout: 1.2000 + 0.0150 = 1.2150.",
                                "topic_slug": "chart_patterns"
                            },
                            {
                                "question": "Scenario: Strong uptrend, flag forming. You see bullish candle inside flag. Action?",
                                "option_a": "Buy immediately",
                                "option_b": "Wait for upper channel breakout",
                                "option_c": "Sell short",
                                "option_d": "Double position",
                                "correct_answer": "B",
                                "explanation": "Don't trade inside patterns. Wait for confirmed breakout above flag resistance.",
                                "topic_slug": "chart_patterns"
                            },
                            {
                                "question": "Mistake: Buying a bear flag because 'it looks bullish'. Result?",
                                "option_a": "Profit when trend reverses",
                                "option_b": "Loss when trend continues down",
                                "option_c": "Guaranteed win",
                                "option_d": "No effect",
                                "correct_answer": "B",
                                "explanation": "Bear flags resolve downward. Counter-trend trading leads to losses when pole trend continues.",
                                "topic_slug": "chart_patterns"
                            }
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
A Pin Bar (Pinocchio bar) is a candlestick with a long wick and small body, showing sharp price rejection. The long wick "lies" about where price is going (hence the name), signaling potential reversal.

## Concept Explanation
**Bullish Pin Bar**:
- **Appearance**: Long lower wick (2-3x body length), small body at top
- **Meaning**: Sellers pushed price down, but buyers aggressively rejected lower prices
- **Location**: Best at support levels or bottom of downtrend
- **Entry**: Buy above pin bar high
- **Stop**: Below pin bar low

**Bearish Pin Bar**:
- **Appearance**: Long upper wick, small body at bottom
- **Meaning**: Buyers pushed up, sellers rejected higher prices
- **Location**: Best at resistance levels or top of uptrend
- **Entry**: Sell below pin bar low

**Rejection Wicks**:
- Any candle with wick extending far beyond body shows rejection
- Context matters: wick at support = bullish; wick at resistance = bearish

## Step-by-Step Breakdown
**Trading the Pin Bar**:
1. **Locate Context**: Identify support/resistance or trend extreme
2. **Spot Pattern**: Look for long wick (3x body minimum), small opposite-side body
3. **Confirm**: Next candle should close in direction of pin bar signal
4. **Enter**: Break of pin bar high (bullish) or low (bearish)
5. **Manage**: 50% take profit at 1R, move stop to breakeven

## Real Trading Example
**EUR/USD Support Bounce**:
- **Context**: Triple touch support at 1.0850 (strong level)
- **Pin Bar**: H4 candle: Open 1.0850, Low 1.0820 (30-pip wick), Close 1.0855
- **Analysis**: 30-pip lower wick shows strong rejection of 1.0820
- **Entry**: Buy 1.0860 (break above pin bar)
- **Stop**: 1.0815 (below wick low)
- **Target**: 1.0900 (next resistance, 40 pips)
- **Risk**: 45 pips. **Reward**: 40 pips. **Adjustment**: Wait for better R:R or take 50% at 1.0880

<svg class="ac-svg-diagram" viewBox="0 0 200 300">
  <line x1="100" y1="50" x2="100" y2="250" stroke="#60a5fa" stroke-width="2"/>
  <rect x="85" y="80" width="30" height="20" fill="#22c55e" opacity="0.8"/>
  <line x1="100" y1="80" x2="100" y2="40" stroke="#22c55e" stroke-width="2"/>
  <text x="120" y="70" fill="#22c55e" font-size="10">Upper Wick</text>
  <line x1="100" y1="100" x2="100" y2="260" stroke="#22c55e" stroke-width="2"/>
  <text x="120" y="180" fill="#22c55e" font-size="10">Long Lower Wick</text>
  <text x="100" y="280" text-anchor="middle" fill="#9ca3af" font-size="12">Strong Buying Pressure</text>
</svg>

## Common Beginner Mistake
**Trading Every Pin Bar**: Pin bars appear constantly. A pin bar in the middle of a range or against strong trend is a trap. Only trade pins at clear support/resistance with confluence (trendline, moving average, or Fibonacci).

## Key Takeaway
The wick tells the story of rejection. Long wick = strong rejection of that price level. Trade pin bars only at significant levels where institutions defend prices.

## Practice Question
What is the minimum recommended wick-to-body ratio for a valid pin bar?""",
                        "quiz": [
                            {
                                "question": "What characterizes a bullish pin bar?",
                                "option_a": "Long upper wick, small body at bottom",
                                "option_b": "Long lower wick, small body at top",
                                "option_c": "No wicks, large body",
                                "option_d": "Equal wicks both sides",
                                "correct_answer": "B",
                                "explanation": "Bullish pin bar has long lower wick showing rejection of lower prices, with small body near high.",
                                "topic_slug": "candlestick_patterns"
                            },
                            {
                                "question": "Where do pin bars work best?",
                                "option_a": "Middle of range",
                                "option_b": "Strong support/resistance only",
                                "option_c": "During high volatility news",
                                "option_d": "Any random location",
                                "correct_answer": "B",
                                "explanation": "Pin bars require context. They work best at key technical levels where rejection has meaning.",
                                "topic_slug": "candlestick_patterns"
                            },
                            {
                                "question": "Calculate: Pin bar body is 5 pips, lower wick is 15 pips. Ratio?",
                                "option_a": "1:1",
                                "option_b": "2:1",
                                "option_c": "3:1",
                                "option_d": "4:1",
                                "correct_answer": "C",
                                "explanation": "Wick (15) ÷ Body (5) = 3:1 ratio. Minimum 2:1 required, 3:1 is ideal.",
                                "topic_slug": "candlestick_patterns"
                            },
                            {
                                "question": "Scenario: Bearish pin bar at all-time high resistance. Action?",
                                "option_a": "Ignore it",
                                "option_b": "Sell break below pin bar low",
                                "option_c": "Buy immediately",
                                "option_d": "Remove all stops",
                                "correct_answer": "B",
                                "explanation": "Bearish pin bar at resistance is high-probability short setup. Enter on break of low.",
                                "topic_slug": "candlestick_patterns"
                            },
                            {
                                "question": "Mistake: Trading pin bar mid-trend without level. Risk?",
                                "option_a": "High probability setup",
                                "option_b": "No confluence, likely continuation pattern",
                                "option_c": "Guaranteed profit",
                                "option_d": "Lower spreads",
                                "correct_answer": "B",
                                "explanation": "Pins without support/resistance confluence often fail as price continues trending.",
                                "topic_slug": "candlestick_patterns"
                            }
                        ]
                    },
                    {
                        "title": "Engulfing Patterns and Doji",
                        "content": """## Simple Definition
Engulfing patterns occur when one candle completely engulfs the previous candle's body, showing overwhelming shift in momentum. Doji candles show complete indecision with equal open and close.

## Concept Explanation
**Bullish Engulfing**:
- **Structure**: Green candle where body completely covers previous red candle's body
- **Psychology**: Buyers overwhelmed sellers from previous session
- **Location**: Bottom of downtrend or at strong support
- **Confirmation**: Next candle closes higher

**Bearish Engulfing**:
- **Structure**: Red candle body completely covers previous green body
- **Psychology**: Sellers took control from buyers
- **Location**: Top of uptrend or strong resistance
- **Confirmation**: Next candle closes lower

**Doji Types**:
- **Standard Doji**: Open = Close, small wicks (indecision)
- **Dragonfly Doji**: Long lower wick (bullish reversal at support)
- **Gravestone Doji**: Long upper wick (bearish reversal at resistance)
- **Long-Legged Doji**: Long wicks both sides (major indecision, trend change likely)

## Step-by-Step Breakdown
**Trading Engulfing Patterns**:
1. **Identify Trend**: Must be at end of extended move (not middle)
2. **Spot Pattern**: Second candle body fully engulfs first candle body (shadows don't matter)
3. **Check Size**: Engulfing candle should be larger than average (high volume)
4. **Enter**: Break above engulfing high (bullish) or below low (bearish)
5. **Stop**: Beyond pattern extreme (below bullish engulfing low)

## Real Trading Example
**USD/JPY Bearish Engulfing at Resistance**:
- **Context**: Approaches 147.00 resistance (previous high)
- **Day 1**: Green candle 146.50-147.00 (50 pips)
- **Day 2**: Red candle 147.00-145.80 (engulfs previous body completely)
- **Volume**: Higher on Day 2 (institutional selling)
- **Entry**: Sell 145.75 (break of engulfing low)
- **Stop**: 147.10 (above pattern high)
- **Target**: 144.00 (previous support, 175 pips)
- **Risk**: 135 pips. **Reward**: 175 pips. **R:R**: 1:1.3 (acceptable due to strong signal)

<div class="ac-tradingview-widget" data-symbol="FX:USDJPY"></div>

## Common Beginner Mistake
**Trading Small Engulfing Patterns**: Engulfing candles must show conviction—significantly larger than surrounding candles. Small engulfing in quiet markets are just noise, not trend changes.

## Key Takeaway
Engulfing patterns show conviction shifts. Bullish engulfing at support = buyers defending. Bearish engulfing at resistance = sellers active. Doji shows exhaustion—prepare for breakout direction next candle.

## Practice Question
What must be true about the second candle in a bullish engulfing pattern?""",
                        "quiz": [
                            {
                                "question": "Bullish engulfing requires:",
                                "option_a": "Green candle bigger than previous red body",
                                "option_b": "Any green candle after red",
                                "option_c": "Long upper wick",
                                "option_d": "Small body",
                                "correct_answer": "A",
                                "explanation": "Bullish engulfing requires current green candle body to completely cover previous red candle body.",
                                "topic_slug": "candlestick_patterns"
                            },
                            {
                                "question": "What does a Gravestone Doji indicate?",
                                "option_a": "Strong buying",
                                "option_b": "Bullish continuation",
                                "option_c": "Rejection of higher prices",
                                "option_d": "Low volatility",
                                "correct_answer": "C",
                                "explanation": "Gravestone doji has long upper wick showing rejection of higher prices—bearish at resistance.",
                                "topic_slug": "candlestick_patterns"
                            },
                            {
                                "question": "Calculate: Bearish engulfing at resistance, 50-pip stop. Minimum target for 1:2 R:R?",
                                "option_a": "25 pips",
                                "option_b": "50 pips",
                                "option_c": "100 pips",
                                "option_d": "200 pips",
                                "correct_answer": "C",
                                "explanation": "For 1:2 risk/reward with 50-pip risk, target must be 100 pips away.",
                                "topic_slug": "candlestick_patterns"
                            },
                            {
                                "question": "Scenario: Doji forms after strong 200-pip uptrend. Interpretation?",
                                "option_a": "Buy more",
                                "option_b": "Trend exhaustion, prepare for reversal",
                                "option_c": "Sell immediately",
                                "option_d": "Ignore",
                                "correct_answer": "B",
                                "explanation": "Doji after extended move shows exhaustion. Wait for next candle direction confirmation.",
                                "topic_slug": "candlestick_patterns"
                            },
                            {
                                "question": "Mistake: Trading engulfing in middle of range. Why wrong?",
                                "option_a": "Too profitable",
                                "option_b": "No trend context, just noise",
                                "option_c": "Guaranteed success",
                                "option_d": "Better fills",
                                "correct_answer": "B",
                                "explanation": "Engulfing patterns need trend context. In ranges, they're just normal oscillation noise.",
                                "topic_slug": "candlestick_patterns"
                            }
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
RSI (Relative Strength Index) measures momentum on a 0-100 scale. It identifies overbought conditions (potential sells) and oversold conditions (potential buys), plus divergence signals.

## Concept Explanation
**RSI Levels**:
- **Above 70**: Overbought (price may fall, but can stay overbought in strong trends)
- **Below 30**: Oversold (price may rise, but can stay oversold in crashes)
- **50 Level**: Bullish above, Bearish below (trend filter)
- **Centerline Cross**: RSI crossing 50 can signal trend shifts

**Divergence** (Most Reliable Signal):
- **Bullish Divergence**: Price makes lower low, RSI makes higher low (buy signal)
- **Bearish Divergence**: Price makes higher high, RSI makes lower high (sell signal)
- **Hidden Bullish**: Price higher low, RSI lower low (trend continuation)
- **Hidden Bearish**: Price lower high, RSI higher high (trend continuation)

## Step-by-Step Breakdown
**Trading RSI Divergence**:
1. **Identify Trend**: Mark swing highs and lows on price
2. **Compare RSI**: Check corresponding RSI highs/lows at same points
3. **Spot Divergence**: Price and RSI moving opposite directions?
4. **Confirm**: Wait for price to show reversal candle at divergence point
5. **Enter**: Trade reversal direction with stop beyond recent extreme
6. **Manage**: Divergence can persist—use tight risk management

## Real Trading Example
**EUR/USD Bullish Divergence**:
- **Price Action**: Drops from 1.1000 to 1.0850 (new low), then 1.0800 (lower low)
- **RSI Check**: First low RSI 28, second low RSI 35 (higher low)
- **Divergence**: Price lower, RSI higher = Bullish divergence
- **Confirmation**: Bullish engulfing at 1.0800
- **Entry**: Buy 1.0810
- **Stop**: 1.0780 (below divergence low)
- **Target**: 1.0900 (previous resistance)
- **Result**: RSI divergence predicts momentum shift before price shows it

<svg class="ac-svg-diagram" viewBox="0 0 400 200">
  <path d="M 50 150 L 100 120 L 150 140 L 200 80" fill="none" stroke="#ef4444" stroke-width="2"/>
  <text x="220" y="80" fill="#ef4444" font-size="12">Price Lower Low</text>
  <path d="M 50 150 L 100 130 L 150 145 L 200 100" fill="none" stroke="#22c55e" stroke-width="2" stroke-dasharray="5,5"/>
  <text x="220" y="100" fill="#22c55e" font-size="12">RSI Higher Low</text>
  <text x="200" y="180" text-anchor="middle" fill="#fbbf24" font-size="14" font-weight="bold">BULLISH DIVERGENCE</text>
</svg>

## Common Beginner Mistake
**RSI Overbought = Immediate Short**: Beginners see RSI > 70 and sell immediately. In strong uptrends, RSI can stay overbought for weeks while price continues higher. Always use RSI with price action confirmation, not as standalone signal.

## Key Takeaway
RSI measures momentum, not just overbought/oversold. Divergence between price and RSI is the highest-probability signal—showing that momentum is shifting before price reflects it. Never trade RSI alone; always confirm with support/resistance or candlestick patterns.

## Practice Question
What does bullish divergence indicate when price makes a lower low but RSI makes a higher low?""",
                        "quiz": [
                            {
                                "question": "RSI above 70 indicates:",
                                "option_a": "Guaranteed reversal down",
                                "option_b": "Overbought conditions, potential reversal",
                                "option_c": "Strong bearish trend",
                                "option_d": "Low volatility",
                                "correct_answer": "B",
                                "explanation": "RSI >70 shows overbought conditions, but in strong trends price can stay overbought. Wait for confirmation.",
                                "topic_slug": "indicators"
                            },
                            {
                                "question": "What is bullish divergence?",
                                "option_a": "Price and RSI both rising",
                                "option_b": "Price lower low, RSI higher low",
                                "option_c": "Price higher high, RSI higher high",
                                "option_d": "RSI above 70",
                                "correct_answer": "B",
                                "explanation": "Bullish divergence occurs when price drops to lower low but RSI forms higher low, showing momentum strengthening.",
                                "topic_slug": "indicators"
                            },
                            {
                                "question": "Calculate: RSI is 75, price at resistance with bearish pin bar. Signal?",
                                "option_a": "Strong buy",
                                "option_b": "Overbought + rejection = sell",
                                "option_c": "Hold longs",
                                "option_d": "Add to longs",
                                "correct_answer": "B",
                                "explanation": "Overbought RSI (75) combined with price rejection at resistance = high-probability short setup.",
                                "topic_slug": "indicators"
                            },
                            {
                                "question": "Scenario: Strong uptrend, RSI 85 for 5 days. Action?",
                                "option_a": "Sell immediately because overbought",
                                "option_b": "Wait for price action reversal, trend may continue",
                                "option_c": "Buy more",
                                "option_d": "Double position",
                                "correct_answer": "B",
                                "explanation": "RSI can remain overbought in strong trends. Wait for bearish price action before counter-trend trading.",
                                "topic_slug": "indicators"
                            },
                            {
                                "question": "Mistake: Trading RSI overbought without price confirmation. Risk?",
                                "option_a": "Missing trend continuation",
                                "option_b": "Selling into strong trend, getting stopped out",
                                "option_c": "Guaranteed profit",
                                "option_d": "Lower risk",
                                "correct_answer": "B",
                                "explanation": "Without price confirmation, RSI overbought signals fail in trending markets causing losses.",
                                "topic_slug": "indicators"
                            }
                        ]
                    },
                    {
                        "title": "MACD and Moving Averages",
                        "content": """## Simple Definition
MACD (Moving Average Convergence Divergence) shows the relationship between two moving averages (12 and 26 EMA). It consists of the MACD line, Signal line (9 EMA of MACD), and Histogram showing momentum strength.

## Concept Explanation
**MACD Components**:
- **MACD Line**: 12 EMA minus 26 EMA (faster moving)
- **Signal Line**: 9 EMA of MACD Line (slower trigger)
- **Histogram**: MACD Line minus Signal Line (momentum visualization)
- **Zero Line**: Centerline separating bullish/bearish momentum

**Signals**:
- **Crossover**: MACD crosses above Signal = Buy. Below = Sell.
- **Zero Line Cross**: MACD crosses above 0 = Bullish trend shift
- **Histogram**: Growing bars = accelerating momentum. Shrinking = deceleration.
- **Divergence**: Price makes high, MACD makes lower high = Bearish divergence

**Moving Average Confluence**:
- Price above 20, 50, 200 EMA = Strong uptrend (buy pullbacks to 20 EMA)
- Death Cross (50 crosses below 200) = Long-term bearish
- Golden Cross (50 crosses above 200) = Long-term bullish

## Step-by-Step Breakdown
**Trading MACD Crossovers**:
1. **Check Trend**: Price above/below 200 EMA for bias
2. **Wait Cross**: MACD crosses Signal line in trend direction
3. **Histogram**: Bars should expand (momentum confirmation)
4. **Entry**: Price pullback to MA + MACD cross alignment
5. **Stop**: Beyond recent swing point or opposite side of MA

## Real Trading Example
**Trend Following Setup**:
- **Daily**: Price above 200 EMA (bullish bias)
- **H4**: Pullback to 50 EMA, MACD histogram shrinking (momentum fading)
- **H1**: MACD crosses above Signal line at 50 EMA support
- **Entry**: Buy at 50 EMA with MACD cross confirmation
- **Stop**: Below 50 EMA and recent low
- **Logic**: Trend (Daily) + Pullback (H4) + Momentum Shift (MACD) = High probability

<div class="ac-tradingview-widget" data-symbol="FX:EURUSD"></div>

## Common Beginner Mistake
**MACD Lag Trading**: MACD is lagging (based on MAs). Trading every cross leads to entering late and exiting late. Use MACD for trend confirmation and divergence only, not as primary entry trigger.

## Key Takeaway
MACD confirms trend direction and momentum but lags price. Best used to: 1) Confirm trend direction (above/below zero), 2) Identify divergence warnings, 3) Time entries in established trends. Never use MACD alone in ranging markets.

## Practice Question
What does it indicate when the MACD line crosses above the Signal line while above the zero line?""",
                        "quiz": [
                            {
                                "question": "MACD crossing above Signal line indicates:",
                                "option_a": "Bearish momentum",
                                "option_b": "Bullish momentum shift",
                                "option_c": "No change",
                                "option_d": "Market closed",
                                "correct_answer": "B",
                                "explanation": "MACD crossing above Signal = bullish momentum acceleration (buy signal in uptrends).",
                                "topic_slug": "indicators"
                            },
                            {
                                "question": "Histogram shrinking while price rising shows:",
                                "option_a": "Increasing momentum",
                                "option_b": "Momentum deceleration, potential reversal",
                                "option_c": "Strong trend",
                                "option_d": "Low volatility",
                                "correct_answer": "B",
                                "explanation": "Shrinking histogram = momentum slowing even if price still rising. Early warning of potential reversal.",
                                "topic_slug": "indicators"
                            },
                            {
                                "question": "Calculate: Price 100 pips above 200 EMA, MACD crosses below signal. Interpretation?",
                                "option_a": "Trend continuation buy",
                                "option_b": "Overextended trend, potential pullback",
                                "option_c": "Golden cross",
                                "option_d": "No significance",
                                "correct_answer": "B",
                                "explanation": "Price far above 200 EMA + MACD bearish cross suggests overextended market due for pullback.",
                                "topic_slug": "indicators"
                            },
                            {
                                "question": "Scenario: MACD shows bullish cross but price below 200 EMA. Action?",
                                "option_a": "Buy full position",
                                "option_b": "Avoid or small size—counter-trend",
                                "option_c": "Sell short",
                                "option_d": "Double leverage",
                                "correct_answer": "B",
                                "explanation": "MACD crosses against major trend (200 EMA) are lower probability. Avoid or reduce size significantly.",
                                "topic_slug": "indicators"
                            },
                            {
                                "question": "Mistake: Trading every MACD cross regardless of trend. Result?",
                                "option_a": "High win rate",
                                "option_b": "Many false signals in choppy markets",
                                "option_c": "Guaranteed profits",
                                "option_d": "Lower spreads",
                                "correct_answer": "B",
                                "explanation": "MACD generates many false signals in ranges. Always filter by trend direction (200 EMA).",
                                "topic_slug": "indicators"
                            }
                        ]
                    }
                ]
            },
            {
                "title": "Trading Strategies",
                "description": "Building a complete, rule-based trading strategy.",
                "lessons": [
                    {
                        "title": "Strategy Components",
                        "content": """## Simple Definition
A trading strategy is a complete set of rules covering: when to enter, when to exit (profit and loss), how much to trade (position size), and which markets to trade. Without all four, you're gambling, not trading.

## Concept Explanation
**Strategy Framework**:
1. **Market Selection**: Which pairs, timeframes, and sessions?
2. **Setup Criteria**: What conditions must exist before considering trade?
3. **Entry Rules**: Exact trigger that gets you into the trade
4. **Exit Rules**: Stop loss (invalidation point) and take profit (target)
5. **Risk Management**: Position sizing, max daily loss, drawdown limits
6. **Review Process**: Daily/weekly analysis of trades taken

**Example Strategy (Trend Pullback)**:
- **Market**: EUR/USD, GBP/USD only
- **Timeframe**: H4 for trend, H1 for entry
- **Setup**: Price above 200 EMA, pulling back to 50 EMA
- **Entry**: Bullish pin bar or engulfing at 50 EMA
- **Stop**: Below pullback low (20-30 pips)
- **Target**: Previous swing high (1:2 minimum R:R)
- **Risk**: 1% per trade, max 3 trades per day

## Step-by-Step Breakdown
**Building Your Strategy**:
1. **Choose Style**: Scalping (M5-M15), Day trading (H1-H4), Swing (D1)
2. **Select Tools**: Price action, indicators, or combination?
3. **Define Edge**: What market condition does your strategy exploit?
4. **Backtest**: 100+ historical trades to verify positive expectancy
5. **Demo Trade**: 3 months forward testing before live capital
6. **Journal**: Record every trade with screenshots and emotions

## Real Trading Example
**The London Open Breakout Strategy**:
- **Market**: GBP/USD (volatile)
- **Time**: 08:00-09:00 GMT (London open)
- **Setup**: Asian session range established (20:00-08:00)
- **Entry**: Buy stop 5 pips above Asian high, Sell stop 5 pips below Asian low
- **Stop**: Opposite side of Asian range
- **Target**: 1:1.5 Risk/Reward minimum
- **Filter**: Only trade if ADR (Average Daily Range) > 80 pips
- **Risk**: 1% per trade, cancel pending if not triggered by 09:30

## Common Beginner Mistake
**Strategy Hopping**: Trying strategy for 3 losses, abandoning for new "better" system. No strategy wins every trade. Edge appears over 20+ trades. Stick to one strategy for 100 trades minimum before judging performance.

## Key Takeaway
Consistency comes from rules, not intuition. Write your strategy rules on paper. If you can't explain your strategy to a 10-year-old, it's too complicated. Simple strategies executed consistently beat complex strategies executed sporadically.

## Practice Question
What is the minimum Risk:Reward ratio recommended for a sustainable trading strategy?""",
                        "quiz": [
                            {
                                "question": "A complete trading strategy must include:",
                                "option_a": "Only entry rules",
                                "option_b": "Entries, exits, position sizing, and market selection",
                                "option_c": "Only stop losses",
                                "option_d": "A lucky charm",
                                "correct_answer": "B",
                                "explanation": "Complete strategies define entries, exits (stop/target), position sizing, and which markets to trade.",
                                "topic_slug": "strategy"
                            },
                            {
                                "question": "How many trades minimum to evaluate a strategy?",
                                "option_a": "3",
                                "option_b": "10",
                                "option_c": "100",
                                "option_d": "1",
                                "correct_answer": "C",
                                "explanation": "Need 100+ trades to see statistical edge. Variance is too high in small samples.",
                                "topic_slug": "strategy"
                            },
                            {
                                "question": "Calculate: Strategy wins 40% of time, 1:2 R:R average. Profitability?",
                                "option_a": "Losing",
                                "option_b": "Breakeven",
                                "option_c": "Profitable",
                                "option_d": "Cannot determine",
                                "correct_answer": "C",
                                "explanation": "40% win rate with 1:2 R:R = profitable. (40×2) - (60×1) = +20 per 100 trades.",
                                "topic_slug": "strategy"
                            },
                            {
                                "question": "Scenario: 3 losses in a row with new strategy. Action?",
                                "option_a": "Change strategy immediately",
                                "option_b": "Continue if rules followed, review after 20 trades",
                                "option_c": "Increase size to recover",
                                "option_d": "Trade random pairs",
                                "correct_answer": "B",
                                "explanation": "3 losses is normal variance. If rules were followed correctly, continue and review larger sample.",
                                "topic_slug": "strategy"
                            },
                            {
                                "question": "Mistake: Adding new indicators every week. Result?",
                                "option_a": "Better edge",
                                "option_b": "Curve-fitting, no consistency",
                                "option_c": "Guaranteed profits",
                                "option_d": "Lower risk",
                                "correct_answer": "B",
                                "explanation": "Constantly changing indicators leads to curve-fitting past data, not predictive edge.",
                                "topic_slug": "strategy"
                            }
                        ]
                    },
                    {
                        "title": "Backtesting and Forward Testing",
                        "content": """## Simple Definition
Backtesting applies your strategy rules to historical data to verify profitability. Forward testing (paper trading) validates backtest results with real-time data without risking capital.

## Concept Explanation
**Backtesting Process**:
1. **Manual Backtest**: Scroll through 2+ years of charts, mark every setup
2. **Record Data**: Entry, exit, R:R, win rate, consecutive losses, max drawdown
3. **Statistics Needed**:
   - Win Rate %
   - Average R:R per trade
   - Expectancy (mathematical edge)
   - Max consecutive losses
   - Worst drawdown period

**Expectancy Formula**:

Expectancy = (Win% × AvgWin) - (Loss% × AvgLoss)

Positive expectancy > 0 means strategy wins long-term.

**Forward Testing**:
- Trade strategy on demo account for 3 months minimum
- Must match live conditions (spreads, slippage, execution time)
- If backtest showed 60% win rate but forward test shows 45%, strategy failed validation

## Step-by-Step Breakdown
**Validating a Strategy**:
1. **Historical Test**: 100+ trades over different market conditions (trending, ranging)
2. **Analyze Metrics**: If expectancy < 0, strategy is unprofitable—fix or discard
3. **Demo Phase**: 50+ forward test trades minimum
4. **Micro Live**: Trade 0.01 lots for 20 trades to confirm execution
5. **Scale Up**: Only increase size after proven consistency

## Real Trading Example
**Backtest Results - Pin Bar Strategy**:
- **Period**: 2022-2024 (2 years)
- **Trades**: 240
- **Win Rate**: 48%
- **Average Win**: 2.5R
- **Average Loss**: 1R
- **Expectancy**: (0.48×2.5) - (0.52×1) = 1.2 - 0.52 = +0.68 per trade
- **Conclusion**: Profitable long-term. Max 6 consecutive losses (prepare mentally)
- **Forward Test**: 3 months demo confirmed 46% win rate, valid for live trading

## Common Beginner Mistake
**Curve Fitting**: Adding so many filters to backtest that it shows 90% win rate on past data, but fails on new data because it was optimized for specific historical quirks, not market principles.

## Key Takeaway
Backtesting proves your strategy had edge in the past. Forward testing proves edge continues in current conditions. Never risk real money until both tests show positive expectancy. One losing month in backtest is normal—look for profitability over 100+ trades.

## Practice Question
What is the minimum acceptable sample size for a statistically significant backtest?""",
                        "quiz": [
                            {
                                "question": "What is the purpose of backtesting?",
                                "option_a": "To predict exact future prices",
                                "option_b": "To verify strategy edge historically",
                                "option_c": "To avoid losses entirely",
                                "option_d": "To impress friends",
                                "correct_answer": "B",
                                "explanation": "Backtesting verifies your strategy had positive expectancy over historical data.",
                                "topic_slug": "strategy"
                            },
                            {
                                "question": "Calculate expectancy: 50% win rate, 2R average win, 1R average loss.",
                                "option_a": "0",
                                "option_b": "0.5",
                                "option_c": "1.0",
                                "option_d": "2.0",
                                "correct_answer": "B",
                                "explanation": "(0.5×2) - (0.5×1) = 1.0 - 0.5 = +0.5 expectancy per trade.",
                                "topic_slug": "strategy"
                            },
                            {
                                "question": "Forward testing means:",
                                "option_a": "Testing on past data",
                                "option_b": "Demo trading real-time data",
                                "option_c": "Skipping testing",
                                "option_d": "Using maximum leverage",
                                "correct_answer": "B",
                                "explanation": "Forward testing is demo trading current market data to validate backtest results.",
                                "topic_slug": "strategy"
                            },
                            {
                                "question": "Scenario: Backtest shows 80% win rate but forward test shows 40%. Problem?",
                                "option_a": "Strategy curve-fitted to past data",
                                "option_b": "Strategy improved",
                                "option_c": "Markets changed permanently",
                                "option_d": "No problem",
                                "correct_answer": "A",
                                "explanation": "Large discrepancy suggests curve-fitting (over-optimization) to historical noise, not true edge.",
                                "topic_slug": "strategy"
                            },
                            {
                                "question": "Mistake: Backtesting only bull markets. Risk?",
                                "option_a": "Strategy fails in bear markets",
                                "option_b": "Better performance",
                                "option_c": "Lower risk",
                                "option_d": "Guaranteed profits",
                                "correct_answer": "A",
                                "explanation": "Testing only favorable conditions creates false confidence. Strategy may fail in different market regimes.",
                                "topic_slug": "strategy"
                            }
                        ]
                    }
                ]
            }
        ]
    },
    {
        "level_name": "Advanced",
        "description": "Trade like an institution—master market structure, liquidity concepts, and professional risk management. Build robust systems that survive any market condition.",
        "modules": [
            {
                "title": "Market Structure",
                "description": "BOS, CHoCH, order blocks, and fair value gaps.",
                "lessons": [
                    {
                        "title": "Break of Structure (BOS) and CHoCH",
                        "content": """## Simple Definition
**BOS (Break of Structure)**: Price breaks above previous high in uptrend (or below previous low in downtrend), confirming trend continuation.
**CHoCH (Change of Character)**: Price breaks below previous low in uptrend (or above previous high in downtrend), signaling potential trend reversal.

## Concept Explanation
**Market Structure Basics**:
- **Uptrend**: Series of Higher Highs (HH) and Higher Lows (HL)
- **Downtrend**: Series of Lower Highs (LH) and Lower Lows (LL)
- **Bullish BOS**: Break above last HH = trend continuing up
- **Bearish BOS**: Break below last LL = trend continuing down
- **Bullish CHoCH**: Break above last LH in downtrend = possible trend change up
- **Bearish CHoCH**: Break below last HL in uptrend = possible trend change down

**Internal vs External Structure**:
- **External**: Swing highs/lows on H4/Daily (major trend)
- **Internal**: H1 swing points (intraday structure for entries)
- **Rule**: Trade internal structure in direction of external structure

## Step-by-Step Breakdown
**Trading CHoCH Reversals**:
1. **Identify Trend**: Mark HH/HL sequence (uptrend) or LH/LL (downtrend)
2. **Watch for Break**: Price breaks last HL (uptrend) or last LH (downtrend)
3. **Confirm**: Close beyond structure point, not just wick
4. **Enter**: Retest of broken structure level (now support/resistance flip)
5. **Manage**: Stop beyond new extreme, target previous swing

## Real Trading Example
**Bearish CHoCH on EUR/USD**:
- **Trend**: Uptrend with HH at 1.1000, HL at 1.0900, new HH at 1.1050
- **Change**: Price drops below 1.0900 (previous HL) with momentum
- **CHoCH Confirmed**: Uptrend structure broken
- **Entry**: Retest of 1.0900 area which becomes resistance
- **Stop**: Above 1.1050 (last HH, invalidation)
- **Target**: 1.0800 (previous untested support)
- **Logic**: Institutions taking profit at highs, structure shift confirmed

<svg class="ac-svg-diagram" viewBox="0 0 400 250">
  <text x="200" y="20" text-anchor="middle" fill="#fbbf24" font-size="14" font-weight="bold">BEARISH CHoCH</text>
  <path d="M 50 200 L 100 150 L 150 180 L 200 100" fill="none" stroke="#22c55e" stroke-width="2"/>
  <text x="210" y="100" fill="#22c55e" font-size="12">HH</text>
  <path d="M 200 100 L 250 140" fill="none" stroke="#22c55e" stroke-width="2"/>
  <text x="260" y="130" fill="#22c55e" font-size="12">HL</text>
  <path d="M 250 140 L 300 80" fill="none" stroke="#22c55e" stroke-width="2"/>
  <text x="310" y="80" fill="#22c55e" font-size="12">HH</text>
  <path d="M 300 80 L 350 200" fill="none" stroke="#ef4444" stroke-width="3"/>
  <line x1="250" y1="140" x2="350" y2="140" stroke="#ef4444" stroke-width="1" stroke-dasharray="5,5"/>
  <text x="300" y="155" fill="#ef4444" font-size="12">CHoCH Break Below HL</text>
  <text x="350" y="220" fill="#ef4444" font-size="12">Trend Change</text>
</svg>

## Common Beginner Mistake
**CHoCH Hunting**: Taking every internal CHoCH on M15 as trend reversal. Minor structure breaks constantly. Only trade CHoCH when external structure (H4/Daily) aligns or at major supply/demand zones.

## Key Takeaway
Structure tells you who controls the market. BOS = Trend continues, add to positions. CHoCH = Control shifting, prepare for reversal or deep pullback. Always know where you are in the structure sequence.

## Practice Question
What does a Break of Structure (BOS) indicate in an established uptrend?""",
                        "quiz": [
                            {
                                "question": "BOS in uptrend means:",
                                "option_a": "Trend reversal",
                                "option_b": "Trend continuation (new HH)",
                                "option_c": "Market crash",
                                "option_d": "No significance",
                                "correct_answer": "B",
                                "explanation": "Break of Structure above previous high confirms uptrend continuation.",
                                "topic_slug": "market_structure"
                            },
                            {
                                "question": "CHoCH indicates:",
                                "option_a": "Trend continuation",
                                "option_b": "Potential trend reversal",
                                "option_c": "Low volatility",
                                "option_d": "Gap fill",
                                "correct_answer": "B",
                                "explanation": "Change of Character breaks previous HL/LH structure, signaling possible trend change.",
                                "topic_slug": "market_structure"
                            },
                            {
                                "question": "Which structure matters most for swing trading?",
                                "option_a": "M5 internal structure",
                                "option_b": "H4/Daily external structure",
                                "option_c": "Tick chart",
                                "option_d": "All equal",
                                "correct_answer": "B",
                                "explanation": "External structure on higher timeframes determines major trend direction for swing trading.",
                                "topic_slug": "market_structure"
                            },
                            {
                                "question": "Scenario: Price breaks below HL in strong uptrend. Action?",
                                "option_a": "Immediately sell everything",
                                "option_b": "Wait for retest and confirmation",
                                "option_c": "Double long position",
                                "option_d": "Remove stop losses",
                                "correct_answer": "B",
                                "explanation": "Wait for retest of broken structure as resistance and confirmation candle before assuming reversal.",
                                "topic_slug": "market_structure"
                            },
                            {
                                "question": "Mistake: Trading M15 CHoCH against H4 trend. Risk?",
                                "option_a": "High probability reversal",
                                "option_b": "Minor pullback in major trend, likely stopped out",
                                "option_c": "Guaranteed profit",
                                "option_d": "Lower risk",
                                "correct_answer": "B",
                                "explanation": "Low timeframe structure breaks are often pullbacks in higher timeframe trends, causing losses.",
                                "topic_slug": "market_structure"
                            }
                        ]
                    },
                    {
                        "title": "Order Blocks and Fair Value Gaps",
                        "content": """## Simple Definition
**Order Block (OB)**: The last opposing candle before a significant move, representing institutional orders. **Fair Value Gap (FVG)**: Imbalance zone where price moved rapidly without filling orders, creating magnet for future price.

## Concept Explanation
**Bullish Order Block**:
- Last bearish candle before aggressive bullish move
- Shows where institutions placed buy orders before markup
- Price often returns to "mitigate" (fill) these orders before continuing
- Valid only if move created new structure (BOS/CHoCH)

**Bearish Order Block**:
- Last bullish candle before aggressive bearish move
- Institutional sell zone
- Future resistance when price retraces

**Fair Value Gaps**:
- Three-candle pattern: Middle candle has no overlap with neighbors
- Represents inefficient price movement
- Price usually returns to fill gap before continuing
- Types: Bullish FVG (support), Bearish FVG (resistance)

## Step-by-Step Breakdown
**Trading Order Blocks**:
1. **Identify Move**: Strong impulsive move creating structure break
2. **Mark OB**: Last opposing candle before the move
3. **Wait**: Price returns to OB zone (mitigation)
4. **Confirm**: Reaction at OB (pin bar, engulfing, or sharp rejection)
5. **Enter**: In direction of original impulse
6. **Stop**: Beyond OB extreme or recent swing

## Real Trading Example
**Bullish Order Block Trade**:
- **Move**: GBP/USD rallies 150 pips from 1.2500, breaking above previous high (BOS)
- **OB Identification**: Last red candle before rally: 1.2510-1.2530
- **Wait**: Price pulls back 3 days later to 1.2520 (OB zone)
- **Confirm**: Bullish engulfing at 1.2520
- **Entry**: Buy 1.2525
- **Stop**: 1.2490 (below OB low)
- **Target**: 1.2650 (next resistance)
- **Logic**: Institutions defend their entry zone; we front-run their next accumulation

<svg class="ac-svg-diagram" viewBox="0 0 300 200">
  <rect x="50" y="80" width="40" height="40" fill="#ef4444" opacity="0.5"/>
  <text x="70" y="105" text-anchor="middle" fill="#fff" font-size="10">OB</text>
  <line x1="90" y1="100" x2="200" y2="60" stroke="#22c55e" stroke-width="3"/>
  <text x="150" y="70" fill="#22c55e" font-size="12">Strong Move (BOS)</text>
  <path d="M 200 60 Q 250 100 200 140" fill="none" stroke="#60a5fa" stroke-width="2" stroke-dasharray="5,5"/>
  <text x="220" y="110" fill="#60a5fa" font-size="12">Retest</text>
  <line x1="200" y1="140" x2="280" y2="40" stroke="#22c55e" stroke-width="3"/>
  <text x="240" y="70" fill="#22c55e" font-size="12">Continuation</text>
</svg>

## Common Beginner Mistake
**Trading Every OB**: Not all order blocks are equal. Only trade OBs that preceded significant structure breaks (BOS/CHoCH) on H4+. Minor OBs on low timeframes fail frequently.

## Key Takeaway
Order blocks show where smart money entered. Fair Value Gaps show where price is likely to return for "cleanup." Trade these zones only when they align with higher timeframe structure and show price reaction confirmation.

## Practice Question
What qualifies as a valid Bullish Order Block?""",
                        "quiz": [
                            {
                                "question": "Order Block is:",
                                "option_a": "Any candle",
                                "option_b": "Last opposing candle before significant move",
                                "option_c": "Moving average",
                                "option_d": "Random support",
                                "correct_answer": "B",
                                "explanation": "OB is specifically the last opposing candle before an impulsive move that broke structure.",
                                "topic_slug": "market_structure"
                            },
                            {
                                "question": "Fair Value Gap represents:",
                                "option_a": "Balanced market",
                                "option_b": "Price imbalance likely to be filled",
                                "option_c": "Trend continuation only",
                                "option_d": "Low volatility",
                                "correct_answer": "B",
                                "explanation": "FVG is inefficiency where price moved too fast. Market usually returns to fill these gaps.",
                                "topic_slug": "market_structure"
                            },
                            {
                                "question": "Calculate: OB high 1.2500, OB low 1.2480. Entry at 50% of zone?",
                                "option_a": "1.2490",
                                "option_b": "1.2500",
                                "option_c": "1.2480",
                                "option_d": "1.2600",
                                "correct_answer": "A",
                                "explanation": "50% of 1.2480-1.2500 zone = 1.2490. Common entry for optimal risk/reward within OB.",
                                "topic_slug": "market_structure"
                            },
                            {
                                "question": "Scenario: Price hits OB but immediately breaks through. Action?",
                                "option_a": "Hold position",
                                "option_b": "OB failed, exit immediately",
                                "option_c": "Double position",
                                "option_d": "Move stop further away",
                                "correct_answer": "B",
                                "explanation": "If price slices through OB without reaction, the level is invalid. Exit and reassess.",
                                "topic_slug": "market_structure"
                            },
                            {
                                "question": "Mistake: Trading OB on M5 without H4 context. Risk?",
                                "option_a": "High probability",
                                "option_b": "OB may be minor in larger trend",
                                "option_c": "Guaranteed fills",
                                "option_d": "Better spreads",
                                "correct_answer": "B",
                                "explanation": "Low timeframe OBs lack institutional significance. Always check alignment with H4/Daily structure.",
                                "topic_slug": "market_structure"
                            }
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
**Liquidity Pools**: Clusters of stop orders and pending orders above/below key levels where institutional traders seek to fill large positions. **Stop Hunt**: Price briefly breaking a level to trigger retail stops before reversing sharply.

## Concept Explanation
**Where is Liquidity?**:
- **Above Swing Highs**: Retail buy stops and breakout traders
- **Below Swing Lows**: Retail sell stops and breakdown traders
- **Equal Highs/Lows**: Multiple swing points at exact same level = concentrated orders
- **Round Numbers**: 1.1000, 1.2000 (psychological clustering)

**The Stop Hunt Pattern**:
1. Market approaches obvious level (previous high)
2. Retail traders place buy stop above high (breakout entry)
3. Institutions push price slightly above high, triggering those stops
4. Institutions sell into the liquidity (filling their short orders)
5. Price collapses back below level, leaving retail trapped

**Inducement**: Minor structure break designed to lure retail in before major move opposite.

## Step-by-Step Breakdown
**Avoiding Stop Hunts**:
1. **Identify Liquidity**: Mark all obvious swing highs/lows where retail place stops
2. **Expect Hunt**: Assume price will take stops before real move
3. **Entry Adjustment**: Place entries 10-15 pips beyond obvious level (after sweep)
4. **Stop Placement**: Don't place stops at obvious levels (1.1000, swing high exact)
5. **Confirmation**: Wait for return inside range after sweep (failure of breakout)

## Real Trading Example
**The Liquidity Grab**:
- **Setup**: EUR/USD double top at 1.1000 (clear resistance)
- **Retail Action**: Traders place buy stops at 1.1005 (breakout entry)
- **Smart Money**: Institutions see cluster of 1.1005 stops
- **Execution**: Price spikes to 1.1010 (taking stops), institutions sell heavily
- **Result**: Price collapses to 1.0950 in 2 hours
- **Lesson**: Place sell limits at 1.1010 (above liquidity) not buy stops

<svg class="ac-svg-diagram" viewBox="0 0 400 200">
  <rect x="150" y="40" width="100" height="20" fill="rgba(167,139,250,0.3)" stroke="#a78bfa" rx="5"/>
  <text x="200" y="55" text-anchor="middle" fill="#a78bfa" font-size="12">Liquidity Pool (Buy Stops)</text>
  <line x1="200" y1="60" x2="200" y2="100" stroke="#60a5fa" stroke-width="2" marker-end="url(#arrowhead)"/>
  <path d="M 50 150 L 150 100 L 200 100" fill="none" stroke="#22c55e" stroke-width="2"/>
  <path d="M 200 100 L 220 70 L 200 150" fill="none" stroke="#ef4444" stroke-width="3"/>
  <text x="230" y="70" fill="#ef4444" font-size="12">Stop Hunt</text>
  <text x="200" y="170" text-anchor="middle" fill="#ef4444" font-size="14" font-weight="bold">Sharp Reversal</text>
</svg>

## Common Beginner Mistake
**Obvious Stop Placement**: Placing stop loss exactly below swing low or at round number. Algorithms hunt these exact levels. Always use buffer (ATR or 1.5x spread) beyond obvious points.

## Key Takeaway
Markets move to take liquidity. Before major reversals, price often takes obvious highs/lows. Don't place stops at obvious levels. Expect "fakeouts" before real moves.

## Practice Question
Why do institutions push price above previous highs before reversing down?""",
                        "quiz": [
                            {
                                "question": "Liquidity pools are found:",
                                "option_a": "Randomly",
                                "option_b": "Above highs/below lows where stops cluster",
                                "option_c": "Only at round numbers",
                                "option_d": "Inside ranges",
                                "correct_answer": "B",
                                "explanation": "Liquidity concentrates above swing highs (buy stops) and below swing lows (sell stops).",
                                "topic_slug": "liquidity"
                            },
                            {
                                "question": "Stop hunt purpose is to:",
                                "option_a": "Help retail traders",
                                "option_b": "Trigger stops so institutions can fill orders",
                                "option_c": "Break support permanently",
                                "option_d": "Create volatility for fun",
                                "correct_answer": "B",
                                "explanation": "Institutions hunt stops to generate liquidity for their large orders (selling into buy stops).",
                                "topic_slug": "liquidity"
                            },
                            {
                                "question": "Where should you NOT place stop losses?",
                                "option_a": "Below swing low",
                                "option_b": "At exact round numbers",
                                "option_c": "Behind strong structure",
                                "option_d": "Both A and B",
                                "correct_answer": "D",
                                "explanation": "Never place stops at exact swing lows or round numbers—most hunted levels. Use buffers.",
                                "topic_slug": "liquidity"
                            },
                            {
                                "question": "Scenario: Price breaks above resistance, triggers your stop, then reverses sharply. This is:",
                                "option_a": "Bad luck",
                                "option_b": "Stop hunt/liquidity grab",
                                "option_c": "Trend continuation",
                                "option_d": "Gap fill",
                                "correct_answer": "B",
                                "explanation": "Classic stop hunt—break above resistance takes buy stops/breakout traders, then reverses.",
                                "topic_slug": "liquidity"
                            },
                            {
                                "question": "Mistake: Placing buy stop 5 pips above obvious resistance. Risk?",
                                "option_a": "Perfect entry",
                                "option_b": "Stop hunted immediately before reversal",
                                "option_c": "Guaranteed breakout",
                                "option_d": "Lower risk",
                                "correct_answer": "B",
                                "explanation": "Buy stops above obvious levels are liquidity targets. Wait for retest of broken level as support.",
                                "topic_slug": "liquidity"
                            }
                        ]
                    },
                    {
                        "title": "Smart Money Concepts",
                        "content": """## Simple Definition
Smart Money refers to institutional traders (banks, hedge funds) whose large orders move markets. Smart Money Concepts (SMC) involve reading their footprints: order blocks, liquidity grabs, and accumulation/distribution phases.

## Concept Explanation
**Accumulation/Distribution**:
- **Accumulation**: Smart money buying at wholesale prices (long consolidation at lows)
- **Markup**: Aggressive move up as retail FOMO joins
- **Distribution**: Smart money selling to retail at highs (choppy range at top)
- **Markdown**: Aggressive move down

**Displacement**: Large impulsive candle showing institutional order flow. Displacement + structure break = high probability setup.

**Inducement**: Minor structure break designed to trap retail traders before major move opposite direction (bullish inducement before bearish move).

**Breaker Block**: When bullish order block fails and becomes resistance (or vice versa).

## Step-by-Step Breakdown
**Trading with Smart Money**:
1. **Identify Trend**: External structure on H4/Daily
2. **Find OB**: Order block in direction of trend
3. **Wait for Inducement**: Minor counter-trend move to take liquidity
4. **Displacement**: Strong candle breaking internal structure toward trend
5. **Entry**: FVG or OB retest after displacement
6. **Stop**: Beyond inducement level (opposite side)

## Real Trading Example
**Smart Money Short Setup**:
- **Trend**: Daily bearish (lower lows)
- **Inducement**: Price rallies to take previous H1 high (liquidity grab)
- **Displacement**: Sharp H1 candle down breaking last H1 low
- **OB**: Bearish order block at top of inducement
- **Entry**: Retest of OB or Fair Value Gap below displacement
- **Stop**: Above inducement high
- **Target**: Next liquidity pool (below previous swing low)
- **Logic**: Retail bought the inducement (fakeout), smart money sells displacement

<div class="ac-tradingview-widget" data-symbol="FX:EURUSD"></div>

## Common Beginner Mistake
**Labeling Every Level as SMC**: Not every support is an order block. SMC requires specific criteria: displacement, structure break, and mitigation. Random lines on charts aren't institutional levels.

## Key Takeaway
Trade with institutions, not against them. Wait for them to show their hand via displacement and structure breaks. Don't fight the inducement—wait for it to complete, then trade the real move.

## Practice Question
What does "inducement" mean in Smart Money Concepts?""",
                        "quiz": [
                            {
                                "question": "Inducement is:",
                                "option_a": "Trend continuation",
                                "option_b": "Minor structure break to trap retail before major move",
                                "option_c": "Breakout pattern",
                                "option_d": "Moving average cross",
                                "correct_answer": "B",
                                "explanation": "Inducement takes liquidity from retail traders before smart money reverses price sharply.",
                                "topic_slug": "liquidity"
                            },
                            {
                                "question": "Displacement shows:",
                                "option_a": "Low volatility",
                                "option_b": "Institutional order flow (large candles)",
                                "option_c": "Market close",
                                "option_d": "Random noise",
                                "correct_answer": "B",
                                "explanation": "Displacement is large impulsive candle showing institutional participation and direction intent.",
                                "topic_slug": "liquidity"
                            },
                            {
                                "question": "When a bullish OB fails and becomes resistance, it's called:",
                                "option_a": "Order block",
                                "option_b": "Breaker block",
                                "option_c": "Fair value gap",
                                "option_d": "Support",
                                "correct_answer": "B",
                                "explanation": "Breaker block is failed order block that flips to opposite role (support becomes resistance).",
                                "topic_slug": "liquidity"
                            },
                            {
                                "question": "Scenario: Price takes H1 high, then collapses breaking H1 low sharply. This is:",
                                "option_a": "Trend continuation up",
                                "option_b": "Inducement then displacement down",
                                "option_c": "Accumulation phase",
                                "option_d": "Random volatility",
                                "correct_answer": "B",
                                "explanation": "Taking highs (inducement) followed by strong move down (displacement) = smart money distribution.",
                                "topic_slug": "liquidity"
                            },
                            {
                                "question": "Mistake: Fighting displacement candles. Risk?",
                                "option_a": "Catching the bottom",
                                "option_b": "Runaway losses against institutional flow",
                                "option_c": "Guaranteed reversal",
                                "option_d": "Better fills",
                                "correct_answer": "B",
                                "explanation": "Displacement shows institutional commitment. Counter-trading it leads to large losses as trend continues.",
                                "topic_slug": "liquidity"
                            }
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
Portfolio risk considers total exposure across all open trades, including correlations between pairs. Trading EUR/USD and GBP/USD simultaneously is nearly the same trade due to 90%+ correlation.

## Concept Explanation
**Correlation Coefficient (-1 to +1)**:
- **+0.9+**: Pairs move together (EUR/USD & GBP/USD)
- **-0.9+**: Pairs move opposite (EUR/USD & USD/CHF)
- **0**: No correlation (EUR/USD & USD/JPY sometimes)

**Risk Implications**:
- Long EUR/USD + Long GBP/USD = 2x risk on same directional bet
- If correlation is +0.9, you're risking 1.9% instead of perceived 2% (0.95 correlation factor)

**Basket Risk**:
- USD pairs: If long EUR/USD, GBP/USD, AUD/USD, you're massively short USD (concentrated risk)
- Risk events (NFP) affect all simultaneously

**Diversification**:
- Trade different asset classes (Forex + Gold + Indices)
- Trade uncorrelated pairs (EUR/USD & USD/JPY have lower correlation)
- Reduce size when trading correlated pairs simultaneously

## Step-by-Step Breakdown
**Calculating Portfolio Heat**:
1. **List Positions**: All open trades with direction
2. **Check Correlations**: Use 30-day correlation matrix
3. **Adjust Risk**: If trading 2 pairs with 0.9 correlation at 1% each, actual risk ~1.9%
4. **Limit Exposure**: Max 3% total portfolio risk across all correlated positions
5. **Hedge Check**: Are you accidentally hedging (EUR/USD long + USD/CHF long = roughly neutral)?

## Real Trading Example
**Correlation Disaster**:
- **Trader**: Long EUR/USD (1%), Long GBP/USD (1%), Long AUD/USD (1%), Long NZD/USD (1%)
- **Perceived Risk**: 4% total
- **Actual Risk**: ~3.8% (all pairs +085 correlated, move together)
- **Event**: Fed announces hawkish policy, USD strengthens
- **Result**: All 4 positions lose simultaneously, -3.5% account in 2 hours
- **Lesson**: Correlated pairs don't diversify; they compound risk

<svg class="ac-svg-diagram" viewBox="0 0 400 150">
  <rect x="50" y="50" width="80" height="40" fill="rgba(34,197,94,0.3)" stroke="#22c55e" rx="5"/>
  <text x="90" y="75" text-anchor="middle" fill="#22c55e" font-size="10">EUR/USD Long</text>
  <rect x="150" y="50" width="80" height="40" fill="rgba(34,197,94,0.3)" stroke="#22c55e" rx="5"/>
  <text x="190" y="75" text-anchor="middle" fill="#22c55e" font-size="10">GBP/USD Long</text>
  <rect x="250" y="50" width="80" height="40" fill="rgba(34,197,94,0.3)" stroke="#22c55e" rx="5"/>
  <text x="290" y="75" text-anchor="middle" fill="#22c55e" font-size="10">AUD/USD Long</text>
  <text x="200" y="120" text-anchor="middle" fill="#ef4444" font-size="14" font-weight="bold">90% Correlated = 3x Risk on USD Weakness</text>
</svg>

## Common Beginner Mistake
**Diversification Illusion**: Opening 5 different pairs thinking they're diversified when 4 are USD pairs. When USD moves strongly, all positions act as one large bet.

## Key Takeaway
Check correlation before adding positions. Max 2 high-correlation trades at reduced size each. True diversification requires uncorrelated instruments or opposite-direction trades.

## Practice Question
What happens to your portfolio risk if you trade EUR/USD and GBP/USD long simultaneously with 1% risk each?""",
                        "quiz": [
                            {
                                "question": "EUR/USD and GBP/USD correlation is roughly:",
                                "option_a": "-0.9 (opposite)",
                                "option_b": "0 (no relation)",
                                "option_c": "+0.9 (same direction)",
                                "option_d": "Random",
                                "correct_answer": "C",
                                "explanation": "EUR/USD and GBP/USD move together ~90% of time due to European economic ties and USD component.",
                                "topic_slug": "advanced_risk"
                            },
                            {
                                "question": "Trading 3 correlated pairs at 1% risk each equals actual risk of roughly:",
                                "option_a": "1%",
                                "option_b": "2%",
                                "option_c": "3%",
                                "option_d": "0.5%",
                                "correct_answer": "C",
                                "explanation": "High correlation means positions move together. Actual risk approaches sum of individual risks.",
                                "topic_slug": "advanced_risk"
                            },
                            {
                                "question": "Which pairs typically move opposite to EUR/USD?",
                                "option_a": "GBP/USD",
                                "option_b": "USD/CHF",
                                "option_c": "AUD/USD",
                                "option_d": "EUR/GBP",
                                "correct_answer": "B",
                                "explanation": "USD/CHF moves inverse to EUR/USD ~90% of time (USD base vs USD quote).",
                                "topic_slug": "advanced_risk"
                            },
                            {
                                "question": "Scenario: Long EUR/USD and Short USD/CHF simultaneously. Effect?",
                                "option_a": "Diversified",
                                "option_b": "Nearly same trade twice",
                                "option_c": "Hedged",
                                "option_d": "Risk-free",
                                "correct_answer": "B",
                                "explanation": "Long EUR/USD = anti-USD. Short USD/CHF = anti-USD. Both same directional bet on USD weakness.",
                                "topic_slug": "advanced_risk"
                            },
                            {
                                "question": "Mistake: 5 positions all USD-pairs same direction during NFP. Risk?",
                                "option_a": "Diversified safety",
                                "option_b": "Concentrated explosion risk",
                                "option_c": "Guaranteed profit",
                                "option_d": "No correlation",
                                "correct_answer": "B",
                                "explanation": "USD events affect all USD pairs simultaneously. Correlated exposure compounds into massive single-event risk.",
                                "topic_slug": "advanced_risk"
                            }
                        ]
                    },
                    {
                        "title": "Drawdown Recovery and Psychology",
                        "content": """## Simple Definition
Drawdown is peak-to-trough decline in account balance. Recovery is the mathematical and psychological process of returning to breakeven. A 50% drawdown requires 100% gain to recover—prevention is critical.

## Concept Explanation
**Drawdown Mathematics**:
- **10% Loss**: Requires 11% gain to recover
- **20% Loss**: Requires 25% gain
- **50% Loss**: Requires 100% gain
- **80% Loss**: Requires 400% gain (nearly impossible)

**Drawdown Phases**:
1. **Normal**: <10% (routine variance)
2. **Deep**: 10-20% (requires strategy review, reduce size 50%)
3. **Critical**: >20% (halt trading, extensive review, return to demo)

**Recovery Rules**:
- Never increase risk to "make it back faster"
- Reduce size by 50% during recovery phase
- Focus on process, not P&L
- Return to breakeven on reduced size before scaling up

## Step-by-Step Breakdown
**Surviving Drawdowns**:
1. **Accept**: Drawdowns are statistically inevitable
2. **Analyze**: Is it normal variance or broken edge?
3. **Adjust**: Reduce risk per trade by 50% until 3 consecutive wins
4. **Review**: Journal showing emotional decisions vs mechanical?
5. **Resume**: Only return to normal size after new equity high

## Real Trading Example
**The Recovery Trap**:
- **Trader**: Down 25% ($7,500 from $10,000)
- **Mistake**: Increases risk to 4% to "recover faster"
- **Result**: Next 3 losses = -12% additional ($900 remaining)
- **Mathematical Reality**: Now needs 1000%+ gain to recover (impossible)
- **Proper Approach**: Reduce to 0.5% risk, accept 150 trades to recover slowly
- **Lesson**: Increasing risk in drawdown guarantees ruin

<svg class="ac-svg-diagram" viewBox="0 0 400 200">
  <line x1="50" y1="180" x2="350" y2="180" stroke="#9ca3af" stroke-width="1"/>
  <text x="200" y="195" text-anchor="middle" fill="#9ca3af" font-size="12">Starting Equity</text>
  <line x1="50" y1="180" x2="200" y2="120" stroke="#ef4444" stroke-width="2"/>
  <text x="125" y="140" fill="#ef4444" font-size="12">50% Drawdown</text>
  <path d="M 200 120 Q 250 120 350 60" fill="none" stroke="#22c55e" stroke-width="2" stroke-dasharray="5,5"/>
  <text x="275" y="90" fill="#22c55e" font-size="12">Requires 100% Gain</text>
  <text x="200" y="40" text-anchor="middle" fill="#fbbf24" font-size="14" font-weight="bold">Recovery is Exponentially Harder</text>
</svg>

## Common Beginner Mistake
**Revenge Trading**: After 3 losses, trader doubles position size on "sure thing" to recover. This emotional decision-making creates catastrophic drawdowns that end careers.

## Key Takeaway
Preserve capital at all costs. A 20% drawdown requires 25% gain—difficult but doable. A 50% drawdown requires doubling—nearly impossible under psychological pressure. Never risk more than 2%, never increase size in drawdown.

## Practice Question
If your account drops 50%, what percentage gain is required to return to breakeven?""",
                        "quiz": [
                            {
                                "question": "10% drawdown requires what gain to recover?",
                                "option_a": "10%",
                                "option_b": "11%",
                                "option_c": "20%",
                                "option_d": "5%",
                                "correct_answer": "B",
                                "explanation": "After 10% loss, you have 90% left. Need 11% of that 90% to recover original amount.",
                                "topic_slug": "advanced_risk"
                            },
                            {
                                "question": "50% drawdown requires what gain?",
                                "option_a": "50%",
                                "option_b": "75%",
                                "option_c": "100%",
                                "option_d": "25%",
                                "correct_answer": "C",
                                "explanation": "50% drawdown leaves half account. Need 100% gain on remaining half to recover original balance.",
                                "topic_slug": "advanced_risk"
                            },
                            {
                                "question": "During drawdown, proper action is:",
                                "option_a": "Increase size to recover faster",
                                "option_b": "Reduce size 50%, focus on process",
                                "option_c": "Trade more pairs",
                                "option_d": "Remove stops",
                                "correct_answer": "B",
                                "explanation": "Reduce risk during drawdown. Focus on execution quality, not recovery speed.",
                                "topic_slug": "advanced_risk"
                            },
                            {
                                "question": "Scenario: Down 20%, next trade looks perfect. Action?",
                                "option_a": "Triple size to recover",
                                "option_b": "Trade normal or reduced size",
                                "option_c": "Skip trade entirely",
                                "option_d": "Use maximum leverage",
                                "correct_answer": "B",
                                "explanation": "Never increase size in drawdown. Trade normal or reduced size until consistent wins return.",
                                "topic_slug": "advanced_risk"
                            },
                            {
                                "question": "Mistake: Checking P&L every 5 minutes during drawdown. Effect?",
                                "option_a": "Better decisions",
                                "option_b": "Emotional trading, revenge trades",
                                "option_c": "Faster recovery",
                                "option_d": "No effect",
                                "correct_answer": "B",
                                "explanation": "Obsessing over P&L creates emotional pressure leading to revenge trading and larger losses.",
                                "topic_slug": "advanced_risk"
                            }
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
Trading is 80% psychology and 20% strategy. The ability to execute a strategy consistently under stress distinguishes professionals from amateurs. Loss aversion and overconfidence are primary psychological traps.

## Concept Explanation
**Loss Aversion**:
- Losses feel 2.5x stronger than equivalent gains
- Causes holding losers too long (avoid realizing loss) and cutting winners early (fear of gain turning to loss)
- Solution: Pre-define exits, automate if possible, focus on process over outcome

**Overconfidence Bias**:
- After 3 wins, traders increase size and deviate from rules
- Belief that "I've mastered this" leads to sloppy execution
- Solution: Maintain consistent risk regardless of recent performance

**Recency Bias**:
- Placing too much weight on recent trades vs long-term statistics
- After losses, seeing setups as "riskier" even if edge unchanged
- Solution: Trade probabilities, not feelings. Review 100-trade sample, not last 3

## Step-by-Step Breakdown
**Mental State Management**:
1. **Pre-Trading Routine**: Meditation, review rules, check economic calendar
2. **During Trade**: Focus on execution quality, not P&L. Set alerts, step away
3. **Post-Trade Review**: Log emotions (fear, greed, FOMO) with trade data
4. **Breaks**: Mandatory 24-hour break after 3 consecutive losses
5. **Peak Performance**: Trade only when physically rested, mentally sharp

## Real Trading Example
**The Tilt Spiral**:
- **08:00**: Loses trade 1 (-1%), feels annoyed
- **08:30**: Takes sub-par setup to "make it back" (revenge trade)
- **09:00**: Loses trade 2 (-2% total), anger increases
- **09:15**: Removes stop loss on trade 3 "to give it room"
- **10:00**: Trade 3 hits -8% (blow up)
- **Analysis**: 3R loss became 8R disaster due to emotional escalation
- **Professional Approach**: Stop after loss 2, review, return tomorrow

<svg class="ac-svg-diagram" viewBox="0 0 400 150">
  <text x="200" y="30" text-anchor="middle" fill="#ef4444" font-size="16" font-weight="bold">The Emotional Spiral</text>
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
**Outcome Attachment**: Defining self-worth by daily P&L. Two winning days = "I'm a genius." Two losing days = "I'm terrible." This volatility destroys consistency.

## Key Takeaway
Separate identity from trading results. You are not your P&L. Focus on process execution: Did I follow rules? Did I size correctly? The outcome of any single trade is random; the edge appears over 100 trades.

## Practice Question
What is "loss aversion" and how does it affect trading decisions?""",
                        "quiz": [
                            {
                                "question": "Loss aversion causes traders to:",
                                "option_a": "Take profits too quickly and hold losers too long",
                                "option_b": "Trade perfectly",
                                "option_c": "Avoid all risk",
                                "option_d": "Increase size after wins",
                                "correct_answer": "A",
                                "explanation": "Losses feel 2.5x worse than gains, causing premature profit-taking and reluctant loss realization.",
                                "topic_slug": "psychology"
                            },
                            {
                                "question": "After 3 consecutive wins, traders typically become:",
                                "option_a": "More careful",
                                "option_b": "Overconfident, increase size",
                                "option_c": "Stop trading",
                                "option_d": "Less emotional",
                                "correct_answer": "B",
                                "explanation": "Recency bias and overconfidence lead to size increases and rule deviation after wins.",
                                "topic_slug": "psychology"
                            },
                            {
                                "question": "Best practice after 3 consecutive losses:",
                                "option_a": "Trade larger to recover",
                                "option_b": "Mandatory 24-hour break",
                                "option_c": "Trade different pairs",
                                "option_d": "Remove stops",
                                "correct_answer": "B",
                                "explanation": "3 losses indicate emotional involvement or market regime change. Break prevents tilt spiral.",
                                "topic_slug": "psychology"
                            },
                            {
                                "question": "Scenario: Up 5% this week. Proper action?",
                                "option_a": "Increase size for bigger gains",
                                "option_b": "Maintain consistent risk, withdraw profits",
                                "option_c": "Trade more hours",
                                "option_d": "Risk entire profit on one trade",
                                "correct_answer": "B",
                                "explanation": "Maintain consistency. Withdraw profits periodically to separate from trading capital.",
                                "topic_slug": "psychology"
                            },
                            {
                                "question": "Mistake: Defining self-worth by daily P&L. Consequence?",
                                "option_a": "Consistent performance",
                                "option_b": "Emotional volatility, inconsistent execution",
                                "option_c": "Better focus",
                                "option_d": "Higher profits",
                                "correct_answer": "B",
                                "explanation": "Attaching identity to results creates emotional swings that destroy mechanical execution.",
                                "topic_slug": "psychology"
                            }
                        ]
                    },
                    {
                        "title": "Building Mental Toughness",
                        "content": """## Simple Definition
Mental toughness is the ability to maintain strategic discipline under financial and emotional pressure. It's developed through deliberate practice, routine, and acceptance of variance.

## Concept Explanation
**The Performance Arc**:
- **Amateur**: Results dictate emotions → emotions dictate next trade
- **Professional**: Process dictates action → results accumulate over time

**Acceptance of Variance**:
- Even 60% win rate means 40% losses
- 40% win rate with 1:2 R:R is profitable (expect 6 losses in 10)
- "Right" trades lose often; "wrong" trades win sometimes
- Focus on decision quality, not outcome

**Routine Architecture**:
- **Pre-Market**: 30 minutes of analysis without trading
- **Trading Hours**: Maximum 4 hours (fatigue management)
- **Post-Market**: Journal, review, physical exercise
- **Weekend**: Strategy review, backtesting, no live trading

**Pressure Management**:
- Breathing techniques (4-7-8 method) before entries
- Physical exercise reduces cortisol (stress hormone)
- Sleep 8 hours—fatigue increases emotional reactivity 300%

## Step-by-Step Breakdown
**Developing Discipline**:
1. **Mechanical Execution**: Follow strategy exactly for 100 trades regardless of results
2. **Emotion Labeling**: "I'm feeling FOMO" (recognizing emotion reduces its power)
3. **Small Commitments**: Win the morning routine, win the trading day
4. **Identity Shift**: "I am a professional trader who follows process" (not "I try to make money")

## Real Trading Example
**The Professional Difference**:
- **Scenario**: Strategy signal appears at resistance
- **Amateur Response**: "It looks too high, I'll wait for better entry" (subjective override)
- **Price**: Continues 100 pips without amateur
- **Amateur**: Jumps in late, buys top, loses
- **Professional Response**: "Signal is signal. Execute with defined risk."
- **Result**: Professional takes 2R profit while amateur chases

<div class="ac-tradingview-widget" data-symbol="FX:EURUSD"></div>

## Common Beginner Mistake
**System Hopping**: Abandoning strategy after 5 losses because "it doesn't work." No strategy works every week. Edge appears over series of trades, not individual outcomes.

## Key Takeaway
Mental toughness isn't eliminating emotions—it's executing despite them. Build routines that remove decision fatigue. Accept that 40% of your trades will lose even when executed perfectly. Variance is the cost of doing business.

## Practice Question
Why do professional traders focus on process rather than individual trade outcomes?""",
                        "quiz": [
                            {
                                "question": "Mental toughness means:",
                                "option_a": "Having no emotions",
                                "option_b": "Executing strategy despite emotions",
                                "option_c": "Winning every trade",
                                "option_d": "Avoiding losses",
                                "correct_answer": "B",
                                "explanation": "Mental toughness is following process when feeling fear or greed, not eliminating feelings.",
                                "topic_slug": "psychology"
                            },
                            {
                                "question": "With 40% win rate and 1:2 R:R, expectancy per 10 trades is:",
                                "option_a": "Loss",
                                "option_b": "Break even",
                                "option_c": "Profit (4 wins × 2R - 6 losses × 1R = +2R)",
                                "option_d": "Cannot calculate",
                                "correct_answer": "C",
                                "explanation": "(4 wins × 2R) - (6 losses × 1R) = 8R - 6R = +2R profit per 10 trades.",
                                "topic_slug": "psychology"
                            },
                            {
                                "question": "Best pre-trading routine includes:",
                                "option_a": "Checking social media",
                                "option_b": "30 minutes analysis, breathing exercises",
                                "option_c": "Trading immediately upon waking",
                                "option_d": "Large coffee only",
                                "correct_answer": "B",
                                "explanation": "Preparation and calm mental state reduce emotional trading errors.",
                                "topic_slug": "psychology"
                            },
                            {
                                "question": "Scenario: Perfect setup but feeling fearful after 2 losses. Action?",
                                "option_a": "Skip trade",
                                "option_b": "Take trade with reduced size if valid",
                                "option_c": "Trade double size to overcome fear",
                                "option_d": "Change strategy",
                                "correct_answer": "B",
                                "explanation": "Fear is data, not directive. Reduce size to manage emotion, but take valid setups.",
                                "topic_slug": "psychology"
                            },
                            {
                                "question": "Mistake: Changing strategy after 5 losses. Problem?",
                                "option_a": "Strategy improvement",
                                "option_b": "No statistical significance, curve-fitting to recent variance",
                                "option_c": "Better results",
                                "option_d": "Lower risk",
                                "correct_answer": "B",
                                "explanation": "5 trades is variance, not edge. Changing strategies constantly prevents mastering any edge.",
                                "topic_slug": "psychology"
                            }
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
Systematic backtesting involves testing strategy over multiple market conditions (trending, ranging, high/low volatility) with walk-forward analysis to prevent curve-fitting.

## Concept Explanation
**Walk-Forward Analysis**:
1. Optimize strategy on period A (2020-2022)
2. Test on "unseen" period B (2022-2024) without changes
3. If period B profitable, strategy has real edge (not curve-fit)
4. If period B fails, strategy optimized for noise, not signal

**Market Regimes**:
- **Trending**: ADR > 100 pips, directional persistence
- **Ranging**: ADR < 60 pips, mean-reversion behavior
- **Volatile**: Expansion in ATR, gap risk
- **Quiet**: Compression before expansion

**Robustness Tests**:
- Does strategy work on multiple pairs? (If not, curve-fitted to one)
- Does parameter change from 20 to 25 EMA destroy results? (If yes, fragile)
- Does it survive spread widening by 2 pips?

## Step-by-Step Breakdown
**Professional Backtest**:
1. **Data**: 5+ years tick data, include spreads and slippage
2. **In-Sample**: Optimize on 60% of data
3. **Out-of-Sample**: Validate on remaining 40%
4. **Monte Carlo**: Randomize trade sequence 1000x to test worst-case drawdowns
5. **Sensitivity**: Change parameters ±20%, results should remain profitable

## Real Trading Example
**Robust vs Curve-Fitted**:
- **Curve-Fitted Strategy**: RSI(14), MA(20), MACD(12,26,9) on EUR/USD only, 2023 data
- **Result**: 90% win rate in backtest, 35% in forward test (failed)
- **Robust Strategy**: Pin bar at support/resistance, 2:1 R:R, any major pair
- **Result**: 48% win rate consistently across 5 pairs, 5 years
- **Lesson**: Simple robust edges outperform optimized fragile systems

## Common Beginner Mistake
**Optimization Bias**: Adding filters until backtest shows 80%+ win rate. This creates "perfect" historical performance that fails immediately on new data because it was fit to noise.

## Key Takeaway
Simple strategies with slight edge, executed consistently, outperform complex optimized systems. If strategy breaks when changing EMA from 20 to 21, it's not robust enough for live trading.

## Practice Question
What is "walk-forward analysis" and why is it critical?""",
                        "quiz": [
                            {
                                "question": "Walk-forward analysis tests:",
                                "option_a": "Past data only",
                                "option_b": "Strategy on unseen data after optimization",
                                "option_c": "Demo trading",
                                "option_d": "Spreads only",
                                "correct_answer": "B",
                                "explanation": "Optimize on one period, test on completely different period to verify edge isn't curve-fitted.",
                                "topic_slug": "strategy_dev"
                            },
                            {
                                "question": "Curve-fitting means:",
                                "option_a": "Perfect fit to future data",
                                "option_b": "Over-optimized to historical noise, fails on new data",
                                "option_c": "Robust strategy design",
                                "option_d": "Risk management",
                                "correct_answer": "B",
                                "explanation": "Curve-fitting creates false excellence on past data by fitting randomness, not true market patterns.",
                                "topic_slug": "strategy_dev"
                            },
                            {
                                "question": "Robust strategy should survive:",
                                "option_a": "Parameter changes",
                                "option_b": "Different pairs",
                                "option_c": "Spread variations",
                                "option_d": "All of the above",
                                "correct_answer": "D",
                                "explanation": "True edge persists across parameter variations, multiple instruments, and realistic conditions.",
                                "topic_slug": "strategy_dev"
                            },
                            {
                                "question": "Scenario: Strategy works on EUR/USD but fails on GBP/USD. Problem?",
                                "option_a": "GBP/USD is random",
                                "option_b": "Strategy curve-fitted to EUR/USD specifics",
                                "option_c": "Different timezones",
                                "option_d": "Better on EUR",
                                "correct_answer": "B",
                                "explanation": "Robust edges work across similar instruments. Pair-specific performance suggests over-optimization.",
                                "topic_slug": "strategy_dev"
                            },
                            {
                                "question": "Mistake: Optimizing until 90% win rate achieved. Result?",
                                "option_a": "Future success",
                                "option_b": "Curve-fitted system that fails on new data",
                                "option_c": "Guaranteed profits",
                                "option_d": "Lower drawdown",
                                "correct_answer": "B",
                                "explanation": "90% win rates in backtests usually mean fitting to historical quirks, not predictive patterns.",
                                "topic_slug": "strategy_dev"
                            }
                        ]
                    },
                    {
                        "title": "Edge and Expectancy",
                        "content": """## Simple Definition
**Edge** is the mathematical advantage your strategy has over random chance. **Expectancy** quantifies that edge per trade: (Win% × AvgWin) - (Loss% × AvgLoss). Positive expectancy > 0 means long-term profitability.

## Concept Explanation
**Calculating Edge**:
- **Win Rate**: 45% (percentage of winning trades)
- **Average Win**: 2.2R (reward when right)
- **Average Loss**: 1.0R (risk when wrong)
- **Expectancy**: (0.45 × 2.2) - (0.55 × 1.0) = 0.99 - 0.55 = +0.44R per trade

**Law of Large Numbers**:
- Edge appears over 100+ trades
- 10 trades = variance (randomness dominates)
- 100 trades = edge emerging
- 1000 trades = deterministic results (if positive expectancy)

**R-Multiple Thinking**:
- Measure all outcomes in units of risk (R), not dollars
- +2R win = twice your risked amount
- -1R loss = exactly what was risked
- Allows comparison across different trade sizes

## Step-by-Step Breakdown
**Verifying Edge**:
1. **Record**: Minimum 100 live or forward-test trades
2. **Calculate**: Win rate and average R-multiple for wins/losses
3. **Expectancy**: Must be > 0.2R per trade (compensates for slippage/emotions)
4. **Distribution**: Check for fat tails (rare huge losses that skew results)
5. **Consecutive Losses**: Prepare mentally for worst streak from data

## Real Trading Example
**The Edge Reality**:
- **Strategy**: Support/Resistance bounces, 1:2 R:R minimum
- **Backtest**: 500 trades, 42% win rate, +1.8R avg win, -1R avg loss
- **Expectancy**: (0.42 × 1.8) - (0.58 × 1) = 0.756 - 0.58 = +0.176R
- **Monthly**: 20 trades × 0.176R = +3.5R per month
- **Capital**: $10k, 1% risk ($100), 3.5R = $350/month (3.5% return)
- **Annual**: ~42% return with proper execution
- **Key**: 58% of months feel "bad" due to win rate below 50%, but mathematically profitable

<svg class="ac-svg-diagram" viewBox="0 0 400 120">
  <rect x="50" y="30" width="300" height="60" fill="rgba(34,197,94,0.2)" stroke="#22c55e" rx="5"/>
  <text x="200" y="55" text-anchor="middle" fill="#22c55e" font-size="14" font-weight="bold">Expectancy = (Win% × AvgWin) - (Loss% × AvgLoss)</text>
  <text x="200" y="80" text-anchor="middle" fill="#9ca3af" font-size="12">Example: (40% × 2R) - (60% × 1R) = +0.2R per trade</text>
</svg>

## Common Beginner Mistake
**Win Rate Obsession**: Believing 70% win rate is necessary. A 40% win rate with 1:3 R:R is highly profitable (+0.6R expectancy). Focus on R:R and expectancy, not just accuracy.

## Key Takeaway
Trading is a probability business, not a prediction business. A 40% win rate with proper R:R outperforms 60% win rate with poor R:R. Calculate expectancy, trust the math, execute 1000 times.

## Practice Question
A strategy wins 35% of trades with average win of 3R and average loss of 1R. What is the expectancy?""",
                        "quiz": [
                            {
                                "question": "Expectancy formula is:",
                                "option_a": "Win% + Loss%",
                                "option_b": "(Win% × AvgWin) - (Loss% × AvgLoss)",
                                "option_c": "Total profit only",
                                "option_d": "Random",
                                "correct_answer": "B",
                                "explanation": "Expectancy = (Probability of Win × Average Win) - (Probability of Loss × Average Loss).",
                                "topic_slug": "strategy_dev"
                            },
                            {
                                "question": "Calculate: 35% win rate, 3R avg win, 1R avg loss. Expectancy?",
                                "option_a": "0",
                                "option_b": "0.05R",
                                "option_c": "+0.05R",
                                "option_d": "+0.5R",
                                "correct_answer": "C",
                                "explanation": "(0.35 × 3) - (0.65 × 1) = 1.05 - 0.65 = +0.40R per trade.",
                                "topic_slug": "strategy_dev"
                            },
                            {
                                "question": "Which is more important for profitability?",
                                "option_a": "High win rate only",
                                "option_b": "Positive expectancy",
                                "option_c": "Number of trades",
                                "option_d": "Low win rate",
                                "correct_answer": "B",
                                "explanation": "Positive expectancy (combination of win rate and R:R) determines long-term profitability.",
                                "topic_slug": "strategy_dev"
                            },
                            {
                                "question": "Scenario: 60% win rate but 0.8R avg win, 1R avg loss. Expectancy?",
                                "option_a": "+0.28R",
                                "option_b": "0",
                                "option_c": "-0.28R (losing)",
                                "option_d": "+1R",
                                "correct_answer": "C",
                                "explanation": "(0.6 × 0.8) - (0.4 × 1) = 0.48 - 0.40 = -0.08R. Actually losing despite 60% wins!",
                                "topic_slug": "strategy_dev"
                            },
                            {
                                "question": "Mistake: Focusing only on win rate, ignoring R:R. Risk?",
                                "option_a": "Profitable system",
                                "option_b": "High win rate but negative expectancy (losing)",
                                "option_c": "Better psychology",
                                "option_d": "Lower drawdown",
                                "correct_answer": "B",
                                "explanation": "Many high win-rate systems have poor R:R, creating negative expectancy despite feeling 'accurate'.",
                                "topic_slug": "strategy_dev"
                            }
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
A trading system integrates strategy (entries/exits), risk management (position sizing, drawdown limits), psychology (emotional controls), and routine (execution consistency) into a repeatable business model.

## Concept Explanation
**The Trading Business Plan**:
1. **Operations**: When, what, and how long to trade
2. **Strategy**: Specific entry/exit rules with backtested edge
3. **Risk Protocols**: Maximum risk per trade, day, week, and total drawdown halt
4. **Capital Allocation**: What percentage of total wealth is risk capital
5. **Review Cycles**: Weekly performance review, monthly strategy audit
6. **Infrastructure**: Platform, data feeds, backup internet/power

**Redundancy**:
- Two brokers (if one fails during volatility)
- Cloud-based journaling (local drive crashes)
- Pre-written contingency plans ("If I lose 20%, I do X")

**Scalability**:
- System works with $1k or $100k (just add zeros)
- Can you execute 10x size without emotional breakdown?
- Automation possibilities for execution

## Step-by-Step Breakdown
**System Checklist**:
- [ ] Strategy has positive expectancy over 100+ trades
- [ ] Risk per trade capped at 2%
- [ ] Maximum 6% daily loss limit (trading halt)
- [ ] Maximum 12% monthly drawdown (mandatory break)
- [ ] Pre-market routine defined and followed
- [ ] Trade journal with screenshots and emotions
- [ ] Weekly review process scheduled
- [ ] Broker funds segregated from living expenses

## Real Trading Example
**The Professional System**:
- **Capital**: $50,000 (2% of net worth—can afford to lose)
- **Strategy**: SMC (Order Blocks + FVG) on EUR/USD, GBP/USD
- **Risk**: 1% per trade ($500), max 3 trades/day
- **Schedule**: London/NY overlap only (3 hours)
- **Daily Limit**: -3% ($1,500) = stop trading
- **Review**: Sunday evening backtest review, Wednesday mid-week check
- **Journal**: Evernote with entry screenshots, R-multiple, emotion rating
- **Growth**: After 3 profitable months, increase size 25%

<svg class="ac-svg-diagram" viewBox="0 0 400 200">
  <rect x="50" y="50" width="100" height="100" fill="rgba(96,165,250,0.3)" stroke="#60a5fa" rx="5"/>
  <text x="100" y="105" text-anchor="middle" fill="#60a5fa" font-size="12">Strategy</text>
  <rect x="170" y="50" width="100" height="100" fill="rgba(245,158,11,0.3)" stroke="#f59e0b" rx="5"/>
  <text x="220" y="105" text-anchor="middle" fill="#f59e0b" font-size="12">Risk Mgmt</text>
  <rect x="290" y="50" width="100" height="100" fill="rgba(34,197,94,0.3)" stroke="#22c55e" rx="5"/>
  <text x="340" y="105" text-anchor="middle" fill="#22c55e" font-size="12">Psychology</text>
  <text x="200" y="180" text-anchor="middle" fill="#fbbf24" font-size="16" font-weight="bold">INTEGRATED SYSTEM</text>
</svg>

## Common Beginner Mistake
**Incomplete System**: Having entry rules but no daily loss limits. Strategy works but trader loses account to tilt. All components must be defined before first trade.

## Key Takeaway
Treat trading as a business, not a hobby. Businesses have operating procedures, risk management, and quality control. Your trading system is your franchise—document it, follow it, refine it. Survival and consistency come from systems, not impulses.

## Practice Question
What is the purpose of a maximum daily loss limit in a trading system?""",
                        "quiz": [
                            {
                                "question": "A trading system includes:",
                                "option_a": "Only entry rules",
                                "option_b": "Strategy, risk, psychology, and routine",
                                "option_c": "Only indicators",
                                "option_d": "Only capital",
                                "correct_answer": "B",
                                "explanation": "Complete systems integrate all elements: strategy, risk protocols, psychological controls, and operational routine.",
                                "topic_slug": "system"
                            },
                            {
                                "question": "Daily loss limit purpose is:",
                                "option_a": "Make back losses faster",
                                "option_b": "Prevent tilt spiral and large drawdowns",
                                "option_c": "Increase trading size",
                                "option_d": "Guarantee profits",
                                "correct_answer": "B",
                                "explanation": "Daily limits halt trading before emotional decisions create catastrophic losses.",
                                "topic_slug": "system"
                            },
                            {
                                "question": "Scalability means system works:",
                                "option_a": "Only with large accounts",
                                "option_b": "With any account size proportionally",
                                "option_c": "Only in bull markets",
                                "option_d": "Only one time",
                                "correct_answer": "B",
                                "explanation": "True systems scale—same rules, same percentages, just different dollar amounts.",
                                "topic_slug": "system"
                            },
                            {
                                "question": "Scenario: Strategy profitable but no daily limit. Risk?",
                                "option_a": "Safe trading",
                                "option_b": "Single bad day can destroy months of gains",
                                "option_c": "Better performance",
                                "option_d": "Lower risk",
                                "correct_answer": "B",
                                "explanation": "Without daily limits, emotional trading sessions can erase weeks of disciplined profits in hours.",
                                "topic_slug": "system"
                            },
                            {
                                "question": "Mistake: Trading without written business plan. Consequence?",
                                "option_a": "Consistency",
                                "option_b": "Inconsistent execution, no improvement framework",
                                "option_c": "Higher profits",
                                "option_d": "Better focus",
                                "correct_answer": "B",
                                "explanation": "Without documented system, you cannot identify what's failing or measure improvement.",
                                "topic_slug": "system"
                            }
                        ]
                    },
                    {
                        "title": "Professional Execution Plan",
                        "content": """## Simple Definition
Execution excellence is the bridge between strategy theory and realized profits. It involves precise order placement, timing optimization, and post-trade analysis to minimize slippage and maximize edge retention.

## Concept Explanation
**Order Types**:
- **Limit Orders**: Your price or better (avoids spread, risk of no fill)
- **Stop Orders**: Market order when price reached (guaranteed fill, slippage risk)
- **Stop-Limit**: Hybrid (limit slippage but may not fill in fast markets)

**Execution Timing**:
- **Avoid**: First 5 minutes of session (spreads wide, noise)
- **Avoid**: High-impact news releases (NFP, FOMC) unless news strategy
- **Optimal**: 15-30 minutes after session open, trends established, spreads normalized
- **Avoid**: Friday after 4 PM EST (weekend gap risk)

**Trade Management**:
- **Scale Out**: Close 50% at 1R (breakeven stop), 25% at 2R, 25% runner
- **Breakeven Stops**: Move to entry after 1R profit (eliminates risk, may get whipped)
- **Time Stops**: Exit if trade not working within expected timeframe (opportunity cost)

**Review Framework**:
- **Immediate**: Log trade within 5 minutes (emotion fresh)
- **End of Day**: Review all trades, patterns, deviations
- **Weekend**: Statistical analysis, strategy health check
- **Monthly**: Equity curve analysis, drawdown assessment

## Step-by-Step Breakdown
**Execution Checklist**:
1. **Pre-Trade**: Check correlation with existing positions
2. **Entry**: Limit order at technical level (not market order)
3. **Stop**: Set immediately, hidden from broker if possible
4. **Target**: Pre-set or manual at resistance/support
5. **Management**: Scale out per plan, move stop at 1R
6. **Post-Trade**: Screenshot chart, log R-multiple, emotional state

## Real Trading Example
**Professional vs Amateur Execution**:
- **Setup**: GBP/USD bullish pin bar at support
- **Amateur**: Market buy at 1.2550 (0.5 pip spread), stop 1.2520 (30 pips)
- **Professional**: Limit buy at 1.2545 (better fill), stop 1.2515 (30 pips from fill)
- **Difference**: 5 pips better entry = $50 savings per lot, compounded over 1000 trades
- **Management**: Amateur holds to target or stop. Professional takes 50% at 1.2575 (1R), moves stop to breakeven, risk-free runner

<div class="ac-tradingview-widget" data-symbol="FX:GBPUSD"></div>

## Common Beginner Mistake
**Market Orders**: Always using market orders creates slippage costs (2-5 pips per trade). On 1000 trades/year, 3-pip average slippage = 3000 pips lost to execution—often the difference between profit and loss.

## Key Takeaway
Edge is thin. Execution excellence preserves that edge. Use limit orders for entries, manage trades with scale-out techniques, and review every trade to identify execution drift. Trading is a business of basis points—optimize every component.

## Practice Question
Why should you consider using limit orders instead of market orders for entries?""",
                        "quiz": [
                            {
                                "question": "Limit orders vs market orders:",
                                "option_a": "Market orders always better",
                                "option_b": "Limit orders avoid spread costs, get better fills",
                                "option_c": "No difference",
                                "option_d": "Limit orders are slower",
                                "correct_answer": "B",
                                "explanation": "Limit orders placed at your price avoid spread markup and often get filled at better prices than market orders.",
                                "topic_slug": "system"
                            },
                            {
                                "question": "Scale out technique means:",
                                "option_a": "All or nothing exit",
                                "option_b": "Closing partial positions at different targets",
                                "option_c": "Adding to losers",
                                "option_d": "Removing stops",
                                "correct_answer": "B",
                                "explanation": "Scale out: Close 50% at 1R (secure profit), 25% at 2R, 25% runner for home runs.",
                                "topic_slug": "system"
                            },
                            {
                                "question": "Best time to avoid trading?",
                                "option_a": "London open",
                                "option_b": "NFP release",
                                "option_c": "NY overlap",
                                "option_d": "Tuesday afternoon",
                                "correct_answer": "B",
                                "explanation": "High impact news creates spread widening and slippage. Avoid unless specifically news trading.",
                                "topic_slug": "system"
                            },
                            {
                                "question": "Scenario: Up 1R on trade. Stop placement?",
                                "option_a": "Leave at original stop",
                                "option_b": "Move to breakeven (risk-free trade)",
                                "option_c": "Remove stop",
                                "option_d": "Tighten to 0.5R",
                                "correct_answer": "B",
                                "explanation": "At 1R profit, moving stop to entry creates risk-free runner—can't lose money on trade.",
                                "topic_slug": "system"
                            },
                            {
                                "question": "Mistake: Not logging trades immediately. Risk?",
                                "option_a": "Better memory",
                                "option_b": "Forgotten details, missed improvement opportunities",
                                "option_c": "Faster trading",
                                "option_d": "Lower stress",
                                "correct_answer": "B",
                                "explanation": "Delaying journaling leads to forgotten emotional states and execution errors, preventing improvement.",
                                "topic_slug": "system"
                            }
                        ]
                    }
                ]
            }
        ]
    }
]
