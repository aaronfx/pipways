/**
 * Enhanced Signals v21.0 — Merged Architecture
 *
 * SECTION 1: EnhancedSignalsPage class
 *   — Owns the section lifecycle: fetch, stats, tabs, grid cards, refresh interval
 *   — renderGridChart(): lightweight chart per card (Map-based, one per signal)
 *   — viewAnalysis():    opens modal and hands off to ProChart for full PRO render
 *
 * SECTION 2: ProChart IIFE
 *   — Modal-level PRO renderer: patterns, zones, projections, DOM overlays
 *   — Single global chartInstance (modal pattern — one at a time)
 *   — Exposes window.ProChart.{ create, destroy, validateCandles, tradeState, ensureLoaded }
 *
 * Integration contract:
 *   Grid cards  → renderGridChart() uses window.ProChart.validateCandles + window.LightweightCharts
 *   Modal       → viewAnalysis()    calls window.ProChart.create('modal-chart-container', signal)
 *   calculateStatus() delegates to window.ProChart.tradeState() when available
 */

// ═══════════════════════════════════════════════════════════════════════════════
// SECTION 1 — EnhancedSignalsPage
// ═══════════════════════════════════════════════════════════════════════════════

class EnhancedSignalsPage {
    constructor() {
        this.charts           = new Map();
        this.signals          = [];
        this._refreshInterval = null;
        this._sectionVisible  = false;
        this._initialized     = false;
        console.log('[EnhancedSignals] Instance created v21.1');
    }

    // ── Lifecycle ──────────────────────────────────────────────────────────────

    init() {
        console.log('[EnhancedSignals] init() v21.1');
        this._sectionVisible = true;

        // Modal close — button, Escape key, backdrop click
        const closeBtn = document.getElementById('closeModal');
        if (closeBtn) closeBtn.addEventListener('click', () => this.closeModal());
        document.addEventListener('keydown', (e) => { if (e.key === 'Escape') this.closeModal(); });
        const modal = document.getElementById('signalModal');
        if (modal) modal.addEventListener('click', (e) => { if (e.target === modal) this.closeModal(); });

        this.loadSignals();
        this._refreshInterval = setInterval(() => {
            if (this._sectionVisible) this.loadSignals();
        }, 30000);
    }

    // Called by dashboard when section becomes hidden (#9)
    pause()  { this._sectionVisible = false; }
    resume() { this._sectionVisible = true;  this.loadSignals(); }

    destroy() {
        if (this._refreshInterval) { clearInterval(this._refreshInterval); this._refreshInterval = null; }
        this._sectionVisible = false;
        this._initialized    = false;  // #17: reset so init() fires again on next visit
        // #7: disconnect observers before removing charts
        this.charts.forEach(({ chart, observer }) => {
            if (observer) observer.disconnect();
            if (chart)    chart.remove();
        });
        this.charts.clear();
        if (window.ProChart) window.ProChart.destroy();
    }

    // ── Signal Loading ─────────────────────────────────────────────────────────

    async loadSignals() {
        const container = document.getElementById('enhanced-signals-container');
        if (!container) { console.warn('[EnhancedSignals] Container not found'); return; }

        try {
            const response = await fetch('/api/signals/enhanced');
            if (!response.ok) throw new Error('HTTP ' + response.status);

            const signals = await response.json();

            // Keep only the most recent signal per symbol — prevents duplicate cards
            const seen = new Set();
            this.signals = (signals || []).filter(s => {
                if (seen.has(s.symbol)) return false;
                seen.add(s.symbol);
                return true;
            });

            this._updateStats();   // #4: also fetches win rate async
            this._renderGrid();

        } catch (err) {
            console.error('[EnhancedSignals] Load error:', err);
            container.innerHTML = `
                <div class="col-span-full" style="padding:24px;color:#f87171;text-align:center;">
                    <i class="fas fa-exclamation-triangle" style="font-size:2rem;margin-bottom:10px;display:block;"></i>
                    Error loading signals: ${err.message}
                </div>`;
        }
    }

    _renderGrid() {
        const container = document.getElementById('enhanced-signals-container');
        if (!container) return;

        if (this.signals.length === 0) {
            // #7: destroy before wiping DOM
            this._destroyGridCharts();
            container.innerHTML = `
                <div class="col-span-full" style="text-align:center;padding:60px 20px;">
                    <div style="font-size:48px;margin-bottom:16px;">📊</div>
                    <h3 style="color:#9ca3af;font-size:1.1rem;font-weight:600;margin-bottom:8px;">No Active Signals</h3>
                    <p style="color:#6b7280;font-size:.875rem;">Waiting for trading opportunities…</p>
                </div>`;
            return;
        }

        // #7: destroy old observers + charts BEFORE wiping DOM containers
        this._destroyGridCharts();

        container.innerHTML = this.signals.map(s => this.renderSignalCard(s)).join('');
    }

    _destroyGridCharts() {
        // #7: disconnect ResizeObserver for every card before chart.remove()
        this.charts.forEach(({ chart, observer }) => {
            if (observer) observer.disconnect();
            if (chart)    chart.remove();
        });
        this.charts.clear();
    }

    // ── Stats Row ──────────────────────────────────────────────────────────────

    _updateStats() {
        // Active = signals with status 'active' (from DB, not time-based)
        const active = this.signals.filter(s => (s.status || 'active') === 'active').length;

        const avgConf = this.signals.length
            ? Math.round(this.signals.reduce((sum, s) => sum + (s.confidence || 70), 0) / this.signals.length)
            : null;

        const rrValues = this.signals.map(s => this._calcRR(s)).filter(Boolean);
        const avgRR    = rrValues.length
            ? (rrValues.reduce((a, b) => a + b, 0) / rrValues.length).toFixed(1)
            : null;

        const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        set('enhanced-stat-active',     active);
        set('enhanced-stat-confidence', avgConf != null ? avgConf + '%' : '—');
        set('enhanced-stat-rr',         avgRR   != null ? avgRR + 'R'  : '—');

        // #4: Fetch win rate separately (async, non-blocking)
        fetch('/api/signals/winrate?days=7')
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (data && data.win_rate_pct != null) {
                    set('enhanced-stat-winrate', data.win_rate_pct + '%');
                }
            })
            .catch(() => {});   // silent — winrate is a nice-to-have
    }

    _calcRR(signal) {
        const entry  = parseFloat(signal.entry);
        const target = parseFloat(signal.target);
        const stop   = parseFloat(signal.stop);
        if (!entry || !target || !stop) return null;
        const reward = Math.abs(target - entry);
        const risk   = Math.abs(entry  - stop);
        return risk > 0 ? reward / risk : null;
    }

    // ── Status ─────────────────────────────────────────────────────────────────

    // #2: calculateStatus reads DB status — bot updates via /close endpoints
    calculateStatus(signal) {
        const dbStatus = (signal.status || 'active').toLowerCase();
        if (dbStatus === 'closed_tp')     return { text: 'TARGET HIT',  class: 'target_hit', icon: '✓', bg: 'rgba(0,255,136,0.2)',   color: '#00ff88' };
        if (dbStatus === 'closed_sl')     return { text: 'STOPPED OUT', class: 'stopped',    icon: '✗', bg: 'rgba(255,71,87,0.2)',   color: '#ff4757' };
        if (dbStatus === 'closed_manual') return { text: 'CLOSED',      class: 'expired',    icon: '⚪', bg: 'rgba(139,148,158,0.2)', color: '#8b949e' };
        if (dbStatus === 'expired')       return { text: 'EXPIRED',     class: 'expired',    icon: '⚪', bg: 'rgba(139,148,158,0.2)', color: '#8b949e' };
        // Still active — time-based PENDING vs LIVE TRADE
        const mins = (Date.now() - new Date(signal.created_at)) / 60000;
        if (mins < 5) return { text: 'PENDING',    class: 'pending', icon: '⏳', bg: 'rgba(255,193,7,0.2)',  color: '#ffc107' };
        return             { text: 'LIVE TRADE', class: 'active',  icon: '●',  bg: 'rgba(0,201,167,0.2)', color: '#00c9a7' };
    }

    // ── Grid Chart (#7 — {chart,observer} stored together so both can be cleaned up) ──

    renderGridChart(signal) {
        const container = document.getElementById('chart-' + signal.id);
        if (!container) return;
        try {
            const LC = window.LightweightCharts;
            if (!LC) {
                container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#555;font-size:12px;">Chart lib not ready</div>';
                return;
            }
            // Grid cards have no candles (/enhanced excludes them) — always use validated fallback
            const candles = (window.ProChart && window.ProChart.validateCandles)
                ? window.ProChart.validateCandles(signal) : [];
            if (!candles || candles.length < 5) {
                container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#555;font-size:12px;">No chart data</div>';
                return;
            }
            const isClosed  = ['closed_tp','closed_sl','closed_manual','expired'].includes(signal.status || '');
            const upColor   = isClosed ? '#1d4a38' : '#00d084';
            const downColor = isClosed ? '#4a1d1d' : '#ff4757';
            const chart = LC.createChart(container, {
                width: container.clientWidth, height: container.clientHeight,
                layout: { background: { type: 'solid', color: '#0a0a0f' }, textColor: '#6b7280', fontFamily: "'Inter',sans-serif" },
                grid:   { vertLines: { color: 'rgba(255,255,255,0.02)' }, horzLines: { color: 'rgba(255,255,255,0.02)' } },
                crosshair:       { mode: LC.CrosshairMode.None },
                rightPriceScale: { borderColor: 'rgba(255,255,255,0.05)', scaleMargins: { top: 0.1, bottom: 0.1 } },
                timeScale:       { borderColor: 'rgba(255,255,255,0.05)', visible: false },
                handleScroll: false, handleScale: false,
            });
            const cs = chart.addCandlestickSeries({ upColor, downColor, borderUpColor: upColor, borderDownColor: downColor, wickUpColor: upColor, wickDownColor: downColor });
            cs.setData(candles);
            const entry = parseFloat(signal.entry), target = parseFloat(signal.target), stop = parseFloat(signal.stop);
            if (entry)  cs.createPriceLine({ price: entry,  color: '#ffffff', lineWidth: 1, lineStyle: LC.LineStyle.Solid,  axisLabelVisible: false });
            if (target) cs.createPriceLine({ price: target, color: '#00d084', lineWidth: 1, lineStyle: LC.LineStyle.Dashed, axisLabelVisible: false });
            if (stop)   cs.createPriceLine({ price: stop,   color: '#ff4757', lineWidth: 1, lineStyle: LC.LineStyle.Dashed, axisLabelVisible: false });
            chart.timeScale().fitContent();
            // #7: store observer alongside chart so _destroyGridCharts() can disconnect it
            const ro = new ResizeObserver((entries) => { if (chart && entries[0]) chart.resize(entries[0].contentRect.width, entries[0].contentRect.height); });
            ro.observe(container);
            this.charts.set(signal.id, { chart, observer: ro });
        } catch (err) {
            console.error('[GridChart] ' + signal.symbol + ':', err);
            container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#ef4444;font-size:12px;">Chart error</div>';
        }
    }

    // ── Card Rendering ─────────────────────────────────────────────────────────

    renderSignalCard(signal) {
        const pattern  = signal.pattern_name || signal.pattern || 'Breakout';
        const status   = this.calculateStatus(signal);
        const isBuy    = (signal.direction || '').toUpperCase().includes('BUY');
        const isActive = status.class === 'active';
        const isExpired= status.class === 'expired' || status.class === 'stopped';
        const expiry   = this._formatExpiry(signal);
        const flagHtml = this._getFlag(signal.symbol || '');
        const conf     = signal.confidence || 70;

        // Published time — "5 mins ago" / "2h ago"
        const publishedAgo = signal.created_at ? this._timeAgo(signal.created_at) : '';

        // Confidence bar — real SMC confluence score, not fake news sentiment
        const confBarWidth = Math.min(100, Math.max(0, conf));
        const confColor    = conf >= 80 ? '#00d084' : conf >= 60 ? '#f59e0b' : '#ef4444';
        const confLabel    = conf >= 80 ? 'HIGH' : conf >= 60 ? 'MEDIUM' : 'LOW';

        const topBadge = isActive
            ? '<span class="sig-live-trade">LIVE TRADE</span>'
            : status.class === 'target_hit'
                ? '<span class="sig-target-hit-badge">✓ TARGET HIT</span>'
                : status.class === 'stopped'
                    ? '<span class="badge badge-danger">✗ STOPPED</span>'
                    : '<span style="height:22px;display:inline-block;"></span>';

        return `
            <div class="signal-card rounded-xl overflow-hidden cursor-pointer${isExpired ? ' opacity-60' : ''}"
                 data-signal-id="${signal.id}"
                 onclick="window.enhancedSignals.viewAnalysis(${signal.id})">

                <!-- Top bar -->
                <div class="flex items-center justify-between px-3 pt-3 pb-1">
                    ${topBadge}
                    <div class="sig-brand-icon"><i class="fas fa-chart-line"></i></div>
                </div>

                <!-- Symbol row: flag + symbol + pattern name -->
                <div class="flex items-center justify-between px-3 pb-2 gap-2">
                    <div class="flex items-center gap-2 min-w-0">
                        ${flagHtml}
                        <span class="text-white font-bold" style="font-size:15px;letter-spacing:.02em;">${signal.symbol}</span>
                    </div>
                    <span class="text-gray-400 text-xs font-semibold uppercase tracking-wide flex-shrink-0"
                          style="max-width:140px;font-size:11px;"
                          title="${pattern}">${pattern}</span>
                </div>

                <!-- Direction pill — centered -->
                <div class="flex justify-center pb-3">
                    <span class="${isBuy ? 'sig-buystop-pill' : 'sig-sellstop-pill'}">
                        ${isBuy ? 'BUY STOP' : 'SELL STOP'}
                    </span>
                </div>

                <!-- Price list -->
                <div class="sig-price-list px-3">
                    <div class="sig-row">
                        <span class="sig-label">Entry</span>
                        <span class="sig-value level-entry">${signal.entry}</span>
                    </div>
                    <div class="sig-row">
                        <span class="sig-label">Target</span>
                        <span class="sig-value level-target">${signal.target}</span>
                    </div>
                    <div class="sig-row">
                        <span class="sig-label">Stop</span>
                        <span class="sig-value level-stop">${signal.stop}</span>
                    </div>
                    <div class="sig-row">
                        <span class="sig-label">Expires</span>
                        ${expiry}
                    </div>
                    ${publishedAgo ? `<div class="sig-row">
                        <span class="sig-label">Published</span>
                        <span style="color:#6b7280;font-size:11px;font-family:monospace;">${publishedAgo}</span>
                    </div>` : ''}
                </div>

                <!-- Confidence bar -->
                <div style="padding:0 12px 10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                        <span style="color:#6b7280;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;">Confidence</span>
                        <span style="color:${confColor};font-size:11px;font-weight:700;">${conf}% <span style="opacity:.7;">${confLabel}</span></span>
                    </div>
                    <div style="height:5px;background:#1f2937;border-radius:3px;overflow:hidden;">
                        <div style="width:${confBarWidth}%;height:100%;background:${confColor};border-radius:3px;transition:width .4s ease;"></div>
                    </div>
                </div>

                <!-- Pattern SVG — static, instant, no chart library needed -->
                <div class="relative mx-3 mt-3 rounded-lg overflow-hidden" style="height:175px;background:#0a0a0f;border:1px solid #1f2937;">
                    ${this._drawPatternSVG(signal)}
                    <div class="sig-tf-badge">${(signal.timeframe || 'M5').toUpperCase()}</div>
                </div>

                <!-- Footer -->
                <div class="p-3">
                    <button class="sig-learn-btn"
                            onclick="event.stopPropagation(); window.enhancedSignals.viewAnalysis(${signal.id})">
                        LEARN MORE
                    </button>
                </div>
            </div>`;
    }

    // ── Static Pattern SVG ─────────────────────────────────────────────────────
    // Uses pattern_name (primary) and structure (fallback) to classify.
    // Candles are crafted per-pattern to visually show the formation.

    _drawPatternSVG(signal) {
        const isBuy   = (signal.direction || '').toUpperCase().includes('BUY');
        const pName   = (signal.pattern_name || signal.pattern || '').toLowerCase();
        const pStruct = (signal.structure || '').toLowerCase();

        // Classify — pattern_name is authoritative
        let pType = isBuy ? 'breakout' : 'breakdown';
        if      (pName.includes('descending triangle') || pStruct === 'horizontal_bottom') pType = 'desc_triangle';
        else if (pName.includes('ascending triangle')  || pStruct === 'horizontal_top')   pType = 'asc_triangle';
        else if (pName.includes('symmetrical')         || pStruct === 'converging')        pType = 'sym_triangle';
        else if (pName.includes('rising wedge')        || pStruct === 'converging_rising') pType = 'rising_wedge';
        else if (pName.includes('falling wedge')       || pStruct === 'converging_falling')pType = 'falling_wedge';
        else if (pName.includes('bear flag')           || pStruct === 'parallel_up')       pType = 'bear_flag';
        else if (pName.includes('bull flag')           || pStruct === 'parallel_down')     pType = 'bull_flag';
        else if (pName.includes('descending channel')  || pStruct === 'parallel_falling')  pType = 'desc_channel';
        else if (pName.includes('ascending channel')   || pStruct === 'parallel_rising')   pType = 'asc_channel';

        const w = 320, h = 175;
        const G = '#00d084', R = '#ff4757', W = '#ffffff';

        // Fixed vertical levels (px) — SELL: stop=top, entry=mid, target=bottom
        const stopPx   = isBuy ? 138 : 18;
        const entryPx  = isBuy ? 96  : 72;
        const targetPx = isBuy ? 22  : 148;

        // Candle area: spans vertically from slightly above stop to slightly below entry
        const aTop = Math.min(stopPx, entryPx) - 10;
        const aBot = Math.max(stopPx, entryPx) + 10;
        const aH   = aBot - aTop;
        const nC   = 9, cw = 13, cGap = 5, x0 = 10;
        // Normalize: n=0 → aTop, n=1 → aBot
        const yN = n => aTop + n * aH;

        // Zone (right 32%)
        const zX = w * 0.68, zW = w * 0.32;

        // Each candle def: [highN, lowN, openN, closeN, bull]  (all 0-1 normalized)
        let defs, topPath, botPath;

        if (pType === 'desc_triangle') {
            // Falling highs, flat lows → break DOWN
            defs = [
                [0.05,0.62,0.12,0.56,false], [0.18,0.62,0.32,0.57,false],
                [0.28,0.62,0.48,0.60,true],  [0.38,0.62,0.52,0.59,false],
                [0.48,0.62,0.60,0.58,false], [0.56,0.62,0.68,0.59,true],
                [0.64,0.62,0.74,0.60,false], [0.70,0.62,0.78,0.61,false],
                [0.72,0.82,0.78,0.80,false], // breakdown candle — stays in risk zone above entry
            ];
            // Falling resistance: top-left to mid-right
            topPath = `M ${x0},${yN(0.05)} L ${x0+7*(cw+cGap)+cw},${yN(0.70)}`;
            // Flat support dashed
            botPath = `M ${x0},${yN(0.63)} L ${zX},${yN(0.63)}`;

        } else if (pType === 'asc_triangle') {
            defs = [
                [0.05,0.92,0.88,0.10,true],  [0.05,0.80,0.76,0.10,true],
                [0.05,0.68,0.64,0.10,false],  [0.05,0.58,0.54,0.10,true],
                [0.05,0.50,0.46,0.10,false],  [0.05,0.42,0.38,0.10,true],
                [0.05,0.36,0.32,0.10,false],  [0.05,0.30,0.26,0.10,true],
                [0.03,0.08,0.26,0.05,true],  // breakout candle
            ];
            topPath = `M ${x0},${yN(0.05)} L ${zX},${yN(0.05)}`; // flat resistance
            botPath = `M ${x0},${yN(0.92)} L ${x0+7*(cw+cGap)+cw},${yN(0.30)}`; // rising support

        } else if (pType === 'sym_triangle') {
            defs = [
                [0.02,0.96,0.20,0.30,true],  [0.12,0.86,0.28,0.25,false],
                [0.20,0.78,0.36,0.30,true],  [0.28,0.70,0.42,0.35,false],
                [0.34,0.64,0.46,0.38,true],  [0.40,0.58,0.50,0.42,false],
                [0.44,0.54,0.52,0.46,true],  [0.46,0.52,0.52,0.48,false],
                isBuy ? [0.42,0.18,0.48,0.20,true] : [0.48,0.80,0.48,0.78,false],
            ];
            topPath = `M ${x0},${yN(0.02)} L ${x0+7*(cw+cGap)},${yN(0.46)}`;
            botPath = `M ${x0},${yN(0.96)} L ${x0+7*(cw+cGap)},${yN(0.54)}`;

        } else if (pType === 'rising_wedge') {
            defs = [
                [0.08,0.75,0.72,0.62,false],[0.04,0.65,0.62,0.52,true],
                [0.06,0.58,0.55,0.48,false],[0.04,0.50,0.47,0.40,true],
                [0.06,0.44,0.41,0.35,false],[0.04,0.38,0.35,0.30,true],
                [0.06,0.33,0.30,0.27,false],[0.04,0.28,0.26,0.24,true],
                [0.08,0.95,0.24,0.90,false],
            ];
            topPath = `M ${x0},${yN(0.08)} L ${x0+7*(cw+cGap)},${yN(0.06)}`;
            botPath = `M ${x0},${yN(0.75)} L ${x0+7*(cw+cGap)},${yN(0.28)}`;

        } else if (pType === 'falling_wedge') {
            defs = [
                [0.22,0.88,0.26,0.34,true],[0.30,0.80,0.34,0.42,false],
                [0.36,0.74,0.40,0.48,true],[0.42,0.68,0.46,0.52,false],
                [0.46,0.63,0.50,0.54,true],[0.50,0.58,0.54,0.56,false],
                [0.52,0.55,0.56,0.53,true],[0.53,0.53,0.56,0.52,false],
                [0.18,0.28,0.52,0.20,true],
            ];
            topPath = `M ${x0},${yN(0.22)} L ${x0+7*(cw+cGap)},${yN(0.52)}`;
            botPath = `M ${x0},${yN(0.88)} L ${x0+7*(cw+cGap)},${yN(0.53)}`;

        } else if (pType === 'bear_flag') {
            defs = [
                [0.02,0.38,0.34,0.05,false],[0.04,0.42,0.38,0.08,false],
                [0.20,0.52,0.50,0.25,true], [0.22,0.56,0.53,0.28,false],
                [0.28,0.60,0.57,0.33,true], [0.30,0.64,0.60,0.36,false],
                [0.34,0.67,0.63,0.40,true], [0.36,0.70,0.65,0.42,false],
                [0.38,0.95,0.65,0.92,false],
            ];
            topPath = `M ${x0+2*(cw+cGap)},${yN(0.22)} L ${x0+7*(cw+cGap)},${yN(0.36)}`;
            botPath = `M ${x0+2*(cw+cGap)},${yN(0.54)} L ${x0+7*(cw+cGap)},${yN(0.68)}`;

        } else if (pType === 'bull_flag') {
            defs = [
                [0.62,0.96,0.92,0.66,true], [0.58,0.88,0.84,0.62,true],
                [0.50,0.78,0.76,0.54,false],[0.46,0.74,0.72,0.50,false],
                [0.42,0.70,0.68,0.46,true], [0.40,0.68,0.65,0.44,false],
                [0.36,0.65,0.62,0.40,true], [0.34,0.63,0.60,0.38,false],
                [0.08,0.36,0.36,0.10,true],
            ];
            topPath = `M ${x0+2*(cw+cGap)},${yN(0.50)} L ${x0+7*(cw+cGap)},${yN(0.36)}`;
            botPath = `M ${x0+2*(cw+cGap)},${yN(0.76)} L ${x0+7*(cw+cGap)},${yN(0.62)}`;

        } else if (pType === 'desc_channel') {
            defs = [
                [0.05,0.32,0.08,0.28,false],[0.14,0.42,0.18,0.37,true],
                [0.17,0.46,0.22,0.42,false],[0.26,0.56,0.32,0.51,true],
                [0.30,0.60,0.36,0.56,false],[0.40,0.70,0.46,0.66,true],
                [0.44,0.74,0.50,0.70,false],[0.54,0.84,0.60,0.80,true],
                [0.58,0.92,0.62,0.89,false],
            ];
            topPath = `M ${x0},${yN(0.05)} L ${x0+8*(cw+cGap)},${yN(0.58)}`;
            botPath = `M ${x0},${yN(0.32)} L ${x0+8*(cw+cGap)},${yN(0.88)}`;

        } else if (pType === 'asc_channel') {
            defs = [
                [0.58,0.90,0.86,0.62,true], [0.52,0.83,0.80,0.56,false],
                [0.46,0.76,0.74,0.50,true], [0.40,0.70,0.68,0.44,false],
                [0.34,0.64,0.62,0.38,true], [0.28,0.58,0.56,0.32,false],
                [0.22,0.52,0.50,0.26,true], [0.16,0.46,0.44,0.20,false],
                [0.04,0.24,0.22,0.08,true],
            ];
            topPath = `M ${x0},${yN(0.58)} L ${x0+8*(cw+cGap)},${yN(0.04)}`;
            botPath = `M ${x0},${yN(0.90)} L ${x0+8*(cw+cGap)},${yN(0.24)}`;

        } else {
            // Breakout/Breakdown — tight consolidation then decisive candle
            const flat = 0.52;
            defs = [
                [flat-0.30,flat+0.08,flat-0.14,flat+0.04,false],
                [flat-0.28,flat+0.08,flat-0.12,flat+0.04,true],
                [flat-0.30,flat+0.09,flat-0.14,flat+0.05,false],
                [flat-0.28,flat+0.08,flat-0.12,flat+0.04,true],
                [flat-0.29,flat+0.09,flat-0.13,flat+0.05,false],
                [flat-0.28,flat+0.08,flat-0.12,flat+0.04,true],
                [flat-0.30,flat+0.09,flat-0.14,flat+0.05,false],
                [flat-0.28,flat+0.08,flat-0.12,flat+0.04,true],
                isBuy
                    ? [flat-0.50,flat+0.02,flat-0.25,flat-0.42,true]
                    : [flat-0.02,flat+0.50,flat+0.22,flat+0.44,false],
            ];
            topPath = `M ${x0},${yN(flat-0.28)} L ${x0+7*(cw+cGap)+cw},${yN(flat-0.28)}`;
            botPath = null;
        }

        const svg_candles = defs.map((d, i) => {
            const [hN,lN,oN,cN,bull] = d;
            const px = x0 + i*(cw+cGap);
            const hY = yN(hN), lY = yN(lN);
            const oY = yN(Math.min(oN,cN)), cY = yN(Math.max(oN,cN));
            const bH = Math.max(2, cY-oY);
            const col = bull ? G : R;
            return `<rect x="${px}" y="${oY}" width="${cw}" height="${bH}" rx="1" fill="${col}" opacity="0.88"/>
                    <line x1="${px+cw/2}" y1="${hY}" x2="${px+cw/2}" y2="${lY}" stroke="${col}" stroke-width="1" opacity="0.5"/>`;
        }).join('');

        return `<svg width="100%" height="100%" viewBox="0 0 ${w} ${h}"
                     preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg"
                     style="position:absolute;top:0;left:0;">
            <rect x="${zX}" y="${Math.min(entryPx,targetPx)}" width="${zW}" height="${Math.abs(targetPx-entryPx)}" fill="rgba(0,208,132,0.14)"/>
            <rect x="${zX}" y="${Math.min(entryPx,stopPx)}"   width="${zW}" height="${Math.abs(stopPx-entryPx)}"   fill="rgba(255,71,87,0.14)"/>
            ${svg_candles}
            ${topPath ? `<path d="${topPath}" stroke="${R}" stroke-width="1.8" fill="none" opacity="0.85"/>` : ''}
            ${botPath ? `<path d="${botPath}" stroke="${G}" stroke-width="1.8" fill="none" stroke-dasharray="5,3" opacity="0.80"/>` : ''}
            <line x1="0"    y1="${entryPx}"  x2="${w}" y2="${entryPx}"  stroke="${W}" stroke-width="1.5" opacity="0.9"/>
            <line x1="${zX}" y1="${targetPx}" x2="${w}" y2="${targetPx}" stroke="${G}" stroke-width="1"   stroke-dasharray="4,3" opacity="0.85"/>
            <line x1="${zX}" y1="${stopPx}"   x2="${w}" y2="${stopPx}"   stroke="${R}" stroke-width="1"   stroke-dasharray="4,3" opacity="0.85"/>
            <text x="${w-3}" y="${targetPx-3}" text-anchor="end" fill="${G}" font-size="9" font-family="monospace" font-weight="bold">TARGET</text>
            <text x="${w-3}" y="${entryPx-3}"  text-anchor="end" fill="${W}" font-size="9" font-family="monospace" font-weight="bold">ENTRY</text>
            <text x="${w-3}" y="${stopPx-3}"   text-anchor="end" fill="${R}" font-size="9" font-family="monospace" font-weight="bold">STOP</text>
        </svg>`;
    }

        // ── Helpers ────────────────────────────────────────────────────────────────

    _getFlag(symbol) {
        const FLAGS = {
            USD:'us', EUR:'eu', GBP:'gb', JPY:'jp', CHF:'ch', CAD:'ca',
            AUD:'au', NZD:'nz', SGD:'sg', HKD:'hk', SEK:'se', NOK:'no',
            DKK:'dk', MXN:'mx', ZAR:'za', TRY:'tr', CNH:'cn', CNY:'cn',
            BRL:'br', INR:'in', NGN:'ng', KWD:'kw', AED:'ae', SAR:'sa',
        };
        const SPECIALS = {
            XAU:'🥇', XAG:'🥈', OIL:'🛢', WTI:'🛢', BTC:'₿', ETH:'Ξ',
            US30:'🇺🇸', US500:'🇺🇸', SPX:'🇺🇸', NAS100:'🇺🇸', NDX:'🇺🇸',
            UK100:'🇬🇧', GER40:'🇩🇪', DAX:'🇩🇪', CHINA50:'🇨🇳',
            JPN225:'🇯🇵', AUS200:'🇦🇺', HK50:'🇭🇰',
        };
        const sym   = (symbol || '').toUpperCase();
        const base  = sym.slice(0, 3);
        const quote = sym.slice(3, 6);

        // Specials (commodities, indices) — single icon
        for (const [key, icon] of Object.entries(SPECIALS)) {
            if (sym.startsWith(key) || sym === key) {
                return `<div class="sig-flag"><span style="font-size:18px;line-height:1;">${icon}</span></div>`;
            }
        }

        // Forex pairs — show BOTH base and quote flags overlapping
        const baseCode  = FLAGS[base];
        const quoteCode = FLAGS[quote];
        if (baseCode && quoteCode) {
            return `<div class="sig-flag" style="position:relative;width:44px;height:32px;flex-shrink:0;">
                <img src="https://flagcdn.com/w40/${baseCode}.png" alt="${base}" loading="lazy"
                     style="position:absolute;left:0;top:4px;width:26px;height:20px;border-radius:3px;object-fit:cover;border:1px solid #374151;"
                     onerror="this.style.display='none'">
                <img src="https://flagcdn.com/w40/${quoteCode}.png" alt="${quote}" loading="lazy"
                     style="position:absolute;left:16px;top:8px;width:26px;height:20px;border-radius:3px;object-fit:cover;border:1px solid #374151;"
                     onerror="this.style.display='none'">
            </div>`;
        }
        if (baseCode) {
            return `<div class="sig-flag"><img src="https://flagcdn.com/w40/${baseCode}.png" alt="${base}" loading="lazy" onerror="this.parentNode.innerHTML='<span style=font-size:16px>💱</span>'"></div>`;
        }
        return `<div class="sig-flag"><span style="font-size:15px;">💱</span></div>`;
    }

    _timeAgo(dateStr) {
        if (!dateStr) return '';
        const diff = Date.now() - new Date(dateStr).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 1)  return 'just now';
        if (mins < 60) return mins + ' min' + (mins === 1 ? '' : 's') + ' ago';
        const hrs = Math.floor(mins / 60);
        if (hrs < 24)  return hrs + 'h ' + (mins % 60) + 'm ago';
        return Math.floor(hrs / 24) + 'd ago';
    }

    _formatExpiry(signal) {
        if (!signal.expires_at) return '<span class="expiry-time">—</span>';
        const diff = new Date(signal.expires_at) - new Date();
        if (diff <= 0) return '<span style="color:#ef4444;font-weight:600;font-family:monospace;">Expired</span>';
        const d = Math.floor(diff / 86400000);
        const h = Math.floor((diff % 86400000) / 3600000);
        const m = Math.floor((diff % 3600000) / 60000);
        const label = d > 0 ? (d + 'd ' + h + 'h') : h > 0 ? (h + 'h ' + m + 'm') : (m + 'm');
        return '<span class="expiry-time" style="font-family:monospace;">' + label + '</span>';
    }

    _getCurrencyName(symbol) {
        const NAMES = {
            EURUSD:'Euro vs US Dollar', GBPUSD:'British Pound vs US Dollar',
            USDJPY:'US Dollar vs Japanese Yen', USDCHF:'US Dollar vs Swiss Franc',
            AUDUSD:'Australian Dollar vs USD', USDCAD:'US Dollar vs Canadian Dollar',
            NZDUSD:'New Zealand Dollar vs USD', GBPJPY:'British Pound vs Yen',
            EURJPY:'Euro vs Japanese Yen', EURGBP:'Euro vs British Pound',
            XAUUSD:'Gold vs US Dollar', XAGUSD:'Silver vs US Dollar',
            BTCUSD:'Bitcoin vs US Dollar', ETHUSD:'Ethereum vs US Dollar',
            US30:'Dow Jones 30', US500:'S&P 500', NAS100:'NASDAQ 100',
            UK100:'FTSE 100', GER40:'DAX 40', CHINA50:'China 50 Index',
            JPN225:'Nikkei 225', AUS200:'ASX 200',
        };
        return NAMES[(symbol || '').toUpperCase()] || symbol;
    }

    _getPatternDescription(pattern) {
        const D = {
            'Pennant':'The Pennant is a short-term continuation pattern that develops after a strong directional move, symbolizing a pause in momentum. It resembles a small symmetrical triangle formed by converging trendlines as volatility temporarily contracts.\n\nThe pattern shows that both buyers and sellers are waiting for new direction following an impulsive move.\n\nA breakout in the direction of the prior trend validates the pattern and signals continuation.\n\nPrice objectives are often set by adding the length of the prior move (the flagpole) to the breakout level.',
            'Ascending Triangle':'The Ascending Triangle is a bullish continuation pattern with a flat upper resistance and a rising lower support. Buyers are becoming increasingly aggressive while sellers hold a fixed ceiling.\n\nEach swing low is higher than the last, showing accumulating demand. A breakout above resistance typically triggers a sharp move upward.',
            'Descending Triangle':'The Descending Triangle is a bearish continuation pattern with a flat support and descending resistance. Sellers grow more aggressive while buyers defend a fixed floor.\n\nA breakdown below support typically leads to a sharp move downward equal to the height of the triangle.',
            'Symmetrical Triangle':'The Symmetrical Triangle is a consolidation pattern where both trendlines converge. Neither buyers nor sellers have a clear advantage as range narrows.\n\nA breakout in the direction of the prior trend signals the next significant move.',
            'Rising Wedge':'The Rising Wedge is a bearish pattern where both support and resistance slope upward but converge. Price makes higher highs and higher lows but momentum is weakening.\n\nA breakdown below the lower trendline signals bearish continuation.',
            'Falling Wedge':'The Falling Wedge is a bullish pattern where both lines slope downward but converge. Selling pressure is decreasing as the pattern matures.\n\nA breakout above the upper trendline signals bullish continuation.',
            'Bull Flag':'The Bull Flag is a bullish continuation pattern: a sharp upward move (the flagpole) followed by a brief rectangular consolidation that slopes slightly downward.\n\nThe measured target is derived by adding the flagpole length to the breakout point.',
            'Bear Flag':'The Bear Flag is a bearish continuation pattern: a sharp downward move followed by a brief consolidation sloping slightly upward.\n\nA breakdown below flag support confirms continuation.',
            'Double Top':'The Double Top is a bearish reversal pattern where price tests a resistance level twice and fails to break through. A breakdown below the neckline confirms the reversal.',
            'Double Bottom':'The Double Bottom is a bullish reversal pattern where price tests a support level twice and holds. A breakout above the neckline confirms the reversal.',
            'Breakout':'A Breakout Setup occurs when price decisively breaks through a key support or resistance level with increased momentum, signalling the start of a new directional move.\n\nThe entry is placed just beyond the breakout level with a stop below the broken structure.',
        };
        return D[pattern] || ('The ' + pattern + ' pattern signals a potential trading opportunity. Monitor key price levels for confirmation of the expected directional move.');
    }

    // ── Modal — opens skeleton immediately, fetches full signal (with candles) async ──

    viewAnalysis(signalId) {
        // Use cached signal for immediate render
        const signal = this.signals.find(s => s.id === signalId);
        if (!signal) return;

        this._openModal(signal);

        // #6: Fetch full signal row (includes candles) for PRO chart
        fetch('/api/signals/' + signalId)
            .then(r => r.ok ? r.json() : null)
            .then(full => {
                if (full && window.ProChart) {
                    const chartDiv   = document.getElementById('modal-chart-container');
                    const loadingDiv = document.getElementById('sig-chart-loading');
                    if (chartDiv) chartDiv.style.display = 'block';
                    window.ProChart.create('modal-chart-container', full)
                        .then(() => { if (loadingDiv) loadingDiv.style.display = 'none'; })
                        .catch(err => {
                            console.error('[Modal] ProChart error:', err);
                            if (loadingDiv) loadingDiv.style.display = 'none';
                            if (chartDiv) chartDiv.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#ef4444;font-size:13px;">Chart error: ' + err.message + '</div>';
                        });
                }
            })
            .catch(() => {
                // Fallback: try rendering with cached signal (no candles — uses fallback data)
                if (window.ProChart) {
                    const chartDiv   = document.getElementById('modal-chart-container');
                    const loadingDiv = document.getElementById('sig-chart-loading');
                    if (chartDiv) chartDiv.style.display = 'block';
                    window.ProChart.create('modal-chart-container', signal)
                        .then(() => { if (loadingDiv) loadingDiv.style.display = 'none'; })
                        .catch(() => { if (loadingDiv) loadingDiv.style.display = 'none'; });
                }
            });
    }

    _openModal(signal) {
        const pattern      = signal.pattern_name || signal.pattern || 'Breakout';
        const rr           = this._calcRR(signal);
        const isBuy        = (signal.direction || '').toUpperCase().includes('BUY');
        const status       = this.calculateStatus(signal);
        const isActive     = status.class === 'active';
        const flagHtml     = this._getFlag(signal.symbol || '');
        const currName     = this._getCurrencyName(signal.symbol || '');
        const conf         = signal.confidence || 70;
        const description  = signal.rationale || this._getPatternDescription(pattern);
        const publishedAt  = signal.created_at
            ? new Date(signal.created_at).toLocaleString([], {day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'})
            : '—';
        const expiresAt    = signal.expires_at
            ? new Date(signal.expires_at).toLocaleString([], {day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'})
            : '—';

        // Confidence — real SMC score (no fake sentiment calculation)
        const confBarWidth = Math.min(100, Math.max(0, conf));
        const confColor    = conf >= 80 ? '#00d084' : conf >= 60 ? '#f59e0b' : '#ef4444';
        const confLabel    = conf >= 80 ? 'HIGH CONFIDENCE' : conf >= 60 ? 'MEDIUM CONFIDENCE' : 'LOW CONFIDENCE';

        // Minimal modal title
        const titleEl = document.getElementById('modalTitle');
        if (titleEl) titleEl.textContent = signal.symbol + ' · ' + pattern;

        const modalContent = document.getElementById('modalContent');
        if (!modalContent) return;

        modalContent.innerHTML = `
            <!-- ── Hero header (Image 2) ── -->
            <div class="sig-modal-hero">
                <div style="display:flex;align-items:flex-start;gap:12px;flex-wrap:wrap;flex:1;">
                    ${flagHtml}
                    <div>
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap;">
                            <span style="background:#1f2937;color:#9ca3af;padding:3px 10px;border-radius:6px;font-size:12px;font-weight:600;">${signal.symbol}</span>
                            <span style="color:white;font-size:17px;font-weight:700;">${currName}</span>
                        </div>
                        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
                            <span class="${isBuy ? 'sig-buystop-pill' : 'sig-sellstop-pill'}" style="font-size:11px;padding:4px 14px;">
                                ${isBuy ? 'BUY STOP' : 'SELL STOP'}
                            </span>
                            ${isActive ? '<span class="sig-live-trade" style="font-size:10px;">LIVE TRADE</span>' : ''}
                        </div>
                    </div>
                </div>
                <div style="text-align:right;flex-shrink:0;">
                    <div style="font-size:28px;font-weight:700;color:white;font-family:monospace;line-height:1;">${signal.entry}</div>
                    ${rr ? `<div style="color:#22c55e;font-size:13px;font-weight:600;margin-top:4px;">R:R ${rr.toFixed(1)} : 1</div>` : ''}
                </div>
            </div>

            <!-- ── Stats grid (Pattern | Entry | Target | Stop) ── -->
            <div class="sig-modal-stats">
                <div class="sig-modal-stat">
                    <span class="sig-modal-stat-label">Pattern</span>
                    <span class="sig-modal-stat-value" style="color:#a78bfa;font-size:12px;">${pattern}</span>
                </div>
                <div class="sig-modal-stat">
                    <span class="sig-modal-stat-label">Entry</span>
                    <span class="sig-modal-stat-value level-entry">${signal.entry}</span>
                </div>
                <div class="sig-modal-stat">
                    <span class="sig-modal-stat-label">Target</span>
                    <span class="sig-modal-stat-value level-target">${signal.target}</span>
                </div>
                <div class="sig-modal-stat">
                    <span class="sig-modal-stat-label">Stop</span>
                    <span class="sig-modal-stat-value level-stop">${signal.stop}</span>
                </div>
            </div>

            <!-- ── Confidence bar ── -->
            <div class="sig-sentiment-row">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span style="color:#6b7280;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;">SMC Confidence</span>
                    <span style="color:${confColor};font-size:13px;font-weight:700;">${conf}% — ${confLabel}</span>
                </div>
                <div style="height:7px;background:#1f2937;border-radius:4px;overflow:hidden;">
                    <div style="width:${confBarWidth}%;height:100%;background:linear-gradient(90deg,${confColor}99,${confColor});border-radius:4px;"></div>
                </div>
            </div>

            <!-- ── PRO Chart (Image 3) ── -->
            <div style="position:relative;border-radius:10px;overflow:hidden;border:1px solid #1f2937;margin-bottom:16px;">
                <div id="sig-chart-loading" style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:400px;background:#0a0a0f;color:#6b7280;">
                    <div class="spinner" style="margin-bottom:12px;"></div>
                    <div style="font-size:13px;">Building Market Chart…</div>
                </div>
                <div id="modal-chart-container" style="width:100%;height:400px;display:none;"></div>
            </div>

            <!-- ── Trade Idea section ── -->
            <div class="sig-trade-idea">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap;">
                    <span style="color:white;font-size:18px;font-weight:700;">Trade Idea</span>
                    <div class="sig-brand-icon"><i class="fas fa-chart-line"></i></div>
                    ${isActive ? '<span class="sig-live-trade">LIVE TRADE</span>' : ''}
                </div>
                <div style="color:#6b7280;font-size:12px;margin-bottom:16px;">
                    Published: ${publishedAt}
                    ${signal.expires_at ? ' &nbsp;·&nbsp; Expires: ' + expiresAt : ''}
                    &nbsp;·&nbsp; ${signal.timeframe || 'M5'} timeframe
                </div>

                ${(() => {
                    const paras = description.split('\n\n').filter(p => p.trim());
                    const body  = paras.slice(0, -1);
                    const watch = paras[paras.length - 1] || '';
                    // Render body paragraphs
                    const bodyHtml = body.map(p =>
                        `<p style="color:#d1d5db;font-size:14px;line-height:1.75;margin:0 0 12px 0;">${p}</p>`
                    ).join('');
                    // Render Watch section — split by newline and style each ✅ ⚠️ 💡 line
                    const watchLines = watch.split('\n').filter(l => l.trim());
                    const watchHtml = watchLines.length ? `
                        <div style="margin-top:16px;background:#0f1117;border:1px solid #1f2937;border-radius:10px;padding:14px;">
                            <div style="color:#6b7280;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">What To Watch</div>
                            ${watchLines.map(line => {
                                const isGood = line.startsWith('✅');
                                const isWarn = line.startsWith('⚠');
                                const isTip  = line.startsWith('💡');
                                const icon   = isGood ? '✅' : isWarn ? '⚠️' : isTip ? '💡' : '•';
                                const col    = isGood ? '#22c55e' : isWarn ? '#f59e0b' : isTip ? '#818cf8' : '#9ca3af';
                                const bg     = isGood ? 'rgba(34,197,94,0.07)' : isWarn ? 'rgba(245,158,11,0.07)' : isTip ? 'rgba(129,140,248,0.07)' : 'transparent';
                                const text   = line.replace(/^[✅⚠️💡•]\s*/, '').trim();
                                return `<div style="display:flex;gap:10px;align-items:flex-start;padding:9px 10px;background:${bg};border-radius:7px;margin-bottom:6px;">
                                    <span style="font-size:14px;flex-shrink:0;line-height:1.5;">${icon}</span>
                                    <span style="color:#d1d5db;font-size:13px;line-height:1.6;">${text}</span>
                                </div>`;
                            }).join('')}
                        </div>` : '';
                    return bodyHtml + watchHtml;
                })()}

                ${rr ? `<div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap;">
                    <span class="badge badge-success">R:R ${rr.toFixed(1)}</span>
                    <span class="pattern-badge">${pattern}</span>
                    <span class="timeframe-badge">${signal.timeframe || 'M5'}</span>
                </div>` : ''}
            </div>

            <!-- ── #12: SMC Confluence panel ── -->
            ${(signal.bias_d1 || signal.bias_h4 || signal.bos_m5) ? `
            <div style="background:#0f1117;border:1px solid #1f2937;border-radius:10px;padding:14px;margin-top:12px;">
                <div style="color:#6b7280;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">SMC Confluence</div>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
                    <div style="text-align:center;padding:8px;background:rgba(31,41,55,0.5);border-radius:8px;">
                        <div style="color:#6b7280;font-size:10px;margin-bottom:4px;">D1 Bias</div>
                        <div style="font-size:13px;font-weight:700;color:${signal.bias_d1==='BULL'?'#22c55e':signal.bias_d1==='BEAR'?'#ef4444':'#9ca3af'};">${signal.bias_d1||'—'}</div>
                    </div>
                    <div style="text-align:center;padding:8px;background:rgba(31,41,55,0.5);border-radius:8px;">
                        <div style="color:#6b7280;font-size:10px;margin-bottom:4px;">H4 Bias</div>
                        <div style="font-size:13px;font-weight:700;color:${signal.bias_h4==='BULL'?'#22c55e':signal.bias_h4==='BEAR'?'#ef4444':'#9ca3af'};">${signal.bias_h4||'—'}</div>
                    </div>
                    <div style="text-align:center;padding:8px;background:rgba(31,41,55,0.5);border-radius:8px;">
                        <div style="color:#6b7280;font-size:10px;margin-bottom:4px;">M5 BOS</div>
                        <div style="font-size:13px;font-weight:700;color:${signal.bos_m5==='UP'?'#22c55e':signal.bos_m5==='DOWN'?'#ef4444':'#9ca3af'};">${signal.bos_m5||'—'}</div>
                    </div>
                </div>
            </div>` : ''}`;

        // Show modal
        const modal = document.getElementById('signalModal');
        if (modal) { modal.classList.remove('hidden'); modal.classList.add('flex'); }
    }

    closeModal() {
        const modal = document.getElementById('signalModal');
        if (modal) { modal.classList.add('hidden'); modal.classList.remove('flex'); }
        if (window.ProChart) window.ProChart.destroy();
    }
}

// ── Bootstrap ──────────────────────────────────────────────────────────────────
const enhancedSignals = new EnhancedSignalsPage();
window.enhancedSignals = enhancedSignals;
console.log('[EnhancedSignals] Module loaded v21.0');


// ═══════════════════════════════════════════════════════════════════════════════
// SECTION 2 — ProChart IIFE
// Modal-level PRO renderer. All internals private.
// Public API exposed on window.ProChart
// ═══════════════════════════════════════════════════════════════════════════════

(function () {
    'use strict';

    // #18: jsdelivr CDN (more reliable than unpkg) — pin exact version
    var LIGHTWEIGHT_CHARTS_CDN = 'https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js';
    var LightweightCharts = null;
    var chartInstance     = null;
    var candlestickSeries = null;

    // ── Pattern Definitions ────────────────────────────────────────────────────

    var PATTERNS = {
        'ASCENDING_TRIANGLE':   { name: 'Ascending Triangle',   icon: '▲', structure: 'horizontal_top'      },
        'DESCENDING_TRIANGLE':  { name: 'Descending Triangle',  icon: '▼', structure: 'horizontal_bottom'   },
        'SYMMETRICAL_TRIANGLE': { name: 'Symmetrical Triangle', icon: '◊', structure: 'converging'          },
        'RISING_WEDGE':         { name: 'Rising Wedge',         icon: '⚠', structure: 'converging_rising'   },
        'FALLING_WEDGE':        { name: 'Falling Wedge',        icon: '⚡', structure: 'converging_falling' },
        'BULL_FLAG':            { name: 'Bull Flag',            icon: '🚩', structure: 'parallel_down'      },
        'BEAR_FLAG':            { name: 'Bear Flag',            icon: '🏴', structure: 'parallel_up'        },
        'ASCENDING_CHANNEL':    { name: 'Ascending Channel',    icon: '📈', structure: 'parallel_rising'    },
        'DESCENDING_CHANNEL':   { name: 'Descending Channel',   icon: '📉', structure: 'parallel_falling'   },
        'DOUBLE_TOP':           { name: 'Double Top',           icon: 'M',  structure: 'double_peak'         },
        'DOUBLE_BOTTOM':        { name: 'Double Bottom',        icon: 'W',  structure: 'double_trough'       },
        'BREAKOUT':             { name: 'Breakout Setup',       icon: '💥', structure: 'breakout'           }
    };

    // ── Trade State Engine ─────────────────────────────────────────────────────

    function determineTradeState(signal, currentPrice) {
        var entry  = parseFloat(signal.entry)  || 0;
        var target = parseFloat(signal.target) || 0;
        var stop   = parseFloat(signal.stop)   || 0;
        var isBuy  = (signal.direction || '').toUpperCase().indexOf('BUY') !== -1;

        if (!entry || !currentPrice) {
            return { state: 'UNKNOWN', label: 'Unknown', color: '#6b7280', icon: '?', bg: 'rgba(107,114,128,0.2)' };
        }

        if (isBuy) {
            if (currentPrice >= target) return { state: 'TARGET_HIT', label: 'TARGET HIT',  color: '#00ff88', icon: '✓', bg: 'rgba(0,255,136,0.2)'  };
            if (currentPrice <= stop)   return { state: 'STOPPED',    label: 'STOPPED OUT', color: '#ff4757', icon: '✗', bg: 'rgba(255,71,87,0.2)'   };
            if (currentPrice >= entry)  return { state: 'ACTIVE',     label: 'LIVE TRADE',  color: '#00c9a7', icon: '●', bg: 'rgba(0,201,167,0.2)'   };
            return                             { state: 'PENDING',    label: 'BUY STOP',    color: '#f5a623', icon: '◐', bg: 'rgba(245,166,35,0.2)'  };
        } else {
            if (currentPrice <= target) return { state: 'TARGET_HIT', label: 'TARGET HIT',  color: '#00ff88', icon: '✓', bg: 'rgba(0,255,136,0.2)'  };
            if (currentPrice >= stop)   return { state: 'STOPPED',    label: 'STOPPED OUT', color: '#ff4757', icon: '✗', bg: 'rgba(255,71,87,0.2)'   };
            if (currentPrice <= entry)  return { state: 'ACTIVE',     label: 'LIVE TRADE',  color: '#00c9a7', icon: '●', bg: 'rgba(0,201,167,0.2)'   };
            return                             { state: 'PENDING',    label: 'SELL STOP',   color: '#f5a623', icon: '◐', bg: 'rgba(245,166,35,0.2)'  };
        }
    }

    // ── Swing Point Detection ──────────────────────────────────────────────────

    function findSwingPoints(candles, strength) {
        strength = strength || 3;
        if (!candles || candles.length < 5) return { highs: [], lows: [] };
        var highs = [], lows = [];
        for (var i = strength; i < candles.length - strength; i++) {
            var c = candles[i];
            var isHigh = true, isLow = true;
            for (var j = 1; j <= strength; j++) {
                if (candles[i-j].high >= c.high || candles[i+j].high >= c.high) isHigh = false;
                if (candles[i-j].low  <= c.low  || candles[i+j].low  <= c.low)  isLow  = false;
            }
            if (isHigh) highs.push({ time: c.time, price: c.high, idx: i });
            if (isLow)  lows.push( { time: c.time, price: c.low,  idx: i });
        }
        return { highs: highs, lows: lows };
    }

    // ── Line Helper ────────────────────────────────────────────────────────────

    function addLine(chart, data, color, width, style) {
        var s = chart.addLineSeries({ color: color, lineWidth: width, lineStyle: style, lastValueVisible: false });
        s.setData(data);
        return s;
    }

    // ── Pattern Structure Renderers ────────────────────────────────────────────

    function drawPatternStructure(chart, candles, pattern, signal) {
        if (!chart || !candles || candles.length < 10) return;
        var expired = isSignalExpired(signal);
        var color   = expired ? 'rgba(148,163,184,0.5)' : '#00e5ff';
        var width   = expired ? 1 : 3;
        var LC      = LightweightCharts;

        // ── #11 PATH A: Bot-provided explicit lines (authoritative — draw verbatim) ──
        if (signal.pattern_lines && Array.isArray(signal.pattern_lines) && signal.pattern_lines.length > 0) {
            var ROLE_COLORS = {
                'resistance': expired ? 'rgba(239,68,68,0.4)'  : '#ef4444',
                'support':    expired ? 'rgba(34,197,94,0.4)'  : '#22c55e',
                'neckline':   expired ? 'rgba(251,191,36,0.4)' : '#fbbf24',
                'projection': expired ? 'rgba(99,102,241,0.4)' : '#818cf8',
                'default':    color
            };
            var STYLE_MAP = { 'solid': LC.LineStyle.Solid, 'dashed': LC.LineStyle.Dashed, 'dotted': LC.LineStyle.Dotted };
            // Clamp timestamps to candle range — LightweightCharts silently drops out-of-range points
            var minT = candles[0].time;
            var maxT = candles[candles.length-1].time + (candles[candles.length-1].time - candles[0].time) * 0.5;
            var clamp = function(t) { return Math.min(Math.max(t, minT), maxT); };
            signal.pattern_lines.forEach(function(line) {
                if (!line.p1 || !line.p2) return;
                var lc = ROLE_COLORS[line.role] || ROLE_COLORS['default'];
                var ls = STYLE_MAP[line.style]  || LC.LineStyle.Solid;
                var lw = (line.role === 'projection') ? 1 : (expired ? 1 : 2);
                addLine(chart, [
                    { time: clamp(line.p1.time), value: line.p1.price },
                    { time: clamp(line.p2.time), value: line.p2.price }
                ], lc, lw, ls);
            });
            return;
        }

        // ── PATH B: Bot-provided pivot points — connect them directly (semi-real) ──
        if (signal.pattern_points && Array.isArray(signal.pattern_points) && signal.pattern_points.length >= 2) {
            var sorted = signal.pattern_points.slice().sort(function(a,b){ return a.time - b.time; });
            for (var i = 0; i < sorted.length - 1; i++) {
                addLine(chart, [{ time: sorted[i].time, value: sorted[i].price }, { time: sorted[i+1].time, value: sorted[i+1].price }], color, width, LC.LineStyle.Solid);
            }
            return;
        }

        // ── PATH C: Swing detection on real candles (fallback only) ──
        // Only reaches here when both pattern_lines and pattern_points are absent.
        var sw      = findSwingPoints(candles);
        var highs   = sw.highs;
        var lows    = sw.lows;
        var key     = (pattern || '').toUpperCase().replace(/\s+/g, '_');
        var patDef  = PATTERNS[key] || PATTERNS['BREAKOUT'];

        switch (patDef.structure) {
            case 'horizontal_top':
                drawAscendingTriangle(chart, candles, highs, lows, color, width, LC); break;
            case 'horizontal_bottom':
                drawDescendingTriangle(chart, candles, highs, lows, color, width, LC); break;
            case 'converging':
            case 'converging_rising':
            case 'converging_falling':
                drawConvergingPattern(chart, candles, highs, lows, color, width, signal, LC); break;
            case 'parallel_down':
            case 'parallel_up':
            case 'parallel_rising':
            case 'parallel_falling':
                drawChannelPattern(chart, candles, highs, lows, color, width, signal, LC); break;
            case 'double_peak':
            case 'double_trough':
                drawDoublePattern(chart, candles, highs, lows, color, width, patDef.structure, LC); break;
            default:
                drawAutoTrendlines(chart, candles, highs, lows, color, width, LC);
        }
    }

    function drawAscendingTriangle(chart, candles, highs, lows, color, width, LC) {
        var rh = highs.slice(-3); if (rh.length < 2) return;
        var rl = lows.slice(-3);  if (rl.length < 2) return;
        var topLevel = Math.min.apply(null, rh.map(function(h){ return h.price; }));
        addLine(chart, [{ time: rh[0].time, value: topLevel }, { time: candles[candles.length-1].time, value: topLevel }], color, width, LC.LineStyle.Solid);
        addLine(chart, [{ time: rl[0].time, value: rl[0].price }, { time: rl[rl.length-1].time, value: rl[rl.length-1].price }], color, width, LC.LineStyle.Solid);
    }

    function drawDescendingTriangle(chart, candles, highs, lows, color, width, LC) {
        var rl = lows.slice(-3);  if (rl.length < 2) return;
        var rh = highs.slice(-3); if (rh.length < 2) return;
        var bottomLevel = Math.max.apply(null, rl.map(function(l){ return l.price; }));
        addLine(chart, [{ time: rl[0].time, value: bottomLevel }, { time: candles[candles.length-1].time, value: bottomLevel }], color, width, LC.LineStyle.Solid);
        addLine(chart, [{ time: rh[0].time, value: rh[0].price }, { time: rh[rh.length-1].time, value: rh[rh.length-1].price }], color, width, LC.LineStyle.Solid);
    }

    function drawConvergingPattern(chart, candles, highs, lows, color, width, signal, LC) {
        if (highs.length < 2 || lows.length < 2) { drawAutoTrendlines(chart, candles, highs, lows, color, width, LC); return; }
        var entryT = getEntryTime(signal, candles);
        var entryP = parseFloat(signal.entry) || 0;
        var sH = highs[highs.length-2];
        var sL = lows[lows.length-2];
        addLine(chart, [{ time: sH.time, value: sH.price }, { time: entryT, value: entryP }], color, width, LC.LineStyle.Solid);
        addLine(chart, [{ time: sL.time, value: sL.price }, { time: entryT, value: entryP }], color, width, LC.LineStyle.Solid);
    }

    function drawChannelPattern(chart, candles, highs, lows, color, width, signal, LC) {
        var uh = highs.slice(-2); var ul = lows.slice(-2);
        if (uh.length < 2 || ul.length < 2) { drawAutoTrendlines(chart, candles, highs, lows, color, width, LC); return; }
        var entryT = getEntryTime(signal, candles);
        addLine(chart, [{ time: uh[0].time, value: uh[0].price }, { time: entryT, value: uh[1].price }], color, width, LC.LineStyle.Solid);
        addLine(chart, [{ time: ul[0].time, value: ul[0].price }, { time: entryT, value: ul[1].price }], color, width, LC.LineStyle.Solid);
    }

    function drawDoublePattern(chart, candles, highs, lows, color, width, structure, LC) {
        var isPeak = structure === 'double_peak';
        var pts    = isPeak ? highs.slice(-2) : lows.slice(-2);
        if (pts.length < 2) return;
        var neckLevel = isPeak
            ? Math.min.apply(null, lows.slice(-2).map(function(l){ return l.price; }))
            : Math.max.apply(null, highs.slice(-2).map(function(h){ return h.price; }));
        addLine(chart, [{ time: pts[0].time, value: neckLevel }, { time: candles[candles.length-1].time, value: neckLevel }], color, width, LC.LineStyle.Dashed);
    }

    function drawAutoTrendlines(chart, candles, highs, lows, color, width, LC) {
        // For Breakout/default — draw a flat horizontal key level at the most recent swing high
        // (the level price broke through). This is more meaningful than random diagonal lines.
        if (!candles || candles.length < 5) return;
        var lastTime = candles[candles.length-1].time;
        var firstZoneTime = candles[Math.floor(candles.length * 0.5)].time;

        if (highs.length >= 1) {
            // Flat resistance — the level that was broken
            var resistanceLevel = highs[highs.length-1].price;
            addLine(chart, [
                { time: firstZoneTime, value: resistanceLevel },
                { time: lastTime,      value: resistanceLevel }
            ], color, width, LC.LineStyle.Dashed);
        }
        if (lows.length >= 1) {
            // Flat support — the floor holding price up
            var supportLevel = lows[lows.length-1].price;
            addLine(chart, [
                { time: firstZoneTime, value: supportLevel },
                { time: lastTime,      value: supportLevel }
            ], color, width, LC.LineStyle.Dashed);
        }
    }

    // ── Curved Projection ──────────────────────────────────────────────────────

    function drawCurvedProjection(chart, candles, signal, tradeState) {
        if (!chart || !candles || candles.length < 5) return;
        var entry  = parseFloat(signal.entry)  || 0;
        var target = parseFloat(signal.target) || 0;
        if (!entry || !target) return;
        var LC       = LightweightCharts;
        var lastTime = candles[candles.length-1].time;
        var spanFwd  = (lastTime - candles[0].time) * 0.3;
        var steps    = 20;
        var data     = [];
        for (var i = 0; i <= steps; i++) {
            var t     = i / steps;
            var time  = Math.floor(lastTime + spanFwd * t);
            var price;
            if (tradeState.state === 'TARGET_HIT') {
                price = entry + (target - entry) * (1 - Math.pow(1-t, 3));
            } else if (tradeState.state === 'ACTIVE') {
                var curve = t;
                if (t > 0.2 && t < 0.4) curve = t - 0.05 * Math.sin((t-0.2) * Math.PI / 0.2);
                price = entry + (target - entry) * curve;
            } else {
                price = t < 0.3 ? entry : entry + (target - entry) * ((t-0.3)/0.7);
            }
            data.push({ time: time, value: price });
        }
        addLine(chart, data,
            tradeState.state === 'TARGET_HIT' ? '#00ff88' : 'rgba(0,201,167,0.6)',
            2, LC.LineStyle.Dotted);
    }

    // ── Premium Zones (histogram-based — proper solid filled rectangles) ─────────
    //
    // LightweightCharts addHistogramSeries with `base` draws a solid filled bar
    // between `base` (entry price) and `value` (target or stop price) at every
    // time point — this is the correct API for filled price zones.
    //
    // Reference chart appearance (images 3,4,5):
    //   - Dark teal/green solid fill between ENTRY and TARGET
    //   - Dark red solid fill between STOP and ENTRY
    //   - Bright border lines at TOP and BOTTOM of each zone
    //   - Vertical dashed line at the signal entry bar

    function drawPremiumZones(chart, candles, signal, tradeState) {
        if (!chart || !candles || candles.length < 5) return;
        var LC     = LightweightCharts;
        var entry  = parseFloat(signal.entry)  || 0;
        var target = parseFloat(signal.target) || 0;
        var stop   = parseFloat(signal.stop)   || 0;
        var isBuy  = (signal.direction || '').toUpperCase().indexOf('BUY') !== -1;
        if (!entry || !target || !stop) return;

        var isExpired = tradeState.state === 'STOPPED' || isSignalExpired(signal);

        // Find which candles fall within the zone window (from signal creation onward)
        var startTime = signal.created_at
            ? Math.floor(new Date(signal.created_at).getTime() / 1000)
            : candles[Math.floor(candles.length * 0.65)].time;
        startTime = Math.max(startTime, candles[0].time);

        // Use ACTUAL candle timestamps so histogram bars exactly match candle width — no gaps
        var zoneCandles = candles.filter(function(c) { return c.time >= startTime; });
        if (zoneCandles.length < 2) {
            // Fallback: use last 30% of candles
            zoneCandles = candles.slice(Math.floor(candles.length * 0.7));
        }

        // Project forward — add ~12 future bars at the same interval
        var interval = candles.length > 1
            ? candles[candles.length-1].time - candles[candles.length-2].time
            : 300;
        var lastT = candles[candles.length-1].time;
        var futureTimes = [];
        for (var f = 1; f <= 12; f++) {
            futureTimes.push(lastT + interval * f);
        }

        // All time points: real candles in zone + future projection bars
        var allTimes = zoneCandles.map(function(c) { return c.time; }).concat(futureTimes);

        // Strong colors matching reference images (dark filled rectangles)
        var profitFill   = isExpired ? 'rgba(0,120,90,0.30)'  : 'rgba(0,150,110,0.38)';
        var profitBorder = isExpired ? 'rgba(0,180,120,0.50)' : '#00d084';
        var riskFill     = isExpired ? 'rgba(140,20,20,0.28)' : 'rgba(180,30,30,0.38)';
        var riskBorder   = isExpired ? 'rgba(200,50,50,0.50)' : '#ff4757';

        if (isBuy) {
            drawSolidZone(chart, LC, allTimes, entry, target, profitFill, profitBorder);
            drawSolidZone(chart, LC, allTimes, stop,  entry,  riskFill,   riskBorder);
        } else {
            drawSolidZone(chart, LC, allTimes, target, entry, profitFill, profitBorder);
            drawSolidZone(chart, LC, allTimes, entry,  stop,  riskFill,   riskBorder);
        }

        // Vertical dashed line at signal entry bar
        var entryBarTime = Math.max(startTime, candles[0].time);
        var priceRange   = Math.abs(target - stop);
        addLine(chart, [
            { time: entryBarTime, value: Math.min(entry, stop)   - priceRange * 0.05 },
            { time: entryBarTime, value: Math.max(entry, target) + priceRange * 0.05 }
        ], 'rgba(200,200,200,0.40)', 1, LC.LineStyle.Dashed);
    }

    function drawSolidZone(chart, LC, timePoints, bottomPrice, topPrice, fillColor, borderColor) {
        if (!timePoints || timePoints.length < 2) return;
        if (topPrice <= bottomPrice) return;

        // addHistogramSeries with base=bottomPrice draws solid bars from bottomPrice to value (topPrice)
        // Using actual candle timestamps means bar width matches candle width — no gaps, solid fill
        var hist = chart.addHistogramSeries({
            color:            fillColor,
            base:             bottomPrice,
            priceLineVisible: false,
            lastValueVisible: false,
            priceScaleId:     'right',
        });
        hist.setData(timePoints.map(function(t) {
            return { time: t, value: topPrice };
        }));

        // Border lines — solid top, slightly thinner bottom
        addLine(chart, [
            { time: timePoints[0], value: topPrice },
            { time: timePoints[timePoints.length-1], value: topPrice }
        ], borderColor, 2, LC.LineStyle.Solid);

        addLine(chart, [
            { time: timePoints[0], value: bottomPrice },
            { time: timePoints[timePoints.length-1], value: bottomPrice }
        ], borderColor, 1, LC.LineStyle.Solid);
    }

    // ── Price Lines ────────────────────────────────────────────────────────────

    function drawPremiumPriceLevels(series, entry, target, stop, tradeState) {
        if (!series) return;
        var LC      = LightweightCharts;
        var expired = tradeState.state === 'STOPPED' || tradeState.state === 'TARGET_HIT';
        if (entry) {
            series.createPriceLine({ price: entry, color: expired ? '#666' : '#ffffff', lineWidth: 3, lineStyle: LC.LineStyle.Solid, axisLabelVisible: true, title: tradeState.state === 'PENDING' ? tradeState.label : 'ENTRY' });
        }
        if (target) {
            var tHit = tradeState.state === 'TARGET_HIT';
            series.createPriceLine({ price: target, color: tHit ? '#00ff88' : (expired ? '#2d4a3e' : '#00ff88'), lineWidth: tHit ? 4 : 2, lineStyle: tHit ? LC.LineStyle.Solid : LC.LineStyle.Dashed, axisLabelVisible: true, title: tHit ? '✓ TARGET HIT' : 'TARGET' });
        }
        if (stop) {
            var sHit = tradeState.state === 'STOPPED';
            series.createPriceLine({ price: stop, color: sHit ? '#ff4757' : (expired ? '#4a2d2d' : '#ff4757'), lineWidth: sHit ? 4 : 2, lineStyle: sHit ? LC.LineStyle.Solid : LC.LineStyle.Dashed, axisLabelVisible: true, title: sHit ? '✗ STOPPED' : 'STOP' });
        }
    }

    // ── DOM Overlays ───────────────────────────────────────────────────────────

    function addStatusBadge(container, tradeState) {
        var old = container.querySelector('.pro-status-badge');
        if (old) old.parentNode.removeChild(old);
        var b = document.createElement('div');
        b.className = 'pro-status-badge';
        b.style.cssText = 'position:absolute;top:14px;right:14px;background:rgba(10,10,15,0.95);border:1px solid ' + tradeState.color + '40;border-radius:8px;padding:7px 14px;display:flex;align-items:center;gap:8px;font-weight:700;font-size:12px;text-transform:uppercase;letter-spacing:.5px;z-index:100;backdrop-filter:blur(8px);box-shadow:0 4px 20px ' + tradeState.color + '20;';
        b.innerHTML = '<span style="color:' + tradeState.color + '">' + tradeState.icon + '</span><span style="color:' + tradeState.color + '">' + tradeState.label + '</span>';
        container.appendChild(b);
    }

    function addAIOverlay(container, signal, tradeState) {
        var old = container.querySelector('.pro-ai-overlay');
        if (old) old.parentNode.removeChild(old);
        var pattern = signal.pattern_name || signal.pattern;
        if (!pattern) return;
        var isBuy = (signal.direction || '').toUpperCase().indexOf('BUY') !== -1;
        var analyses = {
            'PENDING':    isBuy ? ('Waiting for breakout above ' + signal.entry) : ('Waiting for breakdown below ' + signal.entry),
            'ACTIVE':     'Momentum building toward ' + signal.target + ' target',
            'TARGET_HIT': 'Target reached successfully',
            'STOPPED':    'Trade stopped at loss level'
        };
        var ov = document.createElement('div');
        ov.className = 'pro-ai-overlay';
        ov.style.cssText = 'position:absolute;bottom:14px;left:14px;background:linear-gradient(135deg,rgba(99,102,241,0.2),rgba(79,70,229,0.1));border:1px solid rgba(99,102,241,0.3);border-radius:8px;padding:10px 14px;z-index:100;backdrop-filter:blur(8px);';
        ov.innerHTML = '<div style="font-size:11px;font-weight:700;color:#818cf8;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">' + pattern + '</div><div style="font-size:12px;color:#e0e7ff;font-weight:500;">' + (analyses[tradeState.state] || '') + '</div>';
        container.appendChild(ov);
    }

    // ── Candle Validation & Fallback ───────────────────────────────────────────

    function validateAndFixCandles(signal) {
        if (signal.candles && Array.isArray(signal.candles) && signal.candles.length >= 20) return signal.candles;
        if (signal.pattern_points && Array.isArray(signal.pattern_points) && signal.pattern_points.length >= 2) return generateCandlesFromPoints(signal);
        return generateRealisticCandles(signal);
    }

    function generateRealisticCandles(signal) {
        var entry  = parseFloat(signal.entry)  || 100;
        var target = parseFloat(signal.target) || entry * 1.02;
        var stop   = parseFloat(signal.stop)   || entry * 0.98;
        var isBuy  = (signal.direction || '').toUpperCase().indexOf('BUY') !== -1;
        var range  = Math.max(Math.abs(target-entry), Math.abs(entry-stop));
        var vol    = range * 0.15;
        var now    = Math.floor(Date.now() / 1000);
        var intv   = 300;
        var price  = isBuy ? entry - range*0.5 : entry + range*0.5;
        var seed   = signal.id || 12345;
        var rnd    = function() { seed = (seed*9301+49297)%233280; return seed/233280; };
        var candles = [];
        for (var i = 80; i >= 0; i--) {
            var time    = now - (i*intv);
            var prog    = (80-i)/80;
            var isGreen = rnd() < (isBuy ? 0.6 : 0.4) + prog*0.1;
            var body    = vol*(0.3+rnd()*0.7);
            var wick    = vol*rnd()*0.4;
            var open    = price;
            var close   = isGreen ? open+body : open-body;
            candles.push({ time: time, open: +open.toFixed(5), high: +(Math.max(open,close)+wick).toFixed(5), low: +(Math.min(open,close)-wick).toFixed(5), close: +close.toFixed(5) });
            price = close + (rnd()-0.5)*vol*0.1;
        }
        var adj = entry - candles[candles.length-1].close;
        for (var k = candles.length-15; k < candles.length; k++) {
            var f = (k-(candles.length-15))/15;
            candles[k].open  = +(candles[k].open  + adj*f).toFixed(5);
            candles[k].high  = +(candles[k].high  + adj*f).toFixed(5);
            candles[k].low   = +(candles[k].low   + adj*f).toFixed(5);
            candles[k].close = +(candles[k].close + adj*f).toFixed(5);
        }
        return candles;
    }

    // #13: Use same seeded LCG as generateRealisticCandles — chart stable across refreshes
    function generateCandlesFromPoints(signal) {
        var pts  = signal.pattern_points || [];
        var base = pts[0] ? pts[0].price : (parseFloat(signal.entry) || 100);
        var now  = Math.floor(Date.now() / 1000);
        var intv = 300;
        var seed = (signal.id || 99999) + 1;
        var rnd  = function() { seed = (seed*9301+49297)%233280; return seed/233280; };
        var candles = [];
        for (var i = 60; i >= 0; i--) {
            var time  = now - (i*intv);
            var v     = base * 0.002;
            var open  = base  + (rnd()-0.5)*v;
            var close = open  + (rnd()-0.5)*v;
            candles.push({ time: time, open: +open.toFixed(5), high: +(Math.max(open,close)+rnd()*v*0.5).toFixed(5), low: +(Math.min(open,close)-rnd()*v*0.5).toFixed(5), close: +close.toFixed(5) });
            base = close;
        }
        return candles;
    }

    // ── Utilities ──────────────────────────────────────────────────────────────

    function isSignalExpired(signal) {
        if (!signal.expires_at) return false;
        return new Date(signal.expires_at) < new Date();
    }

    function getEntryTime(signal, candles) {
        if (signal.breakout_point && signal.breakout_point.time) return signal.breakout_point.time;
        if (candles && candles.length > 5) return candles[candles.length-3].time;
        return Math.floor(Date.now() / 1000);
    }

    function loadLightweightCharts() {
        if (LightweightCharts) return Promise.resolve(LightweightCharts);
        if (window.LightweightCharts) { LightweightCharts = window.LightweightCharts; return Promise.resolve(LightweightCharts); }
        return new Promise(function(resolve, reject) {
            var s   = document.createElement('script');
            s.src   = LIGHTWEIGHT_CHARTS_CDN;
            s.onload  = function() { LightweightCharts = window.LightweightCharts; resolve(LightweightCharts); };
            s.onerror = function() { reject(new Error('Failed to load LightweightCharts CDN')); };
            document.head.appendChild(s);
        });
    }

    // ── Main Chart Creation ────────────────────────────────────────────────────

    function createProChart(containerId, signal) {
        return loadLightweightCharts().then(function() {
            var container = document.getElementById(containerId);
            if (!container) throw new Error('Container #' + containerId + ' not found');

            if (chartInstance) { chartInstance.remove(); chartInstance = null; candlestickSeries = null; }

            // #14: Always render chart — pattern gates only the structure drawing, not the chart itself
            var patternName = signal.pattern_name || signal.pattern || 'Breakout';

            var candles = validateAndFixCandles(signal);
            if (!candles || candles.length < 10) {
                container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#6b7280;">Insufficient chart data</div>';
                return;
            }

            var currentPrice = candles[candles.length-1].close;
            var tradeState   = determineTradeState(signal, currentPrice);
            var isExpired    = tradeState.state === 'STOPPED' || isSignalExpired(signal);
            var LC           = LightweightCharts;

            chartInstance = LC.createChart(container, {
                width:  container.clientWidth,
                height: container.clientHeight,
                layout: {
                    background:  { type: 'solid', color: '#0a0a0f' },
                    textColor:   isExpired ? '#4b5563' : '#9ca3af',
                    fontFamily:  "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
                },
                grid: {
                    vertLines: { color: 'rgba(255,255,255,0.03)' },
                    horzLines: { color: 'rgba(255,255,255,0.03)' }
                },
                crosshair: {
                    mode: LC.CrosshairMode.Normal,
                    vertLine: { color: 'rgba(99,102,241,0.5)', width: 1, style: LC.LineStyle.Dashed, labelBackgroundColor: '#1e1b4b' },
                    horzLine: { color: 'rgba(99,102,241,0.5)', width: 1, style: LC.LineStyle.Dashed, labelBackgroundColor: '#1e1b4b' }
                },
                rightPriceScale: { borderColor: 'rgba(255,255,255,0.1)', scaleMargins: { top: 0.12, bottom: 0.22 } },
                timeScale:       { borderColor: 'rgba(255,255,255,0.1)', timeVisible: true, secondsVisible: false }
            });

            // Draw zones FIRST so candlesticks render on top (z-order matters)
            drawPremiumZones(chartInstance, candles, signal, tradeState);

            candlestickSeries = chartInstance.addCandlestickSeries({
                upColor:         isExpired ? '#065f46' : '#26a69a',
                downColor:       isExpired ? '#7f1d1d' : '#ef5350',
                borderUpColor:   isExpired ? '#065f46' : '#26a69a',
                borderDownColor: isExpired ? '#7f1d1d' : '#ef5350',
                wickUpColor:     isExpired ? '#065f46' : '#26a69a',
                wickDownColor:   isExpired ? '#7f1d1d' : '#ef5350',
            });
            candlestickSeries.setData(candles);

            drawPatternStructure(chartInstance, candles, patternName, signal);
            drawCurvedProjection(chartInstance, candles, signal, tradeState);
            drawPremiumPriceLevels(candlestickSeries,
                parseFloat(signal.entry), parseFloat(signal.target), parseFloat(signal.stop), tradeState);

            container.style.position = 'relative';
            addStatusBadge(container, tradeState);
            addAIOverlay(container, signal, tradeState);

            // Zoom to last 60 candles so entry zone is prominent, not tiny
            var totalBars = candles.length;
            var showBars  = Math.min(60, totalBars);
            chartInstance.timeScale().setVisibleLogicalRange({
                from: totalBars - showBars,
                to:   totalBars + 6   // 6 future bars for projection
            });

            var ro = new ResizeObserver(function(entries) {
                if (chartInstance && entries[0]) chartInstance.resize(entries[0].contentRect.width, entries[0].contentRect.height);
            });
            ro.observe(container);

            console.log('[ProChart] ' + patternName + ' | ' + tradeState.label + ' | ' + candles.length + ' candles');
        });
    }

    // ── Public API ─────────────────────────────────────────────────────────────

    window.ProChart = {
        create:          createProChart,
        destroy:         function() { if (chartInstance) { chartInstance.remove(); chartInstance = null; candlestickSeries = null; } },
        ensureLoaded:    loadLightweightCharts,
        validateCandles: validateAndFixCandles,
        tradeState:      determineTradeState,
        patterns:        PATTERNS
    };

    console.log('[ProChart] IIFE registered v21.0');

})();
