/**
 * Dashboard Module
 */
const DashboardPage = {
    async render() {
        const app = document.getElementById('app');
        const user = Store.getUser();
        
        app.innerHTML = `
            <div class="page-header">
                <h1>Welcome back, ${user?.full_name || user?.email || 'Trader'}</h1>
                <p>Here's your trading overview for today</p>
            </div>
            
            <div class="stats-grid" style="margin-bottom: 2rem;">
                <div class="stat-card">
                    <h3>Active Signals</h3>
                    <div class="stat-value text-primary" id="activeSignals">--</div>
                </div>
                <div class="stat-card">
                    <h3>Courses in Progress</h3>
                    <div class="stat-value text-success" id="courseCount">--</div>
                </div>
                <div class="stat-card">
                    <h3>AI Mentor</h3>
                    <div class="stat-value text-info">Ready</div>
                </div>
                <div class="stat-card">
                    <h3>Account Type</h3>
                    <div class="stat-value text-warning">${user?.subscription_tier || 'Free'}</div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 2rem;">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Recent Trading Signals</h3>
                    </div>
                    <div class="card-body" id="recentSignals">
                        <p>Loading signals...</p>
                    </div>
                </div>
                
                <div>
                    <div class="card" style="margin-bottom: 1.5rem;">
                        <div class="card-header">
                            <h3 class="card-title">Quick Actions</h3>
                        </div>
                        <div class="card-body" style="display: flex; flex-direction: column; gap: 0.75rem;">
                            <a href="#/ai-mentor" class="btn btn-primary">
                                <span>💬</span> Ask AI Mentor
                            </a>
                            <a href="#/chart-analysis" class="btn btn-success">
                                <span>📊</span> Analyze Chart
                            </a>
                            <a href="#/signals" class="btn btn-info">
                                <span>📈</span> View All Signals
                            </a>
                            <a href="#/performance" class="btn btn-secondary">
                                <span>📊</span> Performance Stats
                            </a>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Daily Insight</h3>
                        </div>
                        <div class="card-body">
                            <p id="dailyWisdom" style="font-style: italic; color: var(--gray-600);">Loading...</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Load data
        this.loadData();
    },
    
    async loadData() {
        try {
            // Load signals
            const signals = await API.getSignals({ limit: 5 });
            document.getElementById('activeSignals').textContent = signals.length || 0;
            
            const recentDiv = document.getElementById('recentSignals');
            if (signals && signals.length > 0) {
                recentDiv.innerHTML = signals.map(s => `
                    <div style="padding: 1rem; border-bottom: 1px solid var(--gray-200);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong>${s.symbol}</strong>
                            <span class="badge badge-${s.direction === 'BUY' ? 'success' : 'danger'}">${s.direction}</span>
                        </div>
                        <div style="margin-top: 0.5rem; font-size: 0.875rem; color: var(--gray-600);">
                            Entry: ${s.entry_price} | SL: ${s.stop_loss} | TP: ${s.take_profit}
                        </div>
                    </div>
                `).join('');
            } else {
                recentDiv.innerHTML = '<p class="text-muted">No active signals</p>';
            }
            
            // Load course count
            try {
                const courses = await API.getCourses();
                document.getElementById('courseCount').textContent = courses?.length || 0;
            } catch (e) {
                document.getElementById('courseCount').textContent = '0';
            }
            
            // Load daily wisdom
            try {
                const wisdom = await API.getDailyWisdom();
                document.getElementById('dailyWisdom').textContent = `"${wisdom.quote}" — ${wisdom.author}`;
            } catch (e) {
                document.getElementById('dailyWisdom').textContent = '"Plan the trade, trade the plan."';
            }
        } catch (e) {
            console.error('Dashboard load error:', e);
        }
    }
};
