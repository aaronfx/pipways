"""
Pipways Trading Academy — Complete Professional Curriculum
36 Lessons (3 Levels × 6 Modules × 2 Lessons)
Features: Structured content, quiz questions, SVG diagrams, chart examples
Format: Clean markdown with visual teaching style
Improvements: Removed TradingView widgets, added chart placeholders, standardized format
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
                            "content": """## Quick Definition
    
    Forex (Foreign Exchange) is the global marketplace where currencies are traded. It operates **24 hours a day, 5 days a week**, with over **$7.5 trillion** traded daily.
    
    ---
    
    ## Concept Explanation
    
    Unlike stock markets with centralized exchanges, Forex is **decentralized** and operates across major financial centers: Sydney, Tokyo, London, and New York.
    
    ### How Currency Pairs Work
    
    *   **Base Currency**: The first currency (EUR in EUR/USD)
    *   **Quote Currency**: The second currency (USD in EUR/USD)
    *   **Exchange Rate**: How much of the quote currency equals one unit of base currency
    
    ---
    
    ## Step-by-Step Breakdown
    
    1.  **Select a Currency Pair**: Start with EUR/USD for tight spreads
    2.  **Analyze Direction**: Buy if you expect the base currency to strengthen
    3.  **Calculate Position Size**: Based on your risk (1-2% rule)
    4.  **Set Stop Loss**: Maximum amount you are willing to lose
    5.  **Execute**: Buy or sell based on your analysis
    
    ---
    
    ## Real Trading Example
    
    **Scenario**: You expect EUR to strengthen against USD
    
    *   **Entry**: Buy at **1.0850**
    *   **Position Size**: **0.1 lots** ($1 per pip)
    *   **Stop Loss**: **1.0830** (20 pips = **$20** risk)
    *   **Take Profit**: **1.0890** (40 pips = **$40** reward)
    *   **Risk:Reward Ratio**: **1:2**
    
    ---
    
    ## 📊 Chart Example
    
    <svg class="ac-svg-diagram" viewBox="0 0 480 200" xmlns="http://www.w3.org/2000/svg"><rect width="480" height="200" fill="#0d1117" rx="8"/><text x="240" y="16" text-anchor="middle" fill="#a78bfa" font-size="11" font-weight="bold">EUR/USD — Entry Example (1:2 Risk:Reward)</text><polyline points="20,160 60,150 100,155 140,130 180,120 220,110 260,125 300,100 340,85 380,90 440,70" fill="none" stroke="#34d399" stroke-width="2.5"/><circle cx="140" cy="130" r="5" fill="#fbbf24"/><text x="148" y="126" fill="#fbbf24" font-size="10">BUY 1.0850</text><line x1="140" y1="148" x2="420" y2="148" stroke="#f87171" stroke-width="1" stroke-dasharray="4"/><text x="422" y="152" fill="#f87171" font-size="9">SL 1.0830</text><line x1="140" y1="112" x2="420" y2="112" stroke="#34d399" stroke-width="1" stroke-dasharray="4"/><text x="422" y="116" fill="#34d399" font-size="9">TP 1.0890</text><text x="240" y="190" text-anchor="middle" fill="#6b7280" font-size="9">Risk: 20 pips ($20) | Reward: 40 pips ($40) | R:R = 1:2</text></svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **Overtrading**: New traders believe more trades equals more profit. Reality: **Quality over quantity**. Taking 5 random trades typically loses more than taking 1 high-probability setup.
    
    ---
    
    ## 💡 Pro Tip
    
    Focus on **major pairs** (EUR/USD, GBP/USD, USD/JPY) when learning. They have the tightest spreads (**0.1-0.3 pips**) and most predictable behavior.
    
    ---
    
    ## Key Takeaway
    
    Forex trading is about **probability and risk management**, not prediction. Your edge comes from managing risk, not being right every time.
    
    ---
    
    ## Practice Question
    
    If EUR/USD rises from **1.0500** to **1.0550**, how many pips did it move?""",
                            "quiz": [
                                {"question": "What does EUR/USD represent?", "option_a": "Euros per US Dollar", "option_b": "US Dollars per Euro", "option_c": "Exchange rate index", "option_d": "Stock price", "correct_answer": "B", "explanation": "EUR/USD shows how many USD one Euro buys. If rate is 1.0850, €1 = $1.0850.", "topic_slug": "forex_basics"},
                                {"question": "What is a pip in most currency pairs?", "option_a": "0.01", "option_b": "0.001", "option_c": "0.0001", "option_d": "1.0", "correct_answer": "C", "explanation": "For most pairs, 1 pip = 0.0001 (4th decimal place). JPY pairs use 0.01.", "topic_slug": "forex_basics"},
                                {"question": "Calculate: EUR/USD moves from 1.0500 to 1.0550. How many pips?", "option_a": "5 pips", "option_b": "50 pips", "option_c": "500 pips", "option_d": "0.5 pips", "correct_answer": "B", "explanation": "1.0550 - 1.0500 = 0.0050 = 50 pips.", "topic_slug": "forex_basics"},
                                {"question": "Scenario: You buy EUR/USD at 1.0850 with 0.1 lots. Price drops to 1.0800. Loss?", "option_a": "$5", "option_b": "$50", "option_c": "$500", "option_d": "$5,000", "correct_answer": "B", "explanation": "50 pips × $1/pip (0.1 lots) = $50 loss.", "topic_slug": "forex_basics"},
                                {"question": "Why should beginners avoid 1:500 leverage?", "option_a": "Lower profits", "option_b": "Extreme risk", "option_c": "Higher spreads", "option_d": "Slower execution", "correct_answer": "B", "explanation": "High leverage amplifies losses. A 20-pip move can wipe out a small account.", "topic_slug": "forex_basics"}
                            ]
                        },
                        {
                            "title": "Who Trades Forex and Why?",
                            "content": """## Quick Definition
    
    Forex participants range from **central banks** to individual retail traders, each with different goals and market impact.
    
    ---
    
    ## Concept Explanation
    
    ### Market Hierarchy by Volume
    
    **Tier 1: Central Banks & Major Commercial Banks** — 50%+ of volume
    *   Control monetary policy (interest rates)
    *   Create largest price movements
    
    **Tier 2: Hedge Funds & Corporations** — 40% of volume
    *   Facilitate international transactions
    *   Speculate with massive capital
    
    **Tier 3: Retail Traders** — Less than 10% of volume
    *   Speculate on price movements
    
    ---
    
    ## Step-by-Step Breakdown
    
    1.  **Identify the Big Players**: Central banks create the biggest moves
    2.  **Follow Institutional Flow**: Trade in the direction of large orders
    3.  **Avoid Fighting Trends**: Never counter-trade central bank interventions
    4.  **Use Your Agility**: Retail advantage is speed, not size
    
    ---
    
    ## Real Trading Example
    
    **The SNB Shock (2015)**: Swiss National Bank unexpectedly removed the EUR/CHF peg at 1.20. The franc surged **30%** in minutes.
    
    *   **Impact**: Retail traders with stops below 1.20 were wiped out
    *   **Lesson**: Never fight central banks
    
    ---
    
    ## 📊 Chart Example
    
        
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
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **Fighting the Banks**: Trying to catch falling knives during central bank interventions. Retail traders cannot reverse institutional flows.
    
    ---
    
    ## 💡 Pro Tip
    
    **Follow the Smart Money**: When price breaks key levels with momentum, institutions are likely entering.
    
    ---
    
    ## Key Takeaway
    
    You are a small fish in a big ocean. Your advantage is **agility**, not size.
    
    ---
    
    ## Practice Question
    
    Which market participant creates the largest price movements?""",
                            "quiz": [
                                {"question": "Which participant moves markets most?", "option_a": "Retail traders", "option_b": "Central banks", "option_c": "Your broker", "option_d": "Social media influencers", "correct_answer": "B", "explanation": "Central banks control interest rates and monetary policy.", "topic_slug": "market_participants"},
                                {"question": "Why do corporations trade forex?", "option_a": "To speculate for profit", "option_b": "To convert foreign earnings", "option_c": "To manipulate prices", "option_d": "For entertainment", "correct_answer": "B", "explanation": "Corporations trade to convert foreign revenue back to domestic currency.", "topic_slug": "market_participants"},
                                {"question": "What percentage of daily volume comes from retail traders?", "option_a": "50%", "option_b": "25%", "option_c": "10%", "option_d": "Less than 10%", "correct_answer": "D", "explanation": "Retail traders represent less than 10% of the $7.5 trillion daily volume.", "topic_slug": "market_participants"},
                                {"question": "Scenario: Deutsche Bank sells $2B EUR/USD. You buy 1 micro lot. Effect?", "option_a": "You reverse the trend", "option_b": "Institutional volume dwarfs your trade", "option_c": "You profit immediately", "option_d": "Bank follows your position", "correct_answer": "B", "explanation": "Institutional volume is massive compared to retail trades.", "topic_slug": "market_participants"},
                                {"question": "Best practice when central bank intervenes?", "option_a": "Trade against the intervention", "option_b": "Trade with the flow or stay out", "option_c": "Double your position size", "option_d": "Use maximum leverage", "correct_answer": "B", "explanation": "Never fight central banks. Trade with their flow or wait.", "topic_slug": "market_participants"}
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
                            "content": """## Quick Definition
    
    Currency pairs are categorized by liquidity: **Majors** (most traded), **Minors** (crosses without USD), and **Exotics** (emerging markets).
    
    ---
    
    ## Concept Explanation
    
    ### Major Pairs (All include USD)
    
    *   **EUR/USD**: 28% of daily volume, tightest spreads
    *   **USD/JPY**: 13%, "safe haven" during uncertainty
    *   **GBP/USD**: 11%, most volatile major
    
    ### Minor (Cross) Pairs
    
    Pairs without USD: EUR/GBP, EUR/JPY, GBP/JPY
    *   Wider spreads than majors
    *   Still liquid enough for trading
    
    ### Exotic Pairs
    
    USD/ZAR, USD/TRY, USD/MXN
    *   **Huge spreads** (50-200 pips)
    *   **High volatility** and swap fees
    
    ---
    
    ## Step-by-Step Breakdown
    
    1.  **Start with Majors**: Trade EUR/USD exclusively while learning
    2.  **Check Spread Costs**: Exotics cost $50+ per trade vs $0.20 for majors
    3.  **Monitor Correlations**: EUR/USD and GBP/USD move together ~90%
    4.  **Avoid Weekend Gaps**: Exotics gap massively on Sunday opens
    
    ---
    
    ## Real Trading Example
    
    **Beginner Account**: $1,000
    
    *   **Bad Choice**: USD/ZAR with **50-pip spread** = $50 cost (5% of account)
    *   **Good Choice**: EUR/USD with **0.2-pip spread** = $0.20 cost
    
    ---
    
    ## 📊 Chart Example
    
    <svg class="ac-svg-diagram" viewBox="0 0 480 200" xmlns="http://www.w3.org/2000/svg"><rect width="480" height="200" fill="#0d1117" rx="8"/><text x="240" y="20" text-anchor="middle" fill="#a78bfa" font-size="12" font-weight="bold">Currency Pair Categories</text><rect x="20" y="35" width="130" height="145" fill="rgba(52,211,153,0.08)" stroke="#34d399" rx="6"/><text x="85" y="55" text-anchor="middle" fill="#34d399" font-size="11" font-weight="bold">MAJORS</text><text x="85" y="72" text-anchor="middle" fill="#9ca3af" font-size="9">Tightest spreads</text><text x="85" y="90" text-anchor="middle" fill="#e5e7eb" font-size="10">EUR/USD</text><text x="85" y="108" text-anchor="middle" fill="#e5e7eb" font-size="10">GBP/USD</text><text x="85" y="126" text-anchor="middle" fill="#e5e7eb" font-size="10">USD/JPY</text><text x="85" y="144" text-anchor="middle" fill="#e5e7eb" font-size="10">USD/CHF</text><text x="85" y="168" text-anchor="middle" fill="#34d399" font-size="9">Best for beginners</text><rect x="170" y="35" width="130" height="145" fill="rgba(96,165,250,0.08)" stroke="#60a5fa" rx="6"/><text x="235" y="55" text-anchor="middle" fill="#60a5fa" font-size="11" font-weight="bold">MINORS</text><text x="235" y="72" text-anchor="middle" fill="#9ca3af" font-size="9">No USD involved</text><text x="235" y="90" text-anchor="middle" fill="#e5e7eb" font-size="10">EUR/GBP</text><text x="235" y="108" text-anchor="middle" fill="#e5e7eb" font-size="10">EUR/JPY</text><text x="235" y="126" text-anchor="middle" fill="#e5e7eb" font-size="10">GBP/JPY</text><text x="235" y="144" text-anchor="middle" fill="#e5e7eb" font-size="10">AUD/JPY</text><text x="235" y="168" text-anchor="middle" fill="#60a5fa" font-size="9">Good for variety</text><rect x="320" y="35" width="140" height="145" fill="rgba(245,158,11,0.08)" stroke="#f59e0b" rx="6"/><text x="390" y="55" text-anchor="middle" fill="#f59e0b" font-size="11" font-weight="bold">EXOTICS</text><text x="390" y="72" text-anchor="middle" fill="#9ca3af" font-size="9">Emerging markets</text><text x="390" y="90" text-anchor="middle" fill="#e5e7eb" font-size="10">USD/TRY</text><text x="390" y="108" text-anchor="middle" fill="#e5e7eb" font-size="10">USD/ZAR</text><text x="390" y="126" text-anchor="middle" fill="#e5e7eb" font-size="10">USD/MXN</text><text x="390" y="144" text-anchor="middle" fill="#e5e7eb" font-size="10">EUR/TRY</text><text x="390" y="168" text-anchor="middle" fill="#f59e0b" font-size="9">Wide spreads — avoid</text></svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **Trading Exotics for "Excitement"**: Beginners see USD/TRY moving 500 pips daily but ignore the **200-pip spread** and **$20/night swap fees**.
    
    ---
    
    ## 💡 Pro Tip
    
    Master **one pair** before diversifying. EUR/USD has the cleanest price action and best liquidity.
    
    ---
    
    ## Key Takeaway
    
    Start with EUR/USD only. Tight spreads save money; liquidity ensures your stops execute at the right price.
    
    ---
    
    ## Practice Question
    
    Which pair is generally best for beginners and why?""",
                            "quiz": [
                                {"question": "Which is a major pair?", "option_a": "EUR/GBP", "option_b": "EUR/USD", "option_c": "USD/ZAR", "option_d": "GBP/JPY", "correct_answer": "B", "explanation": "Majors always include USD. EUR/USD is most traded with tightest spreads.", "topic_slug": "currency_pairs"},
                                {"question": "Which pair type has widest spreads?", "option_a": "Majors", "option_b": "Minors", "option_c": "Exotics", "option_d": "All equal", "correct_answer": "C", "explanation": "Exotics like USD/TRY have 50-200 pip spreads vs 0.1-0.3 for majors.", "topic_slug": "currency_pairs"},
                                {"question": "Calculate: 0.1 lots USD/ZAR with 50-pip spread. Cost?", "option_a": "$0.50", "option_b": "$5", "option_c": "$50", "option_d": "$500", "correct_answer": "C", "explanation": "0.1 lots = $1/pip. 50 pips × $1 = $50 spread cost.", "topic_slug": "currency_pairs"},
                                {"question": "EUR/USD and GBP/USD correlation?", "option_a": "Opposite", "option_b": "90% same direction", "option_c": "No correlation", "option_d": "Random", "correct_answer": "B", "explanation": "Both move against USD, making them highly correlated.", "topic_slug": "currency_pairs"},
                                {"question": "Best practice for exotic pairs?", "option_a": "Trade as beginner", "option_b": "Avoid until experienced", "option_c": "Use max leverage", "option_d": "Trade daily", "correct_answer": "B", "explanation": "Exotics have massive spreads and overnight fees.", "topic_slug": "currency_pairs"}
                            ]
                        },
                        {
                            "title": "Reading Pips and Spreads",
                            "content": """## Quick Definition
    
    A **pip** is the smallest price move (0.0001 for most pairs). The **spread** is the difference between buy (ask) and sell (bid) prices.
    
    ---
    
    ## Concept Explanation
    
    ### Pip Values by Pair
    
    *   **Most pairs**: 0.0001 = 1 pip (4th decimal)
    *   **JPY pairs**: 0.01 = 1 pip (2nd decimal)
    
    ### Lot Sizes
    
    *   **Standard (1.0)**: $10 per pip
    *   **Mini (0.1)**: $1 per pip
    *   **Micro (0.01)**: $0.10 per pip
    
    ---
    
    ## Step-by-Step Breakdown
    
    1.  **Calculate Exposure**: 0.5 lots EUR/USD at 1.0850 = $54,250 notional
    2.  **Determine Pip Value**: 0.5 lots = $5 per pip
    3.  **Calculate Spread Cost**: 2-pip spread × $5 = $10 entry cost
    4.  **Include in Risk**: $100 risk budget - $10 spread = $90 for actual stop
    
    ---
    
    ## Real Trading Example
    
    **Account**: $5,000 | Risk: 2% = $100 | EUR/USD Buy
    
    *   **Setup**: Entry 1.0850, Stop at 1.0830 (20 pips)
    *   **Spread**: 1.5 pips (0.00015)
    *   **Effective Stop**: 20 - 1.5 = 18.5 pips
    *   **Calculation**: $100 ÷ 18.5 pips = $5.40/pip = **0.54 lots**
    
    <svg class="ac-svg-diagram" viewBox="0 0 400 120">
      <rect x="20" y="30" width="150" height="40" fill="rgba(239,68,68,0.2)" stroke="#ef4444" rx="5"/>
      <text x="95" y="55" text-anchor="middle" fill="#ef4444" font-size="12">Bid: 1.08498</text>
      <line x1="170" y1="50" x2="230" y2="50" stroke="#f59e0b" stroke-width="2"/>
      <text x="200" y="45" text-anchor="middle" fill="#f59e0b" font-size="12">2 pips</text>
      <rect x="230" y="30" width="150" height="40" fill="rgba(34,197,94,0.2)" stroke="#22c55e" rx="5"/>
      <text x="305" y="55" text-anchor="middle" fill="#22c55e" font-size="12">Ask: 1.08502</text>
    </svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **Ignoring Spread in Stop Loss**: You set a 10-pip stop, but spread is 3 pips. Your actual stop is only **7 pips** away—a **30% increase** in risk.
    
    ---
    
    ## 💡 Pro Tip
    
    **Trade During Active Hours**: Spreads widen to 5-10 pips during Asian session. Trade London/NY overlap for tightest spreads.
    
    ---
    
    ## Key Takeaway
    
    Pips measure movement; spreads measure cost. Calculate both before entering.
    
    ---
    
    ## Practice Question
    
    If you trade 0.3 lots with 1.5-pip spread, what is entry cost?""",
                            "quiz": [
                                {"question": "1 pip on EUR/USD standard lot?", "option_a": "$0.10", "option_b": "$1", "option_c": "$10", "option_d": "$100", "correct_answer": "C", "explanation": "1 standard lot moves $10 per pip.", "topic_slug": "pips_lots"},
                                {"question": "What is the spread?", "option_a": "Trend direction", "option_b": "Difference between bid and ask", "option_c": "Commission fee", "option_d": "Swap rate", "correct_answer": "B", "explanation": "Spread is buy price minus sell price.", "topic_slug": "pips_lots"},
                                {"question": "Calculate: 0.3 lots, 1.5-pip spread. Cost?", "option_a": "$0.45", "option_b": "$4.50", "option_c": "$45", "option_d": "$450", "correct_answer": "B", "explanation": "0.3 lots = $3/pip. 1.5 × $3 = $4.50.", "topic_slug": "pips_lots"},
                                {"question": "You set 15-pip stop, spread is 2 pips. Actual distance?", "option_a": "15", "option_b": "17", "option_c": "13", "option_d": "30", "correct_answer": "C", "explanation": "15 - 2 = 13 pips actual distance.", "topic_slug": "pips_lots"},
                                {"question": "Trading without pip value calculation?", "option_a": "Lower risk", "option_b": "Cannot size positions correctly", "option_c": "Higher profits", "option_d": "No effect", "correct_answer": "B", "explanation": "Without pip value, you cannot calculate proper position size.", "topic_slug": "pips_lots"}
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
                            "content": """## Quick Definition
    
    **Leverage** allows controlling large positions with small capital. Expressed as ratio (1:100), meaning $1,000 controls $100,000 position.
    
    ---
    
    ## Concept Explanation
    
    ### How Leverage Works
    *   **1:100 leverage**: $1,000 margin controls $100,000 position
    *   **1:50 leverage**: $1,000 controls $50,000
    
    ### Double-Edged Sword
    *   **1% market move** with 1:100 leverage = **100% gain or loss** on margin
    *   Leverage amplifies BOTH profits AND losses equally
    
    ### Margin Requirements
    *   **Margin Used**: Position Size ÷ Leverage
    *   **Free Margin**: Equity - Margin Used (keep >50% to avoid calls)
    
    ---
    
    ## Step-by-Step Breakdown
    
    1.  **Calculate Margin**: Position Size ÷ Leverage = Required Margin
    2.  **Monitor Free Margin**: Keep buffer above 50% of used margin
    3.  **Understand Margin Call**: Equity drops below required margin = positions closed
    4.  **Use Conservative Leverage**: 1:10 to 1:30 maximum for beginners
    
    ---
    
    ## Real Trading Example
    
    **Account**: $5,000 with 1:100 leverage
    
    *   **Trade**: Buy 0.5 lots ($50,000 notional)
    *   **Margin Used**: $50,000 ÷ 100 = $500
    *   **Free Margin**: $5,000 - $500 = $4,500 buffer
    *   **Liquidation Risk**: Account drops to $500 = margin call
    
    <svg class="ac-svg-diagram" viewBox="0 0 400 150">
      <rect x="20" y="60" width="80" height="40" fill="rgba(245,158,11,0.3)" stroke="#f59e0b" rx="5"/>
      <text x="60" y="85" text-anchor="middle" fill="#f59e0b" font-size="12">$1,000</text>
      <line x1="100" y1="80" x2="140" y2="80" stroke="#60a5fa" stroke-width="2"/>
      <text x="120" y="70" text-anchor="middle" fill="#60a5fa" font-size="10">1:100</text>
      <rect x="140" y="40" width="240" height="80" fill="rgba(34,197,94,0.2)" stroke="#22c55e" rx="5"/>
      <text x="260" y="80" text-anchor="middle" fill="#22c55e" font-size="16">$100,000 Position</text>
      <text x="200" y="130" text-anchor="middle" fill="#ef4444" font-size="12">1% move = ±$1,000</text>
    </svg>
    
    ---
    
    ## 📊 Chart Example
    
    <svg class="ac-svg-diagram" viewBox="0 0 480 200" xmlns="http://www.w3.org/2000/svg"><rect width="480" height="200" fill="#0d1117" rx="8"/><text x="240" y="20" text-anchor="middle" fill="#a78bfa" font-size="11" font-weight="bold">Leverage: Amplifies Both Gains AND Losses</text><text x="30" y="55" fill="#9ca3af" font-size="10">No Leverage (1:1)</text><rect x="30" y="62" width="60" height="16" fill="#34d399" rx="3"/><text x="95" y="74" fill="#34d399" font-size="10">$1,000 controls $1,000</text><text x="30" y="100" fill="#9ca3af" font-size="10">1:10 Leverage</text><rect x="30" y="107" width="120" height="16" fill="#fbbf24" rx="3"/><text x="155" y="119" fill="#fbbf24" font-size="10">$1,000 controls $10,000</text><text x="30" y="145" fill="#9ca3af" font-size="10">1:100 Leverage ⚠️</text><rect x="30" y="152" width="300" height="16" fill="#f87171" rx="3"/><text x="335" y="164" fill="#f87171" font-size="10">$1,000 controls $100,000</text><text x="240" y="192" text-anchor="middle" fill="#6b7280" font-size="9">Higher leverage = bigger position = risk of account wipeout on small moves</text></svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **Maximum Leverage**: Using 1:500 with $1,000 account. A **20-pip move** ($100 at 1 lot) wipes out the account. Brokers offer high leverage to encourage overtrading.
    
    ---
    
    ## 💡 Pro Tip
    
    **Use 1:10 to 1:30 Leverage**: Even with small accounts, use low leverage. It forces proper position sizing and prevents catastrophic losses.
    
    ---
    
    ## Key Takeaway
    
    Use 1:10 to 1:30 leverage. Never risk >2% per trade regardless of available leverage. Leverage is a tool, not a strategy.
    
    ---
    
    ## Practice Question
    
    With 1:200 leverage and $2,000 account, maximum theoretical position size?""",
                            "quiz": [
                                {"question": "1:100 leverage, $1,000 controls?", "option_a": "$1,000", "option_b": "$10,000", "option_c": "$100,000", "option_d": "$1,000,000", "correct_answer": "C", "explanation": "$1,000 × 100 = $100,000 maximum position size.", "topic_slug": "leverage"},
                                {"question": "Effect of leverage on losses?", "option_a": "Decrease", "option_b": "Stay same", "option_c": "Amplify equally with gains", "option_d": "Disappear", "correct_answer": "C", "explanation": "Leverage amplifies both gains AND losses equally.", "topic_slug": "leverage"},
                                {"question": "Calculate: $10,000 account, 1:50 leverage. Position size?", "option_a": "$5,000", "option_b": "$50,000", "option_c": "$500,000", "option_d": "$20,000", "correct_answer": "C", "explanation": "$10,000 × 50 = $500,000 maximum theoretical position.", "topic_slug": "leverage"}
                            ]
                        },
                        {
                            "title": "Position Sizing Calculation",
                            "content": """## Quick Definition
    
    **Position sizing** determines lot size based on account size, risk percentage, and stop loss distance. This is the most critical skill for survival.
    
    ---
    
    ## Concept Explanation
    
    ### The Formula
    **Position Size** = Account Risk ($) ÷ (Stop Loss (pips) × Pip Value ($))
    
    ### Variables
    *   **Account Risk**: 1-2% of account balance
    *   **Stop Loss**: Technical invalidation point (not arbitrary)
    *   **Pip Value**: $10 per pip for standard lot
    
    ---
    
    ## Step-by-Step Breakdown
    
    **Example**: $10,000 account, 2% risk, 50-pip stop
    
    1.  **Risk Amount**: $10,000 × 2% = **$200**
    2.  **Pip Value Needed**: $200 ÷ 50 pips = **$4/pip**
    3.  **Lot Size**: $4 ÷ $10 = **0.4 lots**
    
    ---
    
    ## Real Trading Example
    
    **Account**: $3,000 | Risk: 1% ($30) | Stop: 30 pips
    
    *   **Calculation**: $30 ÷ 30 pips = $1/pip needed
    *   **Lot Size**: $1/pip = **0.1 lots** (1 mini lot)
    *   **Result**: Perfect sizing for risk parameters
    
    ---
    
    ## 📊 Chart Example
    
    <svg class="ac-svg-diagram" viewBox="0 0 480 200" xmlns="http://www.w3.org/2000/svg"><rect width="480" height="200" fill="#0d1117" rx="8"/><text x="240" y="20" text-anchor="middle" fill="#a78bfa" font-size="12" font-weight="bold">Position Sizing Formula</text><rect x="30" y="32" width="420" height="40" fill="rgba(124,58,237,0.15)" stroke="#7c3aed" rx="6"/><text x="240" y="50" text-anchor="middle" fill="#c4b5fd" font-size="11">Lot Size = (Account × Risk%) ÷ (Stop Loss pips × Pip Value)</text><text x="240" y="65" text-anchor="middle" fill="#9ca3af" font-size="9">Max risk = 1–2% of account per trade</text><text x="30" y="95" fill="#fbbf24" font-size="11" font-weight="bold">Example:</text><text x="30" y="113" fill="#e5e7eb" font-size="10">Account: $10,000 | Risk: 1% = $100 | SL: 20 pips | Pip Value: $1</text><text x="30" y="133" fill="#34d399" font-size="12" font-weight="bold">Lot Size = $100 ÷ (20 × $1) = 0.5 mini lots</text><text x="30" y="162" fill="#9ca3af" font-size="9">Safe:</text><rect x="70" y="152" width="60" height="12" fill="#34d399" rx="2"/><text x="100" y="162" text-anchor="middle" fill="#0d1117" font-size="9">1–2%</text><rect x="145" y="152" width="60" height="12" fill="#f59e0b" rx="2"/><text x="175" y="162" text-anchor="middle" fill="#0d1117" font-size="9">3–5%</text><rect x="220" y="152" width="60" height="12" fill="#f87171" rx="2"/><text x="250" y="162" text-anchor="middle" fill="#0d1117" font-size="9">5%+ danger</text><text x="240" y="190" text-anchor="middle" fill="#6b7280" font-size="9">Never risk more than 2% on a single trade</text></svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **Fixed Lot Sizes**: Trading 1.0 lot every trade regardless of account or stop distance. This creates random risk (0.5% to 20% per trade) and guarantees blowup.
    
    ---
    
    ## 💡 Pro Tip
    
    **Size for the Stop**: Calculate position size AFTER determining technical stop placement. Never adjust your stop to fit a desired position size.
    
    ---
    
    ## Key Takeaway
    
    Position sizing is the only "holy grail." Calculate size before entering; never adjust stop to fit desired size. Proper sizing ensures survival through losing streaks.
    
    ---
    
    ## Practice Question
    
    $5,000 account, 2% risk, 25-pip stop. What lot size?""",
                            "quiz": [
                                {"question": "Position sizing formula?", "option_a": "Account × leverage", "option_b": "Risk ÷ (stop × pip value)", "option_c": "Maximum lots", "option_d": "Random", "correct_answer": "B", "explanation": "Size = Account Risk ($) ÷ (Stop (pips) × Pip Value ($)).", "topic_slug": "position_sizing"},
                                {"question": "$10,000 account, 2% risk. Risk amount?", "option_a": "$20", "option_b": "$200", "option_c": "$2,000", "option_d": "$200,000", "correct_answer": "B", "explanation": "$10,000 × 2% = $200 maximum risk per trade.", "topic_slug": "position_sizing"},
                                {"question": "Calculate: $5,000, 1% risk, 40-pip stop. Pip value needed?", "option_a": "$1.25", "option_b": "$12.50", "option_c": "$125", "option_d": "$1,250", "correct_answer": "A", "explanation": "$5,000 × 1% = $50. $50 ÷ 40 pips = $1.25/pip.", "topic_slug": "position_sizing"}
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
                            "content": """## Quick Definition
    
    The Forex market operates **24/5**, divided into three sessions: Asian (Tokyo), London, and New York. Each has unique characteristics affecting volatility and liquidity.
    
    ---
    
    ## Concept Explanation
    
    ### Asian Session (Tokyo): 00:00–09:00 UTC
    *   Lower volatility, range-bound movement
    *   JPY pairs most active
    *   **Best for**: Range trading
    
    ### London Session: 08:00–17:00 UTC
    *   **Highest liquidity** globally—35-40% of daily volume
    *   EUR, GBP, CHF most active
    *   **Best for**: Trend following, breakouts
    
    ### New York Session: 13:00–22:00 UTC
    *   USD pairs volatile
    *   Overlap with London (13:00–17:00 UTC) = **Golden Hours**
    
    ---
    
    ## Step-by-Step Breakdown
    
    1.  **Identify Your Session**: Trade when you are sharp AND market is active
    2.  **Golden Window**: 13:00–17:00 UTC = 70% of daily volume
    3.  **Avoid Low Liquidity**: Friday evenings, Sunday opens, holidays
    4.  **Session-Specific Pairs**: Trade JPY during Asian, EUR during London
    
    ---
    
    ## Real Trading Example
    
    **London Breakout Strategy**:
    *   **Wait**: Asian range formation (20:00–08:00 UTC)
    *   **Place**: Buy stop above Asian high, Sell stop below Asian low
    *   **Trigger**: London open often creates breakouts
    *   **Result**: 70% of daily range established in first 2 hours
    
    ---
    
    ## 📊 Chart Example
    
        
    <svg class="ac-svg-diagram" viewBox="0 0 600 150">
      <rect x="20" y="50" width="160" height="50" fill="rgba(251,191,36,0.2)" stroke="#fbbf24" rx="5"/>
      <text x="100" y="78" text-anchor="middle" fill="#fbbf24" font-size="12">Asian (00-09 UTC)</text>
      <rect x="200" y="50" width="180" height="50" fill="rgba(96,165,250,0.3)" stroke="#60a5fa" rx="5"/>
      <text x="290" y="78" text-anchor="middle" fill="#60a5fa" font-size="12">London (08-17 UTC)</text>
      <rect x="340" y="50" width="180" height="50" fill="rgba(52,211,153,0.3)" stroke="#34d399" rx="5"/>
      <text x="430" y="78" text-anchor="middle" fill="#34d399" font-size="12">NY (13-22 UTC)</text>
      <rect x="380" y="30" width="140" height="15" fill="rgba(167,139,250,0.5)" rx="3"/>
      <text x="450" y="42" text-anchor="middle" fill="#fff" font-size="10">GOLDEN</text>
    </svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **Trading Asian Session**: Trading at midnight wondering why price barely moves. Low liquidity means wider spreads and false breakouts.
    
    ---
    
    ## 💡 Pro Tip
    
    **Golden Hours (8am-12pm EST)**: 70% of daily volume happens here. If you can only trade 2 hours, make it this window.
    
    ---
    
    ## Key Takeaway
    
    Quality trading happens during specific hours. The London-NY overlap offers best opportunities.
    
    ---
    
    ## Practice Question
    
    When does highest liquidity occur?""",
                            "quiz": [
                                {"question": "Three major sessions?", "option_a": "Morning/Afternoon/Evening", "option_b": "Asian/London/New York", "option_c": "Open/High/Close", "option_d": "Bull/Bear/Sideways", "correct_answer": "B", "explanation": "The three major sessions are Asian, London, and New York.", "topic_slug": "sessions"},
                                {"question": "Active pairs during Asian session?", "option_a": "EUR/USD", "option_b": "USD/CAD", "option_c": "JPY pairs", "option_d": "GBP pairs", "correct_answer": "C", "explanation": "JPY pairs are most active during Tokyo hours.", "topic_slug": "sessions"},
                                {"question": "London-New York overlap (UTC)?", "option_a": "08:00-12:00", "option_b": "13:00-17:00", "option_c": "20:00-00:00", "option_d": "00:00-04:00", "correct_answer": "B", "explanation": "13:00-17:00 UTC is the overlap offering highest liquidity.", "topic_slug": "sessions"},
                                {"question": "Trading GBP/USD at 03:00 UTC?", "option_a": "High volatility", "option_b": "Tight spreads", "option_c": "Low liquidity", "option_d": "Major breakout", "correct_answer": "C", "explanation": "03:00 UTC is deep Asian session—low liquidity for GBP pairs.", "topic_slug": "sessions"},
                                {"question": "Risk of trading Sunday evening?", "option_a": "Guaranteed trends", "option_b": "Weekend gaps", "option_c": "Low spreads", "option_d": "High liquidity", "correct_answer": "B", "explanation": "Sunday opens often have gaps from weekend news.", "topic_slug": "sessions"}
                            ]
                        },
                        {
                            "title": "Best Times to Trade",
                            "content": """## Quick Definition
    
    Not all trading hours are equal. The **Golden Window** offers the best combination of liquidity, volatility, and directional movement.
    
    ---
    
    ## Concept Explanation
    
    ### The Golden Window: 13:00–17:00 UTC
    *   70% of daily volume concentrated here
    *   Tightest spreads (0.1-0.3 pips on majors)
    *   Most directional moves occur
    
    ### Times to Avoid
    *   **Friday after 18:00 UTC**: Weekend gap risk
    *   **Sunday 21:00–23:00 UTC**: Erratic, low volume
    *   **Major news releases**: Unless trading news specifically
    *   **Holidays**: Banks closed, liquidity dries up
    
    ---
    
    ## Step-by-Step Breakdown
    
    1.  **Pre-Market**: Check economic calendar, mark key levels
    2.  **Golden Window**: Execute high-probability setups
    3.  **Afternoon**: Manage existing positions only
    4.  **Evening**: Journal trades, no new entries
    
    ---
    
    ## Real Trading Example
    
    **2-Hour Trader Schedule**:
    *   **12:30 UTC**: Analyze charts, mark S/R
    *   **13:00 UTC**: Wait for valid setup
    *   **14:30 UTC**: Enter valid setup
    *   **16:00 UTC**: Close positions, journal
    
    ---
    
    ## 📊 Chart Example
    
    <svg class="ac-svg-diagram" viewBox="0 0 480 180" xmlns="http://www.w3.org/2000/svg"><rect width="480" height="180" fill="#0d1117" rx="8"/><text x="240" y="18" text-anchor="middle" fill="#a78bfa" font-size="11" font-weight="bold">Best Trading Hours (GMT)</text><text x="30" y="38" fill="#6b7280" font-size="8">00:00</text><text x="105" y="38" fill="#6b7280" font-size="8">06:00</text><text x="175" y="38" fill="#6b7280" font-size="8">08:00</text><text x="280" y="38" fill="#6b7280" font-size="8">13:00</text><text x="365" y="38" fill="#6b7280" font-size="8">17:00</text><text x="435" y="38" fill="#6b7280" font-size="8">22:00</text><rect x="30" y="46" width="75" height="22" fill="rgba(96,165,250,0.3)" stroke="#60a5fa" rx="3"/><text x="67" y="62" text-anchor="middle" fill="#60a5fa" font-size="9">Tokyo</text><rect x="170" y="46" width="145" height="22" fill="rgba(167,139,250,0.3)" stroke="#a78bfa" rx="3"/><text x="242" y="62" text-anchor="middle" fill="#a78bfa" font-size="9">London</text><rect x="270" y="46" width="160" height="22" fill="rgba(52,211,153,0.3)" stroke="#34d399" rx="3"/><text x="350" y="62" text-anchor="middle" fill="#34d399" font-size="9">New York</text><rect x="270" y="46" width="75" height="22" fill="rgba(251,191,36,0.5)" stroke="#fbbf24" rx="3"/><text x="307" y="62" text-anchor="middle" fill="#fbbf24" font-size="9">OVERLAP ⭐</text><text x="30" y="100" fill="#fbbf24" font-size="10" font-weight="bold">⭐ London–NY Overlap (13:00–17:00 GMT) = Highest volume and volatility</text><text x="30" y="118" fill="#9ca3af" font-size="9">EUR/USD and GBP/USD most active during London–NY overlap</text><text x="30" y="136" fill="#6b7280" font-size="9">Avoid Asian session for major pairs — low volume, wide spreads</text><text x="30" y="162" fill="#34d399" font-size="9">Rule: Trade during sessions that match your currency pair</text></svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **All-Day Trading**: Sitting at charts 8+ hours leads to fatigue, revenge trading, and losses during choppy sessions.
    
    ---
    
    ## 💡 Pro Tip
    
    **Set a Time Limit**: Professional traders trade 2-4 hours maximum. After that, decision fatigue increases errors.
    
    ---
    
    ## Key Takeaway
    
    Trade 2 hours during Golden Window beats 8 random hours. More trades ≠ more profit.
    
    ---
    
    ## Practice Question
    
    Why avoid holding trades over weekend?""",
                            "quiz": [
                                {"question": "The 'Golden Window'?", "option_a": "Any profitable time", "option_b": "London-NY overlap 13:00-17:00 UTC", "option_c": "Weekend trading", "option_d": "Holidays", "correct_answer": "B", "explanation": "13:00-17:00 UTC offers best liquidity and directional moves.", "topic_slug": "sessions"},
                                {"question": "Avoid trading when?", "option_a": "Tuesday 14:00 UTC", "option_b": "Friday evening UTC", "option_c": "Thursday 10:00 UTC", "option_d": "Wednesday overlap", "correct_answer": "B", "explanation": "Friday evening has weekend gap risk.", "topic_slug": "sessions"},
                                {"question": "Cost difference: Friday 5-pip vs Wed 0.5-pip, 1 lot?", "option_a": "$5", "option_b": "$45", "option_c": "$50", "option_d": "$500", "correct_answer": "B", "explanation": "4.5 pip difference × $10 = $45 extra cost.", "topic_slug": "sessions"},
                                {"question": "Perfect setup at 22:00 UTC Sunday?", "option_a": "Enter immediately", "option_b": "Wait for Monday liquidity", "option_c": "Increase size", "option_d": "Market order", "correct_answer": "B", "explanation": "Sunday 22:00 has gap risk and low liquidity.", "topic_slug": "sessions"},
                                {"question": "8 hours straight trading consequence?", "option_a": "More profit", "option_b": "Fatigue and overtrading", "option_c": "Better focus", "option_d": "Guaranteed success", "correct_answer": "B", "explanation": "Long sessions cause decision fatigue and poor execution.", "topic_slug": "sessions"}
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
                            "content": """## Quick Definition
    
    Never risk more than **1-2% of total account equity** on any single trade. This ensures survival through inevitable losing streaks.
    
    ---
    
    ## Concept Explanation
    
    ### Survival Math
    *   **2% risk**: 50 consecutive losses to blow account
    *   **5% risk**: 20 losses to blow account
    *   **10% risk**: 10 losses to blow account
    
    ### Compounding Protection
    *   2% risk preserves 98% of capital after loss
    *   Easy to recover from 2% losses psychologically
    
    ---
    
    ## Step-by-Step Breakdown
    
    1.  **Calculate 2%**: Balance × 0.02 = Max Risk ($)
    2.  **Determine Stop Distance**: Technical level minus entry
    3.  **Size Accordingly**: (Pips × Pip Value) ≤ Max Risk
    4.  **Hard Stop**: Set immediately upon entry
    
    ---
    
    ## Real Trading Example
    
    **Month 1 - 2% Risk ($10,000 account)**:
    *   Week 1: 5 wins, 3 losses = +$400
    *   Week 2: 4 wins, 4 losses = $0
    *   Week 3: 3 wins, 5 losses = -$400
    *   **Net**: Break even despite losing more trades
    
    ---
    
    ## 📊 Chart Example
    
    <svg class="ac-svg-diagram" viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg"><rect width="480" height="190" fill="#0d1117" rx="8"/><text x="240" y="18" text-anchor="middle" fill="#a78bfa" font-size="11" font-weight="bold">Account Survival After 10 Consecutive Losses ($10,000 start)</text><text x="30" y="48" fill="#9ca3af" font-size="10">1% risk:</text><rect x="100" y="38" width="260" height="16" fill="#34d399" rx="3"/><text x="365" y="50" fill="#34d399" font-size="10">$9,044 remaining ✅</text><text x="30" y="80" fill="#9ca3af" font-size="10">2% risk:</text><rect x="100" y="70" width="230" height="16" fill="#fbbf24" rx="3"/><text x="335" y="82" fill="#fbbf24" font-size="10">$8,171 remaining ✅</text><text x="30" y="112" fill="#9ca3af" font-size="10">5% risk:</text><rect x="100" y="102" width="160" height="16" fill="#fb923c" rx="3"/><text x="265" y="114" fill="#fb923c" font-size="10">$5,987 remaining ⚠️</text><text x="30" y="144" fill="#9ca3af" font-size="10">10% risk:</text><rect x="100" y="134" width="75" height="16" fill="#f87171" rx="3"/><text x="180" y="146" fill="#f87171" font-size="10">$3,487 remaining ❌</text><text x="240" y="175" text-anchor="middle" fill="#34d399" font-size="9">Professional traders risk 0.5–2% max. Consistency beats home runs.</text></svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **"I only have $500, so I need 20% risk"**: This guarantees failure. Small accounts should trade micro lots with 1% risk.
    
    ---
    
    ## 💡 Pro Tip
    
    **1% for Learning, 2% for Earning**: Use 1% risk while learning. Move to 2% only after consistent profitability.
    
    ---
    
    ## Key Takeaway
    
    The 1-2% rule is survival math. You must survive losing streaks to reach winning streaks.
    
    ---
    
    ## Practice Question
    
    $5,000 account, 2% risk. Maximum dollar risk per trade?""",
                            "quiz": [
                                {"question": "Maximum recommended risk per trade?", "option_a": "10%", "option_b": "5%", "option_c": "1-2%", "option_d": "25%", "correct_answer": "C", "explanation": "Never risk more than 1-2% per trade to survive losing streaks.", "topic_slug": "risk_management"},
                                {"question": "With 2% risk, consecutive losses to blow account?", "option_a": "10", "option_b": "20", "option_c": "50", "option_d": "5", "correct_answer": "C", "explanation": "2% × 50 = 100%. Requires 50 consecutive losses.", "topic_slug": "risk_management"},
                                {"question": "Calculate: $5,000 account, 2% risk. Max loss?", "option_a": "$10", "option_b": "$100", "option_c": "$1,000", "option_d": "$10,000", "correct_answer": "B", "explanation": "$5,000 × 2% = $100 maximum risk per trade.", "topic_slug": "risk_management"}
                            ]
                        },
                        {
                            "title": "Stop Loss and Take Profit",
                            "content": """## Quick Definition
    
    Every trade requires predetermined exit points: **Stop Loss** (maximum acceptable loss) and **Take Profit** (target where reward justifies risk).
    
    ---
    
    ## Concept Explanation
    
    ### Stop Loss Placement
    *   **Long trades**: SL below support or recent low
    *   **Short trades**: SL above resistance or recent high
    *   **Volatility buffer**: Add 1-2x ATR to avoid noise
    
    ### Take Profit Targets
    *   **Minimum 1:2 Risk:Reward**
    *   **Previous swing highs/lows**: Natural resistance/support
    *   **Trailing stops**: Move SL to breakeven at 1R profit
    
    ---
    
    ## Step-by-Step Breakdown
    
    **Trade Setup - EUR/USD Long**:
    1.  **Entry**: 1.0850 (break of resistance)
    2.  **Stop**: 1.0830 (below support, 20 pips)
    3.  **Take Profit**: 1.0890 (next resistance, 40 pips)
    4.  **Risk**: $200 (2% of $10k)
    5.  **Reward**: $400 (40 pips × $5/pip)
    6.  **R:R**: 1:2
    
    ---
    
    ## Real Trading Example
    
    **Perfect Setup - EUR/USD**:
    *   **Context**: Bounces off 1.0850 support (3rd touch)
    *   **Confirmation**: Bullish engulfing candle
    *   **Entry**: 1.0852
    *   **SL**: 1.0840 (12 pips)
    *   **TP**: 1.0872 (20 pips)
    *   **Position**: 0.16 lots ($1.60/pip × 12 = $192 risk)
    *   **Result**: 1.67 R:R, target hit in 4 hours
    
    ---
    
    ## 📊 Chart Example
    
    <svg class="ac-svg-diagram" viewBox="0 0 480 200" xmlns="http://www.w3.org/2000/svg"><rect width="480" height="200" fill="#0d1117" rx="8"/><text x="240" y="18" text-anchor="middle" fill="#a78bfa" font-size="11" font-weight="bold">Stop Loss Placement — Below Support</text><polyline points="30,170 70,155 100,162 140,140 170,148 210,125 240,132 280,110 310,118 350,95 390,102 430,80" fill="none" stroke="#60a5fa" stroke-width="2"/><line x1="30" y1="148" x2="460" y2="148" stroke="#34d399" stroke-width="1.5" stroke-dasharray="5"/><text x="33" y="143" fill="#34d399" font-size="9">Support Zone</text><circle cx="210" cy="125" r="5" fill="#fbbf24"/><text x="215" y="120" fill="#fbbf24" font-size="9">Entry (buy at support)</text><line x1="30" y1="163" x2="460" y2="163" stroke="#f87171" stroke-width="1.5" stroke-dasharray="3"/><text x="33" y="175" fill="#f87171" font-size="9">Stop Loss (below support — avoids stop hunts)</text><line x1="30" y1="95" x2="460" y2="95" stroke="#34d399" stroke-width="1" stroke-dasharray="3"/><text x="33" y="90" fill="#34d399" font-size="9">Take Profit</text><text x="240" y="195" text-anchor="middle" fill="#6b7280" font-size="9">Place stop BELOW support (not at it). Target minimum 1:2 risk:reward.</text></svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **Moving Stop Losses**: Price approaches SL, trader moves it "just a bit lower" to avoid loss. Turns planned $100 loss into unplanned $300+ loss.
    
    ---
    
    ## 💡 Pro Tip
    
    **Set and Forget**: Enter SL and TP immediately upon entry. Set alerts, not watches. Walk away.
    
    ---
    
    ## Key Takeaway
    
    Set SL and TP before clicking buy/sell. Once entered, only move SL toward profit (trailing), never away from it.
    
    ---
    
    ## Practice Question
    
    You enter EUR/USD at 1.1000, SL at 1.0980, TP at 1.1040. Risk:Reward ratio?""",
                            "quiz": [
                                {"question": "Where is SL for BUY trade?", "option_a": "Above resistance", "option_b": "Below support", "option_c": "At entry", "option_d": "Random", "correct_answer": "B", "explanation": "Buy stops go below support.", "topic_slug": "risk_management"},
                                {"question": "Minimum recommended R:R ratio?", "option_a": "1:1", "option_b": "1:2", "option_c": "1:0.5", "option_d": "2:1", "correct_answer": "B", "explanation": "Minimum 1:2 R:R allows 40% win rate to be profitable.", "topic_slug": "risk_management"},
                                {"question": "Calculate: Entry 1.1000, SL 1.0980, TP 1.1040. R:R?", "option_a": "1:1", "option_b": "1:2", "option_c": "2:1", "option_d": "4:1", "correct_answer": "B", "explanation": "20 pips risk, 40 pips reward = 1:2 ratio.", "topic_slug": "risk_management"}
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
                            "content": """## Quick Definition
    
    Candlestick charts display price using "candles" showing **Open, High, Low, Close (OHLC)** for specific periods.
    
    ---
    
    ## Concept Explanation
    
    ### Candle Anatomy
    *   **Body**: Area between open and close
        *   **Green**: Close > Open (Bullish)
        *   **Red**: Close < Open (Bearish)
    *   **Wicks**: Lines showing high and low
    
    ### Reading Sentiment
    *   **Large body**: Strong conviction
    *   **Small body**: Indecision
    *   **Long upper wick**: Rejection of higher prices
    
    ---
    
    ## Step-by-Step Breakdown
    
    **Reading a Candle**:
    1.  **Body size**: Large = strong conviction. Small = indecision.
    2.  **Wick length**: Long upper wick = rejection.
    3.  **Color sequence**: Green after red = potential reversal.
    4.  **Context**: Single candle means nothing. Three candles = pattern.
    
    ---
    
    ## Real Trading Example
    
    **The Hammer Pattern** (Bullish Reversal):
    *   **Appearance**: Small body at top, long lower wick
    *   **Location**: Bottom of downtrend
    *   **Meaning**: Sellers pushed down, buyers regained control
    *   **Entry**: Buy above hammer high
    *   **Stop**: Below hammer low
    
    ---
    
    ## 📊 Chart Example
    
    <svg class="ac-svg-diagram" viewBox="0 0 480 200" xmlns="http://www.w3.org/2000/svg"><rect width="480" height="200" fill="#0d1117" rx="8"/><text x="240" y="18" text-anchor="middle" fill="#a78bfa" font-size="11" font-weight="bold">Candlestick Anatomy</text><text x="100" y="38" text-anchor="middle" fill="#34d399" font-size="11" font-weight="bold">Bullish (Green)</text><line x1="100" y1="48" x2="100" y2="68" stroke="#34d399" stroke-width="2"/><rect x="75" y="68" width="50" height="80" fill="rgba(52,211,153,0.3)" stroke="#34d399" stroke-width="2" rx="2"/><line x1="100" y1="148" x2="100" y2="168" stroke="#34d399" stroke-width="2"/><text x="140" y="63" fill="#9ca3af" font-size="9">High (upper wick)</text><text x="140" y="85" fill="#34d399" font-size="9">Close (top of body)</text><text x="140" y="138" fill="#34d399" font-size="9">Open (bottom)</text><text x="140" y="162" fill="#9ca3af" font-size="9">Low (lower wick)</text><text x="340" y="38" text-anchor="middle" fill="#f87171" font-size="11" font-weight="bold">Bearish (Red)</text><line x1="340" y1="48" x2="340" y2="68" stroke="#f87171" stroke-width="2"/><rect x="315" y="68" width="50" height="80" fill="rgba(239,68,68,0.3)" stroke="#f87171" stroke-width="2" rx="2"/><line x1="340" y1="148" x2="340" y2="168" stroke="#f87171" stroke-width="2"/><text x="255" y="85" text-anchor="end" fill="#f87171" font-size="9">Open (top)</text><text x="255" y="138" text-anchor="end" fill="#f87171" font-size="9">Close (bottom)</text><text x="240" y="190" text-anchor="middle" fill="#6b7280" font-size="9">Green = buyers dominated | Red = sellers dominated | Body size = conviction</text></svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **Candlestick Trading Without Context**: Taking "perfect" bullish engulfing at top of 6-month uptrend against major resistance.
    
    ---
    
    ## 💡 Pro Tip
    
    **Start with Daily Charts**: Daily candles contain more information and noise-filtering than lower timeframes.
    
    ---
    
    ## Key Takeaway
    
    Candles show sentiment. Wicks show rejection. Bodies show conviction. Always read within context.
    
    ---
    
    ## Practice Question
    
    What does long upper wick indicate?""",
                            "quiz": [
                                {"question": "Green candle indicates?", "option_a": "Closed lower than open", "option_b": "Closed higher than open", "option_c": "No movement", "option_d": "Market closed", "correct_answer": "B", "explanation": "Green candles mean Close > Open.", "topic_slug": "candlestick_patterns"},
                                {"question": "Long upper wick shows?", "option_a": "Strong buying", "option_b": "Rejection of higher prices", "option_c": "Closed high", "option_d": "Low volatility", "correct_answer": "B", "explanation": "Long upper wick means price rejected from higher levels.", "topic_slug": "candlestick_patterns"},
                                {"question": "Open 1.1000, Close 1.1020, High 1.1030, Low 1.0990. Body size?", "option_a": "10 pips", "option_b": "20 pips", "option_c": "40 pips", "option_d": "30 pips", "correct_answer": "B", "explanation": "Body = Close - Open = 20 pips.", "topic_slug": "candlestick_patterns"}
                            ]
                        },
                        {
                            "title": "Support and Resistance Basics",
                            "content": """## Quick Definition
    
    **Support**: Price level where buying overcomes selling, causing bounces.
    **Resistance**: Price level where selling overcomes buying, causing rejections.
    
    ---
    
    ## Concept Explanation
    
    ### Why These Levels Exist
    *   **Psychological**: Round numbers (1.1000, 1.2000)
    *   **Historical**: Previous highs/lows leave unfilled orders
    *   **Institutional**: Banks place large orders at specific prices
    
    ### Role Reversal
    *   Once support breaks, it often becomes resistance
    *   Once resistance breaks, it often becomes support
    
    ---
    
    ## Step-by-Step Breakdown
    
    **Drawing Support**:
    1.  Find 2+ price lows at similar level (±15 pips)
    2.  Connect lows with horizontal line
    3.  Extend into future
    4.  More touches = stronger support
    
    ---
    
    ## Real Trading Example
    
    **Triple Top Pattern**:
    *   **Setup**: EUR/USD tests 1.1000 three times over 2 months
    *   **Each test**: Produces long upper wicks (rejection)
    *   **Trade**: Short at 1.0990, SL at 1.1020, TP at 1.0850
    *   **Risk**: 30 pips | **Reward**: 140 pips | **R:R**: 1:4.7
    
    ---
    
    ## 📊 Chart Example
    
    <svg class="ac-svg-diagram" viewBox="0 0 480 195" xmlns="http://www.w3.org/2000/svg"><rect width="480" height="195" fill="#0d1117" rx="8"/><text x="240" y="18" text-anchor="middle" fill="#a78bfa" font-size="11" font-weight="bold">Support &amp; Resistance Levels</text><polyline points="30,165 70,148 100,162 140,135 180,148 220,125 250,142 290,118 320,135 360,108 400,122 440,100" fill="none" stroke="#60a5fa" stroke-width="2"/><line x1="30" y1="122" x2="460" y2="122" stroke="#f87171" stroke-width="1.5" stroke-dasharray="6"/><text x="35" y="117" fill="#f87171" font-size="10" font-weight="bold">RESISTANCE — sellers push price down here</text><line x1="30" y1="162" x2="460" y2="162" stroke="#34d399" stroke-width="1.5" stroke-dasharray="6"/><text x="35" y="178" fill="#34d399" font-size="10" font-weight="bold">SUPPORT — buyers push price up here</text><text x="148" y="114" fill="#f87171" font-size="14">↓</text><text x="228" y="114" fill="#f87171" font-size="14">↓</text><text x="68" y="158" fill="#34d399" font-size="14">↑</text><text x="178" y="158" fill="#34d399" font-size="14">↑</text></svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **Exact Price Levels**: Drawing lines at exact prices (1.0850) instead of zones (1.0840–1.0860). Markets are messy—use 10-20 pip zones.
    
    ---
    
    ## 💡 Pro Tip
    
    **3-Touch Rule**: A level is not valid until price has reversed off it at least 3 times.
    
    ---
    
    ## Key Takeaway
    
    Support and resistance are zones, not lines. The more times tested, the weaker they become.
    
    ---
    
    ## Practice Question
    
    What happens to support once clearly broken?""",
                            "quiz": [
                                {"question": "Support represents?", "option_a": "Selling pressure", "option_b": "Buying overcoming selling", "option_c": "Market top", "option_d": "Random price", "correct_answer": "B", "explanation": "Support is where buyers step in.", "topic_slug": "support_resistance"},
                                {"question": "What is 'role reversal'?", "option_a": "Traders swapping", "option_b": "Broken resistance becomes support", "option_c": "Trend reversal", "option_d": "Price gaps", "correct_answer": "B", "explanation": "Once resistance breaks, it often becomes support.", "topic_slug": "support_resistance"},
                                {"question": "Touches needed to validate level?", "option_a": "1", "option_b": "2 or more", "option_c": "10", "option_d": "None", "correct_answer": "B", "explanation": "Need at least 2-3 clear touches with reversals.", "topic_slug": "support_resistance"}
                            ]
                        }
                    ]
                }
            ]
        },
    {
            "level_name": "Intermediate",
            "description": "Build technical analysis skills with trend analysis, chart patterns, and indicator strategies. Learn to read market structure and identify high-probability setups.",
            "modules": [
                {
                    "title": "Trend Analysis",
                    "description": "Identifying and trading with the trend using multiple timeframes.",
                    "lessons": [
                        {
                            "title": "Identifying Trends",
                            "content": """## Quick Definition
    
    A **trend** is the general direction of price movement over time. Trends exist in three timeframes simultaneously: primary (long-term), intermediate (medium-term), and short-term.
    
    ---
    
    ## Concept Explanation
    
    ### Types of Trends
    *   **Uptrend**: Higher highs and higher lows
    *   **Downtrend**: Lower highs and lower lows
    *   **Sideways/Range**: Price oscillates between support and resistance
    
    ### Trend Strength Indicators
    *   **Steepness**: Steeper = stronger (but exhausting faster)
    *   **Duration**: Longer trends = more reliable
    *   **Volume**: Rising volume confirms trend strength
    
    ---
    
    ## Step-by-Step Breakdown
    
    **Identifying an Uptrend**:
    1.  Connect higher lows with trendline
    2.  Check that each high is higher than previous
    3.  Confirm on higher timeframe
    4.  Trade only in trend direction (buy dips)
    
    ---
    
    ## Real Trading Example
    
    **EUR/USD Daily Trend** (Feb-May 2024):
    *   Higher lows: 1.0650 → 1.0700 → 1.0750
    *   Higher highs: 1.0800 → 1.0850 → 1.0900
    *   20 EMA slope: Positive (+0.15% daily)
    *   ADX: 35 (strong trend)
    *   Result: 450-pip move over 3 months
    
    ---
    
    ## 📊 Chart Example
    
    <svg class="ac-svg-diagram" viewBox="0 0 480 195" xmlns="http://www.w3.org/2000/svg"><rect width="480" height="195" fill="#0d1117" rx="8"/><text x="240" y="16" text-anchor="middle" fill="#a78bfa" font-size="11" font-weight="bold">Trend Structure: Higher Highs/Lows vs Lower Highs/Lows</text><text x="80" y="35" text-anchor="middle" fill="#34d399" font-size="10" font-weight="bold">UPTREND</text><polyline points="20,170 50,152 80,162 110,132 140,148 170,112" fill="none" stroke="#34d399" stroke-width="2"/><circle cx="50" cy="152" r="4" fill="#fbbf24"/><text x="45" y="147" fill="#fbbf24" font-size="8">HL</text><circle cx="110" cy="132" r="4" fill="#34d399"/><text x="114" y="128" fill="#34d399" font-size="8">HH</text><circle cx="140" cy="148" r="4" fill="#fbbf24"/><text x="144" y="158" fill="#fbbf24" font-size="8">HL</text><circle cx="170" cy="112" r="4" fill="#34d399"/><text x="174" y="108" fill="#34d399" font-size="8">HH</text><line x1="240" y1="30" x2="240" y2="180" stroke="#374151" stroke-width="1" stroke-dasharray="4"/><text x="360" y="35" text-anchor="middle" fill="#f87171" font-size="10" font-weight="bold">DOWNTREND</text><polyline points="260,80 290,100 320,90 350,118 380,106 410,135 440,122 460,148" fill="none" stroke="#f87171" stroke-width="2"/><circle cx="290" cy="100" r="4" fill="#f87171"/><text x="286" y="95" fill="#f87171" font-size="8">LH</text><circle cx="380" cy="106" r="4" fill="#f87171"/><text x="376" y="101" fill="#f87171" font-size="8">LH</text><circle cx="440" cy="122" r="4" fill="#fbbf24"/><text x="444" y="138" fill="#fbbf24" font-size="8">LL</text><text x="240" y="188" text-anchor="middle" fill="#6b7280" font-size="9">Trade WITH the trend — HH+HL = buy setups | LH+LL = sell setups</text></svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **Counter-Trend Trading**: Trying to pick tops in strong uptrends. "It can't go higher" is the most expensive phrase in trading. Trade with the trend until structure breaks.
    
    ---
    
    ## 💡 Pro Tip
    
    **The 200-Day Rule**: Price above 200-day MA = long-term uptrend. Only trade long above, short below. This simple filter improves win rates significantly.
    
    ---
    
    ## Key Takeaway
    
    The trend is your friend until it ends. Use higher highs/lows to identify direction. Counter-trend trading requires expertise—master trend-following first.
    
    ---
    
    ## Practice Question
    
    What sequence defines an uptrend?""",
                            "quiz": [
                                {"question": "What defines an uptrend?", "option_a": "Lower highs, lower lows", "option_b": "Higher highs, higher lows", "option_c": "Equal highs, equal lows", "option_d": "Random movement", "correct_answer": "B", "explanation": "Higher highs and higher lows = uptrend.", "topic_slug": "trend_analysis"},
                                {"question": "Best trading practice in strong uptrend?", "option_a": "Short every rally", "option_b": "Buy pullbacks", "option_c": "Trade opposite direction", "option_d": "Avoid trading", "correct_answer": "B", "explanation": "Buy dips in uptrends, sell rallies in downtrends.", "topic_slug": "trend_analysis"},
                                {"question": "Price above 200-day MA indicates?", "option_a": "Bear market", "option_b": "Long-term uptrend", "option_c": "Sideways market", "option_d": "Reversal coming", "correct_answer": "B", "explanation": "200-day MA acts as long-term trend filter.", "topic_slug": "trend_analysis"}
                            ]
                        },
                        {
                            "title": "Multiple Timeframe Analysis",
                            "content": """## Quick Definition
    
    **Multiple Timeframe Analysis (MTA)** uses longer timeframes to identify the primary trend, intermediate for timing, and shorter for precise entries. This creates a complete market view.
    
    ---
    
    ## Concept Explanation
    
    ### The Triple Screen Method
    *   **Screen 1 (Higher TF)**: Weekly/Daily for trend direction
    *   **Screen 2 (Intermediate TF)**: H4/H1 for setups
    *   **Screen 3 (Lower TF)**: M15/M5 for entries
    
    ### Timeframe Alignment Rules
    *   All timeframes aligned = highest probability trades
    *   Higher TF trend > Lower TF signals
    *   Conflict = stay out or reduce size
    
    ---
    
    ## Step-by-Step Breakdown
    
    **Example: EUR/USD Long Setup**:
    1.  **Daily**: Price above 20 EMA, uptrend confirmed
    2.  **H4**: Pullback to support, bullish hammer formed
    3.  **M15**: Break of micro-resistance, momentum building
    4.  **Entry**: M15 breakout with all timeframes aligned
    
    ---
    
    ## Real Trading Example
    
    **GBP/JPY Breakout** (March 2024):
    *   **Weekly**: Above 50 MA, bullish structure
    *   **Daily**: Break of 185.00 resistance
    *   **H4**: Retest of broken resistance as support
    *   **H1**: Bullish engulfing at support
    *   **Result**: 200-pip move in 2 days, 1:4 R:R
    
    ---
    
    ## 📊 Chart Example
    
    <svg class="ac-svg-diagram" viewBox="0 0 480 195" xmlns="http://www.w3.org/2000/svg"><rect width="480" height="195" fill="#0d1117" rx="8"/><text x="240" y="18" text-anchor="middle" fill="#a78bfa" font-size="11" font-weight="bold">Multi-Timeframe Analysis (Top-Down Approach)</text><rect x="130" y="30" width="220" height="34" fill="rgba(245,158,11,0.15)" stroke="#f59e0b" rx="6"/><text x="240" y="48" text-anchor="middle" fill="#f59e0b" font-size="11">Monthly / Weekly</text><text x="240" y="60" text-anchor="middle" fill="#9ca3af" font-size="9">Overall trend direction</text><line x1="240" y1="64" x2="240" y2="76" stroke="#374151" stroke-width="2"/><rect x="90" y="76" width="300" height="34" fill="rgba(96,165,250,0.15)" stroke="#60a5fa" rx="6"/><text x="240" y="94" text-anchor="middle" fill="#60a5fa" font-size="11">Daily / 4-Hour</text><text x="240" y="106" text-anchor="middle" fill="#9ca3af" font-size="9">Key levels, structure, context</text><line x1="240" y1="110" x2="240" y2="122" stroke="#374151" stroke-width="2"/><rect x="50" y="122" width="380" height="34" fill="rgba(52,211,153,0.15)" stroke="#34d399" rx="6"/><text x="240" y="140" text-anchor="middle" fill="#34d399" font-size="11">1-Hour / 15-Minute</text><text x="240" y="152" text-anchor="middle" fill="#9ca3af" font-size="9">Entry timing and precise stop placement</text><text x="240" y="180" text-anchor="middle" fill="#fbbf24" font-size="9">Rule: Only enter trades where all 3 timeframes agree on direction</text></svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **Timeframe Confusion**: Taking M5 signals against the daily trend. The lower timeframe has more noise. Always check if the higher timeframe supports your trade direction.
    
    ---
    
    ## 💡 Pro Tip
    
    **Use 4x Multipliers**: If trading H1, check H4 (4x higher) for trend and M15 (4x lower) for entries. This creates natural alignment without over-complication.
    
    ---
    
    ## Key Takeaway
    
    Trade in the direction of the higher timeframe trend. Use lower timeframes for precision entries. When timeframes conflict, the higher timeframe wins.
    
    ---
    
    ## Practice Question
    
    Daily shows uptrend, H1 shows sell signal. What do you do?""",
                            "quiz": [
                                {"question": "Purpose of higher timeframe?", "option_a": "Precise entries", "option_b": "Trend direction", "option_c": "Stop placement", "option_d": "Exit timing", "correct_answer": "B", "explanation": "Higher TF identifies primary trend direction.", "topic_slug": "trend_analysis"},
                                {"question": "Timeframe conflict resolution?", "option_a": "Trade lower TF", "option_b": "Higher TF wins", "option_c": "Average both", "option_d": "Increase size", "correct_answer": "B", "explanation": "Higher timeframe trend supersedes lower TF signals.", "topic_slug": "trend_analysis"},
                                {"question": "Best practice when timeframes conflict?", "option_a": "Trade anyway", "option_b": "Stay out or reduce size", "option_c": "Trade both directions", "option_d": "Use maximum leverage", "correct_answer": "B", "explanation": "Conflicting signals = reduced probability. Stay out or size down.", "topic_slug": "trend_analysis"}
                            ]
                        }
                    ]
                },
                {
                    "title": "Support and Resistance Mastery",
                    "description": "Advanced S/R concepts including zones, trendlines, and channels.",
                    "lessons": [
                        {
                            "title": "Dynamic Support and Resistance",
                            "content": """## Quick Definition
    
    **Dynamic Support/Resistance** moves with price, unlike static horizontal levels. Includes moving averages, trendlines, and channels that adapt to current market conditions.
    
    ---
    
    ## Concept Explanation
    
    ### Moving Averages as Dynamic S/R
    *   **20 EMA**: Short-term dynamic S/R
    *   **50 SMA**: Intermediate trend filter
    *   **200 SMA**: Long-term trend filter
    
    ### Trendlines
    *   Connect higher lows (uptrend) or lower highs (downtrend)
    *   More touches = stronger trendline
    *   Break of trendline = potential reversal
    
    ---
    
    ## Step-by-Step Breakdown
    
    **Drawing Valid Trendlines**:
    1.  Identify at least 2 touch points
    2.  Connect with straight line
    3.  Extend into future
    4.  Wait for 3rd touch for validation
    5.  Trade bounces or breaks with confirmation
    
    ---
    
    ## Real Trading Example
    
    **USD/JPY Trendline Trade** (April 2024):
    *   Trendline: 3 touches from 147.00 → 148.50 → 149.00
    *   4th touch entry: 149.50
    *   Stop: Below trendline at 149.10 (40 pips)
    *   Target: Previous high at 151.00 (150 pips)
    *   Result: 3.75 R:R, target hit in 5 days
    
    ---
    
    ## 📊 Chart Example
    
    <svg class="ac-svg-diagram" viewBox="0 0 480 195" xmlns="http://www.w3.org/2000/svg"><rect width="480" height="195" fill="#0d1117" rx="8"/><text x="240" y="18" text-anchor="middle" fill="#a78bfa" font-size="11" font-weight="bold">Dynamic S&amp;R — Moving Averages as Support</text><polyline points="20,130 60,115 90,125 130,100 160,115 200,90 240,105 280,80 320,95 360,70 400,85 440,60" fill="none" stroke="#60a5fa" stroke-width="2"/><polyline points="20,135 60,120 90,128 130,105 160,118 200,95 240,108 280,85 320,98 360,75 400,88 440,65" fill="none" stroke="#34d399" stroke-width="1.5"/><polyline points="20,150 60,143 90,140 130,128 160,132 200,120 240,122 280,110 320,114 360,102 400,108 440,94" fill="none" stroke="#f59e0b" stroke-width="1.5"/><rect x="25" y="155" width="55" height="12" fill="rgba(96,165,250,0.15)" rx="2"/><text x="52" y="165" text-anchor="middle" fill="#60a5fa" font-size="9">Price</text><rect x="90" y="155" width="65" height="12" fill="rgba(52,211,153,0.15)" rx="2"/><text x="122" y="165" text-anchor="middle" fill="#34d399" font-size="9">MA20 (Fast)</text><rect x="165" y="155" width="65" height="12" fill="rgba(245,158,11,0.15)" rx="2"/><text x="197" y="165" text-anchor="middle" fill="#f59e0b" font-size="9">MA50 (Slow)</text><text x="240" y="185" text-anchor="middle" fill="#6b7280" font-size="9">Price bouncing off MA = dynamic support. MA20 above MA50 = uptrend.</text></svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **Forcing Trendlines**: Drawing lines to fit the chart rather than valid touch points. Invalid trendlines produce false signals. Only trade validated trendlines with 3+ clean touches.
    
    ---
    
    ## 💡 Pro Tip
    
    **Combine Static and Dynamic**: When horizontal support aligns with a moving average (confluence), the level is significantly stronger. Look for these high-probability zones.
    
    ---
    
    ## Key Takeaway
    
    Dynamic levels adapt to price action. Moving averages and trendlines act as moving support/resistance. Confluence of multiple levels increases reliability.
    
    ---
    
    ## Practice Question
    
    What validates a trendline?""",
                            "quiz": [
                                {"question": "Dynamic support example?", "option_a": "Horizontal level", "option_b": "20 EMA", "option_c": "Round number", "option_d": "Previous high", "correct_answer": "B", "explanation": "Moving averages act as dynamic, evolving support.", "topic_slug": "support_resistance"},
                                {"question": "Trendline validation requires?", "option_a": "1 touch", "option_b": "2 touches", "option_c": "3+ touches", "option_d": "No touches", "correct_answer": "C", "explanation": "3+ touches validate a trendline as significant.", "topic_slug": "support_resistance"},
                                {"question": "200 SMA typically acts as?", "option_a": "Day trading support", "option_b": "Long-term trend filter", "option_c": "Scalping tool", "option_d": "Entry trigger", "correct_answer": "B", "explanation": "200 SMA defines long-term trend direction.", "topic_slug": "support_resistance"}
                            ]
                        },
                        {
                            "title": "Chart Patterns",
                            "content": """## Quick Definition
    
    **Chart Patterns** are recognizable price formations that predict future movements. Patterns reflect market psychology and repeat across all markets and timeframes.
    
    ---
    
    ## Concept Explanation
    
    ### Reversal Patterns
    *   **Head and Shoulders**: Classic reversal, target = head to neckline distance
    *   **Double Top/Bottom**: Test of support/resistance twice
    *   **Wedge**: Converging trendlines, typically reverses
    
    ### Continuation Patterns
    *   **Flags and Pennants**: Brief consolidation in strong trends
    *   **Triangles**: Symmetrical, ascending, descending
    *   **Rectangles**: Range-bound consolidation
    
    ---
    
    ## Step-by-Step Breakdown
    
    **Trading a Bull Flag**:
    1.  Identify strong bullish move (the "pole")
    2.  Wait for consolidation (flag) with lower volume
    3.  Enter on break above flag resistance
    4.  Target: Pole height added to breakout point
    5.  Stop: Below flag support
    
    ---
    
    ## Real Trading Example
    
    **EUR/USD Bull Flag** (May 2024):
    *   Pole: 1.0700 → 1.0800 (100 pips)
    *   Flag: Consolidation 1.0780-1.0800
    *   Breakout: Close above 1.0800
    *   Entry: 1.0805
    *   Target: 1.0905 (100 pips from breakout)
    *   Stop: 1.0775 (30 pips)
    *   Result: 3.3 R:R, target reached in 3 days
    
    ---
    
    ## 📊 Chart Example
    
    <svg class="ac-svg-diagram" viewBox="0 0 480 195" xmlns="http://www.w3.org/2000/svg"><rect width="480" height="195" fill="#0d1117" rx="8"/><text x="240" y="16" text-anchor="middle" fill="#a78bfa" font-size="11" font-weight="bold">Key Chart Patterns</text><text x="80" y="35" text-anchor="middle" fill="#f87171" font-size="9" font-weight="bold">Head &amp; Shoulders (Bearish)</text><polyline points="20,120 40,100 60,110 80,78 100,110 120,100 140,120" fill="none" stroke="#f87171" stroke-width="2"/><line x1="20" y1="120" x2="140" y2="120" stroke="#f87171" stroke-width="1" stroke-dasharray="3"/><text x="80" y="138" text-anchor="middle" fill="#9ca3af" font-size="8">Neckline break → sell</text><text x="240" y="35" text-anchor="middle" fill="#34d399" font-size="9" font-weight="bold">Double Bottom (Bullish)</text><polyline points="175,80 195,120 215,102 235,120 255,80" fill="none" stroke="#34d399" stroke-width="2"/><line x1="175" y1="102" x2="255" y2="102" stroke="#34d399" stroke-width="1" stroke-dasharray="3"/><text x="215" y="138" text-anchor="middle" fill="#9ca3af" font-size="8">Break above → buy</text><text x="390" y="35" text-anchor="middle" fill="#60a5fa" font-size="9" font-weight="bold">Bull Flag (Continuation)</text><line x1="320" y1="125" x2="320" y2="78" stroke="#60a5fa" stroke-width="2"/><polyline points="320,78 340,100 360,105 380,100 400,106 420,100" fill="none" stroke="#60a5fa" stroke-width="2"/><text x="380" y="138" text-anchor="middle" fill="#9ca3af" font-size="8">Break up → continuation</text><text x="240" y="162" text-anchor="middle" fill="#9ca3af" font-size="9">Patterns repeat because human psychology repeats across all markets</text><text x="240" y="180" text-anchor="middle" fill="#fbbf24" font-size="9">Always wait for CONFIRMATION (breakout candle) before entering</text></svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **Anticipating Patterns**: Entering before pattern completion. Wait for confirmation (break of neckline, close outside pattern). Premature entries catch false breakouts.
    
    ---
    
    ## 💡 Pro Tip
    
    **Volume Confirmation**: Valid patterns have volume characteristics. Reversal patterns often have climactic volume at formation. Continuation patterns have declining volume during consolidation. Use volume to confirm pattern validity.
    
    ---
    
    ## Key Takeaway
    
    Patterns are roadmaps of market psychology. Wait for completion and confirmation. Measure targets using pattern height. Not every pattern works—manage risk accordingly.
    
    ---
    
    ## Practice Question
    
    Target measurement for head and shoulders pattern?""",
                            "quiz": [
                                {"question": "Head and shoulders pattern type?", "option_a": "Continuation", "option_b": "Reversal", "option_c": "Consolidation", "option_d": "Trend", "correct_answer": "B", "explanation": "Head and shoulders signals trend reversal.", "topic_slug": "chart_patterns"},
                                {"question": "Bull flag target calculation?", "option_a": "Flag width", "option_b": "Pole height added to breakout", "option_c": "Half pole height", "option_d": "Double pole height", "correct_answer": "B", "explanation": "Measure pole, add to breakout point for target.", "topic_slug": "chart_patterns"},
                                {"question": "Key mistake with patterns?", "option_a": "Waiting for confirmation", "option_b": "Using volume", "option_c": "Entering before completion", "option_d": "Setting stops", "correct_answer": "C", "explanation": "Never enter before pattern completes and confirms.", "topic_slug": "chart_patterns"}
                            ]
                        }
                    ]
                },
                {
                    "title": "Technical Indicators",
                    "description": "Using RSI, MACD, and moving averages for confirmation.",
                    "lessons": [
                        {
                            "title": "Moving Average Strategies",
                            "content": """## Quick Definition
    
    **Moving Averages (MA)** smooth price data to identify trend direction. Crossovers, dynamic support, and slope analysis generate trading signals.
    
    ---
    
    ## Concept Explanation
    
    ### Types of Moving Averages
    *   **SMA**: Simple average, equal weight to all periods
    *   **EMA**: Exponential average, more weight to recent prices
    *   **WMA**: Weighted average, linear weighting
    
    ### Common Strategies
    *   **Golden Cross**: 50 SMA crosses above 200 SMA (bullish)
    *   **Death Cross**: 50 SMA crosses below 200 SMA (bearish)
    *   **EMA Slope**: Rising = uptrend, falling = downtrend
    
    ---
    
    ## Step-by-Step Breakdown
    
    **EMA Crossover System**:
    1.  Plot 9 EMA and 21 EMA
    2.  9 crosses above 21 = Buy signal
    3.  Stop: Below recent swing low
    4.  Exit: 9 crosses back below 21
    5.  Filter: Only take trades in direction of 50 EMA trend
    
    ---
    
    ## Real Trading Example
    
    **GBP/USD EMA Crossover** (June 2024):
    *   Setup: 9 EMA crosses above 21 EMA at 1.2650
    *   50 EMA slope: Positive (uptrend confirmed)
    *   Entry: 1.2655
    *   Stop: 1.2620 (35 pips)
    *   Target: 1.2750 (95 pips)
    *   Result: 2.7 R:R, exit on bearish cross at 1.2740
    
    ---
    
    ## 📊 Chart Example
    
    <svg class="ac-svg-diagram" viewBox="0 0 480 195" xmlns="http://www.w3.org/2000/svg"><rect width="480" height="195" fill="#0d1117" rx="8"/><text x="240" y="18" text-anchor="middle" fill="#a78bfa" font-size="11" font-weight="bold">Moving Average Crossover (Golden Cross / Death Cross)</text><polyline points="20,150 60,140 100,145 140,120 180,130 220,100 260,90 300,80 340,85 380,70 420,65 460,55" fill="none" stroke="#9ca3af" stroke-width="1.5" opacity="0.4"/><polyline points="20,155 60,148 100,148 140,126 180,133 220,105 260,94 300,83 340,87 380,73 420,67 460,57" fill="none" stroke="#34d399" stroke-width="2"/><polyline points="20,165 60,160 100,158 140,150 180,148 220,138 260,128 300,115 340,108 380,100 420,92 460,85" fill="none" stroke="#f59e0b" stroke-width="2"/><circle cx="220" cy="138" r="10" fill="none" stroke="#fbbf24" stroke-width="2"/><text x="225" y="128" fill="#fbbf24" font-size="8">Golden</text><text x="225" y="138" fill="#fbbf24" font-size="8">Cross</text><text x="225" y="150" fill="#34d399" font-size="8">BUY ↑</text><rect x="25" y="168" width="55" height="12" fill="rgba(52,211,153,0.2)" rx="2"/><text x="52" y="178" text-anchor="middle" fill="#34d399" font-size="9">MA20 Fast</text><rect x="90" y="168" width="55" height="12" fill="rgba(245,158,11,0.2)" rx="2"/><text x="117" y="178" text-anchor="middle" fill="#f59e0b" font-size="9">MA50 Slow</text><text x="320" y="178" fill="#6b7280" font-size="9">MA20 crosses MA50 upward = trend shift</text></svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **MA Whipsaws**: Taking every crossover in choppy markets. Moving averages lag—false signals abound in ranges. Add filters (ADX > 25, price above/below 200 MA) to avoid chop.
    
    ---
    
    ## 💡 Pro Tip
    
    **The 8/21 EMA Combo**: These Fibonacci-based periods are widely watched by institutions. The 8/21 crossover often creates self-fulfilling momentum as algorithmic systems respond to these specific levels.
    
    ---
    
    ## Key Takeaway
    
    Moving averages work best in trending markets. Combine multiple MAs for confirmation. Always consider slope, not just position. Range-bound markets produce false signals.
    
    ---
    
    ## Practice Question
    
    What is a Golden Cross?""",
                            "quiz": [
                                {"question": "Golden Cross definition?", "option_a": "9 crosses 21 EMA", "option_b": "50 crosses 200 SMA upward", "option_c": "200 crosses 50 SMA", "option_d": "Price crosses MA", "correct_answer": "B", "explanation": "50 SMA crossing above 200 SMA = Golden Cross (bullish).", "topic_slug": "indicators"},
                                {"question": "Best market condition for MAs?", "option_a": "Range-bound", "option_b": "Trending", "option_c": "High volatility", "option_d": "Low volume", "correct_answer": "B", "explanation": "Moving averages excel in trending markets, fail in ranges.", "topic_slug": "indicators"},
                                {"question": "EMA vs SMA difference?", "option_a": "EMA is slower", "option_b": "EMA weights recent prices more", "option_c": "SMA is more accurate", "option_d": "No difference", "correct_answer": "B", "explanation": "EMA gives more weight to recent price data.", "topic_slug": "indicators"}
                            ]
                        },
                        {
                            "title": "Momentum Indicators (RSI and MACD)",
                            "content": """## Quick Definition
    
    **Momentum Indicators** measure the speed and strength of price movements. RSI identifies overbought/oversold conditions. MACD shows trend direction and momentum changes.
    
    ---
    
    ## Concept Explanation
    
    ### RSI (Relative Strength Index)
    *   Scale: 0-100
    *   >70: Overbought (potential reversal down)
    *   <30: Oversold (potential reversal up)
    *   Divergence: RSI disagrees with price = warning signal
    
    ### MACD
    *   Components: MACD line, Signal line, Histogram
    *   Crossover: MACD crosses signal = entry signal
    *   Histogram: Shows momentum strength
    
    ---
    
    ## Step-by-Step Breakdown
    
    **RSI Divergence Strategy**:
    1.  Price makes higher high
    2.  RSI makes lower high (bearish divergence)
    3.  Wait for price to break support
    4.  Enter short on confirmation
    5.  Stop: Above recent high
    
    ---
    
    ## Real Trading Example
    
    **AUD/USD Bearish Divergence** (April 2024):
    *   Price: High at 0.6650, then 0.6680 (higher high)
    *   RSI: 72 at first high, 68 at second (lower high)
    *   Break: Close below 0.6620 support
    *   Entry: 0.6615
    *   Stop: 0.6690 (75 pips)
    *   Target: 0.6500 (115 pips)
    *   Result: 1.5 R:R, target hit in 4 days
    
    ---
    
    ## 📊 Chart Example
    
    <svg class="ac-svg-diagram" viewBox="0 0 480 210" xmlns="http://www.w3.org/2000/svg"><rect width="480" height="210" fill="#0d1117" rx="8"/><text x="240" y="16" text-anchor="middle" fill="#a78bfa" font-size="11" font-weight="bold">RSI &amp; MACD Momentum Indicators</text><text x="30" y="35" fill="#60a5fa" font-size="10" font-weight="bold">RSI (14)</text><rect x="20" y="40" width="200" height="70" fill="rgba(0,0,0,0.3)" rx="4"/><line x1="20" y1="58" x2="220" y2="58" stroke="#f87171" stroke-width="1" stroke-dasharray="3" opacity="0.7"/><text x="224" y="62" fill="#f87171" font-size="8">70 Overbought</text><line x1="20" y1="90" x2="220" y2="90" stroke="#34d399" stroke-width="1" stroke-dasharray="3" opacity="0.7"/><text x="224" y="94" fill="#34d399" font-size="8">30 Oversold</text><polyline points="30,82 55,72 80,58 105,52 130,65 155,76 180,90 205,82" fill="none" stroke="#60a5fa" stroke-width="2"/><text x="110" y="120" text-anchor="middle" fill="#9ca3af" font-size="8">Above 70 = sell signal | Below 30 = buy signal</text><text x="270" y="35" fill="#f59e0b" font-size="10" font-weight="bold">MACD (12,26,9)</text><rect x="260" y="40" width="200" height="70" fill="rgba(0,0,0,0.3)" rx="4"/><line x1="260" y1="75" x2="460" y2="75" stroke="#374151" stroke-width="1"/><rect x="270" y="68" width="7" height="7" fill="#34d399" opacity="0.8"/><rect x="282" y="65" width="7" height="10" fill="#34d399" opacity="0.8"/><rect x="294" y="62" width="7" height="13" fill="#34d399" opacity="0.8"/><rect x="306" y="67" width="7" height="8" fill="#34d399" opacity="0.8"/><rect x="330" y="75" width="7" height="6" fill="#f87171" opacity="0.8"/><rect x="342" y="75" width="7" height="10" fill="#f87171" opacity="0.8"/><rect x="354" y="75" width="7" height="8" fill="#f87171" opacity="0.8"/><polyline points="270,70 295,63 318,75 342,79 368,74 392,70" fill="none" stroke="#fbbf24" stroke-width="1.5"/><text x="360" y="120" text-anchor="middle" fill="#9ca3af" font-size="8">Green=bullish | Red=bearish momentum</text><text x="240" y="145" text-anchor="middle" fill="#fbbf24" font-size="9">⭐ RSI oversold + MACD bullish cross = strong buy confluence</text><text x="240" y="163" text-anchor="middle" fill="#9ca3af" font-size="9">Never use indicators alone — confirm with price action and structure</text><text x="240" y="180" text-anchor="middle" fill="#6b7280" font-size="8">RSI period: 14 | MACD: 12, 26, 9 (default settings on all platforms)</text></svg>
    
    ---
    
    ## 🚫 Common Beginner Mistake
    
    **RSI Overreliance**: Selling just because RSI > 70 in strong uptrends. Overbought can stay overbought for weeks. Use RSI for divergence, not standalone signals. Confirm with price action.
    
    ---
    
    ## 💡 Pro Tip
    
    **MACD Histogram Strategy**: Watch for histogram divergence before the actual MACD crossover. Early momentum shifts appear in histogram first, giving you advance warning of trend changes.
    
    ---
    
    ## Key Takeaway
    
    Momentum indicators confirm price action. RSI shows overbought/oversold and divergence. MACD identifies trend changes. Never use indicators alone—always confirm with price structure.
    
    ---
    
    ## Practice Question
    
    What does RSI bearish divergence indicate?""",
                            "quiz": [
                                {"question": "RSI > 70 indicates?", "option_a": "Strong buy", "option_b": "Overbought, potential reversal", "option_c": "Undervalued", "option_d": "Trend continuation", "correct_answer": "B", "explanation": "RSI > 70 suggests overbought conditions.", "topic_slug": "indicators"},
                                {"question": "Bearish divergence occurs when?", "option_a": "Price and RSI both rise", "option_b": "Price rises, RSI falls", "option_c": "Both fall", "option_d": "RSI rises, price falls", "correct_answer": "B", "explanation": "Price makes higher high while RSI makes lower high = bearish divergence.", "topic_slug": "indicators"},
                                {"question": "MACD histogram shows?", "option_a": "Trend direction only", "option_b": "Momentum strength", "option_c": "Volume", "option_d": "Support levels", "correct_answer": "B", "explanation": "Histogram represents momentum strength and acceleration.", "topic_slug": "indicators"}
                            ]
                        }
                    ]
                }
            ]
        },
    {
        "level_name": "Advanced",
        "description": "Master institutional trading concepts, advanced risk management, and system development. Learn Smart Money Concepts, portfolio management, and build your complete trading business.",
        "modules": [
            {
                "title": "Fibonacci and Advanced Tools",
                "description": "Fibonacci retracements, extensions, and confluence trading.",
                "lessons": [
                    {
                        "title": "Fibonacci Retracements and Extensions",
                        "content": """## Quick Definition
    
    bonacci Retracements** measure pullback depth within trends using ratios derived from the Fibonacci sequence (23.6%, 38.2%, 50%, 61.8%). **Extensions** project profit targets beyond the 100% level (127.2%, 161.8%, 261.8%).
    
    
    
    oncept Explanation
    
    Key Fibonacci Levels
    
    vel | Significance |
    ----|--------------|
    38.2%** | Shallow retracement in strong trends |
    50%** | Midpoint (not true Fibonacci but widely used) |
    61.8%** | Golden Ratio—deepest healthy retracement |
    78.6%** | Deep retracement, often last chance |
    
    Extension Targets
    **127.2%** (1.272): First target, conservative
    **161.8%** (1.618): Golden extension, primary target
    **261.8%** (2.618): Extended target in strong trends
    
    
    
    tep-by-Step Breakdown
    
    awing Fibonacci Retracement**:
    Identify clear impulse move (swing low to high for uptrends)
    Draw tool from swing start to swing end
    Mark 38.2%, 50%, 61.8% levels
    Wait for price to reach these zones
    Look for confirmation signals at Fib levels
    Enter with stop beyond 78.6% or swing extreme
    
    
    
    eal Trading Example
    
    R/USD Fibonacci Trade** (June 2024):
    Impulse: 1.0700 → 1.0900 (200 pips)
    Retracement: Pullback to 1.0820 (61.8% level)
    Confirmation: Bullish hammer at 61.8%
    Entry: 1.0825
    Stop: 1.0785 (below 78.6%, 40 pips)
    Target 1: 1.0924 (127.2% extension)
    Target 2: 1.0956 (161.8% extension)
    Result: Both targets hit over 5 days
    
     class="ac-svg-diagram" viewBox="0 0 400 200">
    ine x1="50" y1="150" x2="350" y2="50" stroke="#60a5fa" stroke-width="2"/>
    ext x="30" y="155" fill="#60a5fa" font-size="12">0%</text>
    ext x="360" y="55" fill="#60a5fa" font-size="12">100%</text>
    ine x1="150" y1="125" x2="170" y2="125" stroke="#f59e0b" stroke-width="3"/>
    ext x="180" y="130" fill="#f59e0b" font-size="10">38.2%</text>
    ine x1="200" y1="100" x2="220" y2="100" stroke="#f59e0b" stroke-width="3"/>
    ext x="230" y="105" fill="#f59e0b" font-size="10">50%</text>
    ine x1="250" y1="75" x2="270" y2="75" stroke="#22c55e" stroke-width="3"/>
    ext x="280" y="80" fill="#22c55e" font-size="10">61.8%</text>
    ircle cx="260" cy="75" r="5" fill="#22c55e"/>
    ext x="260" y="60" text-anchor="middle" fill="#22c55e" font-size="10">Entry Zone</text>
    g>
    
    
    
     Chart Example
    
    bonacci Levels](/static/charts/fibonacci_retracement_example.png)
    
    
    
     Common Beginner Mistake
    
    rcing Fibonacci Everywhere**: Drawing Fibonacci on every chart regardless of trend clarity. Fibonacci only works with clear impulse moves in established trends. Choppy, ranging markets produce random Fibonacci signals.
    
    
    
     Pro Tip
    
    e 61.8% Sweet Spot**: The 61.8% retracement (Golden Ratio) is the highest-probability entry zone in healthy trends. Price often respects this level before continuing. Combine with price action confirmation for best results.
    
    
    
    ey Takeaway
    
    nacci levels are self-fulfilling because institutions use them. The 38.2-61.8% zone offers the best risk/reward for entries. Extensions project logical profit targets. Always confirm with price action—Fibonacci alone is not enough.
    
    
    
    ractice Question
    
     strong uptrend, which Fibonacci retracement level typically offers the deepest "healthy" pullback entry?""",
                        "quiz": [
                            {"question": "Most significant Fibonacci retracement?", "option_a": "23.6%", "option_b": "38.2%", "option_c": "61.8%", "option_d": "78.6%", "correct_answer": "C", "explanation": "61.8% is the Golden Ratio and highest-probability retracement level.", "topic_slug": "fibonacci"},
                            {"question": "Fibonacci extension target for strong trends?", "option_a": "100%", "option_b": "127.2%", "option_c": "161.8%", "option_d": "261.8%", "correct_answer": "C", "explanation": "161.8% is the Golden extension, primary target in strong trends.", "topic_slug": "fibonacci"},
                            {"question": "Fibonacci works best in?", "option_a": "Choppy markets", "option_b": "Clear trending markets", "option_c": "Range-bound markets", "option_d": "All markets equally", "correct_answer": "B", "explanation": "Fibonacci requires clear impulse moves found in trending markets.", "topic_slug": "fibonacci"}
                        ]
                    },
                    {
                        "title": "Confluence Trading",
                        "content": """## Quick Definition
    
    nfluence** occurs when multiple technical factors align at the same price zone, creating higher-probability trading setups. More confluence = higher probability + better risk/reward.
    
    
    
    oncept Explanation
    
    Types of Confluence
    
    rizontal Confluence**:
    Previous support/resistance
    Round numbers (1.1000, 1.2000)
    Psychological levels
    
    namic Confluence**:
    Moving averages (20, 50, 200 EMA/SMA)
    Trendlines
    Channels
    
    bonacci Confluence**:
    Multiple Fibonacci levels align
    Fibonacci + horizontal level
    Fibonacci + dynamic level
    
    The Confluence Score
    
    nfluence Factors | Probability | Recommended Size |
    ----------------|-------------|-------------------|
    factor | 45-50% | 0.5% risk |
    factors | 55-60% | 1% risk |
     factors | 65-75% | 2% risk |
    
    
    
    tep-by-Step Breakdown
    
    ilding Confluence Zones**:
    Identify horizontal support/resistance
    Check if Fibonacci retracement aligns
    Check if moving average is nearby
    Look for trendline confluence
    Check for round numbers
    Mark the zone where 3+ factors align
    Wait for price action confirmation
    
    
    
    eal Trading Example
    
    P/USD Perfect Confluence** (May 2024):
    **Horizontal**: Previous resistance at 1.2500
    **Fibonacci**: 61.8% retracement at 1.2490
    **Dynamic**: 50 EMA at 1.2505
    **Psychological**: Round number 1.2500
    **Confirmation**: Bullish pin bar at 1.2500
    Entry: 1.2505
    Stop: 1.2455 (50 pips)
    Target: 1.2620 (115 pips)
    Result: 2.3 R:R, target hit in 4 days
    
    
    
     Chart Example
    
    nfluence Trading](/static/charts/confluence_trading_zones.png)
    
    
    
     Common Beginner Mistake
    
    e-Factor Trading**: Taking trades based solely on one indicator or level. Single-factor setups have lower probability and require wider stops. Always seek minimum 2-3 confluence factors for A-grade setups.
    
    
    
     Pro Tip
    
    e Magnet Zone**: When 3+ factors align within 10-15 pips, you have found a "magnet zone." Price is drawn to these areas. Even if price overshoots, it often returns to respect these high-confluence zones.
    
    
    
    ey Takeaway
    
    luence stacks probability in your favor. Look for zones where horizontal, dynamic, and Fibonacci levels align. 3+ confluence factors = A-grade setups. Single-factor setups should be avoided or sized smaller.
    
    
    
    ractice Question
    
     is the minimum number of confluence factors recommended for A-grade setups?""",
                        "quiz": [
                            {"question": "Types of confluence include?", "option_a": "Only horizontal", "option_b": "Horizontal, dynamic, Fibonacci", "option_c": "Only Fibonacci", "option_d": "Only indicators", "correct_answer": "B", "explanation": "Three main types: horizontal (S/R), dynamic (MAs), and Fibonacci levels.", "topic_slug": "fibonacci"},
                            {"question": "Recommended risk for 3+ confluence factors?", "option_a": "0.5%", "option_b": "1%", "option_c": "2%", "option_d": "5%", "correct_answer": "C", "explanation": "High confluence (3+ factors) justifies standard 2% risk per trade.", "topic_slug": "fibonacci"},
                            {"question": "Confluence zone definition?", "option_a": "Single indicator", "option_b": "Multiple factors aligning", "option_c": "Random price area", "option_d": "News event zone", "correct_answer": "B", "explanation": "Confluence is when multiple technical factors align at the same price.", "topic_slug": "fibonacci"}
                        ]
                    }
                ]
            },
            {
                "title": "Market Structure and Smart Money",
                "description": "Institutional trading concepts including order blocks and liquidity.",
                "lessons": [
                    {
                        "title": "Order Blocks and Institutional Levels",
                        "content": """## Quick Definition
    
    der Blocks (OB)** are the last opposing candle before a strong impulsive move, representing where institutions accumulated or distributed positions. They act as magnets for future price action.
    
    
    
    oncept Explanation
    
    Types of Order Blocks
    
    llish Order Block**:
    Last bearish candle before strong bullish move
    Acts as support when price returns
    Often formed at market structure shifts
    
    arish Order Block**:
    Last bullish candle before strong bearish move
    Acts as resistance when price returns
    Validated by Break of Structure (BOS)
    
    Key Characteristics
    **Displacement**: Strong impulsive move away from OB
    **Mitigation**: Price returns to OB to fill remaining orders
    **Break of Structure**: Confirms directional intent
    
    
    
    tep-by-Step Breakdown
    
    ading Order Blocks**:
    Identify clear impulse move (displacement)
    Mark the last opposing candle (the OB)
    Wait for price to return to OB zone
    Confirm with lower timeframe structure break
    Enter with stop beyond OB extreme
    Target next liquidity pool or extension
    
    
    
    eal Trading Example
    
    R/USD Bullish Order Block** (April 2024):
    **Impulse**: Strong bullish move from 1.0700 → 1.0850
    **OB**: Last bearish candle before impulse (1.0720-1.0735)
    **Return**: Price retraces to OB zone 5 days later
    **Confirmation**: 15m bullish engulfing at OB
    Entry: 1.0730
    Stop: 1.0705 (25 pips)
    Target: 1.0820 (90 pips)
    Result: 3.6 R:R, target hit in 2 days
    
     class="ac-svg-diagram" viewBox="0 0 400 200">
    ect x="100" y="120" width="40" height="30" fill="#ef4444" opacity="0.6" rx="3"/>
    ext x="120" y="140" text-anchor="middle" fill="white" font-size="10">OB</text>
    ine x1="140" y1="135" x2="280" y2="60" stroke="#22c55e" stroke-width="3"/>
    ext x="210" y="90" text-anchor="middle" fill="#22c55e" font-size="12">Displacement</text>
    ath d="M 300 60 Q 320 100 280 120" stroke="#60a5fa" stroke-width="2" stroke-dasharray="5,5"/>
    ext x="320" y="90" fill="#60a5fa" font-size="10">Return to OB</text>
    ircle cx="120" cy="120" r="8" fill="none" stroke="#f59e0b" stroke-width="2"/>
    ext x="120" y="175" text-anchor="middle" fill="#f59e0b" font-size="10">Entry Zone</text>
    g>
    
    
    
     Chart Example
    
    der Blocks](/static/charts/order_block_example.png)
    
    
    
     Common Beginner Mistake
    
    rking Every Candle**: Drawing boxes around every pullback candle. Not every consolidation is an order block. Valid OBs require clear displacement and Break of Structure. Focus on significant swing points only.
    
    
    
     Pro Tip
    
     Mitigation Concept**: Institutions leave unfilled orders at OBs. When price returns, these orders get filled, creating the reaction. The best entries are at the 50% of the OB body—where most institutional orders remain unexecuted.
    
    
    
    ey Takeaway
    
    r blocks reveal institutional footprints. Valid OBs show displacement and structure breaks. Price returns to OBs to mitigate (fill) remaining orders. Trade the return with confirmation for high-probability entries.
    
    
    
    ractice Question
    
     validates an order block?""",
                        "quiz": [
                            {"question": "Order Block definition?", "option_a": "Any consolidation", "option_b": "Last opposing candle before displacement", "option_c": "Breakout candle", "option_d": "Random price level", "correct_answer": "B", "explanation": "OB is the last opposing candle before strong impulsive move.", "topic_slug": "market_structure"},
                            {"question": "OB validation requires?", "option_a": "Slow movement", "option_b": "Displacement and structure break", "option_c": "Range-bound price", "option_d": "High volume only", "correct_answer": "B", "explanation": "Valid OBs require strong displacement away and Break of Structure.", "topic_slug": "market_structure"},
                            {"question": "Best entry in OB zone?", "option_a": "Top of OB", "option_b": "50% of OB body", "option_c": "Bottom of OB", "option_d": "Anywhere in zone", "correct_answer": "B", "explanation": "50% of OB body typically has most unfilled institutional orders.", "topic_slug": "market_structure"}
                        ]
                    },
                    {
                        "title": "Liquidity and Market Structure",
                        "content": """## Quick Definition
    
    quidity** refers to pools of orders (stop losses, breakout traders) that institutions target before major moves. **Market Structure** tracks highs and lows to determine trend direction and institutional intent.
    
    
    
    oncept Explanation
    
    Types of Liquidity
    
    y-Side Liquidity (BSL)**:
    Cluster of buy stops above swing highs
    Targets of breakout traders
    Institutions sell into these pools
    
    ll-Side Liquidity (SSL)**:
    Cluster of sell stops below swing lows
    Targets of breakdown traders
    Institutions buy from these pools
    
    Market Structure Shifts
    
    eak of Structure (BOS)**:
    Price breaks previous high/low with momentum
    Confirms trend continuation
    Indicates institutional commitment
    
    ange of Character (CHoCH)**:
    First sign of trend reversal
    Breaks structure in opposite direction
    Indicates institutional shift in bias
    
    
    
    tep-by-Step Breakdown
    
    e AMD (Accumulation-Manipulation-Distribution) Cycle**:
    **Accumulation**: Institutions build positions in range
    **Manipulation**: Price sweeps liquidity (stops) to trap retail
    **Distribution**: True move in institutional direction
    **Mark**: OBs and Fair Value Gaps form during distribution
    
    
    
    eal Trading Example
    
    P/JPY Liquidity Sweep** (March 2024):
    **Setup**: Price near 188.00 with swing highs at 188.50
    **Accumulation**: Consolidation 187.80-188.20
    **Manipulation**: Spike to 188.60 (sweeps BSL above 188.50)
    **Distribution**: Sharp rejection back below 188.00
    **Entry**: Break below 188.00 after sweep
    Stop: 188.70 (above manipulation high)
    Target: 186.50 (next SSL pool)
    Result: 150-pip move captured
    
    
    
     Chart Example
    
    quidity Sweep](/static/charts/liquidity_sweep_example.png)
    
    
    
     Common Beginner Mistake
    
    ading the Sweep**: Entering when price breaks a level without waiting for manipulation completion. Retail traders get swept out at highs/lows while institutions enter on the reversal. Wait for the sweep + rejection.
    
    
    
     Pro Tip
    
    e Liquidity Magnet**: Price is drawn to liquidity pools like a magnet. Before any major move, price typically sweeps the nearest liquidity (taking out stops), then reverses in the true direction. Never place stops at obvious levels—they will be swept.
    
    
    
    ey Takeaway
    
    ets move to harvest liquidity. Institutions sweep retail stops before true moves. Understanding BOS and CHoCH reveals institutional intent. Wait for liquidity sweeps before entering—don't be the liquidity being harvested.
    
    
    
    ractice Question
    
     typically happens before a major trend reversal?""",
                        "quiz": [
                            {"question": "Buy-Side Liquidity (BSL) is found?", "option_a": "Below swing lows", "option_b": "Above swing highs", "option_c": "At moving averages", "option_d": "In the middle of ranges", "correct_answer": "B", "explanation": "BSL is above swing highs—where breakout traders place stops.", "topic_slug": "market_structure"},
                            {"question": "CHoCH indicates?", "option_a": "Trend continuation", "option_b": "Potential trend reversal", "option_c": "Consolidation", "option_d": "No significance", "correct_answer": "B", "explanation": "Change of Character signals shift in market structure.", "topic_slug": "market_structure"},
                            {"question": "Liquidity sweep purpose?", "option_a": "Help retail traders", "option_b": "Harvest stops before true move", "option_c": "Random price action", "option_d": "Confirm trend", "correct_answer": "B", "explanation": "Institutions sweep liquidity to fill orders before reversing.", "topic_slug": "market_structure"}
                        ]
                    }
                ]
            },
            {
                "title": "Advanced Risk Management",
                "description": "Portfolio heat, correlation, and expectancy.",
                "lessons": [
                    {
                        "title": "Expectancy and Profit Factor",
                        "content": """## Quick Definition
    
    pectancy** measures the average profit/loss per trade over time—your true edge. **Profit Factor** compares total gains to total losses. These metrics determine if your system is profitable and sustainable.
    
    
    
    oncept Explanation
    
    Expectancy Formula
    pectancy = (Win Rate × Avg Win) – (Loss Rate × Avg Loss)**
    
    ple:
    Win Rate: 45%
    Avg Win: 2.5R
    Loss Rate: 55%
    Avg Loss: 1R
    Expectancy: (0.45 × 2.5) – (0.55 × 1) = 1.125 – 0.55 = **+0.575R per trade**
    
    Profit Factor
    ofit Factor = Gross Profit / Gross Loss**
    
    1.0+ = Breakeven
    1.3+ = Acceptable
    1.5+ = Good
    2.0+ = Excellent
    
    
    
    tep-by-Step Breakdown
    
    lculating Your Edge**:
    Track minimum 100 trades for statistical significance
    Calculate win rate (wins / total trades)
    Calculate average win in R-multiples
    Calculate average loss in R-multiples
    Apply expectancy formula
    Positive expectancy = tradable edge
    Negative expectancy = broken system or execution issues
    
    
    
    eal Trading Example
    
    ader A vs Trader B (100 trades each)**:
    
    ader A**:
    Win Rate: 65%
    Avg Win: 1.2R
    Avg Loss: 1R
    Expectancy: (0.65 × 1.2) – (0.35 × 1) = 0.78 – 0.35 = **+0.43R**
    
    ader B**:
    Win Rate: 40%
    Avg Win: 3R
    Avg Loss: 1R
    Expectancy: (0.40 × 3) – (0.60 × 1) = 1.2 – 0.6 = **+0.60R**
    
    sult**: Trader B makes more despite lower win rate due to better R:R!
    
     class="ac-svg-diagram" viewBox="0 0 400 150">
    ect x="20" y="30" width="170" height="90" fill="rgba(96,165,250,0.2)" stroke="#60a5fa" rx="5"/>
    ext x="105" y="55" text-anchor="middle" fill="#60a5fa" font-size="14">Trader A</text>
    ext x="105" y="75" text-anchor="middle" fill="#9ca3af" font-size="12">65% Win Rate</text>
    ext x="105" y="95" text-anchor="middle" fill="#9ca3af" font-size="12">1.2:1 R:R</text>
    ext x="105" y="115" text-anchor="middle" fill="#22c55e" font-size="12">+0.43R</text>
    
    ect x="210" y="30" width="170" height="90" fill="rgba(245,158,11,0.2)" stroke="#f59e0b" rx="5"/>
    ext x="295" y="55" text-anchor="middle" fill="#f59e0b" font-size="14">Trader B</text>
    ext x="295" y="75" text-anchor="middle" fill="#9ca3af" font-size="12">40% Win Rate</text>
    ext x="295" y="95" text-anchor="middle" fill="#9ca3af" font-size="12">3:1 R:R</text>
    ext x="295" y="115" text-anchor="middle" fill="#22c55e" font-size="12">+0.60R</text>
    g>
    
    
    
     Chart Example
    
    pectancy](/static/charts/expectancy_calculation_example.png)
    
    
    
     Common Beginner Mistake
    
    cusing on Win Rate Alone**: A 70% win rate seems impressive, but if average win is 0.8R and average loss is 1.5R, the system loses money. Expectancy combines win rate AND R-multiples. Optimize for positive expectancy, not win rate.
    
    
    
     Pro Tip
    
    e R-Multiple Focus**: Track all trades in R-multiples (units of risk), not dollars. This normalizes results regardless of account size. A 2R win is always twice your risk—easy to compare across different position sizes.
    
    
    
    ey Takeaway
    
    ctancy is your true edge. Positive expectancy = profitable system over time. Win rate alone is meaningless—R-multiples matter more. Track minimum 100 trades before judging a system. Profit factor > 1.5 indicates good system health.
    
    
    
    ractice Question
    
    er has 50% win rate, 2:1 average R:R. Expectancy per trade?""",
                        "quiz": [
                            {"question": "Expectancy formula components?", "option_a": "Only win rate", "option_b": "Win rate and R-multiples", "option_c": "Only profit factor", "option_d": "Only drawdown", "correct_answer": "B", "explanation": "Expectancy = (Win Rate × Avg Win) – (Loss Rate × Avg Loss).", "topic_slug": "advanced_risk"},
                            {"question": "Good profit factor threshold?", "option_a": "0.5", "option_b": "1.0", "option_c": "1.5+", "option_d": "3.0", "correct_answer": "C", "explanation": "Profit factor above 1.5 indicates healthy system performance.", "topic_slug": "advanced_risk"},
                            {"question": "50% win rate, 2:1 R:R expectancy?", "option_a": "0R", "option_b": "+0.5R", "option_c": "+1.0R", "option_d": "+1.5R", "correct_answer": "B", "explanation": "(0.5 × 2) – (0.5 × 1) = 1 – 0.5 = +0.5R per trade.", "topic_slug": "advanced_risk"}
                        ]
                    },
                    {
                        "title": "Portfolio Heat and Correlation",
                        "content": """## Quick Definition
    
    rtfolio Heat** is total exposed risk across all open positions. **Correlation** measures how similarly different pairs move. Managing both prevents catastrophic drawdowns when markets move together.
    
    
    
    oncept Explanation
    
    Portfolio Heat Calculation
    tal Heat = Sum of all position risks**
    
    ple:
    Position 1: 2% risk
    Position 2: 2% risk
    Position 3: 1% risk
    **Total Heat**: 5%
    
    essional limits:
    Retail traders: Maximum 6-8% heat
    Professional traders: Maximum 3-5% heat
    
    Correlation Risk
    
    ghly Correlated Pairs** (>0.80):
    EUR/USD and GBP/USD
    AUD/USD and NZD/USD
    Gold (XAU/USD) and EUR/USD (often)
    
    fect**: Trading correlated pairs = doubling risk on same move
    
    Diversification Score
    
    tup | Correlation | Adjusted Risk |
    ----|-------------|---------------|
    R/USD only | N/A | 2% |
    R/USD + GBP/USD | 0.90 | Effectively 3.8% |
    R/USD + USD/JPY | 0.20 | Effectively 2.2% |
    
    
    
    tep-by-Step Breakdown
    
    naging Portfolio Risk**:
    Calculate individual position risk (1-2%)
    Check correlation between all open positions
    Adjust for correlation:
    *   >0.80 correlation: Reduce each position by 50%
    *   0.50-0.80: Reduce by 25%
    Sum total portfolio heat
    Ensure total heat < 6% (retail) or < 3% (pro)
    Monitor heat daily; reduce if approaching limits
    
    
    
    eal Trading Example
    
    rtfolio Heat Mistake** (April 2024):
    **Trader**: Long EUR/USD (2% risk), Long GBP/USD (2% risk), Long AUD/USD (2% risk)
    **Correlation**: All positively correlated (~0.85)
    **Effective Heat**: 5.1% (not 6%)
    **USD News**: Strong NFP triggers USD rally
    **Result**: All positions hit stops simultaneously
    **Loss**: -5.1% in 1 hour (not acceptable -6%)
    **Lesson**: Correlated positions compound risk
    
    
    
     Chart Example
    
    rrelation](/static/charts/correlation_matrix_example.png)
    
    
    
     Common Beginner Mistake
    
    rrelated Portfolio**: Taking 3 long positions on EUR/USD, GBP/USD, and AUD/USD simultaneously. These move together 85%+ of the time. A USD strengthening event hits all three stops at once. Diversify across uncorrelated pairs or reduce size per correlated trade.
    
    
    
     Pro Tip
    
    e Correlation Rotation**: Maintain a watchlist of 3 uncorrelated groups:
    Group 1: EUR pairs (EUR/USD, EUR/JPY)
    Group 2: USD/Commodity pairs (USD/CAD, USD/NOK)
    Group 3: Safe havens (USD/JPY, USD/CHF)
    
    r have more than 1 position per group simultaneously.
    
    
    
    ey Takeaway
    
    folio heat management prevents catastrophic correlated losses. Maximum 6% total risk for retail traders. Highly correlated pairs should be treated as one position. True diversification requires uncorrelated markets.
    
    
    
    ractice Question
    
    trade EUR/USD and GBP/USD (0.90 correlation) with 2% each. Effective heat?""",
                        "quiz": [
                            {"question": "Portfolio heat definition?", "option_a": "Account balance", "option_b": "Total risk across all positions", "option_c": "Number of trades", "option_d": "Win rate", "correct_answer": "B", "explanation": "Heat = sum of all active position risks.", "topic_slug": "advanced_risk"},
                            {"question": "Maximum recommended heat for retail?", "option_a": "15%", "option_b": "6-8%", "option_c": "20%", "option_d": "2%", "correct_answer": "B", "explanation": "Retail traders should limit total portfolio heat to 6-8%.", "topic_slug": "advanced_risk"},
                            {"question": "EUR/USD and GBP/USD correlation?", "option_a": "None", "option_b": "Negative", "option_c": "High positive (~0.90)", "option_d": "Random", "correct_answer": "C", "explanation": "These pairs are highly correlated—trading both doubles exposure.", "topic_slug": "advanced_risk"}
                        ]
                    }
                ]
            },
            {
                "title": "Trading System Development",
                "description": "Building and backtesting your own trading system.",
                "lessons": [
                    {
                        "title": "Backtesting Your Strategy",
                        "content": """## Quick Definition
    
    cktesting** applies trading rules to historical data to measure performance. It validates your edge before risking real capital and reveals whether your system has positive expectancy.
    
    
    
    oncept Explanation
    
    Types of Backtesting
    
    nual Backtesting**:
    Scroll through historical charts bar by bar
    Apply your rules precisely as written
    Record every trade outcome
    Time-consuming but builds intuition
    
    tomated Backtesting**:
    Code strategy in trading platform
    Run on years of historical data
    Instant results and statistics
    Risk of overfitting (curve-fitting)
    
    Key Metrics to Track
    
    tric | Minimum Target | Notes |
    -----|---------------|-------|
    mple Size | 100+ trades | Statistical significance |
    n Rate | 40%+ | With good R:R can be profitable |
    ofit Factor | 1.3+ | Gross profit / gross loss |
    x Drawdown | <20% | Worst peak-to-trough decline |
    pectancy | >0.2R | Positive edge per trade |
    
    
    
    tep-by-Step Breakdown
    
    nual Backtesting Process**:
    Define precise entry/exit/stop rules (write them down)
    Select 2-3 years of historical data
    Start at beginning, scroll candle by candle
    Mark every valid setup (even if not taking them)
    Record: Entry, Stop, Target, Outcome (win/loss), R-multiple
    Complete minimum 100 trades
    Calculate win rate, expectancy, profit factor
    If positive expectancy, proceed to demo trading
    
    
    
    eal Trading Example
    
    eakout Strategy Backtest Results** (EUR/USD, 2022-2024):
    **Sample**: 156 trades over 2 years
    **Win Rate**: 42.3%
    **Avg Win**: 2.8R
    **Avg Loss**: 1R
    **Expectancy**: (0.423 × 2.8) – (0.577 × 1) = **+0.61R**
    **Profit Factor**: 1.62
    **Max Drawdown**: 18.4%
    **Conclusion**: System has edge—proceed to forward testing
    
    
    
     Chart Example
    
    cktesting](/static/charts/backtesting_equity_curve.png)
    
    
    
     Common Beginner Mistake
    
    erry-Picking**: Only recording "perfect" setups and ignoring marginal ones. This inflates results unrealistically. Backtest ALL setups that meet your criteria—even ugly ones. Real trading includes ugly setups.
    
    
    
     Pro Tip
    
    e Blind Backtest**: Have someone else backtest your rules without knowing your preferred pairs or timeframes. If results are positive on multiple pairs/timeframes, your edge is robust (not curve-fitted).
    
    
    
    ey Takeaway
    
    testing proves your edge exists historically. Minimum 100 trades for statistical validity. Track expectancy, not just win rate. If backtest fails, system is broken—don't trade it live. Walk-forward testing validates backtest results.
    
    
    
    ractice Question
    
    mum sample size for statistically valid backtest?""",
                        "quiz": [
                            {"question": "Backtesting purpose?", "option_a": "Predict exact prices", "option_b": "Validate edge historically", "option_c": "Replace live trading", "option_d": "Eliminate risk", "correct_answer": "B", "explanation": "Backtesting validates whether your system has positive expectancy.", "topic_slug": "system_development"},
                            {"question": "Minimum trades for valid backtest?", "option_a": "10", "option_b": "50", "option_c": "100+", "option_d": "1000", "correct_answer": "C", "explanation": "Minimum 100 trades for statistical significance.", "topic_slug": "system_development"},
                            {"question": "Danger of automated backtesting?", "option_a": "Too slow", "option_b": "Overfitting (curve-fitting)", "option_c": "No data available", "option_d": "Too expensive", "correct_answer": "B", "explanation": "Automated tests can overfit to past data—failing in live markets.", "topic_slug": "system_development"}
                        ]
                    },
                    {
                        "title": "Creating Your Trading System",
                        "content": """## Quick Definition
    
    Trading System** is a complete set of rules covering: setups, entries, exits, risk management, and position sizing. Good systems remove discretion and emotion from trading decisions.
    
    
    
    oncept Explanation
    
    System Components
    
     Market Selection**
    Which pairs/instruments to trade
    Minimum daily volume requirements
    Preferred trading sessions
    
     Setup Criteria**
    Precise conditions for valid trade
    Confluence requirements (minimum factors)
    Timeframe alignment rules
    
     Entry Rules**
    Specific trigger conditions
    Order types (market, limit, stop)
    Confirmation requirements
    
     Exit Rules**
    Stop loss placement (technical vs fixed)
    Take profit targets (R-multiples)
    Trailing stop conditions
    
     Risk Management**
    Fixed % risk per trade
    Maximum daily/weekly loss limits
    Correlation adjustments
    
    
    
    tep-by-Step Breakdown
    
    ilding Your System**:
    Choose ONE setup to master (e.g., pin bars at S/R)
    Write exact entry rules (no ambiguity)
    Define stop loss rules (always technical)
    Set minimum R:R (1:2 or better)
    Fix risk per trade (1-2%)
    Backtest 100+ trades
    Paper trade for 20 trades
    Go live with reduced size (0.5%)
    Scale up after 50 successful live trades
    
    
    
    eal Trading Example
    
    e "London Breakout" System**:
    
    tup**:
    Asian session range forms (20:00-08:00 UTC)
    Price near session high or low
    Minimum range: 30 pips
    
    try**:
    Buy stop 5 pips above Asian high
    Sell stop 5 pips below Asian low
    
    op**: Beyond opposite side of range
    
    rget**: 2R minimum
    
    sk**: 1% per trade, max 2 trades/day
    
    sult**: 38% win rate, 2.4:1 R:R, +0.41R expectancy
    
    
    
     Chart Example
    
    ading System](/static/charts/trading_system_flowchart.png)
    
    
    
     Common Beginner Mistake
    
    stem Hopping**: Abandoning a system after 10-20 losses. Even good systems have losing streaks. Backtest results showed 40% win rate—you should EXPECT 6 losses in a row occasionally. Stick to your system through variance.
    
    
    
     Pro Tip
    
    e "One Setup" Rule**: Master ONE setup completely before adding others. Most successful traders use 2-3 setups maximum. Specialization beats diversification in trading. Become the world's best pin bar trader rather than average at 10 patterns.
    
    
    
    ey Takeaway
    
    mplete trading system leaves no decisions to discretion. Every scenario is covered by rules. Backtest before trading live. Paper trade before sizing up. Master one setup before diversifying. Consistency comes from system discipline.
    
    
    
    ractice Question
    
    many setups should a beginner focus on initially?""",
                        "quiz": [
                            {"question": "Most important system component?", "option_a": "Complex indicators", "option_b": "Clear, unambiguous rules", "option_c": "High win rate", "option_d": "Many setups", "correct_answer": "B", "explanation": "Clear rules eliminate discretion and emotion.", "topic_slug": "system_development"},
                            {"question": "Beginner setup recommendation?", "option_a": "Master 10 setups", "option_b": "Master 1 setup first", "option_c": "No setup needed", "option_d": "Use all available patterns", "correct_answer": "B", "explanation": "Master one setup completely before adding complexity.", "topic_slug": "system_development"},
                            {"question": "Before trading live?", "option_a": "Start immediately", "option_b": "Backtest then paper trade", "option_c": "Skip testing", "option_d": "Use maximum size", "correct_answer": "B", "explanation": "Validate with backtesting, then paper trade before risking capital.", "topic_slug": "system_development"}
                        ]
                    }
                ]
            },
            {
                "title": "The Complete Trading Plan",
                "description": "Building your trading business plan.",
                "lessons": [
                    {
                        "title": "Creating Your Trading Plan",
                        "content": """## Quick Definition
    
    Trading Plan** is your complete business blueprint covering goals, strategies, routines, and review processes. It transforms trading from gambling into a structured business operation.
    
    
    
    oncept Explanation
    
    Trading Plan Components
    
    ction 1: Goals and Objectives**
    Monthly/Yearly return targets (realistic: 3-5% monthly)
    Maximum acceptable drawdown (15-20%)
    Timeline to profitability (6-12 months)
    Account growth milestones
    
    ction 2: Trading Strategy**
    Specific setups you will trade
    Entry/exit rules (exact criteria)
    Risk per trade (1-2%)
    Maximum trades per day/week
    
    ction 3: Risk Management**
    Daily loss limit (e.g., 3%)
    Weekly loss limit (e.g., 6%)
    Correlation rules
    Portfolio heat maximum (6%)
    
    ction 4: Routine and Schedule**
    Pre-market preparation time
    Active trading hours
    Post-market review time
    Weekend analysis time
    
    ction 5: Review Process**
    Weekly performance review
    Monthly deep analysis
    Quarterly strategy evaluation
    Annual goal reassessment
    
    
    
    tep-by-Step Breakdown
    
    iting Your Plan**:
    Document your complete trading system
    Set realistic 6-month and 1-year goals
    Define daily routine (pre, during, post market)
    Create risk limits and circuit breakers
    Establish review schedule
    Print and sign the plan (commitment)
    Review weekly—track adherence
    Update quarterly if needed
    
    
    
    eal Trading Example
    
    ofessional Trading Plan Snapshot**:
    
    als**:
    Monthly target: 4% return
    Max drawdown: 15%
    12-month goal: 60% account growth
    
    rategy**:
    Primary: Breakout system (H4)
    Secondary: Pin bar reversals (Daily)
    Risk: 1.5% per trade
    
    sk Limits**:
    Daily max loss: 3%
    Weekly max loss: 6%
    Consecutive losses: Stop after 3
    
    utine**:
    Pre-market: 7:00-8:00 UTC (analysis)
    Trading: 8:00-12:00 UTC only
    Review: 20:00 UTC daily
    
    sult**: 90% plan adherence = consistent profitability
    
    
    
     Chart Example
    
    ading Plan](/static/charts/trading_plan_template.png)
    
    
    
     Common Beginner Mistake
    
    e Mental Plan**: Having a "rough idea" but nothing written down. Written plans are 3x more likely to be followed. Write it, print it, post it by your monitor. Vague plans produce vague results.
    
    
    
     Pro Tip
    
    e Signature Rule**: Print your trading plan, sign it, and post it by your trading station. The physical act of signing creates psychological commitment. Refer to it when tempted to break rules.
    
    
    
    ey Takeaway
    
     trading plan is your business plan. It covers every aspect of your trading operation. Write it down. Review it weekly. Update it quarterly. Follow it religiously. Traders with written plans outperform those without by 3:1.
    
    
    
    ractice Question
    
    often should you review your trading plan performance?""",
                        "quiz": [
                            {"question": "Trading plan purpose?", "option_a": "Predict prices", "option_b": "Structure trading as business", "option_c": "Replace analysis", "option_d": "Guarantee profits", "correct_answer": "B", "explanation": "A trading plan is your complete business blueprint for trading.", "topic_slug": "trading_plan"},
                            {"question": "Key plan components?", "option_a": "Only entry rules", "option_b": "Goals, strategy, risk, routine, review", "option_c": "Only profit targets", "option_d": "Only stop losses", "correct_answer": "B", "explanation": "Complete plans cover goals, strategy, risk management, routine, and review process.", "topic_slug": "trading_plan"},
                            {"question": "Realistic monthly return target?", "option_a": "50%", "option_b": "3-5%", "option_c": "20%", "option_d": "100%", "correct_answer": "B", "explanation": "Professional traders target 3-5% monthly—higher is unsustainable.", "topic_slug": "trading_plan"}
                        ]
                    },
                    {
                        "title": "Performance Review and Optimization",
                        "content": """## Quick Definition
    
    rformance Review** is systematic analysis of your trading results to identify strengths, weaknesses, and optimization opportunities. Regular review transforms good traders into great ones.
    
    
    
    oncept Explanation
    
    Review Frequencies
    
    ily Review (5-10 minutes)**:
    Did I follow my plan?
    Emotional state during trades
    Any rule violations?
    Lessons for tomorrow
    
    ekly Review (30-60 minutes)**:
    Win rate and expectancy
    R-multiple distribution
    Setup performance comparison
    Mistake patterns
    
    nthly Review (2-3 hours)**:
    Equity curve analysis
    Drawdown periods study
    Strategy performance by market condition
    Goal progress assessment
    
    arterly Review (Full day)**:
    System optimization
    Strategy refinement
    Major rule adjustments
    Goal reassessment
    
    Key Metrics to Analyze
    
    tric | Good | Excellent |
    -----|------|-----------|
    n Rate | 45%+ | 55%+ |
    ofit Factor | 1.5+ | 2.0+ |
    pectancy | >0.3R | >0.5R |
    an Adherence | 80%+ | 90%+ |
    
    
    
    tep-by-Step Breakdown
    
    ekly Review Process**:
    Export all trades for the week
    Calculate win rate, avg win, avg loss
    Compute expectancy and profit factor
    Review each losing trade—identify errors
    Categorize mistakes (emotional, technical, execution)
    Set focus for next week (one improvement area)
    Journal insights and commitments
    
    
    
    eal Trading Example
    
    nthly Review Insights** (Trader X):
    
    ta**:
    Win Rate: 52%
    Profit Factor: 1.4 (below 1.5 target)
    Expectancy: +0.35R
    
    ttern Discovered**:
    Trades after 2pm UTC: -0.2R expectancy
    Trades before 10am UTC: +0.6R expectancy
    
    timization**:
    Eliminated afternoon trading
    Increased morning session focus
    Next month: +0.58R expectancy
    
    
    
     Chart Example
    
    rformance Review](/static/charts/performance_review_dashboard.png)
    
    
    
     Common Beginner Mistake
    
    ipping Reviews**: Trading day after day without review is like practicing golf without watching your swing. You repeat the same errors indefinitely. Even 10 minutes of daily review compounds into massive improvement over a year.
    
    
    
     Pro Tip
    
    e One-Focus Rule**: Each week, identify ONE area to improve. Don't try to fix everything at once. If you're cutting winners early, focus only on that for one week. Master one skill before moving to the next.
    
    
    
    ey Takeaway
    
    ormance review separates professionals from amateurs. Review daily, weekly, monthly, quarterly. Track metrics, identify patterns, optimize continuously. The trader who reviews consistently beats the trader who doesn't—regardless of starting skill level.
    
    
    
    ractice Question
    
     frequency for in-depth strategy review?""",
                        "quiz": [
                            {"question": "Performance review purpose?", "option_a": "Find scapegoats", "option_b": "Identify improvement areas", "option_c": "Avoid losses", "option_d": "Predict next trade", "correct_answer": "B", "explanation": "Review identifies patterns and areas for optimization.", "topic_slug": "trading_plan"},
                            {"question": "Daily review duration?", "option_a": "5-10 minutes", "option_b": "2 hours", "option_c": "All evening", "option_d": "No review needed", "correct_answer": "A", "explanation": "Daily review should be quick—5-10 minutes maximum.", "topic_slug": "trading_plan"},
                            {"question": "Quarterly review purpose?", "option_a": "Daily adjustments", "option_b": "Major strategy optimization", "option_c": "Entry timing", "option_d": "News analysis", "correct_answer": "B", "explanation": "Quarterly reviews allow for major system adjustments.", "topic_slug": "trading_plan"}
                        ]
                    }
                ]
            }
        ]
    }
]
