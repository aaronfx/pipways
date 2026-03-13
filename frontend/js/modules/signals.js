/**
 * Signals Module
 */
const SignalsPage = {
    signals: [],
    
    async render() {
        const app = document.getElementById('app');
        
        app.innerHTML = `
            <div class="page-header" style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1>Trading Signals</h1>
                    <p>Active trading signals and market analysis</p>
                </div>
                <button onclick="SignalsPage.refresh()" class="btn btn-primary">
                    <span>🔄</span> Refresh
                </button>
            </div>
            
            <div id="signalsGrid" class="signals-grid">Loading...</div>
        `;
        
        await this.loadSignals();
    },
    
    async loadSignals() {
        try {
            this.signals = await API.getSignals();
            const container = document.getElementById('signalsGrid');
            
            if (!this.signals || this.signals.length === 0) {
                container.innerHTML = `
                    <div class="card" style="grid-column: 1 / -1; text-align: center; padding: 3rem;">
                        <p class="text-muted">No active signals available</p>
                        <p>Check back later for new opportunities</p>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = this.signals.map(s => `
                <div class="signal-card ${s.direction?.toLowerCase()}">
                    <div class="signal-header">
                        <h3>${s.symbol}</h3>
                        <span class="badge badge-${s.direction === 'BUY' ? 'success' : 'danger'}">${s.direction}</span>
                    </div>
                    <div class="signal-body">
                        <div class="signal-row">
                            <span>Entry Price</span>
                            <strong>${s.entry_price}</strong>
                        </div>
                        <div class="signal-row">
                            <span>Stop Loss</span>
                            <span class="text-danger">${s.stop_loss}</span>
                        </div>
                        <div class="signal-row">
                            <span>Take Profit</span>
                            <span class="text-success">${s.take_profit}</span>
                        </div>
                        <div class="signal-row">
                            <span>Timeframe</span>
                            <span>${s.timeframe || 'N/A'}</span>
                        </div>
                    </div>
                    <div class="signal-footer">
                        <small class="text-muted">${new Date(s.created_at).toLocaleString()}</small>
                        ${s.ai_confidence ? `<span class="badge badge-info">AI: ${Math.round(s.ai_confidence * 100)}%</span>` : ''}
                    </div>
                </div>
            `).join('');
            
        } catch (e) {
            document.getElementById('signalsGrid').innerHTML = `
                <div class="error" style="grid-column: 1 / -1;">
                    Failed to load signals: ${e.message}
                </div>
            `;
        }
    },
    
    refresh() {
        this.render();
    }
};
