/**
 * AI Tools Module
 */
const ai = {
    loadAITools(container) {
        if (!auth.requireAuth()) return;

        container.innerHTML = `
            <div class="page-header">
                <h1>AI Trading Tools</h1>
            </div>
            <div class="grid">
                <div class="card">
                    <h3>💬 AI Trading Mentor</h3>
                    <p>Ask questions and get AI-powered trading advice.</p>
                    <button class="primary" onclick="ai.showChat()">Start Chat</button>
                </div>
                <div class="card">
                    <h3>📊 Performance Analysis</h3>
                    <p>Upload your trading history for AI analysis.</p>
                    <button class="primary" onclick="ai.showPerformanceForm()">Analyze Performance</button>
                </div>
                <div class="card">
                    <h3>📈 Chart Analysis</h3>
                    <p>Get AI analysis of price charts and patterns.</p>
                    <button class="primary" onclick="ai.showChartAnalysis()">Analyze Chart</button>
                </div>
            </div>

            <div id="ai-workspace" style="margin-top: 2rem;"></div>
        `;
    },

    showChat() {
        const workspace = document.getElementById('ai-workspace');
        workspace.innerHTML = `
            <div class="card">
                <h3>AI Trading Mentor</h3>
                <div id="chat-history" style="height: 300px; overflow-y: auto; border: 1px solid var(--border); padding: 1rem; margin: 1rem 0; border-radius: 0.375rem;"></div>
                <div style="display: flex; gap: 0.5rem;">
                    <input type="text" id="chat-input" placeholder="Ask a question..." style="flex: 1;" onkeypress="if(event.key==='Enter') ai.sendMessage()">
                    <button onclick="ai.sendMessage()">Send</button>
                </div>
            </div>
        `;
    },

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const history = document.getElementById('chat-history');
        const message = input.value.trim();
        if (!message) return;

        // Add user message
        history.innerHTML += `<div style="margin-bottom: 0.5rem;"><strong>You:</strong> ${message}</div>`;
        input.value = '';

        try {
            const response = await api.post('/api/ai/chat', { message, history: [] });
            history.innerHTML += `<div style="margin-bottom: 0.5rem;"><strong>AI:</strong> ${response.response || response.message}</div>`;
            history.scrollTop = history.scrollHeight;
        } catch (error) {
            ui.showToast('Failed to get response: ' + error.message, 'error');
        }
    },

    showPerformanceForm() {
        const workspace = document.getElementById('ai-workspace');
        workspace.innerHTML = `
            <div class="card">
                <h3>Performance Analysis</h3>
                <form onsubmit="ai.analyzePerformance(event)">
                    <textarea name="trades" rows="5" placeholder="Paste your trade history (JSON format)"></textarea>
                    <input type="number" name="balance" placeholder="Account Balance" step="0.01">
                    <button type="submit" class="primary">Analyze</button>
                </form>
                <div id="analysis-result" style="margin-top: 1rem;"></div>
            </div>
        `;
    },

    async analyzePerformance(e) {
        e.preventDefault();
        const form = e.target;
        const trades = JSON.parse(form.trades.value || '[]');
        const balance = parseFloat(form.balance.value) || 0;

        try {
            const result = await api.post('/api/performance/analyze', { trades, account_balance: balance });
            document.getElementById('analysis-result').innerHTML = `
                <div class="card" style="background: var(--bg);">
                    <h4>Analysis Results</h4>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                        <div>Win Rate: <strong>${result.win_rate}%</strong></div>
                        <div>Total Trades: <strong>${result.total_trades}</strong></div>
                        <div>Profit Factor: <strong>${result.profit_factor || 'N/A'}</strong></div>
                        <div>Trader Score: <strong>${result.trader_score}/100</strong></div>
                    </div>
                </div>
            `;
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    },

    showChartAnalysis() {
        ui.showToast('Chart analysis feature - upload an image to analyze');
    }
};
