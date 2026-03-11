/**
 * Webinars Module
 */
const webinars = {
    async loadWebinars(container) {
        container.innerHTML = '<div class="loading">Loading webinars...</div>';

        try {
            const data = await api.get('/webinars?upcoming=true');

            let html = `
                <div class="page-header">
                    <h1>Live Webinars</h1>
                    ${auth.requireAdmin() ? '<button class="primary" onclick="webinars.showCreateModal()">Schedule Webinar</button>' : ''}
                </div>
                <div class="webinars-list">
                    ${data.length === 0 ? '<p>No upcoming webinars.</p>' : 
                      data.map(w => this.renderWebinarCard(w)).join('')}
                </div>
            `;

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="error">Failed to load webinars: ${error.message}</div>`;
        }
    },

    renderWebinarCard(webinar) {
        const isPremium = webinar.is_premium ? '<span class="badge badge-premium">VIP Only</span>' : '';
        const isUpcoming = new Date(webinar.scheduled_at) > new Date();

        return `
            <div class="card webinar-card">
                <div class="card-header">
                    <h3>${webinar.title}</h3>
                    ${isPremium}
                </div>
                <p>${webinar.description || ''}</p>
                <div style="margin: 1rem 0;">
                    <div><strong>Date:</strong> ${ui.formatDate(webinar.scheduled_at)}</div>
                    <div><strong>Duration:</strong> ${webinar.duration_minutes} minutes</div>
                </div>
                ${webinar.meeting_link && !webinar.is_premium ? 
                    `<a href="${webinar.meeting_link}" target="_blank" class="button primary">Join Meeting</a>` : 
                    isPremium ? '<button onclick="auth.showLoginModal()">VIP Login Required</button>' : ''}
                ${auth.requireAdmin() ? `
                    <div style="margin-top: 1rem;">
                        <button onclick="webinars.editWebinar(${webinar.id})">Edit</button>
                        <button class="secondary" onclick="webinars.deleteWebinar(${webinar.id})">Delete</button>
                    </div>
                ` : ''}
            </div>
        `;
    },

    showCreateModal() {
        ui.showToast('Create webinar form would appear here');
    },

    editWebinar(id) {
        ui.showToast('Edit webinar form would appear here');
    },

    async deleteWebinar(id) {
        if (!confirm('Delete this webinar?')) return;
        try {
            await api.delete(`/webinars/${id}`);
            ui.showToast('Webinar deleted', 'success');
            this.loadWebinars(document.getElementById('main-content'));
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    }
};
