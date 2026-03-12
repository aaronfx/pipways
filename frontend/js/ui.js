/**
 * UI Utilities Module
 * Added: Mobile responsive helpers and fixed loading overlay
 */

const ui = {
    loadingCount: 0,

    init() {
        this.setupEventListeners();
        this.updateTheme();
        this.setupMobileMenu();
        // Ensure loading is hidden on init
        this.hideLoading();
    },

    setupEventListeners() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal.show').forEach(modal => {
                    this.closeModal(modal.id);
                });
            }
        });

        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
        });
    },

    setupMobileMenu() {
        // Mobile sidebar toggle
        const sidebarToggle = document.getElementById('mobile-menu-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                document.getElementById('sidebar').classList.toggle('open');
            });
        }

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) {
                const sidebar = document.getElementById('sidebar');
                const toggle = document.getElementById('mobile-menu-toggle');
                if (sidebar && toggle && !sidebar.contains(e.target) && !toggle.contains(e.target)) {
                    sidebar.classList.remove('open');
                }
            }
        });
    },

    updateTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-theme', 'dark');
        }
    },

    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.classList.toggle('open');
    },

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastMessage = document.getElementById('toast-message');
        if (!toast || !toastMessage) return;
        
        toast.className = `toast show ${type}`;
        toastMessage.textContent = message;
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    },

    showLoading(text = 'Processing...') {
        this.loadingCount++;
        const loadingText = document.getElementById('loading-text');
        const overlay = document.getElementById('loading-overlay');
        if (loadingText) loadingText.textContent = text;
        if (overlay) overlay.classList.remove('hidden');
    },

    hideLoading() {
        this.loadingCount = Math.max(0, this.loadingCount - 1);
        if (this.loadingCount === 0) {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) overlay.classList.add('hidden');
        }
    },

    forceHideLoading() {
        this.loadingCount = 0;
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.classList.add('hidden');
    },

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
    },

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    },

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    formatPrice(price) {
        if (price === null || price === undefined || price === '') return '-';
        const num = parseFloat(price);
        if (isNaN(num)) return '-';
        return num.toFixed(5);
    }
};
