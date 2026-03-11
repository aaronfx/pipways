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
        if (!token) return;

        try {
            const user = await api.get('/auth/me');
            this.currentUser = user;
            this.updateUI();
        } catch (e) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
        }
    },

    updateUI() {
        const loginBtn = document.getElementById('login-btn');
        const logoutBtn = document.getElementById('logout-btn');
        const userInfo = document.getElementById('user-info');

        if (this.currentUser) {
            loginBtn.style.display = 'none';
            logoutBtn.style.display = 'block';
            userInfo.style.display = 'block';
            userInfo.textContent = this.currentUser.full_name || this.currentUser.email;

            // Show admin link if admin
            if (this.currentUser.role === 'admin' || this.currentUser.role === 'moderator') {
                this.addAdminLink();
            }
        } else {
            loginBtn.style.display = 'block';
            logoutBtn.style.display = 'none';
            userInfo.style.display = 'none';
        }
    },

    addAdminLink() {
        const navLinks = document.querySelector('.nav-links');
        if (!navLinks.querySelector('a[href="/admin"]')) {
            const adminLink = document.createElement('a');
            adminLink.href = '/admin';
            adminLink.textContent = 'Admin';
            navLinks.appendChild(adminLink);
        }
    },

    showLoginModal() {
        document.getElementById('login-modal').classList.add('show');
    },

    closeLoginModal() {
        document.getElementById('login-modal').classList.remove('show');
    },

    showRegisterModal() {
        this.closeLoginModal();
        document.getElementById('register-modal').classList.add('show');
    },

    closeRegisterModal() {
        document.getElementById('register-modal').classList.remove('show');
    },

    async handleLogin(e) {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        try {
            // Use direct fetch for auth endpoints (not under /api)
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

        try {
            // Use direct fetch for auth endpoints (not under /api)
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
            this.updateUI();
            this.closeRegisterModal();
            ui.showToast('Registration successful!', 'success');
            ui.handleRoute();
        } catch (error) {
            ui.showToast(error.message || 'Registration failed', 'error');
        }
    },

    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        this.currentUser = null;
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
