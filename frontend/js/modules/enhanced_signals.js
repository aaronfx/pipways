// Enhanced Signals Page Module — InsightPro Edition v4
// Deploy to: frontend/js/modules/enhanced_signals.js

(function () {
    'use strict';

    // ═══════════════════════════════════════════════════════════════════════════
    // PATTERN EDUCATION DATA
    // ═══════════════════════════════════════════════════════════════════════════

    const PATTERN_EDUCATION = {
        'SYMMETRICAL': {
            title: 'Symmetrical Triangle',
            description: `The Symmetrical Triangle is a continuation pattern that develops when price consolidates between converging trendlines, with lower highs and higher lows forming equal slopes.

This pattern represents a period of indecision where neither buyers nor sellers have control. Volume typically decreases as the pattern develops, indicating a buildup of pressure.

A breakout occurs when price decisively moves beyond one of the trendlines, usually in the direction of the prior trend. The breakout is often accompanied by increased volume.

Price targets are typically calculated by measuring the height of the triangle at its widest point and projecting that distance from the breakout level.`
        },
        'TRIANGLE': {
            title: 'Triangle Pattern',
            description: `The Triangle is a consolidation pattern formed by converging trendlines as price makes a series of lower highs and higher lows.

This pattern indicates a battle between buyers and sellers, with volatility contracting as the pattern matures. The narrowing price range suggests an imminent breakout.

Traders watch for a decisive close outside the triangle boundaries to confirm the breakout direction. False breakouts are common, so confirmation is essential.

The measured move target equals the triangle's height projected from the breakout point.`
        },
        'WEDGE': {
            title: 'Wedge Pattern',
            description: `The Wedge is a reversal pattern characterized by converging trendlines that both slope in the same direction — either up (rising wedge) or down (falling wedge).

A Rising Wedge forms during an uptrend and signals bearish reversal, while a Falling Wedge forms during a downtrend and signals bullish reversal.

The pattern shows momentum weakening as price makes smaller advances within the wedge. Volume typically diminishes as the pattern develops.

Breakouts usually occur in the opposite direction of the wedge slope. Price targets are set by measuring the wedge's height and projecting from the breakout.`
        },
        'FLAG': {
            title: 'Flag Pattern',
            description: `The Flag is a short-term continuation pattern that develops after a strong directional move (the flagpole), representing a brief pause before the trend resumes.

The flag portion consists of parallel trendlines sloping against the prior trend direction. This counter-trend consolidation typically lasts 1-3 weeks.

Volume contracts during flag formation and expands on the breakout. The pattern is considered reliable when the flagpole shows strong momentum.

Price objectives are calculated by measuring the flagpole length and adding it to the breakout level.`
        },
        'PENNANT': {
            title: 'Pennant Pattern',
            description: `The Pennant is a short-term continuation pattern that develops after a strong directional move, symbolizing a pause in momentum. It resembles a small symmetrical triangle formed by converging trendlines as volatility temporarily contracts.

The pattern shows that both buyers and sellers are waiting for new direction following an impulsive move.

A breakout in the direction of the prior trend validates the pattern and signals continuation.

Price objectives are often set by adding or subtracting the length of the prior move (the flagpole) from the breakout level.`
        },
        'DOUBLE_BOTTOM': {
            title: 'Double Bottom',
            description: `The Double Bottom is a bullish reversal pattern that forms after a downtrend, consisting of two consecutive troughs at approximately the same price level.

The pattern resembles the letter "W" and indicates that selling pressure has been tested twice at the support level and failed to push prices lower.

Confirmation occurs when price breaks above the peak between the two bottoms (the neckline). Volume often increases on the second bottom and the breakout.

The price target is calculated by measuring the distance from the bottoms to the neckline and projecting that distance above the breakout.`
        },
        'DOUBLE_TOP': {
            title: 'Double Top',
            description: `The Double Top is a bearish reversal pattern that forms after an uptrend, consisting of two consecutive peaks at approximately the same price level.

The pattern resembles the letter "M" and indicates that buying pressure has been tested twice at the resistance level and failed to push prices higher.

Confirmation occurs when price breaks below the trough between the two tops (the neckline). Volume often decreases on the second top.

The price target is calculated by measuring the distance from the tops to the neckline and projecting that distance below the breakdown.`
        },
        'BREAKOUT': {
            title: 'Breakout Setup',
            description: `A Breakout occurs when price moves decisively beyond a significant support or resistance level, signaling the start of a new trend or continuation of an existing one.

Key characteristics include increased volume on the breakout, a clear break of the level (not just a wick), and follow-through in subsequent candles.

False breakouts are common, so traders often wait for a candle close beyond the level or a retest of the broken level as new support/resistance.

Stop losses are typically placed below the breakout level for longs or above for shorts.`
        },
        'SUPPORT': {
            title: 'Support Level',
            description: `A Support level is a price zone where buying interest is strong enough to overcome selling pressure, causing price to bounce or reverse.

Support forms at previous lows, round numbers, moving averages, or areas of high trading volume. The more times a level is tested, the more significant it becomes.

Traders look for bullish candlestick patterns, divergences, or volume spikes at support to confirm potential reversals.

When support breaks, it often becomes resistance. The strength of support is measured by how many times it has held and the time elapsed since it formed.`
        },
        'REVERSAL': {
            title: 'Reversal Pattern',
            description: `A Reversal pattern signals a potential change in the prevailing trend direction, from bullish to bearish or vice versa.

Key reversal signals include exhaustion candles, divergence between price and momentum indicators, and pattern completions at key levels.

Confirmation is essential before trading reversals — premature entries against the trend can be costly. Wait for a clear break of structure.

Risk management is critical as reversals can take time to develop and may involve multiple false signals before the actual turn.`
        }
    };

    function getPatternEducation(pattern) {
        const key = (pattern || 'BREAKOUT').toUpperCase().replace(/[^A-Z]/g, '_');
        if (PATTERN_EDUCATION[key]) return PATTERN_EDUCATION[key];
        for (const [k, v] of Object.entries(PATTERN_EDUCATION)) {
            if (key.includes(k) || k.includes(key)) return v;
        }
        return {
            title: pattern || 'Pattern Analysis',
            description: `This trading pattern has been identified by our AI analysis system based on technical chart formations and price action.

The pattern suggests a potential trading opportunity with defined entry, target, and stop loss levels.

Always conduct your own analysis and use proper risk management when trading.`
        };
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // CSS — InsightPro Style
    // ═══════════════════════════════════════════════════════════════════════════

    const IQ_STYLES = `
    /* ══════════════════════════════════════════════════════════════════════════
       InsightPro Signal Cards — Premium Trading UI
       ══════════════════════════════════════════════════════════════════════════ */

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    #signalsGrid {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 20px !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    @media (max-width: 1100px) {
        #signalsGrid { grid-template-columns: repeat(2, 1fr) !important; }
    }
    @media (max-width: 700px) {
        #signalsGrid { grid-template-columns: 1fr !important; }
    }

    /* ── Signal Card ─────────────────────────────────────────────────────────── */
    .iq-card {
        background: linear-gradient(180deg, #1a1a1e 0%, #111113 100%);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        overflow: hidden;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .iq-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    }

    /* Header with badges */
    .iq-header {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 16px 16px 12px;
        position: relative;
    }

    /* Live Trade Badge */
    .iq-live-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 18px;
        background: linear-gradient(135deg, #00c9a7 0%, #00b894 100%);
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.1em;
        color: #000;
        text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(0, 200, 150, 0.3);
    }
    .iq-live-badge::before {
        content: '';
        width: 6px;
        height: 6px;
        background: #000;
        border-radius: 50%;
        animation: iq-pulse 1.5s ease-in-out infinite;
    }
    @keyframes iq-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }

    /* TradingView Icon */
    .iq-tv-icon {
        position: absolute;
        right: 16px;
        top: 50%;
        transform: translateY(-50%);
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        text-decoration: none;
    }
    .iq-tv-icon:hover {
        transform: translateY(-50%) scale(1.1);
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }
    .iq-tv-icon svg {
        width: 16px;
        height: 16px;
        fill: #fff;
    }

    /* Symbol Row */
    .iq-symbol-row {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 0 20px 12px;
    }

    /* Asset Icon */
    .iq-asset-icon {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        font-weight: 800;
        flex-shrink: 0;
        border: 3px solid rgba(255,255,255,0.1);
    }
    .iq-asset-icon.gold {
        background: linear-gradient(145deg, #ffd700 0%, #daa520 50%, #b8860b 100%);
        color: #1a1a1a;
        border-color: rgba(255,215,0,0.3);
        box-shadow: 0 4px 15px rgba(255,215,0,0.2);
    }
    .iq-asset-icon.silver {
        background: linear-gradient(145deg, #e8e8e8 0%, #c0c0c0 50%, #a8a8a8 100%);
        color: #1a1a1a;
        border-color: rgba(192,192,192,0.3);
    }
    .iq-asset-icon.crypto {
        background: linear-gradient(145deg, #f7931a 0%, #e67e00 100%);
        color: #fff;
        border-color: rgba(247,147,26,0.3);
        box-shadow: 0 4px 15px rgba(247,147,26,0.2);
    }
    .iq-asset-icon.indices {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        color: #fff;
        border-color: rgba(255,255,255,0.15);
        font-size: 13px;
    }
    .iq-asset-icon.forex {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        color: #fff;
        border-color: rgba(255,255,255,0.15);
        font-size: 13px;
    }

    .iq-symbol-info {
        flex: 1;
        min-width: 0;
    }
    .iq-symbol-name {
        display: flex;
        align-items: baseline;
        gap: 10px;
    }
    .iq-symbol-text {
        font-size: 18px;
        font-weight: 700;
        color: #fff;
        letter-spacing: -0.02em;
    }
    .iq-pattern-tag {
        font-size: 12px;
        font-weight: 500;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }

    /* Order Badge */
    .iq-order-row {
        display: flex;
        justify-content: center;
        padding: 0 20px 16px;
    }
    .iq-order-badge {
        display: inline-block;
        padding: 10px 28px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .iq-order-buy {
        background: linear-gradient(135deg, #00c9a7 0%, #00b894 100%);
        color: #000;
        box-shadow: 0 4px 15px rgba(0, 200, 150, 0.25);
    }
    .iq-order-sell {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
        color: #fff;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.25);
    }

    /* Price Grid */
    .iq-prices {
        padding: 0 20px 16px;
    }
    .iq-price-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255,255,255,0.04);
    }
    .iq-price-row:last-child {
        border-bottom: none;
    }
    .iq-price-label {
        font-size: 14px;
        font-weight: 500;
        color: #6b7280;
    }
    .iq-price-value {
        font-size: 15px;
        font-weight: 600;
        font-family: 'SF Mono', 'JetBrains Mono', 'Consolas', monospace;
        color: #fff;
    }
    .iq-price-value.target { color: #00d4aa; }
    .iq-price-value.stop { color: #ff6b6b; }
    .iq-price-value.expires { color: #f5a623; }

    /* Chart */
    .iq-chart {
        width: 100%;
        height: 140px;
        background: linear-gradient(180deg, #0d0d10 0%, #0a0a0c 100%);
        position: relative;
        overflow: hidden;
    }
    .iq-chart svg {
        width: 100%;
        height: 100%;
    }
    .iq-tf-badge {
        position: absolute;
        bottom: 10px;
        right: 12px;
        width: 32px;
        height: 32px;
        background: rgba(0,0,0,0.8);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 700;
        color: #fff;
    }

    /* Learn More Button */
    .iq-learn-btn {
        display: block;
        width: calc(100% - 32px);
        margin: 0 16px 16px;
        padding: 14px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        color: #fff;
        font-size: 13px;
        font-weight: 600;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    .iq-learn-btn:hover {
        background: rgba(255,255,255,0.06);
        border-color: rgba(255,255,255,0.15);
    }

    /* Tab Bar */
    .iq-tab-bar {
        display: flex;
        gap: 32px;
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    .iq-tab-item {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 14px;
        font-weight: 500;
        color: #6b7280;
        cursor: pointer;
        transition: color 0.2s ease;
        padding: 6px 0;
    }
    .iq-tab-item:hover { color: #9ca3af; }
    .iq-tab-item.active { color: #fff; }
    .iq-tab-dot {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
    }
    .iq-tab-item.ai-driven .iq-tab-dot {
        background: linear-gradient(135deg, #f5a623, #e67e00);
        color: #000;
    }
    .iq-tab-item.analysis-iq .iq-tab-dot {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: #fff;
    }

    /* ══════════════════════════════════════════════════════════════════════════
       Modal — InsightPro Style
       ══════════════════════════════════════════════════════════════════════════ */
    .iq-modal-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.92);
        backdrop-filter: blur(8px);
        z-index: 9999;
        display: flex;
        align-items: flex-start;
        justify-content: center;
        padding: 32px 16px;
        overflow-y: auto;
        opacity: 0;
        transition: opacity 0.25s ease;
        pointer-events: none;
    }
    .iq-modal-overlay.open {
        opacity: 1;
        pointer-events: all;
    }
    .iq-modal {
        background: linear-gradient(180deg, #1a1a1e 0%, #111113 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        width: 100%;
        max-width: 900px;
        margin: 20px 0;
        overflow: hidden;
        box-shadow: 0 32px 64px rgba(0,0,0,0.5);
    }

    /* Modal Header */
    .iq-modal-header {
        background: linear-gradient(180deg, #0d0d10 0%, #111113 100%);
        padding: 24px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }

    /* Top row: Flag, Symbol, Name, Price */
    .iq-modal-top {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 16px;
    }
    .iq-modal-flag {
        width: 52px;
        height: 40px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        background: #1a1a2e;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .iq-modal-symbol-badge {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: #fff;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.02em;
    }
    .iq-modal-pair-name {
        font-size: 22px;
        font-weight: 600;
        color: #fff;
        flex: 1;
    }
    .iq-modal-price-box {
        text-align: right;
    }
    .iq-modal-live-price {
        font-size: 36px;
        font-weight: 700;
        color: #fff;
        font-family: 'SF Mono', 'JetBrains Mono', monospace;
        letter-spacing: -0.02em;
    }
    .iq-modal-price-change {
        font-size: 14px;
        font-weight: 600;
        margin-top: 2px;
    }
    .iq-modal-price-change.up { color: #00d4aa; }
    .iq-modal-price-change.down { color: #ff6b6b; }

    /* Badges row */
    .iq-modal-badges {
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
    }
    .iq-modal-live-badge {
        display: inline-flex;
        align-items: center;
        padding: 8px 16px;
        background: linear-gradient(135deg, #f5a623 0%, #e67e00 100%);
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.1em;
        color: #000;
        text-transform: uppercase;
    }

    /* Info grid */
    .iq-modal-info {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 20px;
    }
    @media (max-width: 700px) {
        .iq-modal-info { grid-template-columns: repeat(3, 1fr); }
    }
    .iq-modal-info-item {
        text-align: center;
    }
    .iq-modal-info-value {
        font-size: 18px;
        font-weight: 700;
        color: #00d4aa;
        font-family: 'SF Mono', 'JetBrains Mono', monospace;
        margin-bottom: 4px;
    }
    .iq-modal-info-value.pattern {
        color: #fff;
        font-family: 'Inter', sans-serif;
        font-size: 16px;
    }
    .iq-modal-info-value.entry { color: #fff; }
    .iq-modal-info-value.stop { color: #ff6b6b; }
    .iq-modal-info-label {
        font-size: 11px;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Sentiment */
    .iq-sentiment {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }
    .iq-sentiment-bar {
        width: 80px;
        height: 6px;
        background: #333;
        border-radius: 3px;
        overflow: hidden;
        display: flex;
    }
    .iq-sentiment-bear { background: linear-gradient(90deg, #ff6b6b, #ff8787); }
    .iq-sentiment-bull { background: linear-gradient(90deg, #00d4aa, #00e6b8); }
    .iq-sentiment-label {
        font-size: 11px;
        font-weight: 600;
        color: #6b7280;
    }

    /* Modal Body */
    .iq-modal-body {
        padding: 28px;
    }

    /* Chart in modal */
    .iq-modal-chart {
        width: 100%;
        height: 220px;
        background: linear-gradient(180deg, #0d0d10 0%, #0a0a0c 100%);
        border-radius: 12px;
        margin-bottom: 28px;
        overflow: hidden;
        position: relative;
    }
    .iq-modal-chart svg {
        width: 100%;
        height: 100%;
    }
    .iq-modal-chart .iq-tf-badge {
        bottom: 14px;
        right: 14px;
        width: 36px;
        height: 36px;
        font-size: 12px;
    }

    /* Trade Idea section */
    .iq-modal-title-row {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 12px;
    }
    .iq-modal-title {
        font-size: 28px;
        font-weight: 700;
        color: #fff;
    }
    .iq-modal-tv-link {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        transition: transform 0.2s ease;
    }
    .iq-modal-tv-link:hover { transform: scale(1.1); }
    .iq-modal-tv-link svg { width: 18px; height: 18px; fill: #fff; }

    .iq-modal-meta {
        font-size: 13px;
        color: #f5a623;
        margin-bottom: 24px;
        line-height: 1.6;
    }

    .iq-modal-description {
        font-size: 16px;
        line-height: 1.9;
        color: #d1d5db;
        white-space: pre-line;
    }

    /* Modal Footer */
    .iq-modal-footer {
        padding: 20px 28px;
        border-top: 1px solid rgba(255,255,255,0.06);
        display: flex;
        gap: 14px;
    }
    .iq-modal-btn {
        padding: 14px 32px;
        border-radius: 10px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .iq-modal-btn-primary {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        border: none;
        color: #fff;
        flex: 1;
    }
    .iq-modal-btn-primary:hover {
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
    }
    .iq-modal-btn-secondary {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.1);
        color: #9ca3af;
    }
    .iq-modal-btn-secondary:hover {
        background: rgba(255,255,255,0.06);
        color: #fff;
    }

    /* Countdown urgent */
    .iq-countdown.urgent { color: #ff6b6b !important; animation: iq-urgent 1s infinite; }
    @keyframes iq-urgent {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    `;

    function injectStyles() {
        if (document.getElementById('iq-styles')) return;
        const el = document.createElement('style');
        el.id = 'iq-styles';
        el.textContent = IQ_STYLES;
        document.head.appendChild(el);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // API
    // ═══════════════════════════════════════════════════════════════════════════

    async function apiGet(endpoint) {
        const token = localStorage.getItem('pipways_token');
        if (!token) throw new Error('Not authenticated');

        const response = await fetch(endpoint, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        if (response.status === 401) {
            localStorage.removeItem('pipways_token');
            window.location.href = '/';
            throw new Error('Unauthorized');
        }
        if (response.status === 402) throw new Error('Subscription required');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        return response.json();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // STATE
    // ═══════════════════════════════════════════════════════════════════════════

    let allSignals = [];
    let filteredSignals = [];
    let currentTab = 'ai-driven';
    let updateInterval = null;
    let countdownTimers = [];
    let iqModal = null;

    // ═══════════════════════════════════════════════════════════════════════════
    // INIT
    // ═══════════════════════════════════════════════════════════════════════════

    function init() {
        console.log('[InsightPro] Initialising v4...');
        injectStyles();
        injectTabBar();
        injectModal();
        setupEventListeners();
        loadSignals();

        if (updateInterval) clearInterval(updateInterval);
        updateInterval = setInterval(loadSignals, 60000);
    }

    function injectTabBar() {
        if (document.getElementById('iq-tab-bar')) return;

        const bar = document.createElement('div');
        bar.id = 'iq-tab-bar';
        bar.className = 'iq-tab-bar';
        bar.innerHTML = `
            <div id="iq-tab-ai" class="iq-tab-item ai-driven active" data-tab="ai-driven">
                <span class="iq-tab-dot">✦</span>
                AI-Driven Trade Ideas
            </div>
            <div id="iq-tab-pattern" class="iq-tab-item analysis-iq" data-tab="analysis-iq">
                <span class="iq-tab-dot">◈</span>
                Pattern Trade Ideas
            </div>
        `;

        const grid = document.getElementById('signalsGrid');
        const parent = grid?.parentElement;
        if (parent) parent.insertBefore(bar, grid);
    }

    function injectModal() {
        if (document.getElementById('iq-modal-overlay')) return;

        const overlay = document.createElement('div');
        overlay.id = 'iq-modal-overlay';
        overlay.className = 'iq-modal-overlay';
        overlay.innerHTML = `<div class="iq-modal" id="iq-modal"></div>`;
        document.body.appendChild(overlay);
        iqModal = overlay;

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeModal();
        });
    }

    function setupEventListeners() {
        document.addEventListener('click', (e) => {
            const tab = e.target.closest('[data-tab]');
            if (tab) switchTab(tab.dataset.tab);
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeModal();
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // DATA
    // ═══════════════════════════════════════════════════════════════════════════

    async function loadSignals() {
        const grid = document.getElementById('signalsGrid');
        if (!grid) return;

        try {
            const signals = await apiGet('/signals/enhanced');
            allSignals = signals || [];
            applyFilters();
        } catch (error) {
            console.error('[InsightPro] Error:', error);
        }
    }

    function applyFilters() {
        if (currentTab === 'analysis-iq') {
            filteredSignals = allSignals.filter(s => s.is_pattern_idea === true);
        } else {
            filteredSignals = allSignals.filter(s => (s.confidence || 0) >= 70 && !s.is_pattern_idea);
        }
        renderSignals();
    }

    function switchTab(tab) {
        currentTab = tab;
        document.getElementById('iq-tab-ai')?.classList.toggle('active', tab === 'ai-driven');
        document.getElementById('iq-tab-pattern')?.classList.toggle('active', tab === 'analysis-iq');
        applyFilters();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // RENDER
    // ═══════════════════════════════════════════════════════════════════════════

    function renderSignals() {
        const grid = document.getElementById('signalsGrid');
        if (!grid) return;

        countdownTimers.forEach(clearInterval);
        countdownTimers = [];

        if (!filteredSignals.length) {
            grid.innerHTML = `
                <div class="col-span-full text-center py-16">
                    <p style="color:#6b7280; font-size:15px;">No active signals found.</p>
                </div>`;
            return;
        }

        grid.innerHTML = filteredSignals.map(s => renderCard(s)).join('');
        startCountdowns();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // CHART SVG GENERATOR
    // ═══════════════════════════════════════════════════════════════════════════

    function generateChartSVG(pattern, isBuy, seed = 1, isModal = false) {
        const w = isModal ? 860 : 280;
        const h = isModal ? 220 : 140;
        const patternType = (pattern || '').toUpperCase();

        // Pseudo-random
        let s = seed;
        const rand = (min, max) => { s = (s * 9301 + 49297) % 233280; return min + (s / 233280) * (max - min); };

        // Generate candles
        const numCandles = isModal ? 50 : 28;
        const candles = [];
        let price = 50;
        const trend = isBuy ? 0.15 : -0.15;

        for (let i = 0; i < numCandles; i++) {
            const vol = 1.5 + rand(0, 2.5);
            const open = price;
            const change = trend + rand(-1.2, 1.2);
            const close = open + change;
            const high = Math.max(open, close) + rand(0.2, vol);
            const low = Math.min(open, close) - rand(0.2, vol);
            candles.push({ open, close, high, low, bull: close > open });
            price = close;
        }

        // Normalize
        const allP = candles.flatMap(c => [c.high, c.low]);
        const minP = Math.min(...allP), maxP = Math.max(...allP);
        const range = maxP - minP || 1;
        const padY = isModal ? 20 : 15;
        const toY = p => h - padY - ((p - minP) / range) * (h - padY * 2);

        // Draw candles
        const gap = (w - 20) / numCandles;
        const cw = isModal ? 10 : 6;
        let svg = '';

        candles.forEach((c, i) => {
            const x = 10 + i * gap + gap / 2;
            const color = c.bull ? '#26a69a' : '#ef5350';
            const yH = toY(c.high), yL = toY(c.low);
            const yO = toY(c.open), yC = toY(c.close);
            const top = Math.min(yO, yC);
            const ht = Math.max(1, Math.abs(yO - yC));
            
            // Wick
            svg += `<line x1="${x}" y1="${yH}" x2="${x}" y2="${yL}" stroke="${color}" stroke-width="1" stroke-linecap="round"/>`;
            // Body
            svg += `<rect x="${x - cw/2}" y="${top}" width="${cw}" height="${ht}" fill="${color}" rx="1"/>`;
        });

        // Pattern lines
        const lc = '#818cf8'; // Lighter purple for better visibility
        const lw = isModal ? 2.5 : 2;
        const midY = toY((maxP + minP) / 2);
        const topY = toY(maxP - range * 0.12);
        const botY = toY(minP + range * 0.12);
        const startX = isModal ? 60 : 20;
        const endX = w - (isModal ? 60 : 20);

        if (patternType.includes('SYMMETRICAL') || patternType.includes('TRIANGLE')) {
            // Converging triangle
            svg += `<line x1="${startX}" y1="${topY}" x2="${endX}" y2="${midY+3}" stroke="${lc}" stroke-width="${lw}" stroke-linecap="round"/>`;
            svg += `<line x1="${startX}" y1="${botY}" x2="${endX}" y2="${midY-3}" stroke="${lc}" stroke-width="${lw}" stroke-linecap="round"/>`;
        } else if (patternType.includes('WEDGE')) {
            // Wedge - both lines slope same direction
            const slopeDir = isBuy ? -1 : 1;
            const topStart = toY(maxP - range * 0.15);
            const botStart = toY(minP + range * 0.25);
            const topEnd = topStart + slopeDir * (h * 0.15);
            const botEnd = botStart + slopeDir * (h * 0.25);
            svg += `<line x1="${startX}" y1="${topStart}" x2="${endX}" y2="${topEnd}" stroke="${lc}" stroke-width="${lw}" stroke-linecap="round"/>`;
            svg += `<line x1="${startX}" y1="${botStart}" x2="${endX}" y2="${botEnd}" stroke="${lc}" stroke-width="${lw}" stroke-linecap="round"/>`;
        } else if (patternType.includes('FLAG')) {
            // Parallel sloping lines
            const flagStart = isModal ? 180 : 60;
            const y1s = toY(minP + range * 0.7);
            const y2s = toY(minP + range * 0.4);
            const slope = isBuy ? 0.08 : -0.08;
            svg += `<line x1="${flagStart}" y1="${y1s}" x2="${endX}" y2="${y1s + slope * (endX - flagStart)}" stroke="${lc}" stroke-width="${lw}" stroke-linecap="round"/>`;
            svg += `<line x1="${flagStart}" y1="${y2s}" x2="${endX}" y2="${y2s + slope * (endX - flagStart)}" stroke="${lc}" stroke-width="${lw}" stroke-linecap="round"/>`;
        } else if (patternType.includes('PENNANT')) {
            // Small converging triangle
            const cx = w * 0.55;
            const spread = isModal ? 100 : 55;
            const vSpread = isModal ? 30 : 18;
            svg += `<line x1="${cx - spread}" y1="${midY - vSpread}" x2="${cx + spread * 0.7}" y2="${midY}" stroke="${lc}" stroke-width="${lw}" stroke-linecap="round"/>`;
            svg += `<line x1="${cx - spread}" y1="${midY + vSpread}" x2="${cx + spread * 0.7}" y2="${midY}" stroke="${lc}" stroke-width="${lw}" stroke-linecap="round"/>`;
        } else if (patternType.includes('DOUBLE') && patternType.includes('BOTTOM')) {
            const by = toY(minP + range * 0.08);
            const x1 = isModal ? 200 : 70, x2 = isModal ? 550 : 180;
            const r = isModal ? 8 : 5;
            svg += `<circle cx="${x1}" cy="${by}" r="${r}" fill="none" stroke="${lc}" stroke-width="${lw}"/>`;
            svg += `<circle cx="${x2}" cy="${by}" r="${r}" fill="none" stroke="${lc}" stroke-width="${lw}"/>`;
            svg += `<line x1="${x1}" y1="${by}" x2="${x2}" y2="${by}" stroke="${lc}" stroke-width="1" stroke-dasharray="6,4"/>`;
        } else if (patternType.includes('DOUBLE') && patternType.includes('TOP')) {
            const ty = toY(maxP - range * 0.08);
            const x1 = isModal ? 200 : 70, x2 = isModal ? 550 : 180;
            const r = isModal ? 8 : 5;
            svg += `<circle cx="${x1}" cy="${ty}" r="${r}" fill="none" stroke="${lc}" stroke-width="${lw}"/>`;
            svg += `<circle cx="${x2}" cy="${ty}" r="${r}" fill="none" stroke="${lc}" stroke-width="${lw}"/>`;
            svg += `<line x1="${x1}" y1="${ty}" x2="${x2}" y2="${ty}" stroke="${lc}" stroke-width="1" stroke-dasharray="6,4"/>`;
        } else {
            // Default: horizontal support/resistance
            svg += `<line x1="${startX}" y1="${midY}" x2="${endX}" y2="${midY}" stroke="${lc}" stroke-width="${lw}" stroke-dasharray="8,4"/>`;
        }

        return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><rect width="100%" height="100%" fill="transparent"/>${svg}</svg>`;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // CARD RENDER
    // ═══════════════════════════════════════════════════════════════════════════

    function getAssetIcon(symbol) {
        const map = {
            'XAUUSD': { text: 'Au', cls: 'gold' },
            'XAGUSD': { text: 'Ag', cls: 'silver' },
            'BTCUSD': { text: 'B', cls: 'crypto' },
            'ETHUSD': { text: 'Ξ', cls: 'crypto' },
            'US30': { text: 'US', cls: 'indices' },
            'GER40': { text: 'DE', cls: 'indices' },
            'CHINA50': { text: 'CN', cls: 'indices' },
        };
        if (map[symbol]) return map[symbol];

        // Forex pairs - use country code
        const cc = symbol?.substring(0, 2);
        return { text: cc || '??', cls: 'forex' };
    }

    function getFlag(symbol) {
        const flags = {
            'EU': '🇪🇺', 'GB': '🇬🇧', 'US': '🇺🇸', 'JP': '🇯🇵', 
            'AU': '🇦🇺', 'NZ': '🇳🇿', 'CA': '🇨🇦', 'CH': '🇨🇭',
            'CN': '🇨🇳', 'DE': '🇩🇪', 'XA': '🪙'
        };
        const cc = symbol?.substring(0, 2);
        return flags[cc] || '🌐';
    }

    function renderCard(signal) {
        const isBuy = (signal.direction || '').toUpperCase().includes('BUY');
        const pattern = (signal.pattern || 'PATTERN').replace(/_/g, ' ');
        const patternShort = pattern.length > 14 ? pattern.substring(0, 12) + '...' : pattern;
        const tf = signal.timeframe || '4H';
        const icon = getAssetIcon(signal.symbol);
        const tvSymbol = getTVSymbol(signal.symbol);

        // TradingView icon SVG
        const tvSvg = `<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M7 14l3-3 2 2 5-5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

        return `
        <div class="iq-card">
            <!-- Header -->
            <div class="iq-header">
                <span class="iq-live-badge">Live Trade</span>
                <a href="https://www.tradingview.com/chart/?symbol=${tvSymbol}" target="_blank" class="iq-tv-icon" title="View on TradingView">
                    ${tvSvg}
                </a>
            </div>

            <!-- Symbol -->
            <div class="iq-symbol-row">
                <div class="iq-asset-icon ${icon.cls}">${icon.text}</div>
                <div class="iq-symbol-info">
                    <div class="iq-symbol-name">
                        <span class="iq-symbol-text">${esc(signal.symbol)}</span>
                        <span class="iq-pattern-tag">${esc(patternShort)}</span>
                    </div>
                </div>
            </div>

            <!-- Order Badge -->
            <div class="iq-order-row">
                <span class="iq-order-badge ${isBuy ? 'iq-order-buy' : 'iq-order-sell'}">
                    ${isBuy ? 'BUY STOP' : 'SELL STOP'}
                </span>
            </div>

            <!-- Prices -->
            <div class="iq-prices">
                <div class="iq-price-row">
                    <span class="iq-price-label">Entry</span>
                    <span class="iq-price-value">${esc(signal.entry || '—')}</span>
                </div>
                <div class="iq-price-row">
                    <span class="iq-price-label">Target</span>
                    <span class="iq-price-value target">${esc(signal.target || '—')}</span>
                </div>
                <div class="iq-price-row">
                    <span class="iq-price-label">Stop</span>
                    <span class="iq-price-value stop">${esc(signal.stop || '—')}</span>
                </div>
                <div class="iq-price-row">
                    <span class="iq-price-label">Expires</span>
                    <span class="iq-price-value expires iq-countdown" data-expiry="${signal.expires_at || ''}">${formatCountdown(signal.expires_at)}</span>
                </div>
            </div>

            <!-- Chart -->
            <div class="iq-chart">
                ${generateChartSVG(signal.pattern, isBuy, signal.id, false)}
                <div class="iq-tf-badge">${esc(tf)}</div>
            </div>

            <!-- Learn More -->
            <button class="iq-learn-btn" onclick="window.EnhancedSignalsPage.openDeepInsight(${signal.id})">
                Learn More
            </button>
        </div>`;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // MODAL
    // ═══════════════════════════════════════════════════════════════════════════

    function getTVSymbol(symbol) {
        const map = {
            'EURUSD': 'FX:EURUSD', 'GBPUSD': 'FX:GBPUSD', 'USDJPY': 'FX:USDJPY',
            'AUDUSD': 'FX:AUDUSD', 'NZDUSD': 'FX:NZDUSD', 'AUDCAD': 'FX:AUDCAD',
            'GBPJPY': 'FX:GBPJPY', 'EURJPY': 'FX:EURJPY',
            'XAUUSD': 'OANDA:XAUUSD', 'XAGUSD': 'OANDA:XAGUSD',
            'US30': 'TVC:DJI', 'GER40': 'XETR:DAX', 'CHINA50': 'SSE:000001',
            'BTCUSD': 'BITSTAMP:BTCUSD', 'ETHUSD': 'BITSTAMP:ETHUSD',
        };
        return map[symbol] || `FX:${symbol}`;
    }

    function getPairName(symbol) {
        const names = {
            'EURUSD': 'Euro vs US Dollar',
            'GBPUSD': 'British Pound vs US Dollar',
            'USDJPY': 'US Dollar vs Japanese Yen',
            'AUDUSD': 'Australian Dollar vs US Dollar',
            'NZDUSD': 'New Zealand Dollar vs US Dollar',
            'AUDCAD': 'Australian Dollar vs Canadian Dollar',
            'GBPJPY': 'British Pound vs Japanese Yen',
            'EURJPY': 'Euro vs Japanese Yen',
            'XAUUSD': 'Gold vs US Dollar',
            'XAGUSD': 'Silver vs US Dollar',
            'US30': 'Dow Jones Industrial Average',
            'GER40': 'Germany 40 Index',
            'CHINA50': 'China A50 Index',
            'BTCUSD': 'Bitcoin vs US Dollar',
            'ETHUSD': 'Ethereum vs US Dollar',
        };
        return names[symbol] || signal.full_name || symbol;
    }

    function openDeepInsight(signalId) {
        const signal = allSignals.find(s => s.id === signalId);
        if (!signal || !iqModal) return;

        const isBuy = (signal.direction || '').toUpperCase().includes('BUY');
        const pattern = (signal.pattern || 'Pattern').replace(/_/g, ' ');
        const edu = getPatternEducation(signal.pattern);
        const tvSymbol = getTVSymbol(signal.symbol);
        const flag = getFlag(signal.symbol);
        const pairName = getPairName(signal.symbol);
        const bullish = signal.sentiment_bullish || 50;
        const bearish = 100 - bullish;
        const tf = signal.timeframe || '4H';

        // Timestamps
        const pubDate = signal.created_at 
            ? new Date(signal.created_at).toLocaleString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
            : '—';
        const expDate = signal.expires_at 
            ? new Date(signal.expires_at).toLocaleString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
            : '—';

        const tvSvg = `<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M7 14l3-3 2 2 5-5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

        const modal = document.getElementById('iq-modal');
        modal.innerHTML = `
            <!-- Header -->
            <div class="iq-modal-header">
                <div class="iq-modal-top">
                    <div class="iq-modal-flag">${flag}</div>
                    <span class="iq-modal-symbol-badge">${esc(signal.symbol)}</span>
                    <span class="iq-modal-pair-name">${esc(pairName)}</span>
                    <div class="iq-modal-price-box">
                        <div class="iq-modal-live-price">${esc(signal.entry || '—')}</div>
                        <div class="iq-modal-price-change ${isBuy ? 'up' : 'down'}">
                            ${isBuy ? '▲' : '▼'} ${esc(signal.price_change || '+0.00%')}
                        </div>
                    </div>
                </div>

                <div class="iq-modal-badges">
                    <span class="iq-order-badge ${isBuy ? 'iq-order-buy' : 'iq-order-sell'}">
                        ${isBuy ? 'BUY STOP' : 'SELL STOP'}
                    </span>
                    <span class="iq-modal-live-badge">Live Trade</span>
                </div>

                <div class="iq-modal-info">
                    <div class="iq-modal-info-item">
                        <div class="iq-modal-info-value pattern">${esc(pattern)}</div>
                        <div class="iq-modal-info-label">Pattern</div>
                    </div>
                    <div class="iq-modal-info-item">
                        <div class="iq-modal-info-value entry">${esc(signal.entry || '—')}</div>
                        <div class="iq-modal-info-label">Entry</div>
                    </div>
                    <div class="iq-modal-info-item">
                        <div class="iq-modal-info-value">${esc(signal.target || '—')}</div>
                        <div class="iq-modal-info-label">Target</div>
                    </div>
                    <div class="iq-modal-info-item">
                        <div class="iq-modal-info-value stop">${esc(signal.stop || '—')}</div>
                        <div class="iq-modal-info-label">Stop</div>
                    </div>
                    <div class="iq-modal-info-item">
                        <div class="iq-sentiment">
                            <span class="iq-sentiment-label">🐻 ${bearish}%</span>
                            <div class="iq-sentiment-bar">
                                <div class="iq-sentiment-bear" style="width:${bearish}%"></div>
                                <div class="iq-sentiment-bull" style="width:${bullish}%"></div>
                            </div>
                            <span class="iq-sentiment-label">${bullish}% 🐂</span>
                        </div>
                        <div class="iq-modal-info-label">News Sentiment</div>
                    </div>
                </div>
            </div>

            <!-- Body -->
            <div class="iq-modal-body">
                <!-- Chart -->
                <div class="iq-modal-chart">
                    ${generateChartSVG(signal.pattern, isBuy, signal.id, true)}
                    <div class="iq-tf-badge">${esc(tf)}</div>
                </div>

                <!-- Trade Idea -->
                <div class="iq-modal-title-row">
                    <span class="iq-modal-title">Trade Idea</span>
                    <a href="https://www.tradingview.com/chart/?symbol=${tvSymbol}" target="_blank" class="iq-modal-tv-link" title="View on TradingView">
                        ${tvSvg}
                    </a>
                </div>

                <span class="iq-modal-live-badge" style="margin-bottom:16px; display:inline-block;">Live Trade</span>

                <div class="iq-modal-meta">
                    Published at: ${pubDate}<br>
                    Expires at: ${expDate}
                </div>

                <div class="iq-modal-description">${esc(edu.description)}</div>
            </div>

            <!-- Footer -->
            <div class="iq-modal-footer">
                <button class="iq-modal-btn iq-modal-btn-primary" onclick="window.EnhancedSignalsPage.copyToMT5(${signal.id})">
                    Copy to MT5
                </button>
                <button class="iq-modal-btn iq-modal-btn-secondary" onclick="window.EnhancedSignalsPage.closeModal()">
                    Close
                </button>
            </div>
        `;

        iqModal.classList.add('open');
    }

    function closeModal() {
        iqModal?.classList.remove('open');
    }

    function copyToMT5(signalId) {
        if (window.MT5Copier?.execute) return window.MT5Copier.execute(signalId);
        if (window.SignalCopier?.copy) return window.SignalCopier.copy(signalId);
        alert('Signal copied! Open MT5 to execute.');
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // UTILS
    // ═══════════════════════════════════════════════════════════════════════════

    function startCountdowns() {
        const tick = () => {
            document.querySelectorAll('.iq-countdown[data-expiry]').forEach(el => {
                const exp = el.dataset.expiry;
                if (!exp) return;
                el.textContent = formatCountdown(exp);
                const ms = new Date(exp) - Date.now();
                el.classList.toggle('urgent', ms > 0 && ms < 3600000);
            });
        };
        tick();
        countdownTimers.push(setInterval(tick, 1000));
    }

    function formatCountdown(iso) {
        if (!iso) return '—';
        const ms = new Date(iso) - Date.now();
        if (ms <= 0) return 'EXPIRED';
        const h = Math.floor(ms / 3600000);
        const m = Math.floor((ms % 3600000) / 60000);
        if (h >= 24) return `${Math.floor(h/24)}d ${h%24}h`;
        return `${h}h ${m}m`;
    }

    function esc(str) {
        if (str == null) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API
    // ═══════════════════════════════════════════════════════════════════════════

    window.EnhancedSignalsPage = {
        init,
        loadSignals,
        openDeepInsight,
        closeModal,
        copyToMT5,
        switchTab,
        openSignalModal: openDeepInsight,
        closeIQModal: closeModal,
    };

})();
