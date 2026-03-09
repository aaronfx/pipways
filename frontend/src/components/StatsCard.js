
import { Component } from './Component.js';

export class StatsCard extends Component {
    render() {
        const { title, value, icon, color = 'primary', trend = null } = this.props;

        return this.createElement(`
            <div class="stat-card">
                <div class="stat-icon" style="background: var(--${color}-light); color: var(--${color});">
                    <i class="fas ${icon}"></i>
                </div>
                <div class="stat-content">
                    <h3 class="stat-value">${value}</h3>
                    <p class="stat-title">${title}</p>
                    ${trend ? `<span class="stat-trend ${trend >= 0 ? 'up' : 'down'}">${trend >= 0 ? '+' : ''}${trend}%</span>` : ''}
                </div>
            </div>
        `);
    }
}
