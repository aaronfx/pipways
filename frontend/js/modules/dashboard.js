const Dashboard = {
    async render() {
        const app = document.getElementById('app');
        const user = Store.getUser();
        
        app.innerHTML = `
            <div class="container">
                <h1>Welcome, ${user?.full_name || user?.email || 'Trader'}</h1>
                
                <div class="grid-3">
                    <div class="card">
                        <h3>Trading Signals</h3>
                        <p>View active trading signals</p>
                        <a href="#/signals" class="btn btn-primary">View Signals</a>
                    </div>
                    <div class="card">
                        <h3>AI Mentor</h3>
                        <p>Get trading advice</p>
                        <a href="#/ai-mentor" class="btn btn-primary">Ask AI</a>
                    </div>
                    <div class="card">
                        <h3>Chart Analysis</h3>
                        <p>Analyze chart patterns</p>
                        <a href="#/chart-analysis" class="btn btn-primary">Analyze</a>
                    </div>
                </div>
                
                <div style="margin-top: 2rem;">
                    <h2>Quick Stats</h2>
                    <div id="stats">Loading...</div>
                </div>
            </div>
        `;
        
        this.loadStats();
    },
    
    async loadStats() {
        // Load real data here
        document.getElementById('stats').innerHTML = `
            <div class="grid-3">
                <div class="stat-card">
                    <div class="stat-value">0</div>
                    <div class="stat-label">Active Signals</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">0</div>
                    <div class="stat-label">Courses</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">Ready</div>
                    <div class="stat-label">AI Status</div>
                </div>
            </div>
        `;
    }
};
