/**
 * UI Utilities
 */
const ui = {
    init() {
        this.setupRouting();
        this.loadInitialView();
    },

    setupRouting() {
        window.addEventListener('popstate', () => this.handleRoute());
        document.addEventListener('click', (e) => {
            if (e.target.matches('a[href^="/"]')) {
                e.preventDefault();
                const href = e.target.getAttribute('href');
                window.history.pushState({}, '', href);
                this.handleRoute();
            }
        });
    },

    handleRoute() {
        const path = window.location.pathname;
        const main = document.getElementById('main-content');

        switch(path) {
            case '/':
            case '/home':
                this.renderHome(main);
                break;
            case '/signals':
                signals.loadSignals(main);
                break;
            case '/blog':
                blog.loadPosts(main);
                break;
            case '/courses':
                courses.loadCourses(main);
                break;
            case '/webinars':
                webinars.loadWebinars(main);
                break;
            case '/ai-tools':
                ai.loadAITools(main);
                break;
            case '/admin':
                admin.loadDashboard(main);
                break;
            default:
                if (path.startsWith('/blog/')) {
                    const postId = path.split('/')[2];
                    blog.loadPostDetail(main, postId);
                } else {
                    this.renderHome(main);
                }
        }
    },

    loadInitialView() {
        this.handleRoute();
    },

    renderHome(container) {
        container.innerHTML = `
            <div class="hero">
                <h1>Welcome to Pipways</h1>
                <p>Professional trading signals, education, and AI-powered analysis</p>
                <div class="hero-actions">
                    <button class="primary" onclick="window.location='/signals'">View Signals</button>
                    <button class="secondary" onclick="window.location='/courses'">Start Learning</button>
                </div>
            </div>
            <div class="grid" style="margin-top: 2rem;">
                <div class="card">
                    <h3>📈 Trading Signals</h3>
                    <p>Get real-time buy/sell signals with entry, stop loss, and take profit levels.</p>
                    <a href="/signals">View Signals →</a>
                </div>
                <div class="card">
                    <h3>🎓 Courses</h3>
                    <p>Learn from beginner to advanced trading strategies.</p>
                    <a href="/courses">Browse Courses →</a>
                </div>
                <div class="card">
                    <h3>🤖 AI Tools</h3>
                    <p>Analyze your performance and get AI trading mentor guidance.</p>
                    <a href="/ai-tools">Try AI Tools →</a>
                </div>
            </div>
        `;
    },

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.style.borderLeftColor = type === 'error' ? 'var(--danger)' : 
                                      type === 'success' ? 'var(--success)' : 'var(--primary)';
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 5000);
    },

    formatDate(dateStr) {
        if (!dateStr) return 'N/A';
        return new Date(dateStr).toLocaleString();
    },

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
