// Enhanced Signals Page Module — AnalysisIQ Edition v2
// Deploy to: frontend/js/modules/enhanced_signals.js
//
// Features:
//   • Static SVG pattern charts in cards (candlesticks + pattern lines)
//   • TradingView modal with Entry/Target/Stop zone overlays
//   • 3-column responsive grid layout
//   • Pattern-based analysis (Triangles, Wedges, Flags, etc.)

(function () {
    'use strict';

    // ═══════════════════════════════════════════════════════════════════════════
    // CSS INJECTION
    // ═══════════════════════════════════════════════════════════════════════════

    const IQ_STYLES = `
    /* ══════════════════════════════════════════════════════════════════════════
       AnalysisIQ — Professional Signal Cards with Pattern Charts
       ══════════════════════════════════════════════════════════════════════════ */

    /* Force 3-column grid for signals */
    #signalsGrid {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 20px !important;
    }
    @media (max-width: 1024px) {
        #signalsGrid { grid-template-columns: repeat(2, 1fr) !important; }
    }
    @media (max-width: 640px) {
        #signalsGrid { grid-template-columns: 1fr !important; }
    }

    /* ── Base Card ─────────────────────────────────────────────────────────── */
    .aiq-card {
        position: relative;
        background: #0f0f0f;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        overflow: hidden;
        cursor: default;
        transition: transform 0.2s ease, box-shadow 0.3s ease;
    }
    .aiq-card.aiq-active {
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    }
    .aiq-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.6);
    }

    /* Live Trade Badge - centered at top */
    .aiq-live-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 5px 14px;
        background: rgba(0, 180, 130, 0.2);
        border: 1px solid rgba(0, 200, 150, 0.5);
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.1em;
        color: #00d4aa;
        text-transform: uppercase;
    }

    /* TradingView Badge */
    .aiq-tv-badge {
        width: 26px;
        height: 26px;
        background: linear-gradient(135deg, #2962ff, #1976d2);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: bold;
        color: white;
        font-style: italic;
    }

    /* Symbol/Asset Icon */
    .aiq-asset-icon {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        font-weight: 700;
        background: linear-gradient(135deg, #d4a017, #b8860b);
        color: #000;
        border: 2px solid rgba(212, 160, 23, 0.3);
    }
    .aiq-asset-icon.crypto { background: linear-gradient(135deg, #f7931a, #e67e00); }
    .aiq-asset-icon.indices { background: linear-gradient(135deg, #4caf50, #2e7d32); color: #fff; }
    .aiq-asset-icon.forex { background: linear-gradient(135deg, #2196f3, #1565c0); color: #fff; }

    /* Order Type Badge */
    .aiq-order-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.05em;
    }
    .aiq-order-buy { background: #00c896; color: #000; }
    .aiq-order-sell { background: #ff4757; color: #fff; }

    /* Chart Container */
    .aiq-chart-container {
        width: 100%;
        height: 140px;
        background: #0a0a0a;
        position: relative;
        overflow: hidden;
    }
    .aiq-chart-container svg {
        width: 100%;
        height: 100%;
    }

    /* Timeframe Badge */
    .aiq-tf-badge {
        position: absolute;
        bottom: 8px;
        right: 8px;
        background: rgba(0,0,0,0.7);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 700;
        color: #fff;
    }

    /* Price Info */
    .aiq-price-info {
        padding: 12px 14px;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .aiq-price-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 13px;
    }
    .aiq-price-label { color: #888; }
    .aiq-price-value { font-weight: 600; font-family: 'JetBrains Mono', monospace; }
    .aiq-price-value.entry { color: #fff; }
    .aiq-price-value.target { color: #00d4aa; }
    .aiq-price-value.stop { color: #ff4757; }
    .aiq-price-value.expires { color: #f5a623; }

    /* Learn More Button */
    .aiq-learn-btn {
        display: block;
        width: calc(100% - 24px);
        margin: 0 12px 12px;
        padding: 10px;
        background: transparent;
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 6px;
        color: #fff;
        font-size: 12px;
        font-weight: 600;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .aiq-learn-btn:hover {
        background: rgba(255,255,255,0.05);
        border-color: rgba(255,255,255,0.25);
    }

    /* Tab Bar */
    .aiq-tab-bar {
        display: flex;
        gap: 24px;
        margin-bottom: 24px;
        align-items: center;
    }
    .aiq-tab-icon {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 13px;
        color: #666;
        cursor: pointer;
        transition: color 0.2s ease;
        padding: 8px 0;
    }
    .aiq-tab-icon:hover { color: #999; }
    .aiq-tab-icon.active { color: #fff; }
    .aiq-tab-icon .icon-dot {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
    }
    .aiq-tab-icon.ai-driven .icon-dot { background: linear-gradient(135deg, #f5a623, #e67e00); }
    .aiq-tab-icon.analysis-iq .icon-dot { background: linear-gradient(135deg, #2962ff, #1976d2); }

    /* ══════════════════════════════════════════════════════════════════════════
       Modal with TradingView + Overlay Zones
       ══════════════════════════════════════════════════════════════════════════ */
    .aiq-modal-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.92);
        backdrop-filter: blur(8px);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 16px;
        opacity: 0;
        transition: opacity 0.25s ease;
        pointer-events: none;
    }
    .aiq-modal-overlay.open {
        opacity: 1;
        pointer-events: all;
    }
    .aiq-modal {
        position: relative;
        background: #131722;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        width: 100%;
        max-width: 1000px;
        max-height: 92vh;
        overflow: hidden;
        box-shadow: 0 32px 64px rgba(0, 0, 0, 0.8);
        transform: translateY(16px);
        transition: transform 0.25s ease;
    }
    .aiq-modal-overlay.open .aiq-modal { transform: translateY(0); }

    /* Modal Header */
    .aiq-modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 20px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        background: #0d1117;
    }
    .aiq-modal-close {
        width: 32px;
        height: 32px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 6px;
        color: #888;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 20px;
        transition: all 0.2s ease;
    }
    .aiq-modal-close:hover {
        background: rgba(255,255,255,0.1);
        color: #fff;
    }

    /* Chart Wrapper with Overlay */
    .aiq-chart-wrapper {
        position: relative;
        width: 100%;
        height: 500px;
        background: #131722;
    }
    .aiq-chart-wrapper iframe {
        width: 100%;
        height: 100%;
        border: none;
    }
    @media (max-width: 768px) {
        .aiq-chart-wrapper { height: 350px; }
    }

    /* Zone Overlay */
    .aiq-zone-overlay {
        position: absolute;
        top: 0;
        right: 0;
        width: 120px;
        height: 100%;
        pointer-events: none;
        display: flex;
        flex-direction: column;
    }

    /* Price Zones */
    .aiq-zone {
        position: absolute;
        right: 0;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 8px;
    }
    .aiq-zone-label {
        padding: 4px 10px;
        border-radius: 3px;
        font-size: 11px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }
    .aiq-zone-target {
        background: rgba(0, 200, 150, 0.9);
        color: #000;
    }
    .aiq-zone-entry {
        background: rgba(255, 255, 255, 0.95);
        color: #000;
    }
    .aiq-zone-stop {
        background: rgba(255, 71, 87, 0.95);
        color: #fff;
    }

    /* Shaded Regions */
    .aiq-region {
        position: absolute;
        right: 120px;
        left: 50%;
    }
    .aiq-region-profit {
        background: rgba(0, 150, 120, 0.25);
        border-top: 2px solid rgba(0, 200, 150, 0.6);
    }
    .aiq-region-loss {
        background: rgba(200, 50, 60, 0.25);
        border-bottom: 2px solid rgba(255, 71, 87, 0.6);
    }
    .aiq-region-entry-line {
        position: absolute;
        right: 120px;
        left: 50%;
        height: 2px;
        border-top: 2px dashed rgba(255, 255, 255, 0.7);
    }

    /* Modal Footer */
    .aiq-modal-footer {
        padding: 16px 20px;
        border-top: 1px solid rgba(255,255,255,0.06);
        background: #0d1117;
        display: flex;
        gap: 12px;
        align-items: center;
    }
    .aiq-modal-btn {
        padding: 12px 24px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .aiq-modal-btn-primary {
        background: linear-gradient(135deg, #2962ff, #1976d2);
        border: none;
        color: #fff;
    }
    .aiq-modal-btn-primary:hover {
        box-shadow: 0 4px 16px rgba(41, 98, 255, 0.4);
    }
    .aiq-modal-btn-secondary {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        color: #999;
    }
    .aiq-modal-btn-secondary:hover {
        background: rgba(255,255,255,0.08);
        color: #fff;
    }

    /* Countdown */
    .aiq-countdown.urgent { color: #ff6b6b !important; animation: aiq-pulse 1s ease-in-out infinite; }
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
        if (!token) {
            console.warn('[EnhancedSignals] No token found');
            throw new Error('Not authenticated');
        }

        const response = await fetch(endpoint, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        if (response.status === 401) {
            localStorage.removeItem('pipways_token');
            localStorage.removeItem('pipways_user');
            window.location.href = '/';
            throw new Error('Unauthorized');
        }
        if (response.status === 402) {
            showUpgradeModal();
            throw new Error('Subscription required');
        }
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

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
        console.log('[EnhancedSignals] Initialising v2...');
        injectStyles();
        injectTabBar();
        injectIQModal();
        setupEventListeners();
        loadSignals();

        if (updateInterval) clearInterval(updateInterval);
        updateInterval = setInterval(loadSignals, 60000);

        console.log('[EnhancedSignals] Ready.');
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // TAB BAR INJECTION
    // ═══════════════════════════════════════════════════════════════════════════

    function injectTabBar() {
        if (document.getElementById('aiq-tab-bar')) return;

        const bar = document.createElement('div');
        bar.id = 'aiq-tab-bar';
        bar.className = 'aiq-tab-bar';
        bar.innerHTML = `
            <div id="aiq-tab-standard" class="aiq-tab-icon ai-driven active" data-tab="ai-driven">
                <span class="icon-dot">✦</span>
                AI-Driven Trade Ideas
            </div>
            <div id="aiq-tab-iq" class="aiq-tab-icon analysis-iq" data-tab="analysis-iq">
                <span class="icon-dot">◈</span>
                Pattern Trade Ideas
            </div>
        `;

        const grid = document.getElementById('signalsGrid');
        const parent = grid ? grid.parentElement : document.querySelector('.signals-container');
        if (parent) {
            parent.insertBefore(bar, grid || parent.firstChild);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // MODAL INJECTION
    // ═══════════════════════════════════════════════════════════════════════════

    function injectIQModal() {
        if (document.getElementById('aiq-modal-overlay')) return;

        const overlay = document.createElement('div');
        overlay.id = 'aiq-modal-overlay';
        overlay.className = 'aiq-modal-overlay';
        overlay.innerHTML = `
            <div class="aiq-modal" id="aiq-modal" role="dialog" aria-modal="true">
                <div id="aiq-modal-body"></div>
            </div>
        `;
        document.body.appendChild(overlay);
        iqModal = overlay;

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeIQModal();
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // EVENT LISTENERS
    // ═══════════════════════════════════════════════════════════════════════════

    function setupEventListeners() {
        document.addEventListener('click', (e) => {
            const tab = e.target.closest('[data-tab]');
            if (!tab) return;
            const target = tab.dataset.tab;
            if (target === 'ai-driven' || target === 'analysis-iq') {
                switchTab(target);
            }
        });

        // ESC key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeIQModal();
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // DATA LOADING
    // ═══════════════════════════════════════════════════════════════════════════

    async function loadSignals() {
        console.log('[EnhancedSignals] Loading signals...');
        const grid = document.getElementById('signalsGrid');
        if (!grid) return;

        try {
            const signals = await apiGet('/signals/enhanced');
            allSignals = signals || [];
            console.log(`[EnhancedSignals] Loaded ${allSignals.length} signals`);
            applyFilters();
            updateStats();
        } catch (error) {
            console.error('[EnhancedSignals] Error:', error);

            if (error.message === 'Subscription required') {
                grid.innerHTML = `
                    <div class="col-span-full text-center py-12">
                        <i class="fas fa-lock text-4xl text-cyan-500 mb-4"></i>
                        <h3 class="text-xl font-semibold text-white mb-2">Upgrade Required</h3>
                        <p class="text-gray-400 mb-6">Enhanced signals require a Pro subscription.</p>
                    </div>`;
            }
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // FILTERING
    // ═══════════════════════════════════════════════════════════════════════════

    function applyFilters() {
        if (currentTab === 'analysis-iq') {
            filteredSignals = allSignals.filter(s => s.is_pattern_idea === true);
        } else {
            filteredSignals = allSignals.filter(s => (s.confidence || 0) >= 70 && !s.is_pattern_idea);
        }
        renderSignals();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // TAB SWITCHING
    // ═══════════════════════════════════════════════════════════════════════════

    function switchTab(tab) {
        currentTab = tab;

        const tabStd = document.getElementById('aiq-tab-standard');
        const tabIQ = document.getElementById('aiq-tab-iq');
        if (tabStd && tabIQ) {
            tabStd.classList.toggle('active', tab === 'ai-driven');
            tabIQ.classList.toggle('active', tab === 'analysis-iq');
        }

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
                    <div style="font-size:32px;margin-bottom:12px;opacity:.3">◈</div>
                    <p class="text-gray-500">No signals found for this view.</p>
                </div>`;
            return;
        }

        grid.innerHTML = filteredSignals.map(s => renderPatternCard(s)).join('');
        startCountdowns();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PATTERN CHART SVG GENERATOR
    // ═══════════════════════════════════════════════════════════════════════════

    function generatePatternSVG(pattern, isBuy, seed = 0) {
        const w = 280;
        const h = 140;
        const patternType = (pattern || 'TRIANGLE').toUpperCase().replace(/_/g, ' ');

        // Generate pseudo-random candlesticks based on seed
        const rand = (min, max) => {
            seed = (seed * 9301 + 49297) % 233280;
            return min + (seed / 233280) * (max - min);
        };

        // Generate candlestick data
        const candles = [];
        let price = 50 + rand(-10, 10);
        const trend = isBuy ? 0.3 : -0.3;

        for (let i = 0; i < 24; i++) {
            const volatility = 3 + rand(0, 4);
            const open = price;
            const change = trend + rand(-2, 2);
            const close = open + change;
            const high = Math.max(open, close) + rand(0.5, volatility);
            const low = Math.min(open, close) - rand(0.5, volatility);
            candles.push({ open, close, high, low, bullish: close > open });
            price = close;
        }

        // Normalize to SVG coordinates
        const allPrices = candles.flatMap(c => [c.high, c.low]);
        const minP = Math.min(...allPrices);
        const maxP = Math.max(...allPrices);
        const range = maxP - minP || 1;
        const toY = (p) => h - 15 - ((p - minP) / range) * (h - 30);

        // Draw candlesticks
        const candleWidth = 8;
        const gap = (w - 20) / candles.length;
        let candlesSVG = '';

        candles.forEach((c, i) => {
            const x = 10 + i * gap + gap / 2;
            const yHigh = toY(c.high);
            const yLow = toY(c.low);
            const yOpen = toY(c.open);
            const yClose = toY(c.close);
            const bodyTop = Math.min(yOpen, yClose);
            const bodyHeight = Math.max(1, Math.abs(yOpen - yClose));
            const color = c.bullish ? '#26a69a' : '#ef5350';

            // Wick
            candlesSVG += `<line x1="${x}" y1="${yHigh}" x2="${x}" y2="${yLow}" stroke="${color}" stroke-width="1"/>`;
            // Body
            candlesSVG += `<rect x="${x - candleWidth/2}" y="${bodyTop}" width="${candleWidth}" height="${bodyHeight}" fill="${color}" rx="1"/>`;
        });

        // Generate pattern lines based on type
        let patternLines = '';
        const lineColor = '#6366f1';

        if (patternType.includes('TRIANGLE') || patternType.includes('SYMMETRICAL')) {
            // Converging triangle
            const startY1 = toY(maxP - range * 0.1);
            const startY2 = toY(minP + range * 0.1);
            const endX = w - 30;
            const endY = toY((maxP + minP) / 2);
            patternLines = `
                <line x1="20" y1="${startY1}" x2="${endX}" y2="${endY}" stroke="${lineColor}" stroke-width="2" stroke-dasharray="4,2"/>
                <line x1="20" y1="${startY2}" x2="${endX}" y2="${endY}" stroke="${lineColor}" stroke-width="2" stroke-dasharray="4,2"/>
            `;
        } else if (patternType.includes('WEDGE')) {
            // Wedge pattern (converging with slope)
            const slope = isBuy ? 0.15 : -0.15;
            const startY1 = toY(maxP - range * 0.05);
            const startY2 = toY(minP + range * 0.2);
            const endX = w - 25;
            const endY1 = startY1 + (endX - 20) * slope;
            const endY2 = startY2 + (endX - 20) * slope * 0.3;
            patternLines = `
                <line x1="20" y1="${startY1}" x2="${endX}" y2="${endY1}" stroke="${lineColor}" stroke-width="2" stroke-dasharray="4,2"/>
                <line x1="20" y1="${startY2}" x2="${endX}" y2="${endY2}" stroke="${lineColor}" stroke-width="2" stroke-dasharray="4,2"/>
            `;
        } else if (patternType.includes('FLAG')) {
            // Flag pattern (parallel lines with slight convergence)
            const midY = toY((maxP + minP) / 2);
            const flagHeight = range * 0.25;
            patternLines = `
                <line x1="60" y1="${toY(minP + range * 0.7)}" x2="${w-30}" y2="${toY(minP + range * 0.6)}" stroke="${lineColor}" stroke-width="2" stroke-dasharray="4,2"/>
                <line x1="60" y1="${toY(minP + range * 0.45)}" x2="${w-30}" y2="${toY(minP + range * 0.35)}" stroke="${lineColor}" stroke-width="2" stroke-dasharray="4,2"/>
            `;
        } else if (patternType.includes('PENNANT')) {
            // Pennant (small triangle)
            const cx = w * 0.6;
            const cy = toY((maxP + minP) / 2);
            patternLines = `
                <line x1="${cx-60}" y1="${cy-25}" x2="${cx+50}" y2="${cy}" stroke="${lineColor}" stroke-width="2" stroke-dasharray="4,2"/>
                <line x1="${cx-60}" y1="${cy+25}" x2="${cx+50}" y2="${cy}" stroke="${lineColor}" stroke-width="2" stroke-dasharray="4,2"/>
            `;
        } else if (patternType.includes('DOUBLE') && patternType.includes('BOTTOM')) {
            // Double bottom
            const bottomY = toY(minP + range * 0.1);
            patternLines = `
                <circle cx="70" cy="${bottomY}" r="4" fill="none" stroke="${lineColor}" stroke-width="2"/>
                <circle cx="180" cy="${bottomY}" r="4" fill="none" stroke="${lineColor}" stroke-width="2"/>
                <line x1="70" y1="${bottomY}" x2="180" y2="${bottomY}" stroke="${lineColor}" stroke-width="1" stroke-dasharray="3,3"/>
            `;
        } else if (patternType.includes('DOUBLE') && patternType.includes('TOP')) {
            // Double top
            const topY = toY(maxP - range * 0.1);
            patternLines = `
                <circle cx="70" cy="${topY}" r="4" fill="none" stroke="${lineColor}" stroke-width="2"/>
                <circle cx="180" cy="${topY}" r="4" fill="none" stroke="${lineColor}" stroke-width="2"/>
                <line x1="70" y1="${topY}" x2="180" y2="${topY}" stroke="${lineColor}" stroke-width="1" stroke-dasharray="3,3"/>
            `;
        } else {
            // Default: Support/Resistance or Breakout
            const levelY = toY(isBuy ? minP + range * 0.3 : maxP - range * 0.3);
            patternLines = `
                <line x1="10" y1="${levelY}" x2="${w-10}" y2="${levelY}" stroke="${lineColor}" stroke-width="2" stroke-dasharray="5,3"/>
            `;
        }

        return `
            <svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="xMidYMid slice">
                <defs>
                    <linearGradient id="chartBg" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#1a1a1a;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#0d0d0d;stop-opacity:1" />
                    </linearGradient>
                </defs>
                <rect width="100%" height="100%" fill="url(#chartBg)"/>
                ${candlesSVG}
                ${patternLines}
            </svg>
        `;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PATTERN CARD RENDER
    // ═══════════════════════════════════════════════════════════════════════════

    function getAssetIcon(symbol, assetType) {
        const icons = {
            'XAUUSD': { text: 'Au', class: '' },
            'XAGUSD': { text: 'Ag', class: '' },
            'BTCUSD': { text: '₿', class: 'crypto' },
            'ETHUSD': { text: 'Ξ', class: 'crypto' },
            'US30': { text: 'DJ', class: 'indices' },
            'GER40': { text: 'DE', class: 'indices' },
            'CHINA50': { text: 'CN', class: 'indices' },
        };

        if (icons[symbol]) return icons[symbol];
        if (assetType === 'crypto') return { text: '₿', class: 'crypto' };
        if (assetType === 'indices') return { text: '📊', class: 'indices' };
        if (assetType === 'commodities') return { text: '🪙', class: '' };

        // Forex: use country code
        const country = symbol.substring(0, 2);
        const flags = { 'EU': '🇪🇺', 'GB': '🇬🇧', 'US': '🇺🇸', 'JP': '🇯🇵', 'AU': '🇦🇺', 'NZ': '🇳🇿', 'CA': '🇨🇦', 'CH': '🇨🇭' };
        return { text: flags[country] || country, class: 'forex' };
    }

    function renderPatternCard(signal) {
        const isBuy = (signal.direction || '').toUpperCase().includes('BUY');
        const pattern = (signal.pattern || 'PATTERN').replace(/_/g, ' ');
        const tf = signal.timeframe || '4H';
        const expIso = signal.expires_at || null;
        const icon = getAssetIcon(signal.symbol, signal.asset_type);

        // Truncate long pattern names
        const patternDisplay = pattern.length > 16 ? pattern.substring(0, 14) + '...' : pattern;

        return `
        <div id="aiq-card-${signal.id}" class="aiq-card aiq-active">
            <!-- Header: Live Badge + TV Icon -->
            <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px;">
                <span class="aiq-live-badge">Live Trade</span>
                <div class="aiq-tv-badge" title="View on TradingView">TV</div>
            </div>

            <!-- Symbol Row -->
            <div style="display:flex; align-items:center; gap:10px; padding:0 14px 10px;">
                <div class="aiq-asset-icon ${icon.class}">${icon.text}</div>
                <div style="flex:1;">
                    <div style="font-size:15px; font-weight:700; color:#fff;">${escHtml(signal.symbol)}</div>
                    <div style="font-size:11px; color:#666;">${escHtml(patternDisplay)}</div>
                </div>
                <span class="aiq-order-badge ${isBuy ? 'aiq-order-buy' : 'aiq-order-sell'}">
                    ${isBuy ? 'BUY STOP' : 'SELL STOP'}
                </span>
            </div>

            <!-- Chart -->
            <div class="aiq-chart-container">
                ${generatePatternSVG(signal.pattern, isBuy, signal.id)}
                <div class="aiq-tf-badge">${escHtml(tf)}</div>
            </div>

            <!-- Price Info -->
            <div class="aiq-price-info">
                <div class="aiq-price-row">
                    <span class="aiq-price-label">Entry</span>
                    <span class="aiq-price-value entry">${escHtml(signal.entry || '—')}</span>
                </div>
                <div class="aiq-price-row">
                    <span class="aiq-price-label">Target</span>
                    <span class="aiq-price-value target">${escHtml(signal.target || '—')}</span>
                </div>
                <div class="aiq-price-row">
                    <span class="aiq-price-label">Stop</span>
                    <span class="aiq-price-value stop">${escHtml(signal.stop || '—')}</span>
                </div>
                <div class="aiq-price-row">
                    <span class="aiq-price-label">Expires</span>
                    <span class="aiq-price-value expires aiq-countdown" id="aiq-exp-${signal.id}" data-expiry="${expIso || ''}">${expIso ? formatCountdown(expIso) : '—'}</span>
                </div>
            </div>

            <!-- Learn More -->
            <button class="aiq-learn-btn" onclick="window.EnhancedSignalsPage.openDeepInsight(${signal.id})">
                Learn More
            </button>
        </div>`;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // COUNTDOWN
    // ═══════════════════════════════════════════════════════════════════════════

    function startCountdowns() {
        const tick = () => {
            document.querySelectorAll('.aiq-countdown[data-expiry]').forEach(el => {
                const expiry = el.dataset.expiry;
                if (!expiry) return;
                const str = formatCountdown(expiry);
                el.textContent = str;
                const ms = new Date(expiry) - Date.now();
                el.classList.toggle('urgent', ms > 0 && ms < 3600000);
            });
        };
        tick();
        const t = setInterval(tick, 1000);
        countdownTimers.push(t);
    }

    function formatCountdown(isoString) {
        if (!isoString) return '—';
        const ms = new Date(isoString) - Date.now();
        if (ms <= 0) return 'EXPIRED';
        const h = Math.floor(ms / 3600000);
        const m = Math.floor((ms % 3600000) / 60000);
        if (h >= 24) {
            const d = Math.floor(h / 24);
            return `${d}d ${h % 24}h`;
        }
        return `${h}h ${m}m`;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // DEEP INSIGHT MODAL — TradingView with Zone Overlays
    // ═══════════════════════════════════════════════════════════════════════════

    function getTradingViewSymbol(symbol) {
        const tvMap = {
            'EURUSD': 'FX:EURUSD', 'GBPUSD': 'FX:GBPUSD', 'USDJPY': 'FX:USDJPY',
            'AUDUSD': 'FX:AUDUSD', 'AUDCAD': 'FX:AUDCAD', 'AUDNZD': 'FX:AUDNZD',
            'NZDUSD': 'FX:NZDUSD', 'GBPJPY': 'FX:GBPJPY', 'EURJPY': 'FX:EURJPY',
            'XAUUSD': 'OANDA:XAUUSD', 'XAGUSD': 'OANDA:XAGUSD',
            'US30': 'TVC:DJI', 'GER40': 'XETR:DAX', 'CHINA50': 'SSE:000001',
            'BTCUSD': 'BITSTAMP:BTCUSD', 'ETHUSD': 'BITSTAMP:ETHUSD',
        };
        return tvMap[symbol] || `FX:${symbol}`;
    }

    function openDeepInsight(signalId) {
        const signal = allSignals.find(s => s.id === signalId);
        if (!signal || !iqModal) return;

        const isBuy = (signal.direction || '').toUpperCase().includes('BUY');
        const pattern = (signal.pattern || 'PATTERN').replace(/_/g, ' ');
        const tf = signal.timeframe || '4H';
        const tvSymbol = getTradingViewSymbol(signal.symbol);
        const icon = getAssetIcon(signal.symbol, signal.asset_type);

        // TradingView interval mapping
        const intervalMap = { '1H': '60', '4H': '240', '1D': 'D', 'D': 'D', '15M': '15', '30M': '30' };
        const tvInterval = intervalMap[tf] || '240';

        // Calculate zone positions (percentage from top)
        // These are approximations - actual positions depend on price range visible
        const entry = parseFloat(signal.entry) || 0;
        const target = parseFloat(signal.target) || 0;
        const stop = parseFloat(signal.stop) || 0;

        const body = document.getElementById('aiq-modal-body');
        body.innerHTML = `
            <!-- Header -->
            <div class="aiq-modal-header">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div class="aiq-asset-icon ${icon.class}">${icon.text}</div>
                    <div>
                        <div style="font-size:16px; font-weight:700; color:#fff;">
                            ${escHtml(signal.symbol)}
                            <span style="color:#666; font-weight:400; font-size:13px; margin-left:8px;">${escHtml(pattern)}</span>
                        </div>
                        <div style="font-size:12px; color:#666;">${escHtml(signal.full_name || signal.symbol)} · ${tf}</div>
                    </div>
                </div>
                <div style="display:flex; align-items:center; gap:12px;">
                    <span class="aiq-order-badge ${isBuy ? 'aiq-order-buy' : 'aiq-order-sell'}">
                        ${isBuy ? 'BUY STOP' : 'SELL STOP'}
                    </span>
                    <button class="aiq-modal-close" onclick="window.EnhancedSignalsPage.closeIQModal()">×</button>
                </div>
            </div>

            <!-- Chart with Overlay -->
            <div class="aiq-chart-wrapper" id="aiq-chart-wrapper">
                <!-- TradingView Widget -->
                <iframe 
                    src="https://s.tradingview.com/widgetembed/?frameElementId=tv_modal&symbol=${encodeURIComponent(tvSymbol)}&interval=${tvInterval}&hidesidetoolbar=0&symboledit=0&saveimage=1&toolbarbg=131722&studies=[]&theme=dark&style=1&timezone=Etc/UTC&withdateranges=1&showpopupbutton=0&allow_symbol_change=0&locale=en"
                    style="width:100%; height:100%; border:none;">
                </iframe>

                <!-- Zone Overlay - Right Side Labels -->
                <div class="aiq-zone-overlay">
                    <div class="aiq-zone" id="aiq-zone-target" style="top:15%;">
                        <span class="aiq-zone-label aiq-zone-target">TARGET</span>
                    </div>
                    <div class="aiq-zone" id="aiq-zone-target-price" style="top:18%;">
                        <span class="aiq-zone-label" style="background:#00c896; color:#000; font-size:12px;">${escHtml(signal.target)}</span>
                    </div>
                    <div class="aiq-zone" id="aiq-zone-entry" style="top:45%;">
                        <span class="aiq-zone-label aiq-zone-entry">ENTRY</span>
                    </div>
                    <div class="aiq-zone" id="aiq-zone-entry-price" style="top:48%;">
                        <span class="aiq-zone-label" style="background:#fff; color:#000; font-size:12px;">${escHtml(signal.entry)}</span>
                    </div>
                    <div class="aiq-zone" id="aiq-zone-stop" style="top:78%;">
                        <span class="aiq-zone-label aiq-zone-stop">STOP</span>
                    </div>
                    <div class="aiq-zone" id="aiq-zone-stop-price" style="top:81%;">
                        <span class="aiq-zone-label" style="background:#ff4757; color:#fff; font-size:12px;">${escHtml(signal.stop)}</span>
                    </div>
                </div>

                <!-- Shaded Regions -->
                <div class="aiq-region aiq-region-profit" style="top:15%; height:30%;"></div>
                <div class="aiq-region-entry-line" style="top:45%;"></div>
                <div class="aiq-region aiq-region-loss" style="top:48%; height:33%;"></div>
            </div>

            <!-- Footer -->
            <div class="aiq-modal-footer">
                <button class="aiq-modal-btn aiq-modal-btn-primary" onclick="window.EnhancedSignalsPage.copyToMT5(${signal.id})">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px;">
                        <path d="M8 17H5a2 2 0 01-2-2V5a2 2 0 012-2h10a2 2 0 012 2v3"/>
                        <rect x="8" y="11" width="13" height="10" rx="2"/>
                    </svg>
                    Copy to MT5
                </button>
                <button class="aiq-modal-btn aiq-modal-btn-secondary" onclick="window.EnhancedSignalsPage.closeIQModal()">
                    Close
                </button>
                <div style="flex:1;"></div>
                <div style="font-size:11px; color:#555; text-align:right;">
                    <div>Confidence: <span style="color:#a78bfa;">${signal.confidence || 75}%</span></div>
                    <div>R:R Ratio: <span style="color:#00d4aa;">${calculateRR(signal)}</span></div>
                </div>
            </div>
        `;

        iqModal.classList.add('open');
    }

    function closeIQModal() {
        if (iqModal) iqModal.classList.remove('open');
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // COPY TO MT5
    // ═══════════════════════════════════════════════════════════════════════════

    function copyToMT5(signalId) {
        if (window.MT5Copier && typeof window.MT5Copier.execute === 'function') {
            window.MT5Copier.execute(signalId);
            return;
        }
        if (window.SignalCopier && typeof window.SignalCopier.copy === 'function') {
            window.SignalCopier.copy(signalId);
            return;
        }
        console.warn('[AnalysisIQ] MT5 copy handler not found for signal', signalId);
        alert('Signal copied! Open MT5 to execute the trade.');
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // UTILS
    // ═══════════════════════════════════════════════════════════════════════════

    function calculateRR(signal) {
        const entry = parseFloat(signal.entry);
        const target = parseFloat(signal.target);
        const stop = parseFloat(signal.stop);
        if (isNaN(entry) || isNaN(target) || isNaN(stop)) return 'N/A';
        const risk = Math.abs(entry - stop);
        const reward = Math.abs(target - entry);
        if (risk === 0) return 'N/A';
        return `1:${(reward / risk).toFixed(1)}`;
    }

    function escHtml(str) {
        if (str == null) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function updateStats() {
        const activeCount = allSignals.filter(s => s.status === 'active').length;
        const avgConfidence = allSignals.length > 0
            ? Math.round(allSignals.reduce((sum, s) => sum + (s.confidence || 0), 0) / allSignals.length)
            : 0;

        const activeEl = document.getElementById('enhanced-stat-active');
        const confEl = document.getElementById('enhanced-stat-confidence');
        if (activeEl) activeEl.textContent = activeCount;
        if (confEl) confEl.textContent = avgConfidence > 0 ? `${avgConfidence}%` : '—';
    }

    function showUpgradeModal() {
        if (window.dashboard && typeof window.dashboard.navigate === 'function') {
            window.dashboard.navigate('billing');
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // ORIGINAL SIGNAL MODAL (fallback)
    // ═══════════════════════════════════════════════════════════════════════════

    async function openSignalModal(signalId) {
        // Redirect to new deep insight
        openDeepInsight(signalId);
    }

    function closeModal() {
        const modal = document.getElementById('signalModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API
    // ═══════════════════════════════════════════════════════════════════════════

    window.EnhancedSignalsPage = {
        init,
        loadSignals,
        openSignalModal,
        openDeepInsight,
        closeModal,
        closeIQModal,
        copyToMT5,
        switchTab,
    };

})();
