
import { Component } from './Component.js';
import { store } from '../state.js';
import { router } from '../router.js';

export class Sidebar extends Component {
    render() {
        const { user } = store.getState();
        const isAdmin = store.isAdmin();

        return this.createElement(`
            <aside class="sidebar">
                <div class="sidebar-header">
                    <div class="sidebar-logo">
                        <i class="fas fa-chart-line"></i>
                        <span>Pipways Pro</span>
                    </div>
                </div>

                <nav class="sidebar-nav">
                    ${this.renderNavItem('/', 'fa-home', 'Dashboard')}
                    ${this.renderNavItem('/signals', 'fa-satellite-dish', 'Signals')}
                    ${this.renderNavItem('/analysis', 'fa-robot', 'AI Analysis')}
                    ${this.renderNavItem('/performance', 'fa-chart-pie', 'Performance')}
                    ${this.renderNavItem('/mentor', 'fa-comments', 'AI Mentor')}
                    ${this.renderNavItem('/blog', 'fa-newspaper', 'Blog')}
                    ${isAdmin ? this.renderNavItem('/admin', 'fa-cog', 'Admin', true) : ''}
                </nav>

                <div class="sidebar-footer">
                    <div class="user-card">
                        <div class="user-avatar">${(user?.full_name || user?.email || 'U').charAt(0).toUpperCase()}</div>
                        <div class="user-info">
                            <div class="user-name">${user?.full_name || user?.email}</div>
                            <div class="user-tier ${user?.subscription_tier || 'free'}">${user?.subscription_tier || 'Free'}</div>
                        </div>
                    </div>
                    <button class="btn btn-outline btn-sm" id="logout-btn">
                        <i class="fas fa-sign-out-alt"></i> Logout
                    </button>
                </div>
            </aside>
        `);
    }

    renderNavItem(href, icon, text, isAdmin = false) {
        const currentPath = window.location.pathname;
        const active = currentPath === href ? 'active' : '';
        return `
            <a href="${href}" data-link class="nav-link ${active} ${isAdmin ? 'admin-link' : ''}">
                <i class="fas ${icon}"></i>
                <span>${text}</span>
                ${isAdmin ? '<span class="badge badge-warning">A</span>' : ''}
            </a>
        `;
    }

    bindEvents() {
        const logoutBtn = this.element.querySelector('#logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                store.logout();
                router.navigate('/login');
            });
        }
    }
}
