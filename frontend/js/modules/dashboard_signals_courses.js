// Dashboard Module: Signals & Courses
// Extracted from dashboard.js for maintainability

DashboardController.prototype.loadSignals = async function() {
    if (typeof PublicPages !== 'undefined') {
        await PublicPages.signals('signals-container', this);
        return;
    }
    const container = document.getElementById('signals-container');
    if (!container) return;
    container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500"><i class="fas fa-spinner fa-spin mr-2"></i>Loading signals…</div>';
    try {
        const data = await this.apiRequest('/api/signals/active');
        const signals = Array.isArray(data) ? data : (data.signals || []);
        if (!signals.length) {
            container.innerHTML = `<div class="col-span-full pw-empty">
                <div class="pw-empty-icon"><i class="fas fa-satellite-dish text-xl" style="color:#6b7280;"></i></div>
                <p class="pw-empty-title">No active signals right now</p>
                <p class="pw-empty-sub">New signals are posted regularly by our analysts. Check back soon.</p>
            </div>`;
            return;
        }
        container.innerHTML = signals.map(s => `
            <div class="bg-gray-800 rounded-xl p-5 border border-gray-700 hover:border-purple-600/50 transition-colors">
                <div class="flex justify-between items-start mb-3">
                    <h4 class="font-bold text-white text-lg">${s.symbol || '—'}</h4>
                    <span class="px-2.5 py-1 rounded-full text-xs font-bold ${s.direction === 'BUY' ? 'bg-green-900/60 text-green-300 border border-green-700' : 'bg-red-900/60 text-red-300 border border-red-700'}">${s.direction || '—'}</span>
                </div>
                <div class="text-sm text-gray-400 space-y-1.5">
                    <div class="flex justify-between"><span>Entry</span><span class="text-white font-mono">${s.entry_price ?? '—'}</span></div>
                    <div class="flex justify-between"><span>Stop Loss</span><span class="text-red-400 font-mono">${s.stop_loss ?? '—'}</span></div>
                    <div class="flex justify-between"><span>Take Profit</span><span class="text-green-400 font-mono">${s.take_profit ?? '—'}</span></div>
                    <div class="flex justify-between"><span>Timeframe</span><span class="text-gray-300">${s.timeframe || '—'}</span></div>
                </div>
                <div class="flex justify-between items-center mt-3 pt-3 border-t border-gray-700">
                    <small class="text-gray-600">${s.created_at ? new Date(s.created_at).toLocaleDateString() : ''}</small>
                    ${s.ai_confidence ? `<span class="text-xs text-purple-400 font-semibold">AI ${Math.round(s.ai_confidence * 100)}%</span>` : ''}
                </div>
            </div>
        `).join('');
    } catch (error) {
        container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">Failed to load signals. Please try again.</div>';
    }
};

DashboardController.prototype.loadCourses = async function() {
    window.location.href = '/academy';
    return;
};

