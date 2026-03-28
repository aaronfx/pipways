/**
 * PRO TradingView-Level Chart System v20.1
 * Fixed version - no syntax errors
 */

class EnhancedSignalsPage {
    constructor() {
        this.charts = new Map();
        this.signals = [];
        console.log('[EnhancedSignals] Instance created');
    }

    init() {
        console.log('[EnhancedSignals] PRO System initialized v20.1');
        this.activeTab = 'ai';

        // Wire tab buttons
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

        this.loadSignals();

        // Auto-refresh every 30 seconds (stored so we can clear it later)
        this._refreshInterval = setInterval(() => this.loadSignals(), 30000);
    }

    async loadSignals() {
        const container = document.getElementById('enhanced-signals-container');
        if (!container) {
            console.warn('[EnhancedSignals] Container not found — section not visible yet');
            return;
        }

        try {
            const response = await fetch('/api/signals/enhanced');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const signals = await response.json();
            this.signals = signals || [];

            // ── Update stats row ────────────────────────────────────────────
            const active = this.signals.filter(s => {
                const mins = (Date.now() - new Date(s.created_at).getTime()) / 60000;
                return mins < 60;
            }).length;

            const avgConf = this.signals.length
                ? Math.round(this.signals.reduce((sum, s) => sum + (s.confidence || 70), 0) / this.signals.length)
                : null;

            const rrValues = this.signals
                .map(s => {
                    const entry = parseFloat(s.entry), target = parseFloat(s.target), stop = parseFloat(s.stop);
                    if (!entry || !target || !stop) return null;
                    const reward = Math.abs(target - entry);
                    const risk   = Math.abs(entry - stop);
                    return risk > 0 ? reward / risk : null;
                })
                .filter(Boolean);
            const avgRR = rrValues.length
                ? (rrValues.reduce((a, b) => a + b, 0) / rrValues.length).toFixed(1)
                : null;

            const statActive = document.getElementById('enhanced-stat-active');
            const statConf   = document.getElementById('enhanced-stat-confidence');
            const statRR     = document.getElementById('enhanced-stat-rr');
            if (statActive) statActive.textContent = active;
            if (statConf)   statConf.textContent   = avgConf != null ? `${avgConf}%` : '—';
            if (statRR)     statRR.textContent      = avgRR != null ? `${avgRR}R` : '—';

            // ── Render cards ────────────────────────────────────────────────
            if (this.signals.length === 0) {
                container.innerHTML = `
                    <div class="col-span-full" style="text-align:center;padding:60px 20px;color:#666;">
                        <div style="font-size:48px;margin-bottom:20px;">📊</div>
                        <h3 style="color:#9ca3af;font-size:1.1rem;font-weight:600;margin-bottom:8px;">No Active Signals</h3>
                        <p style="color:#6b7280;font-size:.875rem;">Waiting for trading opportunities…</p>
                    </div>`;
                return;
            }

            // Respect active tab filter
            const filtered = this.activeTab === 'pattern'
                ? this.signals.filter(s => s.pattern_name || s.pattern)
                : this.signals;

            container.innerHTML = filtered.length
                ? filtered.map(s => this.renderSignalCard(s)).join('')
                : `<div class="col-span-full" style="text-align:center;padding:40px;color:#6b7280;">
                       No pattern-based signals available.
                   </div>`;

            // Initialize charts after DOM update
            setTimeout(() => {
                filtered.forEach(s => this.renderChart(s));
            }, 100);

        } catch (err) {
            console.error('[EnhancedSignals] Load error:', err);
            container.innerHTML = `
                <div class="col-span-full" style="padding:20px;color:#f87171;text-align:center;">
                    <i class="fas fa-exclamation-triangle" style="font-size:2rem;margin-bottom:8px;display:block;"></i>
                    Error loading signals: ${err.message}
                </div>`;
        }
    }

    renderSignalCard(signal) {
        const status = this.calculateStatus(signal);
        const pattern = signal.pattern_name || signal.pattern || 'Breakout';
        const hasCandles = signal.candles && signal.candles.length > 0;
        
        return `
            <div class="signal-card-pro" data-signal-id="${signal.id}" style="
                background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
                border: 1px solid #30363d;
                border-radius: 12px;
                margin-bottom: 20px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            ">
                <!-- Header -->
                <div class="signal-header" style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 16px 20px;
                    border-bottom: 1px solid #30363d;
                    background: rgba(0,0,0,0.3);
                ">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div class="symbol-badge" style="
                            background: ${signal.direction === 'BUY' ? 'rgba(0,208,132,0.2)' : 'rgba(255,71,87,0.2)'};
                            color: ${signal.direction === 'BUY' ? '#00d084' : '#ff4757'};
                            padding: 6px 12px;
                            border-radius: 6px;
                            font-weight: bold;
                            font-size: 16px;
                        ">
                            ${signal.symbol}
                        </div>
                        <div class="timeframe" style="
                            background: rgba(255,255,255,0.1);
                            color: #8b949e;
                            padding: 4px 8px;
                            border-radius: 4px;
                            font-size: 12px;
                        ">
                            ${signal.timeframe || 'M5'}
                        </div>
                    </div>
                    
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div class="direction-badge ${signal.direction}" style="
                            background: ${signal.direction === 'BUY' ? '#00d084' : '#ff4757'};
                            color: white;
                            padding: 6px 16px;
                            border-radius: 6px;
                            font-weight: bold;
                            font-size: 14px;
                        ">
                            ${signal.direction === 'BUY' ? '▲ BUY' : '▼ SELL'}
                        </div>
                        <div class="status-badge ${status.class}" style="
                            background: ${status.bg};
                            color: ${status.color};
                            padding: 4px 12px;
                            border-radius: 20px;
                            font-size: 12px;
                            font-weight: 600;
                        ">
                            ${status.icon} ${status.text}
                        </div>
                    </div>
                </div>
                
                <!-- Pattern Info -->
                <div class="pattern-info" style="
                    padding: 12px 20px;
                    background: rgba(255,255,255,0.03);
                    border-bottom: 1px solid #30363d;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <div>
                        <div style="color: #58a6ff; font-weight: 600; font-size: 14px;">
                            Pattern: ${pattern}
                        </div>
                        <div style="color: #8b949e; font-size: 12px; margin-top: 2px;">
                            ${this.getPatternDescription(pattern, signal.direction)}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #8b949e; font-size: 11px;">Confidence</div>
                        <div style="color: #fff; font-weight: bold; font-size: 18px;">
                            ${signal.confidence || 70}%
                        </div>
                    </div>
                </div>
                
                <!-- Price Levels -->
                <div class="price-levels" style="
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 1px;
                    background: #30363d;
                ">
                    <div class="level" style="background: #0d1117; padding: 16px; text-align: center;">
                        <div style="color: #8b949e; font-size: 11px; margin-bottom: 4px;">ENTRY</div>
                        <div style="color: #fff; font-weight: bold; font-size: 18px; text-shadow: 0 0 10px rgba(255,255,255,0.3);">
                            ${signal.entry}
                        </div>
                    </div>
                    <div class="level" style="background: #0d1117; padding: 16px; text-align: center;">
                        <div style="color: #8b949e; font-size: 11px; margin-bottom: 4px;">TARGET</div>
                        <div style="color: #00d084; font-weight: bold; font-size: 18px; text-shadow: 0 0 10px rgba(0,208,132,0.3);">
                            ${signal.target}
                        </div>
                    </div>
                    <div class="level" style="background: #0d1117; padding: 16px; text-align: center;">
                        <div style="color: #8b949e; font-size: 11px; margin-bottom: 4px;">STOP</div>
                        <div style="color: #ff4757; font-weight: bold; font-size: 18px; text-shadow: 0 0 10px rgba(255,71,87,0.3);">
                            ${signal.stop}
                        </div>
                    </div>
                </div>
                
                <!-- Chart -->
                <div class="chart-wrapper" style="
                    position: relative;
                    height: 320px;
                    background: #0d1117;
                ">
                    ${hasCandles ? `
                        <div id="chart-${signal.id}" style="width:100%;height:100%;"></div>
                    ` : `
                        <div style="
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            height: 100%;
                            color: #666;
                            flex-direction: column;
                        ">
                            <div style="font-size: 32px; margin-bottom: 10px;">📈</div>
                            <div>No chart data available</div>
                        </div>
                    `}
                </div>
                
                <!-- Footer -->
                <div class="signal-footer" style="
                    padding: 12px 20px;
                    border-top: 1px solid #30363d;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background: rgba(0,0,0,0.2);
                ">
                    <div style="color: #8b949e; font-size: 12px;">
                        ID: #${signal.id} • ${new Date(signal.created_at).toLocaleString()}
                    </div>
                    <button onclick="enhancedSignals.viewAnalysis(${signal.id})" style="
                        background: linear-gradient(135deg, #58a6ff 0%, #0969da 100%);
                        color: white;
                        border: none;
                        padding: 8px 20px;
                        border-radius: 6px;
                        cursor: pointer;
                        font-weight: 600;
                        font-size: 13px;
                    ">
                        View Analysis
                    </button>
                </div>
            </div>
        `;
    }

    calculateStatus(signal) {
        // In real implementation, compare with current market price
        // For now, use created_at time to simulate
        const created = new Date(signal.created_at);
        const now = new Date();
        const minutesSince = (now - created) / 1000 / 60;
        
        if (minutesSince < 5) {
            return { text: 'PENDING', class: 'pending', icon: '⏳', bg: 'rgba(255,193,7,0.2)', color: '#ffc107' };
        } else if (minutesSince < 60) {
            return { text: 'ACTIVE', class: 'active', icon: '🔴', bg: 'rgba(0,208,132,0.2)', color: '#00d084' };
        } else {
            return { text: 'EXPIRED', class: 'expired', icon: '⚪', bg: 'rgba(139,148,158,0.2)', color: '#8b949e' };
        }
    }

    getPatternDescription(pattern, direction) {
        const descriptions = {
            'Ascending Triangle': 'Bullish continuation pattern',
            'Descending Triangle': 'Bearish continuation pattern',
            'Symmetrical Triangle': 'Breakout imminent',
            'Rising Wedge': 'Bearish reversal setup',
            'Falling Wedge': 'Bullish reversal setup',
            'Bull Flag': 'Continuation after rally',
            'Bear Flag': 'Continuation after drop',
            'Double Top': 'Reversal pattern',
            'Double Bottom': 'Reversal pattern',
            'Breakout': 'Momentum breakout setup'
        };
        return descriptions[pattern] || 'Technical pattern detected';
    }

    renderChart(signal) {
        const container = document.getElementById(`chart-${signal.id}`);
        if (!container || !signal.candles || signal.candles.length === 0) {
            return;
        }

        try {
            // Check if LightweightCharts is available
            if (typeof LightweightCharts === 'undefined') {
                console.error('[Chart] LightweightCharts not loaded');
                container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#666;">Chart library not loaded</div>';
                return;
            }

            const chart = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: container.clientHeight,
                layout: {
                    background: { type: 'solid', color: '#0d1117' },
                    textColor: '#c9d1d9',
                },
                grid: {
                    vertLines: { color: 'rgba(48,54,61,0.3)' },
                    horzLines: { color: 'rgba(48,54,61,0.3)' },
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                },
                rightPriceScale: {
                    borderColor: '#30363d',
                    scaleMargins: { top: 0.1, bottom: 0.1 },
                },
                timeScale: {
                    borderColor: '#30363d',
                    timeVisible: true,
                    secondsVisible: false,
                },
            });

            this.charts.set(signal.id, chart);

            // Candlestick series
            const candleSeries = chart.addCandlestickSeries({
                upColor: '#00d084',
                downColor: '#ff4757',
                borderVisible: false,
                wickUpColor: '#00d084',
                wickDownColor: '#ff4757',
            });

            const candles = signal.candles.map(c => ({
                time: c.time,
                open: c.open,
                high: c.high,
                low: c.low,
                close: c.close
            }));

            candleSeries.setData(candles);

            // Add price lines with glow effect
            const entryPrice = parseFloat(signal.entry);
            const targetPrice = parseFloat(signal.target);
            const stopPrice = parseFloat(signal.stop);

            candleSeries.createPriceLine({
                price: entryPrice,
                color: '#ffffff',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Solid,
                title: 'ENTRY',
                axisLabelVisible: true,
            });

            candleSeries.createPriceLine({
                price: targetPrice,
                color: '#00d084',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Solid,
                title: 'TARGET',
                axisLabelVisible: true,
            });

            candleSeries.createPriceLine({
                price: stopPrice,
                color: '#ff4757',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Solid,
                title: 'STOP',
                axisLabelVisible: true,
            });

            // Draw pattern structure if points available
            if (signal.pattern_points && signal.pattern_points.length >= 2) {
                this.drawPatternLines(chart, signal);
            }

            chart.timeScale().fitContent();
            
            console.log(`[Chart] Rendered for ${signal.symbol} with ${candles.length} candles`);

        } catch (err) {
            console.error('[Chart] Error rendering:', err);
            container.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#ff4757;">Chart error: ${err.message}</div>`;
        }
    }

    drawPatternLines(chart, signal) {
        const points = signal.pattern_points;
        if (!points || points.length < 2) return;

        // Sort by time
        const sorted = [...points].sort((a, b) => a.time - b.time);
        
        // Draw lines between consecutive points
        for (let i = 0; i < sorted.length - 1; i++) {
            const p1 = sorted[i];
            const p2 = sorted[i + 1];
            
            if (!p1.time || !p2.time) continue;
            
            const lineSeries = chart.addLineSeries({
                color: '#58a6ff',
                lineWidth: 2,
                lastValueVisible: false,
                priceLineVisible: false,
            });

            lineSeries.setData([
                { time: p1.time, value: p1.price },
                { time: p2.time, value: p2.price }
            ]);
        }
    }

    viewAnalysis(signalId) {
        console.log(`[EnhancedSignals] Viewing analysis for signal ${signalId}`);
        const signal = this.signals.find(s => s.id === signalId);
        if (!signal) return;
        
        // Create modal or navigate to detail view
        alert(`Analysis for ${signal.symbol} ${signal.direction}\n\nPattern: ${signal.pattern_name || 'Breakout'}\nEntry: ${signal.entry}\nTarget: ${signal.target}\nStop: ${signal.stop}`);
    }

    destroy() {
        if (this._refreshInterval) {
            clearInterval(this._refreshInterval);
            this._refreshInterval = null;
        }
        this.charts.forEach(chart => chart.remove());
        this.charts.clear();
    }
}

// Create global instance (init is called by loadSectionData when the section is shown,
// which also guarantees the DOM elements exist at that point)
const enhancedSignals = new EnhancedSignalsPage();
window.enhancedSignals = enhancedSignals;

console.log('[EnhancedSignals] Module loaded successfully v20.1');
