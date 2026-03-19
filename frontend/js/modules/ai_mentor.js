/**
 * AI Mentor Frontend with Trading Academy Integration
 * Renders lesson recommendation cards below AI responses
 */

class AIMentor {
    constructor() {
        this.apiBaseUrl = '/api/ai';
        this.chatContainer = document.getElementById('chat-messages');
        this.inputField = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-btn');
        this.academyProgress = null;

        this.init();
    }

    init() {
        // Event listeners
        this.sendButton?.addEventListener('click', () => this.sendMessage());
        this.inputField?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        // Quick command buttons
        document.querySelectorAll('.quick-cmd-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const cmd = e.target.dataset.cmd;
                this.handleQuickCommand(cmd);
            });
        });

        // Display welcome message
        this.addWelcomeMessage();
    }

    addWelcomeMessage() {
        const welcomeHTML = `
            <div class="message ai-message">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <div class="message-text">
                        Welcome to your AI Trading Mentor! Ask me about strategies, risk management, 
                        or specific concepts. I'll recommend Academy lessons tailored to your questions.
                    </div>
                    <div class="message-time">${this.getCurrentTime()}</div>
                </div>
            </div>
        `;
        this.chatContainer?.insertAdjacentHTML('beforeend', welcomeHTML);
    }

    async sendMessage() {
        const message = this.inputField?.value.trim();
        if (!message) return;

        // Add user message
        this.addMessage(message, 'user');
        this.inputField.value = '';

        // Show typing indicator
        this.showTyping();

        try {
            const response = await fetch(`${this.apiBaseUrl}/mentor/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    message: message,
                    context: { timestamp: new Date().toISOString() }
                })
            });

            if (!response.ok) throw new Error('Failed to get response');

            const data = await response.json();

            // Remove typing indicator
            this.hideTyping();

            // Add AI message with recommendations
            this.addMessage(data.response, 'ai', data.recommendations);

            // Update progress sidebar if available
            if (data.academy_progress) {
                this.updateProgressSidebar(data.academy_progress);
            }

        } catch (error) {
            this.hideTyping();
            this.addMessage(
                "I'm having trouble connecting. Please try again shortly.", 
                'ai',
                [{
                    type: 'lesson',
                    title: 'Trading Academy',
                    description: 'Browse all lessons',
                    url: '/academy.html',
                    reason: 'recommended'
                }]
            );
        }
    }

    addMessage(text, sender, recommendations = []) {
        const isAI = sender === 'ai';
        const messageHTML = `
            <div class="message ${isAI ? 'ai-message' : 'user-message'}">
                <div class="message-avatar">${isAI ? '🤖' : '👤'}</div>
                <div class="message-content">
                    <div class="message-text">${this.escapeHtml(text)}</div>
                    <div class="message-time">${this.getCurrentTime()}</div>

                    ${isAI && recommendations.length > 0 ? this.renderLessonCards(recommendations) : ''}
                </div>
            </div>
        `;

        this.chatContainer?.insertAdjacentHTML('beforeend', messageHTML);
        this.scrollToBottom();
    }

    renderLessonCards(recommendations) {
        if (!recommendations || recommendations.length === 0) return '';

        const cardsHTML = recommendations.map((rec, index) => {
            const isNextStep = rec.reason === 'next_step';
            const cardClass = isNextStep ? 'lesson-card-next' : 'lesson-card-recommended';
            const badgeText = isNextStep ? 'Continue Learning' : 'Recommended Lesson';
            const badgeClass = isNextStep ? 'badge-next' : 'badge-recommended';
            const lessonId = rec.metadata?.lesson_id || '';

            return `
                <div class="lesson-card ${cardClass}" 
                     onclick="mentor.openLesson(${lessonId}, '${rec.url}')"
                     data-lesson-id="${lessonId}">
                    <div class="lesson-card-header">
                        <span class="lesson-badge ${badgeClass}">${badgeText}</span>
                        <span class="lesson-icon">📚</span>
                    </div>
                    <div class="lesson-card-body">
                        <h4 class="lesson-title">${this.escapeHtml(rec.title)}</h4>
                        <p class="lesson-description">${this.escapeHtml(rec.description)}</p>
                    </div>
                    <div class="lesson-card-footer">
                        <button class="lesson-cta-btn">
                            ${isNextStep ? '▶ Continue' : '🎯 Start Lesson'}
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        return `
            <div class="lesson-recommendations">
                <div class="recommendations-label">📖 Recommended for you:</div>
                <div class="lesson-cards-container">
                    ${cardsHTML}
                </div>
            </div>
        `;
    }

    async openLesson(lessonId, url) {
        // Track the click
        if (lessonId) {
            try {
                await fetch(`${this.apiBaseUrl}/mentor/track-lesson-click?lesson_id=${lessonId}`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });
            } catch (e) {
                console.log('Tracking failed, continuing anyway');
            }
        }

        // Navigate to academy
        window.open(url, '_blank');
    }

    handleQuickCommand(cmd) {
        const commands = {
            '/next': 'What should I learn next?',
            '/review-trades': 'Can you review my recent trades?',
            '/signals': 'Show me active trading signals',
            '/help': 'What can you help me with?'
        };

        const message = commands[cmd] || cmd;
        if (this.inputField) {
            this.inputField.value = message;
            this.sendMessage();
        }
    }

    showTyping() {
        const typingHTML = `
            <div class="message ai-message typing-indicator" id="typing-indicator">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <div class="typing-dots">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        `;
        this.chatContainer?.insertAdjacentHTML('beforeend', typingHTML);
        this.scrollToBottom();
    }

    hideTyping() {
        const indicator = document.getElementById('typing-indicator');
        indicator?.remove();
    }

    scrollToBottom() {
        if (this.chatContainer) {
            this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getCurrentTime() {
        return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    updateProgressSidebar(progress) {
        const progressEl = document.getElementById('academy-progress');
        if (progressEl && progress) {
            progressEl.innerHTML = `
                <div class="progress-header">
                    <span>${progress.current_level || 'Beginner'}</span>
                    <span>${progress.completion_rate || 0}% Complete</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progress.completion_rate || 0}%"></div>
                </div>
            `;
        }
    }
}

// Initialize
let mentor;
document.addEventListener('DOMContentLoaded', () => {
    mentor = new AIMentor();
});

// Expose to global scope for onclick handlers
window.mentor = mentor;
