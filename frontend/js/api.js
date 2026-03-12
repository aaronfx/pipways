const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000/api' 
    : 'https://your-api.onrender.com/api';

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

        try {
            Store.setState('loading', true);
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                Store.logout();
                window.location.hash = '#/login';
                throw new Error('Session expired');
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Request failed');
            }

            return await response.json();
        } catch (error) {
            UI.showToast(error.message, 'error');
            throw error;
        } finally {
            Store.setState('loading', false);
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

        const response = await fetch(`${this.baseURL}/auth/login`, {
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
        return this.request(`/signals?${query}`);
    }

    async createSignal(data) {
        return this.request('/signals', {
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
        return this.request(`/courses?${query}`);
    }

    async createCourse(data) {
        return this.request('/courses', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async getBlogPosts(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/blog?${query}`);
    }

    async getBlogPost(slug) {
        return this.request(`/blog/slug/${slug}`);
    }

    async getWebinars(upcoming = true) {
        return this.request(`/webinars?upcoming=${upcoming}`);
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
        return this.request('/admin/dashboard');
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
        return this.request('/blog/capture-email', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async submitQuiz(courseId, quizId, answers) {
        return this.request(`/courses/${courseId}/quizzes/${quizId}/submit`, {
            method: 'POST',
            body: JSON.stringify({ answers })
        });
    }

    async getMyProgress() {
        return this.request('/courses/my-progress');
    }
}

const API = new ApiClient();