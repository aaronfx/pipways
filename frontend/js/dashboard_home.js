/**
 * dashboard_home.js — Dashboard Enhancements
 *
 * Targets IDs that ACTUALLY EXIST in dashboard.html:
 *   greeting-text       — already rendered by dashboard.js; we only touch it if user has perf data
 *   dash-perf-body      — performance card body
 *   dash-learning-body  — academy continue-learning card
 *
 * Also:
 *   - Adds Pro lock badges to sidebar nav links for free users
 *   - Triggers onboarding quiz for new users (if onboarding.js is loaded)
 *
 * Load AFTER dashboard.js. Works as a silent progressive enhancement.
 */

const DashboardHomePatch = {

    init(dash) {
        if (!dash) return;
        this._dash = dash;

        // Run after dashboard has fully initialized (brief delay)
        setTimeout(() => {
            this._enhanceGreeting(dash.user);
            this._enhancePerfCard();
            this._applyLockIcons(dash.user);
            if (window.Onboarding) Onboarding.init(dash.user);
        }, 600);
    },

    // ── Greeting: append performance grade if cached ─────────────────────────
    _enhanceGreeting(user) {
        const subEl = document.getElementById('greeting-sub');
        if (!subEl) return;

        // Only augment if sub-line is still showing generic text or is empty
        const perf = (() => {
            try { return JSON.parse(localStorage.getItem('pipways_performance') || '{}'); }
            catch (_) { return {}; }
        })();

        if (perf?.overall_grade) {
            const score  = perf.overall_score || 0;
            const color  = score >= 75 ? '#34d399' : score >= 50 ? '#fbbf24' : '#f87171';
            const grade  = perf.overall_grade.split(' ')[0];
            subEl.innerHTML = `Last performance grade: <span style="color:${color};font-weight:700;">${grade}</span> &mdash;
                <button onclick="dashboard.navigate('performance')"
                    style="background:none;border:none;color:#a78bfa;font-size:inherit;
                           cursor:pointer;padding:0;text-decoration:underline;">review trades</button>`;
        }
    },

    // ── Performance card: show cached grade or prompt ─────────────────────────
    _enhancePerfCard() {
        const el = document.getElementById('dash-perf-body');
        if (!el) return;

        // Don't overwrite if dashboard.js already wrote real content
        if (el.dataset.enhanced === '1') return;

        const perf = (() => {
            try { return JSON.parse(localStorage.getItem('pipways_performance') || '{}'); }
            catch (_) { return {}; }
        })();

        if (!perf?.overall_grade) return; // dashboard.js handles the empty state fine

        const score      = perf.overall_score || 0;
        const color      = score >= 75 ? '#34d399' : score >= 50 ? '#fbbf24' : '#f87171';
        const grade      = perf.overall_grade.split(' ')[0];
        const trades     = perf.trades_count || 0;
        const cacheAge   = perf.cached_at
            ? Math.round((Date.now() - perf.cached_at) / 86400000)
            : null;
        const ageNote    = cacheAge !== null
            ? `<span style="color:#4b5563;font-size:.7rem;">${cacheAge === 0 ? 'today' : cacheAge + 'd ago'}</span>`
            : '';

        el.innerHTML = `
            <div style="display:flex;align-items:center;gap:.75rem;padding:.25rem 0;">
                <div style="font-size:2.25rem;font-weight:800;line-height:1;color:${color};">${grade}</div>
                <div>
                    <div style="font-size:.75rem;color:#9ca3af;">${score}/100 &bull; ${trades} trades ${ageNote}</div>
                    <div style="display:flex;gap:.5rem;margin-top:.4rem;">
                        ${(perf.improvements || []).slice(0, 1).map(imp =>
                            `<div style="font-size:.7rem;color:#6b7280;line-height:1.4;">${imp}</div>`
                        ).join('')}
                    </div>
                </div>
            </div>
            <button onclick="dashboard.navigate('performance')"
                class="w-full py-2 rounded-lg text-xs font-semibold transition-all mt-3"
                style="background:rgba(124,58,237,.15);border:1px solid rgba(124,58,237,.3);color:#a78bfa;">
                Analyse Trades →
            </button>`;
        el.dataset.enhanced = '1';
    },

    // ── Sidebar lock icons for free users ────────────────────────────────────
    _applyLockIcons(user) {
        if (!user) return;
        const tier = user.subscription_tier || 'free';
        if (tier !== 'free') return;

        const proSections = ['analysis', 'performance'];

        proSections.forEach(section => {
            const link = document.querySelector(`[data-section="${section}"]`);
            if (!link || link.querySelector('.pro-lock-badge')) return;

            const badge = document.createElement('span');
            badge.className = 'pro-lock-badge';
            badge.style.cssText = [
                'display:inline-flex', 'align-items:center', 'gap:2px',
                'font-size:.6rem', 'font-weight:700', 'padding:1px 5px',
                'border-radius:99px', 'background:rgba(124,58,237,.25)',
                'color:#a78bfa', 'border:1px solid rgba(124,58,237,.3)',
                'flex-shrink:0', 'margin-left:auto',
            ].join(';');
            badge.innerHTML = '🔒 Pro';
            link.style.display = 'flex';
            link.style.justifyContent = 'space-between';
            link.style.alignItems = 'center';
            link.appendChild(badge);
        });
    },
};

// Auto-init once dashboard is available
document.addEventListener('DOMContentLoaded', () => {
    const tryInit = (attempts = 0) => {
        if (typeof dashboard !== 'undefined' && dashboard.user) {
            DashboardHomePatch.init(dashboard);
        } else if (attempts < 20) {
            setTimeout(() => tryInit(attempts + 1), 300);
        }
    };
    tryInit();
});

window.DashboardHomePatch = DashboardHomePatch;
