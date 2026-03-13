const Router = {
    routes: {
        '/dashboard': () => Dashboard.render(),
        '/signals': () => Signals.render(),
        '/courses': () => Courses.render(),
        '/blog': () => Blog.render(),
        '/webinars': () => Webinars.render(),
        '/ai-mentor': () => AIMentor.render(),
        '/chart-analysis': () => ChartAnalysis.render(),
        '/performance': () => Performance.render(),
        '/admin': () => {
            if (!Store.getUser()?.is_admin) {
                window.location.hash = '#/dashboard';
                return;
            }
            Admin.render();
        }
    },
    
    init() {
        window.addEventListener('hashchange', () => this.route());
        this.route();
    },
    
    route() {
        const hash = window.location.hash.slice(1) || '/dashboard';
        const app = document.getElementById('app');
        
        if (!this.routes[hash]) {
            app.innerHTML = '<div class="error">Page not found</div>';
            return;
        }
        
        app.innerHTML = '<div class="loading">Loading...</div>';
        try {
            this.routes[hash]();
        } catch (e) {
            app.innerHTML = `<div class="error">Error: ${e.message}</div>`;
        }
    }
};
