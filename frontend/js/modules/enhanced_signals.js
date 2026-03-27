// frontend/js/modules/enhanced_signals.js
window.EnhancedSignalsPage = (function() {
    let signalsData = [];
    let filteredSignals = [];
    let currentFilters = {
        confidence: 60,
        asset: 'all',
        country: 'all', 
        pattern: 'all',
        status: 'all'
    };

    function init() {
        setupEventListeners();
        loadSignals();
        setupRealTimeUpdates();
    }

    function setupEventListeners() {
        // Filter controls
        document.querySelectorAll('input[type="radio"]').forEach(radio => {
            radio.addEventListener('change', handleFilterChange);
        });

        // Mobile filter toggle
        const filterToggle = document.getElementById('filterToggle');
        if (filterToggle) {
            filterToggle.addEventListener('click', toggleMobileFilters);
        }

        // Modal controls
        const closeModal = document.getElementById('closeModal');
        if (closeModal) {
            closeModal.addEventListener('click', closeSignalModal);
        }

        // Tab controls
        document.getElementById('aiDrivenTab')?.addEventListener('click', () => switchTab('ai'));
        document.getElementById('patternTab')?.addEventListener('click', () => switchTab('pattern'));
    }

    async function loadSignals() {
        try {
            UI.showLoading('Loading signals...');
            
            const response = await API.get('/signals/enhanced', {
                params: currentFilters
            });
            
            if (response.data) {
                signalsData = response.data;
                applyFilters();
                renderSignals();
            }
        } catch (error) {
            console.error('Error loading signals:', error);
            UI.showToast('Failed to load signals', 'error');
            
            // Handle 402 payment required
            if (error.response?.status === 402) {
                PipwaysUsage.showUpgradeModal('signals');
            }
        } finally {
            UI.hideLoading();
        }
    }

    function handleFilterChange() {
        // Update current filters
        currentFilters.confidence = document.querySelector('input[name="confidence"]:checked')?.value || 60;
        currentFilters.asset = document.querySelector('input[name="asset"]:checked')?.value || 'all';
        currentFilters.country = document.querySelector('input[name="country"]:checked')?.value || 'all';
        currentFilters.pattern = document.querySelector('input[name="pattern"]:checked')?.value || 'all';
        currentFilters.status = document.querySelector('input[name="status"]:checked')?.value || 'all';
        
        applyFilters();
        renderSignals();
    }

    function applyFilters() {
        filteredSignals = signalsData.filter(signal => {
            if (signal.confidence < parseInt(currentFilters.confidence)) return false;
            if (currentFilters.asset !== 'all' && signal.asset_type !== currentFilters.asset) return false;
            if (currentFilters.country !== 'all' && signal.country !== currentFilters.country && signal.country !== 'all') return false;
            if (currentFilters.pattern !== 'all' && signal.pattern.toLowerCase() !== currentFilters.pattern) return false;
            return true;
        });
    }

    function renderSignals() {
        const grid = document.getElementById('signalsGrid');
        if (!grid) return;

        grid.innerHTML = '';

        if (filteredSignals.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <i class="fas fa-chart-line text-4xl text-gray-600 mb-4"></i>
                    <h3 class="text-xl font-semibold text-gray-400 mb-2">No signals found</h3>
                    <p class="text-gray-500">Try adjusting your filters or check back later for new signals.</p>
                </div>
            `;
            return;
        }

        filteredSignals.forEach(signal => {
            const card = createSignalCard(signal);
            grid.appendChild(card);
        });
    }

    function createSignalCard(signal) {
        const changeClass = signal.price_change?.startsWith('+') ? 'text-green-400' : 'text-red-400';
        const directionClass = signal.direction.includes('BUY') ? 'buy-stop' : 'sell-stop';
        
        const card = document.createElement('div');
        card.className = 'signal-card p-4';
        card.innerHTML = `
            <div class="flex items-start justify-between mb-4">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-red-500 flex items-center justify-center">
                        <span class="text-white text-xs font-bold">${getCountryFlags(signal.symbol)}</span>
                    </div>
                    <div>
                        <h3 class="font-bold text-white">${signal.symbol}</h3>
                        <p class="text-xs text-gray-400">${signal.full_name || signal.symbol}</p>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-lg font-bold text-white">${signal.current_price || signal.entry}</div>
                    <div class="text-xs ${changeClass}">${signal.price_change || ''} (${signal.price_change_percent || ''})</div>
                </div>
            </div>

            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-2">
                    <span class="live-badge">LIVE TRADE</span>
                    <span class="pattern-badge">${signal.pattern}</span>
                </div>
                <span class="timeframe-badge">${signal.timeframe}</span>
            </div>

            <div class="mb-4">
                <div class="${directionClass} text-center">${signal.direction}</div>
            </div>

            <div class="trade-levels">
                <div class="level-item">
                    <div class="level-label">Entry</div>
                    <div class="level-value level-entry">${signal.entry}</div>
                </div>
                <div class="level-item">
                    <div class="level-label">Target</div>
                    <div class="level-value level-target">${signal.target}</div>
                </div>
                <div class="level-item">
                    <div class="level-label">Stop</div>
                    <div class="level-value level-stop">${signal.stop}</div>
                </div>
            </div>

            <div class="mb-4">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs text-gray-400">News Sentiment</span>
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-red-400">${signal.sentiment_bearish || 50}% ▼</span>
                        <span class="text-xs text-green-400">${signal.sentiment_bullish || 50}% ▲</span>
                    </div>
                </div>
                <div class="sentiment-bar">
                    <div class="sentiment-fill ${(signal.sentiment_bullish || 50) > (signal.sentiment_bearish || 50) ? 'sentiment-bullish' : 'sentiment-bearish'}" 
                         style="width: ${Math.max(signal.sentiment_bearish || 50, signal.sentiment_bullish || 50)}%"></div>
                </div>
            </div>

            <div class="mini-chart mb-4 relative">
                <div class="absolute inset-2">
                    <!-- Simulated pattern based on signal data -->
                    ${renderMiniChart(signal)}
                </div>
                <div class="chart-overlay">
                    <div class="text-xs text-gray-400">${signal.timeframe} Pattern Analysis</div>
                </div>
            </div>

            <div class="text-center mb-4">
                <span class="text-xs text-gray-400">Expires: </span>
                <span class="text-xs expiry-time">${calculateTimeRemaining(signal.expires_at)}</span>
            </div>

            <div class="flex gap-2">
                <button class="learn-btn flex-1" onclick="EnhancedSignalsPage.showSignalDetails(${signal.id})">LEARN MORE</button>
                <button class="install-ea-btn flex-1" onclick="EnhancedSignalsPage.viewChart(${signal.id})">VIEW CHART</button>
            </div>
        `;
        
        return card;
    }

    function renderMiniChart(signal) {
        // Create simple candlestick representation based on pattern
        const candlesticks = [];
        for (let i = 0; i < 6; i++) {
            const isGreen = Math.random() > 0.5;
            const height = 6 + Math.random() * 8;
            candlesticks.push(`
                <div class="absolute bottom-1/3 w-1 bg-${isGreen ? 'green' : 'red'}-500" 
                     style="left: ${12 + i * 4}px; height: ${height}px;"></div>
            `);
        }
        
        // Add pattern lines based on signal.pattern
        let patternLines = '';
        if (signal.pattern === 'FLAG') {
            patternLines = `
                <div class="absolute bottom-1/2 left-8 w-20 h-0.5 bg-purple-400 opacity-60"></div>
                <div class="absolute bottom-1/3 left-8 w-20 h-0.5 bg-purple-400 opacity-60"></div>
            `;
        }
        
        return candlesticks.join('') + patternLines;
    }

    function showSignalDetails(signalId) {
        const signal = signalsData.find(s => s.id === signalId);
        if (!signal) return;

        // Update modal with signal data
        document.getElementById('modalTitle').textContent = `${signal.symbol} - ${signal.full_name}`;
        
        // Load detailed chart analysis
        loadChartAnalysis(signalId);
        
        // Show modal
        const modal = document.getElementById('signalModal');
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    async function loadChartAnalysis(signalId) {
        try {
            const response = await API.get(`/signals/${signalId}/chart-analysis`);
            if (response.data) {
                updateModalWithAnalysis(response.data);
            }
        } catch (error) {
            console.error('Error loading chart analysis:', error);
        }
    }

    function viewChart(signalId) {
        showSignalDetails(signalId);
    }

    function setupRealTimeUpdates() {
        // Update prices every 5 seconds
        setInterval(async () => {
            if (signalsData.length > 0) {
                try {
                    await loadSignals(); // Refresh all signal data
                } catch (error) {
                    console.error('Error updating signals:', error);
                }
            }
        }, 5000);
    }

    function getCountryFlags(symbol) {
        const flagMap = {
            'AUDCAD': '🇦🇺🇨🇦',
            'EURUSD': '🇪🇺🇺🇸',
            'GBPJPY': '🇬🇧🇯🇵',
            'CHINA50': '🇨🇳',
            'TSLA': '🇺🇸',
            // Add more mappings
        };
        return flagMap[symbol.replace('/', '')] || '🌍';
    }

    function calculateTimeRemaining(expiresAt) {
        if (!expiresAt) return 'N/A';
        
        const now = new Date();
        const expiry = new Date(expiresAt);
        const diff = expiry - now;
        
        if (diff <= 0) return 'Expired';
        
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        
        if (hours > 24) {
            const days = Math.floor(hours / 24);
            const remainingHours = hours % 24;
            return `${days}d ${remainingHours}h`;
        }
        
        return `${hours}h ${minutes}m`;
    }

    // Public API
    return {
        init,
        showSignalDetails,
        viewChart,
        loadSignals,
        applyFilters
    };
})();

// Auto-initialize if we're on the signals page
if (window.location.pathname.includes('/signals') || document.getElementById('signalsGrid')) {
    document.addEventListener('DOMContentLoaded', () => {
        EnhancedSignalsPage.init();
    });
}
