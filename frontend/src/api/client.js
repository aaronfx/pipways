import { store } from '../state.js';

const API_URL = 'https://pipways-api-nhem.onrender.com';

class ApiClient {
    async request(endpoint, options = {}) {
        const token = store.getState().token;
        
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` }),
                ...options.headers
            },
            ...options
        };

        if (config.body && !(config.body instanceof FormData)) {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(`${API_URL}${endpoint}`, config);
            
            if (response.status === 401) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    return this.request(endpoint, options);
                } else {
                    store.logout();
                    window.router.navigate('/login');
                    throw new Error('Session expired');
                }
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Request failed');
            }

            return response.json();
        } catch (error) {
            this.showToast(error.message, 'error');
            throw error;
        }
    }

    async refreshToken() {
        const refreshToken = store.getState().refreshToken;
        if (!refreshToken) return false;

        try {
            const response = await fetch(`${API_URL}/auth/refresh`, {
                method: 'POST',
                headers: { 
                    'Authorization': `Bearer ${refreshToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);
                store.setState({ 
                    token: data.access_token, 
                    refreshToken: data.refresh_token 
                });
                return true;
            }
            return false;
        } catch (e) {
            return false;
        }
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 24px;
            background: ${type === 'error' ? '#ef4444' : '#10b981'};
            color: white;
            border-radius: 8px;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    login = (creds) => this.request('/auth/login', { method: 'POST', body: creds });
    register = (data) => this.request('/auth/register', { method: 'POST', body: data });
    
    getStats = () => this.request('/admin/stats');
    getUsers = (page = 1) => this.request(`/admin/users?page=${page}&limit=10`);
    deleteUser = (id) => this.request(`/admin/users/${id}`, { method: 'DELETE' });
    
    getPosts = () => this.request('/blog/posts?limit=50');
    createPost = (data) => this.request('/admin/blog', { method: 'POST', body: data });
    
    getCourses = () => this.request('/courses?limit=50');
    createCourse = (data) => this.request('/admin/courses', { method: 'POST', body: data });
    
    getWebinars = () => this.request('/webinars?limit=50');
    createWebinar = (data) => this.request('/admin/webinars', { method: 'POST', body: data });
    
    createSignal = (data) => this.request('/admin/signals', { method: 'POST', body: data });
    
    analyzePerformance = (data) => this.request('/ai/analyze/performance', { method: 'POST', body: data });
    analyzeChart = (formData) => this.request('/ai/analyze/chart', { 
        method: 'POST', 
        body: formData,
        headers: {}
    });
    sendChatMessage = (msg, context = 'trading') => this.request('/ai/chat', { 
        method: 'POST', 
        body: { message: msg, context } 
    });
    getChatHistory = (limit = 50) => this.request(`/ai/chat/history?limit=${limit}`);
}

export const api = new ApiClient();
