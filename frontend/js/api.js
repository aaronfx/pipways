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
        const token = Store.getToken();

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
            Store.setState('loading', true);
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                Store.logout();
                window.location.hash = '#/';
                throw new Error('Session expired. Please login again.');
            }

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Request failed' }));
                throw new Error(error.detail || `Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            UI.showToast(error.message, 'error');
            throw error;
        } finally {
            Store.setState('loading', false);
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

        if (!response.ok) throw new Error('Invalid credentials');
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
}

const API = new ApiClient();
