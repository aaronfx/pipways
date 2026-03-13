const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://pipwaysapp.onrender.com';

class ApiClient {
    constructor() {
        this.baseURL = API_BASE_URL;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const token = Store ? Store.getToken() : localStorage.getItem('token');

        const headers = {
            ...this.defaultHeaders,
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        };

        if (options.body instanceof FormData) {
            delete headers['Content-Type'];
        }

        try {
            if (Store) Store.setState('loading', true);
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '/index.html';
                throw new Error('Session expired');
            }

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Request failed' }));
                throw new Error(error.detail || `Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            if (typeof UI !== 'undefined') UI.showToast(error.message, 'error');
            throw error;
        } finally {
            if (Store) Store.setState('loading', false);
        }
    }

    async register(data) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async login(username, password) {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${this.baseURL}/auth/token`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Invalid credentials');
        return response.json();
    }

    async getMe() {
        return this.request('/auth/me');
    }

    async getSignals(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/signals/active?${query}`);
    }

    async createSignal(data) {
        return this.request('/signals/create', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateSignal(id, data) {
        return this.request(`/signals/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async deleteSignal(id) {
        return this.request(`/signals/${id}`, {
            method: 'DELETE'
        });
    }

    async getCourses(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/courses/list?${query}`);
    }

    async createCourse(data) {
        return this.request('/courses', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async getBlogPosts(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/blog/posts?${query}`);
    }

    async getBlogPost(slug) {
        return this.request(`/blog/posts/${slug}`);
    }

    async getWebinars(upcoming = true) {
        return this.request(`/webinars/upcoming?upcoming=${upcoming}`);
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        return this.request('/media/upload', {
            method: 'POST',
            headers: {},
            body: formData
        });
    }

    async getAdminStats() {
        return this.request('/admin/users');
    }

    async getUsers(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/admin/users?${query}`);
    }

    async calculateRisk(data) {
        return this.request('/risk/calculate', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async getRiskHistory() {
        return this.request('/risk/history');
    }

    async captureEmail(data) {
        return this.request('/blog-enhanced/capture-email', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async submitQuiz(courseId, quizId, answers) {
        return this.request(`/courses-enhanced/courses/${courseId}/complete`, {
            method: 'POST',
            body: JSON.stringify({ lesson_id: quizId, answers })
        });
    }

    // AI Market Analysis
    async analyzeMarket(data) {
        return this.request('/ai/analyze', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async batchScreen(symbols) {
        return this.request('/ai/batch-screen', {
            method: 'POST',
            body: JSON.stringify(symbols)
        });
    }

    async getSentiment(symbol) {
        return this.request(`/ai/sentiment/${symbol}`);
    }

    async validateSignal(data) {
        return this.request('/ai/validate-signal', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // AI Mentor
    async askMentor(question, skillLevel = 'intermediate', topic = null) {
        return this.request('/ai/mentor/ask', {
            method: 'POST',
            body: JSON.stringify({
                question,
                skill_level: skillLevel,
                topic,
                context: window.location.hash
            })
        });
    }

    async getLearningPath(goal, currentLevel, timeAvailable, markets = ['forex']) {
        return this.request('/ai/mentor/learning-path', {
            method: 'POST',
            body: JSON.stringify({
                goal,
                current_level: currentLevel,
                time_available: timeAvailable,
                preferred_markets: markets
            })
        });
    }

    async reviewTrade(tradeData) {
        return this.request('/ai/mentor/review-trade', {
            method: 'POST',
            body: JSON.stringify(tradeData)
        });
    }

    async getDailyWisdom() {
        return this.request('/ai/mentor/daily-wisdom');
    }

    // Chart Analysis
    async analyzeChartImage(file, symbol = null, timeframe = null) {
        const formData = new FormData();
        formData.append('file', file);
        if (symbol) formData.append('symbol', symbol);
        if (timeframe) formData.append('timeframe', timeframe);
        
        return this.request('/ai/chart/analyze', {
            method: 'POST',
            headers: {},
            body: formData
        });
    }

    async getPatternLibrary(patternType = null) {
        const url = patternType 
            ? `/ai/chart/pattern-library?pattern_type=${patternType}`
            : '/ai/chart/pattern-library';
        return this.request(url, { method: 'POST' });
    }

    // Performance Analysis
    async analyzeJournal(trades) {
        return this.request('/ai/performance/analyze-journal', {
            method: 'POST',
            body: JSON.stringify(trades)
        });
    }

    async getPerformanceStats(days = 30) {
        return this.request(`/ai/performance/dashboard-stats?days=${days}`);
    }
}

const API = new ApiClient();
