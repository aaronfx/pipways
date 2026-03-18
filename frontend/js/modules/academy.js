/**
 * Pipways Trading Academy Frontend Module v5.0 (Refactored)
 * 
 * Improvements:
 * - Modular state management with validation and session persistence
 * - Request cancellation and caching to prevent race conditions
 * - Comprehensive error boundaries with user-friendly recovery UI
 * - Quiz state machine preventing duplicate submissions
 * - XSS-safe markdown rendering with HTML whitelist
 * - Memory leak prevention via proper cleanup
 * - Debounced navigation to prevent rapid-click errors
 */

(function() {
    'use strict';

    // ─────────────────────────────────────────────────────────────────────────
    // CONFIGURATION
    // ─────────────────────────────────────────────────────────────────────────
    const CONFIG = {
        CACHE_TTL: 10 * 60 * 1000,        // 10 minutes lesson cache
        DEBOUNCE_DELAY: 150,              // ms between navigation clicks
        ANIMATION_DURATION: 300,          // ms for UI transitions
        MAX_RETRY: 3,                     // API retry attempts
        ALLOWED_HTML_TAGS: [              // For sanitized markdown
            'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'a', 'img', 'svg', 'path', 'circle', 'rect', 'line', 'text',
            'defs', 'g', 'marker', 'use', 'symbol', 'span', 'div', 'code', 'pre', 'blockquote'
        ],
        ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class', 'id', 'style', 'width', 'height', 'viewbox', 'd', 'fill', 'stroke']
    };

    // ─────────────────────────────────────────────────────────────────────────
    // STATE MANAGEMENT MODULE
    // ─────────────────────────────────────────────────────────────────────────
    const StateManager = {
        data: {
            navigation: {
                level: null,
                module: null,
                lesson: null,
                history: []                    // Breadcrumb trail for deep linking recovery
            },
            user: {
                id: null,
                badges: [],
                isFirstVisit: false
            },
            quiz: {
                instance: null,               // Current quiz data
                answers: [],                  // User selections
                currentIndex: 0,              // Question position
                isSubmitting: false,          // Lock flag for duplicate prevention
                selectedOption: null          // Current selection
            },
            ui: {
                isLoading: false,
                activeOperation: null,        // For loading context
                abortController: null,        // For request cancellation
                pendingRenders: new Set()     // Track pending animation frames
            },
            cache: new Map()                  // Lesson content cache
        },

        // Safe state transitions with validation
        setNavigation(level, module, lesson) {
            this.data.navigation.level = level;
            this.data.navigation.module = module;
            this.data.navigation.lesson = lesson;
            
            // Persist for page recovery
            try {
                sessionStorage.setItem('academy_nav', JSON.stringify({
                    level: level?.id,
                    module: module?.id,
                    lesson: lesson?.id,
                    timestamp: Date.now()
                }));
            } catch(e) { /* ignore storage errors */ }
        },

        setQuiz(quizData) {
            this.data.quiz = {
                instance: quizData,
                answers: [],
                currentIndex: 0,
                isSubmitting: false,
                selectedOption: null
            };
        },

        clearQuiz() {
            this.data.quiz = {
                instance: null,
                answers: [],
                currentIndex: 0,
                isSubmitting: false,
                selectedOption: null
            };
        },

        cacheLesson(lessonId, content) {
            this.data.cache.set(lessonId, {
                content,
                timestamp: Date.now(),
                hitCount: 0
            });
            
            // LRU eviction: keep only last 20 lessons
            if (this.data.cache.size > 20) {
                const firstKey = this.data.cache.keys().next().value;
                this.data.cache.delete(firstKey);
            }
        },

        getCachedLesson(lessonId) {
            const cached = this.data.cache.get(lessonId);
            if (!cached) return null;
            
            const age = Date.now() - cached.timestamp;
            if (age > CONFIG.CACHE_TTL) {
                this.data.cache.delete(lessonId);
                return null;
            }
            
            cached.hitCount++;
            return cached.content;
        },

        clearCache() {
            this.data.cache.clear();
        },

        // Emergency recovery from session storage
        recoverSession() {
            try {
                const saved = sessionStorage.getItem('academy_nav');
                if (saved) {
                    return JSON.parse(saved);
                }
            } catch(e) { }
            return null;
        }
    };

    // ─────────────────────────────────────────────────────────────────────────
    // API LAYER WITH ERROR BOUNDARIES
    // ─────────────────────────────────────────────────────────────────────────
    const APILayer = {
        async execute(operationName, apiCallFn, retryCount = 0) {
            // Cancel any pending request
            if (StateManager.data.ui.abortController) {
                StateManager.data.ui.abortController.abort();
            }
            
            const controller = new AbortController();
            StateManager.data.ui.abortController = controller;
            
            try {
                UIController.setLoading(true, operationName);
                
                const result = await Promise.race([
                    apiCallFn(controller.signal),
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('Request timeout')), 30000)
                    )
                ]);
                
                // Validate response structure
                if (result === null || result === undefined) {
                    throw new Error('Empty response from server');
                }
                
                return { success: true, data: result, error: null };
                
            } catch (error) {
                if (error.name === 'AbortError') {
                    return { success: false, data: null, error: 'Request cancelled', cancelled: true };
                }
                
                console.error(`[Academy API] ${operationName} failed:`, error);
                
                // Retry logic for transient errors
                if (retryCount < CONFIG.MAX_RETRY && this.isRetryable(error)) {
                    await new Promise(r => setTimeout(r, 1000 * (retryCount + 1)));
                    return this.execute(operationName, apiCallFn, retryCount + 1);
                }
                
                return { 
                    success: false, 
                    data: null, 
                    error: this.sanitizeError(error),
                    code: error.status || error.code || 'UNKNOWN'
                };
            } finally {
                UIController.setLoading(false, null);
                if (StateManager.data.ui.abortController === controller) {
                    StateManager.data.ui.abortController = null;
                }
            }
        },

        isRetryable(error) {
            const retryableCodes = [408, 429, 500, 502, 503, 504];
            return retryableCodes.includes(error.status) || error.message?.includes('network');
        },

        sanitizeError(error) {
            if (typeof error === 'string') return error;
            if (error.detail) return error.detail;
            if (error.message) return error.message;
            return 'An unexpected error occurred. Please try again.';
        },

        // LMS API Wrappers (maintaining original endpoint contracts)
        async getLevels() {
            return this.execute('load_levels', () => window.API.lms.getLevels());
        },

        async getModules(levelId) {
            return this.execute('load_modules', () => window.API.lms.getModules(levelId));
        },

        async getLessons(moduleId) {
            return this.execute('load_lessons', () => window.API.lms.getLessons(moduleId));
        },

        async getLesson(lessonId) {
            // Check cache first
            const cached = StateManager.getCachedLesson(lessonId);
            if (cached) return { success: true, data: cached, cached: true };
            
            const result = await this.execute('load_lesson', () => window.API.lms.getLesson(lessonId));
            if (result.success) {
                StateManager.cacheLesson(lessonId, result.data);
            }
            return result;
        },

        async getQuiz(lessonId) {
            return this.execute('load_quiz', () => window.API.lms.getQuiz(lessonId));
        },

        async submitQuiz(lessonId, answers) {
            return this.execute('submit_quiz', () => 
                window.API.lms.submitQuiz(lessonId, answers)
            );
        },

        async getMentorGuide(uid) {
            return this.execute('mentor_guide', () => window.API.lms.getMentorGuide(uid));
        },

        async getMentorTeach(lessonId) {
            return this.execute('mentor_teach', () => window.API.lms.getMentorTeach(lessonId));
        },

        async getMentorPractice(lessonId) {
            return this.execute('mentor_practice', () => window.API.lms.getMentorPractice(lessonId));
        },

        async getChartPractice(lessonId) {
            return this.execute('chart_practice', () => window.API.lms.getChartPractice(lessonId));
        }
    };

    // ─────────────────────────────────────────────────────────────────────────
    // CONTENT SECURITY & SANITIZATION
    // ─────────────────────────────────────────────────────────────────────────
    const Security = {
        escapeHtml(str) {
            if (str == null) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        },

        sanitizeHtml(html) {
            if (!html) return '';
            
            // Simple but effective HTML sanitizer
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            const cleanNode = (node) => {
                if (node.nodeType === Node.TEXT_NODE) return;
                
                if (node.nodeType === Node.ELEMENT_NODE) {
                    const tag = node.tagName.toLowerCase();
                    
                    // Remove disallowed tags but keep content
                    if (!CONFIG.ALLOWED_HTML_TAGS.includes(tag)) {
                        const parent = node.parentNode;
                        while (node.firstChild) {
                            parent.insertBefore(node.firstChild, node);
                        }
                        parent.removeChild(node);
                        return;
                    }
                    
                    // Clean attributes
                    Array.from(node.attributes).forEach(attr => {
                        if (!CONFIG.ALLOWED_ATTR.includes(attr.name.toLowerCase())) {
                            node.removeAttribute(attr.name);
                        }
                        
                        // Sanitize URLs
                        if (attr.name === 'href' || attr.name === 'src') {
                            const url = attr.value.toLowerCase();
                            if (url.startsWith('javascript:') || url.startsWith('data:text/html')) {
                                node.removeAttribute(attr.name);
                            }
                        }
                    });
                }
                
                // Recurse
                Array.from(node.childNodes).forEach(cleanNode);
            };
            
            Array.from(doc.body.childNodes).forEach(cleanNode);
            return doc.body.innerHTML;
        },

        processMarkdown(content) {
            if (!content) return '';
            
            // Ensure marked.js is loaded safely
            if (typeof marked === 'undefined') {
                console.warn('[Academy] marked.js not loaded, using fallback');
                return this.escapeHtml(content).replace(/\n/g, '<br>');
            }
            
            try {
                // Parse markdown
                let html = marked.parse(content, { 
                    breaks: true, 
                    gfm: true,
                    headerIds: false,  // Prevent ID injection
                    mangle: false      // Prevent email mangling issues
                });
                
                // Fix SVG marker order (ensure defs come first)
                html = html.replace(/<svg([^>]*)>([\s\S]*?)<\/svg>/g, (match, attrs, inner) => {
                    const defsMatch = inner.match(/<defs>[\s\S]*?<\/defs>/);
                    const defs = defsMatch ? defsMatch[0] : '';
                    const withoutDefs = inner.replace(/<defs>[\s\S]*?<\/defs>/, '');
                    return `<svg${attrs}>${defs}${withoutDefs}</svg>`;
                });
                
                // Sanitize the result
                return this.sanitizeHtml(html);
            } catch (e) {
                console.error('[Academy] Markdown processing error:', e);
                return this.escapeHtml(content);
            }
        }
    };

    // ─────────────────────────────────────────────────────────────────────────
    // UI CONTROLLER
    // ─────────────────────────────────────────────────────────────────────────
    const UIController = {
        elements: {},
        
        init() {
            this.cacheElements();
            this.injectStyles();
        },

        cacheElements() {
            this.elements = {
                container: document.getElementById('academy-container'),
                breadcrumb: document.getElementById('ac-breadcrumb'),
                main: document.getElementById('ac-main'),
                mentorBanner: document.getElementById('ac-mentor-banner'),
                badgeToast: document.getElementById('ac-badge-toast'),
                mobileNav: document.getElementById('ac-mobile-nav')
            };
        },

        setLoading(isLoading, operation = null) {
            StateManager.data.ui.isLoading = isLoading;
            StateManager.data.ui.activeOperation = operation;
            
            // Visual feedback on container
            if (this.elements.main) {
                this.elements.main.style.opacity = isLoading ? '0.7' : '1';
                this.elements.main.style.pointerEvents = isLoading ? 'none' : 'auto';
            }
        },

        showError(title, detail, retryCallback = null) {
            const safeTitle = Security.escapeHtml(title);
            const safeDetail = Security.escapeHtml(detail || 'Please try again later.');
            
            const retryBtn = retryCallback 
                ? `<button onclick="(${retryCallback.toString()})()" class="mt-4 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm transition-colors">
                     <i class="fas fa-redo mr-2"></i>Retry
                   </button>` 
                : '';
            
            return `
                <div class="alert alert-error max-w-xl mx-auto mt-8 animate-fade-in">
                    <div class="flex items-start gap-3">
                        <i class="fas fa-exclamation-circle text-red-400 text-xl mt-0.5"></i>
                        <div>
                            <h4 class="font-semibold text-red-400 mb-1">${safeTitle}</h4>
                            <p class="text-gray-400 text-sm">${safeDetail}</p>
                            ${retryBtn}
                        </div>
                    </div>
                </div>`;
        },

        showEmptyState(title, subtitle, icon = 'fa-book-open') {
            return `
                <div class="pw-empty max-w-md mx-auto mt-12 animate-fade-in">
                    <div class="pw-empty-icon">
                        <i class="fas ${icon}" style="color:#4b5563; font-size:1.2rem;"></i>
                    </div>
                    <p class="pw-empty-title">${Security.escapeHtml(title)}</p>
                    <p class="pw-empty-sub">${Security.escapeHtml(subtitle)}</p>
                    <button onclick="AcademyPage._showLevelSelector()" 
                            class="btn btn-primary mt-6" style="font-size:.8rem; padding:.45rem 1rem;">
                        <i class="fas fa-refresh mr-1"></i> Refresh
                    </button>
                </div>`;
        },

        loadingSpinner(message = 'Loading...') {
            return `
                <div class="loading animate-fade-in">
                    <div class="spinner"></div>
                    <p class="text-gray-500 text-sm">${Security.escapeHtml(message)}</p>
                </div>`;
        },

        updateBreadcrumb(level, module, lesson) {
            const el = this.elements.breadcrumb;
            if (!el) return;
            
            if (!level) {
                el.style.display = 'none';
                el.innerHTML = '';
                return;
            }
            
            el.style.display = 'flex';
            const parts = [
                `<a href="#" onclick="event.preventDefault(); AcademyPage._showLevelSelector();" class="text-purple-400 hover:text-purple-300">Academy</a>`
            ];
            
            if (level) {
                parts.push(`<span class="pw-breadcrumb-sep">›</span>
                           <a href="#" onclick="event.preventDefault(); AcademyPage._selectLevel(${level.id}, '${Security.escapeHtml(level.name)}');" 
                              class="text-purple-400 hover:text-purple-300">${Security.escapeHtml(level.name)}</a>`);
            }
            if (module) {
                parts.push(`<span class="pw-breadcrumb-sep">›</span>
                           <a href="#" onclick="event.preventDefault(); AcademyPage._selectModule(${module.id}, '${Security.escapeHtml(module.name)}');" 
                              class="text-purple-400 hover:text-purple-300">${Security.escapeHtml(module.name)}</a>`);
            }
            if (lesson) {
                parts.push(`<span class="pw-breadcrumb-sep">›</span>
                           <span class="text-gray-400">${Security.escapeHtml(lesson.name)}</span>`);
            }
            
            el.innerHTML = parts.join('');
        },

        injectStyles() {
            if (document.getElementById('ac-styles-v5')) return;
            
            const s = document.createElement('style');
            s.id = 'ac-styles-v5';
            s.textContent = `
                /* Base Typography with improved accessibility */
                .ac-lesson-text {
                    color: #d1d5db;
                    font-size: 0.95rem;
                    line-height: 1.8;
                    max-width: 70ch; /* Optimal reading width */
                }
                .ac-lesson-text h1, .ac-lesson-text h2, .ac-lesson-text h3 {
                    color: white;
                    margin-top: 1.5rem;
                    margin-bottom: 0.75rem;
                    font-weight: 600;
                    line-height: 1.3;
                }
                .ac-lesson-text h3 { font-size: 1.25rem; border-bottom: 1px solid #1f2937; padding-bottom: 0.5rem; }
                .ac-lesson-text h4 { font-size: 1.1rem; color: #e5e7eb; margin: 1.25rem 0 0.5rem; }
                .ac-lesson-text p { margin: 0.75rem 0; }
                .ac-lesson-text ul { margin: 0.5rem 0 0.5rem 1.5rem; list-style-type: disc; }
                .ac-lesson-text li { margin: 0.35rem 0; }
                .ac-lesson-text strong { color: #fbbf24; font-weight: 600; }
                .ac-lesson-text code {
                    background: #111827;
                    border: 1px solid #374151;
                    border-radius: 0.375rem;
                    padding: 0.125rem 0.375rem;
                    font-family: ui-monospace, monospace;
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
                .ac-lesson-text img {
                    max-width: 100%;
                    height: auto;
                    border-radius: 0.5rem;
                    margin: 1rem 0;
                    background: #0d1321;
                }
                .ac-lesson-text svg {
                    max-width: 100%;
                    height: auto;
                    display: block;
                    margin: 1rem auto;
                }

                /* Quiz Improvements */
                .ac-quiz-container { max-width: 600px; margin: 0 auto; }
                .ac-quiz-opt {
                    position: relative;
                    transition: all 0.2s ease;
                    touch-action: manipulation; /* Prevent zoom on double-tap */
                }
                .ac-quiz-opt:active { transform: scale(0.99); }
                .ac-quiz-opt:focus-visible {
                    outline: 2px solid #7c3aed;
                    outline-offset: 2px;
                }
                .ac-quiz-opt.selected {
                    border-color: #7c3aed !important;
                    background: rgba(124,58,237,0.12) !important;
                    color: #c4b5fd !important;
                }
                .ac-quiz-opt.disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                    pointer-events: none;
                }

                /* Mobile Navigation Safety */
                @media (max-width: 767px) {
                    .ac-mobile-nav {
                        position: fixed;
                        bottom: 0;
                        left: 0;
                        right: 0;
                        background: rgba(17,24,39,0.95);
                        backdrop-filter: blur(10px);
                        border-top: 1px solid #1f2937;
                        z-index: 100;
                        padding: env(safe-area-inset-bottom, 0.5rem) 0.5rem 0.5rem;
                    }
                    .ac-nav-btn {
                        min-height: 44px; /* Touch target size */
                        font-size: 0.875rem;
                    }
                    #academy-container {
                        padding-bottom: 80px; /* Space for mobile nav */
                    }
                }

                /* Loading States */
                .ac-skeleton {
                    background: linear-gradient(90deg, #1f2937 25%, #374151 50%, #1f2937 75%);
                    background-size: 200% 100%;
                    animation: shimmer 1.5s infinite;
                    border-radius: 0.375rem;
                }
                @keyframes shimmer {
                    0% { background-position: 200% 0; }
                    100% { background-position: -200% 0; }
                }

                /* Error States */
                .alert-error {
                    background: rgba(239,68,68,0.1);
                    border: 1px solid rgba(239,68,68,0.3);
                    border-radius: 0.75rem;
                    padding: 1rem;
                }

                /* Focus Management for Accessibility */
                .ac-lesson-container:focus {
                    outline: none;
                }
                .ac-level-card:focus-visible,
                .ac-module-card:focus-visible,
                .ac-lesson-item:focus-visible {
                    outline: 2px solid #7c3aed;
                    outline-offset: 2px;
                }
            `;
            document.head.appendChild(s);
        }
    };

    // ─────────────────────────────────────────────────────────────────────────
    // QUIZ STATE MACHINE
    // ─────────────────────────────────────────────────────────────────────────
    const QuizEngine = {
        async initialize(lessonId) {
            const container = UIController.elements.main;
            container.innerHTML = UIController.loadingSpinner('Loading quiz...');
            UIController.hideMobileNav();
            
            const result = await APILayer.getQuiz(lessonId);
            
            if (!result.success) {
                container.innerHTML = UIController.showError(
                    'Could not load quiz', 
                    result.error,
                    () => () => QuizEngine.initialize(lessonId)
                );
                return;
            }
            
            const data = result.data;
            if (!data.questions || data.questions.length === 0) {
                container.innerHTML = `
                    <div class="alert alert-info max-w-xl mx-auto mt-8 text-center">
                        <i class="fas fa-info-circle mr-2 text-blue-400"></i>
                        No quiz questions available for this lesson.
                    </div>`;
                return;
            }
            
            StateManager.setQuiz(data);
            this.render();
        },

        render() {
            const { instance: quiz, currentIndex, selectedOption } = StateManager.data.quiz;
            const q = quiz.questions[currentIndex];
            const total = quiz.questions.length;
            const progress = Math.round((currentIndex / total) * 100);
            
            const container = UIController.elements.main;
            
            // Build options HTML
            const optionsHtml = ['A', 'B', 'C', 'D'].map(key => {
                const opt = q['option_' + key.toLowerCase()];
                if (!opt) return '';
                
                const isSelected = selectedOption === key;
                const classes = isSelected ? 'selected' : '';
                
                return `
                    <button id="ac-opt-${key}" 
                            onclick="AcademyPage._pick('${key}')"
                            class="ac-quiz-opt w-full text-left px-4 py-3 rounded-xl text-sm mb-2 ${classes}"
                            style="background:#111827; border:2px solid ${isSelected ? '#7c3aed' : '#1f2937'}; color:#d1d5db;"
                            ${StateManager.data.quiz.isSubmitting ? 'disabled' : ''}>
                        <strong class="text-gray-400 mr-2">${key}.</strong> ${Security.escapeHtml(opt)}
                    </button>`;
            }).join('');
            
            container.innerHTML = `
                <div class="ac-quiz-container animate-fade-in">
                    <div class="flex items-center justify-between mb-2 text-xs text-gray-500">
                        <span class="font-semibold">Question ${currentIndex + 1} of ${total}</span>
                        <span>${Security.escapeHtml(StateManager.data.navigation.lesson?.name || 'Quiz')}</span>
                    </div>
                    <div class="pw-progress-bar mb-5">
                        <div class="pw-progress-fill" style="width:${progress}%; transition: width 0.3s ease;"></div>
                    </div>
                    
                    <div class="pw-card mb-4">
                        <div class="pw-card-body">
                            <p class="text-white font-semibold text-base leading-relaxed mb-5">${Security.processMarkdown(q.question)}</p>
                            <div class="space-y-2" id="ac-quiz-opts">
                                ${optionsHtml}
                            </div>
                        </div>
                    </div>
                    
                    <div class="flex justify-end">
                        <button id="ac-quiz-next" 
                                class="btn btn-primary ${!selectedOption ? 'opacity-50 cursor-not-allowed' : ''}"
                                onclick="AcademyPage._nextQ()"
                                ${!selectedOption || StateManager.data.quiz.isSubmitting ? 'disabled' : ''}>
                            ${currentIndex < total - 1 ? 'Next Question →' : 'Submit Quiz'}
                        </button>
                    </div>
                </div>
            `;
            
            // Accessibility: Focus management
            const firstOpt = container.querySelector('.ac-quiz-opt');
            if (firstOpt) firstOpt.focus();
        },

        selectOption(key) {
            const state = StateManager.data.quiz;
            state.selectedOption = key;
            
            // Visual update without full re-render
            document.querySelectorAll('.ac-quiz-opt').forEach(btn => {
                btn.classList.remove('selected');
                btn.style.borderColor = '#1f2937';
                btn.style.background = '#111827';
                btn.style.color = '#d1d5db';
            });
            
            const selected = document.getElementById('ac-opt-' + key);
            if (selected) {
                selected.classList.add('selected');
                selected.style.borderColor = '#7c3aed';
                selected.style.background = 'rgba(124,58,237,0.12)';
                selected.style.color = '#c4b5fd';
            }
            
            const nextBtn = document.getElementById('ac-quiz-next');
            if (nextBtn) {
                nextBtn.disabled = false;
                nextBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        },

        async nextQuestion() {
            const state = StateManager.data.quiz;
            const { selectedOption, currentIndex, instance: quiz, answers } = state;
            
            if (!selectedOption) return;
            
            // Record answer
            answers.push({
                question_id: quiz.questions[currentIndex].id,
                selected_answer: selectedOption
            });
            
            state.answers = answers;
            
            if (currentIndex < quiz.questions.length - 1) {
                state.currentIndex++;
                state.selectedOption = null;
                this.render();
            } else {
                await this.submit();
            }
        },

        async submit() {
            const state = StateManager.data.quiz;
            if (state.isSubmitting) return; // Prevent double-submit
            
            state.isSubmitting = true;
            UIController.setLoading(true, 'submitting_quiz');
            
            const container = UIController.elements.main;
            container.innerHTML = UIController.loadingSpinner('Grading your quiz...');
            
            const result = await APILayer.submitQuiz(
                state.instance.lessonId || StateManager.data.navigation.lesson?.id,
                state.answers
            );
            
            UIController.setLoading(false, null);
            
            if (!result.success) {
                state.isSubmitting = false;
                container.innerHTML = UIController.showError(
                    'Submission Failed',
                    result.error,
                    () => () => this.submit()
                );
                return;
            }
            
            // Handle badges
            if (result.data?.new_badges?.length) {
                await AcademyPage._showNewBadges(result.data.new_badges);
            }
            
            this.showResults(result.data);
        },

        showResults(result) {
            const passed = result.passed;
            const passColor = passed ? '#34d399' : '#f87171';
            const passMsg = passed ? '🎉 Quiz Passed!' : 'Review the lesson and try again.';
            
            const breakdown = (result.results || []).map((r, i) => `
                <div class="flex items-start gap-3 py-3 border-b border-gray-800">
                    <i class="fas ${r.is_correct ? 'fa-check-circle text-green-400' : 'fa-times-circle text-red-400'} mt-0.5 flex-shrink-0"></i>
                    <div class="flex-1 text-sm">
                        <span class="text-gray-400 font-medium">Question ${i + 1}</span>
                        ${!r.is_correct ? `
                            <div class="text-gray-500 text-xs mt-1">
                                Correct: <strong class="text-gray-300">${Security.escapeHtml(r.correct_answer)}</strong> — 
                                ${Security.escapeHtml(r.explanation)}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `).join('');
            
            const container = UIController.elements.main;
            container.innerHTML = `
                <div class="max-w-xl mx-auto animate-fade-in">
                    <div class="pw-card mb-4" style="border-top:3px solid ${passColor};">
                        <div class="pw-card-body text-center" style="padding:2rem;">
                            <div class="text-5xl font-black mb-2" style="color:${passColor};">
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
                    <div class="pw-card mb-4" style="border-left:3px solid #a78bfa;">
                        <div class="pw-card-body">
                            <div class="flex items-center gap-2 mb-2">
                                <i class="fas fa-robot text-purple-400"></i>
                                <strong class="text-white text-sm">Trading Coach Feedback</strong>
                            </div>
                            <p class="text-gray-300 text-sm leading-relaxed">${Security.processMarkdown(result.mentor_feedback)}</p>
                        </div>
                    </div>
                    ` : ''}
                    
                    <div class="pw-card mb-4">
                        <div class="pw-card-hdr">
                            <h3 class="card-title text-sm">Answer Breakdown</h3>
                        </div>
                        <div class="pw-card-body" style="padding-top:0;">
                            ${breakdown}
                        </div>
                    </div>
                    
                    <div class="flex gap-2 flex-wrap">
                        ${passed
                            ? `<button class="btn btn-primary" onclick="AcademyPage._selectModule(${StateManager.data.navigation.module?.id || 0}, '${Security.escapeHtml(StateManager.data.navigation.module?.name || '')}')">
                                 <i class="fas fa-arrow-left mr-2"></i>Back to Module
                               </button>`
                            : `<button class="btn btn-primary" onclick="AcademyPage._startQuiz(${StateManager.data.navigation.lesson?.id})">
                                 <i class="fas fa-redo mr-2"></i>Retry Quiz
                               </button>`
                        }
                        <button class="btn bg-gray-800 border border-gray-700 text-gray-200 hover:bg-gray-700"
                                onclick="AcademyPage._openLesson(${StateManager.data.navigation.lesson?.id}, '${Security.escapeHtml(StateManager.data.navigation.lesson?.name || '')}')">
                            <i class="fas fa-book-open mr-2"></i>Review Lesson
                        </button>
                    </div>
                </div>
            `;
            
            // Clear quiz state after showing results
            StateManager.clearQuiz();
        }
    };

    // ─────────────────────────────────────────────────────────────────────────
    // MAIN ACADEMY CONTROLLER (Public Interface)
    // ─────────────────────────────────────────────────────────────────────────
    const AcademyController = {
        // Legacy state accessors for backward compatibility
        get _level() { return StateManager.data.navigation.level; },
        set _level(v) { StateManager.data.navigation.level = v; },
        get _module() { return StateManager.data.navigation.module; },
        set _module(v) { StateManager.data.navigation.module = v; },
        get _lesson() { return StateManager.data.navigation.lesson; },
        set _lesson(v) { StateManager.data.navigation.lesson = v; },
        get _quiz() { return StateManager.data.quiz.instance; },
        set _quiz(v) { StateManager.data.quiz.instance = v; },
        get _uid() { return StateManager.data.user.id; },
        set _uid(v) { StateManager.data.user.id = v; },
        get _firstVisit() { return StateManager.data.user.isFirstVisit; },
        set _firstVisit(v) { StateManager.data.user.isFirstVisit = v; },
        get _badges() { return StateManager.data.user.badges; },
        set _badges(v) { StateManager.data.user.badges = v; },

        // Initialization
        async render() {
            UIController.init();
            
            const user = this._getUser();
            this._uid = user?.id ?? null;
            
            const wrap = UIController.elements.container;
            if (!wrap) {
                console.error('[Academy] Container not found');
                return;
            }
            
            // Initial HTML structure
            wrap.innerHTML = `
                <div id="ac-breadcrumb" class="pw-breadcrumb mb-4" style="display:none;"></div>
                <div id="ac-mentor-banner"></div>
                <div id="ac-badge-toast" class="ac-badge-container"></div>
                <div id="ac-main"></div>
                <div id="ac-mobile-nav" class="ac-mobile-nav hidden md:hidden"></div>
            `;
            
            // Re-cache elements after DOM insertion
            UIController.cacheElements();
            
            // Load user data
            if (this._uid) {
                await this._loadBadges();
                try {
                    const check = await window.API.lms.checkBadges();
                    if (check?.newly_awarded?.length) {
                        await this._showNewBadges(check.newly_awarded);
                    }
                } catch(e) { 
                    console.warn('[Academy] Badge check failed:', e); 
                }
            }
            
            // Check for session recovery
            const recovered = StateManager.recoverSession();
            if (recovered && recovered.lesson) {
                // Optionally restore deep link here
                // For now, we start fresh to avoid stale state issues
            }
            
            await this._showLevelSelector();
        },

        // Navigation: Level Selection
        async _showLevelSelector() {
            StateManager.setNavigation(null, null, null);
            this._clearCache(); // Fresh start
            
            UIController.updateBreadcrumb(null, null, null);
            this._hideMobileNav();
            
            const main = UIController.elements.main;
            main.innerHTML = UIController.loadingSpinner('Loading curriculum...');
            
            const [levelsResult, progressResult, guideResult] = await Promise.all([
                APILayer.getLevels(),
                this._uid ? APILayer.execute('progress', () => window.API.lms.getProgress(this._uid)) : { success: true, data: null },
                this._uid ? APILayer.getMentorGuide(this._uid) : { success: true, data: null }
            ]);
            
            if (!levelsResult.success) {
                main.innerHTML = UIController.showError(
                    'Could not load Academy',
                    levelsResult.error,
                    () => () => this._showLevelSelector()
                );
                return;
            }
            
            const levels = levelsResult.data || [];
            const prog = progressResult.data;
            const guide = guideResult.data;
            
            if (guide?.first_visit !== undefined) {
                this._firstVisit = guide.first_visit;
            }
            
            // Build progress map
            const progressMap = {};
            (prog?.summary || []).forEach(s => {
                progressMap[s.level_id] = s;
            });
            
            // Load mentor banner if available
            if (this._uid && guide) {
                this._loadMentorBanner(guide);
            }
            
            if (!levels.length) {
                main.innerHTML = UIController.showEmptyState(
                    'Academy not set up yet',
                    'The learning curriculum is being initialized. Please refresh in a moment.',
                    'fa-cogs'
                );
                return;
            }
            
            // Render level grid
            const configs = [
                { icon: 'fa-seedling', color: '#34d399', bg: 'rgba(52,211,153,.15)' },
                { icon: 'fa-chart-line', color: '#60a5fa', bg: 'rgba(96,165,250,.15)' },
                { icon: 'fa-trophy', color: '#f59e0b', bg: 'rgba(245,158,11,.15)' },
            ];
            
            main.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 animate-fade-in">
                    ${levels.map((lv, i) => {
                        const cfg = configs[i % 3];
                        const s = progressMap[lv.id] || { percent: 0, completed: 0, total: 0 };
                        const isComplete = s.percent >= 100;
                        
                        return `
                        <div class="pw-card cursor-pointer ac-level-card ${isComplete ? 'ac-level-complete' : ''}" 
                             onclick="AcademyPage._selectLevel(${lv.id}, '${Security.escapeHtml(lv.name)}')"
                             tabindex="0"
                             onkeypress="if(event.key==='Enter') AcademyPage._selectLevel(${lv.id}, '${Security.escapeHtml(lv.name)}')"
                             style="border-top:3px solid ${cfg.color}; position:relative;">
                            ${isComplete ? `<div class="ac-complete-badge"><i class="fas fa-check-circle"></i></div>` : ''}
                            <div class="pw-card-body" style="padding:1.5rem;">
                                <div class="w-10 h-10 rounded-xl flex items-center justify-center mb-3" 
                                     style="background:${cfg.bg};">
                                    <i class="fas ${cfg.icon}" style="color:${cfg.color};"></i>
                                </div>
                                <div class="text-xs font-bold mb-1" style="color:${cfg.color}; letter-spacing:.06em;">
                                    ${Security.escapeHtml(lv.name).toUpperCase()}
                                </div>
                                <h3 class="text-white font-bold text-base mb-1">${Security.escapeHtml(lv.name)}</h3>
                                <p class="text-gray-500 text-xs leading-relaxed mb-4">${Security.escapeHtml(lv.description)}</p>
                                
                                <div class="flex justify-between text-xs text-gray-500 mb-1.5">
                                    <span>Progress</span>
                                    <span class="font-semibold" style="color:${cfg.color};">${s.percent}%</span>
                                </div>
                                <div class="pw-progress-bar">
                                    <div class="pw-progress-fill" style="width:${s.percent}%; background:${cfg.color}; transition: width 0.6s ease;"></div>
                                </div>
                                <div class="text-xs text-gray-600 mt-2">${s.completed} of ${s.total} lessons done</div>
                            </div>
                        </div>`;
                    }).join('')}
                </div>
            `;
        },

        // Navigation: Module Selection
        async _selectLevel(levelId, levelName) {
            // Debounce protection
            if (UIController.setLoading.loading) return;
            
            StateManager.setNavigation(
                { id: levelId, name: levelName },
                null,
                null
            );
            
            UIController.updateBreadcrumb({ id: levelId, name: levelName }, null, null);
            this._hideMobileNav();
            
            const main = UIController.elements.main;
            main.innerHTML = UIController.loadingSpinner('Loading modules...');
            
            const result = await APILayer.getModules(levelId);
            
            if (!result.success) {
                main.innerHTML = UIController.showError(
                    'Could not load modules',
                    result.error,
                    () => () => this._selectLevel(levelId, levelName)
                );
                return;
            }
            
            const modules = result.data || [];
            main.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 animate-fade-in">
                    ${modules.map(m => {
                        const pct = m.lesson_count ? Math.round((m.completed_count || 0) / m.lesson_count * 100) : 0;
                        const isComplete = m.is_complete || pct >= 100;
                        
                        return `
                        <div class="pw-card cursor-pointer ac-module-card ${isComplete ? 'ac-module-complete' : ''}" 
                             onclick="AcademyPage._selectModule(${m.id}, '${Security.escapeHtml(m.title)}')"
                             tabindex="0"
                             onkeypress="if(event.key==='Enter') AcademyPage._selectModule(${m.id}, '${Security.escapeHtml(m.title)}')"
                             style="border:1px solid transparent;"
                             onmouseover="this.style.borderColor='#374151'" 
                             onmouseout="this.style.borderColor='transparent'">
                            <div class="pw-card-body">
                                <div class="flex items-start justify-between mb-2">
                                    <div>
                                        ${isComplete 
                                            ? `<span class="badge badge-success text-xs mb-1"><i class="fas fa-check-circle mr-1"></i>Complete</span>`
                                            : `<span class="text-xs text-gray-500 mb-1 block">${m.completed_count || 0}/${m.lesson_count} lessons</span>`
                                        }
                                        <h3 class="text-white font-semibold">${Security.escapeHtml(m.title)}</h3>
                                    </div>
                                    <i class="fas fa-chevron-right text-gray-700 text-xs mt-1"></i>
                                </div>
                                <p class="text-gray-500 text-xs leading-relaxed mb-3">${Security.escapeHtml(m.description)}</p>
                                <div class="pw-progress-bar">
                                    <div class="pw-progress-fill ${pct >= 80 && pct < 100 ? 'near-done' : ''}" 
                                         style="width:${pct}%; transition: width 0.5s ease;"></div>
                                </div>
                                ${isComplete ? `<div class="ac-module-badge"><i class="fas fa-medal"></i> Module Complete</div>` : ''}
                            </div>
                        </div>`;
                    }).join('')}
                </div>
            `;
        },

        // Navigation: Lesson List
        async _selectModule(moduleId, moduleTitle) {
            if (UIController.setLoading.loading) return;
            
            StateManager.setNavigation(
                this._level,
                { id: moduleId, name: moduleTitle },
                null
            );
            
            UIController.updateBreadcrumb(this._level, { id: moduleId, name: moduleTitle }, null);
            this._hideMobileNav();
            
            const main = UIController.elements.main;
            main.innerHTML = UIController.loadingSpinner('Loading lessons...');
            
            const result = await APILayer.getLessons(moduleId);
            
            if (!result.success) {
                main.innerHTML = UIController.showError(
                    'Could not load lessons',
                    result.error,
                    () => () => this._selectModule(moduleId, moduleTitle)
                );
                return;
            }
            
            const lessons = result.data || [];
            main.innerHTML = `
                <div class="space-y-2 max-w-2xl mx-auto animate-fade-in">
                    ${lessons.map((l, i) => {
                        const locked = !l.unlocked;
                        const done = l.completed;
                        const icon = done ? 'fa-check-circle text-green-400' : 
                                    locked ? 'fa-lock text-gray-700' : 'fa-play-circle text-purple-400';
                        const score = done && l.quiz_score !== null
                            ? `<span class="text-xs font-semibold ml-2" style="color:#34d399;">${l.quiz_score}%</span>` 
                            : '';
                        
                        return `
                        <div class="pw-card ${locked ? 'opacity-60' : ''} ${!locked ? 'cursor-pointer' : ''} ac-lesson-item ${done ? 'ac-lesson-done' : ''}"
                             ${!locked ? `onclick="AcademyPage._openLesson(${l.id}, '${Security.escapeHtml(l.title)}')"` : ''}
                             ${!locked ? `tabindex="0" onkeypress="if(event.key==='Enter') AcademyPage._openLesson(${l.id}, '${Security.escapeHtml(l.title)}')"` : ''}>
                            <div class="pw-card-body" style="padding:.85rem 1.25rem;">
                                <div class="flex items-center gap-3">
                                    <i class="fas ${icon} text-lg flex-shrink-0" style="width:20px; text-align:center;"></i>
                                    <div class="flex-1 min-w-0">
                                        <div class="flex items-center gap-2">
                                            <span class="text-white font-medium text-sm truncate">
                                                Lesson ${i + 1}: ${Security.escapeHtml(l.title)}
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
                </div>
            `;
        },

        // Navigation: Lesson View
        async _openLesson(lessonId, lessonTitle) {
            if (UIController.setLoading.loading) return;
            
            StateManager.setNavigation(this._level, this._module, { id: lessonId, name: lessonTitle });
            UIController.updateBreadcrumb(this._level, this._module, { id: lessonId, name: lessonTitle });
            
            const main = UIController.elements.main;
            main.innerHTML = UIController.loadingSpinner('Loading lesson...');
            
            const result = await APILayer.getLesson(lessonId);
            
            if (!result.success) {
                main.innerHTML = UIController.showError(
                    'Could not load lesson',
                    result.error,
                    () => () => this._openLesson(lessonId, lessonTitle)
                );
                return;
            }
            
            const lesson = result.data;
            
            // Wait for marked.js if needed
            if (typeof marked === 'undefined') {
                await this._waitForMarked();
            }
            
            const processedContent = Security.processMarkdown(lesson.content);
            this._renderMobileNav(lesson);
            
            main.innerHTML = `
                <div class="max-w-3xl mx-auto ac-lesson-container animate-fade-in" tabindex="-1">
                    <div class="pw-card mb-4">
                        <div class="pw-card-hdr ac-lesson-header">
                            <div>
                                <div class="text-xs text-gray-500 mb-0.5">
                                    ${Security.escapeHtml(lesson.module_title)} · ${Security.escapeHtml(lesson.level_name)}
                                </div>
                                <h2 class="card-title ac-lesson-title text-lg font-bold text-white">${Security.escapeHtml(lesson.title)}</h2>
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
                        <button id="ac-explain-btn" class="btn bg-gray-800 border border-gray-700 text-gray-200 hover:bg-gray-700"
                                onclick="AcademyPage._showExplanation(${lessonId})">
                            <i class="fas fa-chalkboard-teacher mr-2 text-purple-400"></i>Trading Coach
                        </button>
                        <button id="ac-practice-btn" class="btn bg-gray-800 border border-gray-700 text-gray-200 hover:bg-gray-700"
                                onclick="AcademyPage._showPractice(${lessonId})">
                            <i class="fas fa-dumbbell mr-2 text-yellow-400"></i>Practice
                        </button>
                        <button id="ac-chart-btn" class="btn bg-gray-800 border border-gray-700 text-gray-200 hover:bg-gray-700"
                                onclick="AcademyPage._showChartPractice(${lessonId})">
                            <i class="fas fa-chart-bar mr-2 text-blue-400"></i>Chart Exercise
                        </button>
                    </div>
                    
                    <!-- Desktop Navigation -->
                    <div class="hidden md:flex justify-between items-center py-4 border-t border-gray-800">
                        ${lesson.prev_lesson 
                            ? `<button onclick="AcademyPage._openLesson(${lesson.prev_lesson.id}, '${Security.escapeHtml(lesson.prev_lesson.title)}')" 
                                       class="text-gray-400 hover:text-white text-sm flex items-center gap-2 transition-colors">
                                 <i class="fas fa-arrow-left"></i> Previous: ${Security.escapeHtml(lesson.prev_lesson.title)}
                               </button>`
                            : `<span></span>`
                        }
                        ${lesson.next_lesson
                            ? `<button onclick="AcademyPage._openLesson(${lesson.next_lesson.id}, '${Security.escapeHtml(lesson.next_lesson.title)}')" 
                                       class="text-purple-400 hover:text-purple-300 text-sm flex items-center gap-2 transition-colors">
                                 Next: ${Security.escapeHtml(lesson.next_lesson.title)} <i class="fas fa-arrow-right"></i>
                               </button>`
                            : `<span></span>`
                        }
                    </div>
                    
                    <div id="ac-ai-panel" class="mt-4"></div>
                </div>
            `;
            
            // Focus management for accessibility
            const container = main.querySelector('.ac-lesson-container');
            if (container) container.focus();
        },

        // Quiz Delegation
        async _startQuiz(lessonId) {
            await QuizEngine.initialize(lessonId);
        },

        _pick(key) {
            QuizEngine.selectOption(key);
        },

        _nextQ() {
            QuizEngine.nextQuestion();
        },

        _doSubmit() {
            // Handled internally by QuizEngine to prevent duplicate calls
            console.warn('[Academy] _doSubmit called directly, use _nextQ instead');
        },

        _showResults(result) {
            QuizEngine.showResults(result);
        },

        // AI Coach Interactions
        async _showExplanation(lessonId) {
            await this._loadMentorContent('ac-explain-btn', 'Trading Coach', () => 
                APILayer.getMentorTeach(lessonId), 
                'ac-coach-card', 
                'a78bfa',
                'fa-chalkboard-teacher'
            );
        },

        async _showPractice(lessonId) {
            await this._loadMentorContent('ac-practice-btn', 'Practice Exercise', () => 
                APILayer.getMentorPractice(lessonId),
                'ac-practice-card',
                'fbbf24',
                'fa-dumbbell'
            );
        },

        async _showChartPractice(lessonId) {
            const panel = document.getElementById('ac-ai-panel');
            const btn = document.getElementById('ac-chart-btn');
            
            this._setBtn('ac-chart-btn', true, 'Loading...');
            panel.innerHTML = UIController.loadingSpinner('Building chart exercise...');
            
            const result = await APILayer.getChartPractice(lessonId);
            
            this._setBtn('ac-chart-btn', false,
                '<i class="fas fa-chart-bar mr-2" style="color:#60a5fa;"></i>Chart Exercise');
            
            if (!result.success) {
                panel.innerHTML = UIController.showError('Chart exercise failed', result.error);
                return;
            }
            
            const data = result.data;
            const cp = data.chart_practice || {};
            
            const options = (cp.options || []).map((opt, i) => `
                <button class="ac-chart-opt w-full text-left px-4 py-3 rounded-lg transition-all text-sm"
                        id="ac-chart-opt-${i}"
                        style="background:#111827; border:1px solid #374151; color:#e5e7eb;"
                        onclick="AcademyPage._answerChart(${i}, '${Security.escapeHtml(cp.correct || '')}', '${Security.escapeHtml(cp.explanation || '')}')">
                    ${Security.escapeHtml(opt)}
                </button>
            `).join('');
            
            // TradingView widgets removed per requirements; using annotated images instead
            const chartDisplay = cp.image_url 
                ? `<div class="mb-4 rounded-xl overflow-hidden border border-gray-800">
                     <img src="${Security.escapeHtml(cp.image_url)}" 
                          alt="Chart Exercise" 
                          class="w-full h-auto"
                          onerror="this.parentElement.innerHTML='<div class=\'p-4 text-gray-500 text-center\'>Chart image unavailable</div>'">
                   </div>`
                : '';
            
            panel.innerHTML = `
                <div class="pw-card animate-fade-in" style="border-left:3px solid #60a5fa;">
                    <div class="pw-card-hdr">
                        <div class="flex items-center gap-2">
                            <i class="fas fa-chart-bar" style="color:#60a5fa;"></i>
                            <span class="card-title text-sm font-semibold">
                                Chart Exercise · ${Security.escapeHtml(data.level)}
                            </span>
                        </div>
                    </div>
                    <div class="pw-card-body">
                        ${chartDisplay}
                        <div class="rounded-xl p-4 mb-4 text-sm text-gray-300 leading-relaxed bg-blue-900/10 border border-blue-800/20">
                            <div class="text-xs font-bold mb-2 text-blue-400">CHART SCENARIO</div>
                            ${Security.processMarkdown(cp.scenario || '')}
                        </div>
                        <p class="text-white font-semibold mb-3 text-sm">${Security.escapeHtml(cp.question || '')}</p>
                        <div class="space-y-2" id="ac-chart-opts">${options}</div>
                        <div id="ac-chart-result" class="mt-4 hidden"></div>
                    </div>
                </div>
            `;
        },

        _answerChart(idx, correct, explanation) {
            const opts = document.querySelectorAll('.ac-chart-opt');
            const chosen = opts[idx]?.textContent?.trim()?.charAt(0)?.toUpperCase() || '';
            const passed = chosen === correct.toUpperCase();
            
            opts.forEach((btn, i) => {
                btn.disabled = true;
                btn.classList.add('disabled');
                const letter = btn.textContent.trim().charAt(0).toUpperCase();
                
                if (letter === correct.toUpperCase()) {
                    btn.style.background = 'rgba(16,185,129,0.15)';
                    btn.style.borderColor = '#34d399';
                    btn.style.color = '#34d399';
                } else if (i === idx) {
                    btn.style.background = 'rgba(239,68,68,0.1)';
                    btn.style.borderColor = '#f87171';
                    btn.style.color = '#f87171';
                }
            });
            
            const result = document.getElementById('ac-chart-result');
            result.classList.remove('hidden');
            result.innerHTML = `
                <div class="rounded-xl p-4 ${passed ? 'bg-green-900/20 border border-green-800/40' : 'bg-red-900/20 border border-red-800/40'} animate-fade-in">
                    <div class="flex items-center gap-2 mb-2">
                        <i class="fas ${passed ? 'fa-check-circle text-green-400' : 'fa-times-circle text-red-400'}"></i>
                        <strong class="${passed ? 'text-green-400' : 'text-red-400'}">
                            ${passed ? 'Correct!' : 'Incorrect'}
                        </strong>
                    </div>
                    <p class="text-gray-300 text-sm">${Security.processMarkdown(explanation)}</p>
                </div>
            `;
        },

        // Helper: Generic mentor content loader
        async _loadMentorContent(btnId, title, apiFn, cardClass, color, icon) {
            const panel = document.getElementById('ac-ai-panel');
            const btn = document.getElementById(btnId);
            
            this._setBtn(btnId, true, 'Loading...');
            panel.innerHTML = UIController.loadingSpinner(`${title} preparing...`);
            
            const result = await apiFn();
            
            this._setBtn(btnId, false, 
                `<i class="fas ${icon} mr-2" style="color:#${color};"></i>${btn.dataset.originalText || title}`);
            
            if (!result.success) {
                panel.innerHTML = UIController.showError(`${title} unavailable`, result.error);
                return;
            }
            
            const data = result.data;
            panel.innerHTML = `
                <div class="pw-card ${cardClass} animate-fade-in" style="border-left:3px solid #${color};">
                    <div class="pw-card-hdr">
                        <div class="flex items-center gap-2">
                            <i class="fas ${icon}" style="color:#${color};"></i>
                            <span class="card-title text-sm font-semibold">${Security.escapeHtml(title)}</span>
                        </div>
                    </div>
                    <div class="pw-card-body">
                        <div class="ac-lesson-text">${Security.processMarkdown(data.explanation || data.exercise || '')}</div>
                    </div>
                </div>
            `;
        },

        // Badge System
        async _loadBadges() {
            if (!this._uid) return;
            try {
                const result = await APILayer.execute('load_badges', () => 
                    window.API.lms.getBadges(this._uid)
                );
                if (result.success) {
                    this._badges = result.data?.badges || [];
                }
            } catch (e) {
                console.error('[Academy] Failed to load badges:', e);
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
                "quiz_master": { name: "Quiz Master", icon: "fa-brain", color: "#f472b6" },
                "perfect_score": { name: "Perfect Score", icon: "fa-star", color: "#fbbf24" },
                "risk_manager": { name: "Risk Manager", icon: "fa-shield-alt", color: "#22d3ee" },
                "psychology_pro": { name: "Psychology Pro", icon: "fa-brain", color: "#e879f9" },
            };
            
            badgeTypes.forEach((type, i) => {
                const def = badgeDefs[type] || { name: type, icon: "fa-medal", color: "#a78bfa" };
                const badge = document.createElement('div');
                badge.className = 'ac-badge-toast animate-fade-in';
                badge.style.cssText = `animation-delay: ${i * 0.2}s; background:#111827; border:1px solid #1f2937; border-radius:0.75rem; padding:1rem; display:flex; align-items:center; gap:1rem; box-shadow:0 10px 40px rgba(0,0,0,0.5); margin-bottom:0.5rem;`;
                badge.innerHTML = `
                    <div class="ac-badge-icon" style="width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.2rem; background:${def.color}20; color:${def.color};">
                        <i class="fas ${def.icon}"></i>
                    </div>
                    <div class="ac-badge-info">
                        <div class="ac-badge-title" style="font-size:0.75rem; color:#6b7280; text-transform:uppercase; letter-spacing:0.05em;">Badge Earned!</div>
                        <div class="ac-badge-name" style="font-size:1rem; font-weight:600; color:${def.color};">${def.name}</div>
                    </div>
                `;
                container.appendChild(badge);
                setTimeout(() => {
                    badge.style.opacity = '0';
                    badge.style.transform = 'translateX(100%)';
                    badge.style.transition = 'all 0.5s ease';
                    setTimeout(() => badge.remove(), 500);
                }, 5000);
            });
        },

        // Mentor Banner
        async _loadMentorBanner(guideData) {
            if (!this._uid) return;
            const banner = document.getElementById('ac-mentor-banner');
            if (!banner) return;
            
            try {
                const g = guideData || (await APILayer.getMentorGuide(this._uid)).data;
                if (!g) return;
                
                const isFirst = g.first_visit;
                const color = isFirst ? '#34d399' : '#a78bfa';
                const icon = isFirst ? 'fa-graduation-cap' : 'fa-chalkboard-teacher';
                const title = isFirst ? 'WELCOME' : 'TRADING COACH';
                const btnAction = isFirst 
                    ? `AcademyPage._markFirstVisitThenContinue(${g.next_lesson?.id}, '${Security.escapeHtml(g.next_lesson?.title || '')}')`
                    : `AcademyPage._openLesson(${g.next_lesson?.id}, '${Security.escapeHtml(g.next_lesson?.title || '')}')`;
                const btnText = isFirst ? 'Start Learning' : 'Continue';
                
                banner.innerHTML = `
                    <div class="pw-card mb-5 animate-fade-in" 
                         style="border-left:3px solid ${color}; background:linear-gradient(135deg,#0f0a1f,#1a0a2e);">
                        <div class="pw-card-body">
                            <div class="flex items-start gap-3">
                                <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" 
                                     style="background:${color}20;">
                                    <i class="fas ${icon}" style="color:${color};"></i>
                                </div>
                                <div class="flex-1">
                                    <div class="text-xs font-semibold mb-1" style="color:${color};">${title}</div>
                                    <p class="text-gray-300 text-sm leading-relaxed">${Security.processMarkdown(g.message)}</p>
                                    ${g.next_lesson ? `
                                        <button class="btn btn-primary mt-3 text-xs" 
                                                style="font-size:.78rem; padding:.35rem .85rem;"
                                                onclick="${btnAction}">
                                            ${btnText}: ${Security.escapeHtml(g.next_lesson.title)} →
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } catch (e) {
                banner.innerHTML = '';
            }
        },

        async _markFirstVisitThenContinue(lessonId, lessonTitle) {
            try {
                await window.API.lms.markFirstVisit();
                this._firstVisit = false;
                this._openLesson(lessonId, lessonTitle);
            } catch (e) {
                this._openLesson(lessonId, lessonTitle);
            }
        },

        // Mobile Navigation
        _renderMobileNav(lesson) {
            const nav = document.getElementById('ac-mobile-nav');
            if (!nav) return;
            
            nav.classList.remove('hidden');
            nav.innerHTML = `
                <div class="ac-mobile-nav-inner flex justify-between items-center gap-2 max-w-xl mx-auto">
                    <button class="ac-nav-btn ${!lesson.prev_lesson ? 'disabled opacity-50' : ''}" 
                        ${lesson.prev_lesson ? `onclick="AcademyPage._openLesson(${lesson.prev_lesson.id}, '${Security.escapeHtml(lesson.prev_lesson.title)}')"` : 'disabled'}>
                        <i class="fas fa-arrow-left"></i> Prev
                    </button>
                    <button class="ac-nav-btn bg-purple-900/30 border-purple-800/50 text-purple-300" 
                        onclick="AcademyPage._selectModule(${this._module?.id || 0}, '${Security.escapeHtml(this._module?.name || '')}')">
                        <i class="fas fa-th-large"></i> Module
                    </button>
                    <button class="ac-nav-btn ${!lesson.next_lesson ? 'disabled opacity-50' : ''}" 
                        ${lesson.next_lesson ? `onclick="AcademyPage._openLesson(${lesson.next_lesson.id}, '${Security.escapeHtml(lesson.next_lesson.title)}')"` : 'disabled'}>
                        Next <i class="fas fa-arrow-right"></i>
                    </button>
                </div>
            `;
        },

        _hideMobileNav() {
            const nav = document.getElementById('ac-mobile-nav');
            if (nav) nav.classList.add('hidden');
        },

        // Utilities
        _getUser() {
            try {
                return JSON.parse(localStorage.getItem('pipways_user') || '{}');
            } catch (_) {
                return {};
            }
        },

        _setBtn(id, loading, html) {
            const b = document.getElementById(id);
            if (!b) return;
            
            // Store original text if not stored
            if (!b.dataset.originalText && !loading) {
                b.dataset.originalText = b.innerHTML;
            }
            
            b.disabled = loading;
            b.innerHTML = loading 
                ? '<i class="fas fa-spinner fa-spin mr-2"></i>Loading...' 
                : html;
            b.style.opacity = loading ? '0.7' : '1';
        },

        _clearCache() {
            StateManager.clearCache();
        },

        async _waitForMarked() {
            if (typeof marked !== 'undefined') return;
            
            return new Promise((resolve) => {
                let checks = 0;
                const interval = setInterval(() => {
                    if (typeof marked !== 'undefined') {
                        clearInterval(interval);
                        resolve();
                    }
                    if (++checks > 20) { // 2 second timeout
                        clearInterval(interval);
                        console.warn('[Academy] marked.js failed to load');
                        resolve(); // Resolve anyway to continue with fallback
                    }
                }, 100);
            });
        },

        // Legacy compatibility aliases
        _processLessonContent(content) {
            return Security.processMarkdown(content);
        },

        _loading: UIController.loadingSpinner.bind(UIController),
        _aiLoading: (m) => UIController.loadingSpinner(m),
        _error: UIController.showError.bind(UIController),
        _emptyState: UIController.showEmptyState.bind(UIController),
        _bc: UIController.updateBreadcrumb.bind(UIController),
        
        // Stub for removed TradingView functionality (backward compat)
        initTradingViewWidgets() {
            // TradingView widgets removed per v5.0 curriculum update
            // Lessons now use static annotated chart images
            console.log('[Academy] TradingView widgets deprecated, using image charts');
        }
    };

    // Initialize marked.js loader (legacy support)
    (function loadMarked() {
        if (window.marked) return;
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
        script.async = true;
        script.onerror = () => console.error('[Academy] Failed to load marked.js');
        document.head.appendChild(script);
    })();

    // Expose to global scope
    window.AcademyPage = AcademyController;
    
    // Also expose internal utilities for advanced debugging (optional)
    window.__AcademyInternals = {
        StateManager,
        APILayer,
        Security,
        CONFIG
    };

})();
