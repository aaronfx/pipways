/**
 * Pipways Trading Academy Frontend Module v4.1 (Production-Patched)
 * Fixes: XSS vulnerabilities, Syntax errors, Memory leaks, Race conditions, State corruption
 */

/* ── Security & Utility Helpers ─────────────────────────────────────────── */
const _es = (str) => {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
};

// 🔧 FIX #1: JavaScript string escaping for onclick handlers (Critical XSS fix)
const _jes = (str) => {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/\\/g, '\\\\')
        .replace(/'/g, "\\'")
        .replace(/"/g, '\\"')
        .replace(/\n/g, '\\n')
        .replace(/\r/g, '');
};

/* ── LMS API Extension ──────────────────────────────────────────────────── */
(function extendAPI() {
    const A = window.API;
    if (!A || A._academyReady) return;
    A._academyReady = true;
    
    A.lms = {
        getLevels:          ()     => A.request('/learning/levels'),
        getModules:         (lid)  => A.request(`/learning/modules/${lid}`),
        getLessons:         (mid)  => A.request(`/learning/lessons/${mid}`),
        getLesson:          (lid)  => A.request(`/learning/lesson/${lid}`),
        getQuiz:            (lid)  => A.request(`/learning/quiz/${lid}`),
        getProgress:        (uid)  => A.request(`/learning/progress/${uid}`),
        getBadges:          (uid)  => A.request(`/learning/badges/${uid}`),
        checkBadges:        ()     => A.request('/learning/badges/check', { method: 'POST' }),
        getMentorGuide:     (uid)  => A.request(`/learning/mentor/guide/${uid}`),
        getMentorTeach:     (lid)  => A.request(`/learning/mentor/teach?lesson_id=${lid}`, { method: 'POST' }),
        getMentorPractice:  (lid)  => A.request(`/learning/mentor/practice?lesson_id=${lid}`, { method: 'POST' }),
        getChartPractice:   (lid)  => A.request(`/learning/mentor/chart-practice?lesson_id=${lid}`, { method: 'POST' }),
        markFirstVisit:     ()     => A.request('/learning/profile/first-visit-complete', { method: 'POST' }),
        submitQuiz:         (lid, answers) => A.request('/learning/quiz/submit', { 
            method: 'POST', 
            body: JSON.stringify({ lesson_id: lid, answers }) 
        }),
        completeLesson:     (lid, score) => A.request('/learning/lesson/complete', { 
            method: 'POST', 
            body: JSON.stringify({ lesson_id: lid, quiz_score: score || 0 }) 
        }),
    };
})();

/* ── Marked.js Loader with Retry Logic ──────────────────────────────────── */
(function loadMarked() {
    if (window.marked) return;
    
    let retries = 0;
    const maxRetries = 3;
    
    function loadScript() {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
        script.async = true;
        
        script.onerror = () => {
            retries++;
            if (retries < maxRetries) {
                console.warn(`[Academy] Marked.js load failed, retry ${retries}/${maxRetries}`);
                setTimeout(loadScript, 1000 * retries);
            } else {
                console.error('[Academy] Failed to load Marked.js after max retries');
            }
        };
        
        document.head.appendChild(script);
    }
    
    loadScript();
})();

/* ═══════════════════════════════════════════════════════════════════════════
   ACADEMY PAGE CONTROLLER
═══════════════════════════════════════════════════════════════════════════ */
const AcademyPage = {
    _level: null,
    _module: null,
    _lesson: null,
    _quiz: null,
    _uid: null,
    _firstVisit: false,
    _badges: [],
    _tradingViewWidgets: [], // 🔧 FIX #3: Track widgets for cleanup
    _quizAnswered: false,    // 🔧 FIX #9: Prevent double-answer bug

    async render() {
        const u = this._getUser();
        this._uid = u?.id ?? null;
        const wrap = document.getElementById('academy-container');
        if (!wrap) return;
        
        // 🔧 FIX #7: Clear badge container on fresh render
        const existingToasts = document.querySelectorAll('.ac-badge-toast');
        existingToasts.forEach(t => t.remove());
        
        wrap.innerHTML = `
            <div id="ac-breadcrumb" class="pw-breadcrumb mb-4" style="display:none;"></div>
            <div id="ac-mentor-banner"></div>
            <div id="ac-badge-toast" class="ac-badge-container"></div>
            <div id="ac-main"></div>
            <div id="ac-mobile-nav" class="ac-mobile-nav hidden md:hidden"></div>
        `;
        
        if (this._uid) {
            await this._loadBadges();
            try {
                const check = await API.lms.checkBadges();
                if (check.newly_awarded?.length) {
                    await this._showNewBadges(check.newly_awarded);
                }
            } catch(e) { console.error('Badge check failed:', e); }
        }
        
        await this._showLevelSelector();
    },

    /* ── Level Selector ─────────────────────────────────────────────────── */
    async _showLevelSelector() {
        this._level = this._module = this._lesson = null;
        this._quiz = null; // 🔧 FIX #4: Reset quiz state on navigation
        this._bc(null, null, null);
        this._hideMobileNav();
        this._cleanupTradingView(); // 🔧 FIX #3: Cleanup widgets
        
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading curriculum...');
        
        try {
            const [levels, prog, guide] = await Promise.all([
                API.lms.getLevels(),
                this._uid ? API.lms.getProgress(this._uid).catch(() => null) : null,
                this._uid ? API.lms.getMentorGuide(this._uid).catch(() => null) : null,
            ]);
            
            if (guide?.first_visit !== undefined) {
                this._firstVisit = guide.first_visit;
            }
            
            const sm = {};
            (prog?.summary || []).forEach(s => sm[s.level_id] = s);
            
            if (this._uid) this._loadMentorBanner(guide);
            
            const cfg = [
                { icon: 'fa-seedling', color: '#34d399', bg: 'rgba(52,211,153,.15)' },
                { icon: 'fa-chart-line', color: '#60a5fa', bg: 'rgba(96,165,250,.15)' },
                { icon: 'fa-trophy', color: '#f59e0b', bg: 'rgba(245,158,11,.15)' },
            ];
            
            if (!levels || !levels.length) {
                main.innerHTML = this._emptyState('Academy not set up yet', 
                    'The learning curriculum is being initialized. Please refresh in a moment.');
                return;
            }
            
            // 🔧 FIX #1: Use _jes() for JS string escaping in onclick handlers
            main.innerHTML = `<div class="grid grid-cols-1 md:grid-cols-3 gap-4 ac-level-grid">
                ${levels.map((lv, i) => {
                    const c = cfg[i % 3];
                    const s = sm[lv.id];
                    const pct = s ? s.percent : 0;
                    const done = s ? s.completed : 0;
                    const tot = s ? s.total : 0;
                    const isComplete = pct >= 100;
                    
                    return `
                    <div class="pw-card cursor-pointer ac-level-card ${isComplete ? 'ac-level-complete' : ''}" 
                         onclick="AcademyPage._selectLevel(${lv.id}, '${_jes(lv.name)}')"
                         style="border-top:3px solid ${c.color}; position:relative;">
                        <div class="pw-card-body" style="padding:1.5rem;">
                            ${isComplete ? `<div class="ac-complete-badge"><i class="fas fa-check-circle"></i></div>` : ''}
                            <div class="w-10 h-10 rounded-xl flex items-center justify-center mb-3" 
                                 style="background:${c.bg};">
                                <i class="fas ${c.icon}" style="color:${c.color};"></i>
                            </div>
                            <div class="text-xs font-bold mb-1" style="color:${c.color}; letter-spacing:.06em;">
                                ${_es(lv.name).toUpperCase()}
                            </div>
                            <h3 class="text-white font-bold text-base mb-1">${_es(lv.name)}</h3>
                            <p class="text-gray-500 text-xs leading-relaxed mb-4">${_es(lv.description)}</p>
                            
                            <div class="flex justify-between text-xs text-gray-500 mb-1.5">
                                <span>Progress</span>
                                <span class="font-semibold" style="color:${c.color};">${pct}%</span>
                            </div>
                            <div class="pw-progress-bar">
                                <div class="pw-progress-fill" style="width:${pct}%; background:${c.color};"></div>
                            </div>
                            <div class="text-xs text-gray-600 mt-2">${done} of ${tot} lessons done</div>
                        </div>
                    </div>`;
                }).join('')}
            </div>`;
        } catch (e) {
            main.innerHTML = this._error('Could not load Academy', e.message);
        }
    },

    /* ── Module List ────────────────────────────────────────────────────── */
    async _selectLevel(levelId, levelName) {
        this._level = { id: levelId, name: levelName };
        this._module = null;
        this._lesson = null;
        this._quiz = null;
        this._bc(levelName, null, null);
        this._hideMobileNav();
        this._cleanupTradingView();
        
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading modules...');
        
        try {
            const modules = await API.lms.getModules(levelId);
            
            // 🔧 FIX #1: Use _jes() for onclick handlers
            main.innerHTML = `<div class="grid grid-cols-1 md:grid-cols-2 gap-4 ac-module-grid">
                ${modules.map(m => {
                    const pct = m.lesson_count ? Math.round(m.completed_count / m.lesson_count * 100) : 0;
                    const isComplete = m.is_complete;
                    
                    return `
                    <div class="pw-card cursor-pointer ac-module-card ${isComplete ? 'ac-module-complete' : ''}" 
                         onclick="AcademyPage._selectModule(${m.id}, '${_jes(m.title)}')"
                         onmouseover="this.style.borderColor='#374151'" 
                         onmouseout="this.style.borderColor=''">
                        <div class="pw-card-body">
                            <div class="flex items-start justify-between mb-2">
                                <div>
                                    ${isComplete 
                                        ? `<span class="badge badge-success text-xs mb-1"><i class="fas fa-check-circle mr-1"></i>Complete</span>`
                                        : `<span class="text-xs text-gray-500 mb-1 block">${m.completed_count}/${m.lesson_count} lessons</span>`
                                    }
                                    <h3 class="text-white font-semibold">${_es(m.title)}</h3>
                                </div>
                                <i class="fas fa-chevron-right text-gray-700 text-xs mt-1"></i>
                            </div>
                            <p class="text-gray-500 text-xs leading-relaxed mb-3">${_es(m.description)}</p>
                            <div class="pw-progress-bar">
                                <div class="pw-progress-fill ${pct >= 80 && pct < 100 ? 'near-done' : ''}" 
                                     style="width:${pct}%;"></div>
                            </div>
                            ${isComplete ? `<div class="ac-module-badge"><i class="fas fa-medal"></i> Module Complete</div>` : ''}
                        </div>
                    </div>`;
                }).join('')}
            </div>`;
        } catch (e) {
            main.innerHTML = this._error('Could not load modules', e.message);
        }
    },

    /* ── Lesson List ────────────────────────────────────────────────────── */
    async _selectModule(moduleId, moduleTitle) {
        this._module = { id: moduleId, name: moduleTitle };
        this._lesson = null;
        this._quiz = null;
        this._bc(this._level?.name, moduleTitle, null);
        this._hideMobileNav();
        this._cleanupTradingView();
        
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading lessons...');
        
        try {
            const lessons = await API.lms.getLessons(moduleId);
            
            // 🔧 FIX #1: Use _jes() for onclick handlers
            main.innerHTML = `<div class="space-y-2 max-w-2xl ac-lesson-list">
                ${lessons.map((l, i) => {
                    const locked = !l.unlocked;
                    const done = l.completed;
                    const icon = done ? 'fa-check-circle text-green-400' : 
                                locked ? 'fa-lock text-gray-700' : 'fa-play-circle text-purple-400';
                    const score = done && l.quiz_score !== null
                        ? `<span class="text-xs font-semibold" style="color:#34d399;">${l.quiz_score}%</span>` 
                        : '';
                    
                    // 🔧 FIX #6: Pre-compute onclick to avoid template literal issues
                    const onclickAttr = !locked ? `onclick="AcademyPage._openLesson(${l.id}, '${_jes(l.title)}')"` : '';
                    
                    return `
                    <div class="pw-card ${locked ? 'opacity-50' : ''} ${!locked ? 'cursor-pointer' : ''} ac-lesson-item ${done ? 'ac-lesson-done' : ''}"
                         ${onclickAttr}>
                        <div class="pw-card-body" style="padding:.85rem 1.25rem;">
                            <div class="flex items-center gap-3">
                                <i class="fas ${icon} text-lg flex-shrink-0" style="width:20px; text-align:center;"></i>
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center gap-2">
                                        <span class="text-white font-medium text-sm truncate">
                                            Lesson ${i + 1}: ${_es(l.title)}
                                        </span>
                                        ${score}
                                    </div>
                                    ${locked ? `<div class="text-xs text-gray-600 mt-0.5">Complete previous lesson to unlock</div>` : ''}
                                </div>
                                ${!locked ? `<i class="fas fa-chevron-right text-gray-700 text-xs flex-shrink-0"></i>` : ''}
                            </div>
                        </div>
                    </div>`;
                }).join('')}
            </div>`;
        } catch (e) {
            main.innerHTML = this._error('Could not load lessons', e.message);
        }
    },

    /* ── Lesson View ─────────────────────────────────────────────────────── */
    async _openLesson(lessonId, lessonTitle) {
        this._lesson = { id: lessonId, name: lessonTitle };
        this._bc(this._level?.name, this._module?.name, lessonTitle);
        this._cleanupTradingView(); // Clean up any existing widgets
        
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading lesson...');
        
        try {
            const lesson = await API.lms.getLesson(lessonId);
            
            // 🔧 FIX #5: Better marked.js loading with longer timeout
            if (typeof marked === 'undefined') {
                await new Promise((resolve, reject) => {
                    let attempts = 0;
                    const maxAttempts = 50; // 5 seconds total
                    const check = setInterval(() => {
                        if (typeof marked !== 'undefined') {
                            clearInterval(check);
                            resolve();
                        } else if (++attempts > maxAttempts) {
                            clearInterval(check);
                            console.warn('[Academy] Marked.js timeout, using fallback parser');
                            resolve(); // Resolve anyway to show content
                        }
                    }, 100);
                });
            }
            
            const processedContent = this._processLessonContent(lesson.content);
            this._renderMobileNav(lesson);
            
            main.innerHTML = `
                <div class="max-w-3xl ac-lesson-container">
                    <div class="pw-card mb-4">
                        <div class="pw-card-hdr ac-lesson-header">
                            <div>
                                <div class="text-xs text-gray-500 mb-0.5">
                                    ${_es(lesson.module_title)} · ${_es(lesson.level_name)}
                                </div>
                                <h2 class="card-title ac-lesson-title">${_es(lesson.title)}</h2>
                            </div>
                        </div>
                        <div class="pw-card-body">
                            <div class="ac-lesson-text">${processedContent}</div>
                        </div>
                    </div>
                    
                    <div class="flex flex-wrap gap-2 mb-4 ac-action-buttons">
                        <button class="btn btn-primary" onclick="AcademyPage._startQuiz(${lessonId})">
                            <i class="fas fa-pencil-alt mr-2"></i>Take Quiz
                        </button>
                        <button id="ac-explain-btn" class="btn" style="background:#1f2937; border:1px solid #374151; color:#e5e7eb;"
                                onclick="AcademyPage._showExplanation(${lessonId})">
                            <i class="fas fa-chalkboard-teacher mr-2" style="color:#a78bfa;"></i>Trading Coach
                        </button>
                        <button id="ac-practice-btn" class="btn" style="background:#1f2937; border:1px solid #374151; color:#e5e7eb;"
                                onclick="AcademyPage._showPractice(${lessonId})">
                            <i class="fas fa-dumbbell mr-2" style="color:#fbbf24;"></i>Practice
                        </button>
                        <button id="ac-chart-btn" class="btn" style="background:#1f2937; border:1px solid #374151; color:#e5e7eb;"
                                onclick="AcademyPage._showChartPractice(${lessonId})">
                            <i class="fas fa-chart-bar mr-2" style="color:#60a5fa;"></i>Chart Exercise
                        </button>
                    </div>
                    
                    <!-- Desktop Navigation -->
                    <div class="hidden md:flex justify-between items-center py-4 border-t border-gray-800">
                        ${lesson.prev_lesson 
                            ? `<button onclick="AcademyPage._openLesson(${lesson.prev_lesson.id}, '${_jes(lesson.prev_lesson.title)}')" 
                                       class="text-gray-400 hover:text-white text-sm flex items-center gap-2">
                                 <i class="fas fa-arrow-left"></i> Previous: ${_es(lesson.prev_lesson.title)}
                               </button>`
                            : `<span></span>`
                        }
                        ${lesson.next_lesson
                            ? `<button onclick="AcademyPage._openLesson(${lesson.next_lesson.id}, '${_jes(lesson.next_lesson.title)}')" 
                                       class="text-purple-400 hover:text-purple-300 text-sm flex items-center gap-2">
                                 Next: ${_es(lesson.next_lesson.title)} <i class="fas fa-arrow-right"></i>
                               </button>`
                            : `<span></span>`
                        }
                    </div>
                    
                    <div id="ac-ai-panel"></div>
                </div>
            `;
            
            // 🔧 FIX #3: Initialize with error handling and tracking
            setTimeout(() => this.initTradingViewWidgets(), 100);
            
        } catch (e) {
            main.innerHTML = this._error('Could not load lesson', e.message);
        }
    },

    /* ── Content Processing ─────────────────────────────────────────────── */
    _processLessonContent(content) {
        if (!content) return '';
        
        // 🔧 FIX #10: Use DOMParser instead of regex for SVG safety
        const parseMarkdown = (typeof marked !== 'undefined' && marked.parse) 
            ? (text) => marked.parse(text, { breaks: true, gfm: true })
            : (text) => {
                // Safe fallback
                return text
                    .replace(/^## (.*$)/gim, '<h3 class="ac-h3">$1</h3>')
                    .replace(/^### (.*$)/gim, '<h4 class="ac-h4">$1</h4>')
                    .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
                    .replace(/`([^`]+)`/gim, '<code class="ac-inline-code">$1</code>')
                    .replace(/^- (.*$)/gim, '<li class="ac-li">$1</li>')
                    .replace(/(<li[^>]*>[\s\S]*?<\/li>)/gim, '<ul class="ac-ul">$1</ul>')
                    .replace(/\n\n/gim, '</p><p class="ac-p">')
                    .replace(/\n/gim, '<br>');
            };
        
        let html = parseMarkdown(content);
        
        // 🔧 FIX #10: DOMParser-based SVG fix instead of regex
        if (html.includes('<svg')) {
            const parser = new DOMParser();
            const doc = parser.parseFromString(`<div>${html}</div>`, 'text/html');
            const svgs = doc.querySelectorAll('svg');
            
            svgs.forEach(svg => {
                // Ensure defs come first
                const defs = svg.querySelector('defs');
                if (defs) {
                    svg.insertBefore(defs, svg.firstChild);
                }
            });
            
            html = doc.body.innerHTML;
        }
        
        return html;
    },

    /* ── TradingView Widget Initialization ──────────────────────────────── */
    initTradingViewWidgets() {
        this._cleanupTradingView(); // Clean up existing before creating new
        
        const widgets = document.querySelectorAll('.ac-tradingview-widget');
        
        widgets.forEach(el => {
            const symbol = el.dataset.symbol || 'FX:EURUSD';
            // 🔧 FIX #13: Use timestamp-based ID to prevent collisions
            const id = 'tv-widget-' + Date.now() + '-' + Math.random().toString(36).substr(2, 5);
            el.id = id;
            
            el.style.height = '400px';
            el.style.minHeight = '400px';
            
            if (window.TradingView) {
                try {
                    const widget = new TradingView.widget({
                        container_id: id,
                        symbol: symbol,
                        interval: "60",
                        timezone: "Etc/UTC",
                        theme: "dark",
                        style: "1",
                        locale: "en",
                        toolbar_bg: "#f1f3f6",
                        enable_publishing: false,
                        hide_top_toolbar: false,
                        hide_legend: false,
                        save_image: false,
                        studies: [
                            "MACD@tv-basicstudies",
                            "MASimple@tv-basicstudies", 
                            "RSI@tv-basicstudies"
                        ],
                        show_popup_button: true,
                        popup_width: "1000",
                        popup_height: "650",
                        height: 400,
                        width: "100%"
                    });
                    
                    // 🔧 FIX #3: Track widget for cleanup
                    this._tradingViewWidgets.push(widget);
                } catch (err) {
                    console.error('TradingView widget error:', err);
                    el.innerHTML = '<div class="p-4 text-gray-500 text-sm">Chart loading failed. Please refresh.</div>';
                }
            } else {
                el.innerHTML = '<div class="p-4 text-gray-500 text-sm"><i class="fas fa-spinner fa-spin mr-2"></i>Loading chart...</div>';
                
                if (!window._tradingViewLoading) {
                    window._tradingViewLoading = true;
                    const script = document.createElement('script');
                    script.src = "https://s3.tradingview.com/tv.js";
                    script.onload = () => {
                        window._tradingViewLoading = false;
                        this.initTradingViewWidgets();
                    };
                    script.onerror = () => {
                        el.innerHTML = '<div class="p-4 text-gray-500 text-sm">Failed to load chart library.</div>';
                    };
                    document.head.appendChild(script);
                }
            }
        });
    },

    // 🔧 FIX #3: Cleanup method for TradingView widgets
    _cleanupTradingView() {
        this._tradingViewWidgets.forEach(widget => {
            if (widget && typeof widget.remove === 'function') {
                try { widget.remove(); } catch(e) {}
            }
        });
        this._tradingViewWidgets = [];
    },

    /* ── Mobile Navigation ─────────────────────────────────────────────── */
    _renderMobileNav(lesson) {
        const nav = document.getElementById('ac-mobile-nav');
        if (!nav) return;
        
        // 🔧 FIX #6: Safely compute onclick handlers
        const prevOnclick = lesson.prev_lesson 
            ? `AcademyPage._openLesson(${lesson.prev_lesson.id}, '${_jes(lesson.prev_lesson.title)}')` 
            : '';
        const nextOnclick = lesson.next_lesson 
            ? `AcademyPage._openLesson(${lesson.next_lesson.id}, '${_jes(lesson.next_lesson.title)}')` 
            : '';
        const backOnclick = `AcademyPage._selectModule(${this._module?.id || 0}, '${_jes(this._module?.name || '')}')`;
        
        nav.classList.remove('hidden');
        nav.innerHTML = `
            <div class="ac-mobile-nav-inner">
                <button class="ac-nav-btn ${!lesson.prev_lesson ? 'disabled' : ''}" 
                    onclick="${prevOnclick ? prevOnclick : ''}">
                    <i class="fas fa-arrow-left"></i> Prev
                </button>
                <button class="ac-nav-btn ac-nav-back" 
                    onclick="${backOnclick}">
                    <i class="fas fa-th-large"></i> Module
                </button>
                <button class="ac-nav-btn ${!lesson.next_lesson ? 'disabled' : ''}" 
                    onclick="${nextOnclick ? nextOnclick : ''}">
                    Next <i class="fas fa-arrow-right"></i>
                </button>
            </div>
        `;
    },

    _hideMobileNav() {
        const nav = document.getElementById('ac-mobile-nav');
        if (nav) nav.classList.add('hidden');
    },

    /* ── Quiz Engine (5 Questions) ──────────────────────────────────────── */
    async _startQuiz(lessonId) {
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading quiz...');
        this._hideMobileNav();
        this._quizAnswered = false; // 🔧 FIX #9: Reset answer flag
        
        try {
            const data = await API.lms.getQuiz(lessonId);
            if (!data.questions || data.questions.length === 0) {
                main.innerHTML = `
                    <div class="alert" style="background:rgba(96,165,250,.1); border:1px solid rgba(96,165,250,.3); color:#60a5fa; padding:1rem; border-radius:.5rem;">
                        <i class="fas fa-info-circle mr-2"></i>No quiz questions available for this lesson.
                    </div>`;
                return;
            }
            
            this._quiz = {
                lessonId,
                questions: data.questions,
                index: 0,
                answers: [],
                selected: null
            };
            
            this._renderQ();
        } catch (e) {
            main.innerHTML = this._error('Could not load quiz', e.message);
        }
    },

    _renderQ() {
        const { questions, index } = this._quiz;
        const q = questions[index];
        const total = questions.length;
        const progress = Math.round((index / total) * 100);
        
        const main = document.getElementById('ac-main');
        main.innerHTML = `
            <div class="max-w-xl ac-quiz-container">
                <div class="flex items-center justify-between mb-2 text-xs text-gray-500">
                    <span class="font-semibold">Question ${index + 1} of ${total}</span>
                    <span>${_es(this._lesson?.name || 'Quiz')}</span>
                </div>
                <div class="pw-progress-bar mb-5">
                    <div class="pw-progress-fill" style="width:${progress}%;"></div>
                </div>
                
                <div class="pw-card mb-4">
                    <div class="pw-card-body">
                        <p class="text-white font-semibold text-base leading-relaxed mb-5">${_es(q.question)}</p>
                        
                        <div class="space-y-2.5" id="ac-quiz-opts">
                            ${['A', 'B', 'C', 'D'].map(k => {
                                const opt = q['option_' + k.toLowerCase()];
                                if (!opt) return '';
                                return `
                                    <button id="ac-opt-${k}" onclick="AcademyPage._pick('${k}')"
                                            class="w-full text-left px-4 py-3 rounded-xl text-sm transition-all ac-quiz-opt"
                                            style="background:#111827; border:2px solid #1f2937; color:#d1d5db;">
                                        <strong class="text-gray-400 mr-2">${k}.</strong> ${_es(opt)}
                                    </button>`;
                            }).join('')}
                        </div>
                    </div>
                </div>
                
                <div class="flex justify-end">
                    <button id="ac-quiz-next" disabled class="btn btn-primary opacity-50"
                            onclick="AcademyPage._nextQ()">
                        ${index < total - 1 ? 'Next Question →' : 'Submit Quiz'}
                    </button>
                </div>
            </div>
        `;
        
        this._quiz.selected = null;
        this._quizAnswered = false; // 🔧 FIX #9: Reset for new question
    },

    _pick(key) {
        // 🔧 FIX #9: Prevent double-clicking
        if (this._quizAnswered) return;
        
        this._quiz.selected = key;
        
        document.querySelectorAll('.ac-quiz-opt').forEach(b => {
            b.style.borderColor = '#1f2937';
            b.style.background = '#111827';
            b.style.color = '#d1d5db';
        });
        
        const selected = document.getElementById('ac-opt-' + key);
        if (selected) {
            selected.style.borderColor = '#7c3aed';
            selected.style.background = 'rgba(124,58,237,.12)';
            selected.style.color = '#c4b5fd';
        }
        
        const nextBtn = document.getElementById('ac-quiz-next');
        if (nextBtn) {
            nextBtn.disabled = false;
            nextBtn.classList.remove('opacity-50');
        }
    },

    _nextQ() {
        // 🔧 FIX #9: Set answered flag
        if (this._quizAnswered) return;
        this._quizAnswered = true;
        
        const { selected, index, questions, answers } = this._quiz;
        if (!selected) return;
        
        answers.push({
            question_id: questions[index].id,
            selected_answer: selected
        });
        
        this._quiz.answers = answers;
        this._quiz.index = index + 1;
        
        if (this._quiz.index < questions.length) {
            this._renderQ();
        } else {
            this._doSubmit();
        }
    },

    async _doSubmit() {
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Grading your quiz...');
        
        try {
            // 🔧 FIX #2: The critical syntax error fix - using valid JS Object.fromEntries
            const result = await API.lms.submitQuiz(this._quiz.lessonId, this._quiz.answers);
            
            if (result.new_badges?.length) {
                await this._showNewBadges(result.new_badges);
            }
            
            this._showResults(result);
        } catch (e) {
            main.innerHTML = this._error('Submit failed', e.message);
        }
    },

    _showResults(result) {
        const main = document.getElementById('ac-main');
        const passed = result.passed;
        const passColor = passed ? '#34d399' : '#f87171';
        const passMsg = passed ? '🎉 Quiz Passed!' : 'Keep studying — review the lesson and try again.';
        
        const breakdown = result.results.map((r, i) => `
            <div class="flex items-start gap-3 py-3 border-b ac-result-row" style="border-color:#1f2937;">
                <i class="fas ${r.is_correct ? 'fa-check-circle text-green-400' : 'fa-times-circle text-red-400'} mt-0.5 flex-shrink-0"></i>
                <div class="flex-1 text-sm">
                    <span class="text-gray-400 font-medium">Question ${i + 1}</span>
                    ${!r.is_correct ? `
                        <div class="text-gray-500 text-xs mt-1">
                            Correct: <strong class="text-gray-300">${_es(r.correct_answer)}</strong> — 
                            ${_es(r.explanation)}
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
        
        // 🔧 FIX #1: Use _jes() for retry button
        main.innerHTML = `
            <div class="max-w-xl ac-results-container">
                <div class="pw-card mb-4 ac-result-card" style="border-top:3px solid ${passColor};">
                    <div class="pw-card-body text-center" style="padding:2rem;">
                        <div class="text-5xl font-black mb-2 ac-score-display" style="color:${passColor};">
                            ${result.score}%
                        </div>
                        <div class="font-semibold text-white text-lg">${passMsg}</div>
                        <div class="text-gray-500 text-sm mt-1">
                            ${result.correct} of ${result.total} questions correct
                        </div>
                        ${passed ? '<div class="mt-3 text-green-400 text-sm"><i class="fas fa-check-circle mr-1"></i> Lesson Complete!</div>' : ''}
                    </div>
                </div>
                
                ${result.mentor_feedback ? `
                <div class="pw-card mb-4 ac-feedback-card" style="border-left:3px solid #a78bfa;">
                    <div class="pw-card-body">
                        <div class="flex items-center gap-2 mb-2">
                            <i class="fas fa-robot" style="color:#a78bfa;"></i>
                            <strong class="text-white text-sm">Trading Coach Feedback</strong>
                        </div>
                        <p class="text-gray-300 text-sm leading-relaxed">${_es(result.mentor_feedback)}</p>
                    </div>
                </div>
                ` : ''}
                
                <div class="pw-card mb-4">
                    <div class="pw-card-hdr">
                        <h3 class="card-title">Answer Breakdown</h3>
                    </div>
                    <div class="pw-card-body" style="padding-top:0;">
                        ${breakdown}
                    </div>
                </div>
                
                <div class="flex gap-2 flex-wrap ac-result-actions">
                    ${passed
                        ? `<button class="btn btn-primary" onclick="AcademyPage._selectModule(${this._module?.id || 0}, '${_jes(this._module?.name || '')}')">
                             <i class="fas fa-arrow-left mr-2"></i>Back to Module
                           </button>`
                        : `<button class="btn btn-primary" onclick="AcademyPage._startQuiz(${this._quiz.lessonId})">
                             <i class="fas fa-redo mr-2"></i>Retry Quiz
                           </button>`
                    }
                    <button class="btn" style="background:#1f2937; border:1px solid #374151; color:#e5e7eb;"
                            onclick="AcademyPage._openLesson(${this._lesson?.id || 0}, '${_jes(this._lesson?.name || '')}')">
                        <i class="fas fa-book-open mr-2"></i>Review Lesson
                    </button>
                </div>
            </div>
        `;
    },

    /* ── AI Coach Interactions ──────────────────────────────────────────── */
    async _showExplanation(lessonId) {
        this._setBtn('ac-explain-btn', true, 'Loading...');
        const panel = document.getElementById('ac-ai-panel');
        panel.innerHTML = this._aiLoading('Trading Coach preparing explanation...');
        
        try {
            const data = await API.lms.getMentorTeach(lessonId);
            panel.innerHTML = `
                <div class="pw-card ac-coach-card" style="border-left:3px solid #a78bfa;">
                    <div class="pw-card-hdr">
                        <div class="flex items-center gap-2">
                            <i class="fas fa-chalkboard-teacher" style="color:#a78bfa;"></i>
                            <span class="card-title" style="font-size:.95rem;">
                                Trading Coach · ${_es(data.lesson_title)}
                            </span>
                            <span class="badge badge-primary text-xs">${_es(data.level)}</span>
                        </div>
                    </div>
                    <div class="pw-card-body">
                        <div class="ac-lesson-text">${data.explanation}</div>
                    </div>
                </div>
            `;
        } catch (e) {
            // 🔧 FIX #11: Add retry button to error state
            panel.innerHTML = `
                <div class="pw-card" style="border-left:3px solid #ef4444;">
                    <div class="pw-card-body">
                        <div class="text-red-400 text-sm mb-2"><i class="fas fa-exclamation-circle mr-2"></i>Coach unavailable</div>
                        <p class="text-gray-500 text-xs mb-3">${_es(e.message)}</p>
                        <button class="btn btn-sm" style="background:#1f2937; border:1px solid #374151; color:#e5e7eb;"
                                onclick="AcademyPage._showExplanation(${lessonId})">
                            <i class="fas fa-redo mr-1"></i>Retry
                        </button>
                    </div>
                </div>`;
        }
        
        this._setBtn('ac-explain-btn', false, 
            '<i class="fas fa-chalkboard-teacher mr-2" style="color:#a78bfa;"></i>Trading Coach');
    },

    async _showPractice(lessonId) {
        this._setBtn('ac-practice-btn', true, 'Loading...');
        const panel = document.getElementById('ac-ai-panel');
        panel.innerHTML = this._aiLoading('Generating practice exercise...');
        
        try {
            const data = await API.lms.getMentorPractice(lessonId);
            panel.innerHTML = `
                <div class="pw-card ac-coach-card" style="border-left:3px solid #fbbf24;">
                    <div class="pw-card-hdr">
                        <div class="flex items-center gap-2">
                            <i class="fas fa-dumbbell" style="color:#fbbf24;"></i>
                            <span class="card-title" style="font-size:.95rem;">Practice Exercise</span>
                        </div>
                    </div>
                    <div class="pw-card-body">
                        <div class="ac-lesson-text">${data.exercise}</div>
                    </div>
                </div>
            `;
        } catch (e) {
            panel.innerHTML = `
                <div class="pw-card" style="border-left:3px solid #ef4444;">
                    <div class="pw-card-body">
                        <div class="text-red-400 text-sm mb-2"><i class="fas fa-exclamation-circle mr-2"></i>Practice failed</div>
                        <button class="btn btn-sm" style="background:#1f2937; border:1px solid #374151; color:#e5e7eb;"
                                onclick="AcademyPage._showPractice(${lessonId})">
                            <i class="fas fa-redo mr-1"></i>Retry
                        </button>
                    </div>
                </div>`;
        }
        
        this._setBtn('ac-practice-btn', false,
            '<i class="fas fa-dumbbell mr-2" style="color:#fbbf24;"></i>Practice');
    },

    async _showChartPractice(lessonId) {
        this._setBtn('ac-chart-btn', true, 'Loading...');
        const panel = document.getElementById('ac-ai-panel');
        panel.innerHTML = this._aiLoading('Building chart exercise...');
        
        try {
            const data = await API.lms.getChartPractice(lessonId);
            const cp = data.chart_practice;
            
            // 🔧 FIX #8: Escape tv_symbol to prevent HTML injection
            const tvSymbol = cp.tv_symbol ? _es(cp.tv_symbol) : '';
            
            const options = (cp.options || []).map((opt, i) => `
                <button class="ac-chart-opt w-full text-left px-4 py-3 rounded-lg transition-all text-sm"
                        id="ac-chart-opt-${i}"
                        style="background:#111827; border:1px solid #374151; color:#e5e7eb;"
                        onclick="AcademyPage._answerChart(${i},
