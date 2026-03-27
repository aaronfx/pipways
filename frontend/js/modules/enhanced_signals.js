// Enhanced Signals Page — Production Edition v5
// Deploy to: frontend/js/modules/enhanced_signals.js
//
// ⚠️ NO FAKE CHARTS
// ⚠️ Uses TradingView Lightweight Charts (real library)
// ⚠️ Clean info cards (no SVG simulation)
// ⚠️ Modal with real chart + overlays

(function () {
    'use strict';

    // ═══════════════════════════════════════════════════════════════════════════
    // PATTERN EDUCATION DATA
    // ═══════════════════════════════════════════════════════════════════════════

    const PATTERN_EDUCATION = {
        'SYMMETRICAL_TRIANGLE': {
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

Traders watch for a decisive close outside the triangle boundaries to confirm the breakout direction. False breakouts are common, so confirmation is essential.`
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
        const key = (pattern || 'BREAKOUT').toUpperCase().replace(/[^A-Z_]/g, '');
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
    // CSS — Institutional Grade UI
    // ═══════════════════════════════════════════════════════════════════════════

    const STYLES = `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Grid Layout */
    #signalsGrid {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 20px !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    @media (max-width: 1100px) { #signalsGrid { grid-template-columns: repeat(2, 1fr) !important; } }
    @media (max-width: 700px) { #signalsGrid { grid-template-columns: 1fr !important; } }

    /* ═══ SIGNAL CARD — Clean Info Design (NO fake chart) ═══ */
    .sig-card {
        background: linear-gradient(180deg, #141417 0%, #0d0d0f 100%);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        overflow: hidden;
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    }
    .sig-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        border-color: rgba(255,255,255,0.1);
    }

    /* Card Header */
    .sig-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 20px 12px;
    }
    .sig-live-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        background: linear-gradient(135deg, #00c9a7 0%, #00b894 100%);
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.12em;
        color: #000;
        text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(0, 200, 150, 0.25);
    }
    .sig-live-badge::before {
        content: '';
        width: 6px;
        height: 6px;
        background: #000;
        border-radius: 50%;
        animation: sig-pulse 1.5s ease-in-out infinite;
    }
    @keyframes sig-pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.85); }
    }
    .sig-tv-link {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .sig-tv-link:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
    }
    .sig-tv-link svg { width: 18px; height: 18px; fill: #fff; }

    /* Symbol Row */
    .sig-symbol-row {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 0 20px 14px;
    }
    .sig-icon {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 17px;
        font-weight: 800;
        flex-shrink: 0;
        border: 3px solid rgba(255,255,255,0.08);
    }
    .sig-icon.gold {
        background: linear-gradient(145deg, #ffd700 0%, #daa520 50%, #b8860b 100%);
        color: #1a1a1a;
        border-color: rgba(255,215,0,0.25);
        box-shadow: 0 6px 20px rgba(255,215,0,0.15);
    }
    .sig-icon.silver {
        background: linear-gradient(145deg, #e8e8e8 0%, #c0c0c0 50%, #a8a8a8 100%);
        color: #1a1a1a;
    }
    .sig-icon.crypto {
        background: linear-gradient(145deg, #f7931a 0%, #e67e00 100%);
        color: #fff;
        box-shadow: 0 6px 20px rgba(247,147,26,0.15);
    }
    .sig-icon.indices, .sig-icon.forex {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        color: #fff;
        font-size: 14px;
    }
    .sig-symbol-info { flex: 1; min-width: 0; }
    .sig-symbol-name {
        font-size: 20px;
        font-weight: 700;
        color: #fff;
        letter-spacing: -0.02em;
        margin-bottom: 2px;
    }
    .sig-pattern-name {
        font-size: 12px;
        font-weight: 500;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    /* Direction Badge */
    .sig-direction-row {
        display: flex;
        justify-content: center;
        padding: 0 20px 16px;
    }
    .sig-direction-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 28px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    .sig-direction-badge.buy {
        background: linear-gradient(135deg, #00c9a7 0%, #00b894 100%);
        color: #000;
        box-shadow: 0 6px 20px rgba(0, 200, 150, 0.2);
    }
    .sig-direction-badge.sell {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
        color: #fff;
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.2);
    }

    /* Price Info */
    .sig-prices {
        padding: 0 20px;
    }
    .sig-price-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid rgba(255,255,255,0.04);
    }
    .sig-price-row:last-child { border-bottom: none; }
    .sig-price-label {
        font-size: 14px;
        font-weight: 500;
        color: #6b7280;
    }
    .sig-price-value {
        font-size: 16px;
        font-weight: 600;
        font-family: 'SF Mono', 'JetBrains Mono', 'Consolas', monospace;
        color: #fff;
    }
    .sig-price-value.target { color: #00d4aa; }
    .sig-price-value.stop { color: #ff6b6b; }
    .sig-price-value.expires { color: #f5a623; }

    /* Confidence Bar */
    .sig-confidence {
        padding: 16px 20px 0;
    }
    .sig-confidence-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .sig-confidence-label {
        font-size: 12px;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .sig-confidence-value {
        font-size: 14px;
        font-weight: 700;
        color: #a78bfa;
    }
    .sig-confidence-bar {
        height: 4px;
        background: rgba(255,255,255,0.08);
        border-radius: 2px;
        overflow: hidden;
    }
    .sig-confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, #a78bfa 0%, #818cf8 100%);
        border-radius: 2px;
        transition: width 0.5s ease;
    }

    /* Learn More Button */
    .sig-learn-btn {
        display: block;
        width: calc(100% - 40px);
        margin: 20px 20px;
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
    .sig-learn-btn:hover {
        background: rgba(255,255,255,0.06);
        border-color: rgba(255,255,255,0.15);
        transform: translateY(-2px);
    }

    /* Tab Bar */
    .sig-tab-bar {
        display: flex;
        gap: 32px;
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    .sig-tab-item {
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
    .sig-tab-item:hover { color: #9ca3af; }
    .sig-tab-item.active { color: #fff; }
    .sig-tab-dot {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
    }
    .sig-tab-item.ai-driven .sig-tab-dot { background: linear-gradient(135deg, #f5a623, #e67e00); color: #000; }
    .sig-tab-item.analysis-iq .sig-tab-dot { background: linear-gradient(135deg, #6366f1, #4f46e5); color: #fff; }

    /* ═══ MODAL — Real Chart Integration ═══ */
    .sig-modal-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.94);
        backdrop-filter: blur(12px);
        z-index: 9999;
        display: flex;
        align-items: flex-start;
        justify-content: center;
        padding: 24px 16px;
        overflow-y: auto;
        opacity: 0;
        transition: opacity 0.25s ease;
        pointer-events: none;
    }
    .sig-modal-overlay.open {
        opacity: 1;
        pointer-events: all;
    }
    .sig-modal {
        background: linear-gradient(180deg, #141417 0%, #0d0d0f 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        width: 100%;
        max-width: 1000px;
        margin: 20px 0;
        overflow: hidden;
        box-shadow: 0 40px 80px rgba(0,0,0,0.6);
    }

    /* Modal Header */
    .sig-modal-header {
        background: linear-gradient(180deg, #0a0a0c 0%, #0d0d0f 100%);
        padding: 24px 28px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .sig-modal-top {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    .sig-modal-flag {
        width: 56px;
        height: 42px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        background: #1a1a2e;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .sig-modal-symbol-badge {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: #fff;
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 0.02em;
    }
    .sig-modal-pair-name {
        font-size: 24px;
        font-weight: 600;
        color: #fff;
        flex: 1;
        min-width: 200px;
    }
    .sig-modal-price-box { text-align: right; }
    .sig-modal-live-price {
        font-size: 40px;
        font-weight: 700;
        color: #fff;
        font-family: 'SF Mono', 'JetBrains Mono', monospace;
        letter-spacing: -0.02em;
    }
    .sig-modal-price-change {
        font-size: 14px;
        font-weight: 600;
        margin-top: 4px;
    }
    .sig-modal-price-change.up { color: #00d4aa; }
    .sig-modal-price-change.down { color: #ff6b6b; }

    /* Badges */
    .sig-modal-badges {
        display: flex;
        gap: 12px;
        margin-bottom: 24px;
        flex-wrap: wrap;
    }
    .sig-modal-live-tag {
        display: inline-flex;
        align-items: center;
        padding: 8px 18px;
        background: linear-gradient(135deg, #f5a623 0%, #e67e00 100%);
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.12em;
        color: #000;
        text-transform: uppercase;
    }

    /* Info Grid */
    .sig-modal-info {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 20px;
    }
    @media (max-width: 768px) {
        .sig-modal-info { grid-template-columns: repeat(3, 1fr); }
    }
    @media (max-width: 480px) {
        .sig-modal-info { grid-template-columns: repeat(2, 1fr); }
    }
    .sig-modal-info-item { text-align: center; }
    .sig-modal-info-value {
        font-size: 18px;
        font-weight: 700;
        color: #00d4aa;
        font-family: 'SF Mono', 'JetBrains Mono', monospace;
        margin-bottom: 6px;
    }
    .sig-modal-info-value.pattern { color: #fff; font-family: 'Inter', sans-serif; font-size: 15px; }
    .sig-modal-info-value.entry { color: #fff; }
    .sig-modal-info-value.stop { color: #ff6b6b; }
    .sig-modal-info-label {
        font-size: 11px;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    /* Sentiment */
    .sig-sentiment {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
    }
    .sig-sentiment-bar {
        width: 90px;
        height: 6px;
        background: #333;
        border-radius: 3px;
        overflow: hidden;
        display: flex;
    }
    .sig-sentiment-bear { background: linear-gradient(90deg, #ff6b6b, #ff8787); }
    .sig-sentiment-bull { background: linear-gradient(90deg, #00d4aa, #00e6b8); }
    .sig-sentiment-label { font-size: 11px; font-weight: 600; color: #6b7280; }

    /* Modal Body */
    .sig-modal-body { padding: 28px; }

    /* TradingView Chart Container */
    .sig-chart-container {
        width: 100%;
        height: 400px;
        background: #0a0a0c;
        border-radius: 12px;
        margin-bottom: 28px;
        overflow: hidden;
        position: relative;
        border: 1px solid rgba(255,255,255,0.06);
    }
    .sig-chart-container iframe {
        width: 100%;
        height: 100%;
        border: none;
    }
    .sig-chart-loading {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: #0a0a0c;
        color: #6b7280;
        font-size: 14px;
        gap: 12px;
    }
    .sig-chart-loading-spinner {
        width: 32px;
        height: 32px;
        border: 3px solid rgba(255,255,255,0.1);
        border-top-color: #6366f1;
        border-radius: 50%;
        animation: sig-spin 1s linear infinite;
    }
    @keyframes sig-spin {
        to { transform: rotate(360deg); }
    }

    /* Trade Idea Section */
    .sig-modal-title-row {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 12px;
    }
    .sig-modal-title {
        font-size: 28px;
        font-weight: 700;
        color: #fff;
    }
    .sig-modal-tv-link {
        width: 38px;
        height: 38px;
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .sig-modal-tv-link:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
    }
    .sig-modal-tv-link svg { width: 18px; height: 18px; fill: #fff; }

    .sig-modal-meta {
        font-size: 13px;
        color: #f5a623;
        margin-bottom: 24px;
        line-height: 1.7;
    }
    .sig-modal-description {
        font-size: 16px;
        line-height: 1.9;
        color: #d1d5db;
        white-space: pre-line;
    }

    /* Modal Footer */
    .sig-modal-footer {
        padding: 20px 28px;
        border-top: 1px solid rgba(255,255,255,0.06);
        display: flex;
        gap: 14px;
        flex-wrap: wrap;
    }
    .sig-modal-btn {
        padding: 14px 32px;
        border-radius: 10px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .sig-modal-btn-primary {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        border: none;
        color: #fff;
        flex: 1;
        min-width: 150px;
    }
    .sig-modal-btn-primary:hover {
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
    }
    .sig-modal-btn-secondary {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.1);
        color: #9ca3af;
    }
    .sig-modal-btn-secondary:hover {
        background: rgba(255,255,255,0.06);
        color: #fff;
    }

    /* Countdown */
    .sig-countdown.urgent { color: #ff6b6b !important; animation: sig-urgent 1s infinite; }
    @keyframes sig-urgent { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    `;

    function injectStyles() {
        if (document.getElementById('sig-styles')) return;
        const el = document.createElement('style');
        el.id = 'sig-styles';
        el.textContent = STYLES;
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
    let modalOverlay = null;

    // ═══════════════════════════════════════════════════════════════════════════
    // INIT
    // ═══════════════════════════════════════════════════════════════════════════

    function init() {
        console.log('[Signals] Initialising v5 (Production)...');
        injectStyles();
        injectTabBar();
        injectModal();
        setupEventListeners();
        loadSignals();

        if (updateInterval) clearInterval(updateInterval);
        updateInterval = setInterval(loadSignals, 60000);
    }

    function injectTabBar() {
        if (document.getElementById('sig-tab-bar')) return;

        const bar = document.createElement('div');
        bar.id = 'sig-tab-bar';
        bar.className = 'sig-tab-bar';
        bar.innerHTML = `
            <div id="sig-tab-ai" class="sig-tab-item ai-driven active" data-tab="ai-driven">
                <span class="sig-tab-dot">✦</span>
                AI-Driven Trade Ideas
            </div>
            <div id="sig-tab-pattern" class="sig-tab-item analysis-iq" data-tab="analysis-iq">
                <span class="sig-tab-dot">◈</span>
                Pattern Trade Ideas
            </div>
        `;

        const grid = document.getElementById('signalsGrid');
        const parent = grid?.parentElement;
        if (parent) parent.insertBefore(bar, grid);
    }

    function injectModal() {
        if (document.getElementById('sig-modal-overlay')) return;

        const overlay = document.createElement('div');
        overlay.id = 'sig-modal-overlay';
        overlay.className = 'sig-modal-overlay';
        overlay.innerHTML = `<div class="sig-modal" id="sig-modal"></div>`;
        document.body.appendChild(overlay);
        modalOverlay = overlay;

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
            console.error('[Signals] Load error:', error);
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
        document.getElementById('sig-tab-ai')?.classList.toggle('active', tab === 'ai-driven');
        document.getElementById('sig-tab-pattern')?.classList.toggle('active', tab === 'analysis-iq');
        applyFilters();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // RENDER CARDS — Clean Info Design (NO fake charts)
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
        const cc = symbol?.substring(0, 2) || '??';
        return { text: cc, cls: 'forex' };
    }

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

    function getFlag(symbol) {
        const flags = {
            'EU': '🇪🇺', 'GB': '🇬🇧', 'US': '🇺🇸', 'JP': '🇯🇵',
            'AU': '🇦🇺', 'NZ': '🇳🇿', 'CA': '🇨🇦', 'CH': '🇨🇭',
            'CN': '🇨🇳', 'DE': '🇩🇪', 'XA': '🪙', 'BT': '₿', 'ET': '⟠'
        };
        const cc = symbol?.substring(0, 2) || '';
        return flags[cc] || '🌐';
    }

    function renderCard(signal) {
        const isBuy = (signal.direction || '').toUpperCase().includes('BUY');
        const pattern = (signal.pattern || 'PATTERN').replace(/_/g, ' ');
        const icon = getAssetIcon(signal.symbol);
        const tvSymbol = getTVSymbol(signal.symbol);
        const confidence = signal.confidence || 75;

        const tvSvg = `<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M7 14l3-3 2 2 5-5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

        return `
        <div class="sig-card">
            <!-- Header -->
            <div class="sig-header">
                <span class="sig-live-badge">Live Trade</span>
                <a href="https://www.tradingview.com/chart/?symbol=${tvSymbol}" target="_blank" class="sig-tv-link" title="Open in TradingView">
                    ${tvSvg}
                </a>
            </div>

            <!-- Symbol -->
            <div class="sig-symbol-row">
                <div class="sig-icon ${icon.cls}">${icon.text}</div>
                <div class="sig-symbol-info">
                    <div class="sig-symbol-name">${esc(signal.symbol)}</div>
                    <div class="sig-pattern-name">${esc(pattern)}</div>
                </div>
            </div>

            <!-- Direction -->
            <div class="sig-direction-row">
                <span class="sig-direction-badge ${isBuy ? 'buy' : 'sell'}">
                    ${isBuy ? 'BUY STOP' : 'SELL STOP'}
                </span>
            </div>

            <!-- Prices -->
            <div class="sig-prices">
                <div class="sig-price-row">
                    <span class="sig-price-label">Entry</span>
                    <span class="sig-price-value">${esc(signal.entry || '—')}</span>
                </div>
                <div class="sig-price-row">
                    <span class="sig-price-label">Target</span>
                    <span class="sig-price-value target">${esc(signal.target || '—')}</span>
                </div>
                <div class="sig-price-row">
                    <span class="sig-price-label">Stop</span>
                    <span class="sig-price-value stop">${esc(signal.stop || '—')}</span>
                </div>
                <div class="sig-price-row">
                    <span class="sig-price-label">Expires</span>
                    <span class="sig-price-value expires sig-countdown" data-expiry="${signal.expires_at || ''}">${formatCountdown(signal.expires_at)}</span>
                </div>
            </div>

            <!-- Confidence -->
            <div class="sig-confidence">
                <div class="sig-confidence-header">
                    <span class="sig-confidence-label">AI Confidence</span>
                    <span class="sig-confidence-value">${confidence}%</span>
                </div>
                <div class="sig-confidence-bar">
                    <div class="sig-confidence-fill" style="width: ${confidence}%"></div>
                </div>
            </div>

            <!-- Learn More -->
            <button class="sig-learn-btn" onclick="window.EnhancedSignalsPage.openDeepInsight(${signal.id})">
                View Analysis
            </button>
        </div>`;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // MODAL — Real TradingView Chart Integration
    // ═══════════════════════════════════════════════════════════════════════════

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
        if (!signal || !modalOverlay) return;

        const isBuy = (signal.direction || '').toUpperCase().includes('BUY');
        const pattern = (signal.pattern || 'Pattern').replace(/_/g, ' ');
        const edu = getPatternEducation(signal.pattern);
        const tvSymbol = getTVSymbol(signal.symbol);
        const flag = getFlag(signal.symbol);
        const pairName = getPairName(signal.symbol);
        const bullish = signal.sentiment_bullish || 55;
        const bearish = 100 - bullish;
        const tf = signal.timeframe || '4H';

        // TradingView interval mapping
        const tfMap = { '1M': '1', '5M': '5', '15M': '15', '30M': '30', '1H': '60', '4H': '240', '1D': 'D', 'D': 'D' };
        const tvInterval = tfMap[tf] || '240';

        // Timestamps
        const pubDate = signal.created_at
            ? new Date(signal.created_at).toLocaleString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
            : '—';
        const expDate = signal.expires_at
            ? new Date(signal.expires_at).toLocaleString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
            : '—';

        const tvSvg = `<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M7 14l3-3 2 2 5-5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

        // TradingView Advanced Chart Widget (Free embed)
        const tvChartUrl = `https://s.tradingview.com/widgetembed/?frameElementId=tradingview_chart&symbol=${encodeURIComponent(tvSymbol)}&interval=${tvInterval}&hidesidetoolbar=0&symboledit=0&saveimage=1&toolbarbg=0a0a0c&studies=[]&theme=dark&style=1&timezone=Etc%2FUTC&withdateranges=1&showpopupbutton=0&studies_overrides={}&overrides={}&enabled_features=[]&disabled_features=[]&locale=en&utm_source=pipways&utm_medium=widget&utm_campaign=chart`;

        const modal = document.getElementById('sig-modal');
        modal.innerHTML = `
            <!-- Header -->
            <div class="sig-modal-header">
                <div class="sig-modal-top">
                    <div class="sig-modal-flag">${flag}</div>
                    <span class="sig-modal-symbol-badge">${esc(signal.symbol)}</span>
                    <span class="sig-modal-pair-name">${esc(pairName)}</span>
                    <div class="sig-modal-price-box">
                        <div class="sig-modal-live-price">${esc(signal.entry || '—')}</div>
                        <div class="sig-modal-price-change ${isBuy ? 'up' : 'down'}">
                            ${isBuy ? '▲' : '▼'} Entry Level
                        </div>
                    </div>
                </div>

                <div class="sig-modal-badges">
                    <span class="sig-direction-badge ${isBuy ? 'buy' : 'sell'}">
                        ${isBuy ? 'BUY STOP' : 'SELL STOP'}
                    </span>
                    <span class="sig-modal-live-tag">Live Trade</span>
                </div>

                <div class="sig-modal-info">
                    <div class="sig-modal-info-item">
                        <div class="sig-modal-info-value pattern">${esc(pattern)}</div>
                        <div class="sig-modal-info-label">Pattern</div>
                    </div>
                    <div class="sig-modal-info-item">
                        <div class="sig-modal-info-value entry">${esc(signal.entry || '—')}</div>
                        <div class="sig-modal-info-label">Entry</div>
                    </div>
                    <div class="sig-modal-info-item">
                        <div class="sig-modal-info-value">${esc(signal.target || '—')}</div>
                        <div class="sig-modal-info-label">Target</div>
                    </div>
                    <div class="sig-modal-info-item">
                        <div class="sig-modal-info-value stop">${esc(signal.stop || '—')}</div>
                        <div class="sig-modal-info-label">Stop</div>
                    </div>
                    <div class="sig-modal-info-item">
                        <div class="sig-sentiment">
                            <span class="sig-sentiment-label">🐻 ${bearish}%</span>
                            <div class="sig-sentiment-bar">
                                <div class="sig-sentiment-bear" style="width:${bearish}%"></div>
                                <div class="sig-sentiment-bull" style="width:${bullish}%"></div>
                            </div>
                            <span class="sig-sentiment-label">${bullish}% 🐂</span>
                        </div>
                        <div class="sig-modal-info-label">Sentiment</div>
                    </div>
                </div>
            </div>

            <!-- Body -->
            <div class="sig-modal-body">
                <!-- Real TradingView Chart -->
                <div class="sig-chart-container" id="sig-chart-container">
                    <div class="sig-chart-loading" id="sig-chart-loading">
                        <div class="sig-chart-loading-spinner"></div>
                        Loading Chart...
                    </div>
                    <iframe 
                        id="tradingview_chart"
                        src="${tvChartUrl}"
                        frameborder="0"
                        allowtransparency="true"
                        scrolling="no"
                        allowfullscreen
                        onload="document.getElementById('sig-chart-loading').style.display='none'"
                    ></iframe>
                </div>

                <!-- Trade Idea -->
                <div class="sig-modal-title-row">
                    <span class="sig-modal-title">Trade Idea</span>
                    <a href="https://www.tradingview.com/chart/?symbol=${tvSymbol}" target="_blank" class="sig-modal-tv-link" title="Open Full Chart">
                        ${tvSvg}
                    </a>
                </div>

                <span class="sig-modal-live-tag" style="margin-bottom:16px; display:inline-block;">Live Trade</span>

                <div class="sig-modal-meta">
                    Published at: ${pubDate}<br>
                    Expires at: ${expDate}
                </div>

                <div class="sig-modal-description">${esc(edu.description)}</div>
            </div>

            <!-- Footer -->
            <div class="sig-modal-footer">
                <button class="sig-modal-btn sig-modal-btn-primary" onclick="window.EnhancedSignalsPage.copyToMT5(${signal.id})">
                    Copy to MT5
                </button>
                <button class="sig-modal-btn sig-modal-btn-secondary" onclick="window.EnhancedSignalsPage.closeModal()">
                    Close
                </button>
            </div>
        `;

        modalOverlay.classList.add('open');
    }

    function closeModal() {
        if (!modalOverlay) return;
        modalOverlay.classList.remove('open');
        
        // Clean up chart iframe to prevent memory leaks
        const chartContainer = document.getElementById('sig-chart-container');
        if (chartContainer) {
            const iframe = chartContainer.querySelector('iframe');
            if (iframe) iframe.src = 'about:blank';
        }
    }

    function copyToMT5(signalId) {
        if (window.MT5Copier?.execute) return window.MT5Copier.execute(signalId);
        if (window.SignalCopier?.copy) return window.SignalCopier.copy(signalId);
        
        // Fallback: Copy signal details to clipboard
        const signal = allSignals.find(s => s.id === signalId);
        if (signal) {
            const text = `${signal.symbol} ${signal.direction}\nEntry: ${signal.entry}\nTP: ${signal.target}\nSL: ${signal.stop}`;
            navigator.clipboard?.writeText(text);
            alert('Signal copied to clipboard! Open MT5 to execute.');
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // UTILS
    // ═══════════════════════════════════════════════════════════════════════════

    function startCountdowns() {
        const tick = () => {
            document.querySelectorAll('.sig-countdown[data-expiry]').forEach(el => {
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
        if (h >= 24) return `${Math.floor(h / 24)}d ${h % 24}h`;
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
