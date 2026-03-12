const RiskCalculator = {
    async render(container) {
        container.innerHTML = `
            <div class="page-header">
                <h1>💰 Risk Management Calculator</h1>
                <p>Calculate optimal position size based on your account and risk tolerance</p>
            </div>

            <div class="risk-calculator">
                <div class="calculator-form">
                    <div class="form-group">
                        <label>Account Balance ($)</label>
                        <input type="number" id="accountBalance" value="10000" min="100">
                    </div>

                    <div class="form-group">
                        <label>Risk Per Trade (%)</label>
                        <input type="number" id="riskPercent" value="1" min="0.1" max="5" step="0.1">
                        <small>Recommended: 1-2% max</small>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>Entry Price</label>
                            <input type="number" id="entryPrice" step="0.00001" required>
                        </div>
                        <div class="form-group">
                            <label>Stop Loss</label>
                            <input type="number" id="stopLoss" step="0.00001" required>
                        </div>
                        <div class="form-group">
                            <label>Take Profit</label>
                            <input type="number" id="takeProfit" step="0.00001" required>
                        </div>
                    </div>

                    <button onclick="RiskCalculator.calculate()" class="btn btn-primary btn-lg">
                        Calculate Position Size
                    </button>
                </div>

                <div id="calculationResult" class="calculation-result" style="display:none"></div>

                ${Store.isAuthenticated() ? `
                <div class="history-section" style="margin-top: 2rem;">
                    <h3>Recent Calculations</h3>
                    <div id="calcHistory"></div>
                </div>
                ` : ''}
            </div>
        `;

        if (Store.isAuthenticated()) {
            this.loadHistory();
        }
    },

    async calculate() {
        const data = {
            account_balance: parseFloat(document.getElementById('accountBalance').value),
            risk_percent: parseFloat(document.getElementById('riskPercent').value),
            entry_price: parseFloat(document.getElementById('entryPrice').value),
            stop_loss: parseFloat(document.getElementById('stopLoss').value),
            take_profit: parseFloat(document.getElementById('takeProfit').value)
        };

        if (data.risk_percent > 2) {
            UI.showToast('Warning: Risking more than 2% per trade is dangerous', 'warning');
        }

        try {
            const result = await API.calculateRisk(data);
            this.displayResults(result);
        } catch (error) {
            UI.showToast('Calculation failed: ' + error.message, 'error');
        }
    },

    displayResults(result) {
        const container = document.getElementById('calculationResult');
        const isValid = result.recommendation === 'valid';

        container.innerHTML = `
            <div style="background: ${isValid ? '#dcfce7' : '#fef3c7'}; padding: 2rem; border-radius: 0.5rem;">
                <h3>Position Size Results</h3>
                <div class="result-grid">
                    <div class="result-item">
                        <span class="label">Position Size</span>
                        <span class="value highlight">${result.position_size} lots</span>
                    </div>
                    <div class="result-item">
                        <span class="label">Units</span>
                        <span class="value">${result.units.toLocaleString()}</span>
                    </div>
                    <div class="result-item">
                        <span class="label">Max Loss</span>
                        <span class="value risk">$${result.max_loss}</span>
                    </div>
                    <div class="result-item">
                        <span class="label">Risk:Reward</span>
                        <span class="value ${result.risk_reward_ratio >= 2 ? 'good' : 'bad'}">
                            1:${result.risk_reward_ratio}
                        </span>
                    </div>
                </div>

                ${result.recommendation !== 'valid' ? `
                <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.5); border-radius: 0.375rem;">
                    <strong>⚠️ ${result.recommendation.replace('_', ' ').toUpperCase()}</strong>
                    <p>${this.getRecommendationText(result.recommendation)}</p>
                </div>
                ` : ''}
            </div>
        `;
        container.style.display = 'block';
    },

    getRecommendationText(rec) {
        const texts = {
            'poor_risk_reward': 'Risk/Reward ratio should be at least 1:1.5',
            'high_risk': 'Consider reducing risk per trade to 1-2%',
            'below_minimum_lot': 'Position size below broker minimum (0.01 lots)'
        };
        return texts[rec] || 'Review your parameters';
    },

    async loadHistory() {
        try {
            const history = await API.getRiskHistory();
            const container = document.getElementById('calcHistory');
            if (history.length === 0) {
                container.innerHTML = '<p>No calculations yet</p>';
                return;
            }

            container.innerHTML = history.map(h => `
                <div style="padding: 0.75rem; border-bottom: 1px solid #e5e7eb;">
                    <span>${new Date(h.calculated_at).toLocaleDateString()}</span>
                    <span style="margin-left: 1rem;">${h.position_size} lots @ ${h.risk_percent}% risk</span>
                    <span style="margin-left: 1rem;">R:R ${h.risk_reward_ratio}</span>
                </div>
            `).join('');
        } catch (e) {
            console.error('Failed to load history');
        }
    }
};