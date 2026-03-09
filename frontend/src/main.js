import { router } from './router.js';
import { store } from './state.js';
import { LoginPage } from './pages/LoginPage.js';
import { DashboardPage } from './pages/DashboardPage.js';
import { AdminPage } from './pages/AdminPage.js';
import { AnalysisPage } from './pages/AnalysisPage.js';
import { PerformancePage } from './pages/PerformancePage.js';
import { MentorPage } from './pages/MentorPage.js';
import { BlogPage } from './pages/BlogPage.js';

router.register('/login', LoginPage);
router.register('/', DashboardPage);
router.register('/admin', AdminPage);
router.register('/analysis', AnalysisPage);
router.register('/performance', PerformancePage);
router.register('/mentor', MentorPage);
router.register('/blog', BlogPage);

const init = () => {
    const token = localStorage.getItem('access_token');
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    
    if (token && user) {
        store.setState({ token, user });
    }
    
    router.render();
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
