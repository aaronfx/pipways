// Enhanced Signals Module for Pipways Dashboard
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
    let loadMoreAvailable = true;

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
        // Handle window resize
        window.addEventListener('resize', handleWindowResize);
        
        // Initial mobile check
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
        // ESC to close modal
        if (e.key === 'Escape') {
            const modal = document.getElementById('signalModal');
            if (modal && !modal.classList.contains('hidden')) {
                closeSignalModal();
            }
        }
        
        // R to refresh signals
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
            
            const response = await window.API.get('/signals/enhanced', { params });
            
            if (response && response.data) {
                signalsData = response.data;
                console.log(`Loaded ${signalsData.length} signals`);
                applyFilters();
                renderSignals();
                updateStats();
            } else {
                throw new Error('No data received from API');
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
        // In a real implementation, this would load additional signals
        // For now, just show a message
        UI.showToast('All available signals loaded', 'info');
        
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        if (loadMoreBtn) {
            loadMoreBtn.style.display = 'none';
        }
    }

    function handleSignalsError(error) {
        console.error('Signals error:', error);
        
        // Handle 402 payment required
        if (error.response?.status === 402) {
            window.PipwaysUsage?.showUpgradeModal('signals', {
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
            return;
        }
        
        // Show error state
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
                <p class="text-gray-500 mb-4">${message}</p>
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
        
        // Close mobile filters on selection (mobile UX improvement)
        if (window.innerWidth < 768) {
            setTimeout(closeMobileFilters, 300);
        }
    }

    function handleApplyFilters() {
        console.log('Applying filters:', currentFilters);
        loadSignals(); // Reload from server with new filters
    }

    function handleResetFilters() {
        console.log('Resetting filters');
        
        // Reset filter values
        currentFilters = {
            confidence: 60,
            asset: 'all',
            country: 'all',
            pattern: 'all',
            status: 'all'
        };
        
        // Update UI
        document.getElementById('conf60')?.checked && (document.getElementById('conf60').checked = true);
        document.getElementById('assetAll')?.checked && (document.getElementById('assetAll').checked = true);
        document.getElementById('countryAll')?.checked && (document.getElementById('countryAll').checked = true);
        document.getElementById('patternAll')?.checked && (document.getElementById('patternAll').checked = true);
        document.getElementById('statusAll')?.checked && (document.getElementById('statusAll').checked = true);
        
        // Reload signals
        loadSignals();
    }

    function applyFilters() {
        if (!signalsData || !Array.isArray(signalsData)) {
            filteredSignals = [];
            return;
        }
        
        filteredSignals = signalsData.filter(signal => {
            // Confidence filter
            if (signal.confidence < parseInt(currentFilters.confidence)) return false;
            
            // Asset type filter
            if (currentFilters.asset !== 'all' && signal.asset_type !== currentFilters.asset) return false;
            
            // Country filter
            if (currentFilters.country !== 'all' && 
                signal.country !== currentFilters.country && 
                signal.country !== 'all') return false;
            
            // Pattern filter
            if (currentFilters.pattern !== 'all' && 
                signal.pattern?.toLowerCase() !== currentFilters.pattern) return false;
            
            // Status filter (for future use)
            if (currentFilters.status !== 'all' && signal.status !== currentFilters.status) return false;
            
            return true;
        });
        
        console.log(`Filtered ${filteredSignals.length} signals from ${signalsData.length} total`);
    }

    function renderSignals() {
        const grid = document.getElementById('signalsGrid');
        if (!grid) return;

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

        // Clear grid
        grid.innerHTML = '';

        // Render each signal card
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
        card.style.animationDelay = `${index * 50}ms`; // Stagger animations
        
        // Safely handle potential null/undefined values
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
        
        card.innerHTML = `
            <div class="flex items-start justify-between mb-4">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-red-500 flex items-center justify-center">
                        <span class="text-white text-xs font-bold">${getCountryFlags(symbol)}</span>
                    </div>
                    <div>
                        <h3 class="font-bold text-white">${escapeHtml(symbol)}</h3>
                        <p class="text-xs text-gray-400">${escapeHtml(fullName)}</p>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-lg font-bold text-white">${escapeHtml(currentPrice)}</div>
                    <div class="text-xs ${changeClass}">${escapeHtml(priceChange)} (${escapeHtml(priceChangePercent)})</div>
                </div>
            </div>

            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-2">
                    <span class="live-badge">LIVE TRADE</span>
                    <span class="pattern-badge">${escapeHtml(pattern)}</span>
                </div>
                <span class="timeframe-badge">${escapeHtml(timeframe)}</span>
            </div>

            <div class="mb-4">
                <div class="${directionClass} text-center">${escapeHtml(direction)}</div>
            </div>

            <div class="trade-levels">
                <div class="level-item">
                    <div class="level-label">Entry</div>
                    <div class="level-value level-entry">${escapeHtml(entry)}</div>
                </div>
                <div class="level-item">
                    <div class="level-label">Target</div>
                    <div class="level-value level-target">${escapeHtml(target)}</div>
                </div>
                <div class="level-item">
                    <div class="level-label">Stop</div>
                    <div class="level-value level-stop">${escapeHtml(stop)}</div>
                </div>
            </div>

            <div class="mb-4">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs text-gray-400">News Sentiment</span>
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-red-400">${sentimentBearish}% ▼</span>
                        <span class="text-xs text-green-400">${sentimentBullish}% ▲</span>
                    </div>
                </div>
                <div class="sentiment-bar">
                    <div class="sentiment-fill ${sentimentBullish > sentimentBearish ? 'sentiment-bullish' : 'sentiment-bearish'}" 
                         style="width: ${Math.max(sentimentBearish, sentimentBullish)}%"></div>
                </div>
            </div>

            <div class="mini-chart mb-4 relative">
                ${renderMiniChart(signal)}
                <div class="chart-overlay">
                    <div class="text-xs text-gray-400">${escapeHtml(timeframe)} Pattern Analysis</div>
                </div>
            </div>

            <div class="text-center mb-4">
                <span class="text-xs text-gray-400">Expires: </span>
                <span class="text-xs expiry-time">${escapeHtml(expiry)}</span>
            </div>

            <div class="flex gap-2">
                <button class="learn-btn flex-1" onclick="EnhancedSignalsPage.showSignalDetails(${signal.id})">
                    LEARN MORE
                </button>
                <button class="install-ea-btn flex-1" onclick="EnhancedSignalsPage.viewChart(${signal.id})">
                    VIEW CHART
                </button>
            </div>
        `;
        
        return card;
    }

    function renderMiniChart(signal) {
        // Create simple candlestick representation
        let candlesticks = '';
        const patternType = signal.pattern?.toLowerCase() || 'flag';
        
        for (let i = 0; i < 6; i++) {
            const isGreen = Math.random() > 0.5;
            const height = 6 + Math.random() * 8;
            const left = 12 + i * 4;
            
            candlesticks += `
                <div class="absolute bottom-1/3 w-1 h-${Math.round(height)} bg-${isGreen ? 'green' : 'red'}-500" 
                     style="left: ${left}px; height: ${height}px;"></div>
            `;
        }
        
        // Add pattern lines based on signal.pattern
        let patternLines = '';
        if (patternType === 'flag') {
            patternLines = `
                <div class="absolute bottom-1/2 left-8 w-20 h-0.5 bg-purple-400 opacity-60"></div>
                <div class="absolute bottom-1/3 left-8 w-20 h-0.5 bg-purple-400 opacity-60"></div>
            `;
        } else if (patternType === 'wedge') {
            patternLines = `
                <div class="absolute bottom-1/2 left-8 w-20 h-0.5 bg-purple-400 opacity-60 transform -rotate-12"></div>
                <div class="absolute bottom-1/3 left-8 w-20 h-0.5 bg-purple-400 opacity-60 transform rotate-6"></div>
            `;
        }
        
        return `<div class="absolute inset-2">${candlesticks}${patternLines}</div>`;
    }

    function showSignalDetails(signalId) {
        const signal = signalsData.find(s => s.id === signalId);
        if (!signal) {
            UI.showToast('Signal not found', 'error');
            return;
        }

        console.log('Showing details for signal:', signalId);
        
        // Update modal title
        const modalTitle = document.getElementById('modalTitle');
        if (modalTitle) {
            modalTitle.textContent = `${signal.symbol} - ${signal.full_name || signal.symbol}`;
        }
        
        // Load detailed analysis
        loadChartAnalysis(signalId);
        
        // Show modal
        const modal = document.getElementById('signalModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            
            // Focus trap for accessibility
            const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (firstFocusable) {
                firstFocusable.focus();
            }
        }
    }

    async function loadChartAnalysis(signalId) {
        const modalContent = document.getElementById('modalContent');
        if (!modalContent) return;
        
        // Show loading state
        modalContent.innerHTML = `
            <div class="text-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-4"></div>
                <p class="text-gray-400">Loading detailed analysis...</p>
            </div>
        `;
        
        try {
            const response = await window.API.get(`/signals/${signalId}/chart-analysis`);
            
            if (response && response.data) {
                updateModalWithAnalysis(response.data);
            } else {
                throw new Error('No analysis data received');
            }
            
        } catch (error) {
            console.error('Error loading chart analysis:', error);
            
            // Handle 402 error for detailed analysis
            if (error.response?.status === 402) {
                modalContent.innerHTML = `
                    <div class="text-center py-8">
                        <i class="fas fa-lock text-4xl text-purple-500 mb-4"></i>
                        <h3 class="text-xl font-semibold text-white mb-2">Detailed Analysis</h3>
                        <p class="text-gray-400 mb-6">Upgrade to Pro to access in-depth chart analysis and pattern insights.</p>
                        <button onclick="PipwaysUsage.showUpgradeModal('signals_detailed_analysis')" 
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
                        <p class="text-gray-500">Failed to load detailed analysis. Please try again.</p>
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
        const chartLevels = data.chart_levels;
        
        modalContent.innerHTML = `
            <!-- Signal Header Info -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div class="space-y-4">
                    <div class="flex items-center gap-4">
                        <div class="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500 to-red-500 flex items-center justify-center">
                            <span class="text-white text-sm font-bold">${getCountryFlags(signal.symbol)}</span>
                        </div>
                        <div>
                            <div class="text-2xl font-bold text-white">${escapeHtml(signal.current_price || signal.entry)}</div>
                            <div class="text-sm ${signal.price_change?.startsWith('+') ? 'text-green-400' : 'text-red-400'}">
                                ${escapeHtml(signal.price_change || '')} (${escapeHtml(signal.price_change_percent || '')})
                            </div>
                        </div>
                    </div>
                    
                    <div class="flex items-center gap-3">
                        <span class="live-badge">LIVE TRADE</span>
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
                            <div class="level-value level-entry">${escapeHtml(signal.entry)}</div>
                        </div>
                        <div class="level-item">
                            <div class="level-label">Target</div>
                            <div class="level-value level-target">${escapeHtml(signal.target)}</div>
                        </div>
                        <div class="level-item">
                            <div class="level-label">Stop</div>
                            <div class="level-value level-stop">${escapeHtml(signal.stop)}</div>
                        </div>
                    </div>
                    
                    <div>
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-sm text-gray-400">News Sentiment</span>
                            <div class="flex items-center gap-2">
                                <span class="text-sm text-red-400">${signal.sentiment_bearish || 50}% ▼</span>
                                <span class="text-sm text-green-400">${signal.sentiment_bullish || 50}% ▲</span>
                            </div>
                        </div>
                        <div class="sentiment-bar">
                            <div class="sentiment-fill ${(signal.sentiment_bullish || 50) > (signal.sentiment_bearish || 50) ? 'sentiment-bullish' : 'sentiment-bearish'}" 
                                 style="width: ${Math.max(signal.sentiment_bearish || 50, signal.sentiment_bullish || 50)}%"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Analysis Section -->
            <div class="bg-gray-800 rounded-lg p-6 mb-6">
                <h3 class="text-lg font-bold text-white mb-4 flex items-center">
                    <i class="fas fa-lightbulb text-yellow-400 mr-2"></i>
                    Trade Analysis
                </h3>
                <div class="space-y-4 text-gray-300">
                    <p class="leading-relaxed">
                        ${escapeHtml(analysis?.description || 'The pattern shows a potential continuation setup with clear entry, target, and stop loss levels defined.')}
                    </p>
                    <p class="leading-relaxed">
                        This analysis is based on technical patterns and market structure. Always consider your risk management rules and market conditions.
                    </p>
                </div>
            </div>

            <!-- Risk Analysis -->
            <div class="bg-gray-800 rounded-lg p-6 mb-6">
                <h3 class="text-lg font-bold text-white mb-4">Risk Management</h3>
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <span class="text-gray-400">Risk/Reward:</span>
                        <div class="font-mono text-green-400 font-bold text-lg">${calculateRiskReward(signal)}:1</div>
                    </div>
                    <div>
                        <span class="text-gray-400">Confidence:</span>
                        <div class="font-mono text-white font-bold">${signal.confidence || 75}%</div>
                    </div>
                </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="flex flex-col md:flex-row gap-4">
                <button onclick="EnhancedSignalsPage.openFullChart(${signal.id})" 
                        class="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-3 px-6 rounded-lg font-medium transition-colors">
                    <i class="fas fa-chart-line mr-2"></i>
                    Analyze Full Chart
                </button>
                <button onclick="EnhancedSignalsPage.setPriceAlert(${signal.id})" 
                        class="flex-1 bg-orange-600 hover:bg-orange-700 text-white py-3 px-6 rounded-lg font-medium transition-colors">
                    <i class="fas fa-bell mr-2"></i>
                    Set Price Alert
                </button>
                <button onclick="EnhancedSignalsPage.shareAnalysis(${signal.id})" 
                        class="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-3 px-6 rounded-lg font-medium transition-colors">
                    <i class="fas fa-share mr-2"></i>
                    Share Analysis
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
        console.log('Viewing chart for signal:', signalId);
        showSignalDetails(signalId);
    }

    function openFullChart(signalId) {
        const signal = signalsData.find(s => s.id === signalId);
        if (!signal) return;
        
        // Check if user has access to full charts
        const user = window.Store?.getUser();
        const userTier = user?.subscription_tier || 'free';
        
        if (userTier === 'free') {
            window.PipwaysUsage?.showUpgradeModal('signals_chart_access', {
                title: 'Full Chart Analysis',
                message: 'Upgrade to Pro to access interactive charts and TradingView integration.',
                features: [
                    'Interactive TradingView charts',
                    'Technical indicators',
                    'Pattern overlays',
                    'Multiple timeframes'
                ]
            });
            return;
        }
        
        // Open TradingView or similar integration
        UI.showToast('Opening advanced chart analysis...', 'info');
        // In production: window.open(`https://tradingview.com/chart/?symbol=${signal.symbol}`, '_blank');
    }

    function setPriceAlert(signalId) {
        const signal = signalsData.find(s => s.id === signalId);
        if (!signal) return;
        
        UI.showToast(`Price alert set for ${signal.symbol}`, 'success');
        // Implement price alert functionality
    }

    function shareAnalysis(signalId) {
        const signal = signalsData.find(s => s.id === signalId);
        if (!signal) return;
        
        const shareText = `Check out this ${signal.pattern} pattern on ${signal.symbol} - Entry: ${signal.entry}, Target: ${signal.target}`;
        
        if (navigator.share) {
            navigator.share({
                title: `${signal.symbol} Signal Analysis`,
                text: shareText,
                url: window.location.href
            });
        } else {
            // Fallback - copy to clipboard
            navigator.clipboard?.writeText(shareText).then(() => {
                UI.showToast('Analysis copied to clipboard', 'success');
            });
        }
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
        
        // Filter signals based on tab (if needed)
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
        // Update performance stats based on current signals
        const liveSignals = filteredSignals.filter(s => s.status === 'active').length;
        
        // Update live signals count
        const liveSignalsElements = document.querySelectorAll('.stat-value');
        if (liveSignalsElements.length >= 3) {
            liveSignalsElements[2].textContent = liveSignals;
        }
    }

    function setupRealTimeUpdates() {
        // Update signals every 30 seconds
        setInterval(async () => {
            if (!isLoading && signalsData.length > 0) {
                try {
                    await loadSignals();
                } catch (error) {
                    console.error('Error in real-time update:', error);
                }
            }
        }, 30000);
    }

    // Utility functions
    function getCountryFlags(symbol) {
        const flagMap = {
            'AUDCAD': '🇦🇺🇨🇦',
            'EURUSD': '🇪🇺🇺🇸',
            'EURSEEK': '🇪🇺🇸🇪',
            'EUR/SEK': '🇪🇺🇸🇪',
            'GBPJPY': '🇬🇧🇯🇵',
            'EURAUD': '🇪🇺🇦🇺',
            'AUDNZD': '🇦🇺🇳🇿',
            'CHINA50': '🇨🇳',
            'TSLANAS': '🇺🇸',
            'TSLA.NAS': '🇺🇸',
            'AAPL.NAS': '🇺🇸'
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
            
            if (risk === 0) return '0.0';
            
            const rr = reward / risk;
            return rr.toFixed(1);
        } catch (e) {
            return '0.0';
        }
    }

    function escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') return unsafe;
        
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Public API
    return {
        init,
        loadSignals,
        showSignalDetails,
        viewChart,
        openFullChart,
        setPriceAlert,
        shareAnalysis,
        applyFilters,
        switchTab
    };
})();

// Auto-initialize when page is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the enhanced signals page
    if (document.getElementById('signalsGrid')) {
        console.log('Enhanced Signals Page detected, initializing...');
        EnhancedSignalsPage.init();
    }
});

// Also initialize if the page is loaded dynamically
if (typeof window !== 'undefined' && window.dashboard) {
    const originalRenderPage = window.dashboard.renderPage;
    if (originalRenderPage) {
        window.dashboard.renderPage = function(page) {
            if (page === 'enhanced-signals') {
                // Let the original render first
                originalRenderPage.call(this, page);
                // Then initialize our enhanced signals
                setTimeout(() => {
                    if (window.EnhancedSignalsPage && document.getElementById('signalsGrid')) {
                        EnhancedSignalsPage.init();
                    }
                }, 100);
                return;
            }
            originalRenderPage.call(this, page);
        };
    }
}
