import { store } from './state.js';
import { router } from './router.js';  // Import router directly

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

            // Handle 401 Unauthorized
            if (response.status === 401) {
                console.log('Token expired, attempting refresh...');
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    // Retry with new token
                    return this.request(endpoint, options);
                } else {
                    // Refresh failed, logout and redirect
                    console.log('Refresh failed, logging out...');
                    store.logout();
                    router.navigate('/login');  // Use imported router, not window.router
                    throw new Error('Session expired. Please login again.');
                }
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Request failed: ${response.status}`);
            }

            return response.json();
        } catch (error) {
            // Don't show toast for auth errors, just throw
            if (!error.message.includes('Session expired')) {
                this.showToast(error.message, 'error');
            }
            throw error;
        }
    }

    async refreshToken() {
        const refreshToken = store.getState().refreshToken;
        if (!refreshToken) {
            console.log('No refresh token available');
            return false;
        }

        try {
            const response = await fetch(`${API_URL}/auth/refresh`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: refreshToken })  // Send in body, not header
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);
                store.setState({ 
                    token: data.access_token, 
                    refreshToken: data.refresh_token 
                });
                console.log('Token refreshed successfully');
                return true;
            }
            
            console.log('Refresh endpoint returned:', response.status);
            return false;
        } catch (e) {
            console.error('Refresh error:', e);
            return false;
        }
    }

    showToast(message, type = 'info') {
        // Remove existing toasts
        const existing = document.querySelectorAll('.toast');
        existing.forEach(t => t.remove());

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 24px;
            background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#6366f1'};
            color: white;
            border-radius: 8px;
            z-index: 10000;
            animation: slideIn 0.3s ease;
            max-width: 400px;
            word-wrap: break-word;
        `;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Auth endpoints
    login = (creds) => this.request('/auth/login', { method: 'POST', body: creds });
    register = (data) => this.request('/auth/register', { method: 'POST', body: data });

    // Admin endpoints
    getStats = () => this.request('/admin/stats');
    getUsers = (page = 1) => this.request(`/admin/users?page=${page}&limit=10`);
    deleteUser = (id) => this.request(`/admin/users/${id}`, { method: 'DELETE' });

    // Blog endpoints
    getPosts = () => this.request('/blog/posts?limit=50');
    createPost = (data) => this.request('/admin/blog', { method: 'POST', body: data });

    // Courses endpoints
    getCourses = () => this.request('/courses?limit=50');
    createCourse = (data) => this.request('/admin/courses', { method: 'POST', body: data });

    // Webinars endpoints
    getWebinars = () => this.request('/webinars?limit=50');
    createWebinar = (data) => this.request('/admin/webinars', { method: 'POST', body: data });

    // Signals endpoints
    createSignal = (data) => this.request('/admin/signals', { method: 'POST', body: data });

    // AI endpoints
    analyzePerformance = (data) => this.request('/ai/analyze/performance', { method: 'POST', body: data });
    analyzeChart = (formData) => this.request('/ai/analyze/chart', { 
        method: 'POST', 
        body: formData,
        headers: {} // Let browser set for FormData
    });
    sendChatMessage = (msg, context = 'trading') => this.request('/ai/chat', { 
        method: 'POST', 
        body: { message: msg, context } 
    });
    getChatHistory = (limit = 50) => this.request(`/ai/chat/history?limit=${limit}`);
}

export const api = new ApiClient();
