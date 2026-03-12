/**
 * Pipways Authentication Module v3.5
 * Handles login, registration, and token management
 */

const Auth = {
    API_URL: '/auth',
    TOKEN_KEY: 'pipways_token',
    USER_KEY: 'pipways_user',
    _initialized: false,
    
    /**
     * Initialize auth module
     */
    init() {
        // Guard against double initialization (app.js also calls this)
        if (this._initialized) {
            return;
        }
        this._initialized = true;
        
        console.log('Auth module initialized');
        this.bindAuthForms();
        this.checkAuthStatus();
    },
    
    /**
     * Bind login and register form handlers
     */
    bindAuthForms() {
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleLogin();
            });
        }
        
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleRegister();
            });
        }
        
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }
    },
    
    /**
     * Handle user login - READS DIRECTLY FROM FORM INPUTS ONLY
     */
    async handleLogin() {
        // Read credentials directly from form fields only - NO URL PARAMS
        const emailField = document.getElementById('email');
        const passwordField = document.getElementById('password');
        
        // Validate elements exist
        if (!emailField || !passwordField) {
            this.showError('Login form not found');
            return;
        }
        
        // Get values directly from inputs
        const email = emailField.value.trim();
        const password = passwordField.value;
        
        // Validate fields
        if (!email || !password) {
            this.showError('Please enter both email and password');
            return;
        }
        
        try {
            this.showLoading(true);
            
            // POST to /auth/login
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
                throw new Error(data.detail || 'Login failed');
            }
            
            // Store token and user data
            this.setToken(data.access_token);
            this.setUser({
                email: email,
                ...data
            });
            
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
        const fullName = document.getElementById('fullName')?.value?.trim();
        const email = document.getElementById('email')?.value?.trim();
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
        
        if (!token) {
            this.redirectToLogin();
            return false;
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
                    return false;
                }
                throw new Error('Auth check failed');
            }
            
            const userData = await response.json();
            this.setUser(userData);
            this.updateUserUI(userData);
            
            return true;
            
        } catch (error) {
            console.error('Auth check failed:', error);
            return false;
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
     * Redirect to login page
     */
    redirectToLogin() {
        if (!window.location.pathname.includes('index.html') && 
            !window.location.pathname.includes('login')) {
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

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    Auth.init();
});

// Export for use in other modules
window.Auth = Auth;
