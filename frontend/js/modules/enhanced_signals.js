// Enhanced Signals Module for Pipways Dashboard
// Fixed version - uses fetch directly instead of window.API
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
    let currentTab = 'ai';
    let isLoading = false;

    // Helper function for API calls
    async function apiGet(endpoint) {
        const token = localStorage.getItem('token');
        const response = await fetch(endpoint, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = new Error(`API Error: ${response.status}`);
            error.response = { status: response.status };
            throw error;
        }
        
        return response.json();
    }

    async function apiPost(endpoint, data = {}) {
        const token = localStorage.getItem('token');
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = new Error(`API Error: ${response.status}`);
            error.response = { status: response.status };
            throw error;
        }
        
        return response.json();
    }

    function init() {
        console.log('Enhanced Signals Page initializing...');
        setupEventListeners();
        loadSignals();
        setupRealTimeUpdates();
        setupResponsiveHandling();
    }

    function setupEventListeners() {
        // Filter controls
        document.querySelectorAll('input[type="radio"]').forEach(radio => {
            radio.addEventListener('change', handleFilterChange);
        });

        // Filter buttons
        const applyFiltersBtn = document.getElementById('applyFilters');
        const resetFiltersBtn = document.getElementById('resetFilters');
        
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', handleApplyFilters);
        }
        
        if (resetFiltersBtn) {
            resetFiltersBtn.addEventListener('click', handleResetFilters);
        }

        // Mobile filter controls
        const filterToggle = document.getElementById('filterToggle');
        const closeMobileFilter = document.getElementById('closeMobileFilter');
        const mobileOverlay = document.getElementById('mobileOverlay');
        
        if (filterToggle) {
            filterToggle.addEventListener('click', toggleMobileFilters);
        }
        
        if (closeMobileFilter) {
            closeMobileFilter.addEventListener('click', closeMobileFilters);
        }
        
        if (mobileOverlay) {
            mobileOverlay.addEventListener('click', closeMobileFilters);
        }

        // Modal controls
        const closeModal = document.getElementById('closeModal');
        if (closeModal) {
            closeModal.addEventListener('click', closeSignalModal);
        }

        // Tab controls
        const aiDrivenTab = document.getElementById('aiDrivenTab');
        const patternTab = document.getElementById('patternTab');
        
        if (aiDrivenTab) {
            aiDrivenTab.addEventListener('click', () => switchTab('ai'));
        }
        
        if (patternTab) {
            patternTab.addEventListener('click', () => switchTab('pattern'));
        }

        // Load more button
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', loadMoreSignals);
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', handleKeyboardShortcuts);
    }

    function setupResponsiveHandling() {
        window.addEventListener('resize', handleWindowResize);
        handleWindowResize();
    }

    function handleWindowResize() {
        const isMobile = window.innerWidth < 768;
        const sidebar = document.getElementById('filterSidebar');
        if (!isMobile && sidebar) {
            sidebar.classList.remove('active');
        }
    }

    function handleKeyboardShortcuts(e) {
        if (e.key === 'Escape') {
            const modal = document.getElementById('signalModal');
            if (modal && !modal.classList.contains('hidden')) {
                closeSignalModal();
            }
        }
        if (e.key === 'r' && e.ctrlKey) {
            e.preventDefault();
            loadSignals();
        }
    }

    async function loadSignals() {
        if (isLoading) return;
        
        try {
            isLoading = true;
            showLoadingState();
            
            const params = new URLSearchParams({
                confidence: currentFilters.confidence,
                asset_type: currentFilters.asset,
                country: currentFilters.country,
                pattern: currentFilters.pattern,
                status: currentFilters.status
            });
            
            console.log('Loading signals with params:', params.toString());
            
            // Use direct fetch instead of window.API
            const data = await apiGet(`/signals/enhanced?${params.toString()}`);
            
            if (data && Array.isArray(data)) {
                signalsData = data;
                console.log(`Loaded ${signalsData.length} signals`);
                applyFilters();
                renderSignals();
                updateStats();
            } else {
                throw new Error('Invalid data received from API');
            }
            
        } catch (error) {
            console.error('Error loading signals:', error);
            handleSignalsError(error);
        } finally {
            isLoading = false;
            hideLoadingState();
        }
    }

    async function loadMoreSignals() {
        showToast('All available signals loaded', 'info');
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        if (loadMoreBtn) {
            loadMoreBtn.style.display = 'none';
        }
    }

    function handleSignalsError(error) {
        console.error('Signals error:', error);
        
        // Handle 402 payment required
        if (error.response?.status === 402) {
            if (window.PipwaysUsage?.showUpgradeModal) {
                window.PipwaysUsage.showUpgradeModal('signals', {
                    title: 'Enhanced Market Signals',
                    message: 'Upgrade to Pro to access advanced signal filtering and analysis.',
                    features: [
                        'View all active signals',
                        'Advanced pattern filtering',
                        'Detailed chart analysis',
                        'Real-time price updates',
                        'Email signal alerts'
                    ]
                });
            }
            return;
        }
        
        // Handle 401 unauthorized
        if (error.response?.status === 401) {
            showErrorState('Please log in to view signals');
            return;
        }
        
        showErrorState(error.message || 'Failed to load signals');
    }

    function showLoadingState() {
        const grid = document.getElementById('signalsGrid');
        if (!grid) return;

        grid.innerHTML = `
            <div class="col-span-full text-center py-12">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
                <p class="text-gray-400">Loading market signals...</p>
            </div>
        `;
    }

    function hideLoadingState() {
        // Loading state is replaced by actual content in renderSignals()
    }

    function showErrorState(message) {
        const grid = document.getElementById('signalsGrid');
        if (!grid) return;

        grid.innerHTML = `
            <div class="col-span-full text-center py-12">
                <i class="fas fa-exclamation-triangle text-4xl text-red-500 mb-4"></i>
                <h3 class="text-xl font-semibold text-gray-300 mb-2">Unable to Load Signals</h3>
                <p class="text-gray-500 mb-4">${escapeHtml(message)}</p>
                <button onclick="EnhancedSignalsPage.loadSignals()" 
                        class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                    Try Again
                </button>
            </div>
        `;
    }

    function handleFilterChange(e) {
        const filterType = e.target.name;
        const filterValue = e.target.value;
        
        console.log(`Filter changed: ${filterType} = ${filterValue}`);
        currentFilters[filterType] = filterValue;
        applyFilters();
        renderSignals();
        
        if (window.innerWidth < 768) {
            setTimeout(closeMobileFilters, 300);
        }
    }

    function handleApplyFilters() {
        console.log('Applying filters:', currentFilters);
        loadSignals();
    }

    function handleResetFilters() {
        console.log('Resetting filters');
        
        currentFilters = {
            confidence: 60,
            asset: 'all',
            country: 'all',
            pattern: 'all',
            status: 'all'
        };
        
        // Reset radio buttons
        const conf60 = document.getElementById('conf60');
        const assetAll = document.getElementById('assetAll');
        const countryAll = document.getElementById('countryAll');
        const patternAll = document.getElementById('patternAll');
        const statusAll = document.getElementById('statusAll');
        
        if (conf60) conf60.checked = true;
        if (assetAll) assetAll.checked = true;
        if (countryAll) countryAll.checked = true;
        if (patternAll) patternAll.checked = true;
        if (statusAll) statusAll.checked = true;
        
        loadSignals();
    }

    function applyFilters() {
        if (!signalsData || !Array.isArray(signalsData)) {
            filteredSignals = [];
            return;
        }
        
        filteredSignals = signalsData.filter(signal => {
            if (signal.confidence < parseInt(currentFilters.confidence)) return false;
            if (currentFilters.asset !== 'all' && signal.asset_type !== currentFilters.asset) return false;
            if (currentFilters.country !== 'all' && 
                signal.country !== currentFilters.country && 
                signal.country !== 'all') return false;
            if (currentFilters.pattern !== 'all' && 
                signal.pattern?.toLowerCase() !== currentFilters.pattern) return false;
            if (currentFilters.status !== 'all' && signal.status !== currentFilters.status) return false;
            return true;
        });
        
        console.log(`Filtered ${filteredSignals.length} signals from ${signalsData.length} total`);
    }

    function renderSignals() {
        const grid = document.getElementById('signalsGrid');
        if (!grid) return;

        // Update results count
        const resultsCount = document.getElementById('resultsCount');
        if (resultsCount) {
            resultsCount.textContent = filteredSignals.length;
        }

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

        grid.innerHTML = '';
        filteredSignals.forEach((signal, index) => {
            const card = createSignalCard(signal, index);
            grid.appendChild(card);
        });
    }

    function createSignalCard(signal, index) {
        const changeClass = signal.price_change?.startsWith('+') ? 'text-green-400' : 'text-red-400';
        const directionClass = signal.direction?.includes('BUY') ? 'buy-stop' : 'sell-stop';
        
        const card = document.createElement('div');
        card.className = 'signal-card p-4';
        card.style.animationDelay = `${index * 50}ms`;
        
        const symbol = signal.symbol || 'Unknown';
        const fullName = signal.full_name || symbol;
        const currentPrice = signal.current_price || signal.entry || '0.0000';
        const priceChange = signal.price_change || '';
        const priceChangePercent = signal.price_change_percent || '';
        const pattern = signal.pattern || 'PATTERN';
        const timeframe = signal.timeframe || '1H';
        const direction = signal.direction || 'BUY';
        const entry = signal.entry || '0.0000';
        const target = signal.target || '0.0000';
        const stop = signal.stop || '0.0000';
        const sentimentBearish = signal.sentiment_bearish || 50;
        const sentimentBullish = signal.sentiment_bullish || 50;
        const expiry = signal.expiry || 'N/A';
        const confidence = signal.confidence || 75;
        
        card.innerHTML = `
            <div class="flex items-start justify-between mb-4">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                        <span class="text-white text-xs font-bold">${getCountryFlags(symbol)}</span>
                    </div>
                    <div>
                        <h3 class="font-bold text-white">${escapeHtml(symbol)}</h3>
                        <p class="text-xs text-gray-400">${escapeHtml(fullName)}</p>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-lg font-bold text-white font-mono">${escapeHtml(currentPrice)}</div>
                    <div class="text-xs ${changeClass}">${escapeHtml(priceChange)} (${escapeHtml(priceChangePercent)})</div>
                </div>
            </div>

            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-2">
                    <span class="live-badge">LIVE</span>
                    <span class="pattern-badge">${escapeHtml(pattern)}</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="timeframe-badge">${escapeHtml(timeframe)}</span>
                    <span class="text-xs text-purple-400 font-bold">${confidence}%</span>
                </div>
            </div>

            <div class="mb-4">
                <div class="${directionClass} text-center">${escapeHtml(direction)}</div>
            </div>

            <div class="trade-levels">
                <div class="level-item">
                    <div class="level-label">Entry</div>
                    <div class="level-value level-entry font-mono">${escapeHtml(entry)}</div>
                </div>
                <div class="level-item">
                    <div class="level-label">Target</div>
                    <div class="level-value level-target font-mono">${escapeHtml(target)}</div>
                </div>
                <div class="level-item">
                    <div class="level-label">Stop Loss</div>
                    <div class="level-value level-stop font-mono">${escapeHtml(stop)}</div>
                </div>
            </div>

            <div class="mb-4">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs text-gray-400">Sentiment</span>
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-red-400">${sentimentBearish}%</span>
                        <span class="text-xs text-green-400">${sentimentBullish}%</span>
                    </div>
                </div>
                <div class="sentiment-bar">
                    <div class="sentiment-fill ${sentimentBullish > sentimentBearish ? 'sentiment-bullish' : 'sentiment-bearish'}" 
                         style="width: ${Math.max(sentimentBearish, sentimentBullish)}%"></div>
                </div>
            </div>

            <div class="text-center mb-4">
                <span class="text-xs text-gray-400">Expires: </span>
                <span class="text-xs expiry-time">${escapeHtml(expiry)}</span>
            </div>

            <div class="flex gap-2">
                <button class="learn-btn flex-1" onclick="EnhancedSignalsPage.showSignalDetails(${signal.id})">
                    <i class="fas fa-info-circle mr-1"></i> Details
                </button>
                <button class="install-ea-btn flex-1" onclick="EnhancedSignalsPage.viewChart(${signal.id})">
                    <i class="fas fa-chart-line mr-1"></i> Chart
                </button>
            </div>
        `;
        
        return card;
    }

    function showSignalDetails(signalId) {
        const signal = signalsData.find(s => s.id === signalId);
        if (!signal) {
            showToast('Signal not found', 'error');
            return;
        }

        console.log('Showing details for signal:', signalId);
        
        const modalTitle = document.getElementById('modalTitle');
        if (modalTitle) {
            modalTitle.textContent = `${signal.symbol} - ${signal.full_name || signal.symbol}`;
        }
        
        loadChartAnalysis(signalId);
        
        const modal = document.getElementById('signalModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }

    async function loadChartAnalysis(signalId) {
        const modalContent = document.getElementById('modalContent');
        if (!modalContent) return;
        
        modalContent.innerHTML = `
            <div class="text-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-4"></div>
                <p class="text-gray-400">Loading detailed analysis...</p>
            </div>
        `;
        
        try {
            const data = await apiGet(`/signals/${signalId}/chart-analysis`);
            
            if (data) {
                updateModalWithAnalysis(data);
            } else {
                throw new Error('No analysis data received');
            }
            
        } catch (error) {
            console.error('Error loading chart analysis:', error);
            
            if (error.response?.status === 402) {
                modalContent.innerHTML = `
                    <div class="text-center py-8">
                        <i class="fas fa-lock text-4xl text-purple-500 mb-4"></i>
                        <h3 class="text-xl font-semibold text-white mb-2">Pro Feature</h3>
                        <p class="text-gray-400 mb-6">Upgrade to Pro to access detailed chart analysis.</p>
                        <button onclick="window.location.hash='billing'" 
                                class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-colors">
                            Upgrade to Pro
                        </button>
                    </div>
                `;
            } else {
                modalContent.innerHTML = `
                    <div class="text-center py-8">
                        <i class="fas fa-exclamation-triangle text-4xl text-red-500 mb-4"></i>
                        <h3 class="text-xl font-semibold text-gray-300 mb-2">Analysis Error</h3>
                        <p class="text-gray-500">Failed to load analysis. Please try again.</p>
                    </div>
                `;
            }
        }
    }

    function updateModalWithAnalysis(data) {
        const modalContent = document.getElementById('modalContent');
        if (!modalContent) return;
        
        const signal = data.signal;
        const analysis = data.analysis;
        
        modalContent.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div class="space-y-4">
                    <div class="flex items-center gap-4">
                        <div class="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                            <span class="text-white text-sm font-bold">${getCountryFlags(signal.symbol)}</span>
                        </div>
                        <div>
                            <div class="text-2xl font-bold text-white font-mono">${escapeHtml(signal.current_price || signal.entry)}</div>
                            <div class="text-sm ${signal.price_change?.startsWith('+') ? 'text-green-400' : 'text-red-400'}">
                                ${escapeHtml(signal.price_change || '')} (${escapeHtml(signal.price_change_percent || '')})
                            </div>
                        </div>
                    </div>
                    
                    <div class="flex items-center gap-3">
                        <span class="live-badge">LIVE</span>
                        <span class="pattern-badge">${escapeHtml(signal.pattern || 'PATTERN')}</span>
                        <span class="timeframe-badge">${escapeHtml(signal.timeframe || '1H')}</span>
                    </div>
                    
                    <div class="${signal.direction?.includes('BUY') ? 'buy-stop' : 'sell-stop'} text-center py-2">
                        ${escapeHtml(signal.direction || 'BUY')}
                    </div>
                </div>
                
                <div class="space-y-4">
                    <h3 class="font-bold text-white">Trade Levels</h3>
                    <div class="trade-levels">
                        <div class="level-item">
                            <div class="level-label">Entry</div>
                            <div class="level-value level-entry font-mono">${escapeHtml(signal.entry)}</div>
                        </div>
                        <div class="level-item">
                            <div class="level-label">Target</div>
                            <div class="level-value level-target font-mono">${escapeHtml(signal.target)}</div>
                        </div>
                        <div class="level-item">
                            <div class="level-label">Stop Loss</div>
                            <div class="level-value level-stop font-mono">${escapeHtml(signal.stop)}</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-gray-700 rounded-lg p-6 mb-6">
                <h3 class="text-lg font-bold text-white mb-4 flex items-center">
                    <i class="fas fa-lightbulb text-yellow-400 mr-2"></i>
                    Analysis
                </h3>
                <div class="space-y-4 text-gray-300">
                    <p>${escapeHtml(analysis?.pattern_description || 'Pattern identified with clear entry and exit levels.')}</p>
                    <p><strong>Risk/Reward:</strong> ${escapeHtml(analysis?.risk_reward_ratio || calculateRiskReward(signal))}</p>
                    <p><strong>Recommendation:</strong> ${escapeHtml(analysis?.recommendation || 'Follow your risk management rules.')}</p>
                </div>
            </div>
            
            <div class="flex flex-col md:flex-row gap-4">
                <button onclick="EnhancedSignalsPage.closeSignalModal()" 
                        class="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-3 px-6 rounded-lg font-medium transition-colors">
                    Close
                </button>
            </div>
        `;
    }

    function closeSignalModal() {
        const modal = document.getElementById('signalModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    function viewChart(signalId) {
        showSignalDetails(signalId);
    }

    function switchTab(tab) {
        currentTab = tab;
        
        const aiTab = document.getElementById('aiDrivenTab');
        const patternTab = document.getElementById('patternTab');
        
        if (aiTab && patternTab) {
            if (tab === 'ai') {
                aiTab.classList.add('active');
                patternTab.classList.remove('active');
            } else {
                patternTab.classList.add('active');
                aiTab.classList.remove('active');
            }
        }
        
        renderSignals();
    }

    function toggleMobileFilters() {
        const sidebar = document.getElementById('filterSidebar');
        const overlay = document.getElementById('mobileOverlay');
        
        if (sidebar && overlay) {
            sidebar.classList.add('active');
            overlay.classList.add('active');
        }
    }

    function closeMobileFilters() {
        const sidebar = document.getElementById('filterSidebar');
        const overlay = document.getElementById('mobileOverlay');
        
        if (sidebar && overlay) {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
        }
    }

    function updateStats() {
        const liveSignals = filteredSignals.filter(s => s.status === 'active').length;
        const statValues = document.querySelectorAll('.stat-value');
        if (statValues.length >= 3) {
            statValues[2].textContent = liveSignals;
        }
    }

    function setupRealTimeUpdates() {
        setInterval(async () => {
            if (!isLoading && signalsData.length > 0) {
                try {
                    await loadSignals();
                } catch (error) {
                    console.error('Error in real-time update:', error);
                }
            }
        }, 60000); // Update every 60 seconds
    }

    // Utility functions
    function getCountryFlags(symbol) {
        const flagMap = {
            'AUDCAD': '🇦🇺🇨🇦', 'EURUSD': '🇪🇺🇺🇸', 'EURSEEK': '🇪🇺🇸🇪',
            'GBPJPY': '🇬🇧🇯🇵', 'EURAUD': '🇪🇺🇦🇺', 'AUDNZD': '🇦🇺🇳🇿',
            'CHINA50': '🇨🇳', 'XAUUSD': '🥇', 'BTCUSD': '₿',
            'US30': '🇺🇸', 'US100': '🇺🇸', 'US500': '🇺🇸'
        };
        const cleanSymbol = symbol.replace('/', '').replace('.', '').toUpperCase();
        return flagMap[cleanSymbol] || '🌍';
    }

    function calculateRiskReward(signal) {
        try {
            const entry = parseFloat(signal.entry);
            const target = parseFloat(signal.target);
            const stop = parseFloat(signal.stop);
            const reward = Math.abs(target - entry);
            const risk = Math.abs(entry - stop);
            if (risk === 0) return '0.0:1';
            return (reward / risk).toFixed(1) + ':1';
        } catch (e) {
            return 'N/A';
        }
    }

    function escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') return unsafe || '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function showToast(message, type = 'info') {
        // Simple toast implementation
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg text-white z-50 ${
            type === 'error' ? 'bg-red-600' : 
            type === 'success' ? 'bg-green-600' : 'bg-blue-600'
        }`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    // Public API
    return {
        init,
        loadSignals,
        showSignalDetails,
        viewChart,
        closeSignalModal,
        applyFilters,
        switchTab
    };
})();

// Auto-initialize when signalsGrid is present
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('signalsGrid')) {
        console.log('Enhanced Signals Page detected, initializing...');
        EnhancedSignalsPage.init();
    }
});
