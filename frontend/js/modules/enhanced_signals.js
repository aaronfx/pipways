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
        this.charts           = new Map(); // signalId → LightweightCharts instance (grid)
        this.signals          = [];
        this.activeTab        = 'ai';
        this._refreshInterval = null;
        console.log('[EnhancedSignals] Instance created v21.0');
    }

    // ── Lifecycle ──────────────────────────────────────────────────────────────

    init() {
        console.log('[EnhancedSignals] init() v21.0');
        this.activeTab = 'ai';

        // Tab buttons
        const aiTab  = document.getElementById('aiDrivenTab');
        const patTab = document.getElementById('patternTab');
        if (aiTab && patTab) {
            aiTab.addEventListener('click', () => {
                this.activeTab = 'ai';
                aiTab.classList.replace('bg-gray-700', 'bg-purple-600');
                aiTab.classList.replace('text-gray-400', 'text-white');
                patTab.classList.replace('bg-purple-600', 'bg-gray-700');
                patTab.classList.replace('text-white', 'text-gray-400');
                this.loadSignals();
            });
            patTab.addEventListener('click', () => {
                this.activeTab = 'pattern';
                patTab.classList.replace('bg-gray-700', 'bg-purple-600');
                patTab.classList.replace('text-gray-400', 'text-white');
                aiTab.classList.replace('bg-purple-600', 'bg-gray-700');
                aiTab.classList.replace('text-white', 'text-gray-400');
                this.loadSignals();
            });
        }

        // Modal close — button, Escape key, backdrop click
        const closeBtn = document.getElementById('closeModal');
        if (closeBtn) closeBtn.addEventListener('click', () => this.closeModal());
        document.addEventListener('keydown', (e) => { if (e.key === 'Escape') this.closeModal(); });
        const modal = document.getElementById('signalModal');
        if (modal) modal.addEventListener('click', (e) => { if (e.target === modal) this.closeModal(); });

        this.loadSignals();
        this._refreshInterval = setInterval(() => this.loadSignals(), 30000);
    }

    destroy() {
        if (this._refreshInterval) { clearInterval(this._refreshInterval); this._refreshInterval = null; }
        this.charts.forEach(c => c.remove());
        this.charts.clear();
        if (window.ProChart) window.ProChart.destroy();
    }

    // ── Signal Loading ─────────────────────────────────────────────────────────

    async loadSignals() {
        const container = document.getElementById('enhanced-signals-container');
        if (!container) {
            console.warn('[EnhancedSignals] Container not found');
            return;
        }

        try {
            const response = await fetch('/api/signals/enhanced');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const signals = await response.json();
            this.signals  = signals || [];

            this._updateStats();

            if (this.signals.length === 0) {
                this.charts.forEach(c => c.remove());
                this.charts.clear();
                container.innerHTML = `
                    <div class="col-span-full" style="text-align:center;padding:60px 20px;">
                        <div style="font-size:48px;margin-bottom:16px;">📊</div>
                        <h3 style="color:#9ca3af;font-size:1.1rem;font-weight:600;margin-bottom:8px;">No Active Signals</h3>
                        <p style="color:#6b7280;font-size:.875rem;">Waiting for trading opportunities…</p>
                    </div>`;
                return;
            }

            const filtered = this.activeTab === 'pattern'
                ? this.signals.filter(s => s.pattern_name || s.pattern)
                : this.signals;

            // Destroy old chart instances BEFORE wiping their DOM containers
            this.charts.forEach(c => c.remove());
            this.charts.clear();

            container.innerHTML = filtered.length
                ? filtered.map(s => this.renderSignalCard(s)).join('')
                : `<div class="col-span-full" style="text-align:center;padding:40px;color:#6b7280;">
                       No pattern-based signals available.
                   </div>`;

            // Render grid charts after DOM settles; ensure LightweightCharts is loaded first
            setTimeout(async () => {
                if (window.ProChart && window.ProChart.ensureLoaded) {
                    await window.ProChart.ensureLoaded();
                }
                filtered.forEach(s => this.renderGridChart(s));
            }, 100);

        } catch (err) {
            console.error('[EnhancedSignals] Load error:', err);
            container.innerHTML = `
                <div class="col-span-full" style="padding:24px;color:#f87171;text-align:center;">
                    <i class="fas fa-exclamation-triangle" style="font-size:2rem;margin-bottom:10px;display:block;"></i>
                    Error loading signals: ${err.message}
                </div>`;
        }
    }

    // ── Stats Row ──────────────────────────────────────────────────────────────

    _updateStats() {
        const active = this.signals.filter(s => {
            const mins = (Date.now() - new Date(s.created_at).getTime()) / 60000;
            return mins < 60;
        }).length;

        const avgConf = this.signals.length
            ? Math.round(this.signals.reduce((sum, s) => sum + (s.confidence || 70), 0) / this.signals.length)
            : null;

        const rrValues = this.signals.map(s => this._calcRR(s)).filter(Boolean);
        const avgRR    = rrValues.length
            ? (rrValues.reduce((a, b) => a + b, 0) / rrValues.length).toFixed(1)
            : null;

        const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        set('enhanced-stat-active',     active);
        set('enhanced-stat-confidence', avgConf != null ? (avgConf + '%') : '—');
        set('enhanced-stat-rr',         avgRR   != null ? (avgRR + 'R')  : '—');
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

    // ── Card Rendering ─────────────────────────────────────────────────────────

    renderSignalCard(signal) {
        const pattern = signal.pattern_name || signal.pattern || 'Breakout';
        const status  = this.calculateStatus(signal);
        const rr      = this._calcRR(signal);

        return `
            <div class="signal-card-pro" data-signal-id="${signal.id}"
                 onclick="window.enhancedSignals.viewAnalysis(${signal.id})"
                 style="background:linear-gradient(135deg,#1a1f2e 0%,#0d1117 100%);
                        border:1px solid #30363d;border-radius:12px;overflow:hidden;
                        box-shadow:0 4px 20px rgba(0,0,0,0.4);cursor:pointer;
                        transition:border-color .2s,transform .2s;">

                <!-- Header -->
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:14px 16px;border-bottom:1px solid #30363d;background:rgba(0,0,0,0.3);">
                    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                        <div style="background:${signal.direction === 'BUY' ? 'rgba(0,208,132,0.2)' : 'rgba(255,71,87,0.2)'};
                                    color:${signal.direction === 'BUY' ? '#00d084' : '#ff4757'};
                                    padding:5px 11px;border-radius:6px;font-weight:700;font-size:15px;">
                            ${signal.symbol}
                        </div>
                        <div style="background:rgba(255,255,255,0.07);color:#8b949e;
                                    padding:3px 8px;border-radius:4px;font-size:11px;">
                            ${signal.timeframe || 'M5'}
                        </div>
                        ${pattern !== 'Breakout' ? `
                        <div style="background:rgba(88,166,255,0.15);color:#58a6ff;
                                    padding:3px 8px;border-radius:4px;font-size:11px;font-weight:600;">
                            ${pattern}
                        </div>` : ''}
                    </div>
                    <div style="display:flex;align-items:center;gap:8px;flex-shrink:0;">
                        <div style="background:${signal.direction === 'BUY' ? '#00d084' : '#ff4757'};
                                    color:white;padding:5px 12px;border-radius:6px;font-weight:700;font-size:13px;">
                            ${signal.direction === 'BUY' ? '▲ BUY' : '▼ SELL'}
                        </div>
                        <div style="background:${status.bg};color:${status.color};
                                    padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;">
                            ${status.icon} ${status.text}
                        </div>
                    </div>
                </div>

                <!-- Price Levels -->
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:#30363d;">
                    <div style="background:#0d1117;padding:12px;text-align:center;">
                        <div style="color:#8b949e;font-size:10px;margin-bottom:3px;text-transform:uppercase;">Entry</div>
                        <div style="color:#fff;font-weight:700;font-size:15px;font-family:monospace;">${signal.entry}</div>
                    </div>
                    <div style="background:#0d1117;padding:12px;text-align:center;">
                        <div style="color:#8b949e;font-size:10px;margin-bottom:3px;text-transform:uppercase;">Target</div>
                        <div style="color:#00d084;font-weight:700;font-size:15px;font-family:monospace;">${signal.target}</div>
                    </div>
                    <div style="background:#0d1117;padding:12px;text-align:center;">
                        <div style="color:#8b949e;font-size:10px;margin-bottom:3px;text-transform:uppercase;">Stop</div>
                        <div style="color:#ff4757;font-weight:700;font-size:15px;font-family:monospace;">${signal.stop}</div>
                    </div>
                </div>

                <!-- Lightweight grid chart — always rendered (ProChart generates fallback candles) -->
                <div style="position:relative;height:200px;background:#0a0a0f;">
                    <div id="chart-${signal.id}" style="width:100%;height:100%;"></div>
                </div>

                <!-- Footer -->
                <div style="padding:10px 16px;border-top:1px solid #30363d;
                            display:flex;justify-content:space-between;align-items:center;
                            background:rgba(0,0,0,0.2);">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <span style="color:#6b7280;font-size:11px;">${signal.confidence || 70}% confidence</span>
                        ${rr ? `<span style="background:rgba(34,197,94,0.15);color:#22c55e;
                                           padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">
                                    R:R ${rr.toFixed(1)}
                                </span>` : ''}
                    </div>
                    <div style="color:#58a6ff;font-size:12px;font-weight:600;">View Full Analysis →</div>
                </div>
            </div>`;
    }

    // ── Status (delegates to ProChart.tradeState when ready) ──────────────────

    calculateStatus(signal) {
        if (window.ProChart && window.ProChart.tradeState) {
            const candles      = signal.candles;
            const currentPrice = (candles && candles.length)
                ? candles[candles.length - 1].close
                : parseFloat(signal.entry);
            const ts = window.ProChart.tradeState(signal, currentPrice);
            return { text: ts.label, class: ts.state.toLowerCase(), icon: ts.icon, bg: ts.bg || 'rgba(107,114,128,0.2)', color: ts.color };
        }
        // Fallback: time-based (used before ProChart IIFE executes)
        const mins = (Date.now() - new Date(signal.created_at)) / 60000;
        if (mins <  5) return { text: 'PENDING', class: 'pending', icon: '⏳', bg: 'rgba(255,193,7,0.2)',   color: '#ffc107' };
        if (mins < 60) return { text: 'ACTIVE',  class: 'active',  icon: '●',  bg: 'rgba(0,208,132,0.2)',  color: '#00d084' };
        return              { text: 'EXPIRED', class: 'expired', icon: '⚪', bg: 'rgba(139,148,158,0.2)', color: '#8b949e' };
    }

    // ── Grid Chart (lightweight — one per card) ────────────────────────────────

    renderGridChart(signal) {
        const container = document.getElementById('chart-' + signal.id);
        if (!container) return;

        try {
            const LC = window.LightweightCharts;
            if (!LC) {
                container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#555;font-size:12px;">Chart lib not ready</div>';
                return;
            }

            // ProChart provides validated/fallback candles
            const candles = (window.ProChart && window.ProChart.validateCandles)
                ? window.ProChart.validateCandles(signal)
                : (signal.candles || []);

            if (!candles || candles.length < 5) {
                container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#555;font-size:12px;">No chart data</div>';
                return;
            }

            const isExpired = signal.expires_at
                ? new Date(signal.expires_at) < new Date()
                : (Date.now() - new Date(signal.created_at)) / 60000 > 60;

            const upColor   = isExpired ? '#1d4a38' : '#00d084';
            const downColor = isExpired ? '#4a1d1d' : '#ff4757';

            const chart = LC.createChart(container, {
                width:  container.clientWidth,
                height: container.clientHeight,
                layout: {
                    background: { type: 'solid', color: '#0a0a0f' },
                    textColor:  '#6b7280',
                    fontFamily: "'Inter', sans-serif",
                },
                grid: {
                    vertLines: { color: 'rgba(255,255,255,0.02)' },
                    horzLines: { color: 'rgba(255,255,255,0.02)' }
                },
                crosshair:       { mode: LC.CrosshairMode.None },
                rightPriceScale: { borderColor: 'rgba(255,255,255,0.05)', scaleMargins: { top: 0.1, bottom: 0.1 } },
                timeScale:       { borderColor: 'rgba(255,255,255,0.05)', visible: false },
                handleScroll:    false,
                handleScale:     false,
            });

            this.charts.set(signal.id, chart);

            const cs = chart.addCandlestickSeries({
                upColor, downColor,
                borderUpColor: upColor, borderDownColor: downColor,
                wickUpColor:   upColor, wickDownColor:   downColor,
            });
            cs.setData(candles);

            const entry  = parseFloat(signal.entry);
            const target = parseFloat(signal.target);
            const stop   = parseFloat(signal.stop);
            if (entry)  cs.createPriceLine({ price: entry,  color: '#ffffff', lineWidth: 1, lineStyle: LC.LineStyle.Solid,  axisLabelVisible: false });
            if (target) cs.createPriceLine({ price: target, color: '#00d084', lineWidth: 1, lineStyle: LC.LineStyle.Dashed, axisLabelVisible: false });
            if (stop)   cs.createPriceLine({ price: stop,   color: '#ff4757', lineWidth: 1, lineStyle: LC.LineStyle.Dashed, axisLabelVisible: false });

            chart.timeScale().fitContent();

            const ro = new ResizeObserver((entries) => {
                if (chart && entries[0]) chart.resize(entries[0].contentRect.width, entries[0].contentRect.height);
            });
            ro.observe(container);

        } catch (err) {
            console.error('[GridChart] ' + signal.symbol + ':', err);
            container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#ef4444;font-size:12px;">Chart error</div>';
        }
    }

    // ── Modal — PRO Chart ──────────────────────────────────────────────────────

    viewAnalysis(signalId) {
        const signal = this.signals.find(s => s.id === signalId);
        if (!signal) return;

        const pattern = signal.pattern_name || signal.pattern || 'Breakout';
        const rr      = this._calcRR(signal);

        const titleEl = document.getElementById('modalTitle');
        if (titleEl) titleEl.textContent = signal.symbol + ' — ' + signal.direction + ' Signal';

        const modalContent = document.getElementById('modalContent');
        if (!modalContent) return;

        modalContent.innerHTML =
            '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;">' +
                '<div style="background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:12px;text-align:center;">' +
                    '<div style="color:#8b949e;font-size:10px;margin-bottom:4px;text-transform:uppercase;">Entry</div>' +
                    '<div style="color:#fff;font-weight:700;font-size:17px;font-family:monospace;">' + signal.entry + '</div>' +
                '</div>' +
                '<div style="background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:12px;text-align:center;">' +
                    '<div style="color:#8b949e;font-size:10px;margin-bottom:4px;text-transform:uppercase;">Target</div>' +
                    '<div style="color:#00d084;font-weight:700;font-size:17px;font-family:monospace;">' + signal.target + '</div>' +
                '</div>' +
                '<div style="background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:12px;text-align:center;">' +
                    '<div style="color:#8b949e;font-size:10px;margin-bottom:4px;text-transform:uppercase;">Stop</div>' +
                    '<div style="color:#ff4757;font-weight:700;font-size:17px;font-family:monospace;">' + signal.stop + '</div>' +
                '</div>' +
            '</div>' +
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:8px;">' +
                '<div style="display:flex;gap:8px;flex-wrap:wrap;">' +
                    '<span style="background:rgba(88,166,255,0.15);color:#58a6ff;padding:4px 10px;border-radius:6px;font-size:12px;font-weight:600;">' + pattern + '</span>' +
                    (rr ? '<span style="background:rgba(34,197,94,0.15);color:#22c55e;padding:4px 10px;border-radius:6px;font-size:12px;font-weight:600;">R:R ' + rr.toFixed(1) + '</span>' : '') +
                    '<span style="background:rgba(255,255,255,0.07);color:#9ca3af;padding:4px 10px;border-radius:6px;font-size:12px;">' + (signal.timeframe || 'M5') + '</span>' +
                '</div>' +
                '<span style="color:#6b7280;font-size:12px;">' + (signal.confidence || 70) + '% confidence</span>' +
            '</div>' +
            '<div style="position:relative;border-radius:10px;overflow:hidden;border:1px solid #30363d;margin-bottom:16px;">' +
                '<div id="sig-chart-loading" style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:420px;background:#0a0a0f;color:#6b7280;">' +
                    '<div style="font-size:28px;margin-bottom:10px;">⏳</div>' +
                    '<div style="font-size:13px;">Loading PRO chart…</div>' +
                '</div>' +
                '<div id="modal-chart-container" style="width:100%;height:420px;display:none;"></div>' +
            '</div>' +
            (signal.rationale
                ? '<div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.3);border-radius:8px;padding:14px;">' +
                      '<div style="color:#818cf8;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">AI Analysis</div>' +
                      '<div style="color:#e0e7ff;font-size:13px;line-height:1.65;">' + signal.rationale + '</div>' +
                  '</div>'
                : '');

        // Show modal (needs flex removed from hidden state)
        const modal = document.getElementById('signalModal');
        if (modal) { modal.classList.remove('hidden'); modal.classList.add('flex'); }

        // Fire PRO chart
        if (window.ProChart) {
            const chartDiv   = document.getElementById('modal-chart-container');
            const loadingDiv = document.getElementById('sig-chart-loading');
            if (chartDiv) chartDiv.style.display = 'block';

            window.ProChart.create('modal-chart-container', signal)
                .then(function() {
                    if (loadingDiv) loadingDiv.style.display = 'none';
                })
                .catch(function(err) {
                    console.error('[Modal] ProChart error:', err);
                    if (loadingDiv) loadingDiv.style.display = 'none';
                    if (chartDiv) chartDiv.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#ef4444;font-size:13px;">Chart error: ' + err.message + '</div>';
                });
        }
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

    var LIGHTWEIGHT_CHARTS_CDN = 'https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js';
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
        var sw      = findSwingPoints(candles);
        var highs   = sw.highs;
        var lows    = sw.lows;
        var key     = (pattern || '').toUpperCase().replace(/\s+/g, '_');
        var patDef  = PATTERNS[key] || PATTERNS['BREAKOUT'];
        var expired = isSignalExpired(signal);
        var color   = expired ? 'rgba(148,163,184,0.5)' : '#00e5ff';
        var width   = expired ? 1 : 3;
        var LC      = LightweightCharts;

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
        if (highs.length >= 2) addLine(chart, [{ time: highs[highs.length-2].time, value: highs[highs.length-2].price }, { time: highs[highs.length-1].time, value: highs[highs.length-1].price }], color, width, LC.LineStyle.Solid);
        if (lows.length  >= 2) addLine(chart, [{ time: lows[lows.length-2].time,   value: lows[lows.length-2].price   }, { time: lows[lows.length-1].time,   value: lows[lows.length-1].price   }], color, width, LC.LineStyle.Solid);
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

    // ── Premium Zones ──────────────────────────────────────────────────────────

    function drawPremiumZones(chart, candles, signal, tradeState) {
        if (!chart || !candles || candles.length < 5) return;
        var entry  = parseFloat(signal.entry)  || 0;
        var target = parseFloat(signal.target) || 0;
        var stop   = parseFloat(signal.stop)   || 0;
        var isBuy  = (signal.direction || '').toUpperCase().indexOf('BUY') !== -1;
        if (!entry || !target || !stop) return;
        var lastTime   = candles[candles.length-1].time;
        var startTime  = candles[Math.floor(candles.length * 0.6)].time;
        var futureTime = lastTime + (lastTime - candles[0].time) * 0.4;
        var isExpired  = tradeState.state === 'STOPPED' || isSignalExpired(signal);
        var pB = isExpired ? 'rgba(0,255,136,0.15)' : 'rgba(0,255,136,0.25)';
        var pE = isExpired ? 'rgba(0,255,136,0.3)'  : '#00ff88';
        var rB = isExpired ? 'rgba(255,71,87,0.15)' : 'rgba(255,71,87,0.25)';
        var rE = isExpired ? 'rgba(255,71,87,0.3)'  : '#ff4757';
        if (isBuy) {
            drawZone(chart, startTime, futureTime, target, entry, pB, pE);
            drawZone(chart, startTime, futureTime, entry,  stop,  rB, rE);
        } else {
            drawZone(chart, startTime, futureTime, stop,  entry,  rB, rE);
            drawZone(chart, startTime, futureTime, entry, target, pB, pE);
        }
    }

    function drawZone(chart, t0, t1, top, bottom, fillColor, borderColor) {
        var LC     = LightweightCharts;
        var steps  = 10;
        var dt     = (t1 - t0) / steps;
        var mkData = function(val) {
            var d = [];
            for (var i = 0; i <= steps; i++) d.push({ time: t0 + dt*i, value: val });
            return d;
        };
        addLine(chart, mkData(top),    borderColor, 2, LC.LineStyle.Solid);
        addLine(chart, mkData(bottom), borderColor, 2, LC.LineStyle.Solid);
        var fillSteps = 5;
        var dp = (top - bottom) / fillSteps;
        for (var j = 1; j < fillSteps; j++) {
            addLine(chart, mkData(bottom + dp*j),
                fillColor.replace('0.25','0.08').replace('0.15','0.04'),
                1, LC.LineStyle.Solid);
        }
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

    function generateCandlesFromPoints(signal) {
        var pts  = signal.pattern_points || [];
        var base = pts[0] ? pts[0].price : (parseFloat(signal.entry) || 100);
        var now  = Math.floor(Date.now() / 1000);
        var intv = 300;
        var candles = [];
        for (var i = 60; i >= 0; i--) {
            var time  = now - (i*intv);
            var v     = base * 0.002;
            var open  = base  + (Math.random()-0.5)*v;
            var close = open  + (Math.random()-0.5)*v;
            candles.push({ time: time, open: +open.toFixed(5), high: +(Math.max(open,close)+Math.random()*v*0.5).toFixed(5), low: +(Math.min(open,close)-Math.random()*v*0.5).toFixed(5), close: +close.toFixed(5) });
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

            var patternName = signal.pattern_name || signal.pattern;
            if (!patternName) {
                container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#6b7280;">No pattern detected for this signal</div>';
                return;
            }

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
                rightPriceScale: { borderColor: 'rgba(255,255,255,0.1)', scaleMargins: { top: 0.15, bottom: 0.15 } },
                timeScale:       { borderColor: 'rgba(255,255,255,0.1)', timeVisible: true, secondsVisible: false }
            });

            candlestickSeries = chartInstance.addCandlestickSeries({
                upColor:         isExpired ? '#065f46' : '#10b981',
                downColor:       isExpired ? '#7f1d1d' : '#ef4444',
                borderUpColor:   isExpired ? '#065f46' : '#10b981',
                borderDownColor: isExpired ? '#7f1d1d' : '#ef4444',
                wickUpColor:     isExpired ? '#065f46' : '#10b981',
                wickDownColor:   isExpired ? '#7f1d1d' : '#ef4444',
            });
            candlestickSeries.setData(candles);

            drawPatternStructure(chartInstance, candles, patternName, signal);
            drawPremiumZones(chartInstance, candles, signal, tradeState);
            drawCurvedProjection(chartInstance, candles, signal, tradeState);
            drawPremiumPriceLevels(candlestickSeries,
                parseFloat(signal.entry), parseFloat(signal.target), parseFloat(signal.stop), tradeState);

            container.style.position = 'relative';
            addStatusBadge(container, tradeState);
            addAIOverlay(container, signal, tradeState);

            chartInstance.timeScale().fitContent();

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
