const PerformancePage = {
    async render(container) {
        container.innerHTML = `
            <div class="page-header">
                <h1>📈 Performance Analytics</h1>
                <p>Deep insights into your trading performance</p>
            </div>
            
            <div class="performance-dashboard">
                <div class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                    <div class="stat-card" style="background: white; padding: 1.5rem; border-radius: 0.5rem; text-align: center;">
                        <h3>Win Rate</h3>
                        <p class="stat-value" id="winRate" style="font-size: 2rem; color: #3b82f6;">--</p>
                    </div>
                    <div class="stat-card" style="background: white; padding: 1.5rem; border-radius: 0.5rem; text-align: center;">
                        <h3>Profit Factor</h3>
                        <p class="stat-value" id="profitFactor" style="font-size: 2rem; color: #10b981;">--</p>
                    </div>
                    <div class="stat-card" style="background: white; padding: 1.5rem; border-radius: 0.5rem; text-align: center;">
                        <h3>Expectancy</h3>
                        <p class="stat-value" id="expectancy" style="font-size: 2rem; color: #f59e0b;">--</p>
                    </div>
                    <div class="stat-card" style="background: white; padding: 1.5rem; border-radius: 0.5rem; text-align: center;">
                        <h3>Grade</h3>
                        <p class="stat-value" id="grade" style="font-size: 2rem; color: #8b5cf6;">--</p>
                    </div>
                </div>
                
                <div class="analysis-section" style="background: white; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 2rem;">
                    <h3>Upload Trade Journal</h3>
                    <p style="color: #64748b; margin-bottom: 1rem;">Export your trades from your broker and upload for AI analysis</p>
                    <textarea id="tradeJournal" placeholder="Paste trade data here (JSON format)" 
                              style="width: 100%; height: 150px; padding: 0.75rem; border: 1px solid #e2e8f0; border-radius: 0.375rem; margin-bottom: 1rem;"></textarea>
                    <button onclick="PerformancePage.analyzeTrades()" class="btn btn-primary">Analyze Performance</button>
                </div>
                
                <div id="analysisResults" style="display: none;">
                    <!-- Results populated here -->
                </div>
            </div>
        `;
        
        this.loadQuickStats();
    },

    async loadQuickStats() {
        try {
            const stats = await API.getPerformanceStats(30);
            document.getElementById('winRate').textContent = stats.summary.win_rate + '%';
            document.getElementById('profitFactor').textContent = '1.8'; // Demo
            document.getElementById('expectancy').textContent = '$125'; // Demo
            document.getElementById('grade').textContent = 'B+'; // Demo
        } catch (e) {
            console.error('Failed to load stats');
        }
    },

    async analyzeTrades() {
        const textarea = document.getElementById('tradeJournal');
        const data = textarea.value.trim();
        
        if (!data) {
            UI.showToast('Please paste trade data first', 'warning');
            return;
        }
        
        try {
            const trades = JSON.parse(data);
            const results = await API.analyzeJournal(trades);
            this.displayAnalysis(results);
        } catch (e) {
            UI.showToast('Invalid data format. Please use JSON.', 'error');
        }
    },

    displayAnalysis(results) {
        const container = document.getElementById('analysisResults');
        container.style.display = 'block';
        
        container.innerHTML = `
            <div class="analysis-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 2rem;">
                <div class="left-column">
                    <div class="card" style="background: white; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                        <h3>Overall Grade: ${results.overall_grade}</h3>
                        <div class="score-bar" style="background: #e2e8f0; height: 1.5rem; border-radius: 0.75rem; overflow: hidden; margin: 1rem 0;">
                            <div style="background: ${results.overall_score > 70 ? '#10b981' : results.overall_score > 50 ? '#f59e0b' : '#ef4444'}; 
                                        width: ${results.overall_score}%; height: 100%; transition: width 0.5s;">
                            </div>
                        </div>
                        <p>Score: ${results.overall_score}/100</p>
                        <p style="color: #64748b; margin-top: 0.5rem;">${results.next_milestone}</p>
                    </div>
                    
                    <div class="card" style="background: white; padding: 1.5rem; border-radius: 0.5rem;">
                        <h3>Psychology Insights</h3>
                        <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                            <li>Best state: ${results.psychology.best_trading_state}</li>
                            <li>Worst state: ${results.psychology.worst_trading_state}</li>
                            <li>Emotional consistency: ${results.psychology.emotional_consistency}</li>
                        </ul>
                        ${results.psychology.revenge_trading_detected ? 
                            '<div class="alert" style="background: #fee2e2; color: #991b1b; padding: 0.75rem; border-radius: 0.375rem; margin-top: 1rem;">⚠️ Revenge trading detected in your history</div>' : ''}
                    </div>
                </div>
                
                <div class="right-column">
                    <div class="card" style="background: white; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                        <h3>Improvements Needed</h3>
                        <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                            ${results.improvements.map(i => `<li style="margin-bottom: 0.5rem;">${i}</li>`).join('')}
                        </ul>
                    </div>
                    
                    <div class="card" style="background: white; padding: 1.5rem; border-radius: 0.5rem;">
                        <h3>Best Trading Hours</h3>
                        <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                            ${results.patterns.best_trading_hours.map(h => `<li>${h}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }
};
