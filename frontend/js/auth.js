/**
 * Pipways Authentication Module
 * Handles login, registration, and token management
 */

const Auth = {
    // API Base URL - MUST match backend router prefix
    API_URL: '/api/auth',
    
    // Token storage keys
    TOKEN_KEY: 'pipways_token',
    USER_KEY: 'pipways_user',
    
    /**
     * Initialize auth module
     */
    init() {
        console.log('Auth module initialized');
        this.bindAuthForms();
        this.checkAuthStatus();
    },
    
    /**
     * Bind login and register form handlers
     */
    bindAuthForms() {
        // Login form
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleLogin();
            });
        }
        
        // Register form
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleRegister();
            });
        }
        
        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }
    },
    
    /**
     * Handle user login
     */
    async handleLogin() {
        const email = document.getElementById('email')?.value;
        const password = document.getElementById('password')?.value;
        
        if (!email || !password) {
            this.showError('Please enter both email and password');
            return;
        }
        
        try {
            this.showLoading(true);
            
            const response = await fetch(`${this.API_URL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || `Login failed: ${response.status}`);
            }
            
            // Store token and user data
            this.setToken(data.access_token);
            this.setUser(data.user || { email: email });
            
            // Redirect to dashboard
            window.location.href = '/dashboard.html';
            
        } catch (error) {
            console.error('Login error:', error);
            this.showError(error.message || 'Login failed. Please try again.');
        } finally {
            this.showLoading(false);
        }
    },
    
    /**
     * Handle user registration
     */
    async handleRegister() {
        const fullName = document.getElementById('fullName')?.value;
        const email = document.getElementById('email')?.value;
        const password = document.getElementById('password')?.value;
        const confirmPassword = document.getElementById('confirmPassword')?.value;
        
        if (!fullName || !email || !password) {
            this.showError('Please fill in all fields');
            return;
        }
        
        if (password !== confirmPassword) {
            this.showError('Passwords do not match');
            return;
        }
        
        if (password.length < 6) {
            this.showError('Password must be at least 6 characters');
            return;
        }
        
        try {
            this.showLoading(true);
            
            const response = await fetch(`${this.API_URL}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    full_name: fullName,
                    email: email,
                    password: password
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Registration failed');
            }
            
            // Store credentials temporarily for auto-login
            document.getElementById('email').value = email;
            document.getElementById('password').value = password;
            
            // Auto-login after registration
            await this.handleLogin();
            
        } catch (error) {
            console.error('Registration error:', error);
            this.showError(error.message || 'Registration failed. Please try again.');
        } finally {
            this.showLoading(false);
        }
    },
    
    /**
     * Check if user is authenticated
     */
    async checkAuthStatus() {
        const token = this.getToken();
        const currentPage = window.location.pathname;
        
        // Skip auth check on login page
        if (currentPage.includes('index.html') || currentPage === '/' || currentPage === '') {
            return;
        }
        
        if (!token) {
            this.redirectToLogin();
            return;
        }
        
        try {
            const response = await fetch(`${this.API_URL}/me`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) {
                if (response.status === 401) {
                    this.logout();
                    return;
                }
                throw new Error('Auth check failed');
            }
            
            const userData = await response.json();
            this.setUser(userData);
            this.updateUserUI(userData);
            
        } catch (error) {
            console.error('Auth check failed:', error);
            // Don't logout on network errors, just log
        }
    },
    
    /**
     * Logout user
     */
    logout() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        this.redirectToLogin();
    },
    
    /**
     * Get stored token
     */
    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },
    
    /**
     * Store token
     */
    setToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
    },
    
    /**
     * Get stored user data
     */
    getUser() {
        const user = localStorage.getItem(this.USER_KEY);
        return user ? JSON.parse(user) : null;
    },
    
    /**
     * Store user data
     */
    setUser(userData) {
        localStorage.setItem(this.USER_KEY, JSON.stringify(userData));
    },
    
    /**
     * Check if user is admin/moderator
     */
    isAdmin() {
        const user = this.getUser();
        return user && (user.role === 'admin' || user.role === 'moderator');
    },
    
    /**
     * Check if user has VIP access
     */
    isVIP() {
        const user = this.getUser();
        return user && (user.subscription_tier === 'vip' || this.isAdmin());
    },
    
    /**
     * Redirect to login page
     */
    redirectToLogin() {
        const currentPage = window.location.pathname;
        if (!currentPage.includes('index.html') && !currentPage.includes('login')) {
            window.location.href = '/index.html';
        }
    },
    
    /**
     * Update UI with user info
     */
    updateUserUI(userData) {
        const userNameEl = document.getElementById('userName');
        const userEmailEl = document.getElementById('userEmail');
        const userTierEl = document.getElementById('userTier');
        
        if (userNameEl) userNameEl.textContent = userData.full_name || userData.email;
        if (userEmailEl) userEmailEl.textContent = userData.email;
        if (userTierEl) userTierEl.textContent = userData.subscription_tier?.toUpperCase() || 'FREE';
    },
    
    /**
     * Show error message
     */
    showError(message) {
        const errorEl = document.getElementById('errorMessage');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
            setTimeout(() => {
                errorEl.style.display = 'none';
            }, 5000);
        } else {
            alert(message);
        }
    },
    
    /**
     * Show/hide loading state
     */
    showLoading(show) {
        const loginBtn = document.getElementById('loginBtn');
        const registerBtn = document.getElementById('registerBtn');
        
        if (loginBtn) {
            loginBtn.disabled = show;
            loginBtn.textContent = show ? 'Loading...' : 'Login';
        }
        
        if (registerBtn) {
            registerBtn.disabled = show;
            registerBtn.textContent = show ? 'Loading...' : 'Create Account';
        }
    }
};

// Initialize auth when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    Auth.init();
});

// Export for use in other modules - BOTH cases for compatibility
window.Auth = Auth;
window.auth = Auth;  // This fixes the "auth is not defined" error
