/**
 * email_settings.js — Email Preferences Panel
 *
 * Renders a settings panel for users to control which emails they receive.
 * Call EmailSettings.render(container) from your settings section.
 *
 * Also auto-inserts a small "Email Notifications" card into the dashboard
 * sidebar if #email-settings-anchor exists in the DOM.
 */

const EmailSettings = {

    _prefs: null,

    async render(container) {
        if (!container) return;
        container.innerHTML = `
            <div style="max-width:560px;">
                <h3 style="color:white;font-size:1rem;font-weight:700;margin:0 0 4px;">
                    Email Notifications
                </h3>
                <p style="color:#6b7280;font-size:.85rem;margin:0 0 20px;">
                    Choose which emails Pipways sends you.
                </p>
                <div id="email-prefs-body" style="display:flex;flex-direction:column;gap:1px;
                     background:#1f2937;border-radius:.75rem;overflow:hidden;border:1px solid #374151;">
                    <div style="text-align:center;padding:2rem;color:#6b7280;font-size:.85rem;">
                        <i class="fas fa-spinner fa-spin"></i> Loading preferences…
                    </div>
                </div>
                <button id="email-prefs-save" onclick="EmailSettings.save()"
                    style="margin-top:1rem;padding:.7rem 1.5rem;border-radius:.5rem;
                           background:#7c3aed;color:white;border:none;font-weight:700;
                           font-size:.875rem;cursor:pointer;display:none;">
                    Save Preferences
                </button>
                <p id="email-prefs-saved" style="display:none;margin-top:.5rem;
                   color:#34d399;font-size:.8rem;">✓ Saved</p>
            </div>`;

        await this._load();
        this._renderRows();
    },

    async _load() {
        try {
            this._prefs = await API.request('/email/preferences');
        } catch (_) {
            this._prefs = {
                welcome: true,
                lesson_complete: true,
                certificate: true,
                signal_alerts: false,
                weekly_digest: false,
                promotions: false,
            };
        }
    },

    _rows: [
        { key: 'welcome',        label: 'Welcome email',        desc: 'Sent once when you first sign up',  locked: true },
        { key: 'lesson_complete',label: 'Lesson completions',   desc: 'A nudge when you finish a lesson + what\'s next' },
        { key: 'certificate',    label: 'Certificate earned',   desc: 'Congratulations email with your cert number' },
        { key: 'signal_alerts',  label: 'Signal alerts',        desc: 'Email when a new trading signal is posted (opt-in)' },
        { key: 'weekly_digest',  label: 'Weekly digest',        desc: 'Summary of signals, new lessons and blog posts' },
        { key: 'promotions',     label: 'Promotions & offers',  desc: 'Special deals and platform updates' },
    ],

    _renderRows() {
        const body = document.getElementById('email-prefs-body');
        const save = document.getElementById('email-prefs-save');
        if (!body || !this._prefs) return;

        body.innerHTML = this._rows.map(row => `
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:14px 18px;background:#111827;">
            <div>
                <div style="color:${row.locked ? '#6b7280' : 'white'};font-size:.875rem;font-weight:600;">
                    ${row.label}
                    ${row.locked ? '<span style="font-size:.7rem;color:#4b5563;margin-left:4px;">(always on)</span>' : ''}
                </div>
                <div style="color:#6b7280;font-size:.78rem;margin-top:2px;">${row.desc}</div>
            </div>
            <label style="position:relative;display:inline-block;width:42px;height:24px;flex-shrink:0;margin-left:16px;">
                <input type="checkbox" id="pref-${row.key}"
                    ${this._prefs[row.key] ? 'checked' : ''}
                    ${row.locked ? 'disabled' : ''}
                    onchange="EmailSettings._onChange()"
                    style="opacity:0;width:0;height:0;position:absolute;">
                <span onclick="if(!this.previousElementSibling.disabled){this.previousElementSibling.click()}"
                    style="position:absolute;cursor:${row.locked ? 'default' : 'pointer'};
                           top:0;left:0;right:0;bottom:0;border-radius:34px;transition:.3s;
                           background:${this._prefs[row.key] ? '#7c3aed' : '#374151'};"
                    id="toggle-${row.key}">
                    <span style="position:absolute;height:18px;width:18px;left:${this._prefs[row.key] ? '21px' : '3px'};
                                 bottom:3px;background:white;border-radius:50%;transition:.3s;"></span>
                </span>
            </label>
        </div>`).join('');

        if (save) save.style.display = 'none';

        // Wire toggles to visual update
        this._rows.forEach(row => {
            const cb = document.getElementById(`pref-${row.key}`);
            if (cb && !row.locked) {
                cb.addEventListener('change', () => {
                    const track  = document.getElementById(`toggle-${row.key}`);
                    const thumb  = track?.querySelector('span');
                    if (track)  track.style.background  = cb.checked ? '#7c3aed' : '#374151';
                    if (thumb)  thumb.style.left         = cb.checked ? '21px' : '3px';
                });
            }
        });
    },

    _onChange() {
        const save = document.getElementById('email-prefs-save');
        const saved = document.getElementById('email-prefs-saved');
        if (save)  save.style.display  = 'inline-block';
        if (saved) saved.style.display = 'none';
    },

    async save() {
        const updated = {};
        this._rows.forEach(row => {
            const cb = document.getElementById(`pref-${row.key}`);
            updated[row.key] = cb ? cb.checked : (this._prefs[row.key] ?? false);
        });

        try {
            await API.request('/email/preferences', {
                method: 'POST',
                body: JSON.stringify(updated),
            });
            this._prefs = updated;
            const save  = document.getElementById('email-prefs-save');
            const saved = document.getElementById('email-prefs-saved');
            if (save)  save.style.display  = 'none';
            if (saved) { saved.style.display = 'block'; setTimeout(() => saved.style.display = 'none', 3000); }
            if (typeof UI !== 'undefined') UI.showToast('Email preferences saved', 'success');
        } catch (e) {
            if (typeof UI !== 'undefined') UI.showToast('Save failed: ' + e.message, 'error');
        }
    },
};

window.EmailSettings = EmailSettings;
