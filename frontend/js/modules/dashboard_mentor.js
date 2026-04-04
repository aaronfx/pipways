// Dashboard Module: AI Mentor
// Extracted from dashboard.js for maintainability

DashboardController.prototype.loadMentor = async function() {
    await this.loadCoachInsights();
    this.loadMentorHistory();
};

DashboardController.prototype.loadCoachInsights = async function() {
    try {
        const data = await this.apiRequest('/ai/mentor/insights');

        document.getElementById('coach-insights-loading').classList.add('hidden');
        document.getElementById('coach-insights-content').classList.remove('hidden');

        document.getElementById('trading-personality').textContent = data.trading_personality || 'Developing Trader';
        document.getElementById('discipline-score').textContent = (data.discipline_score || 0) + '%';
        document.getElementById('consistency-score').textContent = (data.consistency_score || 0) + '%';

        const strengthsList = document.getElementById('ai-strengths-list');
        strengthsList.innerHTML = (data.strengths || []).map(s => `
            <li class="text-sm text-gray-300 flex items-start gap-2">
                <span class="w-1.5 h-1.5 bg-green-400 rounded-full mt-1.5 flex-shrink-0"></span>
                <span>${s}</span>
            </li>
        `).join('');

        const weaknessesList = document.getElementById('ai-weaknesses-list');
        weaknessesList.innerHTML = (data.weaknesses || []).map(w => `
            <li class="text-sm text-gray-300 flex items-start gap-2">
                <span class="w-1.5 h-1.5 bg-yellow-400 rounded-full mt-1.5 flex-shrink-0"></span>
                <span>${w}</span>
            </li>
        `).join('');

        document.getElementById('risk-profile').textContent = data.risk_profile || 'Moderate';

        const stepsList = document.getElementById('next-steps-list');
        stepsList.innerHTML = (data.recommended_next_steps || []).map(step => `
            <li class="flex items-start gap-2">
                <span class="text-blue-400 mt-0.5">→</span>
                <span>${step}</span>
            </li>
        `).join('');

        this.updateRecommendationsList(data.recommended_resources || []);

    } catch (e) {
        console.error('Failed to load coach insights:', e);
        document.getElementById('coach-insights-loading').innerHTML = 
            '<span class="text-gray-500">Upload journal to see insights</span>';
    }
}

DashboardController.prototype.updateRecommendationsList = function(resources) {
    return;
};

DashboardController.prototype.loadMentorHistory = function() {
    try {
        const history = JSON.parse(localStorage.getItem('mentor_history') || '[]');
        const container = document.getElementById('mentor-messages');
        if (!container) return;

        if (history.length > 0) {
            container.innerHTML = '';
            history.forEach(msg => {
                if (msg.role === 'user') {
                    this.appendMentorMessage(msg.content, 'user', false);
                } else {
                    this.appendMentorMessage(msg.content, 'assistant', false);
                }
            });
        } else {
            const summaryRaw = localStorage.getItem('mentor_session_summary');
            if (summaryRaw) {
                const summary = JSON.parse(summaryRaw);
                const age = Date.now() - new Date(summary.saved_at).getTime();
                if (age < 7 * 86400000 && summary.messages?.length > 0) {
                    const lastUserMsg = summary.messages.filter(m => m.role === 'user').pop();
                    const notice = document.createElement('div');
                    notice.className = 'flex justify-center mb-3';
                    notice.innerHTML = `
                        <div class="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs"
                             style="background:rgba(124,58,237,.1);border:1px solid rgba(124,58,237,.2);color:#a78bfa;">
                            <i class="fas fa-history" style="font-size:.65rem;"></i>
                            Previous session context loaded
                            ${lastUserMsg ? `· Last: "${lastUserMsg.content.slice(0, 40)}${lastUserMsg.content.length > 40 ? '…' : ''}"` : ''}
                        </div>`;
                    container.innerHTML = '';
                    container.appendChild(notice);
                    const welcome = document.createElement('div');
                    welcome.className = 'flex gap-3 animate-fade-in';
                    welcome.innerHTML = `
                        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                            <i class="fas fa-robot text-xs text-white"></i>
                        </div>
                        <div class="bg-gray-800 p-4 rounded-2xl rounded-tl-none border border-gray-700" style="max-width:85%;">
                            <div class="mentor-prose">Welcome back! I remember our last conversation. What would you like to work on today?</div>
                        </div>`;
                    container.appendChild(welcome);
                }
            }
        }
    } catch (e) {
        console.error('Error loading mentor history:', e);
    }
};

DashboardController.prototype.saveMentorHistory = function() {
    try {
        const container = document.getElementById('mentor-messages');
        if (!container) return;

        const messages = [];
        container.querySelectorAll('.message-wrapper').forEach(el => {
            const role = el.dataset.role;
            const content = el.dataset.content;
            if (role && content) {
                messages.push({role, content, timestamp: new Date().toISOString()});
            }
        });

        const trimmed = messages.slice(-20);
        localStorage.setItem('mentor_history', JSON.stringify(trimmed));

        const summary = messages.slice(-6).map(m => ({
            role: m.role,
            content: m.content.slice(0, 300)
        }));
        localStorage.setItem('mentor_session_summary', JSON.stringify({
            saved_at: new Date().toISOString(),
            messages: summary
        }));
    } catch (e) {
        console.error('Error saving mentor history:', e);
    }
};

DashboardController.prototype._getMentorHistory = function() {
    try {
        const raw = JSON.parse(localStorage.getItem('mentor_history') || '[]');
        if (raw.length > 0) {
            return raw.slice(-16).map(m => ({
                role: m.role === 'user' ? 'user' : 'assistant',
                content: (m.content || '').slice(0, 800)
            }));
        }
        const summaryRaw = localStorage.getItem('mentor_session_summary');
        if (!summaryRaw) return [];
        const summary = JSON.parse(summaryRaw);
        const age = Date.now() - new Date(summary.saved_at).getTime();
        if (age > 7 * 86400000) return [];
        return (summary.messages || []).map(m => ({
            role: m.role === 'user' ? 'user' : 'assistant',
            content: m.content
        }));
    } catch (_) { return []; }
};

DashboardController.prototype._getCachedPerformance = function() {
    try {
        if (this._cachedPerformance) {
            const age = Date.now() - this._cachedPerformance.cached_at;
            if (age < 86400000) return this._cachedPerformance;
        }
        const raw = localStorage.getItem('pipways_performance');
        if (!raw) return null;
        const data = JSON.parse(raw);
        if (Date.now() - data.cached_at > 86400000) return null;
        this._cachedPerformance = data;
        return data;
    } catch (_) { return null; }
};

DashboardController.prototype._getSlashPreview = function(cmd) {
    const previews = {
        '/signals':       '📡 Fetching active signals and asking mentor to analyse them…',
        '/review-trades': '📊 Pulling your performance data for AI review…',
        '/strategy':      '🎯 Checking your strategy readiness based on your progress…',
        '/next':          '📚 Finding your recommended next learning step…',
        '/progress':      '📈 Generating your full progress breakdown…',
        '/help':          null
    };
    return previews[cmd.toLowerCase()] || null;
}

DashboardController.prototype.sendMentorMessage = async function() {
    const input = document.getElementById('mentor-input');
    const message = input.value.trim();
    if (!message) return;

    if (message.toLowerCase() === '/help') {
        input.value = '';
        this.appendMentorMessage('/help', 'user');
        this.appendMentorMessage(
            `**Available commands:**\n` +
            `• \`/signals\` — Analyse active market signals\n` +
            `• \`/review-trades\` — Review your performance stats\n` +
            `• \`/strategy\` — Check your strategy readiness\n` +
            `• \`/next\` — What to learn next\n` +
            `• \`/progress\` — Full progress breakdown\n\n` +
            `Or just ask me anything about trading!`,
            'assistant'
        );
        return;
    }

    this.appendMentorMessage(message, 'user');
    input.value = '';

    const preview = this._getSlashPreview(message);
    if (preview) {
        const previewEl = document.getElementById('mentor-typing');
        const span = previewEl?.querySelector('span');
        if (span) span.textContent = preview;
    }

    document.getElementById('mentor-typing').classList.remove('hidden');
    this._hideMentorRecommendations();

    const history = this._getMentorHistory();

    try {
        const cachedPerf = this._getCachedPerformance();

        const response = await this.apiRequest('/ai/mentor/ask', {
            method: 'POST',
            body: JSON.stringify({
                message: message,
                question: message,
                skill_level: 'intermediate',
                include_platform_context: true,
                conversation_history: history,
                cached_performance: cachedPerf
            })
        });

        document.getElementById('mentor-typing').classList.add('hidden');
        const span = document.getElementById('mentor-typing')?.querySelector('span');
        if (span) span.textContent = 'AI is analyzing your data...';

        if (!response || typeof response !== 'object') {
            throw new Error('Invalid response format from mentor API');
        }

        const replyText = response.response || response.message || response.answer || '';
        await this.typeMentorResponse(replyText || 'I received your message but had trouble generating a response. Please try again.');

        const recs = response.recommendations || response.suggested_resources || [];
        console.log(`[Mentor] ${recs.length} recommendation(s):`, recs);
        if (recs.length > 0) {
            this._renderMentorLessonCards(recs);
            this.updateRecommendationsList(recs);
        }

        this.saveMentorHistory();

    } catch (e) {
        document.getElementById('mentor-typing').classList.add('hidden');
        console.error('[Mentor] sendMentorMessage error:', e);
        this.appendMentorMessage('Sorry, I encountered an error. Please try again.', 'error');
    }
};

DashboardController.prototype._hideMentorRecommendations = function() {
    const panel = document.getElementById('mentor-recommendations');
    if (panel) panel.classList.add('hidden');
};

DashboardController.prototype._renderMentorLessonCards = function(recommendations) {
    const panel = document.getElementById('mentor-recommendations');
    const grid  = document.getElementById('mentor-rec-grid');
    const count = document.getElementById('mentor-rec-count');
    if (!panel || !grid) {
        console.warn('[Mentor] #mentor-recommendations or #mentor-rec-grid not found');
        return;
    }

    grid.innerHTML = '';
    if (count) count.textContent = recommendations.length;

    const typeIcons = {
        course:   { icon: 'fa-graduation-cap', col: '#a78bfa', bg: 'rgba(167,139,250,.15)' },
        lesson:   { icon: 'fa-play-circle',    col: '#a78bfa', bg: 'rgba(167,139,250,.15)' },
        blog:     { icon: 'fa-newspaper',       col: '#2dd4bf', bg: 'rgba(45,212,191,.15)'  },
        strategy: { icon: 'fa-chess',           col: '#fbbf24', bg: 'rgba(251,191,36,.15)'  },
        default:  { icon: 'fa-lightbulb',       col: '#60a5fa', bg: 'rgba(96,165,250,.15)'  }
    };

    recommendations.forEach(rec => {
        const lessonId = rec.metadata?.lesson_id || rec.id || null;
        const url      = rec.url || null;
        const t        = typeIcons[rec.type] || typeIcons.default;

        const _base = window.location.origin;
        let dest;
        if (url && url.includes('?lesson=')) {
            dest = url.startsWith('http') ? url : _base + url;
        } else if (lessonId) {
            dest = `${_base}/academy.html?lesson=${lessonId}`;
        } else if (url) {
            dest = url.startsWith('http') ? url : _base + url;
        } else {
            dest = `${_base}/academy.html`;
        }

        console.log(`[Mentor Rec] "${rec.title}" → ${dest} (lessonId=${lessonId}, url=${url})`);

        const card = document.createElement('div');
        card.className = 'cursor-pointer rounded-xl p-3 transition-all duration-200';
        card.style.cssText = 'background:#111827;border:1px solid #1f2937;';
        card.onmouseover = () => { card.style.borderColor = '#7c3aed'; card.style.background = 'rgba(124,58,237,.08)'; };
        card.onmouseout  = () => { card.style.borderColor = '#1f2937'; card.style.background = '#111827'; };

        const ctaLabel = (lessonId || (url && url.includes('?lesson='))) ? 'Start Lesson' : 'Open Academy';
        const ctaIcon  = (lessonId || (url && url.includes('?lesson='))) ? 'fa-play-circle' : 'fa-graduation-cap';

        card.innerHTML = `
            <div class="flex items-start gap-3">
                <div class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                     style="background:${t.bg};">
                    <i class="fas ${t.icon} text-sm" aria-hidden="true" style="color:${t.col};"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="text-sm font-semibold text-white truncate mb-0.5">${this._escapeHtml(rec.title)}</div>
                    ${rec.description ? `<div class="text-xs mb-2" style="color:#9ca3af;line-height:1.4;">${this._escapeHtml(rec.description)}</div>` : ''}
                    <button class="text-xs font-semibold flex items-center gap-1 px-2.5 py-1.5 rounded-lg transition-all"
                            style="background:${t.bg};color:${t.col};border:1px solid ${t.col}33;"
                            onclick="event.stopPropagation(); window.location.href='${dest}';">
                        <i class="fas ${ctaIcon}" aria-hidden="true" style="font-size:.7rem;"></i>
                        &nbsp;${ctaLabel}&nbsp;<i class="fas fa-arrow-right" aria-hidden="true" style="font-size:.5rem;"></i>
                    </button>
                </div>
            </div>`;

        card.addEventListener('click', () => { window.location.href = dest; });
        grid.appendChild(card);
    });

    panel.classList.remove('hidden');

    const msgs = document.getElementById('mentor-messages');
    if (msgs) setTimeout(() => msgs.scrollTo({ top: msgs.scrollHeight, behavior: 'smooth' }), 100);
};

DashboardController.prototype.updateRecommendationsList = function(resources) {
    return;
};

DashboardController.prototype._escapeHtml = function(str) {
    const d = document.createElement('div');
    d.textContent = str || '';
    return d.innerHTML;
};

DashboardController.prototype.askMentor = async function(question) {
    const input = document.getElementById('mentor-input');
    input.value = question;
    await this.sendMentorMessage();
};

DashboardController.prototype.appendMentorMessage = function(text, sender, animate = true) {
    const container = document.getElementById('mentor-messages');
    if (!container) return;

    const wrapper = document.createElement('div');
    wrapper.className = `message-wrapper flex gap-3 ${animate ? 'animate-fade-in' : ''}`;
    wrapper.dataset.role = sender;
    wrapper.dataset.content = text;

    if (sender === 'user') {
        wrapper.classList.add('flex-row-reverse');
        wrapper.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center flex-shrink-0">
                <i class="fas fa-user text-xs text-white"></i>
            </div>
            <div class="bg-purple-600 p-3 rounded-2xl rounded-tr-none max-w-[80%]">
                <p class="text-white text-sm">${text}</p>
            </div>
        `;
    } else if (sender === 'error') {
        wrapper.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-red-900 flex items-center justify-center flex-shrink-0">
                <i class="fas fa-exclamation text-xs text-red-400"></i>
            </div>
            <div class="bg-red-900/30 border border-red-700/50 p-3 rounded-2xl rounded-tl-none max-w-[80%]">
                <p class="text-red-200 text-sm">${text}</p>
            </div>
        `;
    } else {
        const rendered = window._renderMd ? window._renderMd(text) : text;
        wrapper.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-1">
                <i class="fas fa-robot text-xs text-white"></i>
            </div>
            <div class="bg-gray-800 p-4 rounded-2xl rounded-tl-none border border-gray-700" style="max-width:85%;">
                <div class="mentor-prose">${rendered}</div>
            </div>
        `;
    }

    container.appendChild(wrapper);
    container.scrollTop = container.scrollHeight;
};

DashboardController.prototype.typeMentorResponse = async function(text) {
    const container = document.getElementById('mentor-messages');
    if (!container) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper flex gap-3 animate-fade-in';
    wrapper.dataset.role = 'assistant';
    wrapper.dataset.content = text;

    wrapper.innerHTML = `
        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-1">
            <i class="fas fa-robot text-xs text-white"></i>
        </div>
        <div class="bg-gray-800 p-4 rounded-2xl rounded-tl-none border border-gray-700" style="max-width:85%;">
            <div class="mentor-prose typing-content"></div>
        </div>
    `;

    container.appendChild(wrapper);
    container.scrollTop = container.scrollHeight;

    const contentEl = wrapper.querySelector('.typing-content');

    const words = text.split(' ');
    let currentText = '';
    for (let i = 0; i < words.length; i++) {
        currentText += (i > 0 ? ' ' : '') + words[i];
        contentEl.textContent = currentText;
        container.scrollTop = container.scrollHeight;
        if (words.length < 80) {
            await new Promise(r => setTimeout(r, 18));
        }
    }

    contentEl.innerHTML = window._renderMd ? window._renderMd(text) : text;
    container.scrollTop = container.scrollHeight;
    wrapper.dataset.content = text;
};

DashboardController.prototype.toggleMentorHelp = function() {
    const panel = document.getElementById('mentor-help-panel');
    panel.classList.toggle('hidden');
};

DashboardController.prototype.clearMentorChat = function() {
    if (confirm('Clear conversation history?')) {
        localStorage.removeItem('mentor_history');
        this._toast('Conversation history cleared', 'info');
        const container = document.getElementById('mentor-messages');
        if (container) {
            container.innerHTML = `
                <div class="flex gap-3 animate-fade-in">
                    <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                        <i class="fas fa-robot text-xs text-white"></i>
                    </div>
                    <div class="bg-gray-700 p-4 rounded-2xl rounded-tl-none max-w-[85%] border border-gray-600">
                        <p class="text-gray-200 text-sm">Chat history cleared. How can I help you today?</p>
                    </div>
                </div>
            `;
        }
        this._hideMentorRecommendations();
    }
};

DashboardController.prototype._handleMentorLessonClick = async function(lessonId, url) {
    if (lessonId) {
        this.apiRequest('/ai/mentor/track-lesson-click', {
            method: 'POST',
            body: JSON.stringify({ lesson_id: String(lessonId) })
        }).catch(e => console.warn('[Mentor] Lesson click tracking failed:', e));
    }

    const _origin = window.location.origin;
    const destination = url
        ? (url.startsWith('http') ? url : _origin + url)
        : (lessonId ? `${_origin}/academy.html?lesson=${lessonId}` : `${_origin}/academy.html`);

    console.log('[Mentor] Navigating to lesson:', destination);
    window.location.href = destination;
};

