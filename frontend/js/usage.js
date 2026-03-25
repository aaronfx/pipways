/**
 * Pipways Usage Manager — usage.js
 * Load this on every authenticated page BEFORE other scripts.
 *
 * Provides:
 *   PipwaysUsage.tier            — "free" | "basic" | "pro"
 *   PipwaysUsage.can(feature)    — boolean: has remaining uses
 *   PipwaysUsage.remaining(feature) — integer remaining uses (999 = unlimited)
 *   PipwaysUsage.used(feature)   — integer used
 *   PipwaysUsage.limit(feature)  — integer limit
 *   PipwaysUsage.refresh()       — re-fetch /auth/me and update state
 *   PipwaysUsage.renderBadge(feature, containerEl) — inject usage badge into any element
 *
 * Automatically:
 *   • Intercepts all fetch() calls returning 402 → shows upgrade modal
 *   • Keeps localStorage in sync after every /auth/me call
 *   • Refreshes usage state after a successful feature use
 */

(function (global) {
    'use strict';

    // ── Tier config ──────────────────────────────────────────────────────────
    const TIER_CONFIG = {
        free:  { label: 'Free',  color: '#6b7280', badge: 'bg-gray-700',  next: 'pro',  price_ngn: null },
        pro:   { label: 'Pro',   color: '#a78bfa', badge: 'bg-purple-900', next: null,  price_ngn: 15000 },
    };

    const FEATURE_LABELS = {
        chart_analysis: 'Chart Analysis',
        performance:    'Performance Analysis',
        ai_mentor:      'AI Mentor',
        stock_research: 'AI Stock Research',
    };

    // ── Internal state ───────────────────────────────────────────────────────
    let _state = {
        tier:            'free',
        tier_label:      'Free',
        next_tier:       'basic',
        next_tier_price: 15,
        features:        {},
        loaded:          false,
    };

    // ── Load from localStorage on init ──────────────────────────────────────
    function _loadFromStorage() {
        try {
            const raw = localStorage.getItem('pipways_usage');
            if (raw) {
                const parsed = JSON.parse(raw);
                if (parsed && typeof parsed === 'object') {
                    _state = { ..._state, ...parsed, loaded: true };
                }
            }
            // Also pick up tier from pipways_user (set on login)
            const userRaw = localStorage.getItem('pipways_user');
            if (userRaw) {
                const user = JSON.parse(userRaw);
                if (user && user.subscription_tier) {
                    _state.tier = user.subscription_tier;
                }
            }
        } catch (_) {}
    }

    function _saveToStorage() {
        try {
            localStorage.setItem('pipways_usage', JSON.stringify({
                tier:            _state.tier,
                tier_label:      _state.tier_label,
                next_tier:       _state.next_tier,
                next_tier_price: _state.next_tier_price,
                features:        _state.features,
            }));
        } catch (_) {}
    }

    // ── Fetch /auth/me and update state ─────────────────────────────────────
    async function refresh() {
        const token = localStorage.getItem('pipways_token');
        if (!token) return;
        try {
            const res = await _origFetch(`${window.location.origin}/auth/me`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) return;
            const data = await res.json();

            // Update user in localStorage
            if (data) {
                const user = JSON.parse(localStorage.getItem('pipways_user') || '{}');
                user.subscription_tier = data.subscription_tier || 'free';
                localStorage.setItem('pipways_user', JSON.stringify({ ...user, ...data, usage: undefined }));
            }

            // Update usage state
            if (data.usage) {
                _state = {
                    tier:            data.usage.tier            || data.subscription_tier || 'free',
                    tier_label:      data.usage.tier_label      || 'Free',
                    next_tier:       data.usage.next_tier       || null,
                    next_tier_price: data.usage.next_tier_price || null,
                    features:        data.usage.features        || {},
                    loaded:          true,
                };
                _saveToStorage();
                _updateAllBadges();
                // Notify any listeners (e.g. dashboard._initUsageBars) that data is ready
                document.dispatchEvent(new CustomEvent('pipways:usage-updated', {
                    detail: { tier: _state.tier, features: _state.features }
                }));
            }
        } catch (e) {
            console.warn('[PipwaysUsage] refresh failed:', e);
        }
    }

    // ── Public API ───────────────────────────────────────────────────────────
    const PipwaysUsage = {
        get tier() { return _state.tier; },
        get tierLabel() { return _state.tier_label; },
        get isLoaded() { return _state.loaded; },

        can(feature) {
            const f = _state.features[feature];
            if (!f) return true; // unknown feature = allow
            return !f.at_limit;
        },

        remaining(feature) {
            const f = _state.features[feature];
            if (!f) return 999;
            return f.unlimited ? 999 : (f.remaining ?? 999);
        },

        used(feature) {
            return _state.features[feature]?.used ?? 0;
        },

        limit(feature) {
            return _state.features[feature]?.limit ?? 999;
        },

        isUnlimited(feature) {
            return _state.features[feature]?.unlimited ?? false;
        },

        isWarning(feature) {
            return _state.features[feature]?.warning ?? false;
        },

        isAtLimit(feature) {
            return _state.features[feature]?.at_limit ?? false;
        },

        refresh,

        /**
         * Injects a usage badge into a container element.
         * Automatically re-renders when state updates.
         *
         * @param {string} feature
         * @param {HTMLElement} el
         * @param {object} opts — { compact: bool }
         */
        renderBadge(feature, el, opts = {}) {
            if (!el) return;
            el.dataset.usageBadge = feature;
            _renderBadge(feature, el, opts);
        },

        showUpgradeModal,
    };

    // ── Badge rendering ──────────────────────────────────────────────────────
    function _renderBadge(feature, el, opts = {}) {
        const f = _state.features[feature];
        if (!f) { el.innerHTML = ''; return; }

        if (f.unlimited) {
            el.innerHTML = opts.compact
                ? ''
                : `<span style="font-size:.7rem;color:#34d399;font-weight:600;">Unlimited</span>`;
            return;
        }

        const pct      = f.limit > 0 ? Math.round((f.used / f.limit) * 100) : 0;
        const color    = f.at_limit ? '#ef4444' : f.warning ? '#f59e0b' : '#34d399';
        const label    = f.at_limit ? '0 remaining' : `${f.remaining} remaining`;
        const resetTxt = f.resets ? ` · resets ${f.resets}` : '';

        if (opts.compact) {
            el.innerHTML = `<span style="font-size:.72rem;font-weight:700;color:${color};">${label}</span>`;
        } else {
            el.innerHTML = `
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.25rem;">
                    <span style="font-size:.72rem;color:#6b7280;">${f.used} of ${f.limit} used${resetTxt}</span>
                    <span style="font-size:.72rem;font-weight:700;color:${color};">${label}</span>
                </div>
                <div style="height:4px;background:#1f2937;border-radius:2px;overflow:hidden;">
                    <div style="height:100%;width:${pct}%;background:${color};border-radius:2px;transition:width .4s ease;"></div>
                </div>
                ${f.at_limit ? `<div style="margin-top:.4rem;font-size:.68rem;color:#ef4444;">
                    <i class="fas fa-lock" style="margin-right:.25rem;"></i>
                    Limit reached · <a href="/pricing.html" style="color:#a78bfa;text-decoration:underline;">Upgrade</a> to continue
                </div>` : ''}`;
        }
    }

    function _updateAllBadges() {
        document.querySelectorAll('[data-usage-badge]').forEach(el => {
            const feature = el.dataset.usageBadge;
            const compact = el.dataset.usageCompact === 'true';
            _renderBadge(feature, el, { compact });
        });
    }

    // ── Upgrade Modal ────────────────────────────────────────────────────────
    function showUpgradeModal(feature, used, limit, opts = {}) {
        const existing = document.getElementById('pw-upgrade-modal');
        if (existing) existing.remove();

        const label        = FEATURE_LABELS[feature] || feature;
        const tier         = _state.tier;
        const nextTier     = _state.next_tier;
        const nextPrice    = _state.next_tier_price;
        const tierCfg      = TIER_CONFIG[tier] || TIER_CONFIG.free;
        const nextTierCfg  = TIER_CONFIG[nextTier] || {};

        // Build tier cards — NGN pricing via Paystack
        const basicCard = _planCard({
            name:      'Pro Monthly',
            planKey:   'pro_monthly',
            price_ngn: 15000,
            color:     '#a78bfa',
            highlight: true,
            features:  [
                'Unlimited AI Mentor sessions',
                'Chart Analysis (unlimited)',
                'Full signal history + alerts',
                'Performance analytics',
                'Webinar recordings',
            ],
        });

        const proCard = _planCard({
            name:      'Pro Annual',
            planKey:   'pro_annual',
            price_ngn: 12500,
            color:     '#fbbf24',
            highlight: false,
            features:  [
                'Everything in Pro Monthly',
                'Save ₦30,000 per year',
                '2 months effectively free',
                'Priority support',
            ],
        });

        const modal = document.createElement('div');
        modal.id = 'pw-upgrade-modal';
        modal.innerHTML = `
        <div style="position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:99999;display:flex;align-items:center;justify-content:center;padding:1rem;backdrop-filter:blur(4px);" onclick="if(event.target===this)this.parentElement.remove()">
            <div style="background:#0d1117;border:1px solid #1f2937;border-radius:1.25rem;max-width:620px;width:100%;max-height:90vh;overflow-y:auto;box-shadow:0 24px 80px rgba(0,0,0,.7);">

                <!-- Header -->
                <div style="padding:1.5rem 1.5rem 0;display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;">
                    <div>
                        <div style="display:inline-flex;align-items:center;gap:.5rem;font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#f87171;background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.25);padding:.25rem .75rem;border-radius:9999px;margin-bottom:.75rem;">
                            <i class="fas fa-lock"></i> Limit Reached
                        </div>
                        <h2 style="font-size:1.2rem;font-weight:800;color:white;margin-bottom:.35rem;">You've used all ${limit} free ${label} ${limit === 1 ? 'use' : 'uses'}</h2>
                        <p style="font-size:.85rem;color:#6b7280;line-height:1.5;">
                            Upgrade to keep analysing — your next insight could be the one that changes your trading.
                        </p>
                    </div>
                    <button onclick="document.getElementById('pw-upgrade-modal').remove()" style="background:none;border:none;color:#4b5563;cursor:pointer;font-size:1.1rem;padding:.25rem;flex-shrink:0;margin-top:-.25rem;">
                        <i class="fas fa-times"></i>
                    </button>
                </div>

                <!-- Plan cards -->
                <div style="padding:1.25rem 1.5rem;display:grid;grid-template-columns:1fr 1fr;gap:.75rem;">
                    ${basicCard}
                    ${proCard}
                </div>

                <!-- Footer note -->
                <div style="padding:.75rem 1.5rem 1.5rem;text-align:center;">
                    <p style="font-size:.75rem;color:#4b5563;">
                        Cancel anytime · NGN billing via Paystack · Instant access
                    </p>
                    <a href="/pricing.html" style="font-size:.78rem;color:#a78bfa;text-decoration:underline;margin-top:.35rem;display:inline-block;">
                        Compare all plan features →
                    </a>
                </div>
            </div>
        </div>`;

        document.body.appendChild(modal);
    }

    function _planCard({ name, planKey, price_ngn, color, highlight, features }) {
        const border   = highlight ? `border-color:${color};` : 'border-color:#374151;';
        const badge    = highlight ? `<div style="font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:${color};background:${color}20;border:1px solid ${color}44;padding:.2rem .6rem;border-radius:9999px;margin-bottom:.6rem;display:inline-block;">Most Popular</div>` : '';
        const btnStyle = highlight
            ? `background:${color};color:#0d1117;border:none;`
            : 'background:#1f2937;color:#e5e7eb;border:1px solid #374151;';
        // Use Paystack if available, else fall back to pricing page
        const onClick  = `onclick="document.getElementById('pw-upgrade-modal')?.remove(); if(window.PaymentsPage){PaymentsPage.startPayment('${planKey}')}else{window.location.href='/pricing.html'}" `;

        return `
        <div style="background:#111827;border:1px solid;${border}border-radius:1rem;padding:1.1rem;display:flex;flex-direction:column;gap:.6rem;">
            ${badge}
            <div>
                <div style="font-size:.95rem;font-weight:800;color:white;">${name}</div>
                <div style="font-size:1.35rem;font-weight:800;color:${color};">₦${price_ngn.toLocaleString()}<span style="font-size:.75rem;font-weight:400;color:#6b7280;">/mo</span></div>
            </div>
            <ul style="list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:.3rem;">
                ${features.map(f => `<li style="font-size:.75rem;color:#9ca3af;display:flex;align-items:flex-start;gap:.4rem;"><i class="fas fa-check" style="color:${color};margin-top:.15rem;font-size:.6rem;flex-shrink:0;"></i>${f}</li>`).join('')}
            </ul>
            <button ${onClick} style="display:block;width:100%;text-align:center;padding:.6rem;border-radius:.6rem;font-size:.82rem;font-weight:700;cursor:pointer;margin-top:auto;${btnStyle}">
                Upgrade →
            </button>
        </div>`;
    }

    // ── Global 402 interceptor ───────────────────────────────────────────────
    // Save original fetch before patching
    const _origFetch = window.fetch.bind(window);

    window.fetch = async function (...args) {
        const response = await _origFetch(...args);

        if (response.status === 402) {
            // Clone so the original can still be read by the caller
            const clone = response.clone();
            try {
                const data = await clone.json();
                if (data && data.error === 'limit_reached') {
                    showUpgradeModal(
                        data.feature   || 'feature',
                        data.used      || 0,
                        data.limit     || 0,
                    );
                    // Refresh usage state so counters update immediately
                    setTimeout(refresh, 800);
                }
            } catch (_) {}
        }

        return response;
    };

    // ── DOM-ready: load state and refresh ───────────────────────────────────
    _loadFromStorage();

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _onReady);
    } else {
        _onReady();
    }

    function _onReady() {
        // Refresh from server if user is logged in
        if (localStorage.getItem('pipways_token')) {
            refresh().then(() => _updateAllBadges());
        }

        // Expose globally
        global.PipwaysUsage = PipwaysUsage;

        // Re-render badges whenever the state module fires a custom event
        document.addEventListener('pipways:usage-updated', _updateAllBadges);
    }

    // Expose now (even before DOMContentLoaded) so other scripts can call .can()
    global.PipwaysUsage = PipwaysUsage;

})(window);


/* ═══════════════════════════════════════════════════════════════════════════════
   HOW TO USE IN YOUR FEATURE ROUTES (HTML/JS)

   1. Load this file in <head> or before your feature scripts:
      <script src="/js/usage.js"></script>

   2. Guard any feature button:
      if (!PipwaysUsage.can('chart_analysis')) {
          PipwaysUsage.showUpgradeModal('chart_analysis', PipwaysUsage.used('chart_analysis'), PipwaysUsage.limit('chart_analysis'));
          return;
      }

   3. Show a usage badge in any container:
      PipwaysUsage.renderBadge('chart_analysis', document.getElementById('chart-usage-bar'));

      Or with HTML data attribute (auto-renders and auto-updates):
      <div data-usage-badge="chart_analysis"></div>
      <div data-usage-badge="ai_mentor" data-usage-compact="true"></div>

   4. After a feature successfully runs, refresh state:
      await someFeatureApiCall();
      PipwaysUsage.refresh();    // updates counters on page without reload

   5. The 402 interceptor is automatic — no extra code needed.
      Any fetch() that returns 402 with { error: "limit_reached" }
      will automatically show the upgrade modal.

   BACKEND INTEGRATION:
   Add this one line at the top of any gated route:
       await check_and_record_usage(current_user["id"], "chart_analysis")

   That's it. The rest is automatic.
═══════════════════════════════════════════════════════════════════════════════ */
