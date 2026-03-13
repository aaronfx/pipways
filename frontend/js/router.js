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

        // Parse path and query string
        const [path, queryString] = hash.split('?');
        const params = new URLSearchParams(queryString || '');

        let route = this.routes[path];
        let slug = null;

        // Handle dynamic routes like /blog/post-slug
        if (!route) {
            const parts = path.split('/');
            if (parts.length >= 3 && parts[1] === 'blog') {
                route = 'blogPost';
                slug = parts[2];
            } else {
                route = 'notFound';
            }
        }

        UI.setActiveNav(path);

        // Auth checks
        if (route === 'dashboard' && !Auth.requireAuth()) return;
        if (route === 'admin' && !Auth.requireAdmin()) return;

        Store.setState('currentPage', route);
        this.currentPage = route;

        // Route rendering
        try {
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
                    if (slug) BlogPage.renderPost(app, slug);
                    else this.renderNotFound(app);
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
                default:
                    this.renderNotFound(app);
            }
        } catch (error) {
            console.error('Route error:', error);
            app.innerHTML = `<div class="error">Failed to load page: ${error.message}</div>`;
        }
    },

    renderHome(container) {
        container.innerHTML = `
            <div class="hero">
                <h1>Professional Trading Signals & Education</h1>
                <p>Join thousands of successful traders using our AI-powered signals and expert courses.</p>
                <div class="hero-buttons">
                    <button class="btn btn-primary btn-lg" onclick="window.location.hash='#/signals'">
                        View Signals
                    </button>
                    <button class="btn btn-secondary btn-lg" onclick="window.location.hash='#/courses'">
                        Browse Courses
                    </button>
                </div>
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

    renderNotFound(container) {
        container.innerHTML = `
            <div class="text-center" style="padding: 4rem 1rem;">
                <h1>404</h1>
                <p>Page not found</p>
                <a href="#/" class="btn btn-primary">Go Home</a>
            </div>
        `;
    },

    go(path) {
        window.location.hash = path;
    }
};
