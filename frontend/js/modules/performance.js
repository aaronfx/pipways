const PerformancePage = {
    async render() {
        const app = document.getElementById('app');
        
        app.innerHTML = `
            <div class="page-header">
                <h1>📈 Performance Analytics</h1>
                <p>Analyze your trading performance and psychology</p>
            </div>
            
            <div class="stats-grid" style="margin-bottom: 2rem;">
                <div class="stat-card">
                    <h3>Win Rate</h3>
                    <div class="stat-value text-primary" id="winRate">--</div>
                </div>
                <div class="stat-card">
                    <h3>Profit Factor</h3>
                    <div class="stat-value text-success" id="profitFactor">--</div>
                </div>
                <div class="stat-card">
                    <h3>Expectancy</h3>
                    <div class="stat-value text-warning" id="expectancy">--</div>
                </div>
                <div class="stat-card">
                    <h3>Grade</h3>
                    <div class="stat-value text-info" id="grade">--</div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Upload Trade Journal</h3>
                    </div>
                    <div class="card-body">
                        <p style="color: var(--gray-600); margin-bottom: 0.5rem;">Upload MT4/MT5 export or paste trade data (JSON/CSV)</p>
                        <div style="margin-bottom: 0.75rem; display: flex; gap: 0.5rem; align-items: center;">
                            <input type="file" id="journalFile" accept=".csv,.html,.htm,.pdf,.xlsx"
                                style="font-size: 0.8rem; color: var(--gray-600);"
                                onchange="PerformancePage.handleFileUpload(event)">
                            <span style="font-size: 0.75rem; color: var(--gray-400);">or paste below ↓</span>
                        </div>
                        <textarea id="tradeJournal" rows="6" class="form-control" style="font-family: monospace; font-size: 0.75rem;" placeholder='[
  {
    "entry_date": "2024-01-01T10:00:00",
    "symbol": "EURUSD",
    "direction": "BUY",
    "entry_price": 1.0850,
    "exit_price": 1.0900,
    "stop_loss": 1.0800,
    "take_profit": 1.0950,
    "pnl": 50.00,
    "outcome": "win"
  }
]'></textarea>
                        <button onclick="PerformancePage.analyze()" class="btn btn-primary btn-block mt-3">
                            Analyze Performance
                        </button>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Quick Stats (30 Days)</h3>
                    </div>
                    <div class="card-body" id="quickStats">
                        <p class="text-muted">Click "Analyze Performance" to see detailed statistics</p>
                    </div>
                </div>
            </div>
            
            <div id="analysisResults" style="display: none; margin-top: 2rem;"></div>
        `;
        
        this.loadQuickStats();
    },
    
    async loadQuickStats() {
        // Load cached performance from localStorage first
        try {
            const cached = localStorage.getItem('pipways_performance');
            if (cached) {
                const data = JSON.parse(cached);
                const stats = data.statistics || {};
                const el_wr = document.getElementById('winRate');
                const el_pf = document.getElementById('profitFactor');
                const el_gr = document.getElementById('grade');
                if (el_wr) el_wr.textContent = (stats.win_rate || '--') + (stats.win_rate ? '%' : '');
                if (el_pf) el_pf.textContent = stats.profit_factor || '--';
                if (el_gr) el_gr.textContent = data.overall_grade || '--';
                console.log('[Performance] Loaded cached results');
                return;
            }
        } catch(_) {}
        try {
            const stats = await (typeof API.getPerformanceStats === 'function'
                ? API.getPerformanceStats(30)
                : API.request('/ai/performance/summary'));
            document.getElementById('winRate').textContent = stats.summary?.win_rate + '%' || '--';
            document.getElementById('profitFactor').textContent = '1.8';
            document.getElementById('expectancy').textContent = '$125';
            document.getElementById('grade').textContent = 'B+';
            
            document.getElementById('quickStats').innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div class="bg-success text-success" style="padding: 1rem; border-radius: var(--radius);">
                        <small>Total Trades</small>
                        <p style="font-size: 1.25rem; font-weight: 600; margin: 0;">${stats.summary?.trades_taken || 0}</p>
                    </div>
                    <div class="bg-primary" style="padding: 1rem; border-radius: var(--radius); color: white;">
                        <small>Net P&L</small>
                        <p style="font-size: 1.25rem; font-weight: 600; margin: 0;">$${stats.summary?.net_pnl || 0}</p>
                    </div>
                </div>
            `;
        } catch (e) {
            console.error('Stats load error:', e);
        }
    },
    
    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        const ext = file.name.split('.').pop().toLowerCase();

        if (ext === 'csv') {
            const text = await file.text();
            // Put CSV text in textarea for backend to parse
            const textarea = document.getElementById('tradeJournal');
            if (textarea) textarea.value = text;
            UI.showToast('CSV loaded — click Analyze to process', 'info');
        } else {
            // For binary formats (xlsx, pdf, html), send directly to the multi-format endpoint
            const formData = new FormData();
            formData.append('file', file);
            try {
                UI.showToast('Parsing file...', 'info');
                const result = await API.request('/ai/performance/upload-journal', {
                    method: 'POST',
                    headers: {},
                    body: formData
                });
                this.displayAnalysis(result);
            } catch (e) {
                UI.showToast('File parse failed: ' + e.message, 'error');
            }
        }
    },

    async analyze() {
        const textarea = document.getElementById('tradeJournal');
        const data = textarea.value.trim();
        
        if (!data) {
            UI.showToast('Please paste trade data first', 'warning');
            return;
        }
        
        try {
            const trades = JSON.parse(data);
            let results;
            if (typeof API.analyzeJournal === 'function') {
                results = await API.analyzeJournal(trades);
            } else {
                results = await API.request('/ai/performance/analyze-journal', {
                    method: 'POST',
                    body: JSON.stringify({ trades })
                });
            }
            this.displayAnalysis(results);
        } catch (e) {
            // 402 limit reached — show upgrade modal
            if (e.message && (e.message.includes('limit_reached') || e.message.includes('402'))) {
                // Show inline upgrade UI
                const container = document.getElementById('analysisResults');
                if (container) {
                    container.style.display = 'block';
                    container.innerHTML = `
                        <div style="text-align:center;padding:3rem;background:#111827;
                                    border-radius:12px;border:1px solid #374151;margin-top:1rem;">
                            <div style="font-size:2.5rem;margin-bottom:1rem;">🔒</div>
                            <p style="color:white;font-weight:700;font-size:1.1rem;margin-bottom:.5rem;">Free limit reached</p>
                            <p style="color:#9ca3af;font-size:.875rem;margin-bottom:1.5rem;">
                                You've used your free performance analysis.<br>Upgrade to Pro for unlimited access.
                            </p>
                            <div style="display:flex;gap:.75rem;justify-content:center;flex-wrap:wrap;">
                                <button onclick="window.PaymentsPage ? PaymentsPage.startPayment('pro_monthly') : window.location.href='/pricing.html'"
                                    style="padding:10px 24px;background:#7c3aed;color:white;border:none;
                                           border-radius:8px;font-weight:700;font-size:.9rem;cursor:pointer;">
                                    Upgrade to Pro →
                                </button>
                                <a href="/pricing.html"
                                    style="padding:10px 24px;background:#1f2937;color:#9ca3af;border:1px solid #374151;
                                           border-radius:8px;font-weight:600;font-size:.9rem;text-decoration:none;
                                           display:inline-flex;align-items:center;">
                                    See Plans
                                </a>
                            </div>
                        </div>`;
                }
                // Also trigger modal
                setTimeout(() => {
                    if (window.PipwaysUsage && PipwaysUsage.showUpgradeModal) {
                        PipwaysUsage.showUpgradeModal('performance',
                            PipwaysUsage.used('performance'),
                            PipwaysUsage.limit('performance'));
                    } else if (window.PaymentsPage) {
                        PaymentsPage.showUpgradeModal('Performance Analytics');
                    }
                }, 300);
                return;
            }
            // Parse JSON error messages cleanly
            let msg;
            try { msg = JSON.parse(e.message).detail || JSON.parse(e.message).error || e.message; }
            catch (_) { msg = e.message || 'Analysis failed'; }
            if (typeof UI !== 'undefined') UI.showToast('Error: ' + msg, 'error');
            else alert('Error: ' + msg);
        }
    },
    
    displayAnalysis(results) {
        // ── Save to localStorage so AI Mentor can access results ──
        try {
            const stats = results.statistics || {};
            const aiCoach = results.ai_coach || {};
            localStorage.setItem('pipways_performance', JSON.stringify({
                cached_at:      Date.now(),
                overall_grade:  results.overall_grade,
                overall_score:  results.overall_score,
                statistics:     stats,
                ai_coach:       aiCoach,
                improvements:   results.improvements || [],
                next_milestone: results.next_milestone || '',
                trades_count:   stats.total_trades || 0
            }));
            console.log('[Performance] Results cached for AI Mentor access');
        } catch(e) { console.warn('[Performance] Cache save failed:', e); }

        const container = document.getElementById('analysisResults');
        container.style.display = 'block';
        
        const stats = results.statistics;
        const psych = results.psychology;
        
        container.innerHTML = `
            <div class="card" style="margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h2 style="margin: 0;">Overall Grade: ${results.overall_grade}</h2>
                    <span style="font-size: 1.5rem; color: var(--gray-500);">${results.overall_score}/100</span>
                </div>
                <div class="progress" style="margin-bottom: 1rem;">
                    <div class="progress-bar" style="width: ${results.overall_score}%; background: ${results.overall_score > 70 ? 'var(--success)' : results.overall_score > 50 ? 'var(--warning)' : 'var(--danger)'};"></div>
                </div>
                <p class="text-muted">${results.next_milestone}</p>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 1.5rem;">
                <div class="card">
                    <h3 style="margin-bottom: 1rem;">Trading Statistics</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; font-size: 0.875rem;">
                        <div><span class="text-muted">Total Trades:</span><br><strong>${stats.total_trades}</strong></div>
                        <div><span class="text-muted">Win Rate:</span><br><strong>${stats.win_rate}%</strong></div>
                        <div><span class="text-muted">Profit Factor:</span><br><strong>${stats.profit_factor}</strong></div>
                        <div><span class="text-muted">Expectancy:</span><br><strong>$${stats.expectancy}</strong></div>
                    </div>
                </div>
                
                <div class="card">
                    <h3 style="margin-bottom: 1rem;">Psychology Profile</h3>
                    <ul style="list-style: none; padding: 0; font-size: 0.875rem;">
                        <li style="margin-bottom: 0.75rem;"><span class="text-muted">Best State:</span> <strong class="text-success">${psych.best_trading_state}</strong></li>
                        <li style="margin-bottom: 0.75rem;"><span class="text-muted">Consistency:</span> <strong>${psych.emotional_consistency}</strong></li>
                        ${psych.revenge_trading_detected ? '<li class="bg-danger text-danger" style="padding: 0.75rem; border-radius: var(--radius);">⚠️ Revenge trading detected</li>' : ''}
                    </ul>
                </div>
            </div>
            
            <div class="card">
                <h3 style="margin-bottom: 1rem;">Actionable Improvements</h3>
                <ul style="padding-left: 1.5rem;">
                    ${results.improvements?.map(i => `<li style="margin-bottom: 0.75rem;">${i}</li>`).join('') || '<li>Keep up the good work!</li>'}
                </ul>
            </div>
        `;
        
        // Update header stats
        document.getElementById('winRate').textContent = stats.win_rate + '%';
        document.getElementById('profitFactor').textContent = stats.profit_factor;
        document.getElementById('expectancy').textContent = '$' + stats.expectancy;
        document.getElementById('grade').textContent = results.overall_grade.split(' ')[0];
    }
};
