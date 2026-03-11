/**
 * Webinars Module
 * Fixed: Uses data.webinars.map() with safe checks
 */

const webinars = {
    async loadWebinars() {
        const container = document.getElementById('webinars-grid');
        if (!container) return;

        try {
            const data = await api.get('/api/webinars?upcoming=true');
            
            // FIXED: Safe check
            if (!data || !Array.isArray(data.webinars)) {
                container.innerHTML = '<div class="content-card"><p style="text-align: center; color: var(--text-secondary);">No upcoming webinars scheduled</p></div>';
                return;
            }

            const webinarsList = data.webinars;
            
            if (webinarsList.length === 0) {
                container.innerHTML = '<div class="content-card"><p style="text-align: center; color: var(--text-secondary);">No upcoming webinars scheduled</p></div>';
                return;
            }

            container.innerHTML = webinarsList.map(webinar => this.renderWebinarCard(webinar)).join('');
            
        } catch (error) {
            container.innerHTML = `<div class="content-card"><p style="text-align: center; color: var(--danger);">Error: ${error.message}</p></div>`;
        }
    },

    renderWebinarCard(webinar) {
        const isPremium = webinar.is_premium ? '<span class="badge badge-premium">VIP Only</span>' : '';
        const scheduledDate = ui.formatDate(webinar.scheduled_at);

        return `
            <div class="content-card webinar-card" style="${webinar.is_premium ? 'border: 2px solid var(--warning);' : ''}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3>${webinar.title}</h3>
                    ${isPremium}
                </div>
                <p style="color: var(--text-secondary); margin-bottom: 1rem;">${webinar.description || ''}</p>
                <div style="margin-bottom: 1rem;">
                    <div><strong>Date:</strong> ${scheduledDate}</div>
                    <div><strong>Duration:</strong> ${webinar.duration_minutes} minutes</div>
                    ${webinar.max_participants ? `<div><strong>Max Participants:</strong> ${webinar.max_participants}</div>` : ''}
                </div>
                ${webinar.reminder_message ? `<div style="background: var(--bg); padding: 0.5rem; border-radius: 0.25rem; margin-bottom: 1rem; font-size: 0.9rem;"><strong>Reminder:</strong> ${webinar.reminder_message}</div>` : ''}
                
                <div style="display: flex; gap: 0.5rem;">
                    ${webinar.meeting_link && !webinar.is_premium ? 
                        `<a href="${webinar.meeting_link}" target="_blank" class="btn btn-primary">Join Meeting</a>` : 
                        webinar.is_premium ? '<button class="btn btn-premium" onclick="auth.requireAuth() || ui.showToast(\'VIP subscription required\', \'warning\')">VIP Login Required</button>' : ''}
                </div>
            </div>
        `;
    }
};
