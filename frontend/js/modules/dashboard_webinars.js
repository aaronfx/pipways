// Dashboard Module: Webinars
// Extracted from dashboard.js for maintainability

DashboardController.prototype.loadWebinars = async function() {
    const container = document.getElementById('webinars-container');
    if (!container) return;

    container.innerHTML = `
        <div class="space-y-4">
            ${[1,2,3].map(() => `
            <div class="bg-gray-800 rounded-xl p-5 border border-gray-700 flex gap-4 items-start">
                <div class="shimmer-line" style="width:56px;height:72px;border-radius:.5rem;flex-shrink:0;"></div>
                <div class="flex-1 space-y-2 pt-1">
                    <div class="shimmer-line" style="width:60%;height:14px;"></div>
                    <div class="shimmer-line-sm" style="width:80%;"></div>
                    <div class="shimmer-line-sm" style="width:40%;"></div>
                </div>
            </div>`).join('')}
        </div>`;

    try {
        const data = await this.apiRequest('/webinars/upcoming?upcoming=true');
        const webinars = Array.isArray(data) ? data : (data.webinars || []);

        if (!webinars.length) {
            container.innerHTML = `
                <div class="text-center py-16">
                    <div class="w-16 h-16 rounded-full bg-purple-900/30 flex items-center justify-center mx-auto mb-4">
                        <i class="fas fa-video text-2xl text-purple-400"></i>
                    </div>
                    <p class="text-white font-semibold text-lg">No sessions scheduled yet</p>
                    <p class="text-gray-500 text-sm mt-1">Live mentorship sessions are coming soon. Check back shortly.</p>
                </div>`;
            return;
        }

        const live     = webinars.filter(w => w.status === 'live');
        const upcoming = webinars.filter(w => !w.is_completed && w.status !== 'live');
        const past     = webinars.filter(w => w.is_completed && w.recording_url);

        let html = '';

        if (live.length) {
            const w = live[0];
            const wJson = JSON.stringify(w).replace(/"/g, '&quot;');
            html += `
            <div class="rounded-xl p-5 mb-6 border animate-fade-in"
                 style="background:linear-gradient(135deg,rgba(239,68,68,.12),rgba(124,58,237,.10));border-color:rgba(239,68,68,.35);">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div class="flex items-center gap-3">
                        <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold"
                             style="background:rgba(239,68,68,.2);color:#f87171;">
                            <span class="w-1.5 h-1.5 rounded-full bg-red-400" style="animation:pulse-dot 1s infinite;"></span>
                            LIVE NOW
                        </div>
                        <div>
                            <p class="text-white font-bold">${w.title}</p>
                            <p class="text-sm text-gray-400">
                                ${w.presenter ? `<i class="fas fa-user mr-1"></i>${w.presenter}` : ''}
                                ${w.duration_minutes ? `<span class="ml-3"><i class="fas fa-clock mr-1"></i>${w.duration_minutes} mins</span>` : ''}
                            </p>
                        </div>
                    </div>
                    <button onclick="dashboard.openSessionRoom(JSON.parse(this.dataset.w))"
                            data-w="${wJson}"
                            class="flex-shrink-0 flex items-center gap-2 px-5 py-2.5 rounded-lg font-semibold text-sm transition-all"
                            style="background:#ef4444;color:white;">
                        <i class="fas fa-play-circle"></i> Join Session
                    </button>
                </div>
            </div>`;
        }

        if (upcoming.length) {
            html += `<h3 class="text-white font-bold text-base mb-3 flex items-center gap-2">
                <i class="fas fa-calendar-alt text-purple-400 text-sm"></i> Upcoming Sessions
            </h3>`;
            upcoming.forEach(w => {
                const date    = w.scheduled_at ? new Date(w.scheduled_at) : null;
                const wJson   = JSON.stringify(w).replace(/"/g, '&quot;');
                const hasStream = !!(w.youtube_url || w.embed_url);
                html += `
                <div class="bg-gray-800 rounded-xl p-5 border border-gray-700 flex flex-col sm:flex-row
                            justify-between items-start sm:items-center gap-4 mb-3
                            hover:border-purple-600/40 transition-colors animate-fade-in">
                    <div class="flex gap-4 items-start">
                        ${date ? `
                        <div class="text-center min-w-[56px] rounded-lg p-2 flex-shrink-0"
                             style="background:rgba(124,58,237,.15);border:1px solid rgba(124,58,237,.25);">
                            <div class="text-2xl font-bold" style="color:#a78bfa;">${date.getDate()}</div>
                            <div class="text-xs text-gray-400 uppercase">${date.toLocaleString('default',{month:'short'})}</div>
                            <div class="text-xs text-gray-500">${date.toLocaleString('default',{weekday:'short'})}</div>
                        </div>` : ''}
                        <div>
                            <h4 class="font-bold text-white">${w.title}</h4>
                            <p class="text-sm text-gray-400 mt-0.5 line-clamp-2">${w.description || ''}</p>
                            <div class="text-xs text-gray-500 mt-1.5 flex gap-3 flex-wrap items-center">
                                ${w.presenter ? `<span><i class="fas fa-user mr-1"></i>${w.presenter}</span>` : ''}
                                ${w.duration_minutes ? `<span><i class="fas fa-clock mr-1"></i>${w.duration_minutes} mins</span>` : ''}
                                ${date ? `<span><i class="fas fa-clock mr-1"></i>${date.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})} WAT</span>` : ''}
                                ${hasStream ? `<span class="px-1.5 py-0.5 rounded text-xs font-semibold"
                                    style="background:rgba(34,197,94,.15);color:#4ade80;">
                                    <i class="fas fa-broadcast-tower mr-1"></i>Live stream
                                </span>` : ''}
                            </div>
                        </div>
                    </div>
                    <div class="flex gap-2 flex-shrink-0">
                        ${hasStream ? `
                        <button onclick="dashboard.openSessionRoom(JSON.parse(this.dataset.w))"
                                data-w="${wJson}"
                                class="px-3 py-2 rounded-lg text-sm font-semibold transition-colors"
                                style="background:rgba(124,58,237,.15);color:#a78bfa;border:1px solid rgba(124,58,237,.3);">
                            <i class="fas fa-eye mr-1"></i> Preview
                        </button>` : ''}
                        <button id="reg-btn-${w.id}"
                                onclick="dashboard.registerForWebinar(${w.id}, this)"
                                class="px-4 py-2 rounded-lg text-sm font-semibold transition-all"
                                style="background:rgba(124,58,237,.2);color:#a78bfa;border:1px solid rgba(124,58,237,.3);">
                            <i class="fas fa-calendar-check mr-1"></i> Register Free
                        </button>
                    </div>
                </div>`;
            });
        }

        if (past.length) {
            html += `
            <div class="mt-6">
                <h3 class="text-white font-bold text-base mb-3 flex items-center gap-2">
                    <i class="fas fa-play-circle text-blue-400 text-sm"></i> Past Recordings
                </h3>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                ${past.map(w => {
                    const date = w.scheduled_at ? new Date(w.scheduled_at) : null;
                    const wJson = JSON.stringify(w).replace(/"/g, '&quot;');
                    return `
                    <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden
                                hover:border-blue-600/40 transition-colors cursor-pointer group"
                         onclick="dashboard.openSessionRoom(JSON.parse(this.dataset.w))"
                         data-w="${wJson}">
                        <div class="relative h-28 flex items-center justify-center"
                             style="background:linear-gradient(135deg,#1e1b4b,#0f172a);">
                            <i class="fas fa-play-circle text-4xl text-white/20 group-hover:text-white/40 transition-colors"></i>
                            <div class="absolute top-2 left-2 px-2 py-0.5 rounded text-xs font-bold"
                                 style="background:rgba(59,130,246,.25);color:#93c5fd;">Recorded</div>
                        </div>
                        <div class="p-3">
                            <p class="text-white text-sm font-semibold line-clamp-1">${w.title}</p>
                            <p class="text-xs text-gray-500 mt-0.5">
                                ${w.presenter ? w.presenter + ' · ' : ''}
                                ${date ? date.toLocaleDateString() : ''}
                            </p>
                        </div>
                    </div>`;
                }).join('')}
                </div>
            </div>`;
        }

        container.innerHTML = html;

        upcoming.forEach(async w => {
            try {
                const r = await this.apiRequest(`/webinars/${w.id}/my-registration`);
                if (r.registered) {
                    const btn = document.getElementById(`reg-btn-${w.id}`);
                    if (btn) {
                        btn.innerHTML = '<i class="fas fa-check mr-1"></i> Registered';
                        btn.disabled = true;
                        btn.style.cssText += ';background:rgba(16,185,129,.15);color:#34d399;border-color:rgba(16,185,129,.3);cursor:default;';
                    }
                }
            } catch (_) { /* non-fatal */ }
        });

    } catch (error) {
        console.error('[Dashboard] loadWebinars error:', error);
        container.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-exclamation-circle text-red-400 text-xl mb-2 block"></i>
                Failed to load sessions. Please refresh and try again.
            </div>`;
    }
};

DashboardController.prototype.openSessionRoom = function(w) {
    const container = document.getElementById('webinars-container');
    if (!container) return;

    let embedUrl = '';
    if (w.youtube_url) {
        const m = w.youtube_url.match(/(?:v=|youtu\.be\/)([A-Za-z0-9_-]{11})/);
        if (m) embedUrl = `https://www.youtube.com/embed/${m[1]}?autoplay=1&rel=0&modestbranding=1`;
    }
    if (!embedUrl && w.embed_url) embedUrl = w.embed_url;
    if (!embedUrl && w.recording_url) {
        const m = w.recording_url.match(/(?:v=|youtu\.be\/)([A-Za-z0-9_-]{11})/);
        if (m) embedUrl = `https://www.youtube.com/embed/${m[1]}?rel=0&modestbranding=1`;
    }

    const date = w.scheduled_at ? new Date(w.scheduled_at) : null;

    const videoBlock = embedUrl ? `
        <div style="position:relative;width:100%;border-radius:.75rem;overflow:hidden;background:#000;aspect-ratio:16/9;">
            <iframe src="${embedUrl}"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"
                allowfullscreen
                style="position:absolute;inset:0;width:100%;height:100%;border:none;">
            </iframe>
        </div>` : `
        <div class="flex flex-col items-center justify-center rounded-xl gap-4 py-12"
             style="background:#111827;border:2px dashed #374151;aspect-ratio:16/9;">
            <i class="fas fa-broadcast-tower text-4xl text-gray-600"></i>
            <div class="text-center">
                <p class="text-white font-semibold">Stream starts when the session goes live</p>
                <p class="text-gray-500 text-sm mt-1">
                    ${date ? 'Scheduled: ' + date.toLocaleString([], {dateStyle:'medium',timeStyle:'short'}) : ''}
                </p>
            </div>
            ${w.meeting_link ? `
            <a href="${w.meeting_link}" target="_blank" rel="noopener"
               class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold"
               style="background:rgba(59,130,246,.2);color:#93c5fd;border:1px solid rgba(59,130,246,.3);">
                <i class="fas fa-external-link-alt"></i> Open Zoom as backup
            </a>` : ''}
        </div>`;

    container.innerHTML = `
    <div class="animate-fade-in">
        <button onclick="dashboard.loadWebinars()"
                class="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors mb-5">
            <i class="fas fa-arrow-left"></i> Back to Sessions
        </button>
        <div class="flex flex-col lg:flex-row gap-5">
            <div class="flex-1 min-w-0">
                ${videoBlock}
                <div class="mt-4 bg-gray-800 rounded-xl p-4 border border-gray-700">
                    <div class="flex items-start justify-between gap-3 flex-wrap">
                        <div>
                            <h2 class="text-white font-bold text-lg">${w.title}</h2>
                            ${date ? `<p class="text-sm text-gray-400 mt-0.5">
                                <i class="fas fa-calendar mr-1"></i>
                                ${date.toLocaleString([],{dateStyle:'full',timeStyle:'short'})} WAT
                            </p>` : ''}
                        </div>
                        ${w.status === 'live' ? `
                        <div class="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold flex-shrink-0"
                             style="background:rgba(239,68,68,.2);color:#f87171;">
                            <span class="w-1.5 h-1.5 rounded-full bg-red-400" style="animation:pulse-dot 1s infinite;"></span>
                            LIVE
                        </div>` : ''}
                    </div>
                    ${w.description ? `<p class="text-gray-400 text-sm mt-3 leading-relaxed">${w.description}</p>` : ''}
                    <div class="flex gap-4 mt-3 text-xs text-gray-500 flex-wrap">
                        ${w.presenter ? `<span><i class="fas fa-user mr-1 text-purple-400"></i>${w.presenter}</span>` : ''}
                        ${w.duration_minutes ? `<span><i class="fas fa-clock mr-1 text-blue-400"></i>${w.duration_minutes} mins</span>` : ''}
                    </div>
                </div>
            </div>
            <div class="w-full lg:w-72 xl:w-80 flex-shrink-0 space-y-4">
                ${w.presenter ? `
                <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">
                    <div class="flex items-center gap-3 mb-3">
                        <div class="w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold flex-shrink-0"
                             style="background:linear-gradient(135deg,#7c3aed,#3b82f6);color:white;">
                            ${w.presenter.charAt(0).toUpperCase()}
                        </div>
                        <div>
                            <p class="text-white font-semibold text-sm">${w.presenter}</p>
                            <p class="text-xs text-purple-400">Session Host</p>
                        </div>
                    </div>
                    ${w.speaker_bio ? `<p class="text-gray-400 text-xs leading-relaxed">${w.speaker_bio}</p>` : ''}
                </div>` : ''}
                <div class="rounded-xl p-4 border"
                     style="background:linear-gradient(135deg,rgba(124,58,237,.08),rgba(59,130,246,.05));border-color:rgba(124,58,237,.25);">
                    <p class="text-white font-semibold text-sm mb-1 flex items-center gap-2">
                        <i class="fas fa-bolt text-yellow-400 text-xs"></i>
                        Try while watching
                    </p>
                    <p class="text-gray-500 text-xs mb-3">Apply what you learn in real time:</p>
                    <div class="space-y-2">
                        <button onclick="dashboard.navigate('analysis')"
                                class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all hover:opacity-90"
                                style="background:rgba(124,58,237,.15);color:#c4b5fd;border:1px solid rgba(124,58,237,.2);">
                            <i class="fas fa-chart-bar w-4 text-center"></i>
                            <div class="text-left">
                                <div class="font-semibold text-xs">AI Chart Analysis</div>
                                <div class="text-purple-400 text-xs opacity-70">Upload &amp; analyse your chart</div>
                            </div>
                            <i class="fas fa-arrow-right ml-auto text-xs opacity-50"></i>
                        </button>
                        <button onclick="dashboard.navigate('mentor')"
                                class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all hover:opacity-90"
                                style="background:rgba(59,130,246,.12);color:#93c5fd;border:1px solid rgba(59,130,246,.2);">
                            <i class="fas fa-robot w-4 text-center"></i>
                            <div class="text-left">
                                <div class="font-semibold text-xs">AI Mentor</div>
                                <div class="text-blue-400 text-xs opacity-70">Ask questions live</div>
                            </div>
                            <i class="fas fa-arrow-right ml-auto text-xs opacity-50"></i>
                        </button>
                        <button onclick="dashboard.navigate('enhanced-signals')"
                                class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all hover:opacity-90"
                                style="background:rgba(16,185,129,.1);color:#6ee7b7;border:1px solid rgba(16,185,129,.2);">
                            <i class="fas fa-satellite-dish w-4 text-center"></i>
                            <div class="text-left">
                                <div class="font-semibold text-xs">Live Signals</div>
                                <div class="text-green-400 text-xs opacity-70">Follow along on the chart</div>
                            </div>
                            <i class="fas fa-arrow-right ml-auto text-xs opacity-50"></i>
                        </button>
                    </div>
                </div>
                ${w.tags ? `
                <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">
                    <p class="text-xs text-gray-500 mb-2 font-semibold uppercase tracking-wider">Topics</p>
                    <div class="flex flex-wrap gap-1.5">
                        ${w.tags.split(',').map(t => t.trim()).filter(Boolean).map(t => `
                        <span class="px-2 py-0.5 rounded text-xs"
                              style="background:rgba(124,58,237,.15);color:#a78bfa;">
                            ${t}
                        </span>`).join('')}
                    </div>
                </div>` : ''}
            </div>
        </div>
    </div>`;
};

DashboardController.prototype.registerForWebinar = async function(id, btn) {
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Registering…';
    }
    try {
        const res = await this.apiRequest(`/webinars/${id}/register`, { method: 'POST' });
        if (btn) {
            btn.innerHTML = '<i class="fas fa-check mr-1"></i> Registered';
            btn.style.cssText += ';background:rgba(16,185,129,.15);color:#34d399;border-color:rgba(16,185,129,.3);cursor:default;';
        }
        this._toast(res.message || "You're registered! We'll remind you before the session.", 'success');
    } catch (err) {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-calendar-check mr-1"></i> Register Free';
        }
        this._toast('Registration failed. Please try again.', 'error');
    }
};

