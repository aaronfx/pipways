const UI = {
    init() {
        this.spinner = document.getElementById('loadingSpinner');
        this.toastContainer = document.getElementById('toastContainer');
        this.modal = null;

        Store.subscribe((state) => {
            if (state.loading) {
                this.showSpinner();
            } else {
                this.hideSpinner();
            }
        });
    },

    showSpinner() {
        if (this.spinner) this.spinner.style.display = 'flex';
    },

    hideSpinner() {
        if (this.spinner) this.spinner.style.display = 'none';
    },

    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;

        this.toastContainer.appendChild(toast);

        setTimeout(() => toast.classList.add('show'), 10);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    showModal(content) {
        this.closeModal();

        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = 'activeModal';
        modal.innerHTML = `
            <div class="modal-content">
                <button class="modal-close" onclick="UI.closeModal()">&times;</button>
                ${content}
            </div>
        `;

        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeModal();
        });

        document.body.appendChild(modal);
        document.body.style.overflow = 'hidden';
        this.modal = modal;
    },

    closeModal() {
        if (this.modal) {
            this.modal.remove();
            this.modal = null;
            document.body.style.overflow = '';
        }
    },

    formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    },

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    setActiveNav(route) {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${route}`) {
                link.classList.add('active');
            }
        });
    },

    buildTable(headers, rows, actions = null) {
        let html = '<div class="table-responsive"><table class="table"><thead><tr>';
        headers.forEach(h => html += `<th>${h}</th>`);
        if (actions) html += '<th>Actions</th>';
        html += '</tr></thead><tbody>';

        rows.forEach(row => {
            html += '<tr>';
            row.forEach(cell => html += `<td>${cell}</td>`);
            if (actions) html += `<td>${actions(row)}</td>`;
            html += '</tr>';
        });

        html += '</tbody></table></div>';
        return html;
    }
};