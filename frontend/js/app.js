/**
 * Main Application Module
 * Updated to support modular admin dashboard with proper auth flow
 */

const app = {
    currentSection: 'home',

    init() {
        ui.init();
        auth.init();
        
        // Don't init admin here - wait for auth
        if(auth.currentUser) {
            this.initUserData();
        }
    },

    initUserData() {
        signals.loadSignals();
        courses.loadCourses();
        webinars.loadWebinars();
        blog.loadBlogPosts();
        
        // Initialize admin features only if user is admin
        if(auth.currentUser && (auth.currentUser.role === 'admin' || auth.currentUser.role === 'moderator')) {
            // Show admin nav item
            const adminNavItem = document.getElementById('admin-nav-item');
            if(adminNavItem) adminNavItem.classList.remove('hidden');
            
            // Show admin badge
            const adminBadge = document.getElementById('admin-badge');
            if(adminBadge) adminBadge.classList.remove('hidden');
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

        // Section specific loading - ONLY if authenticated
        if(!auth.currentUser) {
            ui.showToast('Please login to access this feature', 'error');
            return;
        }

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
                    // Only init admin nav and load data when explicitly entering admin section
                    if(typeof adminNav !== 'undefined') {
                        adminNav.init();
                    }
                }
                break;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
