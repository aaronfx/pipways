// In your api.js request method, ensure you have this error handling:
async request(endpoint, options = {}) {
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

    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
    }

    if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
        config.body = JSON.stringify(config.body);
    }

    try {
        const response = await fetch(url, config);
        const contentType = response.headers.get('content-type');
        
        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                auth.currentUser = null;
                auth.showAuthWall();
                throw new Error('Session expired. Please login again.');
            }
            
            if (response.status === 403) {
                throw new Error('Forbidden - Admin access required');
            }
            
            let errorMessage;
            try {
                if (contentType && contentType.includes('application/json')) {
                    const errorData = await response.clone().json();
                    errorMessage = errorData.detail || errorData.message || `Request failed: ${response.status}`;
                } else {
                    const text = await response.clone().text();
                    errorMessage = `Server error (${response.status}): ${text.substring(0, 100)}`;
                }
            } catch (e) {
                errorMessage = `Request failed: ${response.status}`;
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
}
