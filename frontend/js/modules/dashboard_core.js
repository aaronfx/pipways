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

// Helper function for safe HTML escaping (used across multiple modules)
const _e = (s) => s == null ? '' : String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

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
        // Extracted: defined in dashboard_password_reset.js
    }

    _showResetModal(token) {
        // Extracted: defined in dashboard_password_reset.js
    }

    _renderResetForm(area, token) {
        // Extracted: defined in dashboard_password_reset.js
    }

    _checkPwStrength(pw) {
        // Extracted: defined in dashboard_password_reset.js
    }

    _checkPwMatch() {
        // Extracted: defined in dashboard_password_reset.js
    }

    async submitPasswordReset(token) {
        // Extracted: defined in dashboard_password_reset.js
    }

    _loadCachedPerformance() {
        // Extracted: defined in dashboard_journal.js
    }


    // ── Auth & User Management ────────────────────────────────────────────
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

    _isAdminUser(user) {
        if (!user) return false;
        if (user.is_admin === true)     return true;
        if (user.role === 'admin')      return true;
        if (user.is_superuser === true) return true;
        const email = (user.email || '').toLowerCase();
        if (email === 'admin@pipways.com' || email.startsWith('admin+')) return true;
        return false;
    }

    async _refreshUserFromServer() {
        try {
            const fresh = await this.apiRequest('/auth/me');
            if (fresh && fresh.email) {
                this.user = { ...this.user, ...fresh };
                localStorage.setItem('pipways_user', JSON.stringify(this.user));
                this.updateUserDisplay();
                this.renderAdminMenu();
            }
        } catch (_) {
            // Non-fatal — stale data is better than crashing
        }
    }


    // ── Navigation & Routing ──────────────────────────────────────────────
    setupNavigation() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                const section = e.currentTarget.dataset.section;
                const href = e.currentTarget.getAttribute('href');
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
            setTimeout(() => {
                const firstLink = sidebar?.querySelector('a, button');
                firstLink?.focus();
            }, 310);
        };
        const closeSidebar = () => {
            sidebar?.classList.add('-translate-x-full');
            overlay?.classList.add('hidden');
            btn?.setAttribute('aria-expanded', 'false');
            btn?.focus();
        };

        if (btn) btn.addEventListener('click', () => {
            sidebar?.classList.contains('-translate-x-full') ? openSidebar() : closeSidebar();
        });

        overlay?.addEventListener('click', closeSidebar);

        document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && sidebar && !sidebar.classList.contains('-translate-x-full')) {
                closeSidebar();
            }
        });
    }

    navigate(section) {
        this._currentSection = section;

        document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
        const activeLink = document.querySelector(`[data-section="${section}"]`);
        if (activeLink) activeLink.classList.add('active');

        document.querySelectorAll('.section').forEach(el => el.classList.add('hidden'));
        const target = document.getElementById(`section-${section}`);
        if (target) {
            target.classList.remove('hidden');
            target.style.animation = 'none';
            target.offsetHeight;
            target.style.animation = 'fadeIn 0.35s ease-out both';
            this.loadSectionData(section);
        }

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
            'subscription': { title: 'Subscription & Plans', sub: 'Upgrade your account to unlock all features' },
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

        document.getElementById('sidebar')?.classList.add('-translate-x-full');
        document.getElementById('sidebar-overlay')?.classList.add('hidden');

        document.querySelector('main')?.scrollTo({ top: 0, behavior: 'smooth' });
    }

    async loadSectionData(section) {
        try {
            switch(section) {
                case 'dashboard': this.loadDashboardStats(); break;
                case 'signals':
                case 'enhanced-signals': 
                    if (typeof window.enhancedSignals !== 'undefined') {
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
                case 'subscription': {
                    const container = document.getElementById('subscription-content');
                    if (window.PaymentsPage) {
                        PaymentsPage.render(container);
                    }
                    break;
                }
                case 'risk': {
                    const rc = document.getElementById('risk-calculator-container');
                    if (!rc) break;
                    if (typeof RiskCalculator !== 'undefined') {
                        if (!rc._rcRendered) { rc._rcRendered = true; await RiskCalculator.render(rc); }
                    } else {
                        rc.innerHTML = `
                            <div class="max-w-5xl mx-auto">
                                <div id="rc-loading-note" class="bg-yellow-900/20 border border-yellow-700/40 rounded-xl p-4 mb-4 flex items-center gap-3">
                                    <i class="fas fa-info-circle text-yellow-400"></i>
                                    <p class="text-sm text-yellow-200">
                                        Loading calculator…
                                        <a href="/risk-calculator" target="_blank" class="underline text-yellow-300 ml-2">Open in full page →</a>
                                    </p>
                                </div>
                                <iframe src="/risk-calculator"
                                    style="width:100%;height:calc(100vh - 220px);border:none;border-radius:12px;background:#111827;"
                                    onload="document.getElementById('rc-loading-note')?.remove()">
                                </iframe>
                            </div>`;
                    }
                    break;
                }
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
                        // Patch Quill editor to accept HTML paste after CMS renders
                        setTimeout(() => this._patchQuillHtmlPaste(), 600);
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


    // ── API Requests ──────────────────────────────────────────────────────
    async apiRequest(endpoint, options = {}) {
        const token = localStorage.getItem('pipways_token');
        const headers = {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        };
        if (options.body instanceof FormData) delete headers['Content-Type'];
        const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

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


    // ── Dashboard Stats (section loader) ──────────────────────────────────
    async loadDashboardStats() {
        // Extracted: defined in dashboard_stats.js
    }

    _initSessionPill() {
        // Extracted: defined in dashboard_stats.js
    }

    _initSocialProof() {
        // Extracted: defined in dashboard_stats.js
    }

    _initUsageBars() {
        // Extracted: defined in dashboard_stats.js
    }

    async _loadDashboardCards() {
        // Extracted: defined in dashboard_stats.js
    }

    _setGreeting() {
        // Extracted: defined in dashboard_stats.js
    }

    _initClock() {
        // Extracted: defined in dashboard_stats.js
    }

    _initTicker() {
        // Extracted: defined in dashboard_stats.js
    }

    _updateNextStepCard(progress, courses, academyResume) {
        // Extracted: defined in dashboard_stats.js
    }


    // ── Journal/Performance (section loader) ──────────────────────────────
    setJournalFormat(format) {
        // Extracted: defined in dashboard_journal.js
    }

    setupJournalUpload() {
        // Extracted: defined in dashboard_journal.js
    }

    async handleJournalFile(file) {
        // Extracted: defined in dashboard_journal.js
    }

    displayJournalAnalysis(result) {
        // Extracted: defined in dashboard_journal.js
    }

    _updateDashPerfCard(result) {
        // Extracted: defined in dashboard_journal.js
    }

    addManualTrade() {
        // Extracted: defined in dashboard_journal.js
    }

    showManualEntry() {
        // Extracted: defined in dashboard_journal.js
    }

    renderEquityCurve(equityData) {
        // Extracted: defined in dashboard_journal.js
    }

    renderTradeDistribution(distribution) {
        // Extracted: defined in dashboard_journal.js
    }

    renderMonthlyPerformance(monthlyData) {
        // Extracted: defined in dashboard_journal.js
    }


    // ── Signals & Courses (section loaders) ───────────────────────────────
    async loadSignals() {
        // Extracted: defined in dashboard_signals_courses.js
    }

    async loadCourses() {
        // Extracted: defined in dashboard_signals_courses.js
    }


    // ── Webinars (section loader) ─────────────────────────────────────────
    async loadWebinars() {
        // Extracted: defined in dashboard_webinars.js
    }

    openSessionRoom(w) {
        // Extracted: defined in dashboard_webinars.js
    }

    async registerForWebinar(id, btn) {
        // Extracted: defined in dashboard_webinars.js
    }


    // ── Blog (section loader) ─────────────────────────────────────────────
    async loadBlog() {
        // Extracted: defined in dashboard_blog.js
    }


    // ── AI Mentor (section loader) ────────────────────────────────────────
    async loadMentor() {
        // Extracted: defined in dashboard_mentor.js
    }

    async loadCoachInsights() {
        // Extracted: defined in dashboard_mentor.js
    }

    loadMentorHistory() {
        // Extracted: defined in dashboard_mentor.js
    }

    saveMentorHistory() {
        // Extracted: defined in dashboard_mentor.js
    }

    async sendMentorMessage() {
        // Extracted: defined in dashboard_mentor.js
    }

    async typeMentorResponse(text) {
        // Extracted: defined in dashboard_mentor.js
    }

    appendMentorMessage(text, sender, animate = true) {
        // Extracted: defined in dashboard_mentor.js
    }

    clearMentorChat() {
        // Extracted: defined in dashboard_mentor.js
    }

    toggleMentorHelp() {
        // Extracted: defined in dashboard_mentor.js
    }

    askMentor(question) {
        // Extracted: defined in dashboard_mentor.js
    }

    _escapeHtml(str) {
        // Extracted: defined in dashboard_mentor.js
    }

    _handleMentorLessonClick(lessonId, url) {
        // Extracted: defined in dashboard_mentor.js
    }

    _getSlashPreview(cmd) {
        // Extracted: defined in dashboard_mentor.js
    }

    _hideMentorRecommendations() {
        // Extracted: defined in dashboard_mentor.js
    }

    _renderMentorLessonCards(recommendations) {
        // Extracted: defined in dashboard_mentor.js
    }

    updateRecommendationsList(resources) {
        // Extracted: defined in dashboard_mentor.js
    }

    _getMentorHistory() {
        // Extracted: defined in dashboard_mentor.js
    }

    _getCachedPerformance() {
        // Extracted: defined in dashboard_mentor.js
    }


    // ── Utility & UI Helpers ──────────────────────────────────────────────
    _toast(message, type = 'success', duration = 3200) {
        const icons = { success:'fa-check-circle', error:'fa-exclamation-circle', info:'fa-info-circle', warning:'fa-exclamation-triangle' };
        const t = document.createElement('div');
        t.className = `pw-toast ${type}`;
        t.setAttribute('role', 'alert');
        t.setAttribute('aria-live', 'assertive');
        t.setAttribute('aria-atomic', 'true');
        t.innerHTML = `<i class="fas ${icons[type]||icons.info} text-sm flex-shrink-0"></i><span>${message}</span>`;
        const existing = document.querySelectorAll('.pw-toast');
        const BASE = 24;
        const HEIGHT = 56;
        t.style.bottom = `${BASE + existing.length * HEIGHT}px`;
        document.body.appendChild(t);
        setTimeout(() => {
            t.style.animation = 'toast-out .3s ease-in both';
            setTimeout(() => {
                t.remove();
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
        if (isHidden && dot) dot.style.display = 'none';
        const notifTrigger = document.getElementById('notif-btn');
        if (notifTrigger) notifTrigger.setAttribute('aria-expanded', String(isHidden));
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

    _patchQuillHtmlPaste() {
        const editorEl = document.querySelector('.ql-editor');
        const containerEl = document.querySelector('.ql-container');
        if (!editorEl || !containerEl) {
            console.log('[CMS] Quill editor or container not found yet.');
            return;
        }

        if (!window.quill) {
            if (window._quillInstance) {
                window.quill = window._quillInstance;
            } else {
                console.log('[CMS] Quill instance not exposed on window.');
                return;
            }
        }

        if (window.quill) {
            console.log('[CMS] Quill instance found; applying HTML paste patch.');
        }

        if (editorEl._htmlPatchApplied) return;
        editorEl._htmlPatchApplied = true;

        editorEl.addEventListener('paste', (e) => {
            const clipboardData = e.clipboardData || window.clipboardData;
            const html = clipboardData?.getData('text/html');
            const text = clipboardData?.getData('text/plain');

            if (!html && !/<[a-z][\s\S]*>/i.test(text)) return;

            e.preventDefault();

            const content = html || text;

            // Re-attempt finding Quill instance in case it was set after patch init
            const quill = window.quill
                || (typeof Quill !== 'undefined' && typeof Quill.find === 'function' && Quill.find(containerEl));

            if (quill && typeof quill.clipboard?.dangerouslyPasteHTML === 'function') {
                const range = quill.getSelection(true);
                const index = range ? range.index : quill.getLength();
                quill.clipboard.dangerouslyPasteHTML(index, content, 'user');
                if (quill) window.quill = quill; // ensure it stays exposed
                this._toast('HTML pasted and rendered', 'success', 2000);
            } else {
                // Fallback: inject directly into the editor element
                const selection = window.getSelection();
                if (selection.rangeCount) {
                    selection.deleteFromDocument();
                    const range = selection.getRangeAt(0);
                    const fragment = range.createContextualFragment(content);
                    range.insertNode(fragment);
                    selection.collapseToEnd();
                } else {
                    editorEl.innerHTML += content;
                }
                this._toast('HTML pasted', 'success', 2000);
            }
        }, true); // capture phase — fires before Quill's own paste handler

        console.log('[CMS] Quill HTML paste patch applied ✓');
    }

    logout() {
        localStorage.removeItem('pipways_token');
        localStorage.removeItem('pipways_user');
        window.location.href = '/';
    }
};
