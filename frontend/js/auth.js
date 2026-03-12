/**
 * Authentication Module
 * Fixed: Admin button visibility, role checking, auth flow, and loading overlay
 */

const auth = {
    currentUser: null,
    isLoading: false,

    init() {
        this.checkAuth();
    },

    async checkAuth() {
        const token = localStorage.getItem('access_token');
        if (!token) {
            this.showAuthWall();
            return;
        }

        try {
            const response = await fetch(`${window.location.origin}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Auth check failed');
            }
            
            const user = await response.json();
            this.currentUser = user;
            this.hideAuthWall();
            this.updateUI();
            
            // Initialize app data after successful auth
            if (window.app) {
                app.initUserData();
            }
        } catch (e) {
            console.error('Auth check failed:', e);
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            this.showAuthWall();
        }
    },

    showAuthWall() {
        const authWall = document.getElementById('auth-wall');
        const mainApp = document.getElementById('main-app');
        if (authWall) authWall.classList.remove('hidden');
        if (mainApp) mainApp.classList.add('hidden');
        
        // Reset current user
        this.currentUser = null;
        this.updateAdminUI();
    },

    hideAuthWall() {
        const authWall = document.getElementById('auth-wall');
        const mainApp = document.getElementById('main-app');
        if (authWall) authWall.classList.add('hidden');
        if (mainApp) mainApp.classList.remove('hidden');
    },

    showRegister() {
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        const loginError = document.getElementById('login-error');
        const registerError = document.getElementById('register-error');
        
        if (loginForm) loginForm.classList.add('hidden');
        if (registerForm) registerForm.classList.remove('hidden');
        if (loginError) loginError.style.display = 'none';
        if (registerError) registerError.style.display = 'none';
    },

    showLogin() {
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        const loginError = document.getElementById('login-error');
        const registerError = document.getElementById('register-error');
        
        if (registerForm) registerForm.classList.add('hidden');
        if (loginForm) loginForm.classList.remove('hidden');
        if (loginError) loginError.style.display = 'none';
        if (registerError) registerError.style.display = 'none';
    },

    updateUI() {
        if (!this.currentUser) {
            this.updateAdminUI();
            return;
        }

        // Update user info displays
        const userName = document.getElementById('user-name');
        const userEmail = document.getElementById('user-email');
        const userAvatar = document.getElementById('user-avatar');
        
        if (userName) userName.textContent = this.currentUser.full_name || this.currentUser.email;
        if (userEmail) userEmail.textContent = this.currentUser.email;
        if (userAvatar) {
            userAvatar.textContent = (this.currentUser.full_name || this.currentUser.email).charAt(0).toUpperCase();
        }

        // Update VIP button if applicable
        const vipBtn = document.getElementById('btn-telegram-vip');
        if (vipBtn && this.currentUser.subscription_tier === 'vip') {
            vipBtn.innerHTML = '<i class="fas fa-crown"></i> Join VIP Channel';
            vipBtn.onclick = () => window.open('https://t.me/pipways_vip', '_blank');
            vipBtn.classList.remove('btn-premium');
            vipBtn.classList.add('btn-success');
        }

        // Update admin UI elements
        this.updateAdminUI();
    },

    updateAdminUI() {
        // Determine if user is admin
        const isAdmin = this.currentUser && (this.currentUser.role === 'admin' || this.currentUser.role === 'moderator');
        
        // Update admin badge in sidebar
        const adminBadge = document.getElementById('admin-badge');
        if (adminBadge) {
            if (isAdmin) {
                adminBadge.classList.remove('hidden');
            } else {
                adminBadge.classList.add('hidden');
            }
        }
        
        // Update admin nav item visibility
        const adminNavItem = document.getElementById('admin-nav-item');
        if (adminNavItem) {
            if (isAdmin) {
                adminNavItem.classList.remove('hidden');
            } else {
                adminNavItem.classList.add('hidden');
            }
        }
    },

    async handleLogin(e) {
        e.preventDefault();
        if (this.isLoading) return;
        
        const form = e.target;
        const errorDiv = document.getElementById('login-error');
        
        ui.showLoading('Logging in...');
        this.isLoading = true;
        
        if (errorDiv) {
            errorDiv.style.display = 'none';
            errorDiv.textContent = '';
        }

        try {
            const response = await fetch(`${window.location.origin}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: form.email.value,
                    password: form.password.value
                })
            });

            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                throw new Error('Server returned non-JSON response');
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || data.message || `Login failed: ${response.status}`);
            }

            // Store tokens
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            
            // Set current user
            this.currentUser = data.user;
            
            // Update UI
            this.hideAuthWall();
            this.updateUI();
            ui.showToast('Login successful!', 'success');
            
            // Initialize app data
            if (window.app) {
                setTimeout(() => app.initUserData(), 100);
            }
            
        } catch (error) {
            console.error('Login error:', error);
            if (errorDiv) {
                errorDiv.textContent = error.message || 'Network error. Please check your connection.';
                errorDiv.style.display = 'block';
            }
        } finally {
            ui.forceHideLoading(); // Force hide to ensure overlay is removed
            this.isLoading = false;
        }
    },

    async handleRegister(e) {
        e.preventDefault();
        if (this.isLoading) return;
        
        const form = e.target;
        const errorDiv = document.getElementById('register-error');
        
        const password = form.password.value;
        
        // Password validation
        if (password.length < 8) {
            if (errorDiv) {
                errorDiv.textContent = 'Password must be at least 8 characters';
                errorDiv.style.display = 'block';
            }
            return;
        }
        if (!/[A-Z]/.test(password)) {
            if (errorDiv) {
                errorDiv.textContent = 'Password must contain an uppercase letter';
                errorDiv.style.display = 'block';
            }
            return;
        }
        if (!/[a-z]/.test(password)) {
            if (errorDiv) {
                errorDiv.textContent = 'Password must contain a lowercase letter';
                errorDiv.style.display = 'block';
            }
            return;
        }
        if (!/[0-9]/.test(password)) {
            if (errorDiv) {
                errorDiv.textContent = 'Password must contain a number';
                errorDiv.style.display = 'block';
            }
            return;
        }

        ui.showLoading('Creating account...');
        this.isLoading = true;
        
        if (errorDiv) errorDiv.style.display = 'none';

        try {
            const response = await fetch(`${window.location.origin}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: form.email.value,
                    password: form.password.value,
                    full_name: form.full_name.value
                })
            });

            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Server error');
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Registration failed');
            }

            // Store tokens
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            
            // Set current user
            this.currentUser = data.user;
            
            // Update UI
            this.hideAuthWall();
            this.updateUI();
            ui.showToast('Account created successfully!', 'success');
            
            // Initialize app data
            if (window.app) {
                setTimeout(() => app.initUserData(), 100);
            }
            
        } catch (error) {
            console.error('Registration error:', error);
            if (errorDiv) {
                errorDiv.textContent = error.message || 'Registration failed. Please try again.';
                errorDiv.style.display = 'block';
            }
        } finally {
            ui.forceHideLoading(); // Force hide to ensure overlay is removed
            this.isLoading = false;
        }
    },

    logout() {
        // Clear AI chat history if exists
        if (window.ai && window.ai.chatHistory) {
            window.ai.chatHistory = [];
        }
        
        // Clear stored tokens
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Reset user state
        this.currentUser = null;
        
        // Show auth wall
        this.showAuthWall();
        
        // Reset forms
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        
        if (loginForm) loginForm.reset();
        if (registerForm) registerForm.reset();
        
        // Switch back to login view
        this.showLogin();
        
        ui.showToast('Logged out successfully', 'info');
    },

    requireAuth() {
        if (!this.currentUser) {
            ui.showToast('Please login to access this feature', 'error');
            this.showAuthWall();
            return false;
        }
        return true;
    },

    requireAdmin() {
        if (!this.currentUser) {
            ui.showToast('Please login to access this feature', 'error');
            this.showAuthWall();
            return false;
        }
        
        if (this.currentUser.role !== 'admin' && this.currentUser.role !== 'moderator') {
            ui.showToast('Admin access required', 'error');
            return false;
        }
        
        return true;
    },

    // Token refresh handler
    async refreshToken() {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
            this.logout();
            return null;
        }

        try {
            const response = await fetch(`${window.location.origin}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${refreshToken}`
                }
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            return data.access_token;
        } catch (error) {
            console.error('Token refresh error:', error);
            this.logout();
            return null;
        }
    },

    // Get current auth token
    getToken() {
        return localStorage.getItem('access_token');
    },

    // Check if user has specific role
    hasRole(role) {
        return this.currentUser && this.currentUser.role === role;
    },

    // Check if user is VIP
    isVip() {
        return this.currentUser && this.currentUser.subscription_tier === 'vip';
    }
};
