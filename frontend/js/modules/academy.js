/**
 * Pipways Trading Academy — Frontend Controller v5.0
 * Drop-in replacement for academy.js
 * Features: Redesigned hero, enhanced cards, quiz engine, badge toasts, AI panel, mobile nav
 */

/* ── LMS API Extension ────────────────────────────────────────────────────── */
(function extendAPI() {
    const A = window.API;
    if (!A || A._academyReady) return;
    A._academyReady = true;
    A.lms = {
        getLevels:         ()      => A.request('/learning/levels'),
        getModules:        (lid)   => A.request(`/learning/modules/${lid}`),
        getLessons:        (mid)   => A.request(`/learning/lessons/${mid}`),
        getLesson:         (lid)   => A.request(`/learning/lesson/${lid}`),
        getQuiz:           (lid)   => A.request(`/learning/quiz/${lid}`),
        getProgress:       (uid)   => A.request(`/learning/progress/${uid}`),
        getBadges:         (uid)   => A.request(`/learning/badges/${uid}`),
        checkBadges:       ()      => A.request('/learning/badges/check', { method: 'POST' }),
        getMentorGuide:    (uid)   => A.request(`/learning/mentor/guide/${uid}`),
        getMentorTeach:    (lid)   => A.request(`/learning/mentor/teach?lesson_id=${lid}`,    { method: 'POST' }),
        getMentorPractice: (lid)   => A.request(`/learning/mentor/practice?lesson_id=${lid}`, { method: 'POST' }),
        getChartPractice:  (lid)   => A.request(`/learning/mentor/chart-practice?lesson_id=${lid}`, { method: 'POST' }),
        markFirstVisit:    ()      => A.request('/learning/profile/first-visit-complete', { method: 'POST' }),
        submitQuiz:        (lid, answers) => A.request('/learning/quiz/submit', {
            method: 'POST', body: JSON.stringify({ lesson_id: lid, answers })
        }),
        completeLesson: (lid, score) => A.request('/learning/lesson/complete', {
            method: 'POST', body: JSON.stringify({ lesson_id: lid, quiz_score: score || 0 })
        }),
    };
})();

/* ── Marked.js loader ─────────────────────────────────────────────────────── */
(function loadMarked() {
    if (window.marked) return;
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
    s.async = true;
    document.head.appendChild(s);
})();

/* ══════════════════════════════════════════════════════════════════════════════
   ACADEMY PAGE CONTROLLER v5.0
══════════════════════════════════════════════════════════════════════════════ */
const AcademyPage = {
    /* state */
    _uid:        null,
    _level:      null,
    _module:     null,
    _lesson:     null,
    _quiz:       null,
    _badges:     [],
    _progress:   null,  // cached overall progress
    _lessonNav:  { prev: null, next: null },

    /* ── Entry point ──────────────────────────────────────────────────────── */
    async render() {
        const u = this._getUser();
        this._uid = u?.id ?? null;

        /* Kick off badge check in background */
        if (this._uid) {
            this._loadBadgesAndUpdateHero();
        }

        await this._showLevelSelector();
    },

    /* ── LEVEL SELECTOR ────────────────────────────────────────────────────── */
    async _showLevelSelector() {
        this._level = this._module = this._lesson = null;
        this._bc(null, null, null);
        this._hideMobileBar();

        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading curriculum…');

        try {
            const [levels, prog, guide] = await Promise.all([
                API.lms.getLevels(),
                this._uid ? API.lms.getProgress(this._uid).catch(() => null) : null,
                this._uid ? API.lms.getMentorGuide(this._uid).catch(() => null) : null,
            ]);

            if (this._uid && guide) this._renderCoachBanner(guide);

            const sm = {};
            (prog?.summary || []).forEach(s => sm[s.level_id] = s);

            /* Update hero ring if we have overall progress */
            if (prog) {
                const total     = prog.total_lessons || 0;
                const completed = prog.completed_lessons || 0;
                const pct       = total ? Math.round(completed / total * 100) : 0;
                this._setHeroRing(pct);
            }

            if (!levels || !levels.length) {
                main.innerHTML = this._emptyState(
                    'Curriculum loading…',
                    'The Trading Academy is being set up. Please refresh in a moment or contact support.'
                );
                return;
            }

            const palette = [
                { color: '#34d399', bg: 'rgba(52,211,153,.12)',  icon: 'fa-seedling',    gradient: '#34d399,#10b981' },
                { color: '#60a5fa', bg: 'rgba(96,165,250,.12)',  icon: 'fa-chart-line',  gradient: '#60a5fa,#3b82f6' },
                { color: '#f59e0b', bg: 'rgba(245,158,11,.12)',  icon: 'fa-trophy',      gradient: '#f59e0b,#d97706' },
            ];

            main.innerHTML = `
                <div class="ac-level-grid">
                    ${levels.map((lv, i) => {
                        const p  = palette[i % 3];
                        const s  = sm[lv.id];
                        const pct  = s ? s.percent : 0;
                        const done = s ? s.completed : 0;
                        const tot  = s ? s.total : 0;
                        const full = pct >= 100;

                        return `
                        <div class="ac-level-card"
                             style="border-top:0;"
                             onclick="AcademyPage._selectLevel(${lv.id}, '${_es(lv.name)}')">
                            <div class="ac-level-card-top" style="background:linear-gradient(90deg,${p.gradient});"></div>
                            <div class="ac-level-card-body">
                                ${full ? `<div class="ac-level-done-badge"><i class="fas fa-check"></i></div>` : ''}
                                <div class="ac-level-icon" style="background:${p.bg};">
                                    <i class="fas ${p.icon}" style="color:${p.color};"></i>
                                </div>
                                <div class="ac-level-tag" style="color:${p.color};">${_es(lv.name)}</div>
                                <div class="ac-level-name">${_es(lv.name)}</div>
                                <div class="ac-level-desc">${_es(lv.description)}</div>

                                <div style="display:flex;justify-content:space-between;font-size:.72rem;color:#6b7280;margin-bottom:.35rem;">
                                    <span>Progress</span>
                                    <span style="color:${p.color};font-weight:700;">${pct}%</span>
                                </div>
                                <div class="pw-progress-bar">
                                    <div class="pw-progress-fill ${pct >= 80 && !full ? 'near-done' : ''}"
                                         style="width:${pct}%;background:linear-gradient(90deg,${p.gradient});"></div>
                                </div>
                                <div class="ac-level-footer">
                                    <span style="font-size:.7rem;color:#4b5563;">${done} / ${tot} lessons</span>
                                    <span style="font-size:.72rem;color:${p.color};">
                                        ${full ? '<i class="fas fa-check-circle mr-1"></i>Complete' : 'Open →'}
                                    </span>
                                </div>
                            </div>
                        </div>`;
                    }).join('')}
                </div>`;

        } catch (e) {
            main.innerHTML = this._error('Could not load Academy', e.message);
        }
    },

    /* ── MODULE LIST ──────────────────────────────────────────────────────── */
    async _selectLevel(levelId, levelName) {
        this._level = { id: levelId, name: levelName };
        this._module = null;
        this._bc(levelName, null, null);
        this._hideMobileBar();

        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading modules…');

        try {
            const modules = await API.lms.getModules(levelId);

            main.innerHTML = `<div class="ac-module-grid">
                ${modules.map(m => {
                    const pct  = m.lesson_count ? Math.round(m.completed_count / m.lesson_count * 100) : 0;
                    const full = m.is_complete;

                    return `
                    <div class="ac-module-card ${full ? 'complete' : ''}"
                         onclick="AcademyPage._selectModule(${m.id}, '${_es(m.title)}')">
                        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:.5rem;">
                            <div style="flex:1;min-width:0;">
                                ${full
                                    ? `<span class="badge badge-success text-xs mb-1.5"><i class="fas fa-check-circle mr-1"></i>Complete</span>`
                                    : `<span style="font-size:.7rem;color:#6b7280;" class="block mb-1">${m.completed_count}/${m.lesson_count} lessons</span>`
                                }
                                <div style="font-size:.95rem;font-weight:700;color:white;">${_es(m.title)}</div>
                            </div>
                            <i class="fas fa-chevron-right text-gray-700 text-xs mt-1 flex-shrink-0"></i>
                        </div>
                        <p style="font-size:.78rem;color:#6b7280;line-height:1.5;">${_es(m.description)}</p>
                        <div>
                            <div style="display:flex;justify-content:space-between;font-size:.7rem;color:#4b5563;margin-bottom:.3rem;">
                                <span>Module progress</span>
                                <span style="color:${pct >= 100 ? '#34d399' : '#a78bfa'};font-weight:600;">${pct}%</span>
                            </div>
                            <div class="pw-progress-bar">
                                <div class="pw-progress-fill ${pct >= 80 && pct < 100 ? 'near-done' : ''}"
                                     style="width:${pct}%;${pct >= 100 ? 'background:#10b981;' : ''}"></div>
                            </div>
                            ${full ? `<div style="font-size:.7rem;color:#10b981;margin-top:.4rem;"><i class="fas fa-medal mr-1"></i>Module Complete</div>` : ''}
                        </div>
                    </div>`;
                }).join('')}
            </div>`;

        } catch (e) {
            main.innerHTML = this._error('Could not load modules', e.message);
        }
    },

    /* ── LESSON LIST ──────────────────────────────────────────────────────── */
    async _selectModule(moduleId, moduleTitle) {
        this._module = { id: moduleId, name: moduleTitle };
        this._lesson = null;
        this._bc(this._level?.name, moduleTitle, null);
        this._hideMobileBar();

        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading lessons…');

        try {
            const lessons = await API.lms.getLessons(moduleId);

            main.innerHTML = `
                <div class="mb-4" style="max-width:680px;">
                    <div style="font-size:.78rem;color:#6b7280;margin-bottom:.85rem;">
                        ${lessons.filter(l => l.completed).length} of ${lessons.length} lessons completed
                    </div>
                    <div class="ac-lesson-list">
                        ${lessons.map((l, i) => {
                            const locked = !l.unlocked;
                            const done   = l.completed;
                            const scoreTag = (done && l.quiz_score !== null)
                                ? `<span style="font-size:.7rem;font-weight:700;color:#34d399;margin-left:auto;padding:.15rem .5rem;background:rgba(52,211,153,.12);border-radius:9999px;">${l.quiz_score}%</span>`
                                : '';

                            return `
                            <div class="ac-lesson-row ${locked ? 'locked' : ''} ${done ? 'done' : ''}"
                                 ${!locked ? `onclick="AcademyPage._openLesson(${l.id}, '${_es(l.title)}')"` : ''}>
                                <div class="ac-lesson-num">
                                    ${done  ? '<i class="fas fa-check" style="font-size:.65rem;"></i>'
                                    : locked ? '<i class="fas fa-lock" style="font-size:.6rem;"></i>'
                                             : String(i + 1)}
                                </div>
                                <div style="flex:1;min-width:0;">
                                    <div style="font-size:.875rem;font-weight:600;color:${done ? '#6b7280' : 'white'};${done ? 'text-decoration:line-through;' : ''}">
                                        Lesson ${i + 1}: ${_es(l.title)}
                                    </div>
                                    ${locked ? `<div style="font-size:.7rem;color:#4b5563;margin-top:.15rem;">Complete previous lesson to unlock</div>` : ''}
                                </div>
                                ${scoreTag}
                                ${!locked ? `<i class="fas fa-chevron-right" style="font-size:.75rem;color:#374151;flex-shrink:0;"></i>` : ''}
                            </div>`;
                        }).join('')}
                    </div>
                </div>`;

        } catch (e) {
            main.innerHTML = this._error('Could not load lessons', e.message);
        }
    },

    /* ── LESSON VIEW ──────────────────────────────────────────────────────── */
    async _openLesson(lessonId, lessonTitle) {
        this._lesson = { id: lessonId, name: lessonTitle };
        this._bc(this._level?.name, this._module?.name, lessonTitle);

        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading lesson…');

        try {
            const lesson = await API.lms.getLesson(lessonId);

            /* Wait for marked.js */
            if (typeof marked === 'undefined') {
                await new Promise(resolve => {
                    const t = setInterval(() => { if (typeof marked !== 'undefined') { clearInterval(t); resolve(); } }, 100);
                    setTimeout(() => { clearInterval(t); resolve(); }, 2500);
                });
            }

            const html = this._processContent(lesson.content);
            this._lessonNav = { prev: lesson.prev_lesson || null, next: lesson.next_lesson || null };
            this._renderMobileBar(lesson);

            main.innerHTML = `
                <div class="ac-lesson-container">

                    <!-- Lesson card -->
                    <div class="mb-1">
                        <div class="ac-lesson-header-band"></div>
                        <div class="ac-lesson-content">
                            <div class="ac-lesson-meta">
                                ${_es(lesson.level_name)} &rsaquo; ${_es(lesson.module_title)}
                            </div>
                            <h2 class="ac-lesson-title">${_es(lesson.title)}</h2>
                            <div class="ac-lesson-text mt-4">${html}</div>
                        </div>
                    </div>

                    <!-- Action bar -->
                    <div class="ac-action-bar">
                        <button class="ac-action-btn ac-action-btn-primary"
                                onclick="AcademyPage._startQuiz(${lessonId})">
                            <i class="fas fa-pencil-alt"></i> Take Quiz
                        </button>
                        <button id="ac-btn-coach" class="ac-action-btn ac-action-btn-ghost"
                                onclick="AcademyPage._showCoach(${lessonId})">
                            <i class="fas fa-chalkboard-teacher" style="color:#a78bfa;"></i> Trading Coach
                        </button>
                        <button id="ac-btn-practice" class="ac-action-btn ac-action-btn-ghost"
                                onclick="AcademyPage._showPractice(${lessonId})">
                            <i class="fas fa-dumbbell" style="color:#fbbf24;"></i> Practice
                        </button>
                        <button id="ac-btn-chart" class="ac-action-btn ac-action-btn-ghost"
                                onclick="AcademyPage._showChart(${lessonId})">
                            <i class="fas fa-chart-bar" style="color:#60a5fa;"></i> Chart Exercise
                        </button>
                    </div>

                    <!-- AI output panel -->
                    <div id="ac-ai-panel" style="display:none;"></div>

                    <!-- Desktop lesson navigation -->
                    <div class="hidden md:flex justify-between items-center py-4 border-t mt-2"
                         style="border-color:#1f2937;">
                        ${lesson.prev_lesson
                            ? `<button onclick="AcademyPage._openLesson(${lesson.prev_lesson.id}, '${_es(lesson.prev_lesson.title)}')"
                                       style="font-size:.82rem;color:#9ca3af;display:flex;align-items:center;gap:.4rem;cursor:pointer;background:none;border:none;padding:0;">
                                   <i class="fas fa-arrow-left"></i> ${_es(lesson.prev_lesson.title)}
                               </button>`
                            : `<span></span>`}
                        ${lesson.next_lesson
                            ? `<button onclick="AcademyPage._openLesson(${lesson.next_lesson.id}, '${_es(lesson.next_lesson.title)}')"
                                       style="font-size:.82rem;color:#a78bfa;display:flex;align-items:center;gap:.4rem;cursor:pointer;background:none;border:none;padding:0;">
                                   ${_es(lesson.next_lesson.title)} <i class="fas fa-arrow-right"></i>
                               </button>`
                            : `<span></span>`}
                    </div>

                </div>`;

            setTimeout(() => this._initTradingView(), 150);

        } catch (e) {
            main.innerHTML = this._error('Could not load lesson', e.message);
        }
    },

    /* ── QUIZ ENGINE ──────────────────────────────────────────────────────── */
    async _startQuiz(lessonId) {
        const main = document.getElementById('ac-main');
        main.innerHTML = this._loading('Loading quiz…');
        this._hideMobileBar();

        try {
            const data = await API.lms.getQuiz(lessonId);
            if (!data.questions?.length) {
                main.innerHTML = `<div style="max-width:640px;">
                    <div style="background:rgba(96,165,250,.1);border:1px solid rgba(96,165,250,.3);color:#60a5fa;padding:1.1rem 1.25rem;border-radius:.75rem;font-size:.875rem;">
                        <i class="fas fa-info-circle mr-2"></i>No quiz available for this lesson yet.
                    </div></div>`;
                return;
            }

            this._quiz = { lessonId, questions: data.questions, index: 0, answers: [], selected: null };
            this._renderQuizQuestion();

        } catch (e) {
            main.innerHTML = this._error('Could not load quiz', e.message);
        }
    },

    _renderQuizQuestion() {
        const q    = this._quiz;
        const qn   = q.questions[q.index];
        const tot  = q.questions.length;
        const opts = [
            { key: 'A', text: qn.option_a },
            { key: 'B', text: qn.option_b },
            { key: 'C', text: qn.option_c },
            { key: 'D', text: qn.option_d },
        ].filter(o => o.text);

        const dots = q.questions.map((_, i) => {
            const res = q.answers[i];
            const cls = i < q.index
                ? (res?.correct ? 'correct' : 'wrong')
                : (i === q.index ? 'active' : '');
            return `<div class="ac-quiz-dot ${cls}"></div>`;
        }).join('');

        const main = document.getElementById('ac-main');
        main.innerHTML = `
            <div class="ac-quiz-wrap">
                <div class="ac-quiz-card">
                    <!-- Progress -->
                    <div class="ac-quiz-progress">
                        <div class="ac-quiz-dots">${dots}</div>
                        <span style="font-size:.75rem;color:#6b7280;margin-left:auto;">
                            ${q.index + 1} / ${tot}
                        </span>
                    </div>

                    <!-- Question -->
                    <div class="ac-quiz-q">${_es(qn.question)}</div>

                    <!-- Options -->
                    <div class="ac-quiz-opts" id="ac-quiz-opts">
                        ${opts.map(o => `
                            <button class="ac-quiz-opt" id="ac-opt-${o.key}"
                                    onclick="AcademyPage._selectOpt('${o.key}')">
                                <div class="ac-quiz-opt-letter">${o.key}</div>
                                <span>${_es(o.text)}</span>
                            </button>`).join('')}
                    </div>

                    <!-- Confirm button -->
                    <div id="ac-quiz-confirm" style="margin-top:1.25rem;display:none;">
                        <button class="ac-action-btn ac-action-btn-primary w-full justify-center"
                                style="width:100%;"
                                onclick="AcademyPage._confirmAnswer()">
                            Confirm Answer →
                        </button>
                    </div>

                    <!-- Explanation panel -->
                    <div id="ac-quiz-explain" style="display:none;margin-top:1.25rem;"></div>
                </div>

                <!-- Back to lesson -->
                <button onclick="AcademyPage._openLesson(${q.lessonId}, '${_es(this._lesson?.name || '')}')"
                        style="font-size:.8rem;color:#6b7280;display:flex;align-items:center;gap:.4rem;background:none;border:none;cursor:pointer;padding:.5rem 0;">
                    <i class="fas fa-arrow-left"></i> Back to lesson
                </button>
            </div>`;
    },

    _selectOpt(key) {
        this._quiz.selected = key;
        document.querySelectorAll('.ac-quiz-opt').forEach(b => b.classList.remove('selected'));
        const btn = document.getElementById(`ac-opt-${key}`);
        if (btn) btn.classList.add('selected');
        document.getElementById('ac-quiz-confirm').style.display = '';
    },

    _confirmAnswer() {
        const q  = this._quiz;
        const qn = q.questions[q.index];
        if (!q.selected) return;

        const correct = q.selected === qn.correct_answer;
        q.answers.push({ question_id: qn.id, selected_answer: q.selected, correct });

        /* Style buttons */
        document.querySelectorAll('.ac-quiz-opt').forEach(btn => {
            btn.disabled = true;
            const letter = btn.id.replace('ac-opt-', '');
            if (letter === qn.correct_answer) btn.classList.add('correct');
            else if (letter === q.selected)   btn.classList.add('wrong');
        });
        document.getElementById('ac-quiz-confirm').style.display = 'none';

        /* Explanation */
        const exDiv = document.getElementById('ac-quiz-explain');
        exDiv.style.display = '';
        exDiv.innerHTML = `
            <div style="padding:1rem;border-radius:.65rem;
                 background:${correct ? 'rgba(16,185,129,.08)' : 'rgba(239,68,68,.08)'};
                 border:1px solid ${correct ? 'rgba(52,211,153,.3)' : 'rgba(239,68,68,.3)'};">
                <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.5rem;">
                    <i class="fas ${correct ? 'fa-check-circle' : 'fa-times-circle'}"
                       style="color:${correct ? '#34d399' : '#f87171'};"></i>
                    <strong style="color:${correct ? '#34d399' : '#f87171'};">
                        ${correct ? 'Correct!' : 'Incorrect'}
                    </strong>
                </div>
                <p style="font-size:.82rem;color:#9ca3af;margin:0;">${_es(qn.explanation || '')}</p>
                <button onclick="AcademyPage._nextQuestion()"
                        class="ac-action-btn ac-action-btn-primary"
                        style="margin-top:.9rem;font-size:.8rem;">
                    ${q.index + 1 < q.questions.length ? 'Next Question →' : 'View Results →'}
                </button>
            </div>`;
    },

    _nextQuestion() {
        const q = this._quiz;
        q.index++;
        q.selected = null;
        if (q.index < q.questions.length) {
            this._renderQuizQuestion();
        } else {
            this._showResults();
        }
    },

    async _showResults() {
        const q      = this._quiz;
        const total  = q.questions.length;
        const correct= q.answers.filter(a => a.correct).length;
        const pct    = Math.round(correct / total * 100);
        const passed = pct >= 70;

        /* Submit to backend */
        try {
            const payload = q.answers.map(a => ({ question_id: a.question_id, selected_answer: a.selected_answer }));
            await API.lms.submitQuiz(q.lessonId, payload);
            await API.lms.completeLesson(q.lessonId, pct);

            /* Check for new badges */
            if (this._uid) {
                const check = await API.lms.checkBadges().catch(() => null);
                if (check?.newly_awarded?.length) this._showBadgeToasts(check.newly_awarded);
            }
        } catch (e) { /* non-fatal */ }

        const circumference = 2 * Math.PI * 45;
        const offset = circumference - (pct / 100) * circumference;
        const color  = pct >= 80 ? '#34d399' : pct >= 70 ? '#fbbf24' : '#f87171';
        const grade  = pct >= 90 ? 'A+' : pct >= 80 ? 'A' : pct >= 70 ? 'B' : pct >= 60 ? 'C' : 'F';

        document.getElementById('ac-main').innerHTML = `
            <div class="ac-quiz-wrap">
                <div class="ac-quiz-card" style="text-align:center;">
                    <!-- Ring -->
                    <div class="ac-result-ring">
                        <svg class="ac-result-ring-svg" width="110" height="110" viewBox="0 0 110 110">
                            <circle cx="55" cy="55" r="45" fill="none" stroke="#1f2937" stroke-width="8"/>
                            <circle cx="55" cy="55" r="45" fill="none"
                                    stroke="${color}" stroke-width="8"
                                    stroke-linecap="round"
                                    stroke-dasharray="${circumference}"
                                    stroke-dashoffset="${offset}"
                                    style="transition:stroke-dashoffset 1s ease;"/>
                        </svg>
                        <div class="ac-result-grade">
                            <span class="ac-result-pct" style="color:${color};">${grade}</span>
                            <span class="ac-result-lbl">${pct}%</span>
                        </div>
                    </div>

                    <h3 style="font-size:1.2rem;font-weight:800;color:white;margin-bottom:.4rem;">
                        ${passed ? '🎉 Quiz Passed!' : 'Keep Practising'}
                    </h3>
                    <p style="font-size:.85rem;color:#6b7280;margin-bottom:1.5rem;">
                        ${correct} of ${total} correct · ${pct}% score
                    </p>

                    <!-- Score breakdown dots -->
                    <div style="display:flex;justify-content:center;gap:.5rem;margin-bottom:1.5rem;">
                        ${q.answers.map(a => `
                            <div style="width:10px;height:10px;border-radius:50%;
                                 background:${a.correct ? '#34d399' : '#ef4444'};"></div>`).join('')}
                    </div>

                    <div style="display:flex;flex-wrap:wrap;gap:.6rem;justify-content:center;">
                        <button class="ac-action-btn ac-action-btn-primary"
                                onclick="AcademyPage._openLesson(${q.lessonId}, '${_es(this._lesson?.name || '')}')">
                            <i class="fas fa-book-open"></i> Back to Lesson
                        </button>
                        ${this._lessonNav.next ? `
                            <button class="ac-action-btn ac-action-btn-ghost"
                                    onclick="AcademyPage._openLesson(${this._lessonNav.next.id}, '${_es(this._lessonNav.next.title)}')">
                                Next Lesson <i class="fas fa-arrow-right"></i>
                            </button>` : ''}
                        <button class="ac-action-btn ac-action-btn-ghost"
                                onclick="AcademyPage._startQuiz(${q.lessonId})">
                            <i class="fas fa-redo"></i> Retry Quiz
                        </button>
                    </div>
                </div>
            </div>`;
    },

    /* ── AI PANELS ────────────────────────────────────────────────────────── */
    async _showCoach(lessonId) {
        this._openAIPanel('Trading Coach', 'fa-chalkboard-teacher', '#a78bfa');
        try {
            const r = await API.lms.getMentorTeach(lessonId);
            this._fillAIPanel(r.explanation || r.message || r);
        } catch (e) { this._fillAIPanel('Coach unavailable — please try again.'); }
    },

    async _showPractice(lessonId) {
        this._openAIPanel('Practice Scenario', 'fa-dumbbell', '#fbbf24');
        try {
            const r = await API.lms.getMentorPractice(lessonId);
            this._fillAIPanel(r.practice || r.message || r);
        } catch (e) { this._fillAIPanel('Practice module unavailable — please try again.'); }
    },

    async _showChart(lessonId) {
        this._openAIPanel('Chart Exercise', 'fa-chart-bar', '#60a5fa');
        try {
            const r = await API.lms.getChartPractice(lessonId);
            if (r.question && r.options) {
                this._fillChartExercise(r);
            } else {
                this._fillAIPanel(r.explanation || r.message || r);
            }
        } catch (e) { this._fillAIPanel('Chart exercise unavailable — please try again.'); }
    },

    _openAIPanel(title, icon, color) {
        const p = document.getElementById('ac-ai-panel');
        if (!p) return;
        p.style.display = '';
        p.innerHTML = `
            <div class="ac-ai-panel">
                <div class="ac-ai-panel-header">
                    <div class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                         style="background:${color}20;">
                        <i class="fas ${icon}" style="color:${color};font-size:.82rem;"></i>
                    </div>
                    <span style="font-size:.85rem;font-weight:600;color:white;">${title}</span>
                    <div class="ac-ai-dot" style="margin-left:.25rem;"></div>
                </div>
                <div id="ac-ai-content">
                    <div class="ac-ai-typing">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>`;
        p.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    },

    _fillAIPanel(text) {
        const el = document.getElementById('ac-ai-content');
        if (!el) return;
        const safe = typeof text === 'string' ? text : JSON.stringify(text);
        el.innerHTML = `<div class="ac-ai-content">${_es(safe)}</div>`;
    },

    _fillChartExercise(data) {
        const el = document.getElementById('ac-ai-content');
        if (!el) return;
        const opts = (data.options || []);
        el.innerHTML = `
            <p style="font-size:.875rem;color:#d1d5db;font-weight:600;margin-bottom:.85rem;">${_es(data.question)}</p>
            <div style="display:flex;flex-direction:column;gap:.4rem;" id="ac-chart-opts">
                ${opts.map((o, i) => `
                    <button id="ac-copt-${i}" class="ac-quiz-opt"
                            onclick="AcademyPage._answerChart(${i},'${_es(data.correct)}','${_es(data.explanation || '')}')">
                        <div class="ac-quiz-opt-letter">${String.fromCharCode(65+i)}</div>
                        <span>${_es(o)}</span>
                    </button>`).join('')}
            </div>
            <div id="ac-chart-result" style="display:none;margin-top:1rem;"></div>`;
    },

    _answerChart(idx, correct, explanation) {
        document.querySelectorAll('#ac-chart-opts .ac-quiz-opt').forEach((btn, i) => {
            btn.disabled = true;
            const letter = String.fromCharCode(65 + i);
            if (letter === correct.toUpperCase())   { btn.classList.add('correct'); }
            else if (i === idx)                     { btn.classList.add('wrong'); }
        });
        const chosen  = String.fromCharCode(65 + idx);
        const passed  = chosen === correct.toUpperCase();
        const result  = document.getElementById('ac-chart-result');
        result.style.display = '';
        result.innerHTML = `
            <div style="padding:.85rem 1rem;border-radius:.65rem;
                 background:${passed ? 'rgba(16,185,129,.08)' : 'rgba(239,68,68,.08)'};
                 border:1px solid ${passed ? 'rgba(52,211,153,.3)' : 'rgba(239,68,68,.3)'};">
                <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.4rem;">
                    <i class="fas ${passed ? 'fa-check-circle' : 'fa-times-circle'}"
                       style="color:${passed ? '#34d399' : '#f87171'};"></i>
                    <strong style="color:${passed ? '#34d399' : '#f87171'};">${passed ? 'Correct!' : 'Incorrect'}</strong>
                </div>
                <p style="font-size:.82rem;color:#9ca3af;margin:0;">${_es(explanation)}</p>
            </div>`;
    },

    /* ── BADGE SYSTEM ─────────────────────────────────────────────────────── */
    async _loadBadgesAndUpdateHero() {
        if (!this._uid) return;
        try {
            const data = await API.lms.getBadges(this._uid);
            this._badges = data.badges || [];
            this._renderHeroBadges();

            const check = await API.lms.checkBadges().catch(() => null);
            if (check?.newly_awarded?.length) this._showBadgeToasts(check.newly_awarded);
        } catch (e) { /* non-fatal */ }
    },

    _badgeDefs: {
        beginner_trader:   { name: 'Beginner Trader',   icon: 'fa-seedling',    color: '#34d399' },
        technical_analyst: { name: 'Technical Analyst', icon: 'fa-chart-line',  color: '#60a5fa' },
        strategy_builder:  { name: 'Strategy Builder',  icon: 'fa-chess-knight',color: '#a78bfa' },
        pipways_certified: { name: 'Pipways Certified', icon: 'fa-certificate', color: '#f59e0b' },
        quiz_master:       { name: 'Quiz Master',       icon: 'fa-brain',       color: '#f472b6' },
        perfect_score:     { name: 'Perfect Score',     icon: 'fa-star',        color: '#fbbf24' },
        risk_manager:      { name: 'Risk Manager',      icon: 'fa-shield-alt',  color: '#22d3ee' },
        psychology_pro:    { name: 'Psychology Pro',    icon: 'fa-cogs',        color: '#e879f9' },
    },

    _renderHeroBadges() {
        const el = document.getElementById('ac-badge-mini');
        if (!el || !this._badges.length) return;
        el.innerHTML = this._badges.slice(0, 4).map(b => {
            const d = this._badgeDefs[b.badge_type] || { icon: 'fa-medal', color: '#a78bfa' };
            return `<div style="width:24px;height:24px;border-radius:50%;
                         background:${d.color}20;border:1px solid ${d.color}40;
                         display:flex;align-items:center;justify-content:center;"
                         title="${_es(d.name || b.badge_type)}">
                         <i class="fas ${d.icon}" style="font-size:.6rem;color:${d.color};"></i>
                    </div>`;
        }).join('');
        document.getElementById('ac-hero-ring')?.classList.remove('hidden');
    },

    _showBadgeToasts(types) {
        const stack = document.getElementById('ac-toast-stack');
        if (!stack) return;
        types.forEach((type, i) => {
            const d = this._badgeDefs[type] || { name: type, icon: 'fa-medal', color: '#a78bfa' };
            const el = document.createElement('div');
            el.className = 'ac-toast-badge';
            el.style.animationDelay = `${i * 0.25}s`;
            el.innerHTML = `
                <div style="width:38px;height:38px;border-radius:50%;
                     background:${d.color}20;border:1px solid ${d.color}40;
                     display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <i class="fas ${d.icon}" style="color:${d.color};"></i>
                </div>
                <div>
                    <div style="font-size:.68rem;color:#6b7280;text-transform:uppercase;letter-spacing:.06em;">Badge Earned!</div>
                    <div style="font-size:.9rem;font-weight:700;color:${d.color};">${_es(d.name)}</div>
                </div>`;
            stack.appendChild(el);
            setTimeout(() => el.remove(), 5500 + i * 300);
        });
    },

    /* ── HERO RING ────────────────────────────────────────────────────────── */
    _setHeroRing(pct) {
        const ringEl = document.getElementById('ac-hero-ring');
        const fill   = document.getElementById('ac-ring-fill');
        const pctEl  = document.getElementById('ac-ring-pct');
        if (!ringEl || !fill) return;

        ringEl.classList.remove('hidden');
        pctEl.textContent = pct + '%';

        const circumference = 2 * Math.PI * 35;
        fill.style.strokeDasharray  = circumference;
        fill.style.strokeDashoffset = circumference;

        /* Animate */
        requestAnimationFrame(() => {
            setTimeout(() => {
                fill.style.strokeDashoffset = circumference - (pct / 100) * circumference;
            }, 300);
        });
    },

    /* ── MENTOR BANNER ────────────────────────────────────────────────────── */
    _renderCoachBanner(g) {
        const banner = document.getElementById('ac-mentor-banner');
        if (!banner || !g) return;

        const isFirst = g.first_visit;
        banner.innerHTML = `
            <div class="ac-coach-strip" style="border-left:3px solid ${isFirst ? '#34d399' : '#a78bfa'};">
                <div class="ac-coach-icon"
                     style="background:${isFirst ? 'rgba(52,211,153,.15)' : 'rgba(167,139,250,.15)'};">
                    <i class="fas ${isFirst ? 'fa-graduation-cap' : 'fa-chalkboard-teacher'}"
                       style="color:${isFirst ? '#34d399' : '#a78bfa'};"></i>
                </div>
                <div style="flex:1;">
                    <div style="font-size:.68rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
                         color:${isFirst ? '#34d399' : '#a78bfa'};margin-bottom:.35rem;">
                        ${isFirst ? 'Welcome' : 'Trading Coach'}
                    </div>
                    <p style="font-size:.82rem;color:#d1d5db;line-height:1.6;margin:0 0 .6rem;">${_es(g.message || '')}</p>
                    ${g.next_lesson ? `
                        <button class="ac-action-btn ac-action-btn-primary"
                                style="font-size:.78rem;padding:.4rem .9rem;"
                                onclick="AcademyPage.${isFirst ? '_markFirstAndContinue' : '_openLesson'}(${g.next_lesson.id}, '${_es(g.next_lesson.title)}')">
                            ${isFirst ? 'Start Learning' : 'Continue'}: ${_es(g.next_lesson.title)} →
                        </button>` : ''}
                </div>
            </div>`;
    },

    async _markFirstAndContinue(lessonId, lessonTitle) {
        try { await API.lms.markFirstVisit(); } catch (_) {}
        this._openLesson(lessonId, lessonTitle);
    },

    /* ── BREADCRUMB ───────────────────────────────────────────────────────── */
    _bc(level, module_, lesson) {
        const el = document.getElementById('ac-breadcrumb');
        if (!el) return;
        if (!level) { el.style.display = 'none'; el.innerHTML = ''; return; }
        el.style.display = 'flex';

        const sep = `<span class="pw-breadcrumb-sep">›</span>`;
        el.innerHTML = `
            <a href="#" onclick="AcademyPage._showLevelSelector();return false;" style="color:#a78bfa;">Academy</a>
            ${level  ? sep + `<a href="#" onclick="AcademyPage._selectLevel(${this._level?.id||0},'${_es(level)}');return false;" style="color:#a78bfa;">${_es(level)}</a>` : ''}
            ${module_? sep + `<a href="#" onclick="AcademyPage._selectModule(${this._module?.id||0},'${_es(module_)}');return false;" style="color:#a78bfa;">${_es(module_)}</a>` : ''}
            ${lesson ? sep + `<span style="color:#9ca3af;">${_es(lesson)}</span>` : ''}`;
    },

    /* ── MOBILE NAV BAR ───────────────────────────────────────────────────── */
    _renderMobileBar(lesson) {
        const bar = document.getElementById('ac-mobile-bar');
        if (!bar) return;
        bar.style.display = '';

        const prevBtn = document.getElementById('ac-mob-prev');
        const nextBtn = document.getElementById('ac-mob-next');
        if (prevBtn) {
            prevBtn.disabled = !lesson.prev_lesson;
            if (lesson.prev_lesson) {
                prevBtn.onclick = () => this._openLesson(lesson.prev_lesson.id, lesson.prev_lesson.title);
            }
        }
        if (nextBtn) {
            nextBtn.disabled = !lesson.next_lesson;
            if (lesson.next_lesson) {
                nextBtn.onclick = () => this._openLesson(lesson.next_lesson.id, lesson.next_lesson.title);
            }
        }
    },

    _hideMobileBar() {
        const bar = document.getElementById('ac-mobile-bar');
        if (bar) bar.style.display = 'none';
    },

    _mobNav(dir) {
        const nav = this._lessonNav;
        const target = dir === 'prev' ? nav.prev : nav.next;
        if (target) this._openLesson(target.id, target.title);
    },

    /* ── CONTENT PROCESSING ───────────────────────────────────────────────── */
    _processContent(content) {
        if (!content) return '';
        const md = (typeof marked !== 'undefined' && marked.parse)
            ? t => marked.parse(t, { breaks: true, gfm: true })
            : t => t
                .replace(/^## (.+)$/gm,  '<h2 class="ac-h2">$1</h2>')
                .replace(/^### (.+)$/gm, '<h3 class="ac-h3">$1</h3>')
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/^- (.+)$/gm, '<li>$1</li>')
                .replace(/\n\n/g, '</p><p>')
                .replace(/^/, '<p>').replace(/$/, '</p>');

        let html = md(content);

        /* Fix SVG defs order */
        html = html.replace(/<svg([^>]*)>([\s\S]*?)<\/svg>/g, (m, attrs, inner) => {
            const defsMatch = inner.match(/<defs>[\s\S]*?<\/defs>/);
            const defs = defsMatch ? defsMatch[0] : '';
            const rest = inner.replace(/<defs>[\s\S]*?<\/defs>/, '');
            return `<svg${attrs}>${defs}${rest}</svg>`;
        });

        return html;
    },

    /* ── TRADINGVIEW ──────────────────────────────────────────────────────── */
    _initTradingView() {
        document.querySelectorAll('.ac-tradingview-widget').forEach(el => {
            const symbol = el.dataset.symbol || 'FX:EURUSD';
            if (!el.id) el.id = 'tv-' + Math.random().toString(36).substr(2, 8);
            el.style.height = '400px';

            if (window.TradingView) {
                try {
                    new TradingView.widget({
                        container_id: el.id, symbol, interval: '60',
                        timezone: 'Etc/UTC', theme: 'dark', style: '1', locale: 'en',
                        enable_publishing: false, hide_top_toolbar: false,
                        save_image: false, height: 400, width: '100%',
                        studies: ['MACD@tv-basicstudies','MASimple@tv-basicstudies','RSI@tv-basicstudies'],
                    });
                } catch (_) { el.innerHTML = '<p class="text-gray-500 text-sm p-4">Chart unavailable</p>'; }
            } else {
                el.innerHTML = '<p class="text-gray-500 text-sm p-4"><i class="fas fa-spinner fa-spin mr-2"></i>Loading chart…</p>';
                if (!window._tvLoading) {
                    window._tvLoading = true;
                    const s = document.createElement('script');
                    s.src = 'https://s3.tradingview.com/tv.js';
                    s.onload = () => { window._tvLoading = false; this._initTradingView(); };
                    document.head.appendChild(s);
                }
            }
        });
    },

    /* ── HELPERS ──────────────────────────────────────────────────────────── */
    _getUser() {
        try { return JSON.parse(localStorage.getItem('pipways_user') || '{}'); }
        catch (_) { return {}; }
    },

    _loading: msg => `
        <div style="text-align:center;padding:3rem 1rem;">
            <div style="width:40px;height:40px;border:3px solid #1f2937;border-top-color:#7c3aed;
                 border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 1rem;"></div>
            <p style="font-size:.85rem;color:#6b7280;">${msg}</p>
        </div>`,

    _emptyState: (title, sub) => `
        <div style="text-align:center;padding:4rem 1rem;">
            <div style="width:56px;height:56px;border-radius:50%;border:2px dashed #374151;
                 display:flex;align-items:center;justify-content:center;margin:0 auto 1rem;">
                <i class="fas fa-graduation-cap" style="color:#4b5563;"></i>
            </div>
            <div style="font-size:.9rem;font-weight:600;color:#6b7280;margin-bottom:.35rem;">${title}</div>
            <div style="font-size:.78rem;color:#4b5563;">${sub}</div>
        </div>`,

    _error: (title, detail) => `
        <div style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.25);
             color:#f87171;padding:1rem 1.25rem;border-radius:.75rem;font-size:.875rem;max-width:540px;">
            <i class="fas fa-exclamation-triangle mr-2"></i>
            <strong>${_es(title)}</strong>
            ${detail ? `<p style="margin:.5rem 0 0;font-size:.78rem;color:#fca5a5;">${_es(detail)}</p>` : ''}
        </div>`,
};

/* ── HTML escape util ─────────────────────────────────────────────────────── */
function _es(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
