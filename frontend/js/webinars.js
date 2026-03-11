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
                    ${auth.currentUser && (auth.currentUser.role === 'admin' || auth.currentUser.role === 'moderator') ? 
                        '<button class="primary" onclick="webinars.showCreateModal()">Schedule Webinar</button>' : ''}
                </div>
                <div class="webinars-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem;">
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
        const scheduledDate = ui.formatDate(webinar.scheduled_at);

        return `
            <div class="card webinar-card" style="${webinar.is_premium ? 'border: 2px solid var(--warning);' : ''}">
                <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                    <h3>${webinar.title}</h3>
                    ${isPremium}
                </div>
                <p>${webinar.description || ''}</p>
                <div style="margin: 1rem 0;">
                    <div><strong>Date:</strong> ${scheduledDate}</div>
                    <div><strong>Duration:</strong> ${webinar.duration_minutes} minutes</div>
                    ${webinar.max_participants ? `<div><strong>Max Participants:</strong> ${webinar.max_participants}</div>` : ''}
                </div>
                ${webinar.reminder_message ? `<div style="background: var(--bg); padding: 0.5rem; border-radius: 0.25rem; margin: 0.5rem 0; font-size: 0.9rem;"><strong>Reminder:</strong> ${webinar.reminder_message}</div>` : ''}
                
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                    ${webinar.meeting_link && !webinar.is_premium ? 
                        `<a href="${webinar.meeting_link}" target="_blank" class="button primary">Join Meeting</a>` : 
                        webinar.is_premium ? '<button onclick="auth.requireAuth() || ui.showToast(\'VIP subscription required\', \'warning\')">VIP Login Required</button>' : ''}
                    
                    ${auth.currentUser && (auth.currentUser.role === 'admin' || auth.currentUser.role === 'moderator') ? `
                        <button onclick="webinars.editWebinar(${webinar.id})">Edit</button>
                        <button class="secondary" onclick="webinars.deleteWebinar(${webinar.id})">Delete</button>
                    ` : ''}
                </div>
            </div>
        `;
    },

    showCreateModal() {
        const container = document.getElementById('main-content');
        const now = new Date();
        const minDate = now.toISOString().slice(0, 16); // Format for datetime-local input

        container.innerHTML = `
            <div class="card" style="max-width: 800px; margin: 0 auto;">
                <h2>Schedule New Webinar</h2>
                <form onsubmit="webinars.handleCreate(event)">
                    <div class="form-group">
                        <label>Title</label>
                        <input type="text" name="title" required>
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <textarea name="description" rows="4" required></textarea>
                    </div>
                    <div class="form-group">
                        <label>Scheduled Date & Time</label>
                        <input type="datetime-local" name="scheduled_at" min="${minDate}" required>
                    </div>
                    <div class="form-group">
                        <label>Duration (minutes)</label>
                        <input type="number" name="duration_minutes" value="60" min="15" required>
                    </div>
                    <div class="form-group">
                        <label>Meeting Link</label>
                        <input type="url" name="meeting_link" placeholder="https://zoom.us/j/... or https://meet.google.com/...">
                    </div>
                    <div class="form-group">
                        <label>Max Participants</label>
                        <input type="number" name="max_participants" value="100" min="1">
                    </div>
                    <div class="form-group">
                        <label>Reminder Message</label>
                        <textarea name="reminder_message" rows="2" placeholder="Custom reminder message for participants..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" name="is_premium"> VIP Only
                        </label>
                    </div>
                    <div style="display: flex; gap: 1rem;">
                        <button type="submit" class="primary">Schedule</button>
                        <button type="button" onclick="window.location='/webinars'">Cancel</button>
                    </div>
                </form>
            </div>
        `;
    },

    async handleCreate(e) {
        e.preventDefault();
        const form = e.target;
        const scheduledAt = new Date(form.scheduled_at.value);
        
        const data = {
            title: form.title.value,
            description: form.description.value,
            scheduled_at: scheduledAt.toISOString(),
            duration_minutes: parseInt(form.duration_minutes.value),
            meeting_link: form.meeting_link.value,
            max_participants: parseInt(form.max_participants.value) || 100,
            reminder_message: form.reminder_message.value,
            is_premium: form.is_premium.checked
        };

        try {
            await api.post('/webinars', data);
            ui.showToast('Webinar scheduled successfully', 'success');
            window.location.href = '/webinars';
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    },

    async editWebinar(id) {
        try {
            // Fetch all webinars to find this one (since we don't have individual GET endpoint)
            const webinarsList = await api.get('/webinars?limit=100');
            const webinar = webinarsList.find(w => w.id === id);
            
            if (!webinar) {
                ui.showToast('Webinar not found', 'error');
                return;
            }

            const container = document.getElementById('main-content');
            const scheduledDate = new Date(webinar.scheduled_at);
            const formattedDate = scheduledDate.toISOString().slice(0, 16);

            container.innerHTML = `
                <div class="card" style="max-width: 800px; margin: 0 auto;">
                    <h2>Edit Webinar</h2>
                    <form onsubmit="webinars.handleUpdate(event, ${id})">
                        <div class="form-group">
                            <label>Title</label>
                            <input type="text" name="title" value="${webinar.title}" required>
                        </div>
                        <div class="form-group">
                            <label>Description</label>
                            <textarea name="description" rows="4" required>${webinar.description || ''}</textarea>
                        </div>
                        <div class="form-group">
                            <label>Scheduled Date & Time</label>
                            <input type="datetime-local" name="scheduled_at" value="${formattedDate}" required>
                        </div>
                        <div class="form-group">
                            <label>Duration (minutes)</label>
                            <input type="number" name="duration_minutes" value="${webinar.duration_minutes}" min="15" required>
                        </div>
                        <div class="form-group">
                            <label>Meeting Link</label>
                            <input type="url" name="meeting_link" value="${webinar.meeting_link || ''}">
                        </div>
                        <div class="form-group">
                            <label>Max Participants</label>
                            <input type="number" name="max_participants" value="${webinar.max_participants || 100}" min="1">
                        </div>
                        <div class="form-group">
                            <label>Reminder Message</label>
                            <textarea name="reminder_message" rows="2">${webinar.reminder_message || ''}</textarea>
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" name="is_premium" ${webinar.is_premium ? 'checked' : ''}> VIP Only
                            </label>
                        </div>
                        <div style="display: flex; gap: 1rem;">
                            <button type="submit" class="primary">Update</button>
                            <button type="button" onclick="window.location='/webinars'">Cancel</button>
                        </div>
                    </form>
                </div>
            `;
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    },

    async handleUpdate(e, id) {
        e.preventDefault();
        const form = e.target;
        const scheduledAt = new Date(form.scheduled_at.value);
        
        const data = {
            title: form.title.value,
            description: form.description.value,
            scheduled_at: scheduledAt.toISOString(),
            duration_minutes: parseInt(form.duration_minutes.value),
            meeting_link: form.meeting_link.value,
            max_participants: parseInt(form.max_participants.value) || 100,
            reminder_message: form.reminder_message.value,
            is_premium: form.is_premium.checked
        };

        try {
            await api.put(`/webinars/${id}`, data);
            ui.showToast('Webinar updated successfully', 'success');
            window.location.href = '/webinars';
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    },

    async deleteWebinar(id) {
        if (!confirm('Are you sure you want to delete this webinar? This action cannot be undone.')) return;
        
        try {
            await api.delete(`/webinars/${id}`);
            ui.showToast('Webinar deleted successfully', 'success');
            this.loadWebinars(document.getElementById('main-content'));
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    }
};
