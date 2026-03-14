/**
 * Pipways API Client - Production Grade
 */
const API_BASE = window.location.origin;

const api = {
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('pipways_token');
        const headers = {
            'Accept': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        };

        if (options.body && !(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }

        try {
            console.log(`[API] ${options.method || 'GET'} ${endpoint}`);
            const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
            
            if (res.status === 401) {
                localStorage.removeItem('pipways_token');
                localStorage.removeItem('pipways_user');
                window.location.href = '/';
                throw new Error('Session expired');
            }

            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
                throw new Error(err.detail || `Request failed: ${res.status}`);
            }

            return res.json();
        } catch (error) {
            console.error('[API Error]', error);
            throw error;
        }
    },

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

    // FIXED: Correct endpoints matching main.py
    getSignals() {
        return this.request('/signals');
    },

    getCourses() {
        return this.request('/courses');
    },

    getWebinars(upcoming = true) {
        return this.request(`/webinars?upcoming=${upcoming}`);
    },

    // FIXED: Using /blog instead of /blog/posts (adjust if your blog.py has specific routes)
    getBlogPosts() {
        return this.request('/blog');
    },

    analyzeJournal(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        return fetch(`${API_BASE}/ai/performance/analyze-journal`, {
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

    askMentor(question, skillLevel = 'intermediate') {
        return this.request('/ai/mentor/ask', {
            method: 'POST',
            body: JSON.stringify({ question, skill_level: skillLevel })
        });
    },

    getAdminStats() {
        return this.request('/admin/users');
    }
};

window.api = api;
