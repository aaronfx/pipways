import { Component } from '../components/Component.js';
import { Sidebar } from '../components/Sidebar.js';
import { api } from '../api/client.js';
import { showLoading } from '../utils/helpers.js';

export class WebinarsPage extends Component {
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
            
            <div id="webinars-list" class="webinars-grid">
                <p class="text-secondary">Loading webinars...</p>
            </div>
        `;
        
        container.appendChild(main);
        this.element = container;
        
        setTimeout(() => this.loadWebinars(), 0);
        
        return container;
    }

    async loadWebinars() {
        const container = this.element?.querySelector('#webinars-list');
        if (!container) return;
        
        try {
            showLoading(true, 'Loading webinars...');
            const data = await api.getWebinars();
            
            if (data?.webinars?.length > 0) {
                container.innerHTML = data.webinars.map(webinar => `
                    <div class="webinar-card card">
                        <div class="webinar-header">
                            <h3>${webinar.title}</h3>
                            <span class="badge badge-success">Live</span>
                        </div>
                        <p>${webinar.description || ''}</p>
                        <div class="webinar-meta">
                            <span><i class="fas fa-calendar"></i> ${new Date(webinar.scheduled_at).toLocaleString()}</span>
                            <span><i class="fas fa-clock"></i> ${webinar.duration_minutes} min</span>
                        </div>
                        <button class="btn btn-primary btn-sm">Join Webinar</button>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<p class="text-secondary">No upcoming webinars.</p>';
            }
        } catch (error) {
            console.error('Failed to load webinars:', error);
            if (container) {
                container.innerHTML = '<p class="text-danger">Failed to load webinars.</p>';
            }
        } finally {
            showLoading(false);
        }
    }
}
