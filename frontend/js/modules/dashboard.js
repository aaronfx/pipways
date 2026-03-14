/**
 * Pipways Trading Platform - Dashboard Controller
 * Updated with Chart Analysis, Performance, AI Mentor & Admin Fix
 */

class DashboardController {
    constructor() {
        this.user = null;
        this.currentSection = 'dashboard';
        this.charts = {};
        this.uploadedTrades = [];
        this.currentAnalysis = null;
        this.patternLibrary = [];

        this.init();
    }

    async init() {
        console.log('[Dashboard] Initializing...');

        // Check auth
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/login';
            return;
        }

        // Load user data
        await this.loadUserData();

        // Setup navigation
        this.setupNavigation();

        // Setup event listeners
        this.setupEventListeners();

        // Render admin menu (FIXED)
        this.renderAdminMenu();

        // Load initial section
        this.loadSection('dashboard');

        console.log('[Dashboard] Initialized successfully');
    }

    async loadUserData() {
        try {
            const response = await api.get('/users/me');
            this.user = response;
            this.updateUserDisplay();
        } catch (error) {
            console.error('[Dashboard] Failed to load user:', error);
            if (error.status === 401) {
                localStorage.removeItem('access_token');
                window.location.href = '/login';
            }
        }
    }

    updateUserDisplay() {
        const userNameEl = document.getElementById('user-name');
        const userEmailEl = document.getElementById('user-email');

        if (userNameEl && this.user) {
            userNameEl.textContent = this.user.full_name || this.user.username || 'Trader';
        }
        if (userEmailEl && this.user) {
            userEmailEl.textContent = this.user.email || '';
        }
    }

    // FIXED: Admin menu rendering with multiple fallback checks
    renderAdminMenu() {
        const user = this.user || {};

        // Check multiple possible admin field names
        const isAdmin = user.is_admin === true || 
                       user.role === 'admin' ||
                       user.is_superuser === true ||
                       user.role === 'superuser' ||
                       user.is_staff === true ||
                       user.admin === true ||
                       user.role === 'staff';

        console.log('[Admin Check]', user.email, 'Admin:', isAdmin, 'Role:', user.role);

        const adminMenu = document.getElementById('admin-menu-container');
        const adminBtn = document.getElementById('admin-dashboard-btn');

        if (adminMenu) {
            if (isAdmin) {
                adminMenu.classList.remove('hidden');
                adminMenu.style.display = 'block';
            } else {
                adminMenu.classList.add('hidden');
                adminMenu.style.display = 'none';
            }
        }

        if (adminBtn) {
            if (isAdmin) {
                adminBtn.classList.remove('hidden');
                adminBtn.style.display = 'inline-flex';
            } else {
                adminBtn.classList.add('hidden');
                adminBtn.style.display = 'none';
            }
        }
    }

    setupNavigation() {
        const navLinks = document.querySelectorAll('[data-section]');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.currentTarget.dataset.section;
                this.loadSection(section);

                // Update active state
                navLinks.forEach(l => l.classList.remove('active'));
                e.currentTarget.classList.add('active');
            });
        });
    }

    setupEventListeners() {
        // Logout
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }

        // Mobile menu toggle
        const mobileMenuBtn = document.getElementById('mobile-menu-btn');
        if (mobileMenuBtn) {
            mobileMenuBtn.addEventListener('click', () => {
                document.getElementById('sidebar')?.classList.toggle('open');
            });
        }
    }

    async loadSection(sectionName) {
        console.log('[Dashboard] Loading section:', sectionName);
        this.currentSection = sectionName;

        // Hide all sections
        document.querySelectorAll('.section-content').forEach(el => {
            el.classList.add('hidden');
            el.style.display = 'none';
        });

        // Show target section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.remove('hidden');
            targetSection.style.display = 'block';
        }

        // Load section-specific content
        switch(sectionName) {
            case 'dashboard':
                await this.loadDashboardData();
                break;
            case 'chart-analysis':
                await this.loadChartAnalysis();
                break;
            case 'performance':
                await this.loadPerformance();
                break;
            case 'mentor':
                await this.loadMentor();
                break;
            case 'journal':
                await this.loadJournal();
                break;
            case 'signals':
                await this.loadSignals();
                break;
            case 'admin':
                await this.loadAdminDashboard();
                break;
        }

        // Update URL hash
        window.location.hash = sectionName;
    }

    // ==================== CHART ANALYSIS SECTION ====================
    async loadChartAnalysis() {
        console.log('[Chart Analysis] Loading...');

        const container = document.getElementById('chart-analysis-content');
        if (!container) return;

        // Initialize pattern library
        await this.loadPatternLibrary();

        // Setup chart upload form
        this.setupChartUploadForm();

        // Setup drag and drop
        this.setupDragAndDrop();
    }

    setupChartUploadForm() {
        const form = document.getElementById('chart-upload-form');
        const fileInput = document.getElementById('chart-file-input');
        const analyzeBtn = document.getElementById('analyze-chart-btn');

        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                await this.analyzeChart();
            });
        }

        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleChartFileSelect(e.target.files[0]);
            });
        }
    }

    setupDragAndDrop() {
        const dropZone = document.getElementById('chart-drop-zone');
        if (!dropZone) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('drag-active');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('drag-active');
            }, false);
        });

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleChartFileSelect(files[0]);
            }
        });
    }

    handleChartFileSelect(file) {
        if (!file) return;

        console.log('[Chart] File selected:', file.name);

        // Validate file type
        const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            this.showNotification('Please upload a valid image file (JPEG, PNG, WEBP)', 'error');
            return;
        }

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.getElementById('chart-preview');
            if (preview) {
                preview.src = e.target.result;
                preview.classList.remove('hidden');
            }
            this.currentChartFile = file;
            this.currentChartBase64 = e.target.result;
        };
        reader.readAsDataURL(file);

        // Enable analyze button
        const analyzeBtn = document.getElementById('analyze-chart-btn');
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
        }
    }

    async analyzeChart() {
        if (!this.currentChartBase64) {
            this.showNotification('Please select a chart image first', 'error');
            return;
        }

        const analyzeBtn = document.getElementById('analyze-chart-btn');
        const loadingSpinner = document.getElementById('chart-analysis-loading');
        const resultsContainer = document.getElementById('chart-analysis-results');

        // Show loading
        if (analyzeBtn) analyzeBtn.disabled = true;
        if (loadingSpinner) loadingSpinner.classList.remove('hidden');

        try {
            const response = await api.analyzeChart({
                image: this.currentChartBase64,
                timeframe: document.getElementById('chart-timeframe')?.value || 'H1',
                symbol: document.getElementById('chart-symbol')?.value || 'AUTO'
            });

            this.currentAnalysis = response;
            this.displayChartAnalysis(response);

        } catch (error) {
            console.error('[Chart Analysis] Error:', error);
            this.showNotification('Failed to analyze chart. Please try again.', 'error');
        } finally {
            if (analyzeBtn) analyzeBtn.disabled = false;
            if (loadingSpinner) loadingSpinner.classList.add('hidden');
        }
    }

    displayChartAnalysis(analysis) {
        const container = document.getElementById('chart-analysis-results');
        if (!container) return;

        container.classList.remove('hidden');

        // Display symbol
        const symbolEl = document.getElementById('analysis-symbol');
        if (symbolEl) symbolEl.textContent = analysis.symbol || 'Unknown';

        // Display pattern
        const patternEl = document.getElementById('analysis-pattern');
        if (patternEl) patternEl.textContent = analysis.pattern || 'No pattern detected';

        // Display bias
        const biasEl = document.getElementById('analysis-bias');
        if (biasEl) {
            biasEl.textContent = analysis.bias || 'Neutral';
            biasEl.className = `bias-badge ${(analysis.bias || '').toLowerCase()}`;
        }

        // Display confidence
        const confidenceEl = document.getElementById('analysis-confidence');
        if (confidenceEl) {
            const confidence = analysis.confidence || 0;
            confidenceEl.textContent = `${confidence}%`;
            confidenceEl.style.width = `${confidence}%`;
        }

        // Display trade setup
        const setup = analysis.trade_setup || {};

        // Update trade validator inputs
        const entryInput = document.getElementById('validator-entry');
        const slInput = document.getElementById('validator-sl');
        const tpInput = document.getElementById('validator-tp');

        if (entryInput && setup.entry) entryInput.value = setup.entry;
        if (slInput && setup.stop_loss) slInput.value = setup.stop_loss;
        if (tpInput && setup.take_profit) tpInput.value = setup.take_profit;

        // Display key levels
        const levelsHtml = this.generateKeyLevelsHtml(analysis.key_levels);
        const levelsContainer = document.getElementById('key-levels-list');
        if (levelsContainer) levelsContainer.innerHTML = levelsHtml;

        // Setup validator button
        const validateBtn = document.getElementById('validate-trade-btn');
        if (validateBtn) {
            validateBtn.onclick = () => this.validateTradeSetup();
        }

        // Setup save signal button
        const saveSignalBtn = document.getElementById('save-signal-btn');
        if (saveSignalBtn) {
            saveSignalBtn.onclick = () => this.saveGeneratedSignal(analysis);
        }

        // Show attached chart in results
        const attachedChart = document.getElementById('attached-chart-preview');
        if (attachedChart && this.currentChartBase64) {
            attachedChart.src = this.currentChartBase64;
            attachedChart.classList.remove('hidden');
        }
    }

    generateKeyLevelsHtml(levels) {
        if (!levels || levels.length === 0) {
            return '<p class="text-gray-500">No key levels detected</p>';
        }

        return levels.map(level => `
            <div class="level-item ${level.type}">
                <span class="level-price">${level.price}</span>
                <span class="level-type">${level.type}</span>
                <span class="level-strength">${level.strength || ''}</span>
            </div>
        `).join('');
    }

    async loadPatternLibrary() {
        try {
            const patterns = await api.getPatternLibrary();
            this.patternLibrary = patterns || [];

            const container = document.getElementById('pattern-library-grid');
            if (container) {
                container.innerHTML = this.patternLibrary.map(pattern => `
                    <div class="pattern-card" data-pattern="${pattern.name}">
                        <img src="${pattern.image}" alt="${pattern.name}">
                        <h4>${pattern.name}</h4>
                        <p>${pattern.description}</p>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('[Pattern Library] Failed to load:', error);
        }
    }

    // ==================== TRADE VALIDATOR ====================
    async validateTradeSetup() {
        const entry = parseFloat(document.getElementById('validator-entry')?.value);
        const sl = parseFloat(document.getElementById('validator-sl')?.value);
        const tp = parseFloat(document.getElementById('validator-tp')?.value);
        const symbol = document.getElementById('validator-symbol')?.value || this.currentAnalysis?.symbol || 'EURUSD';

        if (!entry || !sl || !tp) {
            this.showNotification('Please fill in Entry, SL, and TP values', 'error');
            return;
        }

        try {
            const result = await api.validateTrade({
                entry_price: entry,
                stop_loss: sl,
                take_profit: tp,
                symbol: symbol,
                setup_type: this.currentAnalysis?.pattern || 'manual',
                chart_analysis: this.currentAnalysis
            });

            this.displayValidationResult(result);

        } catch (error) {
            console.error('[Trade Validator] Error:', error);
            this.showNotification('Validation failed. Please check your inputs.', 'error');
        }
    }

    displayValidationResult(result) {
        const container = document.getElementById('validation-result');
        if (!container) return;

        container.classList.remove('hidden');

        const scoreEl = document.getElementById('validation-score');
        if (scoreEl) {
            scoreEl.textContent = result.quality_score || 0;
            scoreEl.className = `score-circle ${result.recommendation || 'neutral'}`;
        }

        const rrEl = document.getElementById('validation-rr');
        if (rrEl) rrEl.textContent = result.risk_reward_ratio || 'N/A';

        const probEl = document.getElementById('validation-probability');
        if (probEl) probEl.textContent = `${result.probability || 0}%`;

        const warningsEl = document.getElementById('validation-warnings');
        if (warningsEl) {
            if (result.warnings && result.warnings.length > 0) {
                warningsEl.innerHTML = result.warnings.map(w => `<li>${w}</li>`).join('');
            } else {
                warningsEl.innerHTML = '<li class="text-green-600">No warnings - Good setup!</li>';
            }
        }

        const suggestionsEl = document.getElementById('validation-suggestions');
        if (suggestionsEl) {
            if (result.suggestions && result.suggestions.length > 0) {
                suggestionsEl.innerHTML = result.suggestions.map(s => `<li>${s}</li>`).join('');
            } else {
                suggestionsEl.innerHTML = '<li>Setup looks optimal</li>';
            }
        }
    }

    async saveGeneratedSignal(analysis) {
        if (!analysis) return;

        try {
            await api.saveSignal({
                symbol: analysis.symbol,
                pattern: analysis.pattern,
                bias: analysis.bias,
                entry_price: analysis.trade_setup?.entry,
                stop_loss: analysis.trade_setup?.stop_loss,
                take_profit: analysis.trade_setup?.take_profit,
                confidence: analysis.confidence,
                chart_image: this.currentChartBase64,
                analysis_data: analysis
            });

            this.showNotification('Signal saved successfully!', 'success');

        } catch (error) {
            console.error('[Save Signal] Error:', error);
            this.showNotification('Failed to save signal', 'error');
        }
    }

    // ==================== PERFORMANCE SECTION ====================
    async loadPerformance() {
        console.log('[Performance] Loading...');

        await this.loadPerformanceStats();
        await this.loadEquityCurve();
        await this.loadTradeDistribution();
        await this.setupJournalUpload();
    }

    async loadPerformanceStats() {
        try {
            const stats = await api.getPerformanceStats(30);

            // Update stats cards
            const winRateEl = document.getElementById('stat-win-rate');
            const profitFactorEl = document.getElementById('stat-profit-factor');
            const expectancyEl = document.getElementById('stat-expectancy');
            const drawdownEl = document.getElementById('stat-drawdown');

            if (winRateEl) winRateEl.textContent = `${stats.win_rate || 0}%`;
            if (profitFactorEl) profitFactorEl.textContent = stats.profit_factor || '0.0';
            if (expectancyEl) expectancyEl.textContent = `$${stats.expectancy || 0}`;
            if (drawdownEl) drawdownEl.textContent = `${stats.max_drawdown || 0}%`;

            // Load psychology insights
            if (stats.psychology_profile) {
                this.displayPsychologyProfile(stats.psychology_profile);
            }

        } catch (error) {
            console.error('[Performance Stats] Error:', error);
        }
    }

    displayPsychologyProfile(profile) {
        const container = document.getElementById('psychology-profile');
        if (!container) return;

        container.innerHTML = `
            <div class="psychology-card">
                <h4>Trading Psychology Profile</h4>
                <div class="trait-list">
                    ${Object.entries(profile.traits || {}).map(([trait, score]) => `
                        <div class="trait-item">
                            <span class="trait-name">${trait}</span>
                            <div class="trait-bar">
                                <div class="trait-fill" style="width: ${score}%"></div>
                            </div>
                            <span class="trait-score">${score}%</span>
                        </div>
                    `).join('')}
                </div>
                <div class="psychology-insights">
                    <h5>Key Insights</h5>
                    <ul>
                        ${(profile.insights || []).map(insight => `<li>${insight}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }

    async loadEquityCurve() {
        try {
            const data = await api.request('/ai/performance/equity-curve?days=30');

            const ctx = document.getElementById('equity-curve-chart');
            if (!ctx) return;

            if (this.charts.equity) {
                this.charts.equity.destroy();
            }

            this.charts.equity = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates || [],
                    datasets: [{
                        label: 'Equity',
                        data: data.equity || [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('[Equity Curve] Error:', error);
        }
    }

    async loadTradeDistribution() {
        try {
            const data = await api.request('/ai/performance/trade-distribution');

            const ctx = document.getElementById('trade-distribution-chart');
            if (!ctx) return;

            if (this.charts.distribution) {
                this.charts.distribution.destroy();
            }

            this.charts.distribution = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Winners', 'Losers', 'Break Even'],
                    datasets: [{
                        data: [data.wins || 0, data.losses || 0, data.break_even || 0],
                        backgroundColor: [
                            'rgba(75, 192, 192, 0.8)',
                            'rgba(255, 99, 132, 0.8)',
                            'rgba(255, 206, 86, 0.8)'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        } catch (error) {
            console.error('[Trade Distribution] Error:', error);
        }
    }

    // ==================== JOURNAL UPLOAD (MULTI-FORMAT) ====================
    async setupJournalUpload() {
        const uploadForm = document.getElementById('journal-upload-form');
        const fileInput = document.getElementById('journal-file-input');

        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.uploadJournalFile(e.target.files[0]);
                }
            });
        }

        // Setup format buttons
        document.querySelectorAll('[data-format]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const format = e.currentTarget.dataset.format;
                this.setJournalFormat(format);
            });
        });
    }

    setJournalFormat(format) {
        this.currentJournalFormat = format;

        // Update UI
        document.querySelectorAll('[data-format]').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.format === format) {
                btn.classList.add('active');
            }
        });

        // Update file input accept attribute
        const fileInput = document.getElementById('journal-file-input');
        if (fileInput) {
            const acceptMap = {
                'mt4': '.html,.htm',
                'mt5': '.html,.htm',
                'csv': '.csv',
                'excel': '.xlsx,.xls',
                'pdf': '.pdf',
                'image': '.png,.jpg,.jpeg,.webp'
            };
            fileInput.accept = acceptMap[format] || '*';
        }

        console.log('[Journal] Format selected:', format);
    }

    async uploadJournalFile(file) {
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('format', this.currentJournalFormat || 'auto');

        const uploadBtn = document.getElementById('journal-upload-btn');
        const loadingSpinner = document.getElementById('journal-upload-loading');

        if (uploadBtn) uploadBtn.disabled = true;
        if (loadingSpinner) loadingSpinner.classList.remove('hidden');

        try {
            const result = await api.uploadJournal(formData);

            this.uploadedTrades = result.trades || [];
            this.displayUploadedTrades(this.uploadedTrades);

            // Show auto-analysis if available
            if (result.analysis) {
                this.displayJournalAnalysis(result.analysis);
            }

            this.showNotification(`Successfully imported ${this.uploadedTrades.length} trades`, 'success');

        } catch (error) {
            console.error('[Journal Upload] Error:', error);
            this.showNotification('Failed to upload journal file', 'error');
        } finally {
            if (uploadBtn) uploadBtn.disabled = false;
            if (loadingSpinner) loadingSpinner.classList.add('hidden');
        }
    }

    displayUploadedTrades(trades) {
        const container = document.getElementById('journal-trades-list');
        if (!container) return;

        if (trades.length === 0) {
            container.innerHTML = '<p class="text-gray-500">No trades found in file</p>';
            return;
        }

        container.innerHTML = trades.map(trade => `
            <div class="trade-item ${trade.profit >= 0 ? 'win' : 'loss'}">
                <div class="trade-header">
                    <span class="trade-symbol">${trade.symbol}</span>
                    <span class="trade-type ${trade.type}">${trade.type}</span>
                    <span class="trade-profit ${trade.profit >= 0 ? 'positive' : 'negative'}">
                        ${trade.profit >= 0 ? '+' : ''}$${trade.profit}
                    </span>
                </div>
                <div class="trade-details">
                    <span>Entry: ${trade.entry_price}</span>
                    <span>Exit: ${trade.exit_price}</span>
                    <span>${trade.open_time}</span>
                </div>
            </div>
        `).join('');
    }

    displayJournalAnalysis(analysis) {
        const container = document.getElementById('journal-ai-analysis');
        if (!container) return;

        container.classList.remove('hidden');
        container.innerHTML = `
            <h4>AI Analysis</h4>
            <div class="analysis-grid">
                <div class="analysis-item">
                    <span class="label">Total Trades</span>
                    <span class="value">${analysis.total_trades}</span>
                </div>
                <div class="analysis-item">
                    <span class="label">Win Rate</span>
                    <span class="value">${analysis.win_rate}%</span>
                </div>
                <div class="analysis-item">
                    <span class="label">Avg Profit</span>
                    <span class="value">$${analysis.avg_profit}</span>
                </div>
                <div class="analysis-item">
                    <span class="label">Avg Loss</span>
                    <span class="value">$${analysis.avg_loss}</span>
                </div>
            </div>
            <div class="psychology-summary">
                <h5>Psychology Insights</h5>
                <p>${analysis.psychology_summary || 'No specific insights available'}</p>
            </div>
        `;
    }

    // ==================== AI MENTOR SECTION ====================
    async loadMentor() {
        console.log('[AI Mentor] Loading...');

        const chatContainer = document.getElementById('mentor-chat-container');
        const input = document.getElementById('mentor-input');
        const sendBtn = document.getElementById('mentor-send-btn');

        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMentorMessage());
        }

        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMentorMessage();
                }
            });
        }

        // Load skill level selector
        const skillSelect = document.getElementById('mentor-skill-level');
        if (skillSelect) {
            skillSelect.addEventListener('change', (e) => {
                this.mentorSkillLevel = e.target.value;
            });
        }

        // Add welcome message
        if (chatContainer && chatContainer.children.length === 0) {
            this.addMentorMessage('ai', 'Hello! I'm your AI Trading Mentor. Ask me anything about trading strategies, risk management, or market analysis!');
        }
    }

    async sendMentorMessage() {
        const input = document.getElementById('mentor-input');
        const message = input?.value?.trim();

        if (!message) return;

        // Add user message
        this.addMentorMessage('user', message);
        input.value = '';

        // Show typing indicator
        this.showMentorTyping(true);

        try {
            const response = await api.askMentor(message, this.mentorSkillLevel || 'intermediate');

            this.showMentorTyping(false);
            this.addMentorMessage('ai', response.answer || response.response || 'I'm not sure about that. Could you rephrase your question?');

            // Display related resources if available
            if (response.resources && response.resources.length > 0) {
                this.addMentorResources(response.resources);
            }

        } catch (error) {
            console.error('[AI Mentor] Error:', error);
            this.showMentorTyping(false);
            this.addMentorMessage('ai', 'Sorry, I'm having trouble connecting right now. Please try again later.');
        }
    }

    addMentorMessage(sender, text) {
        const container = document.getElementById('mentor-chat-container');
        if (!container) return;

        const messageEl = document.createElement('div');
        messageEl.className = `chat-message ${sender}`;
        messageEl.innerHTML = `
            <div class="message-bubble">
                <p>${this.escapeHtml(text)}</p>
            </div>
            <span class="message-time">${new Date().toLocaleTimeString()}</span>
        `;

        container.appendChild(messageEl);
        container.scrollTop = container.scrollHeight;
    }

    addMentorResources(resources) {
        const container = document.getElementById('mentor-chat-container');
        if (!container) return;

        const resourcesEl = document.createElement('div');
        resourcesEl.className = 'chat-message ai resources';
        resourcesEl.innerHTML = `
            <div class="message-bubble">
                <p><strong>Related Resources:</strong></p>
                <ul>
                    ${resources.map(r => `<li><a href="${r.url}" target="_blank">${r.title}</a></li>`).join('')}
                </ul>
            </div>
        `;

        container.appendChild(resourcesEl);
        container.scrollTop = container.scrollHeight;
    }

    showMentorTyping(show) {
        const container = document.getElementById('mentor-chat-container');
        if (!container) return;

        let typingEl = document.getElementById('mentor-typing');

        if (show) {
            if (!typingEl) {
                typingEl = document.createElement('div');
                typingEl.id = 'mentor-typing';
                typingEl.className = 'chat-message ai typing';
                typingEl.innerHTML = `
                    <div class="message-bubble">
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                    </div>
                `;
                container.appendChild(typingEl);
                container.scrollTop = container.scrollHeight;
            }
        } else if (typingEl) {
            typingEl.remove();
        }
    }

    // ==================== OTHER SECTIONS ====================
    async loadDashboardData() {
        console.log('[Dashboard] Loading overview...');
        // Load summary stats
        try {
            const stats = await api.getPerformanceStats(7);

            const weeklyPnL = document.getElementById('dashboard-weekly-pnl');
            const activeTrades = document.getElementById('dashboard-active-trades');

            if (weeklyPnL) weeklyPnL.textContent = `$${stats.total_profit || 0}`;
            if (activeTrades) activeTrades.textContent = stats.active_trades || 0;

        } catch (error) {
            console.error('[Dashboard] Error loading stats:', error);
        }
    }

    async loadJournal() {
        console.log('[Journal] Loading...');
        // Journal is loaded via the upload functionality
    }

    async loadSignals() {
        console.log('[Signals] Loading...');
        // Load saved signals
        try {
            const signals = await api.request('/signals');
            const container = document.getElementById('signals-list');
            if (container && signals) {
                container.innerHTML = signals.map(signal => `
                    <div class="signal-card">
                        <div class="signal-header">
                            <span class="signal-symbol">${signal.symbol}</span>
                            <span class="signal-bias ${signal.bias}">${signal.bias}</span>
                        </div>
                        <div class="signal-details">
                            <p>Entry: ${signal.entry_price}</p>
                            <p>SL: ${signal.stop_loss} | TP: ${signal.take_profit}</p>
                            <p>Confidence: ${signal.confidence}%</p>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('[Signals] Error:', error);
        }
    }

    async loadAdminDashboard() {
        console.log('[Admin] Loading...');
        if (!this.user?.is_admin && !this.user?.role === 'admin') {
            this.showNotification('Access denied', 'error');
            this.loadSection('dashboard');
            return;
        }

        try {
            const users = await api.request('/admin/users');
            const container = document.getElementById('admin-users-list');
            if (container) {
                container.innerHTML = users.map(user => `
                    <tr>
                        <td>${user.email}</td>
                        <td>${user.full_name || user.username}</td>
                        <td>${user.role || 'user'}</td>
                        <td>
                            <button onclick="dashboard.toggleUserRole('${user.id}')">
                                ${user.is_admin ? 'Remove Admin' : 'Make Admin'}
                            </button>
                        </td>
                    </tr>
                `).join('');
            }
        } catch (error) {
            console.error('[Admin] Error:', error);
        }
    }

    // ==================== UTILITIES ====================
    handleLogout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// API Helper Methods (Added to existing api object)
if (typeof api !== 'undefined') {
    api.analyzeChart = function(data) {
        return this.request('/ai/chart/analyze', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    };

    api.getPatternLibrary = function() {
        return this.request('/ai/chart/pattern-library');
    };

    api.validateTrade = function(data) {
        return this.request('/ai/trade/validate', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    };

    api.saveSignal = function(data) {
        return this.request('/ai/signal/save', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    };

    api.getPerformanceStats = function(days = 30) {
        return this.request(`/ai/performance/dashboard?days=${days}`);
    };

    api.uploadJournal = function(formData) {
        return this.request('/ai/performance/upload-journal', {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set content-type for FormData
        });
    };

    api.askMentor = function(question, skillLevel = 'intermediate') {
        return this.request('/ai/mentor/ask', {
            method: 'POST',
            body: JSON.stringify({ 
                question, 
                skill_level: skillLevel 
            })
        });
    };
}

// Initialize dashboard
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new DashboardController();
});
