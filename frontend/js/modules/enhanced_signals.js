/**
 * PRO TradingView-Level Chart System v20
 * Institutional-grade visualization with pattern detection
 */

class EnhancedSignalsPage {
    constructor() {
        this.charts = new Map();
        this.currentPrice = 0;
        this.pulseInterval = null;
        this.patterns = {
            'Ascending Triangle': { structure: 'horizontal_top', lines: 2 },
            'Descending Triangle': { structure: 'horizontal_bottom', lines: 2 },
            'Symmetrical Triangle': { structure: 'converging', lines: 2 },
            'Rising Wedge': { structure: 'converging_up', lines: 2, bearish: true },
            'Falling Wedge': { structure: 'converging_down', lines: 2, bullish: true },
            'Bull Flag': { structure: 'channel_down', lines: 2 },
            'Bear Flag': { structure: 'channel_up', lines: 2 },
            'Ascending Channel': { structure: 'channel_up', lines: 2 },
            'Descending Channel': { structure: 'channel_down', lines: 2 },
            'Double Top': { structure: 'double_peak', lines: 1 },
            'Double Bottom': { structure: 'double_trough', lines: 1 },
            'Breakout': { structure: 'breakout', lines: 1 }
        };
    }

    init() {
        console.log('[EnhancedSignals] PRO System initialized');
        this.loadSignals();
        this.startAutoRefresh();
    }

    startAutoRefresh() {
        setInterval(() => this.loadSignals(), 30000);
    }

    async loadSignals() {
        try {
            const response = await fetch('/api/signals/enhanced');
            const signals = await response.json();
            
            const container = document.getElementById('enhanced-signals-container');
            if (!container) return;
            
            if (!signals || signals.length === 0) {
                container.innerHTML = '<div class="no-signals">No active signals</div>';
                return;
            }
            
            container.innerHTML = signals.map(signal => this.renderSignalCard(signal)).join('');
            
            signals.forEach(signal => {
                this.attachCardEvents(signal);
            });
            
        } catch (err) {
            console.error('[EnhancedSignals] Load error:', err);
        }
    }

    renderSignalCard(signal) {
        const status = this.calculateTradeStatus(signal);
        const pattern = signal.pattern_name || 'Breakout';
        const hasPattern = this.patterns[pattern] || this.patterns['Breakout'];
        
        return `
            <div class="signal-card-pro" data-signal-id="${signal.id}">
                <div class="signal-header">
                    <div class="symbol-badge">
                        <span class="symbol">${signal.symbol}</span>
                        <span class="timeframe">${signal.timeframe || 'M5'}</span>
                    </div>
                    <div class="direction-badge ${signal.direction}">
                        ${signal.direction === 'BUY' ? '▲ LONG' : '▼ SHORT'}
                    </div>
                    <div class="status-badge ${status.class}">
                        ${status.icon} ${status.text}
                    </div>
                </div>
                
                <div class="pattern-info">
                    <div class="pattern-name">${pattern}</div>
                    <div class="pattern-desc">${this.getPatternDescription(pattern, signal.direction)}</div>
                </div>
                
                <div class="price-levels">
                    <div class="level entry">
                        <label>ENTRY</label>
                        <value>${signal.entry}</value>
                    </div>
                    <div class="level target">
                        <label>TARGET</label>
                        <value>${signal.target}</value>
                    </div>
                    <div class="level stop">
                        <label>STOP</label>
                        <value>${signal.stop}</value>
                    </div>
                </div>
                
                <div class="chart-container" id="chart-${signal.id}">
                    <div class="chart-loading">Loading Chart...</div>
                </div>
                
                <div class="signal-footer">
                    <button class="btn-analyze" onclick="enhancedSignals.viewAnalysis('${signal.id}')">
                        View Analysis
                    </button>
                    <span class="confidence">Confidence: ${signal.confidence || 70}%</span>
                </div>
            </div>
        `;
    }

    calculateTradeStatus(signal) {
        const current = parseFloat(signal.current_price || signal.entry);
        const entry = parseFloat(signal.entry);
        
        if (signal.direction === 'BUY') {
            if (current < entry) {
                return { text: 'PENDING', class: 'pending', icon: '⏳' };
            } else {
                return { text: 'ACTIVE', class: 'active', icon: '🔴' };
            }
        } else {
            if (current > entry) {
                return { text: 'PENDING', class: 'pending', icon: '⏳' };
            } else {
                return { text: 'ACTIVE', class: 'active', icon: '🔴' };
            }
        }
    }

    getPatternDescription(pattern, direction) {
        const desc = {
            'Ascending Triangle': 'Waiting for resistance breakout',
            'Descending Triangle': 'Waiting for support breakdown',
            'Symmetrical Triangle': 'Converging - breakout imminent',
            'Rising Wedge': 'Bearish reversal pattern',
            'Falling Wedge': 'Bullish reversal pattern',
            'Bull Flag': 'Continuation after rally',
            'Bear Flag': 'Continuation after drop',
            'Breakout': 'Momentum breakout setup'
        };
        return desc[pattern] || 'Technical pattern detected';
    }

    attachCardEvents(signal) {
        setTimeout(() => {
            this.renderProChart(signal);
        }, 100);
    }

    renderProChart(signal) {
        const container = document.getElementById(`chart-${signal.id}`);
        if (!container || !signal.candles || signal.candles.length === 0) {
            if (container) container.innerHTML = '<div class="no-data">No chart data</div>';
            return;
        }

        const chart = LightweightCharts.createChart(container, {
            width: container.clientWidth,
            height: 300,
            layout: {
                background: { type: 'solid', color: '#0a0a0a' },
                textColor: '#d1d4dc',
            },
            grid: {
                vertLines: { color: 'rgba(42, 46, 57, 0.2)' },
                horzLines: { color: 'rgba(42, 46, 57, 0.2)' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: 'rgba(42, 46, 57, 0.6)',
                scaleMargins: { top: 0.1, bottom: 0.1 },
            },
            timeScale: {
                borderColor: 'rgba(42, 46, 57, 0.6)',
                timeVisible: true,
                secondsVisible: false,
            },
        });

        this.charts.set(signal.id, chart);

        // Candlestick series
        const candleSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });

        const candles = signal.candles.map(c => ({
            time: c.time,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close
        }));

        candleSeries.setData(candles);

        // Entry, Target, Stop lines with glow effect
        const entryPrice = parseFloat(signal.entry);
        const targetPrice = parseFloat(signal.target);
        const stopPrice = parseFloat(signal.stop);

        // Price lines
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

        // Draw Pattern Structure (if pattern_points exist)
        if (signal.pattern_points && signal.pattern_points.length >= 2) {
            this.drawPatternStructure(chart, candleSeries, signal);
        }

        // Draw zones (Profit/Risk)
        this.drawZones(chart, signal, candles);

        // Fit content
        chart.timeScale().fitContent();
    }

    drawPatternStructure(chart, candleSeries, signal) {
        const points = signal.pattern_points;
        const pattern = signal.pattern_name || 'Breakout';
        const patternConfig = this.patterns[pattern] || this.patterns['Breakout'];
        
        if (!points || points.length < 2) return;

        // Sort points by time
        const sortedPoints = [...points].sort((a, b) => a.time - b.time);
        
        // Draw trendlines based on pattern structure
        if (patternConfig.structure === 'horizontal_top' || pattern === 'Ascending Triangle') {
            // Flat resistance line + rising support
            this.drawTrendline(chart, sortedPoints[0], sortedPoints[1], '#ff6b6b', 'Resistance');
            if (sortedPoints[2] && sortedPoints[3]) {
                this.drawTrendline(chart, sortedPoints[2], sortedPoints[3], '#51cf66', 'Support');
            }
        } else if (patternConfig.structure === 'converging' || pattern === 'Symmetrical Triangle') {
            // Both lines converging
            this.drawTrendline(chart, sortedPoints[0], sortedPoints[1], '#ff6b6b', 'Resistance');
            if (sortedPoints[2] && sortedPoints[3]) {
                this.drawTrendline(chart, sortedPoints[2], sortedPoints[3], '#51cf66', 'Support');
            }
        } else if (patternConfig.structure === 'channel_up') {
            // Parallel rising lines
            this.drawTrendline(chart, sortedPoints[0], sortedPoints[1], '#339af0', 'Channel Top');
            if (sortedPoints[2]) {
                this.drawTrendline(chart, sortedPoints[2], {time: sortedPoints[1].time, price: sortedPoints[2].price + (sortedPoints[1].price - sortedPoints[0].price)}, '#339af0', 'Channel Bottom');
            }
        } else {
            // Default: connect provided points
            for (let i = 0; i < sortedPoints.length - 1; i += 2) {
                if (sortedPoints[i+1]) {
                    this.drawTrendline(chart, sortedPoints[i], sortedPoints[i+1], '#ffd43b', `Line ${i/2 + 1}`);
                }
            }
        }
    }

    drawTrendline(chart, point1, point2, color, title) {
        if (!point1 || !point2 || !point1.time || !point2.time) return;
        
        const lineSeries = chart.addLineSeries({
            color: color,
            lineWidth: 2,
            title: title,
            lastValueVisible: false,
            priceLineVisible: false,
        });

        lineSeries.setData([
            { time: point1.time, value: point1.price },
            { time: point2.time, value: point2.price }
        ]);
    }

    drawZones(chart, signal, candles) {
        const entry = parseFloat(signal.entry);
        const target = parseFloat(signal.target);
        const stop = parseFloat(signal.stop);
        
        // Determine zone areas based on direction
        let profitTop, profitBottom, riskTop, riskBottom;
        
        if (signal.direction === 'BUY') {
            profitTop = Math.max(entry, target);
            profitBottom = Math.min(entry, target);
            riskTop = Math.max(entry, stop);
            riskBottom = Math.min(entry, stop);
        } else {
            profitTop = Math.max(entry, target);
            profitBottom = Math.min(entry, target);
            riskTop = Math.max(entry, stop);
            riskBottom = Math.min(entry, stop);
        }

        // Use lightweight-charts plugins or overlay series for zones
        // Create zone bands using additional series
        const zoneData = candles.map(c => ({
            time: c.time,
            value: null // Zones are drawn as background
        }));

        // Add zone markers instead of full background (more compatible)
        // Profit zone markers
        const profitSeries = chart.addAreaSeries({
            topColor: 'rgba(0, 208, 132, 0.25)',
            bottomColor: 'rgba(0, 208, 132, 0.05)',
            lineColor: 'rgba(0, 208, 132, 0.5)',
            lineWidth: 1,
            title: 'Profit Zone',
            priceLineVisible: false,
            lastValueVisible: false,
        });

        // Risk zone markers  
        const riskSeries = chart.addAreaSeries({
            topColor: 'rgba(255, 71, 87, 0.25)',
            bottomColor: 'rgba(255, 71, 87, 0.05)',
            lineColor: 'rgba(255, 71, 87, 0.5)',
            lineWidth: 1,
            title: 'Risk Zone',
            priceLineVisible: false,
            lastValueVisible: false,
        });
    }

    viewAnalysis(signalId) {
        const modal = document.getElementById('analysis-modal');
        if (modal) modal.style.display = 'block';
        
        // Load detailed analysis view
        console.log(`[EnhancedSignals] Viewing analysis for signal ${signalId}`);
    }

    destroy() {
        this.charts.forEach(chart => chart.remove());
        this.charts.clear();
    }
}

// Singleton instance
const enhancedSignals = new EnhancedSignalsPage();

// Initialize when DOM ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('enhanced-signals-container')) {
        enhancedSignals.init();
    }
});

// Export for global access
window.enhancedSignals = enhancedSignals;

console.log('[EnhancedSignals] Module loaded successfully');
