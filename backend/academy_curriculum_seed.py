"""
Pipways Trading Academy — Curriculum v2.0
Babypips-style rewrite: conversational, story-led, NGX-localised.
28 Lessons · 3 Levels · 14 Modules · 2 Lessons each

CALLOUT SYNTAX (parsed by the frontend renderer):
  > [!HOOK]     Opening story / analogy (purple left-border)
  > [!DEF]      Plain-English definition box (blue)
  > [!EXAMPLE]  Worked trade example with real numbers (indigo)
  > [!NGX]      Nigerian market parallel (amber — Pipways' moat)
  > [!MISTAKE]  Common error box (red)
  > [!TIP]      Pro insight box (green)
  > [!TAKEAWAY] Single-sentence lesson summary (gray)
"""

ACADEMY_CURRICULUM = [

# ══════════════════════════════════════════════════════════════════════════════
# LEVEL 1 — BEGINNER
# ══════════════════════════════════════════════════════════════════════════════
{
    "level_name": "Beginner",
    "description": "Start here. No experience needed. You'll learn what Forex is, who moves it, how to read prices, and the one risk rule that separates traders who survive from those who blow up in week one.",
    "modules": [

        # ── MODULE 1 ──────────────────────────────────────────────────────────
        {
            "title": "Introduction to Forex Trading",
            "description": "What the Forex market is, who is in it, and why it moves.",
            "lessons": [
                {
                    "title": "What is Forex Trading?",
                    "content": """\
> [!HOOK]
> In January 2015, the Swiss National Bank quietly removed a currency peg it had held for three years. Within 60 seconds, the Swiss franc surged 30%. Fortunes were made and destroyed before most people had finished their morning coffee. That is Forex — the world's largest financial market, running 24 hours a day, moving $7.5 trillion before you wake up.

> [!DEF]
> **Forex** (Foreign Exchange) is the global marketplace where one currency is exchanged for another. It operates 24 hours a day, 5 days a week, with over **$7.5 trillion traded daily** — more than all the world's stock markets combined.

Every time a Nigerian company pays a US supplier in dollars, a tourist exchanges naira at the airport, or an investor buys a UK property in pounds — that is the Forex market at work. You are doing the same thing at a smaller scale, with the goal of profiting from exchange rate movement.

### How a trade works

Currencies trade in pairs. You buy one and simultaneously sell another.

- **Base currency** — the one you buy or sell (EUR in EUR/USD)
- **Quote currency** — the one you pay with (USD in EUR/USD)
- **Exchange rate** — how much quote currency buys one unit of base

If EUR/USD is 1.0850, one Euro buys $1.0850. If you think the euro strengthens, you buy. If the rate moves to 1.0900, you profit 50 pips.

### Why prices move

Supply and demand. Strong economies attract buyers for their currency. Weak data, rising inflation, or political instability drives sellers. Interest rate decisions, employment data, and central bank statements are the biggest catalysts.

> [!EXAMPLE]
> **EUR/USD buy setup after weak US jobs data:**
>
> - Entry: 1.0850 · Stop: 1.0820 (30 pips) · Target: 1.0910 (60 pips)
> - Position size: 0.1 lots ($1/pip)
> - Risk: $30 · Reward: $60 · R:R = 1:2
>
> The outcome is fully defined before you enter a single order. That is the entire discipline.

> [!NGX]
> **Nigerian angle:** USD/NGN is one of the most closely watched pairs in Nigeria. When the CBN adjusts monetary policy or oil prices shift sharply, the naira reacts immediately. Nigerian traders who understand Forex mechanics can read these moves rather than watching helplessly as import costs change overnight.

> [!MISTAKE]
> New traders think Forex is about predicting the future. It is not. It is about managing risk on a probability. Even the best setups fail 40% of the time. What separates profitable traders is making more on winners than they lose on losers — not being right every time.

> [!TIP]
> Start with EUR/USD. It has the tightest spread (0.1–0.3 pips), highest liquidity, and most predictable behaviour of any pair. Master one pair before adding a second.

> [!TAKEAWAY]
> Forex trading is the business of buying one currency and selling another — profits come not from prediction but from consistent risk management applied to high-probability setups.
""",
                    "quiz": [
                        {"question": "EUR/USD is quoted at 1.0850. What does this mean?", "option_a": "1 USD buys 1.0850 EUR", "option_b": "1 EUR buys 1.0850 USD", "option_c": "The EUR has fallen 1.0850%", "option_d": "USD is the base currency", "correct_answer": "B", "explanation": "EUR is the base currency. A rate of 1.0850 means each Euro buys $1.0850 USD.", "topic_slug": "forex_basics"},
                        {"question": "EUR/USD moves from 1.0800 to 1.0850. How many pips?", "option_a": "5", "option_b": "50", "option_c": "0.5", "option_d": "500", "correct_answer": "B", "explanation": "1.0850 - 1.0800 = 0.0050 = 50 pips. For 4-decimal pairs, 1 pip = 0.0001.", "topic_slug": "forex_basics"},
                        {"question": "You buy 0.1 lots EUR/USD at 1.0850. Price falls to 1.0800. Your loss?", "option_a": "$5", "option_b": "$500", "option_c": "$50", "option_d": "$5,000", "correct_answer": "C", "explanation": "50 pips x $1/pip (0.1 lots) = $50 loss.", "topic_slug": "forex_basics"},
                        {"question": "Which best describes the Forex market?", "option_a": "A centralised exchange like the NYSE", "option_b": "A decentralised global network of banks and traders", "option_c": "A government-controlled currency auction", "option_d": "A market open only during London hours", "correct_answer": "B", "explanation": "Forex has no central exchange. It operates across banks, brokers, and ECNs globally, 24 hours, 5 days.", "topic_slug": "forex_basics"},
                        {"question": "A trader wins 60% of trades but still loses money overall. Most likely reason?", "option_a": "Trading the wrong pairs", "option_b": "Winning trades average less than losing trades", "option_c": "Trading too infrequently", "option_d": "Using too little leverage", "correct_answer": "B", "explanation": "Win rate alone means nothing. A 60% win rate with 1:0.5 R:R is a losing system. Wins must be larger than losses on average.", "topic_slug": "forex_basics"}
                    ]
                },
                {
                    "title": "Who Trades Forex and Why?",
                    "content": """\
> [!HOOK]
> On October 16, 1992 — Black Wednesday — George Soros bet $10 billion that the British pound was overvalued. The Bank of England fought back with everything it had. By evening, the UK had crashed out of the European Exchange Rate Mechanism and Soros had made $1 billion in a single day. You will never trade at his scale, but understanding who the players are tells you exactly which waves to ride and which ones will drown you.

> [!DEF]
> The Forex market has a **hierarchy of participants** — from central banks moving entire economies down to retail traders like you. Knowing each tier explains why prices move the way they do and which direction the real money is flowing.

### The four tiers

**Tier 1 — Central Banks (30%+ of volume)**
The Fed, ECB, and CBN set interest rates and can intervene directly. When the Fed raises rates, the dollar strengthens. These are the tide — slow, massive, unstoppable.

**Tier 2 — Commercial Banks and Hedge Funds (~50%)**
Goldman Sachs, JPMorgan, and macro funds trade hundreds of billions daily. They create the trends you see on charts. Their order flows produce the support and resistance levels you will trade.

**Tier 3 — Corporations (~15%)**
Companies like Dangote, Shell, and Apple exchange currencies daily just to run their businesses. A Nigerian importer paying a US supplier must buy dollars — creating predictable demand at certain price levels.

**Tier 4 — Retail Traders (<5%)**
You. Small, nimble, zero market impact. Your advantage is freedom. You have no mandate, no risk committee, no obligation to deploy capital. You can sit out when conditions are poor. The big players cannot.

> [!EXAMPLE]
> **The CBN intervention trade:**
>
> The CBN announces an unexpected 200bps rate hike. USD/NGN drops 400 pips within 30 minutes as naira demand overwhelms sellers.
>
> A retail trader who understood CBN's hawkish rhetoric entered short USD/NGN the day before the announcement — and rode the move with a 1:3 risk-reward setup. The institutional action created the move. The retail trader read the setup and positioned early.

> [!NGX]
> **NGX parallel:** When Coronation Asset Management or Stanbic IBTC rotate into NGX equities, they buy in sizes that move prices. You see their footprint in volume spikes and gap-up opens on MTNN and DANGCEM. Following institutional flow works exactly the same in NGX stocks as it does in currency pairs.

> [!MISTAKE]
> Retail traders often try to fade big moves — assuming a large spike must reverse. Sometimes it does. But when a central bank or major institution is behind the move, fading it is standing in front of a train. Know who is driving before betting against it.

> [!TIP]
> Follow central bank meeting calendars (Fed, ECB, CBN MPC). Rate decisions and forward guidance create the biggest directional moves of the year. Trade the confirmed setup after the event — not the speculation before it.

> [!TAKEAWAY]
> Retail traders make up less than 5% of Forex volume — survival means trading in the same direction as the institutions and central banks that move the other 95%.
""",
                    "quiz": [
                        {"question": "Which participant has the greatest ability to move currency prices?", "option_a": "Retail traders", "option_b": "Multinational corporations", "option_c": "Central banks", "option_d": "Hedge funds", "correct_answer": "C", "explanation": "Central banks set interest rates and can directly intervene — they create the macro trends every other participant trades around.", "topic_slug": "market_participants"},
                        {"question": "A hedge fund is aggressively buying EUR/USD. The smartest retail response is:", "option_a": "Sell — big moves always reverse", "option_b": "Wait for a pullback entry to join the buy trend", "option_c": "Ignore it — retail traders are unaffected by hedge funds", "option_d": "Buy a different pair instead", "correct_answer": "B", "explanation": "Trading with institutional flow is the retail trader's biggest edge. Look for a pullback entry to enter in the same direction.", "topic_slug": "market_participants"},
                        {"question": "The main advantage retail traders have over institutional players is:", "option_a": "More capital", "option_b": "Better data feeds", "option_c": "Freedom to sit out when conditions are unfavourable", "option_d": "Lower spreads", "correct_answer": "C", "explanation": "Institutions have mandates and must deploy capital regardless. You can wait for ideal conditions — that patience is your biggest structural edge.", "topic_slug": "market_participants"},
                        {"question": "Why do Nigerian importers create predictable Forex demand?", "option_a": "They speculate on currency moves", "option_b": "They must buy USD regularly to pay for imports regardless of the rate", "option_c": "They set exchange rates for their sector", "option_d": "They copy central bank trades", "correct_answer": "B", "explanation": "Import-dependent corporations buy foreign currency regularly regardless of rate. This creates demand at predictable levels and times.", "topic_slug": "market_participants"},
                        {"question": "The Fed signals three rate cuts in the coming year. You would expect:", "option_a": "The USD to strengthen significantly", "option_b": "No change — markets already priced it in", "option_c": "The USD to weaken as rate differentials narrow", "option_d": "Other central banks to raise rates in response", "correct_answer": "C", "explanation": "Lower rates reduce yield on USD assets, reducing demand for dollars. USD typically weakens in a rate-cutting cycle.", "topic_slug": "market_participants"}
                    ]
                },
            ]
        },

        # ── MODULE 2 ──────────────────────────────────────────────────────────
        {
            "title": "Currency Pairs and Price Quotes",
            "description": "The alphabet of Forex — read any price quote at a glance.",
            "lessons": [
                {
                    "title": "Major, Minor and Exotic Pairs",
                    "content": """\
> [!HOOK]
> Walk into any Nigerian bureau de change and you'll see rates for USD, GBP, and EUR on the board. Tight rates, fast service — the staff know these currencies inside out. Ask for the Czech koruna rate and you'll get a blank stare. That is exactly the difference between major, minor, and exotic pairs, and it explains everything about which ones you should trade first.

> [!DEF]
> Currency pairs are grouped by **liquidity and volume**. Major pairs always include USD and have the tightest spreads. Minor pairs pair two major currencies without USD. Exotic pairs include one emerging-market currency and carry much wider spreads and higher volatility.

### Major pairs — your home base

| Pair | Nickname | Description |
|------|----------|-------------|
| EUR/USD | Fiber | Euro vs US Dollar |
| GBP/USD | Cable | British Pound vs Dollar |
| USD/JPY | Ninja | Dollar vs Japanese Yen |
| USD/CHF | Swissie | Dollar vs Swiss Franc |
| USD/CAD | Loonie | Dollar vs Canadian Dollar |
| AUD/USD | Aussie | Australian Dollar vs Dollar |
| NZD/USD | Kiwi | New Zealand Dollar vs Dollar |

EUR/USD alone represents roughly 23% of all Forex trades daily. Spreads are paper-thin, behaviour is predictable. This is where beginners belong.

### Minor pairs — removing the dollar

EUR/GBP, EUR/AUD, GBP/JPY. Two major currencies without USD. Slightly wider spreads, can move sharply when both economies release data on the same day.

### Exotic pairs — high spread, high caution

USD/NGN, USD/ZAR, USD/TRY. Spreads can be 30–100 pips. News events cause gaps and slippage. Not for beginners — but every Nigerian trader should understand USD/NGN structurally.

> [!EXAMPLE]
> **Spread comparison:**
>
> - EUR/USD spread: 0.2 pips → on 0.1 lot, you start $0.20 in the hole
> - USD/NGN spread: 40 pips → on 0.1 lot, you start $4.00 in the hole
>
> To break even on EUR/USD, price needs to move 0.2 pips in your favour. On USD/NGN, it needs 40 pips. That spread cost compounds across every trade you take.

> [!NGX]
> **NGX parallel:** Blue-chip NGX stocks like MTNN, GTCO, and ZENITH are the equivalent of major pairs — high volume, tight bid-ask spreads, predictable price behaviour. Small-cap and mid-cap stocks are the exotics — wide spreads, thin volume, erratic moves. The logic of starting with the most liquid instruments applies identically.

> [!MISTAKE]
> Beginners are drawn to exotic pairs because "USD/TRY moved 300 pips!" sounds exciting — until you realise the spread was 100 pips and volatility hit your stop twice before the move happened. Stick to majors until you are consistently profitable.

> [!TIP]
> USD/JPY is an excellent second pair for beginners. It is heavily influenced by one factor — Bank of Japan policy — making it more predictable than pairs driven by multiple variables. The 2-decimal pip value also forces you to calculate carefully, building a good habit.

> [!TAKEAWAY]
> Start with EUR/USD, master one pair before adding another, and avoid exotic pairs until your risk management is rock solid — the wide spreads make them unforgiving.
""",
                    "quiz": [
                        {"question": "What makes a currency pair 'major'?", "option_a": "It includes the EUR", "option_b": "It always includes the USD on one side", "option_c": "It has high volatility", "option_d": "It is traded only in Europe and the US", "correct_answer": "B", "explanation": "All seven major pairs include USD as either the base or quote currency. This gives them the highest liquidity and tightest spreads.", "topic_slug": "currency_pairs"},
                        {"question": "EUR/GBP is classified as:", "option_a": "A major pair", "option_b": "A minor pair", "option_c": "An exotic pair", "option_d": "A regional pair", "correct_answer": "B", "explanation": "EUR/GBP pairs two major currencies without USD — the definition of a minor pair.", "topic_slug": "currency_pairs"},
                        {"question": "Best pair for a beginner on demo?", "option_a": "USD/TRY", "option_b": "USD/NGN", "option_c": "EUR/USD", "option_d": "GBP/ZAR", "correct_answer": "C", "explanation": "EUR/USD has the tightest spreads, highest liquidity, and most stable behaviour — ideal for learning.", "topic_slug": "currency_pairs"},
                        {"question": "USD/NGN has a 40-pip spread. EUR/USD has a 0.3-pip spread. Trading USD/NGN costs approximately how much more in spread?", "option_a": "The same", "option_b": "Slightly more", "option_c": "Over 130x more per trade", "option_d": "Less, because NGN moves faster", "correct_answer": "C", "explanation": "40 / 0.3 = 133x. Every USD/NGN trade costs 133 times more in spread than EUR/USD.", "topic_slug": "currency_pairs"},
                        {"question": "Compared to EUR/USD, GBP/JPY (a minor pair) will typically have:", "option_a": "A tighter spread", "option_b": "Higher volatility and a wider spread", "option_c": "Lower daily volume", "option_d": "More predictable price behaviour", "correct_answer": "B", "explanation": "Minor pairs exclude USD. Without the world's reserve currency providing liquidity, they carry wider spreads and tend to be more volatile.", "topic_slug": "currency_pairs"}
                    ]
                },
                {
                    "title": "Reading Pips and Spreads",
                    "content": """\
> [!HOOK]
> Every time you open a Forex trade, you immediately lose money. Not because you made a bad call — because of the spread. Understanding pips and spreads is not optional background knowledge. It is the arithmetic that determines whether a trading strategy is even viable before a single trade is placed.

> [!DEF]
> A **pip** is the smallest standard price move in a currency pair — typically the fourth decimal place (0.0001) for most pairs. The **spread** is the difference between the buy (ask) and sell (bid) price — your broker's fee, paid the moment you enter any trade.

### Calculating pips

EUR/USD moves from 1.0850 to 1.0900:
1.0900 − 1.0850 = 0.0050 = **50 pips**

USD/JPY (2-decimal pair) moves from 149.50 to 150.00:
150.00 − 149.50 = 0.50 = **50 pips** (1 pip = 0.01 for JPY pairs)

### Pip value by lot size

| Lot Type | Size | EUR/USD Pip Value |
|----------|------|-------------------|
| Standard | 100,000 units | $10/pip |
| Mini | 10,000 units | $1/pip |
| Micro | 1,000 units | $0.10/pip |

### The spread — your real entry cost

EUR/USD: Bid 1.0849 / Ask 1.0851 → Spread = 2 pips

You BUY at the ask (1.0851). You SELL at the bid (1.0849). The moment you buy, you are 2 pips in the red. Price must move 2 pips in your direction just to break even.

> [!EXAMPLE]
> **Spread impact on a scalping strategy:**
>
> Strategy targets 10 pips profit per trade. Broker A charges 3-pip spread. Broker B charges 0.2-pip spread.
>
> - Broker A: net gain per win = 10 − 3 = **7 pips**. Need 30% win rate to cover spread alone.
> - Broker B: net gain per win = 10 − 0.2 = **9.8 pips**. Need 2% win rate to cover spread alone.
>
> Over 500 trades, the difference in spread costs alone is enormous. Broker selection is strategy selection.

> [!NGX]
> **NGX parallel:** Every NGX stock has a bid-ask spread. MTNN might show Bid ₦220.00 / Ask ₦220.50. If you buy at market, you are immediately ₦0.50 behind. On illiquid mid-caps the spread widens to ₦2–5, making short-term trading expensive. Savvy NGX traders use limit orders to buy at the bid rather than the ask, reducing their spread cost.

> [!MISTAKE]
> Comparing brokers only on commission without checking spreads. A "zero commission" broker charging 3 pips on EUR/USD is 10–15x more expensive per trade than a commission-charging broker with 0.2-pip spread. Always calculate total round-trip cost: spread + commission.

> [!TIP]
> During major news events (NFP, Fed rate decisions, CBN MPC), spreads widen dramatically — sometimes 10–20x normal. A 0.3-pip EUR/USD spread can hit 5 pips during a Fed announcement. Avoid entering new positions in the 5 minutes before and after high-impact news.

> [!TAKEAWAY]
> Every trade starts with the spread as an immediate cost — choosing a tight-spread broker and timing entries away from news events compounds into significant savings across thousands of trades.
""",
                    "quiz": [
                        {"question": "EUR/USD moves from 1.1200 to 1.1265. How many pips?", "option_a": "6.5", "option_b": "65", "option_c": "650", "option_d": "0.65", "correct_answer": "B", "explanation": "1.1265 - 1.1200 = 0.0065 = 65 pips.", "topic_slug": "pips_spreads"},
                        {"question": "You hold 1 mini lot EUR/USD and price moves 30 pips in your favour. Profit?", "option_a": "$3", "option_b": "$30", "option_c": "$300", "option_d": "$3,000", "correct_answer": "B", "explanation": "1 mini lot on EUR/USD = $1/pip. 30 pips x $1 = $30.", "topic_slug": "pips_spreads"},
                        {"question": "EUR/USD Bid: 1.0920 / Ask: 1.0923. What is the spread?", "option_a": "1 pip", "option_b": "2 pips", "option_c": "3 pips", "option_d": "23 pips", "correct_answer": "C", "explanation": "1.0923 - 1.0920 = 0.0003 = 3 pips spread.", "topic_slug": "pips_spreads"},
                        {"question": "You open a buy with a 2-pip spread, targeting 8 pips. Actual net gain if target is hit?", "option_a": "10 pips", "option_b": "8 pips", "option_c": "6 pips", "option_d": "4 pips", "correct_answer": "C", "explanation": "Target 8 pips minus 2-pip spread cost = 6 pips net. You enter 2 pips in the hole immediately.", "topic_slug": "pips_spreads"},
                        {"question": "Spreads widen from 0.3 to 5 pips during a Fed announcement. A trader enters mid-announcement. The primary risk?", "option_a": "Position size is too large", "option_b": "The broker may reject the order", "option_c": "Price must move 5 pips just to break even — a tight stop will be hit by spread alone", "option_d": "Pip value changes during news", "correct_answer": "C", "explanation": "Entering on a 5-pip spread means your breakeven is 5 pips away from entry. Any stop tighter than 5 pips will be triggered by the spread before the market even moves.", "topic_slug": "pips_spreads"}
                    ]
                },
            ]
        },

        # ── MODULE 3 ──────────────────────────────────────────────────────────
        {
            "title": "Pips, Lots, and Leverage",
            "description": "The financial mechanics of every trade — how size and leverage determine what you actually risk.",
            "lessons": [
                {
                    "title": "Understanding Leverage",
                    "content": """\
> [!HOOK]
> In 2021, a retail trader turned a $1,000 account into $48,000 in three weeks using 500:1 leverage. Three weeks later, a margin call wiped the entire balance. He had discovered the double-edged sword that has destroyed more trading accounts than any strategy failure ever has. Leverage is the most powerful tool in Forex — and the most dangerous if you do not understand it precisely.

> [!DEF]
> **Leverage** lets you control a position larger than your account balance. With 100:1 leverage, a $1,000 deposit controls a $100,000 position. Every pip movement in that $100,000 position hits your $1,000 account in full — amplifying both profits and losses by 100x.

### How leverage works

With $1,000 and 100:1 leverage:
- Buying power = $1,000 × 100 = **$100,000**
- You can open 1 standard lot EUR/USD

A 50-pip move = $500 profit → **50% return on your $1,000.**

Now the other side: a 100-pip move against you = **$1,000 loss — your entire account**, without a crash. Just a bad afternoon.

### Margin — the deposit behind the position

When you use leverage, your broker holds a portion of your account as **margin** — a good-faith deposit securing the position.

Margin = (Position size × price) ÷ Leverage

1 lot EUR/USD at 1.0850 with 100:1: ($100,000 × 1.0850) ÷ 100 = **$1,085 required margin**

If losses erode your free margin below the broker's threshold, you get a **margin call** — positions auto-close at a loss.

> [!EXAMPLE]
> **Two traders, same account, same trade, different leverage:**
>
> Account: $5,000. EUR/USD entry: 1.0850. Stop: 50 pips. Target: 100 pips.
>
> **Trader A (10:1 effective):** 0.1 lot → Risk: $50 (1%) → Potential profit: $100
> **Trader B (100:1 effective):** 1.0 lot → Risk: $500 (10%) → Potential profit: $1,000
>
> After 10 consecutive losses (possible even with a 60% win rate):
> Trader A is down 10% and recovers. Trader B's account no longer exists.

> [!NGX]
> **NGX parallel:** The Nigerian Exchange is a cash market with no leverage. But some Nigerian traders access CFDs on NGX stocks through offshore brokers offering 5:1 leverage. The same principle applies — leverage amplifies NGN exposure beyond your deposit. Without strict position sizing, a sharp sell-off in an illiquid mid-cap forces margin liquidation at the worst possible price.

> [!MISTAKE]
> Using the maximum leverage your broker offers because it is available. Brokers offer high leverage as a marketing tool — it generates more spread revenue for them. Your job is to ignore the maximum and use only what fits inside your risk management rules.

> [!TIP]
> Think in terms of **effective leverage** (position notional ÷ account balance), not your broker's advertised ceiling. Keep effective leverage below 10:1 as a beginner. Once you are consistently profitable for 6 months, you can reconsider. Not before.

> [!TAKEAWAY]
> Leverage multiplies every outcome — a beginner's goal is to use the minimum effective leverage that still generates meaningful returns while keeping each trade's risk at 1–2% of account equity.
""",
                    "quiz": [
                        {"question": "Account: $2,000, leverage: 50:1. Maximum position size?", "option_a": "$2,000", "option_b": "$20,000", "option_c": "$100,000", "option_d": "$200,000", "correct_answer": "C", "explanation": "$2,000 x 50 = $100,000 maximum notional exposure.", "topic_slug": "leverage"},
                        {"question": "You have $3,000 and open 1.0 standard lot EUR/USD at 100:1. A 30-pip move against you causes what loss?", "option_a": "$30", "option_b": "$300", "option_c": "$3,000", "option_d": "$30,000", "correct_answer": "B", "explanation": "Standard lot = $10/pip. 30 pips x $10 = $300 loss.", "topic_slug": "leverage"},
                        {"question": "A margin call happens when:", "option_a": "Your broker offers you a deposit bonus", "option_b": "Losses consume your margin and positions are force-closed", "option_c": "You request to increase your leverage", "option_d": "The swap fee is charged overnight", "correct_answer": "B", "explanation": "A margin call happens when account equity falls below the margin requirement. Positions are force-closed to prevent the account going negative.", "topic_slug": "leverage"},
                        {"question": "Professional traders with large accounts often use 3:1–5:1 effective leverage. Why?", "option_a": "It limits profit potential to stay humble", "option_b": "No single trade can cause catastrophic account damage", "option_c": "Regulatory requirements force it", "option_d": "High leverage is only available to retail traders", "correct_answer": "B", "explanation": "Low effective leverage means even a string of losses won't destroy the account. Capital preservation is always priority one for professionals.", "topic_slug": "leverage"},
                        {"question": "Trader A risks 1% per trade. Trader B risks 15%. After 5 consecutive losses, Trader A has lost approximately:", "option_a": "The same percentage as Trader B", "option_b": "About 5%, while Trader B has lost ~54%", "option_c": "More, because smaller sizes have less hedging", "option_d": "Both are wiped out", "correct_answer": "B", "explanation": "0.99^5 = ~95% remaining (5% loss). 0.85^5 = ~44% remaining (56% loss). Risk sizing is everything.", "topic_slug": "leverage"}
                    ]
                },
                {
                    "title": "Position Sizing Calculation",
                    "content": """\
> [!HOOK]
> Every professional trader in the world knows exactly how many lots to trade before they enter. Not roughly — exactly, to the decimal place. This single calculation, done correctly every single time, is what separates traders who survive long-term from those who blow up. It takes 30 seconds. There is no excuse not to do it.

> [!DEF]
> **Position sizing** is the calculation that determines how many lots to trade so that if your stop loss is hit, you lose exactly the amount you planned to risk — no more, no less.

### The formula

```
Lot Size = (Account Balance × Risk%) ÷ (Stop Loss pips × Pip Value per lot)
```

### Worked example

Account: $10,000 · Risk: 1% · Stop: 40 pips · Pair: EUR/USD

1. Max dollar risk: $10,000 × 1% = **$100**
2. Pip value (mini lot): $1/pip
3. Lot size: $100 ÷ (40 × $1) = **2.5 mini lots = 0.25 standard lots**

Enter 0.25 lots. If stopped out exactly at your stop, you lose $100 — exactly 1% of account.

### The stop comes first — always

The stop loss is determined by the chart, not by your budget. You find where your trade idea is technically wrong, place the stop there, then size the position so losing to that stop costs your planned risk amount.

Never work backward from "I want to risk X pips" — that produces technically meaningless stops.

> [!EXAMPLE]
> **Complete position sizing on GBP/USD:**
>
> Account: $5,000 · Risk: 1% ($50) · Entry: 1.2650 · Stop: 1.2610 (40 pips) · Target: 1.2730 (80 pips)
>
> Lot size = $50 ÷ (40 × $1) = 1.25 mini lots → round down to **0.12 lots**
>
> If stopped: 40 pips x $1.20 = $48 ≈ 1% ✓
> If target hit: 80 pips x $1.20 = $96 ≈ 2% ✓
> R:R = 1:2 ✓

> [!NGX]
> **NGX parallel:** Same logic for stock sizing. ₦500,000 account, 2% risk (₦10,000), buying ZENITH BANK with stop ₦1.50 below entry:
>
> Shares = ₦10,000 ÷ ₦1.50 = **6,666 shares maximum**
>
> This keeps your loss fixed regardless of whether the stock gaps or hits your stop exactly.

> [!MISTAKE]
> Eyeballing position size — "0.5 lots feels about right." Without calculating, a wide stop combined with a large lot size can risk 10–15% of your account on a single trade. Three losses in a row and months of gains are gone.

> [!TIP]
> Recalculate position size before every single entry. Your account balance changes after wins and losses — last week's lot size is wrong this week. Build a simple spreadsheet or phone note with the formula. The 30-second recalculation is your protection against one trade destroying your account.

> [!TAKEAWAY]
> Position sizing is the formula that connects your risk management rules to your chart analysis — get it right every trade and no single loss will ever seriously damage your account.
""",
                    "quiz": [
                        {"question": "Account: $8,000. Risk: 2%. Stop: 50 pips. EUR/USD pip value: $1/mini lot. Correct lot size?", "option_a": "0.32 lots", "option_b": "1.6 lots", "option_c": "0.016 lots", "option_d": "3.2 lots", "correct_answer": "A", "explanation": "$8,000 x 2% = $160 risk. $160 / (50 x $1) = 3.2 mini lots = 0.32 standard lots.", "topic_slug": "position_sizing"},
                        {"question": "The technically correct stop is 120 pips away. Your 2% risk allows only $80. You should:", "option_a": "Tighten the stop to 30 pips to fit your budget", "option_b": "Trade a smaller lot size so 120 pips = $80 risk", "option_c": "Skip the trade — 120-pip stop is too wide", "option_d": "Increase risk to 5% this once", "correct_answer": "B", "explanation": "Never move the stop to fit the position size. Calculate the lot size that makes the technically correct stop equal your planned dollar risk.", "topic_slug": "position_sizing"},
                        {"question": "After wins, your account grew from $5,000 to $7,500. Position size should be calculated using:", "option_a": "$5,000 (original balance)", "option_b": "$7,500 (current balance)", "option_c": "The average of both", "option_d": "Same lot sizes as before", "correct_answer": "B", "explanation": "Always use current account balance. Your risk percentage applies to what is at risk today, not what was there last month.", "topic_slug": "position_sizing"},
                        {"question": "Correct order of trade planning:", "option_a": "Choose lot size → find entry → place cheap stop", "option_b": "Find entry → place technically correct stop → calculate lot size from stop distance", "option_c": "Calculate lot size first → find entry → choose stop to match", "option_d": "Set profit target → work backward to find entry and stop", "correct_answer": "B", "explanation": "The stop must be placed where the trade idea is technically wrong. Then size the position to make that stop cost your planned risk amount.", "topic_slug": "position_sizing"},
                        {"question": "Trader risks $200 on a USD/JPY trade with a 25-pip stop (pip value ~$0.91/mini lot). Approximate lot size?", "option_a": "0.88 lots", "option_b": "8.8 lots", "option_c": "0.088 lots", "option_d": "4.4 lots", "correct_answer": "A", "explanation": "$200 / (25 x $0.91) = $200 / $22.75 ≈ 8.8 mini lots = 0.88 standard lots.", "topic_slug": "position_sizing"}
                    ]
                },
            ]
        },

        # ── MODULE 4 ──────────────────────────────────────────────────────────
        {
            "title": "Trading Sessions and Market Timing",
            "description": "When to trade, when to sit out, and why timing changes everything.",
            "lessons": [
                {
                    "title": "Trading Sessions Explained",
                    "content": """\
> [!HOOK]
> A EUR/USD chart at 3am Lagos time looks like a flatline with random twitches. That same pair at 2pm Lagos time — during the London-New York overlap — moves 80 pips in 30 minutes. Same pair. Same chart. Completely different beast. Session timing is the difference between trading in a swimming pool and trading in the ocean.

> [!DEF]
> The **Forex trading day** is divided into four main sessions — Sydney, Tokyo, London, and New York — each corresponding to when major financial centres open. Volume, volatility, and pip ranges surge during session opens and the overlaps between them.

### The four sessions (all times in WAT / Lagos time)

| Session | Opens WAT | Closes WAT | Best pairs |
|---------|-----------|------------|-----------|
| Sydney | 11pm | 8am | AUD/USD, NZD/USD |
| Tokyo | 1am | 10am | USD/JPY, AUD/JPY |
| London | 9am | 6pm | EUR/USD, GBP/USD |
| New York | 2pm | 11pm | EUR/USD, USD/CAD |

### The overlaps — where the real action is

**Tokyo–London (9am–10am WAT):** Brief but volatile, especially for GBP/JPY and EUR/GBP. Often produces the day's first major move.

**London–New York (2pm–6pm WAT):** The prime time. Both the largest financial centres trading simultaneously. EUR/USD registers its highest daily volume and biggest moves in this 4-hour window.

> [!EXAMPLE]
> **Session impact in numbers (EUR/USD):**
>
> - Tuesday 4am WAT (dead zone): average hourly range = 8 pips
> - Tuesday 3pm WAT (London-NY overlap): average hourly range = 45 pips
>
> A strategy needing 30 pips to hit target works at 3pm WAT. At 4am WAT, price rarely moves enough and the trade sits open accumulating overnight swap risk.

> [!NGX]
> **NGX trading hours:** The Nigerian Exchange runs 10am–2:30pm WAT. This overlaps directly with the start of the London session — meaning an active Lagos trader can monitor both markets in the same morning window. If you trade both NGX stocks and Forex, the 10am–2pm WAT slot is your most productive block.

> [!MISTAKE]
> Trading EUR/USD at midnight and wondering why levels are not holding and every breakout fakes out. Low-volume sessions have thin liquidity. Individual large orders can spike price through your stop and reverse immediately. This is not bad luck — it is session dynamics.

> [!TIP]
> Set your trading hours in writing and treat them as a rule. Most successful retail traders use a 2–4 hour window during peak session times rather than watching screens all day. For Lagos traders: 9am–12pm WAT and 2pm–5pm WAT cover both the London open and the London-NY overlap.

> [!TAKEAWAY]
> Trade during high-volume sessions — especially the London-New York overlap from 2pm–6pm WAT — and your strategy's performance will dramatically improve compared to trading at random hours.
""",
                    "quiz": [
                        {"question": "Which window produces the highest volume and biggest moves for EUR/USD?", "option_a": "Sydney session", "option_b": "Tokyo session", "option_c": "London session only", "option_d": "London-New York overlap (2pm-6pm WAT)", "correct_answer": "D", "explanation": "The London-NY overlap combines the two largest financial centres. EUR/USD volume peaks in this 4-hour window daily.", "topic_slug": "trading_sessions"},
                        {"question": "In WAT (Lagos time), the London-New York overlap runs approximately:", "option_a": "9am-1pm", "option_b": "2pm-6pm", "option_c": "6pm-10pm", "option_d": "11pm-3am", "correct_answer": "B", "explanation": "London opens 9am WAT, New York 2pm WAT, London closes 6pm WAT. Overlap = 2pm-6pm WAT.", "topic_slug": "trading_sessions"},
                        {"question": "EUR/USD is making choppy small moves with frequent fake breakouts. Most likely cause?", "option_a": "Your strategy has stopped working", "option_b": "You are trading during a low-volume session", "option_c": "The Euro is fundamentally weak", "option_d": "Your data feed is delayed", "correct_answer": "B", "explanation": "Choppy, low-range, false-breakout behaviour is the hallmark of low-volume session windows. The fix is timing, not strategy.", "topic_slug": "trading_sessions"},
                        {"question": "A Lagos trader wants to trade USD/JPY. The best session window is:", "option_a": "London open (9am WAT)", "option_b": "Tokyo session (1am-10am WAT)", "option_c": "New York close (8pm-11pm WAT)", "option_d": "Sydney open (11pm WAT)", "correct_answer": "B", "explanation": "USD/JPY is most active during the Tokyo session when Japan's financial markets are open and driving yen direction.", "topic_slug": "trading_sessions"},
                        {"question": "Why do EUR/USD spreads widen during the Sydney-only session?", "option_a": "Australian banks charge extra for European pairs", "option_b": "Low liquidity means fewer competing orders, so brokers widen to manage risk", "option_c": "EUR/USD is not available during Sydney", "option_d": "The ECB restricts trading during off-hours", "correct_answer": "B", "explanation": "Low volume = fewer market makers competing = wider spreads. Brokers protect themselves by widening during thin conditions.", "topic_slug": "trading_sessions"}
                    ]
                },
                {
                    "title": "Best Times to Trade",
                    "content": """\
> [!HOOK]
> A surgeon does not schedule complex operations at 3am. A Lagos market trader does not set up their stall at midnight. Timing is a force multiplier on whatever skill you have. Two identical traders with identical strategies — one trading at the right time, one trading at random — will produce completely different results over a year.

> [!DEF]
> **Optimal trading times** are windows when volume is high, spreads are tight, and price moves with enough momentum to reach targets before reversing — not the hours when you happen to be free.

### The tier system for Forex timing

**Tier 1 — Highest probability (trade your primary strategy here)**
- London open: 9am–12pm WAT
- London-New York overlap: 2pm–6pm WAT

**Tier 2 — Moderate (selective trades with proven setups only)**
- New York session: 2pm–9pm WAT
- Tokyo-London handoff: 8am–10am WAT

**Tier 3 — Avoid unless you have a specialist strategy**
- Sydney session only: 11pm–1am WAT
- Early Tokyo: 1am–4am WAT
- Friday close and weekend: 9pm WAT onward

### News events — the wildcard

High-impact news (NFP, Fed rate decisions, CBN MPC) can override all session rules. Spreads spike, slippage is extreme, price can move 100+ pips in seconds before reversing. Unless you have a specific news trading strategy: **close positions or step aside 15 minutes before and after.**

> [!EXAMPLE]
> **Sample Lagos-based trader schedule:**
>
> | Time (WAT) | Activity |
> |-----------|----------|
> | 8:30am | Review overnight moves, mark key levels |
> | 9:00am | London open — watch for setup triggers |
> | 11:00am | Step away if no quality setup formed |
> | 1:45pm | Pre-New York prep |
> | 2:00pm | London-NY overlap — primary trading window |
> | 5:30pm | Close day trades before London close |
> | 6:30pm | Journal, plan next day |
>
> Total screen time: ~4 hours. Outside this schedule: no trades.

> [!NGX]
> **NGX timing:** The exchange closes 2:30pm WAT. Most active windows: 10am–12pm (open momentum) and 1:30pm–2:30pm (end-of-day institutional positioning). These are the Tier 1 windows for NGX stock traders. The rest of the day is noise for most retail participants.

> [!MISTAKE]
> Trading every hour the market is open because opportunity might appear. The Forex market is technically open 120 hours per week. The best setups appear in maybe 10–15 of those hours. Sitting in charts during dead zones produces boredom trades — low-probability entries taken from impatience, not analysis.

> [!TIP]
> Use an economic calendar (Forex Factory or Investing.com) every morning. Mark that day's high-impact events. Block 15-minute no-trade zones around them. This single habit eliminates most of the news-slippage losses beginners suffer.

> [!TAKEAWAY]
> The best trading schedule focuses on 2–4 hours per day during the London open and London-New York overlap, with a strict no-trade rule around high-impact news events.
""",
                    "quiz": [
                        {"question": "NFP is released at 3:30pm WAT. You have an open EUR/USD position. Wisest action 10 minutes before?", "option_a": "Add to position to capture the move", "option_b": "Close or hedge — news causes unpredictable slippage", "option_c": "Widen the stop to ride volatility", "option_d": "Do nothing — NFP rarely affects EUR/USD", "correct_answer": "B", "explanation": "NFP is the single biggest regular Forex news event. Spreads spike to 10+ pips and price can reverse 100+ pips instantly. Being flat is the safest position.", "topic_slug": "trading_timing"},
                        {"question": "A Lagos trader can only trade 7pm-10pm WAT. Their best option is:", "option_a": "Trade EUR/USD aggressively — it is always active", "option_b": "Accept they cannot trade Forex", "option_c": "Swing trade — capturing multi-day moves that do not require real-time session monitoring", "option_d": "Trade USD/JPY in the late Tokyo session", "correct_answer": "C", "explanation": "If peak sessions are unavailable, shift to longer timeframes (daily/weekly charts, swing trades). Entries and management do not need real-time session monitoring.", "topic_slug": "trading_timing"},
                        {"question": "Why is the first 15 minutes of London open (9am WAT) significant?", "option_a": "Spreads are tightest at exactly 9am", "option_b": "European banks inject liquidity and often establish the day's directional bias for EUR/GBP pairs", "option_c": "It overlaps with Sydney close, creating extra volume", "option_d": "CBN releases daily rate data at 9am WAT", "correct_answer": "B", "explanation": "The London open brings European institutional order flow online. The initial move often establishes the day's direction and creates the first high-probability setup.", "topic_slug": "trading_timing"},
                        {"question": "A trader consistently loses trading EUR/USD from 11pm-2am WAT. Most likely diagnostic cause?", "option_a": "Their analysis is fundamentally flawed", "option_b": "They are trading the lowest-volume window — wide spreads and false breakouts are expected there", "option_c": "They should switch to GBP/USD at that hour", "option_d": "Their broker is widening spreads maliciously", "correct_answer": "B", "explanation": "11pm-2am WAT is Sydney session and early Tokyo — the quietest window for EUR pairs. False breakouts and wide spreads in this period are session characteristics, not strategy failure.", "topic_slug": "trading_timing"},
                        {"question": "The primary reason professional traders limit active trading to 2-4 hours per day:", "option_a": "Regulatory restrictions limit trading hours", "option_b": "More screen time causes decision fatigue and results in impulsive low-probability trades", "option_c": "Brokers charge higher fees after 4 hours", "option_d": "Indicators are less accurate outside this window", "correct_answer": "B", "explanation": "Decision fatigue is well-documented. After hours at charts, traders take bad setups from boredom or FOMO. Strict hour limits protect psychological capital as much as financial capital.", "topic_slug": "trading_timing"}
                    ]
                },
            ]
        },

        # ── MODULE 5 ──────────────────────────────────────────────────────────
        {
            "title": "Basic Risk Management",
            "description": "The rules that keep you in the game — more important than any entry strategy.",
            "lessons": [
                {
                    "title": "The 1-2% Rule",
                    "content": """\
> [!HOOK]
> Nick Leeson brought down Barings Bank — founded in 1762, one of Britain's oldest institutions — by repeatedly adding to losing positions with no stop loss, trying to recover losses. He did not lack skill or intelligence. He lacked the 1% rule. It sounds boring. It is the most important rule in trading.

> [!DEF]
> The **1-2% rule** states that no single trade should risk more than 1–2% of your total account balance. This rule means you can be wrong 50 times in a row and still have over 60% of your account intact — enough to continue trading and recover.

### The maths of survival

| Risk per trade | After 10 losses | Remaining |
|----------------|-----------------|-----------|
| 1% | (0.99)^10 | **90.4%** |
| 2% | (0.98)^10 | **81.7%** |
| 5% | (0.95)^10 | **59.9%** |
| 10% | (0.90)^10 | **34.9%** |
| 20% | (0.80)^10 | **10.7%** |

A 20% risk per trade does not require bad luck to destroy an account — it requires a completely ordinary losing run.

### Why 1% feels small (and why that feeling is wrong)

At 1% risk on a $5,000 account you risk $50 per trade. A 1:2 R:R wins $100. Five consecutive winners grows the account meaningfully. You can take 50 trades exploring a strategy without blowing up. Your psychology stays stable because no single loss hurts.

At 10% risk, three losses cost you 27% of your account. Psychology breaks down, revenge trades follow, the spiral begins.

> [!EXAMPLE]
> **Two traders, $10,000 each, same 5-loss/5-win sequence (1:2 R:R):**
>
> **Trader A (1% risk):** 5 losses = −$500. 5 wins on growing balance ≈ +$1,050. Net: **+$550 profit.**
> **Trader B (10% risk):** 5 losses = account down to $5,905. The emotional damage after losing $4,095 leads to revenge trades before the wins arrive. Account further damaged.
>
> Same sequence. Radically different outcomes because of risk size.

> [!NGX]
> **NGX parallel:** A disciplined NGX investor with ₦1,000,000 risks no more than ₦10,000–₦20,000 per stock position. When OKOMU OIL gaps down on bad earnings, the loss is manageable — not account-ending. This discipline allows surviving the inevitable bad runs that hit every investor.

> [!MISTAKE]
> "I will use 5% just until I build the account up, then lower it." This is the most common and most fatal beginner plan. The high-risk phase comes when you have the least experience and the least proven strategy — exactly when you need the lowest risk, not the highest.

> [!TIP]
> During a drawdown (3+ consecutive losses), reduce risk to 0.5% until you have 3 winning trades at the lower size. This circuit breaker prevents the psychological spiral that turns a normal losing streak into an account-destroying event.

> [!TAKEAWAY]
> Risk 1–2% per trade, always — because surviving long enough to become profitable requires protecting the account through every losing streak your strategy will inevitably produce.
""",
                    "quiz": [
                        {"question": "Account: $6,000. Maximum risk per trade at 1%?", "option_a": "$600", "option_b": "$60", "option_c": "$6", "option_d": "$6,000", "correct_answer": "B", "explanation": "$6,000 x 1% = $60 maximum risk per trade.", "topic_slug": "risk_management"},
                        {"question": "Trader risks 10% per trade. After 7 consecutive losses, account is approximately:", "option_a": "30% of original", "option_b": "50% of original", "option_c": "48% of original", "option_d": "70% of original", "correct_answer": "C", "explanation": "(0.90)^7 = 0.478 = approximately 48% remaining. Now needs 108% return just to recover to starting balance.", "topic_slug": "risk_management"},
                        {"question": "A 1:2 R:R strategy with 1% risk is viable at a 40% win rate because:", "option_a": "It is not — 40% win rate is always unprofitable", "option_b": "Expectancy = (0.4 x 2%) - (0.6 x 1%) = +0.2% per trade", "option_c": "1:2 R:R guarantees reaching target 60% of the time", "option_d": "Low risk percentage automatically improves win rate", "correct_answer": "B", "explanation": "Wins average 2% return. Losses average 1%. Positive expectancy means the strategy makes money over time despite winning less than half the time.", "topic_slug": "risk_management"},
                        {"question": "3 consecutive losses on a strategy with 55% historical win rate. Correct response:", "option_a": "Double size to recover faster", "option_b": "Switch strategy — it has stopped working", "option_c": "Continue with same risk — 3 losses is statistically normal even at 55%", "option_d": "Stop trading for 2 weeks", "correct_answer": "C", "explanation": "Even a 55% win rate strategy will hit 3 consecutive losses regularly. That is expected probability. Staying disciplined, not changing strategy or increasing risk, is the correct response.", "topic_slug": "risk_management"},
                        {"question": "What is a 'circuit breaker' rule in risk management?", "option_a": "A tool that opens trades when volatility drops", "option_b": "A pre-defined drawdown trigger that forces a pause or risk reduction until performance recovers", "option_c": "A broker safety net that stops leverage exceeding 100:1", "option_d": "An indicator that identifies trend reversals", "correct_answer": "B", "explanation": "A circuit breaker is a self-imposed rule: e.g. 'If I lose 5% in one week, I trade half size until I have 5 winning trades.' It prevents emotional spirals from compounding losses.", "topic_slug": "risk_management"}
                    ]
                },
                {
                    "title": "Stop Loss and Take Profit",
                    "content": """\
> [!HOOK]
> Ask any blown-up trader what destroyed their account and you will get one of two answers: "I moved my stop loss when it was about to get hit" or "I never used one." There is no third answer. The stop loss is a contract you make with yourself before entering — proof that you have decided in advance exactly how much you are willing to lose. Break that contract once and you are no longer trading. You are gambling.

> [!DEF]
> A **stop loss** is a pre-set price level that automatically closes your trade if price moves against you, limiting your loss to the amount you planned. A **take profit** closes your trade when price reaches your target. Together they define the risk-reward ratio of every trade before you enter.

### Where to place your stop loss

Stops must be placed at technically meaningful levels — not distances that fit your budget.

1. **Below/above support or resistance** — if buying, stop below the support you need to hold. If that level breaks, the trade idea is wrong.
2. **Below/above a recent swing high/low** — stops behind structure protect against normal movement while invalidating the trade if structure fails.
3. **ATR-based stops** — use the Average True Range at 1.5× for pairs with erratic behaviour.

### Setting take profit

Take profit should be at the next significant resistance (for buys) or support (for sells). The key ratio:

- Minimum: 1:1.5 R:R
- Professional standard: 1:2 to 1:3 R:R

> [!EXAMPLE]
> **EUR/USD buy setup at key support:**
>
> Entry: 1.0850 · Stop: 1.0810 (40 pips below support) · Target: 1.0930 (80 pips, next resistance)
> R:R = 1:2
>
> Even if this setup wins only 45% of the time:
> Expectancy = (0.45 x 80) - (0.55 x 40) = 36 - 22 = **+14 pips per trade average**
> Over 100 trades: +1,400 pips expected profit.

> [!NGX]
> **NGX parallel:** Buying GTCO at ₦45.00 with target ₦50.00 and stop ₦43.00:
> Risk = ₦2, Reward = ₦5, R:R = 1:2.5.
> Shares from risk budget: risking ₦15,000 → 7,500 shares (₦15,000 / ₦2 per share).
> Stop and target set before execution, never after.

> [!MISTAKE]
> Moving the stop loss further away when price approaches it "to give the trade more room." Once you enter a trade, the stop is sacred. Moving it against your position is how a planned 30-pip loss becomes a 150-pip loss. Write this rule: I will never move a stop loss against my position. Full stop.

> [!TIP]
> Set stop loss and take profit as hard orders in your platform the moment you enter the trade. Not mental notes — real orders. Hardware stops survive internet outages, power cuts, and the critical moment when you are not at your screen. In Nigeria, with variable power supply, this is not optional advice.

> [!TAKEAWAY]
> Set your stop at the level where your trade idea is proven wrong, your take profit at the next meaningful technical level, and never touch either order once the trade is live.
""",
                    "quiz": [
                        {"question": "Most technically sound stop loss placement when buying EUR/USD:", "option_a": "50 pips below entry — always fixed distance", "option_b": "Below the nearest support level that, if broken, proves the trade idea wrong", "option_c": "At a level that risks exactly $50 regardless of structure", "option_d": "Above the last resistance level", "correct_answer": "B", "explanation": "Stops must be placed at technically meaningful levels. A fixed-pip stop ignores structure and gets hit by normal price movement.", "topic_slug": "stop_loss"},
                        {"question": "EUR/USD entry: 1.1200, Stop: 1.1160, Target: 1.1280. Risk-reward ratio?", "option_a": "1:1", "option_b": "1:2", "option_c": "2:1", "option_d": "1:3", "correct_answer": "B", "explanation": "Risk = 40 pips (1.1200-1.1160). Reward = 80 pips (1.1280-1.1200). R:R = 40:80 = 1:2.", "topic_slug": "stop_loss"},
                        {"question": "EUR/USD is approaching your stop loss. News is about to release. You believe it will recover. You should:", "option_a": "Move stop lower to avoid getting hit", "option_b": "Close manually before news", "option_c": "Add to position — double down before news", "option_d": "Leave the stop exactly where it is — it was placed for a technical reason", "correct_answer": "D", "explanation": "If the stop was placed correctly, it stays. Moving it violates your risk management plan. If uncertain about news, the correct action was not entering before it.", "topic_slug": "stop_loss"},
                        {"question": "Strategy wins 50% with 1:1.5 R:R. Is it profitable?", "option_a": "No — need over 50% win rate to profit", "option_b": "Yes — expectancy = (0.5 x 1.5R) - (0.5 x 1R) = +0.25R per trade", "option_c": "Only if spreads are zero", "option_d": "It breaks exactly even", "correct_answer": "B", "explanation": "(0.5 x 1.5) - (0.5 x 1.0) = 0.75 - 0.50 = +0.25R per trade. Profitable — wins do not need to exceed 50% when they are larger than losses.", "topic_slug": "stop_loss"},
                        {"question": "Why must stop loss orders be placed as real broker orders, not mental stops?", "option_a": "Mental stops allow more flexible exits", "option_b": "Broker orders execute during power cuts, internet outages, or when you are away from the screen", "option_c": "Broker orders always fill at better prices", "option_d": "Mental stops are not allowed in Nigeria", "correct_answer": "B", "explanation": "Mental stops depend on you being present, alert, and disciplined. Real orders execute regardless. In markets with infrastructure challenges, hard orders are essential.", "topic_slug": "stop_loss"}
                    ]
                },
            ]
        },

        # ── MODULE 6 ──────────────────────────────────────────────────────────
        {
            "title": "Introduction to Trading Charts",
            "description": "Learning to read a chart — the visual language of every price ever traded.",
            "lessons": [
                {
                    "title": "Candlestick Charts Explained",
                    "content": """\
> [!HOOK]
> In 18th-century Japan, rice merchants developed a method of recording price movements that looked like candles. Three centuries later, those same candles are used by every serious trader on the planet, on every financial market, to decode the real story of supply and demand behind every price move. Master candlesticks and you can read any market in the world.

> [!DEF]
> A **candlestick** represents price action over a specific time period — showing open, high, low, and close (OHLC) in a single visual unit. The body shows the open-to-close range. The wicks (shadows) show the extreme highs and lows reached during that period.

### Anatomy of a candlestick

**Bullish candle (green):** Close HIGHER than open.
- Body stretches from open (bottom) to close (top)
- Upper wick = highest price reached
- Lower wick = lowest price reached

**Bearish candle (red):** Close LOWER than open.
- Body stretches from open (top) to close (bottom)

### What the body and wicks tell you

**Long body** = Strong conviction. Buyers or sellers dominated the entire session.

**Short body** = Indecision. Balanced battle between buyers and sellers.

**Long upper wick** = Buyers pushed price high but sellers rejected the move by close. Bearish pressure.

**Long lower wick** = Sellers pushed price down but buyers stepped in strongly. Bullish pressure.

**Doji** = Open and close nearly identical. Maximum indecision. Signals potential reversal when appearing at key levels.

> [!EXAMPLE]
> **Reading a candle's story:**
>
> EUR/USD has been rising 3 hours. A candle appears with a small green body and a long upper wick (price reached 40 pips above open but closed near open).
>
> What this tells you: buyers tried to push higher, sellers rejected the move aggressively. Close was almost unchanged despite the push. This is a warning that the uptrend may be exhausting — experienced traders tighten stops or prepare to exit.

> [!NGX]
> **NGX parallel:** Read any MTNN daily chart. On high-volume earnings days you see large-bodied candles — pure directional conviction. On pre-results uncertainty days you see dojis and small bodies — the market genuinely does not know which way to go. The candles communicate the crowd's emotion in real time, regardless of which market you are watching.

> [!MISTAKE]
> Reading candles in isolation and treating them as guaranteed signals. A hammer (long lower wick, small body) at a random chart location means little. The same hammer at a major support level after a sustained downtrend is a high-probability reversal signal. Context is everything — location plus candle pattern, never candle alone.

> [!TIP]
> Practice "candle by candle" analysis: cover all but the last 3 candles on your chart. Based on those 3, predict what the next one will look like — then reveal it. This builds pattern intuition faster than studying static diagrams ever will.

> [!TAKEAWAY]
> Every candlestick tells the story of the battle between buyers and sellers — the body shows who won, the wicks show how hard both sides fought, and the context determines whether that story matters.
""",
                    "quiz": [
                        {"question": "A red candle has a very long lower wick and a small body at the top. This tells you:", "option_a": "Sellers dominated the entire session", "option_b": "Sellers pushed price far down but buyers strongly rejected the lows and closed near the open", "option_c": "Price gapped down then recovered", "option_d": "Only the close matters — the wick is irrelevant", "correct_answer": "B", "explanation": "A long lower wick on a bearish candle means buyers stepped in aggressively at the lows. Despite closing red, the buying rejection is a bullish signal for the next candle.", "topic_slug": "candlesticks"},
                        {"question": "What is a Doji candlestick?", "option_a": "A large green candle signalling strong buying", "option_b": "A candle where open and close are nearly identical — indicating indecision", "option_c": "A candle that appears only during news events", "option_d": "A candle where price gaps and then fills", "correct_answer": "B", "explanation": "A Doji has almost identical open and close prices, creating a very thin cross-shaped body. It signals indecision — buyers and sellers are evenly matched.", "topic_slug": "candlesticks"},
                        {"question": "After three consecutive large green candles, the fourth has a tiny body and long upper wick. This suggests:", "option_a": "Strong continuation — buy immediately", "option_b": "Bullish momentum may be exhausting — sellers rejected the highs aggressively", "option_c": "A doji always means price will fall exactly the same distance it rose", "option_d": "The news was good — candle size does not matter here", "correct_answer": "B", "explanation": "After a bullish run, a small body with a long upper wick tells you sellers pushed back hard at the highs. Momentum is slowing — a warning to protect profits.", "topic_slug": "candlesticks"},
                        {"question": "EUR/USD 1-hour candle: Open 1.0800, High 1.0860, Low 1.0790, Close 1.0850. Which statement is correct?", "option_a": "It is a bearish candle — the high was hit before the close", "option_b": "It is a bullish candle with a 10-pip upper wick and 10-pip lower wick", "option_c": "It is a doji — open and close are similar", "option_d": "It is a bearish engulfing", "correct_answer": "B", "explanation": "Close (1.0850) > Open (1.0800) = bullish. Upper wick = 1.0860 - 1.0850 = 10 pips. Lower wick = 1.0800 - 1.0790 = 10 pips.", "topic_slug": "candlesticks"},
                        {"question": "A trader sees a hammer candle and immediately buys. Why is this potentially wrong?", "option_a": "Hammer candles always signal continuation, not reversal", "option_b": "The signal has no context — a hammer at a random location is not the same as a hammer at key support after a downtrend", "option_c": "Hammers only work on daily charts", "option_d": "Hammers only work on EUR/USD", "correct_answer": "B", "explanation": "Candle patterns only have significance in context. A hammer at critical support after a downtrend is high-probability. The same pattern mid-range is noise.", "topic_slug": "candlesticks"}
                    ]
                },
                {
                    "title": "Support and Resistance Basics",
                    "content": """\
> [!HOOK]
> Imagine a Lagos market where rice has traded near ₦50,000 a bag for months. Every time it creeps toward ₦55,000, buyers disappear — too expensive. Every time it dips to ₦45,000, a queue forms — everyone senses a bargain. Those price points where buyers reliably appear and sellers reliably appear are support and resistance. They exist in every market on earth, because human psychology is universal.

> [!DEF]
> **Support** is a price level where buying interest consistently overcomes selling pressure, causing price to bounce upward. **Resistance** is where selling interest consistently overcomes buying, causing price to reverse downward. These are the most fundamental and powerful concepts in all of technical analysis.

### Why they work

They work because of **memory**. Traders who bought at a level and watched it fall (trapped buyers) want to exit at breakeven when price returns — creating selling pressure. Traders who missed a move want a second chance — creating buying at pullback levels. These crowd behaviours repeat reliably.

### How to identify them

1. Use a higher timeframe (daily or 4-hour) to mark major levels first
2. Look for areas where price has reversed multiple times — two tests = weak, three or more = strong
3. Mark zones, not precise lines — support is not at exactly 1.0850, it is the 1.0840–1.0860 zone
4. Recognise role reversal: broken resistance becomes new support. Broken support becomes new resistance

> [!EXAMPLE]
> **Role reversal trade:**
>
> EUR/USD is resisted at 1.0900 (rejected twice). Price breaks above 1.0900 on heavy volume and closes at 1.0940.
> On the next day, price pulls back to 1.0900.
>
> Former resistance = now support.
> Entry: 1.0905 · Stop: 1.0860 (below zone) · Target: 1.0980 (next resistance)
> Risk: 45 pips · Reward: 75 pips · R:R: 1:1.67

> [!NGX]
> **NGX parallel:** DANGCEM spent months building resistance at ₦600. When the stock finally broke above ₦600 on an earnings beat and held there for a week, ₦600 became support. Buying on the first pullback to ₦600 — with a stop below ₦590 — was a textbook role-reversal setup on the Nigerian Exchange.

> [!MISTAKE]
> Drawing so many lines that everything looks like support or resistance. A chart with 20 levels is useless — every price is "near" a level. Start with the 3–4 most obvious, cleanest levels where price has reversed convincingly multiple times. Fewer and stronger always beats many and weak.

> [!TIP]
> The more times a level is tested and holds, the stronger it is — but also the more explosive the eventual breakout will be. A support tested 5 times has accumulated stop orders just below it. When it finally breaks, the cascade of those stops creates a fast, powerful move. This is the engine of breakout trading.

> [!TAKEAWAY]
> Support and resistance are price zones where crowd psychology reliably repeats — master identifying these levels and you will know where the highest-probability entries and exits are before price even arrives.
""",
                    "quiz": [
                        {"question": "EUR/USD has bounced off 1.0850 four times in two weeks. This level is:", "option_a": "Weak — too many tests means a break is imminent", "option_b": "Strong — multiple tests that held confirm genuine buying interest", "option_c": "Resistance — a level tested repeatedly becomes resistance", "option_d": "Neutral — four tests has no trading significance", "correct_answer": "B", "explanation": "Multiple tests that hold confirm real buying interest. Three or more clean bounces from the same level = strong, tradeable support.", "topic_slug": "support_resistance"},
                        {"question": "EUR/USD was resisted at 1.1050 for three weeks. Price breaks above on heavy volume and closes at 1.1090. On a pullback to 1.1050, you would expect:", "option_a": "Price to continue falling easily below 1.1050", "option_b": "Former resistance at 1.1050 to now act as support", "option_c": "The level to be irrelevant after such a large break", "option_d": "Increased resistance — it has been tested more times", "correct_answer": "B", "explanation": "Role reversal: resistance broken convincingly becomes new support. Traders who missed the break wait at the breakout level to enter on the pullback.", "topic_slug": "support_resistance"},
                        {"question": "A trader marks support at exactly 1.2000. Price dips to 1.1995 before reversing strongly. The trader says the level failed. This thinking is:", "option_a": "Correct — a level must hold exactly or it is broken", "option_b": "Incorrect — support levels are zones. A 5-pip undershoot before a strong reversal validates the zone", "option_c": "Partially correct — the level is weakened but not broken", "option_d": "Irrelevant — GBP/USD requires different analysis", "correct_answer": "B", "explanation": "Support and resistance are zones, not laser lines. Price regularly tests just below or above a level before reversing — this is normal price behaviour.", "topic_slug": "support_resistance"},
                        {"question": "Highest quality support level for a buy entry:", "option_a": "A level touched only once, briefly", "option_b": "A level where price has been rejected three times with visible bullish candles each time", "option_c": "A round number like 1.2000 regardless of price history", "option_d": "Any level below the current price", "correct_answer": "B", "explanation": "Multiple tests with rejection candles at each touch confirm real buying interest. This is the hallmark of a strong, tradeable support level.", "topic_slug": "support_resistance"},
                        {"question": "How many levels is most useful on a 4-hour chart?", "option_a": "As many as possible", "option_b": "Just one — the most important level only", "option_c": "3–5 key levels — enough to define major structure without clutter", "option_d": "10–15 to cover all potential reversals", "correct_answer": "C", "explanation": "3–5 major levels gives clear structure. Too many creates analysis paralysis — price always seems near a level, making entries meaningless.", "topic_slug": "support_resistance"}
                    ]
                },
            ]
        },

    ]  # end Beginner modules
},  # end Beginner level

# ══════════════════════════════════════════════════════════════════════════════
# LEVEL 2 — INTERMEDIATE
# ══════════════════════════════════════════════════════════════════════════════
{
    "level_name": "Intermediate",
    "description": "You know how the market works. Now learn how to read it. Trends, chart patterns, indicators, and the Fibonacci tool used by institutional traders worldwide — plus how to combine them into high-confidence setups.",
    "modules": [

        # ── MODULE 1 ──────────────────────────────────────────────────────────
        {
            "title": "Trend Analysis",
            "description": "Reading the market's direction — the single skill that separates profitable traders from everyone else.",
            "lessons": [
                {
                    "title": "Identifying Trends",
                    "content": """\
> [!HOOK]
> Jesse Livermore, the most famous speculator in Wall Street history, had one rule that explained his entire fortune: "Never fight the tape." The tape was the ticker — the direction the market was already moving. He did not care about predicting where price would go. He cared about knowing what direction price was already travelling and riding it. That was his entire edge.

> [!DEF]
> A **trend** is a sustained directional bias in price — a series of higher highs and higher lows (uptrend) or lower highs and lower lows (downtrend). Trending markets provide the most reliable and highest-probability trading setups available.

### The structure of a trend

**Uptrend — the staircase up:**
Price makes a new high (Higher High = HH), pulls back to a higher point than the previous pullback (Higher Low = HL), then makes a new HH again. The HL series is your confirmation that buyers are in control — each pullback finds support at a higher level.

**Downtrend — the staircase down:**
Price makes a new low (Lower Low = LL), bounces to a lower level than the previous bounce (Lower High = LH), then breaks to a new LL. LH series confirms sellers are in control.

**Sideways / Ranging:**
Price oscillates between clear support and resistance without consistent new highs or lows. Different trading rules apply.

### Trend entry logic

The lowest-risk entry in a trend is not at the high or low — it is on the **pullback**.

- Uptrend: wait for price to pull back toward a Higher Low, show bullish reversal signals, then buy.
- Downtrend: wait for price to bounce toward a Lower High, show bearish reversal signals, then sell.

> [!EXAMPLE]
> **Uptrend pullback entry:**
>
> EUR/USD uptrend: HH1 at 1.0950, HL1 at 1.0880, HH2 at 1.1020.
> Price pulls back toward expected HL2 (~1.0930–1.0950).
> Bullish engulfing forms at 1.0940.
>
> Entry: 1.0942 · Stop: 1.0905 (below HL zone) · Target: 1.1020 (previous HH)
> Risk: 37 pips · Reward: 78 pips · R:R: 1:2.1

> [!NGX]
> **NGX parallel:** ZENITH BANK spent Q1 2024 in a clear uptrend — each pullback found buyers at higher levels. Traders who waited for pullbacks to the higher-low zones (not chasing new highs) consistently entered with 1:2+ R:R setups. The same structure repeats across every NGX blue chip in trending conditions.

> [!MISTAKE]
> Trying to find a trend on a single timeframe. A 5-minute chart can look like a strong uptrend while the 4-hour is clearly in a downtrend. Higher timeframe trend direction must be established first — it sets the bias. If the daily trend is down, look for sells on lower timeframes, not buys.

> [!TIP]
> A simple rule to define trend: **two Higher Lows in a row = uptrend confirmed. Two Lower Highs in a row = downtrend confirmed.** No indicators needed. Just mark HH/HL or LH/LL on your chart and let structure speak for itself.

> [!TAKEAWAY]
> Trading with the trend means waiting for pullbacks to higher lows (uptrend) or lower highs (downtrend) — entering where the trend's next push is most likely to begin with the best risk-reward available.
""",
                    "quiz": [
                        {"question": "Price sequence: 1.0800 → 1.0900 → 1.0850 → 1.0970 → 1.0920 → 1.1040. What trend is this?", "option_a": "Downtrend — price oscillates", "option_b": "Uptrend — each high is higher and each pullback is higher than the previous", "option_c": "Sideways range", "option_d": "Mixed — unidentifiable", "correct_answer": "B", "explanation": "HH1=1.0900, HL1=1.0850, HH2=1.0970, HL2=1.0920, HH3=1.1040. Each high is higher. Each pullback is higher. Classic uptrend structure.", "topic_slug": "trend_analysis"},
                        {"question": "In a confirmed uptrend, the highest probability entry is:", "option_a": "Buying at the highest high after a breakout", "option_b": "Buying on a pullback to the Higher Low zone when reversal signals appear", "option_c": "Selling the overextension at the top", "option_d": "Waiting for the trend to end before entering", "correct_answer": "B", "explanation": "Pullback entries get you in at the start of the next impulse leg, closest to the stop (HL), giving the best R:R with trend momentum behind you.", "topic_slug": "trend_analysis"},
                        {"question": "Daily chart: GBP/USD in clear downtrend. 1-hour chart: bullish setup visible. You should:", "option_a": "Take the 1-hour buy — it has a good pattern", "option_b": "Ignore the 1-hour buy. Look for 1-hour sell setups aligned with the daily downtrend", "option_c": "The higher timeframe trend does not affect lower timeframe trades", "option_d": "Wait for the daily trend to reverse before trading", "correct_answer": "B", "explanation": "Higher timeframe trend sets the bias. A 1-hour buy fighting a daily downtrend is lower probability. Look for sells aligned with the dominant trend.", "topic_slug": "trend_analysis"},
                        {"question": "Price makes a Higher High but the next pullback drops below the previous Higher Low. This signals:", "option_a": "A trend continuation signal", "option_b": "A break of structure — uptrend structure has failed", "option_c": "A normal pullback — Higher Lows need not hold exactly", "option_d": "A double bottom buy signal", "correct_answer": "B", "explanation": "Breaking the previous Higher Low invalidates the uptrend structure. This is a structural break — often the first sign of a trend reversal.", "topic_slug": "trend_analysis"},
                        {"question": "How to identify a trend without indicators?", "option_a": "You need RSI minimum to confirm direction", "option_b": "Two or more Higher Highs and Higher Lows (uptrend) or Lower Lows and Lower Highs (downtrend) from raw price structure alone", "option_c": "A trend can only be confirmed after it ends", "option_d": "Price action alone cannot identify trends", "correct_answer": "B", "explanation": "Trend is defined by price structure: HH+HL series = uptrend, LH+LL series = downtrend. No indicators needed — they only confirm what structure already shows.", "topic_slug": "trend_analysis"}
                    ]
                },
                {
                    "title": "Multiple Timeframe Analysis",
                    "content": """\
> [!HOOK]
> Stand one metre from a painting and you see a few blurry brushstrokes. Step back to five metres and a face emerges. Step to twenty metres and the full scene appears. The painting has not changed — only your perspective has. That is exactly how timeframes work. The same price action looks completely different depending on which timeframe you are watching. Traders who understand all three levels simultaneously have an enormous edge over those watching only one.

> [!DEF]
> **Multiple Timeframe Analysis (MTFA)** is the practice of analysing the same pair across at least three timeframes — high (trend), medium (setup), and low (entry) — so your trades align with the big-picture direction and maximise probability.

### The three-timeframe hierarchy

**Higher Timeframe (HTF) — the map:**
Daily or 4-hour chart. Determine trend direction and mark major support/resistance. This is your bias. You do not enter here.

**Intermediate Timeframe — the setup:**
1-hour or 4-hour chart. Identify the pattern forming within the HTF trend — the pullback, the consolidation, the potential entry zone.

**Lower Timeframe (LTF) — the trigger:**
15-minute or 5-minute chart. Time your precise entry — finding the candle pattern that triggers the position with the tightest possible stop.

### The process: top-down

1. Daily: EUR/USD uptrend confirmed. Key support zone: 1.0880–1.0900.
2. 4H: Price has pulled back to 1.0890 zone. Bullish pin bar forming at support.
3. 1H: Smaller bullish engulfing candle within the 4H pin bar body.
4. Enter: Buy at 1.0895. Stop below 1H structure. Target: 1.0980 (HTF resistance).

> [!EXAMPLE]
> **MTFA trade on GBP/USD:**
>
> Daily: Clear uptrend. Support zone at 1.2600–1.2620.
> 4H: Price at support zone. Bullish hammer forming.
> 1H: Small bullish engulfing inside the hammer at 1.2615.
>
> Entry: 1.2618 · Stop: 1.2590 (below 1H structure) · Target: 1.2720 (daily resistance)
> Risk: 28 pips · Reward: 102 pips · **R:R: 1:3.6**
>
> MTFA compressed the stop to 28 pips while allowing a 102-pip target — because entry precision (1H) combined with target logic (daily chart).

> [!NGX]
> **NGX parallel:** Analysing GTCO: weekly chart shows uptrend and key level at ₦50. Daily shows a pullback forming a pin bar at ₦50 zone. 30-min shows a bullish candle closing above ₦50.50. That 30-min candle is the entry trigger. Stop below ₦49.50, target ₦55 (weekly resistance). This is MTFA applied directly to NGX equity trading.

> [!MISTAKE]
> Using all three timeframes for information rather than having a clear hierarchy. "Daily says up, 4H says up, 1H says down — I will wait." The lower timeframe is the entry trigger, not a vote that overrides the higher timeframe direction. If daily and 4H both say up, look for 1H pullback entries only.

> [!TIP]
> The 3x rule for timeframe selection: each level should be roughly 3–4x larger than the one below. Good triads: Daily / 4H / 1H · 4H / 1H / 15min · 1H / 15min / 5min. Avoid Daily and 5-minute in the same analysis — the gap is too large for meaningful connection.

> [!TAKEAWAY]
> Multiple timeframe analysis combines the big picture (trend from the daily) with precise timing (entry from the lower timeframe) — giving you trend momentum behind you and a surgically tight stop in front of you.
""",
                    "quiz": [
                        {"question": "In MTFA, the primary role of the highest timeframe is:", "option_a": "Finding precise entry points", "option_b": "Determining trend direction and major S&R — the overall bias", "option_c": "Setting stop loss distances", "option_d": "Measuring pip values for position sizing", "correct_answer": "B", "explanation": "The HTF establishes the dominant trend and key levels. It tells you the direction to trade — not when or exactly where to enter.", "topic_slug": "multi_timeframe"},
                        {"question": "Daily EUR/USD uptrend. 4H shows price at key support. 1H shows a bearish candle. You should:", "option_a": "Sell — the 1H candle is most recent", "option_b": "Wait for a bullish 1H candle to trigger a long entry aligned with the daily uptrend", "option_c": "Use a different pair", "option_d": "Switch to 5-minute for clarity", "correct_answer": "B", "explanation": "The daily uptrend sets the bias: only look for buys. The 1H bearish candle is noise within the larger bullish structure. Wait for a bullish 1H trigger.", "topic_slug": "multi_timeframe"},
                        {"question": "Great 1H setup but the daily chart shows no clear trend and sits at major resistance. You should:", "option_a": "Enter with full size — 1H signal is clear", "option_b": "Enter at half size or skip — HTF resistance with no clear trend reduces probability significantly", "option_c": "Ignore the daily — 1H signals are more accurate", "option_d": "Increase the 1H stop to account for HTF uncertainty", "correct_answer": "B", "explanation": "HTF resistance with no clear trend is a conflict. Lower timeframe setups that fight major HTF levels carry much lower probability.", "topic_slug": "multi_timeframe"},
                        {"question": "An MTFA pullback entry typically results in:", "option_a": "A wider stop because more timeframes are checked", "option_b": "A tighter stop and larger R:R — LTF precision at HTF-level targets", "option_c": "The same R:R as a single-timeframe approach", "option_d": "A smaller profit target", "correct_answer": "B", "explanation": "LTF entry allows a tight stop at LTF structure. The target is set at the HTF resistance level — often much further away. This dramatically improves R:R.", "topic_slug": "multi_timeframe"},
                        {"question": "Which timeframe combination follows the 3x rule correctly?", "option_a": "Monthly / Weekly / Daily", "option_b": "4H / 1H / 15min", "option_c": "Daily / 5min", "option_d": "1H / 30min / 25min", "correct_answer": "B", "explanation": "4H / 1H / 15min: each level is roughly 4x smaller than the previous. Daily/5min skips too many levels, creating a disconnect.", "topic_slug": "multi_timeframe"}
                    ]
                },
            ]
        },

        # ── MODULE 2 ──────────────────────────────────────────────────────────
        {
            "title": "Support and Resistance Mastery",
            "description": "Advanced S&R — dynamic levels, chart patterns, and the setups professionals trade most.",
            "lessons": [
                {
                    "title": "Dynamic Support and Resistance",
                    "content": """\
> [!HOOK]
> Static support and resistance levels are like signposts on a map — useful but fixed. Dynamic support and resistance is like a GPS — it follows price in real time, adjusting as the market moves. The best traders use both, and knowing when each applies is one of the marks of a genuinely advanced analyst.

> [!DEF]
> **Dynamic support and resistance** are levels that move with price — primarily trendlines, channels, and moving averages. Unlike fixed horizontal levels, they capture the ongoing momentum of a trend and provide entry points throughout a directional move.

### Trendlines

A valid trendline requires a minimum of two confirmed swing points to draw and a third touch to validate.

- Uptrend trendline: connect two or more Higher Lows. Price should bounce from this line on each test.
- Downtrend trendline: connect two or more Lower Highs. Price should reverse from it each time.

Rules: use candlestick bodies (not wicks) as primary anchor points. Steeper than 45° = unsustainable and will break sooner.

### Price channels

When price moves between two parallel trendlines, you have a channel. Buy zones at the lower trendline, sell zones at the upper, measured-move targets after a break.

### Moving averages as dynamic S&R

The 20 EMA acts as dynamic support in uptrends and resistance in downtrends. When price pulls back to touch the 20 EMA and bounces in a strong trend, that is the EMA acting as dynamic support — the same concept as a horizontal level, just moving.

> [!EXAMPLE]
> **Trendline bounce trade:**
>
> GBP/USD uptrend. Trendline connecting HL1 (1.2550) and HL2 (1.2620).
> Price pulls back to trendline at 1.2680. Bullish pin bar forms.
>
> Entry: 1.2685 · Stop: 1.2650 (below trendline + buffer) · Target: 1.2780 (previous HH)
> Risk: 35 pips · Reward: 95 pips · R:R: 1:2.7

> [!NGX]
> **NGX parallel:** OKOMU OIL PALM spent much of 2023 in a clear ascending channel. Each touch of the lower channel line (the trendline through Higher Lows) provided low-risk buy entries with the upper channel line as natural profit target. Channels on weekly NGX charts often hold for months, providing repeated opportunities on the same instrument.

> [!MISTAKE]
> Forcing trendlines to connect every wick rather than meaningful swing points. A line touching 8 wicks but missing 2 major body swing lows is not a real trendline — it is wishful pattern-matching. Draw clean lines through the clearest swing bodies, even if a few wicks pierce slightly.

> [!TIP]
> When a trendline breaks, do not immediately trade the break in the new direction. Wait for a **retest** — price often returns to the broken trendline (now acting as resistance) before continuing. The retest entry gives you confirmation the break was real, a tight stop, and excellent R:R on the continuation move.

> [!TAKEAWAY]
> Dynamic S&R moves with the trend — trendlines connect swing lows in uptrends, and the 20 EMA bounce strategy lets you enter at pullbacks with structure and momentum on your side.
""",
                    "quiz": [
                        {"question": "Minimum swing points needed to draw and validate a trendline?", "option_a": "One (the origin point)", "option_b": "Two to draw, three to validate (the third touch confirms it)", "option_c": "Five or more for reliability", "option_d": "An indicator validates the trendline, not price points", "correct_answer": "B", "explanation": "Two points draw the line; the third touch validates it as a meaningful dynamic level. Each subsequent touch adds conviction.", "topic_slug": "dynamic_sr"},
                        {"question": "The 20 EMA has acted as dynamic support 4 times in a strong uptrend. Price is pulling back to it again. This setup:", "option_a": "Should be avoided — too many tests signals a break is coming", "option_b": "Is a well-established dynamic support bounce candidate — look for bullish candle confirmation at the EMA", "option_c": "Is only valid if the EMA is exactly horizontal", "option_d": "Requires simultaneous RSI oversold reading", "correct_answer": "B", "explanation": "Repeated bounces from a dynamic level confirm its significance. More touches = stronger validation. Look for candle confirmation at the touch.", "topic_slug": "dynamic_sr"},
                        {"question": "A downtrend trendline breaks and price pulls back to test it from above. This is called:", "option_a": "A false breakout — sell immediately", "option_b": "A retest — the broken line may now act as support; wait for bullish confirmation before buying", "option_c": "A continuation pattern", "option_d": "A double bottom", "correct_answer": "B", "explanation": "When a trendline breaks, a retest of the broken level from the opposite side is common and often provides the best entry for the new direction.", "topic_slug": "dynamic_sr"},
                        {"question": "A very steep trendline (60°+) typically indicates:", "option_a": "Extremely healthy trend that will last much longer", "option_b": "Unsustainably fast pace — likely to break sooner than a more gradual trendline", "option_c": "Low volatility pair where steep angles are normal", "option_d": "More reliable trendline touches", "correct_answer": "B", "explanation": "Unsustainably steep angles mean momentum is overextended. These trendlines break faster — price eventually settles into a more sustainable, shallower trend.", "topic_slug": "dynamic_sr"},
                        {"question": "Better anchor point for drawing a trendline:", "option_a": "Tip of the candlestick wick at the swing point", "option_b": "Body close of the candle at the swing point", "option_c": "Arbitrary line between wicks of 5 adjacent candles", "option_d": "Midpoint between wick and body", "correct_answer": "B", "explanation": "Body-to-body trendlines are generally cleaner and more respected. Wick-to-wick lines often produce false signals because wicks represent temporary extremes, not sustained price acceptance.", "topic_slug": "dynamic_sr"}
                    ]
                },
                {
                    "title": "Chart Patterns",
                    "content": """\
> [!HOOK]
> In 1932, Richard Schabacker published the first systematic study of chart patterns — formations that appeared before major market moves. Ninety years later, the same patterns still appear on every chart in every market, because they are not random shapes. They are the visual signature of human psychological cycles: greed, fear, uncertainty, and capitulation playing out in price action. Once you see them, you cannot unsee them.

> [!DEF]
> **Chart patterns** are recurring price formations that signal either trend continuation (price is pausing before continuing) or trend reversal (the trend is about to change direction). They work because they represent specific crowd psychology phases that repeat across all markets and timeframes.

### Reversal patterns

**Head and Shoulders:**
Three peaks — higher middle peak (head) flanked by two lower peaks (shoulders). Neckline connects the two troughs. Break below neckline = uptrend reversed. Measured move target = head height projected below neckline.

**Double Top / Double Bottom:**
Two roughly equal highs (double top) or lows (double bottom) at a key level. Break of the "neckline" confirms. Double bottoms are strong buy signals after downtrends.

### Continuation patterns

**Bull Flag / Bear Flag:**
Sharp impulse (the pole) followed by narrow counter-trend channel (the flag). Breakout from the flag in the original direction. Target = pole height from breakout.

**Ascending Triangle:**
Horizontal resistance with series of higher lows compressing toward it. Bullish breakout expected when price finally pierces the horizontal resistance.

> [!EXAMPLE]
> **Bull flag on EUR/USD:**
>
> 120-pip bullish impulse: 1.0800 → 1.0920 (the pole).
> Price consolidates in a downward channel: 1.0920 → 1.0880 (the flag, 8 candles).
> Breakout above the upper flag trendline at 1.0895.
>
> Entry: 1.0898 · Stop: 1.0875 (below flag) · Target: 1.1015 (pole height added to breakout)
> Risk: 23 pips · Reward: 117 pips · **R:R: 1:5.1**

> [!NGX]
> **NGX parallel:** ACCESS BANK formed an ascending triangle in Q4 2023 — horizontal resistance at ₦20, higher lows compressing toward it over 6 weeks. The breakout above ₦20 on heavy volume was the entry. Target: ₦4 (pole height) added to ₦20 breakout = ₦24. NGX blue chips regularly form these patterns on weekly charts due to their institutional ownership base.

> [!MISTAKE]
> Entering a pattern before the breakout is confirmed. "It looks like it is forming a head and shoulders" is not a trade — the neckline break is the trade. Many traders enter early, the pattern fails, and they take an unnecessary loss. Wait for the break, ideally plus a retest.

> [!TIP]
> Volume is your pattern validity checker. A strong breakout on significantly higher-than-average volume confirms institutional participation. A breakout on thin volume is suspicious — often fakes out and reverses. If your broker shows volume data, use it. If not, candle body size is a reasonable proxy.

> [!TAKEAWAY]
> Chart patterns provide pre-defined entries, stops, and targets — a flag tells you exactly where to enter (breakout), where to stop (below the flag), and where to take profit (pole height target) before you place a single order.
""",
                    "quiz": [
                        {"question": "Head and shoulders: neckline at 1.1000, head at 1.1200. Measured move target after neckline break?", "option_a": "1.0800 (200 pips below neckline)", "option_b": "1.0900 (100 pips below neckline)", "option_c": "1.1100 (100 pips above neckline)", "option_d": "1.0950 (150 pips below)", "correct_answer": "A", "explanation": "Head height = 1.1200 - 1.1000 = 200 pips. Target = 1.1000 - 200 = 1.0800.", "topic_slug": "chart_patterns"},
                        {"question": "Continuation patterns vs reversal patterns:", "option_a": "Continuation patterns only occur on daily charts", "option_b": "Continuation patterns form during trend pauses before resuming; reversal patterns signal a direction change", "option_c": "Continuation patterns require volume confirmation; reversal patterns do not", "option_d": "Reversal patterns are more reliable", "correct_answer": "B", "explanation": "Flags, pennants, triangles = continuation. Head and shoulders, double tops/bottoms = reversal. Both have specific entry, stop, and target rules.", "topic_slug": "chart_patterns"},
                        {"question": "Bull flag forms after a 90-pip impulse. Measured move target from breakout?", "option_a": "45 pips (half the pole)", "option_b": "90 pips (equal to the pole)", "option_c": "180 pips (double the pole)", "option_d": "Target is the nearest resistance only", "correct_answer": "B", "explanation": "Bull flag measured move = the pole height projected from the breakout point. A 90-pip pole = 90-pip target from the flag breakout level.", "topic_slug": "chart_patterns"},
                        {"question": "Ascending triangle: horizontal resistance at 1.0950, higher lows compressing over 10 candles. A trader should:", "option_a": "Sell at resistance — ascending triangles are bearish", "option_b": "Buy at each higher low with stop below the triangle", "option_c": "Wait for a confirmed break above 1.0950 before entering long", "option_d": "Pattern is only valid after 20 candles of compression", "correct_answer": "C", "explanation": "The breakout above horizontal resistance confirms the ascending triangle. Entering before the breakout risks a pattern failure. Wait for confirmation.", "topic_slug": "chart_patterns"},
                        {"question": "A double top neckline breaks on unusually low volume. This suggests:", "option_a": "Pattern is more reliable — low volume confirms the break", "option_b": "Potential false breakout — high volume confirms institutional participation; low volume suggests possible return to range", "option_c": "Volume is irrelevant for chart patterns", "option_d": "The measured move target should be doubled", "correct_answer": "B", "explanation": "Volume confirms conviction. A neckline break on thin volume can be a false break — watch for reversal back into range. High-volume breaks are significantly more reliable.", "topic_slug": "chart_patterns"}
                    ]
                },
            ]
        },

        # ── MODULE 3 ──────────────────────────────────────────────────────────
        {
            "title": "Technical Indicators",
            "description": "The tools that confirm what price structure already shows — used correctly, they sharpen entries; used incorrectly, they create noise.",
            "lessons": [
                {
                    "title": "Moving Average Strategies",
                    "content": """\
> [!HOOK]
> A moving average is the most boring indicator on a chart. It is a slow, lagging line that always arrives late to the party. And yet every professional trader in the world watches it. Why? Because while price is noisy and emotional, the moving average cuts through that noise to reveal the underlying trend with clean, emotionless precision. It does not predict. It confirms. And confirmation is exactly what disciplined traders need.

> [!DEF]
> A **moving average** calculates the average closing price over a defined number of periods and plots it as a line. The **SMA** (Simple Moving Average) gives equal weight to all periods. The **EMA** (Exponential Moving Average) weights recent prices more heavily — making it faster and more responsive to current price action.

### The key moving averages

| MA | Periods | Primary use |
|----|---------|-------------|
| 20 EMA | 20 candles | Short-term trend, dynamic S&R |
| 50 EMA | 50 candles | Medium-term trend direction |
| 200 EMA | 200 candles | Long-term bull/bear dividing line |

**Golden Cross:** 50 EMA crosses above 200 EMA → major bullish signal.
**Death Cross:** 50 EMA crosses below 200 EMA → major bearish signal.

### Three core MA strategies

**1. MA as dynamic S&R:** In a strong uptrend, price bounces from the 20 EMA. Buy when price touches the 20 EMA and shows a bullish candle. Stop below the EMA.

**2. MA crossover:** When fast MA (20) crosses above slow MA (50), trend has shifted bullish. Enter on the next pullback.

**3. 200 EMA bias filter:** Price above the 200 EMA → only look for buy setups. Below → only look for sells. This one filter eliminates an enormous number of bad trades.

> [!EXAMPLE]
> **200 EMA bias + 20 EMA entry:**
>
> EUR/USD above the daily 200 EMA → bias is bullish, only buys.
> On the 4H chart, price pulls back to touch the 20 EMA at 1.0880.
> Bullish engulfing candle forms at the touch.
>
> Entry: 1.0885 · Stop: 1.0855 (below 20 EMA) · Target: 1.0960 (daily resistance)
> Risk: 30 pips · Reward: 75 pips · R:R: 1:2.5

> [!NGX]
> **NGX parallel:** On the MTNN weekly chart, the 20-week EMA has acted as consistent dynamic support throughout the 2022–2024 uptrend. Each pullback to the EMA provided low-risk buy entries for patient investors. The 200-week EMA serves as the ultimate support on NGX blue chips — a break below it on a weekly close is a major warning to exit longs.

> [!MISTAKE]
> Trading every MA crossover without additional confirmation. The 20/50 EMA crossover generates false signals frequently in ranging markets. Always require an additional confirmation — a key S&R level, trend structure, or candle pattern — before acting on a crossover alone.

> [!TIP]
> Moving averages are trend-following tools. They perform beautifully in trending markets and terribly in ranging ones. Before using MA-based strategies, check whether the market is trending (use price structure or ADX). If ranging, switch to range-bound strategies and ignore MA signals entirely.

> [!TAKEAWAY]
> Use the 200 EMA to set directional bias, the 20 EMA as dynamic support for entries, and avoid MA strategies entirely during sideways ranging conditions.
""",
                    "quiz": [
                        {"question": "EUR/USD closes above the 200 EMA on the daily chart for the first time in 3 months. Bias should shift to:", "option_a": "Bearish — a major move up always reverses", "option_b": "Bullish — price above 200 EMA signals a shift to longer-term bullish conditions", "option_c": "Neutral — one close above changes nothing", "option_d": "Sell the break — 200 EMA is resistance", "correct_answer": "B", "explanation": "The 200 EMA is the most watched long-term trend divider. A sustained close above it signals institutional buying and shifts bias to bullish setups.", "topic_slug": "moving_averages"},
                        {"question": "Difference between SMA and EMA?", "option_a": "SMA uses closing prices; EMA uses opening prices", "option_b": "EMA weights recent prices more heavily, making it faster to react to new price action", "option_c": "SMA is more accurate for short-term; EMA for long-term", "option_d": "They produce identical results on the same periods", "correct_answer": "B", "explanation": "EMA weights recent candles more, so it reacts faster to price changes. For dynamic S&R and trend trading, EMA is generally more responsive and practical.", "topic_slug": "moving_averages"},
                        {"question": "A Golden Cross forms on the daily EUR/USD chart. The most appropriate response:", "option_a": "Buy immediately at market price", "option_b": "Note the bullish confirmation; look for a pullback entry to the 20 or 50 EMA before entering", "option_c": "Ignore it — lagging indicators are unreliable", "option_d": "Sell — a Golden Cross is a 'sell the news' event", "correct_answer": "B", "explanation": "The Golden Cross confirms bullish trend shift but is not a precise entry signal. It always arrives late. The best entry is on the next pullback to the moving averages.", "topic_slug": "moving_averages"},
                        {"question": "MA crossovers generating multiple false signals. Most likely market condition:", "option_a": "A strong trending market moving too fast for MAs", "option_b": "A sideways, ranging market where MA crossovers are whipsaw-prone", "option_c": "Low liquidity causing MA calculation errors", "option_d": "The periods used are too long", "correct_answer": "B", "explanation": "MAs are trend-following tools. In ranging markets, they cross back and forth repeatedly generating false signals. Recognise the ranging condition and use range strategies instead.", "topic_slug": "moving_averages"},
                        {"question": "The 200 EMA as a trading rule means:", "option_a": "Only trade in the direction of 200 EMA crossovers", "option_b": "Use as a bias filter: above 200 EMA = only buys; below = only sells", "option_c": "Enter whenever price touches the 200 EMA", "option_d": "The 200 EMA is only useful on monthly timeframes", "correct_answer": "B", "explanation": "The 200 EMA as a directional bias filter is one of the most powerful single-rule improvements to any strategy. It eliminates trades against the dominant long-term trend.", "topic_slug": "moving_averages"}
                    ]
                },
                {
                    "title": "Momentum Indicators (RSI and MACD)",
                    "content": """\
> [!HOOK]
> In 1978, Welles Wilder published "New Concepts in Technical Trading Systems" and introduced RSI. In 1979, Gerald Appel refined MACD. Both were designed to answer the same question: not "which direction is price going?" but "how fast is price moving and is that speed sustainable?" These momentum tools are used by more traders worldwide than any other indicators — and most use them completely wrong.

> [!DEF]
> **RSI** (Relative Strength Index) measures the speed and magnitude of recent price changes on a 0–100 scale, identifying potentially overbought (>70) or oversold (<30) conditions. **MACD** measures the relationship between two EMAs to identify momentum shifts and trend changes.

### RSI — the right way to use it

Standard rule: "buy below 30, sell above 70." This is oversimplified and fails in trending markets.

**Better RSI use:**
- In strong uptrends, RSI commonly stays in the 40–80 range for extended periods — selling at 70 costs you the entire trend.
- **RSI divergence** is the most powerful signal: price makes a new high but RSI makes a lower high. Momentum is declining even as price rises — often precedes reversals.

### MACD — momentum shifts

Components:
1. MACD Line: Fast EMA (12) minus Slow EMA (26)
2. Signal Line: 9-period EMA of the MACD line
3. Histogram: MACD minus Signal — shows momentum acceleration/deceleration

Key signals: crossover (MACD crosses Signal), zero-line cross (MACD crosses zero = stronger), histogram divergence.

> [!EXAMPLE]
> **RSI divergence short setup:**
>
> EUR/USD HH1 at 1.0950 — RSI at 75.
> EUR/USD HH2 at 1.0980 (higher price) — RSI at 68 (lower RSI).
>
> Bearish divergence signals weakening buying pressure.
> Entry: short at 1.0975 after bearish candle confirms · Stop: 1.1005 · Target: 1.0895
> Risk: 30 pips · Reward: 80 pips · R:R: 1:2.7

> [!NGX]
> **NGX parallel:** DANGCEM's daily MACD showed a bearish crossover in late Q2 2023 just as the stock hit a resistance zone. Combined with a bearish reversal candle and RSI bearish divergence (price higher, RSI lower), this gave a high-conviction triple-confirmation signal. Multiple confirming indicators at the same level = institutional-grade setup.

> [!MISTAKE]
> Using RSI as a standalone signal: "RSI is at 28 — buy." An RSI of 28 in a strong downtrend means the market is persistently oversold and will go lower. Oversold can mean buy — but only when multiple other factors align (support level, bullish candle, trend structure). RSI alone is noise.

> [!TIP]
> The most powerful setups combine RSI divergence and MACD crossover confirming each other at a key support or resistance level. Three confluent signals at one level: price structure + RSI divergence + MACD crossover = one of the highest-probability setups in technical analysis. This combination is worth waiting for.

> [!TAKEAWAY]
> RSI tells you if momentum is weakening (use divergence, not oversold/overbought levels alone); MACD tells you if momentum is shifting — combined with price structure, they become confirmation tools rather than signal generators.
""",
                    "quiz": [
                        {"question": "EUR/USD in a strong downtrend. RSI reaches 25. A trader buys because 'it is oversold.' Why is this problematic?", "option_a": "RSI below 30 is always a buy signal", "option_b": "In a downtrend, RSI can remain below 30 for extended periods — oversold does not equal reversal", "option_c": "RSI below 30 signals the trend accelerates", "option_d": "The trader needs MACD confirmation first", "correct_answer": "B", "explanation": "In trending markets, RSI stays in extreme territories much longer. Downtrend RSI can oscillate 20-55 for weeks. Buying purely on RSI<30 is catching a falling knife without structural confirmation.", "topic_slug": "momentum_indicators"},
                        {"question": "What is RSI divergence?", "option_a": "RSI moving opposite to MACD", "option_b": "Price makes a new high/low but RSI fails to confirm — signalling weakening momentum", "option_c": "RSI crossing the 50 midline", "option_d": "RSI remaining overbought for more than 5 candles", "correct_answer": "B", "explanation": "Bearish divergence: price higher high but RSI lower high. Bullish divergence: price lower low but RSI higher low. Both signal momentum exhaustion.", "topic_slug": "momentum_indicators"},
                        {"question": "MACD line crosses above signal line AND above zero simultaneously. This indicates:", "option_a": "A minor short-term buy signal only", "option_b": "A significant momentum shift to bullish — both crossover and zero-line cross confirm direction change", "option_c": "Overbought conditions — sell signal", "option_d": "Conflicting signals — ignore", "correct_answer": "B", "explanation": "A crossover plus a zero-line cross simultaneously is one of the strongest MACD buy signals. Both components confirm bullish momentum.", "topic_slug": "momentum_indicators"},
                        {"question": "EUR/USD in uptrend. RSI at 72. Should you sell?", "option_a": "Yes — RSI above 70 is always a sell signal", "option_b": "Not necessarily — in strong uptrends RSI commonly stays 50-80 for extended periods", "option_c": "Yes, but only if MACD also shows a bearish crossover", "option_d": "Only sell if RSI reaches 80", "correct_answer": "B", "explanation": "In trending markets, the RSI '70 rule' fails. Strong uptrends push RSI into the 50-80 range and keep it there. Selling at 70 in a trend costs you the entire trend run.", "topic_slug": "momentum_indicators"},
                        {"question": "Most reliable RSI signal for high-probability entry:", "option_a": "RSI crossing above 50 on any timeframe", "option_b": "RSI below 30 with no other confirmation", "option_c": "RSI divergence at a key S&R level with candle confirmation", "option_d": "RSI above 80 on the 5-minute chart", "correct_answer": "C", "explanation": "RSI divergence at a key level with candle confirmation is a triple-confluence signal: structure, momentum, and price action. One of the highest-quality setups in technical analysis.", "topic_slug": "momentum_indicators"}
                    ]
                },
            ]
        },

    ]  # end Intermediate modules
},  # end Intermediate level

# ══════════════════════════════════════════════════════════════════════════════
# LEVEL 3 — ADVANCED
# ══════════════════════════════════════════════════════════════════════════════
{
    "level_name": "Advanced",
    "description": "Institutional-grade concepts. Fibonacci, Smart Money, expectancy mathematics, portfolio-level risk, and building a complete mechanical trading system. This is where retail traders cross into professional-grade operation.",
    "modules": [

        # ── MODULE 1 ──────────────────────────────────────────────────────────
        {
            "title": "Fibonacci and Advanced Tools",
            "description": "The mathematical ratios that appear in market structure — and how to combine tools into high-confidence entries.",
            "lessons": [
                {
                    "title": "Fibonacci Retracements and Extensions",
                    "content": """\
> [!HOOK]
> In the 13th century, mathematician Leonardo Fibonacci identified a sequence where each number is the sum of the two before it: 1, 1, 2, 3, 5, 8, 13, 21... The ratios between these numbers (61.8%, 38.2%, 23.6%) appear throughout nature: in spiral galaxies, nautilus shells, and the proportions of the human body. They also appear, with remarkable consistency, in financial markets — because markets are moved by human beings, and human psychology follows predictable mathematical patterns.

> [!DEF]
> **Fibonacci retracement** identifies potential support levels during a trend pullback by applying key ratios (23.6%, 38.2%, 50%, 61.8%, 78.6%) to the height of a prior impulse move. **Fibonacci extension** projects potential profit targets beyond the original move using ratios (127.2%, 161.8%, 261.8%).

### Drawing the tool correctly

For an uptrend retracement: draw from the **swing low** (0%) to the **swing high** (100%). The levels drawn are your potential support zones during the pullback.

### The levels

- **23.6%** — Shallow retracement; strong momentum often only pulls back this far
- **38.2%** — First major level; common in strong trends
- **50.0%** — Not a true Fibonacci ratio but widely watched and extremely common reversal point
- **61.8%** — The Golden Ratio — the most important Fibonacci level; highest-probability reversal zone
- **78.6%** — Deep retracement; still within trend structure if it holds

### Extensions for targets

After a 61.8% retracement completes and price resumes the trend:
- **127.2%** — Conservative first target
- **161.8%** — Primary target (most swing trades)
- **261.8%** — For strong trends only

> [!EXAMPLE]
> **Fibonacci retracement entry on EUR/USD:**
>
> Impulse: 1.0700 (swing low) to 1.1000 (swing high) = 300-pip move.
>
> 61.8% retracement: 1.1000 − (300 × 0.618) = **1.0815**
>
> Price pulls back to 1.0815. Bullish pin bar forms.
> Entry: 1.0818 · Stop: 1.0785 (below 78.6%) · Target 161.8% extension: 1.1185
> Risk: 33 pips · Reward: 367 pips · R:R: 1:11 (swing trade)

> [!NGX]
> **NGX parallel:** SEPLAT ENERGY's 2023 impulse from ₦600 to ₦1,400 (800-unit move) provided clear Fibonacci levels. The 61.8% retracement landed at ₦904 — and held precisely. Traders who understood Fibonacci entered buys at ₦904 with the 161.8% extension at ₦1,696 as their swing target. The level worked because institutional traders worldwide use these same ratios.

> [!MISTAKE]
> Using Fibonacci in isolation. A price touching the 61.8% level alone is not a trade. A price touching 61.8% that also coincides with a horizontal support level, produces a bullish candle, and shows RSI divergence — that is a trade. Fibonacci levels gain their power from confluence with other signals.

> [!TIP]
> The most powerful Fibonacci setup is "Fibonacci confluence" — when two or more levels from different timeframe swings land at exactly the same price. For example, the 61.8% of the daily swing and the 38.2% of the weekly swing both pointing to 1.0850. This stacking marks a zone of extraordinary institutional interest.

> [!TAKEAWAY]
> The 61.8% Fibonacci level (the Golden Ratio) is the highest-probability pullback zone in a trend — but only when it aligns with other confirming factors like structure, candle patterns, and indicator confluence.
""",
                    "quiz": [
                        {"question": "EUR/USD: swing low 1.0500, swing high 1.1000. Where is the 61.8% retracement?", "option_a": "1.0691", "option_b": "1.0809", "option_c": "1.0750", "option_d": "1.0618", "correct_answer": "A", "explanation": "Range = 500 pips. 61.8% of 500 = 309 pips. 1.1000 - 309 = 1.0691.", "topic_slug": "fibonacci"},
                        {"question": "Drawing a Fibonacci retracement tool in an uptrend, you draw:", "option_a": "From swing high to swing low", "option_b": "From swing low to swing high", "option_c": "Left to right along the trendline", "option_d": "From most recent candle low to most recent candle high", "correct_answer": "B", "explanation": "In an uptrend, draw from swing low (0%) to swing high (100%). The retracement levels then fall between the high and low, marking pullback support zones.", "topic_slug": "fibonacci"},
                        {"question": "Price retraces to the 50% level but falls further to 61.8%. You should:", "option_a": "Abandon the trade idea — it has failed", "option_b": "Wait to see if the 61.8% level provides a higher-quality entry with better R:R", "option_c": "Add to the position at 61.8% to average down", "option_d": "The 61.8% failure means the 100% level will be hit", "correct_answer": "B", "explanation": "If 50% does not hold, the 61.8% is the next key level. It often provides a better entry — tighter stop, same target = better R:R. Wait for confirmation there.", "topic_slug": "fibonacci"},
                        {"question": "What is Fibonacci confluence?", "option_a": "When Fibonacci levels align with MACD signals", "option_b": "When multiple Fibonacci levels from different timeframe swings converge at the same price zone", "option_c": "When all Fibonacci levels are within 5 pips of each other", "option_d": "When RSI reaches a Fibonacci level simultaneously", "correct_answer": "B", "explanation": "Fibonacci confluence occurs when 61.8% of one swing and 38.2% of a larger swing land at the same price. Traders from different timeframes all have orders near the same level.", "topic_slug": "fibonacci"},
                        {"question": "After entering at the 61.8% retracement, first conservative profit target is:", "option_a": "100% of the original move", "option_b": "127.2% extension", "option_c": "50% extension", "option_d": "200% extension", "correct_answer": "B", "explanation": "The 127.2% extension is the first Fibonacci extension level beyond the original impulse high. Conservative first target; 161.8% is the primary target for most full-trend setups.", "topic_slug": "fibonacci"}
                    ]
                },
                {
                    "title": "Confluence Trading",
                    "content": """\
> [!HOOK]
> Imagine asking five independent witnesses to describe where an accident happened. If they all point to the same intersection, you are confident about the location. One witness? Maybe confused. Five? Almost certainly correct. Confluence in trading follows the same logic — when five independent factors all point to the same price level, the probability of a reaction there is far higher than if only one factor pointed to it.

> [!DEF]
> **Confluence trading** is the practice of combining multiple independent technical signals at the same price level before entering a trade. Each additional confirming factor exponentially increases the probability that the level will hold and the trade will succeed.

### What counts as confluence?

Strong independent confluence factors:
1. **Key horizontal support/resistance** — level tested 2+ times
2. **Fibonacci level** — 38.2%, 50%, or 61.8% retracement
3. **Moving average** — 20, 50, or 200 EMA aligned at the same price
4. **Trendline** — dynamic line intersecting the level
5. **Candlestick pattern** — bullish pin bar, engulfing, etc.
6. **RSI divergence** — bearish or bullish divergence at the level
7. **MACD crossover** — confirming the reversal direction
8. **Round number** — 1.1000, 1.0500, ₦50, ₦100 (psychologically significant)

**Minimum standard:** 3 independent factors before entering.

### Building a confluence checklist

Before any entry, score the setup:
- Higher timeframe structure at this level? (+1)
- Fibonacci level here? (+1)
- Moving average confluent? (+1)
- Trendline passing through? (+1)
- Candle pattern at exact point? (+1)
- RSI or MACD divergence? (+1)

3 factors: standard entry. 5+ factors: consider full position size.

> [!EXAMPLE]
> **5-factor confluence trade on EUR/USD:**
>
> At 1.0850:
> 1. Major horizontal support (held 3 times) ✓
> 2. 61.8% Fibonacci retracement ✓
> 3. 50 EMA sitting at 1.0848 ✓
> 4. Uptrend trendline passing through 1.0845–1.0855 ✓
> 5. Bullish engulfing candle ✓
>
> Entry: 1.0855 · Stop: 1.0815 (below all confluence) · Target: 1.0960
> Risk: 40 pips · Reward: 105 pips · R:R: 1:2.6 · Conviction: Maximum.

> [!NGX]
> **NGX parallel:** When ZENITH BANK hit ₦35 in a pullback: it was a 50% Fibonacci retracement of the annual swing, coincided with the 200-day moving average, sat at previous resistance-turned-support, and formed a weekly bullish hammer. Four confluence factors on a weekly chart. The subsequent move to ₦48 was one of the highest-conviction setups of the year for NGX equity traders.

> [!MISTAKE]
> Counting the same type of evidence twice. RSI at 30 AND stochastic at 20 is NOT two signals — both are momentum oscillators saying the same thing with different calculations. True confluence requires independent analytical methods: price structure, Fibonacci, moving average, momentum, candle pattern. Different methods, same conclusion.

> [!TIP]
> Keep a physical or digital confluence scorecard for each trade idea. Write down every factor and its basis. If you cannot list 3 independent factors, do not enter. This forces honest pre-trade analysis and prevents entry on "feel" or pattern-matching alone.

> [!TAKEAWAY]
> Confluence trading stacks probability in your favour by requiring 3+ independent signals to align at the same price — turning ordinary setups into high-conviction entries with pre-defined risk and maximum edge.
""",
                    "quiz": [
                        {"question": "A trader identifies: RSI below 30, Stochastic below 20, CCI oversold. They count this as 3 confluence factors. Why is this wrong?", "option_a": "Oversold signals do not count as confluence", "option_b": "All three are momentum oscillators measuring the same thing — not independent analytical methods", "option_c": "Only RSI is reliable; others should be ignored", "option_d": "You need 5 factors minimum", "correct_answer": "B", "explanation": "True confluence requires independent methods. Three oscillators all showing oversold is one signal from three different tools, not three independent signals.", "topic_slug": "confluence"},
                        {"question": "A 4-factor confluence zone vs a 2-factor setup: appropriate position sizes?", "option_a": "Same — risk management determines size, not confluence", "option_b": "Larger size for the 4-factor zone; standard or smaller for the 2-factor setup", "option_c": "Smaller size for the confluence zone — more factors means more risk", "option_d": "Never trade the 2-factor setup", "correct_answer": "B", "explanation": "Higher confluence = higher probability = rational basis for larger position size within risk management rules.", "topic_slug": "confluence"},
                        {"question": "5-factor confluence setup but daily trend is opposite. You should:", "option_a": "Enter regardless — 5 factors overrides trend", "option_b": "Reduce size significantly or skip — trading against dominant trend reduces probability even with high confluence", "option_c": "Only enter if 7+ factors are present", "option_d": "This scenario cannot occur — confluence always aligns with trend", "correct_answer": "B", "explanation": "Trend alignment is the highest-priority factor. Counter-trend trades require exceptional confluence AND a clear structural break to justify. Most fail — institutional momentum usually wins.", "topic_slug": "confluence"},
                        {"question": "Professional minimum number of independent confluence factors for a full-size entry?", "option_a": "1 — a clear setup is enough", "option_b": "2 — entry plus confirmation", "option_c": "3 — minimum to establish high probability", "option_d": "10 — professionals use comprehensive checklists", "correct_answer": "C", "explanation": "3 independent confluent factors is the professional minimum. With fewer, you are relying on coincidence. With 3+, you have meaningful statistical backing.", "topic_slug": "confluence"},
                        {"question": "Strongest possible confluence combination for a buy setup:", "option_a": "RSI below 30, Stochastic below 20, Williams oversold", "option_b": "Support level + 61.8% Fibonacci + 200 EMA + bullish engulfing + RSI bullish divergence", "option_c": "Price above daily open + round number level", "option_d": "High volume candle + previous day high as support", "correct_answer": "B", "explanation": "Five independent analytical categories: price structure, mathematical (Fibonacci), trend (200 EMA), candle pattern, and momentum divergence (RSI). Maximum-conviction setup territory.", "topic_slug": "confluence"}
                    ]
                },
            ]
        },

        # ── MODULE 2 ──────────────────────────────────────────────────────────
        {
            "title": "Market Structure and Smart Money",
            "description": "How institutional traders leave footprints in price — and how to follow the money.",
            "lessons": [
                {
                    "title": "Order Blocks and Institutional Levels",
                    "content": """\
> [!HOOK]
> When Goldman Sachs needs to buy $500 million of EUR/USD, they cannot place a market order — it would move the price dramatically against them. Instead, they place orders in batches, often hidden in specific candles and consolidation zones. Those zones are called order blocks. The retail trader who finds them is trading alongside institutional flow. The retail trader who ignores them is trading against it.

> [!DEF]
> An **order block** is the last opposing candle before a significant directional move — typically the last bearish candle before a strong bullish impulse (bullish order block) or the last bullish candle before a strong bearish impulse (bearish order block). These zones represent where institutional traders placed large orders, creating a magnetic pull when price returns.

### What makes a valid order block?

**Bullish Order Block criteria:**
1. A bearish (red) candle or cluster
2. Followed immediately by a strong bullish impulse breaking recent structure
3. The impulse leaves behind an **imbalance** (Fair Value Gap) — a gap where no trading occurred
4. The OB's body zone (open to close of the bearish candle) = your entry zone when price returns

**Bearish Order Block:** the reverse — last bullish candle before a strong bearish displacement.

### Fair Value Gaps

A Fair Value Gap is a 3-candle pattern where the middle candle moves so fast that a gap exists between candle 1's high and candle 3's low. Price tends to return to fill these gaps — creating predictable future support/resistance zones.

> [!EXAMPLE]
> **Order block entry on EUR/USD daily chart:**
>
> Bearish candle: open 1.0950, close 1.0900 (the OB zone).
> Followed by 4 strong bullish candles breaking above 1.1050.
> Three days later, price returns to 1.0920 (within OB zone).
>
> Entry: 1.0922 + bullish candle confirmation · Stop: 1.0880 (below OB)
> Target: 1.1050 (top of original impulse)
> Risk: 42 pips · Reward: 128 pips · R:R: 1:3.0

> [!NGX]
> **NGX parallel:** Before major rallies in OANDO PLC, the chart consistently shows the same pattern: a bearish day or two of selling, then an explosive gap up on volume as institutional buyers accumulate. That "last red day before the gap" is the order block. When OANDO returns to that level on a low-volume pullback, it is an institutional re-accumulation entry — the same mechanics as Forex OBs applied to NGX equities.

> [!MISTAKE]
> Treating every bearish candle before an up-move as an order block. The displacement after the OB must be strong — breaking through significant structure, not just a minor pop. An OB without structural displacement is just a regular candle. Strength of the move away from the OB determines its validity.

> [!TIP]
> Higher timeframe order blocks are stronger than lower timeframe ones. A daily OB holds much better than a 15-minute OB. When you find a daily OB that also coincides with a weekly level, you have a premium zone — where the largest institutional positions tend to concentrate.

> [!TAKEAWAY]
> Order blocks are the institutional footprint left in price — finding the last opposing candle before a strong impulse and waiting for price to return to that zone positions you alongside the same institutional traders who drove the original move.
""",
                    "quiz": [
                        {"question": "What is a bullish order block?", "option_a": "Any bullish candle in an uptrend", "option_b": "The last bearish candle before a strong bullish displacement that breaks market structure", "option_c": "A support level tested three times", "option_d": "A consolidation zone before any upward move", "correct_answer": "B", "explanation": "A bullish OB is specifically the last bearish candle before a strong institutional-driven bullish move. The key is the strength and structural significance of the displacement.", "topic_slug": "order_blocks"},
                        {"question": "Price returns to a bullish OB zone. Ideal entry trigger:", "option_a": "Enter immediately when price touches the OB", "option_b": "Enter only if a bullish candle pattern forms within the OB — confirming buyers are defending the level", "option_c": "Enter at the bottom of the OB regardless", "option_d": "Wait for price to close below the OB then enter on reversal", "correct_answer": "B", "explanation": "Candle confirmation within the OB zone confirms institutional interest. Entering without confirmation risks entering as the OB fails.", "topic_slug": "order_blocks"},
                        {"question": "A Fair Value Gap indicates:", "option_a": "A candle closing at fair market value", "option_b": "An imbalance where price moved so quickly there is a gap between candle 1's high and candle 3's low", "option_c": "When bid and ask prices are equal", "option_d": "A price level considered fair by institutional traders", "correct_answer": "B", "explanation": "An FVG is a structural imbalance. Price often returns to fill the gap because no real price discovery occurred there.", "topic_slug": "order_blocks"},
                        {"question": "Strongest OB signal:", "option_a": "5-minute chart OB with minor displacement", "option_b": "Daily chart OB followed by a strong multi-day impulse breaking a weekly level", "option_c": "Most recent OB regardless of timeframe", "option_d": "OBs at round numbers only", "correct_answer": "B", "explanation": "Higher timeframe + stronger displacement = stronger OB. A daily OB that caused a weekly-level break represents massive institutional interest.", "topic_slug": "order_blocks"},
                        {"question": "Price returns to an OB for the second time. Compared to the first return, the second visit is:", "option_a": "Stronger — more tests validate the level", "option_b": "Same probability as the first", "option_c": "Generally weaker — institutional pending orders were partially or fully filled on the first visit", "option_d": "Only valid if price spent less than 1 hour at the level on the first visit", "correct_answer": "C", "explanation": "Order blocks are most powerful on the first return — that is when most pending institutional orders fill. Each subsequent visit has fewer remaining orders, reducing reaction probability.", "topic_slug": "order_blocks"}
                    ]
                },
                {
                    "title": "Liquidity and Market Structure",
                    "content": """\
> [!HOOK]
> Every stop loss you have ever placed below a support level was part of a pool of liquidity that institutional traders were actively hunting. When that support "breaks" and your stop gets hit, triggering a sharp reversal immediately after — you did not just have bad luck. You were the liquidity. Understanding this is the single most transformative shift in perspective for an intermediate trader moving to advanced level.

> [!DEF]
> **Liquidity** in Forex refers to pools of pending orders (stop losses and pending entries) clustered at predictable levels — equal highs, equal lows, swing points, and round numbers. Institutional traders and algorithms actively target these pools to fill their own large orders at optimal prices.

### Where liquidity lives

**Buy-side liquidity** (orders above price):
- Equal highs / double tops — stop losses of short sellers + breakout buy orders
- Previous swing highs, round numbers

**Sell-side liquidity** (orders below price):
- Equal lows / double bottoms — stop losses of long traders
- Previous swing lows, round numbers

### The liquidity sweep pattern

1. Price approaches a zone of sell-side liquidity (equal lows where stop losses cluster)
2. Price spikes briefly below the lows — sweeping the stops
3. Price immediately reverses with conviction back above the lows
4. The reversal continues to significant structural targets

This happens because institutions need the triggered stops to fill their large buy orders. They create the "breakdown" to generate the selling they need.

### BOS and CHoCH

**BOS (Break of Structure):** In an uptrend, each new Higher High is a BOS — trend continuation confirmed.

**CHoCH (Change of Character):** When the trend's structure is violated for the first time. In an uptrend, CHoCH occurs when price breaks BELOW the most recent Higher Low — the first sign the trend may be reversing.

> [!EXAMPLE]
> **Liquidity sweep entry:**
>
> EUR/USD equal lows at 1.0850 (tested twice — retail stops clustered below).
> Price dips to 1.0840 — stops triggered. Aggressive selling.
> Within 3 candles, price reverses to 1.0875. Bullish engulfing on 15-min.
>
> Entry: 1.0878 · Stop: 1.0832 (below sweep low) · Target: 1.0960 (next buy-side liquidity)
> Risk: 46 pips · Reward: 82 pips · R:R: 1:1.8

> [!NGX]
> **NGX parallel:** NESTLE NIGERIA repeatedly shows liquidity sweeps at support zones — the stock drops 2-3% below key support on thin volume (stop hunting), then reverses with a large volume surge. The reversal candle is the institutional buy. Recognising these sweeps on NGX charts transforms your interpretation of apparent "support breaks."

> [!MISTAKE]
> Treating every sweep as a guaranteed buy/sell signal. Not all sweeps reverse — sometimes the sweep IS the real breakout. Confirmation requirements: (1) the sweep candle must close BACK above the swept level, (2) a strong continuation candle must follow, (3) the sweep should occur at a confluence zone.

> [!TIP]
> Before trading any support or resistance level, ask: "Is this level obvious to retail traders?" Obvious levels = high probability sweep target. This insight helps you: (1) avoid placing stops at obvious clusters — put them at structural levels slightly beyond sweep zones, and (2) wait for sweeps to complete before entering, not before they start.

> [!TAKEAWAY]
> Liquidity sweeps are engineered by institutional order flow to fill large positions at optimal prices — understanding this turns stop hunting from a frustrating mystery into a predictable, tradeable pattern.
""",
                    "quiz": [
                        {"question": "EUR/USD forms equal lows at 1.0850 (two identical swing lows). From a Smart Money perspective, this zone is:", "option_a": "Strong support — equal lows confirm buyers hold this level", "option_b": "A liquidity pool — retail stop losses cluster here, making it a potential institutional sweep target", "option_c": "Irrelevant — equal lows have no special significance", "option_d": "A double bottom buy signal", "correct_answer": "B", "explanation": "Equal lows are one of the most common liquidity targets. Retail traders place stops just below them — institutions sweep below to collect those stops and fill buy orders.", "topic_slug": "liquidity"},
                        {"question": "Price spikes sharply below equal lows, triggers stop losses, then immediately reverses strongly above them within 2 candles. This pattern is called:", "option_a": "A false breakout caused by news", "option_b": "A liquidity sweep — characteristic of institutional order filling", "option_c": "Normal volatility with no significance", "option_d": "A double bottom confirmation", "correct_answer": "B", "explanation": "This is the classic liquidity sweep. The spike below triggers retail stops, fills institutional buy orders, and reverses quickly. Tradeable on confirmation of the reversal candle.", "topic_slug": "liquidity"},
                        {"question": "In an uptrend, a CHoCH occurs when:", "option_a": "Price makes a new Higher High", "option_b": "RSI moves from above 50 to below 50", "option_c": "Price breaks below the most recent Higher Low — first structural evidence the uptrend may be ending", "option_d": "The 20 EMA crosses below the 50 EMA", "correct_answer": "C", "explanation": "CHoCH is the first structural break of the trend's pattern. Breaking the most recent HL means the staircase structure has fractured — earliest warning of potential reversal.", "topic_slug": "liquidity"},
                        {"question": "To avoid having your stop targeted in a liquidity sweep:", "option_a": "Always use wide 200-pip stops", "option_b": "Place stops at obvious round numbers where other retail traders cluster", "option_c": "Place stops at structurally significant levels beyond common cluster zones", "option_d": "Only use mental stops to avoid detection", "correct_answer": "C", "explanation": "Stops placed at obvious levels are literally the target. Place them at structural levels that a genuine position invalidation requires — beyond common sweep zones.", "topic_slug": "liquidity"},
                        {"question": "A BOS to the upside in an established uptrend confirms:", "option_a": "A reversal — sell on the break", "option_b": "Trend continuation — the uptrend is intact and the next move up has begun", "option_c": "A fake breakout — wait for reversion", "option_d": "Overbought conditions requiring position reduction", "correct_answer": "B", "explanation": "BOS = structure break in the direction of the existing trend. In an uptrend, each new Higher High is a BOS confirming bullish structure is intact.", "topic_slug": "liquidity"}
                    ]
                },
            ]
        },

        # ── MODULE 3 ──────────────────────────────────────────────────────────
        {
            "title": "Advanced Risk Management",
            "description": "Professional-grade risk mathematics — the difference between a trader who survives and one who thrives.",
            "lessons": [
                {
                    "title": "Expectancy and Profit Factor",
                    "content": """\
> [!HOOK]
> Ed Seykota, one of the most successful traders of the 20th century, was once asked the key to his success. His answer: "I cut my losses and let my profits run." This was not wisdom — it was mathematics. He had a positive expectancy system. A negative expectancy system cuts profits and lets losses run. Every trading strategy in existence falls into one of these two categories, and most retail traders have never actually calculated which one theirs is.

> [!DEF]
> **Expectancy** is the average profit or loss you can expect per dollar risked across all trades in your strategy. **Profit Factor** is the ratio of total gross profit to total gross loss. Together, these two metrics tell you definitively whether your strategy makes money over time — regardless of how it feels on any individual day.

### Calculating expectancy

```
Expectancy = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)
```

**Example A:** 50% win rate, avg win $200, avg loss $100
= (0.50 × $200) - (0.50 × $100) = $100 - $50 = **+$50/trade** ✓ Profitable

**Example B:** 60% win rate, avg win $50, avg loss $100
= (0.60 × $50) - (0.40 × $100) = $30 - $40 = **−$10/trade** ✗ Losing

Despite the higher win rate, Example B loses money. This is how most retail traders operate.

### Profit Factor

```
Profit Factor = Total Gross Profit ÷ Total Gross Loss
```

| PF | Meaning |
|----|---------|
| < 1.0 | Losing system |
| 1.0 | Breakeven |
| 1.25–1.5 | Viable strategy |
| 1.75–2.5 | Good professional strategy |
| > 2.5 | Exceptional |

### Sample size requirement

An expectancy from 10 trades is meaningless. You need at least **100 trades** before statistics are significant. Most retail traders test strategies for 10 trades, declare them failing, and switch — never knowing if the strategy had edge.

> [!EXAMPLE]
> **200-trade expectancy audit:**
>
> Total trades: 200 · Wins: 90 (45%) · Avg win: $180 (1.8R)
> Losses: 110 (55%) · Avg loss: $100 (1.0R)
>
> Expectancy = (0.45 × $180) - (0.55 × $100) = $81 - $55 = **+$26/trade**
> Profit Factor = (90 × $180) / (110 × $100) = $16,200 / $11,000 = **1.47**
>
> A legitimate profitable strategy with a sub-50% win rate. This is why R:R matters more than win rate.

> [!NGX]
> **NGX parallel:** An NGX swing trader tracked 150 trades over 12 months: 52 wins at avg ₦8,500 profit, 98 losses at avg ₦4,200 loss. Expectancy = (0.347 × ₦8,500) - (0.653 × ₦4,200) = ₦2,949 - ₦2,742 = +₦207/trade. Profitable — barely. The insight led directly to tightening stop losses to improve the avg loss figure without changing strategy or win rate.

> [!MISTAKE]
> Comparing yourself to a "60% win rate benchmark" without considering R:R. Win rate means nothing in isolation. A 35% win rate strategy with 1:3 R:R has expectancy of (0.35 × 3R) - (0.65 × 1R) = +0.40R per trade — more profitable than a 60% win rate strategy with 0.8:1 R:R.

> [!TIP]
> Track expectancy by **setup type**, not overall. Your triangle breakouts might have PF 1.8 while your news reversals have PF 0.7. Combined, results look mediocre. Separated, you discover: stop trading news reversals, only trade triangle breakouts. The 80/20 principle almost always applies to setup types.

> [!TAKEAWAY]
> Positive expectancy — not win rate or gut feel — is the only objective measure of whether a trading strategy has genuine edge, and you need 100+ trades to calculate it meaningfully.
""",
                    "quiz": [
                        {"question": "Strategy: 40% win rate, avg win $300, avg loss $150. Expectancy?", "option_a": "-$30 per trade (losing)", "option_b": "+$30 per trade (profitable)", "option_c": "Breakeven", "option_d": "+$90 per trade", "correct_answer": "B", "explanation": "Expectancy = (0.40 x $300) - (0.60 x $150) = $120 - $90 = +$30 per trade. Profitable despite only 40% wins because wins are twice the size of losses.", "topic_slug": "expectancy"},
                        {"question": "Total gross profit: $12,000. Total gross loss: $8,000 over 150 trades. Profit factor?", "option_a": "0.67", "option_b": "1.50", "option_c": "2.00", "option_d": "4.00", "correct_answer": "B", "explanation": "Profit Factor = $12,000 / $8,000 = 1.50. Above 1.0 = profitable; above 1.5 = a good viable strategy.", "topic_slug": "expectancy"},
                        {"question": "A trader has used a strategy for 15 trades with 7 wins. They conclude it 'has edge.' The problem?", "option_a": "7/15 is a losing win rate", "option_b": "15 trades is statistically insufficient — at least 100 needed before expectancy statistics are meaningful", "option_c": "Expectancy can only be calculated on losing trades", "option_d": "Win rate from 15 trades is accurate if market conditions were identical", "correct_answer": "B", "explanation": "Statistical significance requires ~100+ trades minimum. With 15 trades, random variance (luck) can easily produce misleading results either way.", "topic_slug": "expectancy"},
                        {"question": "A strategy has 65% win rate but negative expectancy. Most likely cause:", "option_a": "A calculation error — 65% always guarantees positive expectancy", "option_b": "Average losing trades are significantly larger than average winning trades", "option_c": "The sample size is too small", "option_d": "High win rate strategies always have negative expectancy", "correct_answer": "B", "explanation": "If avg loss > avg win, even a high win rate cannot overcome the deficit. Classic case: 65% wins of $50 vs 35% losses of $200 = -$37.50 expectancy per trade.", "topic_slug": "expectancy"},
                        {"question": "A trader finds: breakout trades PF 2.1, reversal trades PF 0.8 — they trade both. Optimal solution:", "option_a": "Blend both to average out performance", "option_b": "Stop trading reversal setups entirely — focus exclusively on breakouts where edge is proven", "option_c": "Increase size on reversal trades to recover losses faster", "option_d": "Both are insufficient — start fresh", "correct_answer": "B", "explanation": "PF 0.8 is a losing strategy regardless of how it feels. Remove it from the playbook. Identify what works and double down while eliminating what does not.", "topic_slug": "expectancy"}
                    ]
                },
                {
                    "title": "Portfolio Heat and Correlation",
                    "content": """\
> [!HOOK]
> In August 2015, a single day wiped out hedge funds that believed they were "diversified" across multiple positions. Every position fell simultaneously because they were all correlated to Chinese equities. On paper: 10 separate positions. In practice: 10 copies of the same trade. Portfolio heat management is the professional risk layer that even experienced traders often skip — and pay for eventually.

> [!DEF]
> **Portfolio heat** is the total percentage of your account at risk across all open positions simultaneously. **Correlation** measures how similarly two instruments move — highly correlated positions add to the same directional risk even when they appear to be different trades.

### Why per-trade rules are not enough

Risking 1% per trade sounds conservative. But 8 simultaneous trades all in the same directional bias:

Total portfolio heat = 8 × 1% = **8% at risk at one time**

A correlated event (flash crash, surprise central bank announcement) can close all 8 at stop loss in minutes. 8% drawdown from one event — not a gradual accumulation.

**Professional maximum portfolio heat: 5–8% total at any one time.**

### Currency correlation

| Long on... | Also long on... | Result |
|-----------|----------------|--------|
| EUR/USD | GBP/USD | Same trade (both long Dollar short, +0.90 correlated) |
| EUR/USD | AUD/USD | Similar exposure (+0.75) |
| USD/CAD | USD/CHF | Same trade (both long Dollar, +0.85) |

EUR/USD, GBP/USD, and AUD/USD long simultaneously is not "3 separate 1% trades" — it is a ~2.7% correlated bet that USD falls.

> [!EXAMPLE]
> **Portfolio heat audit:**
>
> Open: Long EUR/USD (1%), Long GBP/USD (1%), Long AUD/USD (0.5%), Short GBP/JPY (1%)
>
> EUR/USD + GBP/USD = highly correlated → ~1.7% combined
> AUD/USD adds ~0.35% incremental
> GBP/JPY short has partial correlation with GBP/USD long → partial offset
>
> Adjusted portfolio heat: ~3.5% — within the 5% professional limit. Acceptable.

> [!NGX]
> **NGX parallel:** Holding GTCO, ACCESS BANK, ZENITH BANK, and UBA simultaneously = four highly correlated banking sector stocks. During a sector selloff (CBN policy change, FX restriction), all four hit stop losses simultaneously. True NGX diversification mixes sectors: banking + consumer goods (DANGFLOUR) + telecoms (MTNN) + oil services (SEPLAT) — stocks with genuinely different macro drivers.

> [!MISTAKE]
> "I am only risking 1% per trade so I am safe." Per-trade control is floor one. Portfolio heat and correlation awareness is floor two. You need both. Many traders discover this only after a correlated liquidation event takes out a week of gains in an afternoon.

> [!TIP]
> Check pair correlations before adding any new position. Tools: Investing.com correlation matrix, FXCM correlation dashboard. Pairs with correlation above 0.80 should be treated as the same position. Combined heat on correlated instruments should follow the same rules as a single position.

> [!TAKEAWAY]
> Portfolio heat management caps total simultaneous risk at 5–8% and adjusts for correlated positions — because 8 positions in the same direction can create the same catastrophic single-event risk as one 8% position.
""",
                    "quiz": [
                        {"question": "6 open positions each risking 2%. Portfolio heat?", "option_a": "2%", "option_b": "12%", "option_c": "6%", "option_d": "0.33%", "correct_answer": "B", "explanation": "6 positions x 2% each = 12% portfolio heat. A correlated event could cause 12% drawdown in a single session.", "topic_slug": "portfolio_risk"},
                        {"question": "EUR/USD long and GBP/USD long with correlation +0.90. Holding both at 1% risk gives you:", "option_a": "True 2% diversified risk", "option_b": "Approximately 1.7% correlated risk — essentially the same directional bet on USD weakening", "option_c": "Only 1% risk because they offset each other", "option_d": "3% risk because correlated positions compound losses", "correct_answer": "B", "explanation": "High positive correlation means both positions move together. Two 1% correlated positions ≈ 1.7% actual incremental risk, not 2% diversified risk.", "topic_slug": "portfolio_risk"},
                        {"question": "Professional maximum portfolio heat at any one time:", "option_a": "1–2% total", "option_b": "5–8% total", "option_c": "20–25% to maximise opportunity", "option_d": "Portfolio heat is not limited — only individual trade risk is", "correct_answer": "B", "explanation": "5–8% total heat allows multiple simultaneous positions while ensuring no single correlated event causes catastrophic damage.", "topic_slug": "portfolio_risk"},
                        {"question": "True diversification means:", "option_a": "Holding 10 or more simultaneous positions", "option_b": "Positions in instruments with genuinely different macro drivers — low or negative correlation", "option_c": "Spreading risk across different timeframes on the same pair", "option_d": "Mixing long and short positions on correlated pairs", "correct_answer": "B", "explanation": "True diversification requires different macro drivers. Low or negative correlation means positions do not all fail simultaneously.", "topic_slug": "portfolio_risk"},
                        {"question": "A correlated liquidation event wipes 4 positions simultaneously. Root cause:", "option_a": "Bad entries on all 4", "option_b": "The 4 positions were highly correlated — exposed to the same macro risk factor", "option_c": "Spreads widened simultaneously on unrelated pairs", "option_d": "Broker system error", "correct_answer": "B", "explanation": "Simultaneous multi-position liquidation is almost always a correlation problem. Individually managed 1% positions all sharing the same underlying risk factor act effectively as one large concentrated position.", "topic_slug": "portfolio_risk"}
                    ]
                },
            ]
        },

        # ── MODULE 4 ──────────────────────────────────────────────────────────
        {
            "title": "Trading System Development",
            "description": "Building a mechanical trading strategy from scratch — the framework used by professional quant traders.",
            "lessons": [
                {
                    "title": "Backtesting Your Strategy",
                    "content": """\
> [!HOOK]
> Every year, thousands of retail traders pay for "proven" courses, implement the strategy in live markets, and lose money. They blame the educator, the market, the broker. The one thing they did not do before risking real money: test the strategy against historical price data. Backtesting is the scientific method applied to trading — and skipping it is launching a product without testing whether anyone wants it.

> [!DEF]
> **Backtesting** is the process of applying a defined trading strategy to historical price data to evaluate its performance before risking real capital. A properly conducted backtest reveals the strategy's edge, expected drawdown, win rate, and profit factor across different market conditions.

### The four phases

**Phase 1 — Define strategy rules precisely:**
Every entry condition, exit condition, stop method, and take profit must be 100% objective. "Buy when it looks bullish" cannot be backtested. "Buy when price closes above the 20 EMA after a pullback to the 50% Fibonacci retracement, stop below the recent swing low" can be.

**Phase 2 — Build the dataset:**
Minimum 2–3 years of historical data. Include trending, ranging, high-volatility, and news-driven periods. A strategy that only works in strong trends is incomplete.

**Phase 3 — Record trades systematically:**
For every signal: entry price, stop, target, outcome, market condition, session, news context. Use a spreadsheet.

**Phase 4 — Analyse results:**
Calculate win rate, profit factor, expectancy, maximum drawdown, maximum consecutive losses, annual return. Compare across pairs, timeframes, and conditions.

> [!EXAMPLE]
> **Backtest results summary (EUR/USD, 1H, 18 months):**
>
> | Metric | Result | Benchmark |
> |--------|--------|-----------|
> | Total trades | 247 | ≥100 required |
> | Win rate | 44% | Not the key metric |
> | Avg win | 2.3R | |
> | Avg loss | 1.0R | |
> | Profit factor | 1.81 | Need ≥1.25 |
> | Max drawdown | 8.2% | Acceptable ≤15% |
> | Expectancy | +0.49R/trade | Positive = edge |
>
> Conclusion: Strategy has edge. Proceed to forward-testing on demo.

> [!NGX]
> **NGX parallel:** An NGX equity trader backtesting a "buy pullback to 20-week EMA on NGX top-20 stocks" strategy across 5 years on MTNN, DANGCEM, GTCO, ZENITH, and NESTLE found: 68% win rate, profit factor 1.62, max drawdown 11%. The backtest provided conviction to deploy real capital — knowing exactly what to expect in different conditions.

> [!MISTAKE]
> Curve fitting — tweaking strategy parameters until the backtest looks perfect. Testing 50 parameter combinations and showing only the one that worked historically is optimising for the past, not the future. The strategy will likely fail in live trading. Test with fixed parameters determined by logic, not by data mining.

> [!TIP]
> After a positive backtest, paper-trade in real-time for 30–50 trades (forward test) before committing real capital. This catches implementation issues (entries you miss, exits you take early), psychological challenges, and confirms the edge holds in current conditions.

> [!TAKEAWAY]
> A backtest with 100+ trades, positive expectancy, acceptable maximum drawdown, and profit factor above 1.25 is the minimum evidence required before committing real capital to any trading strategy.
""",
                    "quiz": [
                        {"question": "Minimum backtest trades needed for statistical reliability?", "option_a": "10 trades across multiple pairs", "option_b": "100 trades on the strategy, same setup type", "option_c": "50 trades in the most recent conditions", "option_d": "30 trades — one month's worth", "correct_answer": "B", "explanation": "Statistical significance begins at ~100 trades. Below this, random variance can produce misleading results in either direction.", "topic_slug": "backtesting"},
                        {"question": "Backtest shows: Win rate 35%, Avg win 3.5R, Avg loss 1.0R, Profit Factor 1.83. Should this strategy be pursued?", "option_a": "No — 35% win rate loses more often than it wins", "option_b": "Yes — positive expectancy (0.35x3.5 - 0.65x1.0 = +0.575R) and PF > 1.5 confirm genuine edge", "option_c": "Only if win rate can be improved above 50%", "option_d": "Results are inconclusive", "correct_answer": "B", "explanation": "Win rate alone means nothing. Positive expectancy (+0.575R/trade) and PF 1.83 confirm a profitable strategy. High R:R strategies can be highly profitable with sub-40% win rates.", "topic_slug": "backtesting"},
                        {"question": "A trader backtests 30 different MA period combinations and reports the one with PF 2.8 as 'proven.' This is problematic because:", "option_a": "MA backtests are always unreliable", "option_b": "Testing many variations and selecting the best is curve fitting — the result is optimised for past data and will likely fail forward", "option_c": "PF 2.8 is too high — no strategy performs this well", "option_d": "The sample size was not stated", "correct_answer": "B", "explanation": "Testing 30 combinations guarantees finding one that worked historically by chance. This is data mining / curve fitting. The correct approach: pick parameters by logic, then test those specific ones once.", "topic_slug": "backtesting"},
                        {"question": "Purpose of forward-testing after a positive backtest:", "option_a": "Verify the backtest mathematics", "option_b": "Confirm the edge holds in current market conditions and identify implementation challenges before risking real capital", "option_c": "Forward testing replaces the backtest", "option_d": "Only required if backtest sample was below 100 trades", "correct_answer": "B", "explanation": "Historical performance does not guarantee future performance. Forward testing in real-time closes the gap between past evidence and live execution.", "topic_slug": "backtesting"},
                        {"question": "A strategy worked in 2020-2022 (strong trends) but failed in 2019 (ranging). Correct conclusion:", "option_a": "Strategy is valid — use it in current trending conditions", "option_b": "Strategy needs a trend filter to avoid ranging conditions — it is incomplete as is", "option_c": "2019 data is outdated — ignore it", "option_d": "All strategies fail in ranging markets — this is expected", "correct_answer": "B", "explanation": "A complete strategy must account for different market conditions. Adding a trend filter (e.g., only trade when ADX > 20) solves the ranging failure before live deployment.", "topic_slug": "backtesting"}
                    ]
                },
                {
                    "title": "Creating Your Trading System",
                    "content": """\
> [!HOOK]
> A trading system is not a collection of indicators. It is a complete decision-making framework that removes human emotion from every trading decision — before, during, and after the trade. The best trading systems are often the simplest. The worst are the most complex. Simplicity is reproducible under pressure; complexity breaks down the moment emotions arrive.

> [!DEF]
> A **trading system** is a set of fully explicit, objective rules governing every aspect of your market participation: what you trade, when you trade, how you enter, how you size positions, how you manage open trades, and how you exit — both at targets and at stops.

### The seven components of a complete system

**1. Universe:** "EUR/USD, GBP/USD on H1 during London and NY sessions."

**2. Setup identification:** "Price in uptrend (above 50 EMA, HH/HL structure). Pulls back to 61.8% Fibonacci. Bullish candle forms."

**3. Entry trigger:** "Buy on close of the confirming bullish candle."

**4. Stop loss rule:** "Below the most recent Higher Low, minimum 10 pips from entry."

**5. Position size rule:** "Risk 1% of current account balance. Calculate lot size from stop distance."

**6. Trade management:** "Move stop to breakeven when trade reaches 1:1 R:R. No further adjustment until target."

**7. Exit rule:** "Close at pre-defined target (1:2 R:R). No exceptions. No moving targets."

### Why rules beat discretion

When you are watching a trade go against you at 3pm on a Friday, you cannot make good decisions under that emotional pressure. A documented system means the calm, rational version of you made the decision already. The emotional version of you simply executes. That is its entire psychological function.

> [!EXAMPLE]
> **Abbreviated system specification:**
>
> Name: FPS — Fibonacci Pullback System
> Universe: EUR/USD, GBP/USD, H1 chart
> Trend filter: Price above daily 200 EMA → buys only
> Setup: Pullback to 50–61.8% Fibonacci after verified impulse with HH/HL structure
> Entry: Close of bullish engulfing or pin bar within zone
> Stop: 10 pips below pullback low · Position size: 1% account risk
> Target: 2.0R · Breakeven: move stop to entry + 5 pips when trade reaches 1:1
> Max open trades: 3 · Max portfolio heat: 5%
> Trading hours: 9am–6pm WAT (London session and overlap only)

> [!NGX]
> **NGX system example:** Universe: NGX top-20 stocks. Setup: weekly EMA bounce with RSI bullish divergence. Entry: Monday open after setup confirms on Friday close. Stop: 5% below entry. Target: previous resistance (typically 10–20% higher). Holds 2–6 weeks. Review every Sunday. This is a complete system — reproducible, objective, emotionless.

> [!MISTAKE]
> Confusing strategy with system. A strategy is an approach ("buy pullbacks"). A system specifies every decision rule without ambiguity. The test: could you hand this document to another person and would they make exactly the same trades as you? If not, it is not yet a system.

> [!TIP]
> Write your system in a document and review it every Sunday. Ask: did I follow every rule this week? If not, write down which rules were broken and why. The answer will consistently be emotion, impatience, or FOMO. The written review creates accountability that verbal commitments never achieve.

> [!TAKEAWAY]
> A complete trading system eliminates discretionary decision-making from every trade by specifying rules for every possible scenario — making your trading reproducible, testable, and emotion-resistant.
""",
                    "quiz": [
                        {"question": "Key difference between a trading strategy and a trading system?", "option_a": "A strategy uses indicators; a system uses price action only", "option_b": "A strategy is an approach; a system specifies every decision rule so it can be executed identically by any person without interpretation", "option_c": "Systems are for automated trading only", "option_d": "A strategy is short-term; a system covers long-term only", "correct_answer": "B", "explanation": "A system is a strategy made fully explicit and objective. If your strategy requires any personal judgment call, it is not yet a system.", "topic_slug": "trading_system"},
                        {"question": "Why is a breakeven stop-move rule ('move stop to entry when trade reaches 1:1') valuable?", "option_a": "It guarantees profits on every trade", "option_b": "It removes the emotional decision of whether to stay in a trade at breakeven — the rule already decided", "option_c": "It improves win rate by counting breakeven exits as wins", "option_d": "It reduces profit factor but improves drawdown", "correct_answer": "B", "explanation": "Pre-defined trade management rules eliminate the most emotionally charged decisions. The rule has already decided before you are in the emotional state.", "topic_slug": "trading_system"},
                        {"question": "System rule: maximum 3 open trades simultaneously. A high-quality 4th setup appears. You should:", "option_a": "Add the 4th — the system should have flexibility for exceptional setups", "option_b": "Skip the 4th — every 'exceptional exception' is the emotional brain overriding the logical brain", "option_c": "Reduce all 4 positions to 0.5% to stay within limits", "option_d": "Close the worst-performing position to make room", "correct_answer": "B", "explanation": "The circuit breaker only functions if it is absolute. 'Feeling confident about the 4th trade' is exactly the emotional state the rule is designed to govern.", "topic_slug": "trading_system"},
                        {"question": "Primary psychological benefit of a documented trading system:", "option_a": "Guarantees profitability by eliminating human error", "option_b": "Under emotional pressure, rules remove the necessity to decide — the system has already decided in a calm rational state", "option_c": "Allows sharing with others to verify validity", "option_d": "Improves memory so fewer rules are forgotten", "correct_answer": "B", "explanation": "The human brain under stress makes poor decisions. A documented system means decisions were made rationally and are executed regardless of current emotional state.", "topic_slug": "trading_system"},
                        {"question": "A complete trading system must include rules for:", "option_a": "Entry signals only — exits are managed by feel", "option_b": "Entry, stop loss, position sizing, trade management, profit target, trading hours, and maximum simultaneous positions", "option_c": "Entry and profit target only — stop loss is always 50 pips", "option_d": "Position sizing and exit only — entries are flexible", "correct_answer": "B", "explanation": "A system with any undefined component will have that component filled by emotion during live trading. Every aspect of the trade lifecycle must be specified.", "topic_slug": "trading_system"}
                    ]
                },
            ]
        },

        # ── MODULE 5 ──────────────────────────────────────────────────────────
        {
            "title": "The Complete Trading Plan",
            "description": "The master document that runs your trading business — written once, followed forever.",
            "lessons": [
                {
                    "title": "Creating Your Trading Plan",
                    "content": """\
> [!HOOK]
> Paul Tudor Jones, who predicted Black Monday 1987 and made a fortune while the market crashed, says the same thing in every interview: "I spend my time thinking about how I will be wrong, not how I will be right." His trading plan was not about predicting the future. It was about defining what he would do in every possible scenario before it happened. That is the trading plan — a precommitment device that forces you to think clearly about every contingency while you are calm, so your calm self governs when your emotional self shows up.

> [!DEF]
> A **trading plan** is a comprehensive written document governing every aspect of your trading operation — from goals and strategy rules to daily routine, risk management, and performance review process. It is your business plan. Trading without one is starting a business without a strategy.

### The 8 components of a complete trading plan

**1. Goals — specific and measurable:**
Not "make money." Instead: "Achieve 3% monthly return on a $10,000 account with maximum 10% drawdown using the Fibonacci Pullback System on EUR/USD."

**2. Trading system rules:** Complete entry, exit, position sizing, and management rules from the previous lesson.

**3. Risk management parameters:** Max risk per trade (1%), max portfolio heat (5%), max daily loss (3% — stop trading if hit), max weekly loss (6%).

**4. Daily routine:** Specific times for pre-market prep, trading window, post-session review.

**5. Psychology rules:** "If I take 3 consecutive losses in one session, I close the platform for the day." "I will not trade within 15 minutes of high-impact news."

**6. Instruments and timeframes:** "EUR/USD and GBP/USD on H1 chart. No other pairs or timeframes until 6 months of consistent results."

**7. Performance review schedule:** Daily 10-minute journal. Weekly 1-hour review. Monthly 2-hour audit. Quarterly full plan review.

**8. Circuit breakers:** "If account drops 10% in one month, I stop live trading for 2 weeks and return to demo."

> [!EXAMPLE]
> **Risk parameter section:**
>
> Max risk per trade: 1.0% · Max portfolio heat: 5.0%
> Daily loss limit: 3.0% — if hit, close all trades, no trading for 24 hours
> Weekly loss limit: 5.0% — if hit, reduce to 0.5% per trade for 2 weeks
> Monthly circuit breaker: 10.0% drawdown → return to demo for 30 days
> Consecutive losses trigger: 4 losses in a row → 24-hour break minimum
>
> Note: Circuit breakers are not weakness. They are the risk management system for the risk management system.

> [!NGX]
> **NGX adaptation:** "NGX portfolio: maximum 5 stocks simultaneously. Maximum 20% in any single stock. Minimum holding period 2 weeks. Daily loss limit: if total portfolio drops 3% in one session, no new purchases that week. Annual review versus NGXASI benchmark."

> [!MISTAKE]
> Writing a trading plan once, filing it, and never reading it again. The plan only works if it is consulted. Check it before each trading day. Review it weekly. Update it quarterly based on what the data says. A dusty trading plan is a pretend trading plan.

> [!TIP]
> The signature rule: print your trading plan, sign it with a date, and post it next to your trading station. The physical act of signing creates psychological accountability. When tempted to break a rule, you see your own signature — your calm, rational self holding your emotional self accountable. Trading coaches charge thousands to teach this.

> [!TAKEAWAY]
> A trading plan converts trading from a series of emotional impulses into a business operation with defined rules, measurable goals, a daily process, and pre-built circuit breakers — making consistent, recoverable performance possible.
""",
                    "quiz": [
                        {"question": "Which goal is correctly written for a trading plan?", "option_a": "Make consistent profits trading Forex", "option_b": "Achieve 2.5% monthly return on $8,000 account, max 8% drawdown, using the EMA bounce system on EUR/USD", "option_c": "Become a full-time trader within 3 months", "option_d": "Trade every day and build wealth over time", "correct_answer": "B", "explanation": "A trading plan goal must be specific, measurable, risk-bounded, and system-tied. Vague goals produce vague results.", "topic_slug": "trading_plan"},
                        {"question": "What is a circuit breaker rule in a trading plan?", "option_a": "An indicator signalling when to enter trades after news events", "option_b": "A pre-defined drawdown trigger that forces a mandatory break from live trading to prevent compounding losses", "option_c": "A broker feature that prevents trading outside defined hours", "option_d": "A rule that automatically increases position size after winning streaks", "correct_answer": "B", "explanation": "Circuit breakers are pre-committed emergency brakes — decided while calm, executed when emotional. They prevent catastrophic loss from compounding.", "topic_slug": "trading_plan"},
                        {"question": "Plan states: 'Max 3 consecutive losses trigger a 24-hour break.' Trader takes 3 losses but feels confident about a 4th setup. They should:", "option_a": "Take the 4th — confidence from analysis overrides plan rules", "option_b": "Honour the plan rule absolutely — confidence is exactly the emotional state the rule is designed to govern", "option_c": "Reduce position size to 0.5% and enter", "option_d": "Take a 30-minute break instead of 24 hours", "correct_answer": "B", "explanation": "'Feeling confident about the 4th trade' is not an exception to the rule — it is the rule's entire purpose. The circuit breaker only functions when it is absolute.", "topic_slug": "trading_plan"},
                        {"question": "How frequently should a trading plan be formally reviewed and potentially updated?", "option_a": "Once — it is written to be permanent", "option_b": "Only when major losses occur", "option_c": "Quarterly, based on 3 months of performance data", "option_d": "Monthly — markets change too fast for longer review periods", "correct_answer": "C", "explanation": "Quarterly review uses 3 months of data — enough for statistical significance. Shorter risks changing working rules based on noise. Longer allows problems to persist too long.", "topic_slug": "trading_plan"},
                        {"question": "Most effective structural solution when a trader consistently breaks trading plan rules:", "option_a": "Memorise the rules so they cannot be forgotten", "option_b": "Print the plan, sign it, post it visibly, and add a daily written compliance checklist", "option_c": "Reduce the number of rules to improve compliance", "option_d": "Trade on a stricter schedule to reduce total decisions", "correct_answer": "B", "explanation": "Physical visibility + signed commitment + daily written compliance creates accountability that mental notes cannot. Writing 'I violated rule 4 because...' forces honest self-assessment every session.", "topic_slug": "trading_plan"}
                    ]
                },
                {
                    "title": "Performance Review and Optimization",
                    "content": """\
> [!HOOK]
> Tiger Woods hits more balls in practice than any golfer in history. But more importantly — after every session, he reviews footage of his swing and makes micro-adjustments. He does not change his entire technique. He makes one small correction, tests it, measures the result, adjusts again. That iterative review process — small data-driven improvements compounding over time — is exactly what separates elite performance from plateau performance. In trading, the journal is your swing footage. The weekly review is your coaching session.

> [!DEF]
> **Performance review** is the systematic analysis of your trading data to identify patterns in results, pinpoint consistent errors, confirm what is working, and make evidence-based adjustments — not opinion-based changes based on how you feel.

### The review cadence

**Daily (10 minutes):**
- Did I follow every rule in my trading plan?
- Emotional state rating (1–10) and what drove it
- Any rule violations and what triggered them?
- Key lesson from today

**Weekly (45–60 minutes):**
- Win rate, average win, average loss, profit factor for the week
- Consistent mistakes this week (pattern, not individual trades)
- One specific improvement to focus on next week

**Monthly (2–3 hours):**
- Equity curve analysis — direction, volatility, drawdown periods
- Performance by setup type, time of day, pair, session
- Psychological patterns — when do you break rules most?

**Quarterly (full day):**
- Statistical significance check
- System parameter review
- Goal progress assessment, annual plan update if needed

### Key metrics to track

| Metric | Acceptable | Good | Exceptional |
|--------|-----------|------|-------------|
| Win rate | 40%+ | 50%+ | 60%+ |
| Profit Factor | 1.25+ | 1.75+ | 2.5+ |
| Expectancy | >0.2R | >0.4R | >0.6R |
| Max Drawdown | <15% | <10% | <7% |
| Plan Adherence | 80%+ | 90%+ | 95%+ |

> [!EXAMPLE]
> **Monthly review insight leading to system improvement:**
>
> Trader tracks performance by time of day. Results:
> 9am–12pm WAT: Win rate 54%, PF 1.88
> 12pm–2pm WAT: Win rate 38%, PF 0.92
> 2pm–6pm WAT: Win rate 51%, PF 1.75
>
> Decision: Eliminate 12pm–2pm WAT trading window entirely.
> Next month: Overall PF improves from 1.42 to 1.71 with fewer total trades.
> One data-driven change. No new strategies. No new indicators.

> [!NGX]
> **NGX tracking:** An NGX equity trader adds one column to their journal: "Entry timing." After 60 trades they discover: stocks bought in the first 30 minutes of NGX open (10am–10:30am) win 62% of the time. Stocks bought after 1pm win 38% of the time. One journal column, 60 trades, one system-changing pattern discovered.

> [!MISTAKE]
> Reviewing only losing trades and ignoring winning ones. Winning trades contain equally important data — why did this work? Was it full plan compliance? Was it a 5-factor confluence setup? Understanding wins helps you create conditions to replicate them. Your wins contain the formula for your edge.

> [!TIP]
> The 80/20 performance review: after 100 trades, sort them by return (highest to lowest). The top 20% of trades generate approximately 80% of your total profit. Identify what those trades have in common — time of day, setup type, confluence score, pair, session. Then ruthlessly focus only on recreating those conditions for every future trade entry.

> [!TAKEAWAY]
> Performance review is the compound interest of trading skill — each weekly review makes you 1% better, and 52 weekly reviews later you are unrecognisable compared to the trader who never reviewed at all.
""",
                    "quiz": [
                        {"question": "Trader tracks performance by session: London open PF 1.9, London-NY overlap PF 1.7, NY-only PF 0.8. Data-driven action:", "option_a": "Continue trading all sessions — overall average is positive", "option_b": "Eliminate NY-only session trading entirely; concentrate on London open and London-NY overlap where edge is proven", "option_c": "Increase position size during NY-only session to recover losses faster", "option_d": "Switch to a different strategy for the NY session", "correct_answer": "B", "explanation": "PF 0.8 is a losing sub-strategy. The data says clearly: stop trading NY-only hours. Eliminating losing sessions while keeping winning ones is the fastest path to improved overall performance.", "topic_slug": "performance_review"},
                        {"question": "Minimum review frequency professionals consider non-negotiable:", "option_a": "Monthly only — daily reviews create noise", "option_b": "Weekly — catches developing patterns before they become expensive habits", "option_c": "Annually — only major overhauls matter", "option_d": "After every losing trade only", "correct_answer": "B", "explanation": "Weekly review is the professional minimum. Monthly is too infrequent — a bad habit repeated for 4 weeks compounds significantly. Weekly review catches it before it becomes costly.", "topic_slug": "performance_review"},
                        {"question": "Review reveals: win rate 48%, but trader consistently exits winners at 0.8R instead of planned 2.0R target. Correct diagnosis:", "option_a": "Win rate needs improvement — aim for 55%+", "option_b": "Premature profit-taking is destroying expectancy — holding to target is the single highest-leverage improvement available", "option_c": "The 2.0R target is unrealistic — reduce it to 0.8R", "option_d": "Strategy needs a new entry rule to produce bigger moves", "correct_answer": "B", "explanation": "Cutting winners early is the most common performance killer. With 0.8R avg win: (0.48x0.8)-(0.52x1.0) = -0.14R. With planned 2.0R: (0.48x2.0)-(0.52x1.0) = +0.44R. Same trades, completely different outcomes.", "topic_slug": "performance_review"},
                        {"question": "Why should winning trades be reviewed as carefully as losing trades?", "option_a": "Winning trades contain errors that cause future losses", "option_b": "Understanding what made your best trades succeed allows identifying and replicating those exact conditions — your wins contain the formula for your edge", "option_c": "Regulators require equal documentation of all trades", "option_d": "Winning trades indicate the strategy is about to stop working", "correct_answer": "B", "explanation": "Your top 20% of trades generate ~80% of profit. Analysing wins reveals: which session, which confluence score, which pair, which market condition — the recipe for your highest-probability setups.", "topic_slug": "performance_review"},
                        {"question": "Monthly equity curve shows consistent profitability in weeks 1–2 but consistent losses in weeks 3–4. Most likely cause through systematic review:", "option_a": "Markets are always weaker at month-end", "option_b": "A psychological pattern — possibly overconfidence after early monthly profits leading to rule violations in later weeks", "option_c": "Random variance — monthly patterns have no meaning", "option_d": "The strategy only works at month-start due to institutional rebalancing", "correct_answer": "B", "explanation": "Consistent within-month patterns almost always have a psychological component. Early wins create overconfidence; overconfidence creates rule violations; rule violations create losses. The journal review makes this pattern visible — and visible patterns can be corrected.", "topic_slug": "performance_review"}
                    ]
                },
            ]
        },

    ]  # end Advanced modules
}   # end Advanced level

]   # end ACADEMY_CURRICULUM
