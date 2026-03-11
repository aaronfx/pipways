/**
 * UI Utilities Module
 * Handles shared UI components, navigation, and helpers
 */

const ui = {
    init() {
        this.setupEventListeners();
        this.updateTheme();
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

    updateTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-theme', 'dark');
        }
    },

    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        sidebar.classList.toggle('open');
    },

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastMessage = document.getElementById('toast-message');
        
        toast.className = `toast show ${type}`;
        toastMessage.textContent = message;
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    },

    showLoading(text = 'Processing...') {
        document.getElementById('loading-text').textContent = text;
        document.getElementById('loading-overlay').classList.remove('hidden');
    },

    hideLoading() {
        document.getElementById('loading-overlay').classList.add('hidden');
    },

    openModal(modalId) {
        document.getElementById(modalId).classList.add('show');
        document.body.style.overflow = 'hidden';
    },

    closeModal(modalId) {
        document.getElementById(modalId).classList.remove('show');
        document.body.style.overflow = '';
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
        if (price === null || price === undefined) return '-';
        return parseFloat(price).toFixed(5);
    }
};
