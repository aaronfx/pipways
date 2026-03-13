const AIMentorPage = {
    messages: [],
    
    async render() {
        const app = document.getElementById('app');
        
        app.innerHTML = `
            <div class="page-header">
                <h1>🎓 AI Trading Mentor</h1>
                <p>Get personalized trading advice and mentorship</p>
            </div>
            
            <div class="mentor-container" style="display: grid; grid-template-columns: 1fr 300px; gap: 2rem;">
                <div>
                    <div class="chat-box" id="chatBox">
                        <div class="message mentor">
                            <div style="display: flex; gap: 1rem;">
                                <div class="message-avatar" style="background: var(--primary); color: white;">🎓</div>
                                <div class="message-content">
                                    <p>Welcome! I'm your AI Trading Mentor. Ask me anything about trading, risk management, or strategy development.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 0.5rem;">
                        <input type="text" id="mentorInput" class="form-control" 
                               placeholder="Ask your trading question..." 
                               style="flex: 1; padding: 0.875rem; border: 1px solid var(--gray-300); border-radius: var(--radius);"
                               onkeypress="if(event.key==='Enter') AIMentorPage.sendMessage()">
                        <button onclick="AIMentorPage.sendMessage()" class="btn btn-primary">
                            Send
                        </button>
                    </div>
                </div>
                
                <div>
                    <div class="card" style="margin-bottom: 1rem;">
                        <div class="card-header">
                            <h3 class="card-title">Quick Topics</h3>
                        </div>
                        <div class="card-body" style="display: flex; flex-direction: column; gap: 0.5rem;">
                            <button onclick="AIMentorPage.ask('How do I manage risk?')" class="btn btn-text text-left">Risk Management</button>
                            <button onclick="AIMentorPage.ask('What is a good risk/reward ratio?')" class="btn btn-text text-left">R:R Ratios</button>
                            <button onclick="AIMentorPage.ask('How do I control emotions while trading?')" class="btn btn-text text-left">Trading Psychology</button>
                            <button onclick="AIMentorPage.ask('Explain support and resistance')" class="btn btn-text text-left">Technical Analysis</button>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Your Progress</h3>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                    <span>Mentor Sessions</span>
                                    <strong>${this.messages.length}</strong>
                                </div>
                                <div class="progress">
                                    <div class="progress-bar" style="width: ${Math.min(this.messages.length * 10, 100)}%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },
    
    async sendMessage() {
        const input = document.getElementById('mentorInput');
        const message = input.value.trim();
        if (!message) return;
        
        this.addMessage(message, 'user');
        input.value = '';
        
        try {
            const response = await API.askMentor(message);
            this.addMessage(response.response, 'mentor', response);
        } catch (e) {
            this.addMessage('Sorry, I encountered an error. Please try again.', 'mentor');
        }
    },
    
    ask(question) {
        document.getElementById('mentorInput').value = question;
        this.sendMessage();
    },
    
    addMessage(text, sender, data = null) {
        const chatBox = document.getElementById('chatBox');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        let html = '<div style="display: flex; gap: 1rem;">';
        
        if (sender === 'mentor') {
            html += `<div class="message-avatar" style="background: var(--primary); color: white;">🎓</div>`;
        } else {
            html += `<div class="message-avatar" style="background: var(--gray-300);">👤</div>`;
        }
        
        html += `<div class="message-content"><p>${text}</p>`;
        
        if (data?.suggested_resources?.length) {
            html += `<div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(0,0,0,0.1);">
                <small><strong>Suggested:</strong> ${data.suggested_resources.join(', ')}</small>
            </div>`;
        }
        
        html += '</div></div>';
        messageDiv.innerHTML = html;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
        
        this.messages.push({ text, sender });
    }
};
