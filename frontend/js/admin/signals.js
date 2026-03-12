/**
 * Admin Signals Management Module
 */

const adminSignals = {
    signals: [],
    editingId: null,
    
    async load() {
        const tbody = document.getElementById('admin-signals-tbody');
        if(!tbody) return;
        
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">Loading signals...</td></tr>';
        
        try {
            const response = await api.get('/api/admin/signals');
            this.signals = response.signals || [];
            this.render();
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Error: ${error.message}</td></tr>`;
        }
    },
    
    render() {
        const tbody = document.getElementById('admin-signals-tbody');
        const filter = document.getElementById('signal-status-filter')?.value;
        
        let filtered = this.signals;
        if(filter) {
            filtered = this.signals.filter(s => s.status === filter);
        }
        
        if(filtered.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center">No signals found</td></tr>';
            return;
        }
        
        tbody.innerHTML = filtered.map(signal => `
            <tr>
                <td><strong>${signal.pair}</strong></td>
                <td>
                    <span class="badge badge-${signal.direction === 'buy' ? 'success' : 'danger'}">
                        ${signal.direction.toUpperCase()}
                    </span>
                </td>
                <td>${ui.formatPrice(signal.entry_price)}</td>
                <td>${ui.formatPrice(signal.stop_loss)}</td>
                <td>${ui.formatPrice(signal.tp1)}${signal.tp2 ? ' / ' + ui.formatPrice(signal.tp2) : ''}</td>
                <td>
                    <span class="status-badge status-${signal.status === 'active' ? 'active' : 'inactive'}">
                        ${signal.status}
                    </span>
                </td>
                <td>${signal.result || '-'}</td>
                <td>
                    <div style="display: flex; gap: 8px;">
                        <button class="btn btn-sm" onclick="adminSignals.edit(${signal.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="adminSignals.delete(${signal.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                        ${signal.status === 'active' ? `
                            <button class="btn btn-sm btn-secondary" onclick="adminSignals.close(${signal.id})">
                                Close
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `).join('');
    },
    
    openModal() {
        this.editingId = null;
        document.getElementById('signal-form').reset();
        document.getElementById('signal-modal-title').textContent = 'Create Signal';
        document.getElementById('signal-id').value = '';
        ui.openModal('signal-modal');
    },
    
    async edit(id) {
        const signal = this.signals.find(s => s.id === id);
        if(!signal) return;
        
        this.editingId = id;
        document.getElementById('signal-modal-title').textContent = 'Edit Signal';
        document.getElementById('signal-id').value = signal.id;
        document.getElementById('signal-pair').value = signal.pair;
        document.getElementById('signal-direction').value = signal.direction;
        document.getElementById('signal-entry').value = signal.entry_price;
        document.getElementById('signal-sl').value = signal.stop_loss || '';
        document.getElementById('signal-tp').value = signal.tp1 || '';
        document.getElementById('signal-analysis').value = signal.analysis || '';
        document.getElementById('signal-premium').checked = signal.is_premium || false;
        document.getElementById('signal-active').checked = signal.status === 'active';
        
        ui.openModal('signal-modal');
    },
    
    async save() {
        const data = {
            pair: document.getElementById('signal-pair').value.toUpperCase(),
            direction: document.getElementById('signal-direction').value,
            entry_price: parseFloat(document.getElementById('signal-entry').value),
            stop_loss: parseFloat(document.getElementById('signal-sl').value) || null,
            tp1: parseFloat(document.getElementById('signal-tp').value) || null,
            tp2: null,
            analysis: document.getElementById('signal-analysis').value,
            is_premium: document.getElementById('signal-premium').checked,
            status: document.getElementById('signal-active').checked ? 'active' : 'inactive'
        };
        
        try {
            ui.showLoading('Saving signal...');
            
            if(this.editingId) {
                await api.put(`/api/admin/signals/${this.editingId}`, data);
                ui.showToast('Signal updated successfully', 'success');
            } else {
                await api.post('/api/admin/signals', data);
                ui.showToast('Signal created successfully', 'success');
            }
            
            ui.closeModal('signal-modal');
            this.load();
            
        } catch (error) {
            ui.showToast('Error saving signal: ' + error.message, 'error');
        } finally {
            ui.hideLoading();
        }
    },
    
    async delete(id) {
        if(!confirm('Are you sure you want to delete this signal?')) return;
        
        try {
            await api.delete(`/api/admin/signals/${id}`);
            ui.showToast('Signal deleted', 'success');
            this.load();
        } catch (error) {
            ui.showToast('Error deleting signal: ' + error.message, 'error');
        }
    },
    
    async close(id) {
        try {
            await api.put(`/api/admin/signals/${id}`, { status: 'closed' });
            ui.showToast('Signal closed', 'success');
            this.load();
        } catch (error) {
            ui.showToast('Error closing signal: ' + error.message, 'error');
        }
    },
    
    search() {
        const term = document.getElementById('signal-search')?.value.toLowerCase();
        if(!term) {
            this.render();
            return;
        }
        
        const filtered = this.signals.filter(s => 
            s.pair.toLowerCase().includes(term) ||
            (s.analysis && s.analysis.toLowerCase().includes(term))
        );
        
        const tbody = document.getElementById('admin-signals-tbody');
        tbody.innerHTML = filtered.map(signal => `
            <tr>
                <td><strong>${signal.pair}</strong></td>
                <td><span class="badge badge-${signal.direction === 'buy' ? 'success' : 'danger'}">${signal.direction.toUpperCase()}</span></td>
                <td>${ui.formatPrice(signal.entry_price)}</td>
                <td>${ui.formatPrice(signal.stop_loss)}</td>
                <td>${ui.formatPrice(signal.tp1)}${signal.tp2 ? ' / ' + ui.formatPrice(signal.tp2) : ''}</td>
                <td><span class="status-badge status-${signal.status === 'active' ? 'active' : 'inactive'}">${signal.status}</span></td>
                <td>${signal.result || '-'}</td>
                <td>
                    <button class="btn btn-sm" onclick="adminSignals.edit(${signal.id})"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-sm btn-danger" onclick="adminSignals.delete(${signal.id})"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('');
    }
};
