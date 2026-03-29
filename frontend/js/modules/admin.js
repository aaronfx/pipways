/**
 * admin.js — Admin Dashboard Module
 * frontend/js/modules/admin.js  →  served at /js/modules/admin.js
 *
 * Depends on: window.dashboard (DashboardController), window.API
 * Both are guaranteed to exist when this script runs because dashboard.html
 * loads this AFTER the inline <script> block that defines them.
 */

// ── Extend window.API with admin-specific methods ────────────────────────────
API.getAdminStats = function() {
    // FIX: was /admin/users which returns a paginated user list, not platform stats.
    // KPI cards (total_users, active_signals, new_today etc.) were all showing 0.
    return dashboard.apiRequest('/admin/stats');
};
API.getAdminUsers = function(page = 1, perPage = 20, search = '') {
    const qs = new URLSearchParams({
        page, per_page: perPage, ...(search && { search }),
    }).toString();
    return dashboard.apiRequest(`/admin/users/list?${qs}`);
};
API.toggleUser = function(userId) {
    return dashboard.apiRequest(`/admin/users/${userId}/toggle`, { method: 'POST' });
};
API.getTradingAnalytics = function() {
    return dashboard.apiRequest('/admin/trading-analytics');
};
API.getAIStats = function() {
    return dashboard.apiRequest('/admin/ai-stats');
};

// ── AdminPage module ──────────────────────────────────────────────────────────
const AdminPage = {

    // ── Inline helpers (no dependency on external UI object) ─────────────────
    _esc(s) {
        if (s == null) return '';
        return String(s)
            .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
            .replace(/"/g,'&quot;').replace(/'/g,'&#039;');
    },
    _date(s) {
        if (!s) return '—';
        try { return new Date(s).toLocaleDateString('en-GB', { day:'2-digit', month:'short', year:'numeric' }); }
        catch(_) { return s; }
    },
    _num(n, fb = 0) { const v = Number(n); return isNaN(v) ? fb : v; },

    // ── Internal state ────────────────────────────────────────────────────────
    _charts:      {},
    _usersPage:   1,
    _usersSearch: '',
    _container:   null,

    // ── Entry point ───────────────────────────────────────────────────────────
    async render(container) {
        if (!container) return;
        this._container = container;

        const user = (() => {
            try { return JSON.parse(localStorage.getItem('pipways_user') || '{}'); }
            catch(_) { return {}; }
        })();
        const isAdmin = user.is_admin === true
            || user.role === 'admin'
            || user.is_superuser === true;

        if (!isAdmin) {
            container.innerHTML = `
                <div class="flex flex-col items-center justify-center py-20 text-center">
                    <div class="w-16 h-16 rounded-full bg-red-900/30 flex items-center justify-center mb-4">
                        <i class="fas fa-lock text-red-400 text-2xl"></i>
                    </div>
                    <h3 class="text-xl font-bold text-white mb-2">Access Denied</h3>
                    <p class="text-gray-400 text-sm">Administrator privileges required.</p>
                </div>`;
            return;
        }

        container.innerHTML = this._skeleton();

        const [stats, trading, aiStats] = await Promise.all([
            API.getAdminStats().catch(() => ({})),
            API.getTradingAnalytics().catch(() => ({})),
            API.getAIStats().catch(() => ({})),
        ]);

        container.innerHTML = this._shell();
        this._renderOverview(stats);
        this._renderTradingSection(trading);
        this._renderAISection(aiStats);
        await this._renderUsersSection();
        this._setupTabs();
    },

    _skeleton() {
        return `<div class="space-y-4 animate-pulse">
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                ${Array(4).fill('<div class="bg-gray-800 rounded-xl h-28 border border-gray-700"></div>').join('')}
            </div>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                ${Array(2).fill('<div class="bg-gray-800 rounded-xl h-64 border border-gray-700"></div>').join('')}
            </div>
        </div>`;
    },

    _shell() {
        return `
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-6">
            <div>
                <h2 class="text-2xl font-bold text-white flex items-center gap-2">
                    <i class="fas fa-shield-alt text-red-400"></i> Admin Dashboard
                </h2>
                <p class="text-sm text-gray-500 mt-0.5">Platform monitoring &amp; management</p>
            </div>
            <div class="flex items-center gap-2">
                <span class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium"
                      style="background:rgba(16,185,129,.12);color:#34d399;border:1px solid rgba(16,185,129,.25);">
                    <span class="w-1.5 h-1.5 bg-green-400 rounded-full inline-block"
                          style="animation:pulse-dot 2s infinite;"></span>
                    System Online
                </span>
                <button onclick="AdminPage._refresh()"
                        class="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-400 hover:text-white
                               bg-gray-800 border border-gray-700 hover:bg-gray-700 transition-all">
                    <i class="fas fa-sync-alt mr-1"></i>Refresh
                </button>
            </div>
        </div>

        <div class="flex gap-1 mb-6 p-1 rounded-xl bg-gray-800/60 border border-gray-700 w-fit flex-wrap">
            <button class="admin-tab active" data-tab="overview">
                <i class="fas fa-chart-pie mr-1.5"></i>Overview
            </button>
            <button class="admin-tab" data-tab="users">
                <i class="fas fa-users mr-1.5"></i>Users
            </button>
            <button class="admin-tab" data-tab="trading">
                <i class="fas fa-chart-bar mr-1.5"></i>Trading
            </button>
            <button class="admin-tab" data-tab="ai">
                <i class="fas fa-robot mr-1.5"></i>AI Monitor
            </button>
        </div>

        <style>
            .admin-tab { padding:.45rem 1rem; border-radius:.6rem; font-size:.82rem; font-weight:600;
                border:none; cursor:pointer; color:#9ca3af; background:transparent;
                transition:all .18s; white-space:nowrap; }
            .admin-tab.active { background:linear-gradient(135deg,#7c3aed,#6d28d9); color:white;
                box-shadow:0 4px 12px rgba(124,58,237,.35); }
            .admin-tab:not(.active):hover { background:#374151; color:white; }
            .admin-section { display:none; }
            .admin-section.visible { display:block; }
            .kpi-card { background:#1f2937; border:1px solid #374151; border-radius:.75rem;
                padding:1.25rem; transition:transform .2s,box-shadow .2s;
                position:relative; overflow:hidden; }
            .kpi-card:hover { transform:translateY(-2px); box-shadow:0 8px 20px -4px rgba(0,0,0,.4); }
            .kpi-card::before { content:''; position:absolute; bottom:0; left:0; right:0; height:3px; }
            .kpi-purple::before{background:linear-gradient(90deg,#7c3aed,transparent);}
            .kpi-blue::before  {background:linear-gradient(90deg,#3b82f6,transparent);}
            .kpi-green::before {background:linear-gradient(90deg,#10b981,transparent);}
            .kpi-orange::before{background:linear-gradient(90deg,#f59e0b,transparent);}
            .kpi-red::before   {background:linear-gradient(90deg,#ef4444,transparent);}
            .kpi-pink::before  {background:linear-gradient(90deg,#ec4899,transparent);}
            .ua-table { width:100%; border-collapse:collapse; }
            .ua-table th { padding:.6rem .85rem; text-align:left; font-size:.72rem; font-weight:700;
                text-transform:uppercase; letter-spacing:.06em; color:#6b7280; background:#111827; }
            .ua-table td { padding:.65rem .85rem; font-size:.82rem; border-bottom:1px solid #1f2937; }
            .ua-table tr:hover td { background:rgba(124,58,237,.05); }
            .ua-badge { display:inline-block; padding:.2rem .6rem; border-radius:9999px;
                font-size:.7rem; font-weight:700; }
        </style>

        <div id="admin-tab-overview"  class="admin-section visible"></div>
        <div id="admin-tab-users"     class="admin-section"></div>
        <div id="admin-tab-trading"   class="admin-section"></div>
        <div id="admin-tab-ai"        class="admin-section"></div>`;
    },

    _setupTabs() {
        document.querySelectorAll('.admin-tab').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.admin-tab').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.admin-section').forEach(s => s.classList.remove('visible'));
                btn.classList.add('active');
                document.getElementById(`admin-tab-${btn.dataset.tab}`)?.classList.add('visible');
            });
        });
    },

    // ── OVERVIEW ─────────────────────────────────────────────────────────────
    _renderOverview(s) {
        const el = document.getElementById('admin-tab-overview');
        if (!el) return;

        const iconColors = {
            'kpi-purple':'#a78bfa','kpi-green':'#34d399','kpi-blue':'#60a5fa',
            'kpi-orange':'#fbbf24','kpi-red':'#f87171','kpi-pink':'#f472b6',
        };
        const kpis = [
            { cls:'kpi-purple', icon:'fa-users',         label:'Total Users',         val:this._num(s.total_users),               sub:`+${this._num(s.new_today)} today` },
            { cls:'kpi-green',  icon:'fa-satellite-dish',label:'Active Signals',      val:this._num(s.active_signals),             sub:`${this._num(s.total_signals)} all-time` },
            { cls:'kpi-blue',   icon:'fa-graduation-cap',label:'Courses',             val:this._num(s.total_courses),              sub:'available' },
            { cls:'kpi-orange', icon:'fa-video',          label:'Upcoming Webinars',  val:this._num(s.upcoming_webinars),          sub:'scheduled' },
            { cls:'kpi-pink',   icon:'fa-robot',          label:'AI Mentor (today)',  val:this._num(s.ai_mentor_requests_today),   sub:'requests' },
            { cls:'kpi-red',    icon:'fa-chart-bar',      label:'Charts Analyzed',    val:this._num(s.charts_analyzed_today),      sub:'today' },
            { cls:'kpi-green',  icon:'fa-file-upload',    label:'Journal Uploads',    val:this._num(s.journal_uploads_today),      sub:'today' },
            { cls:'kpi-blue',   icon:'fa-newspaper',      label:'Blog Posts',         val:this._num(s.total_blog_posts),           sub:'published' },
        ];

        el.innerHTML = `
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            ${kpis.map(k => `
            <div class="kpi-card ${k.cls}">
                <i class="fas ${k.icon} text-sm mb-3 block"
                   style="color:${iconColors[k.cls]||'#a78bfa'};opacity:.8;"></i>
                <p class="text-2xl font-bold text-white leading-none mb-1">${k.val.toLocaleString()}</p>
                <p class="text-xs text-gray-500 font-medium">${k.label}</p>
                <p class="text-xs mt-0.5 text-gray-600">${k.sub}</p>
            </div>`).join('')}
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
            <div class="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <h4 class="font-semibold text-white text-sm mb-4">
                    <i class="fas fa-user-plus text-purple-400 mr-2"></i>User Growth (7 days)
                </h4>
                <div style="height:200px;position:relative;"><canvas id="admin-growth-chart"></canvas></div>
            </div>
            <div class="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <h4 class="font-semibold text-white text-sm mb-4">
                    <i class="fas fa-chart-pie text-blue-400 mr-2"></i>Platform Activity
                </h4>
                <div style="height:200px;position:relative;"><canvas id="admin-activity-chart"></canvas></div>
            </div>
        </div>

        <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div class="flex items-center justify-between px-5 py-4 border-b border-gray-700">
                <h4 class="font-semibold text-white text-sm">
                    <i class="fas fa-clock text-yellow-400 mr-2"></i>Recent Registrations
                </h4>
                <button onclick="document.querySelector('[data-tab=users]')?.click()"
                        class="text-xs text-purple-400 hover:text-purple-300">View all →</button>
            </div>
            <div class="overflow-x-auto">
                <table class="ua-table">
                    <thead><tr><th>Name</th><th>Email</th><th>Joined</th><th>Tier</th><th>Status</th></tr></thead>
                    <tbody>
                        ${(s.recent_users||[]).length
                            ? (s.recent_users||[]).map(u => this._userRow(u)).join('')
                            : '<tr><td colspan="5" class="text-center py-8 text-gray-500 text-sm">No users yet</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>`;

        this._destroyChart('admin-growth-chart');
        this._destroyChart('admin-activity-chart');

        const gc = document.getElementById('admin-growth-chart');
        if (gc && typeof Chart !== 'undefined') {
            const g = s.user_growth || [];
            this._charts['admin-growth-chart'] = new Chart(gc, {
                type: 'bar',
                data: {
                    labels: g.length
                        ? g.map(x => new Date(x.date).toLocaleDateString('en-GB',{day:'2-digit',month:'short'}))
                        : ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
                    datasets: [{ label:'New Users',
                        data: g.length ? g.map(x => this._num(x.count)) : [0,0,0,0,0,0,0],
                        backgroundColor:'rgba(124,58,237,.6)', borderColor:'#7c3aed',
                        borderWidth:1, borderRadius:4 }],
                },
                options: { responsive:true, maintainAspectRatio:false,
                    plugins:{legend:{display:false}},
                    scales:{y:{grid:{color:'rgba(75,85,99,.3)'},ticks:{color:'#9ca3af'},beginAtZero:true},
                            x:{grid:{display:false},ticks:{color:'#9ca3af'}}} },
            });
        }

        const ac = document.getElementById('admin-activity-chart');
        if (ac && typeof Chart !== 'undefined') {
            this._charts['admin-activity-chart'] = new Chart(ac, {
                type: 'doughnut',
                data: {
                    labels: ['AI Mentor','Chart Analysis','Journal','Signals'],
                    datasets: [{ data: [
                        this._num(s.ai_mentor_requests_today)||24,
                        this._num(s.charts_analyzed_today)||18,
                        this._num(s.journal_uploads_today)||9,
                        this._num(s.active_signals)||12,
                    ], backgroundColor:['#7c3aed','#3b82f6','#10b981','#f59e0b'], borderWidth:0 }],
                },
                options: { responsive:true, maintainAspectRatio:false, cutout:'68%',
                    plugins:{legend:{position:'bottom',labels:{color:'#9ca3af',padding:12,font:{size:11}}}} },
            });
        }
    },

    // ── USER MANAGEMENT ───────────────────────────────────────────────────────
    async _renderUsersSection() {
        const el = document.getElementById('admin-tab-users');
        if (!el) return;

        el.innerHTML = `
        <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3
                        px-5 py-4 border-b border-gray-700">
                <h4 class="font-semibold text-white text-sm">
                    <i class="fas fa-users text-purple-400 mr-2"></i>User Management
                </h4>
                <div class="relative">
                    <i class="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-xs"></i>
                    <input type="text" id="admin-user-search" placeholder="Search users…"
                           class="pl-8 pr-3 py-2 text-sm bg-gray-900 border border-gray-700 rounded-lg
                                  text-white placeholder-gray-600 focus:outline-none focus:border-purple-500 w-48"
                           oninput="AdminPage._onSearch(this.value)">
                </div>
            </div>
            <div id="admin-users-body" class="overflow-x-auto"></div>
            <div id="admin-users-pager" class="px-5 py-4 border-t border-gray-700 flex items-center justify-between"></div>
        </div>`;

        await this._loadUsersPage(1, '');
    },

    _onSearch: (() => {
        let t;
        return (v) => { clearTimeout(t); t = setTimeout(() => AdminPage._loadUsersPage(1, v), 350); };
    })(),

    async _loadUsersPage(page, search) {
        this._usersPage   = page;
        this._usersSearch = search;
        const body  = document.getElementById('admin-users-body');
        const pager = document.getElementById('admin-users-pager');
        if (!body) return;

        body.innerHTML = `<div class="py-8 text-center text-gray-500 text-sm">
            <i class="fas fa-spinner fa-spin mr-2"></i>Loading…</div>`;

        try {
            const data  = await API.getAdminUsers(page, 20, search);
            const users = data.users || [];
            const total = this._num(data.total);
            const pages = this._num(data.pages, 1);

            if (!users.length) {
                body.innerHTML = `<div class="py-10 text-center text-gray-500 text-sm">
                    <i class="fas fa-users text-2xl block mb-2 opacity-30"></i>No users found</div>`;
                if (pager) pager.innerHTML = '';
                return;
            }

            body.innerHTML = `
            <table class="ua-table">
                <thead><tr><th>Name</th><th>Email</th><th>Joined</th>
                    <th>Tier</th><th>Role</th><th>Status</th><th class="text-right">Action</th>
                </tr></thead>
                <tbody>${users.map(u => this._userMgmtRow(u)).join('')}</tbody>
            </table>`;

            if (pager) pager.innerHTML = `
                <span class="text-xs text-gray-500">
                    ${((page-1)*20)+1}–${Math.min(page*20,total)} of ${total} users
                </span>
                <div class="flex gap-1">
                    <button onclick="AdminPage._loadUsersPage(${page-1},'${this._esc(search)}')"
                            ${page<=1?'disabled':''}
                            class="px-3 py-1.5 rounded-lg text-xs bg-gray-700 text-gray-300
                                   disabled:opacity-30 hover:bg-gray-600 transition-colors">← Prev</button>
                    <span class="px-3 py-1.5 text-xs text-gray-400">${page}/${pages}</span>
                    <button onclick="AdminPage._loadUsersPage(${page+1},'${this._esc(search)}')"
                            ${page>=pages?'disabled':''}
                            class="px-3 py-1.5 rounded-lg text-xs bg-gray-700 text-gray-300
                                   disabled:opacity-30 hover:bg-gray-600 transition-colors">Next →</button>
                </div>`;

        } catch(err) {
            body.innerHTML = `<div class="py-8 text-center text-red-400 text-sm">
                <i class="fas fa-exclamation-triangle mr-2"></i>${this._esc(err.message)}</div>`;
        }
    },

    _userRow(u) {
        const active = u.is_active !== false;
        const tier   = u.subscription_tier || 'free';
        const tc     = tier==='pro'?'#a78bfa':tier==='enterprise'?'#fbbf24':'#6b7280';
        const as     = active
            ? 'background:rgba(16,185,129,.15);color:#34d399;border:1px solid rgba(16,185,129,.3);'
            : 'background:rgba(239,68,68,.15);color:#f87171;border:1px solid rgba(239,68,68,.3);';
        return `<tr>
            <td class="text-white font-medium">${this._esc(u.username||u.full_name||'—')}</td>
            <td class="text-gray-400">${this._esc(u.email)}</td>
            <td class="text-gray-500">${this._date(u.created_at)}</td>
            <td><span style="color:${tc};font-size:.75rem;font-weight:600;">${this._esc(tier)}</span></td>
            <td><span class="ua-badge" style="${as}">${active?'Active':'Inactive'}</span></td>
        </tr>`;
    },

    _userMgmtRow(u) {
        const active  = u.is_active !== false;
        const isAdmin = u.is_admin === true;
        const tier    = u.subscription_tier || 'free';
        const tc = { pro:'#a78bfa', enterprise:'#fbbf24', free:'#6b7280' }[tier] || '#6b7280';
        const as = active
            ? 'background:rgba(16,185,129,.15);color:#34d399;border:1px solid rgba(16,185,129,.3);'
            : 'background:rgba(239,68,68,.15);color:#f87171;border:1px solid rgba(239,68,68,.3);';
        return `<tr>
            <td class="font-medium text-white">${this._esc(u.full_name || u.username || '—')}</td>
            <td class="text-gray-400">${this._esc(u.email)}</td>
            <td class="text-gray-500">${this._date(u.created_at)}</td>
            <td><span style="color:${tc};font-size:.72rem;font-weight:700;">${tier.toUpperCase()}</span></td>
            <td>${isAdmin
                ? '<span class="ua-badge" style="background:rgba(239,68,68,.15);color:#f87171;border:1px solid rgba(239,68,68,.3);">Admin</span>'
                : '<span class="ua-badge" style="background:rgba(107,114,128,.15);color:#9ca3af;border:1px solid rgba(107,114,128,.3);">User</span>'}</td>
            <td><span class="ua-badge" style="${as}">${active?'● Active':'○ Inactive'}</span></td>
            <td class="text-right">
                <button onclick="AdminPage._toggleUser(${u.id},this)"
                        class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all border
                               ${active
                                   ? 'border-red-800 text-red-400 hover:bg-red-900/30'
                                   : 'border-green-800 text-green-400 hover:bg-green-900/30'}">
                    ${active?'Deactivate':'Activate'}
                </button>
            </td>
        </tr>`;
    },

    async _toggleUser(userId, btn) {
        const orig = btn.textContent.trim(); btn.textContent = '…'; btn.disabled = true;
        try {
            const r = await API.toggleUser(userId);
            await this._loadUsersPage(this._usersPage, this._usersSearch);
            this._toast(r.message || 'User updated', 'success');
        } catch(err) {
            btn.textContent = orig; btn.disabled = false;
            this._toast(err.message || 'Failed', 'error');
        }
    },

    // ── TRADING ANALYTICS ─────────────────────────────────────────────────────
    _renderTradingSection(t) {
        const el = document.getElementById('admin-tab-trading');
        if (!el) return;

        const wr=this._num(t.overall_win_rate), wins=this._num(t.wins),
              losses=this._num(t.losses), pending=this._num(t.pending),
              buy=this._num(t.buy_count), sell=this._num(t.sell_count),
              avgConf=this._num(t.avg_ai_confidence),
              symbols=t.top_symbols||[], monthly=t.monthly_signals||[];

        el.innerHTML = `
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            ${[
                {cls:'kpi-green', icon:'fa-trophy',        label:'Win Rate',         val:`${wr}%`},
                {cls:'kpi-blue',  icon:'fa-satellite-dish',label:'Total Signals',    val:this._num(t.total_signals)},
                {cls:'kpi-purple',icon:'fa-robot',         label:'Avg AI Confidence',val:`${avgConf}%`},
                {cls:'kpi-orange',icon:'fa-balance-scale', label:'BUY / SELL',       val:`${buy}/${sell}`},
            ].map(k => `<div class="kpi-card ${k.cls}">
                <i class="fas ${k.icon} text-sm mb-3 block" style="opacity:.7;color:#a78bfa;"></i>
                <p class="text-2xl font-bold text-white leading-none mb-1">${k.val}</p>
                <p class="text-xs text-gray-500">${k.label}</p>
            </div>`).join('')}
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
            <div class="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <h4 class="font-semibold text-white text-sm mb-4">
                    <i class="fas fa-chart-pie text-green-400 mr-2"></i>Signal Outcomes
                </h4>
                <div style="height:220px;position:relative;"><canvas id="admin-outcome-chart"></canvas></div>
            </div>
            <div class="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <h4 class="font-semibold text-white text-sm mb-4">
                    <i class="fas fa-chart-bar text-blue-400 mr-2"></i>Monthly Volume
                </h4>
                <div style="height:220px;position:relative;"><canvas id="admin-monthly-chart"></canvas></div>
            </div>
        </div>

        <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div class="px-5 py-4 border-b border-gray-700">
                <h4 class="font-semibold text-white text-sm">
                    <i class="fas fa-star text-yellow-400 mr-2"></i>Top Traded Symbols
                </h4>
            </div>
            <div class="overflow-x-auto">
                <table class="ua-table">
                    <thead><tr><th>#</th><th>Symbol</th><th>Signals</th><th>Wins</th><th>Win Rate</th><th>Bar</th></tr></thead>
                    <tbody>
                        ${symbols.length
                            ? symbols.map((s,i) => {
                                const w = this._num(s.win_rate);
                                const c = w>=60?'#34d399':w>=45?'#fbbf24':'#f87171';
                                return `<tr>
                                    <td class="text-gray-600 font-mono">${String(i+1).padStart(2,'0')}</td>
                                    <td class="font-bold text-white">${this._esc(s.symbol)}</td>
                                    <td class="text-gray-300">${this._num(s.count)}</td>
                                    <td class="text-green-400">${this._num(s.wins)}</td>
                                    <td style="color:${c};font-weight:700;">${w}%</td>
                                    <td><div style="width:100px;height:5px;background:#1f2937;border-radius:2px;overflow:hidden;">
                                        <div style="width:${w}%;height:100%;background:${c};border-radius:2px;"></div>
                                    </div></td>
                                </tr>`;
                              }).join('')
                            : '<tr><td colspan="6" class="text-center py-8 text-gray-500 text-sm">No signal data yet</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>`;

        this._destroyChart('admin-outcome-chart');
        this._destroyChart('admin-monthly-chart');

        const oc = document.getElementById('admin-outcome-chart');
        if (oc && typeof Chart !== 'undefined') {
            this._charts['admin-outcome-chart'] = new Chart(oc, {
                type:'doughnut',
                data:{ labels:['Wins','Losses','Pending'],
                       datasets:[{data:[wins||1,losses||1,pending||1],
                           backgroundColor:['#10b981','#ef4444','#6b7280'],borderWidth:0}] },
                options:{ responsive:true, maintainAspectRatio:false, cutout:'65%',
                    plugins:{legend:{position:'bottom',labels:{color:'#9ca3af',padding:12,font:{size:11}}}} },
            });
        }

        const mc = document.getElementById('admin-monthly-chart');
        if (mc && typeof Chart !== 'undefined') {
            this._charts['admin-monthly-chart'] = new Chart(mc, {
                type:'bar',
                data:{ labels: monthly.length ? monthly.map(m=>m.month) : ['Jan','Feb','Mar','Apr','May','Jun'],
                       datasets:[{ label:'Signals',
                           data: monthly.length ? monthly.map(m=>this._num(m.count)) : [0,0,0,0,0,0],
                           backgroundColor:'rgba(59,130,246,.6)', borderColor:'#3b82f6',
                           borderWidth:1, borderRadius:4 }] },
                options:{ responsive:true, maintainAspectRatio:false,
                    plugins:{legend:{display:false}},
                    scales:{ y:{grid:{color:'rgba(75,85,99,.3)'},ticks:{color:'#9ca3af'},beginAtZero:true},
                             x:{grid:{display:false},ticks:{color:'#9ca3af'}} } },
            });
        }
    },

    // ── AI MONITOR ────────────────────────────────────────────────────────────
    _renderAISection(a) {
        const el = document.getElementById('admin-tab-ai');
        if (!el) return;

        const mToday=this._num(a.mentor_requests_today), mWeek=this._num(a.mentor_requests_week),
              cToday=this._num(a.charts_analyzed_today), cWeek=this._num(a.charts_analyzed_week),
              jToday=this._num(a.journal_uploads_today), jMonth=this._num(a.journal_uploads_month),
              daily=a.daily_ai_usage||[], topics=a.top_mentor_topics||[];

        el.innerHTML = `
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            ${[
                {icon:'fa-robot',     color:'#a78bfa',bg:'rgba(124,58,237,.15)',label:'AI Mentor',      today:mToday,week:mWeek, wl:'this week'},
                {icon:'fa-chart-bar', color:'#60a5fa',bg:'rgba(59,130,246,.15)',label:'Chart Analysis', today:cToday,week:cWeek, wl:'this week'},
                {icon:'fa-file-upload',color:'#34d399',bg:'rgba(16,185,129,.15)',label:'Journal Uploads',today:jToday,week:jMonth,wl:'this month'},
            ].map(c => `
            <div class="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <div class="flex items-center gap-3 mb-4">
                    <div class="w-10 h-10 rounded-xl flex items-center justify-center"
                         style="background:${c.bg};">
                        <i class="fas ${c.icon}" style="color:${c.color};"></i>
                    </div>
                    <span class="text-sm font-semibold text-white">${c.label}</span>
                </div>
                <p class="text-3xl font-bold text-white mb-1">${c.today}</p>
                <p class="text-xs text-gray-500">today</p>
                <div class="mt-3 pt-3 border-t border-gray-700 flex items-center justify-between text-xs">
                    <span class="text-gray-500">${c.wl}</span>
                    <span style="color:${c.color};font-weight:700;">${c.week}</span>
                </div>
            </div>`).join('')}
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div class="lg:col-span-2 bg-gray-800 rounded-xl p-5 border border-gray-700">
                <h4 class="font-semibold text-white text-sm mb-4">
                    <i class="fas fa-chart-line text-purple-400 mr-2"></i>Daily AI Requests (7 days)
                </h4>
                <div style="height:220px;position:relative;"><canvas id="admin-ai-usage-chart"></canvas></div>
            </div>
            <div class="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <h4 class="font-semibold text-white text-sm mb-4">
                    <i class="fas fa-fire text-orange-400 mr-2"></i>Top Mentor Topics
                </h4>
                ${topics.length
                    ? `<div class="space-y-3">${topics.map((t,i) => {
                        const max = Math.max(...topics.map(x=>this._num(x.count)),1);
                        const pct = Math.round(this._num(t.count)/max*100);
                        const cols = ['#7c3aed','#3b82f6','#10b981','#f59e0b','#ef4444','#ec4899'];
                        const col  = cols[i % cols.length];
                        return `<div>
                            <div class="flex justify-between items-center mb-1">
                                <span class="text-xs text-gray-300 truncate max-w-[140px]">${this._esc(t.topic)}</span>
                                <span class="text-xs font-bold" style="color:${col};">${this._num(t.count)}</span>
                            </div>
                            <div style="height:4px;background:#374151;border-radius:2px;overflow:hidden;">
                                <div style="width:${pct}%;height:100%;background:${col};border-radius:2px;"></div>
                            </div>
                        </div>`;
                      }).join('')}</div>`
                    : `<div class="flex flex-col items-center justify-center h-40 text-gray-600 text-sm">
                           <i class="fas fa-comment-slash text-2xl mb-2 opacity-30"></i>No topic data yet</div>`}
            </div>
        </div>`;

        this._destroyChart('admin-ai-usage-chart');
        const uc = document.getElementById('admin-ai-usage-chart');
        if (uc && typeof Chart !== 'undefined') {
            this._charts['admin-ai-usage-chart'] = new Chart(uc, {
                type: 'line',
                data: {
                    labels: daily.length
                        ? daily.map(d=>new Date(d.date).toLocaleDateString('en-GB',{weekday:'short'}))
                        : ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
                    datasets: [{
                        label:'Requests',
                        data: daily.length ? daily.map(d=>this._num(d.requests)) : [0,0,0,0,0,0,0],
                        borderColor:'#a78bfa', backgroundColor:'rgba(124,58,237,.12)',
                        fill:true, tension:0.4, pointRadius:4,
                        pointBackgroundColor:'#7c3aed', pointHoverRadius:6,
                    }],
                },
                options: { responsive:true, maintainAspectRatio:false,
                    plugins:{legend:{display:false}},
                    scales:{ y:{grid:{color:'rgba(75,85,99,.3)'},ticks:{color:'#9ca3af'},beginAtZero:true},
                             x:{grid:{display:false},ticks:{color:'#9ca3af'}} } },
            });
        }
    },

    // ── Helpers ───────────────────────────────────────────────────────────────
    _destroyChart(id) {
        if (this._charts[id]) {
            try { this._charts[id].destroy(); } catch(_) {}
            delete this._charts[id];
        }
    },

    async _refresh() { if (this._container) await this.render(this._container); },

    _toast(msg, type = 'info') {
        const existing = document.getElementById('admin-toast');
        if (existing) existing.remove();
        const colors = { success:'rgba(16,185,129,.9)', error:'rgba(239,68,68,.9)', info:'rgba(59,130,246,.9)' };
        const d = document.createElement('div');
        d.id = 'admin-toast';
        d.style.cssText = `position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;
            padding:.75rem 1.25rem;border-radius:.75rem;font-size:.85rem;font-weight:600;
            color:white;max-width:320px;background:${colors[type]||colors.info};
            box-shadow:0 8px 24px rgba(0,0,0,.4);`;
        d.textContent = msg;
        document.body.appendChild(d);
        setTimeout(() => d.remove(), 3500);
    },
};
