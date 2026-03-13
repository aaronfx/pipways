/**
 * UI Utilities
 */
const UI = {
    init() {
        // Create spinner overlay
        this.spinner = document.createElement('div');
        this.spinner.className = 'spinner-overlay';
        this.spinner.innerHTML = '<div class="spinner"></div>';
        this.spinner.style.display = 'none';
        document.body.appendChild(this.spinner);

        // Subscribe to loading state
        Store.subscribe((key, value) => {
            if (key === 'loading') {
                this.spinner.style.display = value ? 'flex' : 'none';
            }
        });
    },

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()" style="background: none; border: none; cursor: pointer; font-size: 1.25rem;">&times;</button>
        `;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentElement) toast.remove();
        }, 5000);
    },

    showModal(content) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <button class="modal-close" onclick="this.closest('.modal').remove()">&times;</button>
                <div style="padding: 2rem;">${content}</div>
            </div>
        `;
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
        
        document.body.appendChild(modal);
    },

    closeModal() {
        document.querySelectorAll('.modal').forEach(m => m.remove());
    },

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },

    formatDate(date) {
        return new Date(date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
};
