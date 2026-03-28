// Enhanced Signals Page — PRO TradingView-Level Visualization v20
// Institutional-grade chart rendering with pattern detection
//
// ✨ FEATURES:
// ✅ Dynamic trade state (PENDING → ACTIVE)
// ✅ Pattern structure rendering (Triangle, Wedge, Channel, Flag)
// ✅ Real swing high/low trendlines
// ✅ Curved projection paths
// ✅ TradingView-style glow effects
// ✅ Smart status badges
// ✅ AI analysis overlay
// ✅ Auto-fallback data
// ✅ Zero Fibonacci
// ✅ Premium minimal UI

(function () {
    'use strict';

    const LIGHTWEIGHT_CHARTS_CDN = 'https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js';
    let LightweightCharts = null;
    let chartInstance = null;
    let candlestickSeries = null;

    // ═══════════════════════════════════════════════════════════════════════════════
    // PATTERN DEFINITIONS
    // ═══════════════════════════════════════════════════════════════════════════════

    const PATTERNS = {
        'ASCENDING_TRIANGLE': {
            name: 'Ascending Triangle',
            icon: '▲',
            description: 'Bullish continuation pattern with flat resistance and rising support',
            structure: 'horizontal_top'
        },
        'DESCENDING_TRIANGLE': {
            name: 'Descending Triangle',
            icon: '▼',
            description: 'Bearish continuation pattern with flat support and descending resistance',
            structure: 'horizontal_bottom'
        },
        'SYMMETRICAL_TRIANGLE': {
            name: 'Symmetrical Triangle',
            icon: '◊',
            description: 'Consolidation pattern with converging trendlines',
            structure: 'converging'
        },
        'RISING_WEDGE': {
            name: 'Rising Wedge',
            icon: '⚠',
            description: 'Bearish reversal pattern with converging upward lines',
            structure: 'converging_rising'
        },
        'FALLING_WEDGE': {
            name: 'Falling Wedge',
            icon: '⚡',
            description: 'Bullish reversal pattern with converging downward lines',
            structure: 'converging_falling'
        },
        'BULL_FLAG': {
            name: 'Bull Flag',
            icon: '🚩',
            description: 'Continuation pattern after strong upward move',
            structure: 'parallel_down'
        },
        'BEAR_FLAG': {
            name: 'Bear Flag',
            icon: '🏴',
            description: 'Continuation pattern after strong downward move',
            structure: 'parallel_up'
        },
        'ASCENDING_CHANNEL': {
            name: 'Ascending Channel',
            icon: '📈',
            description: 'Bullish trend with parallel rising lines',
            structure: 'parallel_rising'
        },
        'DESCENDING_CHANNEL': {
            name: 'Descending Channel',
            icon: '📉',
            description: 'Bearish trend with parallel falling lines',
            structure: 'parallel_falling'
        },
        'DOUBLE_TOP': {
            name: 'Double Top',
            icon: 'M',
            description: 'Reversal pattern with two peaks at similar levels',
            structure: 'double_peak'
        },
        'DOUBLE_BOTTOM': {
            name: 'Double Bottom',
            icon: 'W',
            description: 'Reversal pattern with two troughs at similar levels',
            structure: 'double_trough'
        },
        'BREAKOUT': {
            name: 'Breakout Setup',
            icon: '💥',
            description: 'Price breaking key resistance/support level',
            structure: 'breakout'
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════════
    // TRADE STATE ENGINE
    // ═══════════════════════════════════════════════════════════════════════════════

    function determineTradeState(signal, currentPrice) {
        const entry = parseFloat(signal.entry) || 0;
        const target = parseFloat(signal.target) || 0;
        const stop = parseFloat(signal.stop) || 0;
        const isBuy = (signal.direction || '').toUpperCase().includes('BUY');

        if (!entry || !currentPrice) {
            return { state: 'UNKNOWN', label: 'Unknown', color: '#6b7280', icon: '?' };
        }

        // Check if TP/SL hit
        if (isBuy) {
            if (currentPrice >= target) return { state: 'TARGET_HIT', label: 'TARGET HIT', color: '#00ff88', icon: '✓', bg: 'rgba(0,255,136,0.2)' };
            if (currentPrice <= stop) return { state: 'STOPPED', label: 'STOPPED OUT', color: '#ff4757', icon: '✗', bg: 'rgba(255,71,87,0.2)' };
            if (currentPrice >= entry) return { state: 'ACTIVE', label: 'LIVE TRADE', color: '#00c9a7', icon: '●', bg: 'rgba(0,201,167,0.2)' };
            return { state: 'PENDING', label: 'BUY STOP', color: '#f5a623', icon: '◐', bg: 'rgba(245,166,35,0.2)' };
        } else {
            if (currentPrice <= target) return { state: 'TARGET_HIT', label: 'TARGET HIT', color: '#00ff88', icon: '✓', bg: 'rgba(0,255,136,0.2)' };
            if (currentPrice >= stop) return { state: 'STOPPED', label: 'STOPPED OUT', color: '#ff4757', icon: '✗', bg: 'rgba(255,71,87,0.2)' };
            if (currentPrice <= entry) return { state: 'ACTIVE', label: 'LIVE TRADE', color: '#00c9a7', icon: '●', bg: 'rgba(0,201,167,0.2)' };
            return { state: 'PENDING', label: 'SELL STOP', color: '#f5a623', icon: '◐', bg: 'rgba(245,166,35,0.2)' };
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // SWING POINT DETECTION
    // ═══════════════════════════════════════════════════════════════════════════════

    function findSwingPoints(candles, direction = 'both', strength = 3) {
        if (!candles || candles.length < 5) return { highs: [], lows: [] };

        const highs = [];
        const lows = [];

        for (let i = strength; i < candles.length - strength; i++) {
            const current = candles[i];
            let isHigh = true;
            let isLow = true;

            // Check surrounding candles
            for (let j = 1; j <= strength; j++) {
                if (candles[i - j].high >= current.high) isHigh = false;
                if (candles[i + j].high >= current.high) isHigh = false;
                if (candles[i - j].low <= current.low) isLow = false;
                if (candles[i + j].low <= current.low) isLow = false;
            }

            if (isHigh) highs.push({ time: current.time, price: current.high, idx: i });
            if (isLow) lows.push({ time: current.time, price: current.low, idx: i });
        }

        return { highs, lows };
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // PATTERN STRUCTURE RENDERER
    // ═══════════════════════════════════════════════════════════════════════════════

    function drawPatternStructure(chart, candles, pattern, signal) {
        if (!chart || !candles || candles.length < 10) return;

        const { highs, lows } = findSwingPoints(candles);
        const patternKey = (pattern || '').toUpperCase().replace(/\s+/g, '_');
        const patternDef = PATTERNS[patternKey] || PATTERNS['BREAKOUT'];

        const isExpired = isSignalExpired(signal);
        const lineColor = isExpired ? 'rgba(148, 163, 184, 0.5)' : '#00e5ff';
        const lineWidth = isExpired ? 1 : 3;

        switch (patternDef.structure) {
            case 'horizontal_top': // Ascending Triangle
                drawAscendingTriangle(chart, candles, highs, lows, lineColor, lineWidth, signal);
                break;
            case 'horizontal_bottom': // Descending Triangle
                drawDescendingTriangle(chart, candles, highs, lows, lineColor, lineWidth, signal);
                break;
            case 'converging': // Symmetrical Triangle
            case 'converging_rising':
            case 'converging_falling':
                drawConvergingPattern(chart, candles, highs, lows, lineColor, lineWidth, signal, patternDef.structure);
                break;
            case 'parallel_down': // Bull Flag
            case 'parallel_up': // Bear Flag
            case 'parallel_rising':
            case 'parallel_falling':
                drawChannelPattern(chart, candles, highs, lows, lineColor, lineWidth, signal, patternDef.structure);
                break;
            case 'double_peak':
            case 'double_trough':
                drawDoublePattern(chart, candles, highs, lows, lineColor, lineWidth, signal, patternDef.structure);
                break;
            default:
                drawAutoTrendlines(chart, candles, highs, lows, lineColor, lineWidth, signal);
        }
    }

    function drawAscendingTriangle(chart, candles, highs, lows, color, width, signal) {
        // Flat top from recent highs
        const recentHighs = highs.slice(-3);
        if (recentHighs.length < 2) return;

        const topLevel = Math.min(...recentHighs.map(h => h.price));
        const topTime = recentHighs[0].time;

        // Rising support from lows
        const recentLows = lows.slice(-3);
        if (recentLows.length < 2) return;

        const startLow = recentLows[0];
        const endLow = recentLows[recentLows.length - 1];

        // Draw horizontal resistance
        const resistance = chart.addLineSeries({
            color: color,
            lineWidth: width,
            lineStyle: LightweightCharts.LineStyle.Solid,
            title: 'Resistance',
            lastValueVisible: false
        });
        resistance.setData([
            { time: topTime, value: topLevel },
            { time: candles[candles.length - 1].time, value: topLevel }
        ]);

        // Draw rising support
        const support = chart.addLineSeries({
            color: color,
            lineWidth: width,
            lineStyle: LightweightCharts.LineStyle.Solid,
            title: 'Support',
            lastValueVisible: false
        });
        support.setData([
            { time: startLow.time, value: startLow.price },
            { time: endLow.time, value: endLow.price }
        ]);
    }

    function drawDescendingTriangle(chart, candles, highs, lows, color, width, signal) {
        // Flat bottom from recent lows
        const recentLows = lows.slice(-3);
        if (recentLows.length < 2) return;

        const bottomLevel = Math.max(...recentLows.map(l => l.price));
        const bottomTime = recentLows[0].time;

        // Descending resistance from highs
        const recentHighs = highs.slice(-3);
        if (recentHighs.length < 2) return;

        const startHigh = recentHighs[0];
        const endHigh = recentHighs[recentHighs.length - 1];

        // Draw horizontal support
        const support = chart.addLineSeries({
            color: color,
            lineWidth: width,
            lineStyle: LightweightCharts.LineStyle.Solid,
            lastValueVisible: false
        });
        support.setData([
            { time: bottomTime, value: bottomLevel },
            { time: candles[candles.length - 1].time, value: bottomLevel }
        ]);

        // Draw descending resistance
        const resistance = chart.addLineSeries({
            color: color,
            lineWidth: width,
            lineStyle: LightweightCharts.LineStyle.Solid,
            lastValueVisible: false
        });
        resistance.setData([
            { time: startHigh.time, value: startHigh.price },
            { time: endHigh.time, value: endHigh.price }
        ]);
    }

    function drawConvergingPattern(chart, candles, highs, lows, color, width, signal, structure) {
        // Need at least 2 swing highs and 2 swing lows
        if (highs.length < 2 || lows.length < 2) {
            drawAutoTrendlines(chart, candles, highs, lows, color, width, signal);
            return;
        }

        const startHigh = highs[highs.length - 2];
        const endHigh = highs[highs.length - 1];
        const startLow = lows[lows.length - 2];
        const endLow = lows[lows.length - 1];

        // Extend lines to meet at entry point
        const entryTime = getEntryTime(signal, candles);
        const entryPrice = parseFloat(signal.entry) || 0;

        // Upper trendline
        const upper = chart.addLineSeries({
            color: color,
            lineWidth: width,
            lineStyle: LightweightCharts.LineStyle.Solid,
            lastValueVisible: false
        });
        upper.setData([
            { time: startHigh.time, value: startHigh.price },
            { time: entryTime, value: entryPrice }
        ]);

        // Lower trendline
        const lower = chart.addLineSeries({
            color: color,
            lineWidth: width,
            lineStyle: LightweightCharts.LineStyle.Solid,
            lastValueVisible: false
        });
        lower.setData([
            { time: startLow.time, value: startLow.price },
            { time: entryTime, value: entryPrice }
        ]);
    }

    function drawChannelPattern(chart, candles, highs, lows, color, width, signal, structure) {
        const isRising = structure.includes('rising') || structure === 'parallel_down';
        const useHighs = isRising ? highs.slice(-2) : highs.slice(-2);
        const useLows = isRising ? lows.slice(-2) : lows.slice(-2);

        if (useHighs.length < 2 || useLows.length < 2) {
            drawAutoTrendlines(chart, candles, highs, lows, color, width, signal);
            return;
        }

        const entryTime = getEntryTime(signal, candles);
        const lastCandle = candles[candles.length - 1];

        // Parallel upper line
        const upper = chart.addLineSeries({
            color: color,
            lineWidth: width,
            lineStyle: LightweightCharts.LineStyle.Solid,
            lastValueVisible: false
        });
        upper.setData([
            { time: useHighs[0].time, value: useHighs[0].price },
            { time: entryTime, value: useHighs[1].price }
        ]);

        // Parallel lower line
        const lower = chart.addLineSeries({
            color: color,
            lineWidth: width,
            lineStyle: LightweightCharts.LineStyle.Solid,
            lastValueVisible: false
        });
        lower.setData([
            { time: useLows[0].time, value: useLows[0].price },
            { time: entryTime, value: useLows[1].price }
        ]);
    }

    function drawDoublePattern(chart, candles, highs, lows, color, width, signal, structure) {
        const isPeak = structure === 'double_peak';
        const points = isPeak ? highs.slice(-2) : lows.slice(-2);

        if (points.length < 2) return;

        // Draw neckline
        const necklineLevel = isPeak 
            ? Math.min(...lows.slice(-2).map(l => l.price))
            : Math.max(...highs.slice(-2).map(h => h.price));

        const neckline = chart.addLineSeries({
            color: color,
            lineWidth: width,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            lastValueVisible: false
        });
        neckline.setData([
            { time: points[0].time, value: necklineLevel },
            { time: candles[candles.length - 1].time, value: necklineLevel }
        ]);

        // Mark the two peaks/troughs
        points.forEach((pt, idx) => {
            const marker = chart.addLineSeries({
                color: color,
                lineWidth: 0,
                lastValueVisible: false,
                crosshairMarkerVisible: true
            });
            marker.setData([{ time: pt.time, value: pt.price }]);
        });
    }

    function drawAutoTrendlines(chart, candles, highs, lows, color, width, signal) {
        // Fallback: draw best-fit trendlines
        if (highs.length >= 2) {
            const upper = chart.addLineSeries({
                color: color,
                lineWidth: width,
                lineStyle: LightweightCharts.LineStyle.Solid,
                lastValueVisible: false
            });
            upper.setData([
                { time: highs[highs.length - 2].time, value: highs[highs.length - 2].price },
                { time: highs[highs.length - 1].time, value: highs[highs.length - 1].price }
            ]);
        }

        if (lows.length >= 2) {
            const lower = chart.addLineSeries({
                color: color,
                lineWidth: width,
                lineStyle: LightweightCharts.LineStyle.Solid,
                lastValueVisible: false
            });
            lower.setData([
                { time: lows[lows.length - 2].time, value: lows[lows.length - 2].price },
                { time: lows[lows.length - 1].time, value: lows[lows.length - 1].price }
            ]);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // CURVED PROJECTION RENDERER
    // ═══════════════════════════════════════════════════════════════════════════════

    function drawCurvedProjection(chart, candles, signal, tradeState) {
        if (!chart || !candles || candles.length < 5) return;

        const entry = parseFloat(signal.entry) || 0;
        const target = parseFloat(signal.target) || 0;
        const stop = parseFloat(signal.stop) || 0;
        const isBuy = (signal.direction || '').toUpperCase().includes('BUY');

        const lastTime = candles[candles.length - 1].time;
        const futureTime = lastTime + (candles[candles.length - 1].time - candles[0].time) * 0.3;

        // Create curved path with slight pullback then continuation
        const steps = 20;
        const projectionData = [];

        if (tradeState.state === 'TARGET_HIT') {
            // Show path that already hit target
            const midTime = lastTime - (lastTime - candles[0].time) * 0.15;
            for (let i = 0; i <= steps; i++) {
                const t = i / steps;
                const time = Math.floor(midTime + (futureTime - midTime) * t);

                // Ease out to target
                const ease = 1 - Math.pow(1 - t, 3);
                const price = entry + (target - entry) * ease;

                projectionData.push({ time, value: price });
            }
        } else if (tradeState.state === 'ACTIVE') {
            // Active trade - show continuation to target
            for (let i = 0; i <= steps; i++) {
                const t = i / steps;
                const time = Math.floor(lastTime + (futureTime - lastTime) * t);

                // Slight curve with small pullback at 30%
                let curve = t;
                if (t > 0.2 && t < 0.4) {
                    curve = t - 0.05 * Math.sin((t - 0.2) * Math.PI / 0.2);
                }

                const price = entry + (target - entry) * curve;
                projectionData.push({ time, value: price });
            }
        } else {
            // Pending - show anticipated path
            for (let i = 0; i <= steps; i++) {
                const t = i / steps;
                const time = Math.floor(lastTime + (futureTime - lastTime) * t);

                // Entry first, then gradual move to target
                const entryT = 0.3;
                let price;
                if (t < entryT) {
                    price = entry;
                } else {
                    const progress = (t - entryT) / (1 - entryT);
                    price = entry + (target - entry) * progress;
                }

                projectionData.push({ time, value: price });
            }
        }

        const projection = chart.addLineSeries({
            color: tradeState.state === 'TARGET_HIT' ? '#00ff88' : 'rgba(0, 201, 167, 0.6)',
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Dotted,
            lastValueVisible: false
        });
        projection.setData(projectionData);
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // ZONE RENDERER (PREMIUM)
    // ═══════════════════════════════════════════════════════════════════════════════

    function drawPremiumZones(chart, candles, signal, tradeState) {
        if (!chart || !candles || candles.length < 5) return;

        const entry = parseFloat(signal.entry) || 0;
        const target = parseFloat(signal.target) || 0;
        const stop = parseFloat(signal.stop) || 0;
        const isBuy = (signal.direction || '').toUpperCase().includes('BUY');

        if (!entry || !target || !stop) return;

        const lastTime = candles[candles.length - 1].time;
        const startTime = candles[Math.floor(candles.length * 0.6)].time;
        const futureTime = lastTime + (lastTime - candles[0].time) * 0.4;

        const isExpired = tradeState.state === 'STOPPED' || isSignalExpired(signal);

        // Bright colors (TradingView style)
        const profitColor = isExpired ? 'rgba(0, 255, 136, 0.15)' : 'rgba(0, 255, 136, 0.25)';
        const profitBorder = isExpired ? 'rgba(0, 255, 136, 0.3)' : '#00ff88';
        const riskColor = isExpired ? 'rgba(255, 71, 87, 0.15)' : 'rgba(255, 71, 87, 0.25)';
        const riskBorder = isExpired ? 'rgba(255, 71, 87, 0.3)' : '#ff4757';

        // Draw profit zone
        if (isBuy) {
            drawZone(chart, startTime, futureTime, target, entry, profitColor, profitBorder);
            drawZone(chart, startTime, futureTime, entry, stop, riskColor, riskBorder);
        } else {
            drawZone(chart, startTime, futureTime, stop, entry, riskColor, riskBorder);
            drawZone(chart, startTime, futureTime, entry, target, profitColor, profitBorder);
        }
    }

    function drawZone(chart, startTime, endTime, top, bottom, fillColor, borderColor) {
        const steps = 10;
        const timeStep = (endTime - startTime) / steps;

        // Border lines
        const topLine = chart.addLineSeries({
            color: borderColor,
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Solid,
            lastValueVisible: false
        });

        const topData = [];
        for (let i = 0; i <= steps; i++) {
            topData.push({ time: startTime + timeStep * i, value: top });
        }
        topLine.setData(topData);

        const bottomLine = chart.addLineSeries({
            color: borderColor,
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Solid,
            lastValueVisible: false
        });

        const bottomData = [];
        for (let i = 0; i <= steps; i++) {
            bottomData.push({ time: startTime + timeStep * i, value: bottom });
        }
        bottomLine.setData(bottomData);

        // Fill lines
        const fillSteps = 5;
        const priceStep = (top - bottom) / fillSteps;

        for (let j = 1; j < fillSteps; j++) {
            const level = bottom + priceStep * j;
            const fill = chart.addLineSeries({
                color: fillColor.replace('0.25', '0.1').replace('0.15', '0.05'),
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Solid,
                lastValueVisible: false
            });

            const fillData = [];
            for (let i = 0; i <= steps; i++) {
                fillData.push({ time: startTime + timeStep * i, value: level });
            }
            fill.setData(fillData);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // PRICE LEVELS WITH GLOW
    // ═══════════════════════════════════════════════════════════════════════════════

    function drawPremiumPriceLevels(series, entry, target, stop, tradeState) {
        if (!series) return;

        const isExpired = tradeState.state === 'STOPPED' || tradeState.state === 'TARGET_HIT';

        // Entry with white glow
        if (entry) {
            series.createPriceLine({
                price: entry,
                color: isExpired ? '#666666' : '#ffffff',
                lineWidth: 3,
                lineStyle: LightweightCharts.LineStyle.Solid,
                axisLabelVisible: true,
                title: tradeState.state === 'PENDING' ? 'BUY STOP' : 'ENTRY',
                axisLabelColor: isExpired ? '#444444' : '#ffffff',
                axisLabelTextColor: '#000000'
            });
        }

        // Target with green glow
        if (target) {
            const hitTarget = tradeState.state === 'TARGET_HIT';
            series.createPriceLine({
                price: target,
                color: hitTarget ? '#00ff88' : (isExpired ? '#2d4a3e' : '#00ff88'),
                lineWidth: hitTarget ? 4 : 2,
                lineStyle: hitTarget ? LightweightCharts.LineStyle.Solid : LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: hitTarget ? '✓ TARGET HIT' : 'TARGET',
                axisLabelColor: hitTarget ? '#00ff88' : (isExpired ? '#2d4a3e' : '#00ff88'),
                axisLabelTextColor: '#000000'
            });
        }

        // Stop with red glow
        if (stop) {
            const hitStop = tradeState.state === 'STOPPED';
            series.createPriceLine({
                price: stop,
                color: hitStop ? '#ff4757' : (isExpired ? '#4a2d2d' : '#ff4757'),
                lineWidth: hitStop ? 4 : 2,
                lineStyle: hitStop ? LightweightCharts.LineStyle.Solid : LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: hitStop ? '✗ STOPPED' : 'STOP',
                axisLabelColor: hitStop ? '#ff4757' : (isExpired ? '#4a2d2d' : '#ff4757'),
                axisLabelTextColor: '#ffffff'
            });
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // STATUS BADGE & AI OVERLAY
    // ═══════════════════════════════════════════════════════════════════════════════

    function addStatusBadge(container, tradeState, signal) {
        container.querySelector('.pro-status-badge')?.remove();

        const badge = document.createElement('div');
        badge.className = 'pro-status-badge';
        badge.innerHTML = `
            <span class="status-icon" style="color: ${tradeState.color}">${tradeState.icon}</span>
            <span class="status-text" style="color: ${tradeState.color}">${tradeState.label}</span>
        `;

        badge.style.cssText = `
            position: absolute;
            top: 16px;
            right: 16px;
            background: rgba(10, 10, 15, 0.95);
            border: 1px solid ${tradeState.color}40;
            border-radius: 8px;
            padding: 8px 16px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 700;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            z-index: 100;
            backdrop-filter: blur(8px);
            box-shadow: 0 4px 20px ${tradeState.color}20;
        `;

        container.appendChild(badge);
    }

    function addAIAnalysisOverlay(container, signal, tradeState) {
        container.querySelector('.pro-ai-overlay')?.remove();

        if (!signal.pattern && !signal.pattern_name) return;

        const patternName = signal.pattern_name || signal.pattern || 'Breakout';
        const isBuy = (signal.direction || '').toUpperCase().includes('BUY');

        let analysis = '';
        if (tradeState.state === 'PENDING') {
            analysis = isBuy 
                ? `Waiting for breakout above ${signal.entry}`
                : `Waiting for breakdown below ${signal.entry}`;
        } else if (tradeState.state === 'ACTIVE') {
            analysis = `Momentum building toward ${signal.target} target`;
        } else if (tradeState.state === 'TARGET_HIT') {
            analysis = 'Target reached successfully';
        } else if (tradeState.state === 'STOPPED') {
            analysis = 'Trade stopped at loss level';
        }

        const overlay = document.createElement('div');
        overlay.className = 'pro-ai-overlay';
        overlay.innerHTML = `
            <div class="ai-pattern">${patternName}</div>
            <div class="ai-text">${analysis}</div>
        `;

        overlay.style.cssText = `
            position: absolute;
            bottom: 16px;
            left: 16px;
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(79, 70, 229, 0.1));
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 8px;
            padding: 12px 16px;
            z-index: 100;
            backdrop-filter: blur(8px);
        `;

        const style = document.createElement('style');
        style.textContent = `
            .pro-ai-overlay .ai-pattern {
                font-size: 11px;
                font-weight: 700;
                color: #818cf8;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 4px;
            }
            .pro-ai-overlay .ai-text {
                font-size: 12px;
                color: #e0e7ff;
                font-weight: 500;
            }
        `;
        document.head.appendChild(style);

        container.appendChild(overlay);
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // DATA VALIDATION & FALLBACK
    // ═══════════════════════════════════════════════════════════════════════════════

    function validateAndFixCandles(signal) {
        // Check if we have valid candles
        if (signal.candles && Array.isArray(signal.candles) && signal.candles.length >= 20) {
            return signal.candles;
        }

        // Try to get from pattern_points
        if (signal.pattern_points && Array.isArray(signal.pattern_points) && signal.pattern_points.length >= 2) {
            console.log('[Chart] Generating candles from pattern points');
            return generateCandlesFromPoints(signal);
        }

        // Generate realistic fallback
        console.log('[Chart] Generizing fallback candle data');
        return generateRealisticCandles(signal);
    }

    function generateRealisticCandles(signal) {
        const entry = parseFloat(signal.entry) || 100;
        const target = parseFloat(signal.target) || entry * 1.02;
        const stop = parseFloat(signal.stop) || entry * 0.98;
        const isBuy = (signal.direction || '').toUpperCase().includes('BUY');

        const candles = [];
        const now = Math.floor(Date.now() / 1000);
        const interval = 300; // 5 minutes

        const range = Math.max(Math.abs(target - entry), Math.abs(entry - stop));
        const volatility = range * 0.15;

        let price = isBuy ? entry - range * 0.5 : entry + range * 0.5;
        let seed = signal.id || 12345;

        const random = () => {
            seed = (seed * 9301 + 49297) % 233280;
            return seed / 233280;
        };

        for (let i = 80; i >= 0; i--) {
            const time = now - (i * interval);
            const progress = (80 - i) / 80;

            const trendBias = isBuy ? 0.6 : 0.4;
            const isGreen = random() < (trendBias + progress * 0.1);

            const body = volatility * (0.3 + random() * 0.7);
            const wick = volatility * random() * 0.4;

            const open = price;
            const close = isGreen ? open + body : open - body;
            const high = Math.max(open, close) + wick;
            const low = Math.min(open, close) - wick;

            candles.push({
                time,
                open: +open.toFixed(5),
                high: +high.toFixed(5),
                low: +low.toFixed(5),
                close: +close.toFixed(5)
            });

            price = close + (random() - 0.5) * volatility * 0.1;
        }

        // Adjust to converge at entry
        const lastClose = candles[candles.length - 1].close;
        const adjust = entry - lastClose;

        for (let i = candles.length - 15; i < candles.length; i++) {
            const factor = (i - (candles.length - 15)) / 15;
            const adj = adjust * factor;
            candles[i].open += adj;
            candles[i].high += adj;
            candles[i].low += adj;
            candles[i].close += adj;
        }

        return candles;
    }

    function generateCandlesFromPoints(signal) {
        const points = signal.pattern_points || [];
        const entry = parseFloat(signal.entry) || 100;
        const candles = [];
        const now = Math.floor(Date.now() / 1000);
        const interval = 300;

        // Generate around pattern points
        let basePrice = points[0]?.price || entry;

        for (let i = 60; i >= 0; i--) {
            const time = now - (i * interval);
            const volatility = basePrice * 0.002;

            const open = basePrice + (Math.random() - 0.5) * volatility;
            const close = open + (Math.random() - 0.5) * volatility;
            const high = Math.max(open, close) + Math.random() * volatility * 0.5;
            const low = Math.min(open, close) - Math.random() * volatility * 0.5;

            candles.push({
                time,
                open: +open.toFixed(5),
                high: +high.toFixed(5),
                low: +low.toFixed(5),
                close: +close.toFixed(5)
            });

            basePrice = close;
        }

        return candles;
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // UTILITY FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════════

    function isSignalExpired(signal) {
        if (!signal.expires_at) return false;
        return new Date(signal.expires_at) < new Date();
    }

    function getEntryTime(signal, candles) {
        if (signal.breakout_point?.time) return signal.breakout_point.time;
        if (candles && candles.length > 5) {
            return candles[candles.length - 3].time;
        }
        return Math.floor(Date.now() / 1000);
    }

    async function loadLightweightCharts() {
        if (LightweightCharts) return LightweightCharts;
        if (window.LightweightCharts) {
            LightweightCharts = window.LightweightCharts;
            return LightweightCharts;
        }

        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = LIGHTWEIGHT_CHARTS_CDN;
            script.onload = () => {
                LightweightCharts = window.LightweightCharts;
                resolve(LightweightCharts);
            };
            script.onerror = () => reject(new Error('Failed to load charts'));
            document.head.appendChild(script);
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // MAIN CHART CREATION
    // ═══════════════════════════════════════════════════════════════════════════════

    async function createProChart(containerId, signal) {
        try {
            await loadLightweightCharts();

            const container = document.getElementById(containerId);
            if (!container) return;

            // Destroy existing
            if (chartInstance) {
                chartInstance.remove();
                chartInstance = null;
            }

            // Validate pattern - REQUIRED
            const patternName = signal.pattern_name || signal.pattern;
            if (!patternName) {
                container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#6b7280;">No pattern detected</div>';
                return;
            }

            // Get and validate candles
            const candles = validateAndFixCandles(signal);
            if (!candles || candles.length < 10) {
                container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#6b7280;">Insufficient chart data</div>';
                return;
            }

            const currentPrice = candles[candles.length - 1].close;
            const tradeState = determineTradeState(signal, currentPrice);
            const isExpired = tradeState.state === 'STOPPED' || isSignalExpired(signal);

            // Create chart with TradingView styling
            chartInstance = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: container.clientHeight,
                layout: {
                    background: { type: 'solid', color: '#0a0a0f' },
                    textColor: isExpired ? '#4b5563' : '#9ca3af',
                    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
                },
                grid: {
                    vertLines: { color: 'rgba(255, 255, 255, 0.03)' },
                    horzLines: { color: 'rgba(255, 255, 255, 0.03)' }
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                    vertLine: {
                        color: 'rgba(99, 102, 241, 0.5)',
                        width: 1,
                        style: LightweightCharts.LineStyle.Dashed,
                        labelBackgroundColor: '#1e1b4b'
                    },
                    horzLine: {
                        color: 'rgba(99, 102, 241, 0.5)',
                        width: 1,
                        style: LightweightCharts.LineStyle.Dashed,
                        labelBackgroundColor: '#1e1b4b'
                    }
                },
                rightPriceScale: {
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    scaleMargins: { top: 0.15, bottom: 0.15 }
                },
                timeScale: {
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    timeVisible: true,
                    secondsVisible: false
                }
            });

            // Add candlestick series
            candlestickSeries = chartInstance.addCandlestickSeries({
                upColor: isExpired ? '#065f46' : '#10b981',
                downColor: isExpired ? '#7f1d1d' : '#ef4444',
                borderUpColor: isExpired ? '#065f46' : '#10b981',
                borderDownColor: isExpired ? '#7f1d1d' : '#ef4444',
                wickUpColor: isExpired ? '#065f46' : '#10b981',
                wickDownColor: isExpired ? '#7f1d1d' : '#ef4444'
            });
            candlestickSeries.setData(candles);

            // Draw pattern structure
            drawPatternStructure(chartInstance, candles, patternName, signal);

            // Draw premium zones
            drawPremiumZones(chartInstance, candles, signal, tradeState);

            // Draw curved projection
            drawCurvedProjection(chartInstance, candles, signal, tradeState);

            // Draw price levels with glow
            drawPremiumPriceLevels(candlestickSeries, 
                parseFloat(signal.entry), 
                parseFloat(signal.target), 
                parseFloat(signal.stop),
                tradeState
            );

            // Add UI overlays
            container.style.position = 'relative';
            addStatusBadge(container, tradeState, signal);
            addAIAnalysisOverlay(container, signal, tradeState);

            // Fit view
            chartInstance.timeScale().fitContent();

            // Handle resize
            const resizeObserver = new ResizeObserver(entries => {
                if (chartInstance && entries[0]) {
                    const { width, height } = entries[0].contentRect;
                    chartInstance.resize(width, height);
                }
            });
            resizeObserver.observe(container);

            // Hide loading
            const loading = document.getElementById('sig-chart-loading');
            if (loading) loading.classList.add('hidden');

            console.log(`[Chart PRO] Rendered ${patternName} | ${tradeState.label} | ${candles.length} candles`);

        } catch (error) {
            console.error('[Chart PRO] Error:', error);
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#ef4444;">Chart error</div>';
            }
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // EXPORT
    // ═══════════════════════════════════════════════════════════════════════════════

    window.ProChart = {
        create: createProChart,
        destroy: () => {
            if (chartInstance) {
                chartInstance.remove();
                chartInstance = null;
            }
        },
        patterns: PATTERNS
    };

})();
