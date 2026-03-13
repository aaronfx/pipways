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
        const token = localStorage.getItem('token');

        const headers = {
            ...this.defaultHeaders,
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        };

        // Remove Content-Type for FormData
        if (options.body instanceof FormData) {
            delete headers['Content-Type'];
        }

        try {
            // Show loading if Store exists
            if (typeof Store !== 'undefined' && Store.setState) {
                Store.setState('loading', true);
            }
            
            const response = await fetch(url, {
                ...options,
                headers
            });

            // Handle non-OK responses safely
            if (!response.ok) {
                let errorMessage = `Error ${response.status}`;
                const contentType = response.headers.get('content-type');
                
                try {
                    // Try to parse as JSON first
                    if (contentType && contentType.includes('application/json')) {
                        const errorData = await response.json();
                        errorMessage = errorData.detail || errorData.message || JSON.stringify(errorData);
                    } else {
                        // Try to get text
                        const text = await response.text();
                        // Only use text if it's short and not HTML
                        if (text && text.length < 200 && !text.includes('<')) {
                            errorMessage = text;
                        } else if (text.includes('<')) {
                            errorMessage = `Server error (${response.status}). Please try again.`;
                        }
                    }
                } catch (parseError) {
                    // If parsing fails, use status
                    errorMessage = `Request failed (${response.status})`;
                }
                
                throw new Error(errorMessage);
            }

            // Parse successful response
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
            
        } catch (error) {
            // Handle network errors
            if (error.message === 'Failed to fetch') {
                throw new Error('Network error. Please check your connection.');
            }
            
            // Clean up common error messages
            let cleanMessage = error.message;
            if (cleanMessage.includes('Unexpected token') || cleanMessage.includes('not valid JSON')) {
                cleanMessage = 'Server error. Please try again later.';
            }
            
            // Show toast if UI exists
            if (typeof UI !== 'undefined' && UI.showToast) {
                UI.showToast(cleanMessage, 'error');
            }
            
            throw new Error(cleanMessage);
        } finally {
            if (typeof Store !== 'undefined' && Store.setState) {
                Store.setState('loading', false);
            }
        }
    }

    // Auth endpoints
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

        if (!response.ok) {
            let errorMessage = 'Login failed';
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                const text = await response.text();
                if (text && text.length < 200 && !text.includes('<')) {
                    errorMessage = text;
                }
            }
            throw new Error(errorMessage);
        }

        return response.json();
    }

    async getMe() {
        return this.request('/auth/me');
    }

    // Signals endpoints
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

    // Courses endpoints
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

    async getMyProgress() {
        return this.request('/courses-enhanced/progress');
    }

    // Blog endpoints
    async getBlogPosts(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/blog/posts?${query}`);
    }

    async getBlogPost(slug) {
        return this.request(`/blog/posts/${slug}`);
    }

    // Webinars endpoints
    async getWebinars(upcoming = true) {
        return this.request(`/webinars/upcoming?upcoming=${upcoming}`);
    }

    // Media endpoints
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        return this.request('/media/upload', {
            method: 'POST',
            headers: {},
            body: formData
        });
    }

    // Admin endpoints
    async getAdminStats() {
        return this.request('/admin/users');
    }

    async getUsers(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/admin/users?${query}`);
    }

    // Risk calculator endpoints
    async calculateRisk(data) {
        return this.request('/risk/calculate', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async getRiskHistory() {
        return this.request('/risk/history');
    }

    // Blog enhanced endpoints
    async captureEmail(data) {
        return this.request('/blog-enhanced/capture-email', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Quiz endpoints
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
