const Router = {
    routes: {
        '/': 'home',
        '/signals': 'signals',
        '/courses': 'courses',
        '/blog': 'blog',
        '/blog/:slug': 'blogPost',
        '/webinars': 'webinars',
        '/dashboard': 'dashboard',
        '/admin': 'admin',
        '/risk-calculator': 'riskCalculator',
        '/ai/mentor': 'aiMentor',
        '/ai/chart-analysis': 'chartAnalysis',
        '/ai/performance': 'performance',
        '/ai/sentiment': 'sentiment'
    },

    currentPage: null,

    init() {
        window.addEventListener('hashchange', () => this.handleRoute());
        window.addEventListener('load', () => this.handleRoute());
    },

    handleRoute() {
        const hash = window.location.hash.slice(1) || '/';
        const app = document.getElementById('app');

        const [path, queryString] = hash.split('?');

        let route = this.routes[path];
        let slug = null;

        if (!route) {
            const parts = path.split('/');
            if (parts.length >= 3 && parts[1] === 'blog') {
                route = 'blogPost';
                slug = parts[2];
            } else {
                route = 'notFound';
            }
        }

        if (typeof UI !== 'undefined') UI.setActiveNav(path);

        if (route === 'dashboard' && !this.checkAuth()) return;
        if (route === 'admin' && !this.checkAdmin()) return;
        if (route.startsWith('ai') && !this.checkAuth()) return;

        Store.setState('currentPage', route);
        this.currentPage = route;

        try {
            switch(route) {
                case 'home':
                    this.renderHome(app);
                    break;
                case 'signals':
                    SignalsPage.render(app);
                    break;
                case 'courses':
                    CoursesPage.render(app);
                    break;
                case 'blog':
                    BlogPage.render(app);
                    break;
                case 'blogPost':
                    if (slug) BlogPage.renderPost(app, slug);
                    else this.renderNotFound(app);
                    break;
                case 'webinars':
                    WebinarsPage.render(app);
                    break;
                case 'dashboard':
                    DashboardPage.render(app);
                    break;
                case 'admin':
                    AdminPage.render(app);
                    break;
                case 'riskCalculator':
                    RiskCalculator.render(app);
                    break;
                case 'aiMentor':
                    AIMentorPage.render(app);
                    break;
                case 'chartAnalysis':
                    ChartAnalysisPage.render(app);
                    break;
                case 'performance':
                    PerformancePage.render(app);
                    break;
                case 'sentiment':
                    this.renderSentiment(app);
                    break;
                default:
                    this.renderNotFound(app);
            }
        } catch (error) {
            console.error('Route error:', error);
            app.innerHTML = `<div class="error">Failed to load page: ${error.message}</div>`;
        }
    },

    checkAuth() {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/index.html';
            return false;
        }
        return true;
    },

    checkAdmin() {
        if (!this.checkAuth()) return false;
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        if (!user.is_admin && user.role !== 'admin' && user.role !== 'moderator') {
            window.location.hash = '#/dashboard';
            alert('Admin access required');
            return false;
        }
        return true;
    },

    renderHome(container) {
        container.innerHTML = `
            <div class="hero" style="background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%); color: white; padding: 4rem; border-radius: 1rem; text-align: center; margin-bottom: 2rem;">
                <h1 style="font-size: 2.5rem; margin-bottom: 1rem;">Professional Trading Signals & Education</h1>
                <p style="font-size: 1.25rem; margin-bottom: 2rem; opacity: 0.9;">Join thousands of successful traders using our AI-powered signals and expert courses.</p>
                <div style="display: flex; gap: 1rem; justify-content: center;">
                    <button class="btn btn-lg" onclick="window.location.hash='#/signals'" style="background: #10b981; color: white; padding: 1rem 2rem; border: none; border-radius: 0.5rem; cursor: pointer; font-size: 1.125rem;">View Signals</button>
                    <button class="btn btn-lg" onclick="window.location.hash='#/courses'" style="background: rgba(255,255,255,0.2); color: white; padding: 1rem 2rem; border: 2px solid white; border-radius: 0.5rem; cursor: pointer; font-size: 1.125rem;">Browse Courses</button>
                </div>
            </div>
            <div class="features" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem;">
                <div class="feature-card" style="background: white; padding: 2rem; border-radius: 0.5rem; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                    <h3>Live Signals</h3>
                    <p style="color: #64748b; margin-top: 0.5rem;">Real-time trading signals with high accuracy rates</p>
                </div>
                <div class="feature-card" style="background: white; padding: 2rem; border-radius: 0.5rem; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📚</div>
                    <h3>Expert Courses</h3>
                    <p style="color: #64748b; margin-top: 0.5rem;">Learn from professional traders with proven strategies</p>
                </div>
                <div class="feature-card" style="background: white; padding: 2rem; border-radius: 0.5rem; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🎓</div>
                    <h3>Live Webinars</h3>
                    <p style="color: #64748b; margin-top: 0.5rem;">Weekly training sessions and market analysis</p>
                </div>
            </div>
        `;
    },

    renderSentiment(container) {
        container.innerHTML = `
            <div class="page-header">
                <h1>📊 Market Sentiment</h1>
                <p>Fear & Greed Index and Social Sentiment Analysis</p>
            </div>
            <div style="background: white; padding: 2rem; border-radius: 0.5rem; text-align: center;">
                <p>Enter a symbol to analyze market sentiment.</p>
                <input type="text" id="sentimentSymbol" placeholder="EURUSD" style="padding: 0.5rem; margin: 1rem;">
                <button onclick="Router.loadSentiment()" class="btn btn-primary">Analyze</button>
                <div id="sentimentResult" style="margin-top: 2rem;"></div>
            </div>
        `;
    },

    async loadSentiment() {
        const symbol = document.getElementById('sentimentSymbol').value || 'EURUSD';
        try {
            const data = await API.getSentiment(symbol);
            document.getElementById('sentimentResult').innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 2rem;">
                    <div style="background: #f0fdf4; padding: 1rem; border-radius: 0.5rem;">
                        <h4>Overall Sentiment</h4>
                        <p style="font-size: 1.5rem; color: #166534; text-transform: capitalize;">${data.overall_sentiment}</p>
                    </div>
                    <div style="background: #eff6ff; padding: 1rem; border-radius: 0.5rem;">
                        <h4>Sentiment Score</h4>
                        <p style="font-size: 1.5rem; color: #1e40af;">${(data.sentiment_score * 100).toFixed(1)}%</p>
                    </div>
                    <div style="background: #fef3c7; padding: 1rem; border-radius: 0.5rem;">
                        <h4>Fear & Greed</h4>
                        <p style="font-size: 1.5rem; color: #92400e;">${data.fear_greed_index}</p>
                    </div>
                </div>
            `;
        } catch (e) {
            document.getElementById('sentimentResult').innerHTML = 'Failed to load sentiment';
        }
    },

    renderNotFound(container) {
        container.innerHTML = `
            <div class="text-center" style="padding: 4rem 1rem; text-align: center;">
                <h1 style="font-size: 4rem; color: #e5e7eb;">404</h1>
                <p style="color: #6b7280; margin: 1rem 0;">Page not found</p>
                <a href="#/" class="btn btn-primary" style="background: #3b82f6; color: white; padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 0.375rem;">Go Home</a>
            </div>
        `;
    },

    go(path) {
        window.location.hash = path;
    }
};
