
import { store } from '../state.js';

class Router {
    constructor() {
        this.routes = {};
        this.currentRoute = null;

        window.addEventListener('popstate', () => this.render());
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-link]') || e.target.closest('[data-link]')) {
                e.preventDefault();
                const link = e.target.matches('[data-link]') ? e.target : e.target.closest('[data-link]');
                this.navigate(link.getAttribute('href'));
            }
        });
    }

    register(path, component) {
        this.routes[path] = component;
    }

    navigate(path) {
        window.history.pushState(null, null, path);
        this.render();
    }

    async render() {
        const path = window.location.pathname;
        const route = this.routes[path] || this.routes['/'];

        // Auth check
        if (path !== '/login' && !store.isAuthenticated()) {
            this.navigate('/login');
            return;
        }

        if (path === '/login' && store.isAuthenticated()) {
            this.navigate('/');
            return;
        }

        const app = document.getElementById('app');
        if (app) {
            app.innerHTML = '';
            const page = new route();
            const element = await page.render();
            if (element) {
                app.appendChild(element);
            }
        }

        this.currentRoute = path;
    }
}

export const router = new Router();
