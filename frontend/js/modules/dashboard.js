/**
 * Pipways Dashboard Controller
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
        
        if (userNameEl) userNameEl.textContent = this.user?.full_name || this.user?.email || 'User';
        if (userEmailEl) userEmailEl.textContent = this.user?.email || '';
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
        const adminMenu = document.getElementById('admin-menu');
        if (!adminMenu) return;
        
        const isAdmin = this.user && (this.user.is_admin === true || this.user.role === 'admin');
        adminMenu.classList.toggle('hidden', !isAdmin);
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

        document.getElementById('sidebar')?.classList.add('-translate-x-full');
        document.getElementById('sidebar-overlay')?.classList.add('hidden');
    }

    async loadSectionData(section) {
        try {
            switch(section) {
                case 'signals': await this.loadSignals(); break;
                case 'courses': await this.loadCourses(); break;
                case 'webinars': await this.loadWebinars(); break;
                case 'blog': await this.loadBlog(); break;
                case 'journal': this.setupJournalUpload(); break;
                case 'admin': await this.loadAdminData(); break;
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
            this.showError(container, error.message, () => this.loadSignals());
        }
    }

    renderSignals(signals) {
        const container = document.getElementById('signals-container');
        if (!container) return;
        
        if (!signals || signals.length === 0) {
            container.innerHTML = '<div class="text-center py-8 text-gray-500">No active signals available</div>';
            return;
        }
        
        container.innerHTML = signals.map(signal => `
            <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="font-bold text-white">${signal.symbol}</h4>
                    <span class="text-xs ${signal.direction === 'BUY' ? 'text-green-400' : 'text-red-400'}">${signal.direction}</span>
                </div>
                <div class="text-sm text-gray-400 space-y-1">
                    <div>Entry: <span class="text-white">${signal.entry_price}</span></div>
                    <div>SL: <span class="text-red-400">${signal.stop_loss}</span> / TP: <span class="text-green-400">${signal.take_profit}</span></div>
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
            this.showError(container, error.message, () => this.loadCourses());
        }
    }

    setupCourseFilters() {
        const filterContainer = document.getElementById('course-filters');
        if (!filterContainer) return;
        
        const levels = ['All', 'Beginner', 'Intermediate', 'Advanced'];
        filterContainer.innerHTML = levels.map(level => `
            <button onclick="dashboard.filterCourses('${level}')" 
                    class="filter-btn px-4 py-2 rounded-full text-sm ${level === 'All' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300'}"
                    data-level="${level}">
                ${level}
            </button>
        `).join('');
    }

    filterCourses(level) {
        document.querySelectorAll('.filter-btn').forEach(btn => {
            const isActive = btn.dataset.level === level;
            btn.className = `filter-btn px-4 py-2 rounded-full text-sm ${isActive ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300'}`;
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
            <div class="bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
                <div class="h-40 bg-gradient-to-br from-purple-900 to-blue-900"></div>
                <div class="p-4">
                    <div class="text-xs text-purple-400 mb-1">${course.level || 'Beginner'}</div>
                    <h4 class="font-bold text-white mb-2">${course.title}</h4>
                    <p class="text-sm text-gray-400 mb-3">${course.description || ''}</p>
                    <div class="text-xs text-gray-500">${course.lesson_count || 0} lessons</div>
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
                container.innerHTML = '<div class="text-center py-8 text-gray-500">No upcoming webinars</div>';
                return;
            }
            
            container.innerHTML = webinars.map(webinar => `
                <div class="bg-gray-800 rounded-lg p-4 border border-gray-700 flex justify-between items-center">
                    <div>
                        <h4 class="font-bold text-white">${webinar.title}</h4>
                        <p class="text-sm text-gray-400">${new Date(webinar.scheduled_at).toLocaleDateString()} • ${webinar.presenter || 'TBA'}</p>
                    </div>
                    <button class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded text-sm">Register</button>
                </div>
            `).join('');
        } catch (error) {
            this.showError(container, error.message, () => this.loadWebinars());
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
                container.innerHTML = '<div class="text-center py-8 text-gray-500">No articles available</div>';
                return;
            }
            
            container.innerHTML = posts.map(post => `
                <article class="bg-gray-800 rounded-lg p-4 border border-gray-700">
                    <div class="text-xs text-purple-400 mb-2">${post.category || 'General'}</div>
                    <h4 class="font-bold text-white mb-2">${post.title}</h4>
                    <p class="text-sm text-gray-400 line-clamp-3">${post.excerpt || post.content?.substring(0, 100) + '...' || ''}</p>
                </article>
            `).join('');
        } catch (error) {
            this.showError(container, error.message, () => this.loadBlog());
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
            statusEl.innerHTML = '<span class="text-blue-400"><i class="fas fa-spinner fa-spin mr-2"></i>Analyzing...</span>';
        }
        
        try {
            const result = await api.analyzeJournal(file);
            if (statusEl) {
                statusEl.innerHTML = `<span class="text-green-400"><i class="fas fa-check mr-2"></i>Analysis complete! Found ${result.trades?.length || 0} trades</span>`;
            }
            this.renderJournalAnalysis(result);
        } catch (error) {
            if (statusEl) {
                statusEl.innerHTML = `<span class="text-red-400"><i class="fas fa-exclamation-circle mr-2"></i>${error.message}</span>`;
            }
        }
    }

    renderJournalAnalysis(result) {
        const container = document.getElementById('journal-analysis');
        if (!container) return;
        
        container.innerHTML = `
            <div class="bg-gray-800 rounded-lg p-6 border border-gray-700 mt-4">
                <h4 class="text-lg font-bold text-white mb-4">Analysis Results</h4>
                <div class="grid grid-cols-3 gap-4">
                    <div class="text-center">
                        <div class="text-2xl font-bold text-white">${result.total_trades || 0}</div>
                        <div class="text-sm text-gray-400">Total Trades</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold ${result.profit_factor > 1 ? 'text-green-400' : 'text-red-400'}">${result.profit_factor?.toFixed(2) || '0.00'}</div>
                        <div class="text-sm text-gray-400">Profit Factor</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold text-white">${result.win_rate || 0}%</div>
                        <div class="text-sm text-gray-400">Win Rate</div>
                    </div>
                </div>
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
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <div class="text-3xl font-bold text-white">${stats.total_users || 0}</div>
                        <div class="text-sm text-gray-400">Total Users</div>
                    </div>
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <div class="text-3xl font-bold text-white">${stats.active_signals || 0}</div>
                        <div class="text-sm text-gray-400">Active Signals</div>
                    </div>
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <div class="text-3xl font-bold text-white">${stats.new_today || 0}</div>
                        <div class="text-sm text-gray-400">New Today</div>
                    </div>
                </div>
            `;
        } catch (error) {
            this.showError(container, error.message);
        }
    }

    showSkeleton(container, count = 3) {
        container.innerHTML = Array(count).fill(0).map(() => `
            <div class="animate-pulse bg-gray-800 rounded-lg p-4 border border-gray-700 h-24"></div>
        `).join('');
    }

    showError(container, message, retryCallback = null) {
        container.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-exclamation-triangle text-red-400 text-4xl mb-4"></i>
                <p class="text-gray-400 mb-4">${message}</p>
                ${retryCallback ? `<button onclick="dashboard.retryLoad()" class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg">Retry</button>` : ''}
            </div>
        `;
        if (retryCallback) this.retryCallback = retryCallback;
    }

    retryLoad() {
        if (this.retryCallback) this.retryCallback();
    }

    initFeatureCarousel() {
        const carousel = document.getElementById('feature-carousel');
        if (!carousel) return;
        
        const slides = [
            { icon: 'fa-satellite-dish', title: 'Trading Signals', desc: 'AI-powered signals with high accuracy', color: 'from-purple-600 to-blue-600', section: 'signals' },
            { icon: 'fa-book', title: 'Trading Journal', desc: 'Track and analyze your trading performance', color: 'from-green-600 to-teal-600', section: 'journal' },
            { icon: 'fa-chart-line', title: 'Chart Analysis', desc: 'Advanced technical analysis tools', color: 'from-orange-600 to-red-600', section: 'analysis' },
            { icon: 'fa-robot', title: 'AI Mentor', desc: 'Personalized trading coaching', color: 'from-pink-600 to-purple-600', section: 'mentor' },
            { icon: 'fa-graduation-cap', title: 'Courses', desc: 'Learn from beginner to advanced', color: 'from-blue-600 to-cyan-600', section: 'courses' },
            { icon: 'fa-video', title: 'Webinars', desc: 'Live trading sessions and Q&A', color: 'from-indigo-600 to-purple-600', section: 'webinars' },
            { icon: 'fa-newspaper', title: 'Trading Blog', desc: 'Latest market insights and strategies', color: 'from-yellow-600 to-orange-600', section: 'blog' }
        ];
        
        let currentSlide = 0;
        
        const renderSlides = () => {
            const slide = slides[currentSlide];
            carousel.innerHTML = `
                <div class="bg-gradient-to-r ${slide.color} rounded-xl p-6 md:p-8 text-white cursor-pointer" onclick="dashboard.navigate('${slide.section}')">
                    <div class="flex items-start justify-between">
                        <div>
                            <i class="fas ${slide.icon} text-3xl mb-3 opacity-80"></i>
                            <h3 class="text-xl font-bold mb-1">${slide.title}</h3>
                            <p class="text-white/80 text-sm">${slide.desc}</p>
                        </div>
                        <i class="fas fa-arrow-right text-white/50"></i>
                    </div>
                </div>
            `;
        };
        
        const nextSlide = () => {
            currentSlide = (currentSlide + 1) % slides.length;
            renderSlides();
        };
        
        document.getElementById('carousel-next')?.addEventListener('click', nextSlide);
        document.getElementById('carousel-prev')?.addEventListener('click', () => {
            currentSlide = (currentSlide - 1 + slides.length) % slides.length;
            renderSlides();
        });
        
        setInterval(nextSlide, 5000);
        renderSlides();
    }

    logout() {
        localStorage.removeItem('pipways_token');
        localStorage.removeItem('pipways_user');
        window.location.href = '/';
    }
}

// Initialize dashboard
const dashboard = new DashboardController();
