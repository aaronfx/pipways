/**
 * Pipways Dashboard Controller - PRODUCTION READY
 * All modules implemented: AI Mentor, Chart Analysis, Performance, Admin
 */
class DashboardController {
    constructor() {
        this.user = null;
        this.allCourses = [];
        this.init();
    }

    init() {
        this.checkAuth();
        this.setupNavigation();
        this.setupMobileMenu();
        this.renderAdminMenu();
        this.initFeatureCarousel();
        this.navigate('dashboard');
    }

    checkAuth() {
        const token = localStorage.getItem('pipways_token');
        const userStr = localStorage.getItem('pipways_user');
        
        if (!token || !userStr) {
            window.location.href = '/';
            return;
        }
        
        try {
            this.user = JSON.parse(userStr);
            this.updateUserDisplay();
        } catch (e) {
            console.error('Auth error:', e);
            window.location.href = '/';
        }
    }

    updateUserDisplay() {
        const userNameEl = document.getElementById('user-name');
        const userEmailEl = document.getElementById('user-email');
        const headerUserNameEl = document.getElementById('header-user-name');
        
        if (userNameEl) userNameEl.textContent = this.user?.full_name || this.user?.email || 'User';
        if (userEmailEl) userEmailEl.textContent = this.user?.email || '';
        if (headerUserNameEl) headerUserNameEl.textContent = this.user?.full_name || this.user?.email || 'Trader';
    }

    setupNavigation() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.currentTarget.dataset.section;
                if (section) this.navigate(section);
            });
        });
    }

    setupMobileMenu() {
        const btn = document.getElementById('mobile-menu-btn');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        
        if (btn && sidebar) {
            btn.addEventListener('click', () => {
                sidebar.classList.toggle('-translate-x-full');
                overlay?.classList.toggle('hidden');
            });
        }
        
        if (overlay && sidebar) {
            overlay.addEventListener('click', () => {
                sidebar.classList.add('-translate-x-full');
                overlay.classList.add('hidden');
            });
        }
    }

    renderAdminMenu() {
        const isAdmin = this.user && (
            this.user.is_admin === true || 
            this.user.role === 'admin' ||
            this.user.is_superuser === true
        );
        
        const adminMenuContainer = document.getElementById('admin-menu');
        
        if (adminMenuContainer) {
            if (isAdmin) {
                adminMenuContainer.classList.remove('hidden');
                adminMenuContainer.style.display = 'block';
                console.log('[Dashboard] Admin access enabled for', this.user.email);
            } else {
                adminMenuContainer.classList.add('hidden');
                adminMenuContainer.style.display = 'none';
            }
        }
    }

    navigate(section) {
        document.querySelectorAll('.nav-link').forEach(el => {
            el.classList.remove('bg-purple-600', 'text-white');
            el.classList.add('text-gray-300');
        });
        
        const activeLink = document.querySelector(`[data-section="${section}"]`);
        if (activeLink) {
            activeLink.classList.add('bg-purple-600', 'text-white');
            activeLink.classList.remove('text-gray-300');
        }

        document.querySelectorAll('.section').forEach(el => el.classList.add('hidden'));
        
        const target = document.getElementById(`section-${section}`);
        if (target) {
            target.classList.remove('hidden');
            this.loadSectionData(section);
        }

        const titles = {
            'dashboard': 'Dashboard',
            'signals': 'Trading Signals',
            'journal': 'Trading Journal',
            'courses': 'Trading Courses',
            'webinars': 'Webinars',
            'blog': 'Trading Blog',
            'admin': 'Admin Dashboard',
            'analysis': 'Chart Analysis',
            'performance': 'Performance Analytics',
            'mentor': 'AI Mentor'
        };
        
        const pageTitle = document.getElementById('page-title');
        if (pageTitle) pageTitle.textContent = titles[section] || 'Dashboard';

        document.getElementById('sidebar')?.classList.add('-translate-x-full');
        document.getElementById('sidebar-overlay')?.classList.add('hidden');
    }

    async loadSectionData(section) {
        try {
            switch(section) {
                case 'dashboard': break;
                case 'signals': await this.loadSignals(); break;
                case 'courses': await this.loadCourses(); break;
                case 'webinars': await this.loadWebinars(); break;
                case 'blog': await this.loadBlog(); break;
                case 'journal': this.setupJournalUpload(); break;
                case 'admin': await this.loadAdminData(); break;
                case 'mentor': await this.loadMentor(); break;
                case 'analysis': await this.loadChartAnalysis(); break;
                case 'performance': await this.loadPerformance(); break;
            }
        } catch (err) {
            console.error(`[Dashboard] Error loading ${section}:`, err);
        }
    }

    async loadSignals() {
        const container = document.getElementById('signals-container');
        if (!container) return;
        
        this.showSkeleton(container, 3);
        
        try {
            const data = await api.getSignals();
            const signals = Array.isArray(data) ? data : (data.signals || []);
            this.renderSignals(signals);
        } catch (error) {
            console.error('[Signals Error]', error);
            container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">No active signals available</div>';
        }
    }

    renderSignals(signals) {
        const container = document.getElementById('signals-container');
        if (!container) return;
        
        if (!signals || signals.length === 0) {
            container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">No active signals available</div>';
            return;
        }
        
        container.innerHTML = signals.map(signal => `
            <div class="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-colors">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="font-bold text-white text-lg">${signal.symbol}</h4>
                    <span class="px-2 py-1 rounded text-xs font-bold ${signal.direction === 'BUY' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}">${signal.direction}</span>
                </div>
                <div class="text-sm text-gray-400 space-y-1">
                    <div class="flex justify-between"><span>Entry:</span> <span class="text-white">${signal.entry_price}</span></div>
                    <div class="flex justify-between"><span>SL:</span> <span class="text-red-400">${signal.stop_loss}</span></div>
                    <div class="flex justify-between"><span>TP:</span> <span class="text-green-400">${signal.take_profit}</span></div>
                    <div class="flex justify-between"><span>Timeframe:</span> <span>${signal.timeframe || 'N/A'}</span></div>
                </div>
                <div class="mt-3 pt-3 border-t border-gray-700 text-xs text-gray-500 flex justify-between">
                    <span>${new Date(signal.created_at).toLocaleDateString()}</span>
                    ${signal.ai_confidence ? `<span class="text-purple-400">AI: ${Math.round(signal.ai_confidence * 100)}%</span>` : ''}
                </div>
            </div>
        `).join('');
    }

    async loadCourses() {
        const container = document.getElementById('courses-container');
        if (!container) return;
        
        this.showSkeleton(container, 4);
        
        try {
            const data = await api.getCourses();
            this.allCourses = Array.isArray(data) ? data : (data.courses || []);
            this.renderCourses(this.allCourses);
            this.setupCourseFilters();
        } catch (error) {
            console.error('[Courses Error]', error);
            container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">No courses available</div>';
        }
    }

    setupCourseFilters() {
        const filterContainer = document.getElementById('course-filters');
        if (!filterContainer) return;
        
        const levels = ['All', 'Beginner', 'Intermediate', 'Advanced'];
        filterContainer.innerHTML = levels.map(level => `
            <button onclick="dashboard.filterCourses('${level}')" 
                    class="filter-btn px-4 py-2 rounded-full text-sm transition-colors ${level === 'All' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}"
                    data-level="${level}">
                ${level}
            </button>
        `).join('');
    }

    filterCourses(level) {
        document.querySelectorAll('.filter-btn').forEach(btn => {
            const isActive = btn.dataset.level === level;
            btn.className = `filter-btn px-4 py-2 rounded-full text-sm transition-colors ${isActive ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`;
        });
        
        if (level === 'All') {
            this.renderCourses(this.allCourses);
        } else {
            const filtered = this.allCourses.filter(c => c.level?.toLowerCase() === level.toLowerCase());
            this.renderCourses(filtered);
        }
    }

    renderCourses(courses) {
        const container = document.getElementById('courses-container');
        if (!container) return;
        
        if (!courses || courses.length === 0) {
            container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">No courses available for this level</div>';
            return;
        }
        
        container.innerHTML = courses.map(course => `
            <div class="bg-gray-800 rounded-lg overflow-hidden border border-gray-700 hover:border-gray-600 transition-all hover:transform hover:-translate-y-1">
                <div class="h-40 bg-gradient-to-br from-purple-900 to-blue-900 flex items-center justify-center">
                    <i class="fas fa-graduation-cap text-5xl text-white/20"></i>
                </div>
                <div class="p-4">
                    <div class="flex justify-between items-start mb-2">
                        <span class="text-xs text-purple-400 font-semibold">${course.level || 'Beginner'}</span>
                        ${course.progress > 0 ? `<span class="text-xs text-green-400">${course.progress}% complete</span>` : ''}
                    </div>
                    <h4 class="font-bold text-white mb-2">${course.title}</h4>
                    <p class="text-sm text-gray-400 mb-3 line-clamp-2">${course.description || ''}</p>
                    <div class="flex justify-between items-center text-xs text-gray-500">
                        <span>${course.lesson_count || 0} lessons</span>
                        <button class="text-purple-400 hover:text-purple-300 font-medium">Start Learning →</button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async loadWebinars() {
        const container = document.getElementById('webinars-container');
        if (!container) return;
        
        this.showSkeleton(container, 2);
        
        try {
            const data = await api.getWebinars();
            const webinars = Array.isArray(data) ? data : (data.webinars || []);
            
            if (!webinars || webinars.length === 0) {
                container.innerHTML = '<div class="text-center py-8 text-gray-500">No upcoming webinars scheduled</div>';
                return;
            }
            
            container.innerHTML = webinars.map(webinar => {
                const date = new Date(webinar.scheduled_at);
                return `
                    <div class="bg-gray-800 rounded-lg p-4 border border-gray-700 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                        <div class="flex gap-4">
                            <div class="text-center min-w-[60px] bg-gray-700 rounded-lg p-2">
                                <div class="text-xl font-bold text-purple-400">${date.getDate()}</div>
                                <div class="text-xs text-gray-400 uppercase">${date.toLocaleString('default', {month: 'short'})}</div>
                            </div>
                            <div>
                                <h4 class="font-bold text-white">${webinar.title}</h4>
                                <p class="text-sm text-gray-400">${webinar.description || ''}</p>
                                <div class="text-xs text-gray-500 mt-1">
                                    <span class="mr-3"><i class="fas fa-user mr-1"></i> ${webinar.presenter || 'TBA'}</span>
                                    <span><i class="fas fa-clock mr-1"></i> ${webinar.duration_minutes || 60} mins</span>
                                </div>
                            </div>
                        </div>
                        <button class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm transition-colors whitespace-nowrap">
                            Register Now
                        </button>
                    </div>
                `;
            }).join('');
        } catch (error) {
            console.error('[Webinars Error]', error);
            container.innerHTML = '<div class="text-center py-8 text-gray-500">Failed to load webinars</div>';
        }
    }

    async loadBlog() {
        const container = document.getElementById('blog-container');
        if (!container) return;
        
        this.showSkeleton(container, 3);
        
        try {
            const data = await api.getBlogPosts();
            const posts = Array.isArray(data) ? data : (data.posts || []);
            
            if (!posts || posts.length === 0) {
                container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">No articles available</div>';
                return;
            }
            
            container.innerHTML = posts.map(post => `
                <article class="bg-gray-800 rounded-lg overflow-hidden border border-gray-700 hover:border-gray-600 transition-all cursor-pointer group">
                    <div class="h-48 bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center">
                        <i class="fas fa-newspaper text-5xl text-white/20 group-hover:scale-110 transition-transform"></i>
                    </div>
                    <div class="p-4">
                        <div class="text-xs text-purple-400 mb-2 uppercase tracking-wide">${post.category || 'General'}</div>
                        <h4 class="font-bold text-white mb-2 group-hover:text-purple-400 transition-colors">${post.title}</h4>
                        <p class="text-sm text-gray-400 line-clamp-3 mb-3">${post.excerpt || post.content?.substring(0, 120) + '...' || ''}</p>
                        <div class="text-xs text-gray-500 flex justify-between">
                            <span>${new Date(post.created_at).toLocaleDateString()}</span>
                            <span class="text-purple-400">Read more →</span>
                        </div>
                    </div>
                </article>
            `).join('');
        } catch (error) {
            console.error('[Blog Error]', error);
            container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">Failed to load articles</div>';
        }
    }

    setupJournalUpload() {
        const dropZone = document.getElementById('journal-dropzone');
        const fileInput = document.getElementById('journal-file-input');
        if (!dropZone || !fileInput) return;
        
        dropZone.addEventListener('click', () => fileInput.click());
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('border-purple-500', 'bg-purple-900/20');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('border-purple-500', 'bg-purple-900/20');
        });
        
        dropZone.addEventListener('drop', async (e) => {
            e.preventDefault();
            dropZone.classList.remove('border-purple-500', 'bg-purple-900/20');
            const file = e.dataTransfer.files[0];
            if (file) await this.handleJournalUpload(file);
        });
        
        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (file) await this.handleJournalUpload(file);
        });
    }

    async handleJournalUpload(file) {
        const statusEl = document.getElementById('upload-status');
        if (statusEl) {
            statusEl.classList.remove('hidden');
            statusEl.innerHTML = '<span class="text-blue-400"><i class="fas fa-spinner fa-spin mr-2"></i>Analyzing file...</span>';
        }
        
        try {
            const text = await file.text();
            const trades = JSON.parse(text);
            const result = await api.analyzeJournal(trades);
            
            if (statusEl) {
                statusEl.innerHTML = `<span class="text-green-400"><i class="fas fa-check mr-2"></i>Analysis complete! Found ${result.statistics?.total_trades || 0} trades</span>`;
            }
            this.renderJournalAnalysis(result);
        } catch (error) {
            console.error('[Upload Error]', error);
            if (statusEl) {
                statusEl.innerHTML = `<span class="text-red-400"><i class="fas fa-exclamation-circle mr-2"></i>${error.message}</span>`;
            }
        }
    }

    renderJournalAnalysis(result) {
        const container = document.getElementById('journal-analysis');
        if (!container) return;
        
        const stats = result.statistics || {};
        
        container.innerHTML = `
            <div class="bg-gray-800 rounded-lg p-6 border border-gray-700 mt-4">
                <div class="flex justify-between items-center mb-4">
                    <h4 class="text-lg font-bold text-white">Analysis Results</h4>
                    <span class="px-3 py-1 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold text-sm">
                        Grade: ${result.overall_grade || 'N/A'}
                    </span>
                </div>
                <div class="grid grid-cols-3 gap-4 mb-4">
                    <div class="text-center p-3 bg-gray-900 rounded-lg">
                        <div class="text-xl font-bold text-white">${stats.total_trades || 0}</div>
                        <div class="text-xs text-gray-500">Trades</div>
                    </div>
                    <div class="text-center p-3 bg-gray-900 rounded-lg">
                        <div class="text-xl font-bold ${stats.profit_factor > 1 ? 'text-green-400' : 'text-red-400'}">${stats.profit_factor?.toFixed(2) || '0.00'}</div>
                        <div class="text-xs text-gray-500">Profit Factor</div>
                    </div>
                    <div class="text-center p-3 bg-gray-900 rounded-lg">
                        <div class="text-xl font-bold text-white">${stats.win_rate || 0}%</div>
                        <div class="text-xs text-gray-500">Win Rate</div>
                    </div>
                </div>
                ${result.improvements?.length ? `
                    <div class="space-y-2">
                        <h5 class="font-semibold text-gray-300 text-sm">Recommendations:</h5>
                        ${result.improvements.map(i => `<div class="p-2 bg-blue-900/30 rounded text-sm text-blue-300 border-l-2 border-blue-500">${i}</div>`).join('')}
                    </div>
                ` : ''}
            </div>
        `;
        container.classList.remove('hidden');
    }

    async loadAdminData() {
        const container = document.getElementById('admin-container');
        if (!container) return;
        
        try {
            const stats = await api.getAdminStats();
            container.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <div class="text-3xl font-bold text-white mb-1">${stats.total_users || 0}</div>
                        <div class="text-sm text-gray-400">Total Users</div>
                    </div>
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <div class="text-3xl font-bold text-white mb-1">${stats.active_signals || 0}</div>
                        <div class="text-sm text-gray-400">Active Signals</div>
                    </div>
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <div class="text-3xl font-bold text-white mb-1">${stats.new_today || 0}</div>
                        <div class="text-sm text-gray-400">New Today</div>
                    </div>
                </div>
                <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
                    <h4 class="font-bold text-white mb-4">Quick Actions</h4>
                    <div class="flex flex-wrap gap-3">
                        <button class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">Create Signal</button>
                        <button class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">Add Course</button>
                        <button class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">Schedule Webinar</button>
                        <button class="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">New Blog Post</button>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('[Admin Error]', error);
            container.innerHTML = '<div class="text-red-400 p-4 bg-red-900/20 rounded-lg border border-red-800">Error loading admin data. Ensure you have admin privileges.</div>';
        }
    }

    async loadMentor() {
        const container = document.getElementById('section-mentor');
        if (!container) return;
        
        container.innerHTML = `
            <div class="max-w-6xl mx-auto h-[calc(100vh-200px)]">
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
                    <div class="lg:col-span-2 bg-gray-800 rounded-xl flex flex-col h-full border border-gray-700">
                        <div class="p-4 border-b border-gray-700 flex justify-between items-center flex-shrink-0">
                            <div class="flex items-center gap-3">
                                <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white">
                                    <i class="fas fa-robot"></i>
                                </div>
                                <div>
                                    <h3 class="font-bold text-white">AI Trading Mentor</h3>
                                    <p class="text-xs text-green-400 flex items-center gap-1">
                                        <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                                        Online
                                    </p>
                                </div>
                            </div>
                            <button onclick="dashboard.clearMentorChat()" class="text-gray-400 hover:text-white p-2 transition-colors">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                        </div>
                        
                        <div id="mentor-messages" class="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-900 min-h-0">
                            <div class="flex gap-3">
                                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm flex-shrink-0">
                                    <i class="fas fa-robot"></i>
                                </div>
                                <div class="bg-gray-700 p-3 rounded-2xl rounded-tl-none max-w-[85%] sm:max-w-[80%]">
                                    <p class="text-gray-200">Welcome! I'm your AI Trading Mentor. Ask me anything about trading strategies, risk management, or market analysis.</p>
                                </div>
                            </div>
                        </div>
                        
                        <div class="p-4 border-t border-gray-700 bg-gray-800 rounded-b-xl flex-shrink-0">
                            <div class="flex gap-2">
                                <input type="text" id="mentor-input" placeholder="Ask your trading question..." 
                                    class="flex-1 px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                                    onkeypress="if(event.key==='Enter') dashboard.sendMentorMessage()">
                                <button onclick="dashboard.sendMentorMessage()" class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg transition-colors flex items-center justify-center">
                                    <i class="fas fa-paper-plane"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="space-y-4 hidden lg:block">
                        <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">
                            <h4 class="font-bold text-white mb-3">Quick Topics</h4>
                            <div class="space-y-2">
                                <button onclick="dashboard.askMentor('How do I manage risk effectively?')" class="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-700 text-sm text-gray-300 transition-colors">
                                    Risk Management
                                </button>
                                <button onclick="dashboard.askMentor('What is a good risk/reward ratio?')" class="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-700 text-sm text-gray-300 transition-colors">
                                    R:R Ratios
                                </button>
                                <button onclick="dashboard.askMentor('How do I control emotions while trading?')" class="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-700 text-sm text-gray-300 transition-colors">
                                    Trading Psychology
                                </button>
                                <button onclick="dashboard.askMentor('Explain support and resistance levels')" class="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-700 text-sm text-gray-300 transition-colors">
                                    Technical Analysis
                                </button>
                                <button onclick="dashboard.askMentor('How do I create a trading plan?')" class="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-700 text-sm text-gray-300 transition-colors">
                                    Trading Plan
                                </button>
                            </div>
                        </div>
                        
                        <div class="bg-gray-800 rounded-xl p-4 border border-gray-700 bg-gradient-to-br from-yellow-900/30 to-orange-900/30">
                            <h4 class="font-bold text-white mb-2"><i class="fas fa-lightbulb text-yellow-400 mr-2"></i>Daily Tip</h4>
                            <p class="text-sm text-gray-400">"Never risk more than 2% of your account on a single trade. Consistency beats intensity."</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async sendMentorMessage() {
        const input = document.getElementById('mentor-input');
        if (!input) return;
        
        const message = input.value.trim();
        if (!message) return;
        
        const container = document.getElementById('mentor-messages');
        if (!container) return;
        
        container.innerHTML += `
            <div class="flex gap-3 flex-row-reverse">
                <div class="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center text-white text-sm flex-shrink-0">
                    <i class="fas fa-user"></i>
                </div>
                <div class="bg-purple-600 p-3 rounded-2xl rounded-tr-none max-w-[85%] sm:max-w-[80%]">
                    <p class="text-white">${message}</p>
                </div>
            </div>
        `;
        
        input.value = '';
        container.scrollTop = container.scrollHeight;
        
        const typingId = 'typing-' + Date.now();
        container.innerHTML += `
            <div id="${typingId}" class="flex gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm flex-shrink-0">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="bg-gray-700 p-3 rounded-2xl rounded-tl-none">
                    <div class="flex space-x-1">
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                    </div>
                </div>
            </div>
        `;
        container.scrollTop = container.scrollHeight;
        
        try {
            const response = await api.askMentor(message);
            const typingEl = document.getElementById(typingId);
            if (typingEl) typingEl.remove();
            
            container.innerHTML += `
                <div class="flex gap-3">
                    <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm flex-shrink-0">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="bg-gray-700 p-3 rounded-2xl rounded-tl-none max-w-[85%] sm:max-w-[80%]">
                        <p class="text-gray-200">${response.response}</p>
                        ${response.suggested_resources?.length ? `
                            <div class="mt-2 pt-2 border-t border-gray-600 text-xs text-purple-400">
                                <strong>Suggested:</strong> ${response.suggested_resources.join(', ')}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
            container.scrollTop = container.scrollHeight;
        } catch (e) {
            const typingEl = document.getElementById(typingId);
            if (typingEl) typingEl.remove();
            
            container.innerHTML += `
                <div class="flex gap-3">
                    <div class="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center text-white text-sm flex-shrink-0">
                        <i class="fas fa-exclamation"></i>
                    </div>
                    <div class="bg-red-900/50 p-3 rounded-2xl rounded-tl-none border border-red-700 max-w-[80%]">
                        <p class="text-red-200 text-sm">Sorry, I encountered an error. Please try again.</p>
                    </div>
                </div>
            `;
        }
    }

    askMentor(question) {
        const input = document.getElementById('mentor-input');
        if (input) {
            input.value = question;
            this.sendMentorMessage();
        }
    }

    clearMentorChat() {
        const container = document.getElementById('mentor-messages');
        if (container) {
            container.innerHTML = `
                <div class="flex gap-3">
                    <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm flex-shrink-0">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="bg-gray-700 p-3 rounded-2xl rounded-tl-none max-w-[80%]">
                        <p class="text-gray-200">Chat cleared. How can I help you today?</p>
                    </div>
                </div>
            `;
        }
    }

    async loadChartAnalysis() {
        const container = document.getElementById('section-analysis');
        if (!container) return;
        
        container.innerHTML = `
            <div class="max-w-6xl mx-auto">
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="bg-gray-800 rounded-xl p-6 border border-gray-700">
                        <h3 class="text-xl font-bold text-white mb-4"><i class="fas fa-chart-line mr-2 text-purple-400"></i>AI Chart Analysis</h3>
                        <p class="text-gray-400 mb-6">Upload your chart images for instant pattern recognition and trade setup validation.</p>
                        
                        <div id="chart-dropzone" class="border-2 border-dashed border-gray-600 rounded-xl p-12 text-center hover:border-purple-500 hover:bg-purple-900/10 transition-all cursor-pointer bg-gray-900">
                            <input type="file" id="chart-input" class="hidden" accept="image/*" onchange="dashboard.handleChartUpload(this.files[0])">
                            <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-700 flex items-center justify-center text-purple-400 text-2xl">
                                <i class="fas fa-cloud-upload-alt"></i>
                            </div>
                            <p class="text-gray-300 font-medium mb-1">Drop chart image here</p>
                            <p class="text-sm text-gray-500">or click to browse (PNG, JPG, max 5MB)</p>
                        </div>
                        
                        <div class="grid grid-cols-2 gap-4 mt-4">
                            <div>
                                <label class="block text-sm text-gray-400 mb-1">Symbol</label>
                                <input type="text" id="chart-symbol" placeholder="EURUSD" class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500">
                            </div>
                            <div>
                                <label class="block text-sm text-gray-400 mb-1">Timeframe</label>
                                <select id="chart-timeframe" class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500">
                                    <option value="">Auto-detect</option>
                                    <option value="5M">5M</option>
                                    <option value="15M">15M</option>
                                    <option value="1H">1H</option>
                                    <option value="4H">4H</option>
                                    <option value="1D">1D</option>
                                    <option value="1W">1W</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    
                    <div id="chart-results" class="bg-gray-800 rounded-xl p-6 border border-gray-700 hidden">
                        <p class="text-gray-500 text-center">Upload a chart to see AI analysis results</p>
                    </div>
                </div>
            </div>
        `;
        
        const dropZone = document.getElementById('chart-dropzone');
        const fileInput = document.getElementById('chart-input');
        
        if (dropZone) {
            dropZone.addEventListener('click', () => fileInput?.click());
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('border-purple-500', 'bg-purple-900/20');
            });
            dropZone.addEventListener('dragleave', () => {
                dropZone.classList.remove('border-purple-500', 'bg-purple-900/20');
            });
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('border-purple-500', 'bg-purple-900/20');
                const file = e.dataTransfer.files[0];
                if (file) this.handleChartUpload(file);
            });
        }
    }

    async handleChartUpload(file) {
        if (!file) return;
        if (file.size > 5 * 1024 * 1024) {
            alert('File too large (max 5MB)');
            return;
        }
        
        const resultsDiv = document.getElementById('chart-results');
        if (!resultsDiv) return;
        
        resultsDiv.classList.remove('hidden');
        resultsDiv.innerHTML = '<div class="flex items-center justify-center py-12"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div><span class="ml-3 text-gray-400">Analyzing chart with AI Vision...</span></div>';
        
        const symbol = document.getElementById('chart-symbol')?.value;
        const timeframe = document.getElementById('chart-timeframe')?.value;
        
        try {
            const analysis = await api.analyzeChart(file, symbol, timeframe);
            
            const biasColor = analysis.trading_bias === 'bullish' ? 'text-green-400' : 
                             analysis.trading_bias === 'bearish' ? 'text-red-400' : 'text-gray-400';
            
            resultsDiv.innerHTML = `
                <div class="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6">
                    <div>
                        <h4 class="text-lg font-bold text-white">Analysis Results</h4>
                        <p class="text-sm text-gray-500">${analysis.symbol || symbol || 'Unknown'} ${analysis.timeframe || timeframe || ''}</p>
                    </div>
                    <span class="px-3 py-1 rounded-full ${analysis.confidence > 0.7 ? 'bg-green-900 text-green-300' : 'bg-yellow-900 text-yellow-300'} text-sm font-bold">
                        ${Math.round(analysis.confidence * 100)}% Confidence
                    </span>
                </div>
                
                <div class="mb-6">
                    <span class="text-sm text-gray-400">Trading Bias:</span>
                    <span class="text-2xl font-bold ml-2 ${biasColor} uppercase">${analysis.trading_bias}</span>
                </div>
                
                <div class="space-y-4">
                    <div>
                        <h5 class="font-semibold text-gray-300 mb-2">Patterns Detected</h5>
                        <div class="flex flex-wrap gap-2">
                            ${analysis.patterns_detected?.map(p => `<span class="px-3 py-1 rounded-full bg-blue-900 text-blue-300 text-sm">${p.name}</span>`).join('') || '<span class="text-gray-500">None detected</span>'}
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div class="p-3 bg-red-900/30 rounded-lg border border-red-800">
                            <span class="text-xs text-red-400 font-semibold">RESISTANCE</span>
                            <p class="text-lg font-bold text-red-300">${analysis.resistance_levels?.[0] || 'N/A'}</p>
                        </div>
                        <div class="p-3 bg-green-900/30 rounded-lg border border-green-800">
                            <span class="text-xs text-green-400 font-semibold">SUPPORT</span>
                            <p class="text-lg font-bold text-green-300">${analysis.support_levels?.[0] || 'N/A'}</p>
                        </div>
                    </div>
                    
                    <div>
                        <h5 class="font-semibold text-gray-300 mb-2">AI Insights</h5>
                        <ul class="list-disc list-inside space-y-1 text-sm text-gray-400">
                            ${analysis.key_insights?.map(i => `<li>${i}</li>`).join('') || '<li>No specific insights</li>'}
                        </ul>
                    </div>
                </div>
            `;
        } catch (error) {
            resultsDiv.innerHTML = `<div class="p-4 bg-red-900/50 text-red-300 rounded-lg border border-red-800">Analysis failed: ${error.message}</div>`;
        }
    }

    async loadPerformance() {
        const container = document.getElementById('section-performance');
        if (!container) return;
        
        container.innerHTML = `
            <div class="max-w-6xl mx-auto space-y-6">
                <div class="bg-gray-800 rounded-xl p-6 border border-gray-700">
                    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
                        <div>
                            <h3 class="text-xl font-bold text-white"><i class="fas fa-chart-bar mr-2 text-purple-400"></i>Performance Analytics</h3>
                            <p class="text-gray-400 text-sm">Analyze your trading performance and psychology</p>
                        </div>
                        <select id="analysis-period" onchange="dashboard.loadPerformanceStats()" class="bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500">
                            <option value="30">Last 30 Days</option>
                            <option value="90">Last 90 Days</option>
                            <option value="365">Last Year</option>
                        </select>
                    </div>
                    
                    <div id="performance-stats" class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="p-4 bg-gradient-to-br from-blue-900 to-blue-800 rounded-xl">
                            <div class="text-3xl font-bold text-blue-300 mb-1">--</div>
                            <div class="text-sm text-gray-400">Total Trades</div>
                        </div>
                        <div class="p-4 bg-gradient-to-br from-green-900 to-green-800 rounded-xl">
                            <div class="text-3xl font-bold text-green-300 mb-1">--</div>
                            <div class="text-sm text-gray-400">Win Rate</div>
                        </div>
                        <div class="p-4 bg-gradient-to-br from-purple-900 to-purple-800 rounded-xl">
                            <div class="text-3xl font-bold text-purple-300 mb-1">--</div>
                            <div class="text-sm text-gray-400">Net P&L</div>
                        </div>
                        <div class="p-4 bg-gradient-to-br from-orange-900 to-orange-800 rounded-xl">
                            <div class="text-3xl font-bold text-orange-300 mb-1">--</div>
                            <div class="text-sm text-gray-400">Grade</div>
                        </div>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="bg-gray-800 rounded-xl p-6 border border-gray-700">
                        <h4 class="font-bold text-white mb-4"><i class="fas fa-upload mr-2 text-purple-400"></i>Upload Trade Journal</h4>
                        <p class="text-gray-400 text-sm mb-4">Paste your trade data in JSON format</p>
                        <textarea id="journal-input" rows="8" class="w-full bg-gray-900 border border-gray-700 rounded-lg p-4 text-white font-mono text-sm focus:outline-none focus:border-purple-500" placeholder='[
  {
    "entry_date": "2024-01-01",
    "symbol": "EURUSD",
    "direction": "BUY",
    "entry_price": 1.0850,
    "exit_price": 1.0900,
    "pnl": 50.00,
    "outcome": "win"
  }
]'></textarea>
                        <button onclick="dashboard.analyzePerformance()" class="mt-4 w-full bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-lg transition-colors font-semibold flex items-center justify-center gap-2">
                            <i class="fas fa-brain"></i> Analyze Performance
                        </button>
                    </div>
                    
                    <div id="performance-results" class="bg-gray-800 rounded-xl p-6 border border-gray-700 hidden">
                        <p class="text-gray-500 text-center">Upload trade data to see analysis</p>
                    </div>
                </div>
            </div>
        `;
        
        this.loadPerformanceStats();
    }

    async loadPerformanceStats() {
        const days = document.getElementById('analysis-period')?.value || 30;
        try {
            const stats = await api.getPerformanceStats(days);
            const container = document.getElementById('performance-stats');
            if (container && stats.summary) {
                container.innerHTML = `
                    <div class="p-4 bg-gradient-to-br from-blue-900 to-blue-800 rounded-xl">
                        <div class="text-3xl font-bold text-blue-300 mb-1">${stats.summary.total_trades || 0}</div>
                        <div class="text-sm text-gray-400">Total Trades</div>
                    </div>
                    <div class="p-4 bg-gradient-to-br from-green-900 to-green-800 rounded-xl">
                        <div class="text-3xl font-bold text-green-300 mb-1">${stats.summary.win_rate || 0}%</div>
                        <div class="text-sm text-gray-400">Win Rate</div>
                    </div>
                    <div class="p-4 bg-gradient-to-br from-purple-900 to-purple-800 rounded-xl">
                        <div class="text-3xl font-bold text-purple-300 mb-1">$${stats.summary.total_pnl || 0}</div>
                        <div class="text-sm text-gray-400">Net P&L</div>
                    </div>
                    <div class="p-4 bg-gradient-to-br from-orange-900 to-orange-800 rounded-xl">
                        <div class="text-3xl font-bold text-orange-300 mb-1">B+</div>
                        <div class="text-sm text-gray-400">Grade</div>
                    </div>
                `;
            }
        } catch (e) {
            console.error('Failed to load stats:', e);
        }
    }

    async analyzePerformance() {
        const input = document.getElementById('journal-input');
        const resultsDiv = document.getElementById('performance-results');
        
        if (!input || !resultsDiv) return;
        
        if (!input.value.trim()) {
            alert('Please enter trade data');
            return;
        }
        
        try {
            const trades = JSON.parse(input.value);
            resultsDiv.classList.remove('hidden');
            resultsDiv.innerHTML = '<div class="flex items-center justify-center py-8"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div><span class="ml-3 text-gray-400">Analyzing performance...</span></div>';
            
            const analysis = await api.analyzeJournal(trades);
            const stats = analysis.statistics || {};
            
            resultsDiv.innerHTML = `
                <div class="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6">
                    <h4 class="text-lg font-bold text-white">Analysis Results</h4>
                    <span class="px-4 py-2 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold">
                        Grade: ${analysis.overall_grade || 'N/A'}
                    </span>
                </div>
                
                <div class="grid grid-cols-2 gap-4 mb-6">
                    <div class="text-center p-4 bg-gray-900 rounded-lg">
                        <div class="text-2xl font-bold text-blue-400">${stats.win_rate || 0}%</div>
                        <div class="text-xs text-gray-500">Win Rate</div>
                    </div>
                    <div class="text-center p-4 bg-gray-900 rounded-lg">
                        <div class="text-2xl font-bold text-green-400">${stats.profit_factor || 0}</div>
                        <div class="text-xs text-gray-500">Profit Factor</div>
                    </div>
                    <div class="text-center p-4 bg-gray-900 rounded-lg">
                        <div class="text-2xl font-bold text-purple-400">$${stats.expectancy || 0}</div>
                        <div class="text-xs text-gray-500">Expectancy</div>
                    </div>
                    <div class="text-center p-4 bg-gray-900 rounded-lg">
                        <div class="text-2xl font-bold text-orange-400">${stats.total_trades || 0}</div>
                        <div class="text-xs text-gray-500">Total Trades</div>
                    </div>
                </div>
                
                <div class="space-y-3">
                    <h5 class="font-semibold text-gray-300">Recommendations:</h5>
                    ${analysis.improvements?.map(i => `<div class="p-3 bg-blue-900/30 rounded-lg text-sm text-blue-300 border-l-4 border-blue-500">${i}</div>`).join('') || '<p class="text-gray-500">No recommendations</p>'}
                </div>
            `;
        } catch (e) {
            alert('Invalid JSON format: ' + e.message);
        }
    }

    showSkeleton(container, count = 3) {
        container.innerHTML = Array(count).fill(0).map(() => `
            <div class="animate-pulse bg-gray-800 rounded-lg p-4 border border-gray-700 h-32"></div>
        `).join('');
    }

    initFeatureCarousel() {
        const carousel = document.getElementById('feature-carousel');
        if (!carousel) return;
        
        const slides = [
            { icon: 'fa-satellite-dish', title: 'Trading Signals', desc: 'AI-powered signals with high accuracy', color: 'from-purple-600 to-blue-600', section: 'signals' },
            { icon: 'fa-book', title: 'Trading Journal', desc: 'Track and analyze your trading performance', color: 'from-green-600 to-teal-600', section: 'journal' },
            { icon: 'fa-chart-line', title: 'Chart Analysis', desc: 'Advanced technical analysis with AI Vision', color: 'from-orange-600 to-red-600', section: 'analysis' },
            { icon: 'fa-robot', title: 'AI Mentor', desc: 'Personalized trading coaching 24/7', color: 'from-pink-600 to-purple-600', section: 'mentor' },
            { icon: 'fa-graduation-cap', title: 'Courses', desc: 'Learn from beginner to advanced', color: 'from-blue-600 to-cyan-600', section: 'courses' },
            { icon: 'fa-video', title: 'Webinars', desc: 'Live trading sessions and Q&A', color: 'from-indigo-600 to-purple-600', section: 'webinars' },
            { icon: 'fa-newspaper', title: 'Trading Blog', desc: 'Latest market insights and strategies', color: 'from-yellow-600 to-orange-600', section: 'blog' }
        ];
        
        let currentSlide = 0;
        
        const renderSlides = () => {
            const slide = slides[currentSlide];
            carousel.innerHTML = `
                <div class="bg-gradient-to-r ${slide.color} rounded-xl p-6 md:p-8 text-white cursor-pointer hover:shadow-lg transition-all transform hover:-translate-y-1" onclick="dashboard.navigate('${slide.section}')">
                    <div class="flex items-start justify-between">
                        <div>
                            <i class="fas ${slide.icon} text-3xl mb-3 opacity-80"></i>
                            <h3 class="text-xl font-bold mb-1">${slide.title}</h3>
                            <p class="text-white/80 text-sm">${slide.desc}</p>
                        </div>
                        <i class="fas fa-arrow-right text-white/50 text-xl"></i>
                    </div>
                </div>
            `;
        };
        
        document.getElementById('carousel-next')?.addEventListener('click', () => {
            currentSlide = (currentSlide + 1) % slides.length;
            renderSlides();
        });
        
        document.getElementById('carousel-prev')?.addEventListener('click', () => {
            currentSlide = (currentSlide - 1 + slides.length) % slides.length;
            renderSlides();
        });
        
        setInterval(() => {
            currentSlide = (currentSlide + 1) % slides.length;
            renderSlides();
        }, 5000);
        
        renderSlides();
    }

    logout() {
        localStorage.removeItem('pipways_token');
        localStorage.removeItem('pipways_user');
        window.location.href = '/';
    }
}

const dashboard = new DashboardController();
