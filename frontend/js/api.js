/**
 * API Client - Production Grade
 * Handles OAuth2 authentication and JWT Bearer token management
 */
const API_BASE = window.location.origin;

const API = {
    /**
     * Generic request handler with auth header injection
     */
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('pipways_token');
        const headers = {
            'Accept': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        };

        // Don't override Content-Type for FormData (file uploads)
        if (options.body && !(options.body instanceof FormData)) {
            headers['Content-Type'] = headers['Content-Type'] || 'application/json';
        }

        try {
            const res = await fetch(`${API_BASE}${endpoint}`, {
                ...options,
                headers
            });

            if (res.status === 401) {
                // Token expired or invalid
                localStorage.removeItem('pipways_token');
                localStorage.removeItem('pipways_user');
                window.location.href = '/';
                throw new Error('Session expired. Please login again.');
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

    /**
     * OAuth2 Login - Uses URLSearchParams for form-urlencoded format
     */
    async login(username, password) {
        // CRITICAL: URLSearchParams ensures application/x-www-form-urlencoded
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);
        
        const res = await fetch(`${API_BASE}/auth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            },
            body: params
        });
        
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Login failed');
        }
        
        const data = await res.json();
        
        // Store credentials
        localStorage.setItem('pipways_token', data.access_token);
        localStorage.setItem('pipways_user', JSON.stringify(data.user));
        
        return data;
    },

    /**
     * Registration
     */
    register(data) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    /**
     * Get current user profile
     */
    getMe() {
        return this.request('/auth/me');
    },

    /**
     * Logout helper
     */
    logout() {
        localStorage.removeItem('pipways_token');
        localStorage.removeItem('pipways_user');
        window.location.href = '/';
    },

    // Signals
    getSignals(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this.request(`/signals/active?${qs}`);
    },

    createSignal(data) {
        return this.request('/signals/create', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    updateSignal(id, data) {
        return this.request(`/signals/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    deleteSignal(id) {
        return this.request(`/signals/${id}`, {
            method: 'DELETE'
        });
    },

    // Courses
    getCourses() {
        return this.request('/courses/list');
    },

    getCourseProgress() {
        return this.request('/courses-enhanced/progress');
    },

    // Blog
    getBlogPosts(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this.request(`/blog/posts?${qs}`);
    },

    getBlogPost(slug) {
        return this.request(`/blog/posts/${slug}`);
    },

    // Webinars
    getWebinars(upcoming = true) {
        return this.request(`/webinars/upcoming?upcoming=${upcoming}`);
    },

    // AI Mentor
    askMentor(question, skillLevel = 'intermediate', topic = null) {
        return this.request('/ai/mentor/ask', {
            method: 'POST',
            body: JSON.stringify({
                question,
                skill_level: skillLevel,
                topic,
                context: window.location.hash
            })
        });
    },

    getLearningPath(goal, currentLevel, timeAvailable, markets = ['forex']) {
        return this.request('/ai/mentor/learning-path', {
            method: 'POST',
            body: JSON.stringify({
                goal,
                current_level: currentLevel,
                time_available: timeAvailable,
                preferred_markets: markets
            })
        });
    },

    reviewTrade(tradeData) {
        return this.request('/ai/mentor/review-trade', {
            method: 'POST',
            body: JSON.stringify(tradeData)
        });
    },

    getDailyWisdom() {
        return this.request('/ai/mentor/daily-wisdom');
    },

    // Chart Analysis
    analyzeChartImage(file, symbol = null, timeframe = null) {
        const formData = new FormData();
        formData.append('file', file);
        if (symbol) formData.append('symbol', symbol);
        if (timeframe) formData.append('timeframe', timeframe);
        
        return this.request('/ai/chart/analyze', {
            method: 'POST',
            headers: {}, // Let browser set Content-Type with boundary for FormData
            body: formData
        });
    },

    getPatternLibrary(patternType = null) {
        const url = patternType 
            ? `/ai/chart/pattern-library?pattern_type=${patternType}`
            : '/ai/chart/pattern-library';
        return this.request(url);
    },

    // Performance
    analyzeJournal(trades) {
        return this.request('/ai/performance/analyze-journal', {
            method: 'POST',
            body: JSON.stringify(trades)
        });
    },

    getPerformanceStats(days = 30) {
        return this.request(`/ai/performance/dashboard-stats?days=${days}`);
    },

    // Admin
    getAdminStats() {
        return this.request('/admin/users');
    },

    getUsers(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this.request(`/admin/users?${qs}`);
    },

    // Risk Calculator
    calculateRisk(data) {
        return this.request('/risk/calculate', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    getRiskHistory() {
        return this.request('/risk/history');
    }
};

// Export for global use
window.API = API;

// COMPATIBILITY FIX: Alias for modules using lowercase 'api'
window.api = API;
