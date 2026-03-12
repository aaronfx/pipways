/**
 * Pipways Authentication Module
 * Fixed: Explicit event prevention to stop GET form submission
 */

const Auth = {
    API_URL: "/api/auth",
    TOKEN_KEY: "pipways_token",
    USER_KEY: "pipways_user",

    init() {
        console.log('Auth module initializing...');
        this.bindAuthForms();
        this.checkExistingAuth();
    },

    bindAuthForms() {
        // Critical: Bind to forms with explicit prevention
        const loginForm = document.getElementById("login-form");
        if (loginForm) {
            console.log('Binding login form');
            loginForm.addEventListener("submit", (e) => {
                e.preventDefault();  // STOP default submission
                e.stopImmediatePropagation(); // STOP other listeners
                this.handleLogin(e);
                return false; // Extra safety for older browsers
            });
        }

        const registerForm = document.getElementById("register-form");
        if (registerForm) {
            registerForm.addEventListener("submit", (e) => {
                e.preventDefault();
                e.stopImmediatePropagation();
                this.handleRegister(e);
                return false;
            });
        }

        // Logout button
        const logoutBtn = document.getElementById("logoutBtn");
        if (logoutBtn) {
            logoutBtn.addEventListener("click", () => this.logout());
        }
    },

    async handleLogin(event) {
        // Double-check prevention
        if (event) event.preventDefault();
        
        const form = event ? event.target : document.getElementById("login-form");
        const formData = new FormData(form);
        const email = formData.get("email")?.trim();
        const password = formData.get("password")?.trim();

        if (!email || !password) {
            this.showError("Please enter both email and password", "login");
            return false;
        }

        console.log(`Attempting POST login for: ${email}`);

        try {
            this.showLoading(true, "login");
            this.clearError("login");

            const response = await fetch(`${this.API_URL}/login`, {
                method: "POST",  // Explicit POST
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();
            console.log('Login response:', data);

            if (!response.ok) {
                throw new Error(data.detail || data.message || `HTTP ${response.status}`);
            }

            // Store authentication data
            this.setToken(data.access_token);
            this.setUser(data.user);
            
            console.log('Login successful, redirecting to dashboard...');
            window.location.href = "/dashboard.html";

        } catch (error) {
            console.error("Login error:", error);
            this.showError(error.message || "Login failed. Please try again.", "login");
        } finally {
            this.showLoading(false, "login");
        }
        
        return false; // Prevent any default behavior
    },

    async handleRegister(event) {
        if (event) event.preventDefault();
        
        const form = event ? event.target : document.getElementById("register-form");
        const formData = new FormData(form);
        const fullName = formData.get("full_name")?.trim();
        const email = formData.get("email")?.trim();
        const password = formData.get("password")?.trim();

        if (!fullName || !email || !password) {
            this.showError("Please fill in all fields", "register");
            return false;
        }

        if (password.length < 8) {
            this.showError("Password must be at least 8 characters", "register");
            return false;
        }

        try {
            this.showLoading(true, "register");
            this.clearError("register");

            const response = await fetch(`${this.API_URL}/register`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({ 
                    full_name: fullName, 
                    email, 
                    password 
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || data.message || `HTTP ${response.status}`);
            }

            // Auto-login after registration
            this.setToken(data.access_token);
            this.setUser(data.user);
            window.location.href = "/dashboard.html";

        } catch (error) {
            console.error("Registration error:", error);
            this.showError(error.message || "Registration failed", "register");
        } finally {
            this.showLoading(false, "register");
        }
        
        return false;
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

    getUser() {
        const user = localStorage.getItem(this.USER_KEY);
        return user ? JSON.parse(user) : null;
    },

    checkExistingAuth() {
        // If on login page but already authenticated, redirect
        const token = this.getToken();
        const currentPage = window.location.pathname;
        
        if (token && (currentPage === '/index.html' || currentPage === '/' || currentPage === '')) {
            console.log('Already authenticated, redirecting to dashboard');
            window.location.href = '/dashboard.html';
        }
    },

    showError(message, formType = "login") {
        const errorEl = document.getElementById(`${formType}-error`);
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = "block";
            errorEl.style.color = "#ef4444";
        } else {
            alert(message);
        }
    },

    clearError(formType) {
        const errorEl = document.getElementById(`${formType}-error`);
        if (errorEl) {
            errorEl.textContent = "";
            errorEl.style.display = "none";
        }
    },

    showLoading(show, formType) {
        const btn = document.getElementById(`${formType}-btn`);
        if (btn) {
            btn.disabled = show;
            btn.textContent = show ? 
                (formType === "login" ? "Logging in..." : "Creating Account...") : 
                (formType === "login" ? "Login" : "Create Account");
        }
    },
    
    // Expose methods for inline onclick handlers if needed
    showRegister() {
        document.getElementById("login-form")?.classList.add("hidden");
        document.getElementById("register-form")?.classList.remove("hidden");
    },
    
    showLogin() {
        document.getElementById("register-form")?.classList.add("hidden");
        document.getElementById("login-form")?.classList.remove("hidden");
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener("DOMContentLoaded", () => Auth.init());
} else {
    Auth.init();
}

// Expose globally for onclick handlers
window.auth = Auth;
