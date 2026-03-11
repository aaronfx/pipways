/**
 * Main Application Module
 * Handles routing, initialization, and global event handlers
 */

const app = {
    currentSection: 'home',

    init() {
        ui.init();
        auth.init();
        
        if (auth.currentUser) {
            this.initUserData();
        }
    },

    initUserData() {
        signals.loadSignals();
        courses.loadCourses();
        webinars.loadWebinars();
        blog.loadBlogPosts();
        
        if (auth.currentUser && (auth.currentUser.role === 'admin' || auth.currentUser.role === 'moderator')) {
            admin.loadStats();
        }
    },

    showSection(sectionName, navElement) {
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.add('active');
            this.currentSection = sectionName;
        }

        if (navElement) {
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            navElement.classList.add('active');
        }

        if (window.innerWidth <= 1024) {
            document.getElementById('sidebar').classList.remove('open');
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
                if (auth.requireAdmin()) {
                    admin.loadStats();
                    admin.loadBlogPosts();
                }
                break;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
