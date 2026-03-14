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
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        this.checkAuth();
        this.setupNavigation();
        this.setupMobileMenu();
        this.renderAdminMenu();
        this.initCarousel();
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
        const headerUserEl = document.getElementById('header-user-name');
        
        if (userNameEl) userNameEl.textContent = this.user?.full_name || this.user?.email || 'User';
        if (userEmailEl) userEmailEl.textContent = this.user?.email || '';
        if (headerUserEl) headerUserEl.textContent = this.user?.full_name || this.user?.email || 'Trader';
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
        // Update active nav
        document.querySelectorAll('.nav-link').forEach(el => {
            el.classList.remove('bg-purple-600', 'text-white');
            el.classList.add('text-gray-300');
        });
        
        const activeLink = document.querySelector(`[data-section="${section}"]`);
        if (activeLink) {
            activeLink.classList.add('bg-purple-600', 'text-white');
            activeLink.classList.remove('text-gray-300');
        }

        // Hide all sections
        document.querySelectorAll('.section').forEach(el => el.classList.add('hidden'));
        
        // Show target
        const target = document.getElementById(`section-${section}`);
        if (target) {
            target.classList.remove('hidden');
            this.loadSectionData(section);
        }

        // Update title
        const titles = {
            'dashboard': 'Dashboard',
            'signals': 'Trading Signals',
            'journal': 'Trading Journal',
            'courses': 'Trading Courses',
            'webinars': 'Webinars',
            'blog': 'Trading Blog',
            'admin': 'Admin Dashboard'
        };
        const titleEl = document.getElementById('page-title');
        if (titleEl) titleEl.textContent = titles[section] || 'Dashboard';

        // Close mobile menu
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
                case 'journal': this.setupJournal(); break;
                case 'admin': await this.loadAdmin(); break;
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
            
            if (signals.length === 0) {
                container.innerHTML = '<div class="text-center py-8 text-gray-500">No active signals available</div>';
                return;
            }
            
            container.innerHTML = signals.map(s => `
                <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
                    <div class="flex justify-between items-start mb-2">
                        <h4 class="font-bold text-white">${s.symbol}</h4>
                        <span class="text-xs ${s.direction === 'BUY' ? 'text-green-400' : 'text-red-400'}">${s.direction}</span>
                    </div>
                    <div class="text-sm text-gray-400 space-y-1">
                        <div>Entry: <span class="text-white">${s.entry_price}</span></div>
                        <div>SL: <span class="text-red-400">${s.stop_loss}</span> / TP: <span class="text-green-400">${s.take_profit}</span></div>
                    </div>
                </div>
            `).join('');
        } catch (err) {
            this.showError(container, err.message, () => this.loadSignals());
        }
    }

    async loadCourses() {
        const container = document.getElementById('courses-container');
        const filters = document.getElementById('course-filters');
        if (!container) return;
        
        this.showSkeleton(container, 4);
        
        try {
            const data = await api.getCourses();
            this.allCourses = Array.isArray(data) ? data : (data.courses || []);
            
            // Setup filters
            if (filters) {
                const levels = ['All', 'Beginner', 'Intermediate', 'Advanced'];
                filters.innerHTML = levels.map(l => `
                    <button onclick="dashboard.filterCourses('${l}')" class="filter-btn px-4 py-2 rounded-full text-sm ${l === 'All' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300'}" data-level="${l}">${l}</button>
                `).join('');
            }
            
            this.filterCourses('All');
        } catch (err) {
            this.showError(container, err.message, () => this.loadCourses());
        }
    }

    filterCourses(level) {
        document.querySelectorAll('.filter-btn').forEach(btn => {
            const isActive = btn.dataset.level === level;
            btn.className = `filter-btn px-4 py-2 rounded-full text-sm ${isActive ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300'}`;
        });
        
        const filtered = level === 'All' ? this.allCourses : this.allCourses.filter(c => 
            c.level?.toLowerCase() === level.toLowerCase()
        );
        
        const container = document.getElementById('courses-container');
        if (filtered.length === 0) {
            container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">No courses found for this level</div>';
            return;
        }
        
        container.innerHTML = filtered.map(c => `
            <div class="bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
                <div class="h-40 bg-gradient-to-br from-purple-900 to-blue-900"></div>
                <div class="p-4">
                    <div class="text-xs text-purple-400 mb-1">${c.level || 'Beginner'}</div>
                    <h4 class="font-bold text-white mb-2">${c.title}</h4>
                    <p class="text-sm text-gray-400 mb-3">${c.description || ''}</p>
                    <div class="text-xs text-gray-500">${c.lesson_count || 0} lessons</div>
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
            
            if (webinars.length === 0) {
                container.innerHTML = '<div class="text-center py-8 text-gray-500">No upcoming webinars</div>';
                return;
            }
            
            container.innerHTML = webinars.map(w => `
                <div class="bg-gray-800 rounded-lg p-4 border border-gray-700 flex justify-between items-center">
                    <div>
                        <h4 class="font-bold text-white">${w.title}</h4>
                        <p class="text-sm text-gray-400">${new Date(w.scheduled_at).toLocaleDateString()} • ${w.presenter || 'TBA'}</p>
                    </div>
                    <button class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded text-sm">Register</button>
                </div>
            `).join('');
        } catch (err) {
            this.showError(container, err.message, () => this.loadWebinars());
        }
    }

    async loadBlog() {
        const container = document.getElementById('blog-container');
        if (!container) return;
        
        this.showSkeleton(container, 3);
        
        try {
            const data = await api.getBlogPosts();
            const posts = Array.isArray(data) ? data : (data.posts || []);
            
            if (posts.length === 0) {
                container.innerHTML = '<div class="text-center py-8 text-gray-500">No articles available</div>';
                return;
            }
            
            container.innerHTML = posts.map(p => `
                <article class="bg-gray-800 rounded-lg p-4 border border-gray-700">
                    <div class="text-xs text-purple-400 mb-2">${p.category || 'General'}</div>
                    <h4 class="font-bold text-white mb-2">${p.title}</h4>
                    <p class="text-sm text-gray-400 line-clamp-3">${p.excerpt || p.content?.substring(0, 100) + '...' || ''}</p>
                </article>
            `).join('');
        } catch (err) {
            this.showError(container, err.message, () => this.loadBlog());
        }
    }

    setupJournal() {
        const dropzone = document.getElementById('journal-dropzone');
        const input = document.getElementById('journal-file-input');
        if (!dropzone || !input) return;
        
        dropzone.onclick = () => input.click();
        
        dropzone.ondragover = (e) => {
            e.preventDefault();
            dropzone.classList.add('border-purple-500', 'bg-purple-900/20');
        };
        
        dropzone.ondragleave = () => {
            dropzone.classList.remove('border-purple-500', 'bg-purple-900/20');
        };
        
        dropzone.ondrop = (e) => {
            e.preventDefault();
            dropzone.classList.remove('border-purple-500', 'bg-purple-900/20');
            if (e.dataTransfer.files[0]) this.uploadJournal(e.dataTransfer.files[0]);
        };
        
        input.onchange = (e) => {
            if (e.target.files[0]) this.uploadJournal(e.target.files[0]);
        };
    }

    async uploadJournal(file) {
        const status = document.getElementById('upload-status');
        if (status) {
            status.classList.remove('hidden');
            status.innerHTML = '<span class="text-blue-400"><i class="fas fa-spinner fa-spin mr-2"></i>Analyzing...</span>';
        }
        
        try {
            const result = await api.analyzeJournal(file);
            if (status) {
                status.innerHTML = `<span class="text-green-400"><i class="fas fa-check mr-2"></i>Analysis complete! Found ${result.trades?.length || 0} trades</span>`;
            }
        } catch (err) {
            if (status) {
                status.innerHTML = `<span class="text-red-400"><i class="fas fa-exclamation-circle mr-2"></i>${err.message}</span>`;
            }
        }
    }

    async loadAdmin() {
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
                </div>
            `;
        } catch (err) {
            container.innerHTML = `<div class="text-red-400">Error loading admin data: ${err.message}</div>`;
        }
    }

    initCarousel() {
        const carousel = document.getElementById('feature-carousel');
        if (!carousel) return;
        
        const slides = [
            { title: 'Trading Signals', desc: 'AI-powered signals', icon: 'fa-satellite-dish', color: 'from-purple-600 to-blue-600', link: 'signals' },
            { title: 'Trading Journal', desc: 'Track performance', icon: 'fa-book', color: 'from-green-600 to-teal-600', link: 'journal' },
            { title: 'Chart Analysis', desc: 'Technical tools', icon: 'fa-chart-line', color: 'from-orange-600 to-red-600', link: 'analysis' },
            { title: 'AI Mentor', desc: 'Personalized coaching', icon: 'fa-robot', color: 'from-pink-600 to-purple-600', link: 'mentor' },
            { title: 'Courses', desc: 'Learn to trade', icon: 'fa-graduation-cap', color: 'from-blue-600 to-cyan-600', link: 'courses' }
        ];
        
        let current = 0;
        
        const render = () => {
            const slide = slides[current];
            carousel.innerHTML = `
                <div class="bg-gradient-to-r ${slide.color} rounded-xl p-6 md:p-8 text-white cursor-pointer" onclick="dashboard.navigate('${slide.link}')">
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
        
        render();
        setInterval(() => {
            current = (current + 1) % slides.length;
            render();
        }, 5000);
    }

    showSkeleton(container, count) {
        container.innerHTML = Array(count).fill(0).map(() => `
            <div class="animate-pulse bg-gray-800 rounded-lg p-4 border border-gray-700 h-24"></div>
        `).join('');
    }

    showError(container, msg, retry) {
        container.innerHTML = `
            <div class="text-center py-8 text-red-400">
                <i class="fas fa-exclamation-triangle mb-2"></i>
                <p class="mb-3">${msg}</p>
                ${retry ? `<button onclick="dashboard.retryCallback()" class="bg-purple-600 text-white px-4 py-2 rounded text-sm">Retry</button>` : ''}
            </div>
        `;
        this.retryCallback = retry;
    }

    logout() {
        localStorage.removeItem('pipways_token');
        localStorage.removeItem('pipways_user');
        window.location.href = '/';
    }
}

// Initialize when script loads
let dashboard;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { dashboard = new DashboardController(); });
} else {
    dashboard = new DashboardController();
}
