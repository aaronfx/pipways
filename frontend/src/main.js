import { router } from '/src/router.js';
import { store } from '/src/state.js';
import { LoginPage } from '/src/pages/LoginPage.js';
import { DashboardPage } from '/src/pages/DashboardPage.js';
import { AdminPage } from '/src/pages/AdminPage.js';
import { AnalysisPage } from '/src/pages/AnalysisPage.js';
import { PerformancePage } from '/src/pages/PerformancePage.js';
import { MentorPage } from '/src/pages/MentorPage.js';
import { BlogPage } from '/src/pages/BlogPage.js';

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
