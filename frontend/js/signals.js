/**
 * Signals Module
 */
const signals = {
    async loadSignals(container) {
        container.innerHTML = '<div class="loading">Loading signals...</div>';

        try {
            const data = await api.get('/signals?limit=50');
            const stats = await api.get('/signals/stats').catch(() => ({}));

            let html = `
                <div class="page-header">
                    <h1>Trading Signals</h1>
                    ${auth.requireAdmin() ? '<button class="primary" onclick="signals.showCreateModal()">Create Signal</button>' : ''}
                </div>

                <div class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                    <div class="card" style="text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold; color: var(--primary);">${stats.total || 0}</div>
                        <div>Total Signals</div>
                    </div>
                    <div class="card" style="text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold; color: var(--success);">${stats.active || 0}</div>
                        <div>Active</div>
                    </div>
                    <div class="card" style="text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold; color: var(--warning);">${stats.wins || 0}</div>
                        <div>Wins</div>
                    </div>
                    <div class="card" style="text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold; color: var(--danger);">${stats.losses || 0}</div>
                        <div>Losses</div>
                    </div>
                </div>

                <div class="signals-list">
                    ${data.length === 0 ? '<p>No signals available.</p>' : 
                      data.map(s => this.renderSignalCard(s)).join('')}
                </div>
            `;

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="error">Failed to load signals: ${error.message}</div>`;
        }
    },

    renderSignalCard(signal) {
        const directionColor = signal.direction === 'buy' ? 'var(--success)' : 'var(--danger)';
        const isPremium = signal.is_premium ? '<span class="badge badge-premium">VIP</span>' : '';

        return `
            <div class="card signal-card">
                <div class="card-header">
                    <div>
                        <strong style="color: ${directionColor}; font-size: 1.2rem;">${signal.pair}</strong>
                        ${isPremium}
                        <span class="badge badge-${signal.status === 'active' ? 'success' : 'secondary'}">${signal.status}</span>
                    </div>
                    <small>${ui.formatDate(signal.created_at)}</small>
                </div>
                <div class="signal-details">
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1rem 0;">
                        <div>
                            <small>Direction</small>
                            <div style="color: ${directionColor}; font-weight: bold; text-transform: uppercase;">${signal.direction}</div>
                        </div>
                        <div>
                            <small>Entry</small>
                            <div style="font-weight: bold;">${signal.entry_price}</div>
                        </div>
                        <div>
                            <small>Timeframe</small>
                            <div>${signal.timeframe || 'N/A'}</div>
                        </div>
                    </div>
                    ${signal.stop_loss ? `<div>Stop Loss: <strong>${signal.stop_loss}</strong></div>` : ''}
                    ${signal.tp1 ? `<div>TP1: <strong>${signal.tp1}</strong></div>` : ''}
                    ${signal.tp2 ? `<div>TP2: <strong>${signal.tp2}</strong></div>` : ''}
                    ${signal.analysis ? `<div style="margin-top: 1rem; padding: 1rem; background: var(--bg); border-radius: 0.25rem;">${signal.analysis}</div>` : ''}
                    ${signal.result ? `<div style="margin-top: 0.5rem;">Result: <span class="badge badge-${signal.result === 'WIN' ? 'success' : signal.result === 'LOSS' ? 'danger' : 'warning'}">${signal.result}</span></div>` : ''}
                </div>
                ${auth.requireAdmin() ? `
                    <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
                        <button onclick="signals.showResultModal(${signal.id})">Set Result</button>
                        <button class="secondary" onclick="signals.deleteSignal(${signal.id})">Delete</button>
                    </div>
                ` : ''}
            </div>
        `;
    },

    showCreateModal() {
        // Implementation for creating signals
        ui.showToast('Create signal form would appear here');
    },

    showResultModal(signalId) {
        // Implementation for setting result
        ui.showToast('Set result form would appear here');
    },

    async deleteSignal(signalId) {
        if (!confirm('Delete this signal?')) return;
        try {
            await api.delete(`/signals/${signalId}`);
            ui.showToast('Signal deleted', 'success');
            this.loadSignals(document.getElementById('main-content'));
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    }
};
