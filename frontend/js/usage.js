// ══════════════════════════════════════════════════════════════════════════════
// Pipways Usage Tracking & Upgrade Modal System
// Handles feature limits, 402 interception, and usage badge rendering
// ══════════════════════════════════════════════════════════════════════════════

window.PipwaysUsage = (function() {
    'use strict';

    // ── State ─────────────────────────────────────────────────────────────────
    let userLimits = {};
    let currentTier = 'free';
    let initialized = false;
    let isLoaded = false;

    // ── Feature Configurations ────────────────────────────────────────────────
    const FEATURE_CONFIG = {
        'chart_analysis': {
            displayName: 'AI Chart Analysis',
            description: 'Upload chart images for AI-powered Smart Money analysis',
            limits: { free: 2, basic: 50, pro: null },  // null = unlimited
            period: 'daily'
        },
        'ai_mentor': {
            displayName: 'AI Trading Mentor',
            description: 'Chat with your personal AI trading coach',
            limits: { free: 5, basic: 200, pro: null },
            period: 'daily'
        },
        'performance_analysis': {
            displayName: 'Performance Analytics',
            description: 'Upload trading journal for AI analysis',
            limits: { free: 1, basic: 10, pro: null },
            period: 'monthly'
        },
        'stock_research': {
            displayName: 'AI Stock Research',
            description: 'Fundamental and sentiment analysis on stocks',
            limits: { free: 3, basic: 100, pro: null },
            period: 'daily'
        },
        'signals_visible': {
            displayName: 'Market Signals',
            description: 'Live trading signals from analysts',
            limits: { free: 3, basic: null, pro: null },
            period: 'active'
        },
        'signals_detailed': {
            displayName: 'Signal Analysis',
            description: 'In-depth pattern analysis for signals',
            limits: { free: 1, basic: null, pro: null },
            period: 'daily'
        }
    };

    // ══════════════════════════════════════════════════════════════════════════
    // INITIALIZATION
    // ══════════════════════════════════════════════════════════════════════════

    function init() {
        if (initialized) return;
        initialized = true;

        console.log('PipwaysUsage: Initializing usage tracking system');

        setupUpgradeModal();
        setupFetchInterceptor();
        loadUserLimits();
    }

    // ══════════════════════════════════════════════════════════════════════════
    // LOAD USER LIMITS
    // ══════════════════════════════════════════════════════════════════════════

    async function loadUserLimits() {
        try {
            const token = localStorage.getItem('pipways_token');
            if (!token) {
                console.log('PipwaysUsage: No user found, skipping limits load');
                isLoaded = true;
                return;
            }

            // Try to get user from /auth/me
            const response = await fetch('/auth/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) {
                console.log('PipwaysUsage: Failed to fetch user, using defaults');
                isLoaded = true;
                return;
            }

            const data = await response.json();
            const user = data.user || data;

            currentTier = user.subscription_tier || user.tier || 'free';

            // Build limits from user data or defaults
            userLimits = {
                tier: currentTier,
                features: {}
            };

            // Populate feature limits based on tier
            for (const [featureKey, config] of Object.entries(FEATURE_CONFIG)) {
                const limit = config.limits[currentTier];
                userLimits.features[featureKey] = {
                    limit: limit,
                    usage: user.usage?.[featureKey] || 0,
                    remaining: limit === null ? 'unlimited' : Math.max(0, limit - (user.usage?.[featureKey] || 0)),
                    has_access: limit === null || (limit - (user.usage?.[featureKey] || 0)) > 0
                };
            }

            console.log('PipwaysUsage: User limits loaded for tier:', currentTier);
            isLoaded = true;

            // Dispatch event so dashboard can react
            document.dispatchEvent(new CustomEvent('pipways:usage-updated'));

        } catch (error) {
            console.error('PipwaysUsage: Error loading user limits:', error);
            isLoaded = true;
        }
    }

    // ══════════════════════════════════════════════════════════════════════════
    // FETCH INTERCEPTOR (402 HANDLING)
    // ══════════════════════════════════════════════════════════════════════════

    function setupFetchInterceptor() {
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
                throw error;
            }
        };
    }

    function extractFeatureFromError(errorData, url) {
        if (errorData && errorData.feature) return errorData.feature;

        if (typeof url === 'string') {
            if (url.includes('/ai/chart')) return 'chart_analysis';
            if (url.includes('/ai/mentor')) return 'ai_mentor';
            if (url.includes('/ai/performance')) return 'performance_analysis';
            if (url.includes('/api/stock') || url.includes('/stocks')) return 'stock_research';
            if (url.includes('/signals/enhanced')) return 'signals_visible';
            if (url.includes('/signals/') && url.includes('/chart')) return 'signals_detailed';
        }

        return 'general';
    }

    // ══════════════════════════════════════════════════════════════════════════
    // UPGRADE MODAL
    // ══════════════════════════════════════════════════════════════════════════

    function setupUpgradeModal() {
        if (document.getElementById('upgradeModal')) return;

        const modalHTML = `
            <div id="upgradeModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50" style="backdrop-filter: blur(4px);">
                <div class="bg-gray-900 rounded-lg p-8 max-w-md w-full mx-4 border border-gray-700 shadow-2xl">
                    <div class="text-center">
                        <div class="w-16 h-16 bg-gradient-to-br from-purple-500 to-orange-500 rounded-full flex items-center justify-center mx-auto mb-4">
                            <i class="fas fa-crown text-white text-2xl"></i>
                        </div>
                        <h2 id="upgradeModalTitle" class="text-2xl font-bold text-white mb-2">Upgrade to Pro</h2>
                        <p id="upgradeModalMessage" class="text-gray-400 mb-6">Unlock advanced trading features</p>
                        
                        <div id="upgradeModalFeatures" class="text-left bg-gray-800 rounded-lg p-4 mb-6">
                            <h3 class="font-semibold text-white mb-3">Pro Features Include:</h3>
                            <ul id="upgradeFeaturesList" class="space-y-2 text-sm text-gray-300"></ul>
                        </div>
                        
                        <div class="space-y-3">
                            <button id="upgradeModalBtn" class="w-full bg-gradient-to-r from-purple-600 to-orange-600 text-white font-bold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-orange-700 transition-all">
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

        document.getElementById('upgradeModalClose')?.addEventListener('click', hideUpgradeModal);
        document.getElementById('upgradeModalBtn')?.addEventListener('click', () => {
            hideUpgradeModal();
            window.location.href = '/pricing';
        });
        document.getElementById('upgradeModal')?.addEventListener('click', (e) => {
            if (e.target.id === 'upgradeModal') hideUpgradeModal();
        });
    }

    function showUpgradeModal(feature, options = {}) {
        const modal = document.getElementById('upgradeModal');
        const title = document.getElementById('upgradeModalTitle');
        const message = document.getElementById('upgradeModalMessage');
        const featuresList = document.getElementById('upgradeFeaturesList');

        if (!modal) return;

        const content = getFeatureUpgradeContent(feature);

        if (title) title.textContent = content.title;
        if (message) message.textContent = content.message;
        if (featuresList) {
            featuresList.innerHTML = content.features
                .map(f => `<li class="flex items-center"><i class="fas fa-check text-green-400 mr-2"></i>${f}</li>`)
                .join('');
        }

        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    function hideUpgradeModal() {
        const modal = document.getElementById('upgradeModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    function getFeatureUpgradeContent(feature) {
        const contents = {
            'chart_analysis': {
                title: 'Unlimited Chart Analysis',
                message: 'Upload unlimited charts for AI-powered analysis',
                features: ['50 daily analyses (vs 2 free)', 'Smart Money Concepts', 'Entry & exit recommendations', 'Confidence scoring']
            },
            'ai_mentor': {
                title: 'Unlimited AI Mentor',
                message: 'Get unlimited access to your AI trading coach',
                features: ['200 daily questions (vs 5 free)', 'Personalized advice', 'Strategy coaching', 'Performance tips']
            },
            'signals_visible': {
                title: 'Full Signal Access',
                message: 'View all active trading signals',
                features: ['Unlimited signal access', 'Real-time updates', 'Advanced filtering', 'Email alerts']
            },
            'stock_research': {
                title: 'Unlimited Stock Research',
                message: 'Research any stock with AI analysis',
                features: ['100 daily analyses (vs 3 free)', 'NGX + global stocks', 'Fundamental analysis', 'Sentiment scoring']
            },
            'general': {
                title: 'Upgrade to Pro',
                message: 'Unlock all advanced trading features',
                features: ['Unlimited AI features', 'Full signal access', 'Priority support', 'Advanced analytics']
            }
        };

        return contents[feature] || contents['general'];
    }

    // ══════════════════════════════════════════════════════════════════════════
    // BADGE RENDERING
    // ══════════════════════════════════════════════════════════════════════════

    /**
     * Render a usage badge for a specific feature
     * @param {string} featureName - The feature key (e.g., 'chart_analysis')
     * @param {HTMLElement|string} targetElement - DOM element or selector to render into
     * @param {object} options - Optional display configuration
     */
    function renderBadge(featureName, targetElement, options = {}) {
        // Handle element resolution
        let element;
        if (typeof targetElement === 'string') {
            element = document.querySelector(targetElement);
            if (!element) {
                element = document.querySelector('#' + targetElement);
            }
            if (!element) {
                console.warn(`PipwaysUsage.renderBadge: Target element not found: ${targetElement}`);
                return null;
            }
        } else if (targetElement instanceof HTMLElement) {
            element = targetElement;
        } else {
            console.warn('PipwaysUsage.renderBadge: Invalid target element');
            return null;
        }

        // Get feature config and limits
        const config = FEATURE_CONFIG[featureName];
        const featureData = userLimits.features?.[featureName];

        if (!config) {
            console.warn(`PipwaysUsage.renderBadge: Unknown feature: ${featureName}`);
            return null;
        }

        // Determine what to show based on tier
        const tier = currentTier || 'free';
        const limit = config.limits[tier];
        const usage = featureData?.usage || 0;
        const remaining = limit === null ? 'unlimited' : Math.max(0, limit - usage);

        // Build badge HTML
        let badgeHTML = '';

        if (limit === null) {
            // Unlimited - show Pro badge
            badgeHTML = `
                <div class="flex items-center gap-2 text-xs">
                    <span class="inline-flex items-center px-2 py-0.5 rounded-full font-semibold"
                          style="background:linear-gradient(90deg,rgba(124,58,237,.2),rgba(249,115,22,.2));color:#c4b5fd;border:1px solid rgba(124,58,237,.3);">
                        <i class="fas fa-infinity mr-1" style="font-size:.6rem;"></i>Unlimited
                    </span>
                </div>
            `;
        } else if (limit === 0) {
            // No access
            badgeHTML = `
                <div class="flex items-center gap-2 text-xs">
                    <span class="inline-flex items-center px-2 py-0.5 rounded-full font-semibold"
                          style="background:rgba(239,68,68,.15);color:#f87171;border:1px solid rgba(239,68,68,.3);">
                        <i class="fas fa-lock mr-1" style="font-size:.6rem;"></i>Upgrade Required
                    </span>
                </div>
            `;
        } else {
            // Show usage counter
            const percentUsed = (usage / limit) * 100;
            const isLow = remaining <= 1;
            const color = isLow ? '#f87171' : remaining <= Math.ceil(limit / 3) ? '#fbbf24' : '#34d399';
            const bgColor = isLow ? 'rgba(239,68,68,.1)' : remaining <= Math.ceil(limit / 3) ? 'rgba(251,191,36,.1)' : 'rgba(52,211,153,.1)';
            const borderColor = isLow ? 'rgba(239,68,68,.25)' : remaining <= Math.ceil(limit / 3) ? 'rgba(251,191,36,.25)' : 'rgba(52,211,153,.25)';

            badgeHTML = `
                <div class="flex items-center gap-2">
                    <div class="flex-1">
                        <div class="flex justify-between text-xs mb-1">
                            <span style="color:#6b7280;">${config.period === 'daily' ? 'Today' : 'This month'}</span>
                            <span style="color:${color};font-weight:600;">${remaining}/${limit} remaining</span>
                        </div>
                        <div class="w-full h-1.5 rounded-full" style="background:#1f2937;">
                            <div class="h-full rounded-full transition-all duration-300" 
                                 style="width:${Math.min(100, percentUsed)}%;background:${color};"></div>
                        </div>
                    </div>
                </div>
            `;
        }

        element.innerHTML = badgeHTML;
        return element;
    }

    /**
     * Render a simple tier badge (Free/Basic/Pro)
     * @param {HTMLElement|string} targetElement - DOM element or selector
     * @param {object} options - Optional configuration
     */
    function renderTierBadge(targetElement, options = {}) {
        let element;
        if (typeof targetElement === 'string') {
            element = document.querySelector(targetElement) || document.querySelector('#' + targetElement);
        } else {
            element = targetElement;
        }

        if (!element) {
            console.warn('PipwaysUsage.renderTierBadge: Target element not found');
            return null;
        }

        const tier = options.tier || currentTier || 'free';

        const badges = {
            'free': { text: 'Free', bg: 'rgba(107,114,128,.2)', color: '#9ca3af', border: 'rgba(107,114,128,.3)' },
            'basic': { text: 'Basic', bg: 'rgba(59,130,246,.2)', color: '#60a5fa', border: 'rgba(59,130,246,.3)' },
            'pro': { text: 'Pro', bg: 'linear-gradient(90deg,rgba(124,58,237,.2),rgba(249,115,22,.2))', color: '#c4b5fd', border: 'rgba(124,58,237,.3)', icon: 'fa-crown' },
            'enterprise': { text: 'Enterprise', bg: 'linear-gradient(90deg,rgba(251,191,36,.2),rgba(249,115,22,.2))', color: '#fbbf24', border: 'rgba(251,191,36,.3)', icon: 'fa-building' }
        };

        const config = badges[tier] || badges['free'];

        element.innerHTML = `
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold"
                  style="background:${config.bg};color:${config.color};border:1px solid ${config.border};">
                ${config.icon ? `<i class="fas ${config.icon} mr-1" style="font-size:.6rem;"></i>` : ''}${config.text}
            </span>
        `;

        return element;
    }

    // ══════════════════════════════════════════════════════════════════════════
    // USAGE CHECKING
    // ══════════════════════════════════════════════════════════════════════════

    function checkUsage(feature, amount = 1) {
        const tier = currentTier || 'free';
        const config = FEATURE_CONFIG[feature];
        const featureData = userLimits.features?.[feature];

        if (!config) {
            return { allowed: true, reason: 'unknown_feature' };
        }

        const limit = config.limits[tier];

        // Unlimited
        if (limit === null) {
            return { allowed: true, tier: tier, remaining: 'unlimited' };
        }

        // No access
        if (limit === 0) {
            return { allowed: false, reason: 'upgrade_required', tier: tier };
        }

        // Check numeric limit
        const usage = featureData?.usage || 0;
        const remaining = limit - usage;
        const allowed = remaining >= amount;

        return {
            allowed: allowed,
            reason: allowed ? 'ok' : 'limit_exceeded',
            usage: usage,
            limit: limit,
            remaining: Math.max(0, remaining),
            tier: tier
        };
    }

    function getFeatureLimit(feature) {
        const config = FEATURE_CONFIG[feature];
        const featureData = userLimits.features?.[feature];

        if (!config) return null;

        const tier = currentTier || 'free';
        const limit = config.limits[tier];

        return {
            limit: limit,
            usage: featureData?.usage || 0,
            remaining: limit === null ? 'unlimited' : Math.max(0, limit - (featureData?.usage || 0)),
            period: config.period,
            displayName: config.displayName
        };
    }

    function getUserTier() {
        return currentTier || 'free';
    }

    function canAccessFeature(feature) {
        const config = FEATURE_CONFIG[feature];
        if (!config) return true;

        const tier = currentTier || 'free';
        const limit = config.limits[tier];

        return limit !== 0;
    }

    // ══════════════════════════════════════════════════════════════════════════
    // AUTO-INIT
    // ══════════════════════════════════════════════════════════════════════════

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            console.log('PipwaysUsage: DOM ready, initializing...');
            init();
        });
    } else {
        console.log('PipwaysUsage: DOM ready, initializing...');
        init();
    }

    // ══════════════════════════════════════════════════════════════════════════
    // PUBLIC API
    // ══════════════════════════════════════════════════════════════════════════

    return {
        // State
        get tier() { return currentTier; },
        get isLoaded() { return isLoaded; },
        get limits() { return userLimits; },

        // Core methods
        init: init,
        loadUserLimits: loadUserLimits,
        checkUsage: checkUsage,
        getFeatureLimit: getFeatureLimit,
        getUserTier: getUserTier,
        canAccessFeature: canAccessFeature,

        // Badge rendering
        renderBadge: renderBadge,
        renderTierBadge: renderTierBadge,

        // Modal
        showUpgradeModal: showUpgradeModal,
        hideUpgradeModal: hideUpgradeModal
    };

})();
