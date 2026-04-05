/**
 * payments.js — Paystack Integration for Pipways
 *
 * Loads plans from /payments/plans, shows a pricing modal,
 * then uses Paystack Inline to collect payment without leaving the page.
 *
 * Dependencies (add to dashboard.html before this file):
 *   <script src="https://js.paystack.co/v1/inline.js"></script>
 *
 * Usage:
 *   PaymentsPage.showUpgradeModal()          — from any 402 error handler
 *   PaymentsPage.render(container)           — full pricing page
 */

// ── Inline helpers (avoid dependency on ui.js / store.js) ──────────────────
const _pw = {
    _toastBox: null,
    _ensureToastBox() {
        if (this._toastBox) return this._toastBox;
        let box = document.getElementById('pw-toast-container');
        if (!box) {
            box = document.createElement('div');
            box.id = 'pw-toast-container';
            box.style.cssText = 'position:fixed;bottom:2rem;right:2rem;z-index:9999;display:flex;flex-direction:column;gap:.75rem;';
            document.body.appendChild(box);
        }
        this._toastBox = box;
        return box;
    },
    toast(msg, type = 'info') {
        const colors = { success:'#10b981', error:'#ef4444', warning:'#f59e0b', info:'#3b82f6' };
        const t = document.createElement('div');
        t.style.cssText = `background:#1f2937;color:#f3f4f6;border-left:4px solid ${colors[type]||colors.info};padding:.75rem 1.25rem;border-radius:.5rem;box-shadow:0 4px 12px rgba(0,0,0,.3);min-width:260px;max-width:400px;display:flex;justify-content:space-between;align-items:center;`;
        t.innerHTML = `<span>${msg}</span><button onclick="this.parentElement.remove()" style="background:none;border:none;cursor:pointer;font-size:1.25rem;color:#9ca3af;margin-left:.75rem;">&times;</button>`;
        this._ensureToastBox().appendChild(t);
        setTimeout(() => { if (t.parentElement) t.remove(); }, 5000);
    },
    modal(content) {
        const m = document.createElement('div');
        m.className = 'pw-modal-overlay';
        m.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.6);z-index:1000;display:flex;align-items:center;justify-content:center;padding:1rem;';
        m.innerHTML = `<div style="background:#1f2937;color:#f3f4f6;border-radius:1rem;max-width:600px;width:100%;max-height:90vh;overflow-y:auto;box-shadow:0 25px 50px -12px rgba(0,0,0,.4);position:relative;">
            <button onclick="this.closest('.pw-modal-overlay').remove()" style="position:absolute;top:1rem;right:1rem;background:none;border:none;font-size:1.5rem;cursor:pointer;color:#9ca3af;">&times;</button>
            <div style="padding:2rem;">${content}</div></div>`;
        m.addEventListener('click', e => { if (e.target === m) m.remove(); });
        document.body.appendChild(m);
    },
    closeModal() { document.querySelectorAll('.pw-modal-overlay').forEach(m => m.remove()); }
};

// Provide global UI/Router shims if they don't already exist
if (typeof UI === 'undefined') {
    window.UI = { showToast: (m,t) => _pw.toast(m,t), showModal: c => _pw.modal(c), closeModal: () => _pw.closeModal() };
}
if (typeof Router === 'undefined') {
    window.Router = { navigate(path) { window.location.href = path; } };
}

const PaymentsPage = {

    _plans: null,
    _publicKey: null,

    // ── Hardcoded fallback plans (shown if backend is unreachable) ────────
    _fallbackPlans: {
        pro_monthly: {
            name: 'Pro Monthly', tier: 'pro', amount_ngn: 5000, amount: 500000,
            interval: 'monthly', description: 'Unlimited AI Mentor, Chart Analysis, Performance Analytics, Signals + Telegram',
            features: ['Unlimited AI Mentor sessions', '20 Chart Analyses per month', 'Unlimited Performance Analytics', 'Full trading signals + Telegram alerts', 'Webinar recordings access']
        },
        pro_yearly: {
            name: 'Pro Yearly', tier: 'pro', amount_ngn: 45000, amount: 4500000,
            interval: 'annually', description: 'Everything in Pro, billed yearly. Save N15,000.',
            features: ['Everything in Pro Monthly', 'Save N15,000 vs monthly billing', 'Priority AI response speed']
        },
        power_monthly: {
            name: 'Power Trader', tier: 'pro_plus', amount_ngn: 12000, amount: 1200000,
            interval: 'monthly', description: 'Everything Pro + unlimited Chart Analysis + AI Stock Terminal',
            features: ['Everything in Pro', 'Unlimited Chart Analyses', 'AI Stock Research Terminal', 'Earliest access to new features']
        }
    },

    // ── Load config from backend (with timeout) ────────────────────────────
    async _loadConfig() {
        if (this._plans && this._publicKey) return;

        const timeout = (ms) => new Promise((_, reject) =>
            setTimeout(() => reject(new Error('timeout')), ms));

        try {
            const config = await Promise.race([
                API.request('/payments/config'),
                timeout(8000)
            ]);
            this._publicKey = config.public_key;
        } catch (e) {
            console.warn('[Payments] Config unavailable:', e.message || e);
        }

        try {
            const full = await Promise.race([
                API.request('/payments/plans'),
                timeout(8000)
            ]);
            if (full && typeof full === 'object' && Object.keys(full).length > 0) {
                this._plans = full;
            }
        } catch (e) {
            console.warn('[Payments] Plans unavailable, using fallback:', e.message || e);
        }

        // Always fall back to hardcoded plans if backend didn't return any
        if (!this._plans) {
            this._plans = this._fallbackPlans;
        }
    },

    // ── Full pricing page ───────────────────────────────────────────────────
    async render(container) {
        container.innerHTML = `
            <div class="page-header">
                <h1>Upgrade Your Account</h1>
                <p style="color:#6b7280;">Choose a plan to unlock AI tools, signals, and more</p>
            </div>
            <div id="plans-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.5rem;margin-top:2rem;">
                <div style="text-align:center;padding:3rem;color:#9ca3af;">
                    <i class="fas fa-spinner fa-spin text-2xl"></i>
                    <p style="margin-top:1rem;">Loading plans…</p>
                </div>
            </div>
        `;
        try {
            await this._loadConfig();
        } catch (e) {
            console.error('[Payments] render failed:', e);
        }
        const grid = document.getElementById('plans-grid');
        if (grid) this._renderPlanCards(grid);
    },

    _renderPlanCards(container) {
        if (!this._plans) {
            container.innerHTML = '<p style="color:#ef4444;">Failed to load plans. Please try again.</p>';
            return;
        }

        const user = JSON.parse(localStorage.getItem('pipways_user') || 'null');
        const currentTier = user?.subscription_tier || 'free';

        const planOrder = ['pro_monthly', 'pro_yearly', 'power_monthly'];
        const badges = {
            'pro_yearly': { text: 'Best Value', color: '#10b981' },
            'pro_monthly': { text: 'Most Popular', color: '#3b82f6' },
        };

        container.innerHTML = planOrder.map(key => {
            const plan = this._plans[key];
            if (!plan) return '';
            const isActive = currentTier === plan.tier;
            const badge = badges[key];

            return `
            <div style="background:#111827;border-radius:1rem;padding:2rem;border:2px solid ${isActive ? '#3b82f6' : '#1f2937'};
                        position:relative;box-shadow:0 1px 3px rgba(0,0,0,.3);transition:box-shadow .2s, border-color .2s;"
                 onmouseover="this.style.boxShadow='0 10px 25px rgba(0,0,0,.4)';this.style.borderColor='#374151'"
                 onmouseout="this.style.boxShadow='0 1px 3px rgba(0,0,0,.3)';this.style.borderColor='${isActive ? '#3b82f6' : '#1f2937'}'">

                ${badge ? `<div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);
                    background:${badge.color};color:white;font-size:.75rem;font-weight:700;
                    padding:.25rem .75rem;border-radius:99px;">${badge.text}</div>` : ''}

                ${isActive ? `<div style="position:absolute;top:-12px;right:1rem;
                    background:#10b981;color:white;font-size:.75rem;font-weight:700;
                    padding:.25rem .75rem;border-radius:99px;">Current Plan</div>` : ''}

                <h3 style="font-size:1.25rem;font-weight:700;color:#f9fafb;margin-bottom:.5rem;">
                    ${plan.name}
                </h3>
                <p style="color:#9ca3af;font-size:.875rem;margin-bottom:1.5rem;">${plan.description}</p>

                <div style="margin-bottom:1.5rem;">
                    <span style="font-size:2.25rem;font-weight:800;color:#f9fafb;">
                        ₦${plan.amount_ngn.toLocaleString()}
                    </span>
                    <span style="color:#9ca3af;font-size:.875rem;">
                        /${plan.interval === 'annually' ? 'year' : 'month'}
                    </span>
                </div>

                <ul style="list-style:none;padding:0;margin-bottom:1.5rem;">
                    ${(plan.features || []).map(f => `
                        <li style="display:flex;align-items:center;gap:.5rem;padding:.375rem 0;
                                   font-size:.875rem;color:#d1d5db;border-bottom:1px solid #1f2937;">
                            <i class="fas fa-check" style="color:#10b981;flex-shrink:0;"></i>
                            ${f}
                        </li>
                    `).join('')}
                </ul>

                ${isActive
                    ? `<button disabled style="width:100%;padding:.75rem;border-radius:.5rem;
                          background:#1f2937;color:#9ca3af;border:none;font-weight:600;cursor:default;">
                          Active Plan
                       </button>`
                    : `<button onclick="PaymentsPage.startPayment('${key}')"
                          style="width:100%;padding:.75rem;border-radius:.5rem;
                                 background:#3b82f6;color:white;border:none;font-weight:700;
                                 cursor:pointer;font-size:.9rem;transition:background .2s;"
                          onmouseover="this.style.background='#2563eb'"
                          onmouseout="this.style.background='#3b82f6'">
                          Upgrade to ${plan.tier.charAt(0).toUpperCase() + plan.tier.slice(1)}
                       </button>`
                }
            </div>`;
        }).join('');
    },

    // ── Quick upgrade modal (shown on 402 errors) ───────────────────────────
    async showUpgradeModal(featureName = 'this feature') {
        await this._loadConfig();

        const user = JSON.parse(localStorage.getItem('pipways_user') || 'null');
        const currentTier = user?.subscription_tier || 'free';

        // Suggest pro_monthly as default upgrade
        const suggestedKey = currentTier === 'pro' ? 'power_monthly' : 'pro_monthly';
        const plan = this._plans?.[suggestedKey];

        UI.showModal(`
            <div style="text-align:center;padding:1rem 0 1.5rem;">
                <div style="font-size:2.5rem;margin-bottom:1rem;">🔒</div>
                <h2 style="font-size:1.4rem;font-weight:700;color:#111827;margin-bottom:.5rem;">
                    Upgrade to unlock ${featureName}
                </h2>
                <p style="color:#6b7280;font-size:.9rem;margin-bottom:1.5rem;">
                    You've reached your free tier limit.
                </p>

                ${plan ? `
                <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:.75rem;
                            padding:1.25rem;margin-bottom:1.5rem;text-align:left;">
                    <div style="font-weight:700;color:#111827;">${plan.name}</div>
                    <div style="font-size:1.5rem;font-weight:800;color:#3b82f6;margin:.25rem 0;">
                        ₦${plan.amount_ngn?.toLocaleString()}<span style="font-size:.875rem;color:#9ca3af;">/${plan.interval === 'annually' ? 'year' : 'month'}</span>
                    </div>
                    <ul style="list-style:none;padding:0;margin:.75rem 0 0;">
                        ${(plan.features || []).slice(0, 3).map(f => `
                            <li style="font-size:.8rem;color:#374151;padding:.2rem 0;">
                                <i class="fas fa-check" style="color:#10b981;margin-right:.4rem;"></i>${f}
                            </li>
                        `).join('')}
                    </ul>
                </div>

                <button onclick="UI.closeModal(); PaymentsPage.startPayment('${suggestedKey}')"
                    style="width:100%;padding:.85rem;border-radius:.5rem;background:#3b82f6;
                           color:white;border:none;font-weight:700;cursor:pointer;font-size:1rem;">
                    Upgrade Now — ₦${plan.amount_ngn?.toLocaleString()}
                </button>
                <button onclick="UI.closeModal()"
                    style="width:100%;margin-top:.75rem;padding:.7rem;border-radius:.5rem;
                           background:none;color:#9ca3af;border:1px solid #e5e7eb;cursor:pointer;">
                    Maybe Later
                </button>
                ` : `
                <button onclick="UI.closeModal(); Router.navigate('/pricing')"
                    style="width:100%;padding:.85rem;border-radius:.5rem;background:#3b82f6;
                           color:white;border:none;font-weight:700;cursor:pointer;">
                    View Plans
                </button>`}
            </div>
        `);
    },

    // ── Paystack Inline popup ───────────────────────────────────────────────
    async startPayment(planKey) {
        await this._loadConfig();

        const user = JSON.parse(localStorage.getItem('pipways_user') || 'null');
        if (!user) {
            UI.showToast('Please log in to upgrade', 'warning');
            return;
        }

        if (!this._publicKey) {
            UI.showToast('Payment system unavailable — contact support', 'error');
            return;
        }

        const plan = this._plans?.[planKey];
        if (!plan) {
            UI.showToast('Plan not found', 'error');
            return;
        }

        // Get a reference from backend (backend stores metadata)
        let reference;
        try {
            const init = await API.request('/payments/initiate', {
                method: 'POST',
                body: JSON.stringify({ plan_key: planKey }),
            });
            reference = init.reference;
        } catch (e) {
            UI.showToast('Could not start payment: ' + e.message, 'error');
            return;
        }

        // Paystack Inline popup
        const handler = PaystackPop.setup({
            key:       this._publicKey,
            email:     user.email,
            amount:    plan.amount,          // kobo
            currency:  'NGN',
            ref:       reference,
            metadata: {
                user_id:  user.id,
                plan_key: planKey,
            },
            onClose() {
                UI.showToast('Payment window closed', 'info');
            },
            callback: async (response) => {
                // Verify on backend
                try {
                    const result = await API.request(`/payments/verify/${response.reference}`);
                    UI.showToast(result.message || 'Payment successful!', 'success');

                    // Update local user object with new tier
                    const updated = { ...user, subscription_tier: result.tier };
                    localStorage.setItem('pipways_user', JSON.stringify(updated));

                    // Redirect to dashboard
                    setTimeout(() => Router.navigate('/dashboard'), 1500);
                } catch (err) {
                    UI.showToast('Payment received but verification failed — contact support', 'warning');
                }
            },
        });

        handler.openIframe();
    },
};

window.PaymentsPage = PaymentsPage;

// ── REMOVED: 402 handler monkey-patch ────────────────────────────────────────
// This monkey-patch of API.request has been removed to avoid conflicts with the
// canonical 402 handler in /js/api.js. The API.request method now handles all
// 402 responses directly and calls PaymentsPage.showUpgradeModal when needed.
// See: /js/api.js lines ~50-66 for the primary 402 handler
