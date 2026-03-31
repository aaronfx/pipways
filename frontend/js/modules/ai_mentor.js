/**
 * AI Mentor Frontend with Trading Academy Integration
 * Renders lesson recommendation cards below AI responses
 * 
 * REQUIRED CSS: See CSS block at bottom of file
 */

class AIMentor {
    constructor() {
        this.apiBaseUrl = '/api/ai';
        this.chatContainer = document.getElementById('mentor-messages');
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
        // Personalise greeting using stored user + cached academy progress
        const user = JSON.parse(localStorage.getItem('pipways_user') || '{}');
        const firstName = (user.full_name || user.email || 'Trader').split(' ')[0];
        const perf = JSON.parse(localStorage.getItem('pipways_performance') || '{}');
        let subText = 'Ask me about strategies, risk management, or specific concepts.';
        if (perf.overall_grade) {
            subText = `Your last performance grade was <strong>${perf.overall_grade}</strong>. Ask me how to improve, or explore a new concept.`;
        }
        const welcomeHTML = `
            <div class="message ai-message">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <div class="message-text">
                        Welcome back, <strong>${this.escapeHtml(firstName)}</strong>! 👋<br>
                        ${subText}<br><br>
                        I'll recommend Academy lessons tailored to your questions.
                    </div>
                    <div class="message-time">${this.getCurrentTime()}</div>
                </div>
            </div>
        `;
        this.chatContainer?.insertAdjacentHTML('beforeend', welcomeHTML);
    }

    /**
     * FIXED: Handles API call to /mentor/ask and renders recommendations separately
     */
    async sendMessage() {
        const message = this.inputField?.value.trim();
        if (!message) return;

        // Add user message
        this.addMessage(message, 'user');
        this.inputField.value = '';

        // Show typing indicator
        this.showTyping();

        try {
            // CRITICAL FIX: Direct API call to /mentor/ask (not /api/ai/mentor/ask)
            const response = await fetch(`/ai/mentor/ask`, {
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

            // Add AI text response
            this.addMessage(data.response, 'ai');

            // CRITICAL FIX: Render recommendations into dedicated container
            this.renderRecommendations(data.recommendations || []);

            // Update progress sidebar if available
            if (data.academy_progress) {
                this.updateProgressSidebar(data.academy_progress);
            }

            // Refresh usage counters so badge decrements immediately after this use
            if (window.PipwaysUsage) window.PipwaysUsage.loadUserLimits();

        } catch (error) {
            this.hideTyping();

            // 402 limit reached — show upgrade modal
            if (error.message && (error.message.includes('limit_reached') || error.message.includes('402'))) {
                if (window.PipwaysUsage && PipwaysUsage.showUpgradeModal) {
                    PipwaysUsage.showUpgradeModal('ai_mentor',
                        PipwaysUsage.used('ai_mentor'),
                        PipwaysUsage.limit('ai_mentor'));
                } else if (window.PaymentsPage) {
                    PaymentsPage.showUpgradeModal('AI Mentor');
                }
                this.addMessage(
                    "You've reached your free AI Mentor limit. Upgrade to Pro for unlimited sessions. 👆",
                    'ai'
                );
                this.renderRecommendations([]);
                return;
            }

            this.addMessage(
                "I'm having trouble connecting. Please try again shortly.",
                'ai'
            );
            this.renderRecommendations([]);
        }
    }

    /**
     * Adds chat message to container
     * FIXED: Removed recommendations parameter - now handled separately
     */
    addMessage(text, sender) {
        const isAI = sender === 'ai';
        const messageHTML = `
            <div class="message ${isAI ? 'ai-message' : 'user-message'}">
                <div class="message-avatar">${isAI ? '🤖' : '👤'}</div>
                <div class="message-content">
                    <div class="message-text">${this.escapeHtml(text)}</div>
                    <div class="message-time">${this.getCurrentTime()}</div>
                </div>
            </div>
        `;
        this.chatContainer?.insertAdjacentHTML('beforeend', messageHTML);
        this.scrollToBottom();
    }

    /**
     * NEW: Renders lesson recommendations into dedicated container
     * Prevents duplicates, handles empty state, provides clean UI
     */
    renderRecommendations(recommendations) {
        const container = document.getElementById('mentor-recommendations');
        if (!container) {
            console.warn('[AIMentor] mentor-recommendations container not found in DOM');
            return;
        }

        // CRITICAL: Clear old recommendations to prevent duplicates
        container.innerHTML = '';
        
        // Handle empty recommendations - hide container
        if (!recommendations || recommendations.length === 0) {
            container.style.display = 'none';
            return;
        }

        // Show container and render header
        container.style.display = 'block';
        const header = document.createElement('div');
        header.className = 'recommendations-header';
        header.innerHTML = '<span>📚</span> Recommended Lessons';
        container.appendChild(header);

        // Create grid for cards
        const grid = document.createElement('div');
        grid.className = 'recommendations-grid';

        // Render each recommendation card
        recommendations.forEach((rec) => {
            const lessonId = rec.metadata?.lesson_id;
            const card = this.createRecommendationCard(rec, lessonId);
            grid.appendChild(card);
        });

        container.appendChild(grid);
        this.scrollToBottom();
    }

    /**
     * NEW: Creates a single recommendation card DOM element
     */
    createRecommendationCard(rec, lessonId) {
        const card = document.createElement('div');
        card.className = 'lesson-card';
        
        card.innerHTML = `
            <div class="lesson-card-content">
                <div class="lesson-badge">Trading Academy</div>
                <h4 class="lesson-title">${this.escapeHtml(rec.title)}</h4>
                <p class="lesson-description">${this.escapeHtml(rec.description)}</p>
                <button class="lesson-cta-btn" type="button">
                    Start Lesson →
                </button>
            </div>
        `;

        // Click handler for entire card
        card.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.handleLessonClick(lessonId, rec.url);
        });

        return card;
    }

    /**
     * NEW: Handles lesson click with tracking and navigation
     * FIXED: Uses POST /mentor/track-lesson-click with JSON body
     */
    async handleLessonClick(lessonId, url) {
        // Track click if we have lesson ID
        if (lessonId) {
            try {
                await fetch(`/ai/mentor/track-lesson-click`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    },
                    body: JSON.stringify({ lesson_id: lessonId })  // Required format
                });
            } catch (e) {
                console.error('[AIMentor] Click tracking failed:', e);
                // Continue to navigation even if tracking fails
            }
        }

        // Navigate to lesson URL
        if (url) {
            window.open(url, '_blank');
        }
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

/**
 * REQUIRED CSS - Add to your stylesheet
 * 
 * #mentor-recommendations {
 *     margin: 20px 0;
 *     padding: 20px;
 *     background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
 *     border-radius: 12px;
 *     border: 1px solid #bae6fd;
 * }
 * 
 * .recommendations-header {
 *     font-size: 16px;
 *     font-weight: 600;
 *     color: #0369a1;
 *     margin-bottom: 16px;
 *     display: flex;
 *     align-items: center;
 *     gap: 8px;
 * }
 * 
 * .recommendations-grid {
 *     display: grid;
 *     grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
 *     gap: 16px;
 * }
 * 
 * .lesson-card {
 *     background: white;
 *     border-radius: 10px;
 *     padding: 20px;
 *     box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
 *     cursor: pointer;
 *     transition: all 0.2s ease;
 *     border: 1px solid #e2e8f0;
 *     position: relative;
 *     overflow: hidden;
 * }
 * 
 * .lesson-card:hover {
 *     transform: translateY(-3px);
 *     box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
 *     border-color: #3b82f6;
 * }
 * 
 * .lesson-card::before {
 *     content: '';
 *     position: absolute;
 *     top: 0;
 *     left: 0;
 *     width: 4px;
 *     height: 100%;
 *     background: #3b82f6;
 *     opacity: 0;
 *     transition: opacity 0.2s;
 * }
 * 
 * .lesson-card:hover::before {
 *     opacity: 1;
 * }
 * 
 * .lesson-badge {
 *     display: inline-block;
 *     font-size: 11px;
 *     font-weight: 600;
 *     text-transform: uppercase;
 *     letter-spacing: 0.5px;
 *     color: #3b82f6;
 *     background: #eff6ff;
 *     padding: 4px 10px;
 *     border-radius: 20px;
 *     margin-bottom: 12px;
 * }
 * 
 * .lesson-title {
 *     margin: 0 0 8px 0;
 *     font-size: 16px;
 *     font-weight: 600;
 *     color: #1e293b;
 *     line-height: 1.4;
 * }
 * 
 * .lesson-description {
 *     margin: 0 0 16px 0;
 *     font-size: 14px;
 *     color: #64748b;
 *     line-height: 1.5;
 * }
 * 
 * .lesson-cta-btn {
 *     background: #3b82f6;
 *     color: white;
 *     border: none;
 *     padding: 10px 20px;
 *     border-radius: 8px;
 *     font-size: 14px;
 *     font-weight: 500;
 *     cursor: pointer;
 *     transition: all 0.2s;
 *     display: inline-flex;
 *     align-items: center;
 *     gap: 6px;
 *     width: 100%;
 *     justify-content: center;
 * }
 * 
 * .lesson-cta-btn:hover {
 *     background: #2563eb;
 * }
 */
