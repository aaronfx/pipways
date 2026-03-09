import { Component } from '../components/Component.js';
import { Sidebar } from '../components/Sidebar.js';
import { api } from '../api/client.js';
import { showLoading } from '../utils/helpers.js';

export class WebinarsPage extends Component {
    constructor() {
        super();
        this.webinars = [];
    }

    async render() {
        const container = document.createElement('div');
        container.className = 'main-app';

        const sidebar = new Sidebar();
        container.appendChild(sidebar.render());

        const main = document.createElement('main');
        main.className = 'main-content';
        main.innerHTML = `
            <div class="page-header">
                <h2><i class="fas fa-video" style="color: var(--premium);"></i> Live Webinars</h2>
                <p>Join our expert trading sessions</p>
            </div>

            <div id="webinars-grid" class="blog-grid">
                <div class="loading">Loading webinars...</div>
            </div>
        `;

        container.appendChild(main);
        this.element = container;  // Set element for later use

        // Load webinars after render
        setTimeout(() => this.loadWebinars(), 0);

        return container;
    }

    async loadWebinars() {
        const grid = this.element?.querySelector('#webinars-grid');
        if (!grid) return;

        try {
            showLoading(true, 'Loading webinars...');
            const data = await api.getWebinars();
            this.webinars = data.webinars || [];

            if (this.webinars.length === 0) {
                grid.innerHTML = '<p class="text-secondary">No upcoming webinars scheduled.</p>';
                return;
            }

            grid.innerHTML = this.webinars.map(webinar => `
                <article class="blog-card card">
                    <div class="blog-content">
                        <div class="blog-meta">
                            <span class="badge badge-success">Upcoming</span>
                            ${webinar.is_premium ? '<span class="badge badge-premium">Premium</span>' : ''}
                        </div>
                        <h3 class="blog-title">${webinar.title}</h3>
                        <p class="blog-excerpt">${webinar.description || 'No description available.'}</p>
                        <div class="blog-footer">
                            <span><i class="fas fa-calendar"></i> ${new Date(webinar.scheduled_at).toLocaleString()}</span>
                            <span><i class="fas fa-clock"></i> ${webinar.duration_minutes} min</span>
                        </div>
                        <div style="margin-top: 12px;">
                            <span class="text-secondary">${webinar.registration_count || 0} registered</span>
                        </div>
                    </div>
                </article>
            `).join('');
        } catch (error) {
            console.error('Failed to load webinars:', error);
            // Don't show error if we got redirected to login (session expired)
            if (!error.message.includes('Session expired')) {
                if (grid) {
                    grid.innerHTML = '<p class="text-danger">Failed to load webinars. Please try again.</p>';
                }
            }
        } finally {
            showLoading(false);
        }
    }
}
