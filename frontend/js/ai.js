/**
 * AI Tools Module
 * Fixed: Proper POST requests and FormData for image upload
 */

const ai = {
    chatHistory: [],
    currentChartImage: null,
    currentChartFile: null,  // Store actual File object for upload
    currentPerformanceImage: null,

    async sendChatMessage() {
        const input = document.getElementById('chat-input');
        const messagesContainer = document.getElementById('chat-messages');
        const message = input?.value?.trim();
        
        if (!message || !messagesContainer) return;

        // Add user message to UI
        const userMsgDiv = document.createElement('div');
        userMsgDiv.className = 'chat-message user';
        userMsgDiv.innerHTML = `<div class="chat-bubble"><strong>You:</strong> ${ui.escapeHtml(message)}</div>`;
        messagesContainer.appendChild(userMsgDiv);
        
        input.value = '';
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Add to history
        this.chatHistory.push({ role: "user", content: message });

        try {
            const useKnowledge = document.getElementById('knowledge-toggle')?.checked ?? true;
            
            // FIXED: Explicit POST request with JSON body to /api/ai/mentor
            const response = await api.post('/api/ai/mentor', {
                message: message,
                history: this.chatHistory.slice(-10), // Send last 10 messages for context
                use_knowledge: useKnowledge
            });

            // Extract response
            const aiResponse = response.response || 'No response received from AI';

            // Add to history
            this.chatHistory.push({ role: "assistant", content: aiResponse });

            // Display AI response
            const aiMsgDiv = document.createElement('div');
            aiMsgDiv.className = 'chat-message';
            aiMsgDiv.innerHTML = `<div class="chat-bubble"><strong>AI Mentor:</strong> ${ui.escapeHtml(aiResponse)}</div>`;
            messagesContainer.appendChild(aiMsgDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

        } catch (error) {
            console.error('AI Mentor error:', error);
            const errorMsg = error.message || 'Failed to get response';
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'chat-message';
            errorDiv.innerHTML = `<div class="chat-bubble" style="color: var(--danger);"><strong>Error:</strong> ${ui.escapeHtml(errorMsg)}</div>`;
            messagesContainer.appendChild(errorDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    },

    handleChartUpload(input) {
        const file = input.files[0];
        if (!file) return;

        if (file.size > 10 * 1024 * 1024) {
            ui.showToast('File too large. Max 10MB.', 'error');
            return;
        }

        // Store File object for FormData upload
        this.currentChartFile = file;
        
        // Create preview using FileReader
        const reader = new FileReader();
        reader.onload = (e) => {
            this.currentChartImage = e.target.result; // base64 for preview
            const preview = document.getElementById('chart-preview');
            const container = document.getElementById('chart-preview-container');
            if (preview) preview.src = e.target.result;
            if (container) container.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    },

    async analyzeChart() {
        // FIXED: Check for File object, not just base64 image
        if (!this.currentChartFile) {
            ui.showToast('Please upload an image first', 'error');
            return;
        }

        ui.showLoading('Analyzing chart with AI...');

        try {
            const pair = document.getElementById('chart-pair')?.value || 'EURUSD';
            const timeframe = document.getElementById('chart-timeframe')?.value || '1H';
            const context = document.getElementById('chart-context')?.value || '';

            // FIXED: Use FormData for multipart/form-data upload
            const formData = new FormData();
            formData.append('image', this.currentChartFile);
            formData.append('pair', pair);
            formData.append('timeframe', timeframe);
            if (context) {
                formData.append('context', context);
            }

            // Use api.upload for FormData (sets correct Content-Type with boundary)
            const response = await api.upload('/api/ai/analyze-chart', formData);

            const analysisContent = document.getElementById('chart-analysis-content');
            const resultContainer = document.getElementById('chart-analysis-result');
            
            if (analysisContent) {
                analysisContent.textContent = response.analysis || 'Analysis completed but no content returned';
            }
            if (resultContainer) {
                resultContainer.classList.remove('hidden');
            }
            
        } catch (error) {
            console.error('Chart analysis error:', error);
            ui.showToast('Analysis failed: ' + (error.message || 'Unknown error'), 'error');
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

        // Store file for upload
        this.currentPerformanceFile = file;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            this.currentPerformanceImage = e.target.result;
            const preview = document.getElementById('performance-preview');
            const container = document.getElementById('performance-preview-container');
            if (preview) preview.src = e.target.result;
            if (container) container.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    },

    async analyzePerformanceVision() {
        if (!this.currentPerformanceImage) {
            ui.showToast('Please upload a trading statement image', 'error');
            return;
        }

        ui.showLoading('Analyzing trading performance...');

        try {
            const balance = parseFloat(document.getElementById('vision-account-balance')?.value) || 0;
            const period = parseInt(document.getElementById('vision-trading-period')?.value) || 30;

            // FIXED: Use FormData for performance analysis if it involves file upload
            // or JSON if it's just data. Assuming this endpoint also accepts FormData now.
            const formData = new FormData();
            formData.append('image', this.currentPerformanceFile);
            formData.append('account_balance', balance);
            formData.append('trading_period_days', period);

            const response = await api.upload('/api/performance/analyze-vision', formData);
            this.displayPerformanceResults(response);
            
        } catch (error) {
            console.error('Performance analysis error:', error);
            ui.showToast('Analysis failed: ' + (error.message || 'Server error'), 'error');
        } finally {
            ui.hideLoading();
        }
    },

    displayPerformanceResults(data) {
        const resultsContainer = document.getElementById('analysis-results');
        if (resultsContainer) resultsContainer.classList.remove('hidden');
        
        const score = data.trader_score || 0;
        const scoreEl = document.getElementById('trader-score');
        const scoreCircle = document.getElementById('score-circle');
        
        if (scoreEl) scoreEl.textContent = score;
        if (scoreCircle) scoreCircle.style.setProperty('--score', score);
        
        let interpretation = 'Needs Improvement';
        if (score >= 80) interpretation = 'Excellent Trader';
        else if (score >= 60) interpretation = 'Good Performance';
        else if (score >= 40) interpretation = 'Average Performance';
        
        const interpEl = document.getElementById('score-interpretation');
        if (interpEl) interpEl.textContent = interpretation;

        const summary = document.getElementById('performance-summary');
        if (summary) {
            summary.innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 12px;">
                    <div>Total Trades: <strong>${data.total_trades || 0}</strong></div>
                    <div>Win Rate: <strong>${data.win_rate || 0}%</strong></div>
                    <div>Profit Factor: <strong>${data.profit_factor || 'N/A'}</strong></div>
                    <div>Avg Return: <strong>${data.average_return || 0}%</strong></div>
                </div>
            `;
        }

        const renderList = (items, containerId) => {
            const container = document.getElementById(containerId);
            if (!container) return;
            if (!items || !Array.isArray(items) || items.length === 0) {
                container.innerHTML = '<li>No data available</li>';
                return;
            }
            container.innerHTML = items.map(item => `<li>${ui.escapeHtml(String(item))}</li>`).join('');
        };

        renderList(data.top_mistakes, 'top-mistakes');
        renderList(data.strengths, 'strengths-list');
        renderList(data.improvement_plan, 'improvement-plan');
        
        const adviceEl = document.getElementById('mentor-advice');
        if (adviceEl) adviceEl.textContent = data.mentor_advice || 'Keep practicing and learning from your trades.';
        
        const coursesContainer = document.getElementById('recommended-courses');
        if (coursesContainer) {
            if (data.recommended_courses && Array.isArray(data.recommended_courses) && data.recommended_courses.length > 0) {
                coursesContainer.innerHTML = data.recommended_courses.map(c => 
                    `<span class="badge badge-info">${ui.escapeHtml(String(c))}</span>`
                ).join('');
            } else {
                coursesContainer.innerHTML = '<span class="badge badge-secondary">No specific recommendations</span>';
            }
        }
    }
};
