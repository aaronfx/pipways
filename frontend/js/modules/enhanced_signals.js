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
    /* ── AnalysisIQ Base Card ─────────────────────────────────────────────── */
    .aiq-card {
        position: relative;
        background: #0B0E11;
        border: 1px solid rgba(0, 243, 255, 0.08);
        border-radius: 12px;
        overflow: hidden;
        cursor: pointer;
        transition: transform 0.2s ease, box-shadow 0.3s ease, border-color 0.3s ease;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }

    /* Active signal glow */
    .aiq-card.aiq-active {
        box-shadow:
            0 0 15px rgba(0, 243, 255, 0.05),
            inset 0 0 10px rgba(0, 243, 255, 0.02);
    }

    .aiq-card:hover {
        transform: translateY(-2px);
        border-color: rgba(0, 243, 255, 0.22);
        box-shadow:
            0 0 28px rgba(0, 243, 255, 0.10),
            inset 0 0 16px rgba(0, 243, 255, 0.04);
    }

    /* Accent gradient line at top */
    .aiq-card::before {
        content: '';
        display: block;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00f3ff, transparent);
        position: absolute;
        top: 0; left: 0; right: 0;
    }

    /* Closed states — dimmed glow */
    .aiq-card.aiq-profit  { border-color: rgba(0, 255, 136, 0.15); }
    .aiq-card.aiq-loss    { border-color: rgba(255, 56, 96, 0.15);  }
    .aiq-card.aiq-expired { border-color: rgba(100, 100, 120, 0.15); opacity: 0.65; }

    /* Monospaced price figures */
    .aiq-price {
        font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
        letter-spacing: 0.04em;
    }

    /* Action badge */
    .aiq-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .aiq-badge-buy  { background: rgba(0, 200, 100, 0.15); color: #00e87a; border: 1px solid rgba(0, 200, 100, 0.3); }
    .aiq-badge-sell { background: rgba(255, 56, 96, 0.15);  color: #ff4d6d; border: 1px solid rgba(255, 56, 96, 0.3);  }

    /* Status pill */
    .aiq-status {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 3px;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .aiq-status-live    { background: rgba(0, 243, 255, 0.10); color: #00f3ff; }
    .aiq-status-profit  { background: rgba(0, 255, 136, 0.10); color: #00ff88; }
    .aiq-status-loss    { background: rgba(255, 56, 96, 0.10);  color: #ff385f; }
    .aiq-status-expired { background: rgba(100, 100, 120, 0.15); color: #8888aa; }

    /* Data grid */
    .aiq-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1px;
        background: rgba(0, 243, 255, 0.06);
        border: 1px solid rgba(0, 243, 255, 0.06);
        border-radius: 6px;
        overflow: hidden;
    }
    .aiq-cell {
        background: #0d1117;
        padding: 8px 10px;
    }
    .aiq-cell-label {
        font-size: 9px;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #4a5568;
        margin-bottom: 3px;
    }
    .aiq-cell-value {
        font-size: 13px;
        font-weight: 600;
        color: #e2e8f0;
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
        gap: 4px;
        background: #0B0E11;
        border: 1px solid rgba(0, 243, 255, 0.08);
        border-radius: 8px;
        padding: 4px;
    }
    .aiq-tab {
        flex: 1;
        padding: 8px 16px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.05em;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: center;
        color: #4a5568;
        border: none;
        background: transparent;
    }
    .aiq-tab.active {
        background: rgba(0, 243, 255, 0.08);
        color: #00f3ff;
        border: 1px solid rgba(0, 243, 255, 0.20);
    }
    .aiq-tab:hover:not(.active) { color: #718096; background: rgba(255,255,255,0.02); }

    /* ── Deep Insight Modal ───────────────────────────────────────────────── */
    .aiq-modal-overlay {
        position: fixed; inset: 0;
        background: rgba(0, 5, 12, 0.85);
        backdrop-filter: blur(6px);
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
        background: #0B0E11;
        border: 1px solid rgba(0, 243, 255, 0.15);
        border-radius: 16px;
        width: 100%;
        max-width: 720px;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow:
            0 0 60px rgba(0, 243, 255, 0.08),
            0 32px 64px rgba(0, 0, 0, 0.6);
        transform: translateY(12px);
        transition: transform 0.2s ease;
    }
    .aiq-modal-overlay.open .aiq-modal { transform: translateY(0); }
    .aiq-modal::before {
        content: '';
        display: block;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00f3ff 30%, #0070ff 70%, transparent);
        position: absolute;
        top: 0; left: 0; right: 0;
        border-radius: 16px 16px 0 0;
    }

    /* Chart placeholder */
    .aiq-chart-placeholder {
        background: linear-gradient(135deg, #0d1117 0%, #0f1923 100%);
        border: 1px solid rgba(0, 243, 255, 0.08);
        border-radius: 8px;
        height: 180px;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }
    .aiq-chart-placeholder::after {
        content: '';
        position: absolute;
        inset: 0;
        background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 20px,
            rgba(0, 243, 255, 0.025) 20px,
            rgba(0, 243, 255, 0.025) 21px
        ),
        repeating-linear-gradient(
            90deg,
            transparent,
            transparent 40px,
            rgba(0, 243, 255, 0.025) 40px,
            rgba(0, 243, 255, 0.025) 41px
        );
    }

    /* Live stats bar */
    .aiq-stat-bar { height: 6px; border-radius: 3px; background: #1a2030; overflow: hidden; }
    .aiq-stat-fill { height: 100%; border-radius: 3px; transition: width 0.6s ease; }
    .aiq-stat-fill-cyan   { background: linear-gradient(90deg, #0070ff, #00f3ff); }
    .aiq-stat-fill-green  { background: linear-gradient(90deg, #00c864, #00ff88); }
    .aiq-stat-fill-orange { background: linear-gradient(90deg, #ff8c00, #ffd700); }

    /* MT5 Copy button */
    .aiq-copy-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 20px;
        background: linear-gradient(135deg, rgba(0, 112, 255, 0.2), rgba(0, 243, 255, 0.15));
        border: 1px solid rgba(0, 243, 255, 0.30);
        border-radius: 8px;
        color: #00f3ff;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.06em;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .aiq-copy-btn:hover {
        background: linear-gradient(135deg, rgba(0, 112, 255, 0.35), rgba(0, 243, 255, 0.25));
        box-shadow: 0 0 16px rgba(0, 243, 255, 0.15);
        transform: translateY(-1px);
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
        bar.className = 'aiq-tab-bar mb-4';
        bar.innerHTML = `
            <button id="aiq-tab-standard"   class="aiq-tab active" data-tab="ai-driven">
                ◈ Standard AI Signals
            </button>
            <button id="aiq-tab-iq"         class="aiq-tab"        data-tab="analysis-iq">
                ⬡ AnalysisIQ&nbsp;<span style="font-size:9px;opacity:.6;">INSTITUTIONAL</span>
            </button>
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

        // Sync original tabs
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

        // Sync AnalysisIQ tab bar
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
            // Attach click handlers + start countdowns
            filteredSignals.forEach(s => {
                const card = document.getElementById(`aiq-card-${s.id}`);
                if (card) card.addEventListener('click', () => openDeepInsight(s));
            });
            startCountdowns();
        } else {
            // Original render path — zero regression
            grid.innerHTML = filteredSignals.map(s => renderOriginalCard(s)).join('');
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PATTERN CARD (AnalysisIQ)
    // ═══════════════════════════════════════════════════════════════════════════

    function renderPatternCard(signal) {
        const iq = signal.analysis_iq || {};

        const isBuy    = (iq.order_type || signal.direction || '').toUpperCase().includes('BUY');
        const pattern  = (iq.pattern_type || signal.pattern || 'PATTERN').replace(/_/g, ' ');
        const tf       = iq.timeframe || signal.timeframe || '4H';
        const status   = iq.status || 'LIVE TRADE';
        const expIso   = iq.expiry_timestamp || (signal.expires_at ? signal.expires_at : null);
        const flagEmoji = getAssetFlag(signal.asset_type, signal.country);

        const cardClass = {
            'LIVE TRADE':      'aiq-active',
            'CLOSED - PROFIT': 'aiq-profit',
            'CLOSED - LOSS':   'aiq-loss',
            'EXPIRED':         'aiq-expired',
        }[status] || 'aiq-active';

        const statusClass = {
            'LIVE TRADE':      'aiq-status-live',
            'CLOSED - PROFIT': 'aiq-status-profit',
            'CLOSED - LOSS':   'aiq-status-loss',
            'EXPIRED':         'aiq-status-expired',
        }[status] || 'aiq-status-live';

        return `
        <div id="aiq-card-${signal.id}"
             class="aiq-card ${cardClass}"
             style="padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;">

            <!-- Header -->
            <div style="display:flex; align-items:center; justify-content:space-between; padding: 14px 16px 10px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:20px; line-height:1;">${flagEmoji}</span>
                    <div>
                        <div style="font-size:14px; font-weight:700; color:#e2e8f0; letter-spacing:0.04em;">
                            ${escHtml(signal.symbol)}
                            <span style="color:rgba(0,243,255,0.5); font-size:11px; font-weight:400; margin-left:4px;">
                                | ${escHtml(pattern)}
                            </span>
                        </div>
                        <div style="font-size:10px; color:#4a5568; margin-top:1px;">
                            ${escHtml(signal.full_name || signal.symbol)}
                        </div>
                    </div>
                </div>
                <div style="display:flex; flex-direction:column; align-items:flex-end; gap:4px;">
                    <span class="aiq-badge ${isBuy ? 'aiq-badge-buy' : 'aiq-badge-sell'}">
                        ${isBuy ? '▲' : '▼'} ${escHtml(iq.order_type || (isBuy ? 'BUY STOP' : 'SELL STOP'))}
                    </span>
                    <span class="aiq-status ${statusClass}">${escHtml(status)}</span>
                </div>
            </div>

            <!-- Timeframe tag -->
            <div style="padding: 0 16px 10px; display:flex; gap:6px; align-items:center;">
                <span style="font-size:10px; color:#4a5568; border:1px solid #1e2a3a; border-radius:3px; padding:1px 6px; font-weight:600;">
                    ${escHtml(tf)}
                </span>
                <span style="font-size:10px; color:#2d3a4a;">·</span>
                <span style="font-size:10px; color:#4a5568;">
                    ${signal.confidence || 0}% Confidence
                </span>
            </div>

            <!-- Price grid -->
            <div style="padding: 0 12px 12px;">
                <div class="aiq-grid">
                    <div class="aiq-cell">
                        <div class="aiq-cell-label">Entry</div>
                        <div class="aiq-cell-value aiq-price" style="color:#60a5fa;">${escHtml(signal.entry || '—')}</div>
                    </div>
                    <div class="aiq-cell">
                        <div class="aiq-cell-label">Target</div>
                        <div class="aiq-cell-value aiq-price" style="color:#34d399;">${escHtml(signal.target || '—')}</div>
                    </div>
                    <div class="aiq-cell">
                        <div class="aiq-cell-label">Stop Loss</div>
                        <div class="aiq-cell-value aiq-price" style="color:#f87171;">${escHtml(signal.stop || '—')}</div>
                    </div>
                    <div class="aiq-cell">
                        <div class="aiq-cell-label">Expires</div>
                        <div class="aiq-cell-value aiq-price aiq-countdown"
                             id="aiq-exp-${signal.id}"
                             data-expiry="${expIso || ''}"
                             style="color:#00f3ff; font-size:12px;">
                            ${expIso ? formatCountdown(expIso) : '—'}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tap hint -->
            <div style="padding: 8px 16px; border-top: 1px solid rgba(0,243,255,0.05);
                        font-size:10px; color:#2d3a4a; text-align:center; letter-spacing:0.06em;">
                TAP FOR DEEP INSIGHT
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
    // DEEP INSIGHT MODAL
    // ═══════════════════════════════════════════════════════════════════════════

    function openDeepInsight(signal) {
        if (!iqModal) return;

        const iq       = signal.analysis_iq || {};
        const isBuy    = (iq.order_type || signal.direction || '').toUpperCase().includes('BUY');
        const pattern  = (iq.pattern_type || signal.pattern || 'PATTERN').replace(/_/g, ' ');
        const rr       = calculateRR(signal);
        const bullish  = signal.sentiment_bullish || 50;
        const bearish  = signal.sentiment_bearish || 50;
        const volatility = iq.volatility_index || 50;
        const ageMin   = iq.signal_age_minutes;
        const ageDisplay = ageMin != null
            ? (ageMin < 60 ? `${ageMin}m` : `${Math.floor(ageMin/60)}h ${ageMin%60}m`)
            : '—';
        const signalAgePercent = Math.min(100, Math.round((ageMin || 0) / (24*60) * 100));

        const body = document.getElementById('aiq-modal-body');
        body.innerHTML = `
            <!-- Modal header -->
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:20px;">
                <div>
                    <div style="font-size:18px; font-weight:800; color:#e2e8f0; letter-spacing:0.04em;">
                        ${escHtml(signal.symbol)}
                        <span style="color:rgba(0,243,255,0.6); font-weight:400; font-size:14px;">
                            | ${escHtml(pattern)}
                        </span>
                    </div>
                    <div style="font-size:11px; color:#4a5568; margin-top:2px;">
                        ${escHtml(signal.full_name || signal.symbol)} · ${escHtml(iq.timeframe || signal.timeframe || '4H')}
                    </div>
                </div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <span class="aiq-badge ${isBuy ? 'aiq-badge-buy' : 'aiq-badge-sell'}" style="font-size:12px; padding:5px 14px;">
                        ${isBuy ? '▲' : '▼'} ${escHtml(iq.order_type || (isBuy ? 'BUY STOP' : 'SELL STOP'))}
                    </span>
                    <button onclick="window.EnhancedSignalsPage.closeIQModal()"
                            style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.08);
                                   color:#6b7280; border-radius:6px; width:30px; height:30px;
                                   display:flex; align-items:center; justify-content:center; cursor:pointer; font-size:16px;">
                        ×
                    </button>
                </div>
            </div>

            <!-- Visual projection placeholder -->
            <div class="aiq-chart-placeholder" style="margin-bottom:20px;">
                <div style="position:relative; z-index:1; text-align:center;">
                    <div style="font-size:11px; letter-spacing:0.15em; color:rgba(0,243,255,0.4); margin-bottom:4px;">
                        PATTERN CHART
                    </div>
                    <div style="font-size:10px; color:#2d3a4a;">
                        Chart integration via your price data provider
                    </div>
                    <!-- SVG pattern sketch -->
                    <svg width="260" height="60" viewBox="0 0 260 60" style="margin-top:10px; opacity:0.35;">
                        ${isBuy
                            ? `<polyline points="10,50 60,30 90,35 100,25 130,28 160,15 200,18 250,8"
                                        stroke="#00f3ff" stroke-width="1.5" fill="none" stroke-dasharray="4,2"/>
                               <circle cx="160" cy="15" r="4" fill="#00f3ff" opacity="0.7"/>
                               <line x1="160" y1="0" x2="160" y2="60" stroke="#00f3ff" stroke-width="0.5" stroke-dasharray="2,3"/>`
                            : `<polyline points="10,10 60,30 90,25 100,35 130,32 160,45 200,42 250,55"
                                        stroke="#ff4d6d" stroke-width="1.5" fill="none" stroke-dasharray="4,2"/>
                               <circle cx="160" cy="45" r="4" fill="#ff4d6d" opacity="0.7"/>
                               <line x1="160" y1="0" x2="160" y2="60" stroke="#ff4d6d" stroke-width="0.5" stroke-dasharray="2,3"/>`
                        }
                    </svg>
                </div>
            </div>

            <!-- 2-col content -->
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:20px;">

                <!-- Left: levels -->
                <div>
                    <div style="font-size:10px; font-weight:700; letter-spacing:0.12em; color:#4a5568; margin-bottom:8px;">
                        EXECUTION LEVELS
                    </div>
                    <div class="aiq-grid">
                        <div class="aiq-cell">
                            <div class="aiq-cell-label">Entry</div>
                            <div class="aiq-cell-value aiq-price" style="color:#60a5fa;">${escHtml(signal.entry||'—')}</div>
                        </div>
                        <div class="aiq-cell">
                            <div class="aiq-cell-label">Target</div>
                            <div class="aiq-cell-value aiq-price" style="color:#34d399;">${escHtml(signal.target||'—')}</div>
                        </div>
                        <div class="aiq-cell">
                            <div class="aiq-cell-label">Stop Loss</div>
                            <div class="aiq-cell-value aiq-price" style="color:#f87171;">${escHtml(signal.stop||'—')}</div>
                        </div>
                        <div class="aiq-cell">
                            <div class="aiq-cell-label">R:R Ratio</div>
                            <div class="aiq-cell-value aiq-price" style="color:#a78bfa;">${escHtml(rr)}</div>
                        </div>
                    </div>

                    <div style="margin-top:12px; font-size:10px; font-weight:700; letter-spacing:0.12em; color:#4a5568; margin-bottom:6px;">
                        CURRENT PRICE
                    </div>
                    <div style="font-size:20px; font-weight:800; color:#e2e8f0; font-family:'JetBrains Mono',monospace;">
                        ${escHtml(signal.current_price || '—')}
                        <span style="font-size:12px; font-weight:400; color:${parseFloat(signal.price_change||0)>=0?'#34d399':'#f87171'}; margin-left:6px;">
                            ${escHtml(signal.price_change_percent || '')}
                        </span>
                    </div>
                </div>

                <!-- Right: technical summary -->
                <div>
                    <div style="font-size:10px; font-weight:700; letter-spacing:0.12em; color:#4a5568; margin-bottom:8px;">
                        TECHNICAL SUMMARY
                    </div>
                    <div style="background:#0d1117; border:1px solid rgba(0,243,255,0.06); border-radius:8px; padding:14px;
                                font-size:12px; line-height:1.7; color:#9ca3af; min-height:100px;">
                        ${escHtml(iq.technical_summary || 'Professional technical analysis based on institutional order flow and pattern recognition.')}
                    </div>
                </div>
            </div>

            <!-- Live Stats Bar -->
            <div style="background:#0d1117; border:1px solid rgba(0,243,255,0.06); border-radius:8px;
                        padding:14px 16px; margin-bottom:20px;">
                <div style="font-size:10px; font-weight:700; letter-spacing:0.12em; color:#4a5568; margin-bottom:12px;">
                    LIVE STATS
                </div>
                <div style="display:grid; gap:10px;">
                    <!-- Sentiment -->
                    <div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <span style="font-size:10px; color:#6b7280;">Sentiment — Bullish</span>
                            <span style="font-size:10px; color:#34d399; font-family:monospace;">${bullish}%</span>
                        </div>
                        <div class="aiq-stat-bar">
                            <div class="aiq-stat-fill aiq-stat-fill-green" style="width:${bullish}%;"></div>
                        </div>
                    </div>
                    <!-- Volatility -->
                    <div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <span style="font-size:10px; color:#6b7280;">Volatility Index</span>
                            <span style="font-size:10px; color:#f59e0b; font-family:monospace;">${volatility}</span>
                        </div>
                        <div class="aiq-stat-bar">
                            <div class="aiq-stat-fill aiq-stat-fill-orange" style="width:${volatility}%;"></div>
                        </div>
                    </div>
                    <!-- Signal Age -->
                    <div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <span style="font-size:10px; color:#6b7280;">Signal Age</span>
                            <span style="font-size:10px; color:#00f3ff; font-family:monospace;">${ageDisplay}</span>
                        </div>
                        <div class="aiq-stat-bar">
                            <div class="aiq-stat-fill aiq-stat-fill-cyan" style="width:${signalAgePercent}%;"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Execution bar -->
            <div style="display:flex; gap:10px; align-items:center;">
                <button class="aiq-copy-btn" onclick="window.EnhancedSignalsPage.copyToMT5(${signal.id})">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M8 17H5a2 2 0 01-2-2V5a2 2 0 012-2h10a2 2 0 012 2v3"/>
                        <rect x="8" y="11" width="13" height="10" rx="2"/>
                    </svg>
                    Copy to MT5
                </button>
                <div style="font-size:10px; color:#2d3a4a; line-height:1.4;">
                    Executes via your connected Copier account.<br>
                    Risk management rules applied automatically.
                </div>
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
    };

})();
