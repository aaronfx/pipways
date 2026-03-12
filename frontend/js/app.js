/**
 * Main Application Module
 * Updated to support modular admin dashboard
 */

const app = {
    currentSection: 'home',

    init() {
        ui.init();
        auth.init();
        
        if(auth.currentUser) {
            this.initUserData();
        }
        
        // Initialize admin navigation if on admin page
        if(document.getElementById('admin-section')) {
            adminNav.init();
        }
    },

    initUserData() {
        signals.loadSignals();
        courses.loadCourses();
        webinars.loadWebinars();
        blog.loadBlogPosts();
        
        // Initialize admin data if admin
        if(auth.currentUser && (auth.currentUser.role === 'admin' || auth.currentUser.role === 'moderator')) {
            // Show admin nav item
            const adminNavItem = document.getElementById('admin-nav-item');
            if(adminNavItem) adminNavItem.classList.remove('hidden');
            
            // Load admin stats if on admin page
            if(document.getElementById('admin-section')) {
                adminDashboard.loadStats();
            }
        }
    },

    showSection(sectionName, navElement) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Show target section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if(targetSection) {
            targetSection.classList.add('active');
            this.currentSection = sectionName;
        }

        // Update nav active state
        if(navElement) {
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            navElement.classList.add('active');
        }

        // Mobile sidebar close
        if(window.innerWidth <= 1024) {
            document.getElementById('sidebar').classList.remove('open');
        }

        // Section specific loading
        switch(sectionName) {
            case 'signals':
                signals.loadSignals();
                break;
            case 'courses':
                courses.loadCourses();
                break;
            case 'webinars':
                webinars.loadWebinars();
                break;
            case 'blog':
                blog.loadBlogPosts();
                break;
            case 'admin':
                if(auth.requireAdmin()) {
                    adminDashboard.loadStats();
                    adminNav.switchTab('dashboard');
                }
                break;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
