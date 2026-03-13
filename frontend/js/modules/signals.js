const Signals = {
    async render() {
        document.getElementById('app').innerHTML = `
            <div class="container">
                <h1>Trading Signals</h1>
                <div id="signals-list" class="signals-grid">Loading...</div>
            </div>
        `;
        
        try {
            const signals = await API.getSignals();
            const container = document.getElementById('signals-list');
            
            if (!signals?.length) {
                container.innerHTML = '<p>No active signals</p>';
                return;
            }
            
            container.innerHTML = signals.map(s => `
                <div class="signal-card ${s.direction?.toLowerCase()}">
                    <h3>${s.symbol}</h3>
                    <div class="signal-meta">
                        <span class="badge ${s.direction}">${s.direction}</span>
                        <span>${s.timeframe || 'N/A'}</span>
                    </div>
                    <div class="signal-prices">
                        <div>Entry: <strong>${s.entry_price}</strong></div>
                        <div>SL: <span class="text-red">${s.stop_loss}</span></div>
                        <div>TP: <span class="text-green">${s.take_profit}</span></div>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            document.getElementById('signals-list').innerHTML = 
                `<div class="error">Failed to load: ${e.message}</div>`;
        }
    }
};
