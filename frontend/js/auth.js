/**
 * Authentication Module
 */
const auth = {
    currentUser: null,

    init() {
        this.checkAuth();
        this.updateUI();
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
        } catch (e) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            this.showAuthWall();
        }
    },

    showAuthWall() {
        const authWall = document.getElementById('auth-wall');
        const mainApp = document.getElementById('main-app');
        if (authWall) authWall.style.display = 'flex';
        if (mainApp) mainApp.style.display = 'none';
    },

    hideAuthWall() {
        const authWall = document.getElementById('auth-wall');
        const mainApp = document.getElementById('main-app');
        if (authWall) authWall.style.display = 'none';
        if (mainApp) mainApp.style.display = 'block';
    },

    updateUI() {
        const loginBtn = document.getElementById('login-btn');
        const logoutBtn = document.getElementById('logout-btn');
        const userInfo = document.getElementById('user-info');

        if (this.currentUser) {
            if (loginBtn) loginBtn.style.display = 'none';
            if (logoutBtn) logoutBtn.style.display = 'block';
            if (userInfo) {
                userInfo.style.display = 'block';
                userInfo.textContent = this.currentUser.full_name || this.currentUser.email;
            }

            if (this.currentUser.role === 'admin' || this.currentUser.role === 'moderator') {
                this.addAdminLink();
            }
        } else {
            if (loginBtn) loginBtn.style.display = 'block';
            if (logoutBtn) logoutBtn.style.display = 'none';
            if (userInfo) userInfo.style.display = 'none';
        }
    },

    addAdminLink() {
        const navLinks = document.querySelector('.nav-links');
        if (navLinks && !navLinks.querySelector('a[href="/admin"]')) {
            const adminLink = document.createElement('a');
            adminLink.href = '/admin';
            adminLink.textContent = 'Admin';
            navLinks.appendChild(adminLink);
        }
    },

    showLoginModal() {
        const modal = document.getElementById('login-modal');
        if (modal) modal.classList.add('show');
    },

    closeLoginModal() {
        const modal = document.getElementById('login-modal');
        if (modal) modal.classList.remove('show');
    },

    showRegisterModal() {
        this.closeLoginModal();
        const modal = document.getElementById('register-modal');
        if (modal) modal.classList.add('show');
    },

    closeRegisterModal() {
        const modal = document.getElementById('register-modal');
        if (modal) modal.classList.remove('show');
    },

    validatePassword(password) {
        const errors = [];
        if (password.length < 8) errors.push("Minimum 8 characters");
        if (!/[A-Z]/.test(password)) errors.push("One uppercase letter");
        if (!/[a-z]/.test(password)) errors.push("One lowercase letter");
        if (!/[0-9]/.test(password)) errors.push("One number");
        if (!/[@$!%*?&]/.test(password)) errors.push("One special character (@$!%*?&)");
        return errors;
    },

    async handleLogin(e) {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        try {
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            this.currentUser = data.user;
            this.hideAuthWall();
            this.updateUI();
            this.closeLoginModal();
            ui.showToast('Login successful!', 'success');
            ui.handleRoute();
        } catch (error) {
            ui.showToast(error.message || 'Login failed', 'error');
        }
    },

    async handleRegister(e) {
        e.preventDefault();
        const full_name = document.getElementById('reg-name').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;

        // Password validation
        const validationErrors = this.validatePassword(password);
        if (validationErrors.length > 0) {
            ui.showToast('Password requirements: ' + validationErrors.join(', '), 'error');
            return;
        }

        try {
            const response = await fetch('/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, full_name })
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || 'Registration failed');
            }

            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            this.currentUser = data.user;
            this.hideAuthWall();
            this.updateUI();
            this.closeRegisterModal();
            ui.showToast('Registration successful!', 'success');
            ui.handleRoute();
        } catch (error) {
            ui.showToast(error.message || 'Registration failed', 'error');
        }
    },

    logout() {
        // Clear chat history on logout
        if (window.ai && window.ai.chatHistory) {
            window.ai.chatHistory = [];
        }
        const chatContainer = document.getElementById('chat-history');
        if (chatContainer) chatContainer.innerHTML = '';

        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        this.currentUser = null;
        this.showAuthWall();
        this.updateUI();
        ui.showToast('Logged out', 'info');
        window.location.href = '/';
    },

    requireAuth() {
        if (!this.currentUser) {
            this.showLoginModal();
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
