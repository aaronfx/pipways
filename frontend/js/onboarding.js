/**
 * onboarding.js — Post-Registration Onboarding Flow
 *
 * Shows a 3-step skill assessment to new users right after registration.
 * Routes them to the correct Academy level based on their answers.
 * Uses only the existing Academy levels in the DB.
 *
 * Trigger: call Onboarding.init() inside DashboardController.init()
 * after checkAuth() — it self-dismisses if the user has prior progress.
 *
 * Usage:
 *   <script src="/js/onboarding.js"></script>
 *   // In DashboardController.init():
 *   Onboarding.init(this.user);
 */

const Onboarding = {

    _quiz: [
        {
            q: "How long have you been trading forex?",
            options: [
                { text: "I'm just starting out",     score: 0 },
                { text: "Less than 6 months",         score: 1 },
                { text: "6 months to 2 years",        score: 2 },
                { text: "More than 2 years",           score: 3 },
            ],
        },
        {
            q: "Which of these do you understand?",
            options: [
                { text: "Nothing yet — complete beginner", score: 0 },
                { text: "Pips, lots and basic charts",      score: 1 },
                { text: "Support/resistance + indicators",  score: 2 },
                { text: "SMC, order blocks, liquidity",     score: 3 },
            ],
        },
        {
            q: "What is your main goal?",
            options: [
                { text: "Learn the basics from scratch",   score: 0 },
                { text: "Improve my win rate",             score: 1 },
                { text: "Build a consistent strategy",     score: 2 },
                { text: "Trade like the institutions",     score: 3 },
            ],
        },
    ],

    _answers: [],
    _step: 0,

    // ── Entry point ─────────────────────────────────────────────────────────
    async init(user) {
        if (!user) return;
        // FIX: guard against the API shim not yet being available — onboarding.js
        // loads after the shim in dashboard.html but guard defensively anyway.
        if (typeof API === 'undefined') {
            console.warn('[Onboarding] API shim not ready — skipping');
            return;
        }
        // Skip if user has been here before (flag in localStorage)
        const key = `pipways_onboarded_${user.id}`;
        if (localStorage.getItem(key)) return;

        // Also skip if user already has academy progress
        try {
            const progress = await API.request(`/learning/progress/${user.id}`);
            // FIX: progress shape was assumed to be an object with completed_lessons.
            // If the endpoint returns an array, the check would evaluate NaN > 0 = false
            // and never skip onboarding for returning users. Handle both shapes.
            const completedCount = progress?.completed_lessons
                ?? (Array.isArray(progress) ? progress.length : 0);
            if (completedCount > 0) {
                localStorage.setItem(key, '1');
                return;
            }
        } catch (_) { /* non-fatal */ }

        this._answers = [];
        this._step    = 0;
        this._user    = user;
        this._render();
    },

    // ── Render quiz modal ───────────────────────────────────────────────────
    _render() {
        // Remove any existing modal
        document.getElementById('onboarding-overlay')?.remove();

        const overlay = document.createElement('div');
        overlay.id = 'onboarding-overlay';
        overlay.style.cssText = [
            'position:fixed', 'inset:0', 'background:rgba(0,0,0,.85)',
            'z-index:10010', 'display:flex', 'align-items:center',
            'justify-content:center', 'padding:1rem',
        ].join(';');

        overlay.innerHTML = this._html();
        document.body.appendChild(overlay);
    },

    _html() {
        const total   = this._quiz.length;
        const current = this._quiz[this._step];
        const pct     = Math.round((this._step / total) * 100);

        return `
        <div style="background:#111827;border-radius:1rem;width:100%;max-width:520px;
                    border:1px solid #374151;overflow:hidden;">

            <!-- Header -->
            <div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:24px 28px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <h2 style="color:white;font-size:1.1rem;font-weight:700;margin:0;">
                        📚 Quick Skill Check
                    </h2>
                    <span style="color:rgba(255,255,255,.7);font-size:.8rem;">
                        ${this._step + 1} of ${total}
                    </span>
                </div>
                <!-- Progress bar -->
                <div style="background:rgba(255,255,255,.2);border-radius:99px;height:4px;">
                    <div style="background:white;height:4px;border-radius:99px;width:${pct}%;transition:width .3s;"></div>
                </div>
            </div>

            <!-- Question -->
            <div style="padding:28px;">
                <p style="color:white;font-size:1rem;font-weight:600;margin:0 0 20px;">
                    ${current.q}
                </p>
                <div style="display:flex;flex-direction:column;gap:10px;">
                    ${current.options.map((opt, i) => `
                    <button onclick="Onboarding._answer(${opt.score})"
                        style="text-align:left;padding:12px 16px;border-radius:.5rem;
                               border:1px solid #374151;background:#1f2937;color:#d1d5db;
                               cursor:pointer;font-size:.9rem;transition:all .15s;"
                        onmouseover="this.style.borderColor='#7c3aed';this.style.background='rgba(124,58,237,.15)';this.style.color='white'"
                        onmouseout="this.style.borderColor='#374151';this.style.background='#1f2937';this.style.color='#d1d5db'">
                        ${opt.text}
                    </button>
                    `).join('')}
                </div>
            </div>

            <!-- Skip -->
            <div style="padding:0 28px 20px;text-align:center;">
                <button onclick="Onboarding._skip()"
                    style="background:none;border:none;color:#6b7280;font-size:.8rem;
                           cursor:pointer;text-decoration:underline;">
                    Skip — take me to the beginning
                </button>
            </div>
        </div>`;
    },

    // ── Record answer and advance ───────────────────────────────────────────
    _answer(score) {
        this._answers.push(score);
        this._step++;

        if (this._step < this._quiz.length) {
            this._render();
        } else {
            this._finish();
        }
    },

    _skip() {
        document.getElementById('onboarding-overlay')?.remove();
        this._markDone();
        // Navigate to first lesson of Beginner level
        this._goToLesson(null, 'beginner');
    },

    // ── Compute result and show destination ─────────────────────────────────
    async _finish() {
        const total = this._answers.reduce((a, b) => a + b, 0);
        const max   = this._quiz.length * 3;
        const pct   = total / max;

        let level, label, color;
        if (pct < 0.33) {
            level = 'beginner'; label = 'Beginner';   color = '#34d399';
        } else if (pct < 0.66) {
            level = 'intermediate'; label = 'Intermediate'; color = '#60a5fa';
        } else {
            level = 'advanced'; label = 'Advanced';   color = '#a78bfa';
        }

        // Show result screen
        const overlay = document.getElementById('onboarding-overlay');
        if (!overlay) return;
        overlay.querySelector('div').innerHTML = `
            <div style="padding:36px;text-align:center;">
                <div style="font-size:3rem;margin-bottom:12px;">🎯</div>
                <h2 style="color:white;font-size:1.3rem;font-weight:700;margin-bottom:8px;">
                    We've placed you in
                </h2>
                <div style="display:inline-block;background:${color}22;border:1px solid ${color};
                            border-radius:99px;padding:8px 24px;margin-bottom:16px;">
                    <span style="color:${color};font-weight:700;font-size:1.1rem;">${label} Level</span>
                </div>
                <p style="color:#9ca3af;font-size:.9rem;margin-bottom:28px;">
                    We'll start you here and adapt as you progress.
                    You can always jump between levels in the Academy.
                </p>
                <button onclick="Onboarding._goToLesson(null, '${level}')"
                    style="width:100%;padding:14px;border-radius:.5rem;
                           background:#7c3aed;color:white;border:none;
                           font-weight:700;font-size:1rem;cursor:pointer;">
                    Start ${label} Curriculum →
                </button>
                <button onclick="Onboarding._skip()"
                    style="width:100%;margin-top:10px;padding:10px;border-radius:.5rem;
                           background:none;color:#6b7280;border:1px solid #374151;cursor:pointer;font-size:.85rem;">
                    Browse all levels
                </button>
            </div>
        `;
    },

    // ── Navigate to Academy with the right level selected ───────────────────
    async _goToLesson(lessonId, levelName) {
        document.getElementById('onboarding-overlay')?.remove();
        this._markDone();

        // Store recommended level so academy.html can auto-select it
        if (levelName) {
            localStorage.setItem('pipways_recommended_level', levelName);
        }

        // Navigate to Academy
        window.location.href = '/academy.html';
    },

    _markDone() {
        if (this._user) {
            localStorage.setItem(`pipways_onboarded_${this._user.id}`, '1');
        }
    },
};

window.Onboarding = Onboarding;
