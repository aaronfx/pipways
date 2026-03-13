const AIMentorPage = {
    async render(container) {
        container.innerHTML = `
            <div class="page-header">
                <h1>🎓 AI Trading Mentor</h1>
                <p>Your personal trading coach available 24/7</p>
            </div>
            
            <div class="mentor-container" style="display: grid; grid-template-columns: 1fr 300px; gap: 2rem;">
                <div class="chat-section">
                    <div id="mentorChat" class="chat-box" style="height: 400px; overflow-y: auto; border: 1px solid #e5e7eb; padding: 1rem; border-radius: 0.5rem; background: #f9fafb;">
                        <div class="message system">
                            <p>👋 Welcome! I'm your AI trading mentor. Ask me anything about trading, risk management, or strategy!</p>
                        </div>
                    </div>
                    
                    <div class="input-area" style="margin-top: 1rem; display: flex; gap: 0.5rem;">
                        <input type="text" id="mentorInput" placeholder="Ask your question..." 
                               style="flex: 1; padding: 0.75rem; border: 1px solid #e5e7eb; border-radius: 0.375rem;"
                               onkeypress="if(event.key==='Enter') AIMentorPage.sendMessage()">
                        <button onclick="AIMentorPage.sendMessage()" class="btn btn-primary">Ask</button>
                    </div>
                    
                    <div class="quick-questions" style="margin-top: 1rem;">
                        <small style="color: #64748b;">Quick questions:</small>
                        <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem; flex-wrap: wrap;">
                            <button onclick="AIMentorPage.askQuick('How do I manage risk?')" class="btn btn-sm btn-secondary">Risk Management</button>
                            <button onclick="AIMentorPage.askQuick('What is a good R:R ratio?')" class="btn btn-sm btn-secondary">R:R Ratio</button>
                            <button onclick="AIMentorPage.askQuick('How do I control emotions?')" class="btn btn-sm btn-secondary">Trading Psychology</button>
                        </div>
                    </div>
                </div>
                
                <div class="sidebar">
                    <div class="card" style="background: white; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                        <h3>Daily Wisdom</h3>
                        <p id="dailyWisdom" style="font-style: italic; color: #64748b;">Loading...</p>
                        <button onclick="AIMentorPage.loadDailyWisdom()" class="btn btn-text btn-sm">Refresh</button>
                    </div>
                    
                    <div class="card" style="background: white; padding: 1rem; border-radius: 0.5rem;">
                        <h3>Learning Path</h3>
                        <p style="font-size: 0.875rem; color: #64748b; margin-bottom: 1rem;">Get a personalized curriculum</p>
                        <button onclick="AIMentorPage.showLearningPathModal()" class="btn btn-secondary btn-block">Generate Path</button>
                    </div>
                </div>
            </div>
        `;
        
        this.loadDailyWisdom();
    },

    async sendMessage() {
        const input = document.getElementById('mentorInput');
        const question = input.value.trim();
        if (!question) return;
        
        this.addMessage('user', question);
        input.value = '';
        
        try {
            const response = await API.askMentor(question);
            this.addMessage('mentor', response.response);
            
            // Show follow-ups if available
            if (response.follow_up_questions) {
                this.showFollowUps(response.follow_up_questions);
            }
        } catch (error) {
            this.addMessage('mentor', 'Sorry, I encountered an error. Please try again.');
        }
    },

    askQuick(question) {
        document.getElementById('mentorInput').value = question;
        this.sendMessage();
    },

    addMessage(role, text) {
        const chat = document.getElementById('mentorChat');
        const div = document.createElement('div');
        div.className = `message ${role}`;
        div.style.marginBottom = '1rem';
        div.innerHTML = `
            <div style="display: flex; gap: 0.5rem; ${role === 'user' ? 'flex-direction: row-reverse;' : ''}">
                <span style="font-size: 1.5rem;">${role === 'user' ? '👤' : '🤖'}</span>
                <div style="background: ${role === 'user' ? '#3b82f6' : 'white'}; 
                            color: ${role === 'user' ? 'white' : 'black'};
                            padding: 0.75rem; border-radius: 0.5rem; max-width: 80%;">
                    ${text}
                </div>
            </div>
        `;
        chat.appendChild(div);
        chat.scrollTop = chat.scrollHeight;
    },

    async loadDailyWisdom() {
        try {
            const data = await API.getDailyWisdom();
            document.getElementById('dailyWisdom').innerHTML = 
                `"${data.quote}" — ${data.author}`;
        } catch (e) {
            document.getElementById('dailyWisdom').textContent = 'Trading is 80% psychology and 20% strategy.';
        }
    },

    showLearningPathModal() {
        UI.showModal(`
            <h2>Generate Your Learning Path</h2>
            <form onsubmit="AIMentorPage.generateLearningPath(event)">
                <div class="form-group">
                    <label>Your Goal</label>
                    <select name="goal" required>
                        <option value="consistent_profits">Consistent Monthly Profits</option>
                        <option value="risk_management">Master Risk Management</option>
                        <option value="scalping">Become a Scalper</option>
                        <option value="swing_trading">Swing Trading Mastery</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Current Level</label>
                    <select name="level" required>
                        <option value="beginner">Beginner (0-6 months)</option>
                        <option value="intermediate">Intermediate (6-24 months)</option>
                        <option value="advanced">Advanced (2+ years)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Time Available (hours/week)</label>
                    <select name="time" required>
                        <option value="5">5 hours</option>
                        <option value="10">10 hours</option>
                        <option value="20">20+ hours</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary btn-block">Generate Path</button>
            </form>
        `);
    },

    async generateLearningPath(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        try {
            const path = await API.getLearningPath(
                formData.get('goal'),
                formData.get('level'),
                formData.get('time')
            );
            
            UI.closeModal();
            this.displayLearningPath(path);
        } catch (error) {
            UI.showToast('Failed to generate path', 'error');
        }
    },

    displayLearningPath(path) {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="page-header">
                <h1>📚 Your Learning Path</h1>
                <p>${path.goal} • ${path.duration_weeks} weeks • ${path.weekly_time_commitment}h/week</p>
            </div>
            <div class="learning-path">
                ${path.phases.map((phase, idx) => `
                    <div class="phase-card" style="background: white; padding: 1.5rem; margin-bottom: 1rem; border-radius: 0.5rem; border-left: 4px solid #3b82f6;">
                        <h3>Phase ${idx + 1}: ${phase.focus} <small style="color: #64748b;">(${phase.weeks})</small></h3>
                        <div style="margin: 1rem 0;">
                            <strong>Topics:</strong>
                            <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">
                                ${phase.topics.map(t => `<li>${t}</li>`).join('')}
                            </ul>
                        </div>
                        <div>
                            <strong>Tasks:</strong>
                            <ul style="margin: 0.5rem 0; padding-left: 1.5rem; color: #059669;">
                                ${phase.tasks.map(t => `<li>${t}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                `).join('')}
            </div>
            <button onclick="Router.go('#/ai/mentor')" class="btn btn-secondary">Back to Mentor</button>
        `;
    },

    showFollowUps(questions) {
        const chat = document.getElementById('mentorChat');
        const div = document.createElement('div');
        div.style.marginTop = '0.5rem';
        div.innerHTML = `
            <small style="color: #64748b;">Suggested follow-ups:</small>
            <div style="display: flex; gap: 0.5rem; margin-top: 0.25rem; flex-wrap: wrap;">
                ${questions.map(q => `
                    <button onclick="AIMentorPage.askQuick('${q}')" 
                            style="background: #e0e7ff; border: none; padding: 0.25rem 0.5rem; 
                                   border-radius: 1rem; font-size: 0.75rem; cursor: pointer;">
                        ${q}
                    </button>
                `).join('')}
            </div>
        `;
        chat.appendChild(div);
        chat.scrollTop = chat.scrollHeight;
    }
};
