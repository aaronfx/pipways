/**
 * API Client Module
 * Handles all HTTP communication with the backend
 */

const api = {
    baseURL: '',  // Empty for same-origin
    
    async request(endpoint, options = {}) {
        // Ensure endpoint starts with /
        if (!endpoint.startsWith('/')) {
            endpoint = '/' + endpoint;
        }
        
        const url = `${this.baseURL}${endpoint}`;
        
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // Add auth token if available
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }

        // Handle body serialization
        if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            
            // Handle non-JSON responses (500 errors return HTML)
            const contentType = response.headers.get('content-type');
            
            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    window.location.reload();
                    throw new Error('Session expired. Please login again.');
                }
                
                // Try to parse JSON error, fallback to text
                let errorMessage;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.message || `Request failed: ${response.status}`;
                } catch (e) {
                    const text = await response.text();
                    errorMessage = `Server error (${response.status}): ${text.substring(0, 100)}`;
                }
                throw new Error(errorMessage);
            }

            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            return await response.text();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    get(endpoint) { return this.request(endpoint, { method: 'GET' }); },
    post(endpoint, body) { return this.request(endpoint, { method: 'POST', body }); },
    put(endpoint, body) { return this.request(endpoint, { method: 'PUT', body }); },
    delete(endpoint) { return this.request(endpoint, { method: 'DELETE' }); },
    upload(endpoint, formData) { 
        return this.request(endpoint, { 
            method: 'POST', 
            body: formData, 
            headers: {} 
        }); 
    }
};
