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
        c.innerHTML = `<div class="text-center py-12 text-gray-500">
            <i class="fas fa-spinner fa-spin text-2xl"></i></div>`;
        try {
            const data = await req('/webinars/upcoming?upcoming=true', ctrl);
            const list = Array.isArray(data) ? data : (data.webinars || []);

            if (!list.length) {
                c.innerHTML = `<div class="text-center py-14 text-gray-500">
                    <i class="fas fa-video text-5xl mb-4 block opacity-20"></i>
                    <p class="font-medium">No upcoming webinars scheduled</p>
                    <p class="text-sm mt-1 text-gray-600">Check back soon for live sessions</p>
                </div>`;
                return;
            }

            c.innerHTML = list.map(w => {
                const d = w.scheduled_at ? new Date(w.scheduled_at) : null;
                const statusCls = w.status === 'live'
                    ? 'bg-red-900/50 text-red-300 border border-red-700/60'
                    : 'bg-green-900/40 text-green-300 border border-green-700/50';
                const statusLabel = w.status === 'live' ? '🔴 Live Now' : 'Upcoming';

                return `
                <div class="bg-gray-800/80 rounded-xl border border-gray-700 hover:border-yellow-600/30
                            transition-all hover:-translate-y-0.5 hover:shadow-md hover:shadow-yellow-900/10">
                    <div class="flex flex-col sm:flex-row gap-0">
                        <!-- date block -->
                        ${d ? `
                        <div class="sm:w-28 flex-shrink-0 flex flex-col items-center justify-center
                                    py-5 bg-gray-700/40 rounded-t-xl sm:rounded-l-xl sm:rounded-tr-none border-b sm:border-b-0 sm:border-r border-gray-700/60">
                            <div class="text-3xl font-black text-yellow-400 leading-none">${d.getDate()}</div>
                            <div class="text-xs text-gray-400 uppercase tracking-widest mt-0.5">
                                ${d.toLocaleString('default',{month:'short'})}
                            </div>
                            <div class="text-xs text-gray-600 mt-0.5">
                                ${d.toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit'})}
                            </div>
                        </div>` : ''}
                        <!-- info -->
                        <div class="flex-1 p-5">
                            <div class="flex items-start justify-between gap-2 mb-2">
                                <h4 class="font-bold text-white text-base leading-snug">${w.title}</h4>
                                <span class="text-xs font-semibold px-2 py-0.5 rounded-full flex-shrink-0 ${statusCls}">
                                    ${statusLabel}
                                </span>
                            </div>
                            ${w.description ? `<p class="text-sm text-gray-400 line-clamp-2 mb-3">${w.description}</p>` : ''}
                            <div class="flex flex-wrap gap-3 text-xs text-gray-500 mb-4">
                                ${w.presenter ? `<span><i class="fas fa-user mr-1.5"></i>${w.presenter}</span>` : ''}
                                ${w.duration_minutes ? `<span><i class="fas fa-clock mr-1.5"></i>${w.duration_minutes} mins</span>` : ''}
                                ${w.max_attendees ? `<span><i class="fas fa-users mr-1.5"></i>${w.max_attendees} seats</span>` : ''}
                            </div>
                            ${w.meeting_link
                                ? `<a href="${w.meeting_link}" target="_blank" rel="noopener"
                                      class="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all
                                             hover:brightness-110 active:scale-95"
                                      style="background:rgba(124,58,237,.25);color:#c4b5fd;border:1px solid rgba(124,58,237,.4);">
                                       <i class="fas fa-video text-xs"></i> Join Meeting →
                                   </a>`
                                : `<span class="inline-flex items-center gap-1.5 text-xs text-gray-600 border border-gray-700 px-3 py-1.5 rounded-lg">
                                       <i class="fas fa-hourglass-half"></i> Link coming soon
                                   </span>`}
                        </div>
                    </div>
                </div>`;
            }).join('');

        } catch (e) {
            c.innerHTML = `<div class="text-center py-10 text-gray-500">
                <p class="text-sm text-red-400">Could not load webinars: ${e.message}</p></div>`;
        }
    }


    // ── BLOG ─────────────────────────────────────────────────────────────────
    async function blog(containerId = 'blog-container', ctrl = null) {
        spinner(containerId);
        try {
            const data = await req('/blog/posts', ctrl);
            const list = Array.isArray(data) ? data : (data.posts || []);
            const c = el(containerId); if (!c) return;

            if (!list.length) {
                empty(containerId, 'fa-newspaper', 'No articles published yet');
                return;
            }

            c.innerHTML = list.map((p, i) => {
                const big = i === 0;  // first post gets hero treatment
                const cat = p.category || 'General';
                const date = p.created_at ? new Date(p.created_at).toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'}) : '';

                if (big) {
                    return `
                    <article class="col-span-full bg-gray-800/80 rounded-xl border border-gray-700
                                    hover:border-blue-600/40 transition-all cursor-pointer group overflow-hidden
                                    grid grid-cols-1 lg:grid-cols-2">
                        <div class="relative overflow-hidden ${p.featured_image ? '' : 'h-56 lg:h-auto'}">
                            ${p.featured_image
                                ? `<img src="${p.featured_image}" class="w-full h-56 lg:h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                        onerror="this.parentElement.classList.add('fallback-bg')">`
                                : `<div class="h-56 lg:h-full bg-gradient-to-br from-blue-900 via-indigo-900 to-purple-900 flex items-center justify-center">
                                       <i class="fas fa-newspaper text-6xl text-white/10"></i>
                                   </div>`}
                        </div>
                        <div class="p-6 lg:p-8 flex flex-col justify-center">
                            <div class="flex items-center gap-2 mb-3">
                                <span class="text-xs font-bold text-blue-400 bg-blue-900/40 border border-blue-700/50 px-2.5 py-0.5 rounded-full uppercase tracking-wide">${cat}</span>
                                ${p.featured ? '<span class="text-xs text-yellow-400">⭐ Featured</span>' : ''}
                            </div>
                            <h3 class="text-xl lg:text-2xl font-bold text-white leading-snug mb-3 group-hover:text-blue-300 transition-colors">${p.title}</h3>
                            <p class="text-gray-400 text-sm leading-relaxed mb-5 line-clamp-3">${p.excerpt || ''}</p>
                            <div class="flex items-center justify-between text-xs text-gray-500">
                                <div class="flex items-center gap-3">
                                    ${date ? `<span><i class="fas fa-calendar mr-1"></i>${date}</span>` : ''}
                                    ${p.read_time ? `<span><i class="fas fa-clock mr-1"></i>${p.read_time}</span>` : ''}
                                    ${p.views ? `<span><i class="fas fa-eye mr-1"></i>${p.views}</span>` : ''}
                                </div>
                                <span class="text-blue-400 font-semibold group-hover:text-blue-300">Read →</span>
                            </div>
                        </div>
                    </article>`;
                }

                return `
                <article class="bg-gray-800/80 rounded-xl border border-gray-700 hover:border-blue-600/40
                                transition-all cursor-pointer group overflow-hidden hover:-translate-y-0.5 hover:shadow-md hover:shadow-blue-900/10">
                    ${p.featured_image
                        ? `<div class="overflow-hidden h-44">
                               <img src="${p.featured_image}" class="w-full h-44 object-cover group-hover:scale-105 transition-transform duration-500"
                                    onerror="this.parentElement.outerHTML='<div class=\\'h-44 bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center\\'><i class=\\'fas fa-newspaper text-3xl text-gray-600\\'></i></div>'">`
                        + `</div>`
                        : `<div class="h-44 bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center">
                               <i class="fas fa-newspaper text-4xl text-gray-600 group-hover:text-gray-500 transition-colors"></i>
                           </div>`}
                    <div class="p-5">
                        <div class="flex items-center gap-1.5 mb-2">
                            <span class="text-xs font-semibold text-purple-400 uppercase tracking-wide">${cat}</span>
                        </div>
                        <h4 class="font-bold text-white mb-2 leading-snug group-hover:text-blue-300 transition-colors line-clamp-2">${p.title}</h4>
                        <p class="text-sm text-gray-400 line-clamp-2 mb-4">${p.excerpt || ''}</p>
                        <div class="flex justify-between items-center text-xs text-gray-600">
                            <div class="flex items-center gap-2">
                                ${date ? `<span>${date}</span>` : ''}
                                ${p.read_time ? `<span>· ${p.read_time}</span>` : ''}
                            </div>
                            <span class="text-purple-400 group-hover:text-purple-300 font-medium">Read more →</span>
                        </div>
                    </div>
                </article>`;
            }).join('');

        } catch (e) {
            errBox(containerId, `Could not load articles: ${e.message}`);
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


    // ── public API ────────────────────────────────────────────────────────────
    return { signals, webinars, blog, courses };
})();

window.PublicPages = PublicPages;
