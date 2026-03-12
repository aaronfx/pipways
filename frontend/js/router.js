const Router = {
    routes: {
        '/': 'home',
        '/signals': 'signals',
        '/courses': 'courses',
        '/blog': 'blog',
        '/blog/:slug': 'blogPost',
        '/webinars': 'webinars',
        '/dashboard': 'dashboard',
        '/admin': 'admin',
        '/login': 'login',
        '/risk-calculator': 'riskCalculator'
    },

    currentPage: null,

    init() {
        window.addEventListener('hashchange', () => this.handleRoute());
        window.addEventListener('load', () => this.handleRoute());
    },

    handleRoute() {
        const hash = window.location.hash.slice(1) || '/';
        const app = document.getElementById('app');

        const [path, queryString] = hash.split('?');

        let route = this.routes[path];
        let slug = null;

        if (!route) {
            const parts = path.split('/');
            if (parts[1] === 'blog' && parts[2]) {
                route = 'blogPost';
                slug = parts[2];
            } else {
                route = 'notFound';
            }
        }

        UI.setActiveNav(path);

        if (route === 'dashboard' && !Auth.requireAuth()) return;
        if (route === 'admin' && !Auth.requireAdmin()) return;

        Store.setState('currentPage', route);
        this.currentPage = route;

        switch(route) {
            case 'home':
                this.renderHome(app);
                break;
            case 'signals':
                SignalsPage.render(app);
                break;
            case 'courses':
                CoursesPage.render(app);
                break;
            case 'blog':
                BlogPage.render(app);
                break;
            case 'blogPost':
                BlogPage.renderPost(app, slug);
                break;
            case 'webinars':
                WebinarsPage.render(app);
                break;
            case 'dashboard':
                DashboardPage.render(app);
                break;
            case 'admin':
                AdminPage.render(app);
                break;
            case 'riskCalculator':
                RiskCalculator.render(app);
                break;
            case 'login':
                Auth.requireAuth() ? window.location.hash = '#/dashboard' : this.renderLogin(app);
                break;
            default:
                this.renderNotFound(app);
        }
    },

    renderHome(container) {
        container.innerHTML = `
            <div class="hero">
                <h1>Professional Trading Signals & Education</h1>
                <p>Join thousands of successful traders using our AI-powered signals and expert courses.</p>
                <button class="btn btn-primary btn-lg" onclick="window.location.hash='#/signals'">
                    View Signals
                </button>
            </div>
            <div class="features">
                <div class="feature-card">
                    <h3>📊 Live Signals</h3>
                    <p>Real-time trading signals with high accuracy rates</p>
                </div>
                <div class="feature-card">
                    <h3>📚 Expert Courses</h3>
                    <p>Learn from professional traders with proven strategies</p>
                </div>
                <div class="feature-card">
                    <h3>🎓 Live Webinars</h3>
                    <p>Weekly training sessions and market analysis</p>
                </div>
            </div>
        `;
    },

    renderLogin(container) {
        container.innerHTML = `
            <div class="auth-page">
                <h2>Login</h2>
                ${Auth.loginForm()}
                <p>Don't have an account? <a href="#/register">Register</a></p>
            </div>
        `;
    },

    renderNotFound(container) {
        container.innerHTML = `
            <div class="text-center" style="padding: 4rem 1rem;">
                <h1>404</h1>
                <p>Page not found</p>
                <a href="#/" class="btn btn-primary">Go Home</a>
            </div>
        `;
    }
};