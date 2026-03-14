/**
 * Pipways Dashboard Controller
 * Handles all dashboard functionality with error boundaries
 */
class DashboardController {
    constructor() {
        this.user = null;
        this.currentSection = 'dashboard';
        this.init();
    }

    init() {
        this.checkAuth();
        this.setupNavigation();
        this.setupMobileMenu();
        this.loadUserData();
        this.renderAdminMenu();
        this.initFeatureCarousel();
        
        // Load initial section
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
            console.error('Failed to parse user data');
            window.location.href = '/';
        }
    }

    updateUserDisplay() {
        const userNameEl = document.getElementById('user-name');
        const userEmailEl = document.getElementById('user-email');
        
        if (userNameEl) userNameEl.textContent = this.user.full_name || this.user.email;
        if (userEmailEl) userEmailEl.textContent = this.user.email;
    }

    setupNavigation() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.currentTarget.dataset.section;
                this.navigate(section);
            });
        });
    }

    setupMobileMenu() {
        const mobileMenuBtn = document.getElementById('mobile-menu-btn');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        
        if (mobileMenuBtn) {
            mobileMenuBtn.addEventListener('click', () => {
                sidebar.classList.toggle('-translate-x-full');
                overlay.classList.toggle('hidden');
            });
        }
        
        if (overlay) {
            overlay.addEventListener('click', () => {
                sidebar.classList.add('-translate-x-full');
                overlay.classList.add('hidden');
            });
        }
    }

    renderAdminMenu() {
        const adminMenu = document.getElementById('admin-menu');
        if (!adminMenu) return;
        
        // Check admin status
        const isAdmin = this.user && (this.user.is_admin === true || this.user.role === 'admin');
        
        if (isAdmin) {
            adminMenu.classList.remove('hidden');
        } else {
            adminMenu.classList.add('hidden');
        }
    }

    navigate(section) {
        this.currentSection = section;
        
        // Update UI
        document.querySelectorAll('.nav-link').forEach(el => {
            el.classList.remove('bg-purple-600', 'text-white');
            el.classList.add('text-gray-300', 'hover:bg-gray-700');
        });
        
        const activeLink = document.querySelector(`[data-section="${section}"]`);
        if (activeLink) {
            activeLink.classList.add('bg-purple-600', 'text-white');
            activeLink.classList.remove('text-gray-300', 'hover:bg-gray-700');
        }
        
        // Hide all sections
        document.querySelectorAll('.section').forEach(el => el.classList.add('hidden'));
        
        // Show target section
        const targetSection = document.getElementById(`section-${section}`);
        if (targetSection) {
            targetSection.classList.remove('hidden');
            this.loadSectionData(section);
        }
        
        // Close mobile menu
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        if (sidebar && overlay) {
            sidebar.classList.add('-translate-x-full');
            overlay.classList.add('hidden');
        }
    }

    async loadSectionData(section) {
        switch(section) {
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
        }
    }

    // FIXED: Loading signals with error handling
    async loadSignals() {
        const container = document.getElementById('signals-container');
        if (!container) return;
        
        this.showSkeleton(container, 3);
        
        try {
            const signals = await api.getSignals();
            this.renderSignals(signals || []);
        } catch (error) {
            this.showError(container, error.message, () => this.loadSignals());
        }
    }

    renderSignals(signals) {
        const container = document.getElementById('signals-container');
        if (!container) return;
        
        if (!signals || signals.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12 text-gray-400">
                    <i class="fas fa-satellite-dish text-4xl mb-4"></i>
                    <p>No active signals available</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = signals.map(signal => `
            <div class="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-purple-500 transition-all">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="text-xl font-bold text-white">${signal.symbol}</h3>
                        <span class="text-sm ${signal.direction === 'BUY' ? 'text-green-400' : 'text-red-400'}">
                            ${signal.direction} @ ${signal.entry_price}
                        </span>
                    </div>
                    <span class="bg-purple-900 text-purple-200 px-3 py-1 rounded-full text-sm">
                        ${signal.timeframe || '1H'}
                    </span>
                </div>
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <span class="text-gray-400">Stop Loss</span>
                        <p class="text-red-400 font-mono">${signal.stop_loss}</p>
                    </div>
                    <div>
                        <span class="text-gray-400">Take Profit</span>
                        <p class="text-green-400 font-mono">${signal.take_profit}</p>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // FIXED: Loading courses with all levels including Intermediate
    async loadCourses() {
        const container = document.getElementById('courses-container');
        if (!container) return;
        
        this.showSkeleton(container, 4);
        
        try {
            const courses = await api.getCourses();
            this.allCourses = courses || [];
            this.renderCourses(this.allCourses);
            this.setupCourseFilters();
        } catch (error) {
            this.showError(container, error.message, () => this.loadCourses());
        }
    }

    setupCourseFilters() {
        const filterContainer = document.getElementById('course-filters');
        if (!filterContainer) return;
        
        // FIXED: Added Intermediate filter
        const levels = ['All', 'Beginner', 'Intermediate', 'Advanced'];
        
        filterContainer.innerHTML = levels.map(level => `
            <button onclick="dashboard.filterCourses('${level}')" 
                    class="filter-btn px-4 py-2 rounded-full text-sm font-medium transition-all ${level === 'All' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}"
                    data-level="${level}">
                ${level}
            </button>
        `).join('');
    }

    filterCourses(level) {
        // Update button states
        document.querySelectorAll('.filter-btn').forEach(btn => {
            if (btn.dataset.level === level) {
                btn.classList.add('bg-purple-600', 'text-white');
                btn.classList.remove('bg-gray-700', 'text-gray-300');
            } else {
                btn.classList.remove('bg-purple-600', 'text-white');
                btn.classList.add('bg-gray-700', 'text-gray-300');
            }
        });
        
        // Filter data
        if (level === 'All') {
            this.renderCourses(this.allCourses);
        } else {
            const filtered = this.allCourses.filter(c => 
                c.level && c.level.toLowerCase() === level.toLowerCase()
            );
            this.renderCourses(filtered);
        }
    }

    renderCourses(courses) {
        const container = document.getElementById('courses-container');
        if (!container) return;
        
        if (!courses || courses.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12 text-gray-400">
                    <i class="fas fa-graduation-cap text-4xl mb-4"></i>
                    <p>No courses available for this level</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = courses.map(course => `
            <div class="bg-gray-800 rounded-lg overflow-hidden border border-gray-700 hover:border-purple-500 transition-all group">
                <div class="h-48 bg-gradient-to-br from-purple-900 to-blue-900 relative">
                    ${course.thumbnail_url ? `<img src="${course.thumbnail_url}" class="w-full h-full object-cover">` : ''}
                    <span class="absolute top-4 right-4 bg-black/50 backdrop-blur px-3 py-1 rounded-full text-xs text-white">
                        ${course.level || 'Beginner'}
                    </span>
                </div>
                <div class="p-6">
                    <h3 class="text-lg font-bold text-white mb-2 group-hover:text-purple-400 transition-colors">${course.title}</h3>
                    <p class="text-gray-400 text-sm mb-4 line-clamp-2">${course.description || ''}</p>
                    <div class="flex justify-between items-center">
                        <span class="text-sm text-gray-500">${course.lesson_count || 0} lessons</span>
                        <button class="text-purple-400 hover:text-purple-300 text-sm font-medium">Start Learning →</button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // FIXED: Webinars loading
    async loadWebinars() {
        const container = document.getElementById('webinars-container');
        if (!container) return;
        
        this.showSkeleton(container, 2);
        
        try {
            const webinars = await api.getWebinars();
            this.renderWebinars(webinars || []);
        } catch (error) {
            this.showError(container, error.message, () => this.loadWebinars());
        }
    }

    renderWebinars(webinars) {
        const container = document.getElementById('webinars-container');
        if (!container) return;
        
        if (!webinars || webinars.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12 text-gray-400">
                    <i class="fas fa-video text-4xl mb-4"></i>
                    <p>No upcoming webinars</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = webinars.map(webinar => `
            <div class="bg-gray-800 rounded-lg p-6 border border-gray-700 flex flex-col md:flex-row gap-6">
                <div class="flex-1">
                    <h3 class="text-xl font-bold text-white mb-2">${webinar.title}</h3>
                    <p class="text-gray-400 mb-4">${webinar.description || ''}</p>
                    <div class="flex items-center gap-4 text-sm text-gray-500">
                        <span><i class="fas fa-calendar mr-2"></i>${new Date(webinar.scheduled_at).toLocaleDateString()}</span>
                        <span><i class="fas fa-user mr-2"></i>${webinar.presenter || 'TBA'}</span>
                    </div>
                </div>
                <div class="flex items-center">
                    <button class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg transition-colors">
                        Register
                    </button>
                </div>
            </div>
        `).join('');
    }

    // FIXED: Blog loading
    async loadBlog() {
        const container = document.getElementById('blog-container');
        if (!container) return;
        
        this.showSkeleton(container, 3);
        
        try {
            const posts = await api.getBlogPosts();
            this.renderBlogPosts(posts || []);
        } catch (error) {
            this.showError(container, error.message, () => this.loadBlog());
        }
    }

    renderBlogPosts(posts) {
        const container = document.getElementById('blog-container');
        if (!container) return;
        
        if (!posts || posts.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12 text-gray-400">
                    <i class="fas fa-newspaper text-4xl mb-4"></i>
                    <p>No articles available</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = posts.map(post => `
            <article class="bg-gray-800 rounded-lg overflow-hidden border border-gray-700 hover:border-purple-500 transition-all">
                <div class="p-6">
                    <div class="flex items-center gap-2 mb-3">
                        <span class="text-xs text-purple-400 font-medium uppercase tracking-wide">${post.category || 'General'}</span>
                        <span class="text-gray-600">•</span>
                        <span class="text-xs text-gray-500">${post.read_time || '5 min'}</span>
                    </div>
                    <h3 class="text-xl font-bold text-white mb-2 hover:text-purple-400 cursor-pointer">${post.title}</h3>
                    <p class="text-gray-400 text-sm mb-4 line-clamp-3">${post.excerpt || post.content?.substring(0, 150) + '...' || ''}</p>
                    <a href="/blog/${post.slug}" class="text-purple-400 hover:text-purple-300 text-sm font-medium inline-flex items-center">
                        Read Article <i class="fas fa-arrow-right ml-2"></i>
                    </a>
                </div>
            </article>
        `).join('');
    }

    // FIXED: Trading Journal Upload with multipart/form-data
    setupJournalUpload() {
        const dropZone = document.getElementById('journal-dropzone');
        const fileInput = document.getElementById('journal-file-input');
        const statusEl = document.getElementById('upload-status');
        
        if (!dropZone || !fileInput) return;
        
        // Click to upload
        dropZone.addEventListener('click', () => fileInput.click());
        
        // File selection
        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (file) await this.handleJournalUpload(file);
        });
        
        // Drag and drop
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
    }

    async handleJournalUpload(file) {
        const statusEl = document.getElementById('upload-status');
        const allowedTypes = [
            'text/csv',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/pdf',
            'text/html',
            'image/png',
            'image/jpeg'
        ];
        
        // Validate file type
        const isAllowed = allowedTypes.some(type => file.type === type) || 
                         file.name.endsWith('.csv') || 
                         file.name.endsWith('.xlsx') || 
                         file.name.endsWith('.xls') ||
                         file.name.endsWith('.html') ||
                         file.name.endsWith('.htm');
        
        if (!isAllowed) {
            this.showUploadStatus('Invalid file type. Supported: CSV, Excel, PDF, HTML, Images', 'error');
            return;
        }
        
        this.showUploadStatus('Analyzing your trading data...', 'loading');
        
        try {
            const result = await api.analyzeJournal(file);
            this.showUploadStatus(`Analysis complete! Found ${result.trades?.length || 0} trades.`, 'success');
            this.renderJournalAnalysis(result);
        } catch (error) {
            this.showUploadStatus(error.message || 'Upload failed', 'error');
        }
    }

    showUploadStatus(message, type) {
        const el = document.getElementById('upload-status');
        if (!el) return;
        
        const colors = {
            loading: 'text-blue-400',
            success: 'text-green-400',
            error: 'text-red-400'
        };
        
        const icons = {
            loading: '<i class="fas fa-spinner fa-spin mr-2"></i>',
            success: '<i class="fas fa-check-circle mr-2"></i>',
            error: '<i class="fas fa-exclamation-circle mr-2"></i>'
        };
        
        el.innerHTML = `${icons[type] || ''}<span class="${colors[type] || ''}">${message}</span>`;
        el.classList.remove('hidden');
    }

    renderJournalAnalysis(result) {
        const container = document.getElementById('journal-analysis');
        if (!container) return;
        
        container.innerHTML = `
            <div class="bg-gray-800 rounded-lg p-6 border border-gray-700 mt-6">
                <h4 class="text-lg font-bold text-white mb-4">Analysis Results</h4>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="bg-gray-700/50 p-4 rounded-lg">
                        <div class="text-2xl font-bold text-white">${result.total_trades || 0}</div>
                        <div class="text-sm text-gray-400">Total Trades</div>
                    </div>
                    <div class="bg-gray-700/50 p-4 rounded-lg">
                        <div class="text-2xl font-bold ${result.profit_factor > 1 ? 'text-green-400' : 'text-red-400'}">
                            ${result.profit_factor?.toFixed(2) || '0.00'}
                        </div>
                        <div class="text-sm text-gray-400">Profit Factor</div>
                    </div>
                    <div class="bg-gray-700/50 p-4 rounded-lg">
                        <div class="text-2xl font-bold text-white">${result.win_rate || 0}%</div>
                        <div class="text-sm text-gray-400">Win Rate</div>
                    </div>
                </div>
            </div>
        `;
        container.classList.remove('hidden');
    }

    // Admin data loading
    async loadAdminData() {
        const container = document.getElementById('admin-container');
        if (!container) return;
        
        try {
            const stats = await api.getAdminStats();
            this.renderAdminStats(stats);
        } catch (error) {
            this.showError(container, error.message);
        }
    }

    renderAdminStats(stats) {
        const container = document.getElementById('admin-container');
        if (!container) return;
        
        container.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                    <h3 class="text-gray-400 text-sm mb-1">Total Users</h3>
                    <p class="text-3xl font-bold text-white">${stats.total_users || 0}</p>
                </div>
                <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                    <h3 class="text-gray-400 text-sm mb-1">Active Signals</h3>
                    <p class="text-3xl font-bold text-white">${stats.active_signals || 0}</p>
                </div>
                <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                    <h3 class="text-gray-400 text-sm mb-1">New Today</h3>
                    <p class="text-3xl font-bold text-white">${stats.new_today || 0}</p>
                </div>
            </div>
        `;
    }

    // Utility: Skeleton loader
    showSkeleton(container, count = 3) {
        const skeleton = `
            <div class="animate-pulse space-y-4">
                ${Array(count).fill(0).map(() => `
                    <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
                        <div class="h-4 bg-gray-700 rounded w-3/4 mb-4"></div>
                        <div class="h-3 bg-gray-700 rounded w-1/2"></div>
                    </div>
                `).join('')}
            </div>
        `;
        container.innerHTML = skeleton;
    }

    // Utility: Error display with retry
    showError(container, message, retryCallback = null) {
        container.innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-exclamation-triangle text-4xl text-red-400 mb-4"></i>
                <p class="text-gray-400 mb-4">${message}</p>
                ${retryCallback ? `
                    <button onclick="dashboard.retryLoad()" class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg transition-colors">
                        <i class="fas fa-redo mr-2"></i>Retry
                    </button>
                ` : ''}
            </div>
        `;
        
        if (retryCallback) {
            this.retryCallback = retryCallback;
        }
    }

    retryLoad() {
        if (this.retryCallback) {
            this.retryCallback();
        }
    }

    // Feature Carousel
    initFeatureCarousel() {
        const carousel = document.getElementById('feature-carousel');
        if (!carousel) return;
        
        const slides = [
            {
                icon: 'fa-satellite-dish',
                title: 'Trading Signals',
                desc: 'AI-powered trading signals with high accuracy',
                link: '#signals',
                color: 'from-purple-600 to-blue-600'
            },
            {
                icon: 'fa-book',
                title: 'Trading Journal',
                desc: 'Track and analyze your trading performance',
                link: '#journal',
                color: 'from-green-600 to-teal-600'
            },
            {
                icon: 'fa-chart-line',
                title: 'Chart Analysis',
                desc: 'Advanced technical analysis tools',
                link: '#analysis',
                color: 'from-orange-600 to-red-600'
            },
            {
                icon: 'fa-robot',
                title: 'AI Mentor',
                desc: 'Personalized trading coaching',
                link: '#mentor',
                color: 'from-pink-600 to-purple-600'
            },
            {
                icon: 'fa-graduation-cap',
                title: 'Courses',
                desc: 'Learn from beginner to advanced',
                link: '#courses',
                color: 'from-blue-600 to-cyan-600'
            },
            {
                icon: 'fa-video',
                title: 'Webinars',
                desc: 'Live trading sessions and Q&A',
                link: '#webinars',
                color: 'from-indigo-600 to-purple-600'
            },
            {
                icon: 'fa-newspaper',
                title: 'Trading Blog',
                desc: 'Latest market insights and strategies',
                link: '#blog',
                color: 'from-yellow-600 to-orange-600'
            }
        ];
        
        let currentSlide = 0;
        
        const renderSlides = () => {
            carousel.innerHTML = slides.map((slide, idx) => `
                <div class="carousel-slide ${idx === currentSlide ? 'active' : 'hidden'} w-full flex-shrink-0 px-4">
                    <div class="bg-gradient-to-r ${slide.color} rounded-2xl p-8 md:p-12 text-white relative overflow-hidden group cursor-pointer" onclick="dashboard.navigate('${slide.link.replace('#', '')}')">
                        <div class="relative z-10">
                            <i class="fas ${slide.icon} text-4xl md:text-6xl mb-4 opacity-80 group-hover:scale-110 transition-transform"></i>
                            <h3 class="text-2xl md:text-3xl font-bold mb-2">${slide.title}</h3>
                            <p class="text-white/80 mb-6 max-w-md">${slide.desc}</p>
                            <span class="inline-flex items-center text-sm font-semibold bg-white/20 px-4 py-2 rounded-full backdrop-blur">
                                Explore <i class="fas fa-arrow-right ml-2 group-hover:translate-x-1 transition-transform"></i>
                            </span>
                        </div>
                        <div class="absolute right-0 top-0 w-1/2 h-full opacity-10 transform translate-x-1/4">
                            <i class="fas ${slide.icon} text-[200px]"></i>
                        </div>
                    </div>
                </div>
            `).join('');
        };
        
        const nextSlide = () => {
            currentSlide = (currentSlide + 1) % slides.length;
            renderSlides();
        };
        
        const prevSlide = () => {
            currentSlide = (currentSlide - 1 + slides.length) % slides.length;
            renderSlides();
        };
        
        // Controls
        const prevBtn = document.getElementById('carousel-prev');
        const nextBtn = document.getElementById('carousel-next');
        
        if (prevBtn) prevBtn.addEventListener('click', prevSlide);
        if (nextBtn) nextBtn.addEventListener('click', nextSlide);
        
        // Auto-advance
        setInterval(nextSlide, 5000);
        
        // Touch support
        let touchStartX = 0;
        carousel.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        });
        
        carousel.addEventListener('touchend', (e) => {
            const touchEndX = e.changedTouches[0].screenX;
            if (touchStartX - touchEndX > 50) nextSlide();
            if (touchEndX - touchStartX > 50) prevSlide();
        });
        
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
