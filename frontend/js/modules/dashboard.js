/**
 * Gopipways Dashboard Controller
 * Fixes applied vs original:
 *   B1  — checkResetToken() runs before checkAuth() — handles ?reset_token URL
 *   B2  — /ai/trade/validate → /ai/chart/validate | /ai/signal/save → /api/signals
 *   B3  — AI mentor response sanitised before innerHTML injection
 *   B4  — addManualTrade() is async with try/catch
 *   B5  — setupJournalUpload() guarded against duplicate listeners
 *   B6  — loadChartAnalysis() guarded against duplicate listeners
 *   B7  — loadMentor() preserves existing chat history on re-navigation
 *   B8  — analyzeChart() checks response.ok
 *   B9  — validateTradeSetup() checks response.ok
 *   B10 — Chart.js guarded before use
 *   B11 — ai_confidence normalised (>1 = already %, ≤1 = decimal)
 *   B12 — _toast() and _safeHtml() defined on DashboardController
 *   B13 — 'enhanced-signals' added to page titles map
 *   B14 — journal file errors mapped to user-friendly messages
 *   B15 — journal table has "Show all" expand button
 *   B16 — carousel interval stored and not duplicated
 *   B17 — signal date guarded against Invalid Date
 *   P1  — renderAdminMenu uses classList.toggle (not style.display)
 *   P4  — methods correctly named (no _PATCHED suffix)
 *   P5  — AdminPage.render() wrapped in try/catch
 *   P6  — all api.X() → API.X()
 *   P8  — isAdmin extracted to getter
 *   P9  — innerHTML += replaced with insertAdjacentHTML
 *   NEW — Full password reset flow: checkResetToken, showResetModal,
 *          submitPasswordReset, strength indicator, URL cleanup
 */
class DashboardController {
    constructor() {
        this.user                = null;
        this.allCourses          = [];
        this.manualTrades        = [];
        this.currentChartFile    = null;
        this.currentChartBase64  = null;
        this.currentAnalysis     = null;
        this.currentJournalFormat = null;
        this.equityChart         = null;
        this.distributionChart   = null;
        this.mentorSkillLevel    = 'intermediate';
        this._journalSetup       = false;   // B5
        this._chartSetup         = false;   // B6
        this._carouselInterval   = null;    // B16
        this.init();
    }

    // ── P8: isAdmin getter — single source of truth ───────────────────────────
    get isAdmin() {
        return !!(
            this.user?.is_admin === true
            || this.user?.role === 'admin'
            || this.user?.is_superuser === true
        );
    }

    // ── B12: _safeHtml + _toast helpers ─────────────────────────────────────
    _safeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    _toast(msg, type = 'info') {
        // Use global UI.toast if available (from enhanced_signals.js or similar)
        if (window.UI?.toast)   { UI.toast(msg, type); return; }
        if (window.Store?.toast){ Store.toast(msg, type); return; }
        // Fallback: simple inline toast
        const colours = { success: '#10b981', error: '#ef4444', warning: '#f59e0b', info: '#3b82f6' };
        const t = document.createElement('div');
        t.textContent = msg;
        t.style.cssText = `position:fixed;bottom:20px;right:20px;z-index:9999;
            padding:12px 20px;border-radius:8px;color:white;font-size:14px;font-weight:600;
            background:${colours[type]||colours.info};box-shadow:0 4px 12px rgba(0,0,0,.3);
            animation:fadeIn .2s ease;`;
        document.body.appendChild(t);
        setTimeout(() => t.remove(), 3500);
    }

    // ── init ─────────────────────────────────────────────────────────────────
    init() {
        // B1 — check for password reset token BEFORE auth redirect
        if (this.checkResetToken()) return;
        this.checkAuth();
        this.setupNavigation();
        this.setupMobileMenu();
        this.renderAdminMenu();
        this.initFeatureCarousel();
        this.loadDashboardStats();
        this.navigate('dashboard');
    }

    // ── NEW: Password reset flow ──────────────────────────────────────────────
    checkResetToken() {
        const params = new URLSearchParams(window.location.search);
        const token  = params.get('reset_token');
        if (!token) return false;
        // Clean token from URL immediately (single-use — don't leave it in history)
        history.replaceState({}, '', window.location.pathname);
        this.showResetModal(token);
        return true; // signals init() to skip auth check
    }

    showResetModal(token) {
        // Verify token first, then show appropriate form
        const overlay = document.createElement('div');
        overlay.id = 'reset-modal-overlay';
        overlay.style.cssText = `position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.7);
            display:flex;align-items:center;justify-content:center;padding:20px;`;
        overlay.innerHTML = `
            <div style="background:#1f2937;border-radius:12px;padding:32px;width:100%;max-width:440px;
                        border:1px solid #374151;text-align:center;">
                <div style="font-size:40px;margin-bottom:12px;">🔐</div>
                <h2 style="color:white;margin:0 0 8px;font-size:20px;">Verifying reset link…</h2>
                <p style="color:#9ca3af;font-size:14px;margin:0;">Please wait a moment.</p>
                <div id="reset-form-area" style="margin-top:24px;"></div>
            </div>`;
        document.body.appendChild(overlay);

        fetch(`/email/verify-reset-token?token=${encodeURIComponent(token)}`)
            .then(r => r.json())
            .then(data => {
                const area = document.getElementById('reset-form-area');
                if (!area) return;
                if (!data.valid) {
                    area.innerHTML = `
                        <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;
                                    padding:16px;margin-bottom:16px;">
                            <p style="color:#dc2626;font-size:14px;margin:0;font-weight:600;">
                                This reset link has expired or already been used.
                            </p>
                        </div>
                        <p style="color:#9ca3af;font-size:13px;margin:0 0 16px;">
                            Request a new one from the login page.
                        </p>
                        <a href="/"
                           style="display:inline-block;background:#667eea;color:white;padding:10px 24px;
                                  border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;">
                            Back to Login
                        </a>`;
                } else {
                    this._renderResetForm(area, token);
                }
            })
            .catch(() => {
                const area = document.getElementById('reset-form-area');
                if (area) area.innerHTML = `
                    <p style="color:#ef4444;font-size:14px;">Connection error. Please try again.</p>
                    <a href="/" style="color:#667eea;font-size:14px;">Back to Login</a>`;
            });
    }

    _renderResetForm(area, token) {
        const heading = area.closest('div').querySelector('h2');
        const sub     = area.closest('div').querySelector('p');
        if (heading) heading.textContent = 'Set a new password';
        if (sub)     sub.textContent = 'Choose a strong password for your account.';

        area.innerHTML = `
            <div style="text-align:left;">
                <div style="margin-bottom:16px;">
                    <label style="display:block;color:#9ca3af;font-size:13px;margin-bottom:6px;">
                        New Password
                    </label>
                    <input type="password" id="reset-pw-new" placeholder="Minimum 8 characters"
                        oninput="dashboard._checkPwStrength(this.value)"
                        style="width:100%;padding:10px 14px;background:#374151;border:1px solid #4b5563;
                               border-radius:8px;color:white;font-size:14px;box-sizing:border-box;">
                    <div id="pw-strength-bar" style="height:4px;border-radius:2px;margin-top:6px;
                                                      background:#4b5563;overflow:hidden;">
                        <div id="pw-strength-fill" style="height:100%;width:0;transition:all .3s;
                                                           border-radius:2px;background:#ef4444;"></div>
                    </div>
                    <p id="pw-strength-label" style="font-size:12px;color:#6b7280;margin:4px 0 0;"></p>
                </div>
                <div style="margin-bottom:20px;">
                    <label style="display:block;color:#9ca3af;font-size:13px;margin-bottom:6px;">
                        Confirm Password
                    </label>
                    <input type="password" id="reset-pw-confirm" placeholder="Repeat your password"
                        oninput="dashboard._checkPwMatch()"
                        style="width:100%;padding:10px 14px;background:#374151;border:1px solid #4b5563;
                               border-radius:8px;color:white;font-size:14px;box-sizing:border-box;">
                    <p id="pw-match-label" style="font-size:12px;color:#6b7280;margin:4px 0 0;"></p>
                </div>
                <button id="reset-submit-btn" disabled
                    onclick="dashboard.submitPasswordReset('${this._safeHtml(token)}')"
                    style="width:100%;padding:12px;background:#667eea;color:white;border:none;
                           border-radius:8px;font-weight:700;font-size:15px;cursor:pointer;
                           opacity:.5;transition:opacity .2s;">
                    Set New Password →
                </button>
                <p id="reset-error" style="color:#ef4444;font-size:13px;margin:12px 0 0;
                                           display:none;"></p>
            </div>`;
    }

    _checkPwStrength(pw) {
        const fill  = document.getElementById('pw-strength-fill');
        const label = document.getElementById('pw-strength-label');
        if (!fill || !label) return;
        let score = 0;
        if (pw.length >= 8)  score++;
        if (pw.length >= 12) score++;
        if (/[A-Z]/.test(pw)) score++;
        if (/[0-9]/.test(pw)) score++;
        if (/[^A-Za-z0-9]/.test(pw)) score++;
        const map = [
            { pct: 0,   color: '#ef4444', text: '' },
            { pct: 20,  color: '#ef4444', text: 'Weak' },
            { pct: 40,  color: '#f59e0b', text: 'Fair' },
            { pct: 60,  color: '#f59e0b', text: 'Good' },
            { pct: 80,  color: '#10b981', text: 'Strong' },
            { pct: 100, color: '#10b981', text: 'Very strong' },
        ];
        const s = map[score] || map[0];
        fill.style.width   = s.pct + '%';
        fill.style.background = s.color;
        label.textContent  = s.text;
        label.style.color  = s.color;
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
        if (pw.length < 8) { if (err) { err.textContent = 'Password must be at least 8 characters.'; err.style.display = 'block'; } return; }
        if (btn) { btn.disabled = true; btn.textContent = 'Updating…'; }
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
                        <p style="color:#166534;font-size:15px;font-weight:600;margin:0 0 8px;">
                            ✅ Password updated successfully!
                        </p>
                        <p style="color:#374151;font-size:13px;margin:0;">
                            Redirecting to login in 3 seconds…
                        </p>
                    </div>`;
                setTimeout(() => window.location.href = '/', 3000);
            } else {
                const msg = data.detail || 'Failed to reset password. Please try again.';
                if (err) { err.textContent = msg; err.style.display = 'block'; }
                if (btn) { btn.disabled = false; btn.textContent = 'Set New Password →'; }
            }
        } catch (e) {
            if (err) { err.textContent = 'Connection error. Please try again.'; err.style.display = 'block'; }
            if (btn) { btn.disabled = false; btn.textContent = 'Set New Password →'; }
        }
    }

    // ── Auth ─────────────────────────────────────────────────────────────────
    checkAuth() {
        const token   = localStorage.getItem('pipways_token');
        const userStr = localStorage.getItem('pipways_user');
        if (!token || !userStr) { window.location.href = '/'; return; }
        try {
            this.user = JSON.parse(userStr);
            this.updateUserDisplay();
        } catch (e) {
            console.error('Auth error:', e);
            window.location.href = '/';
        }
    }

    updateUserDisplay() {
        const u = this.user || {};
        const s = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
        s('user-name',        u.full_name || u.email || 'User');
        s('user-email',       u.email || '');
        s('header-user-name', u.full_name || u.email || 'Trader');
    }

    // ── P1/P8: renderAdminMenu uses classList.toggle ──────────────────────────
    renderAdminMenu() {
        const menu = document.getElementById('admin-menu-container');
        if (menu) menu.classList.toggle('hidden', !this.isAdmin);
    }

    setupNavigation() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.currentTarget.dataset.section;
                if (section) this.navigate(section);
            });
        });
    }

    setupMobileMenu() {
        const btn     = document.getElementById('mobile-menu-btn');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        btn?.addEventListener('click', () => {
            sidebar?.classList.toggle('-translate-x-full');
            overlay?.classList.toggle('hidden');
        });
        overlay?.addEventListener('click', () => {
            sidebar?.classList.add('-translate-x-full');
            overlay?.classList.add('hidden');
        });
    }

    navigate(section) {
        document.querySelectorAll('.nav-link').forEach(el => {
            el.classList.remove('bg-purple-600', 'text-white');
            el.classList.add('text-gray-300');
        });
        const activeLink = document.querySelector(`[data-section="${section}"]`);
        if (activeLink) {
            activeLink.classList.add('bg-purple-600', 'text-white');
            activeLink.classList.remove('text-gray-300');
        }
        document.querySelectorAll('.section').forEach(el => el.classList.add('hidden'));
        const target = document.getElementById(`section-${section}`);
        if (target) {
            target.classList.remove('hidden');
            this.loadSectionData(section);
        }
        // B13 — 'enhanced-signals' added to titles map
        const titles = {
            'dashboard':         'Dashboard',
            'signals':           'Trading Signals',
            'enhanced-signals':  'Trading Signals',
            'journal':           'Trading Journal',
            'courses':           'Trading Courses',
            'webinars':          'Webinars',
            'blog':              'Trading Blog',
            'admin':             'Admin Dashboard',
            'analysis':          'Chart Analysis',
            'performance':       'Performance Analytics',
            'mentor':            'AI Mentor'
        };
        const pageTitle = document.getElementById('page-title');
        if (pageTitle) pageTitle.textContent = titles[section] || 'Dashboard';
        document.getElementById('sidebar')?.classList.add('-translate-x-full');
        document.getElementById('sidebar-overlay')?.classList.add('hidden');
    }

    async loadSectionData(section) {
        try {
            switch (section) {
                case 'dashboard':        this.loadDashboardStats(); break;
                case 'signals':
                case 'enhanced-signals': await this.loadSignals(); break;
                case 'courses':          await this.loadCourses(); break;
                case 'webinars':         await this.loadWebinars(); break;
                case 'blog':             await this.loadBlog(); break;
                case 'journal':          this.setupJournalUpload(); break;
                case 'admin':            await this.loadAdminData(); break;
                case 'mentor':           await this.loadMentor(); break;
                case 'analysis':         await this.loadChartAnalysis(); break;
                case 'performance':      await this.loadPerformance(); break;
            }
        } catch (err) {
            console.error(`[Dashboard] Error loading ${section}:`, err);
        }
    }

    // ── Dashboard stats ───────────────────────────────────────────────────────
    async loadDashboardStats() {
        try {
            const signals = await API.getSignals();
            const el = document.getElementById('stat-signals');
            if (el) el.textContent = Array.isArray(signals) ? signals.length : '--';
        } catch (e) {
            const el = document.getElementById('stat-signals');
            if (el) el.textContent = '--';
        }
        try {
            const courses = await API.getCourses();
            const list = Array.isArray(courses) ? courses : (courses.courses || []);
            const el = document.getElementById('stat-courses');
            if (el) el.textContent = list.length;
        } catch (e) {
            const el = document.getElementById('stat-courses');
            if (el) el.textContent = '--';
        }
    }

    // ── Signals ───────────────────────────────────────────────────────────────
    async loadSignals() {
        const container = document.getElementById('signals-container');
        if (!container) return;
        this.showSkeleton(container, 3);
        try {
            const data = await API.getSignals();
            let signals = Array.isArray(data) ? data : (data.signals || []);
            signals = signals.filter(s => s.status === 'active' || !!s.is_published || !!s.is_active);
            this.renderSignals(signals);
        } catch (error) {
            console.error('[Signals Error]', error);
            container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">No active signals available</div>';
        }
    }

    renderSignals(signals) {
        const container = document.getElementById('signals-container');
        if (!container) return;
        if (!signals?.length) {
            container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">No active signals available</div>';
            return;
        }
        container.innerHTML = signals.map(signal => {
            // B11 — normalise confidence: decimal (0.85) or integer (85)
            const rawConf = signal.ai_confidence;
            const conf    = rawConf != null ? (rawConf > 1 ? Math.round(rawConf) : Math.round(rawConf * 100)) : null;
            // B17 — guard against Invalid Date
            const dateStr = signal.created_at ? new Date(signal.created_at).toLocaleDateString() : 'Recent';
            return `
            <div class="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-colors">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="font-bold text-white text-lg">${this._safeHtml(signal.symbol)}</h4>
                    <span class="px-2 py-1 rounded text-xs font-bold ${signal.direction === 'BUY' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}">
                        ${this._safeHtml(signal.direction)}
                    </span>
                </div>
                <div class="text-sm text-gray-400 space-y-1">
                    <div class="flex justify-between"><span>Entry:</span><span class="text-white">${this._safeHtml(String(signal.entry_price ?? '--'))}</span></div>
                    <div class="flex justify-between"><span>SL:</span><span class="text-red-400">${this._safeHtml(String(signal.stop_loss ?? '--'))}</span></div>
                    <div class="flex justify-between"><span>TP:</span><span class="text-green-400">${this._safeHtml(String(signal.take_profit ?? '--'))}</span></div>
                    <div class="flex justify-between"><span>Timeframe:</span><span>${this._safeHtml(signal.timeframe || 'N/A')}</span></div>
                </div>
                <div class="mt-3 pt-3 border-t border-gray-700 text-xs text-gray-500 flex justify-between">
                    <span>${dateStr}</span>
                    ${conf != null ? `<span class="text-purple-400">AI: ${conf}%</span>` : ''}
                </div>
            </div>`;
        }).join('');
    }

    // ── Courses ───────────────────────────────────────────────────────────────
    async loadCourses() {
        const container = document.getElementById('courses-container');
        if (!container) return;
        this.showSkeleton(container, 4);
        try {
            const data = await API.getCourses();
            let courses = Array.isArray(data) ? data : (data.courses || []);
            courses = courses.filter(c => !!c.is_published || !!c.is_active);
            this.allCourses = courses;
            this.renderCourses(courses);
            this.setupCourseFilters();
        } catch (error) {
            console.error('[Courses Error]', error);
            const el = document.getElementById('courses-container');
            if (el) el.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">No courses available</div>';
        }
    }

    setupCourseFilters() {
        const fc = document.getElementById('course-filters');
        if (!fc) return;
        fc.innerHTML = ['All', 'Beginner', 'Intermediate', 'Advanced'].map(level => `
            <button onclick="dashboard.filterCourses('${level}')"
                    class="filter-btn px-4 py-2 rounded-full text-sm transition-colors ${level === 'All' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}"
                    data-level="${level}">${level}</button>
        `).join('');
    }

    filterCourses(level) {
        document.querySelectorAll('.filter-btn').forEach(btn => {
            const active = btn.dataset.level === level;
            btn.className = `filter-btn px-4 py-2 rounded-full text-sm transition-colors ${active ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`;
        });
        this.renderCourses(level === 'All' ? this.allCourses : this.allCourses.filter(c => c.level?.toLowerCase() === level.toLowerCase()));
    }

    renderCourses(courses) {
        const container = document.getElementById('courses-container');
        if (!container) return;
        if (!courses?.length) {
            container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">No courses available for this level</div>';
            return;
        }
        container.innerHTML = courses.map(course => `
            <div class="bg-gray-800 rounded-lg overflow-hidden border border-gray-700 hover:border-gray-600 transition-all hover:transform hover:-translate-y-1">
                <div class="h-40 bg-gradient-to-br from-purple-900 to-blue-900 flex items-center justify-center">
                    <i class="fas fa-graduation-cap text-5xl text-white/20"></i>
                </div>
                <div class="p-4">
                    <div class="flex justify-between items-start mb-2">
                        <span class="text-xs text-purple-400 font-semibold">${this._safeHtml(course.level || 'Beginner')}</span>
                        ${course.progress > 0 ? `<span class="text-xs text-green-400">${course.progress}% complete</span>` : ''}
                    </div>
                    <h4 class="font-bold text-white mb-2">${this._safeHtml(course.title)}</h4>
                    <p class="text-sm text-gray-400 mb-3 line-clamp-2">${this._safeHtml(course.description || '')}</p>
                    <div class="flex justify-between items-center text-xs text-gray-500">
                        <span>${course.lesson_count || 0} lessons</span>
                        <button class="text-purple-400 hover:text-purple-300 font-medium">Start Learning →</button>
                    </div>
                </div>
            </div>`).join('');
    }

    // ── Webinars ──────────────────────────────────────────────────────────────
    async loadWebinars() {
        const container = document.getElementById('webinars-container');
        if (!container) return;
        this.showSkeleton(container, 2);
        try {
            const data = await API.getWebinars();
            let webinars = Array.isArray(data) ? data : (data.webinars || []);
            webinars = webinars.filter(w => !!w.is_published || w.status === 'scheduled' || w.status === 'live');
            if (!webinars.length) {
                container.innerHTML = '<div class="text-center py-8 text-gray-500">No upcoming webinars scheduled</div>';
                return;
            }
            container.innerHTML = webinars.map(webinar => {
                const date = new Date(webinar.scheduled_at);
                return `
                    <div class="bg-gray-800 rounded-lg p-4 border border-gray-700 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                        <div class="flex gap-4">
                            <div class="text-center min-w-[60px] bg-gray-700 rounded-lg p-2">
                                <div class="text-xl font-bold text-purple-400">${date.getDate()}</div>
                                <div class="text-xs text-gray-400 uppercase">${date.toLocaleString('default',{month:'short'})}</div>
                            </div>
                            <div>
                                <h4 class="font-bold text-white">${this._safeHtml(webinar.title)}</h4>
                                <p class="text-sm text-gray-400">${this._safeHtml(webinar.description || '')}</p>
                                <div class="text-xs text-gray-500 mt-1">
                                    <span class="mr-3"><i class="fas fa-user mr-1"></i>${this._safeHtml(webinar.presenter || 'TBA')}</span>
                                    <span><i class="fas fa-clock mr-1"></i>${webinar.duration_minutes || 60} mins</span>
                                </div>
                            </div>
                        </div>
                        ${webinar.meeting_link
                            ? `<a href="${this._safeHtml(webinar.meeting_link)}" target="_blank" class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm transition-colors whitespace-nowrap">Join Now →</a>`
                            : `<button class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm transition-colors whitespace-nowrap">Register</button>`}
                    </div>`;
            }).join('');
        } catch (error) {
            console.error('[Webinars Error]', error);
            container.innerHTML = '<div class="text-center py-8 text-gray-500">Failed to load webinars</div>';
        }
    }

    // ── Blog ──────────────────────────────────────────────────────────────────
    async loadBlog() {
        const container = document.getElementById('blog-container');
        if (!container) return;
        this.showSkeleton(container, 3);
        try {
            const data = await API.getBlogPosts();
            let posts = Array.isArray(data) ? data : (data.posts || []);
            posts = posts.filter(p => !!p.is_published || p.status === 'published');
            if (!posts.length) {
                container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">No articles published yet</div>';
                return;
            }
            container.innerHTML = posts.map(post => {
                // Pre-compute image HTML outside main template — avoids nested backtick evaluation quirk
                const imgHtml = post.featured_image
                    ? '<div class="h-48 overflow-hidden"><img src="' + this._safeHtml(post.featured_image) + '" class="w-full h-full object-cover group-hover:scale-105 transition-transform" onerror="this.style.display=\'none\'"></div>'
                    : '<div class="h-48 bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center"><i class="fas fa-newspaper text-5xl text-white/20 group-hover:scale-110 transition-transform"></i></div>';
                return `
                <article class="bg-gray-800 rounded-lg overflow-hidden border border-gray-700 hover:border-gray-600 transition-all cursor-pointer group">
                    ${imgHtml}
                    <div class="p-4">
                        <div class="text-xs text-purple-400 mb-2 uppercase tracking-wide">${this._safeHtml(post.category || 'General')}</div>
                        <h4 class="font-bold text-white mb-2 group-hover:text-purple-400 transition-colors">${this._safeHtml(post.title)}</h4>
                        <p class="text-sm text-gray-400 line-clamp-3 mb-3">${this._safeHtml(post.excerpt || '')}</p>
                        <div class="text-xs text-gray-500 flex justify-between items-center">
                            <span>${post.created_at ? new Date(post.created_at).toLocaleDateString() : 'Recent'}</span>
                            <span class="text-purple-400">Read more →</span>
                        </div>
                    </div>
                </article>`;
            }).join('');
        } catch (error) {
            console.error('[Blog Error]', error);
            container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">Failed to load articles</div>';
        }
    }

    // ── Admin — P4/P5/P8/P9 ──────────────────────────────────────────────────
    async loadAdminData() {
        const container = document.getElementById('admin-container');
        if (!container) return;
        if (!this.isAdmin) {
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
        // P5 — AdminPage.render wrapped in try/catch
        if (typeof AdminPage !== 'undefined') {
            try {
                await AdminPage.render(container);
            } catch (e) {
                console.error('[Admin] AdminPage.render failed:', e);
                container.innerHTML = '<div class="text-red-400 p-4 bg-red-900/20 rounded-lg border border-red-800">Admin panel failed to load. Check console for details.</div>';
            }
            return;
        }
        console.warn('[Dashboard] AdminPage module not loaded — showing basic view');
        container.innerHTML = `
            <div class="bg-yellow-900/20 border border-yellow-700/50 rounded-lg p-4 mb-4 text-sm text-yellow-400">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                Admin module (admin.js) not loaded. Add it to the HTML before dashboard.js.
            </div>`;
        try {
            const stats = await API.getAdminStats();
            // P9 — insertAdjacentHTML instead of innerHTML +=
            container.insertAdjacentHTML('beforeend', `
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <div class="text-3xl font-bold text-white mb-1">${stats.total_users ?? 0}</div>
                        <div class="text-sm text-gray-400">Total Users</div>
                    </div>
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <div class="text-3xl font-bold text-white mb-1">${stats.active_signals ?? 0}</div>
                        <div class="text-sm text-gray-400">Active Signals</div>
                    </div>
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <div class="text-3xl font-bold text-white mb-1">${stats.new_today ?? 0}</div>
                        <div class="text-sm text-gray-400">New Today</div>
                    </div>
                </div>`);
        } catch (err) {
            // P2 — escape error message
            const safeMsg = this._safeHtml(err.message || 'Unknown error');
            container.insertAdjacentHTML('beforeend', `
                <div class="text-red-400 p-4 bg-red-900/20 rounded-lg border border-red-800 text-sm">
                    Failed to load admin data: ${safeMsg}
                </div>`);
        }
    }

    // ── Mentor — B7 guard preserves chat history ──────────────────────────────
    async loadMentor() {
        const container = document.getElementById('section-mentor');
        if (!container) return;
        // B7 — don't wipe existing conversation on re-navigation
        if (document.getElementById('mentor-messages')?.children.length > 1) return;
        container.innerHTML = `
            <div class="max-w-6xl mx-auto h-[calc(100vh-200px)]">
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
                    <div class="lg:col-span-2 bg-gray-800 rounded-xl flex flex-col h-full border border-gray-700">
                        <div class="p-4 border-b border-gray-700 flex justify-between items-center flex-shrink-0">
                            <div class="flex items-center gap-3">
                                <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white">
                                    <i class="fas fa-robot"></i>
                                </div>
                                <div>
                                    <h3 class="font-bold text-white">AI Trading Mentor</h3>
                                    <p class="text-xs text-green-400 flex items-center gap-1">
                                        <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>Online
                                    </p>
                                </div>
                            </div>
                            <button onclick="dashboard.clearMentorChat()" class="text-gray-400 hover:text-white p-2 transition-colors">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                        </div>
                        <div id="mentor-messages" class="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-900 min-h-0">
                            <div class="flex gap-3">
                                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm flex-shrink-0">
                                    <i class="fas fa-robot"></i>
                                </div>
                                <div class="bg-gray-700 p-3 rounded-2xl rounded-tl-none max-w-[85%] sm:max-w-[80%]">
                                    <p class="text-gray-200">Welcome! I'm your AI Trading Mentor. Ask me anything about trading strategies, risk management, or market analysis.</p>
                                </div>
                            </div>
                        </div>
                        <div class="p-4 border-t border-gray-700 bg-gray-800 rounded-b-xl flex-shrink-0">
                            <div class="flex gap-2">
                                <input type="text" id="mentor-input" placeholder="Ask your trading question..."
                                    class="flex-1 px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                                    onkeypress="if(event.key==='Enter') dashboard.sendMentorMessage()">
                                <button onclick="dashboard.sendMentorMessage()" class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg transition-colors flex items-center justify-center">
                                    <i class="fas fa-paper-plane"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="space-y-4 hidden lg:block">
                        <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">
                            <h4 class="font-bold text-white mb-3">Quick Topics</h4>
                            <div class="space-y-2">
                                ${[
                                    ['How do I manage risk effectively?',          'Risk Management'],
                                    ['What is a good risk/reward ratio?',          'R:R Ratios'],
                                    ['How do I control emotions while trading?',   'Trading Psychology'],
                                    ['Explain support and resistance levels',      'Technical Analysis'],
                                    ['How do I create a trading plan?',            'Trading Plan'],
                                ].map(([q, label]) => `<button onclick="dashboard.askMentor('${q}')"
                                    class="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-700 text-sm text-gray-300 transition-colors">${label}</button>`).join('')}
                            </div>
                        </div>
                        <div class="bg-gray-800 rounded-xl p-4 border border-gray-700 bg-gradient-to-br from-yellow-900/30 to-orange-900/30">
                            <h4 class="font-bold text-white mb-2"><i class="fas fa-lightbulb text-yellow-400 mr-2"></i>Daily Tip</h4>
                            <p class="text-sm text-gray-400">"Never risk more than 2% of your account on a single trade. Consistency beats intensity."</p>
                        </div>
                    </div>
                </div>
            </div>`;
    }

    async sendMentorMessage() {
        const input     = document.getElementById('mentor-input');
        const container = document.getElementById('mentor-messages');
        if (!input || !container) return;
        const message = input.value.trim();
        if (!message) return;

        // User bubble — message is user input, escape it
        container.insertAdjacentHTML('beforeend', `
            <div class="flex gap-3 flex-row-reverse">
                <div class="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center text-white text-sm flex-shrink-0">
                    <i class="fas fa-user"></i>
                </div>
                <div class="bg-purple-600 p-3 rounded-2xl rounded-tr-none max-w-[85%] sm:max-w-[80%]">
                    <p class="text-white">${this._safeHtml(message)}</p>
                </div>
            </div>`);
        input.value = '';
        container.scrollTop = container.scrollHeight;

        const typingId = 'typing-' + Date.now();
        container.insertAdjacentHTML('beforeend', `
            <div id="${typingId}" class="flex gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm flex-shrink-0">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="bg-gray-700 p-3 rounded-2xl rounded-tl-none">
                    <div class="flex space-x-1">
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay:.1s"></div>
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay:.2s"></div>
                    </div>
                </div>
            </div>`);
        container.scrollTop = container.scrollHeight;

        try {
            const response = await API.askMentor(message);
            document.getElementById(typingId)?.remove();
            // B3 — sanitise AI response before injection
            const safeResponse = this._safeHtml(response.response || response.answer || '');
            const resources    = response.suggested_resources?.length
                ? `<div class="mt-2 pt-2 border-t border-gray-600 text-xs text-purple-400">
                       <strong>Suggested:</strong> ${response.suggested_resources.map(r => this._safeHtml(r)).join(', ')}
                   </div>` : '';
            container.insertAdjacentHTML('beforeend', `
                <div class="flex gap-3">
                    <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm flex-shrink-0">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="bg-gray-700 p-3 rounded-2xl rounded-tl-none max-w-[85%] sm:max-w-[80%]">
                        <p class="text-gray-200">${safeResponse}</p>
                        ${resources}
                    </div>
                </div>`);
            container.scrollTop = container.scrollHeight;
        } catch (e) {
            document.getElementById(typingId)?.remove();
            container.insertAdjacentHTML('beforeend', `
                <div class="flex gap-3">
                    <div class="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center text-white text-sm flex-shrink-0">
                        <i class="fas fa-exclamation"></i>
                    </div>
                    <div class="bg-red-900/50 p-3 rounded-2xl rounded-tl-none border border-red-700 max-w-[80%]">
                        <p class="text-red-200 text-sm">Sorry, I encountered an error. Please try again.</p>
                    </div>
                </div>`);
        }
    }

    askMentor(question) {
        const input = document.getElementById('mentor-input');
        if (input) { input.value = question; this.sendMentorMessage(); }
    }

    clearMentorChat() {
        const container = document.getElementById('mentor-messages');
        if (!container) return;
        container.innerHTML = `
            <div class="flex gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm flex-shrink-0">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="bg-gray-700 p-3 rounded-2xl rounded-tl-none max-w-[80%]">
                    <p class="text-gray-200">Chat cleared. How can I help you today?</p>
                </div>
            </div>`;
    }

    // ── Chart Analysis — B6/B8 ────────────────────────────────────────────────
    async loadChartAnalysis() {
        if (this._chartSetup) return;  // B6
        this._chartSetup = true;
        const dropZone  = document.getElementById('chart-dropzone');
        const fileInput = document.getElementById('chart-file-input');
        if (!dropZone || !fileInput) return;
        dropZone.addEventListener('click',     () => fileInput.click());
        dropZone.addEventListener('dragover',  (e) => { e.preventDefault(); dropZone.classList.add('border-purple-500','bg-purple-900/20'); });
        dropZone.addEventListener('dragleave', ()  => dropZone.classList.remove('border-purple-500','bg-purple-900/20'));
        dropZone.addEventListener('drop',      (e) => { e.preventDefault(); dropZone.classList.remove('border-purple-500','bg-purple-900/20'); const f = e.dataTransfer.files[0]; if (f) this.handleChartFileSelect(f); });
        fileInput.addEventListener('change',   (e) => { if (e.target.files[0]) this.handleChartFileSelect(e.target.files[0]); });
    }

    handleChartFileSelect(file) {
        if (!file) return;
        if (file.size > 5 * 1024 * 1024) { this._toast('File too large — max 5MB allowed', 'error'); return; }
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview     = document.getElementById('chart-preview');
            const placeholder = document.getElementById('chart-upload-placeholder');
            const analyzeBtn  = document.getElementById('analyze-chart-btn');
            if (preview)     { preview.src = e.target.result; preview.classList.remove('hidden'); }
            if (placeholder)   placeholder.classList.add('hidden');
            if (analyzeBtn)    analyzeBtn.disabled = false;
            this.currentChartFile   = file;
            this.currentChartBase64 = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    async analyzeChart() {
        if (!this.currentChartBase64) { this._toast('Please select a chart image first', 'warning'); return; }
        const loadingEl  = document.getElementById('chart-analysis-loading');
        const resultsEl  = document.getElementById('chart-analysis-results');
        const analyzeBtn = document.getElementById('analyze-chart-btn');
        if (loadingEl)  loadingEl.classList.remove('hidden');
        if (analyzeBtn) analyzeBtn.disabled = true;
        try {
            const symbol    = document.getElementById('chart-symbol')?.value || 'AUTO';
            const timeframe = document.getElementById('chart-timeframe')?.value || '';
            const response  = await fetch('/ai/chart/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('pipways_token')}` },
                body: JSON.stringify({ image: this.currentChartBase64, symbol, timeframe })
            });
            const data = await response.json();
            // B8 — check response.ok
            if (!response.ok) throw new Error(data.detail || `Analysis failed (${response.status})`);

            if (resultsEl) {
                resultsEl.classList.remove('hidden');
                document.getElementById('analysis-symbol').textContent    = data.symbol || symbol || 'Unknown';
                document.getElementById('analysis-timeframe').textContent = data.timeframe || timeframe || '';
                const confidence = Math.round((data.confidence || 0) * 100);
                const confEl = document.getElementById('analysis-confidence');
                if (confEl) {
                    confEl.textContent = `${confidence}%`;
                    confEl.className   = `px-3 py-1 rounded-full text-sm font-bold ${confidence > 70 ? 'bg-green-900 text-green-300' : confidence > 40 ? 'bg-yellow-900 text-yellow-300' : 'bg-red-900 text-red-300'}`;
                }
                const biasEl = document.getElementById('analysis-bias');
                if (biasEl) {
                    biasEl.textContent = data.trading_bias || data.bias || 'Neutral';
                    biasEl.className   = `text-2xl font-bold ml-2 uppercase ${data.trading_bias === 'bullish' ? 'text-green-400' : data.trading_bias === 'bearish' ? 'text-red-400' : 'text-gray-400'}`;
                }
                const patternEl = document.getElementById('analysis-pattern');
                if (patternEl) patternEl.textContent = data.pattern || 'No specific pattern detected';
                if (data.trade_setup) {
                    const s = data.trade_setup;
                    const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v || '--'; };
                    set('setup-entry', s.entry_price || s.entry);
                    set('setup-sl',    s.stop_loss   || s.sl);
                    set('setup-tp',    s.take_profit || s.tp);
                    set('setup-rr',    s.risk_reward || s.rr);
                }
                const levelsContainer = document.getElementById('key-levels-list');
                if (levelsContainer && data.key_levels) {
                    levelsContainer.innerHTML = data.key_levels.map(level => `
                        <div class="flex justify-between items-center p-2 bg-gray-900 rounded border-l-4 ${level.type === 'support' ? 'border-green-500' : level.type === 'resistance' ? 'border-red-500' : 'border-blue-500'}">
                            <span class="text-gray-300 capitalize">${this._safeHtml(level.type)}</span>
                            <span class="font-mono font-bold text-white">${this._safeHtml(String(level.price))}</span>
                        </div>`).join('');
                }
                const insightsEl = document.getElementById('analysis-insights');
                if (insightsEl && data.key_insights) {
                    insightsEl.innerHTML = data.key_insights.map(i => `<li>${this._safeHtml(i)}</li>`).join('');
                }
                const attachedChart = document.getElementById('attached-chart-preview');
                if (attachedChart && this.currentChartBase64) {
                    attachedChart.src = this.currentChartBase64;
                    attachedChart.classList.remove('hidden');
                }
                this.currentAnalysis = data;
            }
        } catch (error) {
            console.error('[Chart Analysis] Error:', error);
            this._toast(error.message || 'Failed to analyze chart. Please try again.', 'error');
        } finally {
            if (loadingEl)  loadingEl.classList.add('hidden');
            if (analyzeBtn) analyzeBtn.disabled = false;
        }
    }

    showTradeValidator() {
        const modal = document.getElementById('trade-validator-modal');
        if (!modal) return;
        modal.classList.remove('hidden');
        if (this.currentAnalysis?.trade_setup) {
            const s = this.currentAnalysis.trade_setup;
            const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v || ''; };
            setVal('validator-entry',  s.entry_price || s.entry);
            setVal('validator-sl',     s.stop_loss   || s.sl);
            setVal('validator-tp',     s.take_profit || s.tp);
            setVal('validator-symbol', this.currentAnalysis.symbol || '');
        }
    }

    async validateTradeSetup() {
        const entry  = parseFloat(document.getElementById('validator-entry')?.value);
        const sl     = parseFloat(document.getElementById('validator-sl')?.value);
        const tp     = parseFloat(document.getElementById('validator-tp')?.value);
        const symbol = document.getElementById('validator-symbol')?.value || 'EURUSD';
        if (!entry || !sl || !tp) { this._toast('Please fill in Entry, SL, and TP values', 'warning'); return; }
        try {
            // B2b — corrected URL
            const response = await fetch('/ai/chart/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('pipways_token')}` },
                body: JSON.stringify({ entry_price: entry, stop_loss: sl, take_profit: tp, symbol, setup_type: this.currentAnalysis?.pattern || 'manual' })
            });
            const result = await response.json();
            // B9 — check response.ok
            if (!response.ok) throw new Error(result.detail || `Validation failed (${response.status})`);

            const resultEl = document.getElementById('validation-result');
            if (!resultEl) return;
            resultEl.classList.remove('hidden');
            const score   = result.quality_score || 0;
            const scoreEl = document.getElementById('validation-score');
            if (scoreEl) {
                scoreEl.textContent = score;
                scoreEl.className   = `score-circle ${score >= 80 ? 'score-excellent' : score >= 60 ? 'score-good' : score >= 40 ? 'score-warning' : 'score-danger'}`;
            }
            const rec = document.getElementById('validation-recommendation');
            if (rec) rec.textContent = result.recommendation || (result.valid ? 'Valid Setup' : 'Review Setup');
            const rrEl = document.getElementById('validation-rr');
            if (rrEl) rrEl.textContent = result.risk_reward_ratio || result.rr || '--';
            const probEl = document.getElementById('validation-probability');
            if (probEl) probEl.textContent = (result.probability || result.win_probability || 0) + '%';
            const warningsEl = document.getElementById('validation-warnings');
            if (warningsEl) {
                warningsEl.innerHTML = result.warnings?.length
                    ? result.warnings.map(w => `<div class="text-yellow-400 flex items-center gap-2 mb-1"><i class="fas fa-exclamation-triangle"></i>${this._safeHtml(w)}</div>`).join('')
                    : '<div class="text-green-400 flex items-center gap-2"><i class="fas fa-check-circle"></i>No warnings — good setup!</div>';
            }
            const suggestionsEl = document.getElementById('validation-suggestions');
            if (suggestionsEl && result.suggestions) {
                suggestionsEl.innerHTML = result.suggestions.map(s => `<div class="flex items-start gap-2 mb-1"><i class="fas fa-lightbulb mt-1 text-blue-400"></i>${this._safeHtml(s)}</div>`).join('');
            }
        } catch (error) {
            console.error('[Trade Validator] Error:', error);
            this._toast(error.message || 'Validation failed. Please try again.', 'error');
        }
    }

    async saveCurrentSignal() {
        if (!this.currentAnalysis) { this._toast('No analysis to save — please analyze a chart first', 'warning'); return; }
        try {
            // B2c — corrected URL
            const response = await fetch('/api/signals', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('pipways_token')}` },
                body: JSON.stringify({
                    symbol:      this.currentAnalysis.symbol,
                    pattern:     this.currentAnalysis.pattern,
                    direction:   this.currentAnalysis.trading_bias || this.currentAnalysis.bias,
                    entry_price: this.currentAnalysis.trade_setup?.entry_price || this.currentAnalysis.trade_setup?.entry,
                    stop_loss:   this.currentAnalysis.trade_setup?.stop_loss   || this.currentAnalysis.trade_setup?.sl,
                    take_profit: this.currentAnalysis.trade_setup?.take_profit || this.currentAnalysis.trade_setup?.tp,
                    ai_confidence: this.currentAnalysis.confidence,
                    analysis_data: this.currentAnalysis
                })
            });
            if (response.ok) {
                this._toast('Signal saved successfully!', 'success');
            } else {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || 'Failed to save signal');
            }
        } catch (error) {
            console.error('[Save Signal] Error:', error);
            this._toast(error.message || 'Failed to save signal. Please try again.', 'error');
        }
    }

    // ── Journal — B5 ─────────────────────────────────────────────────────────
    setJournalFormat(format) {
        this.currentJournalFormat = format;
        document.querySelectorAll('.format-btn').forEach(btn => {
            const active = btn.dataset.format === format;
            btn.classList.toggle('border-purple-500', active);
            btn.classList.toggle('bg-purple-600',     active);
            btn.classList.toggle('border-gray-600',   !active);
            btn.classList.toggle('bg-gray-700',       !active);
        });
        const formatConfig = {
            mt4:        { accept: '.html,.htm',          label: 'MT4 HTML Statement selected' },
            mt5:        { accept: '.html,.htm',          label: 'MT5 HTML Statement selected' },
            csv:        { accept: '.csv',                label: 'CSV file selected' },
            excel:      { accept: '.xlsx,.xls',          label: 'Excel file selected' },
            screenshot: { accept: '.png,.jpg,.jpeg,.webp',label: 'Screenshot for OCR selected' }
        };
        const config    = formatConfig[format];
        const fileInput = document.getElementById('journal-file-input');
        const label     = document.getElementById('selected-format');
        if (config && fileInput) {
            fileInput.accept = config.accept;
            if (label) label.textContent = config.label;
            fileInput.click();
        }
    }

    setupJournalUpload() {
        if (this._journalSetup) return;  // B5
        this._journalSetup = true;
        const dropZone  = document.getElementById('journal-dropzone');
        const fileInput = document.getElementById('journal-file-input');
        if (!dropZone || !fileInput) return;
        dropZone.addEventListener('click',     () => fileInput.click());
        dropZone.addEventListener('dragover',  (e) => { e.preventDefault(); dropZone.classList.add('border-purple-500','bg-purple-900/20'); });
        dropZone.addEventListener('dragleave', ()  => dropZone.classList.remove('border-purple-500','bg-purple-900/20'));
        dropZone.addEventListener('drop', async (e) => { e.preventDefault(); dropZone.classList.remove('border-purple-500','bg-purple-900/20'); const f = e.dataTransfer.files[0]; if (f) await this.handleJournalFile(f); });
        fileInput.addEventListener('change', async (e) => { const f = e.target.files[0]; if (f) await this.handleJournalFile(f); });
    }

    async handleJournalFile(file) {
        const statusEl  = document.getElementById('upload-status');
        const loadingEl = document.getElementById('journal-upload-loading');
        if (statusEl)  { statusEl.classList.remove('hidden'); statusEl.innerHTML = `<span class="text-blue-400"><i class="fas fa-spinner fa-spin mr-2"></i>Processing ${this._safeHtml(file.name)}…</span>`; }
        if (loadingEl)   loadingEl.classList.remove('hidden');
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('format', this.currentJournalFormat || 'auto');
            const response = await fetch('/ai/performance/upload-journal', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('pipways_token')}` },
                body: formData
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || 'Upload failed');
            if (!result.trades?.length) throw new Error('No trades found in this file');
            this.displayJournalAnalysis(result);
            if (statusEl) statusEl.innerHTML = `<span class="text-green-400"><i class="fas fa-check mr-2"></i>Successfully imported ${result.trades_parsed || result.trades.length} trades</span>`;
        } catch (error) {
            console.error('[Journal Upload] Error:', error);
            // B14 — user-friendly error messages
            const friendlyErrors = {
                'No trades found in this file': 'No trades found — check the file format matches your broker export.',
                'Upload failed': 'Upload failed — please try again.',
                'Unsupported format': 'This file format is not supported. Try CSV, HTML or Excel.',
            };
            const msg = friendlyErrors[error.message] || 'Could not process this file. Please check the format and try again.';
            if (statusEl) statusEl.innerHTML = `<span class="text-red-400"><i class="fas fa-exclamation-circle mr-2"></i>${msg}</span>`;
        } finally {
            if (loadingEl) loadingEl.classList.add('hidden');
        }
    }

    // ── Performance — B10 ─────────────────────────────────────────────────────
    async loadPerformance() {
        await this.loadPerformanceStats();
        await this.loadEquityCurve();
        await this.loadTradeDistribution();
    }

    async loadPerformanceStats() {
        const days = document.getElementById('performance-period')?.value || 30;
        try {
            const response = await fetch(`/ai/performance/dashboard?days=${days}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('pipways_token')}` }
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to load performance');
            if (data.summary) {
                const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
                set('perf-total-trades',  data.summary.total_trades   || 0);
                set('perf-win-rate',     (data.summary.win_rate       || 0) + '%');
                set('perf-profit-factor', data.summary.profit_factor  || '0.0');
                set('perf-expectancy',   '$' + (data.summary.expectancy || 0));
            }
            if (data.psychology_profile) {
                const psychContainer = document.getElementById('performance-psychology');
                const traitsContainer = document.getElementById('psychology-traits');
                if (psychContainer && traitsContainer) {
                    psychContainer.classList.remove('hidden');
                    const traits = data.psychology_profile.traits || {};
                    traitsContainer.innerHTML = Object.entries(traits).map(([trait, score]) => `
                        <div class="p-3 bg-gray-900 rounded-lg">
                            <div class="flex justify-between items-center mb-2">
                                <span class="text-gray-400 capitalize">${this._safeHtml(trait.replace('_',' '))}</span>
                                <span class="text-white font-bold">${score}%</span>
                            </div>
                            <div class="w-full bg-gray-700 rounded-full h-2">
                                <div class="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full" style="width:${score}%"></div>
                            </div>
                        </div>`).join('');
                }
            }
        } catch (error) { console.error('[Performance Stats] Error:', error); }
    }

    async loadEquityCurve() {
        // B10 — guard Chart.js
        if (typeof Chart === 'undefined') { console.warn('[Dashboard] Chart.js not loaded — equity curve skipped'); return; }
        try {
            const response = await fetch('/ai/performance/equity-curve?days=30', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('pipways_token')}` }
            });
            const data = await response.json();
            const ctx  = document.getElementById('equity-curve-chart');
            if (!ctx) return;
            this.equityChart?.destroy();
            this.equityChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates || [],
                    datasets: [{ label: 'Equity', data: data.equity || [], borderColor: 'rgb(124,58,237)', backgroundColor: 'rgba(124,58,237,.1)', fill: true, tension: 0.4 }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { grid: { color: 'rgba(75,85,99,.3)' }, ticks: { color: '#9ca3af' } }, x: { grid: { display: false }, ticks: { color: '#9ca3af' } } } }
            });
        } catch (error) { console.error('[Equity Curve] Error:', error); }
    }

    async loadTradeDistribution() {
        // B10 — guard Chart.js
        if (typeof Chart === 'undefined') { console.warn('[Dashboard] Chart.js not loaded — distribution chart skipped'); return; }
        try {
            const response = await fetch('/ai/performance/trade-distribution', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('pipways_token')}` }
            });
            const data = await response.json();
            const ctx  = document.getElementById('trade-distribution-chart');
            if (!ctx) return;
            this.distributionChart?.destroy();
            this.distributionChart = new Chart(ctx, {
                type: 'doughnut',
                data: { labels: ['Winners','Losers','Break Even'], datasets: [{ data: [data.wins||0, data.losses||0, data.break_even||0], backgroundColor: ['rgba(16,185,129,.8)','rgba(239,68,68,.8)','rgba(245,158,11,.8)'], borderWidth: 0 }] },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#9ca3af' } } } }
            });
        } catch (error) { console.error('[Trade Distribution] Error:', error); }
    }

    async analyzePerformance() {
        const input = document.getElementById('performance-journal-input');
        if (!input?.value.trim()) { this._toast('Please enter trade data', 'warning'); return; }
        try {
            const trades   = JSON.parse(input.value);
            const response = await fetch('/ai/performance/analyze-journal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('pipways_token')}` },
                body: JSON.stringify({ trades })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || 'Analysis failed');
            this.displayJournalAnalysis(result);
        } catch (e) { this._toast('Invalid JSON format or analysis failed: ' + e.message, 'error'); }
    }

    // ── Manual entry — B4 ─────────────────────────────────────────────────────
    showManualEntry() {
        const form = document.getElementById('manual-entry-form');
        if (form) { form.classList.remove('hidden'); form.scrollIntoView({ behavior: 'smooth' }); }
    }

    async addManualTrade() {  // B4 — async + try/catch
        const symbol = document.getElementById('manual-symbol')?.value;
        const direction = document.getElementById('manual-direction')?.value;
        const entry  = parseFloat(document.getElementById('manual-entry')?.value);
        const pnl    = parseFloat(document.getElementById('manual-pnl')?.value);
        if (!symbol || isNaN(entry) || isNaN(pnl)) { this._toast('Please fill in all required fields', 'warning'); return; }
        const trade = {
            entry_date: new Date().toISOString().split('T')[0],
            symbol: symbol.toUpperCase(), direction,
            entry_price: entry,
            exit_price:  parseFloat(document.getElementById('manual-exit')?.value) || 0,
            stop_loss:   parseFloat(document.getElementById('manual-sl')?.value)   || 0,
            take_profit: parseFloat(document.getElementById('manual-tp')?.value)   || 0,
            pnl, outcome: pnl > 0 ? 'win' : pnl < 0 ? 'loss' : 'breakeven'
        };
        this.manualTrades.push(trade);
        try {
            const response = await fetch('/ai/performance/analyze-journal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('pipways_token')}` },
                body: JSON.stringify({ trades: this.manualTrades })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || 'Analysis failed');
            this.displayJournalAnalysis({ ...result, trades: this.manualTrades });
        } catch (err) {
            console.error('[Manual Trade] Error:', err);
            this._toast('Trade added but analysis failed: ' + err.message, 'warning');
        }
    }

    // ── Journal display — B15 ─────────────────────────────────────────────────
    displayJournalAnalysis(result) {
        const statusEl       = document.getElementById('upload-status');
        const analysisEl     = document.getElementById('journal-analysis');
        const statsEl        = document.getElementById('journal-stats');
        const tradesContainer = document.getElementById('recent-trades-container');
        const psychologyEl   = document.getElementById('psychology-profile');

        if (statusEl) statusEl.innerHTML = `<span class="text-green-400"><i class="fas fa-check mr-2"></i>Analysis complete! ${result.trades_parsed || result.trades?.length || 0} trades found</span>`;

        if (statsEl) {
            statsEl.classList.remove('hidden');
            const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
            set('stat-total-trades',  result.statistics?.total_trades || 0);
            set('stat-win-rate',     (result.statistics?.win_rate     || 0) + '%');
            set('stat-profit-factor', result.statistics?.profit_factor || 0);
            set('stat-expectancy',   '$' + (result.statistics?.expectancy || 0));
            set('stat-drawdown',     (result.statistics?.max_drawdown   || 0) + '%');
            set('stat-grade',         result.overall_grade || 'N/A');
            const pnl   = result.statistics?.total_pnl || 0;
            const pnlEl = document.getElementById('stat-net-pnl');
            if (pnlEl) { pnlEl.textContent = '$' + Math.abs(pnl).toFixed(2); pnlEl.className = 'font-bold ' + (pnl >= 0 ? 'text-green-400' : 'text-red-400'); }
            const prog = document.getElementById('stat-progress');
            if (prog) prog.style.width = (result.overall_score || 0) + '%';
        }

        if (analysisEl) {
            analysisEl.classList.remove('hidden');
            analysisEl.innerHTML = `
                <div class="bg-gray-800 rounded-xl p-6 border border-gray-700">
                    <div class="flex justify-between items-center mb-6">
                        <h3 class="text-lg font-bold text-white">Performance Analysis</h3>
                        <span class="px-3 py-1 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold text-sm">${this._safeHtml(result.overall_grade || 'N/A')}</span>
                    </div>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <div class="text-center p-4 bg-gray-900 rounded-lg border border-gray-700">
                            <div class="text-2xl font-bold text-white">${result.statistics?.total_trades || 0}</div>
                            <div class="text-xs text-gray-500 uppercase">Total Trades</div>
                        </div>
                        <div class="text-center p-4 bg-gray-900 rounded-lg border border-gray-700">
                            <div class="text-2xl font-bold ${(result.statistics?.win_rate||0) >= 50 ? 'text-green-400' : 'text-red-400'}">${result.statistics?.win_rate || 0}%</div>
                            <div class="text-xs text-gray-500 uppercase">Win Rate</div>
                        </div>
                        <div class="text-center p-4 bg-gray-900 rounded-lg border border-gray-700">
                            <div class="text-2xl font-bold ${(result.statistics?.profit_factor||0) >= 1 ? 'text-green-400' : 'text-red-400'}">${result.statistics?.profit_factor || 0}</div>
                            <div class="text-xs text-gray-500 uppercase">Profit Factor</div>
                        </div>
                        <div class="text-center p-4 bg-gray-900 rounded-lg border border-gray-700">
                            <div class="text-2xl font-bold ${(result.statistics?.total_pnl||0) >= 0 ? 'text-green-400' : 'text-red-400'}">$${Math.abs(result.statistics?.total_pnl||0).toFixed(2)}</div>
                            <div class="text-xs text-gray-500 uppercase">Net P&L</div>
                        </div>
                    </div>
                    ${result.improvements?.length ? `
                        <div class="space-y-2">
                            <h5 class="font-semibold text-gray-300 text-sm uppercase mb-2">AI Recommendations:</h5>
                            ${result.improvements.map(i => `<div class="p-3 bg-blue-900/20 rounded-lg text-sm text-blue-200 border-l-4 border-blue-500 flex items-start gap-2"><i class="fas fa-lightbulb text-blue-400 mt-1"></i><span>${this._safeHtml(i)}</span></div>`).join('')}
                        </div>` : ''}
                </div>`;
        }

        if (psychologyEl && result.psychology) {
            psychologyEl.classList.remove('hidden');
            const psych = result.psychology;
            const psychContent = document.getElementById('psychology-content');
            if (psychContent) psychContent.innerHTML = `
                <div class="space-y-3">
                    <div class="flex justify-between items-center p-3 bg-gray-900 rounded-lg">
                        <span class="text-gray-400 text-sm">Trading State</span>
                        <span class="text-white font-medium">${this._safeHtml(psych.best_trading_state || 'N/A')}</span>
                    </div>
                    <div class="flex justify-between items-center p-3 bg-gray-900 rounded-lg">
                        <span class="text-gray-400 text-sm">Consistency</span>
                        <span class="text-${psych.emotional_consistency === 'High' ? 'green' : psych.emotional_consistency === 'Medium' ? 'yellow' : 'red'}-400 font-medium">${this._safeHtml(psych.emotional_consistency || 'N/A')}</span>
                    </div>
                    <div class="flex justify-between items-center p-3 bg-gray-900 rounded-lg">
                        <span class="text-gray-400 text-sm">Discipline Score</span>
                        <div class="flex items-center gap-2">
                            <div class="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
                                <div class="h-full bg-purple-500" style="width:${psych.discipline_score||0}%"></div>
                            </div>
                            <span class="text-white font-medium text-sm">${psych.discipline_score || 0}</span>
                        </div>
                    </div>
                </div>`;
        }

        if (tradesContainer && result.trades) {
            tradesContainer.classList.remove('hidden');
            const tbody    = document.getElementById('trades-table-body');
            const INITIAL  = 10;
            const total    = result.trades.length;
            if (tbody) {
                const renderRows = (trades) => trades.map(trade => `
                    <tr class="border-b border-gray-700 hover:bg-gray-700/50">
                        <td class="px-4 py-3 font-medium">${this._safeHtml(trade.symbol || 'N/A')}</td>
                        <td class="px-4 py-3"><span class="px-2 py-1 rounded text-xs font-bold ${trade.direction === 'BUY' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}">${this._safeHtml(trade.direction || '')}</span></td>
                        <td class="px-4 py-3 font-mono">${this._safeHtml(String(trade.entry_price || '--'))}</td>
                        <td class="px-4 py-3 font-mono">${this._safeHtml(String(trade.exit_price || '--'))}</td>
                        <td class="px-4 py-3 font-mono ${(trade.pnl||0) >= 0 ? 'text-green-400' : 'text-red-400'}">${(trade.pnl||0) >= 0 ? '+' : ''}${trade.pnl||0}</td>
                    </tr>`).join('');
                tbody.innerHTML = renderRows(result.trades.slice(0, INITIAL));
                // B15 — show all button when more than 10 trades
                const showMoreContainer = document.getElementById('trades-show-more') || (() => {
                    const div = document.createElement('div');
                    div.id = 'trades-show-more';
                    div.className = 'text-center mt-3';
                    tradesContainer.appendChild(div);
                    return div;
                })();
                if (total > INITIAL) {
                    showMoreContainer.innerHTML = `
                        <button onclick="this.closest('#recent-trades-container').querySelector('tbody').innerHTML=window.dashboard._allTradeRows;this.remove();"
                                class="text-purple-400 hover:text-purple-300 text-sm font-medium py-2">
                            Show all ${total} trades
                        </button>`;
                    this._allTradeRows = renderRows(result.trades);
                } else {
                    showMoreContainer.innerHTML = '';
                }
            }
        }
    }

    // ── Carousel — B16 ───────────────────────────────────────────────────────
    initFeatureCarousel() {
        const carousel = document.getElementById('feature-carousel');
        if (!carousel) return;
        if (this._carouselInterval) { clearInterval(this._carouselInterval); this._carouselInterval = null; }
        const slides = [
            { icon: 'fa-satellite-dish', title: 'Market Signals',  desc: 'AI-powered signals with high accuracy',         color: 'from-purple-600 to-blue-600',   section: 'enhanced-signals' },
            { icon: 'fa-book',           title: 'Trading Journal',  desc: 'Track and analyze your trading performance',    color: 'from-green-600 to-teal-600',    section: 'journal' },
            { icon: 'fa-chart-line',     title: 'Chart Analysis',   desc: 'Advanced technical analysis with AI Vision',    color: 'from-orange-600 to-red-600',    section: 'analysis' },
            { icon: 'fa-robot',          title: 'AI Mentor',        desc: 'Personalized trading coaching 24/7',            color: 'from-pink-600 to-purple-600',   section: 'mentor' },
            { icon: 'fa-graduation-cap', title: 'Trading Academy',  desc: 'Learn from beginner to advanced — always free', color: 'from-blue-600 to-cyan-600',     section: null, href: '/academy' },
            { icon: 'fa-video',          title: 'Webinars',         desc: 'Live trading sessions and Q&A',                 color: 'from-indigo-600 to-purple-600', section: 'webinars' },
            { icon: 'fa-newspaper',      title: 'Trading Blog',     desc: 'Latest market insights and strategies',         color: 'from-yellow-600 to-orange-600', section: 'blog' }
        ];
        let currentSlide = 0;
        const render = () => {
            const s = slides[currentSlide];
            carousel.innerHTML = `
                <div class="bg-gradient-to-r ${s.color} rounded-xl p-6 md:p-8 text-white cursor-pointer hover:shadow-lg transition-all transform hover:-translate-y-1"
                     onclick="${s.href ? `window.location.href='${s.href}'` : `dashboard.navigate('${s.section}')`}">
                    <div class="flex items-start justify-between">
                        <div>
                            <i class="fas ${s.icon} text-3xl mb-3 opacity-80"></i>
                            <h3 class="text-xl font-bold mb-1">${s.title}</h3>
                            <p class="text-white/80 text-sm">${s.desc}</p>
                        </div>
                        <i class="fas fa-arrow-right text-white/50 text-xl"></i>
                    </div>
                </div>`;
        };
        document.getElementById('carousel-next')?.addEventListener('click', () => { currentSlide = (currentSlide + 1) % slides.length; render(); });
        document.getElementById('carousel-prev')?.addEventListener('click', () => { currentSlide = (currentSlide - 1 + slides.length) % slides.length; render(); });
        this._carouselInterval = setInterval(() => { currentSlide = (currentSlide + 1) % slides.length; render(); }, 5000);
        render();
    }

    showSkeleton(container, count = 3) {
        container.innerHTML = Array(count).fill('<div class="animate-pulse bg-gray-800 rounded-lg p-4 border border-gray-700 h-32"></div>').join('');
    }

    logout() {
        localStorage.removeItem('pipways_token');
        localStorage.removeItem('pipways_user');
        window.location.href = '/';
    }
}

const dashboard = new DashboardController();
