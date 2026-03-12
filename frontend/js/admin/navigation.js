/**
 * Admin Navigation Module
 * Handles tab switching and navigation within admin dashboard
 */

const adminNav = {
    currentTab: 'dashboard',
    initialized: false,
    
    init() {
        if(this.initialized) return;
        if(!auth.currentUser) {
            console.log('Cannot init admin nav - not authenticated');
            return;
        }
        this.switchTab('dashboard');
        this.initialized = true;
    },
    
    switchTab(tabName) {
        // Check auth before switching
        if(!auth.currentUser) {
            ui.showToast('Please login to access admin features', 'error');
            return;
        }
        
        // Update tab buttons
        document.querySelectorAll('.admin-nav-tab').forEach(tab => {
            tab.classList.remove('active');
            if(tab.dataset.tab === tabName) {
                tab.classList.add('active');
            }
        });
        
        // Update tab contents
        document.querySelectorAll('.admin-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        const targetContent = document.getElementById(`tab-${tabName}`);
        if(targetContent) {
            targetContent.classList.add('active');
        }
        
        this.currentTab = tabName;
        
        // Load data for the tab
        this.loadTabData(tabName);
    },
    
    loadTabData(tabName) {
        // Verify admin access before loading any data
        if(!auth.currentUser || (auth.currentUser.role !== 'admin' && auth.currentUser.role !== 'moderator')) {
            console.log('Admin access required for tab:', tabName);
            return;
        }
        
        switch(tabName) {
            case 'dashboard':
                adminDashboard.loadStats();
                break;
            case 'signals':
                adminSignals.load();
                break;
            case 'users':
                adminUsers.load();
                break;
            case 'blog':
                adminBlog.load();
                break;
            case 'lms':
                adminLMS.load();
                break;
            case 'webinars':
                adminWebinars.load();
                break;
            case 'settings':
                adminSettings.load();
                break;
        }
    }
};
