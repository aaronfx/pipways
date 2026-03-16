/**
 * Pipways API Client — Production Grade
 * Fixes: baseURL, defaultHeaders, captureEmail, admin methods,
 *        trading analytics, AI stats, user toggle.
 */

const API_BASE = window.location.origin;

const API = {

    // ── FIX: baseURL alias so blog_enhanced.js (uses API.baseURL) doesn't crash ──
    baseURL: window.location.origin,

    // ── FIX: defaultHeaders getter so blog_enhanced.js doesn't crash ──────────
    get defaultHeaders() {
        const token = localStorage.getItem('pipways_token');
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
        };
    },

    // ── Core request handler ──────────────────────────────────────────────────
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

            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
                throw new Error(err.detail || `Request failed: ${res.status}`);
            }

            return res.json();
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Network error. Check your connection.');
            }
            throw error;
        }
    },

    // ── Authentication ────────────────────────────────────────────────────────
    async login(username, password) {
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);

        const res = await fetch(`${API_BASE}/auth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
            },
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
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    getMe() {
        return this.request('/auth/me');
    },

    logout() {
        localStorage.removeItem('pipways_token');
        localStorage.removeItem('pipways_user');
        window.location.href = '/';
    },

    // ── Signals ───────────────────────────────────────────────────────────────
    getSignals(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this.request(`/signals/active?${qs}`);
    },

    createSignal(data) {
        return this.request('/signals/create', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    updateSignal(id, data) {
        return this.request(`/signals/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    deleteSignal(id) {
        return this.request(`/signals/${id}`, { method: 'DELETE' });
    },

    // ── Courses ───────────────────────────────────────────────────────────────
    getCourses() {
        return this.request('/courses/list');
    },

    getCourseProgress() {
        return this.request('/courses-enhanced/progress');
    },

    // ── Blog ──────────────────────────────────────────────────────────────────
    getBlogPosts(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this.request(`/blog/posts?${qs}`);
    },

    getBlogPost(slug) {
        return this.request(`/blog/posts/${slug}`);
    },

    // ── FIX: captureEmail was missing — referenced in blog_enhanced.js ────────
    captureEmail(data) {
        return this.request('/blog/capture-email', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    // ── Webinars ──────────────────────────────────────────────────────────────
    getWebinars(upcoming = true) {
        return this.request(`/webinars/upcoming?upcoming=${upcoming}`);
    },

    // ── AI Mentor ─────────────────────────────────────────────────────────────
    askMentor(question, skillLevel = 'intermediate', topic = null) {
        return this.request('/ai/mentor/ask', {
            method: 'POST',
            body: JSON.stringify({
                question,
                skill_level: skillLevel,
                topic,
                context: window.location.hash,
            }),
        });
    },

    getLearningPath(goal, currentLevel, timeAvailable, markets = ['forex']) {
        return this.request('/ai/mentor/learning-path', {
            method: 'POST',
            body: JSON.stringify({
                goal,
                current_level: currentLevel,
                time_available: timeAvailable,
                preferred_markets: markets,
            }),
        });
    },

    reviewTrade(tradeData) {
        return this.request('/ai/mentor/review-trade', {
            method: 'POST',
            body: JSON.stringify(tradeData),
        });
    },

    getDailyWisdom() {
        return this.request('/ai/mentor/daily-wisdom');
    },

    // ── Chart Analysis ────────────────────────────────────────────────────────
    analyzeChartImage(file, symbol = null, timeframe = null) {
        const formData = new FormData();
        formData.append('file', file);
        if (symbol) formData.append('symbol', symbol);
        if (timeframe) formData.append('timeframe', timeframe);
        return this.request('/ai/chart/analyze', {
            method: 'POST',
            headers: {},          // browser sets Content-Type with boundary
            body: formData,
        });
    },

    getPatternLibrary(patternType = null) {
        const url = patternType
            ? `/ai/chart/pattern-library?pattern_type=${patternType}`
            : '/ai/chart/pattern-library';
        return this.request(url);
    },

    // ── Performance / Journal ─────────────────────────────────────────────────
    analyzeJournal(trades) {
        return this.request('/ai/performance/analyze-journal', {
            method: 'POST',
            body: JSON.stringify(trades),
        });
    },

    getPerformanceStats(days = 30) {
        return this.request(`/ai/performance/dashboard-stats?days=${days}`);
    },

    // ── Risk Calculator ───────────────────────────────────────────────────────
    calculateRisk(data) {
        return this.request('/risk/calculate', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    getRiskHistory() {
        return this.request('/risk/history');
    },

    // ── Admin — overview stats (backward-compat path) ────────────────────────
    getAdminStats() {
        return this.request('/admin/users');
    },

    // ── Admin — paginated user list ───────────────────────────────────────────
    getAdminUsers(page = 1, perPage = 20, search = '') {
        const qs = new URLSearchParams({
            page,
            per_page: perPage,
            ...(search && { search }),
        }).toString();
        return this.request(`/admin/users/list?${qs}`);
    },

    // ── Admin — toggle user active / inactive ─────────────────────────────────
    toggleUser(userId) {
        return this.request(`/admin/users/${userId}/toggle`, { method: 'POST' });
    },

    // ── Admin — trading analytics ─────────────────────────────────────────────
    getTradingAnalytics() {
        return this.request('/admin/trading-analytics');
    },

    // ── Admin — AI usage stats ────────────────────────────────────────────────
    getAIStats() {
        return this.request('/admin/ai-stats');
    },
};

// Make available globally under both names
window.API = API;
window.api = API;   // backward compat for modules that use lowercase `api`
