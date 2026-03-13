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
        
        const res = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });
        
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Error ${res.status}`);
        }
        
        return res.json();
    },
    
    // Auth
    login(username, password) {
        const form = new FormData();
        form.append('username', username);
        form.append('password', password);
        return fetch(`${API_BASE}/auth/token`, {
            method: 'POST',
            body: form
        }).then(r => r.json());
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
    
    // AI Mentor
    askMentor(question, skillLevel = 'intermediate') {
        return this.request('/ai/mentor/ask', {
            method: 'POST',
            body: JSON.stringify({ question, skill_level: skillLevel })
        });
    },
    
    // Chart Analysis
    analyzeChart(file, symbol, timeframe) {
        const form = new FormData();
        form.append('file', file);
        if (symbol) form.append('symbol', symbol);
        if (timeframe) form.append('timeframe', timeframe);
        return this.request('/ai/chart/analyze', {
            method: 'POST',
            headers: {},
            body: form
        });
    },
    
    // Performance
    analyzeJournal(trades) {
        return this.request('/ai/performance/analyze-journal', {
            method: 'POST',
            body: JSON.stringify(trades)
        });
    }
};
