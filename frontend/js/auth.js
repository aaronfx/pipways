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
        document.getElementById('login-error').style.display = 'none';
        document.getElementById('register-error').style.display = 'none';
    },

    showLogin() {
        document.getElementById('register-form').classList.add('hidden');
        document.getElementById('login-form').classList.remove('hidden');
        document.getElementById('login-error').style.display = 'none';
        document.getElementById('register-error').style.display = 'none';
    },

    updateUI() {
        if (!this.currentUser) return;

        document.getElementById('user-name').textContent = this.currentUser.full_name || this.currentUser.email;
        document.getElementById('user-email').textContent = this.currentUser.email;
        document.getElementById('user-avatar').textContent = (this.currentUser.full_name || this.currentUser.email).charAt(0).toUpperCase();

        if (this.currentUser.role === 'admin' || this.currentUser.role === 'moderator') {
            document.getElementById('admin-badge').classList.remove('hidden');
            document.getElementById('admin-nav-item').classList.remove('hidden');
        } else {
            document.getElementById('admin-badge').classList.add('hidden');
            document.getElementById('admin-nav-item').classList.add('hidden');
        }

        const vipBtn = document.getElementById('btn-telegram-vip');
        if (vipBtn && this.currentUser.subscription_tier === 'vip') {
            vipBtn.innerHTML = '<i class="fas fa-crown"></i> Join VIP Channel';
            vipBtn.onclick = () => window.open('https://t.me/pipways_vip', '_blank');
            vipBtn.classList.remove('btn-premium');
            vipBtn.classList.add('btn-success');
        }
    },

    async handleLogin(e) {
        e.preventDefault();
        const form = e.target;
        const errorDiv = document.getElementById('login-error');
        
        ui.showLoading('Logging in...');
        errorDiv.style.display = 'none';
        errorDiv.textContent = '';

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
                console.error('Server returned non-JSON:', text.substring(0, 200));
                
                if (response.status === 500) {
                    throw new Error('Server error. Please try again later.');
                } else if (response.status === 503) {
                    throw new Error('Database not connected. Please contact support.');
                } else if (response.status === 404) {
                    throw new Error('API endpoint not found.');
                } else {
                    throw new Error(`Server error (${response.status}): ${text.substring(0, 100)}`);
                }
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || data.message || `Login failed: ${response.status}`);
            }

            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            this.currentUser = data.user;
            
            this.hideAuthWall();
            this.updateUI();
            ui.showToast('Login successful!', 'success');
            
            if (window.app) {
                setTimeout(() => app.initUserData(), 100);
            }
            
        } catch (error) {
            console.error('Login error:', error);
            errorDiv.textContent = error.message || 'Network error. Please check your connection.';
            errorDiv.style.display = 'block';
        } finally {
            ui.hideLoading();
        }
    },

    async handleRegister(e) {
        e.preventDefault();
        const form = e.target;
        const errorDiv = document.getElementById('register-error');
        
        const password = form.password.value;
        if (password.length < 8) {
            errorDiv.textContent = 'Password must be at least 8 characters';
            errorDiv.style.display = 'block';
            return;
        }
        if (!/[A-Z]/.test(password)) {
            errorDiv.textContent = 'Password must contain an uppercase letter';
            errorDiv.style.display = 'block';
            return;
        }
        if (!/[a-z]/.test(password)) {
            errorDiv.textContent = 'Password must contain a lowercase letter';
            errorDiv.style.display = 'block';
            return;
        }
        if (!/[0-9]/.test(password)) {
            errorDiv.textContent = 'Password must contain a number';
            errorDiv.style.display = 'block';
            return;
        }

        ui.showLoading('Creating account...');
        errorDiv.style.display = 'none';

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
                const text = await response.text();
                throw new Error('Server error: ' + text.substring(0, 100));
            }

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
            console.error('Registration error:', error);
            errorDiv.textContent = error.message || 'Registration failed. Please try again.';
            errorDiv.style.display = 'block';
        } finally {
            ui.hideLoading();
        }
    },

    logout() {
        if (window.ai && window.ai.chatHistory) {
            window.ai.chatHistory = [];
        }
        
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        this.currentUser = null;
        
        this.showAuthWall();
        
        document.getElementById('admin-badge').classList.add('hidden');
        document.getElementById('admin-nav-item').classList.add('hidden');
        
        document.getElementById('login-form').reset();
        document.getElementById('register-form').reset();
        
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
