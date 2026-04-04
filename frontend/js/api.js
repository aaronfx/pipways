/**
 * Pipways — Canonical API Client  (replaces both app.js API object and api.js)
 *
 * Usage in every page:
 *   <script src="/js/api.js"></script>
 *   const data = await API.getSignals();
 *
 * Exposed as both  window.API  and  window.api  (lowercase alias for legacy modules).
 */

const API_BASE = window.location.origin;

const API = {

    // ── Meta ─────────────────────────────────────────────────────────────────
    baseURL: window.location.origin,

    get defaultHeaders() {
        const token = localStorage.getItem('pipways_token');
        return {
            'Content-Type': 'application/json',
            'Accept':        'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
        };
    },

    // ── Core request ─────────────────────────────────────────────────────────
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('pipways_token');
        const headers = {
            'Accept': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers,
        };

        // Never override Content-Type for FormData (file uploads)
        if (options.body && !(options.body instanceof FormData)) {
            headers['Content-Type'] = headers['Content-Type'] || 'application/json';
        }

        try {
            const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

            if (res.status === 401) {
                localStorage.removeItem('pipways_token');
                localStorage.removeItem('pipways_user');
                window.location.href = '/';
                throw new Error('Session expired. Please log in again.');
            }

            // ── 402: subscription limit reached → show upgrade modal ────
            if (res.status === 402) {
                const err = await res.json().catch(() => ({ detail: 'Upgrade required' }));
                const upgradeError = new Error(err.detail || 'Feature limit reached. Please upgrade your plan.');
                upgradeError.status = 402;
                upgradeError.upgrade = true;
                // Trigger upgrade modal if PaymentsPage is available
                if (window.PaymentsPage && typeof window.PaymentsPage.showUpgradeModal === 'function') {
                    try { window.PaymentsPage.showUpgradeModal(err.feature || ''); } catch(e) {}
                }
                throw upgradeError;
            }

            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
                throw new Error(err.detail || `Request failed: ${res.status}`);
            }

            return res.json();
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Network error. Please check your connection.');
            }
            throw error;
        }
    },

    // ── Authentication ────────────────────────────────────────────────────────
    async login(email, password) {
        const params = new URLSearchParams();
        params.append('username', email);
        params.append('password', password);
        const res = await fetch(`${API_BASE}/auth/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json' },
            body: params,
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Login failed');
        }
        const data = await res.json();
        localStorage.setItem('pipways_token', data.access_token);
        localStorage.setItem('pipways_user', JSON.stringify(data.user));
        return data;
    },

    register(data) {
        return this.request('/auth/register', { method: 'POST', body: JSON.stringify(data) });
    },

    getMe() { return this.request('/auth/me'); },

    logout() {
        localStorage.removeItem('pipways_token');
        localStorage.removeItem('pipways_user');
        window.location.href = '/';
    },

    // ── Signals ───────────────────────────────────────────────────────────────
    getSignals(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this.request(`/signals/active${qs ? '?' + qs : ''}`);
    },

    createSignal(data) {
        return this.request('/signals/create', { method: 'POST', body: JSON.stringify(data) });
    },

    // ── Courses ───────────────────────────────────────────────────────────────
    getCourses()        { return this.request('/courses/list'); },
    getCourseProgress() { return this.request('/courses-enhanced/progress'); },
    getCourse(id)       { return this.request(`/courses/${id}`); },

    // ── Blog ──────────────────────────────────────────────────────────────────
    getBlogPosts(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this.request(`/blog/posts${qs ? '?' + qs : ''}`);
    },
    getBlogPost(slug) { return this.request(`/blog/posts/${slug}`); },
    captureEmail(data) {
        return this.request('/blog/capture-email', { method: 'POST', body: JSON.stringify(data) });
    },

    // ── Webinars ──────────────────────────────────────────────────────────────
    getWebinars(upcoming = true) {
        return this.request(`/webinars/upcoming?upcoming=${upcoming}`);
    },

    // ── AI Mentor ─────────────────────────────────────────────────────────────
    askMentor(question, skillLevel = 'intermediate', topic = null) {
        return this.request('/ai/mentor/ask', {
            method: 'POST',
            body: JSON.stringify({ question, skill_level: skillLevel, topic, context: window.location.hash }),
        });
    },

    getMentorInsights() { return this.request('/ai/mentor/insights'); },
    getMentorHistory()  { return this.request('/ai/mentor/history'); },

    clearMentorHistory() {
        return this.request('/ai/mentor/clear-history', { method: 'POST' });
    },

    getLearningPath(goal, currentLevel, timeAvailable, markets = ['forex']) {
        return this.request('/ai/mentor/learning-path', {
            method: 'POST',
            body: JSON.stringify({ goal, current_level: currentLevel, time_available: timeAvailable, preferred_markets: markets }),
        });
    },

    reviewTrade(tradeData) {
        return this.request('/ai/mentor/review-trade', { method: 'POST', body: JSON.stringify(tradeData) });
    },

    getDailyWisdom() { return this.request('/ai/mentor/daily-wisdom'); },

    // ── Chart Analysis ────────────────────────────────────────────────────────
    analyzeChartImage(file, symbol = null, timeframe = null) {
        const formData = new FormData();
        formData.append('file', file);
        if (symbol)    formData.append('symbol', symbol);
        if (timeframe) formData.append('timeframe', timeframe);
        return this.request('/ai/chart/analyze', { method: 'POST', headers: {}, body: formData });
    },

    getPatternLibrary(patternType = null) {
        const url = patternType
            ? `/ai/chart/pattern-library?pattern_type=${patternType}`
            : '/ai/chart/pattern-library';
        return this.request(url);
    },

    // ── Performance / Journal ─────────────────────────────────────────────────
    analyzeJournal(trades) {
        return this.request('/ai/performance/analyze-journal', { method: 'POST', body: JSON.stringify(trades) });
    },

    getPerformanceStats(days = 30) {
        return this.request(`/ai/performance/dashboard-stats?days=${days}`);
    },

    // ── Risk Calculator ───────────────────────────────────────────────────────
    calculateRisk(data) {
        return this.request('/risk/calculate', { method: 'POST', body: JSON.stringify(data) });
    },

    getRiskHistory() { return this.request('/risk/history'); },

    // ── Stock Terminal ────────────────────────────────────────────────────────
    analyzeStock(symbol)    { return this.request(`/api/stock/analyze/${encodeURIComponent(symbol)}`); },
    buildPortfolio(data)    { return this.request('/api/stock/portfolio',   { method: 'POST', body: JSON.stringify(data) }); },
    compareStocks(symbols)  { return this.request('/api/stock/compare',     { method: 'POST', body: JSON.stringify({ symbols }) }); },

    // ── Payments (Paystack) ──────────────────────────────────────────────────────
    getPaymentConfig()  { return this.request('/payments/config'); },
    getPaymentPlans()   { return this.request('/payments/plans'); },
    initializePayment(planKey, currency = 'NGN') {
        return this.request('/payments/initialize', {
            method: 'POST',
            body: JSON.stringify({ plan_key: planKey, currency }),
        });
    },
    verifyPayment(reference) { return this.request(`/payments/verify/${reference}`); },
    getPaymentHistory()  { return this.request('/payments/history'); },

    // ── Email ─────────────────────────────────────────────────────────────────
    captureLeadEmail(email, name = '', source = 'general') {
        return this.request('/email/capture', {
            method: 'POST',
            body: JSON.stringify({ email, name, source }),
        });
    },
    getEmailPrefs()         { return this.request('/email/preferences'); },
    saveEmailPrefs(prefs)   {
        return this.request('/email/preferences', {
            method: 'POST',
            body: JSON.stringify(prefs),
        });
    },

    // ── Admin ─────────────────────────────────────────────────────────────────
    /** Full dashboard stats — total users, signals, AI usage, recent users, growth chart */
    getAdminStats() { return this.request('/admin/users'); },

    /** Paginated user list with optional search */
    getAdminUsers(page = 1, perPage = 20, search = '') {
        const qs = new URLSearchParams({ page, per_page: perPage, ...(search && { search }) }).toString();
        return this.request(`/admin/users/list?${qs}`);
    },

    /** Toggle a user's is_active flag */
    toggleUser(userId) { return this.request(`/admin/users/${userId}/toggle`, { method: 'POST' }); },

    /** Aggregated trading performance metrics */
    getTradingAnalytics() { return this.request('/admin/trading-analytics'); },

    /** AI feature usage stats */
    getAIStats() { return this.request('/admin/ai-stats'); },

    // ── CMS helpers (used by cms.js module) ──────────────────────────────────
    cms: {},   // populated by cms.js when it loads
};

// Expose globally under both names for backward compatibility
window.API = API;
window.api = API;
