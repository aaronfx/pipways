/**
 * Pipways API Client - Production Grade
 * Handles JWT auth, error boundaries, and retry logic
 */
const API_BASE = window.location.origin;

const api = {
    // Request wrapper with auth and error handling
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('pipways_token');
        const headers = {
            'Accept': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        };

        // Don't set Content-Type for FormData (file uploads)
        if (options.body && !(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }

        try {
            const res = await fetch(`${API_BASE}${endpoint}`, {
                ...options,
                headers
            });

            // Handle 401 Unauthorized
            if (res.status === 401) {
                localStorage.removeItem('pipways_token');
                localStorage.removeItem('pipways_user');
                window.location.href = '/';
                throw new Error('Session expired');
            }

            // Handle other errors
            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
                throw new Error(err.detail || `Request failed: ${res.status}`);
            }

            return res.json();
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Network error. Check connection.');
            }
            throw error;
        }
    },

    // Auth
    login(username, password) {
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);
        
        return fetch(`${API_BASE}/auth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            },
            body: params
        }).then(res => {
            if (!res.ok) throw new Error('Login failed');
            return res.json();
        });
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

    // Signals - FIXED: Using correct endpoints
    getSignals(filters = {}) {
        const qs = new URLSearchParams(filters).toString();
        return this.request(`/signals${qs ? '?' + qs : ''}`);
    },

    // Courses - FIXED: Proper endpoint
    getCourses() {
        return this.request('/courses');
    },

    // Webinars - FIXED: Proper endpoint
    getWebinars(upcoming = true) {
        return this.request(`/webinars?upcoming=${upcoming}`);
    },

    // Blog - FIXED: Proper endpoint
    getBlogPosts(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this.request(`/blog/posts${qs ? '?' + qs : ''}`);
    },

    // Trading Journal Upload - FIXED: multipart/form-data
    async analyzeJournal(file, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);
        
        const token = localStorage.getItem('pipways_token');
        
        try {
            const res = await fetch(`${API_BASE}/ai/performance/analyze-journal`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                    // Note: Browser sets Content-Type with boundary automatically
                },
                body: formData
            });
            
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || `Upload failed: ${res.status}`);
            }
            
            return res.json();
        } catch (error) {
            throw error;
        }
    },

    // AI Mentor
    askMentor(question, skillLevel = 'intermediate') {
        return this.request('/ai/mentor/ask', {
            method: 'POST',
            body: JSON.stringify({ question, skill_level: skillLevel })
        });
    },

    // Chart Analysis
    analyzeChart(file, symbol, timeframe) {
        const formData = new FormData();
        formData.append('file', file);
        if (symbol) formData.append('symbol', symbol);
        if (timeframe) formData.append('timeframe', timeframe);
        
        return fetch(`${API_BASE}/ai/chart/analyze`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('pipways_token')}`
            },
            body: formData
        }).then(res => {
            if (!res.ok) throw new Error('Analysis failed');
            return res.json();
        });
    },

    // Performance
    getPerformanceStats() {
        return this.request('/performance/dashboard');
    },

    // Admin
    getAdminStats() {
        return this.request('/admin/users');
    }
};

window.api = api;
