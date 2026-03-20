/**
 * Pipways Premium Video Courses — courses.js  v3.1
 *
 * Features:
 *  • Video course catalog: grouped by level (Beginner / Intermediate / Advanced)
 *  • Welcome message shown ONCE (localStorage gate)
 *  • Full lesson viewer — video player + optional text content
 *  • "Pipways Trading Coach" AI panel inside lessons (NOT "AI Mentor")
 *  • Back-to-course preserves state (no blank grid)
 *  • Progress bars, completion badges, certificate modal
 *  • TradingView chart embed for technical lessons
 *  • Mobile responsive — all views optimised for small screens
 *
 * Exposed as: window.CoursesPage
 * Depends on:  window.location.origin  +  JWT in localStorage('pipways_token')
 *
 * NOTE: This is the PREMIUM VIDEO COURSES section.
 *       Text-based structured learning lives in academy.html (Trading Academy).
 *       DB tables: courses, lessons, course_modules, user_lesson_progress, user_progress
 */
const CoursesPage = (() => {

    // ── State ─────────────────────────────────────────────────────────────────
    let _state = {
        view:         'home',   // 'home' | 'curriculum' | 'lesson'
        courseId:     null,
        courseData:   null,     // full curriculum response
        allLessons:   [],       // flat ordered list for prev/next
        currentLesson:null,
        root:         null,     // DOM element we render into
    };

    // ── Public API ────────────────────────────────────────────────────────────

    async function render(containerId = 'courses-container') {
        _state.root = typeof containerId === 'string'
            ? document.getElementById(containerId) || document.body
            : containerId;
        _state.view = 'home';
        await _renderHome();
    }

    async function openCourse(courseId) {
        _state.courseId = parseInt(courseId);
        _state.view = 'curriculum';
        await _renderCurriculum();
    }

    async function openLesson(lessonId) {
        const lesson = _state.allLessons.find(l => l.id === parseInt(lessonId));
        if (!lesson) { console.warn('[Courses] lesson not found:', lessonId); return; }
        _state.currentLesson = lesson;
        _state.view = 'lesson';
        _renderLesson(lesson);
    }

    async function markComplete(lessonId) {
        const btn = document.getElementById('btn-complete-' + lessonId);
        if (btn) { btn.disabled = true; btn.textContent = 'Saving…'; }
        try {
            const result = await _req(
                '/courses/' + _state.courseId + '/lessons/' + lessonId + '/complete',
                { method: 'POST', body: JSON.stringify({}) }
            );
            const lesson = _state.allLessons.find(l => l.id === parseInt(lessonId));
            if (lesson) lesson.completed = true;

            if (result.course_complete) {
                _showCertModal(result);
                return;
            }
            if (btn) btn.outerHTML = '<span style="color:#34d399;font-size:.85rem;font-weight:600;"><i class="fas fa-check-circle mr-1"></i>Completed</span>';

            const idx  = _state.allLessons.findIndex(l => l.id === parseInt(lessonId));
            const next = _state.allLessons[idx + 1];
            if (next) setTimeout(() => openLesson(next.id), 900);
        } catch (e) {
            if (btn) { btn.disabled = false; btn.textContent = '✓ Mark Complete'; }
            _toast('Could not save: ' + e.message, 'error');
        }
    }

    function closeLesson() {
        if (_state.courseId) {
            _state.view = 'curriculum';
            _renderCurriculumFromCache();
        } else {
            render(_state.root);
        }
    }

    // ── Home view ─────────────────────────────────────────────────────────────

    async function _renderHome() {
        const root = _state.root;
        root.innerHTML = _spinnerHTML('Loading Courses…');

        let courses = [];
        try {
            const data = await _req('/courses/list');
            courses = Array.isArray(data) ? data : (data.courses || []);
        } catch (e) {
            root.innerHTML = _errorHTML('Failed to load courses', e.message);
            return;
        }

        // Separate by level
        const byLevel = { Beginner: [], Intermediate: [], Advanced: [] };
        courses.forEach(c => {
            const lvl = (c.level || 'Beginner');
            const key = lvl.charAt(0).toUpperCase() + lvl.slice(1).toLowerCase();
            if (!byLevel[key]) byLevel[key] = [];
            byLevel[key].push(c);
        });

        // Welcome message — shown only once
        const welcomed = localStorage.getItem('pw_courses_welcomed');
        const welcomeHTML = !welcomed ? _welcomeHTML() : '';

        root.innerHTML = `
        <div class="courses-home" style="width:100%;">
            ${welcomeHTML}

            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.5rem;flex-wrap:wrap;gap:.75rem;">
                <div>
                    <h2 style="font-size:1.5rem;font-weight:800;color:white;margin:0;">Premium Video Courses</h2>
                    <p style="color:#6b7280;font-size:.85rem;margin:.25rem 0 0;">Expert-led video lessons for every level</p>
                </div>
                <div id="courses-progress-summary" style="font-size:.8rem;color:#6b7280;"></div>
            </div>

            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(min(300px,100%),1fr));gap:1.25rem;width:100%;">
                ${_levelCard('Beginner',     byLevel.Beginner     || [], '#10b981', 'fa-play-circle', 'Video courses covering Forex fundamentals and first trade setup.')}
                ${_levelCard('Intermediate', byLevel.Intermediate || [], '#3b82f6', 'fa-video',        'Structured video lessons on technical analysis and strategy building.')}
                ${_levelCard('Advanced',     byLevel.Advanced     || [], '#f59e0b', 'fa-graduation-cap','Expert video courses — institutional concepts, SMC and live trade analysis.')}
            </div>

            ${courses.length === 0 ? `
            <div style="text-align:center;padding:4rem 1rem;color:#4b5563;">
                <i class="fas fa-video" style="font-size:3rem;margin-bottom:1rem;opacity:.3;display:block;"></i>
                <p style="font-weight:600;">No video courses published yet.</p>
                <p style="font-size:.85rem;margin-top:.5rem;">Premium video courses are coming soon. Try the free <a href="/academy" style="color:#a78bfa;">Trading Academy</a> while you wait.</p>
            </div>` : ''}
        </div>`;

        if (!welcomed) {
            // dismiss button handler
            const btn = document.getElementById('courses-welcome-dismiss');
            if (btn) btn.addEventListener('click', () => {
                localStorage.setItem('pw_courses_welcomed', '1');
                const box = document.getElementById('courses-welcome-box');
                if (box) box.style.display = 'none';
            });
            // CTA button
            const cta = document.getElementById('courses-welcome-cta');
            if (cta) cta.addEventListener('click', () => {
                const first = courses[0];
                if (first) openCourse(first.id);
            });
        }

        _loadProgressSummary();
    }

    function _welcomeHTML() {
        return `
        <div id="courses-welcome-box" style="
            background:linear-gradient(135deg,rgba(124,58,237,.18),rgba(59,130,246,.12));
            border:1px solid rgba(124,58,237,.35);
            border-left:4px solid #7c3aed;
            border-radius:.85rem;padding:1.25rem 1.5rem;
            margin-bottom:1.75rem;position:relative;">
            <button id="courses-welcome-dismiss" style="
                position:absolute;top:.75rem;right:.75rem;
                background:none;border:none;color:#6b7280;
                font-size:1.25rem;cursor:pointer;line-height:1;padding:.25rem;">×</button>
            <div style="display:flex;gap:1rem;align-items:flex-start;">
                <div style="width:40px;height:40px;border-radius:50%;
                            background:linear-gradient(135deg,#7c3aed,#3b82f6);
                            flex-shrink:0;display:flex;align-items:center;justify-content:center;">
                    <i class="fas fa-robot" style="color:white;font-size:.9rem;"></i>
                </div>
                <div style="flex:1;min-width:0;">
                    <p style="font-size:.7rem;font-weight:700;color:#a78bfa;text-transform:uppercase;
                               letter-spacing:.08em;margin:0 0 .35rem;">PREMIUM COURSES</p>
                    <p style="color:#e5e7eb;font-size:.9rem;line-height:1.6;margin:0 0 .85rem;">
                        Welcome to Premium Video Courses! These are expert-led video lessons that go
                        deeper than the free Trading Academy. Pick a level to begin — inside each lesson
                        you'll find the <strong style="color:#a78bfa;">Pipways Trading Coach</strong>
                        ready to answer your questions.
                    </p>
                    <button id="courses-welcome-cta"
                        style="background:#7c3aed;color:white;border:none;border-radius:.5rem;
                               padding:.5rem 1.25rem;font-size:.85rem;font-weight:700;cursor:pointer;">
                        Start Learning →
                    </button>
                </div>
            </div>
        </div>`;
    }

    function _levelCard(level, courses, color, icon, desc) {
        const total   = courses.reduce((s, c) => s + (c.lesson_count || 0), 0);
        const pct     = courses.length
            ? Math.round(courses.reduce((s,c) => s + (c.progress||0), 0) / courses.length)
            : 0;
        const colorMap = {
            Beginner:     { border:'rgba(16,185,129,.4)', bg:'rgba(16,185,129,.08)', text:'#34d399' },
            Intermediate: { border:'rgba(59,130,246,.4)', bg:'rgba(59,130,246,.08)', text:'#60a5fa' },
            Advanced:     { border:'rgba(245,158,11,.4)', bg:'rgba(245,158,11,.08)', text:'#fbbf24' },
        };
        const cm = colorMap[level] || colorMap.Beginner;

        const courseList = courses.map(c => `
            <div onclick="CoursesPage.openCourse(${c.id})"
                 style="display:flex;align-items:center;justify-content:space-between;
                        padding:.55rem .75rem;border-radius:.5rem;cursor:pointer;
                        background:rgba(255,255,255,.03);margin-bottom:.3rem;
                        border:1px solid rgba(255,255,255,.06);transition:background .15s;"
                 onmouseover="this.style.background='rgba(255,255,255,.07)'"
                 onmouseout="this.style.background='rgba(255,255,255,.03)'">
                <div style="flex:1;min-width:0;">
                    <p style="color:white;font-size:.82rem;font-weight:600;margin:0;
                               overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                        ${_e(c.title)}
                    </p>
                    <p style="color:#6b7280;font-size:.72rem;margin:.1rem 0 0;">
                        ${c.lesson_count || 0} lessons
                        ${c.progress > 0 ? '· <span style="color:' + cm.text + '">' + c.progress + '% done</span>' : ''}
                    </p>
                </div>
                <i class="fas fa-chevron-right" style="color:#374151;font-size:.65rem;flex-shrink:0;margin-left:.5rem;"></i>
            </div>`).join('');

        const emptyState = courses.length === 0 ? `
            <p style="color:#4b5563;font-size:.8rem;text-align:center;padding:.75rem 0;">
                No courses published yet
            </p>` : '';

        return `
        <div style="background:#111827;border:1px solid ${cm.border};border-top:3px solid ${color};
                    border-radius:.85rem;overflow:hidden;display:flex;flex-direction:column;">
            <div style="padding:1.25rem 1.25rem .75rem;background:${cm.bg};">
                <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:.65rem;">
                    <div style="width:42px;height:42px;border-radius:.6rem;background:${cm.bg};
                                border:1px solid ${cm.border};display:flex;align-items:center;justify-content:center;">
                        <i class="fas ${icon}" style="color:${cm.text};font-size:1.1rem;"></i>
                    </div>
                    <div>
                        <p style="font-size:.7rem;font-weight:700;color:${cm.text};text-transform:uppercase;
                                   letter-spacing:.08em;margin:0;">${level.toUpperCase()}</p>
                        <p style="font-weight:800;color:white;font-size:1.1rem;margin:0;">${level}</p>
                    </div>
                </div>
                <p style="color:#9ca3af;font-size:.82rem;margin:0 0 .75rem;">${desc}</p>
                <div style="display:flex;justify-content:space-between;align-items:center;
                            font-size:.78rem;color:#6b7280;margin-bottom:.4rem;">
                    <span>Progress</span>
                    <span style="color:${cm.text};font-weight:700;">${pct}%</span>
                </div>
                <div style="height:5px;background:#1f2937;border-radius:99px;overflow:hidden;">
                    <div style="height:100%;width:${pct}%;background:${color};border-radius:99px;
                                transition:width .4s ease;"></div>
                </div>
                <p style="color:#4b5563;font-size:.75rem;margin:.4rem 0 0;">
                    ${total} lessons${courses.length > 1 ? ' across ' + courses.length + ' courses' : ''}
                </p>
            </div>
            <div style="padding:.75rem 1.25rem 1.25rem;flex:1;">
                ${courseList}${emptyState}
            </div>
        </div>`;
    }

    async function _loadProgressSummary() {
        try {
            const data = await _req('/courses/enhanced/progress');
            const el   = document.getElementById('courses-progress-summary');
            if (el && data) {
                const done  = data.completed_count  || 0;
                const total = data.total_courses    || 0;
                const pct   = data.overall_progress || 0;
                el.innerHTML = `
                    <span style="color:#6b7280;">${done}/${total} video courses</span>
                    <span style="margin:0 .4rem;color:#374151;">·</span>
                    <span style="color:#a78bfa;font-weight:600;">${pct}%</span>`;
            }
        } catch (_) {}
    }

    // ── Curriculum view ───────────────────────────────────────────────────────

    async function _renderCurriculum() {
        const root = _state.root;
        root.innerHTML = _spinnerHTML('Loading course…');
        try {
            const data = await _req('/courses/' + _state.courseId + '/curriculum');
            _state.courseData = data;
            _state.allLessons = [];
            (data.modules || []).forEach(m => _state.allLessons.push(...(m.lessons || [])));
            _state.allLessons.push(...(data.loose_lessons || []));
            _renderCurriculumFromCache();
        } catch (e) {
            root.innerHTML = _errorHTML('Failed to load curriculum', e.message);
        }
    }

    function _renderCurriculumFromCache() {
        const root = _state.root;
        const data = _state.courseData;
        if (!data) { render(root); return; }
        const c       = data.course   || {};
        const modules = data.modules  || [];
        const loose   = data.loose_lessons || [];

        const colorOf = lvl => ({
            Beginner:     '#10b981', Intermediate: '#3b82f6', Advanced: '#f59e0b'
        }[lvl] || '#7c3aed');
        const accentColor = colorOf(c.level || 'Beginner');

        const modHTML = modules.map((mod, mi) => {
            const done    = mod.lessons.filter(l => l.completed).length;
            const total   = mod.lessons.length;
            const modPct  = total > 0 ? Math.round(done / total * 100) : 0;
            return `
            <div style="background:#111827;border:1px solid #1f2937;border-radius:.75rem;
                        margin-bottom:.75rem;overflow:hidden;">
                <button onclick="CoursesPage._toggleModule('mod-${mod.id}')"
                        style="width:100%;display:flex;align-items:center;gap:.85rem;
                               padding:.9rem 1.1rem;background:none;border:none;cursor:pointer;
                               text-align:left;">
                    <span style="width:28px;height:28px;border-radius:50%;flex-shrink:0;
                                 background:rgba(124,58,237,.2);border:1px solid rgba(124,58,237,.4);
                                 display:flex;align-items:center;justify-content:center;
                                 font-size:.75rem;font-weight:800;color:#a78bfa;">
                        ${mi + 1}
                    </span>
                    <div style="flex:1;min-width:0;">
                        <p style="font-weight:700;color:white;font-size:.9rem;margin:0;
                                   overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                            ${_e(mod.title)}
                        </p>
                        <p style="color:#6b7280;font-size:.72rem;margin:.1rem 0 0;">
                            ${done}/${total} lessons complete
                            ${mod.quiz ? ' · includes quiz' : ''}
                        </p>
                    </div>
                    ${modPct === 100
                        ? '<i class="fas fa-check-circle" style="color:#10b981;font-size:.9rem;flex-shrink:0;"></i>'
                        : '<i class="fas fa-chevron-down" style="color:#4b5563;font-size:.75rem;flex-shrink:0;" id="arr-mod-' + mod.id + '"></i>'}
                </button>
                <div id="mod-${mod.id}" class="hidden"
                     style="border-top:1px solid #1f2937;">
                    ${mod.lessons.map(l => _lessonRow(l)).join('')}
                    ${mod.quiz ? _quizRow(mod.quiz) : ''}
                </div>
            </div>`;
        }).join('');

        const looseHTML = loose.length ? `
            <div style="background:#111827;border:1px solid #1f2937;border-radius:.75rem;
                        margin-bottom:.75rem;overflow:hidden;">
                <div style="padding:.75rem 1.1rem;border-bottom:1px solid #1f2937;">
                    <p style="font-weight:700;color:white;font-size:.9rem;margin:0;">Lessons</p>
                </div>
                ${loose.map(l => _lessonRow(l)).join('')}
            </div>` : '';

        root.innerHTML = `
        <div style="max-width:760px;margin:0 auto;padding:0 .5rem 3rem;">
            <button onclick="CoursesPage.render()"
                    style="display:inline-flex;align-items:center;gap:.5rem;color:#6b7280;
                           background:none;border:none;cursor:pointer;font-size:.85rem;
                           margin-bottom:1.25rem;padding:0;transition:color .15s;"
                    onmouseover="this.style.color='white'"
                    onmouseout="this.style.color='#6b7280'">
                <i class="fas fa-arrow-left"></i> Back to Courses
            </button>

            <div style="background:#111827;border:1px solid #1f2937;border-top:3px solid ${accentColor};
                        border-radius:.85rem;padding:1rem 1.25rem 1.25rem;margin-bottom:1.25rem;">
                <div style="display:flex;align-items:flex-start;gap:1rem;flex-wrap:wrap;">
                    <div style="flex:1;min-width:200px;">
                        <span style="font-size:.7rem;font-weight:700;color:${accentColor};
                                     text-transform:uppercase;letter-spacing:.08em;">
                            ${_e(c.level || 'Beginner')}
                        </span>
                        <h2 style="font-size:1.35rem;font-weight:800;color:white;margin:.25rem 0 .5rem;">
                            ${_e(c.title || '')}
                        </h2>
                        ${c.instructor ? `<p style="color:#9ca3af;font-size:.82rem;margin:0 0 .5rem;">
                            By ${_e(c.instructor)}</p>` : ''}
                        <p style="color:#6b7280;font-size:.85rem;line-height:1.6;margin:0;">
                            ${_e(c.description || '')}
                        </p>
                    </div>
                    ${c.thumbnail_url
                        ? `<img src="${c.thumbnail_url}" alt=""
                               style="width:110px;height:80px;object-fit:cover;border-radius:.5rem;flex-shrink:0;">`
                        : ''}
                </div>
            </div>

            <p style="font-size:.72rem;font-weight:700;color:#4b5563;text-transform:uppercase;
                       letter-spacing:.08em;margin:0 0 .75rem;">Curriculum</p>
            ${modHTML}${looseHTML}
        </div>`;

        // Auto-open first incomplete module
        if (modules.length) {
            const firstIncomplete = modules.find(m => m.lessons.some(l => !l.completed)) || modules[0];
            if (firstIncomplete) _toggleModule('mod-' + firstIncomplete.id);
        }
    }

    function _lessonRow(l) {
        const icon = l.video_url ? 'fa-play-circle' : 'fa-file-alt';
        const iconColor = l.video_url ? '#a78bfa' : '#6b7280';
        const checkmark = l.completed
            ? '<i class="fas fa-check-circle" style="color:#10b981;font-size:.85rem;flex-shrink:0;"></i>'
            : '<div style="width:16px;height:16px;border:1.5px solid #374151;border-radius:50%;flex-shrink:0;"></div>';
        return `
        <div onclick="CoursesPage.openLesson(${l.id})"
             style="display:flex;align-items:center;gap:.85rem;padding:.7rem 1.1rem;
                    cursor:pointer;border-bottom:1px solid #0f172a;transition:background .12s;"
             onmouseover="this.style.background='rgba(124,58,237,.07)'"
             onmouseout="this.style.background='transparent'">
            ${checkmark}
            <i class="fas ${icon}" style="color:${iconColor};font-size:.8rem;width:14px;flex-shrink:0;"></i>
            <span style="flex:1;font-size:.85rem;color:${l.completed ? '#6b7280' : '#d1d5db'};
                          text-decoration:${l.completed ? 'line-through' : 'none'};">
                ${_e(l.title)}
            </span>
            ${l.duration_minutes
                ? `<span style="font-size:.72rem;color:#4b5563;flex-shrink:0;">${l.duration_minutes}m</span>`
                : ''}
            ${l.is_free_preview
                ? `<span style="font-size:.65rem;color:#10b981;font-weight:700;
                               border:1px solid rgba(16,185,129,.3);border-radius:99px;
                               padding:.1rem .4rem;flex-shrink:0;">FREE</span>`
                : ''}
        </div>`;
    }

    function _quizRow(quiz) {
        return `
        <div onclick="typeof QuizPage !== 'undefined' ? QuizPage.open(${_state.courseId}, ${quiz.id}) : CoursesPage._toast('Quiz coming soon','info')"
             style="display:flex;align-items:center;gap:.85rem;padding:.7rem 1.1rem;
                    cursor:pointer;background:rgba(245,158,11,.04);transition:background .12s;"
             onmouseover="this.style.background='rgba(245,158,11,.09)'"
             onmouseout="this.style.background='rgba(245,158,11,.04)'">
            <i class="fas fa-question-circle" style="color:#fbbf24;font-size:.85rem;flex-shrink:0;"></i>
            <span style="flex:1;font-size:.85rem;color:#fbbf24;">${_e(quiz.title)}</span>
            <span style="font-size:.72rem;color:#92400e;">${quiz.question_count || 0} questions</span>
        </div>`;
    }

    function _toggleModule(id) {
        const el  = document.getElementById(id);
        const arr = document.getElementById('arr-' + id);
        if (!el) return;
        const isHidden = el.classList.toggle('hidden');
        if (arr) arr.style.transform = isHidden ? '' : 'rotate(180deg)';
    }

    // ── Lesson viewer ─────────────────────────────────────────────────────────

    function _renderLesson(lesson) {
        const root = _state.root;
        const idx  = _state.allLessons.findIndex(l => l.id === lesson.id);
        const prev = idx > 0 ? _state.allLessons[idx - 1] : null;
        const next = idx < _state.allLessons.length - 1 ? _state.allLessons[idx + 1] : null;
        const courseTitle = (_state.courseData && _state.courseData.course)
            ? _state.courseData.course.title : '';
        const level = (_state.courseData && _state.courseData.course)
            ? (_state.courseData.course.level || 'Beginner') : 'Beginner';

        root.innerHTML = `
        <div style="max-width:860px;margin:0 auto;padding:0 .25rem 4rem;" id="lesson-page">

            <!-- Breadcrumb -->
            <nav style="display:flex;align-items:center;gap:.4rem;font-size:.78rem;
                        color:#4b5563;margin-bottom:1.25rem;flex-wrap:wrap;">
                <button onclick="CoursesPage.render()"
                        style="background:none;border:none;cursor:pointer;color:#6b7280;
                               padding:0;transition:color .12s;"
                        onmouseover="this.style.color='white'"
                        onmouseout="this.style.color='#6b7280'">Courses</button>
                <span>›</span>
                <button onclick="CoursesPage.closeLesson()"
                        style="background:none;border:none;cursor:pointer;color:#6b7280;
                               padding:0;transition:color .12s;"
                        onmouseover="this.style.color='white'"
                        onmouseout="this.style.color='#6b7280'">${_e(level)}</button>
                <span>›</span>
                <span style="color:#e5e7eb;font-weight:600;">${_e(lesson.title)}</span>
            </nav>

            <!-- Lesson header -->
            <div style="margin-bottom:1.5rem;">
                <h1 style="font-size:1.5rem;font-weight:800;color:white;margin:0 0 .35rem;
                            line-height:1.3;">${_e(lesson.title)}</h1>
                <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">
                    <span style="font-size:.75rem;color:#a78bfa;font-weight:600;
                                 text-transform:uppercase;letter-spacing:.06em;">${_e(level)}</span>
                    ${lesson.duration_minutes
                        ? `<span style="font-size:.75rem;color:#4b5563;">
                               <i class="fas fa-${lesson.video_url ? 'play-circle' : 'clock'} mr-1"></i>${lesson.duration_minutes} min ${lesson.video_url ? 'watch' : 'read'}</span>`
                        : ''}
                    ${lesson.completed
                        ? `<span style="font-size:.75rem;color:#10b981;font-weight:600;">
                               <i class="fas fa-check-circle mr-1"></i>Completed</span>`
                        : ''}
                </div>
            </div>

            <!-- Video player -->
            ${lesson.video_url ? _videoPlayer(lesson.video_url) : ''}

            <!-- Main lesson content -->
            <div id="lesson-content-body"
                 style="background:#111827;border:1px solid #1f2937;border-radius:.85rem;
                        padding:1.75rem;margin-bottom:1.25rem;
                        color:#d1d5db;font-size:.92rem;line-height:1.85;">
                ${lesson.content
                    ? lesson.content
                    : '<p style="color:#4b5563;">Lesson content coming soon.</p>'}
            </div>

            <!-- TradingView chart (shown for technical lessons) -->
            ${_isTechnicalLesson(lesson) ? _tradingViewEmbed(lesson) : ''}

            <!-- Navigation row -->
            <div style="display:flex;align-items:center;justify-content:space-between;
                        gap:.75rem;flex-wrap:wrap;margin-bottom:1.25rem;">
                <div style="display:flex;gap:.5rem;flex-wrap:wrap;">
                    ${prev
                        ? `<button onclick="CoursesPage.openLesson(${prev.id})"
                                   style="display:inline-flex;align-items:center;gap:.5rem;
                                          padding:.55rem 1rem;border-radius:.5rem;font-size:.82rem;
                                          background:#1f2937;color:#9ca3af;border:1px solid #374151;
                                          cursor:pointer;transition:all .15s;"
                                   onmouseover="this.style.background='#374151';this.style.color='white'"
                                   onmouseout="this.style.background='#1f2937';this.style.color='#9ca3af'">
                               <i class="fas fa-arrow-left"></i>
                               <span class="lesson-nav-label">Previous</span>
                           </button>`
                        : ''}
                    ${next
                        ? `<button onclick="CoursesPage.openLesson(${next.id})"
                                   style="display:inline-flex;align-items:center;gap:.5rem;
                                          padding:.55rem 1rem;border-radius:.5rem;font-size:.82rem;
                                          background:#1f2937;color:#9ca3af;border:1px solid #374151;
                                          cursor:pointer;transition:all .15s;"
                                   onmouseover="this.style.background='#374151';this.style.color='white'"
                                   onmouseout="this.style.background='#1f2937';this.style.color='#9ca3af'">
                               <span class="lesson-nav-label">Next</span>
                               <i class="fas fa-arrow-right"></i>
                           </button>`
                        : ''}
                </div>

                <div style="display:flex;align-items:center;gap:.75rem;flex-wrap:wrap;">
                    <button onclick="CoursesPage.closeLesson()"
                            style="padding:.55rem 1rem;border-radius:.5rem;font-size:.82rem;
                                   background:none;color:#6b7280;border:1px solid #374151;
                                   cursor:pointer;transition:all .15s;"
                            onmouseover="this.style.color='white'"
                            onmouseout="this.style.color='#6b7280'">
                        Back to Course
                    </button>
                    ${lesson.completed
                        ? `<span style="color:#10b981;font-size:.85rem;font-weight:600;">
                               <i class="fas fa-check-circle mr-1"></i>Completed</span>`
                        : `<button onclick="CoursesPage.markComplete(${lesson.id})"
                                   id="btn-complete-${lesson.id}"
                                   style="padding:.6rem 1.5rem;border-radius:.5rem;font-size:.85rem;
                                          font-weight:700;background:#7c3aed;color:white;border:none;
                                          cursor:pointer;transition:opacity .15s;"
                                   onmouseover="this.style.opacity='.85'"
                                   onmouseout="this.style.opacity='1'">
                               ✓ Mark Complete
                           </button>`}
                </div>
            </div>

            <!-- Pipways Trading Coach -->
            ${_coachPanelHTML(lesson, level)}

        </div>`;

        // Inject responsive styles once
        _injectLessonStyles();
    }

    function _isTechnicalLesson(lesson) {
        const techKeywords = [
            'technical', 'chart', 'candlestick', 'trend', 'support', 'resistance',
            'macd', 'rsi', 'moving average', 'indicator', 'pattern', 'breakout',
            'fibonacci', 'bollinger', 'analysis'
        ];
        const text = ((lesson.title || '') + ' ' + (lesson.content || '')).toLowerCase();
        return techKeywords.some(kw => text.includes(kw));
    }

    function _tradingViewEmbed(lesson) {
        // Pick symbol based on lesson content hints
        let symbol = 'FX:EURUSD';
        const text = ((lesson.title || '') + ' ' + (lesson.content || '')).toLowerCase();
        if (text.includes('gbp')) symbol = 'FX:GBPUSD';
        else if (text.includes('jpy') || text.includes('usd/jpy')) symbol = 'FX:USDJPY';
        else if (text.includes('xau') || text.includes('gold')) symbol = 'TVC:GOLD';

        // Add MA + MACD if indicators lesson
        const studies = text.includes('macd') ? '["MACD@tv-basicstudies","MASimple@tv-basicstudies"]'
                      : text.includes('rsi')  ? '["RSI@tv-basicstudies","MASimple@tv-basicstudies"]'
                      : '["MASimple@tv-basicstudies"]';

        return `
        <div style="background:#111827;border:1px solid #1f2937;border-radius:.85rem;
                    overflow:hidden;margin-bottom:1.25rem;">
            <div style="padding:.75rem 1.25rem;border-bottom:1px solid #1f2937;
                        display:flex;align-items:center;gap:.5rem;">
                <i class="fas fa-chart-candlestick" style="color:#7c3aed;"></i>
                <span style="color:white;font-weight:600;font-size:.85rem;">
                    Live Chart — ${symbol.replace('FX:','').replace('TVC:','')}
                </span>
                <span style="color:#4b5563;font-size:.75rem;margin-left:auto;">Interactive · TradingView</span>
            </div>
            <div style="height:380px;">
                <iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tv_chart&symbol=${symbol}&interval=D&hidesidetoolbar=1&hidetoptoolbar=1&symboledit=1&saveimage=0&toolbarbg=1e2030&studies=${encodeURIComponent(studies)}&theme=dark&style=1&timezone=Etc%2FUTC&withdateranges=1&hidevolume=0"
                        style="width:100%;height:100%;border:none;"
                        allowtransparency="true"
                        scrolling="no"
                        allowfullscreen="">
                </iframe>
            </div>
        </div>`;
    }

    function _coachPanelHTML(lesson, level) {
        const skillMap = { Beginner: 'beginner', Intermediate: 'intermediate', Advanced: 'advanced' };
        const skill = skillMap[level] || 'beginner';
        return `
        <div id="coach-panel"
             style="background:#0f172a;border:1px solid rgba(124,58,237,.3);
                    border-radius:.85rem;overflow:hidden;">
            <button onclick="CoursesPage._toggleCoach()"
                    style="width:100%;display:flex;align-items:center;gap:.75rem;padding:.9rem 1.25rem;
                           background:none;border:none;cursor:pointer;text-align:left;">
                <div style="width:34px;height:34px;border-radius:50%;flex-shrink:0;
                             background:linear-gradient(135deg,#7c3aed,#3b82f6);
                             display:flex;align-items:center;justify-content:center;">
                    <i class="fas fa-robot" style="color:white;font-size:.8rem;"></i>
                </div>
                <div style="flex:1;">
                    <p style="margin:0;font-weight:700;color:white;font-size:.88rem;">
                        Pipways Trading Coach
                    </p>
                    <p style="margin:.1rem 0 0;font-size:.72rem;color:#6b7280;">
                        Ask me anything about this lesson
                    </p>
                </div>
                <i class="fas fa-chevron-down" id="coach-arr"
                   style="color:#4b5563;font-size:.75rem;transition:transform .2s;"></i>
            </button>

            <div id="coach-body" style="display:none;border-top:1px solid rgba(124,58,237,.2);">
                <div id="coach-messages"
                     style="min-height:120px;max-height:340px;overflow-y:auto;
                            padding:1rem 1.25rem;display:flex;flex-direction:column;gap:.75rem;">
                    <div style="display:flex;gap:.65rem;align-items:flex-start;">
                        <div style="width:28px;height:28px;border-radius:50%;flex-shrink:0;
                                    background:linear-gradient(135deg,#7c3aed,#3b82f6);
                                    display:flex;align-items:center;justify-content:center;">
                            <i class="fas fa-robot" style="color:white;font-size:.65rem;"></i>
                        </div>
                        <div style="background:#1e293b;border-radius:.6rem;padding:.6rem .85rem;
                                    max-width:88%;font-size:.82rem;color:#d1d5db;line-height:1.6;">
                            Hi! I'm your Pipways Trading Coach. I'm here to help you understand
                            <strong style="color:#a78bfa;">${_e(lesson.title)}</strong>.
                            What would you like me to explain?
                        </div>
                    </div>
                </div>

                <!-- Quick-ask chips -->
                <div style="padding:.5rem 1.25rem;display:flex;gap:.5rem;flex-wrap:wrap;
                            border-top:1px solid #0f172a;">
                    ${['Explain simply', 'Give an example', 'Why does this matter?', 'Quiz me'].map(q => `
                    <button onclick="CoursesPage._coachQuickAsk('${q}', ${lesson.id}, '${skill}')"
                            style="padding:.3rem .7rem;border-radius:99px;font-size:.72rem;
                                   background:rgba(124,58,237,.15);color:#a78bfa;
                                   border:1px solid rgba(124,58,237,.3);cursor:pointer;
                                   transition:all .15s;"
                            onmouseover="this.style.background='rgba(124,58,237,.3)'"
                            onmouseout="this.style.background='rgba(124,58,237,.15)'">${q}</button>
                    `).join('')}
                </div>

                <div style="padding:.75rem 1.25rem;display:flex;gap:.5rem;
                            border-top:1px solid #0f172a;">
                    <input id="coach-input" type="text"
                           placeholder="Ask a question about ${_e(lesson.title)}…"
                           style="flex:1;background:#1e293b;border:1px solid #334155;border-radius:.5rem;
                                  padding:.55rem .85rem;color:white;font-size:.82rem;outline:none;"
                           onkeydown="if(event.key==='Enter') CoursesPage._coachSend(${lesson.id}, '${skill}')">
                    <button onclick="CoursesPage._coachSend(${lesson.id}, '${skill}')"
                            style="padding:.55rem 1rem;border-radius:.5rem;background:#7c3aed;
                                   color:white;border:none;cursor:pointer;font-size:.82rem;
                                   font-weight:600;white-space:nowrap;transition:opacity .15s;"
                            onmouseover="this.style.opacity='.85'"
                            onmouseout="this.style.opacity='1'">
                        Ask →
                    </button>
                </div>
            </div>
        </div>`;
    }

    function _toggleCoach() {
        const body = document.getElementById('coach-body');
        const arr  = document.getElementById('coach-arr');
        if (!body) return;
        const open = body.style.display === 'none';
        body.style.display = open ? 'block' : 'none';
        if (arr) arr.style.transform = open ? 'rotate(180deg)' : '';
    }

    function _coachQuickAsk(text, lessonId, skill) {
        const lesson = _state.allLessons.find(l => l.id === parseInt(lessonId));
        const fullQ  = text === 'Quiz me'
            ? 'Give me a quick quiz question about ' + (lesson ? lesson.title : 'this lesson')
            : text + ' the concept of ' + (lesson ? lesson.title : 'this lesson');
        _coachAsk(fullQ, lessonId, skill);
    }

    async function _coachSend(lessonId, skill) {
        const input = document.getElementById('coach-input');
        if (!input) return;
        const q = input.value.trim();
        if (!q) return;
        input.value = '';
        await _coachAsk(q, lessonId, skill);
    }

    async function _coachAsk(question, lessonId, skill) {
        const body = document.getElementById('coach-body');
        if (body && body.style.display === 'none') _toggleCoach();

        const msgs = document.getElementById('coach-messages');
        if (!msgs) return;

        // Show user bubble
        msgs.insertAdjacentHTML('beforeend', `
            <div style="display:flex;gap:.65rem;align-items:flex-start;justify-content:flex-end;">
                <div style="background:#7c3aed;border-radius:.6rem;padding:.6rem .85rem;
                            max-width:88%;font-size:.82rem;color:white;line-height:1.6;">
                    ${_e(question)}
                </div>
            </div>`);
        msgs.scrollTop = msgs.scrollHeight;

        // Typing indicator
        const typingId = 'coach-typing-' + Date.now();
        msgs.insertAdjacentHTML('beforeend', `
            <div id="${typingId}" style="display:flex;gap:.65rem;align-items:flex-start;">
                <div style="width:28px;height:28px;border-radius:50%;flex-shrink:0;
                             background:linear-gradient(135deg,#7c3aed,#3b82f6);
                             display:flex;align-items:center;justify-content:center;">
                    <i class="fas fa-robot" style="color:white;font-size:.65rem;"></i>
                </div>
                <div style="background:#1e293b;border-radius:.6rem;padding:.6rem .85rem;
                            font-size:.82rem;color:#6b7280;">
                    <i class="fas fa-circle-notch fa-spin" style="margin-right:.4rem;"></i>Thinking…
                </div>
            </div>`);
        msgs.scrollTop = msgs.scrollHeight;

        try {
            const lesson = _state.allLessons.find(l => l.id === parseInt(lessonId));
            const context = lesson
                ? `Lesson: "${lesson.title}". ${lesson.content ? lesson.content.slice(0, 400) : ''}`
                : '';
            const body2 = JSON.stringify({
                question,
                context,
                skill_level: skill || 'beginner',
                include_platform_context: false,
                topic: lesson ? lesson.title : undefined,
            });
            const res = await _req('/ai/mentor/ask', { method: 'POST', body: body2 });
            const reply = res.response || 'I couldn\'t generate a response. Please try again.';
            document.getElementById(typingId)?.remove();
            msgs.insertAdjacentHTML('beforeend', `
                <div style="display:flex;gap:.65rem;align-items:flex-start;">
                    <div style="width:28px;height:28px;border-radius:50%;flex-shrink:0;
                                 background:linear-gradient(135deg,#7c3aed,#3b82f6);
                                 display:flex;align-items:center;justify-content:center;">
                        <i class="fas fa-robot" style="color:white;font-size:.65rem;"></i>
                    </div>
                    <div style="background:#1e293b;border-radius:.6rem;padding:.75rem .85rem;
                                max-width:88%;font-size:.82rem;color:#d1d5db;line-height:1.7;">
                        ${window._renderMd ? window._renderMd(reply) : reply.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/\n/g,'<br>')}
                    </div>
                </div>`);
        } catch (e) {
            document.getElementById(typingId)?.remove();
            msgs.insertAdjacentHTML('beforeend', `
                <div style="color:#f87171;font-size:.78rem;padding:.4rem .85rem;">
                    Couldn't reach the Trading Coach: ${_e(e.message)}
                </div>`);
        }
        msgs.scrollTop = msgs.scrollHeight;
    }

    // ── Certificate modal ─────────────────────────────────────────────────────

    function _showCertModal(result) {
        document.getElementById('cert-modal')?.remove();
        const modal = document.createElement('div');
        modal.id    = 'cert-modal';
        modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.88);z-index:10001;' +
                              'display:flex;align-items:center;justify-content:center;padding:1rem;';
        modal.innerHTML = `
        <div style="background:linear-gradient(135deg,#1e1b4b,#1a1040);
                    border:1px solid rgba(124,58,237,.5);border-radius:1rem;
                    padding:2.5rem;max-width:460px;width:100%;text-align:center;">
            <div style="font-size:3.5rem;margin-bottom:.75rem;">🎓</div>
            <h2 style="font-size:1.5rem;font-weight:800;color:white;margin:0 0 .5rem;">
                Course Complete!
            </h2>
            <p style="color:#c4b5fd;margin-bottom:1.5rem;font-size:.9rem;line-height:1.6;">
                Congratulations! You've completed this course and earned your certificate.
            </p>
            ${result.certificate_number ? `
            <div style="background:rgba(124,58,237,.15);border:1px solid rgba(124,58,237,.4);
                        border-radius:.75rem;padding:1rem;margin-bottom:1.5rem;">
                <p style="color:#a78bfa;font-size:.72rem;font-weight:700;
                           text-transform:uppercase;letter-spacing:.06em;margin:0 0 .35rem;">
                    Certificate Number
                </p>
                <p style="color:white;font-family:monospace;font-size:.9rem;margin:0;">
                    ${result.certificate_number}
                </p>
            </div>` : ''}
            <button onclick="document.getElementById('cert-modal').remove();CoursesPage.render()"
                    style="padding:.75rem 2rem;border-radius:.5rem;font-weight:700;
                           background:#7c3aed;color:white;border:none;cursor:pointer;
                           font-size:.9rem;width:100%;">
                Back to Academy
            </button>
        </div>`;
        document.body.appendChild(modal);
    }

    // ── Video player ──────────────────────────────────────────────────────────

    function _videoPlayer(url) {
        const yt = url.match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/|shorts\/))([A-Za-z0-9_-]{11})/);
        if (yt) return `
            <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;
                        border-radius:.75rem;margin-bottom:1.25rem;background:#000;">
                <iframe src="https://www.youtube.com/embed/${yt[1]}?rel=0"
                        frameborder="0" allowfullscreen
                        style="position:absolute;top:0;left:0;width:100%;height:100%;"></iframe>
            </div>`;
        const vm = url.match(/vimeo\.com\/(\d+)/);
        if (vm) return `
            <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;
                        border-radius:.75rem;margin-bottom:1.25rem;background:#000;">
                <iframe src="https://player.vimeo.com/video/${vm[1]}"
                        frameborder="0" allowfullscreen
                        style="position:absolute;top:0;left:0;width:100%;height:100%;"></iframe>
            </div>`;
        return `<video controls style="width:100%;border-radius:.75rem;margin-bottom:1.25rem;background:#000;">
            <source src="${url}">Your browser does not support video.</video>`;
    }

    // ── Responsive styles ─────────────────────────────────────────────────────

    function _injectLessonStyles() {
        if (document.getElementById('courses-lesson-styles')) return;
        const s = document.createElement('style');
        s.id = 'courses-lesson-styles';
        s.textContent = `
            .hidden { display: none !important; }

            /* ── Mobile: all views ── */
            @media (max-width: 640px) {
                /* Home: single column level cards */
                .courses-home > div > div[style*="grid"] {
                    grid-template-columns: 1fr !important;
                    gap: .75rem !important;
                }
                /* Home header */
                .courses-home > div > div[style*="space-between"] {
                    flex-direction: column !important;
                    align-items: flex-start !important;
                    gap: .4rem !important;
                }
                /* Curriculum: max-width full */
                #lesson-page { padding: 0 .25rem 4rem; }
                /* Lesson header */
                #lesson-page h1 { font-size: 1.1rem !important; }
                /* Nav buttons */
                .lesson-nav-label { display: none; }
                /* Coach panel */
                #coach-panel { margin: 0 -.25rem; border-radius: .5rem; }
                /* Lesson content */
                #lesson-content-body { padding: 1rem !important; }
                /* Course header card */
                #lesson-page > div > div[style*="flex-wrap"] { flex-direction: column !important; }
                /* Breadcrumb font */
                #lesson-page nav { font-size: .7rem !important; }
                /* Video: ensure 16:9 responsive */
                #lesson-page iframe[src*="youtube"],
                #lesson-page iframe[src*="vimeo"] { border-radius: .5rem !important; }
                /* Quick-ask chips: wrap properly */
                #coach-panel > div > div[style*="flex-wrap"] { gap: .3rem !important; }
                /* Mark complete button full width */
                #lesson-page button[id^="btn-complete"] {
                    width: 100% !important;
                    justify-content: center;
                }
            }
            @media (max-width: 400px) {
                /* Level card body padding */
                .courses-home div[style*="1.25rem 1.25rem"] {
                    padding: .85rem !important;
                }
                #lesson-page h1 { font-size: 1rem !important; }
            }
            #lesson-content-body h2 { font-size:1.1rem; font-weight:700; color:#f9fafb;
                                       margin:1.5rem 0 .6rem; border-bottom:1px solid #1f2937;
                                       padding-bottom:.4rem; }
            #lesson-content-body h3 { font-size:.95rem; font-weight:700; color:#e5e7eb;
                                       margin:1.25rem 0 .4rem; }
            #lesson-content-body p  { margin:0 0 .9rem; }
            #lesson-content-body ul,
            #lesson-content-body ol { padding-left:1.4rem; margin:0 0 .9rem; }
            #lesson-content-body li { margin-bottom:.35rem; }
            #lesson-content-body pre,
            #lesson-content-body code {
                background:#0d1117; border:1px solid #1f2937; border-radius:.4rem;
                padding:.6rem .85rem; font-size:.82rem; overflow-x:auto;
                display:block; margin:.5rem 0; color:#a78bfa;
            }
            #lesson-content-body strong { color:#f9fafb; }
            #lesson-content-body .tip-box {
                background:rgba(59,130,246,.1); border:1px solid rgba(59,130,246,.3);
                border-left:3px solid #3b82f6; border-radius:.5rem;
                padding:.85rem 1rem; margin:.85rem 0;
            }
            #lesson-content-body .warning-box {
                background:rgba(245,158,11,.1); border:1px solid rgba(245,158,11,.3);
                border-left:3px solid #f59e0b; border-radius:.5rem;
                padding:.85rem 1rem; margin:.85rem 0;
            }
            #lesson-content-body .example-box {
                background:rgba(16,185,129,.08); border:1px solid rgba(16,185,129,.25);
                border-left:3px solid #10b981; border-radius:.5rem;
                padding:.85rem 1rem; margin:.85rem 0;
            }
            #coach-input:focus { border-color:#7c3aed; }
        `;
        document.head.appendChild(s);
    }

    // ── Utilities ─────────────────────────────────────────────────────────────

    async function _req(endpoint, options = {}) {
        const token = localStorage.getItem('pipways_token');
        const headers = {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: 'Bearer ' + token } : {}),
            ...options.headers,
        };
        if (options.body instanceof FormData) delete headers['Content-Type'];
        const res = await fetch(window.location.origin + endpoint, { ...options, headers });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: 'HTTP ' + res.status }));
            throw new Error(err.detail || 'Request failed ' + res.status);
        }
        return res.json();
    }

    function _e(str) {
        if (str == null) return '';
        const d = document.createElement('div');
        d.textContent = String(str);
        return d.innerHTML;
    }

    function _toast(msg, type) {
        const d = document.createElement('div');
        const bg = type === 'error' ? 'rgba(239,68,68,.95)'
                 : type === 'info'  ? 'rgba(59,130,246,.95)'
                 : 'rgba(16,185,129,.95)';
        d.style.cssText = 'position:fixed;bottom:1.5rem;right:1.5rem;z-index:99999;' +
                          'padding:.75rem 1.25rem;border-radius:.75rem;font-size:.85rem;' +
                          'font-weight:600;color:white;background:' + bg + ';' +
                          'box-shadow:0 8px 24px rgba(0,0,0,.4);max-width:320px;';
        d.textContent = msg;
        document.body.appendChild(d);
        setTimeout(() => d.remove(), 3500);
    }

    function _spinnerHTML(msg) {
        return `<div style="text-align:center;padding:5rem 1rem;color:#4b5563;">
            <i class="fas fa-circle-notch fa-spin" style="font-size:1.5rem;margin-bottom:.75rem;display:block;"></i>
            <p style="font-size:.85rem;">${msg || 'Loading…'}</p>
        </div>`;
    }

    function _errorHTML(title, detail) {
        return `<div style="text-align:center;padding:3rem 1rem;">
            <i class="fas fa-exclamation-triangle" style="font-size:2rem;color:#ef4444;opacity:.5;display:block;margin-bottom:.75rem;"></i>
            <p style="font-weight:600;color:#f87171;margin:0 0 .35rem;">${_e(title)}</p>
            ${detail ? `<p style="font-size:.8rem;color:#4b5563;margin:0 0 1rem;">${_e(detail)}</p>` : ''}
            <button onclick="CoursesPage.render()"
                    style="padding:.5rem 1.25rem;border-radius:.5rem;background:#374151;
                           color:#d1d5db;border:none;cursor:pointer;font-size:.82rem;">
                Try Again
            </button>
        </div>`;
    }

    // Expose internal helpers needed by inline onclick handlers
    return {
        render, openCourse, openLesson, markComplete, closeLesson,
        _toggleModule, _toggleCoach, _coachSend, _coachQuickAsk, _toast,
    };

})();

window.CoursesPage = CoursesPage;
