/**
 * Pipways Authentication Module
 * Handles login, registration, and token management
 */

const Auth = {

    API_URL: "/api/auth",

    TOKEN_KEY: "pipways_token",
    USER_KEY: "pipways_user",

    init() {
        this.bindAuthForms();
    },

    bindAuthForms() {

        const loginForm = document.getElementById("loginForm");
        if (loginForm) {
            loginForm.addEventListener("submit", (e) => {
                e.preventDefault();
                this.handleLogin();
            });
        }

        const registerForm = document.getElementById("registerForm");
        if (registerForm) {
            registerForm.addEventListener("submit", (e) => {
                e.preventDefault();
                this.handleRegister();
            });
        }

        const logoutBtn = document.getElementById("logoutBtn");
        if (logoutBtn) {
            logoutBtn.addEventListener("click", () => this.logout());
        }
    },

    async handleLogin() {

        const email = document.getElementById("email")?.value.trim();
        const password = document.getElementById("password")?.value.trim();

        if (!email || !password) {
            this.showError("Please enter both email and password");
            return;
        }

        try {

            this.showLoading(true);

            const response = await fetch(`${this.API_URL}/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({
                    email,
                    password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Login failed");
            }

            this.setToken(data.access_token);

            // FIX: use backend user object
            this.setUser(data.user);

            window.location.href = "/dashboard.html";

        } catch (error) {

            console.error("Login error:", error);
            this.showError(error.message);

        } finally {

            this.showLoading(false);

        }
    },

    async handleRegister() {

        const fullName = document.getElementById("fullName")?.value;
        const email = document.getElementById("email")?.value;
        const password = document.getElementById("password")?.value;

        if (!fullName || !email || !password) {
            this.showError("Please fill in all fields");
            return;
        }

        try {

            this.showLoading(true);

            const response = await fetch(`${this.API_URL}/register`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    full_name: fullName,
                    email,
                    password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail);
            }

            await this.handleLogin();

        } catch (error) {

            this.showError(error.message);

        } finally {

            this.showLoading(false);

        }
    },

    logout() {

        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);

        window.location.href = "/index.html";

    },

    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    setToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
    },

    setUser(user) {
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    },

    showError(message) {

        const errorEl = document.getElementById("errorMessage");

        if (errorEl) {

            errorEl.textContent = message;
            errorEl.style.display = "block";

        } else {

            alert(message);

        }

    },

    showLoading(show) {

        const loginBtn = document.getElementById("loginBtn");

        if (loginBtn) {

            loginBtn.disabled = show;
            loginBtn.textContent = show ? "Loading..." : "Login";

        }

    }

};

document.addEventListener("DOMContentLoaded", () => {
    Auth.init();
});

window.Auth = Auth;
