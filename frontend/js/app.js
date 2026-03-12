/**
 * Main Application Module
 * Fixed: Auth check timing, loading states, and section switching
 */

const app = {
    currentSection: 'home',
    dataInitialized: false,

    init() {
        ui.init();
        auth.init();
        // Don't init user data here - wait for auth check in auth.js
    },

    initUserData() {
        if (this.dataInitialized || !auth.currentUser) return;
        
        try {
            // Load all data
            if (typeof signals !== 'undefined' && signals.loadSignals) {
                signals.loadSignals().catch(err => console.error('Signals load failed:', err));
            }
            if (typeof courses !== 'undefined' && courses.loadCourses) {
                courses.loadCourses().catch(err => console.error('Courses load failed:', err));
            }
            if (typeof webinars !== 'undefined' && webinars.loadWebinars) {
                webinars.loadWebinars().catch(err => console.error('Webinars load failed:', err));
            }
            if (typeof blog !== 'undefined' && blog.loadBlogPosts) {
                blog.loadBlogPosts().catch(err => console.error('Blog load failed:', err));
            }
            
            this.dataInitialized = true;
        } catch (error) {
            console.error('Error loading user data:', error);
        }
    },

    showSection(sectionName, navElement) {
        // Check auth for protected sections
        const protectedSections = ['signals', 'courses', 'webinars', 'blog', 'analysis', 'performance', 'mentor', 'admin'];
        
        if (protectedSections.includes(sectionName) && !auth.currentUser) {
            ui.showToast('Please login to access this feature', 'error');
            auth.showAuthWall();
            return;
        }

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
            document.getElementById('sidebar')?.classList.remove('open');
        }

        // Section specific loading
        switch(sectionName) {
            case 'signals':
                if (typeof signals !== 'undefined') signals.loadSignals();
                break;
            case 'courses':
                if (typeof courses !== 'undefined') courses.loadCourses();
                break;
            case 'webinars':
                if (typeof webinars !== 'undefined') webinars.loadWebinars();
                break;
            case 'blog':
                if (typeof blog !== 'undefined') blog.loadBlogPosts();
                break;
            case 'admin':
                if(auth.requireAdmin()) {
                    if(typeof adminNav !== 'undefined') adminNav.init();
                }
                break;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
