/**
 * Authentication Module
 * Handles login, register, logout, and auth state
 */

const auth = {
    currentUser: null,

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
            const user = await api.get('/auth/me');
            this.currentUser = user;
            this.hideAuthWall();
            this.updateUI();
            
            // Load initial data
            if (window.app) {
                app.initUserData();
            }
        } catch (e) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            this.showAuthWall();
        }
    },

    showAuthWall() {
        document.getElementById('auth-wall').classList.remove('hidden');
        document.getElementById('main-app').classList.add('hidden');
    },

    hideAuthWall() {
        document.getElementById('auth-wall').classList.add('hidden');
        document.getElementById('main-app').classList.remove('hidden');
    },

    showRegister() {
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('register-form').classList.remove('hidden');
    },

    showLogin() {
        document.getElementById('register-form').classList.add('hidden');
        document.getElementById('login-form').classList.remove('hidden');
    },

    updateUI() {
        if (!this.currentUser) return;

        // Update user info
        document.getElementById('user-name').textContent = this.currentUser.full_name || this.currentUser.email;
        document.getElementById('user-email').textContent = this.currentUser.email;
        document.getElementById('user-avatar').textContent = (this.currentUser.full_name || this.currentUser.email).charAt(0).toUpperCase();

        // Show admin badge if applicable
        if (this.currentUser.role === 'admin' || this.currentUser.role === 'moderator') {
            document.getElementById('admin-badge').classList.remove('hidden');
            document.getElementById('admin-nav-item').classList.remove('hidden');
        }

        // Update telegram buttons based on subscription
        if (this.currentUser.subscription_tier === 'vip') {
            const vipBtn = document.getElementById('btn-telegram-vip');
            if (vipBtn) {
                vipBtn.textContent = 'Join VIP Channel';
                vipBtn.onclick = () => window.open('https://t.me/pipways_vip', '_blank');
            }
        }
    },

    async handleLogin(e) {
        e.preventDefault();
        const form = e.target;
        const errorDiv = document.getElementById('login-error');
        
        ui.showLoading('Logging in...');

        try {
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: form.email.value,
                    password: form.password.value
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }

            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            this.currentUser = data.user;
            
            this.hideAuthWall();
            this.updateUI();
            ui.showToast('Login successful!', 'success');
            
            // Load user data
            if (window.app) app.initUserData();
            
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        } finally {
            ui.hideLoading();
        }
    },

    async handleRegister(e) {
        e.preventDefault();
        const form = e.target;
        const errorDiv = document.getElementById('register-error');

        // Validate password
        const password = form.password.value;
        if (password.length < 8) {
            errorDiv.textContent = 'Password must be at least 8 characters';
            errorDiv.style.display = 'block';
            return;
        }

        ui.showLoading('Creating account...');

        try {
            const response = await fetch('/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: form.email.value,
                    password: form.password.value,
                    full_name: form.full_name.value
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Registration failed');
            }

            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            this.currentUser = data.user;
            
            this.hideAuthWall();
            this.updateUI();
            ui.showToast('Account created successfully!', 'success');
            
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        } finally {
            ui.hideLoading();
        }
    },

    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        this.currentUser = null;
        
        // Clear chat history
        if (window.ai) ai.chatHistory = [];
        
        this.showAuthWall();
        ui.showToast('Logged out successfully', 'info');
    },

    requireAuth() {
        if (!this.currentUser) {
            ui.showToast('Please login to access this feature', 'error');
            return false;
        }
        return true;
    },

    requireAdmin() {
        if (!this.currentUser || (this.currentUser.role !== 'admin' && this.currentUser.role !== 'moderator')) {
            ui.showToast('Admin access required', 'error');
            return false;
        }
        return true;
    }
};
