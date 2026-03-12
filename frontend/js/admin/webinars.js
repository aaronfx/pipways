/**
 * Admin Webinars Management Module
 */

const adminWebinars = {
    webinars: [],
    editingId: null,
    
    async load() {
        const container = document.getElementById('admin-webinars-list');
        if(!container) return;
        
        container.innerHTML = '<div class="text-center" style="padding: 40px;">Loading webinars...</div>';
        
        try {
            const response = await api.get('/api/webinars?upcoming=false');
            this.webinars = response.webinars || [];
            this.render();
        } catch (error) {
            container.innerHTML = `<div class="text-center text-danger">Error: ${error.message}</div>`;
        }
    },
    
    render() {
        const container = document.getElementById('admin-webinars-list');
        
        if(this.webinars.length === 0) {
            container.innerHTML = '<div class="text-center" style="padding: 40px;">No webinars scheduled</div>';
            return;
        }
        
        container.innerHTML = this.webinars.map(webinar => `
            <div class="webinar-admin-item">
                <div class="webinar-admin-info">
                    <h4>${webinar.title} ${webinar.is_premium ? '<span class="badge badge-premium">VIP</span>' : ''}</h4>
                    <p>${webinar.description || ''}</p>
                    <div class="webinar-admin-meta">
                        <span><i class="fas fa-calendar"></i> ${ui.formatDate(webinar.scheduled_at)}</span>
                        <span><i class="fas fa-clock"></i> ${webinar.duration_minutes} min</span>
                        <span><i class="fas fa-users"></i> Max ${webinar.max_participants || 100}</span>
                    </div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-sm" onclick="adminWebinars.edit(${webinar.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="adminWebinars.delete(${webinar.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    },
    
    openModal() {
        this.editingId = null;
        document.getElementById('webinar-form').reset();
        document.getElementById('webinar-modal-title').textContent = 'Schedule Webinar';
        document.getElementById('webinar-id').value = '';
        ui.openModal('webinar-modal');
    },
    
    async edit(id) {
        const webinar = this.webinars.find(w => w.id === id);
        if(!webinar) return;
        
        this.editingId = id;
        document.getElementById('webinar-modal-title').textContent = 'Edit Webinar';
        document.getElementById('webinar-id').value = webinar.id;
        document.getElementById('webinar-title').value = webinar.title;
        document.getElementById('webinar-description').value = webinar.description || '';
        
        const date = new Date(webinar.scheduled_at);
        const formatted = date.toISOString().slice(0, 16);
        document.getElementById('webinar-datetime').value = formatted;
        
        document.getElementById('webinar-duration').value = webinar.duration_minutes || 60;
        document.getElementById('webinar-link').value = webinar.meeting_link || '';
        document.getElementById('webinar-max-participants').value = webinar.max_participants || 100;
        document.getElementById('webinar-premium').checked = webinar.is_premium || false;
        
        ui.openModal('webinar-modal');
    },
    
    async save() {
        const data = {
            title: document.getElementById('webinar-title').value,
            description: document.getElementById('webinar-description').value,
            scheduled_at: new Date(document.getElementById('webinar-datetime').value).toISOString(),
            duration_minutes: parseInt(document.getElementById('webinar-duration').value) || 60,
            meeting_link: document.getElementById('webinar-link').value,
            max_participants: parseInt(document.getElementById('webinar-max-participants').value) || 100,
            is_premium: document.getElementById('webinar-premium').checked
        };
        
        try {
            ui.showLoading('Saving webinar...');
            
            if(this.editingId) {
                await api.put(`/api/webinars/${this.editingId}`, data);
                ui.showToast('Webinar updated successfully', 'success');
            } else {
                await api.post('/api/webinars', data);
                ui.showToast('Webinar scheduled successfully', 'success');
            }
            
            ui.closeModal('webinar-modal');
            this.load();
            
        } catch (error) {
            ui.showToast('Error saving webinar: ' + error.message, 'error');
        } finally {
            ui.hideLoading();
        }
    },
    
    async delete(id) {
        if(!confirm('Delete this webinar?')) return;
        
        try {
            await api.delete(`/api/webinars/${id}`);
            ui.showToast('Webinar deleted', 'success');
            this.load();
        } catch (error) {
            ui.showToast('Error deleting webinar: ' + error.message, 'error');
        }
    },
    
    search() {
        const term = document.getElementById('webinar-search')?.value.toLowerCase();
        if(!term) {
            this.render();
            return;
        }
        
        const filtered = this.webinars.filter(w => 
            w.title.toLowerCase().includes(term) ||
            (w.description && w.description.toLowerCase().includes(term))
        );
        
        const container = document.getElementById('admin-webinars-list');
        if(filtered.length === 0) {
            container.innerHTML = '<div class="text-center" style="padding: 40px;">No matching webinars</div>';
            return;
        }
        
        container.innerHTML = filtered.map(webinar => `
            <div class="webinar-admin-item">
                <div class="webinar-admin-info">
                    <h4>${webinar.title} ${webinar.is_premium ? '<span class="badge badge-premium">VIP</span>' : ''}</h4>
                    <p>${webinar.description || ''}</p>
                    <div class="webinar-admin-meta">
                        <span><i class="fas fa-calendar"></i> ${ui.formatDate(webinar.scheduled_at)}</span>
                        <span><i class="fas fa-clock"></i> ${webinar.duration_minutes} min</span>
                    </div>
                </div>
                <div>
                    <button class="btn btn-sm" onclick="adminWebinars.edit(${webinar.id})"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-sm btn-danger" onclick="adminWebinars.delete(${webinar.id})"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        `).join('');
    }
};
