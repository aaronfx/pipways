const Auth = {
    async init() {
        const token = Store.getToken();
        if (token) {
            try {
                const user = await API.getMe();
                Store.setUser(user, token);
                this.updateUI();
            } catch (e) {
                console.error('Auth init failed:', e);
                Store.logout();
            }
        }
        this.bindEvents();
    },

    bindEvents() {
        document.getElementById('loginBtn')?.addEventListener('click', () => {
            UI.showModal(this.loginForm());
        });

        document.getElementById('registerBtn')?.addEventListener('click', () => {
            UI.showModal(this.registerForm());
        });

        document.getElementById('logoutBtn')?.addEventListener('click', () => {
            Store.logout();
            this.updateUI();
            window.location.hash = '#/';
            UI.showToast('Logged out successfully', 'success');
        });

        document.addEventListener('submit', async (e) => {
            if (e.target.id === 'loginForm') {
                e.preventDefault();
                await this.handleLogin(e.target);
            }
            if (e.target.id === 'registerForm') {
                e.preventDefault();
                await this.handleRegister(e.target);
            }
        });
    },

    loginForm() {
        return `
            <h2>Login</h2>
            <form id="loginForm">
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="username" required placeholder="your@email.com">
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" required placeholder="••••••••">
                </div>
                <button type="submit" class="btn btn-primary btn-block">Login</button>
                <p style="margin-top: 1rem; text-align: center;">
                    Don't have an account? <a href="#" onclick="UI.closeModal(); document.getElementById('registerBtn').click(); return false;">Register</a>
                </p>
            </form>
        `;
    },

    registerForm() {
        return `
            <h2>Create Account</h2>
            <form id="registerForm">
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email" required placeholder="your@email.com">
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" required minlength="8" placeholder="Min 8 characters">
                </div>
                <div class="form-group">
                    <label>Full Name</label>
                    <input type="text" name="full_name" placeholder="John Doe">
                </div>
                <button type="submit" class="btn btn-primary btn-block">Create Account</button>
                <p style="margin-top: 1rem; text-align: center;">
                    Already have an account? <a href="#" onclick="UI.closeModal(); document.getElementById('loginBtn').click(); return false;">Login</a>
                </p>
            </form>
        `;
    },

    async handleLogin(form) {
        const formData = new FormData(form);
        const email = formData.get('username');
        const password = formData.get('password');

        try {
            const response = await API.login(email, password);
            Store.setUser(response.user || { email }, response.access_token);
            this.updateUI();
            UI.closeModal();
            UI.showToast('Welcome back!', 'success');
            window.location.hash = '#/dashboard';
        } catch (error) {
            UI.showToast(error.message, 'error');
        }
    },

    async handleRegister(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);

        try {
            await API.register(data);
            // Auto login after register
            const loginRes = await API.login(data.email, data.password);
            Store.setUser(loginRes.user || { email: data.email }, loginRes.access_token);
            this.updateUI();
            UI.closeModal();
            UI.showToast('Account created successfully!', 'success');
            window.location.hash = '#/dashboard';
        } catch (error) {
            UI.showToast(error.message, 'error');
        }
    },

    updateUI() {
        const user = Store.state.user;
        const loginBtn = document.getElementById('loginBtn');
        const registerBtn = document.getElementById('registerBtn');
        const userMenu = document.getElementById('userMenu');
        const userName = document.getElementById('userName');
        const dashboardLink = document.getElementById('dashboardLink');
        const adminLink = document.getElementById('adminLink');

        if (user) {
            if (loginBtn) loginBtn.style.display = 'none';
            if (registerBtn) registerBtn.style.display = 'none';
            if (userMenu) userMenu.style.display = 'flex';
            if (userName) userName.textContent = user.email || user.username;
            if (dashboardLink) dashboardLink.style.display = 'inline';
            if (adminLink && user.is_admin) adminLink.style.display = 'inline';
        } else {
            if (loginBtn) loginBtn.style.display = 'inline-block';
            if (registerBtn) registerBtn.style.display = 'inline-block';
            if (userMenu) userMenu.style.display = 'none';
            if (dashboardLink) dashboardLink.style.display = 'none';
            if (adminLink) adminLink.style.display = 'none';
        }
    },

    requireAuth() {
        if (!Store.isAuthenticated()) {
            UI.showModal(this.loginForm());
            UI.showToast('Please login to access this page', 'warning');
            return false;
        }
        return true;
    },

    requireAdmin() {
        if (!Store.state.isAdmin) {
            window.location.hash = '#/';
            UI.showToast('Admin access required', 'error');
            return false;
        }
        return true;
    }
};
