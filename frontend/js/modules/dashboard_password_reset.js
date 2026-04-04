// Dashboard Module: Password Reset
// Extracted from dashboard.js for maintainability

DashboardController.prototype.checkResetToken = function() {
    const params = new URLSearchParams(window.location.search);
    const token  = params.get('reset_token');
    if (!token) return false;
    // Remove token from URL immediately (single-use — don't expose in history)
    history.replaceState({}, '', window.location.pathname);
    this._showResetModal(token);
    return true; // signals init() to skip auth check
};

DashboardController.prototype._showResetModal = function(token) {
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
};

DashboardController.prototype._renderResetForm = function(area, token) {
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
};

DashboardController.prototype._checkPwStrength = function(pw) {
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
};

DashboardController.prototype._checkPwMatch = function() {
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
};

DashboardController.prototype.submitPasswordReset = async function(token) {
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
};

