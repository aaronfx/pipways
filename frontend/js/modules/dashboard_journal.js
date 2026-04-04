// Dashboard Module: Journal
// Extracted from dashboard.js for maintainability

DashboardController.prototype.setJournalFormat = function(format) {
    this.currentJournalFormat = format;
    document.querySelectorAll('.format-btn').forEach(btn => {
        btn.classList.remove('border-purple-500', 'bg-purple-600');
        btn.classList.add('border-gray-600', 'bg-gray-700');
    });
    const activeBtn = document.querySelector(`[data-format="${format}"]`);
    if (activeBtn) {
        activeBtn.classList.remove('border-gray-600', 'bg-gray-700');
        activeBtn.classList.add('border-purple-500', 'bg-purple-600');
    }
    const configs = {
        mt4: { accept: '.html,.htm', label: 'MT4 Statement selected' },
        mt5: { accept: '.html,.htm', label: 'MT5 Statement selected' },
        csv: { accept: '.csv', label: 'CSV File selected' },
        excel: { accept: '.xlsx,.xls', label: 'Excel File selected' },
        screenshot: { accept: '.png,.jpg,.jpeg', label: 'Screenshot for OCR selected' }
    };
    const config = configs[format];
    if (config) {
        document.getElementById('journal-file-input').accept = config.accept;
        document.getElementById('selected-format').textContent = config.label;
    }
};

DashboardController.prototype.setupJournalUpload = function() {
    const dropZone = document.getElementById('journal-dropzone');
    const fileInput = document.getElementById('journal-file-input');
    if (!dropZone || !fileInput) return;

    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-purple-500', 'bg-purple-900/20');
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('border-purple-500', 'bg-purple-900/20');
    });
    dropZone.addEventListener('drop', async (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-purple-500', 'bg-purple-900/20');
        if (e.dataTransfer.files[0]) await this.handleJournalFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', async (e) => {
        if (e.target.files[0]) await this.handleJournalFile(e.target.files[0]);
    });
};

DashboardController.prototype.handleJournalFile = async function(file) {
    const statusEl = document.getElementById('upload-status');
    const loadingEl = document.getElementById('journal-upload-loading');

    if (!this.currentJournalFormat) {
        statusEl.classList.remove('hidden');
        statusEl.innerHTML = '<span class="text-yellow-400">Please select a format first</span>';
        return;
    }

    statusEl.classList.remove('hidden');
    statusEl.innerHTML = '<span class="text-blue-400"><i class="fas fa-spinner fa-spin mr-2"></i>Uploading...</span>';
    loadingEl.classList.remove('hidden');

    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('format', this.currentJournalFormat);

        const token = localStorage.getItem('pipways_token');
        const response = await fetch(`${API_BASE}/ai/performance/upload-journal`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        const result = await response.json();

        if (!response.ok) throw new Error(result.detail || 'Upload failed');

        if (result.trades && result.trades.length > 0) {
            this.lastAnalysisResults = result;
            try {
                const perfCache = {
                    cached_at: Date.now(),
                    overall_grade: result.overall_grade,
                    overall_score: result.overall_score,
                    statistics: result.statistics,
                    ai_coach: result.ai_coach,
                    improvements: result.improvements,
                    next_milestone: result.next_milestone,
                    trades_count: result.trades_parsed
                };
                localStorage.setItem('pipways_performance', JSON.stringify(perfCache));
                this._cachedPerformance = perfCache;
            } catch(_) {}
            this.displayJournalAnalysis(result);
            statusEl.innerHTML = `<span class="text-green-400"><i class="fas fa-check mr-2"></i>Analyzed ${result.trades_parsed} trades</span>`;
            this._toast(`Trade data imported successfully — ${result.trades_parsed} trades analysed`, 'success', 4000);
        } else {
            throw new Error('No trades detected');
        }
    } catch (error) {
        statusEl.innerHTML = `<span class="text-red-400">Error: ${error.message}</span>`;
    } finally {
        loadingEl.classList.add('hidden');
    }
};

DashboardController.prototype.displayJournalAnalysis = function(result) {
    document.getElementById('performance-overview').classList.remove('hidden');
    document.getElementById('analytics-charts').classList.remove('hidden');
    document.getElementById('ai-coach-section').classList.remove('hidden');
    document.getElementById('trade-history').classList.remove('hidden');
    document.getElementById('strategy-detection').classList.remove('hidden');

    this._updateDashPerfCard(result);

    const stats = result.statistics || {};

    document.getElementById('stat-total-trades').textContent = stats.total_trades || 0;
    document.getElementById('stat-win-rate').textContent = (stats.win_rate || 0) + '%';
    document.getElementById('stat-profit-factor').textContent = stats.profit_factor || 0;
    document.getElementById('stat-expectancy').textContent = '$' + (stats.expectancy || 0);
    document.getElementById('stat-max-drawdown').textContent = '$' + (stats.max_drawdown || 0);
    document.getElementById('stat-winning-streak').textContent = stats.winning_streak || 0;
    document.getElementById('stat-losing-streak').textContent = stats.losing_streak || 0;
    document.getElementById('stat-net-pnl').textContent = '$' + Math.abs(stats.net_pnl || 0).toFixed(2);
    document.getElementById('stat-net-pnl').className = 'text-2xl font-bold ' + ((stats.net_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400');

    document.getElementById('overall-grade-badge').textContent = result.overall_grade || 'N/A';
    document.getElementById('detected-strategy').textContent = result.detected_strategy || 'Unknown';
    document.getElementById('risk-consistency-score').textContent = (result.risk_consistency_score || 0) + '%';
    document.getElementById('risk-consistency-bar').style.width = (result.risk_consistency_score || 0) + '%';

    const aiCoach = result.ai_coach || {};
    document.getElementById('ai-discipline-score').textContent = aiCoach.discipline_score || '--';
    document.getElementById('ai-risk-score').textContent = aiCoach.risk_management_score || '--';
    document.getElementById('ai-consistency-score').textContent = aiCoach.strategy_consistency || '--';
    document.getElementById('ai-main-mistake').textContent = aiCoach.main_mistake || 'None detected';
    document.getElementById('ai-recommendation').textContent = aiCoach.recommendation || 'Keep maintaining your trading journal';

    const strengthsList = document.getElementById('ai-strengths');
    strengthsList.innerHTML = (aiCoach.strengths || ['Consistent trading']).map(s => `<li class="flex items-start gap-2"><i class="fas fa-check text-green-400 mt-1"></i> ${s}</li>`).join('');

    const improvementsList = document.getElementById('ai-improvements');
    improvementsList.innerHTML = (aiCoach.improvements || ['Continue current approach']).map(i => `<li class="flex items-start gap-2"><i class="fas fa-arrow-up text-yellow-400 mt-1"></i> ${i}</li>`).join('');

    this.renderEquityCurve(result.equity_curve || []);
    this.renderTradeDistribution(result.trade_distribution || {});
    this.renderMonthlyPerformance(result.monthly_performance || []);

    const tbody = document.getElementById('trades-table-body');
    tbody.innerHTML = (result.trades || []).slice(0, 20).map(trade => `
        <tr class="border-b border-gray-700 hover:bg-gray-800/50">
            <td class="px-4 py-3">${trade.entry_date || '--'}</td>
            <td class="px-4 py-3 font-medium">${trade.symbol || 'N/A'}</td>
            <td class="px-4 py-3"><span class="px-2 py-1 rounded text-xs font-bold ${trade.direction === 'BUY' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}">${trade.direction}</span></td>
            <td class="px-4 py-3 font-mono">${trade.entry_price || '--'}</td>
            <td class="px-4 py-3 font-mono">${trade.exit_price || '--'}</td>
            <td class="px-4 py-3 font-mono ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}">${trade.pnl >= 0 ? '+' : ''}${trade.pnl}</td>
        </tr>
    `).join('');
};

DashboardController.prototype._updateDashPerfCard = function(result) {
    const el = document.getElementById('dash-perf-body');
    if (!el || !result) return;
    const stats   = result.statistics || {};
    const aiCoach = result.ai_coach   || {};
    const winRate = stats.win_rate      || 0;
    const pf      = stats.profit_factor || 0;
    const trades  = stats.total_trades  || 0;
    const grade   = result.overall_grade || 'N/A';
    const netPnl  = stats.net_pnl || 0;
    const rr      = stats.avg_rr_ratio  || (pf > 0 ? (pf - 0.3).toFixed(1) : '—');
    const winColor  = winRate >= 55 ? '#34d399' : winRate >= 45 ? '#fbbf24' : '#f87171';
    const pfColor   = pf >= 1.5 ? '#34d399' : pf >= 1 ? '#fbbf24' : '#f87171';
    const gradeColors = { A:'#34d399', B:'#a78bfa', C:'#fbbf24', D:'#f87171', F:'#f87171' };
    const gradeColor = gradeColors[grade?.[0]] || '#9ca3af';
    const discipline = aiCoach.discipline_score || 0;

    el.innerHTML = `
    <div class="flex items-center justify-between mb-4 pb-3" style="border-bottom:1px solid #1f2937;">
        <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center font-black text-xl"
                 style="background:rgba(${grade?.[0]==='A'?'52,211,153':grade?.[0]==='B'?'167,139,250':'245,158,11'},.12);color:${gradeColor};">
                ${grade}
            </div>
            <div>
                <div class="text-xs text-gray-500">Overall Grade</div>
                <div class="text-xs text-gray-400 mt-0.5">${trades} trades</div>
            </div>
        </div>
        <div class="text-right">
            <div class="text-xs text-gray-500 mb-0.5">Net P&L</div>
            <div class="text-base font-bold ${netPnl >= 0 ? 'text-green-400' : 'text-red-400'}">
                ${netPnl >= 0 ? '+' : ''}$${Math.abs(netPnl).toFixed(0)}
            </div>
        </div>
    </div>
    <div class="grid grid-cols-2 gap-2 mb-4">
        <div class="rounded-lg p-2.5 text-center" style="background:#0d1321;border:1px solid #1f2937;">
            <div class="text-lg font-bold" style="color:${winColor};">${winRate}%</div>
            <div class="text-xs text-gray-600 mt-0.5">Win Rate</div>
        </div>
        <div class="rounded-lg p-2.5 text-center" style="background:#0d1321;border:1px solid #1f2937;">
            <div class="text-lg font-bold text-blue-400">1:${typeof rr==='number'?rr.toFixed(1):rr}</div>
            <div class="text-xs text-gray-600 mt-0.5">RR Ratio</div>
        </div>
        <div class="rounded-lg p-2.5 text-center" style="background:#0d1321;border:1px solid #1f2937;">
            <div class="text-lg font-bold text-white">${trades}</div>
            <div class="text-xs text-gray-600 mt-0.5">Trades</div>
        </div>
        <div class="rounded-lg p-2.5 text-center" style="background:#0d1321;border:1px solid #1f2937;">
            <div class="text-lg font-bold" style="color:${pfColor};">${pf}</div>
            <div class="text-xs text-gray-600 mt-0.5">Profit Factor</div>
        </div>
    </div>
    ${discipline > 0 ? `
    <div class="mb-3">
        <div class="flex justify-between text-xs mb-1">
            <span class="text-gray-500">AI Discipline Score</span>
            <span class="font-semibold text-purple-400">${discipline}%</span>
        </div>
        <div class="pw-progress-bar">
            <div class="pw-progress-fill" style="width:${discipline}%;"></div>
        </div>
    </div>` : ''}
    <div class="rounded-lg mb-3 flex items-center justify-center relative overflow-hidden"
         style="height:48px;background:#0d1321;border:1px solid #1f2937;">
        <svg viewBox="0 0 200 40" class="w-full h-full" preserveAspectRatio="none">
            <defs><linearGradient id="pcg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="${winColor}" stop-opacity=".35"/>
                <stop offset="100%" stop-color="${winColor}" stop-opacity="0"/>
            </linearGradient></defs>
            <polyline points="0,35 25,28 50,32 75,20 100,22 125,14 150,18 175,10 200,12"
                      fill="none" stroke="${winColor}" stroke-width="1.5" opacity=".8"/>
            <polygon points="0,35 25,28 50,32 75,20 100,22 125,14 150,18 175,10 200,12 200,40 0,40"
                     fill="url(#pcg)"/>
        </svg>
        <span class="absolute bottom-1 right-2 text-gray-700" style="font-size:.6rem;">EQUITY</span>
    </div>
    <button onclick="dashboard.navigate('journal')"
        class="w-full py-2 rounded-lg text-xs font-semibold transition-all"
        style="background:rgba(251,146,60,.15);border:1px solid rgba(251,146,60,.3);color:#fb923c;"
        onmouseover="this.style.background='rgba(251,146,60,.25)'" onmouseout="this.style.background='rgba(251,146,60,.15)'">
        <i class="fas fa-chart-bar mr-1.5"></i>Full Performance Analysis
    </button>`;
};

DashboardController.prototype.addManualTrade = function() {
    const trade = {
        entry_date: new Date().toISOString().split('T')[0],
        symbol: document.getElementById('manual-symbol').value.toUpperCase(),
        direction: document.getElementById('manual-direction').value,
        entry_price: parseFloat(document.getElementById('manual-entry').value),
        exit_price: parseFloat(document.getElementById('manual-exit').value) || 0,
        pnl: parseFloat(document.getElementById('manual-pnl').value),
        volume: parseFloat(document.getElementById('manual-volume').value) || 0.1
    };

    this.manualTrades.push(trade);

    this.apiRequest('/ai/performance/analyze-journal', {
        method: 'POST',
        body: JSON.stringify({ trades: this.manualTrades })
    }).then(result => {
        this.lastAnalysisResults = result;
        try {
            localStorage.setItem('pipways_performance', JSON.stringify({
                cached_at: Date.now(),
                overall_grade: result.overall_grade,
                overall_score: result.overall_score,
                statistics: result.statistics,
                ai_coach: result.ai_coach,
                improvements: result.improvements,
                next_milestone: result.next_milestone,
                trades_count: result.trades?.length || 0
            }));
        } catch(_) {}
        this.displayJournalAnalysis(result);
    }).catch(err => {
        alert('Analysis failed: ' + err.message);
    });
};

DashboardController.prototype.showManualEntry = function() {
    document.getElementById('manual-entry-form').classList.remove('hidden');
};

DashboardController.prototype.renderEquityCurve = function(equityData) {
    const ctx = document.getElementById('equity-curve-chart');
    if (!ctx) return;
    if (this.charts.equity) this.charts.equity.destroy();
    const labels = equityData.map(d => d.trade_number);
    const data = equityData.map(d => d.equity);
    this.charts.equity = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets: [{ label: 'Equity', data, borderColor: 'rgb(59, 130, 246)', backgroundColor: 'rgba(59, 130, 246, 0.1)', fill: true, tension: 0.4, pointRadius: 0, pointHoverRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { grid: { color: 'rgba(75, 85, 99, 0.3)' }, ticks: { color: '#9ca3af' } }, x: { display: false } } }
    });
};

DashboardController.prototype.renderTradeDistribution = function(distribution) {
    const ctx = document.getElementById('trade-distribution-chart');
    if (!ctx) return;
    if (this.charts.distribution) this.charts.distribution.destroy();
    this.charts.distribution = new Chart(ctx, {
        type: 'doughnut',
        data: { labels: ['Wins', 'Losses', 'Breakeven'], datasets: [{ data: [distribution.wins || 0, distribution.losses || 0, distribution.breakeven || 0], backgroundColor: ['#10b981', '#ef4444', '#f59e0b'], borderWidth: 0 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#9ca3af', padding: 20 } } } }
    });
};

DashboardController.prototype.renderMonthlyPerformance = function(monthlyData) {
    const ctx = document.getElementById('monthly-performance-chart');
    if (!ctx) return;
    if (this.charts.monthly) this.charts.monthly.destroy();
    const labels = monthlyData.map(d => d.month);
    const data = monthlyData.map(d => d.pnl);
    const colors = data.map(v => v >= 0 ? '#10b981' : '#ef4444');
    this.charts.monthly = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets: [{ label: 'P&L', data, backgroundColor: colors, borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { grid: { color: 'rgba(75, 85, 99, 0.3)' }, ticks: { color: '#9ca3af', callback: v => '$' + v } }, x: { ticks: { color: '#9ca3af' }, grid: { display: false } } } }
    });
};

DashboardController.prototype._loadCachedPerformance = function() {
    try {
        const raw = localStorage.getItem('pipways_performance');
        if (!raw) return;
        const data = JSON.parse(raw);
        // Keep in memory so mentor requests can attach it without re-reading localStorage
        this._cachedPerformance = data;
        const age = Math.round((Date.now() - data.cached_at) / 3600000);
        console.log(`[Dashboard] Loaded cached performance (${age}h old, grade=${data.overall_grade})`);
    } catch(e) {}
};

