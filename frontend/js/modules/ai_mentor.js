const AIMentorPage = {
    messages: [],
    currentUser: null,

    async init() {
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
                <p>Personalized trading guidance & structured learning</p>
            </div>

            <div class="mentor-container" style="display: grid; grid-template-columns: 1fr 340px; gap: 2rem; max-width: 1400px; margin: 0 auto;">
                <!-- Main Chat Area -->
                <div>
                    <div class="chat-box" id="chatBox" style="height: 550px; overflow-y: auto; border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; background: var(--bg-secondary); margin-bottom: 1rem; display: flex; flex-direction: column; gap: 1rem;">
                        <div class="message mentor">
                            <div style="display: flex; gap: 1rem; align-items: flex-start;">
                                <div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, var(--primary), var(--primary-dark)); display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0;">🎓</div>
                                <div style="background: var(--bg); padding: 1rem 1.25rem; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); flex: 1; border: 1px solid var(--border);">
                                    <p style="margin: 0; line-height: 1.5;">Welcome! I'm your AI Trading Mentor. Ask me anything about trading, or type <strong>/next</strong> to continue your Academy lessons.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div style="display: flex; gap: 0.75rem;">
                        <input type="text" id="mentorInput" class="form-control" 
                               placeholder="Ask about trading or type /next to continue..." 
                               style="flex: 1; padding: 1rem; border: 1px solid var(--border); border-radius: 10px; font-size: 1rem;"
                               onkeypress="if(event.key==='Enter') AIMentorPage.sendMessage()">
                        <button onclick="AIMentorPage.sendMessage()" class="btn btn-primary" style="padding: 1rem 1.5rem; border-radius: 10px; font-weight: 600;">
                            Send
                        </button>
                    </div>

                    <div style="margin-top: 0.75rem; display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center;">
                        <span style="font-size: 0.8rem; color: var(--text-muted);">Quick:</span>
                        <button onclick="AIMentorPage.ask('/next')" class="btn btn-sm btn-outline">➡️ Continue</button>
                        <button onclick="AIMentorPage.ask('What is support and resistance?')" class="btn btn-sm btn-outline">📊 S/R Levels</button>
                        <button onclick="AIMentorPage.ask('How do I manage risk?')" class="btn btn-sm btn-outline">🛡️ Risk</button>
                        <button onclick="AIMentorPage.ask('/help')" class="btn btn-sm btn-outline">❓ Help</button>
                    </div>
                </div>

                <!-- Sidebar -->
                <div>
                    <!-- Progress Card -->
                    <div class="card" style="margin-bottom: 1rem; border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 12px; overflow: hidden;">
                        <div class="card-header" style="background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: white; padding: 1rem;">
                            <h3 style="margin: 0; font-size: 1rem; display: flex; align-items: center; gap: 0.5rem;">📚 Your Progress</h3>
                        </div>
                        <div class="card-body" id="progressCard" style="padding: 1rem;">
                            <div style="text-align: center; padding: 1rem; color: var(--text-muted);">
                                <div class="spinner" style="width: 24px; height: 24px; border: 2px solid var(--border); border-top-color: var(--primary); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 0.5rem;"></div>
                                <span style="font-size: 0.9rem;">Loading...</span>
                            </div>
                        </div>
                    </div>

                    <!-- Stats Card -->
                    <div class="card" style="border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 12px;">
                        <div class="card-header" style="background: var(--bg); border-bottom: 1px solid var(--border); padding: 1rem;">
                            <h3 style="margin: 0; font-size: 1rem;">Session Stats</h3>
                        </div>
                        <div class="card-body" style="padding: 1rem;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                                <span style="color: var(--text-muted); font-size: 0.9rem;">Messages</span>
                                <strong style="font-size: 1.1rem;">${this.messages.length}</strong>
                            </div>
                            <div style="height: 6px; background: var(--bg-secondary); border-radius: 3px; overflow: hidden;">
                                <div style="width: ${Math.min(this.messages.length * 5, 100)}%; height: 100%; background: linear-gradient(90deg, var(--primary), var(--success)); transition: width 0.3s;"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <style>
                @keyframes spin { to { transform: rotate(360deg); } }
            </style>
        `;

        this.loadAcademyProgress();
        setTimeout(() => document.getElementById('mentorInput')?.focus(), 100);
    },

    async loadAcademyProgress() {
        try {
            const userId = this.currentUser?.id || 'me';
            const response = await API.get(\`/learning/progress/\${userId}\`);
            const card = document.getElementById('progressCard');

            if (!card || !response) return;

            const rate = response.completion_rate || 0;
            const level = response.summary?.find(s => s.percent < 100)?.level_name || response.summary?.[response.summary.length - 1]?.level_name || 'Beginner';
            const completed = response.completed_lessons || 0;
            const total = response.total_lessons || 1;

            card.innerHTML = `
                <div style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.9rem;">
                        <span style="color: var(--text-muted);">Overall Progress</span>
                        <strong style="color: var(--primary);">${rate}%</strong>
                    </div>
                    <div style="height: 8px; background: var(--bg-secondary); border-radius: 4px; overflow: hidden;">
                        <div style="width: ${rate}%; height: 100%; background: linear-gradient(90deg, var(--success), var(--primary)); border-radius: 4px; transition: width 0.5s ease;"></div>
                    </div>
                </div>
                <div style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                        <span>Current Level:</span>
                        <strong style="color: var(--text);">${level}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Lessons:</span>
                        <strong style="color: var(--text);">${completed}/${total}</strong>
                    </div>
                </div>
                ${rate < 100 ? `
                <button onclick="AIMentorPage.ask('/next')" class="btn btn-primary" style="width: 100%; padding: 0.75rem; border-radius: 8px; font-weight: 600;">
                    Continue Learning →
                </button>
                ` : `
                <div style="text-align: center; padding: 0.75rem; background: rgba(16, 185, 129, 0.1); border-radius: 8px; color: var(--success); font-weight: 600;">
                    🎉 Academy Completed!
                </div>
                `}
            `;
        } catch (e) {
            console.log('[MENTOR] Progress load error:', e);
            const card = document.getElementById('progressCard');
            if (card) {
                card.innerHTML = `
                    <div style="text-align: center; padding: 1rem;">
                        <p style="color: var(--text-muted); margin-bottom: 1rem; font-size: 0.9rem;">Start your trading education!</p>
                        <button onclick="AIMentorPage.ask('/next')" class="btn btn-primary" style="width: 100%;">
                            Start Academy
                        </button>
                    </div>
                `;
            }
        }
    },

    async sendMessage() {
        const input = document.getElementById('mentorInput');
        const msg = input.value.trim();
        if (!msg) return;

        this.addMessage(msg, 'user');
        input.value = '';
        this.showTyping();

        try {
            const res = await API.askMentor(msg);
            this.hideTyping();
            this.addMessage(res.response, 'mentor', res);
            if (res.academy_progress) this.loadAcademyProgress();
        } catch (e) {
            this.hideTyping();
            this.addMessage('Sorry, error occurred. Please try again.', 'mentor');
        }
    },

    ask(q) {
        const input = document.getElementById('mentorInput');
        if (input) {
            input.value = q;
            this.sendMessage();
        }
    },

    showTyping() {
        const box = document.getElementById('chatBox');
        const div = document.createElement('div');
        div.id = 'typingIndicator';
        div.className = 'message mentor';
        div.innerHTML = `
            <div style="display: flex; gap: 1rem; align-items: flex-start;">
                <div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, var(--primary), var(--primary-dark)); display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">🎓</div>
                <div style="background: var(--bg); padding: 1rem 1.5rem; border-radius: 12px; display: flex; gap: 4px; align-items: center;">
                    <span style="width: 8px; height: 8px; background: var(--text-muted); border-radius: 50%; opacity: 0.4; animation: bounce 1s infinite;"></span>
                    <span style="width: 8px; height: 8px; background: var(--text-muted); border-radius: 50%; opacity: 0.4; animation: bounce 1s infinite 0.2s;"></span>
                    <span style="width: 8px; height: 8px; background: var(--text-muted); border-radius: 50%; opacity: 0.4; animation: bounce 1s infinite 0.4s;"></span>
                </div>
            </div>
        `;
        box.appendChild(div);
        box.scrollTop = box.scrollHeight;

        if (!document.getElementById('animStyles')) {
            const s = document.createElement('style');
            s.id = 'animStyles';
            s.textContent = \`@keyframes bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-4px)} }\`;
            document.head.appendChild(s);
        }
    },

    hideTyping() {
        document.getElementById('typingIndicator')?.remove();
    },

    addMessage(text, sender, data = null) {
        const box = document.getElementById('chatBox');
        const div = document.createElement('div');
        div.className = \`message \${sender}\`;
        div.style.marginBottom = '1rem';

        const isMentor = sender === 'mentor';
        const bg = isMentor ? 'var(--bg)' : 'linear-gradient(135deg, var(--primary-light), var(--primary-lighter))';
        const border = isMentor ? '1px solid var(--border)' : 'none';

        let html = \`<div style="display: flex; gap: 1rem; align-items: flex-start; \${!isMentor ? 'flex-direction: row-reverse;' : ''}">\`;

        // Avatar
        html += \`<div style="width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; \${isMentor ? 'background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: white;' : 'background: var(--bg-tertiary);'}">\`;
        html += isMentor ? '🎓' : '👤';
        html += '</div>';

        // Content
        html += \`<div style="max-width: calc(100% - 60px);">\`;
        html += \`<div style="background: \${bg}; padding: 1rem 1.25rem; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: \${border}; line-height: 1.5; color: var(--text);">\`;
        html += text.replace(/\n/g, '<br>');
        html += '</div>';

        // LESSON RECOMMENDATIONS - CRITICAL SECTION
        if (data?.recommendations?.length > 0) {
            const lessons = data.recommendations.filter(r => r.type === 'lesson');
            if (lessons.length > 0) {
                html += \`<div style="margin-top: 0.75rem; display: flex; flex-direction: column; gap: 0.75rem;">\`;

                lessons.forEach(lesson => {
                    const isNext = lesson.reason === 'next_step';
                    const icon = isNext ? '➡️' : '📚';
                    const badge = isNext ? 'Continue' : 'Recommended';
                    const badgeColor = isNext ? 'var(--success)' : 'var(--primary)';
                    const bgColor = isNext ? 'rgba(16, 185, 129, 0.08)' : 'rgba(99, 102, 241, 0.08)';
                    const borderColor = isNext ? 'rgba(16, 185, 129, 0.2)' : 'rgba(99, 102, 241, 0.2)';

                    html += \`
                        <div onclick="AIMentorPage.openLesson(\${lesson.metadata?.lesson_id || 0}, '\${lesson.url || '/academy.html'}')"
                             style="background: \${bgColor}; border: 1px solid \${borderColor}; border-radius: 10px; padding: 1rem; cursor: pointer; transition: all 0.2s;"
                             onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.1)';"
                             onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                            <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                                <span style="font-size: 1.25rem;">\${icon}</span>
                                <span style="font-size: 0.75rem; font-weight: 700; color: \${badgeColor}; text-transform: uppercase; letter-spacing: 0.05em;">\${badge}</span>
                            </div>
                            <div style="font-weight: 700; color: var(--text); margin-bottom: 0.25rem; font-size: 1rem;">\${lesson.title}</div>
                            <div style="font-size: 0.875rem; color: var(--text-muted); margin-bottom: 0.75rem;">\${lesson.description || ''}</div>
                            <button style="background: \${badgeColor}; color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.875rem; font-weight: 600; cursor: pointer; width: 100%;">
                                \${isNext ? 'Resume Lesson →' : 'Open Lesson'}
                            </button>
                        </div>
                    \`;
                });

                html += '</div>';
            }
        }

        html += '</div></div>';
        div.innerHTML = html;
        box.appendChild(div);
        box.scrollTop = box.scrollHeight;

        this.messages.push({ text, sender, data });
    },

    async openLesson(id, url) {
        if (!id && !url) return;
        try {
            await API.post('/ai/mentor/track-lesson-click', { lesson_id: id || 0, action: 'start' });
        } catch (e) {}
        window.open(url || \`/academy.html?lesson=\${id}\`, '_blank');
    }
};

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('app')) {
        AIMentorPage.init();
    }
});
