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
        const token = Store.getToken(); // Use Store method

        const headers = {
            ...this.defaultHeaders,
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        };

        if (options.body instanceof FormData) {
            delete headers['Content-Type'];
        }

        try {
            Store.setState('loading', true);
            
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (!response.ok) {
                let errorMessage = `Error ${response.status}`;
                try {
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        const errorData = await response.json();
                        errorMessage = errorData.detail || errorData.message || JSON.stringify(errorData);
                    } else {
                        const text = await response.text();
                        if (text && text.length < 200 && !text.includes('<')) {
                            errorMessage = text;
                        }
                    }
                } catch (e) {
                    // Ignore parse errors
                }
                throw new Error(errorMessage);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            return await response.text();
            
        } catch (error) {
            if (error.message === 'Failed to fetch') {
                throw new Error('Network error. Please check your connection.');
            }
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

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Login failed');
        }

        return response.json();
    }

    async getMe() {
        return this.request('/auth/me');
    }

    // ... (keep all other existing methods)
}

const API = new ApiClient();
