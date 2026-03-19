const AIMentorPage = {
    messages: [],
    currentUser: null,

    async init() {
        // Load current user info
        try {
            const user = await API.getCurrentUser();
            this.currentUser = user;
        } catch (e) {
            console.log('[MENTOR] User not authenticated');
        }
        await this.render();
    },

    async render() {
        const app = document.getElementById('app');

        app.innerHTML = `
            <div class="page-header">
                <h1>🎓 AI Trading Mentor</h1>
                <p>Get personalized trading advice and structured learning guidance</p>
            </div>

            <div class="mentor-container" style="display: grid; grid-template-columns: 1fr 320px; gap: 2rem;">
                <!-- Main Chat Area -->
                <div>
                    <div class="chat-box" id="chatBox" style="height: 500px; overflow-y: auto; border: 1px solid var(--gray-200); border-radius: var(--radius); padding: 1rem; background: var(--gray-50); margin-bottom: 1rem;">
                        <div class="message mentor" style="margin-bottom: 1rem;">
                            <div style="display: flex; gap: 1rem; align-items: flex-start;">
                                <div class="message-avatar" style="background: var(--primary); color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">🎓</div>
                                <div class="message-content" style="background: white; padding: 1rem; border-radius: var(--radius); box-shadow: 0 1px 3px rgba(0,0,0,0.1); flex: 1;">
                                    <p>Welcome! I'm your AI Trading Mentor. I can help you with:</p>
                                    <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">
                                        <li>Answering trading questions</li>
                                        <li>Reviewing your performance</li>
                                        <li>Recommending Academy lessons</li>
                                        <li>Guiding your learning path</li>
                                    </ul>
                                    <p style="margin-bottom: 0;">Try commands like <code>/next</code> to continue learning, or ask me anything!</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div style="display: flex; gap: 0.5rem;">
                        <input type="text" id="mentorInput" class="form-control" 
                               placeholder="Ask about trading or type /next to continue learning..." 
                               style="flex: 1; padding: 0.875rem; border: 1px solid var(--gray-300); border-radius: var(--radius); font-size: 0.95rem;"
                               onkeypress="if(event.key==='Enter') AIMentorPage.sendMessage()">
                        <button onclick="AIMentorPage.sendMessage()" class="btn btn-primary" style="padding: 0.875rem 1.5rem;">
                            Send
                        </button>
                    </div>

                    <div style="margin-top: 0.5rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
                        <span style="font-size: 0.8rem; color: var(--gray-500);">Quick commands:</span>
                        <button onclick="AIMentorPage.ask('/next')" class="btn btn-sm btn-text" style="font-size: 0.8rem;">/next</button>
                        <button onclick="AIMentorPage.ask('/review-trades')" class="btn btn-sm btn-text" style="font-size: 0.8rem;">/review-trades</button>
                        <button onclick="AIMentorPage.ask('/signals')" class="btn btn-sm btn-text" style="font-size: 0.8rem;">/signals</button>
                        <button onclick="AIMentorPage.ask('/help')" class="btn btn-sm btn-text" style="font-size: 0.8rem;">/help</button>
                    </div>
                </div>

                <!-- Sidebar -->
                <div>
                    <!-- Learning Progress Card -->
                    <div class="card" style="margin-bottom: 1rem; border: none; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div class="card-header" style="background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: white; border-radius: var(--radius) var(--radius) 0 0;">
                            <h3 class="card-title" style="margin: 0; font-size: 1rem;">📚 Learning Progress</h3>
                        </div>
                        <div class="card-body" id="progressCard">
                            <div class="text-center" style="padding: 1rem; color: var(--gray-500);">
                                <div class="spinner"></div>
                                <p>Loading...</p>
                            </div>
                        </div>
                    </div>

                    <!-- Quick Topics Card -->
                    <div class="card" style="margin-bottom: 1rem; border: none; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div class="card-header" style="background: var(--gray-100); border-bottom: 1px solid var(--gray-200);">
                            <h3 class="card-title" style="margin: 0; font-size: 1rem;">Quick Topics</h3>
                        </div>
                        <div class="card-body" style="display: flex; flex-direction: column; gap: 0.5rem; padding: 0.75rem;">
                            <button onclick="AIMentorPage.ask('How do I manage risk?')" class="btn btn-text text-left" style="justify-content: flex-start; padding: 0.5rem;">🛡️ Risk Management</button>
                            <button onclick="AIMentorPage.ask('What is a good risk/reward ratio?')" class="btn btn-text text-left" style="justify-content: flex-start; padding: 0.5rem;">⚖️ R:R Ratios</button>
                            <button onclick="AIMentorPage.ask('How do I control emotions while trading?')" class="btn btn-text text-left" style="justify-content: flex-start; padding: 0.5rem;">🧠 Trading Psychology</button>
                            <button onclick="AIMentorPage.ask('Explain support and resistance')" class="btn btn-text text-left" style="justify-content: flex-start; padding: 0.5rem;">📊 Technical Analysis</button>
                            <button onclick="AIMentorPage.ask('What is an order block?')" class="btn btn-text text-left" style="justify-content: flex-start; padding: 0.5rem;">🏗️ Market Structure</button>
                        </div>
                    </div>

                    <!-- Session Stats -->
                    <div class="card" style="border: none; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div class="card-header" style="background: var(--gray-100); border-bottom: 1px solid var(--gray-200);">
                            <h3 class="card-title" style="margin: 0; font-size: 1rem;">Session Stats</h3>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.9rem;">
                                    <span>Mentor Sessions</span>
                                    <strong>${this.messages.length}</strong>
                                </div>
                                <div class="progress" style="height: 6px; background: var(--gray-200); border-radius: 3px; overflow: hidden;">
                                    <div class="progress-bar" style="width: ${Math.min(this.messages.length * 5, 100)}%; height: 100%; background: var(--primary); transition: width 0.3s;"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Load progress after render
        this.loadAcademyProgress();

        // Focus input
        setTimeout(() => {
            const input = document.getElementById('mentorInput');
            if (input) input.focus();
        }, 100);
    },

    async loadAcademyProgress() {
        try {
            const response = await API.get('/learning/progress/' + (this.currentUser?.id || 'me'));
            const progressCard = document.getElementById('progressCard');

            if (response && progressCard) {
                const completionRate = response.completion_rate || 0;
                const currentLevel = response.summary?.[0]?.level_name || 'Beginner';
                const completed = response.completed_lessons || 0;
                const total = response.total_lessons || 1;

                progressCard.innerHTML = `
                    <div style="margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem; font-size: 0.85rem;">
                            <span style="color: var(--gray-600);">Overall Progress</span>
                            <strong>${completion_rate}%</strong>
                        </div>
                        <div class="progress" style="height: 8px; background: var(--gray-200); border-radius: 4px; overflow: hidden;">
                            <div class="progress-bar" style="width: ${completionRate}%; height: 100%; background: linear-gradient(90deg, var(--success), var(--primary)); transition: width 0.5s;"></div>
                        </div>
                    </div>
                    <div style="font-size: 0.85rem; color: var(--gray-600); margin-bottom: 0.5rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                            <span>Current Level:</span>
                            <strong>${currentLevel}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Completed:</span>
                            <strong>${completed}/${total} lessons</strong>
                        </div>
                    </div>
                    ${completionRate < 100 ? `
                    <button onclick="AIMentorPage.ask('/next')" class="btn btn-primary btn-sm" style="width: 100%; margin-top: 0.5rem;">
                        Continue Learning ➡️
                    </button>
                    ` : `
                    <div style="text-align: center; padding: 0.5rem; background: var(--success-light); border-radius: var(--radius); margin-top: 0.5rem;">
                        <span style="color: var(--success); font-size: 0.85rem;">🎉 Academy Completed!</span>
                    </div>
                    `}
                `;
            }
        } catch (e) {
            console.log('[MENTOR] Could not load progress:', e);
            const progressCard = document.getElementById('progressCard');
            if (progressCard) {
                progressCard.innerHTML = `
                    <div style="text-align: center; padding: 1rem; color: var(--gray-500);">
                        <p style="margin-bottom: 0.5rem;">Start your learning journey!</p>
                        <button onclick="AIMentorPage.ask('/next')" class="btn btn-primary btn-sm">
                            Start Academy
                        </button>
                    </div>
                `;
            }
        }
    },

    async sendMessage() {
        const input = document.getElementById('mentorInput');
        const message = input.value.trim();
        if (!message) return;

        this.addMessage(message, 'user');
        input.value = '';

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await API.askMentor(message);
            this.hideTypingIndicator();
            this.addMessage(response.response, 'mentor', response);

            // Refresh progress if it changed
            if (response.academy_progress) {
                this.loadAcademyProgress();
            }
        } catch (e) {
            this.hideTypingIndicator();
            console.error('[MENTOR] Error:', e);
            this.addMessage('Sorry, I encountered an error. Please try again.', 'mentor');
        }
    },

    ask(question) {
        const input = document.getElementById('mentorInput');
        if (input) {
            input.value = question;
            this.sendMessage();
        }
    },

    showTypingIndicator() {
        const chatBox = document.getElementById('chatBox');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typingIndicator';
        typingDiv.className = 'message mentor';
        typingDiv.style.marginBottom = '1rem';
        typingDiv.innerHTML = `
            <div style="display: flex; gap: 1rem; align-items: flex-start;">
                <div class="message-avatar" style="background: var(--primary); color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">🎓</div>
                <div class="message-content" style="background: white; padding: 1rem; border-radius: var(--radius); box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="display: flex; gap: 4px; align-items: center;">
                        <span style="width: 8px; height: 8px; background: var(--gray-400); border-radius: 50%; animation: bounce 1s infinite;"></span>
                        <span style="width: 8px; height: 8px; background: var(--gray-400); border-radius: 50%; animation: bounce 1s infinite 0.2s;"></span>
                        <span style="width: 8px; height: 8px; background: var(--gray-400); border-radius: 50%; animation: bounce 1s infinite 0.4s;"></span>
                    </div>
                </div>
            </div>
        `;
        chatBox.appendChild(typingDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

        // Add bounce animation if not present
        if (!document.getElementById('mentorAnimations')) {
            const style = document.createElement('style');
            style.id = 'mentorAnimations';
            style.textContent = `
                @keyframes bounce {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-4px); }
                }
            `;
            document.head.appendChild(style);
        }
    },

    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.remove();
    },

    addMessage(text, sender, data = null) {
        const chatBox = document.getElementById('chatBox');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.style.marginBottom = '1rem';

        let html = '<div style="display: flex; gap: 1rem; align-items: flex-start;">';

        if (sender === 'mentor') {
            html += `<div class="message-avatar" style="background: var(--primary); color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0;">🎓</div>`;
        } else {
            html += `<div class="message-avatar" style="background: var(--gray-300); width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0;">👤</div>`;
        }

        html += `<div class="message-content" style="${sender === 'mentor' ? 'background: white;' : 'background: var(--primary-light);'} padding: 1rem; border-radius: var(--radius); box-shadow: 0 1px 3px rgba(0,0,0,0.1); flex: 1; max-width: calc(100% - 60px);">`;

        // Format the message text (convert newlines to breaks)
        const formattedText = text.replace(/\n/g, '<br>');
        html += `<div style="line-height: 1.5; color: var(--gray-800);">${formattedText}</div>`;

        // Render lesson recommendations if present
        if (data && data.recommendations && data.recommendations.length > 0) {
            const lessonRecs = data.recommendations.filter(r => r.type === 'lesson');
            if (lessonRecs.length > 0) {
                html += `<div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--gray-200);">`;

                lessonRecs.forEach(rec => {
                    const isNextStep = rec.reason === 'next_step';
                    const icon = isNextStep ? '➡️' : '📚';
                    const badgeText = isNextStep ? 'Continue Learning' : 'Recommended Lesson';
                    const badgeColor = isNextStep ? 'var(--success)' : 'var(--primary)';

                    html += `
                        <div style="background: ${isNextStep ? '#f0fdf4' : '#eff6ff'}; border: 1px solid ${isNextStep ? '#bbf7d0' : '#bfdbfe'}; border-radius: var(--radius); padding: 0.75rem; margin-bottom: 0.5rem; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;"
                             onclick="AIMentorPage.openLesson(${rec.metadata?.lesson_id || 0}, '${rec.url || ''}')"
                             onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.1)';"
                             onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                                <span style="font-size: 1.2rem;">${icon}</span>
                                <span style="font-size: 0.75rem; font-weight: 600; color: ${badgeColor}; text-transform: uppercase; letter-spacing: 0.05em;">${badgeText}</span>
                            </div>
                            <div style="font-weight: 600; color: var(--gray-900); margin-bottom: 0.25rem;">${rec.title}</div>
                            <div style="font-size: 0.85rem; color: var(--gray-600);">${rec.description || ''}</div>
                            <div style="margin-top: 0.5rem; display: flex; gap: 0.5rem;">
                                <button class="btn btn-sm btn-primary" style="font-size: 0.8rem; padding: 0.25rem 0.75rem;">
                                    ${isNextStep ? 'Resume Lesson →' : 'Open Lesson'}
                                </button>
                            </div>
                        </div>
                    `;
                });

                html += `</div>`;
            }

            // Render other recommendations (non-lesson)
            const otherRecs = data.recommendations.filter(r => r.type !== 'lesson');
            if (otherRecs.length > 0) {
                html += `<div style="margin-top: 0.5rem;">`;
                otherRecs.forEach(rec => {
                    let icon = '📖';
                    if (rec.type === 'signal') icon = '📡';
                    if (rec.type === 'blog') icon = '📝';
                    if (rec.type === 'warning') icon = '⚠️';

                    html += `<div style="font-size: 0.85rem; color: var(--gray-600); margin-bottom: 0.25rem;">${icon} ${rec.title}</div>`;
                });
                html += `</div>`;
            }
        }

        html += '</div></div>';
        messageDiv.innerHTML = html;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

        this.messages.push({ text, sender, data });
    },

    async openLesson(lessonId, url) {
        if (!lessonId) return;

        // Track the click
        try {
            await API.post('/ai/mentor/track-lesson-click', {
                lesson_id: lessonId,
                action: 'start'
            });
        } catch (e) {
            console.log('[MENTOR] Track error:', e);
        }

        // Navigate to academy
        if (url) {
            window.open(url, '_blank');
        } else {
            window.open(`/academy.html?lesson=${lessonId}`, '_blank');
        }
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('app')) {
        AIMentorPage.init();
    }
});
