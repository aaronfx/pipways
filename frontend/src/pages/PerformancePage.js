
import { Component } from '../components/Component.js';
import { Sidebar } from '../components/Sidebar.js';
import { api } from '../api/client.js';
import { showLoading } from '../utils/helpers.js';

export class PerformancePage extends Component {
    constructor() {
        super();
        this.trades = [];
    }

    render() {
        const container = document.createElement('div');
        container.className = 'main-app';

        const sidebar = new Sidebar();
        container.appendChild(sidebar.render());

        const main = document.createElement('main');
        main.className = 'main-content';
        main.innerHTML = `
            <div class="page-header">
                <h2><i class="fas fa-chart-pie" style="color: var(--secondary);"></i> Performance Analyzer</h2>
                <p>AI-powered analysis of your trading performance</p>
            </div>

            <div class="performance-container">
                <div class="trade-entry card">
                    <h3>Add Trade</h3>
                    <form id="trade-form">
                        <div class="form-grid">
                            <div class="form-group">
                                <label class="form-label">Pair</label>
                                <input type="text" name="pair" class="form-input" placeholder="EURUSD" required>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Direction</label>
                                <select name="direction" class="form-input">
                                    <option value="BUY">Buy</option>
                                    <option value="SELL">Sell</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Result (pips)</label>
                                <input type="number" name="pips" class="form-input" step="0.1" required>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Risk %</label>
                                <input type="number" name="risk" class="form-input" step="0.1" placeholder="1.0">
                            </div>
                        </div>
                        <button type="submit" class="btn btn-secondary">
                            <i class="fas fa-plus"></i> Add Trade
                        </button>
                    </form>

                    <div id="trades-list" class="trades-list">
                        ${this.renderTradesList()}
                    </div>
                </div>

                <div class="analysis-section card">
                    <h3>Account Info</h3>
                    <div class="form-group">
                        <label class="form-label">Current Balance</label>
                        <input type="number" id="account-balance" class="form-input" placeholder="10000">
                    </div>

                    <button class="btn btn-primary btn-block" id="analyze-btn" ${this.trades.length === 0 ? 'disabled' : ''}>
                        <i class="fas fa-brain"></i> Analyze Performance
                    </button>

                    <div id="analysis-result" class="analysis-output hidden"></div>
                </div>
            </div>
        `;

        container.appendChild(main);
        return container;
    }

    renderTradesList() {
        if (this.trades.length === 0) {
            return '<p class="text-secondary">No trades added yet. Add your first trade above.</p>';
        }

        return `
            <table class="trades-table">
                <thead>
                    <tr>
                        <th>Pair</th>
                        <th>Dir</th>
                        <th>Pips</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.trades.map((trade, idx) => `
                        <tr class="${trade.pips >= 0 ? 'win' : 'loss'}">
                            <td>${trade.pair}</td>
                            <td>${trade.direction}</td>
                            <td class="${trade.pips >= 0 ? 'positive' : 'negative'}">${trade.pips > 0 ? '+' : ''}${trade.pips}</td>
                            <td>
                                <button class="btn btn-sm btn-danger" onclick="removeTrade(${idx})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            <div class="trades-summary">
                <span>Total: ${this.trades.length} trades</span>
                <span>Wins: ${this.trades.filter(t => t.pips > 0).length}</span>
                <span>Win Rate: ${this.trades.length ? Math.round((this.trades.filter(t => t.pips > 0).length / this.trades.length) * 100) : 0}%</span>
            </div>
        `;
    }

    bindEvents() {
        const form = this.element.querySelector('#trade-form');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(form);

            this.trades.push({
                pair: formData.get('pair').toUpperCase(),
                direction: formData.get('direction'),
                pips: parseFloat(formData.get('pips')),
                risk_percent: parseFloat(formData.get('risk')) || 1
            });

            this.updateTradesList();
            form.reset();
        });

        const analyzeBtn = this.element.querySelector('#analyze-btn');
        analyzeBtn.addEventListener('click', () => this.analyzePerformance());

        window.removeTrade = (idx) => {
            this.trades.splice(idx, 1);
            this.updateTradesList();
        };
    }

    updateTradesList() {
        const list = this.element.querySelector('#trades-list');
        list.innerHTML = this.renderTradesList();

        const analyzeBtn = this.element.querySelector('#analyze-btn');
        analyzeBtn.disabled = this.trades.length === 0;
    }

    async analyzePerformance() {
        if (this.trades.length === 0) return;

        const balance = parseFloat(document.getElementById('account-balance').value) || null;

        showLoading(true, 'AI analyzing your performance...');

        try {
            const result = await api.analyzePerformance({
                trades: this.trades,
                account_balance: balance,
                trading_period_days: 30
            });

            this.displayAnalysis(result.analysis);
        } catch (error) {
            console.error(error);
        } finally {
            showLoading(false);
        }
    }

    displayAnalysis(analysis) {
        const resultDiv = this.element.querySelector('#analysis-result');

        let html = '<div class="analysis-report">';

        if (analysis.structured === false) {
            html += `<div class="analysis-section"><p>${analysis.raw_analysis}</p></div>`;
        } else {
            html += `
                <div class="analysis-section">
                    <h4><i class="fas fa-chart-line"></i> Summary</h4>
                    <p>${analysis.summary}</p>
                </div>

                <div class="analysis-grid">
                    <div class="analysis-card">
                        <h5>Strengths</h5>
                        <ul>${(analysis.strengths || []).map(s => `<li>${s}</li>`).join('')}</ul>
                    </div>
                    <div class="analysis-card">
                        <h5>Areas to Improve</h5>
                        <ul>${(analysis.weaknesses || []).map(w => `<li>${w}</li>`).join('')}</ul>
                    </div>
                </div>

                <div class="analysis-section">
                    <h4><i class="fas fa-lightbulb"></i> Recommendations</h4>
                    <ol>${(analysis.recommendations || []).map(r => `<li>${r}</li>`).join('')}</ol>
                </div>

                <div class="analysis-metrics">
                    <div class="metric">
                        <span class="metric-label">Risk Assessment</span>
                        <span class="metric-value">${analysis.risk_assessment || 'N/A'}/10</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Psychology</span>
                        <span class="metric-value">${analysis.psychology_feedback || 'N/A'}</span>
                    </div>
                </div>
            `;
        }

        html += '</div>';
        resultDiv.innerHTML = html;
        resultDiv.classList.remove('hidden');
        resultDiv.scrollIntoView({ behavior: 'smooth' });
    }
}
