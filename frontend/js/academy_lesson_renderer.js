/**
 * Pipways Academy — Lesson Callout Renderer v2.0
 *
 * Converts > [!HOOK] / > [!DEF] / > [!EXAMPLE] / > [!NGX] /
 *           > [!MISTAKE] / > [!TIP] / > [!TAKEAWAY]
 * markdown blockquote syntax into styled callout HTML.
 *
 * Usage:
 *   const html = renderLessonContent(rawMarkdown);
 *   document.getElementById('lesson-body').innerHTML = html;
 *
 * Dependencies: none (plain JS)
 */

const CALLOUT_CONFIG = {
    HOOK: {
        label: 'Story',
        icon: `<svg class="callout__icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M8 1L10 5.5H15L11 8.5L12.5 13L8 10.5L3.5 13L5 8.5L1 5.5H6L8 1Z"
            stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
        </svg>`,
        cssClass: 'callout--hook',
    },
    DEF: {
        label: 'Definition',
        icon: `<svg class="callout__icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/>
          <path d="M5 6h6M5 8.5h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>`,
        cssClass: 'callout--def',
    },
    EXAMPLE: {
        label: 'Trade Example',
        icon: `<svg class="callout__icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M2 12L6 8L9 11L14 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="14" cy="4" r="1.5" fill="currentColor"/>
        </svg>`,
        cssClass: 'callout--example',
    },
    NGX: {
        label: 'Nigerian Market',
        icon: `<svg class="callout__icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/>
          <path d="M5 5l4 6M5 11l4-6M5 8h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>`,
        cssClass: 'callout--ngx',
    },
    MISTAKE: {
        label: 'Common Mistake',
        icon: `<svg class="callout__icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M8 2L14.5 13H1.5L8 2Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
          <path d="M8 7v3M8 11.5v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>`,
        cssClass: 'callout--mistake',
    },
    TIP: {
        label: 'Pro Tip',
        icon: `<svg class="callout__icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M8 2a4 4 0 0 1 2 7.5V11H6V9.5A4 4 0 0 1 8 2Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
          <path d="M6 12h4M7 14h2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>`,
        cssClass: 'callout--tip',
    },
    TAKEAWAY: {
        label: 'Key Takeaway',
        icon: `<svg class="callout__icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M3 8l3.5 3.5L13 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>`,
        cssClass: 'callout--takeaway',
    },
};

/**
 * Escapes HTML entities in a string.
 */
function escapeHtml(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/**
 * Converts inline markdown to HTML (bold, italic, code, links).
 */
function renderInline(text) {
    return text
        // Bold
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Inline code
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Links
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
}

/**
 * Converts a block of text lines to block HTML (paragraphs, lists, tables, code blocks).
 * @param {string} text - Raw block text
 * @returns {string} HTML string
 */
function renderBlock(text) {
    const lines = text.split('\n');
    const output = [];
    let i = 0;

    while (i < lines.length) {
        const line = lines[i];

        // Skip empty lines
        if (line.trim() === '') {
            i++;
            continue;
        }

        // Fenced code block
        if (line.trim().startsWith('```')) {
            const lang = line.trim().slice(3).trim();
            const codeLines = [];
            i++;
            while (i < lines.length && !lines[i].trim().startsWith('```')) {
                codeLines.push(lines[i]);
                i++;
            }
            i++; // skip closing ```
            output.push(`<pre><code class="language-${lang}">${escapeHtml(codeLines.join('\n'))}</code></pre>`);
            continue;
        }

        // Headings
        const headingMatch = line.match(/^(#{1,3})\s+(.+)/);
        if (headingMatch) {
            const level = headingMatch[1].length + 1; // h2, h3, h4
            output.push(`<h${level}>${renderInline(headingMatch[2])}</h${level}>`);
            i++;
            continue;
        }

        // HR
        if (line.trim() === '---' || line.trim() === '***') {
            output.push('<hr>');
            i++;
            continue;
        }

        // Unordered list
        if (line.match(/^(\s*)[*\-]\s/)) {
            const listLines = [];
            while (i < lines.length && lines[i].match(/^(\s*)[*\-]\s/)) {
                const itemText = lines[i].replace(/^(\s*)[*\-]\s/, '');
                listLines.push(`<li>${renderInline(itemText)}</li>`);
                i++;
            }
            output.push(`<ul>${listLines.join('')}</ul>`);
            continue;
        }

        // Ordered list
        if (line.match(/^\d+\.\s/)) {
            const listLines = [];
            while (i < lines.length && lines[i].match(/^\d+\.\s/)) {
                const itemText = lines[i].replace(/^\d+\.\s/, '');
                listLines.push(`<li>${renderInline(itemText)}</li>`);
                i++;
            }
            output.push(`<ol>${listLines.join('')}</ol>`);
            continue;
        }

        // Table (starts with |)
        if (line.trim().startsWith('|')) {
            const tableLines = [];
            while (i < lines.length && lines[i].trim().startsWith('|')) {
                tableLines.push(lines[i]);
                i++;
            }
            output.push(renderTable(tableLines));
            continue;
        }

        // Paragraph — collect until blank line or block element starts
        const paraLines = [];
        while (
            i < lines.length &&
            lines[i].trim() !== '' &&
            !lines[i].match(/^#{1,3}\s/) &&
            !lines[i].trim().startsWith('|') &&
            !lines[i].trim().startsWith('```') &&
            !lines[i].match(/^(\s*)[*\-]\s/) &&
            !lines[i].match(/^\d+\.\s/) &&
            lines[i].trim() !== '---'
        ) {
            paraLines.push(lines[i]);
            i++;
        }
        if (paraLines.length > 0) {
            // Split on blank-ish lines inside the paragraph block to create
            // separate <p> tags for genuinely separate paragraphs
            const paras = paraLines.join('\n').split(/\n{2,}/);
            paras.forEach(para => {
                const trimmed = para.trim();
                if (trimmed) {
                    // Preserve intentional line breaks within a single paragraph
                    // by joining lines with a space (same-paragraph continuation)
                    output.push(`<p>${renderInline(trimmed.replace(/\n/g, ' '))}</p>`);
                }
            });
        }
    }

    return output.join('\n');
}

/**
 * Renders markdown table lines to HTML table.
 */
function renderTable(lines) {
    const rows = lines
        .filter(l => !l.trim().match(/^\|[-| :]+\|$/)) // skip separator rows
        .map(l => l.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim()));

    if (rows.length === 0) return '';

    const [header, ...body] = rows;
    const thCells = header.map(c => `<th>${renderInline(c)}</th>`).join('');
    const tbodyRows = body.map(row => {
        const tdCells = row.map(c => `<td>${renderInline(c)}</td>`).join('');
        return `<tr>${tdCells}</tr>`;
    }).join('');

    return `<table><thead><tr>${thCells}</tr></thead><tbody>${tbodyRows}</tbody></table>`;
}

/**
 * Main renderer — converts full lesson markdown to HTML.
 * Handles callout blocks and regular markdown.
 *
 * @param {string} markdown - Raw lesson content string
 * @returns {string} Fully rendered HTML
 */
function renderLessonContent(markdown) {
    if (!markdown) return '';

    const lines = markdown.split('\n');
    const output = [];
    let i = 0;

    while (i < lines.length) {
        const line = lines[i];

        // Detect callout opening: > [!TYPE]
        const calloutMatch = line.match(/^>\s*\[!(\w+)\]\s*$/);
        if (calloutMatch) {
            const type = calloutMatch[1].toUpperCase();
            const config = CALLOUT_CONFIG[type];

            // Collect all lines that start with > (the callout body)
            const bodyLines = [];
            i++;
            while (i < lines.length) {
                const bodyLine = lines[i];
                if (bodyLine.startsWith('> ')) {
                    bodyLines.push(bodyLine.slice(2));
                    i++;
                } else if (bodyLine.trim() === '>') {
                    bodyLines.push('');
                    i++;
                } else {
                    break;
                }
            }

            const bodyText = bodyLines.join('\n').trim();
            const bodyHtml = renderBlock(bodyText);

            if (config) {
                output.push(`
<div class="callout ${config.cssClass}" role="note" aria-label="${config.label}">
  <div class="callout__label">
    ${config.icon}
    ${config.label}
  </div>
  <div class="callout__body">${bodyHtml}</div>
</div>`);
            } else {
                // Unknown callout type — render as blockquote
                output.push(`<blockquote>${bodyHtml}</blockquote>`);
            }
            continue;
        }

        // Regular line — collect into a plain block for rendering.
        // Stop at callout openers AND at any > line that could be a callout body.
        const plainLines = [];
        while (
            i < lines.length &&
            !lines[i].match(/^>\s*\[!\w+\]\s*$/) &&
            !lines[i].match(/^>\s/)               // stop before any > line
        ) {
            plainLines.push(lines[i]);
            i++;
        }

        const plainHtml = renderBlock(plainLines.join('\n'));
        if (plainHtml.trim()) {
            output.push(plainHtml);
        }
    }

    return output.join('\n');
}

/**
 * Renders an interactive quiz from quiz data array.
 *
 * @param {Array} quizData - Array of quiz question objects
 * @param {string} lessonTitle - Lesson title for aria labels
 * @returns {string} Quiz HTML string
 */
function renderQuiz(quizData, lessonTitle = 'Lesson') {
    if (!quizData || quizData.length === 0) return '';

    // Unique namespace per lesson to avoid id collisions when multiple
    // lessons are on the same page (review mode, side panel, etc.)
    const ns = 'qz-' + Math.random().toString(36).slice(2, 7);

    const questionsHtml = quizData.map((q, idx) => {
        const options = ['A', 'B', 'C', 'D'];
        const optionKeys = ['option_a', 'option_b', 'option_c', 'option_d'];
        const questionId = `${ns}-${idx}`;

        const optionsHtml = options.map((letter, optIdx) => {
            const optionText = q[optionKeys[optIdx]] || '';
            if (!optionText) return '';
            return `
        <button class="quiz-option"
          data-question-id="${questionId}"
          data-letter="${letter}"
          data-correct="${q.correct_answer}"
          data-explanation="${escapeHtml(q.explanation || '')}"
          onclick="handleQuizAnswer(this)"
          type="button">
          <span class="quiz-option__letter">${letter}</span>
          <span class="quiz-option__text">${renderInline(optionText)}</span>
        </button>`;
        }).join('');

        return `
    <div class="lesson-quiz" id="${questionId}" data-answered="false">
      <div class="lesson-quiz__header">Question ${idx + 1} of ${quizData.length}</div>
      <div class="lesson-quiz__question">${renderInline(q.question)}</div>
      <div class="lesson-quiz__options">${optionsHtml}</div>
      <div class="lesson-quiz__explanation" id="${questionId}-exp"></div>
    </div>`;
    }).join('');

    return `<div class="lesson-quiz-container">${questionsHtml}</div>`;
}

/**
 * Handles quiz answer selection.
 * Called via onclick from quiz option buttons.
 *
 * @param {HTMLElement} btn - The clicked button element
 */
function handleQuizAnswer(btn) {
    const questionId = btn.dataset.questionId;
    const quizEl = document.getElementById(questionId);

    // Prevent re-answering
    if (!quizEl || quizEl.dataset.answered === 'true') return;
    quizEl.dataset.answered = 'true';

    const selectedLetter = btn.dataset.letter;
    const correctLetter = btn.dataset.correct;
    const explanation = btn.dataset.explanation;

    // Disable all options in this question
    quizEl.querySelectorAll('.quiz-option').forEach(opt => {
        opt.disabled = true;
        opt.style.cursor = 'default';
        const optLetter = opt.dataset.letter;

        if (optLetter === correctLetter) {
            opt.classList.add('quiz-option--reveal');
        }
        if (optLetter === selectedLetter && selectedLetter !== correctLetter) {
            opt.classList.add('quiz-option--incorrect');
        }
    });

    // Mark selected correct
    if (selectedLetter === correctLetter) {
        btn.classList.add('quiz-option--correct');
        // Remove the generic 'reveal' and use 'correct' on the clicked btn
        btn.classList.remove('quiz-option--reveal');
    }

    // Show explanation
    const explanationEl = document.getElementById(`${questionId}-exp`);
    if (explanationEl && explanation) {
        const isCorrect = selectedLetter === correctLetter;
        explanationEl.innerHTML = `
      <strong>${isCorrect ? '✓ Correct!' : '✗ Not quite.'}</strong>
      ${explanation}
    `;
        explanationEl.classList.add('is-visible');
        // Smooth scroll into view on mobile
        explanationEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

/**
 * Renders the AI Mentor CTA button at the bottom of each lesson.
 *
 * @param {string} lessonTitle - Title of the current lesson
 * @returns {string} HTML string
 */
function renderMentorCTA(lessonTitle) {
    // Store prompt on a data attribute — never inline JS strings with user content
    const prompt = `I just finished the lesson "${lessonTitle}". Can you help me understand it better and suggest what to study next?`;
    const safeTitle = escapeHtml(lessonTitle);
    const safePrompt = escapeHtml(prompt);

    return `
<div class="lesson-mentor-cta">
  <div class="lesson-mentor-cta__text">
    <strong>Still have questions?</strong>
    <span>Ask the AI Mentor about ${safeTitle}</span>
  </div>
  <button class="lesson-mentor-cta__btn"
    data-mentor-prompt="${safePrompt}"
    onclick="openMentorWithPrompt(this.dataset.mentorPrompt)"
    type="button">
    Ask Mentor →
  </button>
</div>`;
}

/**
 * Opens the AI Mentor panel pre-populated with a prompt.
 * Integrates with ai_mentor.js AIMentor class.
 *
 * @param {string} prompt - Pre-filled message text
 */
function openMentorWithPrompt(prompt) {
    const mentorInput = document.getElementById('message-input');
    const mentorPanel = document.getElementById('ai-mentor-panel');

    if (mentorPanel) {
        mentorPanel.classList.add('is-active');
        mentorPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    if (mentorInput) {
        mentorInput.value = prompt;
        mentorInput.focus();
        // Trigger the mentor's send function if available
        if (window.mentor && typeof window.mentor.sendMessage === 'function') {
            setTimeout(() => window.mentor.sendMessage(), 150);
        }
    }
}

/**
 * Full lesson renderer — combines content, quiz, and mentor CTA.
 *
 * @param {Object} lesson - Lesson object with title, content, quiz
 * @param {Object} options - Rendering options
 * @returns {string} Complete lesson HTML
 */
function renderFullLesson(lesson, options = {}) {
    const {
        showMentorCTA = true,
        showQuiz = true,
        progressPercent = null,
    } = options;

    let html = '<div class="lesson-content">';

    // Optional progress bar
    if (progressPercent !== null) {
        html += `
      <div class="lesson-progress-bar" aria-label="Lesson progress">
        <div class="lesson-progress-bar__fill" style="width: ${progressPercent}%"></div>
      </div>`;
    }

    // Main content
    html += renderLessonContent(lesson.content || '');

    // Quiz section
    if (showQuiz && lesson.quiz && lesson.quiz.length > 0) {
        html += '<hr>';
        html += '<h2>Knowledge Check</h2>';
        html += renderQuiz(lesson.quiz, lesson.title);
    }

    // AI Mentor CTA
    if (showMentorCTA && lesson.title) {
        html += renderMentorCTA(lesson.title);
    }

    html += '</div>';
    return html;
}

// ── Module exports (supports both browser globals and ES modules) ──────────

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        renderLessonContent,
        renderQuiz,
        renderMentorCTA,
        renderFullLesson,
        handleQuizAnswer,
        openMentorWithPrompt,
    };
} else if (typeof window !== 'undefined') {
    window.PipwaysLessonRenderer = {
        renderLessonContent,
        renderQuiz,
        renderMentorCTA,
        renderFullLesson,
        handleQuizAnswer,
        openMentorWithPrompt,
    };
    // Expose globals needed by inline onclick handlers
    window.handleQuizAnswer = handleQuizAnswer;
    window.openMentorWithPrompt = openMentorWithPrompt;
}

/**
 * Drop-in integration helper for academy.js.
 *
 * Call this instead of manually setting innerHTML on the lesson container.
 *
 * @example
 * // In academy.js, replace your current lesson render call with:
 * initLessonRenderer(lesson, {
 *   containerId: 'lesson-content',   // id of the div that holds lesson HTML
 *   currentIndex: 3,                 // 0-based index of this lesson
 *   totalLessons: 28,
 * });
 *
 * @param {Object} lesson          - Lesson object from the API response
 * @param {Object} opts
 * @param {string} opts.containerId    - Target element id (default: 'lesson-content')
 * @param {number} opts.currentIndex   - 0-based lesson index for progress bar
 * @param {number} opts.totalLessons   - Total lesson count for progress bar
 * @param {boolean} opts.showQuiz      - Whether to render quiz (default: true)
 * @param {boolean} opts.showMentorCTA - Whether to render mentor CTA (default: true)
 */
function initLessonRenderer(lesson, opts = {}) {
    const {
        containerId = 'lesson-content',
        currentIndex = null,
        totalLessons = null,
        showQuiz = true,
        showMentorCTA = true,
    } = opts;

    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`[PipwaysRenderer] Container #${containerId} not found.`);
        return;
    }

    const progressPercent = (currentIndex !== null && totalLessons)
        ? Math.round(((currentIndex + 1) / totalLessons) * 100)
        : null;

    container.innerHTML = renderFullLesson(lesson, {
        showQuiz,
        showMentorCTA,
        progressPercent,
    });

    // Scroll lesson to top on navigation
    container.scrollTop = 0;
    window.scrollTo({ top: container.getBoundingClientRect().top + window.scrollY - 80, behavior: 'smooth' });
}

// Expose integration helper globally
if (typeof window !== 'undefined') {
    window.initLessonRenderer = initLessonRenderer;
}
