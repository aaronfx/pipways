
import { Component } from '../components/Component.js';
import { Sidebar } from '../components/Sidebar.js';
import { StatsCard } from '../components/StatsCard.js';
import { store } from '../state.js';

export class DashboardPage extends Component {
    render() {
        const container = document.createElement('div');
        container.className = 'main-app';

        const sidebar = new Sidebar();
        container.appendChild(sidebar.render());

        const main = document.createElement('main');
        main.className = 'main-content';
        main.innerHTML = `
            <div class="page-header">
                <h2><i class="fas fa-home"></i> Dashboard</h2>
                <p>Welcome back, ${store.getState().user?.full_name || 'Trader'}</p>
            </div>

            <div class="stats-grid">
                <div class="stat-card-placeholder">
                    <i class="fas fa-chart-line"></i>
                    <h3>Trading Signals</h3>
                    <p>Active signals will appear here</p>
                </div>
                <div class="stat-card-placeholder">
                    <i class="fas fa-graduation-cap"></i>
                    <h3>Courses</h3>
                    <p>Your learning progress</p>
                </div>
                <div class="stat-card-placeholder">
                    <i class="fas fa-video"></i>
                    <h3>Webinars</h3>
                    <p>Upcoming sessions</p>
                </div>
                <div class="stat-card-placeholder">
                    <i class="fas fa-robot"></i>
                    <h3>AI Analysis</h3>
                    <p>Performance insights</p>
                </div>
            </div>

            <div class="content-grid">
                <div class="content-card">
                    <h3>Recent Activity</h3>
                    <p class="text-secondary">Your recent trades and activity will appear here.</p>
                </div>
                <div class="content-card">
                    <h3>Market Overview</h3>
                    <p class="text-secondary">Market data and news will appear here.</p>
                </div>
            </div>
        `;

        container.appendChild(main);
        return container;
    }
}
