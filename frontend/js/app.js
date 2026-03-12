/**
 * Pipways Main Application Module
 * Handles app initialization and global functionality
 */

const app = {
    /**
     * Initialize the application
     */
    init() {
        console.log('Pipways App v3.5 initialized');
        
        // Initialize Auth module (using correct case)
        if (typeof Auth !== 'undefined') {
            Auth.init();
        } else if (typeof auth !== 'undefined') {
            auth.init();
        } else {
            console.error('Auth module not loaded!');
        }
        
        // Initialize other modules
        this.initNavigation();
        this.initUI();
    },
    
    /**
     * Initialize navigation
     */
    initNavigation() {
        // Mobile menu toggle
        const menuToggle = document.getElementById('menuToggle');
        const navMenu = document.getElementById('navMenu');
        
        if (menuToggle && navMenu) {
            menuToggle.addEventListener('click', () => {
                navMenu.classList.toggle('active');
            });
        }
        
        // Active nav item highlighting
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    },
    
    /**
     * Initialize UI components
     */
    initUI() {
        // Initialize tooltips
        this.initTooltips();
        
        // Initialize modals
        this.initModals();
        
        // Check auth status for protected pages
        this.checkPageAccess();
    },
    
    /**
     * Initialize tooltips
     */
    initTooltips() {
        const tooltips = document.querySelectorAll('[data-tooltip]');
        tooltips.forEach(tooltip => {
            tooltip.addEventListener('mouseenter', (e) => {
                const text = e.target.getAttribute('data-tooltip');
                // Simple tooltip implementation
                console.log('Tooltip:', text);
            });
        });
    },
    
    /**
     * Initialize modals
     */
    initModals() {
        const modalTriggers = document.querySelectorAll('[data-modal]');
        modalTriggers.forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                const modalId = e.target.getAttribute('data-modal');
                const modal = document.getElementById(modalId);
                if (modal) {
                    modal.classList.add('active');
                }
            });
        });
        
        // Close modal on outside click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.classList.remove('active');
            }
        });
    },
    
    /**
     * Check page access permissions
     */
    checkPageAccess() {
        const currentPage = window.location.pathname;
        
        // Pages that require authentication
        const protectedPages = [
            '/dashboard.html',
            '/courses.html',
            '/signals.html',
            '/webinars.html',
            '/profile.html'
        ];
        
        // Admin only pages
        const adminPages = [
            '/admin.html',
            '/admin-dashboard.html'
        ];
        
        const isProtected = protectedPages.some(page => currentPage.includes(page));
        const isAdminPage = adminPages.some(page => currentPage.includes(page));
        
        if (isProtected || isAdminPage) {
            const token = localStorage.getItem('pipways_token');
            
            if (!token) {
                window.location.href = '/index.html';
                return;
            }
            
            if (isAdminPage) {
                const user = JSON.parse(localStorage.getItem('pipways_user') || '{}');
                if (user.role !== 'admin' && user.role !== 'moderator') {
                    alert('Admin access required');
                    window.location.href = '/dashboard.html';
                }
            }
        }
    },
    
    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});

// Export for global access
window.app = app;
