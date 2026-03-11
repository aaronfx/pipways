/**
 * Main Application Module
 * Handles routing, initialization, and global event handlers
 */

const app = {
    currentSection: 'home',

    init() {
        ui.init();
        auth.init();
        
        // Setup navigation
        if (auth.currentUser) {
            this.initUserData();
        }
    },

    initUserData() {
        // Load initial data for dashboard
        signals.loadSignals();
        courses.loadCourses();
        webinars.loadWebinars();
        blog.loadBlogPosts();
        
        // Load admin data if applicable
        if (auth.currentUser && (auth.currentUser.role === 'admin' || auth.currentUser.role === 'moderator')) {
            admin.loadStats();
        }
    },

    showSection(sectionName, navElement) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Show target section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.add('active');
            this.currentSection = sectionName;
        }

        // Update navigation active state
        if (navElement) {
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            navElement.classList.add('active');
        }

        // Close sidebar on mobile
        if (window.innerWidth <= 1024) {
            document.getElementById('sidebar').classList.remove('open');
        }

        // Section-specific initialization
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
                if (auth.requireAdmin()) {
                    admin.loadStats();
                    admin.loadBlogPosts();
                }
                break;
        }
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
