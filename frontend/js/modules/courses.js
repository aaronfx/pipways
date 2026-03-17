/**
 * Pipways LMS — courses.js
 * Renders: course grid → curriculum accordion → lesson modal
 *
 * Depends on: window.API (or window.dashboard.apiRequest)
 * Exposed as: window.CoursesPage
 */
const CoursesPage = {

    // ── State ────────────────────────────────────────────────────────────────
    _currentCourse:    null,
    _currentLesson:    null,
    _allLessons:       [],   // flat list for prev/next nav
    _courseId:         null,

    // ── Entry point ───────────────────────────────────────────────────────────
    async render(containerId = 'courses-container') {
        const root = typeof containerId === 'string'
            ? (document.getElementById(containerId) || document.getElementById('section-courses') || document.body)
            : containerId;

        root.innerHTML = this._skeleton();

        try {
            const data  = await this._req('/courses/list');
            const courses = Array.isArray(data) ? data : (data.courses || []);
            if (!courses.length) {
                root.innerHTML = this._empty('No courses published yet', 'fa-graduation-cap');
                return;
            }
            // FIX: courses-container is already a CSS grid in dashboard.html.
            // Wrapping everything in col-span-full keeps CoursesPage's own inner
            // grid from being broken across the outer grid's columns.
            root.innerHTML = `
                <div class="col-span-full">
                    <div class="flex items-center justify-between mb-6">
                        <h3 class="text-xl font-bold text-white">Trading Academy</h3>
                        <div id="lms-progress-badge" class="text-xs text-gray-400"></div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" id="lms-course-grid">
                        ${courses.map(c => this._courseCard(c)).join('')}
                    </div>
                </div>`;
            this._loadProgressBadge();
        } catch (e) {
            root.innerHTML = this._error('Failed to load courses', e.message);
        }
    },

    // ── Course Card ───────────────────────────────────────────────────────────
    _courseCard(c) {
        const thumb = c.thumbnail_url
            ? `<img src="${c.thumbnail_url}" class="w-full h-44 object-cover"
                     onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">`
            : '';
        const fallback = `<div class="w-full h-44 bg-gradient-to-br from-purple-900 to-blue-900
                               flex items-center justify-center ${c.thumbnail_url ? 'hidden' : ''}">
                               <i class="fas fa-graduation-cap text-5xl text-white/20"></i></div>`;
        const pct    = c.progress || 0;
        const btn    = pct > 0
            ? `<button class="w-full mt-3 py-2 rounded-lg text-sm font-semibold text-white transition-colors"
                       style="background:#7c3aed;" onclick="CoursesPage.openCourse(${c.id})">
                   Continue (${pct}%) →
               </button>`
            : `<button class="w-full mt-3 py-2 rounded-lg text-sm font-semibold text-white transition-colors"
                       style="background:#7c3aed;" onclick="CoursesPage.openCourse(${c.id})">
                   Start Learning →
               </button>`;
        return `
        <div class="bg-gray-800 rounded-xl overflow-hidden border border-gray-700
                    hover:border-purple-600/50 transition-colors cursor-pointer group"
             onclick="CoursesPage.openCourse(${c.id})">
            ${thumb}${fallback}
            <div class="p-4">
                <div class="flex items-center justify-between mb-1">
                    <span class="text-xs text-purple-400 font-semibold uppercase tracking-wide">
                        ${this._e(c.level || 'Beginner')}
                    </span>
                    ${c.instructor ? `<span class="text-xs text-gray-500">${this._e(c.instructor)}</span>` : ''}
                </div>
                <h4 class="font-bold text-white mb-2 group-hover:text-purple-300 transition-colors">
                    ${this._e(c.title)}
                </h4>
                <p class="text-sm text-gray-400 line-clamp-2 mb-3">
                    ${this._e(c.description || '')}
                </p>
                <div class="flex items-center justify-between text-xs text-gray-500 mb-2">
                    <span><i class="fas fa-book-open mr-1"></i>${c.lesson_count || 0} lessons</span>
                    ${pct > 0 ? `<span class="text-green-400">${pct}% done</span>` : ''}
                </div>
                ${pct > 0 ? `<div class="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                    <div class="h-full bg-purple-500 rounded-full transition-all"
                         style="width:${pct}%"></div>
                </div>` : ''}
                ${btn}
            </div>
        </div>`;
    },

    // ── Open Course (curriculum view) ─────────────────────────────────────────
    async openCourse(courseId) {
        this._courseId = courseId;
        const root = document.getElementById('courses-container')
                  || document.getElementById('section-courses')
                  || document.body;
        root.innerHTML = `<div class="col-span-full text-center py-12 text-gray-500">
            <i class="fas fa-spinner fa-spin text-2xl"></i>
            <p class="mt-2">Loading curriculum…</p></div>`;

        try {
            const data = await this._req(`/courses/${courseId}/curriculum`);
            this._currentCourse = data;

            // Flatten all lessons for prev/next nav
            this._allLessons = [];
            (data.modules || []).forEach(m => this._allLessons.push(...(m.lessons || [])));
            this._allLessons.push(...(data.loose_lessons || []));

            root.innerHTML = this._curriculumHTML(data);
        } catch (e) {
            root.innerHTML = this._error('Failed to load curriculum', e.message);
        }
    },

    _courseMetaHTML(c, modules, loose) {
        const allLessons   = modules.flatMap(m => m.lessons || []).concat(loose);
        const totalLessons = allLessons.length;
        const doneLessons  = allLessons.filter(l => l.completed).length;
        const totalMins    = allLessons.reduce((a, l) => a + (l.duration_minutes || 0), 0);
        const durStr       = totalMins >= 60
            ? ('~' + Math.round(totalMins / 60) + 'h ' + (totalMins % 60 ? (totalMins % 60) + 'm' : '')).trim()
            : totalMins > 0 ? '~' + totalMins + 'm' : '';
        const pct = totalLessons > 0 ? Math.round(doneLessons / totalLessons * 100) : 0;

        const metaParts = [];
        if (totalLessons > 0) metaParts.push('<span class="text-xs text-gray-500"><i class="fas fa-book-open mr-1"></i>' + doneLessons + '/' + totalLessons + ' lessons</span>');
        if (durStr)           metaParts.push('<span class="text-xs text-gray-500"><i class="fas fa-clock mr-1"></i>' + durStr + '</span>');
        if (pct > 0)          metaParts.push('<span class="text-xs font-semibold" style="color:#a78bfa;">' + pct + '% complete</span>');

        const nextLesson = allLessons.find(l => !l.completed);
        const ctaBtn = nextLesson
            ? '<div class="mt-4 pt-4 border-t border-gray-700">'
              + '<button onclick="CoursesPage.openLesson(' + nextLesson.id + ')" '
              + 'class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all" '
              + 'style="background:linear-gradient(90deg,#7c3aed,#6d28d9);color:white;">'
              + '<i class="fas fa-play-circle"></i> Continue: '
              + this._e(nextLesson.title.length > 40 ? nextLesson.title.slice(0, 40) + '…' : nextLesson.title)
              + '</button></div>'
            : '';

        return '<div class="bg-gray-800 rounded-xl p-6 mb-6 border border-gray-700">'
            + '<div class="flex items-start justify-between gap-4">'
            + '<div class="flex-1 min-w-0">'
            + '<span class="text-xs text-purple-400 font-semibold uppercase tracking-wide">' + this._e(c.level || 'Beginner') + '</span>'
            + '<h2 class="text-2xl font-bold text-white mt-1">' + this._e(c.title || '') + '</h2>'
            + (c.instructor ? '<p class="text-sm text-gray-400 mt-1">By ' + this._e(c.instructor) + '</p>' : '')
            + '<p class="text-gray-400 text-sm mt-2">' + this._e(c.description || '') + '</p>'
            + (metaParts.length ? '<div class="flex flex-wrap items-center gap-3 mt-3">' + metaParts.join('') + '</div>' : '')
            + '</div>'
            + (c.thumbnail_url ? '<img src="' + c.thumbnail_url + '" class="w-28 h-20 object-cover rounded-lg flex-shrink-0">' : '')
            + '</div>'
            + ctaBtn
            + '</div>';
    },

    _curriculumHTML(data) {
        const c       = data.course || {};
        const modules = data.modules || [];
        const loose   = data.loose_lessons || [];

        const modulesHTML = modules.map((mod, mi) => `
        <div class="bg-gray-800 rounded-xl border border-gray-700 mb-3 overflow-hidden">
            <button class="w-full flex items-center justify-between px-5 py-4 text-left
                           hover:bg-gray-700/50 transition-colors"
                    onclick="CoursesPage._toggleModule('mod-${mod.id}')">
                <div class="flex items-center gap-3">
                    <span class="w-7 h-7 rounded-full bg-purple-900/60 flex items-center justify-center
                                 text-xs font-bold text-purple-300">${mi + 1}</span>
                    <span class="font-semibold text-white">${this._e(mod.title)}</span>
                    <span class="text-xs text-gray-500">${mod.lessons.length} lessons
                        ${mod.quiz ? '+ quiz' : ''}</span>
                </div>
                <i class="fas fa-chevron-down text-gray-500 text-xs transition-transform"
                   id="arr-mod-${mod.id}"></i>
            </button>
            <div id="mod-${mod.id}" class="hidden border-t border-gray-700">
                ${mod.lessons.map(l => this._lessonRow(l)).join('')}
                ${mod.quiz ? this._quizRow(mod.quiz, this._courseId) : ''}
            </div>
        </div>`).join('');

        const looseHTML = loose.length ? `
        <div class="bg-gray-800 rounded-xl border border-gray-700 mb-3 overflow-hidden">
            <div class="px-5 py-3 border-b border-gray-700">
                <span class="font-semibold text-white text-sm">Lessons</span>
            </div>
            ${loose.map(l => this._lessonRow(l)).join('')}
        </div>` : '';

        // FIX: col-span-full wrapper so the curriculum view owns the full row
        // inside the outer grid of courses-container.
        // Also: render the course preview_video (entered at creation time) directly
        // below the info card — it was stored in the DB but never displayed.
        const previewVideoHTML = c.preview_video
            ? `<div class="mb-6">${this._videoPlayer(c.preview_video)}</div>`
            : '';

        return `
        <div class="col-span-full">
        <div class="max-w-3xl mx-auto">
            <button onclick="CoursesPage.render()" class="flex items-center gap-2 text-gray-400
                    hover:text-white text-sm mb-5 transition-colors">
                <i class="fas fa-arrow-left"></i> Back to Courses
            </button>
            ${this._courseMetaHTML(c, modules, loose)}
            ${previewVideoHTML}
            <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Curriculum</h3>
            ${modulesHTML}${looseHTML}
        </div>
        </div>`;
    },

    _lessonRow(l) {
        const icon = l.video_url
            ? 'fa-play-circle text-purple-400'
            : 'fa-file-alt text-gray-500';
        // REC: completed lessons have visual distinction — green tick + muted text
        const doneClass = l.completed ? 'lesson-row-done' : '';
        const titleClass = l.completed ? 'lesson-title text-gray-500 line-through' : 'lesson-title text-gray-300';
        const completedBadge = l.completed
            ? '<i class="fas fa-check-circle text-green-400 text-sm flex-shrink-0"></i>'
            : '';
        // REC: duration estimate shown so learners can plan their time
        const dur = l.duration_minutes ? `<span class="text-xs text-gray-600 flex-shrink-0">${l.duration_minutes}m</span>` : '';
        return `
        <div class="flex items-center gap-3 px-5 py-3 hover:bg-gray-700/40 cursor-pointer
                    border-b border-gray-700/50 last:border-0 transition-colors ${doneClass}"
             onclick="CoursesPage.openLesson(${l.id})">
            <i class="fas ${icon} w-4 flex-shrink-0 ${l.completed ? 'opacity-40' : ''}"></i>
            <span class="flex-1 text-sm transition-colors ${titleClass}">
                ${this._e(l.title)}
            </span>
            ${dur}
            ${l.is_free_preview ? '<span class="text-xs text-green-500 font-semibold">Free</span>' : ''}
            ${completedBadge}
        </div>`;
    },

    _quizRow(quiz, courseId) {
        return `
        <div class="flex items-center gap-3 px-5 py-3 hover:bg-yellow-900/20 cursor-pointer
                    border-b border-gray-700/50 last:border-0 transition-colors"
             onclick="QuizPage ? QuizPage.open(${courseId}, ${quiz.id}) : alert('Quiz module loading…')">
            <i class="fas fa-question-circle text-yellow-400 w-4 flex-shrink-0"></i>
            <span class="flex-1 text-sm text-yellow-300">${this._e(quiz.title)}</span>
            <span class="text-xs text-yellow-600">${quiz.question_count || 0} questions</span>
        </div>`;
    },

    _toggleModule(id) {
        const el  = document.getElementById(id);
        const arr = document.getElementById('arr-' + id);
        if (!el) return;
        const open = el.classList.toggle('hidden');
        if (arr) arr.style.transform = open ? '' : 'rotate(180deg)';
    },

    // ── Lesson Viewer (Modal) ─────────────────────────────────────────────────
    async openLesson(lessonId) {
        // Find lesson in flat list
        const lesson = this._allLessons.find(l => l.id === lessonId);
        if (!lesson) return;
        this._currentLesson = lesson;
        this._showLessonModal(lesson);
    },

    _showLessonModal(lesson) {
        const idx  = this._allLessons.findIndex(l => l.id === lesson.id);
        const prev = idx > 0 ? this._allLessons[idx - 1] : null;
        const next = idx < this._allLessons.length - 1 ? this._allLessons[idx + 1] : null;

        const videoHTML = lesson.video_url
            ? this._videoPlayer(lesson.video_url)
            : '';

        const modal = document.createElement('div');
        modal.id = 'lesson-modal';
        modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:10000;display:flex;align-items:center;justify-content:center;padding:1rem;';
        modal.innerHTML = `
        <div style="background:#111827;border-radius:1rem;width:100%;max-width:800px;
                    max-height:90vh;overflow-y:auto;border:1px solid #374151;">
            <div style="display:flex;align-items:center;justify-content:space-between;
                        padding:1rem 1.25rem;border-bottom:1px solid #374151;">
                <h3 style="font-weight:700;color:white;font-size:1rem;">${this._e(lesson.title)}</h3>
                <button onclick="CoursesPage.closeLesson()"
                        style="background:none;border:none;color:#9ca3af;font-size:1.5rem;cursor:pointer;">×</button>
            </div>

            ${videoHTML}

            <div style="padding:1.25rem;color:#d1d5db;font-size:.9rem;line-height:1.7;">
                ${lesson.content || '<p class="text-gray-500">No additional content for this lesson.</p>'}
            </div>

            <div style="display:flex;align-items:center;justify-content:space-between;
                        padding:1rem 1.25rem;border-top:1px solid #374151;gap:1rem;flex-wrap:wrap;">
                <div style="display:flex;gap:.75rem;">
                    ${prev ? `<button onclick="CoursesPage.openLesson(${prev.id})"
                        style="padding:.5rem 1rem;border-radius:.5rem;font-size:.8rem;
                               background:#1f2937;color:#9ca3af;border:1px solid #374151;cursor:pointer;">
                        ← Previous
                    </button>` : '<span></span>'}
                    ${next ? `<button onclick="CoursesPage.openLesson(${next.id})"
                        style="padding:.5rem 1rem;border-radius:.5rem;font-size:.8rem;
                               background:#1f2937;color:#9ca3af;border:1px solid #374151;cursor:pointer;">
                        Next →
                    </button>` : ''}
                </div>

                ${lesson.completed
                    ? `<span style="color:#34d399;font-size:.85rem;font-weight:600;">
                           <i class="fas fa-check-circle mr-1"></i>Completed
                       </span>`
                    : `<button onclick="CoursesPage.markComplete(${lesson.id})"
                           id="btn-complete-${lesson.id}"
                           style="padding:.6rem 1.5rem;border-radius:.5rem;font-size:.85rem;
                                  font-weight:700;background:#7c3aed;color:white;border:none;cursor:pointer;">
                           ✓ Mark Complete
                       </button>`}
            </div>
        </div>`;

        document.getElementById('lesson-modal')?.remove();
        document.body.appendChild(modal);
        modal.addEventListener('click', e => { if (e.target === modal) this.closeLesson(); });
    },

    _videoPlayer(url) {
        // YouTube
        const ytMatch = url.match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/|shorts\/))([A-Za-z0-9_-]{11})/);
        if (ytMatch) {
            return `<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;">
                <iframe src="https://www.youtube.com/embed/${ytMatch[1]}" frameborder="0" allowfullscreen
                    style="position:absolute;top:0;left:0;width:100%;height:100%;"></iframe>
            </div>`;
        }
        // Vimeo
        const vmMatch = url.match(/vimeo\.com\/(\d+)/);
        if (vmMatch) {
            return `<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;">
                <iframe src="https://player.vimeo.com/video/${vmMatch[1]}" frameborder="0" allowfullscreen
                    style="position:absolute;top:0;left:0;width:100%;height:100%;"></iframe>
            </div>`;
        }
        // Direct MP4 / other
        return `<video controls style="width:100%;max-height:400px;background:#000;">
            <source src="${url}">
            Your browser does not support video.
        </video>`;
    },

    closeLesson() {
        document.getElementById('lesson-modal')?.remove();
    },

    async markComplete(lessonId) {
        const btn = document.getElementById(`btn-complete-${lessonId}`);
        if (btn) { btn.disabled = true; btn.textContent = 'Saving…'; }

        try {
            const result = await this._req(
                `/courses/${this._courseId}/lessons/${lessonId}/complete`,
                { method: 'POST', body: JSON.stringify({}) }
            );

            // Update local lesson state
            const lesson = this._allLessons.find(l => l.id === lessonId);
            if (lesson) lesson.completed = true;

            // Update progress badge
            this._loadProgressBadge();

            if (result.course_complete) {
                this.closeLesson();
                this._showCertModal(result);
                return;
            }

            if (btn) {
                btn.outerHTML = `<span style="color:#34d399;font-size:.85rem;font-weight:600;">
                    <i class="fas fa-check-circle mr-1"></i>Completed
                </span>`;
            }

            // Auto-advance to next lesson after short delay
            const idx  = this._allLessons.findIndex(l => l.id === lessonId);
            const next = this._allLessons[idx + 1];
            if (next) {
                setTimeout(() => this.openLesson(next.id), 800);
            }
        } catch (e) {
            if (btn) { btn.disabled = false; btn.textContent = '✓ Mark Complete'; }
            alert('Could not save progress: ' + e.message);
        }
    },

    _showCertModal(result) {
        const modal = document.createElement('div');
        modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:10001;display:flex;align-items:center;justify-content:center;padding:1rem;';
        modal.innerHTML = `
        <div style="background:linear-gradient(135deg,#1e1b4b,#312e81);border-radius:1rem;
                    padding:2.5rem;max-width:480px;width:100%;text-align:center;
                    border:1px solid rgba(124,58,237,.4);">
            <div style="font-size:3rem;margin-bottom:1rem;">🎓</div>
            <h2 style="font-size:1.5rem;font-weight:800;color:white;margin-bottom:.5rem;">
                Course Complete!
            </h2>
            <p style="color:#c4b5fd;margin-bottom:1.5rem;">
                Congratulations! You've completed this course.
            </p>
            ${result.certificate_number ? `
            <div style="background:rgba(124,58,237,.2);border:1px solid rgba(124,58,237,.4);
                        border-radius:.75rem;padding:1rem;margin-bottom:1.5rem;">
                <p style="color:#a78bfa;font-size:.8rem;font-weight:600;">CERTIFICATE NUMBER</p>
                <p style="color:white;font-family:monospace;font-size:.9rem;margin-top:.25rem;">
                    ${result.certificate_number}
                </p>
            </div>` : ''}
            <button onclick="this.closest('div[style]').remove();CoursesPage.render()"
                    style="padding:.75rem 2rem;border-radius:.5rem;font-weight:700;
                           background:#7c3aed;color:white;border:none;cursor:pointer;font-size:.9rem;">
                Back to Courses
            </button>
        </div>`;
        document.body.appendChild(modal);
    },

    // ── Progress badge ────────────────────────────────────────────────────────
    async _loadProgressBadge() {
        try {
            const data = await this._req('/courses/enhanced/progress');
            const el = document.getElementById('lms-progress-badge');
            if (el) {
                el.textContent = `${data.completed_count || 0} completed · ${data.overall_progress || 0}% overall`;
            }
        } catch (_) {}
    },

    // ── Utility ───────────────────────────────────────────────────────────────
    async _req(endpoint, options = {}) {
        const token = localStorage.getItem('pipways_token');
        const headers = {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...options.headers,
        };
        if (options.body instanceof FormData) delete headers['Content-Type'];

        const res = await fetch(window.location.origin + endpoint, { ...options, headers });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
            throw new Error(err.detail || `Request failed ${res.status}`);
        }
        return res.json();
    },

    _e(str) {
        if (!str) return '';
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    },

    _skeleton() {
        return `<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            ${Array(3).fill(`<div class="bg-gray-800 rounded-xl overflow-hidden border border-gray-700 animate-pulse">
                <div class="h-44 bg-gray-700"></div>
                <div class="p-4 space-y-2">
                    <div class="h-3 bg-gray-700 rounded w-1/3"></div>
                    <div class="h-4 bg-gray-700 rounded w-3/4"></div>
                    <div class="h-3 bg-gray-700 rounded w-full"></div>
                    <div class="h-8 bg-gray-700 rounded mt-3"></div>
                </div>
            </div>`).join('')}
        </div>`;
    },

    _empty(msg, icon = 'fa-inbox') {
        // col-span-full so this single div doesn't appear as one grid cell
        return `<div class="col-span-full text-center py-16 text-gray-500">
            <i class="fas ${icon} text-5xl mb-4 block opacity-30"></i>
            <p class="font-medium">${msg}</p>
        </div>`;
    },

    _error(title, detail = '') {
        return `<div class="col-span-full text-center py-12 text-gray-500">
            <i class="fas fa-exclamation-triangle text-3xl mb-3 block text-red-500/50"></i>
            <p class="font-medium text-red-400">${title}</p>
            ${detail ? `<p class="text-xs mt-1 text-gray-600">${detail}</p>` : ''}
            <button onclick="CoursesPage.render()" class="mt-4 px-4 py-2 rounded-lg text-sm
                    bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors">
                Try Again
            </button>
        </div>`;
    },
};

window.CoursesPage = CoursesPage;
