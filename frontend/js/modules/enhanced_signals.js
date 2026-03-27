// Enhanced Signals Page Module - Fixed localStorage key
// Deploy to: frontend/js/modules/enhanced_signals.js

(function() {
    'use strict';

    // ========================================
    // API Helper Functions (using fetch directly)
    // ========================================
    
    async function apiGet(endpoint) {
        // FIXED: Use pipways_token instead of token
        const token = localStorage.getItem('pipways_token');
        if (!token) {
            console.warn('[EnhancedSignals] No token found');
            throw new Error('Not authenticated');
        }
        
        const response = await fetch(endpoint, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.status === 401) {
            console.warn('[EnhancedSignals] Unauthorized - clearing token');
            localStorage.removeItem('pipways_token');
            localStorage.removeItem('pipways_user');
            window.location.href = '/';
            throw new Error('Unauthorized');
        }
        
        if (response.status === 402) {
            // Payment required - show upgrade modal
            console.warn('[EnhancedSignals] Payment required');
            showUpgradeModal();
            throw new Error('Subscription required');
        }
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        return response.json();
    }
    
    async function apiPost(endpoint, data) {
        // FIXED: Use pipways_token instead of token
        const token = localStorage.getItem('pipways_token');
        if (!token) {
            throw new Error('Not authenticated');
        }
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
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

    // ========================================
    // State Management
    // ========================================
    
    let allSignals = [];
    let filteredSignals = [];
    let currentTab = 'ai-driven';
    let currentFilters = {
        confidence: 60,
        asset: 'all',
        country: 'all',
        pattern: 'all',
        status: 'all'
    };
    let updateInterval = null;

    // ========================================
    // Initialization
    // ========================================
    
    function init() {
        console.log('[EnhancedSignals] Initializing...');
        
        setupEventListeners();
        loadSignals();
        
        // Real-time updates every 60 seconds
        if (updateInterval) clearInterval(updateInterval);
        updateInterval = setInterval(loadSignals, 60000);
        
        console.log('[EnhancedSignals] Initialized successfully');
    }

    // ========================================
    // Event Listeners
    // ========================================
    
    function setupEventListeners() {
        // Tab switching
        const aiTab = document.getElementById('aiDrivenTab');
        const patternTab = document.getElementById('patternTab');
        
        if (aiTab) {
            aiTab.addEventListener('click', () => switchTab('ai-driven'));
        }
        if (patternTab) {
            patternTab.addEventListener('click', () => switchTab('pattern'));
        }
        
        // Filter controls
        document.querySelectorAll('input[name="confidence"]').forEach(input => {
            input.addEventListener('change', (e) => {
                currentFilters.confidence = parseInt(e.target.value);
            });
        });
        
        document.querySelectorAll('input[name="asset"]').forEach(input => {
            input.addEventListener('change', (e) => {
                currentFilters.asset = e.target.value;
            });
        });
        
        document.querySelectorAll('input[name="country"]').forEach(input => {
            input.addEventListener('change', (e) => {
                currentFilters.country = e.target.value;
            });
        });
        
        document.querySelectorAll('input[name="pattern"]').forEach(input => {
            input.addEventListener('change', (e) => {
                currentFilters.pattern = e.target.value;
            });
        });
        
        document.querySelectorAll('input[name="status"]').forEach(input => {
            input.addEventListener('change', (e) => {
                currentFilters.status = e.target.value;
            });
        });
        
        // Apply and Reset buttons
        const applyBtn = document.getElementById('applyFilters');
        const resetBtn = document.getElementById('resetFilters');
        
        if (applyBtn) {
            applyBtn.addEventListener('click', applyFilters);
        }
        if (resetBtn) {
            resetBtn.addEventListener('click', resetFilters);
        }
        
        // Mobile filter toggle
        const filterToggle = document.getElementById('filterToggle');
        const filterSidebar = document.getElementById('filterSidebar');
        const mobileOverlay = document.getElementById('mobileOverlay');
        const closeMobileFilter = document.getElementById('closeMobileFilter');
        
        if (filterToggle && filterSidebar) {
            filterToggle.addEventListener('click', () => {
                filterSidebar.classList.add('active');
                if (mobileOverlay) mobileOverlay.classList.add('active');
            });
        }
        
        if (closeMobileFilter && filterSidebar) {
            closeMobileFilter.addEventListener('click', () => {
                filterSidebar.classList.remove('active');
                if (mobileOverlay) mobileOverlay.classList.remove('active');
            });
        }
        
        if (mobileOverlay && filterSidebar) {
            mobileOverlay.addEventListener('click', () => {
                filterSidebar.classList.remove('active');
                mobileOverlay.classList.remove('active');
            });
        }
        
        // Modal close
        const closeModal = document.getElementById('closeModal');
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
        
        // Load more button
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', loadMoreSignals);
        }
    }

    // ========================================
    // Data Loading
    // ========================================
    
    async function loadSignals() {
        console.log('[EnhancedSignals] Loading signals...');
        
        const grid = document.getElementById('signalsGrid');
        if (!grid) return;
        
        try {
            // Fetch from enhanced signals endpoint
            const signals = await apiGet('/signals/enhanced');
            
            allSignals = signals || [];
            console.log(`[EnhancedSignals] Loaded ${allSignals.length} signals`);
            
            applyFilters();
            updateStats();
            
        } catch (error) {
            console.error('[EnhancedSignals] Error loading signals:', error);
            
            if (error.message === 'Subscription required') {
                grid.innerHTML = `
                    <div class="col-span-full text-center py-12">
                        <i class="fas fa-lock text-4xl text-purple-500 mb-4"></i>
                        <h3 class="text-xl font-semibold mb-2">Upgrade Required</h3>
                        <p class="text-gray-400 mb-6">Enhanced signals require a Pro subscription.</p>
                        <button onclick="dashboard.navigateTo('billing')" class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-semibold">
                            Upgrade Now
                        </button>
                    </div>
                `;
            } else if (error.message !== 'Not authenticated') {
                grid.innerHTML = `
                    <div class="col-span-full text-center py-12">
                        <i class="fas fa-exclamation-triangle text-4xl text-red-500 mb-4"></i>
                        <h3 class="text-xl font-semibold mb-2">Error Loading Signals</h3>
                        <p class="text-gray-400 mb-6">${error.message}</p>
                        <button onclick="window.EnhancedSignalsPage.loadSignals()" class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-semibold">
                            Try Again
                        </button>
                    </div>
                `;
            }
        }
    }

    // ========================================
    // Filtering
    // ========================================
    
    function applyFilters() {
        filteredSignals = allSignals.filter(signal => {
            // Confidence filter
            if ((signal.confidence || 0) < currentFilters.confidence) {
                return false;
            }
            
            // Asset type filter
            if (currentFilters.asset !== 'all') {
                const assetType = (signal.asset_type || 'forex').toLowerCase();
                if (assetType !== currentFilters.asset.toLowerCase()) {
                    return false;
                }
            }
            
            // Country filter
            if (currentFilters.country !== 'all') {
                const country = (signal.country || 'all').toUpperCase();
                if (country !== currentFilters.country.toUpperCase() && country !== 'ALL') {
                    return false;
                }
            }
            
            // Pattern filter
            if (currentFilters.pattern !== 'all') {
                const pattern = (signal.pattern || '').toLowerCase();
                if (!pattern.includes(currentFilters.pattern.toLowerCase())) {
                    return false;
                }
            }
            
            // Status filter
            if (currentFilters.status !== 'all') {
                const status = (signal.status || 'active').toLowerCase();
                if (status !== currentFilters.status.toLowerCase()) {
                    return false;
                }
            }
            
            // Tab filter
            if (currentTab === 'ai-driven') {
                // AI-driven signals have high confidence
                return (signal.confidence || 0) >= 70;
            } else {
                // Pattern signals focus on technical patterns
                return signal.pattern && signal.pattern.length > 0;
            }
        });
        
        renderSignals();
        updateResultsCount();
        
        // Close mobile filter sidebar
        const filterSidebar = document.getElementById('filterSidebar');
        const mobileOverlay = document.getElementById('mobileOverlay');
        if (filterSidebar) filterSidebar.classList.remove('active');
        if (mobileOverlay) mobileOverlay.classList.remove('active');
    }
    
    function resetFilters() {
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
        
        applyFilters();
    }
    
    function updateResultsCount() {
        const resultsCount = document.getElementById('resultsCount');
        if (resultsCount) {
            resultsCount.textContent = filteredSignals.length;
        }
    }

    // ========================================
    // Tab Switching
    // ========================================
    
    function switchTab(tab) {
        currentTab = tab;
        
        const aiTab = document.getElementById('aiDrivenTab');
        const patternTab = document.getElementById('patternTab');
        
        if (aiTab && patternTab) {
            if (tab === 'ai-driven') {
                aiTab.classList.add('active', 'bg-purple-600', 'text-white');
                aiTab.classList.remove('text-gray-400');
                patternTab.classList.remove('active', 'bg-purple-600', 'text-white');
                patternTab.classList.add('text-gray-400');
            } else {
                patternTab.classList.add('active', 'bg-purple-600', 'text-white');
                patternTab.classList.remove('text-gray-400');
                aiTab.classList.remove('active', 'bg-purple-600', 'text-white');
                aiTab.classList.add('text-gray-400');
            }
        }
        
        applyFilters();
    }

    // ========================================
    // Rendering
    // ========================================
    
    function renderSignals() {
        const grid = document.getElementById('signalsGrid');
        if (!grid) return;
        
        if (filteredSignals.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <i class="fas fa-search text-4xl text-gray-500 mb-4"></i>
                    <h3 class="text-xl font-semibold mb-2">No Signals Found</h3>
                    <p class="text-gray-400">Try adjusting your filters to see more signals.</p>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = filteredSignals.map((signal, index) => renderSignalCard(signal, index)).join('');
    }
    
    function renderSignalCard(signal, index) {
        const isBuy = (signal.direction || '').toUpperCase().includes('BUY');
        const directionClass = isBuy ? 'buy-stop' : 'sell-stop';
        const directionLabel = isBuy ? 'BUY' : 'SELL';
        
        const confidence = signal.confidence || 75;
        const confidenceColor = confidence >= 80 ? 'text-green-400' : confidence >= 60 ? 'text-yellow-400' : 'text-red-400';
        
        const bullishPct = signal.sentiment_bullish || 50;
        const bearishPct = signal.sentiment_bearish || 50;
        
        const expiryDisplay = signal.expires_display || calculateExpiryDisplay(signal.expires_at);
        
        return `
            <div class="signal-card rounded-xl p-5 cursor-pointer" onclick="window.EnhancedSignalsPage.openSignalModal(${signal.id})" style="animation-delay: ${index * 0.1}s">
                <!-- Header -->
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-2">
                        <span class="live-badge">LIVE</span>
                        <span class="pattern-badge">${signal.pattern || 'SIGNAL'}</span>
                        <span class="timeframe-badge">${signal.timeframe || 'H4'}</span>
                    </div>
                    <div class="${directionClass}">
                        ${directionLabel}
                    </div>
                </div>
                
                <!-- Symbol Info -->
                <div class="mb-4">
                    <h3 class="text-xl font-bold text-white mb-1">${signal.symbol || 'N/A'}</h3>
                    <p class="text-sm text-gray-400">${signal.full_name || getFullNameFromSymbol(signal.symbol)}</p>
                </div>
                
                <!-- Price Info -->
                <div class="flex items-center gap-3 mb-4">
                    <span class="text-2xl font-bold font-mono text-white">${signal.current_price || signal.entry || '—'}</span>
                    <span class="text-sm ${isBuy ? 'text-green-400' : 'text-red-400'}">${signal.price_change || ''} (${signal.price_change_percent || ''})</span>
                </div>
                
                <!-- Trade Levels -->
                <div class="trade-levels">
                    <div class="level-item">
                        <span class="level-label">Entry</span>
                        <span class="level-value level-entry">${signal.entry || '—'}</span>
                    </div>
                    <div class="level-item">
                        <span class="level-label">Target</span>
                        <span class="level-value level-target">${signal.target || '—'}</span>
                    </div>
                    <div class="level-item">
                        <span class="level-label">Stop Loss</span>
                        <span class="level-value level-stop">${signal.stop || '—'}</span>
                    </div>
                </div>
                
                <!-- Confidence -->
                <div class="flex items-center justify-between mb-4">
                    <span class="text-sm text-gray-400">Confidence</span>
                    <span class="text-lg font-bold ${confidenceColor}">${confidence}%</span>
                </div>
                
                <!-- Sentiment Bar -->
                <div class="mb-4">
                    <div class="flex justify-between text-xs text-gray-400 mb-1">
                        <span>Bearish ${bearishPct}%</span>
                        <span>Bullish ${bullishPct}%</span>
                    </div>
                    <div class="sentiment-bar">
                        <div class="sentiment-fill ${bullishPct > bearishPct ? 'sentiment-bullish' : 'sentiment-bearish'}" style="width: ${Math.max(bullishPct, bearishPct)}%"></div>
                    </div>
                </div>
                
                <!-- Footer -->
                <div class="flex items-center justify-between">
                    <div class="text-sm">
                        <span class="text-gray-400">Expires in</span>
                        <span class="expiry-time ml-1">${expiryDisplay}</span>
                    </div>
                    <button class="learn-btn" onclick="event.stopPropagation(); window.EnhancedSignalsPage.openSignalModal(${signal.id})">
                        View Details
                    </button>
                </div>
            </div>
        `;
    }
    
    function calculateExpiryDisplay(expiresAt) {
        if (!expiresAt) return '24h';
        
        const now = new Date();
        const expiry = new Date(expiresAt);
        const diffMs = expiry - now;
        
        if (diffMs <= 0) return 'Expired';
        
        const hours = Math.floor(diffMs / (1000 * 60 * 60));
        const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        
        if (hours >= 24) {
            const days = Math.floor(hours / 24);
            return `${days}d ${hours % 24}h`;
        }
        
        return `${hours}h ${minutes}m`;
    }
    
    function getFullNameFromSymbol(symbol) {
        const names = {
            'EURUSD': 'Euro / US Dollar',
            'GBPUSD': 'British Pound / US Dollar',
            'USDJPY': 'US Dollar / Japanese Yen',
            'AUDUSD': 'Australian Dollar / US Dollar',
            'USDCAD': 'US Dollar / Canadian Dollar',
            'AUDCAD': 'Australian Dollar / Canadian Dollar',
            'EURSEEK': 'Euro / Swedish Krona',
            'XAUUSD': 'Gold / US Dollar',
            'XAGUSD': 'Silver / US Dollar',
            'CHINA50': 'China A50 Index',
            'US30': 'Dow Jones Industrial Average',
            'NAS100': 'Nasdaq 100 Index',
            'SPX500': 'S&P 500 Index',
            'BTCUSD': 'Bitcoin / US Dollar',
            'ETHUSD': 'Ethereum / US Dollar'
        };
        
        return names[symbol] || symbol || 'Unknown';
    }

    // ========================================
    // Modal
    // ========================================
    
    async function openSignalModal(signalId) {
        const modal = document.getElementById('signalModal');
        const modalContent = document.getElementById('modalContent');
        const modalTitle = document.getElementById('modalTitle');
        
        if (!modal || !modalContent) return;
        
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        
        modalContent.innerHTML = `
            <div class="text-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-4"></div>
                <p class="text-gray-400">Loading signal details...</p>
            </div>
        `;
        
        try {
            const signal = await apiGet(`/signals/${signalId}`);
            
            if (modalTitle) {
                modalTitle.textContent = `${signal.symbol} - ${signal.direction || 'Signal'} Setup`;
            }
            
            const isBuy = (signal.direction || '').toUpperCase().includes('BUY');
            
            modalContent.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Left Column -->
                    <div>
                        <div class="mb-6">
                            <h3 class="text-lg font-bold text-white mb-2">${signal.symbol}</h3>
                            <p class="text-gray-400">${signal.full_name || getFullNameFromSymbol(signal.symbol)}</p>
                        </div>
                        
                        <div class="bg-gray-700 rounded-lg p-4 mb-4">
                            <div class="grid grid-cols-3 gap-4 text-center">
                                <div>
                                    <p class="text-xs text-gray-400 mb-1">Entry</p>
                                    <p class="text-lg font-bold text-blue-400">${signal.entry || '—'}</p>
                                </div>
                                <div>
                                    <p class="text-xs text-gray-400 mb-1">Target</p>
                                    <p class="text-lg font-bold text-green-400">${signal.target || '—'}</p>
                                </div>
                                <div>
                                    <p class="text-xs text-gray-400 mb-1">Stop Loss</p>
                                    <p class="text-lg font-bold text-red-400">${signal.stop || '—'}</p>
                                </div>
                            </div>
                        </div>
                        
                        <div class="space-y-3">
                            <div class="flex justify-between">
                                <span class="text-gray-400">Direction</span>
                                <span class="${isBuy ? 'text-green-400' : 'text-red-400'} font-bold">${signal.direction || 'N/A'}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Pattern</span>
                                <span class="text-white">${signal.pattern || 'N/A'}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Timeframe</span>
                                <span class="text-white">${signal.timeframe || 'H4'}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Confidence</span>
                                <span class="text-purple-400 font-bold">${signal.confidence || 75}%</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Risk:Reward</span>
                                <span class="text-white">${signal.rr_ratio || calculateRR(signal)}</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Right Column -->
                    <div>
                        <div class="bg-gray-700 rounded-lg p-4 mb-4">
                            <h4 class="font-semibold text-white mb-3">Analysis Summary</h4>
                            <p class="text-gray-300 text-sm leading-relaxed">${signal.analysis || signal.description || 'Professional technical analysis based on Smart Money Concepts and institutional order flow patterns.'}</p>
                        </div>
                        
                        <div class="bg-gray-700 rounded-lg p-4">
                            <h4 class="font-semibold text-white mb-3">Market Sentiment</h4>
                            <div class="space-y-2">
                                <div class="flex justify-between text-sm">
                                    <span class="text-gray-400">Bullish</span>
                                    <span class="text-green-400">${signal.sentiment_bullish || 50}%</span>
                                </div>
                                <div class="w-full bg-gray-600 rounded-full h-2">
                                    <div class="bg-green-500 h-2 rounded-full" style="width: ${signal.sentiment_bullish || 50}%"></div>
                                </div>
                                <div class="flex justify-between text-sm">
                                    <span class="text-gray-400">Bearish</span>
                                    <span class="text-red-400">${signal.sentiment_bearish || 50}%</span>
                                </div>
                                <div class="w-full bg-gray-600 rounded-full h-2">
                                    <div class="bg-red-500 h-2 rounded-full" style="width: ${signal.sentiment_bearish || 50}%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-6 pt-6 border-t border-gray-700 flex flex-col sm:flex-row gap-3">
                    <button onclick="window.EnhancedSignalsPage.viewChartAnalysis(${signal.id})" class="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-3 px-6 rounded-lg font-semibold transition-colors">
                        <i class="fas fa-chart-line mr-2"></i>View Chart Analysis
                    </button>
                    <button onclick="window.EnhancedSignalsPage.closeModal()" class="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-3 px-6 rounded-lg font-semibold transition-colors">
                        Close
                    </button>
                </div>
            `;
            
        } catch (error) {
            console.error('[EnhancedSignals] Error loading signal details:', error);
            modalContent.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-exclamation-triangle text-4xl text-red-500 mb-4"></i>
                    <p class="text-red-400">Error loading signal details: ${error.message}</p>
                </div>
            `;
        }
    }
    
    function closeModal() {
        const modal = document.getElementById('signalModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }
    
    function calculateRR(signal) {
        if (!signal.entry || !signal.target || !signal.stop) return 'N/A';
        
        const entry = parseFloat(signal.entry);
        const target = parseFloat(signal.target);
        const stop = parseFloat(signal.stop);
        
        if (isNaN(entry) || isNaN(target) || isNaN(stop)) return 'N/A';
        
        const risk = Math.abs(entry - stop);
        const reward = Math.abs(target - entry);
        
        if (risk === 0) return 'N/A';
        
        const rr = (reward / risk).toFixed(1);
        return `1:${rr}`;
    }

    // ========================================
    // Chart Analysis
    // ========================================
    
    async function viewChartAnalysis(signalId) {
        try {
            const analysis = await apiGet(`/signals/${signalId}/chart-analysis`);
            
            const modalContent = document.getElementById('modalContent');
            if (!modalContent) return;
            
            modalContent.innerHTML = `
                <div class="space-y-6">
                    <div class="bg-gray-700 rounded-lg p-4">
                        <h4 class="font-semibold text-white mb-3">Chart Analysis</h4>
                        <div class="aspect-video bg-gray-800 rounded-lg flex items-center justify-center">
                            ${analysis.chart_image ? 
                                `<img src="${analysis.chart_image}" alt="Chart" class="max-w-full max-h-full rounded-lg">` :
                                `<div class="text-center text-gray-400">
                                    <i class="fas fa-chart-line text-4xl mb-2"></i>
                                    <p>Chart visualization</p>
                                </div>`
                            }
                        </div>
                    </div>
                    
                    <div class="bg-gray-700 rounded-lg p-4">
                        <h4 class="font-semibold text-white mb-3">Technical Analysis</h4>
                        <div class="prose prose-invert text-gray-300 text-sm">
                            ${analysis.technical_analysis || 'Detailed technical analysis based on Smart Money Concepts methodology.'}
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="bg-gray-700 rounded-lg p-3 text-center">
                            <p class="text-xs text-gray-400 mb-1">Support</p>
                            <p class="font-bold text-green-400">${analysis.support_level || '—'}</p>
                        </div>
                        <div class="bg-gray-700 rounded-lg p-3 text-center">
                            <p class="text-xs text-gray-400 mb-1">Resistance</p>
                            <p class="font-bold text-red-400">${analysis.resistance_level || '—'}</p>
                        </div>
                        <div class="bg-gray-700 rounded-lg p-3 text-center">
                            <p class="text-xs text-gray-400 mb-1">Trend</p>
                            <p class="font-bold text-white">${analysis.trend || '—'}</p>
                        </div>
                        <div class="bg-gray-700 rounded-lg p-3 text-center">
                            <p class="text-xs text-gray-400 mb-1">Strength</p>
                            <p class="font-bold text-purple-400">${analysis.strength || '—'}</p>
                        </div>
                    </div>
                    
                    <button onclick="window.EnhancedSignalsPage.openSignalModal(${signalId})" class="w-full bg-gray-700 hover:bg-gray-600 text-white py-3 px-6 rounded-lg font-semibold transition-colors">
                        <i class="fas fa-arrow-left mr-2"></i>Back to Signal Details
                    </button>
                </div>
            `;
            
        } catch (error) {
            console.error('[EnhancedSignals] Error loading chart analysis:', error);
            
            const modalContent = document.getElementById('modalContent');
            if (modalContent) {
                modalContent.innerHTML = `
                    <div class="text-center py-8">
                        <i class="fas fa-lock text-4xl text-purple-500 mb-4"></i>
                        <h3 class="text-xl font-semibold mb-2">Chart Analysis Unavailable</h3>
                        <p class="text-gray-400 mb-6">${error.message}</p>
                        <button onclick="window.EnhancedSignalsPage.openSignalModal(${signalId})" class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-semibold">
                            Back to Signal
                        </button>
                    </div>
                `;
            }
        }
    }

    // ========================================
    // Stats
    // ========================================
    
    function updateStats() {
        // These would be fetched from the API in a real implementation
        const statValues = document.querySelectorAll('.stat-value');
        // Stats are updated from the backend via the signals data
    }

    // ========================================
    // Load More
    // ========================================
    
    function loadMoreSignals() {
        // Implement pagination if needed
        console.log('[EnhancedSignals] Load more clicked');
    }

    // ========================================
    // Upgrade Modal
    // ========================================
    
    function showUpgradeModal() {
        // Use the dashboard's billing page
        if (window.dashboard && typeof window.dashboard.navigateTo === 'function') {
            window.dashboard.navigateTo('billing');
        }
    }

    // ========================================
    // Export Module
    // ========================================
    
    window.EnhancedSignalsPage = {
        init: init,
        loadSignals: loadSignals,
        openSignalModal: openSignalModal,
        closeModal: closeModal,
        viewChartAnalysis: viewChartAnalysis
    };
    
})();
