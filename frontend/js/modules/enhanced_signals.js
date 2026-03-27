// Enhanced Signals Page Module — AnalysisIQ Edition v3
// Deploy to: frontend/js/modules/enhanced_signals.js
//
// Features:
//   • Card with static pattern chart (candlesticks + pattern lines)
//   • Learn More modal with pattern education/explanation
//   • TradingView link opens in new tab
//   • Pattern-based technical analysis content

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
        
        // Try exact match first
        if (PATTERN_EDUCATION[key]) return PATTERN_EDUCATION[key];
        
        // Try partial matches
        for (const [k, v] of Object.entries(PATTERN_EDUCATION)) {
            if (key.includes(k) || k.includes(key)) return v;
        }
        
        // Default
        return {
            title: pattern || 'Pattern Analysis',
            description: `This trading pattern has been identified by our AI analysis system based on technical chart formations and price action.

The pattern suggests a potential trading opportunity with defined entry, target, and stop loss levels.

Always conduct your own analysis and use proper risk management when trading. Past pattern performance does not guarantee future results.`
        };
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // CSS INJECTION
    // ═══════════════════════════════════════════════════════════════════════════

    const IQ_STYLES = `
    /* ══════════════════════════════════════════════════════════════════════════
       AnalysisIQ v3 — Professional Signal Cards
       ══════════════════════════════════════════════════════════════════════════ */

    /* 3-column grid */
    #signalsGrid {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 16px !important;
    }
    @media (max-width: 1100px) {
        #signalsGrid { grid-template-columns: repeat(2, 1fr) !important; }
    }
    @media (max-width: 700px) {
        #signalsGrid { grid-template-columns: 1fr !important; }
    }

    /* ── Card ─────────────────────────────────────────────────────────────────── */
    .aiq-card {
        background: #111;
        border: 1px solid #222;
        border-radius: 16px;
        overflow: hidden;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .aiq-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.5);
    }

    /* Live Trade Badge - centered */
    .aiq-live-badge-wrapper {
        display: flex;
        justify-content: center;
        padding: 12px 16px 8px;
        position: relative;
    }
    .aiq-live-badge {
        display: inline-block;
        padding: 6px 16px;
        background: linear-gradient(135deg, #00b894, #00a885);
        border-radius: 4px;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.12em;
        color: #fff;
        text-transform: uppercase;
    }
    .aiq-tv-icon {
        position: absolute;
        right: 16px;
        top: 50%;
        transform: translateY(-50%);
        width: 28px;
        height: 28px;
        background: linear-gradient(135deg, #5b6eef, #4a5bc7);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: transform 0.2s ease;
    }
    .aiq-tv-icon:hover { transform: translateY(-50%) scale(1.1); }
    .aiq-tv-icon svg { width: 14px; height: 14px; fill: #fff; }

    /* Symbol Row */
    .aiq-symbol-row {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 16px 8px;
    }
    .aiq-asset-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 15px;
        font-weight: 700;
        background: linear-gradient(135deg, #d4a017, #b8860b);
        color: #000;
        border: 2px solid rgba(212, 160, 23, 0.4);
        flex-shrink: 0;
    }
    .aiq-asset-icon.crypto { background: linear-gradient(135deg, #f7931a, #e67e00); }
    .aiq-asset-icon.indices { background: linear-gradient(135deg, #4caf50, #388e3c); color: #fff; }
    .aiq-asset-icon.forex { background: linear-gradient(135deg, #2196f3, #1976d2); color: #fff; }
    .aiq-asset-icon.flag { font-size: 22px; background: #1a1a1a; border-color: #333; }

    .aiq-symbol-info { flex: 1; min-width: 0; }
    .aiq-symbol-name {
        font-size: 16px;
        font-weight: 700;
        color: #fff;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .aiq-pattern-tag {
        font-size: 11px;
        font-weight: 400;
        color: #666;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .aiq-confidence {
        font-size: 11px;
        color: #a78bfa;
        font-weight: 600;
    }

    /* Order Badge */
    .aiq-order-badge-wrapper {
        display: flex;
        justify-content: center;
        padding: 0 16px 10px;
    }
    .aiq-order-badge {
        display: inline-block;
        padding: 6px 20px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.05em;
    }
    .aiq-order-buy { background: #00c896; color: #000; }
    .aiq-order-sell { background: #ff4757; color: #fff; }

    /* Price List */
    .aiq-price-list {
        padding: 0 16px 8px;
    }
    .aiq-price-row {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        font-size: 13px;
    }
    .aiq-price-label { color: #888; }
    .aiq-price-value {
        font-weight: 600;
        font-family: 'SF Mono', 'Consolas', monospace;
    }
    .aiq-price-value.target { color: #00d4aa; }
    .aiq-price-value.stop { color: #ff4757; }
    .aiq-price-value.expires { color: #f5a623; }

    /* Chart Container */
    .aiq-chart {
        width: 100%;
        height: 120px;
        background: #0a0a0a;
        position: relative;
        overflow: hidden;
    }
    .aiq-chart svg {
        width: 100%;
        height: 100%;
    }
    .aiq-tf-badge {
        position: absolute;
        bottom: 8px;
        right: 10px;
        background: rgba(0,0,0,0.8);
        border: 1px solid #333;
        border-radius: 50%;
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        font-weight: 700;
        color: #fff;
    }

    /* Learn More Button */
    .aiq-learn-btn {
        display: block;
        width: calc(100% - 32px);
        margin: 8px 16px 16px;
        padding: 12px;
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
        color: #fff;
        font-size: 12px;
        font-weight: 600;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .aiq-learn-btn:hover {
        background: #222;
        border-color: #444;
    }

    /* Tab Bar */
    .aiq-tab-bar {
        display: flex;
        gap: 24px;
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid #222;
    }
    .aiq-tab-item {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 13px;
        color: #555;
        cursor: pointer;
        transition: color 0.2s ease;
        padding: 4px 0;
    }
    .aiq-tab-item:hover { color: #888; }
    .aiq-tab-item.active { color: #fff; }
    .aiq-tab-dot {
        width: 22px;
        height: 22px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
    }
    .aiq-tab-item.ai-driven .aiq-tab-dot { background: linear-gradient(135deg, #f5a623, #e67e00); color: #000; }
    .aiq-tab-item.analysis-iq .aiq-tab-dot { background: linear-gradient(135deg, #5b6eef, #4a5bc7); color: #fff; }

    /* ══════════════════════════════════════════════════════════════════════════
       Modal — Pattern Education
       ══════════════════════════════════════════════════════════════════════════ */
    .aiq-modal-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.95);
        z-index: 9999;
        display: flex;
        align-items: flex-start;
        justify-content: center;
        padding: 24px;
        overflow-y: auto;
        opacity: 0;
        transition: opacity 0.2s ease;
        pointer-events: none;
    }
    .aiq-modal-overlay.open {
        opacity: 1;
        pointer-events: all;
    }
    .aiq-modal {
        background: #111;
        border: 1px solid #222;
        border-radius: 16px;
        width: 100%;
        max-width: 800px;
        margin: 40px 0;
        overflow: hidden;
    }

    /* Modal Header Bar */
    .aiq-modal-header-bar {
        background: #0a0a0a;
        padding: 16px 20px;
        border-bottom: 1px solid #222;
    }
    .aiq-modal-header-top {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
    }
    .aiq-modal-flag {
        width: 48px;
        height: 36px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        background: #1a1a1a;
        border: 1px solid #333;
    }
    .aiq-modal-symbol-badge {
        background: #2196f3;
        color: #fff;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 700;
    }
    .aiq-modal-full-name {
        font-size: 20px;
        font-weight: 600;
        color: #fff;
        flex: 1;
    }
    .aiq-modal-price {
        text-align: right;
    }
    .aiq-modal-price-value {
        font-size: 28px;
        font-weight: 700;
        color: #fff;
        font-family: 'SF Mono', monospace;
    }
    .aiq-modal-price-change {
        font-size: 13px;
        margin-top: 2px;
    }
    .aiq-modal-price-change.up { color: #00d4aa; }
    .aiq-modal-price-change.down { color: #ff4757; }

    /* Badges Row */
    .aiq-modal-badges {
        display: flex;
        gap: 8px;
        margin-bottom: 16px;
    }

    /* Info Grid */
    .aiq-modal-info-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 16px;
    }
    @media (max-width: 600px) {
        .aiq-modal-info-grid { grid-template-columns: repeat(3, 1fr); }
    }
    .aiq-modal-info-item {
        text-align: center;
    }
    .aiq-modal-info-value {
        font-size: 16px;
        font-weight: 700;
        color: #00d4aa;
        font-family: 'SF Mono', monospace;
        margin-bottom: 2px;
    }
    .aiq-modal-info-value.entry { color: #fff; }
    .aiq-modal-info-value.stop { color: #ff4757; }
    .aiq-modal-info-label {
        font-size: 11px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Sentiment Bar */
    .aiq-sentiment {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .aiq-sentiment-bar {
        flex: 1;
        height: 6px;
        background: #333;
        border-radius: 3px;
        overflow: hidden;
        display: flex;
    }
    .aiq-sentiment-bear {
        background: linear-gradient(90deg, #ff4757, #ff6b7a);
        height: 100%;
    }
    .aiq-sentiment-bull {
        background: linear-gradient(90deg, #00d4aa, #00e6b8);
        height: 100%;
    }
    .aiq-sentiment-label {
        font-size: 11px;
        color: #888;
        white-space: nowrap;
    }

    /* Modal Body */
    .aiq-modal-body {
        padding: 24px;
    }
    .aiq-modal-chart {
        width: 100%;
        height: 200px;
        background: #0a0a0a;
        border-radius: 12px;
        margin-bottom: 24px;
        overflow: hidden;
        position: relative;
    }
    .aiq-modal-chart svg {
        width: 100%;
        height: 100%;
    }
    .aiq-modal-chart .aiq-tf-badge {
        position: absolute;
        bottom: 12px;
        right: 12px;
    }
    .aiq-modal-title-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
    }
    .aiq-modal-title {
        font-size: 24px;
        font-weight: 700;
        color: #fff;
    }
    .aiq-modal-tv-icon {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #5b6eef, #4a5bc7);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
    }
    .aiq-modal-tv-icon svg { width: 16px; height: 16px; fill: #fff; }

    .aiq-modal-meta {
        color: #f5a623;
        font-size: 12px;
        margin-bottom: 20px;
    }

    .aiq-modal-description {
        color: #ccc;
        font-size: 15px;
        line-height: 1.8;
        white-space: pre-line;
    }

    /* Modal Footer */
    .aiq-modal-footer {
        padding: 16px 24px;
        border-top: 1px solid #222;
        display: flex;
        gap: 12px;
    }
    .aiq-modal-btn {
        padding: 14px 28px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .aiq-modal-btn-primary {
        background: linear-gradient(135deg, #5b6eef, #4a5bc7);
        border: none;
        color: #fff;
        flex: 1;
    }
    .aiq-modal-btn-primary:hover {
        box-shadow: 0 4px 20px rgba(91, 110, 239, 0.4);
    }
    .aiq-modal-btn-secondary {
        background: #1a1a1a;
        border: 1px solid #333;
        color: #888;
    }
    .aiq-modal-btn-secondary:hover {
        background: #222;
        color: #fff;
    }

    /* Countdown urgent */
    .aiq-countdown.urgent { color: #ff6b6b !important; animation: aiq-pulse 1s infinite; }
    @keyframes aiq-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    `;

    function injectStyles() {
        if (document.getElementById('aiq-styles')) return;
        const el = document.createElement('style');
        el.id = 'aiq-styles';
        el.textContent = IQ_STYLES;
        document.head.appendChild(el);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // API HELPER
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
        console.log('[AnalysisIQ] Initialising v3...');
        injectStyles();
        injectTabBar();
        injectIQModal();
        setupEventListeners();
        loadSignals();

        if (updateInterval) clearInterval(updateInterval);
        updateInterval = setInterval(loadSignals, 60000);
    }

    function injectTabBar() {
        if (document.getElementById('aiq-tab-bar')) return;

        const bar = document.createElement('div');
        bar.id = 'aiq-tab-bar';
        bar.className = 'aiq-tab-bar';
        bar.innerHTML = `
            <div id="aiq-tab-standard" class="aiq-tab-item ai-driven active" data-tab="ai-driven">
                <span class="aiq-tab-dot">✦</span>
                AI-Driven Trade Ideas
            </div>
            <div id="aiq-tab-iq" class="aiq-tab-item analysis-iq" data-tab="analysis-iq">
                <span class="aiq-tab-dot">◈</span>
                Pattern Trade Ideas
            </div>
        `;

        const grid = document.getElementById('signalsGrid');
        const parent = grid?.parentElement;
        if (parent) parent.insertBefore(bar, grid);
    }

    function injectIQModal() {
        if (document.getElementById('aiq-modal-overlay')) return;

        const overlay = document.createElement('div');
        overlay.id = 'aiq-modal-overlay';
        overlay.className = 'aiq-modal-overlay';
        overlay.innerHTML = `<div class="aiq-modal" id="aiq-modal"></div>`;
        document.body.appendChild(overlay);
        iqModal = overlay;

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeIQModal();
        });
    }

    function setupEventListeners() {
        document.addEventListener('click', (e) => {
            const tab = e.target.closest('[data-tab]');
            if (tab) switchTab(tab.dataset.tab);
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeIQModal();
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
            console.error('[AnalysisIQ] Error:', error);
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
        document.getElementById('aiq-tab-standard')?.classList.toggle('active', tab === 'ai-driven');
        document.getElementById('aiq-tab-iq')?.classList.toggle('active', tab === 'analysis-iq');
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
                    <p style="color:#555;">No signals found.</p>
                </div>`;
            return;
        }

        grid.innerHTML = filteredSignals.map(s => renderCard(s)).join('');
        startCountdowns();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // SVG CHART GENERATOR
    // ═══════════════════════════════════════════════════════════════════════════

    function generateChartSVG(pattern, isBuy, seed = 1, isModal = false) {
        const w = isModal ? 760 : 280;
        const h = isModal ? 200 : 120;
        const patternType = (pattern || '').toUpperCase();

        // Pseudo-random generator
        let s = seed;
        const rand = (min, max) => { s = (s * 9301 + 49297) % 233280; return min + (s / 233280) * (max - min); };

        // Generate candles
        const candles = [];
        let price = 50;
        const trend = isBuy ? 0.2 : -0.2;

        for (let i = 0; i < 20; i++) {
            const vol = 2 + rand(0, 3);
            const open = price;
            const close = open + trend + rand(-1.5, 1.5);
            const high = Math.max(open, close) + rand(0.3, vol);
            const low = Math.min(open, close) - rand(0.3, vol);
            candles.push({ open, close, high, low, bull: close > open });
            price = close;
        }

        // Normalize
        const allP = candles.flatMap(c => [c.high, c.low]);
        const minP = Math.min(...allP), maxP = Math.max(...allP);
        const range = maxP - minP || 1;
        const toY = p => h - 10 - ((p - minP) / range) * (h - 20);

        // Draw candles
        const numCandles = isModal ? 40 : 20;
        const gap = (w - 20) / numCandles;
        const cw = isModal ? 10 : 6;
        let svg = '';

        // Generate more candles if modal
        if (isModal && candles.length < numCandles) {
            let p = candles[candles.length - 1]?.close || 50;
            for (let i = candles.length; i < numCandles; i++) {
                const vol = 2 + rand(0, 3);
                const open = p;
                const close = open + trend + rand(-1.5, 1.5);
                const high = Math.max(open, close) + rand(0.3, vol);
                const low = Math.min(open, close) - rand(0.3, vol);
                candles.push({ open, close, high, low, bull: close > open });
                p = close;
            }
            // Recalculate normalization
            const allP2 = candles.flatMap(c => [c.high, c.low]);
            const minP2 = Math.min(...allP2), maxP2 = Math.max(...allP2);
            const range2 = maxP2 - minP2 || 1;
            const toY2 = p => h - 10 - ((p - minP2) / range2) * (h - 20);
            
            candles.forEach((c, i) => {
                const x = 10 + i * gap + gap / 2;
                const color = c.bull ? '#26a69a' : '#ef5350';
                svg += `<line x1="${x}" y1="${toY2(c.high)}" x2="${x}" y2="${toY2(c.low)}" stroke="${color}" stroke-width="1"/>`;
                const top = Math.min(toY2(c.open), toY2(c.close));
                const ht = Math.max(2, Math.abs(toY2(c.open) - toY2(c.close)));
                svg += `<rect x="${x - cw/2}" y="${top}" width="${cw}" height="${ht}" fill="${color}"/>`;
            });
        } else {
            candles.forEach((c, i) => {
                const x = 10 + i * gap + gap / 2;
                const color = c.bull ? '#26a69a' : '#ef5350';
                svg += `<line x1="${x}" y1="${toY(c.high)}" x2="${x}" y2="${toY(c.low)}" stroke="${color}" stroke-width="1"/>`;
                const top = Math.min(toY(c.open), toY(c.close));
                const ht = Math.max(2, Math.abs(toY(c.open) - toY(c.close)));
                svg += `<rect x="${x - cw/2}" y="${top}" width="${cw}" height="${ht}" fill="${color}"/>`;
            });
        }

        // Pattern lines
        const lc = '#6366f1';
        const lw = isModal ? 3 : 2;
        const midY = toY((maxP + minP) / 2);
        const topY = toY(maxP - range * 0.1);
        const botY = toY(minP + range * 0.1);

        if (patternType.includes('SYMMETRICAL') || patternType.includes('TRIANGLE')) {
            svg += `<line x1="15" y1="${topY}" x2="${w-25}" y2="${midY+5}" stroke="${lc}" stroke-width="${lw}"/>`;
            svg += `<line x1="15" y1="${botY}" x2="${w-25}" y2="${midY-5}" stroke="${lc}" stroke-width="${lw}"/>`;
        } else if (patternType.includes('WEDGE')) {
            const offset = isBuy ? 10 : -10;
            svg += `<line x1="15" y1="${topY}" x2="${w-25}" y2="${midY+offset}" stroke="${lc}" stroke-width="${lw}"/>`;
            svg += `<line x1="15" y1="${botY}" x2="${w-25}" y2="${midY+offset*0.5}" stroke="${lc}" stroke-width="${lw}"/>`;
        } else if (patternType.includes('FLAG')) {
            const y1 = toY(minP + range * 0.65), y2 = toY(minP + range * 0.35);
            const startX = isModal ? 100 : 50;
            svg += `<line x1="${startX}" y1="${y1}" x2="${w-20}" y2="${y1-8}" stroke="${lc}" stroke-width="${lw}"/>`;
            svg += `<line x1="${startX}" y1="${y2}" x2="${w-20}" y2="${y2-8}" stroke="${lc}" stroke-width="${lw}"/>`;
        } else if (patternType.includes('PENNANT')) {
            const cx = w * 0.55;
            const spread = isModal ? 80 : 50;
            svg += `<line x1="${cx-spread}" y1="${midY-20}" x2="${cx+spread*0.8}" y2="${midY}" stroke="${lc}" stroke-width="${lw}"/>`;
            svg += `<line x1="${cx-spread}" y1="${midY+20}" x2="${cx+spread*0.8}" y2="${midY}" stroke="${lc}" stroke-width="${lw}"/>`;
        } else if (patternType.includes('DOUBLE') && patternType.includes('BOTTOM')) {
            const by = toY(minP + range * 0.05);
            const x1 = isModal ? 150 : 60, x2 = isModal ? 450 : 160;
            svg += `<circle cx="${x1}" cy="${by}" r="${isModal ? 8 : 5}" fill="none" stroke="${lc}" stroke-width="${lw}"/>`;
            svg += `<circle cx="${x2}" cy="${by}" r="${isModal ? 8 : 5}" fill="none" stroke="${lc}" stroke-width="${lw}"/>`;
            svg += `<line x1="${x1}" y1="${by}" x2="${x2}" y2="${by}" stroke="${lc}" stroke-width="1" stroke-dasharray="4,2"/>`;
        } else if (patternType.includes('DOUBLE') && patternType.includes('TOP')) {
            const ty = toY(maxP - range * 0.05);
            const x1 = isModal ? 150 : 60, x2 = isModal ? 450 : 160;
            svg += `<circle cx="${x1}" cy="${ty}" r="${isModal ? 8 : 5}" fill="none" stroke="${lc}" stroke-width="${lw}"/>`;
            svg += `<circle cx="${x2}" cy="${ty}" r="${isModal ? 8 : 5}" fill="none" stroke="${lc}" stroke-width="${lw}"/>`;
            svg += `<line x1="${x1}" y1="${ty}" x2="${x2}" y2="${ty}" stroke="${lc}" stroke-width="1" stroke-dasharray="4,2"/>`;
        } else {
            // Default horizontal line
            svg += `<line x1="10" y1="${midY}" x2="${w-10}" y2="${midY}" stroke="${lc}" stroke-width="${lw}" stroke-dasharray="5,3"/>`;
        }

        return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><rect width="100%" height="100%" fill="#0a0a0a"/>${svg}</svg>`;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // CARD RENDER
    // ═══════════════════════════════════════════════════════════════════════════

    function getAssetIcon(symbol, assetType) {
        const map = {
            'XAUUSD': { t: 'Au', c: '' },
            'XAGUSD': { t: 'Ag', c: '' },
            'BTCUSD': { t: '₿', c: 'crypto' },
            'ETHUSD': { t: 'Ξ', c: 'crypto' },
            'US30': { t: '🇺🇸', c: 'flag' },
            'GER40': { t: '🇩🇪', c: 'flag' },
            'CHINA50': { t: '🇨🇳', c: 'flag' },
        };
        if (map[symbol]) return map[symbol];

        const flags = { EU: '🇪🇺', GB: '🇬🇧', US: '🇺🇸', JP: '🇯🇵', AU: '🇦🇺', NZ: '🇳🇿', CA: '🇨🇦', CH: '🇨🇭' };
        const cc = symbol?.substring(0, 2);
        if (flags[cc]) return { t: flags[cc], c: 'flag' };

        return { t: symbol?.substring(0, 2) || '?', c: 'forex' };
    }

    function renderCard(signal) {
        const isBuy = (signal.direction || '').toUpperCase().includes('BUY');
        const pattern = (signal.pattern || 'Pattern').replace(/_/g, ' ');
        const patternShort = pattern.length > 16 ? pattern.substring(0, 14) + '...' : pattern;
        const tf = signal.timeframe || '4H';
        const icon = getAssetIcon(signal.symbol, signal.asset_type);
        const tvSymbol = getTVSymbol(signal.symbol);

        return `
        <div class="aiq-card">
            <!-- Live Trade Badge + TV Icon -->
            <div class="aiq-live-badge-wrapper">
                <span class="aiq-live-badge">Live Trade</span>
                <a href="https://www.tradingview.com/chart/?symbol=${tvSymbol}" target="_blank" class="aiq-tv-icon" title="Open in TradingView">
                    <svg viewBox="0 0 24 24"><path d="M4 4h16v16H4V4zm2 2v12h12V6H6zm2 4h8v2H8v-2z"/></svg>
                </a>
            </div>

            <!-- Symbol Row -->
            <div class="aiq-symbol-row">
                <div class="aiq-asset-icon ${icon.c}">${icon.t}</div>
                <div class="aiq-symbol-info">
                    <div class="aiq-symbol-name">
                        ${esc(signal.symbol)}
                        <span class="aiq-pattern-tag">${esc(patternShort)}</span>
                    </div>
                    <div class="aiq-confidence">${signal.confidence || 75}% Confidence</div>
                </div>
            </div>

            <!-- Order Badge -->
            <div class="aiq-order-badge-wrapper">
                <span class="aiq-order-badge ${isBuy ? 'aiq-order-buy' : 'aiq-order-sell'}">
                    ${isBuy ? 'BUY STOP' : 'SELL STOP'}
                </span>
            </div>

            <!-- Price List -->
            <div class="aiq-price-list">
                <div class="aiq-price-row">
                    <span class="aiq-price-label">Entry</span>
                    <span class="aiq-price-value">${esc(signal.entry || '—')}</span>
                </div>
                <div class="aiq-price-row">
                    <span class="aiq-price-label">Target</span>
                    <span class="aiq-price-value target">${esc(signal.target || '—')}</span>
                </div>
                <div class="aiq-price-row">
                    <span class="aiq-price-label">Stop</span>
                    <span class="aiq-price-value stop">${esc(signal.stop || '—')}</span>
                </div>
                <div class="aiq-price-row">
                    <span class="aiq-price-label">Expires</span>
                    <span class="aiq-price-value expires aiq-countdown" id="aiq-exp-${signal.id}" data-expiry="${signal.expires_at || ''}">${formatCountdown(signal.expires_at)}</span>
                </div>
            </div>

            <!-- Chart -->
            <div class="aiq-chart">
                ${generateChartSVG(signal.pattern, isBuy, signal.id)}
                <div class="aiq-tf-badge">${esc(tf)}</div>
            </div>

            <!-- Learn More -->
            <button class="aiq-learn-btn" onclick="window.EnhancedSignalsPage.openDeepInsight(${signal.id})">
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
            'AUDUSD': 'FX:AUDUSD', 'XAUUSD': 'OANDA:XAUUSD', 'XAGUSD': 'OANDA:XAGUSD',
            'US30': 'TVC:DJI', 'GER40': 'XETR:DAX', 'BTCUSD': 'BITSTAMP:BTCUSD',
        };
        return map[symbol] || `FX:${symbol}`;
    }

    function getCountryFlag(symbol) {
        const cc = symbol?.substring(0, 2);
        const flags = { EU: '🇪🇺', GB: '🇬🇧', US: '🇺🇸', JP: '🇯🇵', AU: '🇦🇺', NZ: '🇳🇿', CA: '🇨🇦', XA: '🪙' };
        return flags[cc] || '🌐';
    }

    function openDeepInsight(signalId) {
        const signal = allSignals.find(s => s.id === signalId);
        if (!signal || !iqModal) return;

        const isBuy = (signal.direction || '').toUpperCase().includes('BUY');
        const pattern = (signal.pattern || 'Pattern').replace(/_/g, ' ');
        const edu = getPatternEducation(signal.pattern);
        const tvSymbol = getTVSymbol(signal.symbol);
        const flag = getCountryFlag(signal.symbol);
        const bullish = signal.sentiment_bullish || 50;
        const bearish = signal.sentiment_bearish || 50;

        // Format dates
        const pubDate = signal.created_at ? new Date(signal.created_at).toLocaleString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—';
        const expDate = signal.expires_at ? new Date(signal.expires_at).toLocaleString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—';

        const modal = document.getElementById('aiq-modal');
        modal.innerHTML = `
            <!-- Header Bar -->
            <div class="aiq-modal-header-bar">
                <div class="aiq-modal-header-top">
                    <div class="aiq-modal-flag">${flag}</div>
                    <span class="aiq-modal-symbol-badge">${esc(signal.symbol)}</span>
                    <span class="aiq-modal-full-name">${esc(signal.full_name || signal.symbol)}</span>
                    <div class="aiq-modal-price">
                        <div class="aiq-modal-price-value">${esc(signal.entry || '—')}</div>
                        <div class="aiq-modal-price-change ${isBuy ? 'up' : 'down'}">
                            ${isBuy ? '▲' : '▼'} ${esc(signal.price_change_percent || '0.00%')}
                        </div>
                    </div>
                </div>

                <div class="aiq-modal-badges">
                    <span class="aiq-order-badge ${isBuy ? 'aiq-order-buy' : 'aiq-order-sell'}">
                        ${isBuy ? 'BUY STOP' : 'SELL STOP'}
                    </span>
                    <span class="aiq-live-badge">Live Trade</span>
                </div>

                <div class="aiq-modal-info-grid">
                    <div class="aiq-modal-info-item">
                        <div class="aiq-modal-info-value entry">${esc(pattern)}</div>
                        <div class="aiq-modal-info-label">Pattern</div>
                    </div>
                    <div class="aiq-modal-info-item">
                        <div class="aiq-modal-info-value entry">${esc(signal.entry || '—')}</div>
                        <div class="aiq-modal-info-label">Entry</div>
                    </div>
                    <div class="aiq-modal-info-item">
                        <div class="aiq-modal-info-value">${esc(signal.target || '—')}</div>
                        <div class="aiq-modal-info-label">Target</div>
                    </div>
                    <div class="aiq-modal-info-item">
                        <div class="aiq-modal-info-value stop">${esc(signal.stop || '—')}</div>
                        <div class="aiq-modal-info-label">Stop</div>
                    </div>
                    <div class="aiq-modal-info-item">
                        <div class="aiq-modal-info-value" style="color:#a78bfa;">${signal.confidence || 75}%</div>
                        <div class="aiq-modal-info-label">Confidence</div>
                    </div>
                    <div class="aiq-modal-info-item" style="grid-column: span 2;">
                        <div class="aiq-sentiment">
                            <span class="aiq-sentiment-label">🐻 ${bearish}%</span>
                            <div class="aiq-sentiment-bar">
                                <div class="aiq-sentiment-bear" style="width:${bearish}%"></div>
                                <div class="aiq-sentiment-bull" style="width:${bullish}%"></div>
                            </div>
                            <span class="aiq-sentiment-label">${bullish}% 🐂</span>
                        </div>
                        <div class="aiq-modal-info-label">News Sentiment</div>
                    </div>
                </div>
            </div>

            <!-- Body: Chart + Pattern Education -->
            <div class="aiq-modal-body">
                <!-- Pattern Chart -->
                <div class="aiq-modal-chart">
                    ${generateChartSVG(signal.pattern, isBuy, signal.id, true)}
                    <div class="aiq-tf-badge">${esc(signal.timeframe || '4H')}</div>
                </div>

                <div class="aiq-modal-title-row">
                    <span class="aiq-modal-title">Trade Idea</span>
                    <a href="https://www.tradingview.com/chart/?symbol=${tvSymbol}" target="_blank" class="aiq-modal-tv-icon" title="Open in TradingView">
                        <svg viewBox="0 0 24 24"><path d="M4 4h16v16H4V4zm2 2v12h12V6H6zm2 4h8v2H8v-2z"/></svg>
                    </a>
                </div>
                <span class="aiq-live-badge" style="margin-bottom:12px;">Live Trade</span>
                <div class="aiq-modal-meta">
                    Published at: ${pubDate}<br>
                    Expires at: ${expDate}
                </div>
                <div class="aiq-modal-description">${esc(edu.description)}</div>
            </div>

            <!-- Footer -->
            <div class="aiq-modal-footer">
                <button class="aiq-modal-btn aiq-modal-btn-primary" onclick="window.EnhancedSignalsPage.copyToMT5(${signal.id})">
                    Copy to MT5
                </button>
                <button class="aiq-modal-btn aiq-modal-btn-secondary" onclick="window.EnhancedSignalsPage.closeIQModal()">
                    Close
                </button>
            </div>
        `;

        iqModal.classList.add('open');
    }

    function closeIQModal() {
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
            document.querySelectorAll('.aiq-countdown[data-expiry]').forEach(el => {
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
        closeIQModal,
        copyToMT5,
        switchTab,
        openSignalModal: openDeepInsight,
        closeModal: closeIQModal,
    };

})();
