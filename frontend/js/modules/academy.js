/**
 * Pipways Trading Academy Frontend Module v3.0 (PATCHED)
 * Changes:
 * - Added TradingView widget integration for technical lessons
 * - Added SVG visual diagrams (candlestick, support/resistance, etc.)
 * - Added first-visit vs Trading Coach banner logic
 * - Added mobile navigation (Next/Prev/Back buttons)
 * - Added badge notification system
 * - Fixed breadcrumb state management for Back to Module
 * - Added responsive CSS for mobile
 */

/* ── LMS API methods ─────────────────────────────────────────────────────── */
(function extendAPI() {
    const A = window.API;
    if (!A || A._academyReady) return;
    A._academyReady = true;
    const req = (url, opts) => A.request(url, opts);
    const get  = (url)       => req(url);
    const post = (url, body) => req(url, { method:'POST', body: body ? JSON.stringify(body) : undefined });

    A.lms = {
        getLevels:          ()     => get('/learning/levels'),
        getModules:         (lid)  => get(`/learning/modules/${lid}`),
        getLessons:         (mid)  => get(`/learning/lessons/${mid}`),
        getLesson:          (lid)  => get(`/learning/lesson/${lid}`),
        getQuiz:            (lid)  => get(`/learning/quiz/${lid}`),
        getProgress:        (uid)  => get(`/learning/progress/${uid}`),
        getBadges:          (uid)  => get(`/learning/badges/${uid}`),
        checkBadges:        ()     => post('/learning/badges/check', {}),
        getMentorGuide:     (uid)  => get(`/learning/mentor/guide/${uid}`),
        getMentorTeach:     (lid)  => post(`/learning/mentor/teach?lesson_id=${lid}`),
        getMentorPractice:  (lid)  => post(`/learning/mentor/practice?lesson_id=${lid}`),
        getChartPractice:   (lid)  => post(`/learning/mentor/chart-practice?lesson_id=${lid}`),
        markFirstVisit:     ()     => post('/learning/profile/first-visit-complete', {}),
        submitQuiz:         (lid, answers) => post('/learning/quiz/submit', { lesson_id: lid, answers }),
        completeLesson:     (lid, score)   => post('/learning/lesson/complete', { lesson_id: lid, quiz_score: score || 0 }),
    };
})();


/* ═══════════════════════════════════════════════════════════════════════════
   ACADEMY PAGE
═══════════════════════════════════════════════════════════════════════════ */
const AcademyPage = {

    _level: null, _module: null, _lesson: null, _quiz: null, _uid: null,
    _firstVisit: false, _badges: [],

    async render() {
        const u = this._getUser(); this._uid = u?.id ?? null;
        const wrap = document.getElementById('academy-container');
        if (!wrap) return;
        wrap.innerHTML = `
            <div id="ac-breadcrumb" class="pw-breadcrumb mb-4" style="display:none;"></div>
            <div id="ac-mentor-banner"></div>
            <div id="ac-badge-toast" class="ac-badge-container"></div>
            <div id="ac-main"></div>
            <div id="ac-mobile-nav" class="ac-mobile-nav hidden md:hidden"></div>`;
        
        // Check badges on load
        if (this._uid) {
            await this._loadBadges();
            const check = await API.lms.checkBadges().catch(()=>({}));
            if (check.newly_awarded?.length) await this._showNewBadges(check.newly_awarded);
        }
        
        await this._showLevelSelector();
    },

    /* ── Level Selector ─────────────────────────────────────────────────── */
    async _showLevelSelector() {
        this._level = this._module = this._lesson = null;
        this._bc(null,null,null);
        this._hideMobileNav();
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading curriculum…');
        
        try {
            const [levels, prog, guide] = await Promise.all([
                API.lms.getLevels(),
                this._uid ? API.lms.getProgress(this._uid).catch(()=>null) : null,
                this._uid ? API.lms.getMentorGuide(this._uid).catch(()=>null) : null,
            ]);
            
            // Store first visit state
            if (guide?.first_visit !== undefined) {
                this._firstVisit = guide.first_visit;
            }
            
            const sm = {};
            (prog?.summary||[]).forEach(s=>sm[s.level_id]=s);
            
            if (this._uid) this._loadMentorBanner(guide);
            
            const cfg = [
                {icon:'fa-seedling',  color:'#34d399', bg:'rgba(52,211,153,.15)'},
                {icon:'fa-chart-line',color:'#60a5fa', bg:'rgba(96,165,250,.15)'},
                {icon:'fa-trophy',    color:'#f59e0b', bg:'rgba(245,158,11,.15)'},
            ];
            
            if (!levels || !levels.length) {
                main.innerHTML = this._emptyState('Academy not set up yet', 
                    'The learning curriculum is being initialized. Please refresh in a moment.');
                return;
            }
            
            main.innerHTML = `<div class="grid grid-cols-1 sm:grid-cols-3 gap-4 ac-level-grid">
            ${levels.map((lv,i)=>{
                const c=cfg[i%3], s=sm[lv.id], pct=s?s.percent:0, done=s?s.completed:0, tot=s?s.total:0;
                const isComplete = pct >= 100;
                return `<div class="pw-card cursor-pointer ac-level-card ${isComplete?'ac-level-complete':''}" 
                        onclick="AcademyPage._selectLevel(${lv.id},'${_es(lv.name)}')" 
                        style="border-top:3px solid ${c.color};position:relative;">
                    <div class="pw-card-body" style="padding:1.5rem;">
                        ${isComplete?`<div class="ac-complete-badge"><i class="fas fa-check-circle"></i></div>`:''}
                        <div class="w-10 h-10 rounded-xl flex items-center justify-center mb-3" style="background:${c.bg};">
                            <i class="fas ${c.icon}" style="color:${c.color};"></i>
                        </div>
                        <div class="text-xs font-bold mb-1" style="color:${c.color};letter-spacing:.06em;">${_es(lv.name).toUpperCase()}</div>
                        <h3 class="text-white font-bold text-base mb-1">${_es(lv.name)}</h3>
                        <p class="text-gray-500 text-xs leading-relaxed mb-4">${_es(lv.description)}</p>
                        <div class="flex justify-between text-xs text-gray-500 mb-1.5">
                            <span>Progress</span>
                            <span class="font-semibold" style="color:${c.color};">${pct}%</span>
                        </div>
                        <div class="pw-progress-bar"><div class="pw-progress-fill" style="width:${pct}%;background:${c.color};"></div></div>
                        <div class="text-xs text-gray-600 mt-2">${done} of ${tot} lessons done</div>
                    </div>
                </div>`;
            }).join('')}
            </div>`;
        } catch(e) {
            main.innerHTML = this._error(
                'Could not load Academy',
                e.message + ' — check that learning.py is mounted in main.py'
            );
        }
    },

    /* ── Module List ────────────────────────────────────────────────────── */
    async _selectLevel(levelId, levelName) {
        this._level = {id:levelId,name:levelName}; this._module=null;
        this._bc(levelName,null,null);
        this._hideMobileNav();
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading modules…');
        try {
            const modules = await API.lms.getModules(levelId);
            main.innerHTML = `<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 ac-module-grid">
            ${modules.map(m=>{
                const pct=m.lesson_count?Math.round(m.completed_count/m.lesson_count*100):0;
                const isComplete = m.is_complete;
                return `<div class="pw-card cursor-pointer ac-module-card ${isComplete?'ac-module-complete':''}" 
                    onclick="AcademyPage._selectModule(${m.id},'${_es(m.title)}')"
                    onmouseover="this.style.borderColor='#374151'" onmouseout="this.style.borderColor=''">
                    <div class="pw-card-body">
                        <div class="flex items-start justify-between mb-2">
                            <div>
                                ${isComplete
                                    ? `<span class="badge badge-success text-xs mb-1"><i class="fas fa-check-circle mr-1"></i>Complete</span>`
                                    : `<span class="text-xs text-gray-500 mb-1 block">${m.completed_count}/${m.lesson_count} lessons</span>`}
                                <h3 class="text-white font-semibold">${_es(m.title)}</h3>
                            </div>
                            <i class="fas fa-chevron-right text-gray-700 text-xs mt-1"></i>
                        </div>
                        <p class="text-gray-500 text-xs leading-relaxed mb-3">${_es(m.description)}</p>
                        <div class="pw-progress-bar"><div class="pw-progress-fill ${pct>=80&&pct<100?'near-done':''}" style="width:${pct}%;"></div></div>
                        ${isComplete?`<div class="ac-module-badge"><i class="fas fa-medal"></i> Module Complete</div>`:''}
                    </div>
                </div>`;
            }).join('')}
            </div>`;
        } catch(e) { main.innerHTML = this._error('Could not load modules', e.message); }
    },

    /* ── Lesson List ────────────────────────────────────────────────────── */
    async _selectModule(moduleId, moduleTitle) {
        this._module = {id:moduleId,name:moduleTitle}; this._lesson=null;
        this._bc(this._level?.name, moduleTitle, null);
        this._hideMobileNav();
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading lessons…');
        try {
            const lessons = await API.lms.getLessons(moduleId);
            main.innerHTML = `<div class="space-y-2 max-w-2xl ac-lesson-list">
            ${lessons.map((l,i)=>{
                const locked=!l.unlocked, done=l.completed;
                const icon = done?'fa-check-circle text-green-400':locked?'fa-lock text-gray-700':'fa-play-circle text-purple-400';
                const score = done&&l.quiz_score!==null
                    ? `<span class="text-xs font-semibold" style="color:#34d399;">${l.quiz_score}%</span>` : '';
                return `<div class="pw-card ${locked?'opacity-50':''} ${!locked?'cursor-pointer':''} ac-lesson-item ${done?'ac-lesson-done':''}"
                    ${!locked?`onclick="AcademyPage._openLesson(${l.id},'${_es(l.title)}')"
                     onmouseover="this.style.borderColor='#374151'" onmouseout="this.style.borderColor=''"`:''}>
                    <div class="pw-card-body" style="padding:.85rem 1.25rem;">
                        <div class="flex items-center gap-3">
                            <i class="fas ${icon} text-lg flex-shrink-0" style="width:20px;text-align:center;"></i>
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center gap-2">
                                    <span class="text-white font-medium text-sm truncate">Lesson ${i+1}: ${_es(l.title)}</span>
                                    ${score}
                                </div>
                                ${locked?`<div class="text-xs text-gray-600 mt-0.5">Complete previous lesson to unlock</div>`:''}
                            </div>
                            ${!locked?`<i class="fas fa-chevron-right text-gray-700 text-xs flex-shrink-0"></i>`:''}
                        </div>
                    </div>
                </div>`;
            }).join('')}
            </div>`;
        } catch(e) { main.innerHTML = this._error('Could not load lessons', e.message); }
    },

    /* ── Lesson View ────────────────────────────────────────────────────── */
    async _openLesson(lessonId, lessonTitle) {
        this._lesson = {id:lessonId,name:lessonTitle};
        this._bc(this._level?.name, this._module?.name, lessonTitle);
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading lesson…');
        try {
            const lesson = await API.lms.getLesson(lessonId);
            
            // Process content for visual aids and charts
            const processedContent = this._processLessonContent(lesson.content, lessonTitle);
            
            // Mobile navigation buttons
            this._renderMobileNav(lesson);
            
            main.innerHTML = `<div class="max-w-3xl ac-lesson-container">
                <div class="pw-card mb-4">
                    <div class="pw-card-hdr ac-lesson-header">
                        <div>
                            <div class="text-xs text-gray-500 mb-0.5">${_es(lesson.module_title)} · ${_es(lesson.level_name)}</div>
                            <h2 class="card-title ac-lesson-title">${_es(lesson.title)}</h2>
                        </div>
                    </div>
                    <div class="pw-card-body">
                        <div class="ac-lesson-text">${processedContent}</div>
                    </div>
                </div>
                
                ${this._renderVisualAids(lessonTitle)}
                
                <div class="flex flex-wrap gap-2 mb-4 ac-action-buttons">
                    <button class="btn btn-primary" onclick="AcademyPage._startQuiz(${lessonId})">
                        <i class="fas fa-pencil-alt mr-2"></i>Take Quiz
                    </button>
                    <button id="ac-explain-btn" class="btn" style="background:#1f2937;border:1px solid #374151;color:#e5e7eb;"
                            onclick="AcademyPage._showExplanation(${lessonId})">
                        <i class="fas fa-chalkboard-teacher mr-2" style="color:#a78bfa;"></i>Trading Coach
                    </button>
                    <button id="ac-practice-btn" class="btn" style="background:#1f2937;border:1px solid #374151;color:#e5e7eb;"
                            onclick="AcademyPage._showPractice(${lessonId})">
                        <i class="fas fa-dumbbell mr-2" style="color:#fbbf24;"></i>Practice
                    </button>
                    <button id="ac-chart-btn" class="btn" style="background:#1f2937;border:1px solid #374151;color:#e5e7eb;"
                            onclick="AcademyPage._showChartPractice(${lessonId})">
                        <i class="fas fa-chart-bar mr-2" style="color:#60a5fa;"></i>Chart Exercise
                    </button>
                </div>
                
                <!-- Desktop Navigation -->
                <div class="hidden md:flex justify-between items-center py-4 border-t border-gray-800">
                    ${lesson.prev_lesson 
                        ? `<button onclick="AcademyPage._openLesson(${lesson.prev_lesson.id},'${_es(lesson.prev_lesson.title)}')" class="text-gray-400 hover:text-white text-sm flex items-center gap-2">
                             <i class="fas fa-arrow-left"></i> Previous: ${_es(lesson.prev_lesson.title)}
                           </button>`
                        : `<span></span>`}
                    ${lesson.next_lesson
                        ? `<button onclick="AcademyPage._openLesson(${lesson.next_lesson.id},'${_es(lesson.next_lesson.title)}')" class="text-purple-400 hover:text-purple-300 text-sm flex items-center gap-2">
                             Next: ${_es(lesson.next_lesson.title)} <i class="fas fa-arrow-right"></i>
                           </button>`
                        : `<span></span>`}
                </div>
                
                <div id="ac-ai-panel"></div>
            </div>`;
            
            // Inject TradingView widgets if chart tags present
            this._injectTradingViewWidgets(lesson.content);
            
        } catch(e) { 
            main.innerHTML = this._error('Could not load lesson', e.message); 
        }
    },

    /* ── Content Processing ─────────────────────────────────────────────── */
    _processLessonContent(content, title) {
        if (!content) return '';
        
        // Convert [CHART:SYMBOL] to widget containers
        let processed = content.replace(/\[CHART:([A-Z]+)\]/g, (match, symbol) => {
            const tvSymbol = symbol === 'GOLD' ? 'TVC:GOLD' : `FX:${symbol}`;
            return `<div class="ac-tradingview-widget" data-symbol="${tvSymbol}" id="tv-widget-${symbol}"></div>`;
        });
        
        // Convert [VISUAL:TYPE] placeholders to SVG diagrams
        processed = processed.replace(/\[VISUAL:([A-Z_]+)\]/g, (match, type) => {
            return this._getSVGDiagram(type);
        });
        
        // Markdown-like processing
        const s = processed.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
        return s
            .replace(/```([\s\S]*?)```/g,'<pre class="ac-code"><code>$1</code></pre>')
            .replace(/`([^`]+)`/g,'<code class="ac-inline-code">$1</code>')
            .replace(/^## (.+)$/gm,'<h3 class="ac-h3">$1</h3>')
            .replace(/^### (.+)$/gm,'<h4 class="ac-h4">$1</h4>')
            .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
            .replace(/^- (.+)$/gm,'<li class="ac-li">$1</li>')
            .replace(/(<li[\s\S]*?<\/li>)/g,'<ul class="ac-ul">$1</ul>')
            .replace(/\n{2,}/g,'</p><p class="ac-p">')
            .replace(/\n/g,'<br>');
    },

    _getSVGDiagram(type) {
        const diagrams = {
            'CANDLESTICK_ANATOMY': `<svg viewBox="0 0 200 120" class="ac-svg-diagram">
                <rect x="20" y="30" width="40" height="60" fill="#22c55e" opacity="0.8"/>
                <line x1="40" y1="10" x2="40" y2="30" stroke="#22c55e" stroke-width="2"/>
                <line x1="40" y1="90" x2="40" y2="110" stroke="#22c55e" stroke-width="2"/>
                <text x="70" y="20" fill="#9ca3af" font-size="8">Wick (High)</text>
                <text x="70" y="65" fill="#9ca3af" font-size="8">Body (Open-Close)</text>
                <text x="70" y="110" fill="#9ca3af" font-size="8">Wick (Low)</text>
                <rect x="120" y="40" width="40" height="40" fill="#ef4444" opacity="0.8"/>
                <line x1="140" y1="20" x2="140" y2="40" stroke="#ef4444" stroke-width="2"/>
                <line x1="140" y1="80" x2="140" y2="100" stroke="#ef4444" stroke-width="2"/>
                <text x="170" y="65" fill="#9ca3af" font-size="8">Bearish</text>
            </svg>`,
            'SUPPORT_RESISTANCE': `<svg viewBox="0 0 200 100" class="ac-svg-diagram">
                <path d="M 10 70 Q 50 70 70 50 T 130 50 T 190 30" fill="none" stroke="#60a5fa" stroke-width="2"/>
                <line x1="0" y1="70" x2="200" y2="70" stroke="#22c55e" stroke-width="2" stroke-dasharray="5,5"/>
                <text x="10" y="85" fill="#22c55e" font-size="8">Support - Price bounces up</text>
                <line x1="0" y1="30" x2="200" y2="30" stroke="#ef4444" stroke-width="2" stroke-dasharray="5,5"/>
                <text x="10" y="25" fill="#ef4444" font-size="8">Resistance - Price rejected</text>
                <circle cx="70" cy="70" r="3" fill="#22c55e"/>
                <circle cx="130" cy="30" r="3" fill="#ef4444"/>
            </svg>`,
            'TREND_STRUCTURE': `<svg viewBox="0 0 200 100" class="ac-svg-diagram">
                <path d="M 20 80 L 50 60 L 80 65 L 110 40 L 140 45 L 170 20" fill="none" stroke="#60a5fa" stroke-width="2"/>
                <line x1="20" y1="60" x2="200" y2="60" stroke="#22c55e" stroke-width="1" stroke-dasharray="3,3" opacity="0.5"/>
                <text x="10" y="60" fill="#22c55e" font-size="8">Higher Low</text>
                <text x="10" y="30" fill="#60a5fa" font-size="8">Higher High</text>
                <text x="100" y="95" fill="#9ca3af" font-size="8">Uptrend = HH + HL</text>
            </svg>`,
            'MARKET_STRUCTURE': `<svg viewBox="0 0 200 100" class="ac-svg-diagram">
                <path d="M 10 80 L 40 50 L 70 60 L 100 30 L 130 40" fill="none" stroke="#a78bfa" stroke-width="2"/>
                <circle cx="40" cy="50" r="4" fill="#f59e0b"/>
                <text x="50" y="45" fill="#f59e0b" font-size="8">Order Block</text>
                <line x1="100" y1="30" x2="130" y2="30" stroke="#ef4444" stroke-width="2"/>
                <text x="105" y="25" fill="#ef4444" font-size="8">BOS</text>
            </svg>`,
            'LIQUIDITY_SWEEP': `<svg viewBox="0 0 200 100" class="ac-svg-diagram">
                <rect x="30" y="20" width="140" height="60" fill="none" stroke="#374151" stroke-width="1"/>
                <line x1="30" y1="35" x2="170" y2="35" stroke="#ef4444" stroke-width="2" stroke-dasharray="3,3"/>
                <text x="35" y="32" fill="#ef4444" font-size="8">Stop Losses (Liquidity)</text>
                <path d="M 50 60 L 80 50 L 110 55 L 140 35" fill="none" stroke="#f59e0b" stroke-width="2"/>
                <circle cx="140" cy="35" r="3" fill="#f59e0b"/>
                <text x="145" y="30" fill="#f59e0b" font-size="8">Sweep</text>
            </svg>`,
            'PIP_SPREAD': `<svg viewBox="0 0 200 80" class="ac-svg-diagram">
                <rect x="20" y="30" width="70" height="20" fill="#1f2937" stroke="#4b5563"/>
                <text x="35" y="44" fill="#9ca3af" font-size="10">1.0850</text>
                <text x="75" y="44" fill="#9ca3af" font-size="10">Bid</text>
                <rect x="110" y="30" width="70" height="20" fill="#1f2937" stroke="#4b5563"/>
                <text x="125" y="44" fill="#9ca3af" font-size="10">1.0852</text>
                <text x="165" y="44" fill="#9ca3af" font-size="10">Ask</text>
                <line x1="90" y1="40" x2="110" y2="40" stroke="#f59e0b" stroke-width="2" marker-end="url(#arrow)"/>
                <text x="95" y="55" fill="#f59e0b" font-size="8">2 pips spread</text>
                <defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#f59e0b"/></marker></defs>
            </svg>`,
            'RISK_2PERCENT': `<svg viewBox="0 0 200 60" class="ac-svg-diagram">
                <rect x="10" y="20" width="180" height="20" fill="#1f2937"/>
                <rect x="10" y="20" width="3.6" height="20" fill="#ef4444"/>
                <text x="15" y="55" fill="#ef4444" font-size="8">2% Risk</text>
                <rect x="13.6" y="20" width="176.4" height="20" fill="#22c55e" opacity="0.3"/>
                <text x="100" y="35" fill="#9ca3af" font-size="10">Account Balance Protected</text>
            </svg>`,
            'SESSIONS_CLOCK': `<svg viewBox="0 0 200 100" class="ac-svg-diagram">
                <circle cx="100" cy="50" r="40" fill="none" stroke="#4b5563"/>
                <path d="M 100 50 L 100 20" stroke="#60a5fa" stroke-width="2"/>
                <path d="M 100 50 L 130 50" stroke="#60a5fa" stroke-width="2"/>
                <text x="85" y="15" fill="#fbbf24" font-size="8">Asian</text>
                <text x="140" y="45" fill="#a78bfa" font-size="8">London</text>
                <text x="85" y="95" fill="#34d399" font-size="8">New York</text>
                <circle cx="100" cy="50" r="3" fill="#fff"/>
            </svg>`,
            'LEVERAGE_EXAMPLE': `<svg viewBox="0 0 200 80" class="ac-svg-diagram">
                <rect x="10" y="30" width="40" height="20" fill="#f59e0b" opacity="0.5"/>
                <text x="15" y="44" fill="#fff" font-size="8">$1,000</text>
                <line x1="50" y1="40" x2="150" y2="40" stroke="#9ca3af" stroke-width="1" stroke-dasharray="3,3"/>
                <text x="75" y="35" fill="#9ca3af" font-size="8">1:100</text>
                <rect x="150" y="20" width="40" height="40" fill="#22c55e" opacity="0.3"/>
                <text x="155" y="44" fill="#fff" font-size="8">$100k</text>
                <text x="70" y="70" fill="#ef4444" font-size="8">Amplifies gains AND losses</text>
            </svg>`,
            'CANDLESTICK_PATTERNS': `<svg viewBox="0 0 200 100" class="ac-svg-diagram">
                <text x="10" y="15" fill="#9ca3af" font-size="8">Pin Bar (Rejection)</text>
                <line x1="30" y1="80" x2="30" y2="20" stroke="#22c55e" stroke-width="2"/>
                <rect x="25" y="50" width="10" height="15" fill="#22c55e"/>
                <text x="60" y="15" fill="#9ca3af" font-size="8">Engulfing</text>
                <rect x="80" y="55" width="12" height="20" fill="#ef4444"/>
                <rect x="95" y="45" width="12" height="35" fill="#22c55e"/>
            </svg>`,
            'CHART_PATTERNS': `<svg viewBox="0 0 200 100" class="ac-svg-diagram">
                <path d="M 20 70 L 50 50 L 80 60 L 110 30 L 140 40 L 170 20" fill="none" stroke="#60a5fa"/>
                <text x="70" y="90" fill="#9ca3af" font-size="8">Head & Shoulders</text>
                <circle cx="50" cy="50" r="2" fill="#a78bfa"/>
                <circle cx="110" cy="30" r="2" fill="#a78bfa"/>
                <circle cx="170" cy="20" r="2" fill="#a78bfa"/>
            </svg>`,
            'DISCIPLINE_CYCLE': `<svg viewBox="0 0 200 100" class="ac-svg-diagram">
                <circle cx="50" cy="50" r="20" fill="none" stroke="#22c55e"/>
                <text x="35" y="55" fill="#22c55e" font-size="8">Rules</text>
                <path d="M 70 50 L 90 50" stroke="#4b5563"/>
                <circle cx="110" cy="50" r="20" fill="none" stroke="#60a5fa"/>
                <text x="95" y="55" fill="#60a5fa" font-size="8">Records</text>
                <path d="M 130 50 L 150 50" stroke="#4b5563"/>
                <circle cx="170" cy="50" r="20" fill="none" stroke="#a78bfa"/>
                <text x="155" y="55" fill="#a78bfa" font-size="8">Review</text>
            </svg>`,
            'FVG_DIAGRAM': `<svg viewBox="0 0 200 100" class="ac-svg-diagram">
                <rect x="20" y="60" width="30" height="20" fill="#ef4444" opacity="0.6"/>
                <rect x="55" y="30" width="30" height="50" fill="#22c55e" opacity="0.6"/>
                <rect x="90" y="40" width="30" height="30" fill="#22c55e" opacity="0.6"/>
                <rect x="50" y="30" width="75" height="10" fill="#f59e0b" opacity="0.3"/>
                <text x="60" y="38" fill="#f59e0b" font-size="8">Fair Value Gap</text>
            </svg>`,
            'MARKET_PARTICIPANTS': `<svg viewBox="0 0 200 120" class="ac-svg-diagram">
                <circle cx="40" cy="30" r="15" fill="#f59e0b" opacity="0.5"/>
                <text x="60" y="35" fill="#9ca3af" font-size="8">Central Banks</text>
                <circle cx="40" cy="70" r="15" fill="#60a5fa" opacity="0.5"/>
                <text x="60" y="75" fill="#9ca3af" font-size="8">Institutions</text>
                <circle cx="40" cy="105" r="10" fill="#a78bfa" opacity="0.5"/>
                <text x="60" y="110" fill="#9ca3af" font-size="8">Retail (You)</text>
            </svg>`,
        };
        return diagrams[type] || `<div class="ac-visual-placeholder">[Visual: ${type}]</div>`;
    },

    _renderVisualAids(title) {
        // Additional visual aids based on lesson title keywords
        const visuals = [];
        const t = title.toLowerCase();
        if (t.includes('candlestick')) visuals.push(this._getSVGDiagram('CANDLESTICK_PATTERNS'));
        if (t.includes('support') || t.includes('resistance')) visuals.push(this._getSVGDiagram('SUPPORT_RESISTANCE'));
        if (t.includes('trend')) visuals.push(this._getSVGDiagram('TREND_STRUCTURE'));
        if (t.includes('pattern')) visuals.push(this._getSVGDiagram('CHART_PATTERNS'));
        if (t.includes('structure') || t.includes('bos') || t.includes('choch')) visuals.push(this._getSVGDiagram('MARKET_STRUCTURE'));
        if (t.includes('liquidity') || t.includes('stop hunt')) visuals.push(this._getSVGDiagram('LIQUIDITY_SWEEP'));
        if (t.includes('psychology') || t.includes('discipline')) visuals.push(this._getSVGDiagram('DISCIPLINE_CYCLE'));
        
        if (visuals.length === 0) return '';
        return `<div class="ac-visual-aids-grid">${visuals.join('')}</div>`;
    },

    _injectTradingViewWidgets(content) {
        if (!content) return;
        const widgets = document.querySelectorAll('.ac-tradingview-widget');
        widgets.forEach(w => {
            const symbol = w.dataset.symbol;
            if (!symbol) return;
            w.innerHTML = `<div class="tradingview-widget-container" style="height:400px;width:100%;">
                <div id="tv-${symbol}"></div>
            </div>`;
            
            setTimeout(() => {
                if (window.TradingView) {
                    new TradingView.widget({
                        container_id: `tv-${symbol}`,
                        symbol: symbol,
                        interval: "240",
                        timezone: "Etc/UTC",
                        theme: "dark",
                        style: "1",
                        locale: "en",
                        toolbar_bg: "#f1f3f6",
                        enable_publishing: false,
                        hide_top_toolbar: false,
                        hide_legend: false,
                        save_image: false,
                        studies: ["RSI@tv-basicstudies", "MACD@tv-basicstudies", "MASimple@tv-basicstudies"],
                        show_popup_button: true,
                        popup_width: "1000",
                        popup_height: "650"
                    });
                } else {
                    // Fallback to widget script
                    const script = document.createElement('script');
                    script.src = "https://s3.tradingview.com/tv.js";
                    script.onload = () => {
                        if (window.TradingView) {
                            new TradingView.widget({
                                container_id: `tv-${symbol}`,
                                symbol: symbol,
                                interval: "240",
                                timezone: "Etc/UTC",
                                theme: "dark",
                                style: "1",
                                locale: "en",
                                height: 400,
                                studies: ["RSI@tv-basicstudies", "MACD@tv-basicstudies"]
                            });
                        }
                    };
                    document.head.appendChild(script);
                }
            }, 100);
        });
    },

    /* ── Mobile Navigation ─────────────────────────────────────────────── */
    _renderMobileNav(lesson) {
        const nav = document.getElementById('ac-mobile-nav');
        if (!nav) return;
        
        nav.classList.remove('hidden');
        nav.innerHTML = `
            <div class="ac-mobile-nav-inner">
                <button class="ac-nav-btn ${!lesson.prev_lesson?'disabled':''}" 
                    onclick="${lesson.prev_lesson?`AcademyPage._openLesson(${lesson.prev_lesson.id},'${_es(lesson.prev_lesson.title)}')`:''}">
                    <i class="fas fa-arrow-left"></i> Prev
                </button>
                <button class="ac-nav-btn ac-nav-back" onclick="AcademyPage._selectModule(${this._module?.id},'${_es(this._module?.name||'')}')">
                    <i class="fas fa-th-large"></i> Module
                </button>
                <button class="ac-nav-btn ${!lesson.next_lesson?'disabled':''}" 
                    onclick="${lesson.next_lesson?`AcademyPage._openLesson(${lesson.next_lesson.id},'${_es(lesson.next_lesson.title)}')`:''}">
                    Next <i class="fas fa-arrow-right"></i>
                </button>
            </div>
        `;
    },

    _hideMobileNav() {
        const nav = document.getElementById('ac-mobile-nav');
        if (nav) nav.classList.add('hidden');
    },

    /* ── AI Trading Coach Interactions ──────────────────────────────────── */
    async _showExplanation(lessonId) {
        this._setBtn('ac-explain-btn',true,'Loading…');
        const panel = document.getElementById('ac-ai-panel');
        panel.innerHTML = this._aiLoading('Trading Coach preparing explanation…');
        try {
            const d = await API.lms.getMentorTeach(lessonId);
            panel.innerHTML = `<div class="pw-card ac-coach-card" style="border-left:3px solid #a78bfa;">
                <div class="pw-card-hdr"><div class="flex items-center gap-2">
                    <i class="fas fa-chalkboard-teacher" style="color:#a78bfa;"></i>
                    <span class="card-title" style="font-size:.95rem;">Trading Coach · ${_es(d.lesson_title)}</span>
                    <span class="badge badge-primary text-xs">${_es(d.level)}</span>
                </div></div>
                <div class="pw-card-body"><div class="ac-lesson-text">${this._md(d.explanation)}</div></div>
            </div>`;
        } catch(e) { panel.innerHTML = this._error('Coach unavailable',e.message); }
        this._setBtn('ac-explain-btn',false,'<i class="fas fa-chalkboard-teacher mr-2" style="color:#a78bfa;"></i>Trading Coach');
    },

    async _showPractice(lessonId) {
        this._setBtn('ac-practice-btn',true,'Loading…');
        const panel = document.getElementById('ac-ai-panel');
        panel.innerHTML = this._aiLoading('Generating practice exercise…');
        try {
            const d = await API.lms.getMentorPractice(lessonId);
            panel.innerHTML = `<div class="pw-card ac-coach-card" style="border-left:3px solid #fbbf24;">
                <div class="pw-card-hdr"><div class="flex items-center gap-2">
                    <i class="fas fa-dumbbell" style="color:#fbbf24;"></i>
                    <span class="card-title" style="font-size:.95rem;">Practice Exercise</span>
                </div></div>
                <div class="pw-card-body"><div class="ac-lesson-text">${this._md(d.exercise)}</div></div>
            </div>`;
        } catch(e) { panel.innerHTML = this._error('Practice failed',e.message); }
        this._setBtn('ac-practice-btn',false,'<i class="fas fa-dumbbell mr-2" style="color:#fbbf24;"></i>Practice');
    },

    async _showChartPractice(lessonId) {
        this._setBtn('ac-chart-btn',true,'Loading…');
        const panel = document.getElementById('ac-ai-panel');
        panel.innerHTML = this._aiLoading('Building chart exercise…');
        try {
            const data = await API.lms.getChartPractice(lessonId);
            const cp   = data.chart_practice;
            const opts = (cp.options||[]).map((opt,i)=>`
                <button class="ac-chart-opt w-full text-left px-4 py-3 rounded-lg transition-all text-sm"
                        id="ac-chart-opt-${i}"
                        style="background:#111827;border:1px solid #374151;color:#e5e7eb;"
                        onclick="AcademyPage._answerChart(${i},'${_es(cp.correct||'')}','${_es(cp.explanation||'')}')">
                    ${_es(opt)}
                </button>`).join('');
            
            // Inject TradingView widget for the exercise
            const tvWidget = cp.tv_symbol ? `<div class="ac-tradingview-widget" data-symbol="${cp.tv_symbol}" id="tv-exercise"></div>` : '';
            
            panel.innerHTML = `<div class="pw-card ac-coach-card" style="border-left:3px solid #60a5fa;">
                <div class="pw-card-hdr"><div class="flex items-center gap-2">
                    <i class="fas fa-chart-bar" style="color:#60a5fa;"></i>
                    <span class="card-title" style="font-size:.95rem;">Chart Exercise · ${_es(data.level)}</span>
                </div></div>
                <div class="pw-card-body">
                    ${tvWidget}
                    <div class="rounded-xl p-4 mb-4 text-sm text-gray-300 leading-relaxed"
                         style="background:rgba(96,165,250,.06);border:1px solid rgba(96,165,250,.15);">
                        <div class="text-xs font-bold mb-2" style="color:#60a5fa;">CHART SCENARIO</div>
                        ${_es(cp.scenario||'')}
                    </div>
                    <p class="text-white font-semibold mb-3 text-sm">${_es(cp.question||'')}</p>
                    <div class="space-y-2" id="ac-chart-opts">${opts}</div>
                    <div id="ac-chart-result" class="mt-4 hidden"></div>
                </div>
            </div>`;
            
            // Initialize the chart widget
            if (cp.tv_symbol) {
                setTimeout(() => this._injectTradingViewWidgets(`[CHART:${cp.tv_symbol.replace('FX:', '').replace('OANDA:', '').replace('TVC:', '')}]`), 100);
            }
        } catch(e) { panel.innerHTML = this._error('Chart exercise failed',e.message); }
        this._setBtn('ac-chart-btn',false,'<i class="fas fa-chart-bar mr-2" style="color:#60a5fa;"></i>Chart Exercise');
    },

    _answerChart(idx, correct, explanation) {
        document.querySelectorAll('.ac-chart-opt').forEach((btn,i)=>{
            btn.disabled = true; btn.style.cursor='default';
            const letter = (btn.textContent.trim().charAt(0)||'').toUpperCase();
            if (letter===correct.toUpperCase()) {
                btn.style.background='rgba(16,185,129,.15)';btn.style.borderColor='#34d399';btn.style.color='#34d399';
            } else if (i===idx) {
                btn.style.background='rgba(239,68,68,.1)';btn.style.borderColor='#f87171';btn.style.color='#f87171';
            }
        });
        const chosen = (document.getElementById('ac-chart-opt-'+idx)?.textContent?.trim()?.charAt(0)||'').toUpperCase();
        const passed = chosen === correct.toUpperCase();
        const r = document.getElementById('ac-chart-result');
        r.classList.remove('hidden');
        r.innerHTML = `<div class="rounded-xl p-4 ${passed?'bg-green-900/20 border border-green-800/40':'bg-red-900/20 border border-red-800/40'}">
            <div class="flex items-center gap-2 mb-2">
                <i class="fas ${passed?'fa-check-circle text-green-400':'fa-times-circle text-red-400'}"></i>
                <strong class="${passed?'text-green-400':'text-red-400'}">${passed?'Correct!':'Incorrect'}</strong>
            </div>
            <p class="text-gray-300 text-sm">${_es(explanation)}</p>
        </div>`;
    },

    /* ── Quiz Engine ────────────────────────────────────────────────────── */
    async _startQuiz(lessonId) {
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading quiz…');
        this._hideMobileNav();
        try {
            const data = await API.lms.getQuiz(lessonId);
            if (!data.questions.length) {
                main.innerHTML=`<div class="alert" style="background:rgba(96,165,250,.1);border:1px solid rgba(96,165,250,.3);color:#60a5fa;padding:1rem;border-radius:.5rem;"><i class="fas fa-info-circle mr-2"></i>No quiz questions for this lesson yet.</div>`;
                return;
            }
            this._quiz = {lessonId, questions:data.questions, index:0, answers:[], selected:null};
            this._renderQ();
        } catch(e) { main.innerHTML = this._error('Could not load quiz',e.message); }
    },

    _renderQ() {
        const {questions,index} = this._quiz;
        const q=questions[index], total=questions.length, pct=Math.round((index/total)*100);
        const main = document.getElementById('ac-main');
        main.innerHTML = `<div class="max-w-xl ac-quiz-container">
            <div class="flex items-center justify-between mb-2 text-xs text-gray-500">
                <span>Question ${index+1} of ${total}</span>
                <span>${_es(this._lesson?.name||'Quiz')}</span>
            </div>
            <div class="pw-progress-bar mb-5"><div class="pw-progress-fill" style="width:${pct}%;"></div></div>
            <div class="pw-card mb-4">
                <div class="pw-card-body">
                    <p class="text-white font-semibold text-base leading-relaxed mb-5">${_es(q.question)}</p>
                    <div class="space-y-2.5" id="ac-quiz-opts">
                    ${['A','B','C','D'].map(k=>`
                        <button id="ac-opt-${k}" onclick="AcademyPage._pick('${k}')"
                                class="w-full text-left px-4 py-3 rounded-xl text-sm transition-all ac-quiz-opt"
                                style="background:#111827;border:2px solid #1f2937;color:#d1d5db;">
                            <strong class="text-gray-400">${k}.</strong> ${_es(q['option_'+k.toLowerCase()])}
                        </button>`).join('')}
                    </div>
                </div>
            </div>
            <div class="flex justify-end">
                <button id="ac-quiz-next" disabled class="btn btn-primary opacity-50"
                        onclick="AcademyPage._nextQ()">
                    ${index<total-1?'Next <i class="fas fa-arrow-right ml-2"></i>':'Submit Quiz <i class="fas fa-check ml-2"></i>'}
                </button>
            </div>
        </div>`;
        this._quiz.selected=null;
    },

    _pick(key) {
        this._quiz.selected=key;
        document.querySelectorAll('#ac-quiz-opts button').forEach(b=>{
            b.style.borderColor='#1f2937';b.style.background='#111827';b.style.color='#d1d5db';
        });
        const c=document.getElementById('ac-opt-'+key);
        if(c){c.style.borderColor='#7c3aed';c.style.background='rgba(124,58,237,.12)';c.style.color='#c4b5fd';}
        const n=document.getElementById('ac-quiz-next');
        if(n){n.disabled=false;n.classList.remove('opacity-50');}
    },

    _nextQ() {
        const {selected,index,questions,answers}=this._quiz;
        if(!selected) return;
        answers.push({question_id:questions[index].id, selected_answer:selected});
        this._quiz.answers=answers; this._quiz.index=index+1;
        this._quiz.index<questions.length ? this._renderQ() : this._doSubmit();
    },

    async _doSubmit() {
        const main=document.getElementById('ac-main');
        main.innerHTML=this._loading('Grading your quiz…');
        try {
            const r = await API.lms.submitQuiz(this._quiz.lessonId, this._quiz.answers);
            
            // Show badges if any
            if (r.new_badges?.length) {
                await this._showNewBadges(r.new_badges);
            }
            
            this._showResults(r);
        } catch(e) { main.innerHTML=this._error('Submit failed',e.message); }
    },

    _showResults(result) {
        const main=document.getElementById('ac-main');
        const passClr=result.passed?'#34d399':'#f87171';
        const passMsg=result.passed?'🎉 Passed!':'Keep studying — you\'ll get it!';
        const breakdown=result.results.map((r,i)=>`
            <div class="flex items-start gap-3 py-2.5 border-b ac-result-row" style="border-color:#1f2937;">
                <i class="fas ${r.is_correct?'fa-check-circle text-green-400':'fa-times-circle text-red-400'} mt-0.5 flex-shrink-0"></i>
                <div class="flex-1 text-sm">
                    <span class="text-gray-400">Q${i+1}</span>
                    ${!r.is_correct?`<div class="text-gray-500 text-xs mt-0.5">Correct: <strong class="text-gray-300">${_es(r.correct_answer)}</strong> — ${_es(r.explanation)}</div>`:''}
                </div>
            </div>`).join('');

        main.innerHTML=`<div class="max-w-xl ac-results-container">
            <div class="pw-card mb-4 ac-result-card" style="border-top:3px solid ${passClr};">
                <div class="pw-card-body text-center" style="padding:2rem;">
                    <div class="text-5xl font-black mb-2 ac-score-display" style="color:${passClr};">${result.score}%</div>
                    <div class="font-semibold text-white text-lg">${passMsg}</div>
                    <div class="text-gray-500 text-sm mt-1">${result.correct} of ${result.total} correct</div>
                </div>
            </div>
            ${result.mentor_feedback?`
            <div class="pw-card mb-4 ac-feedback-card" style="border-left:3px solid #a78bfa;">
                <div class="pw-card-body">
                    <div class="flex items-center gap-2 mb-2">
                        <i class="fas fa-robot" style="color:#a78bfa;"></i>
                        <strong class="text-white text-sm">Trading Coach Feedback</strong>
                    </div>
                    <p class="text-gray-300 text-sm leading-relaxed">${_es(result.mentor_feedback)}</p>
                </div>
            </div>`:''}
            <div class="pw-card mb-4">
                <div class="pw-card-hdr"><h3 class="card-title">Answer Breakdown</h3></div>
                <div class="pw-card-body" style="padding-top:0;">${breakdown}</div>
            </div>
            <div class="flex gap-2 flex-wrap ac-result-actions">
                ${result.passed
                    ?`<button class="btn btn-primary" onclick="AcademyPage._selectModule(${this._module?.id},'${_es(this._module?.name||'')}')"><i class="fas fa-arrow-left mr-2"></i>Back to Module</button>`
                    :`<button class="btn btn-primary" onclick="AcademyPage._startQuiz(${this._quiz.lessonId})"><i class="fas fa-redo mr-2"></i>Retry Quiz</button>`}
                <button class="btn" style="background:#1f2937;border:1px solid #374151;color:#e5e7eb;"
                        onclick="AcademyPage._openLesson(${this._lesson?.id},'${_es(this._lesson?.name||'')}')">
                    <i class="fas fa-book-open mr-2"></i>Review Lesson
                </button>
            </div>
        </div>`;
    },

    /* ── Badge System ───────────────────────────────────────────────────── */
    async _loadBadges() {
        if (!this._uid) return;
        try {
            const data = await API.lms.getBadges(this._uid);
            this._badges = data.badges || [];
        } catch(e) {
            console.error('Failed to load badges:', e);
        }
    },

    async _showNewBadges(badgeTypes) {
        const container = document.getElementById('ac-badge-toast');
        if (!container) return;
        
        const badgeDefs = {
            "beginner_trader": {name: "Beginner Trader", icon: "fa-seedling", color: "#34d399"},
            "technical_analyst": {name: "Technical Analyst", icon: "fa-chart-line", color: "#60a5fa"},
            "strategy_builder": {name: "Strategy Builder", icon: "fa-chess-knight", color: "#a78bfa"},
            "pipways_certified": {name: "Pipways Certified", icon: "fa-certificate", color: "#f59e0b"},
            "quiz_master": {name: "Quiz Master", icon: "fa-brain", color: "#f472b6"},
            "perfect_score": {name: "Perfect Score", icon: "fa-star", color: "#fbbf24"},
            "risk_manager": {name: "Risk Manager", icon: "fa-shield-alt", color: "#22d3ee"},
            "psychology_pro": {name: "Psychology Pro", icon: "fa-brain", color: "#e879f9"},
        };
        
        badgeTypes.forEach((type, i) => {
            const def = badgeDefs[type] || {name: type, icon: "fa-medal", color: "#a78bfa"};
            const badge = document.createElement('div');
            badge.className = 'ac-badge-toast';
            badge.style.animationDelay = `${i * 0.2}s`;
            badge.innerHTML = `
                <div class="ac-badge-icon" style="background:${def.color}20;color:${def.color};">
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

    /* ── AI Mentor/Coach Banner ─────────────────────────────────────────── */
    async _loadMentorBanner(guideData) {
        if (!this._uid) return;
        const banner = document.getElementById('ac-mentor-banner');
        if (!banner) return;
        
        try {
            // If no guideData passed, fetch it
            const g = guideData || await API.lms.getMentorGuide(this._uid);
            
            if (g.first_visit) {
                banner.innerHTML = `<div class="pw-card mb-5 ac-welcome-banner" style="border-left:3px solid #34d399;background:linear-gradient(135deg,#0f0a1f,#1a0a2e);">
                    <div class="pw-card-body"><div class="flex items-start gap-3">
                        <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style="background:rgba(52,211,153,.2);">
                            <i class="fas fa-graduation-cap" style="color:#34d399;"></i>
                        </div>
                        <div class="flex-1">
                            <div class="text-xs font-semibold mb-1" style="color:#34d399;">WELCOME</div>
                            <p class="text-gray-300 text-sm leading-relaxed">${g.message}</p>
                            ${g.next_lesson?`<button class="btn btn-primary mt-3 text-xs" style="font-size:.78rem;padding:.35rem .85rem;"
                                    onclick="AcademyPage._markFirstVisitThenContinue(${g.next_lesson.id},'${_es(g.next_lesson.title)}')">
                                Start Learning: ${_es(g.next_lesson.title)} →
                            </button>`:''}
                        </div>
                    </div></div>
                </div>`;
            } else {
                // Trading Coach recommendation mode
                banner.innerHTML = `<div class="pw-card mb-5 ac-coach-banner" style="border-left:3px solid #a78bfa;background:linear-gradient(135deg,#0f0a1f,#1a0a2e);">
                    <div class="pw-card-body"><div class="flex items-start gap-3">
                        <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style="background:rgba(167,139,250,.2);">
                            <i class="fas fa-chalkboard-teacher" style="color:#a78bfa;"></i>
                        </div>
                        <div class="flex-1">
                            <div class="text-xs font-semibold mb-1" style="color:#a78bfa;">TRADING COACH</div>
                            <p class="text-gray-300 text-sm leading-relaxed">${_es(g.message)}</p>
                            ${g.next_lesson?`<button class="btn btn-primary mt-3 text-xs" style="font-size:.78rem;padding:.35rem .85rem;"
                                    onclick="AcademyPage._openLesson(${g.next_lesson.id},'${_es(g.next_lesson.title)}')">
                                Continue: ${_es(g.next_lesson.title)} →
                            </button>`:''}
                        </div>
                    </div></div>
                </div>`;
            }
        } catch(_) { banner.innerHTML=''; }
    },

    async _markFirstVisitThenContinue(lessonId, lessonTitle) {
        try {
            await API.lms.markFirstVisit();
            this._firstVisit = false;
            this._openLesson(lessonId, lessonTitle);
        } catch(e) {
            console.error('Failed to mark first visit:', e);
            this._openLesson(lessonId, lessonTitle);
        }
    },

    /* ── Breadcrumb ─────────────────────────────────────────────────────── */
    _bc(level, module, lesson) {
        const el=document.getElementById('ac-breadcrumb');
        if(!el) return;
        if(!level){el.style.display='none';el.innerHTML='';return;}
        el.style.display='flex';
        // Safe escape for all values
        const l = level ? _es(level) : '';
        const m = module ? _es(module) : '';
        const le = lesson ? _es(lesson) : '';
        
        el.innerHTML =
            `<a href="#" onclick="AcademyPage._showLevelSelector();return false;" class="text-purple-400">Academy</a>`+
            (level?`<span class="pw-breadcrumb-sep">›</span><a href="#" onclick="AcademyPage._selectLevel(${this._level?.id||0},'${l}');return false;" class="text-purple-400">${l}</a>`:'')+
            (module?`<span class="pw-breadcrumb-sep">›</span><a href="#" onclick="AcademyPage._selectModule(${this._module?.id||0},'${m}');return false;" class="text-purple-400">${m}</a>`:'')+
            (lesson?`<span class="pw-breadcrumb-sep">›</span><span class="text-gray-400">${le}</span>`:'');
    },

    /* ── Helpers ────────────────────────────────────────────────────────── */
    _getUser() { try{return JSON.parse(localStorage.getItem('pipways_user')||'{}');}catch(_){return{};} },
    _loading: m=>`<div class="loading"><div class="spinner"></div><p class="text-gray-500 text-sm">${m}</p></div>`,
    _aiLoading: m=>`<div class="pw-card" style="border-left:3px solid #374151;"><div class="pw-card-body loading"><div class="spinner"></div><p class="text-gray-500 text-sm">${m}</p></div></div>`,
    _error: (t,d)=>`<div class="alert alert-error"><i class="fas fa-exclamation-circle mr-2"></i><strong>${_es(t)}</strong> — ${_es(d||'')}</div>`,
    _emptyState: (t,s)=>`<div class="pw-empty" style="padding:4rem 1rem;">
        <div class="pw-empty-icon" style="width:56px;height:56px;"><i class="fas fa-book-open" style="color:#4b5563;font-size:1.2rem;"></i></div>
        <p class="pw-empty-title">${_es(t)}</p>
        <p class="pw-empty-sub">${_es(s)}</p>
        <button onclick="AcademyPage._showLevelSelector()" class="btn btn-primary mt-4" style="font-size:.8rem;padding:.45rem 1rem;">
            <i class="fas fa-refresh mr-1"></i> Retry
        </button>
    </div>`,
    _setBtn(id, loading, html) {
        const b=document.getElementById(id); if(!b)return;
        b.disabled=loading; b.innerHTML=loading?'<i class="fas fa-spinner fa-spin mr-2"></i>Loading…':html;
    },
    _md(text) {
        if(!text) return '';
        // Simple markdown parser for coach responses
        return text
            .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
            .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
            .replace(/\n\n/g,'</p><p class="ac-p">')
            .replace(/\n/g,'<br>');
    },
};

window.AcademyPage = AcademyPage;

/* ── Styles ─────────────────────────────────────────────────────────────── */
(function(){
    if(document.getElementById('ac-styles')) return;
    const s=document.createElement('style'); s.id='ac-styles';
    s.textContent=`
        /* Base lesson typography */
        .ac-lesson-text{color:#d1d5db;font-size:.9rem;line-height:1.75;}
        .ac-lesson-text .ac-p{margin:.75rem 0;}
        .ac-h3{font-size:1.1rem;font-weight:600;color:white;margin:1.5rem 0 .5rem;}
        .ac-h4{font-size:.95rem;font-weight:600;color:#d1d5db;margin:1.25rem 0 .4rem;}
        .ac-ul{margin:.5rem 0 .5rem 1.25rem;list-style:disc;}
        .ac-li{margin:.2rem 0;}
        .ac-code{display:block;background:#111827;border:1px solid #1f2937;border-radius:.5rem;padding:1rem;font-size:.8rem;font-family:monospace;color:#a78bfa;overflow-x:auto;margin:.75rem 0;}
        .ac-inline-code{background:#111827;border:1px solid #1f2937;border-radius:.3rem;padding:.1rem .4rem;font-size:.8em;font-family:monospace;color:#fbbf24;}
        
        /* Visual diagrams */
        .ac-svg-diagram{width:100%;max-width:400px;height:auto;display:block;margin:1rem auto;background:#0d1321;border-radius:.5rem;padding:1rem;border:1px solid #1f2937;}
        .ac-visual-aids-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin:1rem 0;}
        .ac-visual-placeholder{background:#1f2937;border:1px dashed #4b5563;padding:2rem;text-align:center;color:#6b7280;font-size:.8rem;border-radius:.5rem;}
        
        /* TradingView widgets */
        .ac-tradingview-widget{background:#0d1321;border:1px solid #1f2937;border-radius:.5rem;margin:1rem 0;overflow:hidden;height:400px;}
        
        /* Mobile Navigation */
        .ac-mobile-nav{position:fixed;bottom:0;left:0;right:0;background:#111827;border-top:1px solid #1f2937;z-index:100;padding:.5rem;backdrop-filter:blur(10px);}
        .ac-mobile-nav-inner{display:flex;justify-content:space-between;align-items:center;gap:.5rem;}
        .ac-nav-btn{flex:1;background:#1f2937;border:1px solid #374151;color:#e5e7eb;padding:.75rem;border-radius:.5rem;font-size:.875rem;display:flex;align-items:center;justify-content:center;gap:.5rem;transition:all .2s;}
        .ac-nav-btn:active{transform:scale(0.95);}
        .ac-nav-btn.disabled{opacity:.5;pointer-events:none;}
        .ac-nav-btn.ac-nav-back{background:rgba(124,58,237,.15);border-color:rgba(124,58,237,.3);color:#a78bfa;}
        
        /* Badges */
        .ac-badge-container{position:fixed;top:1rem;right:1rem;z-index:200;display:flex;flex-direction:column;gap:.5rem;pointer-events:none;}
        .ac-badge-toast{background:#111827;border:1px solid #1f2937;border-radius:.75rem;padding:1rem;display:flex;align-items:center;gap:1rem;box-shadow:0 10px 40px rgba(0,0,0,.5);animation:acBadgeSlide .5s ease-out;pointer-events:auto;min-width:250px;}
        @keyframes acBadgeSlide{from{transform:translateX(100%);opacity:0;}to{transform:translateX(0);opacity:1;}}
        .ac-badge-icon{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.2rem;}
        .ac-badge-title{font-size:.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;}
        .ac-badge-name{font-size:1rem;font-weight:600;}
        
        /* Completion states */
        .ac-level-complete,.ac-module-complete{position:relative;}
        .ac-complete-badge{position:absolute;top:-5px;right:-5px;background:#10b981;color:white;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.75rem;border:2px solid #111827;}
        .ac-module-badge{margin-top:.5rem;font-size:.75rem;color:#10b981;display:flex;align-items:center;gap:.25rem;}
        .ac-lesson-done{background:rgba(16,185,129,.05);border-color:rgba(16,185,129,.2)!important;}
        
        /* Quiz improvements */
        .ac-quiz-opt:hover{border-color:#374151!important;background:#1f2937!important;}
        .ac-quiz-opt.selected{border-color:#7c3aed!important;background:rgba(124,58,237,.12)!important;color:#c4b5fd!important;}
        .ac-chart-opt:not(:disabled):hover{border-color:#7c3aed!important;background:rgba(124,58,237,.08)!important;color:#c4b5fd!important;}
        .ac-coach-card{background:linear-gradient(135deg,#0f0a1f,#1a0a2e)!important;}
        
        /* Mobile responsiveness */
        @media (max-width:767px){
            .ac-level-grid,.ac-module-grid{grid-template-columns:1fr!important;}
            .ac-lesson-container,.ac-quiz-container,.ac-results-container{max-width:100%!important;padding:0 .5rem;}
            .ac-lesson-title{font-size:1.1rem!important;}
            .ac-action-buttons{flex-direction:column;}
            .ac-action-buttons button{width:100%;justify-content:center;}
            .ac-svg-diagram{max-width:100%;padding:.5rem;}
            .ac-tradingview-widget{height:300px;}
            .pw-card-body{padding:1rem!important;}
            /* Add padding for fixed bottom nav */
            #academy-container{padding-bottom:80px!important;}
        }
        
        /* Safe HTML escape helper styles */
        .ac-welcome-banner,.ac-coach-banner{transition:all .3s ease;}
    `;
    document.head.appendChild(s);
})();

/* ── Safe HTML escape ───────────────────────────────────────────────────── */
function _es(str){
    return String(str||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
