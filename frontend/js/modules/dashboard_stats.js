// Dashboard Module: Dashboard Stats
// Extracted from dashboard.js for maintainability

DashboardController.prototype.loadDashboardStats = async function() {
    this._initClock();
    this._initTicker();
    this._setGreeting();
    this._initSessionPill();
    this._initSocialProof();
    this._initUsageBars();
    const _navAtStart = this._currentSection;
    await this._loadDashboardCards();
    if (this._currentSection !== _navAtStart) return;
};

DashboardController.prototype._initSessionPill = function() {
    const update = () => {
        const now = new Date();
        const utcH = now.getUTCHours();
        const utcM = now.getUTCMinutes();
        const watH = (utcH + 1) % 24;
        const t = watH * 60 + utcM;

        const sessions = [
            { name: 'Sydney',        open: 23*60, close: 24*60+8*60,  color: '#34d399' },
            { name: 'Tokyo',         open: 1*60,  close: 10*60,       color: '#60a5fa' },
            { name: 'London',        open: 9*60,  close: 18*60,       color: '#a78bfa' },
            { name: 'New York',      open: 14*60, close: 23*60,       color: '#f59e0b' },
        ];
        const overlap = (t >= 9*60 && t < 10*60) ? 'Tokyo–London' :
                        (t >= 14*60 && t < 18*60) ? 'London–NY (Peak)' : null;

        let active = sessions.filter(s => {
            if (s.close > 24*60) return t >= s.open || t < s.close - 24*60;
            return t >= s.open && t < s.close;
        });

        const lbl   = document.getElementById('stat-session-label');
        const nyEl  = document.getElementById('dash-ny-countdown');

        if (lbl) {
            if (overlap) {
                lbl.textContent = overlap + ' overlap';
                lbl.style.color = '#fbbf24';
            } else if (active.length) {
                lbl.textContent = active[0].name + ' open';
                lbl.style.color = active[0].color;
            } else {
                lbl.textContent = 'Markets closed';
                lbl.style.color = '#6b7280';
            }
        }

        if (nyEl) {
            const nyOpenWat = 14*60;
            const minsToNY = t < nyOpenWat ? nyOpenWat - t : (24*60 - t + nyOpenWat);
            const hh = Math.floor(minsToNY / 60);
            const mm = minsToNY % 60;
            nyEl.textContent = t >= 14*60 && t < 23*60 ? 'Open now' : hh + 'h ' + mm + 'm';
        }
    };
    update();
    setInterval(update, 60000);
};

DashboardController.prototype._initSocialProof = function() {
    const el = document.getElementById('dash-social-proof');
    if (!el) return;
    const counts = [247, 312, 289, 271, 334, 298, 261];
    const n = counts[new Date().getDate() % counts.length];
    el.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-green-400 flex-shrink-0" style="animation:pulse-dot 2s infinite;"></span>'
        + '<span style="color:#9ca3af;font-size:.75rem;">'
        + '<strong style="color:white;">' + n + '</strong> chart analyses run today by Gopipways traders</span>';
};

DashboardController.prototype._initUsageBars = function() {
    const _wire = () => {
        const barEl = document.getElementById('dash-chart-usage-bar');
        if (barEl && typeof PipwaysUsage !== 'undefined') {
            PipwaysUsage.renderBadge('chart_analysis', barEl);
        }
        if (typeof PipwaysUsage !== 'undefined') {
            const tier = PipwaysUsage.tier;
            if (tier === 'basic' || tier === 'pro') {
                const lockEl = document.getElementById('dash-signals-lock');
                if (lockEl) lockEl.style.display = 'none';
            }
        }
    };

    if (typeof PipwaysUsage !== 'undefined' && PipwaysUsage.isLoaded) {
        _wire();
    } else {
        document.addEventListener('pipways:usage-updated', _wire, { once: true });
        setTimeout(_wire, 1500);
    }
};

DashboardController.prototype._loadDashboardCards = async function() {
    const safe = fn => fn.catch(() => null);
    const set  = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    const _e   = s => s == null ? '' : String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

    function _premiumFeatureCard(icon, color, bg, border, title, sub, section, href, isPaid, tag) {
        var tagHtml = tag
            ? '<span style="font-size:.65rem;font-weight:700;padding:.15rem .5rem;border-radius:9999px;background:' + color + '20;color:' + color + ';border:1px solid ' + color + '33;flex-shrink:0;">' + tag + '</span>'
            : '';
        var lockHtml = (!isPaid && !href)
            ? '<i class="fas fa-lock" style="font-size:.55rem;margin-left:.3rem;opacity:.55;color:#6b7280;"></i>'
            : '';
        var dataNav = href ? 'data-href="' + href + '"' : 'data-section="' + section + '"';
        return '<div class="pw-tool-card" ' + dataNav + ' '
            + 'style="background:' + bg + ';border:1px solid ' + border + ';border-radius:.75rem;padding:.85rem;cursor:pointer;transition:all .2s;">'
            + '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.5rem;">'
            + '<div style="width:32px;height:32px;border-radius:.5rem;background:' + color + '20;display:flex;align-items:center;justify-content:center;flex-shrink:0;">'
            + '<i class="fas ' + icon + '" style="color:' + color + ';font-size:.82rem;"></i></div>'
            + tagHtml
            + '</div>'
            + '<div style="font-size:.8rem;font-weight:700;color:white;line-height:1.3;">' + title + lockHtml + '</div>'
            + '<div style="font-size:.7rem;color:#6b7280;margin-top:.2rem;line-height:1.35;">' + sub + '</div>'
            + '</div>';
    }

    function _buildToolsHub(isPaid) {
        var html = '<div class="rounded-xl p-4 mb-3 pw-tool-card" data-section="analysis" '
            + 'style="background:linear-gradient(135deg,rgba(96,165,250,.08),rgba(124,58,237,.08));border:1px solid rgba(96,165,250,.2);">'
            + '<div style="display:flex;align-items:center;gap:.75rem;margin-bottom:.5rem;">'
            + '<div style="width:40px;height:40px;border-radius:.75rem;background:rgba(96,165,250,.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;">'
            + '<i class="fas fa-chart-bar" style="color:#60a5fa;font-size:1rem;"></i></div>'
            + '<div style="flex:1;min-width:0;">'
            + '<div style="font-size:.875rem;font-weight:700;color:white;">Analyse a Chart</div>'
            + '<div style="font-size:.72rem;color:#6b7280;">Upload any screenshot — get entry, stop &amp; target instantly</div>'
            + '</div>'
            + '<span style="font-size:.65rem;font-weight:700;padding:.2rem .55rem;border-radius:9999px;background:rgba(52,211,153,.12);color:#34d399;border:1px solid rgba(52,211,153,.25);flex-shrink:0;">Free</span>'
            + '</div>'
            + '<div id="dash-chart-usage"></div>'
            + '<div style="display:flex;align-items:center;justify-content:space-between;margin-top:.5rem;">'
            + '<span style="font-size:.72rem;color:#6b7280;"><i class="fas fa-upload" style="margin-right:.25rem;"></i>Drag &amp; drop or click to upload</span>'
            + '<span style="font-size:.72rem;font-weight:700;color:#60a5fa;">Open →</span>'
            + '</div>'
            + '</div>'
            + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:.65rem;">'
            + _premiumFeatureCard('fa-file-chart-pie','#a78bfa','rgba(124,58,237,.08)','rgba(124,58,237,.2)','Performance Analysis','Upload MT4/MT5 · find your weaknesses','journal',null,isPaid,isPaid?null:'1 free')
            + _premiumFeatureCard('fa-chart-pie','#34d399','rgba(52,211,153,.08)','rgba(52,211,153,.2)','AI Stock Research','NGX + global stocks analysis','stocks',null,isPaid,isPaid?null:'2/day')
            + _premiumFeatureCard('fa-satellite-dish','#f472b6','rgba(244,114,182,.08)','rgba(244,114,182,.2)','Market Signals','Live setups with validation','signals',null,isPaid,isPaid?null:'Preview')
            + _premiumFeatureCard('fa-book-open','#fbbf24','rgba(251,191,36,.08)','rgba(251,191,36,.2)','Trading Academy','28 lessons · always free',null,'/academy',true,'Free')
            + '</div>';
        return html;
    }

    const [courses, webinars, blog, signals, progress, academyResume] = await Promise.all([
        safe(this.apiRequest('/courses/list')),
        safe(this.apiRequest('/webinars/upcoming?upcoming=true')),
        safe(this.apiRequest('/blog/posts')),
        safe(this.apiRequest('/api/signals/active')),
        safe(this.apiRequest(`/learning/progress/${this.user?.id || 0}`)),
        safe(this.apiRequest('/learning/resume')),
    ]);

    const count = d => Array.isArray(d) ? d.length
        : (d?.courses?.length || d?.signals?.length || d?.posts?.length || d?.webinars?.length || 0);

    const setChip = (id, val, sub) => {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = val;
            el.classList.remove('stat-updated');
            void el.offsetWidth;
            el.classList.add('stat-updated');
        }
        const subEl = document.getElementById(id + '-sub');
        if (subEl) subEl.textContent = sub || '';
    };
    const courseArr = Array.isArray(courses) ? courses : [];
    const inProgCount = (progress?.in_progress || []).length;
    const completedCount = (progress?.completed || []).length;
    const coursesSub = '';
    const webinarArr = Array.isArray(webinars) ? webinars : (webinars?.webinars || []);
    const webinarsSub = webinarArr.length > 0 ? 'This week' : '';
    const blogArr = Array.isArray(blog) ? blog : (blog?.posts || []);
    const signalArr = Array.isArray(signals) ? signals : (signals?.signals || []);
    const activeSignals = signalArr.filter(s => s.status === 'active').length;
    const signalsSub = activeSignals > 0 ? `${activeSignals} active now` : signalArr.length > 0 ? 'No active signals' : '';
    const academyLessonsCount = (() => {
        if (progress?.completed_lessons != null) return String(progress.completed_lessons);
        if (!academyResume) return '0';
        if (academyResume.type === 'complete') return '28';
        if (academyResume.overall_percent > 0) {
            const approx = Math.round((academyResume.overall_percent / 100) * 28);
            return approx > 0 ? String(approx) : '1';
        }
        return '0';
    })();
    setChip('stat-courses', academyLessonsCount, academyResume?.type === 'complete' ? 'All done! 🎉' : 'lessons done');
    setChip('stat-webinars', webinars ? count(webinars) : '—', webinarsSub);
    setChip('stat-blog',     blog     ? count(blog)     : '—', blogArr.length > 0 ? 'Latest articles' : '');
    setChip('stat-signals',  signals  ? count(signals)  : '—', signalsSub);

    const learningEl = document.getElementById('dash-learning-body');
    if (learningEl) {
        const name = this.user?.full_name?.split(' ')[0] || 'Trader';

        if (!academyResume || academyResume.type === 'start') {
            learningEl.innerHTML =
                '<div class="flex flex-col items-center text-center py-3">'
                + '<div class="w-14 h-14 rounded-full flex items-center justify-center mb-3" style="background:rgba(52,211,153,.08);border:2px dashed rgba(52,211,153,.2);">'
                + '<i class="fas fa-book-open" style="color:#34d399;font-size:1.25rem;"></i>'
                + '</div>'
                + '<p class="font-semibold text-white mb-1 text-sm">Start your Trading Academy, ' + _e(name) + '</p>'
                + '<p class="text-xs mb-4" style="color:#4b5563;line-height:1.5;">28 free lessons · from first pip to institutional strategy</p>'
                + '<a href="/academy" class="px-4 py-2 rounded-lg text-sm font-semibold text-decoration-none" style="background:linear-gradient(90deg,#7c3aed,#6d28d9);color:white;">'
                + '<i class="fas fa-graduation-cap mr-1.5"></i>Begin Academy →</a>'
                + '</div>';

        } else if (academyResume.type === 'complete') {
            learningEl.innerHTML =
                '<div class="flex flex-col items-center text-center py-3">'
                + '<div class="w-14 h-14 rounded-full flex items-center justify-center mb-3" style="background:rgba(251,191,36,.1);border:2px dashed rgba(251,191,36,.2);">'
                + '<i class="fas fa-trophy" style="color:#fbbf24;font-size:1.25rem;"></i>'
                + '</div>'
                + '<p class="font-semibold text-white mb-1 text-sm">Academy Complete! 🏆</p>'
                + '<p class="text-xs mb-4" style="color:#4b5563;">All 28 lessons done. Review any module anytime.</p>'
                + '<a href="/academy" class="px-4 py-2 rounded-lg text-sm font-semibold text-decoration-none" style="background:rgba(251,191,36,.12);border:1px solid rgba(251,191,36,.3);color:#fbbf24;">'
                + 'Review Academy →</a>'
                + '</div>';

        } else {
            const levelName  = academyResume.level || 'Beginner';
            const levelPct   = 0;
            const totalPct   = academyResume.overall_percent || 0;
            const lessonTitle = academyResume.title || 'Next Lesson';
            const moduleName  = academyResume.module || '';
            const lessonId    = academyResume.lesson_id;

            const levels = [
                { name: 'Beginner',     color: '#34d399' },
                { name: 'Intermediate', color: '#60a5fa' },
                { name: 'Advanced',     color: '#f59e0b' },
            ];
            
            const _summaryMap = {};
            if (progress?.summary?.length) {
                progress.summary.forEach(s => {
                    _summaryMap[(s.level_name || '').toLowerCase()] = Math.round(s.percent || 0);
                });
            }

            const progBars = levels.map(lv => {
                const key = lv.name.toLowerCase();
                const pct = _summaryMap[key] != null ? _summaryMap[key]
                            : (levelName === lv.name ? Math.round(levelPct) : 0);

                return '<div style="margin-bottom:.6rem;">'
                    + '<div class="flex items-center justify-between mb-1">'
                    + '<span class="text-xs" style="color:' + lv.color + ';">' + lv.name + '</span>'
                    + '<span class="text-xs font-bold" style="color:' + lv.color + ';">' + pct + '%</span>'
                    + '</div>'
                    + '<div class="pw-progress-bar" style="height:5px;">'
                    + '<div class="pw-progress-fill" style="width:' + pct + '%;background:' + lv.color + ';transition:width .6s ease;"></div>'
                    + '</div>'
                    + '</div>';
            }).join('');

            const lessonChip =
                '<div class="flex items-center gap-2 mt-3 p-2.5 rounded-lg" style="background:rgba(124,58,237,.07);border:1px solid rgba(124,58,237,.15);">'
                + '<div class="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0" style="background:rgba(124,58,237,.2);">'
                + '<i class="fas fa-play" style="color:#a78bfa;font-size:.55rem;margin-left:1px;"></i></div>'
                + '<div class="min-w-0 flex-1">'
                + '<div class="text-xs" style="color:#6b7280;">' + _e(moduleName) + ' · ' + _e(levelName) + '</div>'
                + '<div class="text-xs font-semibold text-white truncate">' + _e(lessonTitle) + '</div>'
                + '</div>'
                + '<a href="/academy' + (lessonId ? '?lesson=' + lessonId : '') + '" class="text-xs font-semibold flex-shrink-0 text-decoration-none" style="color:#a78bfa;">Continue →</a>'
                + '</div>';

            learningEl.innerHTML = progBars + lessonChip;
        }
    }

    const coursesEl = document.getElementById('dash-courses-body');
    if (coursesEl) {
        const tier = (JSON.parse(localStorage.getItem('pipways_user') || '{}').subscription_tier) || 'free';
        const isPaid = tier === 'basic' || tier === 'pro';

        coursesEl.innerHTML = _buildToolsHub(isPaid);

        coursesEl.querySelectorAll('.pw-tool-card').forEach(function(card) {
            card.addEventListener('click', function() {
                var href    = this.dataset.href;
                var section = this.dataset.section;
                if (href)    window.location.href = href;
                else if (section) dashboard.navigate(section);
            });
            card.addEventListener('mouseenter', function() { this.style.opacity = '0.88'; });
            card.addEventListener('mouseleave',  function() { this.style.opacity = '1'; });
        });

        var badgeEl = document.getElementById('dash-chart-usage');
        if (badgeEl) {
            var _renderToolBadge = function() {
                if (typeof PipwaysUsage !== 'undefined') {
                    PipwaysUsage.renderBadge('chart_analysis', badgeEl);
                }
            };
            if (typeof PipwaysUsage !== 'undefined' && PipwaysUsage.isLoaded) {
                _renderToolBadge();
            } else {
                setTimeout(_renderToolBadge, 1500);
            }
        }
    }

    const insightCard = document.getElementById('ai-insight-card');
    if (insightCard) {
        const completionRate = progress?.overall_progress || 0;
        if (completionRate >= 30) {
            insightCard.classList.remove('hidden');
        } else {
            insightCard.classList.add('hidden');
        }
    }

    if (this.lastAnalysisResults) {
        this._updateDashPerfCard(this.lastAnalysisResults);
    }

    const blogEl = document.getElementById('dash-blog-body');
    if (blogEl) {
        const posts = Array.isArray(blog) ? blog : (blog?.posts || []);
        const list = posts.slice(0, 4);
        if (!list.length) {
            blogEl.innerHTML = `<div class="pw-empty" style="padding:2rem 1rem;">
                <div class="pw-empty-icon" style="width:44px;height:44px;"><i class="fas fa-newspaper" style="color:#6b7280;"></i></div>
                <p class="pw-empty-title">No articles yet</p>
                <p class="pw-empty-sub" style="margin-bottom:1.25rem;">Research and market insights are coming soon.</p>
                <a href="/academy" class="text-xs font-semibold px-4 py-2 rounded-lg text-decoration-none"
                   style="background:rgba(124,58,237,.15);border:1px solid rgba(124,58,237,.3);color:#a78bfa;">
                    <i class="fas fa-graduation-cap mr-1"></i>Browse Academy instead →
                </a>
            </div>`;
        } else {
            // ── FIX: use DOM API instead of nested template literals ──
            // Nested backtick + onerror + col variable caused SyntaxError
            const grid = document.createElement('div');
            grid.className = 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3';

            list.forEach(p => {
                const catColors = {'Market Analysis':'#60a5fa','Strategy':'#a78bfa','Education':'#34d399','General':'#9ca3af'};
                const col  = catColors[p.category] || '#9ca3af';
                const date = p.created_at ? new Date(p.created_at).toLocaleDateString('en-GB',{day:'numeric',month:'short'}) : '';

                const card = document.createElement('div');
                card.className = 'rounded-xl cursor-pointer transition-all duration-200 overflow-hidden';
                card.style.cssText = 'border:1px solid #1f2937;background:#0d1321;';
                card.addEventListener('click', () => dashboard.navigate('blog'));
                card.addEventListener('mouseover', function() { this.style.borderColor = '#374151'; this.style.transform = 'translateY(-2px)'; });
                card.addEventListener('mouseout',  function() { this.style.borderColor = '#1f2937';  this.style.transform = ''; });

                // Thumb — build image/placeholder safely without inline onerror string injection
                const thumb = document.createElement('div');
                thumb.className = 'pw-blog-thumb';

                if (p.featured_image) {
                    const img = document.createElement('img');
                    img.src = p.featured_image;
                    img.alt = '';
                    img.style.cssText = 'width:100%;height:100%;object-fit:cover;';
                    const placeholder = document.createElement('div');
                    placeholder.className = 'pw-blog-thumb-placeholder';
                    placeholder.style.display = 'none';
                    placeholder.innerHTML = '<i class="fas fa-newspaper text-xl" style="color:' + col + ';opacity:.4;"></i>';
                    img.addEventListener('error', function() {
                        this.style.display = 'none';
                        placeholder.style.display = 'flex';
                    });
                    thumb.appendChild(img);
                    thumb.appendChild(placeholder);
                } else {
                    const placeholder = document.createElement('div');
                    placeholder.className = 'pw-blog-thumb-placeholder';
                    placeholder.innerHTML = '<i class="fas fa-newspaper text-xl" style="color:' + col + ';opacity:.4;"></i>';
                    thumb.appendChild(placeholder);
                }

                // Category label overlay
                const overlay = document.createElement('div');
                overlay.className = 'absolute bottom-0 left-0 right-0 px-3 py-1';
                overlay.style.background = 'linear-gradient(transparent,rgba(0,0,0,.6))';
                const catSpan = document.createElement('span');
                catSpan.className = 'text-xs font-bold';
                catSpan.style.color = col;
                catSpan.textContent = (p.category || 'General').toUpperCase();
                overlay.appendChild(catSpan);
                thumb.appendChild(overlay);

                // Body
                const body = document.createElement('div');
                body.className = 'p-3';
                body.innerHTML = '<div class="text-sm font-medium text-white line-clamp-2 mb-2 leading-snug">' + _e(p.title) + '</div>'
                    + '<div class="text-xs text-gray-600">' + date + '</div>';

                card.appendChild(thumb);
                card.appendChild(body);
                grid.appendChild(card);
            });

            blogEl.innerHTML = '';
            blogEl.appendChild(grid);
        }
    }
};

DashboardController.prototype._setGreeting = function() {
    const h = new Date().getHours();
    const greet = h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
    const emoji = h < 12 ? '☀️' : h < 17 ? '📈' : '🌙';
    const subs = h < 12
        ? 'Upload a chart or check your Academy progress to start strong.'
        : h < 17
        ? 'Prime trading window — London–NY overlap is the highest probability session.'
        : 'Review your journal and plan tomorrow\'s setups.';
    const el   = document.getElementById('greeting-text');
    const sub  = document.getElementById('greeting-sub');
    const name = this.user?.full_name?.split(' ')[0] || 'Trader';
    if (el)  el.textContent  = `${greet}, ${name} ${emoji}`;
    if (sub) sub.textContent = subs;
    if (el)  el.classList.remove('hidden');
    if (sub) sub.classList.remove('hidden');
    const tsEl = document.getElementById('insight-timestamp');
    if (tsEl) {
        const d = new Date();
        tsEl.textContent = d.toLocaleDateString('en-GB',{weekday:'short',day:'numeric',month:'short'});
    }
};

DashboardController.prototype._initClock = function() {
    const tick = () => {
        const now    = new Date();
        const clockEl = document.getElementById('live-clock');
        if (clockEl) clockEl.textContent = now.toLocaleTimeString('en-US', { hour12: false });

        const day   = now.getUTCDay();
        const hours = now.getUTCHours();
        const mins  = now.getUTCMinutes();
        const timeInMins = hours * 60 + mins;
        const isOpen = !(day === 6 || (day === 5 && timeInMins >= 21*60) || (day === 0 && timeInMins < 21*60));

        const statusEl = document.getElementById('market-status-text');
        const dotEl    = document.getElementById('market-status-dot');
        if (statusEl) {
            statusEl.textContent = isOpen ? 'Markets Open' : 'Markets Closed';
            statusEl.className   = isOpen ? 'text-green-400 font-medium' : 'text-red-400 font-medium';
        }
        if (dotEl) {
            dotEl.style.background = isOpen ? '#4ade80' : '#f87171';
        }
        const dashDot  = document.getElementById('dash-market-dot');
        const dashText = document.getElementById('dash-market-text');
        if (dashDot)  dashDot.style.background  = isOpen ? '#4ade80' : '#f87171';
        if (dashText) dashText.textContent = isOpen ? 'Markets Open' : 'Markets Closed';
        const heroDot  = document.getElementById('hero-market-dot');
        const heroText = document.getElementById('hero-market-text');
        if (heroDot)  heroDot.style.background  = isOpen ? '#4ade80' : '#f87171';
        if (heroText) heroText.textContent = isOpen ? 'Markets Open' : 'Markets Closed';
    };
    tick();
    this._clockTimer = setInterval(tick, 1000);
};

DashboardController.prototype._initTicker = function() {
    const pairs = [
        { sym: 'EUR/USD', price: '1.0847', chg: '+0.0012', pct: '+0.11%', up: true },
        { sym: 'GBP/USD', price: '1.2634', chg: '-0.0028', pct: '-0.22%', up: false },
        { sym: 'USD/JPY', price: '149.82', chg: '+0.34',   pct: '+0.23%', up: true  },
        { sym: 'XAU/USD', price: '3,024.5', chg: '+8.20',  pct: '+0.27%', up: true  },
        { sym: 'BTC/USD', price: '83,412',  chg: '-1,240', pct: '-1.47%', up: false },
        { sym: 'ETH/USD', price: '1,894.3', chg: '-32.1',  pct: '-1.67%', up: false },
        { sym: 'USD/CHF', price: '0.9021',  chg: '-0.0008',pct: '-0.09%', up: false },
        { sym: 'AUD/USD', price: '0.6341',  chg: '+0.0019',pct: '+0.30%', up: true  },
        { sym: 'NZD/USD', price: '0.5762',  chg: '+0.0011',pct: '+0.19%', up: true  },
        { sym: 'USD/CAD', price: '1.3892',  chg: '-0.0023',pct: '-0.17%', up: false },
        { sym: 'US30',    price: '41,850',  chg: '+120',   pct: '+0.29%', up: true  },
        { sym: 'US100',   price: '18,240',  chg: '-85',    pct: '-0.46%', up: false },
    ];

    const html = pairs.map(p => `
        <div class="ticker-item">
            <span class="ticker-sym">${p.sym}</span>
            <span class="ticker-price">${p.price}</span>
            <span class="${p.up ? 'ticker-up' : 'ticker-dn'}">${p.pct}</span>
        </div>`).join('');
    const track = document.getElementById('ticker-track');
    if (track) track.innerHTML = html + html;

    const fxEl = document.getElementById('dash-forex-tickers');
    if (fxEl) {
        const featured = ['EUR/USD', 'GBP/USD', 'XAU/USD'];
        fxEl.innerHTML = featured.map((sym, i) => {
            const p = pairs.find(x => x.sym === sym);
            if (!p) return '';
            const isLast = i === featured.length - 1;
            const color = p.up ? '#34d399' : '#f87171';
            return `<div class="flex justify-between py-1.5 ${isLast ? '' : 'border-b'}" style="border-color:#1f2937;">
                <div>
                    <span class="text-xs font-semibold" style="color:#e5e7eb;">${p.sym}</span>
                    <span class="text-xs ml-2" style="color:#4b5563;">${p.price}</span>
                </div>
                <span class="text-xs font-bold" data-base="${parseFloat(p.pct)}" style="color:${color};">${p.pct}</span>
            </div>`;
        }).join('');
        setInterval(() => {
            fxEl.querySelectorAll('[data-base]').forEach(el => {
                const base = parseFloat(el.dataset.base) || 0;
                const val  = base + (Math.random() - 0.5) * 0.06;
                const up   = val >= 0;
                el.textContent  = (up ? '+' : '') + val.toFixed(2) + '%';
                el.style.color  = up ? '#34d399' : '#f87171';
            });
        }, 6000);
    }
};

DashboardController.prototype._updateNextStepCard = function(progress, courses, academyResume) {
    const titleEl = document.getElementById('next-step-title');
    const subEl   = document.getElementById('next-step-sub');
    const ctaEl   = document.getElementById('next-step-cta');
    if (!titleEl || !subEl || !ctaEl) return;

    if (academyResume && academyResume.type === 'continue' && academyResume.lesson_id) {
        const lessonTitle = academyResume.title  || 'Next Lesson';
        const moduleName  = academyResume.module || '';
        const levelName   = academyResume.level  || '';
        titleEl.textContent = `Resume: ${lessonTitle}`;
        subEl.textContent   = `${moduleName}${levelName ? ' · ' + levelName : ''}`;
        ctaEl.href          = `/academy?lesson=${academyResume.lesson_id}`;
        ctaEl.innerHTML     = '<i class="fas fa-play-circle text-xs"></i> Continue Lesson';
    } else if (academyResume && academyResume.type === 'complete') {
        titleEl.textContent = 'Academy Complete! 🏆';
        subEl.textContent   = 'All 28 lessons done. Review any module anytime.';
        ctaEl.href          = '/academy';
        ctaEl.innerHTML     = '<i class="fas fa-trophy text-xs"></i> View Academy';
    } else {
        titleEl.textContent = 'Start your Trading Academy';
        subEl.textContent   = '28 lessons · from first pip to institutional strategy';
        ctaEl.href          = '/academy';
        ctaEl.innerHTML     = '<i class="fas fa-graduation-cap text-xs"></i> Go to Academy';
    }
};

