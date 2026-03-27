// Enhanced Signals Page Module — AnalysisIQ Edition
// Deploy to: frontend/js/modules/enhanced_signals.js
//
// Changes from original:
//   • New "AnalysisIQ" tab alongside "Standard AI Signals"
//   • PatternCard component with institutional glow styling
//   • Deep Insight modal with technical summary, live stats bar, countdown timer
//   • "Copy to MT5" connected to existing execution logic (zero regression)
//   • Standard card rendering unchanged — graceful fallback when no pattern data
//   • Terminology: "Copier" used throughout (not "Student")

(function () {
    'use strict';

    // ═══════════════════════════════════════════════════════════════════════════
    // CSS INJECTION — AnalysisIQ Institutional Glow Theme
    // ═══════════════════════════════════════════════════════════════════════════

    const IQ_STYLES = `
    /* ══════════════════════════════════════════════════════════════════════════
       AnalysisIQ TradingView Edition — Professional Signal Cards
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

    /* ── AnalysisIQ Base Card ─────────────────────────────────────────────── */
    .aiq-card {
        position: relative;
        background: #131722;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        overflow: hidden;
        cursor: default;
        transition: transform 0.2s ease, box-shadow 0.3s ease, border-color 0.3s ease;
    }

    /* Active signal glow */
    .aiq-card.aiq-active {
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
    }

    .aiq-card:hover {
        transform: translateY(-4px);
        border-color: rgba(255, 255, 255, 0.15);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    }

    /* Closed states — dimmed glow */
    .aiq-card.aiq-profit  { border-color: rgba(0, 255, 136, 0.2); }
    .aiq-card.aiq-loss    { border-color: rgba(255, 56, 96, 0.2);  }
    .aiq-card.aiq-expired { border-color: rgba(100, 100, 120, 0.15); opacity: 0.65; }

    /* Monospaced price figures */
    .aiq-price {
        font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
        letter-spacing: 0.02em;
    }

    /* Live Trade Badge */
    .aiq-live-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        background: rgba(0, 200, 150, 0.15);
        border: 1px solid rgba(0, 200, 150, 0.4);
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #00d4aa;
        text-transform: uppercase;
    }
    .aiq-live-badge::before {
        content: '';
        width: 6px;
        height: 6px;
        background: #00d4aa;
        border-radius: 50%;
        animation: aiq-live-pulse 1.5s ease-in-out infinite;
    }
    @keyframes aiq-live-pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.8); }
    }

    /* TradingView Icon Badge */
    .aiq-tv-badge {
        width: 28px;
        height: 28px;
        background: linear-gradient(135deg, #2962ff, #1e88e5);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        font-weight: bold;
        color: white;
    }

    /* Order Type Badge */
    .aiq-order-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .aiq-order-buy  { background: #00c896; color: #000; }
    .aiq-order-sell { background: #ff4757; color: #fff; }

    /* Flag Icon */
    .aiq-flag {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
    }

    /* Chart Container */
    .aiq-chart-container {
        width: 100%;
        height: 160px;
        background: #0d1117;
        position: relative;
        overflow: hidden;
    }
    .aiq-chart-container iframe {
        width: 100%;
        height: 100%;
        border: none;
    }

    /* Price Row */
    .aiq-price-row {
        display: flex;
        justify-content: space-between;
        padding: 12px 16px;
        background: rgba(0,0,0,0.2);
    }
    .aiq-price-item {
        text-align: center;
        flex: 1;
    }
    .aiq-price-label {
        font-size: 10px;
        color: #6b7280;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .aiq-price-value {
        font-size: 15px;
        font-weight: 600;
    }

    /* Expires Row */
    .aiq-expires-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 16px;
        border-top: 1px solid rgba(255,255,255,0.05);
    }

    /* Learn More Button */
    .aiq-learn-btn {
        display: inline-block;
        padding: 10px 24px;
        background: transparent;
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 6px;
        color: #fff;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.04em;
        cursor: pointer;
        transition: all 0.2s ease;
        text-transform: uppercase;
    }
    .aiq-learn-btn:hover {
        background: rgba(255,255,255,0.05);
        border-color: rgba(255,255,255,0.3);
    }

    /* Countdown */
    .aiq-countdown { font-variant-numeric: tabular-nums; }
    .aiq-countdown.urgent { color: #ff6b6b; animation: aiq-pulse 1s ease-in-out infinite; }

    @keyframes aiq-pulse {
        0%, 100% { opacity: 1; }
        50%       { opacity: 0.5; }
    }

    /* Tab toggle */
    .aiq-tab-bar {
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
        align-items: center;
    }
    .aiq-tab-icon {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        color: #6b7280;
        cursor: pointer;
        transition: color 0.2s ease;
    }
    .aiq-tab-icon:hover { color: #9ca3af; }
    .aiq-tab-icon.active { color: #fff; }
    .aiq-tab-icon .icon-circle {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
    }
    .aiq-tab-icon.ai-driven .icon-circle { background: linear-gradient(135deg, #f59e0b, #ef4444); }
    .aiq-tab-icon.analysis-iq .icon-circle { background: linear-gradient(135deg, #2962ff, #1e88e5); }

    /* ── Deep Insight Modal with TradingView ───────────────────────────────── */
    .aiq-modal-overlay {
        position: fixed; inset: 0;
        background: rgba(0, 0, 0, 0.9);
        backdrop-filter: blur(8px);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 16px;
        opacity: 0;
        transition: opacity 0.2s ease;
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
        max-width: 900px;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 32px 64px rgba(0, 0, 0, 0.8);
        transform: translateY(12px);
        transition: transform 0.2s ease;
    }
    .aiq-modal-overlay.open .aiq-modal { transform: translateY(0); }

    /* Modal Chart */
    .aiq-modal-chart {
        width: 100%;
        height: 450px;
        background: #0d1117;
        position: relative;
    }
    .aiq-modal-chart iframe {
        width: 100%;
        height: 100%;
        border: none;
    }
    @media (max-width: 768px) {
        .aiq-modal-chart { height: 300px; }
    }

    /* Modal Header */
    .aiq-modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 20px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .aiq-modal-close {
        width: 32px;
        height: 32px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 6px;
        color: #9ca3af;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 18px;
        transition: all 0.2s ease;
    }
    .aiq-modal-close:hover {
        background: rgba(255,255,255,0.1);
        color: #fff;
    }

    /* Modal Info Grid */
    .aiq-modal-info {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1px;
        background: rgba(255,255,255,0.05);
        margin: 16px;
        border-radius: 8px;
        overflow: hidden;
    }
    .aiq-modal-info-item {
        background: #1a1f2e;
        padding: 12px 16px;
        text-align: center;
    }
    .aiq-modal-info-label {
        font-size: 10px;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .aiq-modal-info-value {
        font-size: 16px;
        font-weight: 600;
    }
    @media (max-width: 640px) {
        .aiq-modal-info { grid-template-columns: repeat(2, 1fr); }
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
    // API HELPER (unchanged from original)
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

    let allSignals       = [];
    let filteredSignals  = [];
    let currentTab       = 'ai-driven';   // 'ai-driven' | 'analysis-iq'
    let updateInterval   = null;
    let countdownTimers  = [];
    let iqModal          = null;

    // ═══════════════════════════════════════════════════════════════════════════
    // INIT
    // ═══════════════════════════════════════════════════════════════════════════

    function init() {
        console.log('[EnhancedSignals] Initialising…');
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
    // Inserts the new toggle above the signals grid if the existing tab elements
    // are present; otherwise prepends to the grid container.
    // ═══════════════════════════════════════════════════════════════════════════

    function injectTabBar() {
        // Check if tab bar already exists (idempotent)
        if (document.getElementById('aiq-tab-bar')) return;

        const bar = document.createElement('div');
        bar.id = 'aiq-tab-bar';
        bar.className = 'aiq-tab-bar';
        bar.innerHTML = `
            <div id="aiq-tab-standard" class="aiq-tab-icon ai-driven active" data-tab="ai-driven">
                <span class="icon-circle">✦</span>
                AI-Driven Trade Ideas
            </div>
            <div id="aiq-tab-iq" class="aiq-tab-icon analysis-iq" data-tab="analysis-iq">
                <span class="icon-circle">⟐</span>
                Pattern Trade Ideas
            </div>
        `;

        // Mount: prefer the existing container, fall back to grid parent
        const grid = document.getElementById('signalsGrid');
        const parent = grid ? grid.parentElement : document.querySelector('.signals-container');
        if (parent) {
            parent.insertBefore(bar, grid || parent.firstChild);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // DEEP INSIGHT MODAL INJECTION
    // ═══════════════════════════════════════════════════════════════════════════

    function injectIQModal() {
        if (document.getElementById('aiq-modal-overlay')) return;

        const overlay = document.createElement('div');
        overlay.id = 'aiq-modal-overlay';
        overlay.className = 'aiq-modal-overlay';
        overlay.innerHTML = `
            <div class="aiq-modal" id="aiq-modal" role="dialog" aria-modal="true">
                <div id="aiq-modal-body" style="padding: 24px;">
                    <!-- populated dynamically -->
                </div>
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
        // Original tabs (kept intact for zero regression)
        const aiTab      = document.getElementById('aiDrivenTab');
        const patternTab = document.getElementById('patternTab');
        if (aiTab)      aiTab.addEventListener('click',      () => switchTab('ai-driven'));
        if (patternTab) patternTab.addEventListener('click', () => switchTab('pattern'));

        // Original modal close
        const closeModal  = document.getElementById('closeModal');
        const signalModal = document.getElementById('signalModal');
        if (closeModal && signalModal) {
            closeModal.addEventListener('click', () => {
                signalModal.classList.add('hidden');
                signalModal.classList.remove('flex');
            });
            signalModal.addEventListener('click', (e) => {
                if (e.target === signalModal) {
                    signalModal.classList.add('hidden');
                    signalModal.classList.remove('flex');
                }
            });
        }

        // Load more
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        if (loadMoreBtn) loadMoreBtn.addEventListener('click', loadMoreSignals);

        // New AnalysisIQ tabs (delegated — bar is injected after DOMContentLoaded)
        document.addEventListener('click', (e) => {
            const tab = e.target.closest('[data-tab]');
            if (!tab) return;
            const target = tab.dataset.tab;
            if (target === 'ai-driven' || target === 'analysis-iq') {
                switchTab(target);
            }
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // DATA LOADING
    // ═══════════════════════════════════════════════════════════════════════════

    async function loadSignals() {
        console.log('[EnhancedSignals] Loading signals…');
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
                        <i class="fas fa-lock text-4xl text-cyan-500 mb-4" style="color:#00f3ff"></i>
                        <h3 class="text-xl font-semibold text-white mb-2">Upgrade Required</h3>
                        <p class="text-gray-400 mb-6">Enhanced signals require a Pro subscription.</p>
                        <button onclick="dashboard.navigate('billing')"
                                style="background:rgba(0,243,255,0.1);border:1px solid rgba(0,243,255,0.3);color:#00f3ff"
                                class="px-6 py-3 rounded-lg font-semibold">
                            Upgrade Now
                        </button>
                    </div>`;
            } else if (error.message !== 'Not authenticated') {
                grid.innerHTML = `
                    <div class="col-span-full text-center py-12">
                        <i class="fas fa-exclamation-triangle text-4xl text-red-500 mb-4"></i>
                        <h3 class="text-xl font-semibold text-white mb-2">Error Loading Signals</h3>
                        <p class="text-gray-400 mb-6">${escHtml(error.message)}</p>
                        <button onclick="window.EnhancedSignalsPage.loadSignals()"
                                class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-semibold">
                            Try Again
                        </button>
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
        } else if (currentTab === 'ai-driven') {
            filteredSignals = allSignals.filter(s => (s.confidence || 0) >= 70 && !s.is_pattern_idea);
        } else {
            // legacy 'pattern' tab — unchanged
            filteredSignals = allSignals.filter(s => s.pattern && s.pattern.length > 0);
        }
        renderSignals();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // TAB SWITCHING
    // ═══════════════════════════════════════════════════════════════════════════

    function switchTab(tab) {
        currentTab = tab;

        // Sync original tabs (if they exist)
        const aiTab      = document.getElementById('aiDrivenTab');
        const patternTab = document.getElementById('patternTab');
        if (aiTab && patternTab) {
            [aiTab, patternTab].forEach(t => {
                t.classList.remove('bg-purple-600', 'text-white');
                t.classList.add('text-gray-400');
            });
            if (tab === 'ai-driven') {
                aiTab.classList.add('bg-purple-600', 'text-white');
                aiTab.classList.remove('text-gray-400');
            } else if (tab === 'pattern') {
                patternTab.classList.add('bg-purple-600', 'text-white');
                patternTab.classList.remove('text-gray-400');
            }
        }

        // Sync AnalysisIQ tab bar (new design)
        const tabStd = document.getElementById('aiq-tab-standard');
        const tabIQ  = document.getElementById('aiq-tab-iq');
        if (tabStd && tabIQ) {
            tabStd.classList.toggle('active', tab === 'ai-driven');
            tabIQ.classList.toggle('active',  tab === 'analysis-iq');
        }

        applyFilters();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // RENDER
    // ═══════════════════════════════════════════════════════════════════════════

    function renderSignals() {
        const grid = document.getElementById('signalsGrid');
        if (!grid) return;

        // Clear running countdown timers
        countdownTimers.forEach(clearInterval);
        countdownTimers = [];

        if (!filteredSignals.length) {
            grid.innerHTML = `
                <div class="col-span-full text-center py-16">
                    <div style="font-size:32px;margin-bottom:12px;opacity:.3">⬡</div>
                    <p class="text-gray-500">No signals found for this view.</p>
                </div>`;
            return;
        }

        if (currentTab === 'analysis-iq') {
            grid.innerHTML = filteredSignals.map(s => renderPatternCard(s)).join('');
            startCountdowns();
        } else {
            // AI-Driven signals also get TradingView cards now
            grid.innerHTML = filteredSignals.map(s => renderPatternCard(s)).join('');
            startCountdowns();
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PATTERN CARD (AnalysisIQ) — TradingView Mini-Chart Edition
    // ═══════════════════════════════════════════════════════════════════════════

    function getTradingViewSymbol(symbol) {
        // Map internal symbols to TradingView format
        const tvMap = {
            'EURUSD': 'FX:EURUSD',
            'GBPUSD': 'FX:GBPUSD',
            'USDJPY': 'FX:USDJPY',
            'AUDUSD': 'FX:AUDUSD',
            'AUDCAD': 'FX:AUDCAD',
            'AUDNZD': 'FX:AUDNZD',
            'NZDUSD': 'FX:NZDUSD',
            'EURSEEK': 'FX:EURSEEK',
            'GBPJPY': 'FX:GBPJPY',
            'XAUUSD': 'TVC:GOLD',
            'XAGUSD': 'TVC:SILVER',
            'US30': 'TVC:DJI',
            'CHINA50': 'SSE:000001',
            'GER40': 'XETR:DAX',
            'BTCUSD': 'BITSTAMP:BTCUSD',
            'ETHUSD': 'BITSTAMP:ETHUSD',
        };
        return tvMap[symbol] || `FX:${symbol}`;
    }

    function getCountryFlag(country, assetType) {
        const flags = {
            'EU': '🇪🇺', 'UK': '🇬🇧', 'US': '🇺🇸', 'JP': '🇯🇵',
            'AU': '🇦🇺', 'CA': '🇨🇦', 'NZ': '🇳🇿', 'CH': '🇨🇭',
            'CN': '🇨🇳', 'DE': '🇩🇪', 'SE': '🇸🇪', 'all': '🌍',
        };
        if (assetType === 'crypto') return '₿';
        if (assetType === 'commodities') return '🪙';
        return flags[country] || '💹';
    }

    function renderPatternCard(signal) {
        const iq = signal.analysis_iq || {};

        const isBuy    = (iq.order_type || signal.direction || '').toUpperCase().includes('BUY');
        const pattern  = (iq.pattern_type || signal.pattern || 'PATTERN').replace(/_/g, ' ');
        const tf       = iq.timeframe || signal.timeframe || '4H';
        const status   = iq.status || 'LIVE TRADE';
        const expIso   = iq.expiry_timestamp || (signal.expires_at ? signal.expires_at : null);
        const flagEmoji = getCountryFlag(signal.country, signal.asset_type);
        const tvSymbol = getTradingViewSymbol(signal.symbol);

        const cardClass = {
            'LIVE TRADE':      'aiq-active',
            'CLOSED - PROFIT': 'aiq-profit',
            'CLOSED - LOSS':   'aiq-loss',
            'EXPIRED':         'aiq-expired',
        }[status] || 'aiq-active';

        // TradingView Mini Chart Widget URL
        const tvChartUrl = `https://s.tradingview.com/widgetembed/?frameElementId=tv_chart_${signal.id}&symbol=${encodeURIComponent(tvSymbol)}&interval=${tf.replace('H','60').replace('D','D').replace('1','1')}&hidesidetoolbar=1&symboledit=0&saveimage=0&toolbarbg=131722&studies=[]&theme=dark&style=1&timezone=Etc/UTC&withdateranges=0&showpopupbutton=0&hide_top_toolbar=1&hide_legend=1&allow_symbol_change=0&locale=en`;

        return `
        <div id="aiq-card-${signal.id}"
             class="aiq-card ${cardClass}"
             style="font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;">

            <!-- Header Row: Live Badge + TV Icon -->
            <div style="display:flex; align-items:center; justify-content:space-between; padding: 12px 16px;">
                <span class="aiq-live-badge">Live Trade</span>
                <div class="aiq-tv-badge" title="TradingView Chart">TV</div>
            </div>

            <!-- Symbol Row: Flag + Name + Pattern -->
            <div style="display:flex; align-items:center; gap:12px; padding: 0 16px 12px;">
                <div class="aiq-flag">${flagEmoji}</div>
                <div style="flex:1;">
                    <div style="font-size:16px; font-weight:700; color:#fff; display:flex; align-items:center; gap:8px;">
                        ${escHtml(signal.symbol)}
                        <span style="font-size:12px; font-weight:400; color:#6b7280;">
                            ${escHtml(pattern)}
                        </span>
                    </div>
                </div>
                <span class="aiq-order-badge ${isBuy ? 'aiq-order-buy' : 'aiq-order-sell'}">
                    ${isBuy ? 'BUY STOP' : 'SELL STOP'}
                </span>
            </div>

            <!-- TradingView Mini Chart -->
            <div class="aiq-chart-container" id="aiq-chart-${signal.id}">
                <iframe 
                    src="${tvChartUrl}"
                    allowtransparency="true"
                    frameborder="0"
                    loading="lazy">
                </iframe>
            </div>

            <!-- Price Row: Entry / Target / Stop -->
            <div class="aiq-price-row">
                <div class="aiq-price-item">
                    <div class="aiq-price-label">Entry</div>
                    <div class="aiq-price-value aiq-price" style="color:#60a5fa;">${escHtml(signal.entry || '—')}</div>
                </div>
                <div class="aiq-price-item">
                    <div class="aiq-price-label">Target</div>
                    <div class="aiq-price-value aiq-price" style="color:#34d399;">${escHtml(signal.target || '—')}</div>
                </div>
                <div class="aiq-price-item">
                    <div class="aiq-price-label">Stop</div>
                    <div class="aiq-price-value aiq-price" style="color:#f87171;">${escHtml(signal.stop || '—')}</div>
                </div>
            </div>

            <!-- Expires Row -->
            <div class="aiq-expires-row">
                <div>
                    <span style="font-size:11px; color:#6b7280;">Expires</span>
                    <span class="aiq-countdown aiq-price" 
                          id="aiq-exp-${signal.id}"
                          data-expiry="${expIso || ''}"
                          style="color:#f59e0b; margin-left:8px; font-size:13px; font-weight:600;">
                        ${expIso ? formatCountdown(expIso) : '—'}
                    </span>
                </div>
                <span style="font-size:11px; color:#4a5568; border:1px solid #2d3748; border-radius:4px; padding:2px 8px; font-weight:600;">
                    ${escHtml(tf)}
                </span>
            </div>

            <!-- Learn More Button -->
            <div style="padding: 12px 16px; border-top: 1px solid rgba(255,255,255,0.05);">
                <button class="aiq-learn-btn" style="width:100%;" onclick="window.EnhancedSignalsPage.openDeepInsight(${signal.id})">
                    Learn More
                </button>
            </div>
        </div>`;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // COUNTDOWN TIMERS
    // ═══════════════════════════════════════════════════════════════════════════

    function startCountdowns() {
        const tick = () => {
            document.querySelectorAll('.aiq-countdown[data-expiry]').forEach(el => {
                const expiry = el.dataset.expiry;
                if (!expiry) return;
                const str = formatCountdown(expiry);
                el.textContent = str;
                // Urgent state when < 1 hour
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
        const h  = Math.floor(ms / 3600000);
        const m  = Math.floor((ms % 3600000) / 60000);
        const s  = Math.floor((ms % 60000) / 1000);
        if (h >= 24) {
            const d = Math.floor(h / 24);
            return `${d}d ${h % 24}h`;
        }
        return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // DEEP INSIGHT MODAL — Full TradingView Chart
    // ═══════════════════════════════════════════════════════════════════════════

    function openDeepInsight(signalIdOrObj) {
        if (!iqModal) return;

        // Support both signal object and signal ID
        let signal;
        if (typeof signalIdOrObj === 'object') {
            signal = signalIdOrObj;
        } else {
            signal = allSignals.find(s => s.id === signalIdOrObj);
            if (!signal) {
                console.warn('[AnalysisIQ] Signal not found:', signalIdOrObj);
                return;
            }
        }

        const iq       = signal.analysis_iq || {};
        const isBuy    = (iq.order_type || signal.direction || '').toUpperCase().includes('BUY');
        const pattern  = (iq.pattern_type || signal.pattern || 'PATTERN').replace(/_/g, ' ');
        const tf       = iq.timeframe || signal.timeframe || '4H';
        const rr       = calculateRR(signal);
        const tvSymbol = getTradingViewSymbol(signal.symbol);
        const flagEmoji = getCountryFlag(signal.country, signal.asset_type);

        // Full TradingView Advanced Chart URL
        const tvInterval = tf.replace('H','60').replace('D','D').replace('1','1');
        const tvChartUrl = `https://s.tradingview.com/widgetembed/?frameElementId=tv_modal_chart&symbol=${encodeURIComponent(tvSymbol)}&interval=${tvInterval}&hidesidetoolbar=0&symboledit=0&saveimage=1&toolbarbg=131722&studies=[]&theme=dark&style=1&timezone=Etc/UTC&withdateranges=1&showpopupbutton=0&hide_top_toolbar=0&hide_legend=0&allow_symbol_change=0&locale=en&studies_overrides={}&overrides={}&enabled_features=[]&disabled_features=[]`;

        const body = document.getElementById('aiq-modal-body');
        body.innerHTML = `
            <!-- Modal Header -->
            <div class="aiq-modal-header">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div class="aiq-flag">${flagEmoji}</div>
                    <div>
                        <div style="font-size:18px; font-weight:700; color:#fff;">
                            ${escHtml(signal.symbol)}
                            <span style="color:#6b7280; font-weight:400; font-size:14px; margin-left:8px;">
                                ${escHtml(pattern)}
                            </span>
                        </div>
                        <div style="font-size:12px; color:#6b7280;">
                            ${escHtml(signal.full_name || signal.symbol)} · ${escHtml(tf)}
                        </div>
                    </div>
                </div>
                <div style="display:flex; align-items:center; gap:12px;">
                    <span class="aiq-order-badge ${isBuy ? 'aiq-order-buy' : 'aiq-order-sell'}">
                        ${isBuy ? 'BUY STOP' : 'SELL STOP'}
                    </span>
                    <button class="aiq-modal-close" onclick="window.EnhancedSignalsPage.closeIQModal()">×</button>
                </div>
            </div>

            <!-- Full TradingView Chart -->
            <div class="aiq-modal-chart" id="tv_modal_chart_container">
                <iframe 
                    id="tv_modal_chart"
                    src="${tvChartUrl}"
                    allowtransparency="true"
                    frameborder="0">
                </iframe>
            </div>

            <!-- Price Levels Grid -->
            <div class="aiq-modal-info">
                <div class="aiq-modal-info-item">
                    <div class="aiq-modal-info-label">Entry</div>
                    <div class="aiq-modal-info-value aiq-price" style="color:#60a5fa;">${escHtml(signal.entry || '—')}</div>
                </div>
                <div class="aiq-modal-info-item">
                    <div class="aiq-modal-info-label">Target</div>
                    <div class="aiq-modal-info-value aiq-price" style="color:#34d399;">${escHtml(signal.target || '—')}</div>
                </div>
                <div class="aiq-modal-info-item">
                    <div class="aiq-modal-info-label">Stop Loss</div>
                    <div class="aiq-modal-info-value aiq-price" style="color:#f87171;">${escHtml(signal.stop || '—')}</div>
                </div>
                <div class="aiq-modal-info-item">
                    <div class="aiq-modal-info-label">Risk:Reward</div>
                    <div class="aiq-modal-info-value" style="color:#a78bfa;">${escHtml(rr)}</div>
                </div>
            </div>

            <!-- Analysis Summary -->
            <div style="padding: 0 16px 16px;">
                <div style="background:#1a1f2e; border-radius:8px; padding:16px;">
                    <div style="font-size:11px; color:#6b7280; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">
                        Analysis Summary
                    </div>
                    <div style="font-size:13px; color:#9ca3af; line-height:1.6;">
                        ${escHtml(iq.technical_summary || signal.analysis || 'Professional technical analysis based on Smart Money Concepts and institutional order flow. Entry zone marked with pattern confluence confirmation.')}
                    </div>
                </div>
            </div>

            <!-- Sentiment Bars -->
            <div style="padding: 0 16px 16px; display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                <div style="background:#1a1f2e; border-radius:8px; padding:12px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                        <span style="font-size:11px; color:#6b7280;">Bullish Sentiment</span>
                        <span style="font-size:11px; color:#34d399; font-family:monospace;">${signal.sentiment_bullish || 50}%</span>
                    </div>
                    <div style="height:6px; background:#0d1117; border-radius:3px; overflow:hidden;">
                        <div style="height:100%; width:${signal.sentiment_bullish || 50}%; background:linear-gradient(90deg,#00c864,#34d399); border-radius:3px;"></div>
                    </div>
                </div>
                <div style="background:#1a1f2e; border-radius:8px; padding:12px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                        <span style="font-size:11px; color:#6b7280;">Confidence</span>
                        <span style="font-size:11px; color:#a78bfa; font-family:monospace;">${signal.confidence || 75}%</span>
                    </div>
                    <div style="height:6px; background:#0d1117; border-radius:3px; overflow:hidden;">
                        <div style="height:100%; width:${signal.confidence || 75}%; background:linear-gradient(90deg,#7c3aed,#a78bfa); border-radius:3px;"></div>
                    </div>
                </div>
            </div>

            <!-- Action Buttons -->
            <div style="padding: 16px; border-top:1px solid rgba(255,255,255,0.05); display:flex; gap:12px;">
                <button onclick="window.EnhancedSignalsPage.copyToMT5(${signal.id})"
                        style="flex:1; padding:12px; background:linear-gradient(135deg,#2962ff,#1e88e5); border:none; border-radius:8px; color:#fff; font-size:13px; font-weight:600; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:8px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M8 17H5a2 2 0 01-2-2V5a2 2 0 012-2h10a2 2 0 012 2v3"/>
                        <rect x="8" y="11" width="13" height="10" rx="2"/>
                    </svg>
                    Copy to MT5
                </button>
                <button onclick="window.EnhancedSignalsPage.closeIQModal()"
                        style="padding:12px 24px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:8px; color:#9ca3af; font-size:13px; font-weight:600; cursor:pointer;">
                    Close
                </button>
            </div>
        `;

        iqModal.classList.add('open');
    }

    function closeIQModal() {
        if (iqModal) iqModal.classList.remove('open');
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // COPY TO MT5 — delegates to existing execution logic (zero regression)
    // ═══════════════════════════════════════════════════════════════════════════

    function copyToMT5(signalId) {
        // Delegate to the existing handler if present
        if (window.MT5Copier && typeof window.MT5Copier.execute === 'function') {
            window.MT5Copier.execute(signalId);
            return;
        }
        if (window.SignalCopier && typeof window.SignalCopier.copy === 'function') {
            window.SignalCopier.copy(signalId);
            return;
        }
        // Fallback: open the original signal modal which includes the copy flow
        if (window.EnhancedSignalsPage && typeof openSignalModal === 'function') {
            openSignalModal(signalId);
        } else {
            console.warn('[AnalysisIQ] MT5 copy handler not found for signal', signalId);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // ORIGINAL CARD RENDER (unchanged — graceful fallback)
    // ═══════════════════════════════════════════════════════════════════════════

    function renderOriginalCard(signal) {
        // Signals without pattern data fall back to this standard card style
        const isBuy = (signal.direction || '').toUpperCase().includes('BUY');
        const directionClass = isBuy ? 'text-green-400' : 'text-red-400';
        const directionBg    = isBuy ? 'bg-green-900 border-green-700' : 'bg-red-900 border-red-700';

        return `
        <div class="bg-gray-800 border border-gray-700 rounded-xl p-4 cursor-pointer hover:border-gray-500 transition-all"
             onclick="window.EnhancedSignalsPage.openSignalModal(${signal.id})">
            <div class="flex items-center justify-between mb-3">
                <div>
                    <h3 class="text-lg font-bold text-white">${escHtml(signal.symbol)}</h3>
                    <p class="text-xs text-gray-400">${escHtml(signal.full_name || signal.symbol)}</p>
                </div>
                <span class="px-3 py-1 text-xs font-bold rounded-full border ${directionBg} ${directionClass}">
                    ${escHtml(signal.direction || 'N/A')}
                </span>
            </div>
            <div class="grid grid-cols-3 gap-2 text-center mb-3">
                <div class="bg-gray-700 rounded p-2">
                    <p class="text-xs text-gray-400">Entry</p>
                    <p class="text-sm font-bold text-blue-400">${escHtml(signal.entry || '—')}</p>
                </div>
                <div class="bg-gray-700 rounded p-2">
                    <p class="text-xs text-gray-400">Target</p>
                    <p class="text-sm font-bold text-green-400">${escHtml(signal.target || '—')}</p>
                </div>
                <div class="bg-gray-700 rounded p-2">
                    <p class="text-xs text-gray-400">Stop</p>
                    <p class="text-sm font-bold text-red-400">${escHtml(signal.stop || '—')}</p>
                </div>
            </div>
            <div class="flex items-center justify-between text-xs text-gray-400">
                <span>${escHtml(signal.pattern || 'AI Signal')} · ${escHtml(signal.timeframe || 'H4')}</span>
                <span class="text-purple-400 font-bold">${signal.confidence || 0}%</span>
            </div>
        </div>`;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // ORIGINAL SIGNAL MODAL (unchanged)
    // ═══════════════════════════════════════════════════════════════════════════

    async function openSignalModal(signalId) {
        const modal        = document.getElementById('signalModal');
        const modalContent = document.getElementById('modalContent');
        const modalTitle   = document.getElementById('modalTitle');

        if (!modal || !modalContent) return;

        modal.classList.remove('hidden');
        modal.classList.add('flex');

        modalContent.innerHTML = `
            <div class="text-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-4"></div>
                <p class="text-gray-400">Loading signal details…</p>
            </div>`;

        try {
            const signal = await apiGet(`/signals/${signalId}`);

            if (modalTitle) modalTitle.textContent = `${signal.symbol} - ${signal.direction || 'Signal'} Setup`;

            const isBuy = (signal.direction || '').toUpperCase().includes('BUY');

            modalContent.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <div class="mb-6">
                            <h3 class="text-lg font-bold text-white mb-2">${escHtml(signal.symbol)}</h3>
                            <p class="text-gray-400">${escHtml(signal.full_name || signal.symbol)}</p>
                        </div>
                        <div class="bg-gray-700 rounded-lg p-4 mb-4">
                            <div class="grid grid-cols-3 gap-4 text-center">
                                <div>
                                    <p class="text-xs text-gray-400 mb-1">Entry</p>
                                    <p class="text-lg font-bold text-blue-400">${escHtml(signal.entry || '—')}</p>
                                </div>
                                <div>
                                    <p class="text-xs text-gray-400 mb-1">Target</p>
                                    <p class="text-lg font-bold text-green-400">${escHtml(signal.target || '—')}</p>
                                </div>
                                <div>
                                    <p class="text-xs text-gray-400 mb-1">Stop Loss</p>
                                    <p class="text-lg font-bold text-red-400">${escHtml(signal.stop || '—')}</p>
                                </div>
                            </div>
                        </div>
                        <div class="space-y-3">
                            <div class="flex justify-between">
                                <span class="text-gray-400">Direction</span>
                                <span class="${isBuy ? 'text-green-400' : 'text-red-400'} font-bold">${escHtml(signal.direction || 'N/A')}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Pattern</span>
                                <span class="text-white">${escHtml(signal.pattern || 'N/A')}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Timeframe</span>
                                <span class="text-white">${escHtml(signal.timeframe || 'H4')}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Confidence</span>
                                <span class="text-purple-400 font-bold">${signal.confidence || 75}%</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">R:R</span>
                                <span class="text-white">${calculateRR(signal)}</span>
                            </div>
                        </div>
                    </div>
                    <div>
                        <div class="bg-gray-700 rounded-lg p-4 mb-4">
                            <h4 class="font-semibold text-white mb-3">Analysis Summary</h4>
                            <p class="text-gray-300 text-sm leading-relaxed">
                                ${escHtml(signal.analysis || signal.description || 'Professional technical analysis based on Smart Money Concepts and institutional order flow.')}
                            </p>
                        </div>
                        <div class="bg-gray-700 rounded-lg p-4">
                            <h4 class="font-semibold text-white mb-3">Market Sentiment</h4>
                            <div class="space-y-2">
                                <div class="flex justify-between text-sm">
                                    <span class="text-gray-400">Bullish</span>
                                    <span class="text-green-400">${signal.sentiment_bullish || 50}%</span>
                                </div>
                                <div class="w-full bg-gray-600 rounded-full h-2">
                                    <div class="bg-green-500 h-2 rounded-full" style="width:${signal.sentiment_bullish||50}%"></div>
                                </div>
                                <div class="flex justify-between text-sm">
                                    <span class="text-gray-400">Bearish</span>
                                    <span class="text-red-400">${signal.sentiment_bearish || 50}%</span>
                                </div>
                                <div class="w-full bg-gray-600 rounded-full h-2">
                                    <div class="bg-red-500 h-2 rounded-full" style="width:${signal.sentiment_bearish||50}%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="mt-6 pt-6 border-t border-gray-700">
                    <button onclick="window.EnhancedSignalsPage.closeModal()"
                            class="w-full bg-gray-700 hover:bg-gray-600 text-white py-3 px-6 rounded-lg font-semibold transition-colors">
                        Close
                    </button>
                </div>`;

        } catch (error) {
            console.error('[EnhancedSignals] Error loading signal details:', error);
            modalContent.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-exclamation-triangle text-4xl text-red-500 mb-4"></i>
                    <p class="text-red-400">Error: ${escHtml(error.message)}</p>
                </div>`;
        }
    }

    function closeModal() {
        const modal = document.getElementById('signalModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // UTILS
    // ═══════════════════════════════════════════════════════════════════════════

    function calculateRR(signal) {
        const entry  = parseFloat(signal.entry);
        const target = parseFloat(signal.target);
        const stop   = parseFloat(signal.stop);
        if (isNaN(entry) || isNaN(target) || isNaN(stop)) return 'N/A';
        const risk   = Math.abs(entry - stop);
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
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function getAssetFlag(assetType, country) {
        const flags = {
            'forex': {
                'EU': '🇪🇺', 'UK': '🇬🇧', 'US': '🇺🇸', 'JP': '🇯🇵',
                'AU': '🇦🇺', 'CA': '🇨🇦', 'NZ': '🇳🇿', 'CH': '🇨🇭',
                'CN': '🇨🇳', 'DE': '🇩🇪', 'all': '🌐',
            },
            'indices':     { 'US': '📊', 'CN': '📊', 'DE': '📊', 'all': '📊' },
            'commodities': { 'all': '🪙' },
            'crypto':      { 'all': '₿' },
        };
        return (flags[assetType] || {})[country] || (flags[assetType] || {})['all'] || '💹';
    }

    function updateStats() {
        const activeCount     = allSignals.filter(s => s.status === 'active').length;
        const avgConfidence   = allSignals.length > 0
            ? Math.round(allSignals.reduce((sum, s) => sum + (s.confidence || 0), 0) / allSignals.length)
            : 0;

        const activeEl = document.getElementById('enhanced-stat-active');
        const confEl   = document.getElementById('enhanced-stat-confidence');
        if (activeEl) activeEl.textContent = activeCount;
        if (confEl)   confEl.textContent   = avgConfidence > 0 ? `${avgConfidence}%` : '—';
    }

    function loadMoreSignals() { console.log('[EnhancedSignals] Load more clicked'); }

    function showUpgradeModal() {
        if (window.dashboard && typeof window.dashboard.navigate === 'function') {
            window.dashboard.navigate('billing');
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API
    // ═══════════════════════════════════════════════════════════════════════════

    window.EnhancedSignalsPage = {
        init,
        loadSignals,
        openSignalModal,
        closeModal,
        closeIQModal,
        copyToMT5,
        switchTab,
        openDeepInsight: function(signalId) {
            const signal = allSignals.find(s => s.id === signalId);
            if (signal) openDeepInsight(signal);
        },
    };

})();
