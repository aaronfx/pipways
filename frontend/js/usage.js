// Enhanced Usage Tracking and Upgrade Modal System for Pipways
window.PipwaysUsage = (function() {
    let userLimits = {};
    let upgradeModal = null;
    let initialized = false;

    // Feature display names for user-facing text
    const FEATURE_NAMES = {
        'chart_analysis_daily': 'AI Chart Analysis',
        'ai_mentor_daily': 'AI Trading Mentor',
        'performance_analysis_monthly': 'Performance Analytics',
        'stock_research_daily': 'AI Stock Research',
        'signals_visible': 'Market Signals Access',
        'signals_detailed_analysis': 'Detailed Signal Analysis',
        'signals_chart_access': 'Full Chart Access',
        'signals_pattern_filtering': 'Advanced Signal Filtering',
        'signals_email_alerts': 'Signal Email Alerts',
        'webinar_recordings': 'Webinar Recordings'
    };

    // Feature descriptions for upgrade modal
    const FEATURE_DESCRIPTIONS = {
        'chart_analysis_daily': 'Upload chart images and get AI-powered Smart Money Concepts analysis',
        'ai_mentor_daily': 'Chat with our AI trading coach for personalized guidance',
        'performance_analysis_monthly': 'Upload your trading journal for detailed performance insights',
        'stock_research_daily': 'Get fundamental and sentiment analysis on stocks',
        'signals_visible': 'Access to all live trading signals with entry, target, and stop levels',
        'signals_detailed_analysis': 'In-depth pattern analysis and risk/reward calculations',
        'signals_chart_access': 'Interactive charts with TradingView integration',
        'signals_pattern_filtering': 'Filter signals by pattern type, confidence level, and asset class',
        'signals_email_alerts': 'Instant email notifications when new signals are published',
        'webinar_recordings': 'Access to recorded trading webinars and educational content'
    };

    function init() {
        if (initialized) return;
        
        console.log('PipwaysUsage: Initializing usage tracking system');
        
        setupUpgradeModal();
        setupInterceptors();
        loadUserLimits();
        
        initialized = true;
    }

    function setupUpgradeModal() {
        // Create upgrade modal HTML if it doesn't exist
        if (document.getElementById('upgradeModal')) return;
        
        const modalHTML = `
            <div id="upgradeModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50" style="backdrop-filter: blur(4px);">
                <div class="bg-gray-900 rounded-lg p-8 max-w-md w-full mx-4 border border-gray-700 shadow-2xl">
                    <div class="text-center">
                        <div class="w-16 h-16 bg-gradient-to-br from-purple-500 to-orange-500 rounded-full flex items-center justify-center mx-auto mb-4">
                            <i class="fas fa-crown text-white text-2xl"></i>
                        </div>
                        <h2 id="upgradeModalTitle" class="text-2xl font-bold text-white mb-2">Upgrade to Pro</h2>
                        <p id="upgradeModalMessage" class="text-gray-400 mb-6">Unlock advanced trading features and tools</p>
                        
                        <div id="upgradeModalFeatures" class="text-left bg-gray-800 rounded-lg p-4 mb-6">
                            <h3 class="font-semibold text-white mb-3">Pro Features Include:</h3>
                            <ul id="upgradeFeaturesList" class="space-y-2 text-sm text-gray-300">
                                <!-- Features will be populated dynamically -->
                            </ul>
                        </div>
                        
                        <div class="space-y-3">
                            <button id="upgradeModalBtn" class="w-full bg-gradient-to-r from-purple-600 to-orange-600 text-white font-bold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-orange-700 transition-all duration-200 transform hover:scale-105">
                                Upgrade Now - ₦15,000/month
                            </button>
                            <button id="upgradeModalClose" class="w-full text-gray-400 hover:text-white transition-colors">
                                Maybe Later
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Setup event listeners
        const closeBtn = document.getElementById('upgradeModalClose');
        const upgradeBtn = document.getElementById('upgradeModalBtn');
        const modal = document.getElementById('upgradeModal');
        
        if (closeBtn) {
            closeBtn.addEventListener('click', hideUpgradeModal);
        }
        
        if (upgradeBtn) {
            upgradeBtn.addEventListener('click', () => {
                hideUpgradeModal();
                if (window.PaymentsPage && typeof window.PaymentsPage.showPlans === 'function') {
                    window.PaymentsPage.showPlans();
                } else {
                    window.location.href = '/pricing';
                }
            });
        }
        
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    hideUpgradeModal();
                }
            });
        }
        
        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal && !modal.classList.contains('hidden')) {
                hideUpgradeModal();
            }
        });
    }

    function setupInterceptors() {
        // Intercept fetch requests to handle 402 responses
        const originalFetch = window.fetch;
        
        window.fetch = async function(...args) {
            try {
                const response = await originalFetch.apply(this, args);
                
                if (response.status === 402) {
                    console.log('PipwaysUsage: 402 Payment Required intercepted');
                    
                    try {
                        const errorData = await response.clone().json();
                        const feature = extractFeatureFromError(errorData, args[0]);
                        showUpgradeModal(feature, errorData);
                    } catch (e) {
                        console.error('Error parsing 402 response:', e);
                        showUpgradeModal('general');
                    }
                    
                    return response;
                }
                
                return response;
            } catch (error) {
                console.error('Fetch interceptor error:', error);
                throw error;
            }
        };

        // Also intercept API calls if using axios or similar
        if (window.API && typeof window.API.interceptResponse === 'function') {
            window.API.interceptResponse((error) => {
                if (error.response?.status === 402) {
                    const feature = extractFeatureFromError(error.response.data, error.config.url);
                    showUpgradeModal(feature, error.response.data);
                    return Promise.reject(error);
                }
                return Promise.reject(error);
            });
        }
    }

    function extractFeatureFromError(errorData, url) {
        // Try to extract feature from error data or URL
        if (errorData && errorData.feature) {
            return errorData.feature;
        }
        
        if (typeof url === 'string') {
            if (url.includes('/signals/enhanced')) return 'signals_visible';
            if (url.includes('/signals/') && url.includes('/chart-analysis')) return 'signals_detailed_analysis';
            if (url.includes('/ai/chart')) return 'chart_analysis_daily';
            if (url.includes('/ai/mentor')) return 'ai_mentor_daily';
            if (url.includes('/ai/performance')) return 'performance_analysis_monthly';
            if (url.includes('/api/stock')) return 'stock_research_daily';
        }
        
        return 'general';
    }

    async function loadUserLimits() {
        try {
            const user = window.Store?.getUser();
            if (!user) {
                console.log('PipwaysUsage: No user found, skipping limits load');
                return;
            }
            
            // In a real implementation, load from API
            // For now, use mock data based on user tier
            const tier = user.subscription_tier || 'free';
            
            userLimits = {
                tier: tier,
                features: {
                    'chart_analysis_daily': {
                        limit: tier === 'free' ? 2 : 50,
                        usage: 0,
                        remaining: tier === 'free' ? 2 : 50,
                        has_access: true
                    },
                    'ai_mentor_daily': {
                        limit: tier === 'free' ? 5 : 200,
                        usage: 0,
                        remaining: tier === 'free' ? 5 : 200,
                        has_access: true
                    },
                    'performance_analysis_monthly': {
                        limit: tier === 'free' ? 1 : null,
                        usage: 0,
                        remaining: tier === 'free' ? 1 : 'unlimited',
                        has_access: true
                    },
                    'stock_research_daily': {
                        limit: tier === 'free' ? 3 : 100,
                        usage: 0,
                        remaining: tier === 'free' ? 3 : 100,
                        has_access: true
                    },
                    'signals_visible': {
                        limit: tier === 'free' ? 3 : null,
                        usage: 0,
                        remaining: tier === 'free' ? 3 : 'unlimited',
                        has_access: true
                    },
                    'signals_detailed_analysis': {
                        limit: tier === 'free' ? 1 : null,
                        usage: 0,
                        remaining: tier === 'free' ? 1 : 'unlimited',
                        has_access: true
                    },
                    'signals_chart_access': {
                        limit: tier === 'free' ? false : true,
                        has_access: tier !== 'free'
                    },
                    'signals_pattern_filtering': {
                        limit: tier === 'free' ? false : true,
                        has_access: tier !== 'free'
                    },
                    'signals_email_alerts': {
                        limit: tier === 'free' ? false : true,
                        has_access: tier !== 'free'
                    },
                    'webinar_recordings': {
                        limit: tier === 'free' ? false : true,
                        has_access: tier !== 'free'
                    }
                }
            };
            
            console.log('PipwaysUsage: User limits loaded:', userLimits);
            
        } catch (error) {
            console.error('Error loading user limits:', error);
        }
    }

    function showUpgradeModal(feature, options = {}) {
        const modal = document.getElementById('upgradeModal');
        const title = document.getElementById('upgradeModalTitle');
        const message = document.getElementById('upgradeModalMessage');
        const featuresList = document.getElementById('upgradeFeaturesList');
        
        if (!modal) {
            console.error('PipwaysUsage: Upgrade modal not found');
            return;
        }
        
        // Get feature-specific content
        const featureContent = getFeatureUpgradeContent(feature, options);
        
        // Update modal content
        if (title) {
            title.textContent = featureContent.title;
        }
        
        if (message) {
            message.textContent = featureContent.message;
        }
        
        if (featuresList) {
            featuresList.innerHTML = featureContent.features
                .map(feat => `<li class="flex items-center"><i class="fas fa-check text-green-400 mr-2"></i>${feat}</li>`)
                .join('');
        }
        
        // Show modal
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        
        // Track upgrade modal shown
        trackUpgradeModalShown(feature);
    }

    function hideUpgradeModal() {
        const modal = document.getElementById('upgradeModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    function getFeatureUpgradeContent(feature, options = {}) {
        const defaultContent = {
            title: 'Upgrade to Pro',
            message: 'Unlock advanced trading features and tools to enhance your trading journey.',
            features: [
                'Unlimited AI chart analysis',
                'Advanced AI mentor conversations', 
                'Unlimited performance analytics',
                'Full access to trading signals',
                'Priority customer support'
            ]
        };

        // Feature-specific content
        const featureContent = {
            'signals_visible': {
                title: 'Access All Market Signals',
                message: 'Upgrade to Pro to view all active trading signals with detailed analysis.',
                features: [
                    'View unlimited active signals',
                    'Historical signal performance',
                    'Real-time price updates',
                    'Advanced filtering options',
                    'Email signal alerts'
                ]
            },
            'signals_detailed_analysis': {
                title: 'Detailed Signal Analysis',
                message: 'Get in-depth chart analysis and pattern insights for every signal.',
                features: [
                    'Unlimited detailed analysis',
                    'AI pattern recognition',
                    'Risk/reward calculations',
                    'Market structure analysis',
                    'Entry/exit recommendations'
                ]
            },
            'signals_chart_access': {
                title: 'Full Chart Access',
                message: 'Access interactive charts with professional trading tools.',
                features: [
                    'TradingView integration',
                    'Advanced technical indicators',
                    'Pattern overlay tools',
                    'Multiple timeframe analysis',
                    'Screenshot and sharing tools'
                ]
            },
            'signals_pattern_filtering': {
                title: 'Advanced Signal Filtering',
                message: 'Filter signals by pattern type, confidence level, and asset class.',
                features: [
                    'Pattern-based filtering',
                    'Confidence level selection',
                    'Multi-asset class filters',
                    'Country-specific signals',
                    'Custom filter combinations'
                ]
            },
            'signals_email_alerts': {
                title: 'Signal Email Alerts',
                message: 'Never miss a trading opportunity with instant email notifications.',
                features: [
                    'Real-time signal alerts',
                    'Custom notification settings',
                    'Priority signal access',
                    'Mobile-friendly emails',
                    'Alert customization'
                ]
            },
            'chart_analysis_daily': {
                title: 'Unlimited Chart Analysis',
                message: 'Upload unlimited chart images for AI-powered analysis.',
                features: [
                    '50 daily chart analyses (vs 2 free)',
                    'Smart Money Concepts analysis',
                    'Institution order flow insights',
                    'Entry and exit recommendations',
                    'Confidence scoring'
                ]
            },
            'ai_mentor_daily': {
                title: 'Unlimited AI Mentor Access',
                message: 'Get unlimited access to your personal AI trading coach.',
                features: [
                    '200 daily mentor questions (vs 5 free)',
                    'Personalized trading advice',
                    'Strategy recommendations',
                    'Psychology coaching',
                    'Performance improvement tips'
                ]
            },
            'performance_analysis_monthly': {
                title: 'Unlimited Performance Analytics',
                message: 'Upload unlimited trading journals for detailed performance insights.',
                features: [
                    'Unlimited journal uploads',
                    'Advanced performance metrics',
                    'Psychology profiling',
                    'Risk consistency analysis',
                    'Improvement recommendations'
                ]
            },
            'stock_research_daily': {
                title: 'Unlimited Stock Research',
                message: 'Research unlimited stocks with AI-powered fundamental analysis.',
                features: [
                    '100 daily stock analyses (vs 3 free)',
                    'Nigerian and global stocks',
                    'Fundamental analysis',
                    'Sentiment scoring',
                    'Investment recommendations'
                ]
            }
        };

        // Use custom options if provided
        if (options.title || options.message || options.features) {
            return {
                title: options.title || featureContent[feature]?.title || defaultContent.title,
                message: options.message || featureContent[feature]?.message || defaultContent.message,
                features: options.features || featureContent[feature]?.features || defaultContent.features
            };
        }

        return featureContent[feature] || defaultContent;
    }

    function trackUpgradeModalShown(feature) {
        try {
            // Track that upgrade modal was shown
            console.log(`PipwaysUsage: Upgrade modal shown for feature: ${feature}`);
            
            // In production, send analytics event
            if (window.gtag) {
                window.gtag('event', 'upgrade_modal_shown', {
                    feature: feature,
                    user_tier: userLimits.tier || 'free'
                });
            }
        } catch (error) {
            console.error('Error tracking upgrade modal:', error);
        }
    }

    async function checkUsage(feature, amount = 1) {
        try {
            const user = window.Store?.getUser();
            if (!user) {
                return { allowed: false, reason: 'not_authenticated' };
            }
            
            // Pro users have unlimited access
            if (user.subscription_tier === 'pro' || user.subscription_tier === 'enterprise') {
                return { allowed: true, tier: user.subscription_tier };
            }
            
            // Check limits for free users
            const featureLimit = userLimits.features?.[feature];
            if (!featureLimit) {
                return { allowed: false, reason: 'feature_not_found' };
            }
            
            // Boolean features (access/no access)
            if (typeof featureLimit.limit === 'boolean') {
                return { 
                    allowed: featureLimit.limit,
                    reason: featureLimit.limit ? 'allowed' : 'upgrade_required'
                };
            }
            
            // Numeric limits
            if (typeof featureLimit.limit === 'number') {
                const allowed = (featureLimit.usage + amount) <= featureLimit.limit;
                return {
                    allowed: allowed,
                    reason: allowed ? 'allowed' : 'limit_exceeded',
                    usage: featureLimit.usage,
                    limit: featureLimit.limit,
                    remaining: Math.max(0, featureLimit.limit - featureLimit.usage)
                };
            }
            
            // Unlimited (null limit)
            if (featureLimit.limit === null) {
                return { allowed: true, reason: 'unlimited' };
            }
            
            return { allowed: false, reason: 'unknown_limit_type' };
            
        } catch (error) {
            console.error('Error checking usage:', error);
            return { allowed: false, reason: 'error' };
        }
    }

    function getFeatureLimit(feature) {
        const featureLimit = userLimits.features?.[feature];
        if (!featureLimit) return null;
        
        return {
            limit: featureLimit.limit,
            usage: featureLimit.usage || 0,
            remaining: featureLimit.remaining,
            has_access: featureLimit.has_access
        };
    }

    function getUserTier() {
        const user = window.Store?.getUser();
        return user?.subscription_tier || 'free';
    }

    function canAccessFeature(feature) {
        const featureLimit = userLimits.features?.[feature];
        return featureLimit?.has_access || false;
    }

    // Enhanced signals-specific helper functions
    function canViewAllSignals() {
        return canAccessFeature('signals_visible') && userLimits.features?.['signals_visible']?.limit === null;
    }

    function canAccessDetailedAnalysis() {
        return canAccessFeature('signals_detailed_analysis');
    }

    function canAccessFullCharts() {
        return canAccessFeature('signals_chart_access');
    }

    function canUseAdvancedFilters() {
        return canAccessFeature('signals_pattern_filtering');
    }

    function canReceiveSignalAlerts() {
        return canAccessFeature('signals_email_alerts');
    }

    // Public API
    return {
        init,
        showUpgradeModal,
        hideUpgradeModal,
        checkUsage,
        getFeatureLimit,
        getUserTier,
        canAccessFeature,
        loadUserLimits,
        
        // Enhanced signals helpers
        canViewAllSignals,
        canAccessDetailedAnalysis,
        canAccessFullCharts,
        canUseAdvancedFilters,
        canReceiveSignalAlerts
    };
})();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('PipwaysUsage: DOM ready, initializing...');
    PipwaysUsage.init();
});

// Also initialize immediately if DOM is already loaded
if (document.readyState === 'loading') {
    // DOM is still loading, wait for DOMContentLoaded
} else {
    // DOM is already loaded
    console.log('PipwaysUsage: DOM already loaded, initializing...');
    PipwaysUsage.init();
}

// Handle navigation events (for SPAs)
window.addEventListener('popstate', function() {
    console.log('PipwaysUsage: Navigation detected, reloading limits...');
    PipwaysUsage.loadUserLimits();
});
