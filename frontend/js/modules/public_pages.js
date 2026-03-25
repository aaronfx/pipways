/**
 * Pipways Public Pages — Complete Rebuild
 * Handles: Trading Signals, Webinars, Blog, and delegates Courses to CoursesPage
 *
 * Hooks directly into dashboard.html's existing:
 *   - #signals-container, #webinars-container, #blog-container, #courses-container
 *   - this.loadSignals(), this.loadWebinars(), this.loadBlog(), this.loadCourses()
 *
 * Usage: included as <script src="/js/modules/public_pages.js"></script>
 * Then in DashboardController override the load* methods:
 *   loadSignals  = () => PublicPages.signals('#signals-container', this)
 *   loadWebinars = () => PublicPages.webinars('#webinars-container', this)
 *   loadBlog     = () => PublicPages.blog('#blog-container', this)
 *   loadCourses  = () => PublicPages.courses('#courses-container', this)
 */

const PublicPages = (() => {

    // ── internal request helper ─────────────────────────────────────────────
    async function req(endpoint, ctrl) {
        const fn = ctrl?.apiRequest?.bind(ctrl);
        if (fn) return fn(endpoint);
        const token = localStorage.getItem('pipways_token');
        const res = await fetch(window.location.origin + endpoint, {
            headers: { Authorization: `Bearer ${token}`, Accept: 'application/json' }
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }
        return res.json();
    }

    // ── containers ──────────────────────────────────────────────────────────
    function el(id) {
        return document.getElementById(id)
            || document.querySelector(id)
            || document.getElementById(id.replace('#',''));
    }

    // ── ui helpers ───────────────────────────────────────────────────────────
    function spinner(id) {
        const c = el(id); if (!c) return;
        c.innerHTML = `<div class="col-span-full text-center py-12 text-gray-500">
            <i class="fas fa-spinner fa-spin text-2xl"></i>
        </div>`;
    }

    function empty(id, icon, msg) {
        const c = el(id); if (!c) return;
        c.innerHTML = `<div class="col-span-full text-center py-14 text-gray-500">
            <i class="fas ${icon} text-5xl mb-4 block opacity-20"></i>
            <p class="font-medium text-base">${msg}</p>
        </div>`;
    }

    function errBox(id, msg) {
        const c = el(id); if (!c) return;
        c.innerHTML = `<div class="col-span-full text-center py-10 text-gray-500">
            <i class="fas fa-exclamation-triangle text-red-500/50 text-3xl mb-3 block"></i>
            <p class="text-sm text-red-400">${msg}</p>
        </div>`;
    }

    // ── SIGNALS ──────────────────────────────────────────────────────────────
    async function signals(containerId = 'signals-container', ctrl = null) {
        spinner(containerId);
        try {
            const data = await req('/signals/active', ctrl);
            const list = Array.isArray(data) ? data : (data.signals || []);
            const c = el(containerId); if (!c) return;

            if (!list.length) {
                empty(containerId, 'fa-satellite-dish', 'No active signals at the moment');
                return;
            }

            c.innerHTML = list.map(s => {
                const isBuy = (s.direction || '').toUpperCase() === 'BUY';
                const dirCls = isBuy
                    ? 'bg-green-900/50 text-green-300 border border-green-700/60'
                    : 'bg-red-900/50 text-red-300 border border-red-700/60';

                const rr = s.entry_price && s.stop_loss && s.take_profit
                    ? (Math.abs(s.take_profit - s.entry_price) / Math.abs(s.entry_price - s.stop_loss)).toFixed(2)
                    : null;

                return `
                <div class="bg-gray-800/80 rounded-xl border border-gray-700 hover:border-purple-600/40
                            transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-purple-900/10">
                    <!-- header -->
                    <div class="flex items-center justify-between px-5 py-4 border-b border-gray-700/60">
                        <div class="flex items-center gap-2.5">
                            <span class="font-bold text-white text-lg tracking-wide">${s.symbol || '—'}</span>
                            <span class="text-xs font-semibold px-2.5 py-0.5 rounded-full ${dirCls}">
                                ${(s.direction || '—').toUpperCase()}
                            </span>
                        </div>
                        <div class="flex items-center gap-2">
                            ${s.timeframe ? `<span class="text-xs text-gray-500 bg-gray-700/60 px-2 py-0.5 rounded">${s.timeframe}</span>` : ''}
                            ${s.ai_confidence ? `<span class="text-xs text-purple-400 font-semibold">AI ${Math.round(s.ai_confidence * 100)}%</span>` : ''}
                        </div>
                    </div>
                    <!-- body -->
                    <div class="px-5 py-4 space-y-2.5">
                        <div class="flex justify-between text-sm">
                            <span class="text-gray-400">Entry</span>
                            <span class="text-white font-mono font-semibold">${s.entry_price ?? '—'}</span>
                        </div>
                        <div class="flex justify-between text-sm">
                            <span class="text-gray-400">Stop Loss</span>
                            <span class="text-red-400 font-mono">${s.stop_loss ?? '—'}</span>
                        </div>
                        <div class="flex justify-between text-sm">
                            <span class="text-gray-400">Take Profit</span>
                            <span class="text-green-400 font-mono">${s.take_profit ?? '—'}</span>
                        </div>
                        ${rr ? `
                        <div class="flex justify-between text-sm">
                            <span class="text-gray-400">R:R Ratio</span>
                            <span class="text-blue-400 font-mono font-semibold">1:${rr}</span>
                        </div>` : ''}
                        ${s.analysis ? `
                        <p class="text-xs text-gray-500 border-t border-gray-700/50 pt-2.5 mt-1 leading-relaxed line-clamp-2">
                            ${s.analysis}
                        </p>` : ''}
                    </div>
                    <!-- footer -->
                    <div class="px-5 pb-4 flex justify-between items-center text-xs text-gray-600">
                        <span>${s.created_at ? new Date(s.created_at).toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'2-digit'}) : ''}</span>
                        <span class="flex items-center gap-1.5">
                            <span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
                            Active
                        </span>
                    </div>
                </div>`;
            }).join('');

        } catch (e) {
            errBox(containerId, `Could not load signals: ${e.message}`);
        }
    }


    // ── WEBINARS ─────────────────────────────────────────────────────────────
    async function webinars(containerId = 'webinars-container', ctrl = null) {
        const c = el(containerId); if (!c) return;
        c.innerHTML = '<div style="text-align:center;padding:3rem;color:#6b7280;"><i class="fas fa-spinner fa-spin text-2xl"></i></div>';

        try {
            const data = await req('/webinars/upcoming?upcoming=true', ctrl);
            const list = Array.isArray(data) ? data : (data.webinars || []);

            // Split into upcoming and completed
            const upcoming  = list.filter(w => !w.is_completed);
            const completed = list.filter(w => w.is_completed);

            // Get user tier for gating recordings
            let userTier = 'free';
            try {
                const uRaw = localStorage.getItem('pipways_user');
                if (uRaw) userTier = (JSON.parse(uRaw).subscription_tier || 'free');
            } catch(_) {}
            const isPro = userTier === 'pro' || userTier === 'enterprise';

            if (!upcoming.length && !completed.length) {
                c.innerHTML =
                    '<div style="text-align:center;padding:3.5rem 1rem;">'
                    + '<div style="width:60px;height:60px;border-radius:50%;border:2px dashed #374151;display:flex;align-items:center;justify-content:center;margin:0 auto 1rem;background:#0d1117;">'
                    + '<i class="fas fa-video" style="color:#4b5563;font-size:1.25rem;"></i></div>'
                    + '<p style="font-size:.9rem;font-weight:600;color:#6b7280;margin-bottom:.35rem;">No webinars scheduled yet</p>'
                    + '<p style="font-size:.78rem;color:#4b5563;margin-bottom:1.25rem;">Live sessions with expert traders are coming soon.</p>'
                    + '<button onclick="PublicPages._webinarNotify(this)" '
                    + 'style="background:rgba(251,191,36,.12);color:#fbbf24;border:1px solid rgba(251,191,36,.3);padding:.5rem 1.25rem;border-radius:.5rem;font-size:.82rem;font-weight:600;cursor:pointer;">'
                    + '<i class="fas fa-bell" style="margin-right:.4rem;"></i>Notify me when one is scheduled</button>'
                    + '</div>';
                return;
            }

            // ── Countdown to next upcoming webinar ────────────────────────────
            let countdownBanner = '';
            const nextW = upcoming[0];
            if (nextW && nextW.scheduled_at) {
                const nextDate = new Date(nextW.scheduled_at);
                const diffMs   = nextDate - Date.now();
                if (diffMs > 0) {
                    const days  = Math.floor(diffMs / 86400000);
                    const hrs   = Math.floor((diffMs % 86400000) / 3600000);
                    const mins  = Math.floor((diffMs % 3600000) / 60000);
                    const secs  = Math.floor((diffMs % 60000) / 1000);
                    const parts = [];
                    if (days)  parts.push('<span id="wcd-d">' + days  + '</span><small>d</small>');
                    if (hrs)   parts.push('<span id="wcd-h">' + hrs   + '</span><small>h</small>');
                    if (mins)  parts.push('<span id="wcd-m">' + mins  + '</span><small>m</small>');
                               parts.push('<span id="wcd-s">' + secs  + '</span><small>s</small>');

                    countdownBanner =
                        '<div style="background:linear-gradient(135deg,rgba(124,58,237,.15),rgba(219,39,119,.1));'
                        + 'border:1px solid rgba(124,58,237,.3);border-radius:.85rem;padding:1rem 1.25rem;'
                        + 'display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.75rem;margin-bottom:1.5rem;">'
                        + '<div style="display:flex;align-items:center;gap:.75rem;">'
                        +   '<div style="width:36px;height:36px;border-radius:50%;background:rgba(124,58,237,.2);display:flex;align-items:center;justify-content:center;">'
                        +     '<i class="fas fa-calendar-alt" style="color:#a78bfa;font-size:.9rem;"></i></div>'
                        +   '<div>'
                        +     '<div style="font-size:.7rem;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;">Next Session</div>'
                        +     '<div style="font-weight:700;color:white;font-size:.9rem;">' + (nextW.title || '') + '</div>'
                        +   '</div>'
                        + '</div>'
                        + '<div id="pw-webinar-countdown" style="display:flex;align-items:center;gap:.4rem;font-size:1.1rem;font-weight:800;color:#a78bfa;font-variant-numeric:tabular-nums;">'
                        +   parts.join('<span style="color:#374151;margin:0 .1rem;">:</span>')
                        + '</div>'
                        + '</div>';

                    // Live tick
                    setTimeout(function tick() {
                        const cd = document.getElementById('pw-webinar-countdown');
                        if (!cd) return;
                        const diff = new Date(nextW.scheduled_at) - Date.now();
                        if (diff <= 0) { cd.innerHTML = '<span style="color:#34d399;">Live Now!</span>'; return; }
                        const d2 = Math.floor(diff/86400000);
                        const h2 = Math.floor((diff%86400000)/3600000);
                        const m2 = Math.floor((diff%3600000)/60000);
                        const s2 = Math.floor((diff%60000)/1000);
                        const p2 = [];
                        if (d2) p2.push(d2+'<small>d</small>');
                        if (h2) p2.push(h2+'<small>h</small>');
                        if (m2) p2.push(m2+'<small>m</small>');
                              p2.push(s2+'<small>s</small>');
                        cd.innerHTML = p2.join('<span style="color:#374151;margin:0 .1rem;">:</span>');
                        setTimeout(tick, 1000);
                    }, 1000);
                }
            }

            // ── Card builder ──────────────────────────────────────────────────
            function buildCard(w, isCompleted) {
                const d = w.scheduled_at ? new Date(w.scheduled_at) : null;
                const isLive = w.status === 'live';

                // Status badge
                let statusHtml;
                if (isLive) {
                    statusHtml = '<span style="font-size:.7rem;font-weight:700;padding:.2rem .65rem;border-radius:9999px;'
                        + 'background:rgba(239,68,68,.2);color:#f87171;border:1px solid rgba(239,68,68,.4);">'
                        + '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#f87171;margin-right:.4rem;animation:pulse-dot 1.5s infinite;"></span>Live Now</span>';
                } else if (isCompleted) {
                    statusHtml = '<span style="font-size:.7rem;font-weight:700;padding:.2rem .65rem;border-radius:9999px;'
                        + 'background:rgba(107,114,128,.15);color:#9ca3af;border:1px solid rgba(107,114,128,.3);">✓ Completed</span>';
                } else {
                    statusHtml = '<span style="font-size:.7rem;font-weight:700;padding:.2rem .65rem;border-radius:9999px;'
                        + 'background:rgba(16,185,129,.12);color:#34d399;border:1px solid rgba(16,185,129,.3);">Upcoming</span>';
                }

                // Thumbnail
                const thumb = w.thumbnail
                    ? '<div style="width:120px;flex-shrink:0;overflow:hidden;border-radius:.75rem 0 0 .75rem;">'
                      + '<img src="' + w.thumbnail + '" alt="" style="width:100%;height:100%;object-fit:cover;" onerror="this.parentElement.style.display=\'none\'">'
                      + '</div>'
                    : '<div style="width:6px;flex-shrink:0;background:linear-gradient(180deg,'
                      + (isCompleted ? '#374151,#1f2937' : isLive ? '#ef4444,#dc2626' : '#7c3aed,#6d28d9')
                      + ');border-radius:.75rem 0 0 .75rem;"></div>';

                // Date block
                const dateBlock = d
                    ? '<div style="min-width:72px;flex-shrink:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:1rem .6rem;background:rgba(107,114,128,.08);border-right:1px solid #1f2937;">'
                      + '<div style="font-size:1.8rem;font-weight:900;line-height:1;color:' + (isCompleted ? '#6b7280' : '#fbbf24') + ';">' + d.getDate() + '</div>'
                      + '<div style="font-size:.65rem;text-transform:uppercase;letter-spacing:.08em;color:#9ca3af;margin-top:.1rem;">' + d.toLocaleString('default',{month:'short'}) + '</div>'
                      + '<div style="font-size:.68rem;color:#6b7280;margin-top:.2rem;">' + d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}) + '</div>'
                      + '<div style="font-size:.6rem;color:#4b5563;">Lagos</div>'
                      + '</div>' : '';

                // Tags
                const tagList = (w.tags || '').split(',').map(t => t.trim()).filter(Boolean);
                const tagsHtml = tagList.length
                    ? '<div style="display:flex;flex-wrap:wrap;gap:.3rem;margin-bottom:.6rem;">'
                      + tagList.map(t =>
                          '<span style="font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;'
                          + 'background:rgba(124,58,237,.12);color:#a78bfa;border:1px solid rgba(124,58,237,.2);'
                          + 'padding:.15rem .5rem;border-radius:9999px;">' + t + '</span>'
                        ).join('')
                      + '</div>'
                    : '';

                // Speaker bio (collapsible)
                const bioId = 'bio-' + w.id;
                const speakerHtml = w.speaker_bio
                    ? '<div style="margin-top:.5rem;">'
                      + '<button onclick="(function(){var b=document.getElementById(\'bio-'+w.id+'\');b.style.display=b.style.display===\'none\'?\'block\':\'none\'})()" '
                      + 'style="font-size:.72rem;color:#a78bfa;background:none;border:none;cursor:pointer;padding:0;">'
                      + '<i class="fas fa-user-tie" style="margin-right:.35rem;"></i>About the speaker ▾</button>'
                      + '<div id="' + bioId + '" style="display:none;margin-top:.4rem;padding:.6rem .75rem;background:rgba(124,58,237,.06);'
                      + 'border-left:3px solid rgba(124,58,237,.3);border-radius:0 .4rem .4rem 0;font-size:.78rem;color:#9ca3af;line-height:1.5;">'
                      + w.speaker_bio + '</div></div>'
                    : '';

                // Meta chips
                const metaChips = [
                    w.presenter ? '<span><i class="fas fa-user" style="margin-right:.3rem;"></i>' + w.presenter + '</span>' : '',
                    w.duration_minutes ? '<span><i class="fas fa-clock" style="margin-right:.3rem;"></i>' + w.duration_minutes + ' mins</span>' : '',
                    (!isCompleted && w.max_attendees) ? '<span><i class="fas fa-users" style="margin-right:.3rem;"></i>' + w.max_attendees + ' seats</span>' : '',
                ].filter(Boolean).join('');

                // CTA buttons
                let cta = '';
                if (isCompleted) {
                    if (isPro && w.recording_url) {
                        cta = '<a href="' + w.recording_url + '" target="_blank" rel="noopener" '
                            + 'style="display:inline-flex;align-items:center;gap:.4rem;padding:.5rem 1.1rem;border-radius:.5rem;font-size:.82rem;font-weight:600;text-decoration:none;'
                            + 'background:rgba(16,185,129,.15);color:#34d399;border:1px solid rgba(16,185,129,.3);">'
                            + '<i class="fas fa-play-circle" style="font-size:.8rem;"></i> Watch Recording</a>';
                    } else if (!isPro) {
                        cta = '<button onclick="window.PaymentsPage ? PaymentsPage.showUpgradeModal(\'Webinar Recordings\') : window.location.href=\'/pricing.html\'" '
                            + 'style="display:inline-flex;align-items:center;gap:.4rem;padding:.5rem 1.1rem;border-radius:.5rem;font-size:.82rem;font-weight:600;cursor:pointer;'
                            + 'background:rgba(124,58,237,.12);color:#a78bfa;border:1px solid rgba(124,58,237,.3);">'
                            + '<i class="fas fa-lock" style="font-size:.75rem;"></i> Pro — Watch Recording</button>';
                    } else {
                        cta = '<span style="font-size:.78rem;color:#4b5563;font-style:italic;">Recording not available</span>';
                    }
                } else if (isLive) {
                    cta = '<a href="' + (w.meeting_link || '#') + '" target="_blank" rel="noopener" '
                        + 'style="display:inline-flex;align-items:center;gap:.4rem;padding:.55rem 1.25rem;border-radius:.5rem;font-size:.85rem;font-weight:700;text-decoration:none;'
                        + 'background:rgba(239,68,68,.25);color:#f87171;border:1px solid rgba(239,68,68,.4);animation:pulse-dot 2s infinite;">'
                        + '<i class="fas fa-circle" style="font-size:.6rem;"></i> Join Live Now</a>';
                } else {
                    cta = w.meeting_link
                        ? '<a href="' + w.meeting_link + '" target="_blank" rel="noopener" '
                          + 'style="display:inline-flex;align-items:center;gap:.4rem;padding:.55rem 1.25rem;border-radius:.5rem;font-size:.82rem;font-weight:600;text-decoration:none;'
                          + 'background:rgba(124,58,237,.2);color:#c4b5fd;border:1px solid rgba(124,58,237,.35);">'
                          + '<i class="fas fa-video" style="font-size:.75rem;"></i> Join Meeting →</a>'
                        : '<span style="font-size:.78rem;color:#6b7280;border:1px solid #374151;padding:.4rem .9rem;border-radius:.5rem;">'
                          + '<i class="fas fa-hourglass-half" style="margin-right:.35rem;"></i>Link coming soon</span>';
                }

                // Notify button (upcoming only, not live)
                const notifyBtn = (!isCompleted && !isLive)
                    ? ' <button onclick="PublicPages._webinarNotify(this,' + w.id + ')" '
                      + 'style="display:inline-flex;align-items:center;gap:.35rem;padding:.5rem .9rem;border-radius:.5rem;font-size:.75rem;font-weight:600;cursor:pointer;'
                      + 'background:rgba(251,191,36,.08);color:#fbbf24;border:1px solid rgba(251,191,36,.2);">'
                      + '<i class="fas fa-bell" style="font-size:.7rem;"></i>Remind me</button>'
                    : '';

                // Calendar link (upcoming only)
                let calLink = '';
                if (!isCompleted && d) {
                    const fmt = dt => dt.toISOString().replace(/[-:]/g,'').split('.')[0] + 'Z';
                    const endD = new Date(d.getTime() + (w.duration_minutes||60)*60000);
                    const params = new URLSearchParams({
                        action:'TEMPLATE', text:w.title,
                        dates:fmt(d)+'/'+fmt(endD),
                        details:(w.description||'')+(w.meeting_link?' Join: '+w.meeting_link:''),
                    });
                    calLink = ' <a href="https://calendar.google.com/calendar/render?' + params.toString()
                        + '" target="_blank" rel="noopener" '
                        + 'style="display:inline-flex;align-items:center;gap:.35rem;font-size:.75rem;color:#6b7280;border:1px solid #374151;padding:.4rem .75rem;border-radius:.5rem;text-decoration:none;">'
                        + '<i class="fas fa-calendar-plus" style="font-size:.7rem;"></i>Add to calendar</a>';
                }

                return '<div style="background:#111827;border:1px solid ' + (isCompleted ? '#1f2937' : '#1f2937') + ';border-radius:.85rem;overflow:hidden;'
                     + 'display:flex;flex-direction:row;opacity:' + (isCompleted ? '.85' : '1') + ';margin-bottom:.1rem;"'
                     + ' onmouseover="this.style.borderColor=\'#374151\';this.style.transform=\'translateY(-2px)\';this.style.boxShadow=\'0 8px 24px -6px rgba(0,0,0,.5)\'"'
                     + ' onmouseout="this.style.borderColor=\'#1f2937\';this.style.transform=\'\';this.style.boxShadow=\'\'">>>'
                     + thumb
                     + dateBlock
                     + '<div style="flex:1;padding:1.1rem 1.25rem;">'
                     +   '<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:.75rem;margin-bottom:.4rem;">'
                     +     '<h4 style="font-weight:700;color:' + (isCompleted ? '#9ca3af' : 'white') + ';font-size:.95rem;line-height:1.3;margin:0;">' + (w.title||'') + '</h4>'
                     +     statusHtml
                     +   '</div>'
                     +   tagsHtml
                     +   (w.description ? '<p style="font-size:.8rem;color:#9ca3af;margin:0 0 .6rem;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">' + w.description + '</p>' : '')
                     +   (metaChips ? '<div style="display:flex;flex-wrap:wrap;gap:.6rem;font-size:.73rem;color:#6b7280;margin-bottom:.7rem;">' + metaChips + '</div>' : '')
                     +   speakerHtml
                     +   '<div style="display:flex;align-items:center;flex-wrap:wrap;gap:.5rem;margin-top:.75rem;">'
                     +     cta + notifyBtn + calLink
                     +   '</div>'
                     + '</div>'
                     + '</div>';
            }

            // ── Build full HTML ───────────────────────────────────────────────
            let html = countdownBanner;

            // Upcoming section
            if (upcoming.length) {
                html += '<div style="margin-bottom:1.5rem;">'
                     +  '<h3 style="font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#6b7280;margin-bottom:.75rem;display:flex;align-items:center;gap:.5rem;">'
                     +    '<i class="fas fa-calendar-alt" style="color:#a78bfa;"></i> Upcoming Sessions'
                     +  '</h3>'
                     +  '<div style="display:flex;flex-direction:column;gap:.75rem;">'
                     +  upcoming.map(w => buildCard(w, false)).join('')
                     +  '</div></div>';
            }

            // Completed / Recordings section
            if (completed.length) {
                html += '<div>'
                     +  '<h3 style="font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#6b7280;margin-bottom:.75rem;display:flex;align-items:center;gap:.5rem;">'
                     +    '<i class="fas fa-play-circle" style="color:#6b7280;"></i> Past Sessions'
                     +    (isPro ? '' : ' <span style="font-size:.65rem;background:rgba(124,58,237,.15);color:#a78bfa;border:1px solid rgba(124,58,237,.25);padding:.1rem .5rem;border-radius:9999px;">Pro: recordings</span>')
                     +  '</h3>'
                     +  '<div style="display:flex;flex-direction:column;gap:.75rem;">'
                     +  completed.map(w => buildCard(w, true)).join('')
                     +  '</div></div>';
            }

            c.innerHTML = html;

        } catch (e) {
            c.innerHTML = '<div style="text-align:center;padding:3rem;color:#6b7280;"><p style="color:#f87171;font-size:.9rem;">Could not load webinars: ' + e.message + '</p></div>';
        }
    }



    // Live countdown tick — updates every minute for cards within 48 hrs
    function _startCountdownTickers(container) {
        if (!container) return;
        // Find all countdown spans and update them
        var tick = function() {
            container.querySelectorAll('[data-countdown]').forEach(function(el) {
                var target = parseInt(el.getAttribute('data-countdown'), 10);
                var diffMin = Math.floor((target - Date.now()) / 60000);
                if (diffMin <= 0) {
                    el.textContent = 'Starting now';
                } else {
                    var hrs = Math.floor(diffMin / 60);
                    var mins = diffMin % 60;
                    el.textContent = 'Starts in ' + (hrs > 0 ? hrs + 'h ' : '') + (mins > 0 ? mins + 'm' : '');
                }
            });
        };
        if (container._countdownTimer) clearInterval(container._countdownTimer);
        container._countdownTimer = setInterval(tick, 60000);
    }


    // ── BLOG ─────────────────────────────────────────────────────────────────
    async function blog(containerId, ctrl) {
        if (containerId === undefined) containerId = 'blog-container';
        spinner(containerId);
        try {
            const data = await req('/blog/posts', ctrl);
            const list = Array.isArray(data) ? data : (data.posts || []);
            const c = el(containerId); if (!c) return;

            if (!list.length) {
                empty(containerId, 'fa-newspaper', 'No articles published yet');
                return;
            }

            // Compute reading time if not provided by API (200 wpm average)
            list.forEach(function(p) {
                if (!p.read_time && p.content) {
                    var wc = (p.content.replace(/<[^>]+>/g, ' ')).trim().split(/\s+/).filter(Boolean).length;
                    p.read_time = Math.max(1, Math.ceil(wc / 200)) + ' min read';
                } else if (!p.read_time && p.excerpt) {
                    p.read_time = '1 min read';
                }
            });

            // Collect unique categories for filter bar
            var cats = ['All'];
            list.forEach(function(p) { if (p.category && cats.indexOf(p.category) < 0) cats.push(p.category); });
            var activeCat = 'All';

            var catColors = {
                'Strategy':         '#a78bfa',
                'Analysis':         '#60a5fa',
                'Education':        '#34d399',
                'Market Analysis':  '#60a5fa',
                'Psychology':       '#f472b6',
                'Risk Management':  '#fb923c',
                'SMC':              '#c084fc',
                'Forex':            '#38bdf8',
                'Crypto':           '#fbbf24',
                'Indices':          '#4ade80',
                'General':          '#9ca3af',
            };

            function renderGrid(filterCat) {
                var filtered = filterCat === 'All' ? list : list.filter(function(p){ return p.category === filterCat; });
                if (!filtered.length) {
                    return '<div style="text-align:center;padding:2.5rem 1rem;color:#4b5563;grid-column:1/-1;">'
                         + '<p style="font-size:.85rem;">No articles in this category yet.</p></div>';
                }
                return filtered.map(function(p, i) {
                    var big = (i === 0 && filterCat === 'All');
                    var cat = p.category || 'General';
                    var col = catColors[cat] || '#9ca3af';
                    var date = p.created_at
                        ? new Date(p.created_at).toLocaleDateString('en-GB', {day:'numeric', month:'short', year:'numeric'})
                        : '';
                    var slug = (p.slug || '').replace(/"/g, '');

                    var imgHero = p.featured_image
                        ? '<img src="' + p.featured_image + '" class="w-full h-56 lg:h-full object-cover group-hover:scale-105 transition-transform duration-500"'
                          + ' onerror="this.style.display=\'none\'"height:100%;min-height:14rem;background:linear-gradient(135deg,#1e1b4b,#1a1040,#0f172a);display:flex;align-items:center;justify-content:center;\"><i class=\"fas fa-newspaper\" style=\"font-size:3rem;color:rgba(255,255,255,.07)\"></i></div>\'">'
                        : '<div class="h-56 lg:h-full bg-gradient-to-br from-blue-900 via-indigo-900 to-purple-900 flex items-center justify-center"><i class="fas fa-newspaper text-6xl text-white/10"></i></div>';

                    var imgSmall = p.featured_image
                        ? '<div class="overflow-hidden h-44" style="background:linear-gradient(135deg,#1e1b4b,#0f172a);">'
                          + '<img src="' + p.featured_image + '" class="w-full h-44 object-cover group-hover:scale-105 transition-transform duration-500"'
                          + ' onerror="this.style.display=\'none\'">'
                          + '</div>'
                        : '<div class="h-44 bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center"><i class="fas fa-newspaper text-4xl text-gray-600"></i></div>';

                    var featBadge = p.featured ? '<span class="text-xs text-yellow-400">&#11088; Featured</span>' : '';

                    var dateParts = '';
                    if (date) dateParts += '<span><i class="fas fa-calendar mr-1"></i>' + date + '</span>';
                    if (p.read_time) dateParts += '<span><i class="fas fa-clock mr-1"></i>' + p.read_time + '</span>';
                    if (p.views) dateParts += '<span><i class="fas fa-eye mr-1"></i>' + (p.views >= 1000 ? (p.views/1000).toFixed(1)+'k' : p.views) + '</span>';

                    if (big) {
                        return '<article class="col-span-full bg-gray-800/80 rounded-xl border border-gray-700 hover:border-blue-600/40 transition-all cursor-pointer group overflow-hidden grid grid-cols-1 lg:grid-cols-2 blog-card" data-slug="' + slug + '">'
                            + '<div class="relative overflow-hidden">' + imgHero + '</div>'
                            + '<div class="p-6 lg:p-8 flex flex-col justify-center">'
                            +   '<div class="flex items-center gap-2 mb-3">'
                            +     '<span style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;background:rgba(96,165,250,.12);color:' + col + ';border:1px solid ' + col + '33;padding:.2rem .7rem;border-radius:9999px;">' + cat + '</span>'
                            +     featBadge
                            +   '</div>'
                            +   '<h3 class="text-xl lg:text-2xl font-bold text-white leading-snug mb-3 group-hover:text-blue-300 transition-colors">' + (p.title || '') + '</h3>'
                            +   '<p class="text-gray-400 text-sm leading-relaxed mb-5 line-clamp-3">' + (p.excerpt || '') + '</p>'
                            +   '<div class="flex items-center justify-between text-xs text-gray-500">'
                            +     '<div class="flex items-center gap-3">' + dateParts + '</div>'
                            +     '<span class="text-blue-400 font-semibold group-hover:text-blue-300">Read &#8594;</span>'
                            +   '</div>'
                            + '</div>'
                            + '</article>';
                    }

                    return '<article class="bg-gray-800/80 rounded-xl border border-gray-700 hover:border-blue-600/40 transition-all cursor-pointer group overflow-hidden hover:-translate-y-0.5 hover:shadow-md hover:shadow-blue-900/10 blog-card" data-slug="' + slug + '">'
                        + imgSmall
                        + '<div class="p-5">'
                        +   '<div class="flex items-center gap-1.5 mb-2"><span style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:' + col + ';">' + cat + '</span></div>'
                        +   '<h4 class="font-bold text-white mb-2 leading-snug group-hover:text-blue-300 transition-colors line-clamp-2">' + (p.title || '') + '</h4>'
                        +   '<p class="text-sm text-gray-400 line-clamp-2 mb-4">' + (p.excerpt || '') + '</p>'
                        +   '<div class="flex justify-between items-center text-xs text-gray-600">'
                        +     '<div class="flex items-center gap-2">'
                        +       (date ? '<span>' + date + '</span>' : '')
                        +       (p.read_time ? '<span style="color:#6b7280;">&#183; ' + p.read_time + '</span>' : '')
                        +     '</div>'
                        +     '<span class="text-purple-400 group-hover:text-purple-300 font-medium">Read &#8594;</span>'
                        +   '</div>'
                        + '</div>'
                        + '</article>';
                }).join('');
            }

            // ── blog-container IS already the grid (grid-cols-3 in dashboard.html)
            // The category bar must be a SIBLING before it, not a child inside it.
            // Articles are written directly into blog-container via innerHTML.

            // Remove any existing filter bar (re-render safe)
            var oldBar = document.getElementById('blog-cat-bar');
            if (oldBar) oldBar.parentNode.removeChild(oldBar);

            // Build and insert category filter bar BEFORE the container
            if (cats.length > 2) {
                var bar = document.createElement('div');
                bar.id = 'blog-cat-bar';
                bar.style.cssText = 'display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:1.25rem;';
                cats.forEach(function(cat) {
                    var btn = document.createElement('button');
                    var isActive = cat === 'All';
                    btn.textContent = cat;
                    btn.style.cssText = 'padding:.3rem .85rem;border-radius:9999px;font-size:.75rem;font-weight:600;cursor:pointer;transition:all .15s;border:1px solid '
                        + (isActive ? '#7c3aed;background:rgba(124,58,237,.25);color:#c4b5fd;'
                                    : '#374151;background:transparent;color:#6b7280;');
                    btn.setAttribute('data-cat', cat);
                    btn.onclick = function() {
                        // Update pill styles
                        bar.querySelectorAll('button').forEach(function(b) {
                            var active = b.getAttribute('data-cat') === cat;
                            b.style.border     = '1px solid ' + (active ? '#7c3aed' : '#374151');
                            b.style.background = active ? 'rgba(124,58,237,.25)' : 'transparent';
                            b.style.color      = active ? '#c4b5fd' : '#6b7280';
                        });
                        // Write filtered articles directly into the grid container
                        c.innerHTML = renderGrid(cat);
                        attachClicks();
                    };
                    bar.appendChild(btn);
                });
                // Insert bar as sibling BEFORE the grid container — not inside it
                c.parentNode.insertBefore(bar, c);
            }

            // Write articles directly into blog-container (which is the grid)
            c.innerHTML = renderGrid('All');

            function attachClicks() {
                c.querySelectorAll('.blog-card').forEach(function(card) {
                    card.addEventListener('click', function() {
                        var slug = card.getAttribute('data-slug');
                        if (slug) openPost(slug);
                    });
                });
            }
            attachClicks();

        } catch (e) {
            errBox(containerId, 'Could not load articles: ' + e.message);
        }
    }


    // ── COURSES ───────────────────────────────────────────────────────────────
    async function courses(containerId = 'courses-container', ctrl = null) {
        // Prefer the full CoursesPage LMS module if loaded
        if (typeof window.CoursesPage !== 'undefined') {
            await window.CoursesPage.render(containerId);
            return;
        }

        // Fallback: simple grid
        spinner(containerId);
        try {
            const data = await req('/courses/list', ctrl);
            const list = Array.isArray(data) ? data : (data.courses || []);
            const c = el(containerId); if (!c) return;

            if (!list.length) {
                empty(containerId, 'fa-graduation-cap', 'No courses available yet');
                return;
            }

            c.innerHTML = list.map(course => {
                const pct = course.progress || 0;
                return `
                <div class="bg-gray-800/80 rounded-xl border border-gray-700 overflow-hidden
                            hover:border-purple-600/40 transition-all cursor-pointer group hover:-translate-y-0.5"
                     onclick="window.CoursesPage ? window.CoursesPage.openCourse(${course.id}) : null">
                    ${course.thumbnail_url
                        ? `<div class="overflow-hidden h-44">
                               <img src="${course.thumbnail_url}" class="w-full h-44 object-cover group-hover:scale-105 transition-transform duration-500"
                                    onerror="this.parentElement.innerHTML='<div class=\\'h-44 bg-gradient-to-br from-purple-900 to-blue-900 flex items-center justify-center\\'><i class=\\'fas fa-graduation-cap text-5xl text-white/10\\'></i></div>'">`
                           + `</div>`
                        : `<div class="h-44 bg-gradient-to-br from-purple-900 to-blue-900 flex items-center justify-center">
                               <i class="fas fa-graduation-cap text-5xl text-white/10 group-hover:text-white/20 transition-colors"></i>
                           </div>`}
                    <div class="p-5">
                        <div class="flex justify-between items-center mb-2">
                            <span class="text-xs font-semibold text-purple-400 uppercase tracking-wide">${course.level || 'Beginner'}</span>
                            ${course.instructor ? `<span class="text-xs text-gray-500">${course.instructor}</span>` : ''}
                        </div>
                        <h4 class="font-bold text-white mb-2 group-hover:text-purple-300 transition-colors line-clamp-2">${course.title}</h4>
                        <p class="text-sm text-gray-400 line-clamp-2 mb-4">${course.description || ''}</p>
                        <div class="flex justify-between items-center text-xs text-gray-500 mb-3">
                            <span><i class="fas fa-book-open mr-1.5"></i>${course.lesson_count || 0} lessons</span>
                            ${pct > 0 ? `<span class="text-green-400 font-semibold">${pct}% done</span>` : ''}
                        </div>
                        ${pct > 0 ? `
                        <div class="h-1.5 bg-gray-700 rounded-full overflow-hidden mb-3">
                            <div class="h-full bg-gradient-to-r from-purple-600 to-blue-500 rounded-full transition-all"
                                 style="width:${pct}%"></div>
                        </div>` : ''}
                        <button class="w-full py-2 rounded-lg text-sm font-semibold text-white transition-all
                                       hover:brightness-110 active:scale-95"
                                style="background:rgba(124,58,237,.3);border:1px solid rgba(124,58,237,.4);">
                            ${pct > 0 ? `Continue (${pct}%) →` : 'Start Learning →'}
                        </button>
                    </div>
                </div>`;
            }).join('');

        } catch (e) {
            errBox(containerId, `Could not load courses: ${e.message}`);
        }
    }


    // ── Blog post viewer ─────────────────────────────────────────────────────
    async function openPost(slug) {
        const MODAL_ID = 'blog-post-modal';

        // Fetch the post
        let post;
        try {
            const token = localStorage.getItem('pipways_token');
            const res = await fetch(
                window.location.origin + '/blog/posts/' + encodeURIComponent(slug),
                { headers: { Authorization: 'Bearer ' + token, Accept: 'application/json' } }
            );
            if (!res.ok) throw new Error('HTTP ' + res.status);
            post = await res.json();
        } catch (err) {
            alert('Could not load post: ' + err.message);
            return;
        }

        // Remove existing modal
        var existing = document.getElementById(MODAL_ID);
        if (existing) existing.parentNode.removeChild(existing);

        // Build modal using DOM API — no string quotes to nest
        var overlay = document.createElement('div');
        overlay.id = MODAL_ID;
        overlay.style.cssText = [
            'position:fixed', 'inset:0', 'background:rgba(0,0,0,.88)',
            'z-index:9999', 'display:flex', 'align-items:flex-start',
            'justify-content:center', 'padding:2rem 1rem', 'overflow-y:auto'
        ].join(';');
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) overlay.parentNode.removeChild(overlay);
        });

        // Inner card
        var card = document.createElement('div');
        card.style.cssText = [
            'background:#111827', 'border-radius:1rem', 'width:100%',
            'max-width:760px', 'border:1px solid #374151', 'overflow:hidden',
            'margin-top:1rem'
        ].join(';');

        // ── header ──
        var header = document.createElement('div');
        header.style.cssText = [
            'display:flex', 'justify-content:space-between', 'align-items:center',
            'padding:1rem 1.5rem', 'border-bottom:1px solid #1f2937',
            'position:sticky', 'top:0', 'background:#111827', 'z-index:1'
        ].join(';');

        var catSpan = document.createElement('span');
        catSpan.style.cssText = 'color:#a78bfa;font-size:.8rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;';
        catSpan.textContent = (post.category || 'General');

        var closeBtn = document.createElement('button');
        closeBtn.innerHTML = '&times;';
        closeBtn.style.cssText = 'background:none;border:none;color:#9ca3af;font-size:1.75rem;cursor:pointer;line-height:1;padding:0;';
        closeBtn.onclick = function() { overlay.parentNode.removeChild(overlay); };

        header.appendChild(catSpan);
        header.appendChild(closeBtn);
        card.appendChild(header);

        // ── featured image ──
        if (post.featured_image) {
            var img = document.createElement('img');
            img.src = post.featured_image;
            img.style.cssText = 'width:100%;height:300px;object-fit:cover;display:block;';
            img.onerror = function() {
                this.style.display = 'none';
                var ph = document.createElement('div');
                ph.style.cssText = 'height:280px;background:linear-gradient(135deg,#1e1b4b,#1a1040,#0f172a);border-radius:.75rem;display:flex;align-items:center;justify-content:center;margin-bottom:1.5rem;';
                ph.innerHTML = '<i class="fas fa-newspaper" style="font-size:3rem;color:rgba(255,255,255,.07)"></i>';
                this.parentNode.insertBefore(ph, this.nextSibling);
            };
            card.appendChild(img);
        }

        // ── body ──
        var body = document.createElement('div');
        body.style.cssText = 'padding:2rem;';

        var h1 = document.createElement('h1');
        h1.style.cssText = 'font-size:1.6rem;font-weight:800;color:white;line-height:1.3;margin:0 0 1rem;';
        h1.textContent = post.title || '';
        body.appendChild(h1);

        // meta row
        var meta = document.createElement('div');
        meta.style.cssText = 'display:flex;flex-wrap:wrap;gap:1rem;margin-bottom:1.5rem;color:#6b7280;font-size:.8rem;';
        if (post.created_at) {
            var dateEl = document.createElement('span');
            dateEl.textContent = new Date(post.created_at).toLocaleDateString('en-GB',{day:'numeric',month:'long',year:'numeric'});
            meta.appendChild(dateEl);
        }
        if (post.read_time) {
            var rtEl = document.createElement('span');
            rtEl.textContent = post.read_time;
            meta.appendChild(rtEl);
        }
        if (post.views != null) {
            var vEl = document.createElement('span');
            vEl.textContent = post.views + ' views';
            meta.appendChild(vEl);
        }
        body.appendChild(meta);

        // content — render HTML from Quill (prose typography for dark theme)
        var contentEl = document.createElement('div');
        contentEl.className = 'pw-prose';
        contentEl.style.cssText = [
            'color:#d1d5db',
            'line-height:1.85',
            'font-size:.95rem',
        ].join(';');
        // Inject prose CSS once
        if (!document.getElementById('pw-prose-style')) {
            var ps = document.createElement('style');
            ps.id = 'pw-prose-style';
            ps.textContent = [
                '.pw-prose h1,.pw-prose h2,.pw-prose h3{color:#f3f4f6;font-weight:700;margin:1.4rem 0 .5rem;line-height:1.3;}',
                '.pw-prose h1{font-size:1.5rem;}',
                '.pw-prose h2{font-size:1.2rem;}',
                '.pw-prose h3{font-size:1.05rem;}',
                '.pw-prose p{margin:0 0 .9rem;}',
                '.pw-prose a{color:#a78bfa;text-underline-offset:2px;}',
                '.pw-prose a:hover{color:#c4b5fd;}',
                '.pw-prose strong{color:#f9fafb;font-weight:600;}',
                '.pw-prose em{color:#e5e7eb;}',
                '.pw-prose blockquote{border-left:3px solid #7c3aed;margin:1rem 0;padding:.6rem 1rem;color:#9ca3af;background:rgba(124,58,237,.06);border-radius:0 .4rem .4rem 0;}',
                '.pw-prose pre{background:#0d1117;border:1px solid #374151;border-radius:.5rem;padding:1rem 1.25rem;color:#34d399;font-size:.85rem;overflow-x:auto;margin:1rem 0;}',
                '.pw-prose code{background:#1f2937;color:#a78bfa;padding:.1rem .35rem;border-radius:.25rem;font-size:.85em;}',
                '.pw-prose pre code{background:none;color:inherit;padding:0;}',
                '.pw-prose ul,.pw-prose ol{padding-left:1.5rem;margin:0 0 .9rem;}',
                '.pw-prose li{margin-bottom:.3rem;}',
                '.pw-prose img{max-width:100%;border-radius:.5rem;margin:1rem 0;}',
                '.pw-prose hr{border:none;border-top:1px solid #1f2937;margin:1.5rem 0;}',
            ].join('');
            document.head.appendChild(ps);
        }
        // Use innerHTML for Quill-generated HTML; fall back to pre-wrap for plain text
        var rawContent = post.content || '';
        var isHTML = /<[a-z][\s\S]*>/i.test(rawContent);
        if (isHTML) {
            contentEl.innerHTML = rawContent;
        } else {
            contentEl.style.whiteSpace = 'pre-wrap';
            contentEl.textContent = rawContent;
        }
        body.appendChild(contentEl);

        // tags
        var tags = post.tags || [];
        if (tags.length) {
            var tagRow = document.createElement('div');
            tagRow.style.cssText = 'display:flex;flex-wrap:wrap;gap:.5rem;margin-top:2rem;padding-top:1.5rem;border-top:1px solid #1f2937;';
            tags.forEach(function(t) {
                var tag = document.createElement('span');
                tag.style.cssText = 'background:rgba(124,58,237,.2);color:#a78bfa;border:1px solid rgba(124,58,237,.3);padding:.2rem .7rem;border-radius:9999px;font-size:.75rem;';
                tag.textContent = t;
                tagRow.appendChild(tag);
            });
            body.appendChild(tagRow);
        }

        // Share buttons (copy-link + Twitter + LinkedIn)
        var shareRow = document.createElement('div');
        shareRow.style.cssText = 'display:flex;align-items:center;gap:.6rem;margin-top:1.5rem;padding-top:1.25rem;border-top:1px solid #1f2937;flex-wrap:wrap;';
        var shareLabel = document.createElement('span');
        shareLabel.style.cssText = 'font-size:.75rem;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-right:.25rem;';
        shareLabel.textContent = 'Share';
        shareRow.appendChild(shareLabel);

        var postUrl = window.location.origin + '/blog/' + encodeURIComponent(post.slug || '');
        var postTitle = encodeURIComponent(post.title || '');

        var copyBtn = document.createElement('button');
        copyBtn.innerHTML = '<i class="fas fa-link" style="margin-right:.35rem;font-size:.75rem;"></i>Copy link';
        copyBtn.style.cssText = 'background:rgba(107,114,128,.12);color:#9ca3af;border:1px solid #374151;padding:.3rem .85rem;border-radius:.4rem;font-size:.75rem;cursor:pointer;transition:all .15s;';
        copyBtn.onclick = function() {
            navigator.clipboard.writeText(postUrl).then(function() {
                copyBtn.innerHTML = '<i class="fas fa-check" style="margin-right:.35rem;color:#34d399;"></i>Copied!';
                copyBtn.style.borderColor = 'rgba(16,185,129,.4)';
                setTimeout(function() {
                    copyBtn.innerHTML = '<i class="fas fa-link" style="margin-right:.35rem;font-size:.75rem;"></i>Copy link';
                    copyBtn.style.borderColor = '#374151';
                }, 2200);
            }).catch(function() {
                prompt('Copy this link:', postUrl);
            });
        };
        shareRow.appendChild(copyBtn);

        var twitterBtn = document.createElement('a');
        twitterBtn.href = 'https://twitter.com/intent/tweet?text=' + postTitle + '&url=' + encodeURIComponent(postUrl);
        twitterBtn.target = '_blank';
        twitterBtn.rel = 'noopener';
        twitterBtn.innerHTML = '<i class="fab fa-twitter" style="margin-right:.35rem;"></i>Share';
        twitterBtn.style.cssText = 'display:inline-flex;align-items:center;background:rgba(29,161,242,.1);color:#1da1f2;border:1px solid rgba(29,161,242,.3);padding:.3rem .85rem;border-radius:.4rem;font-size:.75rem;text-decoration:none;transition:all .15s;';
        shareRow.appendChild(twitterBtn);

        var liBtn = document.createElement('a');
        liBtn.href = 'https://www.linkedin.com/sharing/share-offsite/?url=' + encodeURIComponent(postUrl);
        liBtn.target = '_blank';
        liBtn.rel = 'noopener';
        liBtn.innerHTML = '<i class="fab fa-linkedin-in" style="margin-right:.35rem;"></i>Share';
        liBtn.style.cssText = 'display:inline-flex;align-items:center;background:rgba(0,119,181,.1);color:#0a66c2;border:1px solid rgba(0,119,181,.3);padding:.3rem .85rem;border-radius:.4rem;font-size:.75rem;text-decoration:none;transition:all .15s;';
        shareRow.appendChild(liBtn);

        body.appendChild(shareRow);

        card.appendChild(body);
        overlay.appendChild(card);
        document.body.appendChild(overlay);
    }

    // ── public API ────────────────────────────────────────────────────────────
    return { signals, webinars, blog, courses, openPost };

})();

window.PublicPages = PublicPages;

// Notify-me handler — attached after export so it can reference window.PublicPages
window.PublicPages._webinarNotify = function(btn, webinarId) {
    try {
        const stored = JSON.parse(localStorage.getItem('pw_webinar_reminders') || '[]');
        if (webinarId && !stored.includes(webinarId)) stored.push(webinarId);
        localStorage.setItem('pw_webinar_reminders', JSON.stringify(stored));
        localStorage.setItem('pw_webinar_notify', '1');
    } catch(_) {}
    btn.textContent = "\u2713 You'll be notified";
    btn.style.background = 'rgba(16,185,129,.15)';
    btn.style.color = '#34d399';
    btn.style.borderColor = 'rgba(16,185,129,.3)';
    btn.disabled = true;
};
