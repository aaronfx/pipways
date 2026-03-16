/**
 * Pipways LMS — quiz.js
 * Multiple choice quiz UI with scoring, pass/fail, and answer review.
 *
 * Exposed as: window.QuizPage
 * Usage: QuizPage.open(courseId, quizId)
 */
const QuizPage = {

    _courseId: null,
    _quizId:   null,
    _quiz:     null,
    _answers:  {},   // { questionId: "a" | "b" | "c" | "d" }

    // ── Open quiz (loads questions, renders modal) ────────────────────────────
    async open(courseId, quizId) {
        this._courseId = courseId;
        this._quizId   = quizId;
        this._answers  = {};

        this._modal().innerHTML = `
            <div style="text-align:center;padding:3rem;color:#9ca3af;">
                <i class="fas fa-spinner fa-spin text-2xl"></i>
                <p style="margin-top:.75rem;">Loading quiz…</p>
            </div>`;
        document.body.appendChild(this._modalEl);

        try {
            const data = await this._req(`/courses/${courseId}/quizzes/${quizId}`);
            this._quiz = data;
            this._render();
        } catch (e) {
            this._modal().innerHTML = `
                <div style="text-align:center;padding:2rem;color:#f87171;">
                    <i class="fas fa-exclamation-triangle text-3xl mb-3 block"></i>
                    <p>${e.message}</p>
                    <button onclick="QuizPage.close()" style="margin-top:1rem;padding:.5rem 1.5rem;
                        border-radius:.5rem;background:#374151;color:#d1d5db;border:none;cursor:pointer;">
                        Close
                    </button>
                </div>`;
        }
    },

    // ── Render quiz form ──────────────────────────────────────────────────────
    _render() {
        const q   = this._quiz;
        const qHtml = (q.questions || []).map((question, i) => `
        <div style="margin-bottom:1.5rem;" id="q-block-${question.id}">
            <p style="font-weight:600;color:white;margin-bottom:.75rem;font-size:.9rem;">
                ${i + 1}. ${this._e(question.question)}
            </p>
            <div style="display:flex;flex-direction:column;gap:.5rem;">
                ${Object.entries(question.options)
                    .filter(([, v]) => v)
                    .map(([key, val]) => `
                    <label style="display:flex;align-items:center;gap:.75rem;padding:.65rem 1rem;
                                  border-radius:.5rem;cursor:pointer;border:1px solid #374151;
                                  background:#1f2937;transition:all .15s;"
                           id="opt-${question.id}-${key}"
                           onclick="QuizPage._select(${question.id}, '${key}', this)">
                        <span style="width:1.5rem;height:1.5rem;border-radius:50%;border:2px solid #6b7280;
                                     display:flex;align-items:center;justify-content:center;
                                     font-size:.75rem;font-weight:700;flex-shrink:0;color:#9ca3af;"
                              id="dot-${question.id}-${key}">
                            ${key.toUpperCase()}
                        </span>
                        <span style="color:#d1d5db;font-size:.875rem;">${this._e(val)}</span>
                    </label>`).join('')}
            </div>
        </div>`).join('');

        this._modal().innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:1.25rem 1.5rem;border-bottom:1px solid #374151;">
            <div>
                <h3 style="font-weight:700;color:white;font-size:1rem;">${this._e(q.title)}</h3>
                <p style="font-size:.75rem;color:#6b7280;margin-top:.2rem;">
                    ${q.questions.length} questions · Pass: ${q.pass_percentage}%
                </p>
            </div>
            <button onclick="QuizPage.close()"
                    style="background:none;border:none;color:#9ca3af;font-size:1.5rem;cursor:pointer;">×</button>
        </div>
        <div style="padding:1.5rem;overflow-y:auto;max-height:60vh;">
            ${qHtml}
        </div>
        <div style="padding:1.25rem 1.5rem;border-top:1px solid #374151;display:flex;
                    align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.75rem;">
            <p style="font-size:.8rem;color:#6b7280;" id="quiz-ans-counter">
                0 / ${q.questions.length} answered
            </p>
            <button onclick="QuizPage.submit()"
                    style="padding:.65rem 2rem;border-radius:.5rem;font-weight:700;
                           background:#7c3aed;color:white;border:none;cursor:pointer;font-size:.875rem;">
                Submit Quiz
            </button>
        </div>`;
    },

    // ── Select an answer ──────────────────────────────────────────────────────
    _select(questionId, key, labelEl) {
        // Reset all options for this question
        const opts = document.querySelectorAll(`[id^="opt-${questionId}-"]`);
        opts.forEach(el => {
            el.style.borderColor   = '#374151';
            el.style.background    = '#1f2937';
        });
        const dots = document.querySelectorAll(`[id^="dot-${questionId}-"]`);
        dots.forEach(el => {
            el.style.borderColor = '#6b7280';
            el.style.color       = '#9ca3af';
            el.style.background  = 'transparent';
        });

        // Highlight selected
        if (labelEl) {
            labelEl.style.borderColor = '#7c3aed';
            labelEl.style.background  = 'rgba(124,58,237,.15)';
        }
        const dot = document.getElementById(`dot-${questionId}-${key}`);
        if (dot) {
            dot.style.borderColor = '#a78bfa';
            dot.style.color       = 'white';
            dot.style.background  = '#7c3aed';
        }

        this._answers[questionId] = key;

        // Update counter
        const counter = document.getElementById('quiz-ans-counter');
        if (counter) {
            counter.textContent = `${Object.keys(this._answers).length} / ${this._quiz.questions.length} answered`;
        }
    },

    // ── Submit ────────────────────────────────────────────────────────────────
    async submit() {
        const total = (this._quiz.questions || []).length;
        const done  = Object.keys(this._answers).length;

        if (done < total) {
            const proceed = confirm(`You've answered ${done} of ${total} questions. Submit anyway?`);
            if (!proceed) return;
        }

        this._modal().innerHTML = `
            <div style="text-align:center;padding:3rem;color:#9ca3af;">
                <i class="fas fa-spinner fa-spin text-2xl"></i>
                <p style="margin-top:.75rem;">Grading your answers…</p>
            </div>`;

        try {
            // Convert keys to string for API
            const payload = {};
            Object.entries(this._answers).forEach(([k, v]) => { payload[k] = v; });

            const result = await this._req(
                `/courses/${this._courseId}/quizzes/${this._quizId}/submit`,
                {
                    method: 'POST',
                    body:   JSON.stringify(payload),
                }
            );
            this._renderResult(result);
        } catch (e) {
            this._modal().innerHTML = `
                <div style="text-align:center;padding:2rem;">
                    <p style="color:#f87171;">Submission failed: ${e.message}</p>
                    <button onclick="QuizPage._render()"
                            style="margin-top:1rem;padding:.5rem 1.5rem;border-radius:.5rem;
                                   background:#374151;color:#d1d5db;border:none;cursor:pointer;">
                        Try Again
                    </button>
                </div>`;
        }
    },

    // ── Results screen ────────────────────────────────────────────────────────
    _renderResult(result) {
        const passed      = result.passed;
        const score       = result.score;
        const correct     = result.correct_answers;
        const total       = result.total_questions;
        const passColor   = passed ? '#34d399' : '#f87171';
        const passBg      = passed ? 'rgba(16,185,129,.15)' : 'rgba(239,68,68,.15)';
        const passBorder  = passed ? 'rgba(52,211,153,.3)' : 'rgba(248,113,113,.3)';
        const passIcon    = passed ? 'fa-trophy' : 'fa-times-circle';
        const passMsg     = passed ? 'You passed!' : 'Not quite — try again!';

        const breakdownHtml = (result.results_breakdown || []).map(item => {
            const ok   = item.correct;
            const col  = ok ? '#34d399' : '#f87171';
            const icon = ok ? 'fa-check-circle' : 'fa-times-circle';

            // Find question text
            const q = (this._quiz?.questions || []).find(q => String(q.id) === String(item.question_id));

            return `
            <div style="padding:.75rem;border-radius:.5rem;border:1px solid ${ok ? 'rgba(52,211,153,.2)' : 'rgba(248,113,113,.2)'};
                        background:${ok ? 'rgba(16,185,129,.05)' : 'rgba(239,68,68,.05)'};margin-bottom:.5rem;">
                <div style="display:flex;align-items:flex-start;gap:.5rem;">
                    <i class="fas ${icon}" style="color:${col};margin-top:.15rem;flex-shrink:0;"></i>
                    <div style="flex:1;">
                        <p style="font-size:.8rem;color:#d1d5db;">${q ? this._e(q.question) : `Question ${item.question_id}`}</p>
                        <p style="font-size:.75rem;margin-top:.25rem;">
                            <span style="color:#9ca3af;">Your answer: </span>
                            <span style="color:${col};font-weight:600;">${item.your_answer?.toUpperCase() || '—'}</span>
                            ${!ok ? ` <span style="color:#9ca3af;"> · Correct: </span>
                                <span style="color:#34d399;font-weight:600;">${item.correct_answer?.toUpperCase()}</span>` : ''}
                        </p>
                        ${item.explanation ? `<p style="font-size:.73rem;color:#6b7280;margin-top:.2rem;font-style:italic;">${this._e(item.explanation)}</p>` : ''}
                    </div>
                </div>
            </div>`;
        }).join('');

        this._modal().innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:1.25rem 1.5rem;border-bottom:1px solid #374151;">
            <h3 style="font-weight:700;color:white;">Quiz Results</h3>
            <button onclick="QuizPage.close()"
                    style="background:none;border:none;color:#9ca3af;font-size:1.5rem;cursor:pointer;">×</button>
        </div>

        <div style="padding:2rem;text-align:center;border-bottom:1px solid #374151;">
            <div style="display:inline-flex;flex-direction:column;align-items:center;gap:.5rem;
                        padding:1.5rem 2.5rem;border-radius:1rem;
                        background:${passBg};border:1px solid ${passBorder};">
                <i class="fas ${passIcon}" style="color:${passColor};font-size:2.5rem;"></i>
                <p style="font-size:1.5rem;font-weight:800;color:${passColor};">${score}%</p>
                <p style="font-weight:700;color:${passColor};">${passMsg}</p>
                <p style="font-size:.8rem;color:#9ca3af;">${correct} / ${total} correct</p>
            </div>
        </div>

        <div style="padding:1.25rem 1.5rem;max-height:40vh;overflow-y:auto;">
            <p style="font-size:.8rem;font-weight:600;color:#6b7280;text-transform:uppercase;
                      letter-spacing:.05em;margin-bottom:.75rem;">Answer Breakdown</p>
            ${breakdownHtml}
        </div>

        <div style="padding:1.25rem 1.5rem;border-top:1px solid #374151;display:flex;gap:.75rem;justify-content:flex-end;">
            ${!passed ? `<button onclick="QuizPage._render()"
                style="padding:.6rem 1.25rem;border-radius:.5rem;font-size:.85rem;
                       background:#1f2937;color:#9ca3af;border:1px solid #374151;cursor:pointer;">
                Retry Quiz
            </button>` : ''}
            <button onclick="QuizPage.close()"
                style="padding:.6rem 1.5rem;border-radius:.5rem;font-size:.85rem;
                       font-weight:700;background:#7c3aed;color:white;border:none;cursor:pointer;">
                ${passed ? '🎉 Continue' : 'Close'}
            </button>
        </div>`;
    },

    // ── Modal management ──────────────────────────────────────────────────────
    get _modalEl() {
        let el = document.getElementById('quiz-modal-overlay');
        if (!el) {
            el = document.createElement('div');
            el.id = 'quiz-modal-overlay';
            el.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:10002;display:flex;align-items:center;justify-content:center;padding:1rem;';
            el.addEventListener('click', e => { if (e.target === el) QuizPage.close(); });

            const inner = document.createElement('div');
            inner.id = 'quiz-modal-inner';
            inner.style.cssText = 'background:#111827;border-radius:1rem;width:100%;max-width:640px;max-height:90vh;overflow:hidden;display:flex;flex-direction:column;border:1px solid #374151;';
            el.appendChild(inner);
        }
        return el;
    },

    _modal() {
        return document.getElementById('quiz-modal-inner') || this._modalEl.firstChild;
    },

    close() {
        document.getElementById('quiz-modal-overlay')?.remove();
    },

    // ── Request helper ────────────────────────────────────────────────────────
    async _req(endpoint, options = {}) {
        const token = localStorage.getItem('pipways_token');
        const headers = {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...options.headers,
        };
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
};

window.QuizPage = QuizPage;
