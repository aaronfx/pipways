/**
 * Gopipways — Forgot Password Modal
 * Drop-in script for the login page.
 *
 * Usage:
 *   1. Add <script src="/js/forgot_password.js"></script> to your login HTML
 *   2. Make sure your "Forgot password?" element has id="forgot-password-link"
 *      OR call ForgotPassword.show() from any click handler
 *
 * Calls: POST /email/forgot-password { email }
 */
const ForgotPassword = (() => {

    function _createModal() {
        if (document.getElementById('fp-overlay')) return;
        const overlay = document.createElement('div');
        overlay.id = 'fp-overlay';
        overlay.style.cssText = `
            position:fixed;inset:0;z-index:9999;
            background:rgba(0,0,0,.75);
            display:flex;align-items:center;justify-content:center;
            padding:20px;opacity:0;transition:opacity .2s;`;
        overlay.innerHTML = `
            <div id="fp-modal" style="
                background:#1f2937;border-radius:14px;padding:32px;
                width:100%;max-width:420px;border:1px solid #374151;
                transform:translateY(12px);transition:transform .2s;">

                <!-- Header -->
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px;">
                    <div>
                        <h2 style="margin:0 0 4px;color:white;font-size:20px;font-weight:700;">
                            Reset your password
                        </h2>
                        <p id="fp-subtitle" style="margin:0;color:#9ca3af;font-size:14px;">
                            Enter your email and we'll send you a reset link.
                        </p>
                    </div>
                    <button onclick="ForgotPassword.close()" style="
                        background:none;border:none;color:#6b7280;cursor:pointer;
                        font-size:20px;padding:0 0 0 12px;line-height:1;">✕</button>
                </div>

                <!-- Step 1 — email input -->
                <div id="fp-step-1">
                    <div style="margin-bottom:16px;">
                        <label style="display:block;color:#9ca3af;font-size:13px;margin-bottom:6px;">
                            Email address
                        </label>
                        <input type="email" id="fp-email" placeholder="you@example.com"
                            style="width:100%;padding:11px 14px;background:#374151;
                                   border:1px solid #4b5563;border-radius:8px;
                                   color:white;font-size:14px;box-sizing:border-box;
                                   outline:none;transition:border-color .15s;"
                            onfocus="this.style.borderColor='#7c3aed'"
                            onblur="this.style.borderColor='#4b5563'"
                            onkeydown="if(event.key==='Enter') ForgotPassword.submit()">
                    </div>
                    <p id="fp-error" style="color:#ef4444;font-size:13px;margin:0 0 12px;display:none;"></p>
                    <button id="fp-submit-btn" onclick="ForgotPassword.submit()" style="
                        width:100%;padding:12px;
                        background:linear-gradient(135deg,#667eea,#764ba2);
                        color:white;border:none;border-radius:8px;
                        font-weight:700;font-size:15px;cursor:pointer;
                        transition:opacity .2s;">
                        Send Reset Link →
                    </button>
                    <div style="text-align:center;margin-top:16px;">
                        <button onclick="ForgotPassword.close()" style="
                            background:none;border:none;color:#6b7280;
                            font-size:13px;cursor:pointer;text-decoration:underline;">
                            Back to login
                        </button>
                    </div>
                </div>

                <!-- Step 2 — success state -->
                <div id="fp-step-2" style="display:none;text-align:center;">
                    <div style="font-size:48px;margin-bottom:16px;">📬</div>
                    <h3 style="color:white;margin:0 0 8px;font-size:18px;font-weight:700;">
                        Check your inbox
                    </h3>
                    <p style="color:#9ca3af;font-size:14px;line-height:1.6;margin:0 0 20px;">
                        If <strong id="fp-sent-to" style="color:white;"></strong>
                        is registered, a reset link is on its way.<br>
                        Check your spam folder if it doesn't arrive within a minute.
                    </p>
                    <button onclick="ForgotPassword.close()" style="
                        background:linear-gradient(135deg,#667eea,#764ba2);
                        color:white;border:none;border-radius:8px;
                        padding:11px 28px;font-weight:700;font-size:14px;cursor:pointer;">
                        Back to Login
                    </button>
                </div>

            </div>`;

        // Close on backdrop click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) ForgotPassword.close();
        });
        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') ForgotPassword.close();
        });

        document.body.appendChild(overlay);
        // Animate in
        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
            document.getElementById('fp-modal').style.transform = 'translateY(0)';
        });
    }

    function show() {
        _createModal();
        // Reset to step 1 state
        const step1 = document.getElementById('fp-step-1');
        const step2 = document.getElementById('fp-step-2');
        const emailEl = document.getElementById('fp-email');
        const errEl   = document.getElementById('fp-error');
        const btn     = document.getElementById('fp-submit-btn');
        if (step1)   step1.style.display = 'block';
        if (step2)   step2.style.display = 'none';
        if (emailEl) { emailEl.value = ''; emailEl.disabled = false; }
        if (errEl)   { errEl.textContent = ''; errEl.style.display = 'none'; }
        if (btn)     { btn.disabled = false; btn.textContent = 'Send Reset Link →'; btn.style.opacity = '1'; }
        setTimeout(() => document.getElementById('fp-email')?.focus(), 100);
    }

    function close() {
        const overlay = document.getElementById('fp-overlay');
        if (!overlay) return;
        overlay.style.opacity = '0';
        setTimeout(() => overlay.remove(), 200);
    }

    async function submit() {
        const emailEl = document.getElementById('fp-email');
        const errEl   = document.getElementById('fp-error');
        const btn     = document.getElementById('fp-submit-btn');
        const email   = emailEl?.value.trim() || '';

        // Basic validation
        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            if (errEl) { errEl.textContent = 'Please enter a valid email address.'; errEl.style.display = 'block'; }
            emailEl?.focus();
            return;
        }
        if (errEl) { errEl.textContent = ''; errEl.style.display = 'none'; }

        // Disable while sending
        if (btn)     { btn.disabled = true; btn.textContent = 'Sending…'; btn.style.opacity = '.6'; }
        if (emailEl)   emailEl.disabled = true;

        try {
            const res = await fetch('/email/forgot-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            // Always show success (endpoint never reveals if email exists — anti-enumeration)
            const step1  = document.getElementById('fp-step-1');
            const step2  = document.getElementById('fp-step-2');
            const sentTo = document.getElementById('fp-sent-to');
            if (step1)   step1.style.display = 'none';
            if (step2)   step2.style.display = 'block';
            if (sentTo)  sentTo.textContent  = email;
        } catch (err) {
            console.error('[ForgotPassword]', err);
            if (errEl) { errEl.textContent = 'Connection error — please try again.'; errEl.style.display = 'block'; }
            if (btn)   { btn.disabled = false; btn.textContent = 'Send Reset Link →'; btn.style.opacity = '1'; }
            if (emailEl) emailEl.disabled = false;
        }
    }

    // Auto-wire to the "Forgot password?" link on DOM ready
    document.addEventListener('DOMContentLoaded', () => {
        // Try common IDs and text patterns
        const candidates = [
            document.getElementById('forgot-password-link'),
            document.getElementById('forgot-password'),
            document.querySelector('[data-action="forgot-password"]'),
            ...[...document.querySelectorAll('a, button')].filter(el =>
                el.textContent.toLowerCase().includes('forgot password') ||
                el.textContent.toLowerCase().includes('forgot your password') ||
                el.textContent.toLowerCase().includes('reset password')
            )
        ].filter(Boolean);

        candidates.forEach(el => {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                ForgotPassword.show();
            });
        });

        if (candidates.length > 0) {
            console.log(`[ForgotPassword] Wired to ${candidates.length} element(s)`);
        } else {
            console.warn('[ForgotPassword] No forgot-password link found — call ForgotPassword.show() manually');
        }
    });

    return { show, close, submit };
})();
