/**
 * API Client - Complete
 */
const API_BASE = window.location.origin;

const API = {
    async request(endpoint, options = {}) {
        const token = Store.getToken();
        const headers = {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        };

        if (options.body instanceof FormData) {
            delete headers['Content-Type'];
        }

        try {
            Store.setLoading(true);
            
            const res = await fetch(`${API_BASE}${endpoint}`, {
                ...options,
                headers
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || `Error ${res.status}`);
            }

            return res.json();
        } catch (error) {
            if (error.message === 'Failed to fetch') {
                throw new Error('Network error. Please check your connection.');
            }
            throw error;
        } finally {
            Store.setLoading(false);
        }
    },

    // Auth
    async login(username, password) {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        const res = await fetch(`${API_BASE}/auth/token`, {
            method: 'POST',
            body: formData
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Login failed');
        }
        
        return res.json();
    },

    register(data) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    getMe() {
        return this.request('/auth/me');
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
            headers: {},
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
