/**
 * AI Tools Module
 * Handles chat, chart analysis, and performance analysis
 */

const ai = {
    chatHistory: [],
    currentChartImage: null,
    currentPerformanceImage: null,

    async sendChatMessage() {
        const input = document.getElementById('chat-input');
        const messagesContainer = document.getElementById('chat-messages');
        const message = input.value.trim();
        
        if (!message) return;

        // Add user message
        const userMsgDiv = document.createElement('div');
        userMsgDiv.className = 'chat-message user';
        userMsgDiv.innerHTML = `<div class="chat-bubble"><strong>You:</strong> ${ui.escapeHtml(message)}</div>`;
        messagesContainer.appendChild(userMsgDiv);
        
        input.value = '';
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        this.chatHistory.push({ role: "user", content: message });

        try {
            const useKnowledge = document.getElementById('knowledge-toggle')?.checked ?? true;
            
            const response = await api.post('/api/ai/chat', {
                message: message,
                history: this.chatHistory.slice(-5),
                use_knowledge: useKnowledge
            });

            const aiResponse = response.response || response.message || 'No response received';
            this.chatHistory.push({ role: "assistant", content: aiResponse });

            const aiMsgDiv = document.createElement('div');
            aiMsgDiv.className = 'chat-message';
            aiMsgDiv.innerHTML = `<div class="chat-bubble"><strong>AI Mentor:</strong> ${ui.escapeHtml(aiResponse)}</div>`;
            messagesContainer.appendChild(aiMsgDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

        } catch (error) {
            ui.showToast('Failed to get response: ' + error.message, 'error');
        }
    },

    handleChartUpload(input) {
        const file = input.files[0];
        if (!file) return;

        if (file.size > 10 * 1024 * 1024) {
            ui.showToast('File too large. Max 10MB.', 'error');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            this.currentChartImage = e.target.result;
            document.getElementById('chart-preview').src = e.target.result;
            document.getElementById('chart-preview-container').classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    },

    async analyzeChart() {
        if (!this.currentChartImage) {
            ui.showToast('Please upload an image first', 'error');
            return;
        }

        ui.showLoading('Analyzing chart with AI...');

        try {
            const pair = document.getElementById('chart-pair').value || 'EURUSD';
            const timeframe = document.getElementById('chart-timeframe').value || '1H';
            const context = document.getElementById('chart-context').value || '';

            const response = await api.post('/api/ai/analyze-chart', {
                image: this.currentChartImage,
                pair: pair,
                timeframe: timeframe,
                context: context
            });

            document.getElementById('chart-analysis-content').textContent = response.analysis || 'No analysis available';
            document.getElementById('chart-analysis-result').classList.remove('hidden');
            
        } catch (error) {
            ui.showToast('Analysis failed: ' + error.message, 'error');
        } finally {
            ui.hideLoading();
        }
    },

    handlePerformanceUpload(input) {
        const file = input.files[0];
        if (!file) return;

        if (file.size > 10 * 1024 * 1024) {
            ui.showToast('File too large. Max 10MB.', 'error');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            this.currentPerformanceImage = e.target.result;
            document.getElementById('performance-preview').src = e.target.result;
            document.getElementById('performance-preview-container').classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    },

    async analyzePerformanceVision() {
        if (!this.currentPerformanceImage) {
            ui.showToast('Please upload a statement image', 'error');
            return;
        }

        ui.showLoading('Analyzing performance...');

        try {
            const balance = parseFloat(document.getElementById('vision-account-balance').value) || 0;
            const period = parseInt(document.getElementById('vision-trading-period').value) || 30;

            const response = await api.post('/api/performance/analyze-vision', {
                image: this.currentPerformanceImage,
                account_balance: balance,
                trading_period_days: period
            });

            this.displayPerformanceResults(response);
            
        } catch (error) {
            ui.showToast('Analysis failed: ' + error.message, 'error');
        } finally {
            ui.hideLoading();
        }
    },

    displayPerformanceResults(data) {
        document.getElementById('analysis-results').classList.remove('hidden');
        
        // Update score
        const score = data.trader_score || 0;
        document.getElementById('trader-score').textContent = score;
        document.getElementById('score-circle').style.setProperty('--score', score);
        
        // Interpretation
        let interpretation = 'Needs Improvement';
        if (score >= 80) interpretation = 'Excellent Trader';
        else if (score >= 60) interpretation = 'Good Performance';
        else if (score >= 40) interpretation = 'Average Performance';
        
        document.getElementById('score-interpretation').textContent = interpretation;

        // Summary
        document.getElementById('performance-summary').innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 12px;">
                <div>Total Trades: <strong>${data.total_trades || 0}</strong></div>
                <div>Win Rate: <strong>${data.win_rate || 0}%</strong></div>
                <div>Profit Factor: <strong>${data.profit_factor || 'N/A'}</strong></div>
                <div>Avg Return: <strong>${data.average_return || 0}%</strong></div>
            </div>
        `;

        // Lists
        const renderList = (items, containerId) => {
            const container = document.getElementById(containerId);
            if (!items || items.length === 0) {
                container.innerHTML = '<li>No data available</li>';
                return;
            }
            container.innerHTML = items.map(item => `<li>${item}</li>`).join('');
        };

        renderList(data.top_mistakes, 'top-mistakes');
        renderList(data.strengths, 'strengths-list');
        renderList(data.improvement_plan, 'improvement-plan');
        
        // Mentor advice
        document.getElementById('mentor-advice').textContent = data.mentor_advice || 'Keep practicing and learning from your trades.';
        
        // Recommended courses
        const coursesContainer = document.getElementById('recommended-courses');
        if (data.recommended_courses && data.recommended_courses.length > 0) {
            coursesContainer.innerHTML = data.recommended_courses.map(c => 
                `<span class="badge badge-info">${c}</span>`
            ).join('');
        } else {
            coursesContainer.innerHTML = '<span class="badge badge-secondary">No specific recommendations</span>';
        }
    }
};
