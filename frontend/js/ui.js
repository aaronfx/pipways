/**
 * UI Utilities - Complete
 */
const UI = {
    spinner: null,
    toastContainer: null,
    
    init() {
        // Create spinner overlay
        this.spinner = document.createElement('div');
        this.spinner.className = 'spinner-overlay';
        this.spinner.innerHTML = '<div class="spinner"></div>';
        this.spinner.style.cssText = 'display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9998;justify-content:center;align-items:center;';
        document.body.appendChild(this.spinner);

        // Create toast container
        this.toastContainer = document.createElement('div');
        this.toastContainer.id = 'toast-container';
        this.toastContainer.style.cssText = 'position:fixed;bottom:2rem;right:2rem;z-index:9999;display:flex;flex-direction:column;gap:0.75rem;';
        document.body.appendChild(this.toastContainer);

        // Subscribe to loading state
        Store.subscribe((key, value) => {
            if (key === 'loading') {
                this.spinner.style.display = value ? 'flex' : 'none';
            }
        });
    },

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.style.cssText = 'background:white;border-left:4px solid #3b82f6;padding:1rem 1.5rem;border-radius:0.5rem;box-shadow:0 10px 15px -3px rgba(0,0,0,0.1);min-width:300px;max-width:400px;animation:slideIn 0.3s ease-out;display:flex;justify-content:space-between;align-items:center;';
        
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        
        toast.style.borderLeftColor = colors[type] || colors.info;
        
        toast.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()" style="background:none;border:none;cursor:pointer;font-size:1.25rem;color:#9ca3af;">&times;</button>
        `;
        
        this.toastContainer.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentElement) toast.remove();
        }, 5000);
    },

    showModal(content) {
        const modal = document.createElement('div');
        modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:1000;display:flex;align-items:center;justify-content:center;padding:1rem;';
        modal.innerHTML = `
            <div style="background:white;border-radius:1rem;max-width:600px;width:100%;max-height:90vh;overflow-y:auto;box-shadow:0 25px 50px -12px rgba(0,0,0,0.25);position:relative;">
                <button onclick="this.closest('.modal').remove()" style="position:absolute;top:1rem;right:1rem;background:none;border:none;font-size:1.5rem;cursor:pointer;color:#9ca3af;width:32px;height:32px;display:flex;align-items:center;justify-content:center;border-radius:50%;">&times;</button>
                <div style="padding:2rem;">${content}</div>
            </div>
        `;
        modal.className = 'modal';
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
        
        document.body.appendChild(modal);
    },

    closeModal() {
        document.querySelectorAll('.modal').forEach(m => m.remove());
    },

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
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

// Auto-initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => UI.init());
} else {
    UI.init();
}
