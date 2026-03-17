/**
 * Pipways — Trading Academy Frontend Module  (academy.js)
 * Follows the same pattern as admin.js / cms.js / courses.js.
 *
 * Loaded in dashboard.html via:
 *   <script src="/js/modules/academy.js"></script>
 *
 * Registered in DashboardController.loadSectionData:
 *   case 'academy': await AcademyPage.render(); break;
 *
 * Zero modifications to any existing file required beyond the
 * integration lines described at the bottom of this file.
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
        getMentorGuide:     (uid)  => get(`/learning/mentor/guide/${uid}`),
        getMentorTeach:     (lid)  => post(`/learning/mentor/teach?lesson_id=${lid}`),
        getMentorPractice:  (lid)  => post(`/learning/mentor/practice?lesson_id=${lid}`),
        getChartPractice:   (lid)  => post(`/learning/mentor/chart-practice?lesson_id=${lid}`),
        submitQuiz:         (lid, answers) => post('/learning/quiz/submit', { lesson_id: lid, answers }),
        completeLesson:     (lid, score)   => post('/learning/lesson/complete', { lesson_id: lid, quiz_score: score || 0 }),
    };
})();


/* ═══════════════════════════════════════════════════════════════════════════
   ACADEMY PAGE
═══════════════════════════════════════════════════════════════════════════ */
const AcademyPage = {

    _level: null, _module: null, _lesson: null, _quiz: null, _uid: null,

    async render() {
        const u = this._getUser(); this._uid = u?.id ?? null;
        const wrap = document.getElementById('academy-container');
        if (!wrap) return;
        wrap.innerHTML = `
            <div id="ac-breadcrumb" class="pw-breadcrumb mb-4" style="display:none;"></div>
            <div id="ac-mentor-banner"></div>
            <div id="ac-main"></div>`;
        await this._showLevelSelector();
    },

    /* ── Level Selector ─────────────────────────────────────────────────── */
    async _showLevelSelector() {
        this._level = this._module = this._lesson = null;
        this._bc(null,null,null);
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading levels…');
        try {
            const [levels, prog] = await Promise.all([
                API.lms.getLevels(),
                this._uid ? API.lms.getProgress(this._uid).catch(()=>null) : null,
            ]);
            const sm = {};
            (prog?.summary||[]).forEach(s=>sm[s.level_id]=s);
            if (this._uid) this._loadMentorBanner();
            const cfg = [
                {icon:'fa-seedling',  color:'#34d399', bg:'rgba(52,211,153,.15)'},
                {icon:'fa-chart-line',color:'#60a5fa', bg:'rgba(96,165,250,.15)'},
                {icon:'fa-trophy',    color:'#f59e0b', bg:'rgba(245,158,11,.15)'},
            ];
            main.innerHTML = `<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            ${levels.map((lv,i)=>{
                const c=cfg[i%3], s=sm[lv.id], pct=s?s.percent:0, done=s?s.completed:0, tot=s?s.total:0;
                return `<div class="pw-card cursor-pointer" onclick="AcademyPage._selectLevel(${lv.id},'${_es(lv.name)}')" style="border-top:3px solid ${c.color};">
                    <div class="pw-card-body" style="padding:1.5rem;">
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
        } catch(e) { main.innerHTML = this._error('Could not load levels', e.message); }
    },

    /* ── Module List ────────────────────────────────────────────────────── */
    async _selectLevel(levelId, levelName) {
        this._level = {id:levelId,name:levelName}; this._module=null;
        this._bc(levelName,null,null);
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading modules…');
        try {
            const modules = await API.lms.getModules(levelId);
            main.innerHTML = `<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            ${modules.map(m=>{
                const pct=m.lesson_count?Math.round(m.completed_count/m.lesson_count*100):0;
                return `<div class="pw-card cursor-pointer" onclick="AcademyPage._selectModule(${m.id},'${_es(m.title)}')"
                    onmouseover="this.style.borderColor='#374151'" onmouseout="this.style.borderColor=''">
                    <div class="pw-card-body">
                        <div class="flex items-start justify-between mb-2">
                            <div>
                                ${m.is_complete
                                    ? `<span class="badge badge-success text-xs mb-1"><i class="fas fa-check-circle mr-1"></i>Complete</span>`
                                    : `<span class="text-xs text-gray-500 mb-1 block">${m.completed_count}/${m.lesson_count} lessons</span>`}
                                <h3 class="text-white font-semibold">${_es(m.title)}</h3>
                            </div>
                            <i class="fas fa-chevron-right text-gray-700 text-xs mt-1"></i>
                        </div>
                        <p class="text-gray-500 text-xs leading-relaxed mb-3">${_es(m.description)}</p>
                        <div class="pw-progress-bar"><div class="pw-progress-fill ${pct>=80&&pct<100?'near-done':''}" style="width:${pct}%;"></div></div>
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
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading lessons…');
        try {
            const lessons = await API.lms.getLessons(moduleId);
            main.innerHTML = `<div class="space-y-2 max-w-2xl">
            ${lessons.map((l,i)=>{
                const locked=!l.unlocked, done=l.completed;
                const icon = done?'fa-check-circle text-green-400':locked?'fa-lock text-gray-700':'fa-play-circle text-purple-400';
                const score = done&&l.quiz_score!==null
                    ? `<span class="text-xs font-semibold" style="color:#34d399;">${l.quiz_score}%</span>` : '';
                return `<div class="pw-card ${locked?'opacity-50':''} ${!locked?'cursor-pointer':''}"
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
            main.innerHTML = `<div class="max-w-2xl">
                <div class="pw-card mb-4">
                    <div class="pw-card-hdr">
                        <div>
                            <div class="text-xs text-gray-500 mb-0.5">${_es(lesson.module_title)} · ${_es(lesson.level_name)}</div>
                            <h2 class="card-title">${_es(lesson.title)}</h2>
                        </div>
                    </div>
                    <div class="pw-card-body">
                        <div class="ac-lesson-text">${this._md(lesson.content)}</div>
                    </div>
                </div>
                <div class="flex flex-wrap gap-2 mb-4">
                    <button class="btn btn-primary" onclick="AcademyPage._startQuiz(${lessonId})">
                        <i class="fas fa-pencil-alt mr-2"></i>Take Quiz
                    </button>
                    <button id="ac-explain-btn" class="btn" style="background:#1f2937;border:1px solid #374151;color:#e5e7eb;"
                            onclick="AcademyPage._showExplanation(${lessonId})">
                        <i class="fas fa-robot mr-2" style="color:#a78bfa;"></i>AI Explanation
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
                <div id="ac-ai-panel"></div>
            </div>`;
        } catch(e) { main.innerHTML = this._error('Could not load lesson', e.message); }
    },

    async _showExplanation(lessonId) {
        this._setBtn('ac-explain-btn',true,'Loading…');
        const panel = document.getElementById('ac-ai-panel');
        panel.innerHTML = this._aiLoading('AI Mentor preparing explanation…');
        try {
            const d = await API.lms.getMentorTeach(lessonId);
            panel.innerHTML = `<div class="pw-card" style="border-left:3px solid #a78bfa;">
                <div class="pw-card-hdr"><div class="flex items-center gap-2">
                    <i class="fas fa-robot" style="color:#a78bfa;"></i>
                    <span class="card-title" style="font-size:.95rem;">AI Mentor · ${_es(d.lesson_title)}</span>
                    <span class="badge badge-primary text-xs">${_es(d.level)}</span>
                </div></div>
                <div class="pw-card-body"><div class="ac-lesson-text">${this._md(d.explanation)}</div></div>
            </div>`;
        } catch(e) { panel.innerHTML = this._error('Explanation failed',e.message); }
        this._setBtn('ac-explain-btn',false,'<i class="fas fa-robot mr-2" style="color:#a78bfa;"></i>AI Explanation');
    },

    async _showPractice(lessonId) {
        this._setBtn('ac-practice-btn',true,'Loading…');
        const panel = document.getElementById('ac-ai-panel');
        panel.innerHTML = this._aiLoading('Generating practice exercise…');
        try {
            const d = await API.lms.getMentorPractice(lessonId);
            panel.innerHTML = `<div class="pw-card" style="border-left:3px solid #fbbf24;">
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
            panel.innerHTML = `<div class="pw-card" style="border-left:3px solid #60a5fa;">
                <div class="pw-card-hdr"><div class="flex items-center gap-2">
                    <i class="fas fa-chart-bar" style="color:#60a5fa;"></i>
                    <span class="card-title" style="font-size:.95rem;">Chart Exercise · ${_es(data.level)}</span>
                </div></div>
                <div class="pw-card-body">
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
        const q=questions[index], total=questions.length, pct=Math.round(index/total*100);
        const main = document.getElementById('ac-main');
        main.innerHTML = `<div class="max-w-xl">
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
                                class="w-full text-left px-4 py-3 rounded-xl text-sm transition-all"
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
            this._showResults(r);
        } catch(e) { main.innerHTML=this._error('Submit failed',e.message); }
    },

    _showResults(result) {
        const main=document.getElementById('ac-main');
        const passClr=result.passed?'#34d399':'#f87171';
        const passMsg=result.passed?'🎉 Passed!':'Keep studying — you\'ll get it!';
        const breakdown=result.results.map((r,i)=>`
            <div class="flex items-start gap-3 py-2.5 border-b" style="border-color:#1f2937;">
                <i class="fas ${r.is_correct?'fa-check-circle text-green-400':'fa-times-circle text-red-400'} mt-0.5 flex-shrink-0"></i>
                <div class="flex-1 text-sm">
                    <span class="text-gray-400">Q${i+1}</span>
                    ${!r.is_correct?`<div class="text-gray-500 text-xs mt-0.5">Correct: <strong class="text-gray-300">${_es(r.correct_answer)}</strong> — ${_es(r.explanation)}</div>`:''}
                </div>
            </div>`).join('');

        main.innerHTML=`<div class="max-w-xl">
            <div class="pw-card mb-4" style="border-top:3px solid ${passClr};">
                <div class="pw-card-body text-center" style="padding:2rem;">
                    <div class="text-5xl font-black mb-2" style="color:${passClr};">${result.score}%</div>
                    <div class="font-semibold text-white text-lg">${passMsg}</div>
                    <div class="text-gray-500 text-sm mt-1">${result.correct} of ${result.total} correct</div>
                </div>
            </div>
            ${result.mentor_feedback?`
            <div class="pw-card mb-4" style="border-left:3px solid #a78bfa;">
                <div class="pw-card-body">
                    <div class="flex items-center gap-2 mb-2">
                        <i class="fas fa-robot" style="color:#a78bfa;"></i>
                        <strong class="text-white text-sm">Mentor Feedback</strong>
                    </div>
                    <p class="text-gray-300 text-sm leading-relaxed">${_es(result.mentor_feedback)}</p>
                </div>
            </div>`:''}
            <div class="pw-card mb-4">
                <div class="pw-card-hdr"><h3 class="card-title">Answer Breakdown</h3></div>
                <div class="pw-card-body" style="padding-top:0;">${breakdown}</div>
            </div>
            <div class="flex gap-2 flex-wrap">
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

    /* ── AI Mentor Banner ───────────────────────────────────────────────── */
    async _loadMentorBanner() {
        if (!this._uid) return;
        const banner = document.getElementById('ac-mentor-banner');
        if (!banner) return;
        try {
            const g = await API.lms.getMentorGuide(this._uid);
            banner.innerHTML=`<div class="pw-card mb-5" style="border-left:3px solid #a78bfa;background:linear-gradient(135deg,#0f0a1f,#1a0a2e);">
                <div class="pw-card-body"><div class="flex items-start gap-3">
                    <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style="background:rgba(219,39,119,.2);">
                        <i class="fas fa-robot" style="color:#f472b6;"></i>
                    </div>
                    <div class="flex-1">
                        <div class="text-xs font-semibold mb-1" style="color:#a78bfa;">AI MENTOR</div>
                        <p class="text-gray-300 text-sm leading-relaxed">${_es(g.message)}</p>
                        ${g.next_lesson?`<button class="btn btn-primary mt-3 text-xs" style="font-size:.78rem;padding:.35rem .85rem;"
                                onclick="AcademyPage._openLesson(${g.next_lesson.id},'${_es(g.next_lesson.title)}')">
                            Continue: ${_es(g.next_lesson.title)} →
                        </button>`:''}
                    </div>
                </div></div>
            </div>`;
        } catch(_) { banner.innerHTML=''; }
    },

    /* ── Breadcrumb ─────────────────────────────────────────────────────── */
    _bc(level, module, lesson) {
        const el=document.getElementById('ac-breadcrumb');
        if(!el) return;
        if(!level){el.style.display='none';el.innerHTML='';return;}
        el.style.display='flex';
        el.innerHTML=
            `<a href="#" onclick="AcademyPage._showLevelSelector();return false;" class="text-purple-400">Academy</a>`+
            (level?`<span class="pw-breadcrumb-sep">›</span><a href="#" onclick="AcademyPage._selectLevel(${this._level?.id},'${_es(level)}');return false;" class="text-purple-400">${_es(level)}</a>`:'')+
            (module?`<span class="pw-breadcrumb-sep">›</span><a href="#" onclick="AcademyPage._selectModule(${this._module?.id},'${_es(module)}');return false;" class="text-purple-400">${_es(module)}</a>`:'')+
            (lesson?`<span class="pw-breadcrumb-sep">›</span><span class="text-gray-400">${_es(lesson)}</span>`:'');
    },

    /* ── Helpers ────────────────────────────────────────────────────────── */
    _getUser() { try{return JSON.parse(localStorage.getItem('pipways_user')||'{}');}catch(_){return{};} },
    _loading: m=>`<div class="loading"><div class="spinner"></div><p class="text-gray-500 text-sm">${m}</p></div>`,
    _aiLoading: m=>`<div class="pw-card" style="border-left:3px solid #374151;"><div class="pw-card-body loading"><div class="spinner"></div><p class="text-gray-500 text-sm">${m}</p></div></div>`,
    _error: (t,d)=>`<div class="alert alert-error"><i class="fas fa-exclamation-circle mr-2"></i><strong>${_es(t)}</strong> — ${_es(d||'')}</div>`,
    _setBtn(id, loading, html) {
        const b=document.getElementById(id); if(!b)return;
        b.disabled=loading; b.innerHTML=loading?'<i class="fas fa-spinner fa-spin mr-2"></i>Loading…':html;
    },
    _md(text) {
        if(!text) return '';
        const s=text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
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
};

window.AcademyPage = AcademyPage;

/* ── Styles ─────────────────────────────────────────────────────────────── */
(function(){
    if(document.getElementById('ac-styles')) return;
    const s=document.createElement('style'); s.id='ac-styles';
    s.textContent=`
        .ac-lesson-text{color:#d1d5db;font-size:.9rem;line-height:1.75;}
        .ac-lesson-text .ac-p{margin:.75rem 0;}
        .ac-h3{font-size:1rem;font-weight:600;color:white;margin:1.5rem 0 .5rem;}
        .ac-h4{font-size:.95rem;font-weight:600;color:#d1d5db;margin:1.25rem 0 .4rem;}
        .ac-ul{margin:.5rem 0 .5rem 1.25rem;list-style:disc;}
        .ac-li{margin:.2rem 0;}
        .ac-code{display:block;background:#111827;border:1px solid #1f2937;border-radius:.5rem;padding:1rem;font-size:.8rem;font-family:monospace;color:#a78bfa;overflow-x:auto;margin:.75rem 0;}
        .ac-inline-code{background:#111827;border:1px solid #1f2937;border-radius:.3rem;padding:.1rem .4rem;font-size:.8em;font-family:monospace;color:#fbbf24;}
        .ac-chart-opt:not(:disabled):hover{border-color:#7c3aed!important;background:rgba(124,58,237,.08)!important;color:#c4b5fd!important;}
    `;
    document.head.appendChild(s);
})();

/* ── Safe HTML escape ───────────────────────────────────────────────────── */
function _es(str){
    return String(str||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

/*
 ═══════════════════════════════════════════════════════════════════════════
  INTEGRATION — add these 4 small pieces to dashboard.html
 ═══════════════════════════════════════════════════════════════════════════

 1. SIDEBAR NAV (inside the LEARNING nav-section-label block):
    <a href="#" data-section="academy" class="nav-link">
        <i class="fas fa-graduation-cap nav-icon" style="color:#34d399;"></i>
        <span>Trading Academy</span>
    </a>

 2. SECTION HTML (alongside the other <section> blocks):
    <section id="section-academy" class="section hidden">
        <div id="academy-container"></div>
    </section>

 3. loadSectionData switch (add case):
        case 'academy':
            if (typeof AcademyPage !== 'undefined') await AcademyPage.render();
            break;

    navigate() meta map (add entry):
        'academy': { title: 'Trading Academy', sub: 'Structured lessons from beginner to advanced' },

 4. SCRIPT TAG (at the bottom, after other module scripts):
    <script src="/js/modules/academy.js"></script>

 ── Backend integration ──────────────────────────────────────────────────
 main.py — add two lines:
    from . import learning
    app.include_router(learning.router, prefix="/learning", tags=["Learning"])

 File placement:
    lms_init.py  →  backend package directory (same as main.py)
    learning.py  →  backend package directory
    academy.js   →  frontend/js/modules/
 ═══════════════════════════════════════════════════════════════════════════
*/
