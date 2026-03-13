/**
 * Router
 */
const Router = {
    routes: {
        '/dashboard': () => DashboardPage.render(),
        '/signals': () => SignalsPage.render(),
        '/courses': () => CoursesPage.render(),
        '/blog': () => BlogPage.render(),
        '/webinars': () => WebinarsPage.render(),
        '/ai-mentor': () => AIMentorPage.render(),
        '/chart-analysis': () => ChartAnalysisPage.render(),
        '/performance': () => PerformancePage.render(),
        '/admin': () => {
            if (!Store.getUser()?.is_admin) {
                window.location.hash = '#/dashboard';
                UI.showToast('Admin access required', 'error');
                return;
            }
            AdminPage.render();
        }
    },

    init() {
        window.addEventListener('hashchange', () => this.handleRoute());
        
        // Handle initial route
        const hash = window.location.hash;
        if (hash && this.routes[hash.slice(1)]) {
            this.handleRoute();
        } else {
            window.location.hash = '#/dashboard';
        }
    },

    handleRoute() {
        const hash = window.location.hash.slice(1) || '/dashboard';
        const app = document.getElementById('app');
        
        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${hash}`) {
                link.classList.add('active');
            }
        });
        
        // Show loading
        app.innerHTML = '<div class="loading" style="text-align: center; padding: 4rem;">Loading...</div>';
        
        // Route handler
        const handler = this.routes[hash];
        if (handler) {
            try {
                handler();
            } catch (e) {
                console.error('Route error:', e);
                app.innerHTML = `<div class="error" style="padding: 2rem;">Error loading page: ${e.message}</div>`;
            }
        } else {
            app.innerHTML = '<div class="error" style="padding: 2rem;">Page not found</div>';
        }
    },

    navigate(path) {
        window.location.hash = `#${path}`;
    }
};
