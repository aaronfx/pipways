/**
 * Pipways Trading Academy Frontend Module v4.1 (Production)
 * Fixes: HTML rendering, TradingView widgets, SVG diagrams, 5-question quizzes, safe DOM injection.
 */

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

/* ── Marked.js Loader ───────────────────────────────────────────────────── */
(function loadMarked() {
    if (window.marked) return;
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
    script.async = true;
    document.head.appendChild(script);
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

    async render() {
        const u = this._getUser();
        this._uid = u?.id ?? null;
        const wrap = document.getElementById('academy-container');
        if (!wrap) return;
        
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
        this._bc(null, null, null);
        this._hideMobileNav();
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
            
            // Safe progress parsing
            const sm = {};
            if (prog && Array.isArray(prog.summary)) {
                prog.summary.forEach(s => sm[s.level_id] = s);
            }
            
            if (this._uid) this._loadMentorBanner(guide);
            
            const cfg = [
                { icon: 'fa-seedling', color: '#34d399', bg: 'rgba(52,211,153,.15)' },
                { icon: 'fa-chart-line', color: '#60a5fa', bg: 'rgba(96,165,250,.15)' },
                { icon: 'fa-chess-knight', color: '#f59e0b', bg: 'rgba(245,158,11,.15)' },
            ];
            
            if (!levels || !levels.length) {
                main.innerHTML = this._emptyState('Academy not set up yet', 
                    'The learning curriculum is being initialized. Please refresh in a moment.');
                return;
            }
            
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
                         onclick="AcademyPage._selectLevel(${lv.id}, '${_es(lv.name)}')"
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
    async _selectModule(moduleId, moduleTitle) {
        this._module = { id: moduleId, name: moduleTitle };
        this._lesson = null;
        this._bc(this._level?.name, moduleTitle, null);
        this._hideMobileNav();
        
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading lessons...');
        
        try {
            const lessons = await API.lms.getLessons(moduleId);
            
            main.innerHTML = `<div class="space-y-2 max-w-2xl ac-lesson-list">
                ${lessons.map((l, i) => {
                    const locked = !l.unlocked;
                    const done = l.completed;
                    const icon = done ? 'fa-check-circle text-green-400' : 
                                locked ? 'fa-lock text-gray-700' : 'fa-play-circle text-purple-400';
                    const score = done && l.quiz_score !== null
                        ? `<span class="text-xs font-semibold" style="color:#34d399;">${l.quiz_score}%</span>` 
                        : '';
                    
                    return `
                    <div class="pw-card ${locked ? 'opacity-50' : ''} ${!locked ? 'cursor-pointer' : ''} ac-lesson-item ${done ? 'ac-lesson-done' : ''}"
                         ${!locked ? `onclick="AcademyPage._openLesson(${l.id}, '${_es(l.title)}')"` : ''}>
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

    /* ── Lesson View ────────────────────────────────────────────────────── */
    async _openLesson(lessonId, lessonTitle) {
        this._lesson = { id: lessonId, name: lessonTitle };
        this._bc(this._level?.name, this._module?.name, lessonTitle);
        
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading lesson...');
        
        try {
            const lesson = await API.lms.getLesson(lessonId);
            
            if (typeof marked === 'undefined') {
                await new Promise(resolve => {
                    const check = setInterval(() => {
                        if (typeof marked !== 'undefined') {
                            clearInterval(check);
                            resolve();
                        }
                    }, 100);
                    setTimeout(() => { clearInterval(check); resolve(); }, 2000);
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
                    
                    <div class="hidden md:flex justify-between items-center py-4 border-t border-gray-800">
                        ${lesson.prev_lesson 
                            ? `<button onclick="AcademyPage._openLesson(${lesson.prev_lesson.id}, '${_es(lesson.prev_lesson.title)}')" 
                                       class="text-gray-400 hover:text-white text-sm flex items-center gap-2">
                                 <i class="fas fa-arrow-left"></i> Previous: ${_es(lesson.prev_lesson.title)}
                               </button>`
                            : `<span></span>`
                        }
                        ${lesson.next_lesson
                            ? `<button onclick="AcademyPage._openLesson(${lesson.next_lesson.id}, '${_es(lesson.next_lesson.title)}')" 
                                       class="text-purple-400 hover:text-purple-300 text-sm flex items-center gap-2">
                                 Next: ${_es(lesson.next_lesson.title)} <i class="fas fa-arrow-right"></i>
                               </button>`
                            : `<span></span>`
                        }
                    </div>
                    
                    <div id="ac-ai-panel"></div>
                </div>
            `;
            
            setTimeout(() => this.initTradingViewWidgets(), 100);
            
        } catch (e) {
            main.innerHTML = this._error('Could not load lesson', e.message);
        }
    },

    /* ── Content Processing ─────────────────────────────────────────────── */
    _processLessonContent(content) {
        if (!content) return '';
        
        const parseMarkdown = (typeof marked !== 'undefined' && marked.parse) 
            ? (text) => marked.parse(text, { breaks: true, gfm: true })
            : (text) => {
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
        
        // Render SVGs safely
        html = html.replace(/<svg([^>]*)>([\s\S]*?)<\/svg>/g, (match, attrs, inner) => {
            const defsMatch = inner.match(/<defs>[\s\S]*?<\/defs>/);
            const defs = defsMatch ? defsMatch[0] : '';
            const withoutDefs = inner.replace(/<defs>[\s\S]*?<\/defs>/, '');
            return `<svg${attrs}>${defs}${withoutDefs}</svg>`;
        });
        
        return html;
    },

    /* ── TradingView Widget Initialization ──────────────────────────────── */
    initTradingViewWidgets() {
        const widgets = document.querySelectorAll('.ac-tradingview-widget');
        
        widgets.forEach(el => {
            const symbol = el.dataset.symbol || 'FX:EURUSD';
            const id = el.id || 'tv-widget-' + Math.random().toString(36).substr(2, 9);
            el.id = id;
            
            el.style.height = '400px';
            el.style.minHeight = '400px';
            
            if (window.TradingView) {
                try {
                    new TradingView.widget({
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

    /* ── Mobile Navigation ─────────────────────────────────────────────── */
    _renderMobileNav(lesson) {
        const nav = document.getElementById('ac-mobile-nav');
        if (!nav) return;
        
        nav.classList.remove('hidden');
        nav.innerHTML = `
            <div class="ac-mobile-nav-inner">
                <button class="ac-nav-btn ${!lesson.prev_lesson ? 'disabled' : ''}" 
                    onclick="${lesson.prev_lesson ? `AcademyPage._openLesson(${lesson.prev_lesson.id}, '${_es(lesson.prev_lesson.title)}')` : ''}">
                    <i class="fas fa-arrow-left"></i> Prev
                </button>
                <button class="ac-nav-btn ac-nav-back" 
                    onclick="AcademyPage._selectModule(${this._module?.id}, '${_es(this._module?.name || '')}')">
                    <i class="fas fa-th-large"></i> Module
                </button>
                <button class="ac-nav-btn ${!lesson.next_lesson ? 'disabled' : ''}" 
                    onclick="${lesson.next_lesson ? `AcademyPage._openLesson(${lesson.next_lesson.id}, '${_es(lesson.next_lesson.title)}')` : ''}">
                    Next <i class="fas fa-arrow-right"></i>
                </button>
            </div>
        `;
    },

    _hideMobileNav() {
        const nav = document.getElementById('ac-mobile-nav');
        if (nav) nav.classList.add('hidden');
    },

    /* ── Quiz Engine ──────────────────────────────────────── */
    async _startQuiz(lessonId) {
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading quiz...');
        this._hideMobileNav();
        
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
    },

    _pick(key) {
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
                            <i class="fas fa-chalkboard-teacher" style="color:#a78bfa;"></i>
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
                        ? `<button class="btn btn-primary" onclick="AcademyPage._selectModule(${this._module?.id}, '${_es(this._module?.name || '')}')">
                             <i class="fas fa-arrow-left mr-2"></i>Back to Module
                           </button>`
                        : `<button class="btn btn-primary" onclick="AcademyPage._startQuiz(${this._quiz.lessonId})">
                             <i class="fas fa-redo mr-2"></i>Retry Quiz
                           </button>`
                    }
                    <button class="btn" style="background:#1f2937; border:1px solid #374151; color:#e5e7eb;"
                            onclick="AcademyPage._openLesson(${this._lesson?.id}, '${_es(this._lesson?.name || '')}')">
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
            panel.innerHTML = this._error('Coach unavailable', e.message);
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
            panel.innerHTML = this._error('Practice failed', e.message);
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
            
            const options = (cp.options || []).map((opt, i) => `
                <button class="ac-chart-opt w-full text-left px-4 py-3 rounded-lg transition-all text-sm"
                        id="ac-chart-opt-${i}"
                        style="background:#111827; border:1px solid #374151; color:#e5e7eb;"
                        onclick="AcademyPage._answerChart(${i}, '${_es(cp.correct || '')}', '${_es(cp.explanation || '')}')">
                    ${_es(opt)}
                </button>
            `).join('');
            
            const tvWidget = cp.tv_symbol 
                ? `<div class="ac-tradingview-widget" data-symbol="${cp.tv_symbol}" id="tv-exercise"></div>` 
                : '';
            
            panel.innerHTML = `
                <div class="pw-card ac-coach-card" style="border-left:3px solid #60a5fa;">
                    <div class="pw-card-hdr">
                        <div class="flex items-center gap-2">
                            <i class="fas fa-chart-bar" style="color:#60a5fa;"></i>
                            <span class="card-title" style="font-size:.95rem;">
                                Chart Exercise · ${_es(data.level)}
                            </span>
                        </div>
                    </div>
                    <div class="pw-card-body">
                        ${tvWidget}
                        <div class="rounded-xl p-4 mb-4 text-sm text-gray-300 leading-relaxed"
                             style="background:rgba(96,165,250,.06); border:1px solid rgba(96,165,250,.15);">
                            <div class="text-xs font-bold mb-2" style="color:#60a5fa;">CHART SCENARIO</div>
                            ${_es(cp.scenario || '')}
                        </div>
                        <p class="text-white font-semibold mb-3 text-sm">${_es(cp.question || '')}</p>
                        <div class="space-y-2" id="ac-chart-opts">${options}</div>
                        <div id="ac-chart-result" class="mt-4 hidden"></div>
                    </div>
                </div>
            `;
            
            if (cp.tv_symbol) {
                setTimeout(() => this.initTradingViewWidgets(), 100);
            }
        } catch (e) {
            panel.innerHTML = this._error('Chart exercise failed', e.message);
        }
        
        this._setBtn('ac-chart-btn', false,
            '<i class="fas fa-chart-bar mr-2" style="color:#60a5fa;"></i>Chart Exercise');
    },

    _answerChart(idx, correct, explanation) {
        document.querySelectorAll('.ac-chart-opt').forEach((btn, i) => {
            btn.disabled = true;
            btn.style.cursor = 'default';
            const letter = (btn.textContent.trim().charAt(0) || '').toUpperCase();
            
            if (letter === correct.toUpperCase()) {
                btn.style.background = 'rgba(16,185,129,.15)';
                btn.style.borderColor = '#34d399';
                btn.style.color = '#34d399';
            } else if (i === idx) {
                btn.style.background = 'rgba(239,68,68,.1)';
                btn.style.borderColor = '#f87171';
                btn.style.color = '#f87171';
            }
        });
        
        const chosen = (document.getElementById('ac-chart-opt-' + idx)?.textContent?.trim()?.charAt(0) || '').toUpperCase();
        const passed = chosen === correct.toUpperCase();
        
        const result = document.getElementById('ac-chart-result');
        result.classList.remove('hidden');
        result.innerHTML = `
            <div class="rounded-xl p-4 ${passed ? 'bg-green-900/20 border border-green-800/40' : 'bg-red-900/20 border border-red-800/40'}">
                <div class="flex items-center gap-2 mb-2">
                    <i class="fas ${passed ? 'fa-check-circle text-green-400' : 'fa-times-circle text-red-400'}"></i>
                    <strong class="${passed ? 'text-green-400' : 'text-red-400'}">
                        ${passed ? 'Correct!' : 'Incorrect'}
                    </strong>
                </div>
                <p class="text-gray-300 text-sm">${_es(explanation)}</p>
            </div>
        `;
    },

    /* ── Badge System ───────────────────────────────────────────────────── */
    async _loadBadges() {
        if (!this._uid) return;
        try {
            const data = await API.lms.getBadges(this._uid);
            this._badges = data.badges || [];
        } catch (e) {
            console.error('Failed to load badges:', e);
        }
    },

    async _showNewBadges(badgeTypes) {
        const container = document.getElementById('ac-badge-toast');
        if (!container) return;
        
        const badgeDefs = {
            "beginner_trader": { name: "Beginner Trader", icon: "fa-seedling", color: "#34d399" },
            "technical_analyst": { name: "Technical Analyst", icon: "fa-chart-line", color: "#60a5fa" },
            "strategy_builder": { name: "Strategy Builder", icon: "fa-chess-knight", color: "#a78bfa" },
            "pipways_certified": { name: "Pipways Certified", icon: "fa-certificate", color: "#f59e0b" },
            "quiz_master": { name: "Quiz Master", icon: "fa-cogs", color: "#f472b6" },
            "perfect_score": { name: "Perfect Score", icon: "fa-medal", color: "#fbbf24" },
            "risk_manager": { name: "Risk Manager", icon: "fa-shield-alt", color: "#22d3ee" },
            "psychology_pro": { name: "Psychology Pro", icon: "fa-cogs", color: "#e879f9" },
        };
        
        badgeTypes.forEach((type, i) => {
            const def = badgeDefs[type] || { name: type, icon: "fa-medal", color: "#a78bfa" };
            const badge = document.createElement('div');
            badge.className = 'ac-badge-toast';
            badge.style.animationDelay = `${i * 0.2}s`;
            badge.innerHTML = `
                <div class="ac-badge-icon" style="background:${def.color}20; color:${def.color};">
                    <i class="fas ${def.icon}"></i>
                </div>
                <div class="ac-badge-info">
                    <div class="ac-badge-title">Badge Earned!</div>
                    <div class="ac-badge-name" style="color:${def.color};">${def.name}</div>
                </div>
            `;
            container.appendChild(badge);
            setTimeout(() => badge.remove(), 5000);
        });
    },

    /* ── Mentor Banner ──────────────────────────────────────────────────── */
    async _loadMentorBanner(guideData) {
        if (!this._uid) return;
        const banner = document.getElementById('ac-mentor-banner');
        if (!banner) return;
        
        try {
            const g = guideData || await API.lms.getMentorGuide(this._uid);
            
            if (g.first_visit) {
                banner.innerHTML = `
                    <div class="pw-card mb-5 ac-welcome-banner" 
                         style="border-left:3px solid #34d399; background:linear-gradient(135deg,#0f0a1f,#1a0a2e);">
                        <div class="pw-card-body">
                            <div class="flex items-start gap-3">
                                <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" 
                                     style="background:rgba(52,211,153,.2);">
                                    <i class="fas fa-graduation-cap" style="color:#34d399;"></i>
                                </div>
                                <div class="flex-1">
                                    <div class="text-xs font-semibold mb-1" style="color:#34d399;">WELCOME</div>
                                    <p class="text-gray-300 text-sm leading-relaxed">${g.message}</p>
                                    ${g.next_lesson ? `
                                        <button class="btn btn-primary mt-3 text-xs" 
                                                style="font-size:.78rem; padding:.35rem .85rem;"
                                                onclick="AcademyPage._markFirstVisitThenContinue(${g.next_lesson.id}, '${_es(g.next_lesson.title)}')">
                                            Start Learning: ${_es(g.next_lesson.title)} →
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                banner.innerHTML = `
                    <div class="pw-card mb-5 ac-coach-banner" 
                         style="border-left:3px solid #a78bfa; background:linear-gradient(135deg,#0f0a1f,#1a0a2e);">
                        <div class="pw-card-body">
                            <div class="flex items-start gap-3">
                                <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" 
                                     style="background:rgba(167,139,250,.2);">
                                    <i class="fas fa-chalkboard-teacher" style="color:#a78bfa;"></i>
                                </div>
                                <div class="flex-1">
                                    <div class="text-xs font-semibold mb-1" style="color:#a78bfa;">TRADING COACH</div>
                                    <p class="text-gray-300 text-sm leading-relaxed">${_es(g.message)}</p>
                                    ${g.next_lesson ? `
                                        <button class="btn btn-primary mt-3 text-xs" 
                                                style="font-size:.78rem; padding:.35rem .85rem;"
                                                onclick="AcademyPage._openLesson(${g.next_lesson.id}, '${_es(g.next_lesson.title)}')">
                                            Continue: ${_es(g.next_lesson.title)} →
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
        } catch (e) {
            banner.innerHTML = '';
        }
    },

    async _markFirstVisitThenContinue(lessonId, lessonTitle) {
        try {
            await API.lms.markFirstVisit();
            this._firstVisit = false;
            this._openLesson(lessonId, lessonTitle);
        } catch (e) {
            this._openLesson(lessonId, lessonTitle);
        }
    },

    /* ── Breadcrumb ─────────────────────────────────────────────────────── */
    _bc(level, module, lesson) {
        const el = document.getElementById('ac-breadcrumb');
        if (!el) return;
        
        if (!level) {
            el.style.display = 'none';
            el.innerHTML = '';
            return;
        }
        
        el.style.display = 'flex';
        const l = level ? _es(level) : '';
        const m = module ? _es(module) : '';
        const le = lesson ? _es(lesson) : '';
        
        el.innerHTML = `
            <a href="#" onclick="AcademyPage._showLevelSelector(); return false;" class="text-purple-400">Academy</a>
            ${level ? `<span class="pw-breadcrumb-sep">›</span>
                       <a href="#" onclick="AcademyPage._selectLevel(${this._level?.id || 0}, '${l}'); return false;" 
                          class="text-purple-400">${l}</a>` : ''}
            ${module ? `<span class="pw-breadcrumb-sep">›</span>
                        <a href="#" onclick="AcademyPage._selectModule(${this._module?.id || 0}, '${m}'); return false;" 
                           class="text-purple-400">${m}</a>` : ''}
            ${lesson ? `<span class="pw-breadcrumb-sep">›</span><span class="text-gray-400">${le}</span>` : ''}
        `;
    },

    /* ── Helpers ────────────────────────────────────────────────────────── */
    _getUser() {
        try {
            return JSON.parse(localStorage.getItem('pipways_user') || '{}');
        } catch (_) {
            return {};
        }
    },

    _loading: m => `<div class="loading"><div class="spinner"></div><p class="text-gray-500 text-sm">${m}</p></div>`,
    
    _aiLoading: m => `<div class="pw-card" style="border-left:3px solid #374151;">
                        <div class="pw-card-body loading">
                            <div class="spinner"></div>
                            <p class="text-gray-500 text-sm">${m}</p>
                        </div>
                      </div>`,
    
    _error: (t, d) => `<div class="alert alert-error">
                          <i class="fas fa-exclamation-circle mr-2"></i>
                          <strong>${_es(t)}</strong> — ${_es(d || '')}
                       </div>`,
    
    _emptyState: (t, s) => `<div class="pw-empty" style="padding:4rem 1rem;">
                              <div class="pw-empty-icon" style="width:56px; height:56px;">
                                  <i class="fas fa-book-open" style="color:#4b5563; font-size:1.2rem;"></i>
                              </div>
                              <p class="pw-empty-title">${_es(t)}</p>
                              <p class="pw-empty-sub">${_es(s)}</p>
                              <button onclick="AcademyPage._showLevelSelector()" 
                                      class="btn btn-primary mt-4" 
                                      style="font-size:.8rem; padding:.45rem 1rem;">
                                  <i class="fas fa-refresh mr-1"></i> Retry
                              </button>
                            </div>`,

    _setBtn(id, loading, html) {
        const b = document.getElementById(id);
        if (!b) return;
        b.disabled = loading;
        b.innerHTML = loading ? '<i class="fas fa-spinner fa-spin mr-2"></i>Loading...' : html;
    }
};

window.AcademyPage = AcademyPage;

/* ── Global Styles ───────────────────────────────────────────────────────── */
(function injectStyles() {
    if (document.getElementById('ac-styles')) return;
    
    const s = document.createElement('style');
    s.id = 'ac-styles';
    s.textContent = `
        /* Base Typography */
        .ac-lesson-text {
            color: #d1d5db;
            font-size: 0.95rem;
            line-height: 1.8;
        }
        .ac-lesson-text h3.ac-h3 {
            font-size: 1.25rem;
            font-weight: 600;
            color: white;
            margin: 1.5rem 0 0.75rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #1f2937;
        }
        .ac-lesson-text h4.ac-h4 {
            font-size: 1.1rem;
            font-weight: 600;
            color: #e5e7eb;
            margin: 1.25rem 0 0.5rem;
        }
        .ac-lesson-text p.ac-p {
            margin: 0.75rem 0;
        }
        .ac-lesson-text ul.ac-ul {
            margin: 0.5rem 0 0.5rem 1.5rem;
            list-style-type: disc;
        }
        .ac-lesson-text li.ac-li {
            margin: 0.35rem 0;
        }
        .ac-lesson-text strong {
            color: #fbbf24;
            font-weight: 600;
        }
        .ac-lesson-text code.ac-inline-code {
            background: #111827;
            border: 1px solid #374151;
            border-radius: 0.375rem;
            padding: 0.125rem 0.375rem;
            font-family: monospace;
            font-size: 0.875em;
            color: #f472b6;
        }
        .ac-lesson-text pre {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 0.5rem;
            padding: 1rem;
            overflow-x: auto;
            margin: 1rem 0;
        }

        /* TradingView Widgets */
        .ac-tradingview-widget {
            background: #0d1321;
            border: 1px solid #1f2937;
            border-radius: 0.75rem;
            margin: 1.5rem 0;
            overflow: hidden;
            min-height: 400px;
            width: 100%;
        }

        /* SVG Diagrams */
        .ac-svg-diagram {
            width: 100%;
            max-width: 500px;
            margin: 20px auto;
            display: block;
            background: #0d1321;
            border: 1px solid #1f2937;
            border-radius: 0.5rem;
            padding: 1rem;
        }
        .ac-svg-diagram text {
            font-family: system-ui, -apple-system, sans-serif;
        }

        /* Mobile Navigation */
        .ac-mobile-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: #111827;
            border-top: 1px solid #1f2937;
            z-index: 100;
            padding: 0.5rem;
            backdrop-filter: blur(10px);
        }
        .ac-mobile-nav-inner {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.5rem;
            max-width: 600px;
            margin: 0 auto;
        }
        .ac-nav-btn {
            flex: 1;
            background: #1f2937;
            border: 1px solid #374151;
            color: #e5e7eb;
            padding: 0.75rem 0.5rem;
            border-radius: 0.5rem;
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            transition: all 0.2s;
            cursor: pointer;
        }
        .ac-nav-btn:active {
            transform: scale(0.95);
        }
        .ac-nav-btn.disabled {
            opacity: 0.5;
            pointer-events: none;
        }
        .ac-nav-btn.ac-nav-back {
            background: rgba(124,58,237,0.15);
            border-color: rgba(124,58,237,0.3);
            color: #a78bfa;
        }

        /* Badges */
        .ac-badge-container {
            position: fixed;
            top: 1rem;
            right: 1rem;
            z-index: 200;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            pointer-events: none;
        }
        .ac-badge-toast {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 0.75rem;
            padding: 1rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            animation: acBadgeSlide 0.5s ease-out;
            pointer-events: auto;
            min-width: 250px;
        }
        @keyframes acBadgeSlide {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .ac-badge-icon {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }
        .ac-badge-title {
            font-size: 0.75rem;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .ac-badge-name {
            font-size: 1rem;
            font-weight: 600;
        }

        /* Completion States */
        .ac-level-complete, .ac-module-complete {
            position: relative;
        }
        .ac-complete-badge {
            position: absolute;
            top: -5px;
            right: -5px;
            background: #10b981;
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            border: 2px solid #111827;
        }
        .ac-module-badge {
            margin-top: 0.5rem;
            font-size: 0.75rem;
            color: #10b981;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }
        .ac-lesson-done {
            background: rgba(16,185,129,0.05) !important;
            border-color: rgba(16,185,129,0.2) !important;
        }

        /* Quiz */
        .ac-quiz-opt:hover:not(:disabled) {
            border-color: #374151 !important;
            background: #1f2937 !important;
        }
        .ac-quiz-opt.selected {
            border-color: #7c3aed !important;
            background: rgba(124,58,237,0.12) !important;
            color: #c4b5fd !important;
        }
        .ac-chart-opt:not(:disabled):hover {
            border-color: #7c3aed !important;
            background: rgba(124,58,237,0.08) !important;
            color: #c4b5fd !important;
        }

        /* Mobile Responsiveness */
        @media (max-width: 767px) {
            .ac-level-grid, .ac-module-grid {
                grid-template-columns: 1fr !important;
            }
            .ac-lesson-container, .ac-quiz-container, .ac-results-container {
                max-width: 100% !important;
                padding: 0 0.5rem;
            }
            .ac-lesson-title {
                font-size: 1.1rem !important;
            }
            .ac-action-buttons {
                flex-direction: column;
            }
            .ac-action-buttons button {
                width: 100%;
                justify-content: center;
            }
            .ac-svg-diagram {
                max-width: 100%;
                padding: 0.5rem;
            }
            .ac-tradingview-widget {
                min-height: 300px;
            }
            .pw-card-body {
                padding: 1rem !important;
            }
            #academy-container {
                padding-bottom: 80px !important;
            }
            .ac-mobile-nav {
                display: block !important;
            }
        }
        @media (min-width: 768px) {
            .ac-mobile-nav {
                display: none !important;
            }
        }

        /* Utilities */
        .pw-breadcrumb-sep {
            margin: 0 0.5rem;
            color: #4b5563;
        }
    `;
    document.head.appendChild(s);
})();

/* ── HTML Escape Helper ─────────────────────────────────────────────────── */
function _es(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
