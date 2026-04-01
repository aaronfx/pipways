// ── Global API base URL — exposed on window so public_pages.js and all
// other modules can access it regardless of script load order.
window.API_BASE = window.location.origin;
const API_BASE   = window.API_BASE;


// ── Auth & error helpers — defined here (first script block) so they are
// available immediately when DashboardController initialises and calls
// apiRequest during page load, before the chart-analysis block further down.

async function _parseApiError(response) {
    const text = await response.text().catch(() => '');
    try {
        const json = JSON.parse(text);
        if (json.detail)  return json.detail;
        if (json.message) return json.message;
    } catch (_) { /* not JSON */ }
    return text || `HTTP ${response.status}`;
}

function _handleAuthError() {
    localStorage.removeItem('pipways_token');
    localStorage.removeItem('pipways_user');
    alert('Your session has expired. Please log in again.');
    window.location.href = '/';
}

const DashboardController = class {
    constructor() {
        this.user = null;
        this.currentJournalFormat = null;
        this.manualTrades = [];
        this.charts = {};
        this.lastAnalysisResults = null;
        this.init();
    }

    init() {
        // Check for password reset token BEFORE auth redirect
        if (this.checkResetToken()) return;
        this.checkAuth();
        this.setupNavigation();
        this.setupMobileMenu();
        this.loadDashboardStats();
        // Pre-load cached performance so mentor has it immediately
        this._loadCachedPerformance();
        this.navigate('dashboard');
    }


    // ── Password Reset Flow ───────────────────────────────────────────────
    checkResetToken() {
        const params = new URLSearchParams(window.location.search);
        const token  = params.get('reset_token');
        if (!token) return false;
        // Remove token from URL immediately (single-use — don't expose in history)
        history.replaceState({}, '', window.location.pathname);
        this._showResetModal(token);
        return true; // signals init() to skip auth check
    }

    _showResetModal(token) {
        // Hide all dashboard content so reset modal shows on a clean dark page
        document.querySelectorAll('.section').forEach(el => el.classList.add('hidden'));
        const ticker   = document.querySelector('.ticker-wrap');
        const header   = document.querySelector('header');
        const sidebar  = document.getElementById('sidebar');
        const mobileBtn = document.getElementById('mobile-menu-btn');
        if (ticker)    ticker.style.display   = 'none';
        if (header)    header.style.display   = 'none';
        if (sidebar)   sidebar.style.display  = 'none';
        if (mobileBtn) mobileBtn.style.display = 'none';

        const overlay = document.createElement('div');
        overlay.id = 'reset-modal-overlay';
        overlay.style.cssText = 'position:fixed;inset:0;z-index:9999;background:#0f172a;display:flex;align-items:center;justify-content:center;padding:20px;';
        overlay.innerHTML = `
            <div style="background:#1f2937;border-radius:14px;padding:32px;width:100%;max-width:440px;border:1px solid #374151;text-align:center;">
                <div style="font-size:40px;margin-bottom:12px;">🔐</div>
                <h2 id="reset-modal-h2" style="color:white;margin:0 0 8px;font-size:20px;font-weight:700;">Verifying reset link…</h2>
                <p id="reset-modal-p" style="margin:0;color:#9ca3af;font-size:14px;">Please wait a moment.</p>
                <div id="reset-form-area" style="margin-top:24px;"></div>
            </div>`;
        // Clicking outside or pressing Escape sends user to login — not the dashboard
        overlay.addEventListener('click', e => { if (e.target === overlay) window.location.href = '/'; });
        document.addEventListener('keydown', e => { if (e.key === 'Escape') window.location.href = '/'; }, { once: true });
        document.body.appendChild(overlay);

        fetch(`/email/verify-reset-token?token=${encodeURIComponent(token)}`)
            .then(r => r.json())
            .then(data => {
                const area = document.getElementById('reset-form-area');
                if (!area) return;
                if (!data.valid) {
                    document.getElementById('reset-modal-h2').textContent = 'Link expired';
                    document.getElementById('reset-modal-p').textContent = 'This reset link has expired or already been used.';
                    area.innerHTML = `
                        <p style="color:#9ca3af;font-size:13px;margin:0 0 16px;">Request a new one from the login page.</p>
                        <a href="/" style="display:inline-block;background:#667eea;color:white;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;">Back to Login</a>`;
                } else {
                    document.getElementById('reset-modal-h2').textContent = 'Set a new password';
                    document.getElementById('reset-modal-p').textContent = 'Choose a strong password for your account.';
                    this._renderResetForm(area, token);
                }
            })
            .catch(() => {
                const area = document.getElementById('reset-form-area');
                if (area) area.innerHTML = `<p style="color:#ef4444;font-size:14px;">Connection error. Please try again.</p><a href="/" style="color:#667eea;font-size:14px;">Back to Login</a>`;
            });
    }

    _renderResetForm(area, token) {
        area.innerHTML = `
            <div style="text-align:left;">
                <div style="margin-bottom:16px;">
                    <label style="display:block;color:#9ca3af;font-size:13px;margin-bottom:6px;">New Password</label>
                    <input type="password" id="reset-pw-new" placeholder="Minimum 8 characters"
                        oninput="dashboard._checkPwStrength(this.value)"
                        style="width:100%;padding:10px 14px;background:#374151;border:1px solid #4b5563;border-radius:8px;color:white;font-size:14px;box-sizing:border-box;">
                    <div style="height:4px;background:#4b5563;border-radius:2px;margin-top:6px;overflow:hidden;">
                        <div id="pw-strength-fill" style="height:100%;width:0;transition:all .3s;border-radius:2px;background:#ef4444;"></div>
                    </div>
                    <p id="pw-strength-label" style="font-size:12px;color:#6b7280;margin:4px 0 0;"></p>
                </div>
                <div style="margin-bottom:20px;">
                    <label style="display:block;color:#9ca3af;font-size:13px;margin-bottom:6px;">Confirm Password</label>
                    <input type="password" id="reset-pw-confirm" placeholder="Repeat your password"
                        oninput="dashboard._checkPwMatch()"
                        style="width:100%;padding:10px 14px;background:#374151;border:1px solid #4b5563;border-radius:8px;color:white;font-size:14px;box-sizing:border-box;">
                    <p id="pw-match-label" style="font-size:12px;color:#6b7280;margin:4px 0 0;"></p>
                </div>
                <button id="reset-submit-btn" disabled onclick="dashboard.submitPasswordReset('${token}')"
                    style="width:100%;padding:12px;background:#667eea;color:white;border:none;border-radius:8px;font-weight:700;font-size:15px;cursor:pointer;opacity:.5;transition:opacity .2s;">
                    Set New Password →
                </button>
                <p id="reset-error" style="color:#ef4444;font-size:13px;margin:12px 0 0;display:none;"></p>
            </div>`;
    }

    _checkPwStrength(pw) {
        const fill  = document.getElementById('pw-strength-fill');
        const label = document.getElementById('pw-strength-label');
        if (!fill || !label) return;
        let score = 0;
        if (pw.length >= 8)              score++;
        if (pw.length >= 12)             score++;
        if (/[A-Z]/.test(pw))            score++;
        if (/[0-9]/.test(pw))            score++;
        if (/[^A-Za-z0-9]/.test(pw))     score++;
        const levels = [
            { pct: 0,   color: '#ef4444', text: '' },
            { pct: 20,  color: '#ef4444', text: 'Weak' },
            { pct: 40,  color: '#f59e0b', text: 'Fair' },
            { pct: 60,  color: '#f59e0b', text: 'Good' },
            { pct: 80,  color: '#10b981', text: 'Strong' },
            { pct: 100, color: '#10b981', text: 'Very strong' },
        ];
        const s = levels[score] || levels[0];
        fill.style.width      = s.pct + '%';
        fill.style.background = s.color;
        label.textContent     = s.text;
        label.style.color     = s.color;
        this._checkPwMatch();
    }

    _checkPwMatch() {
        const pw1   = document.getElementById('reset-pw-new')?.value     || '';
        const pw2   = document.getElementById('reset-pw-confirm')?.value  || '';
        const label = document.getElementById('pw-match-label');
        const btn   = document.getElementById('reset-submit-btn');
        const valid = pw1.length >= 8 && pw1 === pw2;
        if (label) {
            label.textContent = pw2.length === 0 ? '' : valid ? '✓ Passwords match' : '✗ Passwords do not match';
            label.style.color = valid ? '#10b981' : '#ef4444';
        }
        if (btn) { btn.disabled = !valid; btn.style.opacity = valid ? '1' : '.5'; }
    }

    async submitPasswordReset(token) {
        const pw  = document.getElementById('reset-pw-new')?.value || '';
        const err = document.getElementById('reset-error');
        const btn = document.getElementById('reset-submit-btn');
        if (pw.length < 8) {
            if (err) { err.textContent = 'Password must be at least 8 characters.'; err.style.display = 'block'; }
            return;
        }
        if (btn) { btn.disabled = true; btn.textContent = 'Updating…'; btn.style.opacity = '.7'; }
        try {
            const res  = await fetch('/email/reset-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, new_password: pw })
            });
            const data = await res.json();
            if (res.ok && data.success) {
                const area = document.getElementById('reset-form-area');
                if (area) area.innerHTML = `
                    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px;">
                        <p style="color:#166534;font-size:15px;font-weight:600;margin:0 0 8px;">✅ Password updated!</p>
                        <p style="color:#374151;font-size:13px;margin:0;">Redirecting to login in 3 seconds…</p>
                    </div>`;
                setTimeout(() => window.location.href = '/', 3000);
            } else {
                const msg = data.detail || 'Failed to reset password. Please try again.';
                if (err) { err.textContent = msg; err.style.display = 'block'; }
                if (btn) { btn.disabled = false; btn.textContent = 'Set New Password →'; btn.style.opacity = '1'; }
            }
        } catch (e) {
            if (err) { err.textContent = 'Connection error. Please try again.'; err.style.display = 'block'; }
            if (btn) { btn.disabled = false; btn.textContent = 'Set New Password →'; btn.style.opacity = '1'; }
        }
    }

    _loadCachedPerformance() {
        try {
            const raw = localStorage.getItem('pipways_performance');
            if (!raw) return;
            const data = JSON.parse(raw);
            // Keep in memory so mentor requests can attach it without re-reading localStorage
            this._cachedPerformance = data;
            const age = Math.round((Date.now() - data.cached_at) / 3600000);
            console.log(`[Dashboard] Loaded cached performance (${age}h old, grade=${data.overall_grade})`);
        } catch(e) {}
    }

    checkAuth() {
        const token = localStorage.getItem('pipways_token');
        const userStr = localStorage.getItem('pipways_user');
        if (!token || !userStr) {
            window.location.href = '/';
            return;
        }
        try {
            this.user = JSON.parse(userStr);
            this.updateUserDisplay();
            // Render admin menu immediately with whatever flags are in localStorage
            setTimeout(() => this.renderAdminMenu(), 200);
            // Then silently refresh from server to correct any stale/missing flags
            setTimeout(() => this._refreshUserFromServer(), 500);
        } catch (e) {
            window.location.href = '/';
        }
    }

    updateUserDisplay() {
        const user = this.user || {};
        const name = user.full_name || user.email || 'User';
        // Sidebar profile
        const nameEl  = document.getElementById('user-name');
        const emailEl = document.getElementById('user-email');
        if (nameEl)  nameEl.textContent  = name;
        if (emailEl) emailEl.textContent = user.email || '';
        // Header subtitle — only update the name span, preserve surrounding text
        const nameSpan = document.getElementById('header-user-name');
        if (nameSpan) nameSpan.textContent = user.full_name?.split(' ')[0] || user.email || 'Trader';
    }

    renderAdminMenu() {
        const user = this.user || {};
        const isAdmin = this._isAdminUser(user);
        const adminMenu = document.getElementById('admin-menu-container');
        if (adminMenu) {
            adminMenu.style.display = isAdmin ? 'block' : 'none';
        }
    }

    // Centralised admin check used by renderAdminMenu, loadAdminData, and loadSectionData.
    // Three tiers:
    //   1. Explicit flags from the JWT/user object (most reliable)
    //   2. Email pattern fallback — catches cases where the stored user object
    //      was created before is_admin was added to the JWT payload
    //   3. /auth/me refresh — silently re-fetches the user and updates localStorage
    //      so the next page load has the correct flags without requiring a re-login
    _isAdminUser(user) {
        if (!user) return false;
        if (user.is_admin === true)     return true;
        if (user.role === 'admin')      return true;
        if (user.is_superuser === true) return true;
        // Fallback: treat known admin email patterns as admin
        // (handles cases where is_admin is missing from the stored token)
        const email = (user.email || '').toLowerCase();
        if (email === 'admin@pipways.com' || email.startsWith('admin+')) return true;
        return false;
    }

    // Refresh user data from /auth/me and update localStorage + this.user.
    // Called once on init so stale tokens get corrected silently.
    async _refreshUserFromServer() {
        try {
            const fresh = await this.apiRequest('/auth/me');
            if (fresh && fresh.email) {
                this.user = { ...this.user, ...fresh };
                localStorage.setItem('pipways_user', JSON.stringify(this.user));
                this.updateUserDisplay();
                this.renderAdminMenu();   // re-evaluate with fresh flags
            }
        } catch (_) {
            // Non-fatal — stale data is better than crashing
        }
    }

    setupNavigation() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                const section = e.currentTarget.dataset.section;
                const href = e.currentTarget.getAttribute('href');
                // Allow real href links (not "#") to navigate normally
                if (!section && href && href !== '#') {
                    return;
                }
                e.preventDefault();
                if (section) {
                    console.log('[Dashboard] Navigating to section:', section);
                    this.navigate(section);
                }
            });
        });
    }

    setupMobileMenu() {
        const btn     = document.getElementById('mobile-menu-btn');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');

        const openSidebar  = () => {
            sidebar?.classList.remove('-translate-x-full');
            overlay?.classList.remove('hidden');
            btn?.setAttribute('aria-expanded', 'true');
            // Focus first interactive element in sidebar
            setTimeout(() => {
                const firstLink = sidebar?.querySelector('a, button');
                firstLink?.focus();
            }, 310); // after transition
        };
        const closeSidebar = () => {
            sidebar?.classList.add('-translate-x-full');
            overlay?.classList.add('hidden');
            btn?.setAttribute('aria-expanded', 'false');
            btn?.focus(); // return focus to trigger
        };

        if (btn) btn.addEventListener('click', () => {
            sidebar?.classList.contains('-translate-x-full') ? openSidebar() : closeSidebar();
        });

        overlay?.addEventListener('click', closeSidebar);

        // Escape key closes mobile sidebar
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && sidebar && !sidebar.classList.contains('-translate-x-full')) {
                closeSidebar();
            }
        });
    }

    navigate(section) {
        // ── Update nav active state ───────────────────────────────────────
        // Reset all nav links
        document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
        // Activate the target link
        const activeLink = document.querySelector(`[data-section="${section}"]`);
        if (activeLink) activeLink.classList.add('active');

        // ── Hide all sections, reveal target with fade ────────────────────
        document.querySelectorAll('.section').forEach(el => el.classList.add('hidden'));
        const target = document.getElementById(`section-${section}`);
        if (target) {
            target.classList.remove('hidden');
            // Trigger CSS fade-in on every navigation, not just first load
            target.style.animation = 'none';
            target.offsetHeight; // reflow
            target.style.animation = 'fadeIn 0.35s ease-out both';
            this.loadSectionData(section);
        }

        // ── Header title + subtitle ───────────────────────────────────────
        const meta = {
            'dashboard': { title: 'Dashboard',          sub: 'Your learning & research command centre' },
            'webinars':  { title: 'Live Webinars',         sub: 'Expert-led sessions, market walkthroughs and Q&A' },
            'blog':      { title: 'Research & Blog',       sub: 'Market analysis, trading insights and education' },
            'analysis':  { title: 'Validate Trade Setup',  sub: 'Upload a chart screenshot for AI-powered analysis' },
            'stocks':    { title: 'AI Stock Research',     sub: 'Fundamental and sentiment analysis on global markets' },
            'signals':   { title: 'Market Signals',        sub: 'Live trading opportunities from our analysts' },
            'enhanced-signals': { title: 'Enhanced Signals', sub: 'AI-powered professional trading insights' },
            'journal':   { title: 'Performance Analytics', sub: 'AI-powered coaching from your real trade data' },
            'mentor':    { title: 'AI Mentor',             sub: '24/7 personal trading coach' },
            'admin':     { title: 'Admin Panel',        sub: 'Platform administration' },
            'cms':       { title: 'Content Management', sub: 'Manage courses, blog, signals and users' }
        };
        const m = meta[section] || { title: 'Dashboard', sub: '' };
        const titleEl = document.getElementById('page-title');
        const subEl   = document.getElementById('header-subtitle');
        if (titleEl) titleEl.textContent = m.title;
        if (subEl) {
            const firstName = this.user?.full_name?.split(' ')[0] || this.user?.email || 'Trader';
            if (section === 'dashboard') {
                subEl.innerHTML = `Welcome back, <span id="header-user-name" class="text-purple-400 font-medium">${firstName}</span>`;
            } else {
                subEl.innerHTML = `<span class="text-gray-500">${m.sub}</span>`;
            }
        }

        // ── Breadcrumb — REC: show path for sub-sections ─────────────────
        const bc = document.getElementById('header-breadcrumb');
        if (bc) {
            if (section === 'dashboard') {
                bc.classList.add('hidden');
                bc.innerHTML = '';
            } else {
                bc.classList.remove('hidden');
                bc.innerHTML = `<a href="#" onclick="dashboard.navigate('dashboard');return false;">Home</a>`
                    + `<span class="pw-breadcrumb-sep">›</span>`
                    + `<span class="text-gray-400">${m.title}</span>`;
            }
        }

        // ── Close mobile sidebar ──────────────────────────────────────────
        document.getElementById('sidebar')?.classList.add('-translate-x-full');
        document.getElementById('sidebar-overlay')?.classList.add('hidden');

        // ── Scroll content area back to top ───────────────────────────────
        document.querySelector('main')?.scrollTo({ top: 0, behavior: 'smooth' });
    }

    async loadSectionData(section) {
        try {
            switch(section) {
                case 'dashboard': this.loadDashboardStats(); break;
                case 'signals':   // redirected — fall through to enhanced-signals
                case 'enhanced-signals':
                case 'enhanced-signals': 
                    if (typeof window.enhancedSignals !== 'undefined') {
                        // init() on first visit (registers tabs + interval), loadSignals() after that
                        if (!window.enhancedSignals._initialized) {
                            window.enhancedSignals._initialized = true;
                            window.enhancedSignals.init();
                        } else {
                            window.enhancedSignals.loadSignals();
                        }
                    } else {
                        console.warn('[Dashboard] enhancedSignals module not loaded');
                    }
                    break;
                case 'webinars':  await this.loadWebinars(); break;
                case 'blog':      await this.loadBlog();     break;
                case 'journal':   this.setupJournalUpload(); break;
                case 'mentor':    await this.loadMentor();   break;
                case 'admin': {
                    const container = document.getElementById('admin-container');
                    if (!container) break;
                    if (typeof AdminPage !== 'undefined') {
                        await AdminPage.render(container);
                    } else {
                        container.innerHTML = `
                            <div class="bg-red-900/30 border border-red-700/50 rounded-lg p-6 text-center">
                                <i class="fas fa-exclamation-triangle text-red-400 text-2xl mb-2"></i>
                                <p class="text-red-200">Admin module failed to load.</p>
                                <p class="text-red-400 text-sm">Please refresh the page.</p>
                            </div>`;
                    }
                    break;
                }

                case 'cms': {
                    const container = document.getElementById('cms-container');
                    if (!container) break;
                    if (typeof CMSPage !== 'undefined') {
                        await CMSPage.render(container);
                    } else {
                        container.innerHTML = `
                            <div class="bg-red-900/30 border border-red-700/50 rounded-lg p-6 text-center">
                                <i class="fas fa-exclamation-triangle text-red-400 text-2xl mb-2"></i>
                                <p class="text-red-200">CMS module failed to load.</p>
                                <p class="text-red-400 text-sm">Please refresh the page.</p>
                            </div>`;
                    }
                    break;
                }
                case 'analysis': {
                    const container = document.getElementById('chart-analysis-container');
                    if (container) container.innerHTML = '';
                    if (typeof ChartAnalysisPage !== 'undefined') {
                        await ChartAnalysisPage.render('chart-analysis-container');
                    } else {
                        if (container) container.innerHTML = `
                            <div class="bg-red-900/30 border border-red-700/50 rounded-lg p-6 text-center">
                                <i class="fas fa-exclamation-triangle text-red-400 text-2xl mb-2"></i>
                                <p class="text-red-200">Chart analysis module failed to load.</p>
                                <p class="text-red-400 text-sm">Please refresh the page.</p>
                            </div>`;
                    }
                    break;
                }
            }
        } catch (err) {
            console.error(`[Dashboard] Error loading section ${section}:`, err);
        }
    }

    async loadDashboardStats() {
        this._initClock();
        this._initTicker();
        this._setGreeting();
        this._initSessionPill();
        this._initSocialProof();
        this._initUsageBars();
        await this._loadDashboardCards();
    }

    _initSessionPill() {
        // Pipways session clock — shows which session is live in WAT (UTC+1)
        const update = () => {
            const now = new Date();
            const utcH = now.getUTCHours();
            const utcM = now.getUTCMinutes();
            const watH = (utcH + 1) % 24; // WAT = UTC+1
            const t = watH * 60 + utcM;

            // Session windows in WAT minutes
            const sessions = [
                { name: 'Sydney',        open: 23*60, close: 24*60+8*60,  color: '#34d399' },
                { name: 'Tokyo',         open: 1*60,  close: 10*60,       color: '#60a5fa' },
                { name: 'London',        open: 9*60,  close: 18*60,       color: '#a78bfa' },
                { name: 'New York',      open: 14*60, close: 23*60,       color: '#f59e0b' },
            ];
            const overlap = (t >= 9*60 && t < 10*60) ? 'Tokyo–London' :
                            (t >= 14*60 && t < 18*60) ? 'London–NY (Peak)' : null;

            let active = sessions.filter(s => {
                if (s.close > 24*60) return t >= s.open || t < s.close - 24*60;
                return t >= s.open && t < s.close;
            });

            const lbl   = document.getElementById('stat-session-label');
            const dot   = document.querySelector('#stat-session-pill .w-1\\.5');
            const nyEl  = document.getElementById('dash-ny-countdown');

            if (lbl) {
                if (overlap) {
                    lbl.textContent = overlap + ' overlap';
                    lbl.style.color = '#fbbf24';
                } else if (active.length) {
                    lbl.textContent = active[0].name + ' open';
                    lbl.style.color = active[0].color;
                } else {
                    lbl.textContent = 'Markets closed';
                    lbl.style.color = '#6b7280';
                }
            }

            // NY countdown
            if (nyEl) {
                const nyOpenWat = 14*60; // 2pm WAT
                const minsToNY = t < nyOpenWat ? nyOpenWat - t : (24*60 - t + nyOpenWat);
                const hh = Math.floor(minsToNY / 60);
                const mm = minsToNY % 60;
                nyEl.textContent = t >= 14*60 && t < 23*60 ? 'Open now' : hh + 'h ' + mm + 'm';
            }
        };
        update();
        setInterval(update, 60000);
    }

    _initSocialProof() {
        // Simulated real-time platform activity — replaced with real API data when available
        const el = document.getElementById('dash-social-proof');
        if (!el) return;
        const counts = [247, 312, 289, 271, 334, 298, 261];
        const n = counts[new Date().getDate() % counts.length];
        el.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-green-400 flex-shrink-0" style="animation:pulse-dot 2s infinite;"></span>'
            + '<span style="color:#9ca3af;font-size:.75rem;">'
            + '<strong style="color:white;">' + n + '</strong> chart analyses run today by Pipways traders</span>';
    }

    _initUsageBars() {
        // Wire usage.js badges — wait for PipwaysUsage to finish its /auth/me fetch
        // before rendering, so counters show real data not stale localStorage
        const _wire = () => {
            const barEl = document.getElementById('dash-chart-usage-bar');
            if (barEl && typeof PipwaysUsage !== 'undefined') {
                PipwaysUsage.renderBadge('chart_analysis', barEl);
            }
            // Remove signals lock overlay for paid users
            if (typeof PipwaysUsage !== 'undefined') {
                const tier = PipwaysUsage.tier;
                if (tier === 'basic' || tier === 'pro') {
                    const lockEl = document.getElementById('dash-signals-lock');
                    if (lockEl) lockEl.style.display = 'none';
                }
            }
        };

        if (typeof PipwaysUsage !== 'undefined' && PipwaysUsage.isLoaded) {
            _wire();
        } else {
            // PipwaysUsage hasn't finished its refresh yet — wait for it
            // It fires pipways:usage-updated when done, but also try after 1.5s as fallback
            document.addEventListener('pipways:usage-updated', _wire, { once: true });
            setTimeout(_wire, 1500);
        }
    }

    async _loadDashboardCards() {
        const safe = fn => fn.catch(() => null);
        const set  = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
        const _e   = s => s == null ? '' : String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

        // ── Tool card helpers (Card 5) ────────────────────────────────────
        function _premiumFeatureCard(icon, color, bg, border, title, sub, section, href, isPaid, tag) {
            var tagHtml = tag
                ? '<span style="font-size:.65rem;font-weight:700;padding:.15rem .5rem;border-radius:9999px;background:' + color + '20;color:' + color + ';border:1px solid ' + color + '33;flex-shrink:0;">' + tag + '</span>'
                : '';
            var lockHtml = (!isPaid && !href)
                ? '<i class="fas fa-lock" style="font-size:.55rem;margin-left:.3rem;opacity:.55;color:#6b7280;"></i>'
                : '';
            // Use data attributes to avoid quote nesting in onclick
            var dataNav = href ? 'data-href="' + href + '"' : 'data-section="' + section + '"';
            return '<div class="pw-tool-card" ' + dataNav + ' '
                + 'style="background:' + bg + ';border:1px solid ' + border + ';border-radius:.75rem;padding:.85rem;cursor:pointer;transition:all .2s;">'
                + '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.5rem;">'
                + '<div style="width:32px;height:32px;border-radius:.5rem;background:' + color + '20;display:flex;align-items:center;justify-content:center;flex-shrink:0;">'
                + '<i class="fas ' + icon + '" style="color:' + color + ';font-size:.82rem;"></i></div>'
                + tagHtml
                + '</div>'
                + '<div style="font-size:.8rem;font-weight:700;color:white;line-height:1.3;">' + title + lockHtml + '</div>'
                + '<div style="font-size:.7rem;color:#6b7280;margin-top:.2rem;line-height:1.35;">' + sub + '</div>'
                + '</div>';
        }

        function _buildToolsHub(isPaid) {
            var html = '<div class="rounded-xl p-4 mb-3 pw-tool-card" data-section="analysis" '
                + 'style="background:linear-gradient(135deg,rgba(96,165,250,.08),rgba(124,58,237,.08));border:1px solid rgba(96,165,250,.2);">'
                + '<div style="display:flex;align-items:center;gap:.75rem;margin-bottom:.5rem;">'
                + '<div style="width:40px;height:40px;border-radius:.75rem;background:rgba(96,165,250,.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;">'
                + '<i class="fas fa-chart-bar" style="color:#60a5fa;font-size:1rem;"></i></div>'
                + '<div style="flex:1;min-width:0;">'
                + '<div style="font-size:.875rem;font-weight:700;color:white;">Analyse a Chart</div>'
                + '<div style="font-size:.72rem;color:#6b7280;">Upload any screenshot — get entry, stop &amp; target instantly</div>'
                + '</div>'
                + '<span style="font-size:.65rem;font-weight:700;padding:.2rem .55rem;border-radius:9999px;background:rgba(52,211,153,.12);color:#34d399;border:1px solid rgba(52,211,153,.25);flex-shrink:0;">Free</span>'
                + '</div>'
                + '<div id="dash-chart-usage"></div>'
                + '<div style="display:flex;align-items:center;justify-content:space-between;margin-top:.5rem;">'
                + '<span style="font-size:.72rem;color:#6b7280;"><i class="fas fa-upload" style="margin-right:.25rem;"></i>Drag &amp; drop or click to upload</span>'
                + '<span style="font-size:.72rem;font-weight:700;color:#60a5fa;">Open →</span>'
                + '</div>'
                + '</div>'
                + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:.65rem;">'
                + _premiumFeatureCard('fa-file-chart-pie','#a78bfa','rgba(124,58,237,.08)','rgba(124,58,237,.2)','Performance Analysis','Upload MT4/MT5 · find your weaknesses','journal',null,isPaid,isPaid?null:'1 free')
                + _premiumFeatureCard('fa-chart-pie','#34d399','rgba(52,211,153,.08)','rgba(52,211,153,.2)','AI Stock Research','NGX + global stocks analysis','stocks',null,isPaid,isPaid?null:'2/day')
                + _premiumFeatureCard('fa-satellite-dish','#f472b6','rgba(244,114,182,.08)','rgba(244,114,182,.2)','Market Signals','Live setups with validation','signals',null,isPaid,isPaid?null:'Preview')
                + _premiumFeatureCard('fa-book-open','#fbbf24','rgba(251,191,36,.08)','rgba(251,191,36,.2)','Trading Academy','28 lessons · always free',null,'/academy',true,'Free')
                + '</div>';
            return html;
        }



        // ── Fetch all data in parallel ────────────────────────────────────
        const [courses, webinars, blog, signals, progress, academyResume] = await Promise.all([
            safe(this.apiRequest('/courses/list')),
            safe(this.apiRequest('/webinars/upcoming?upcoming=true')),
            safe(this.apiRequest('/blog/posts')),
            safe(this.apiRequest('/api/signals/active')),
            safe(this.apiRequest('/courses/enhanced/progress')),
            safe(this.apiRequest('/learning/resume')),
        ]);

        const count = d => Array.isArray(d) ? d.length
            : (d?.courses?.length || d?.signals?.length || d?.posts?.length || d?.webinars?.length || 0);

        // ── Stat chips — animate count-in + sub-labels ──────────────────────
        const setChip = (id, val, sub) => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = val;
                el.classList.remove('stat-updated');
                void el.offsetWidth;
                el.classList.add('stat-updated');
            }
            const subEl = document.getElementById(id + '-sub');
            if (subEl) subEl.textContent = sub || '';
        };
        // Derive contextual sub-labels
        const courseArr = Array.isArray(courses) ? courses : [];
        const inProgCount = (progress?.in_progress || []).length;
        const completedCount = (progress?.completed || []).length;
        const coursesSub = ''; // Legacy courses removed — Academy stat chip handles its own label
        const webinarArr = Array.isArray(webinars) ? webinars : (webinars?.webinars || []);
        const webinarsSub = webinarArr.length > 0 ? 'This week' : '';
        const blogArr = Array.isArray(blog) ? blog : (blog?.posts || []);
        const signalArr = Array.isArray(signals) ? signals : (signals?.signals || []);
        const activeSignals = signalArr.filter(s => s.status === 'active').length;
        const signalsSub = activeSignals > 0 ? `${activeSignals} active now` : signalArr.length > 0 ? 'No active signals' : '';
        // Academy lessons completed count for the stat chip
        const academyLessonsCount = (() => {
            if (!academyResume) return '0';
            if (academyResume.type === 'complete') return '28';
            if (academyResume.completed_count != null) return String(academyResume.completed_count);
            // lesson_id is the DB id of the NEXT lesson — use level_percent as proxy
            if (academyResume.level_percent > 0) {
                const approx = Math.round((academyResume.level_percent / 100) * 12); // beginner has ~12 lessons
                return approx > 0 ? String(approx) : '1';
            }
            return '0';
        })();
        setChip('stat-courses', academyLessonsCount, academyResume?.type === 'complete' ? 'All done! 🎉' : 'lessons done');
        setChip('stat-webinars', webinars ? count(webinars) : '—', webinarsSub);
        setChip('stat-blog',     blog     ? count(blog)     : '—', blogArr.length > 0 ? 'Latest articles' : '');
        setChip('stat-signals',  signals  ? count(signals)  : '—', signalsSub);

        // ── Card 1: Continue Learning (Academy-powered) ──────────────────
        const learningEl = document.getElementById('dash-learning-body');
        if (learningEl) {
            const name = this.user?.full_name?.split(' ')[0] || 'Trader';

            if (!academyResume || academyResume.type === 'start') {
                // New user — show inviting empty state
                learningEl.innerHTML =
                    '<div class="flex flex-col items-center text-center py-3">'
                    + '<div class="w-14 h-14 rounded-full flex items-center justify-center mb-3" style="background:rgba(52,211,153,.08);border:2px dashed rgba(52,211,153,.2);">'
                    + '<i class="fas fa-book-open" style="color:#34d399;font-size:1.25rem;"></i>'
                    + '</div>'
                    + '<p class="font-semibold text-white mb-1 text-sm">Start your Trading Academy, ' + _e(name) + '</p>'
                    + '<p class="text-xs mb-4" style="color:#4b5563;line-height:1.5;">28 free lessons · from first pip to institutional strategy</p>'
                    + '<a href="/academy" class="px-4 py-2 rounded-lg text-sm font-semibold text-decoration-none" style="background:linear-gradient(90deg,#7c3aed,#6d28d9);color:white;">'
                    + '<i class="fas fa-graduation-cap mr-1.5"></i>Begin Academy →</a>'
                    + '</div>';

            } else if (academyResume.type === 'complete') {
                learningEl.innerHTML =
                    '<div class="flex flex-col items-center text-center py-3">'
                    + '<div class="w-14 h-14 rounded-full flex items-center justify-center mb-3" style="background:rgba(251,191,36,.1);border:2px dashed rgba(251,191,36,.2);">'
                    + '<i class="fas fa-trophy" style="color:#fbbf24;font-size:1.25rem;"></i>'
                    + '</div>'
                    + '<p class="font-semibold text-white mb-1 text-sm">Academy Complete! 🏆</p>'
                    + '<p class="text-xs mb-4" style="color:#4b5563;">All 28 lessons done. Review any module anytime.</p>'
                    + '<a href="/academy" class="px-4 py-2 rounded-lg text-sm font-semibold text-decoration-none" style="background:rgba(251,191,36,.12);border:1px solid rgba(251,191,36,.3);color:#fbbf24;">'
                    + 'Review Academy →</a>'
                    + '</div>';

            } else {
                // In progress — show level progress bars (the CTA is in "Your Next Step" card)
                const levelName  = academyResume.level || 'Beginner';
                const levelPct   = academyResume.level_percent || 0;
                const totalPct   = academyResume.overall_percent || 0;
                const lessonTitle = academyResume.title || 'Next Lesson';
                const moduleName  = academyResume.module || '';
                const lessonId    = academyResume.lesson_id;

                // Level palette - fix progress calculation using actual progress data
                const levels = [
                    { name: 'Beginner',     color: '#34d399' },
                    { name: 'Intermediate', color: '#60a5fa' },
                    { name: 'Advanced',     color: '#f59e0b' },
                ];
                
                // Calculate progress for each level based on progress data
                const progBars = levels.map(lv => {
                    let pct = 0;
                    
                    // Try to get level progress from the progress data
                    if (progress && progress.levels) {
                        const levelKey = lv.name.toLowerCase();
                        const levelData = progress.levels[levelKey];
                        if (levelData) {
                            pct = Math.round(levelData.percentage || 0);
                        }
                    } else if (levelName === lv.name) {
                        // Fallback to current level percentage
                        pct = Math.round(levelPct);
                    }
                    
                    return '<div style="margin-bottom:.6rem;">'
                        + '<div class="flex items-center justify-between mb-1">'
                        + '<span class="text-xs" style="color:' + lv.color + ';">' + lv.name + '</span>'
                        + '<span class="text-xs font-bold" style="color:' + lv.color + ';">' + pct + '%</span>'
                        + '</div>'
                        + '<div class="pw-progress-bar" style="height:5px;">'
                        + '<div class="pw-progress-fill" style="width:' + pct + '%;background:' + lv.color + ';transition:width .6s ease;"></div>'
                        + '</div>'
                        + '</div>';
                }).join('');

                // Current lesson chip
                const lessonChip =
                    '<div class="flex items-center gap-2 mt-3 p-2.5 rounded-lg" style="background:rgba(124,58,237,.07);border:1px solid rgba(124,58,237,.15);">'
                    + '<div class="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0" style="background:rgba(124,58,237,.2);">'
                    + '<i class="fas fa-play" style="color:#a78bfa;font-size:.55rem;margin-left:1px;"></i></div>'
                    + '<div class="min-w-0 flex-1">'
                    + '<div class="text-xs" style="color:#6b7280;">' + _e(moduleName) + ' · ' + _e(levelName) + '</div>'
                    + '<div class="text-xs font-semibold text-white truncate">' + _e(lessonTitle) + '</div>'
                    + '</div>'
                    + '<a href="/academy' + (lessonId ? '?lesson=' + lessonId : '') + '" class="text-xs font-semibold flex-shrink-0 text-decoration-none" style="color:#a78bfa;">Continue →</a>'
                    + '</div>';

                learningEl.innerHTML = progBars + lessonChip;
            }
        }

        // ── Card 5: Platform Tools Hub (replaces old Courses card) ─────────
        const coursesEl = document.getElementById('dash-courses-body');
        if (coursesEl) {
            const tier = (JSON.parse(localStorage.getItem('pipways_user') || '{}').subscription_tier) || 'free';
            const isPaid = tier === 'basic' || tier === 'pro';

            coursesEl.innerHTML = _buildToolsHub(isPaid);

            // Wire tool card clicks via event delegation (avoids any inline onclick quote issues)
            coursesEl.querySelectorAll('.pw-tool-card').forEach(function(card) {
                card.addEventListener('click', function() {
                    var href    = this.dataset.href;
                    var section = this.dataset.section;
                    if (href)    window.location.href = href;
                    else if (section) dashboard.navigate(section);
                });
                // Hover border effect
                var origBorder = card.style.borderColor;
                card.addEventListener('mouseenter', function() { this.style.opacity = '0.88'; });
                card.addEventListener('mouseleave',  function() { this.style.opacity = '1'; });
            });

            // Render chart analysis usage badge — deferred for PipwaysUsage timing
            var badgeEl = document.getElementById('dash-chart-usage');
            if (badgeEl) {
                var _renderToolBadge = function() {
                    if (typeof PipwaysUsage !== 'undefined') {
                        PipwaysUsage.renderBadge('chart_analysis', badgeEl);
                    }
                };
                if (typeof PipwaysUsage !== 'undefined' && PipwaysUsage.isLoaded) {
                    _renderToolBadge();
                } else {
                    setTimeout(_renderToolBadge, 1500);
                }
            }
        }

        // ── Card 3: Trading Academy Progress ────────────────────────────────
        const academyEl = document.getElementById('dash-academy-body');
        if (academyEl && progress) {
            const progressData = progress.levels || {
                beginner: { percentage: 0, completed: 0, total: 12 },
                intermediate: { percentage: 0, completed: 0, total: 8 },
                advanced: { percentage: 0, completed: 0, total: 8 }
            };

            academyEl.innerHTML = `
                <div class="space-y-3">
                    <!-- Beginner Level -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-lg flex items-center justify-center" style="background:rgba(52,211,153,.12);">
                                <i class="fas fa-seedling text-sm" style="color:#34d399;"></i>
                            </div>
                            <div>
                                <div class="text-sm font-medium text-white">Beginner</div>
                                <div class="text-xs text-gray-400">${progressData.beginner.completed}/${progressData.beginner.total} lessons</div>
                            </div>
                        </div>
                        <div class="text-right">
                            <div class="text-sm font-bold text-green-400">${Math.round(progressData.beginner.percentage || 0)}%</div>
                        </div>
                    </div>
                    
                    <!-- Intermediate Level -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-lg flex items-center justify-center" style="background:rgba(96,165,250,.12);">
                                <i class="fas fa-chart-line text-sm" style="color:#60a5fa;"></i>
                            </div>
                            <div>
                                <div class="text-sm font-medium text-white">Intermediate</div>
                                <div class="text-xs text-gray-400">${progressData.intermediate.completed}/${progressData.intermediate.total} lessons</div>
                            </div>
                        </div>
                        <div class="text-right">
                            <div class="text-sm font-bold text-blue-400">${Math.round(progressData.intermediate.percentage || 0)}%</div>
                        </div>
                    </div>
                    
                    <!-- Advanced Level -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-lg flex items-center justify-center" style="background:rgba(251,191,36,.12);">
                                <i class="fas fa-crown text-sm" style="color:#fbbf24;"></i>
                            </div>
                            <div>
                                <div class="text-sm font-medium text-white">Advanced</div>
                                <div class="text-xs text-gray-400">${progressData.advanced.completed}/${progressData.advanced.total} lessons</div>
                            </div>
                        </div>
                        <div class="text-right">
                            <div class="text-sm font-bold text-yellow-400">${Math.round(progressData.advanced.percentage || 0)}%</div>
                        </div>
                    </div>
                    
                    <!-- Continue Learning CTA -->
                    ${academyResume && academyResume.type !== 'complete' ? `
                    <div class="pt-2 border-t border-gray-700/50">
                        <a href="/academy" class="flex items-center justify-between p-3 rounded-lg transition-all" 
                           style="background:rgba(124,58,237,.08);border:1px solid rgba(124,58,237,.2);"
                           onmouseover="this.style.background='rgba(124,58,237,.12)'"
                           onmouseout="this.style.background='rgba(124,58,237,.08)'">
                            <div>
                                <div class="text-sm font-medium text-purple-300">Continue Learning</div>
                                <div class="text-xs text-gray-400">${academyResume.lesson_title || 'Pick up where you left off'}</div>
                            </div>
                            <i class="fas fa-arrow-right text-purple-400"></i>
                        </a>
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // ── AI Market Insight: show only for users ≥30% academy progress ──
        // Prevents confusing beginners with advanced market commentary
        const insightCard = document.getElementById('ai-insight-card');
        if (insightCard) {
            const completionRate = progress?.overall_progress || 0;
            if (completionRate >= 30) {
                insightCard.classList.remove('hidden');
            } else {
                insightCard.classList.add('hidden');
            }
        }

        // ── Perf card: restore from last journal upload if available ────────
        if (this.lastAnalysisResults) {
            this._updateDashPerfCard(this.lastAnalysisResults);
        }

        // ── Card 6: Latest Blog ───────────────────────────────────────────
        const blogEl = document.getElementById('dash-blog-body');
        if (blogEl) {
            const posts = Array.isArray(blog) ? blog : (blog?.posts || []);
            const list = posts.slice(0, 4);
            if (!list.length) {
                blogEl.innerHTML = `<div class="pw-empty" style="padding:2rem 1rem;">
                    <div class="pw-empty-icon" style="width:44px;height:44px;"><i class="fas fa-newspaper" style="color:#6b7280;"></i></div>
                    <p class="pw-empty-title">No articles yet</p>
                </div>`;
            } else {
                blogEl.innerHTML = `<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                ${list.map(p => {
                    const catColors = {'Market Analysis':'#60a5fa','Strategy':'#a78bfa','Education':'#34d399','General':'#9ca3af'};
                    const col = catColors[p.category] || '#9ca3af';
                    const date = p.created_at ? new Date(p.created_at).toLocaleDateString('en-GB',{day:'numeric',month:'short'}) : '';
                    return `
                    <div class="rounded-xl cursor-pointer transition-all duration-200 overflow-hidden"
                         style="border:1px solid #1f2937;background:#0d1321;"
                         onclick="dashboard.navigate('blog')"
                         onmouseover="this.style.borderColor='#374151';this.style.transform='translateY(-2px)'"
                         onmouseout="this.style.borderColor='#1f2937';this.style.transform=''">
                        <!-- Thumbnail — consistent height regardless of image presence -->
                        <div class="pw-blog-thumb">
                            ${p.featured_image
                                ? `<img src="${p.featured_image}" alt="${_e(p.title)}" onerror="this.parentElement.innerHTML='<div class=pw-blog-thumb-placeholder><i class=\"fas fa-newspaper text-xl\" style=\"color:${col};opacity:.4;\"></i></div>'">`
                                : `<div class="pw-blog-thumb-placeholder"><i class="fas fa-newspaper text-xl" style="color:${col};opacity:.4;"></i></div>`}
                            <div class="absolute bottom-0 left-0 right-0 px-3 py-1" style="background:linear-gradient(transparent,rgba(0,0,0,.6));">
                                <span class="text-xs font-bold" style="color:${col};">${_e(p.category||'General').toUpperCase()}</span>
                            </div>
                        </div>
                        <div class="p-3">
                            <div class="text-sm font-medium text-white line-clamp-2 mb-2 leading-snug">${_e(p.title)}</div>
                            <div class="text-xs text-gray-600">${date}</div>
                        </div>
                    </div>`;
                }).join('')}
                </div>`;
            }
        }
    }

    _updateNextStepCard(progress, courses, academyResume) {
        /**
         * Dynamically updates the "Your Next Step" card.
         * Prioritises Trading Academy data over old courses.
         */
        const titleEl = document.getElementById('next-step-title');
        const subEl   = document.getElementById('next-step-sub');
        const ctaEl   = document.getElementById('next-step-cta');
        if (!titleEl || !subEl || !ctaEl) return;

        if (academyResume && academyResume.type === 'continue' && academyResume.lesson_id) {
            // Actively in-progress in Academy
            const lessonTitle = academyResume.title  || 'Next Lesson';
            const moduleName  = academyResume.module || '';
            const levelName   = academyResume.level  || '';
            titleEl.textContent = `Resume: ${lessonTitle}`;
            subEl.textContent   = `${moduleName}${levelName ? ' · ' + levelName : ''}`;
            ctaEl.href          = `/academy?lesson=${academyResume.lesson_id}`;
            ctaEl.innerHTML     = '<i class="fas fa-play-circle text-xs"></i> Continue Lesson';
        } else if (academyResume && academyResume.type === 'complete') {
            titleEl.textContent = 'Academy Complete! 🏆';
            subEl.textContent   = 'All 28 lessons done. Review any module anytime.';
            ctaEl.href          = '/academy';
            ctaEl.innerHTML     = '<i class="fas fa-trophy text-xs"></i> View Academy';
        } else {
            // Not started or no academy data — prompt to begin
            titleEl.textContent = 'Start your Trading Academy';
            subEl.textContent   = '28 lessons · from first pip to institutional strategy';
            ctaEl.href          = '/academy';
            ctaEl.innerHTML     = '<i class="fas fa-graduation-cap text-xs"></i> Go to Academy';
        }
    }

    _setGreeting() {
        const h = new Date().getHours();
        const greet = h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
        const emoji = h < 12 ? '☀️' : h < 17 ? '📈' : '🌙';
        const subs = h < 12
            ? 'Upload a chart or check your Academy progress to start strong.'
            : h < 17
            ? 'Prime trading window — London–NY overlap is the highest probability session.'
            : 'Review your journal and plan tomorrow\'s setups.';
        const el   = document.getElementById('greeting-text');
        const sub  = document.getElementById('greeting-sub');
        const name = this.user?.full_name?.split(' ')[0] || 'Trader';
        if (el)  el.textContent  = `${greet}, ${name} ${emoji}`;
        if (sub) sub.textContent = subs;
        // Remove hidden class so greeting shows in new layout
        if (el)  el.classList.remove('hidden');
        if (sub) sub.classList.remove('hidden');
        // Set AI insight timestamp
        const tsEl = document.getElementById('insight-timestamp');
        if (tsEl) {
            const d = new Date();
            tsEl.textContent = d.toLocaleDateString('en-GB',{weekday:'short',day:'numeric',month:'short'});
        }
    }


    _initClock() {
        const tick = () => {
            const now    = new Date();
            const clockEl = document.getElementById('live-clock');
            if (clockEl) clockEl.textContent = now.toLocaleTimeString('en-US', { hour12: false });

            // ── Forex market hours: Sun 21:00 UTC – Fri 21:00 UTC ──────────
            const day   = now.getUTCDay();   // 0=Sun … 6=Sat
            const hours = now.getUTCHours();
            const mins  = now.getUTCMinutes();
            const timeInMins = hours * 60 + mins;
            // Open: Sunday 21:00 UTC onward, close: Friday 21:00 UTC
            const isOpen = !(day === 6 || (day === 5 && timeInMins >= 21*60) || (day === 0 && timeInMins < 21*60));

            // Update header pill status text
            const statusEl = document.getElementById('market-status-text');
            const dotEl    = document.getElementById('market-status-dot');
            if (statusEl) {
                statusEl.textContent = isOpen ? 'Markets Open' : 'Markets Closed';
                statusEl.className   = isOpen ? 'text-green-400 font-medium' : 'text-red-400 font-medium';
            }
            if (dotEl) {
                dotEl.style.background = isOpen ? '#4ade80' : '#f87171';
            }
            // Update dashboard greeting indicator
            const dashDot  = document.getElementById('dash-market-dot');
            const dashText = document.getElementById('dash-market-text');
            if (dashDot)  dashDot.style.background  = isOpen ? '#4ade80' : '#f87171';
            if (dashText) dashText.textContent = isOpen ? 'Markets Open' : 'Markets Closed';
            // Sync hero command center market dot
            const heroDot  = document.getElementById('hero-market-dot');
            const heroText = document.getElementById('hero-market-text');
            if (heroDot)  heroDot.style.background  = isOpen ? '#4ade80' : '#f87171';
            if (heroText) heroText.textContent = isOpen ? 'Markets Open' : 'Markets Closed';
        };
        tick();
        this._clockTimer = setInterval(tick, 1000);
    }

    _initTicker() {
        const pairs = [
            { sym: 'EUR/USD', price: '1.0847', chg: '+0.0012', pct: '+0.11%', up: true },
            { sym: 'GBP/USD', price: '1.2634', chg: '-0.0028', pct: '-0.22%', up: false },
            { sym: 'USD/JPY', price: '149.82', chg: '+0.34',   pct: '+0.23%', up: true  },
            { sym: 'XAU/USD', price: '3,024.5', chg: '+8.20',  pct: '+0.27%', up: true  },
            { sym: 'BTC/USD', price: '83,412',  chg: '-1,240', pct: '-1.47%', up: false },
            { sym: 'ETH/USD', price: '1,894.3', chg: '-32.1',  pct: '-1.67%', up: false },
            { sym: 'USD/CHF', price: '0.9021',  chg: '-0.0008',pct: '-0.09%', up: false },
            { sym: 'AUD/USD', price: '0.6341',  chg: '+0.0019',pct: '+0.30%', up: true  },
            { sym: 'NZD/USD', price: '0.5762',  chg: '+0.0011',pct: '+0.19%', up: true  },
            { sym: 'USD/CAD', price: '1.3892',  chg: '-0.0023',pct: '-0.17%', up: false },
            { sym: 'US30',    price: '41,850',  chg: '+120',   pct: '+0.29%', up: true  },
            { sym: 'US100',   price: '18,240',  chg: '-85',    pct: '-0.46%', up: false },
        ];

        // ── Top scrolling ticker ──────────────────────────────────────────
        const html = pairs.map(p => `
            <div class="ticker-item">
                <span class="ticker-sym">${p.sym}</span>
                <span class="ticker-price">${p.price}</span>
                <span class="${p.up ? 'ticker-up' : 'ticker-dn'}">${p.pct}</span>
            </div>`).join('');
        const track = document.getElementById('ticker-track');
        if (track) track.innerHTML = html + html;

        // ── Zone 3 forex snapshot card — populated from same data ─────────
        const fxEl = document.getElementById('dash-forex-tickers');
        if (fxEl) {
            // Show EUR/USD, GBP/USD, XAU/USD — most relevant for London session
            const featured = ['EUR/USD', 'GBP/USD', 'XAU/USD'];
            fxEl.innerHTML = featured.map((sym, i) => {
                const p = pairs.find(x => x.sym === sym);
                if (!p) return '';
                const isLast = i === featured.length - 1;
                const color = p.up ? '#34d399' : '#f87171';
                return `<div class="flex justify-between py-1.5 ${isLast ? '' : 'border-b'}" style="border-color:#1f2937;">
                    <div>
                        <span class="text-xs font-semibold" style="color:#e5e7eb;">${p.sym}</span>
                        <span class="text-xs ml-2" style="color:#4b5563;">${p.price}</span>
                    </div>
                    <span class="text-xs font-bold" data-base="${parseFloat(p.pct)}" style="color:${color};">${p.pct}</span>
                </div>`;
            }).join('');
            // Simulate live micro-drift every 6s so the card looks alive
            setInterval(() => {
                fxEl.querySelectorAll('[data-base]').forEach(el => {
                    const base = parseFloat(el.dataset.base) || 0;
                    const val  = base + (Math.random() - 0.5) * 0.06;
                    const up   = val >= 0;
                    el.textContent  = (up ? '+' : '') + val.toFixed(2) + '%';
                    el.style.color  = up ? '#34d399' : '#f87171';
                });
            }, 6000);
        }
    }


    async apiRequest(endpoint, options = {}) {
        const token = localStorage.getItem('pipways_token');
        const headers = {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        };
        if (options.body instanceof FormData) delete headers['Content-Type'];
        const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

        // 401 anywhere in the app → session expired, force re-login
        if (res.status === 401) {
            _handleAuthError();
            throw new Error('Session expired. Please log in again.');
        }

        if (!res.ok) {
            let msg = `HTTP ${res.status}`;
            try {
                const body = await res.json();
                if (body.detail) msg = body.detail;
                else if (body.message) msg = body.message;
                console.error(`[API] ${res.status} on ${endpoint}:`, body);
            } catch (_) {
                const text = await res.text().catch(() => '');
                console.error(`[API] ${res.status} on ${endpoint} (non-JSON):`, text.slice(0, 200));
            }
            throw new Error(msg);
        }

        return res.json();
    }

    setJournalFormat(format) {
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
    }

    setupJournalUpload() {
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
    }

    async handleJournalFile(file) {
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
                // Cache in localStorage + memory so AI Mentor can access it
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
    }

    _updateDashPerfCard(result) {
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
        <!-- Grade + Net P&L header -->
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

        <!-- 4-stat grid -->
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

        <!-- Mini discipline bar -->
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

        <!-- Mini performance chart placeholder -->
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
    }

    displayJournalAnalysis(result) {
        document.getElementById('performance-overview').classList.remove('hidden');
        document.getElementById('analytics-charts').classList.remove('hidden');
        document.getElementById('ai-coach-section').classList.remove('hidden');
        document.getElementById('trade-history').classList.remove('hidden');
        document.getElementById('strategy-detection').classList.remove('hidden');

        // ── Also refresh the dashboard performance card if it's visible ──
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
    }

    renderEquityCurve(equityData) {
        const ctx = document.getElementById('equity-curve-chart');
        if (!ctx) return;

        if (this.charts.equity) this.charts.equity.destroy();

        const labels = equityData.map(d => d.trade_number);
        const data = equityData.map(d => d.equity);

        this.charts.equity = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Equity',
                    data: data,
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { grid: { color: 'rgba(75, 85, 99, 0.3)' }, ticks: { color: '#9ca3af' } },
                    x: { display: false }
                }
            }
        });
    }

    renderTradeDistribution(distribution) {
        const ctx = document.getElementById('trade-distribution-chart');
        if (!ctx) return;

        if (this.charts.distribution) this.charts.distribution.destroy();

        this.charts.distribution = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Wins', 'Losses', 'Breakeven'],
                datasets: [{
                    data: [distribution.wins || 0, distribution.losses || 0, distribution.breakeven || 0],
                    backgroundColor: ['#10b981', '#ef4444', '#f59e0b'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#9ca3af', padding: 20 } }
                }
            }
        });
    }

    renderMonthlyPerformance(monthlyData) {
        const ctx = document.getElementById('monthly-performance-chart');
        if (!ctx) return;

        if (this.charts.monthly) this.charts.monthly.destroy();

        const labels = monthlyData.map(d => d.month);
        const data = monthlyData.map(d => d.pnl);
        const colors = data.map(v => v >= 0 ? '#10b981' : '#ef4444');

        this.charts.monthly = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'P&L',
                    data: data,
                    backgroundColor: colors,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { 
                        grid: { color: 'rgba(75, 85, 99, 0.3)' }, 
                        ticks: { color: '#9ca3af', callback: v => '$' + v }
                    },
                    x: { ticks: { color: '#9ca3af' }, grid: { display: false } }
                }
            }
        });
    }

    showManualEntry() {
        document.getElementById('manual-entry-form').classList.remove('hidden');
    }

    addManualTrade() {
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
            // Cache in localStorage so AI Mentor can access it
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
    }

    async loadSignals() {
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
    }

    async loadCourses() {
        // Courses section now redirects to Academy
        window.location.href = '/academy';
        return;
        // Legacy code below kept for reference
    }
    async _loadCoursesLegacy() {
        if (typeof PublicPages !== 'undefined') {
            await PublicPages.courses('courses-container', this);
            return;
        }
        const container = document.getElementById('courses-container');
        if (!container) return;
        if (typeof CoursesPage !== 'undefined') {
            await CoursesPage.render('courses-container');
            return;
        }
        container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500"><i class="fas fa-spinner fa-spin mr-2"></i>Loading courses…</div>';
        try {
            const data = await this.apiRequest('/courses/list');
            const courses = Array.isArray(data) ? data : (data.courses || []);
            if (!courses.length) {
                container.innerHTML = `<div class="col-span-full text-center py-12 text-gray-500">
                    <i class="fas fa-graduation-cap text-4xl mb-3 block opacity-30"></i>
                    <p class="font-medium">No courses available yet</p>
                </div>`;
                return;
            }
            container.innerHTML = courses.map(c => `
                <div class="bg-gray-800 rounded-xl overflow-hidden border border-gray-700 hover:border-blue-600/50 transition-colors cursor-pointer"
                     onclick="CoursesPage ? CoursesPage.openCourse(${c.id}) : null">
                    <div class="h-40 bg-gradient-to-br from-purple-900 to-blue-900 flex items-center justify-center">
                        <i class="fas fa-graduation-cap text-5xl text-white/20"></i>
                    </div>
                    <div class="p-4">
                        <span class="text-xs text-purple-400 font-semibold">${c.level || 'Beginner'}</span>
                        <h4 class="font-bold text-white mt-1 mb-2">${c.title}</h4>
                        <p class="text-sm text-gray-400 line-clamp-2 mb-2">${c.description || ''}</p>
                        <div class="text-xs text-gray-500">${c.lesson_count || 0} lessons</div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">Failed to load courses.</div>';
        }
    }

    async loadWebinars() {
        if (typeof PublicPages !== 'undefined') {
            await PublicPages.webinars('webinars-container', this);
            return;
        }
        const container = document.getElementById('webinars-container');
        if (!container) return;
        container.innerHTML = '<div class="text-center py-8 text-gray-500"><i class="fas fa-spinner fa-spin mr-2"></i>Loading webinars…</div>';
        try {
            const data = await this.apiRequest('/webinars/upcoming?upcoming=true');
            const webinars = Array.isArray(data) ? data : (data.webinars || []);
            if (!webinars.length) {
                container.innerHTML = `<div class="pw-empty">
                    <div class="pw-empty-icon"><i class="fas fa-video text-xl" style="color:#6b7280;"></i></div>
                    <p class="pw-empty-title">No webinars scheduled yet</p>
                    <p class="pw-empty-sub">Live sessions with expert traders are coming soon.</p>
                </div>`;
                return;
            }
            container.innerHTML = webinars.map(w => {
                const date = w.scheduled_at ? new Date(w.scheduled_at) : null;
                return `
                <div class="bg-gray-800 rounded-xl p-5 border border-gray-700 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 hover:border-yellow-600/40 transition-colors">
                    <div class="flex gap-4 items-start">
                        ${date ? `<div class="text-center min-w-[56px] bg-gray-700 rounded-lg p-2 flex-shrink-0">
                            <div class="text-2xl font-bold text-yellow-400">${date.getDate()}</div>
                            <div class="text-xs text-gray-400 uppercase">${date.toLocaleString('default',{month:'short'})}</div>
                        </div>` : ''}
                        <div>
                            <h4 class="font-bold text-white">${w.title}</h4>
                            <p class="text-sm text-gray-400 mt-0.5">${w.description || ''}</p>
                            <div class="text-xs text-gray-500 mt-1.5 flex gap-3 flex-wrap">
                                ${w.presenter ? `<span><i class="fas fa-user mr-1"></i>${w.presenter}</span>` : ''}
                                ${w.duration_minutes ? `<span><i class="fas fa-clock mr-1"></i>${w.duration_minutes} mins</span>` : ''}
                            </div>
                        </div>
                    </div>
                    ${w.meeting_link
                        ? `<a href="${w.meeting_link}" target="_blank" class="px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap flex-shrink-0 transition-colors" style="background:rgba(124,58,237,.2);color:#a78bfa;border:1px solid rgba(124,58,237,.3);">Join Now →</a>`
                        : `<span class="px-4 py-2 rounded-lg text-sm font-semibold text-gray-500 border border-gray-700 flex-shrink-0">Coming Soon</span>`}
                </div>`;
            }).join('');
        } catch (error) {
            container.innerHTML = '<div class="text-center py-8 text-gray-500">Failed to load webinars.</div>';
        }
    }

    async loadBlog() {
        if (typeof PublicPages !== 'undefined') {
            await PublicPages.blog('blog-container', this);
            return;
        }
        const container = document.getElementById('blog-container');
        if (!container) return;
        container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500"><i class="fas fa-spinner fa-spin mr-2"></i>Loading articles…</div>';
        try {
            const data = await this.apiRequest('/blog/posts');
            const posts = Array.isArray(data) ? data : (data.posts || []);
            if (!posts.length) {
                container.innerHTML = `<div class="col-span-full pw-empty">
                    <div class="pw-empty-icon"><i class="fas fa-newspaper text-xl" style="color:#6b7280;"></i></div>
                    <p class="pw-empty-title">No articles published yet</p>
                    <p class="pw-empty-sub">Market analysis and educational content is coming soon.</p>
                </div>`;
                return;
            }
            container.innerHTML = posts.map(p => `
                <article class="bg-gray-800 rounded-xl overflow-hidden border border-gray-700 hover:border-blue-600/40 transition-colors cursor-pointer group">
                    ${p.featured_image
                        ? `<img src="${p.featured_image}" class="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300" onerror="this.style.display='none'">`
                        : `<div class="h-48 bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center"><i class="fas fa-newspaper text-5xl text-white/20 group-hover:scale-110 transition-transform"></i></div>`}
                    <div class="p-4">
                        <div class="text-xs text-purple-400 font-semibold uppercase tracking-wide mb-1">${p.category || 'General'}</div>
                        <h4 class="font-bold text-white mb-2 group-hover:text-purple-300 transition-colors">${p.title}</h4>
                        <p class="text-sm text-gray-400 line-clamp-3 mb-3">${p.excerpt || ''}</p>
                        <div class="flex justify-between items-center text-xs text-gray-500">
                            <span>${p.created_at ? new Date(p.created_at).toLocaleDateString() : ''}</span>
                            <span class="text-purple-400">Read more →</span>
                        </div>
                    </div>
                </article>
            `).join('');
        } catch (error) {
            container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">Failed to load articles.</div>';
        }
    }

    async loadMentor() {
        await this.loadCoachInsights();
        this.loadMentorHistory();
    }

    async loadCoachInsights() {
        try {
            const data = await this.apiRequest('/ai/mentor/insights');

            document.getElementById('coach-insights-loading').classList.add('hidden');
            document.getElementById('coach-insights-content').classList.remove('hidden');

            document.getElementById('trading-personality').textContent = data.trading_personality || 'Developing Trader';

            document.getElementById('discipline-score').textContent = (data.discipline_score || 0) + '%';
            document.getElementById('consistency-score').textContent = (data.consistency_score || 0) + '%';

            const strengthsList = document.getElementById('ai-strengths-list');
            strengthsList.innerHTML = (data.strengths || []).map(s => `
                <li class="text-sm text-gray-300 flex items-start gap-2">
                    <span class="w-1.5 h-1.5 bg-green-400 rounded-full mt-1.5 flex-shrink-0"></span>
                    <span>${s}</span>
                </li>
            `).join('');

            const weaknessesList = document.getElementById('ai-weaknesses-list');
            weaknessesList.innerHTML = (data.weaknesses || []).map(w => `
                <li class="text-sm text-gray-300 flex items-start gap-2">
                    <span class="w-1.5 h-1.5 bg-yellow-400 rounded-full mt-1.5 flex-shrink-0"></span>
                    <span>${w}</span>
                </li>
            `).join('');

            document.getElementById('risk-profile').textContent = data.risk_profile || 'Moderate';

            const stepsList = document.getElementById('next-steps-list');
            stepsList.innerHTML = (data.recommended_next_steps || []).map(step => `
                <li class="flex items-start gap-2">
                    <span class="text-blue-400 mt-0.5">→</span>
                    <span>${step}</span>
                </li>
            `).join('');

            this.updateRecommendationsList(data.recommended_resources || []);

        } catch (e) {
            console.error('Failed to load coach insights:', e);
            document.getElementById('coach-insights-loading').innerHTML = 
                '<span class="text-gray-500">Upload journal to see insights</span>';
        }
    }

    updateRecommendationsList(resources) {
        // Sidebar panel removed — recommendations now show as cards below chat.
        // This method is kept as a no-op to avoid errors from existing call sites.
        return;
    }

    _updateRecommendationsList_legacy(resources) {
        const container = document.getElementById('recommendations-list');
        const countBadge = document.getElementById('rec-count');
        if (!container || !countBadge) return;  // panel removed, skip silently

        if (!resources || resources.length === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-500 text-sm py-4">
                    Ask the AI for personalized recommendations
                </div>
            `;
            countBadge.textContent = '0';
            return;
        }

        countBadge.textContent = resources.length;

        const icons = {
            'course': 'fa-graduation-cap text-purple-400',
            'blog': 'fa-newspaper text-blue-400',
            'signal': 'fa-satellite-dish text-green-400',
            'strategy': 'fa-chess text-yellow-400',
            'warning': 'fa-exclamation-triangle text-red-400'
        };

        container.innerHTML = resources.map(rec => `
            <div class="bg-gray-900/50 rounded-lg p-3 border border-gray-700 hover:border-purple-500/50 transition-colors cursor-pointer group">
                <div class="flex items-start gap-3">
                    <div class="mt-0.5">
                        <i class="fas ${icons[rec.type] || 'fa-lightbulb text-gray-400'}"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="text-sm font-medium text-white group-hover:text-purple-400 transition-colors truncate">${rec.title}</div>
                        ${rec.description ? `<div class="text-xs text-gray-400 mt-0.5 line-clamp-2">${rec.description}</div>` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    }

    loadMentorHistory() {
        try {
            const history = JSON.parse(localStorage.getItem('mentor_history') || '[]');
            const container = document.getElementById('mentor-messages');
            if (!container) return;

            if (history.length > 0) {
                // In-session history: restore full chat display
                container.innerHTML = '';
                history.forEach(msg => {
                    if (msg.role === 'user') {
                        this.appendMentorMessage(msg.content, 'user', false);
                    } else {
                        this.appendMentorMessage(msg.content, 'assistant', false);
                    }
                });
            } else {
                // Fresh load — check if there's a previous session summary
                const summaryRaw = localStorage.getItem('mentor_session_summary');
                if (summaryRaw) {
                    const summary = JSON.parse(summaryRaw);
                    const age = Date.now() - new Date(summary.saved_at).getTime();
                    if (age < 7 * 86400000 && summary.messages?.length > 0) {
                        // Show a subtle "context restored" notice — clean UI but user knows
                        const lastUserMsg = summary.messages.filter(m => m.role === 'user').pop();
                        const notice = document.createElement('div');
                        notice.className = 'flex justify-center mb-3';
                        notice.innerHTML = `
                            <div class="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs"
                                 style="background:rgba(124,58,237,.1);border:1px solid rgba(124,58,237,.2);color:#a78bfa;">
                                <i class="fas fa-history" style="font-size:.65rem;"></i>
                                Previous session context loaded
                                ${lastUserMsg ? `· Last: "${lastUserMsg.content.slice(0, 40)}${lastUserMsg.content.length > 40 ? '…' : ''}"` : ''}
                            </div>`;
                        container.innerHTML = '';
                        container.appendChild(notice);
                        // Append welcome message after the notice
                        const welcome = document.createElement('div');
                        welcome.className = 'flex gap-3 animate-fade-in';
                        welcome.innerHTML = `
                            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                                <i class="fas fa-robot text-xs text-white"></i>
                            </div>
                            <div class="bg-gray-800 p-4 rounded-2xl rounded-tl-none border border-gray-700" style="max-width:85%;">
                                <div class="mentor-prose">Welcome back! I remember our last conversation. What would you like to work on today?</div>
                            </div>`;
                        container.appendChild(welcome);
                    }
                }
            }
        } catch (e) {
            console.error('Error loading mentor history:', e);
        }
    }

    saveMentorHistory() {
        try {
            const container = document.getElementById('mentor-messages');
            if (!container) return;

            const messages = [];
            container.querySelectorAll('.message-wrapper').forEach(el => {
                const role = el.dataset.role;
                const content = el.dataset.content;
                if (role && content) {
                    messages.push({role, content, timestamp: new Date().toISOString()});
                }
            });

            // Keep last 20 messages for display history
            const trimmed = messages.slice(-20);
            localStorage.setItem('mentor_history', JSON.stringify(trimmed));

            // Also save a compact summary of last 6 exchanges for cross-session context
            // This gives the AI context even after a refresh without loading full history
            const summary = messages.slice(-6).map(m => ({
                role: m.role,
                content: m.content.slice(0, 300) // truncate long responses
            }));
            localStorage.setItem('mentor_session_summary', JSON.stringify({
                saved_at: new Date().toISOString(),
                messages: summary
            }));
        } catch (e) {
            console.error('Error saving mentor history:', e);
        }
    }

    // ── Get conversation history from localStorage for memory ──────────────
    _getMentorHistory() {
        try {
            const raw = JSON.parse(localStorage.getItem('mentor_history') || '[]');
            if (raw.length > 0) {
                // In-session history — use last 16 messages
                return raw.slice(-16).map(m => ({
                    role: m.role === 'user' ? 'user' : 'assistant',
                    content: (m.content || '').slice(0, 800)
                }));
            }
            // No in-session history (fresh page load) — use cross-session summary
            // This gives the AI context of the last conversation silently
            const summaryRaw = localStorage.getItem('mentor_session_summary');
            if (!summaryRaw) return [];
            const summary = JSON.parse(summaryRaw);
            // Only use if from last 7 days
            const age = Date.now() - new Date(summary.saved_at).getTime();
            if (age > 7 * 86400000) return [];
            return (summary.messages || []).map(m => ({
                role: m.role === 'user' ? 'user' : 'assistant',
                content: m.content
            }));
        } catch (_) { return []; }
    }

    // ── Get cached performance data to send with mentor request ─────────────
    _getCachedPerformance() {
        try {
            // Use in-memory cache first (loaded at startup)
            if (this._cachedPerformance) {
                const age = Date.now() - this._cachedPerformance.cached_at;
                if (age < 86400000) return this._cachedPerformance; // < 24 hours
            }
            // Fallback: read from localStorage
            const raw = localStorage.getItem('pipways_performance');
            if (!raw) return null;
            const data = JSON.parse(raw);
            if (Date.now() - data.cached_at > 86400000) return null;
            this._cachedPerformance = data; // store in memory
            return data;
        } catch (_) { return null; }
    }

    // ── Slash command local preview — show what the command does instantly ──
    _getSlashPreview(cmd) {
        const previews = {
            '/signals':       '📡 Fetching active signals and asking mentor to analyse them…',
            '/review-trades': '📊 Pulling your performance data for AI review…',
            '/strategy':      '🎯 Checking your strategy readiness based on your progress…',
            '/next':          '📚 Finding your recommended next learning step…',
            '/progress':      '📈 Generating your full progress breakdown…',
            '/help':          null  // handled inline
        };
        return previews[cmd.toLowerCase()] || null;
    }

    async sendMentorMessage() {
        const input = document.getElementById('mentor-input');
        const message = input.value.trim();
        if (!message) return;

        // ── Slash command: /help handled entirely client-side ──────────────
        if (message.toLowerCase() === '/help') {
            input.value = '';
            this.appendMentorMessage('/help', 'user');
            this.appendMentorMessage(
                `**Available commands:**
` +
                `• \`/signals\` — Analyse active market signals
` +
                `• \`/review-trades\` — Review your performance stats
` +
                `• \`/strategy\` — Check your strategy readiness
` +
                `• \`/next\` — What to learn next
` +
                `• \`/progress\` — Full progress breakdown

` +
                `Or just ask me anything about trading!`,
                'assistant'
            );
            return;
        }

        this.appendMentorMessage(message, 'user');
        input.value = '';

        // Show slash command preview while waiting
        const preview = this._getSlashPreview(message);
        if (preview) {
            const previewEl = document.getElementById('mentor-typing');
            const span = previewEl?.querySelector('span');
            if (span) span.textContent = preview;
        }

        document.getElementById('mentor-typing').classList.remove('hidden');
        this._hideMentorRecommendations();

        // Get conversation history for memory
        const history = this._getMentorHistory();

        try {
            // Attach cached performance data directly — no backend fetch needed
            const cachedPerf = this._getCachedPerformance();

            const response = await this.apiRequest('/ai/mentor/ask', {
                method: 'POST',
                body: JSON.stringify({
                    message: message,
                    question: message,
                    skill_level: 'intermediate',
                    include_platform_context: true,
                    conversation_history: history,       // ← memory
                    cached_performance: cachedPerf       // ← performance data from localStorage
                })
            });

            document.getElementById('mentor-typing').classList.add('hidden');
            // Restore default typing text
            const span = document.getElementById('mentor-typing')?.querySelector('span');
            if (span) span.textContent = 'AI is analyzing your data...';

            if (!response || typeof response !== 'object') {
                throw new Error('Invalid response format from mentor API');
            }

            const replyText = response.response || response.message || response.answer || '';
            await this.typeMentorResponse(replyText || 'I received your message but had trouble generating a response. Please try again.');

            const recs = response.recommendations || response.suggested_resources || [];
            console.log(`[Mentor] ${recs.length} recommendation(s):`, recs);
            if (recs.length > 0) {
                this._renderMentorLessonCards(recs);
                this.updateRecommendationsList(recs);
            }

            this.saveMentorHistory();

        } catch (e) {
            document.getElementById('mentor-typing').classList.add('hidden');
            console.error('[Mentor] sendMentorMessage error:', e);
            this.appendMentorMessage('Sorry, I encountered an error. Please try again.', 'error');
        }
    }

    // ── Hides the lesson recommendations panel ──────────────────────────────
    _hideMentorRecommendations() {
        const panel = document.getElementById('mentor-recommendations');
        if (panel) panel.classList.add('hidden');
    }

    // ── Renders lesson cards inside the chat column ─────────────────────────
    _renderMentorLessonCards(recommendations) {
        const panel = document.getElementById('mentor-recommendations');
        const grid  = document.getElementById('mentor-rec-grid');
        const count = document.getElementById('mentor-rec-count');
        if (!panel || !grid) {
            console.warn('[Mentor] #mentor-recommendations or #mentor-rec-grid not found');
            return;
        }

        grid.innerHTML = '';
        if (count) count.textContent = recommendations.length;

        const typeIcons = {
            course:   { icon: 'fa-graduation-cap', col: '#a78bfa', bg: 'rgba(167,139,250,.15)' },
            lesson:   { icon: 'fa-play-circle',    col: '#a78bfa', bg: 'rgba(167,139,250,.15)' },
            blog:     { icon: 'fa-newspaper',       col: '#2dd4bf', bg: 'rgba(45,212,191,.15)'  },
            strategy: { icon: 'fa-chess',           col: '#fbbf24', bg: 'rgba(251,191,36,.15)'  },
            default:  { icon: 'fa-lightbulb',       col: '#60a5fa', bg: 'rgba(96,165,250,.15)'  }
        };

        recommendations.forEach(rec => {
            const lessonId = rec.metadata?.lesson_id || rec.id || null;
            const url      = rec.url || null;
            const t        = typeIcons[rec.type] || typeIcons.default;
            const isStatic = rec.metadata?.static === true;

            // Build absolute URL — priority: explicit url with ?lesson= > lesson_id > academy homepage
            const _base = window.location.origin;
            let dest;
            if (url && url.includes('?lesson=')) {
                // Has specific lesson ID in URL — use it directly (best case)
                dest = url.startsWith('http') ? url : _base + url;
            } else if (lessonId) {
                // Has lesson_id in metadata — build specific URL
                dest = `${_base}/academy.html?lesson=${lessonId}`;
            } else if (url) {
                // Has URL but no lesson ID (fallback cards) — use URL as-is
                dest = url.startsWith('http') ? url : _base + url;
            } else {
                // No URL at all — go to academy homepage
                dest = `${_base}/academy.html`;
            }

            console.log(`[Mentor Rec] "${rec.title}" → ${dest} (lessonId=${lessonId}, url=${url})`);

            const card = document.createElement('div');
            card.className = 'cursor-pointer rounded-xl p-3 transition-all duration-200';
            card.style.cssText = 'background:#111827;border:1px solid #1f2937;';
            card.onmouseover = () => { card.style.borderColor = '#7c3aed'; card.style.background = 'rgba(124,58,237,.08)'; };
            card.onmouseout  = () => { card.style.borderColor = '#1f2937'; card.style.background = '#111827'; };

            // Label for CTA button — show "Open Academy" for fallback cards, "Start Lesson" for specific ones
            const ctaLabel = (lessonId || (url && url.includes('?lesson=')))
                ? 'Start Lesson'
                : 'Open Academy';
            const ctaIcon = lessonId || (url && url.includes('?lesson='))
                ? 'fa-play-circle'
                : 'fa-graduation-cap';

            card.innerHTML = `
                <div class="flex items-start gap-3">
                    <div class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                         style="background:${t.bg};">
                        <i class="fas ${t.icon} text-sm" aria-hidden="true" style="color:${t.col};"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="text-sm font-semibold text-white truncate mb-0.5">${this._escapeHtml(rec.title)}</div>
                        ${rec.description ? `<div class="text-xs mb-2" style="color:#9ca3af;line-height:1.4;">${this._escapeHtml(rec.description)}</div>` : ''}
                        <button class="text-xs font-semibold flex items-center gap-1 px-2.5 py-1.5 rounded-lg transition-all"
                                style="background:${t.bg};color:${t.col};border:1px solid ${t.col}33;"
                                onclick="event.stopPropagation(); window.location.href='${dest}';">
                            <i class="fas ${ctaIcon}" aria-hidden="true" style="font-size:.7rem;"></i>
                            &nbsp;${ctaLabel}&nbsp;<i class="fas fa-arrow-right" aria-hidden="true" style="font-size:.5rem;"></i>
                        </button>
                    </div>
                </div>`;

            card.addEventListener('click', () => { window.location.href = dest; });
            grid.appendChild(card);
        });

        panel.classList.remove('hidden');

        // Scroll chat to show the new cards
        const msgs = document.getElementById('mentor-messages');
        if (msgs) setTimeout(() => msgs.scrollTo({ top: msgs.scrollHeight, behavior: 'smooth' }), 100);
    }

    // ── Tracks lesson click and navigates to the specific lesson ───────────
    async _handleMentorLessonClick(lessonId, url) {
        // Track click (fire-and-forget — don't block navigation)
        if (lessonId) {
            this.apiRequest('/ai/mentor/track-lesson-click', {
                method: 'POST',
                body: JSON.stringify({ lesson_id: String(lessonId) })
            }).catch(e => console.warn('[Mentor] Lesson click tracking failed:', e));
        }

        // Build absolute URL to guarantee correct navigation across all paths
        const _origin = window.location.origin;
        const destination = url
            ? (url.startsWith('http') ? url : _origin + url)
            : (lessonId ? `${_origin}/academy.html?lesson=${lessonId}` : `${_origin}/academy.html`);

        console.log('[Mentor] Navigating to lesson:', destination);
        window.location.href = destination;
    }

    // ── Safe HTML escape for card content ───────────────────────────────────
    _escapeHtml(str) {
        const d = document.createElement('div');
        d.textContent = str || '';
        return d.innerHTML;
    }

    async askMentor(question) {
        const input = document.getElementById('mentor-input');
        input.value = question;
        await this.sendMentorMessage();
    }

    appendMentorMessage(text, sender, animate = true) {
        const container = document.getElementById('mentor-messages');
        if (!container) return;

        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper flex gap-3 ${animate ? 'animate-fade-in' : ''}`;
        wrapper.dataset.role = sender;
        wrapper.dataset.content = text;

        if (sender === 'user') {
            wrapper.classList.add('flex-row-reverse');
            wrapper.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-user text-xs text-white"></i>
                </div>
                <div class="bg-purple-600 p-3 rounded-2xl rounded-tr-none max-w-[80%]">
                    <p class="text-white text-sm">${text}</p>
                </div>
            `;
        } else if (sender === 'error') {
            wrapper.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-red-900 flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-exclamation text-xs text-red-400"></i>
                </div>
                <div class="bg-red-900/30 border border-red-700/50 p-3 rounded-2xl rounded-tl-none max-w-[80%]">
                    <p class="text-red-200 text-sm">${text}</p>
                </div>
            `;
        } else {
            const rendered = window._renderMd ? window._renderMd(text) : text;
            wrapper.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-1">
                    <i class="fas fa-robot text-xs text-white"></i>
                </div>
                <div class="bg-gray-800 p-4 rounded-2xl rounded-tl-none border border-gray-700" style="max-width:85%;">
                    <div class="mentor-prose">${rendered}</div>
                </div>
            `;
        }

        container.appendChild(wrapper);
        container.scrollTop = container.scrollHeight;
    }

    async typeMentorResponse(text) {
        const container = document.getElementById('mentor-messages');
        if (!container) return;

        const wrapper = document.createElement('div');
        wrapper.className = 'message-wrapper flex gap-3 animate-fade-in';
        wrapper.dataset.role = 'assistant';
        wrapper.dataset.content = text;

        // Start with a typing indicator inside the bubble
        wrapper.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-1">
                <i class="fas fa-robot text-xs text-white"></i>
            </div>
            <div class="bg-gray-800 p-4 rounded-2xl rounded-tl-none border border-gray-700" style="max-width:85%;">
                <div class="mentor-prose typing-content"></div>
            </div>
        `;

        container.appendChild(wrapper);
        container.scrollTop = container.scrollHeight;

        const contentEl = wrapper.querySelector('.typing-content');

        // Stream word by word as plain text first (fast — 20ms/word)
        const words = text.split(' ');
        let currentText = '';
        for (let i = 0; i < words.length; i++) {
            currentText += (i > 0 ? ' ' : '') + words[i];
            contentEl.textContent = currentText;
            container.scrollTop = container.scrollHeight;
            // Speed: fast for short messages, skip animation for long ones
            if (words.length < 80) {
                await new Promise(r => setTimeout(r, 18));
            }
        }

        // Render final markdown after typing completes
        contentEl.innerHTML = window._renderMd ? window._renderMd(text) : text;

        container.scrollTop = container.scrollHeight;
        wrapper.dataset.content = text;
    }

    toggleMentorHelp() {
        const panel = document.getElementById('mentor-help-panel');
        panel.classList.toggle('hidden');
    }

    clearMentorChat() {
        if (confirm('Clear conversation history?')) {
            localStorage.removeItem('mentor_history');
            this._toast('Conversation history cleared', 'info');
            const container = document.getElementById('mentor-messages');
            if (container) {
                container.innerHTML = `
                    <div class="flex gap-3 animate-fade-in">
                        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                            <i class="fas fa-robot text-xs text-white"></i>
                        </div>
                        <div class="bg-gray-700 p-4 rounded-2xl rounded-tl-none max-w-[85%] border border-gray-600">
                            <p class="text-gray-200 text-sm">Chat history cleared. How can I help you today?</p>
                        </div>
                    </div>
                `;
            }
            // Also hide lesson recommendation cards
            this._hideMentorRecommendations();
        }
    }

    // ── Micro-UX helpers — REC: stacked toasts with vertical offset ────────
    _toast(message, type = 'success', duration = 3200) {
        const icons = { success:'fa-check-circle', error:'fa-exclamation-circle', info:'fa-info-circle', warning:'fa-exclamation-triangle' };
        const t = document.createElement('div');
        t.className = `pw-toast ${type}`;
        t.setAttribute('role', 'alert');
        t.setAttribute('aria-live', 'assertive');
        t.setAttribute('aria-atomic', 'true');
        t.innerHTML = `<i class="fas ${icons[type]||icons.info} text-sm flex-shrink-0"></i><span>${message}</span>`;
        // Offset above any existing toasts so they stack cleanly
        const existing = document.querySelectorAll('.pw-toast');
        const BASE = 24;   // 1.5rem in px
        const HEIGHT = 56; // approximate toast height + gap
        t.style.bottom = `${BASE + existing.length * HEIGHT}px`;
        document.body.appendChild(t);
        setTimeout(() => {
            t.style.animation = 'toast-out .3s ease-in both';
            setTimeout(() => {
                t.remove();
                // Re-stack remaining toasts
                document.querySelectorAll('.pw-toast').forEach((el, i) => {
                    el.style.bottom = `${BASE + i * HEIGHT}px`;
                });
            }, 320);
        }, duration);
    }

    _toggleNotifPanel() {
        const panel = document.getElementById('notif-panel');
        const dot   = document.getElementById('notif-dot');
        if (!panel) return;
        const isHidden = panel.classList.contains('hidden');
        panel.classList.toggle('hidden');
        // Dismiss red dot once opened
        if (isHidden && dot) dot.style.display = 'none';
        // Update aria-expanded on the trigger button
        const notifTrigger = document.getElementById('notif-btn');
        if (notifTrigger) notifTrigger.setAttribute('aria-expanded', String(isHidden));
        // Close on click outside
        if (isHidden) {
            const close = (e) => {
                if (!document.getElementById('notif-wrapper')?.contains(e.target)) {
                    panel.classList.add('hidden');
                    document.removeEventListener('click', close);
                }
            };
            setTimeout(() => document.addEventListener('click', close), 50);
        }
    }


    logout() {
        localStorage.removeItem('pipways_token');
        localStorage.removeItem('pipways_user');
        window.location.href = '/';
    }
};

// FIX: API shim defined AFTER dashboard is instantiated.
const dashboard = new DashboardController();
// Expose on window so external module scripts can access them.
window.dashboard = dashboard;

const API = {
    request(endpoint, opts = {}) {
        return dashboard.apiRequest(endpoint, opts);
    }
};
window.API = API;
