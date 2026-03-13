// Main Application Logic - UI Interaction Layer Fixed

const API_BASE = window.location.origin;

const API = {
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('pipways_token');
        const headers = {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        };
        
        if (options.body instanceof FormData) {
            delete headers['Content-Type'];
        }
        
        const res = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });
        
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Error ${res.status}`);
        }
        
        return res.json();
    },
    
    // Auth
    login(username, password) {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        return fetch(`${API_BASE}/auth/token`, {
            method: 'POST',
            body: formData
        }).then(r => r.json());
    },
    
    register(data) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    getMe() {
        return this.request('/auth/me');
    },
    
    // Signals
    getSignals(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this.request(`/signals/active?${qs}`);
    },
    
    // AI Mentor
    askMentor(question, skillLevel = 'intermediate') {
        return this.request('/ai/mentor/ask', {
            method: 'POST',
            body: JSON.stringify({ question, skill_level: skillLevel })
        });
    },
    
    // Chart Analysis
    analyzeChart(file, symbol, timeframe) {
        const formData = new FormData();
        formData.append('file', file);
        if (symbol) formData.append('symbol', symbol);
        if (timeframe) formData.append('timeframe', timeframe);
        
        return fetch(`${API_BASE}/ai/chart/analyze`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('pipways_token')}` },
            body: formData
        }).then(r => r.json());
    },
    
    // Performance
    analyzeJournal(trades) {
        return this.request('/ai/performance/analyze-journal', {
            method: 'POST',
            body: JSON.stringify(trades)
        });
    },
    
    getPerformanceStats(days = 30) {
        return this.request(`/ai/performance/dashboard-stats?days=${days}`);
    },
    
    // Blog
    getBlogPosts(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this.request(`/blog/posts?${qs}`);
    },
    
    // Admin
    getAdminStats() {
        return this.request('/admin/users');
    }
};

// Navigation State
let currentPage = 'dashboard';

function showPage(page) {
    currentPage = page;
    
    // Close mobile sidebar
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar && sidebar.classList.contains('mobile-open')) {
        sidebar.classList.remove('mobile-open');
        overlay.classList.remove('active');
    }
    
    // Update sidebar active state
    document.querySelectorAll('.sidebar-link').forEach(el => {
        el.classList.remove('active');
    });
    
    const activeNav = document.getElementById(`nav-${page}`);
    if (activeNav) {
        activeNav.classList.add('active');
    }
    
    // Update page title
    const titles = {
        'dashboard': 'Dashboard',
        'journal': 'Trading Journal',
        'analysis': 'Chart Analysis',
        'trade-analysis': 'Trade Analysis',
        'mentor': 'AI Mentor',
        'blog': 'Trading Blog',
        'admin': 'Admin Panel'
    };
    const titleEl = document.getElementById('page-title');
    if (titleEl) {
        titleEl.textContent = titles[page] || page;
    }
    
    // Render content
    const content = document.getElementById('content');
    if (!content) return;
    
    content.innerHTML = '<div class="flex items-center justify-center h-64"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>';
    
    switch(page) {
        case 'dashboard':
            renderDashboard();
            break;
        case 'journal':
            renderJournal();
            break;
        case 'analysis':
            renderChartAnalysis();
            break;
        case 'trade-analysis':
            renderTradeAnalysis();
            break;
        case 'mentor':
            renderMentor();
            break;
        case 'blog':
            renderBlog();
            break;
        case 'admin':
            renderAdmin();
            break;
        default:
            renderDashboard();
    }
}

// Dashboard with Feature Overview Cards
function renderDashboard() {
    const content = document.getElementById('content');
    const user = JSON.parse(localStorage.getItem('pipways_user') || '{}');
    
    content.innerHTML = `
        <div class="space-y-6 max-w-7xl mx-auto">
            <!-- Welcome Banner -->
            <div class="glass-card rounded-2xl p-6 sm:p-8 bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg">
                <h3 class="text-2xl sm:text-3xl font-bold mb-2">Welcome back, ${user.full_name || user.email || 'Trader'}!</h3>
                <p class="text-blue-100 text-sm sm:text-base">Access all your trading tools and insights from your dashboard.</p>
            </div>
            
            <!-- Feature Cards Grid -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
                <!-- Trading Signals -->
                <div onclick="showPage('analysis')" class="glass-card rounded-xl p-6 cursor-pointer hover:scale-105 transition-transform border-l-4 border-blue-500">
                    <div class="flex items-start justify-between mb-4">
                        <div class="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600">
                            <i class="fas fa-signal text-xl"></i>
                        </div>
                        <span class="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded">Live</span>
                    </div>
                    <h4 class="font-bold text-gray-800 mb-1">Trading Signals</h4>
                    <p class="text-sm text-gray-600">Real-time buy/sell signals with entry, stop loss and take profit levels.</p>
                </div>
                
                <!-- AI Mentor -->
                <div onclick="showPage('mentor')" class="glass-card rounded-xl p-6 cursor-pointer hover:scale-105 transition-transform border-l-4 border-purple-500">
                    <div class="flex items-start justify-between mb-4">
                        <div class="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center text-purple-600">
                            <i class="fas fa-robot text-xl"></i>
                        </div>
                        <span class="text-xs font-semibold text-purple-600 bg-purple-50 px-2 py-1 rounded">AI</span>
                    </div>
                    <h4 class="font-bold text-gray-800 mb-1">AI Mentor</h4>
                    <p class="text-sm text-gray-600">Get personalized trading advice and answers to your market questions.</p>
                </div>
                
                <!-- Chart Analysis -->
                <div onclick="showPage('analysis')" class="glass-card rounded-xl p-6 cursor-pointer hover:scale-105 transition-transform border-l-4 border-green-500">
                    <div class="flex items-start justify-between mb-4">
                        <div class="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center text-green-600">
                            <i class="fas fa-chart-bar text-xl"></i>
                        </div>
                        <span class="text-xs font-semibold text-green-600 bg-green-50 px-2 py-1 rounded">Vision</span>
                    </div>
                    <h4 class="font-bold text-gray-800 mb-1">Chart Analysis</h4>
                    <p class="text-sm text-gray-600">Upload charts for instant pattern recognition and technical analysis.</p>
                </div>
                
                <!-- Trade Journal -->
                <div onclick="showPage('journal')" class="glass-card rounded-xl p-6 cursor-pointer hover:scale-105 transition-transform border-l-4 border-orange-500">
                    <div class="flex items-start justify-between mb-4">
                        <div class="w-12 h-12 rounded-lg bg-orange-100 flex items-center justify-center text-orange-600">
                            <i class="fas fa-book text-xl"></i>
                        </div>
                        <span class="text-xs font-semibold text-orange-600 bg-orange-50 px-2 py-1 rounded">Log</span>
                    </div>
                    <h4 class="font-bold text-gray-800 mb-1">Trade Journal</h4>
                    <p class="text-sm text-gray-600">Record and analyze your trades with AI-powered performance insights.</p>
                </div>
                
                <!-- Performance Analytics -->
                <div onclick="showPage('trade-analysis')" class="glass-card rounded-xl p-6 cursor-pointer hover:scale-105 transition-transform border-l-4 border-red-500">
                    <div class="flex items-start justify-between mb-4">
                        <div class="w-12 h-12 rounded-lg bg-red-100 flex items-center justify-center text-red-600">
                            <i class="fas fa-chart-line text-xl"></i>
                        </div>
                        <span class="text-xs font-semibold text-red-600 bg-red-50 px-2 py-1 rounded">Stats</span>
                    </div>
                    <h4 class="font-bold text-gray-800 mb-1">Performance Analytics</h4>
                    <p class="text-sm text-gray-600">Detailed statistics, win rates, and trading psychology analysis.</p>
                </div>
                
                <!-- Blog & Education -->
                <div onclick="showPage('blog')" class="glass-card rounded-xl p-6 cursor-pointer hover:scale-105 transition-transform border-l-4 border-teal-500">
                    <div class="flex items-start justify-between mb-4">
                        <div class="w-12 h-12 rounded-lg bg-teal-100 flex items-center justify-center text-teal-600">
                            <i class="fas fa-graduation-cap text-xl"></i>
                        </div>
                        <span class="text-xs font-semibold text-teal-600 bg-teal-50 px-2 py-1 rounded">Learn</span>
                    </div>
                    <h4 class="font-bold text-gray-800 mb-1">Blog & Education</h4>
                    <p class="text-sm text-gray-600">Trading guides, market insights, and educational resources.</p>
                </div>
                
                <!-- Risk Calculator -->
                <div onclick="showPage('journal')" class="glass-card rounded-xl p-6 cursor-pointer hover:scale-105 transition-transform border-l-4 border-indigo-500">
                    <div class="flex items-start justify-between mb-4">
                        <div class="w-12 h-12 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-600">
                            <i class="fas fa-calculator text-xl"></i>
                        </div>
                        <span class="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2 py-1 rounded">Tool</span>
                    </div>
                    <h4 class="font-bold text-gray-800 mb-1">Risk Calculator</h4>
                    <p class="text-sm text-gray-600">Calculate position sizes and manage risk on every trade.</p>
                </div>
                
                <!-- Webinars -->
                <div onclick="showPage('blog')" class="glass-card rounded-xl p-6 cursor-pointer hover:scale-105 transition-transform border-l-4 border-pink-500">
                    <div class="flex items-start justify-between mb-4">
                        <div class="w-12 h-12 rounded-lg bg-pink-100 flex items-center justify-center text-pink-600">
                            <i class="fas fa-video text-xl"></i>
                        </div>
                        <span class="text-xs font-semibold text-pink-600 bg-pink-50 px-2 py-1 rounded">Live</span>
                    </div>
                    <h4 class="font-bold text-gray-800 mb-1">Webinars</h4>
                    <p class="text-sm text-gray-600">Live trading sessions and recorded educational webinars.</p>
                </div>
            </div>
            
            <!-- Recent Activity Section -->
            <div class="glass-card rounded-xl p-6">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-bold text-gray-800">Recent Signals</h3>
                    <button onclick="showPage('analysis')" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                        View All <i class="fas fa-arrow-right ml-1"></i>
                    </button>
                </div>
                <div id="recent-signals-list" class="space-y-3">
                    <div class="animate-pulse flex space-x-4">
                        <div class="flex-1 space-y-4 py-1">
                            <div class="h-4 bg-gray-200 rounded w-3/4"></div>
                            <div class="space-y-2">
                                <div class="h-4 bg-gray-200 rounded"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Load signals
    loadDashboardSignals();
}

async function loadDashboardSignals() {
    try {
        const signals = await API.getSignals({ limit: 5 });
        const container = document.getElementById('recent-signals-list');
        
        if (signals && signals.length > 0) {
            container.innerHTML = signals.slice(0, 3).map(s => `
                <div class="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-lg border-l-4 ${s.direction === 'BUY' ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'} hover:shadow-md transition-shadow cursor-pointer" onclick="showPage('analysis')">
                    <div class="mb-2 sm:mb-0">
                        <div class="flex items-center gap-2">
                            <strong class="text-lg text-gray-800">${s.symbol}</strong>
                            <span class="px-2 py-1 rounded text-xs font-bold ${s.direction === 'BUY' ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'}">${s.direction}</span>
                        </div>
                        <div class="text-sm text-gray-600 mt-1">
                            Entry: ${s.entry_price} | SL: ${s.stop_loss} | TP: ${s.take_profit}
                        </div>
                    </div>
                    <div class="text-right text-sm text-gray-500">
                        ${new Date(s.created_at).toLocaleDateString()}
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p class="text-gray-500 text-center py-4">No active signals available</p>';
        }
    } catch (e) {
        console.error('Failed to load signals:', e);
        const container = document.getElementById('recent-signals-list');
        if (container) {
            container.innerHTML = '<p class="text-red-500 text-center py-4">Failed to load signals</p>';
        }
    }
}

function renderJournal() {
    const content = document.getElementById('content');
    if (!content) return;
    
    content.innerHTML = `
        <div class="max-w-4xl mx-auto space-y-6">
            <div class="glass-card rounded-xl p-6 sm:p-8">
                <h3 class="text-xl sm:text-2xl font-bold text-gray-800 mb-4">Trading Journal</h3>
                <p class="text-gray-600 mb-6">Record and analyze your trading history. Paste your trade data below for AI analysis.</p>
                
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Trade Data (JSON)</label>
                        <textarea id="journal-input" rows="8" class="w-full p-4 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm" placeholder='[
  {
    "entry_date": "2024-01-01",
    "symbol": "EURUSD",
    "direction": "BUY",
    "entry_price": 1.0850,
    "exit_price": 1.0900,
    "pnl": 50.00,
    "outcome": "win"
  }
]'></textarea>
                    </div>
                    
                    <div class="flex flex-col sm:flex-row gap-4">
                        <button onclick="analyzeJournal()" class="gradient-btn px-6 py-3 rounded-lg text-white font-semibold shadow-lg flex items-center justify-center gap-2 cursor-pointer">
                            <i class="fas fa-brain"></i>
                            Analyze with AI
                        </button>
                        <button onclick="showPage('trade-analysis')" class="px-6 py-3 rounded-lg border-2 border-gray-300 text-gray-700 font-semibold hover:border-blue-500 hover:text-blue-600 transition-colors cursor-pointer">
                            Advanced Analysis
                        </button>
                    </div>
                </div>
            </div>
            
            <div id="journal-results" class="hidden glass-card rounded-xl p-6 sm:p-8">
                <!-- Results injected here -->
            </div>
        </div>
    `;
}

async function analyzeJournal() {
    const input = document.getElementById('journal-input');
    const resultsDiv = document.getElementById('journal-results');
    
    if (!input || !resultsDiv) return;
    
    if (!input.value.trim()) {
        alert('Please enter trade data');
        return;
    }
    
    try {
        const trades = JSON.parse(input.value);
        resultsDiv.classList.remove('hidden');
        resultsDiv.innerHTML = '<div class="flex items-center justify-center py-8"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div><span class="ml-3 text-gray-600">Analyzing...</span></div>';
        
        const analysis = await API.analyzeJournal(trades);
        
        resultsDiv.innerHTML = `
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                <h4 class="text-lg font-bold text-gray-800">Analysis Results</h4>
                <span class="px-4 py-2 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-bold">
                    Grade: ${analysis.overall_grade}
                </span>
            </div>
            
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                <div class="text-center p-4 bg-gray-50 rounded-lg">
                    <div class="text-2xl font-bold text-blue-600">${analysis.statistics?.win_rate || 0}%</div>
                    <div class="text-xs text-gray-600">Win Rate</div>
                </div>
                <div class="text-center p-4 bg-gray-50 rounded-lg">
                    <div class="text-2xl font-bold text-green-600">${analysis.statistics?.profit_factor || 0}</div>
                    <div class="text-xs text-gray-600">Profit Factor</div>
                </div>
                <div class="text-center p-4 bg-gray-50 rounded-lg">
                    <div class="text-2xl font-bold text-purple-600">$${analysis.statistics?.expectancy || 0}</div>
                    <div class="text-xs text-gray-600">Expectancy</div>
                </div>
                <div class="text-center p-4 bg-gray-50 rounded-lg">
                    <div class="text-2xl font-bold text-orange-600">${analysis.statistics?.total_trades || 0}</div>
                    <div class="text-xs text-gray-600">Total Trades</div>
                </div>
            </div>
            
            <div class="space-y-3">
                <h5 class="font-semibold text-gray-800">Recommendations:</h5>
                ${analysis.improvements?.map(i => `<div class="p-3 bg-blue-50 rounded-lg text-sm text-blue-800 border-l-4 border-blue-500">${i}</div>`).join('') || '<p class="text-gray-500">No recommendations</p>'}
            </div>
        `;
    } catch (e) {
        alert('Invalid JSON format: ' + e.message);
    }
}

function renderChartAnalysis() {
    const content = document.getElementById('content');
    if (!content) return;
    
    content.innerHTML = `
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-6xl mx-auto">
            <div class="glass-card rounded-xl p-6 sm:p-8">
                <h3 class="text-xl sm:text-2xl font-bold text-gray-800 mb-4">AI Chart Analysis</h3>
                <p class="text-gray-600 mb-6">Upload your chart images for instant pattern recognition and trade setup validation.</p>
                
                <div class="border-2 border-dashed border-gray-300 rounded-xl p-6 sm:p-8 text-center hover:border-blue-500 transition-colors cursor-pointer bg-gray-50" onclick="document.getElementById('chartUpload').click()">
                    <input type="file" id="chartUpload" accept="image/*" class="hidden" onchange="handleChartUpload(this.files[0])">
                    <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-2xl">
                        <i class="fas fa-cloud-upload-alt"></i>
                    </div>
                    <p class="text-gray-800 font-medium mb-1">Drop chart image here</p>
                    <p class="text-sm text-gray-500">or click to browse (PNG, JPG, max 5MB)</p>
                </div>
                
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Symbol</label>
                        <input type="text" id="chart-symbol" placeholder="EURUSD" class="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Timeframe</label>
                        <select id="chart-timeframe" class="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500">
                            <option value="">Auto-detect</option>
                            <option value="5M">5M</option>
                            <option value="15M">15M</option>
                            <option value="1H">1H</option>
                            <option value="4H">4H</option>
                            <option value="1D">1D</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <div id="chart-results" class="glass-card rounded-xl p-6 sm:p-8 hidden">
                <p class="text-gray-500 text-center">Upload a chart to see AI analysis results</p>
            </div>
        </div>
    `;
}

async function handleChartUpload(file) {
    if (!file) return;
    
    if (file.size > 5 * 1024 * 1024) {
        alert('File too large (max 5MB)');
        return;
    }
    
    const resultsDiv = document.getElementById('chart-results');
    if (!resultsDiv) return;
    
    resultsDiv.classList.remove('hidden');
    resultsDiv.innerHTML = '<div class="flex items-center justify-center py-12"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div><span class="ml-3 text-gray-600">Analyzing chart with AI Vision...</span></div>';
    
    const symbol = document.getElementById('chart-symbol')?.value;
    const timeframe = document.getElementById('chart-timeframe')?.value;
    
    try {
        const analysis = await API.analyzeChart(file, symbol, timeframe);
        
        const biasColor = analysis.trading_bias === 'bullish' ? 'text-green-600' : 
                         analysis.trading_bias === 'bearish' ? 'text-red-600' : 'text-gray-600';
        
        resultsDiv.innerHTML = `
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-start mb-6 gap-4">
                <div>
                    <h4 class="text-lg font-bold text-gray-800">Analysis Results</h4>
                    <p class="text-sm text-gray-500">${analysis.symbol || symbol || 'Unknown'} ${analysis.timeframe || timeframe || ''}</p>
                </div>
                <span class="px-3 py-1 rounded-full ${analysis.confidence > 0.7 ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'} text-sm font-bold">
                    ${Math.round(analysis.confidence * 100)}% Confidence
                </span>
            </div>
            
            <div class="mb-6">
                <span class="text-sm text-gray-600">Trading Bias:</span>
                <span class="text-2xl font-bold ml-2 ${biasColor} uppercase">${analysis.trading_bias}</span>
            </div>
            
            <div class="space-y-4">
                <div>
                    <h5 class="font-semibold text-gray-700 mb-2">Patterns Detected</h5>
                    <div class="flex flex-wrap gap-2">
                        ${analysis.patterns_detected?.map(p => `<span class="px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-sm">${p.name} (${p.reliability})</span>`).join('') || '<span class="text-gray-500">None detected</span>'}
                    </div>
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                    <div class="p-3 bg-red-50 rounded-lg border border-red-100">
                        <span class="text-xs text-red-600 font-semibold">RESISTANCE</span>
                        <p class="text-lg font-bold text-red-700">${analysis.resistance_levels?.[0] || 'N/A'}</p>
                    </div>
                    <div class="p-3 bg-green-50 rounded-lg border border-green-100">
                        <span class="text-xs text-green-600 font-semibold">SUPPORT</span>
                        <p class="text-lg font-bold text-green-700">${analysis.support_levels?.[0] || 'N/A'}</p>
                    </div>
                </div>
                
                <div>
                    <h5 class="font-semibold text-gray-700 mb-2">AI Insights</h5>
                    <ul class="list-disc list-inside space-y-1 text-sm text-gray-600">
                        ${analysis.key_insights?.map(i => `<li>${i}</li>`).join('') || '<li>No specific insights</li>'}
                    </ul>
                </div>
            </div>
        `;
    } catch (error) {
        resultsDiv.innerHTML = `<div class="p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">Analysis failed: ${error.message}</div>`;
    }
}

function renderTradeAnalysis() {
    const content = document.getElementById('content');
    if (!content) return;
    
    content.innerHTML = `
        <div class="max-w-6xl mx-auto space-y-6">
            <div class="glass-card rounded-xl p-6 sm:p-8">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                    <div>
                        <h3 class="text-xl sm:text-2xl font-bold text-gray-800">Advanced Trade Analysis</h3>
                        <p class="text-gray-600 text-sm">Detailed performance analytics and psychology insights</p>
                    </div>
                    <div class="flex gap-2 w-full sm:w-auto">
                        <select id="analysis-period" onchange="loadPerformanceStats()" class="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 flex-1 sm:flex-none">
                            <option value="30">Last 30 Days</option>
                            <option value="90">Last 90 Days</option>
                            <option value="365">Last Year</option>
                        </select>
                    </div>
                </div>
                
                <div id="trade-stats-container" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div class="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl">
                        <div class="text-3xl font-bold text-blue-600 mb-1">--</div>
                        <div class="text-sm text-gray-600">Total Trades</div>
                    </div>
                    <div class="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-xl">
                        <div class="text-3xl font-bold text-green-600 mb-1">--</div>
                        <div class="text-sm text-gray-600">Win Rate</div>
                    </div>
                    <div class="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl">
                        <div class="text-3xl font-bold text-purple-600 mb-1">--</div>
                        <div class="text-sm text-gray-600">Net P&L</div>
                    </div>
                    <div class="p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl">
                        <div class="text-3xl font-bold text-orange-600 mb-1">--</div>
                        <div class="text-sm text-gray-600">Grade</div>
                    </div>
                </div>
            </div>
            
            <div class="glass-card rounded-xl p-6 sm:p-8">
                <h4 class="font-bold text-gray-800 mb-4">Performance Chart</h4>
                <div class="h-64 bg-gray-50 rounded-lg flex items-center justify-center text-gray-400">
                    <i class="fas fa-chart-area text-4xl mb-2"></i>
                    <span class="ml-2">Chart visualization would render here</span>
                </div>
            </div>
        </div>
    `;
    
    loadPerformanceStats();
}

async function loadPerformanceStats() {
    const days = document.getElementById('analysis-period')?.value || 30;
    try {
        const stats = await API.getPerformanceStats(days);
        console.log('Stats loaded:', stats);
        // Update UI would go here
    } catch (e) {
        console.error('Failed to load stats:', e);
    }
}

function renderMentor() {
    const content = document.getElementById('content');
    if (!content) return;
    
    content.innerHTML = `
        <div class="max-w-6xl mx-auto h-[calc(100vh-200px)]">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
                <div class="lg:col-span-2 glass-card rounded-xl flex flex-col h-full">
                    <div class="p-4 border-b border-gray-200 flex justify-between items-center flex-shrink-0">
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white">
                                <i class="fas fa-robot"></i>
                            </div>
                            <div>
                                <h3 class="font-bold text-gray-800">AI Trading Mentor</h3>
                                <p class="text-xs text-green-600 flex items-center gap-1">
                                    <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                                    Online
                                </p>
                            </div>
                        </div>
                        <button onclick="clearMentorChat()" class="text-gray-400 hover:text-gray-600 p-2">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                    
                    <div id="mentor-messages" class="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 min-h-0">
                        <div class="flex gap-3">
                            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm flex-shrink-0">
                                <i class="fas fa-robot"></i>
                            </div>
                            <div class="bg-white p-3 rounded-2xl rounded-tl-none shadow-sm max-w-[85%] sm:max-w-[80%]">
                                <p class="text-gray-800">Welcome! I'm your AI Trading Mentor. Ask me anything about trading strategies, risk management, or market analysis.</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="p-4 border-t border-gray-200 bg-white rounded-b-xl flex-shrink-0">
                        <div class="flex gap-2">
                            <input type="text" id="mentorInput" placeholder="Ask your trading question..." 
                                class="flex-1 px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                onkeypress="if(event.key==='Enter') sendMentorMessage()">
                            <button onclick="sendMentorMessage()" class="gradient-btn px-6 py-3 rounded-lg text-white font-semibold cursor-pointer hover:shadow-lg transition-shadow">
                                <i class="fas fa-paper-plane"></i>
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="space-y-4 hidden lg:block">
                    <div class="glass-card rounded-xl p-4">
                        <h4 class="font-bold text-gray-800 mb-3">Quick Topics</h4>
                        <div class="space-y-2">
                            <button onclick="askMentor('How do I manage risk effectively?')" class="w-full text-left px-4 py-2 rounded-lg hover:bg-blue-50 text-sm text-gray-700 transition-colors cursor-pointer">
                                Risk Management
                            </button>
                            <button onclick="askMentor('What is a good risk/reward ratio?')" class="w-full text-left px-4 py-2 rounded-lg hover:bg-blue-50 text-sm text-gray-700 transition-colors cursor-pointer">
                                R:R Ratios
                            </button>
                            <button onclick="askMentor('How do I control emotions while trading?')" class="w-full text-left px-4 py-2 rounded-lg hover:bg-blue-50 text-sm text-gray-700 transition-colors cursor-pointer">
                                Trading Psychology
                            </button>
                            <button onclick="askMentor('Explain support and resistance levels')" class="w-full text-left px-4 py-2 rounded-lg hover:bg-blue-50 text-sm text-gray-700 transition-colors cursor-pointer">
                                Technical Analysis
                            </button>
                        </div>
                    </div>
                    
                    <div class="glass-card rounded-xl p-4 bg-gradient-to-br from-yellow-50 to-orange-50">
                        <h4 class="font-bold text-gray-800 mb-2">Daily Tip</h4>
                        <p class="text-sm text-gray-600">"Never risk more than 2% of your account on a single trade. Consistency beats intensity."</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function clearMentorChat() {
    const container = document.getElementById('mentor-messages');
    if (!container) return;
    
    container.innerHTML = `
        <div class="flex gap-3">
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm flex-shrink-0">
                <i class="fas fa-robot"></i>
            </div>
            <div class="bg-white p-3 rounded-2xl rounded-tl-none shadow-sm max-w-[80%]">
                <p class="text-gray-800">Chat cleared. How can I help you today?</p>
            </div>
        </div>
    `;
}

function askMentor(question) {
    const input = document.getElementById('mentorInput');
    if (!input) return;
    
    input.value = question;
    sendMentorMessage();
}

async function sendMentorMessage() {
    const input = document.getElementById('mentorInput');
    if (!input) return;
    
    const message = input.value.trim();
    if (!message) return;
    
    const container = document.getElementById('mentor-messages');
    if (!container) return;
    
    // Add user message
    container.innerHTML += `
        <div class="flex gap-3 flex-row-reverse">
            <div class="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 text-sm flex-shrink-0">
                <i class="fas fa-user"></i>
            </div>
            <div class="bg-blue-600 p-3 rounded-2xl rounded-tr-none shadow-sm max-w-[85%] sm:max-w-[80%]">
                <p class="text-white">${message}</p>
            </div>
        </div>
    `;
    
    input.value = '';
    container.scrollTop = container.scrollHeight;
    
    // Show typing indicator
    const typingId = 'typing-' + Date.now();
    container.innerHTML += `
        <div id="${typingId}" class="flex gap-3">
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm flex-shrink-0">
                <i class="fas fa-robot"></i>
            </div>
            <div class="bg-white p-3 rounded-2xl rounded-tl-none shadow-sm">
                <div class="flex space-x-1">
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                </div>
            </div>
        </div>
    `;
    container.scrollTop = container.scrollHeight;
    
    try {
        const response = await API.askMentor(message);
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        
        container.innerHTML += `
            <div class="flex gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm flex-shrink-0">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="bg-white p-3 rounded-2xl rounded-tl-none shadow-sm max-w-[85%] sm:max-w-[80%]">
                    <p class="text-gray-800">${response.response}</p>
                    ${response.suggested_resources ? `<div class="mt-2 pt-2 border-t border-gray-100 text-xs text-blue-600"><strong>Suggested:</strong> ${response.suggested_resources.join(', ')}</div>` : ''}
                </div>
            </div>
        `;
        container.scrollTop = container.scrollHeight;
    } catch (e) {
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        
        container.innerHTML += `
            <div class="flex gap-3">
                <div class="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center text-white text-sm flex-shrink-0">
                    <i class="fas fa-exclamation"></i>
                </div>
                <div class="bg-red-50 p-3 rounded-2xl rounded-tl-none border border-red-100 max-w-[80%]">
                    <p class="text-red-700 text-sm">Sorry, I encountered an error. Please try again.</p>
                </div>
            </div>
        `;
    }
}

function renderBlog() {
    const content = document.getElementById('content');
    if (!content) return;
    
    content.innerHTML = `
        <div class="max-w-6xl mx-auto space-y-6">
            <div class="glass-card rounded-xl p-6 sm:p-8 text-center">
                <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center text-4xl text-blue-600">
                    <i class="fas fa-newspaper"></i>
                </div>
                <h3 class="text-2xl font-bold text-gray-800 mb-2">Trading Blog</h3>
                <p class="text-gray-600 max-w-lg mx-auto mb-6">Latest insights, strategies, and market analysis from our expert traders.</p>
                
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 text-left mt-8">
                    <div class="glass-card rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer">
                        <div class="h-48 bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white text-5xl">
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <div class="p-4">
                            <h4 class="font-bold text-gray-800 mb-2">Understanding Trend Lines</h4>
                            <p class="text-sm text-gray-600 mb-3">Master the art of drawing and interpreting trend lines in your technical analysis.</p>
                            <span class="text-blue-600 text-sm font-semibold">Read More →</span>
                        </div>
                    </div>
                    
                    <div class="glass-card rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer">
                        <div class="h-48 bg-gradient-to-br from-purple-400 to-purple-600 flex items-center justify-center text-white text-5xl">
                            <i class="fas fa-shield-alt"></i>
                        </div>
                        <div class="p-4">
                            <h4 class="font-bold text-gray-800 mb-2">Risk Management Basics</h4>
                            <p class="text-sm text-gray-600 mb-3">Essential risk management strategies every trader must know.</p>
                            <span class="text-blue-600 text-sm font-semibold">Read More →</span>
                        </div>
                    </div>
                    
                    <div class="glass-card rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer">
                        <div class="h-48 bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center text-white text-5xl">
                            <i class="fas fa-brain"></i>
                        </div>
                        <div class="p-4">
                            <h4 class="font-bold text-gray-800 mb-2">Trading Psychology</h4>
                            <p class="text-sm text-gray-600 mb-3">How to master your emotions and maintain discipline in trading.</p>
                            <span class="text-blue-600 text-sm font-semibold">Read More →</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderAdmin() {
    const content = document.getElementById('content');
    if (!content) return;
    
    const user = JSON.parse(localStorage.getItem('pipways_user') || '{}');
    
    if (!user.is_admin) {
        content.innerHTML = `
            <div class="glass-card rounded-xl p-8 text-center border-red-200 bg-red-50 max-w-md mx-auto">
                <i class="fas fa-lock text-4xl text-red-500 mb-4"></i>
                <h3 class="text-xl font-bold text-red-800 mb-2">Access Denied</h3>
                <p class="text-red-600">Admin privileges required.</p>
            </div>
        `;
        return;
    }
    
    content.innerHTML = `
        <div class="max-w-6xl mx-auto space-y-6">
            <div class="glass-card rounded-xl p-6 sm:p-8 bg-gradient-to-r from-gray-800 to-gray-900 text-white">
                <h3 class="text-2xl font-bold mb-2">Admin Dashboard</h3>
                <p class="text-gray-300">Platform management and user administration</p>
            </div>
            
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                <div class="glass-card rounded-xl p-6 border-l-4 border-blue-500">
                    <div class="flex justify-between items-start">
                        <div>
                            <p class="text-gray-600 text-sm">Total Users</p>
                            <p class="text-3xl font-bold text-gray-800 mt-1">1,247</p>
                        </div>
                        <div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600">
                            <i class="fas fa-users"></i>
                        </div>
                    </div>
                </div>
                
                <div class="glass-card rounded-xl p-6 border-l-4 border-green-500">
                    <div class="flex justify-between items-start">
                        <div>
                            <p class="text-gray-600 text-sm">Active Signals</p>
                            <p class="text-3xl font-bold text-gray-800 mt-1">42</p>
                        </div>
                        <div class="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center text-green-600">
                            <i class="fas fa-signal"></i>
                        </div>
                    </div>
                </div>
                
                <div class="glass-card rounded-xl p-6 border-l-4 border-purple-500">
                    <div class="flex justify-between items-start">
                        <div>
                            <p class="text-gray-600 text-sm">System Status</p>
                            <p class="text-3xl font-bold text-green-600 mt-1">Online</p>
                        </div>
                        <div class="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center text-purple-600">
                            <i class="fas fa-server"></i>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="glass-card rounded-xl p-6">
                <h4 class="font-bold text-gray-800 mb-4">Recent Activity</h4>
                <div class="space-y-3">
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600">
                                <i class="fas fa-user-plus text-sm"></i>
                            </div>
                            <div>
                                <p class="text-sm font-semibold text-gray-800">New user registered</p>
                                <p class="text-xs text-gray-500">john@example.com</p>
                            </div>
                        </div>
                        <span class="text-xs text-gray-500">2 min ago</span>
                    </div>
                    
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
                                <i class="fas fa-signal text-sm"></i>
                            </div>
                            <div>
                                <p class="text-sm font-semibold text-gray-800">New signal created</p>
                                <p class="text-xs text-gray-500">EURUSD BUY @ 1.0850</p>
                            </div>
                        </div>
                        <span class="text-xs text-gray-500">15 min ago</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}
