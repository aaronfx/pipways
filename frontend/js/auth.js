const Auth = {
    async init() {
        const token = Store.getToken();
        if (token) {
            try {
                const user = await API.getMe();
                Store.setUser(user, token);
                this.updateUI();
            } catch (e) {
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
                    <label>Email/Username</label>
                    <input type="text" name="username" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit" class="btn btn-primary btn-block">Login</button>
            </form>
        `;
    },

    registerForm() {
        return `
            <h2>Register</h2>
            <form id="registerForm">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" name="username" required>
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" required minlength="8">
                </div>
                <div class="form-group">
                    <label>First Name</label>
                    <input type="text" name="first_name" required>
                </div>
                <div class="form-group">
                    <label>Last Name</label>
                    <input type="text" name="last_name" required>
                </div>
                <button type="submit" class="btn btn-primary btn-block">Register</button>
            </form>
        `;
    },

    async handleLogin(form) {
        const formData = new FormData(form);
        try {
            const response = await API.login(
                formData.get('username'),
                formData.get('password')
            );
            Store.setUser(response.user, response.access_token);
            this.updateUI();
            UI.closeModal();
            UI.showToast('Login successful!', 'success');
            window.location.hash = '#/dashboard';
        } catch (error) {
            UI.showToast(error.message, 'error');
        }
    },

    async handleRegister(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);

        try {
            const response = await API.register(data);
            const loginRes = await API.login(data.username, data.password);
            Store.setUser(loginRes.user, loginRes.access_token);
            this.updateUI();
            UI.closeModal();
            UI.showToast('Registration successful!', 'success');
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
            loginBtn.style.display = 'none';
            registerBtn.style.display = 'none';
            userMenu.style.display = 'flex';
            userName.textContent = user.username;
            dashboardLink.style.display = 'inline';

            if (user.is_admin) {
                adminLink.style.display = 'inline';
            } else {
                adminLink.style.display = 'none';
            }
        } else {
            loginBtn.style.display = 'inline-block';
            registerBtn.style.display = 'inline-block';
            userMenu.style.display = 'none';
            dashboardLink.style.display = 'none';
            adminLink.style.display = 'none';
        }
    },

    requireAuth() {
        if (!Store.isAuthenticated()) {
            window.location.hash = '#/login';
            UI.showToast('Please login first', 'warning');
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