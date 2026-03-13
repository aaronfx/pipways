const PerformancePage = {
    async render(container) {
        container.innerHTML = `
            <div class="page-header" style="margin-bottom: 2rem;">
                <h1>📈 Performance Analytics</h1>
                <p style="color: #64748b;">Deep insights into your trading performance and psychology</p>
            </div>
            
            <div class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h3 style="color: #64748b; font-size: 0.875rem; margin-bottom: 0.5rem;">Win Rate</h3>
                    <p id="winRate" style="font-size: 2rem; color: #3b82f6; font-weight: 600; margin: 0;">--</p>
                </div>
                <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h3 style="color: #64748b; font-size: 0.875rem; margin-bottom: 0.5rem;">Profit Factor</h3>
                    <p id="profitFactor" style="font-size: 2rem; color: #10b981; font-weight: 600; margin: 0;">--</p>
                </div>
                <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h3 style="color: #64748b; font-size: 0.875rem; margin-bottom: 0.5rem;">Expectancy</h3>
                    <p id="expectancy" style="font-size: 2rem; color: #f59e0b; font-weight: 600; margin: 0;">--</p>
                </div>
                <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h3 style="color: #64748b; font-size: 0.875rem; margin-bottom: 0.5rem;">Grade</h3>
                    <p id="grade" style="font-size: 2rem; color: #8b5cf6; font-weight: 600; margin: 0;">--</p>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 2rem;">
                <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h3 style="margin-bottom: 1rem;">Upload Trade Journal</h3>
                    <p style="color: #64748b; margin-bottom: 1rem; font-size: 0.875rem;">Paste your trade data in JSON format for AI analysis</p>
                    <textarea id="tradeJournal" placeholder='[
  {
    "entry_date": "2024-01-01T10:00:00",
    "symbol": "EURUSD",
    "direction": "BUY",
    "entry_price": 1.0850,
    "exit_price": 1.0900,
    "stop_loss": 1.0800,
    "take_profit": 1.0950,
    "pnl": 50.00,
    "outcome": "win",
    "emotion_before": "confident"
  }
]' style="width: 100%; height: 150px; padding: 0.75rem; border: 1px solid #e2e8f0; border-radius: 0.375rem; font-family: monospace; font-size: 0.75rem; margin-bottom: 1rem;"></textarea>
                    <button onclick="PerformancePage.analyzeTrades()" style="width: 100%; background: #3b82f6; color: white; padding: 0.75rem; border: none; border-radius: 0.375rem; cursor: pointer;">Analyze Performance</button>
                </div>
                
                <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h3 style="margin-bottom: 1rem;">Quick Stats (30 Days)</h3>
                    <div id="quickStats">
                        <div style="text-align: center; padding: 2rem; color: #94a3b8;">
                            <p>Click "Analyze Performance" to see detailed statistics</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="analysisResults" style="display: none;">
                <!-- Detailed analysis populated here -->
            </div>
        `;
        
        this.loadQuickStats();
    },

    async loadQuickStats() {
        try {
            const stats = await API.getPerformanceStats(30);
            document.getElementById('winRate').textContent = stats.summary.win_rate + '%';
            document.getElementById('profitFactor').textContent = '1.8';
            document.getElementById('expectancy').textContent = '$125';
            document.getElementById('grade').textContent = 'B+';
            
            document.getElementById('quickStats').innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div style="background: #f0fdf4; padding: 1rem; border-radius: 0.375rem;">
                        <small style="color: #166534;">Total Trades</small>
                        <p style="font-size: 1.25rem; font-weight: 600; color: #166534; margin: 0;">${stats.summary.trades_taken}</p>
                    </div>
                    <div style="background: #eff6ff; padding: 1rem; border-radius: 0.375rem;">
                        <small style="color: #1e40af;">Net P&L</small>
                        <p style="font-size: 1.25rem; font-weight: 600; color: #1e40af; margin: 0;">$${stats.summary.net_pnl}</p>
                    </div>
                    <div style="background: #f0f9ff; padding: 1rem; border-radius: 0.375rem;">
                        <small style="color: #0369a1;">Best Trade</small>
                        <p style="font-size: 1.25rem; font-weight: 600; color: #0369a1; margin: 0;">+$${stats.summary.best_trade}</p>
                    </div>
                    <div style="background: #fef2f2; padding: 1rem; border-radius: 0.375rem;">
                        <small style="color: #991b1b;">Worst Trade</small>
                        <p style="font-size: 1.25rem; font-weight: 600; color: #991b1b; margin: 0;">-$${Math.abs(stats.summary.worst_trade)}</p>
                    </div>
                </div>
            `;
        } catch (e) {
            console.error('Failed to load stats');
        }
    },

    async analyzeTrades() {
        const textarea = document.getElementById('tradeJournal');
        const data = textarea.value.trim();
        
        if (!data) {
            if (typeof UI !== 'undefined') UI.showToast('Please paste trade data first', 'warning');
            else alert('Please paste trade data first');
            return;
        }
        
        try {
            const trades = JSON.parse(data);
            const results = await API.analyzeJournal(trades);
            this.displayAnalysis(results);
        } catch (e) {
            if (typeof UI !== 'undefined') UI.showToast('Invalid data format. Please use JSON.', 'error');
            else alert('Invalid JSON format');
        }
    },

    displayAnalysis(results) {
        const container = document.getElementById('analysisResults');
        container.style.display = 'block';
        
        const stats = results.statistics;
        const psych = results.psychology;
        
        container.innerHTML = `
            <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                    <h2 style="margin: 0;">Overall Grade: ${results.overall_grade}</h2>
                    <span style="font-size: 1.5rem; color: #64748b;">${results.overall_score}/100</span>
                </div>
                <div style="background: #f3f4f6; height: 1.5rem; border-radius: 0.75rem; overflow: hidden; margin-bottom: 1rem;">
                    <div style="background: ${results.overall_score > 70 ? '#10b981' : results.overall_score > 50 ? '#f59e0b' : '#ef4444'}; 
                                width: ${results.overall_score}%; height: 100%; transition: width 0.5s;">
                    </div>
                </div>
                <p style="color: #64748b; margin: 0;">${results.next_milestone}</p>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 1.5rem;">
                <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h3 style="margin-bottom: 1rem; color: #374151;">Trading Statistics</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; font-size: 0.875rem;">
                        <div>
                            <span style="color: #64748b;">Total Trades:</span>
                            <strong style="display: block; font-size: 1.125rem; color: #111827;">${stats.total_trades}</strong>
                        </div>
                        <div>
                            <span style="color: #64748b;">Win Rate:</span>
                            <strong style="display: block; font-size: 1.125rem; color: #111827;">${stats.win_rate}%</strong>
                        </div>
                        <div>
                            <span style="color: #64748b;">Profit Factor:</span>
                            <strong style="display: block; font-size: 1.125rem; color: #111827;">${stats.profit_factor}</strong>
                        </div>
                        <div>
                            <span style="color: #64748b;">Expectancy:</span>
                            <strong style="display: block; font-size: 1.125rem; color: #111827;">$${stats.expectancy}</strong>
                        </div>
                        <div>
                            <span style="color: #64748b;">Avg Win:</span>
                            <strong style="display: block; font-size: 1.125rem; color: #059669;">$${stats.average_win}</strong>
                        </div>
                        <div>
                            <span style="color: #64748b;">Avg Loss:</span>
                            <strong style="display: block; font-size: 1.125rem; color: #dc2626;">$${stats.average_loss}</strong>
                        </div>
                    </div>
                </div>
                
                <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h3 style="margin-bottom: 1rem; color: #374151;">Psychology Profile</h3>
                    <ul style="list-style: none; padding: 0; margin: 0; font-size: 0.875rem;">
                        <li style="margin-bottom: 0.75rem; padding-bottom: 0.75rem; border-bottom: 1px solid #f3f4f6;">
                            <span style="color: #64748b;">Best Trading State:</span>
                            <strong style="display: block; color: #059669; text-transform: capitalize;">${psych.best_trading_state}</strong>
                        </li>
                        <li style="margin-bottom: 0.75rem; padding-bottom: 0.75rem; border-bottom: 1px solid #f3f4f6;">
                            <span style="color: #64748b;">Emotional Consistency:</span>
                            <strong style="display: block; color: ${psych.emotional_consistency === 'high' ? '#059669' : '#d97706'}; text-transform: capitalize;">
                                ${psych.emotional_consistency}
                            </strong>
                        </li>
                        <li style="margin-bottom: 0.75rem; padding-bottom: 0.75rem; border-bottom: 1px solid #f3f4f6;">
                            <span style="color: #64748b;">FOMO Trades:</span>
                            <strong style="display: block; color: ${psych.fomo_trades > 0 ? '#dc2626' : '#059669'};">
                                ${psych.fomo_trades} detected
                            </strong>
                        </li>
                        ${psych.revenge_trading_detected ? `
                        <li style="background: #fee2e2; color: #991b1b; padding: 0.75rem; border-radius: 0.375rem; margin-top: 0.5rem;">
                            ⚠️ Revenge trading detected in your history
                        </li>
                        ` : ''}
                    </ul>
                </div>
            </div>
            
            <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <h3 style="margin-bottom: 1rem; color: #374151;">Actionable Improvements</h3>
                <ul style="padding-left: 1.5rem; margin: 0;">
                    ${results.improvements.map(i => `
                        <li style="margin-bottom: 0.75rem; color: #4b5563; line-height: 1.5;">
                            ${i}
                        </li>
                    `).join('')}
                </ul>
            </div>
            
            <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <h3 style="margin-bottom: 1rem; color: #374151;">Pattern Analysis</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div>
                        <h4 style="font-size: 0.875rem; color: #64748b; margin-bottom: 0.5rem;">Best Trading Hours</h4>
                        <ul style="list-style: none; padding: 0; font-size: 0.875rem;">
                            ${results.patterns.best_trading_hours.map(h => `
                                <li style="padding: 0.25rem 0; color: #374151;">${h}</li>
                            `).join('')}
                        </ul>
                    </div>
                    <div>
                        <h4 style="font-size: 0.875rem; color: #64748b; margin-bottom: 0.5rem;">Streak Analysis</h4>
                        <div style="font-size: 0.875rem;">
                            <div style="margin-bottom: 0.5rem;">
                                <span style="color: #059669;">Max Wins:</span>
                                <strong>${results.patterns.consecutive_analysis.max_consecutive_wins}</strong>
                            </div>
                            <div>
                                <span style="color: #dc2626;">Max Losses:</span>
                                <strong>${results.patterns.consecutive_analysis.max_consecutive_losses}</strong>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Update the header stats
        document.getElementById('winRate').textContent = stats.win_rate + '%';
        document.getElementById('profitFactor').textContent = stats.profit_factor;
        document.getElementById('expectancy').textContent = '$' + stats.expectancy;
        document.getElementById('grade').textContent = results.overall_grade.split(' ')[0];
    }
};
