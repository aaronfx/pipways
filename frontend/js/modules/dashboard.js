/**
 * Pipways Dashboard Controller - COMPLETE VERSION
 * All modules: AI Mentor, Chart Analysis, Performance, Admin, Journal
 */
class DashboardController {
    constructor() {
        this.user = null;
        this.allCourses = [];
        this.manualTrades = [];
        this.currentChartFile = null;
        this.currentChartBase64 = null;
        this.currentAnalysis = null;
        this.currentJournalFormat = null;
        this.equityChart = null;
        this.distributionChart = null;
        this.mentorSkillLevel = 'intermediate';
        this.init();
    }

    init() {
        this.checkAuth();
        this.setupNavigation();
        this.setupMobileMenu();
        this.renderAdminMenu();
        this.initFeatureCarousel();
        this.loadDashboardStats();
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
        const user = this.user || {};
        const userNameEl = document.getElementById('user-name');
        const userEmailEl = document.getElementById('user-email');
        const headerUserNameEl = document.getElementById('header-user-name');

        if (userNameEl) userNameEl.textContent = user.full_name || user.email || 'User';
        if (userEmailEl) userEmailEl.textContent = user.email || '';
        if (headerUserNameEl) headerUserNameEl.textContent = user.full_name || user.email || 'Trader';
    }

    renderAdminMenu() {
        const isAdmin = this.user && (
            this.user.is_admin === true || 
            this.user.role === 'admin' ||
            this.user.is_superuser === true
        );

        const adminMenu = document.getElementById('admin-menu-container');
        if (adminMenu) {
            if (isAdmin) {
                adminMenu.classList.remove('hidden');
            } else {
                adminMenu.classList.add('hidden');
            }
        }
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

        if (overlay) {
            overlay.addEventListener('click', () => {
                sidebar.classList.add('-translate-x-full');
                overlay.classList.add('hidden');
            });
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

        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        if (sidebar) sidebar.classList.add('-translate-x-full');
        if (overlay) overlay.classList.add('hidden');
    }

    async loadSectionData(section) {
        try {
            switch(section) {
                case 'dashboard': 
                    this.loadDashboardStats();
                    break;
                case 'signals': 
                    await this.loadSignals(); 
                    break;
                case 'courses': 
                    await this.loadCourses(); 
                    break;
                case 'webinars': 
                    await this.loadWebinars(); 
                    break;
                case 'blog': 
                    await this.loadBlog(); 
                    break;
                case 'journal': 
                    this.setupJournalUpload(); 
                    break;
                case 'admin': 
                    await this.loadAdminData(); 
                    break;
                case 'mentor': 
                    await this.loadMentor(); 
                    break;
                case 'analysis': 
                    await this.loadChartAnalysis(); 
                    break;
                case 'performance': 
                    await this.loadPerformance(); 
                    break;
            }
        } catch (err) {
            console.error(`[Dashboard] Error loading ${section}:`, err);
        }
    }

    // ==================== EXISTING METHODS ====================

    async loadDashboardStats() {
        try {
            const signals = await API.getSignals();
            document.getElementById('stat-signals').textContent = Array.isArray(signals) ? signals.length : '--';
        } catch (e) {
            document.getElementById('stat-signals').textContent = '--';
        }

        try {
            const courses = await API.getCourses();
            const courseList = Array.isArray(courses) ? courses : (courses.courses || []);
            document.getElementById('stat-courses').textContent = courseList.length;
        } catch (e) {
            document.getElementById('stat-courses').textContent = '--';
        }
    }

    async loadSignals() {
        const container = document.getElementById('signals-container');
        if (!container) return;

        this.showSkeleton(container, 3);

        try {
            const data = await API.getSignals();
            let signals = Array.isArray(data) ? data : (data.signals || []);
            // Only show published/active signals
            signals = signals.filter(s => s.status === 'active' || !!s.is_published || !!s.is_active);
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
            const data = await API.getCourses();
            let courses = Array.isArray(data) ? data : (data.courses || []);
            // Only show published courses
            courses = courses.filter(c => !!c.is_published || !!c.is_active);
            this.allCourses = courses;
            this.renderCourses(courses);
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
            const data = await API.getWebinars();
            let webinars = Array.isArray(data) ? data : (data.webinars || []);
            // Only show published webinars
            webinars = webinars.filter(w => !!w.is_published || w.status === 'scheduled' || w.status === 'live');

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
                        ${webinar.meeting_link
                            ? `<a href="${webinar.meeting_link}" target="_blank" class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm transition-colors whitespace-nowrap">Join Now →</a>`
                            : `<button class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm transition-colors whitespace-nowrap">Register</button>`}
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
            const data = await API.getBlogPosts();
            let posts = Array.isArray(data) ? data : (data.posts || []);
            // Only show published posts
            posts = posts.filter(p => !!p.is_published || p.status === 'published');

            if (!posts || posts.length === 0) {
                container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">No articles published yet</div>';
                return;
            }

            container.innerHTML = posts.map(post => `
                <article class="bg-gray-800 rounded-lg overflow-hidden border border-gray-700 hover:border-gray-600 transition-all cursor-pointer group">
                    ${post.featured_image
                        ? `<div class="h-48 overflow-hidden"><img src="${post.featured_image}" class="w-full h-full object-cover group-hover:scale-105 transition-transform" onerror="this.parentElement.innerHTML='<div class=\'h-48 bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center\'><i class=\'fas fa-newspaper text-5xl text-white/20\'></i></div>'"></div>`
                        : `<div class="h-48 bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center"><i class="fas fa-newspaper text-5xl text-white/20 group-hover:scale-110 transition-transform"></i></div>`}
                    <div class="p-4">
                        <div class="text-xs text-purple-400 mb-2 uppercase tracking-wide">${post.category || 'General'}</div>
                        <h4 class="font-bold text-white mb-2 group-hover:text-purple-400 transition-colors">${post.title}</h4>
                        <p class="text-sm text-gray-400 line-clamp-3 mb-3">${post.excerpt || ''}</p>
                        <div class="text-xs text-gray-500 flex justify-between items-center">
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

    async loadAdminData() {
        const container = document.getElementById('admin-container');
        if (!container) return;

        // Client-side guard before hitting the server
        const isAdmin = this.user && (
            this.user.is_admin === true
            || this.user.role === 'admin'
            || this.user.is_superuser === true
        );
        if (!isAdmin) {
            container.innerHTML = `
                <div class="flex flex-col items-center justify-center py-20 text-center">
                    <div class="w-16 h-16 rounded-full bg-red-900/30 flex items-center justify-center mb-4">
                        <i class="fas fa-lock text-red-400 text-2xl"></i>
                    </div>
                    <h3 class="text-xl font-bold text-white mb-2">Access Denied</h3>
                    <p class="text-gray-400 text-sm">Administrator privileges required.</p>
                </div>`;
            return;
        }

        // FIX: delegate to the full AdminPage module (tabs, charts, paginated users, AI monitor).
        // Previously rendered a static 3-card grid with non-functional Quick Action buttons.
        if (typeof AdminPage !== 'undefined') {
            await AdminPage.render(container);
            return;
        }

        // Fallback: AdminPage module not loaded — show basic stats + warning
        console.warn('[Dashboard] AdminPage module not loaded — showing basic view');
        try {
            const stats = await API.getAdminStats();
            container.innerHTML = `
                <div class="bg-yellow-900/20 border border-yellow-700/50 rounded-lg p-4 mb-4 text-sm text-yellow-400">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    Admin module (admin.js) not loaded. Add it to the HTML before dashboard.js.
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <div class="text-3xl font-bold text-white mb-1">${stats.total_users ?? 0}</div>
                        <div class="text-sm text-gray-400">Total Users</div>
                    </div>
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <div class="text-3xl font-bold text-white mb-1">${stats.active_signals ?? 0}</div>
                        <div class="text-sm text-gray-400">Active Signals</div>
                    </div>
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <div class="text-3xl font-bold text-white mb-1">${stats.new_today ?? 0}</div>
                        <div class="text-sm text-gray-400">New Today</div>
                    </div>
                </div>`;
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
                                <button onclick="dashboard.askMentor('How do I manage risk effectively?')" class="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-700 text-sm text-gray-300 transition-colors">Risk Management</button>
                                <button onclick="dashboard.askMentor('What is a good risk/reward ratio?')" class="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-700 text-sm text-gray-300 transition-colors">R:R Ratios</button>
                                <button onclick="dashboard.askMentor('How do I control emotions while trading?')" class="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-700 text-sm text-gray-300 transition-colors">Trading Psychology</button>
                                <button onclick="dashboard.askMentor('Explain support and resistance levels')" class="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-700 text-sm text-gray-300 transition-colors">Technical Analysis</button>
                                <button onclick="dashboard.askMentor('How do I create a trading plan?')" class="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-700 text-sm text-gray-300 transition-colors">Trading Plan</button>
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
                    <p class="text-white">${message.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</p>
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
            const response = await API.askMentor(message);
            const typingEl = document.getElementById(typingId);
            if (typingEl) typingEl.remove();

            container.innerHTML += `
                <div class="flex gap-3">
                    <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm flex-shrink-0">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="bg-gray-700 p-3 rounded-2xl rounded-tl-none max-w-[85%] sm:max-w-[80%]">
                        <p class="text-gray-200">${response.response || response.answer}</p>
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

    // ==================== NEW CHART ANALYSIS METHODS ====================

    async loadChartAnalysis() {
        const dropZone = document.getElementById('chart-dropzone');
        const fileInput = document.getElementById('chart-file-input');

        if (dropZone && fileInput) {
            dropZone.addEventListener('click', () => fileInput.click());

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
                if (file) this.handleChartFileSelect(file);
            });

            fileInput.addEventListener('change', (e) => {
                if (e.target.files[0]) this.handleChartFileSelect(e.target.files[0]);
            });
        }
    }

    handleChartFileSelect(file) {
        if (!file) return;

        if (file.size > 5 * 1024 * 1024) {
            window.dashboard._toast('File too large — max 5MB allowed', 'error');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.getElementById('chart-preview');
            const placeholder = document.getElementById('chart-upload-placeholder');
            const analyzeBtn = document.getElementById('analyze-chart-btn');

            if (preview) {
                preview.src = e.target.result;
                preview.classList.remove('hidden');
            }
            if (placeholder) placeholder.classList.add('hidden');
            if (analyzeBtn) analyzeBtn.disabled = false;

            this.currentChartFile = file;
            this.currentChartBase64 = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    async analyzeChart() {
        if (!this.currentChartBase64) {
            window.dashboard._toast('Please select a chart image first', 'warning');
            return;
        }

        const loadingEl = document.getElementById('chart-analysis-loading');
        const resultsEl = document.getElementById('chart-analysis-results');
        const analyzeBtn = document.getElementById('analyze-chart-btn');

        if (loadingEl) loadingEl.classList.remove('hidden');
        if (analyzeBtn) analyzeBtn.disabled = true;

        try {
            const symbol = document.getElementById('chart-symbol')?.value || 'AUTO';
            const timeframe = document.getElementById('chart-timeframe')?.value || '';

            const response = await fetch(`${window.location.origin}/ai/chart/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('pipways_token')}`
                },
                body: JSON.stringify({
                    image: this.currentChartBase64,
                    symbol: symbol,
                    timeframe: timeframe
                })
            });

            const data = await response.json();

            if (resultsEl) {
                resultsEl.classList.remove('hidden');

                document.getElementById('analysis-symbol').textContent = data.symbol || symbol || 'Unknown';
                document.getElementById('analysis-timeframe').textContent = data.timeframe || timeframe || '';

                const confidence = Math.round((data.confidence || 0) * 100);
                const confEl = document.getElementById('analysis-confidence');
                confEl.textContent = `${confidence}%`;
                confEl.className = `px-3 py-1 rounded-full text-sm font-bold ${confidence > 70 ? 'bg-green-900 text-green-300' : confidence > 40 ? 'bg-yellow-900 text-yellow-300' : 'bg-red-900 text-red-300'}`;

                const biasEl = document.getElementById('analysis-bias');
                biasEl.textContent = data.trading_bias || data.bias || 'Neutral';
                biasEl.className = `text-2xl font-bold ml-2 uppercase ${data.trading_bias === 'bullish' ? 'text-green-400' : data.trading_bias === 'bearish' ? 'text-red-400' : 'text-gray-400'}`;

                document.getElementById('analysis-pattern').textContent = data.pattern || 'No specific pattern detected';

                if (data.trade_setup) {
                    const setup = data.trade_setup;
                    document.getElementById('setup-entry').textContent = setup.entry_price || setup.entry || '--';
                    document.getElementById('setup-sl').textContent = setup.stop_loss || setup.sl || '--';
                    document.getElementById('setup-tp').textContent = setup.take_profit || setup.tp || '--';
                    document.getElementById('setup-rr').textContent = setup.risk_reward || setup.rr || '--';
                }

                const levelsContainer = document.getElementById('key-levels-list');
                if (levelsContainer && data.key_levels) {
                    levelsContainer.innerHTML = data.key_levels.map(level => `
                        <div class="flex justify-between items-center p-2 bg-gray-900 rounded border-l-4 ${level.type === 'support' ? 'border-green-500' : level.type === 'resistance' ? 'border-red-500' : 'border-blue-500'}">
                            <span class="text-gray-300 capitalize">${level.type}</span>
                            <span class="font-mono font-bold text-white">${level.price}</span>
                        </div>
                    `).join('');
                }

                const insightsEl = document.getElementById('analysis-insights');
                if (insightsEl && data.key_insights) {
                    insightsEl.innerHTML = data.key_insights.map(insight => `<li>${insight}</li>`).join('');
                }

                const attachedChart = document.getElementById('attached-chart-preview');
                if (attachedChart && this.currentChartBase64) {
                    attachedChart.src = this.currentChartBase64;
                    attachedChart.classList.remove('hidden');
                }

                this.currentAnalysis = data;
            }

        } catch (error) {
            console.error('[Chart Analysis] Error:', error);
            window.dashboard._toast('Failed to analyze chart. Please try again.', 'error');
        } finally {
            if (loadingEl) loadingEl.classList.add('hidden');
            if (analyzeBtn) analyzeBtn.disabled = false;
        }
    }

    showTradeValidator() {
        const modal = document.getElementById('trade-validator-modal');
        if (modal) {
            modal.classList.remove('hidden');
            if (this.currentAnalysis?.trade_setup) {
                const setup = this.currentAnalysis.trade_setup;
                document.getElementById('validator-entry').value = setup.entry_price || setup.entry || '';
                document.getElementById('validator-sl').value = setup.stop_loss || setup.sl || '';
                document.getElementById('validator-tp').value = setup.take_profit || setup.tp || '';
                document.getElementById('validator-symbol').value = this.currentAnalysis.symbol || '';
            }
        }
    }

    async validateTradeSetup() {
        const entry = parseFloat(document.getElementById('validator-entry')?.value);
        const sl = parseFloat(document.getElementById('validator-sl')?.value);
        const tp = parseFloat(document.getElementById('validator-tp')?.value);
        const symbol = document.getElementById('validator-symbol')?.value || 'EURUSD';

        if (!entry || !sl || !tp) {
            window.dashboard._toast('Please fill in Entry, SL, and TP values', 'warning');
            return;
        }

        try {
            const response = await fetch(`${window.location.origin}/ai/trade/validate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('pipways_token')}`
                },
                body: JSON.stringify({
                    entry_price: entry,
                    stop_loss: sl,
                    take_profit: tp,
                    symbol: symbol,
                    setup_type: this.currentAnalysis?.pattern || 'manual'
                })
            });

            const result = await response.json();

            const resultEl = document.getElementById('validation-result');
            if (resultEl) {
                resultEl.classList.remove('hidden');

                const scoreEl = document.getElementById('validation-score');
                const score = result.quality_score || 0;
                scoreEl.textContent = score;
                scoreEl.className = `score-circle ${score >= 80 ? 'score-excellent' : score >= 60 ? 'score-good' : score >= 40 ? 'score-warning' : 'score-danger'}`;

                document.getElementById('validation-recommendation').textContent = result.recommendation || (result.valid ? 'Valid Setup' : 'Review Setup');
                document.getElementById('validation-rr').textContent = result.risk_reward_ratio || result.rr || '--';
                document.getElementById('validation-probability').textContent = (result.probability || result.win_probability || 0) + '%';

                const warningsEl = document.getElementById('validation-warnings');
                if (result.warnings && result.warnings.length > 0) {
                    warningsEl.innerHTML = result.warnings.map(w => `<div class="text-yellow-400 flex items-center gap-2 mb-1"><i class="fas fa-exclamation-triangle"></i>${w}</div>`).join('');
                } else {
                    warningsEl.innerHTML = '<div class="text-green-400 flex items-center gap-2"><i class="fas fa-check-circle"></i>No warnings - Good setup!</div>';
                }

                const suggestionsEl = document.getElementById('validation-suggestions');
                if (suggestionsEl && result.suggestions) {
                    suggestionsEl.innerHTML = result.suggestions.map(s => `<div class="flex items-start gap-2 mb-1"><i class="fas fa-lightbulb mt-1 text-blue-400"></i>${s}</div>`).join('');
                }
            }

        } catch (error) {
            console.error('[Trade Validator] Error:', error);
            window.dashboard._toast('Validation failed. Please try again.', 'error');
        }
    }

    async saveCurrentSignal() {
        if (!this.currentAnalysis) {
            window.dashboard._toast('No analysis to save — please analyze a chart first', 'warning');
            return;
        }

        try {
            const response = await fetch(`${window.location.origin}/ai/signal/save`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('pipways_token')}`
                },
                body: JSON.stringify({
                    symbol: this.currentAnalysis.symbol,
                    pattern: this.currentAnalysis.pattern,
                    bias: this.currentAnalysis.trading_bias || this.currentAnalysis.bias,
                    entry_price: this.currentAnalysis.trade_setup?.entry_price || this.currentAnalysis.trade_setup?.entry,
                    stop_loss: this.currentAnalysis.trade_setup?.stop_loss || this.currentAnalysis.trade_setup?.sl,
                    take_profit: this.currentAnalysis.trade_setup?.take_profit || this.currentAnalysis.trade_setup?.tp,
                    confidence: this.currentAnalysis.confidence,
                    chart_image: this.currentChartBase64,
                    analysis_data: this.currentAnalysis
                })
            });

            if (response.ok) {
                window.dashboard._toast('Signal saved successfully!', 'success');
            } else {
                throw new Error('Failed to save signal');
            }
        } catch (error) {
            console.error('[Save Signal] Error:', error);
            window.dashboard._toast('Failed to save signal. Please try again.', 'error');
        }
    }

    // ==================== NEW JOURNAL METHODS ====================

    setJournalFormat(format) {
        this.currentJournalFormat = format;

        document.querySelectorAll('.format-btn').forEach(btn => {
            btn.classList.remove('border-purple-500', 'bg-purple-600');
            btn.classList.add('border-gray-600', 'bg-gray-700');
        });

        const activeBtn = document.querySelector(`[data-format="${format}"]`);
        if (activeBtn) {
            activeBtn.classList.remove('border-gray-600', 'bg-gray-700');
            activeBtn.classList.add('border-purple-500', 'bg-purple-600');
        }

        const fileInput = document.getElementById('journal-file-input');
        const formatLabel = document.getElementById('selected-format');

        const formatConfig = {
            mt4: { accept: '.html,.htm', label: 'MT4 HTML Statement selected' },
            mt5: { accept: '.html,.htm', label: 'MT5 HTML Statement selected' },
            csv: { accept: '.csv', label: 'CSV file selected' },
            excel: { accept: '.xlsx,.xls', label: 'Excel file selected' },
            screenshot: { accept: '.png,.jpg,.jpeg,.webp', label: 'Screenshot for OCR selected' }
        };

        const config = formatConfig[format];
        if (config && fileInput) {
            fileInput.accept = config.accept;
            if (formatLabel) formatLabel.textContent = config.label;
            fileInput.click();
        }
    }

    async handleJournalFile(file) {
        const statusEl = document.getElementById('upload-status');
        const loadingEl = document.getElementById('journal-upload-loading');

        if (statusEl) {
            statusEl.classList.remove('hidden');
            statusEl.innerHTML = `<span class="text-blue-400"><i class="fas fa-spinner fa-spin mr-2"></i>Processing ${file.name}...</span>`;
        }
        if (loadingEl) loadingEl.classList.remove('hidden');

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('format', this.currentJournalFormat || 'auto');

            const response = await fetch(`${window.location.origin}/ai/performance/upload-journal`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('pipways_token')}`
                },
                body: formData
            });

            const result = await response.json();

            if (result.trades && result.trades.length > 0) {
                this.displayJournalAnalysis(result);
                if (statusEl) {
                    statusEl.innerHTML = `<span class="text-green-400"><i class="fas fa-check mr-2"></i>Successfully imported ${result.trades_parsed || result.trades.length} trades</span>`;
                }
            } else {
                throw new Error('No trades found in file');
            }

        } catch (error) {
            console.error('[Journal Upload] Error:', error);
            if (statusEl) {
                statusEl.innerHTML = `<span class="text-red-400"><i class="fas fa-exclamation-circle mr-2"></i>${error.message}</span>`;
            }
        } finally {
            if (loadingEl) loadingEl.classList.add('hidden');
        }
    }

    // ==================== NEW PERFORMANCE METHODS ====================

    async loadPerformance() {
        await this.loadPerformanceStats();
        await this.loadEquityCurve();
        await this.loadTradeDistribution();
    }

    async loadPerformanceStats() {
        const days = document.getElementById('performance-period')?.value || 30;

        try {
            const response = await fetch(`${window.location.origin}/ai/performance/dashboard?days=${days}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('pipways_token')}`
                }
            });

            const data = await response.json();

            if (data.summary) {
                document.getElementById('perf-total-trades').textContent = data.summary.total_trades || 0;
                document.getElementById('perf-win-rate').textContent = (data.summary.win_rate || 0) + '%';
                document.getElementById('perf-profit-factor').textContent = data.summary.profit_factor || '0.0';
                document.getElementById('perf-expectancy').textContent = '$' + (data.summary.expectancy || 0);
            }

            if (data.psychology_profile) {
                const psychContainer = document.getElementById('performance-psychology');
                const traitsContainer = document.getElementById('psychology-traits');

                if (psychContainer && traitsContainer) {
                    psychContainer.classList.remove('hidden');

                    const traits = data.psychology_profile.traits || {};
                    traitsContainer.innerHTML = Object.entries(traits).map(([trait, score]) => `
                        <div class="p-3 bg-gray-900 rounded-lg">
                            <div class="flex justify-between items-center mb-2">
                                <span class="text-gray-400 capitalize">${trait.replace('_', ' ')}</span>
                                <span class="text-white font-bold">${score}%</span>
                            </div>
                            <div class="w-full bg-gray-700 rounded-full h-2">
                                <div class="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full" style="width: ${score}%"></div>
                            </div>
                        </div>
                    `).join('');
                }
            }

        } catch (error) {
            console.error('[Performance Stats] Error:', error);
        }
    }

    async loadEquityCurve() {
        try {
            const response = await fetch(`${window.location.origin}/ai/performance/equity-curve?days=30`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('pipways_token')}`
                }
            });

            const data = await response.json();

            const ctx = document.getElementById('equity-curve-chart');
            if (!ctx) return;

            if (this.equityChart) {
                this.equityChart.destroy();
            }

            this.equityChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates || [],
                    datasets: [{
                        label: 'Equity',
                        data: data.equity || [],
                        borderColor: 'rgb(124, 58, 237)',
                        backgroundColor: 'rgba(124, 58, 237, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            grid: { color: 'rgba(75, 85, 99, 0.3)' },
                            ticks: { color: '#9ca3af' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#9ca3af' }
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
            const response = await fetch(`${window.location.origin}/ai/performance/trade-distribution`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('pipways_token')}`
                }
            });

            const data = await response.json();

            const ctx = document.getElementById('trade-distribution-chart');
            if (!ctx) return;

            if (this.distributionChart) {
                this.distributionChart.destroy();
            }

            this.distributionChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Winners', 'Losers', 'Break Even'],
                    datasets: [{
                        data: [data.wins || 0, data.losses || 0, data.break_even || 0],
                        backgroundColor: [
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(245, 158, 11, 0.8)'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#9ca3af' }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('[Trade Distribution] Error:', error);
        }
    }

    async analyzePerformance() {
        const input = document.getElementById('performance-journal-input');
        if (!input || !input.value.trim()) {
            window.dashboard._toast('Please enter trade data', 'warning');
            return;
        }

        try {
            const trades = JSON.parse(input.value);

            const response = await fetch(`${window.location.origin}/ai/performance/analyze-journal`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('pipways_token')}`
                },
                body: JSON.stringify({ trades })
            });

            const result = await response.json();
            this.displayJournalAnalysis(result);

        } catch (e) {
            window.dashboard._toast('Invalid JSON format: ' + e.message, 'error');
        }
    }

    // ==================== EXISTING JOURNAL METHODS ====================

    showManualEntry() {
        const form = document.getElementById('manual-entry-form');
        if (form) {
            form.classList.remove('hidden');
            form.scrollIntoView({ behavior: 'smooth' });
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
            if (file) await this.handleJournalFile(file);
        });

        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (file) await this.handleJournalFile(file);
        });
    }

    displayJournalAnalysis(result) {
        const statusEl = document.getElementById('upload-status');
        const analysisEl = document.getElementById('journal-analysis');
        const statsEl = document.getElementById('journal-stats');
        const tradesContainer = document.getElementById('recent-trades-container');
        const psychologyEl = document.getElementById('psychology-profile');

        if (statusEl) {
            statusEl.innerHTML = `<span class="text-green-400"><i class="fas fa-check mr-2"></i>Analysis complete! ${result.trades_parsed || result.trades?.length || 0} trades found</span>`;
        }

        if (statsEl) {
            statsEl.classList.remove('hidden');
            document.getElementById('stat-total-trades').textContent = result.statistics?.total_trades || 0;
            document.getElementById('stat-win-rate').textContent = (result.statistics?.win_rate || 0) + '%';
            document.getElementById('stat-profit-factor').textContent = result.statistics?.profit_factor || 0;
            document.getElementById('stat-expectancy').textContent = '$' + (result.statistics?.expectancy || 0);
            document.getElementById('stat-drawdown').textContent = (result.statistics?.max_drawdown || 0) + '%';

            const pnl = result.statistics?.total_pnl || 0;
            const pnlEl = document.getElementById('stat-net-pnl');
            pnlEl.textContent = '$' + Math.abs(pnl).toFixed(2);
            pnlEl.className = 'font-bold ' + (pnl >= 0 ? 'text-green-400' : 'text-red-400');

            document.getElementById('stat-grade').textContent = result.overall_grade || 'N/A';
            document.getElementById('stat-progress').style.width = (result.overall_score || 0) + '%';
        }

        if (analysisEl) {
            analysisEl.classList.remove('hidden');
            analysisEl.innerHTML = `
                <div class="bg-gray-800 rounded-xl p-6 border border-gray-700">
                    <div class="flex justify-between items-center mb-6">
                        <h3 class="text-lg font-bold text-white">Performance Analysis</h3>
                        <span class="px-3 py-1 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold text-sm">${result.overall_grade}</span>
                    </div>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <div class="text-center p-4 bg-gray-900 rounded-lg border border-gray-700">
                            <div class="text-2xl font-bold text-white">${result.statistics?.total_trades || 0}</div>
                            <div class="text-xs text-gray-500 uppercase">Total Trades</div>
                        </div>
                        <div class="text-center p-4 bg-gray-900 rounded-lg border border-gray-700">
                            <div class="text-2xl font-bold ${result.statistics?.win_rate >= 50 ? 'text-green-400' : 'text-red-400'}">${result.statistics?.win_rate || 0}%</div>
                            <div class="text-xs text-gray-500 uppercase">Win Rate</div>
                        </div>
                        <div class="text-center p-4 bg-gray-900 rounded-lg border border-gray-700">
                            <div class="text-2xl font-bold ${result.statistics?.profit_factor >= 1 ? 'text-green-400' : 'text-red-400'}">${result.statistics?.profit_factor || 0}</div>
                            <div class="text-xs text-gray-500 uppercase">Profit Factor</div>
                        </div>
                        <div class="text-center p-4 bg-gray-900 rounded-lg border border-gray-700">
                            <div class="text-2xl font-bold ${result.statistics?.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}">$${Math.abs(result.statistics?.total_pnl || 0).toFixed(2)}</div>
                            <div class="text-xs text-gray-500 uppercase">Net P&L</div>
                        </div>
                    </div>

                    ${result.improvements?.length ? `
                        <div class="space-y-2">
                            <h5 class="font-semibold text-gray-300 text-sm uppercase mb-2">AI Recommendations:</h5>
                            ${result.improvements.map(i => `
                                <div class="p-3 bg-blue-900/20 rounded-lg text-sm text-blue-200 border-l-4 border-blue-500 flex items-start gap-2">
                                    <i class="fas fa-lightbulb text-blue-400 mt-1"></i>
                                    <span>${i}</span>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
        }

        if (psychologyEl && result.psychology) {
            psychologyEl.classList.remove('hidden');
            const psych = result.psychology;
            document.getElementById('psychology-content').innerHTML = `
                <div class="space-y-3">
                    <div class="flex justify-between items-center p-3 bg-gray-900 rounded-lg">
                        <span class="text-gray-400 text-sm">Trading State</span>
                        <span class="text-white font-medium">${psych.best_trading_state || 'N/A'}</span>
                    </div>
                    <div class="flex justify-between items-center p-3 bg-gray-900 rounded-lg">
                        <span class="text-gray-400 text-sm">Consistency</span>
                        <span class="text-${psych.emotional_consistency === 'High' ? 'green' : psych.emotional_consistency === 'Medium' ? 'yellow' : 'red'}-400 font-medium">${psych.emotional_consistency || 'N/A'}</span>
                    </div>
                    <div class="flex justify-between items-center p-3 bg-gray-900 rounded-lg">
                        <span class="text-gray-400 text-sm">Discipline Score</span>
                        <div class="flex items-center gap-2">
                            <div class="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
                                <div class="h-full bg-purple-500" style="width: ${psych.discipline_score || 0}%"></div>
                            </div>
                            <span class="text-white font-medium text-sm">${psych.discipline_score || 0}</span>
                        </div>
                    </div>
                </div>
            `;
        }

        if (tradesContainer && result.trades) {
            tradesContainer.classList.remove('hidden');
            const tbody = document.getElementById('trades-table-body');
            tbody.innerHTML = result.trades.slice(0, 10).map(trade => `
                <tr class="border-b border-gray-700 hover:bg-gray-700/50">
                    <td class="px-4 py-3 font-medium">${trade.symbol || 'N/A'}</td>
                    <td class="px-4 py-3">
                        <span class="px-2 py-1 rounded text-xs font-bold ${trade.direction === 'BUY' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}">${trade.direction}</span>
                    </td>
                    <td class="px-4 py-3 font-mono">${trade.entry_price || '--'}</td>
                    <td class="px-4 py-3 font-mono">${trade.exit_price || '--'}</td>
                    <td class="px-4 py-3 font-mono ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}">${trade.pnl >= 0 ? '+' : ''}${trade.pnl}</td>
                </tr>
            `).join('');
        }
    }

    addManualTrade() {
        const symbol = document.getElementById('manual-symbol').value;
        const direction = document.getElementById('manual-direction').value;
        const entry = parseFloat(document.getElementById('manual-entry').value);
        const pnl = parseFloat(document.getElementById('manual-pnl').value);

        if (!symbol || isNaN(entry) || isNaN(pnl)) {
            window.dashboard._toast('Please fill in all required fields', 'warning');
            return;
        }

        const trade = {
            entry_date: new Date().toISOString().split('T')[0],
            symbol: symbol.toUpperCase(),
            direction: direction,
            entry_price: entry,
            exit_price: parseFloat(document.getElementById('manual-exit').value) || 0,
            stop_loss: parseFloat(document.getElementById('manual-sl').value) || 0,
            take_profit: parseFloat(document.getElementById('manual-tp').value) || 0,
            pnl: pnl,
            outcome: pnl > 0 ? 'win' : (pnl < 0 ? 'loss' : 'breakeven')
        };

        this.manualTrades.push(trade);

        fetch(`${window.location.origin}/ai/performance/analyze-journal`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('pipways_token')}`
            },
            body: JSON.stringify({ trades: this.manualTrades })
        })
        .then(r => r.json())
        .then(result => {
            this.displayJournalAnalysis({...result, trades: this.manualTrades});
        });
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
            { icon: 'fa-satellite-dish', title: 'Market Signals',  desc: 'AI-powered signals with high accuracy',         color: 'from-purple-600 to-blue-600',   section: 'enhanced-signals' },
            { icon: 'fa-book',           title: 'Trading Journal',  desc: 'Track and analyze your trading performance',    color: 'from-green-600 to-teal-600',    section: 'journal' },
            { icon: 'fa-chart-line',     title: 'Chart Analysis',   desc: 'Advanced technical analysis with AI Vision',    color: 'from-orange-600 to-red-600',    section: 'analysis' },
            { icon: 'fa-robot',          title: 'AI Mentor',        desc: 'Personalized trading coaching 24/7',            color: 'from-pink-600 to-purple-600',   section: 'mentor' },
            { icon: 'fa-graduation-cap', title: 'Trading Academy',  desc: 'Learn from beginner to advanced — always free', color: 'from-blue-600 to-cyan-600',     section: null, href: '/academy' },
            { icon: 'fa-video',          title: 'Webinars',         desc: 'Live trading sessions and Q&A',                 color: 'from-indigo-600 to-purple-600', section: 'webinars' },
            { icon: 'fa-newspaper',      title: 'Trading Blog',     desc: 'Latest market insights and strategies',         color: 'from-yellow-600 to-orange-600', section: 'blog' }
        ];

        let currentSlide = 0;

        const renderSlides = () => {
            const slide = slides[currentSlide];
            carousel.innerHTML = `
                <div class="bg-gradient-to-r ${slide.color} rounded-xl p-6 md:p-8 text-white cursor-pointer hover:shadow-lg transition-all transform hover:-translate-y-1" onclick="${slide.href ? `window.location.href='${slide.href}'` : `dashboard.navigate('${slide.section}')`}">
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

// NOTE: api.js defines window.API and window.api globally.
// The local duplicate api object has been removed — use window.API everywhere.

const dashboard = new DashboardController();
