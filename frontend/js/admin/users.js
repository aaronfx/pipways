/**
 * Admin Users Management Module
 */

const adminUsers = {
    users: [],
    
    async load() {
        const tbody = document.getElementById('admin-users-tbody');
        if(!tbody) return;
        
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">Loading users...</td></tr>';
        
        try {
            const response = await api.get('/api/admin/users?limit=100');
            this.users = Array.isArray(response) ? response : [];
            this.render();
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Error: ${error.message}</td></tr>`;
        }
    },
    
    render() {
        const tbody = document.getElementById('admin-users-tbody');
        const roleFilter = document.getElementById('user-role-filter')?.value;
        
        let filtered = this.users;
        if(roleFilter) {
            filtered = this.users.filter(u => u.role === roleFilter);
        }
        
        if(filtered.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">No users found</td></tr>';
            return;
        }
        
        tbody.innerHTML = filtered.map(user => `
            <tr>
                <td>
                    <div class="user-cell">
                        <div class="user-cell-avatar">${(user.full_name || user.email).charAt(0).toUpperCase()}</div>
                        <div class="user-cell-info">
                            <div class="user-cell-name">${user.full_name || 'N/A'}</div>
                        </div>
                    </div>
                </td>
                <td>${user.email}</td>
                <td>
                    <select class="form-select form-select-sm" onchange="adminUsers.updateRole(${user.id}, this.value)">
                        <option value="user" ${user.role === 'user' ? 'selected' : ''}>User</option>
                        <option value="moderator" ${user.role === 'moderator' ? 'selected' : ''}>Moderator</option>
                        <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>Admin</option>
                    </select>
                </td>
                <td>
                    <span class="badge badge-${user.subscription_tier === 'vip' ? 'premium' : 'secondary'}">
                        ${user.subscription_tier.toUpperCase()}
                    </span>
                </td>
                <td>
                    <span class="status-badge status-${user.subscription_status === 'active' ? 'active' : 'inactive'}">
                        ${user.subscription_status}
                    </span>
                </td>
                <td>${ui.formatDate(user.created_at)}</td>
                <td>
                    <div style="display: flex; gap: 8px;">
                        <button class="btn btn-sm" onclick="adminUsers.viewDetails(${user.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="adminUsers.disable(${user.id})">
                            <i class="fas fa-ban"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    },
    
    async updateRole(userId, role) {
        try {
            await api.put(`/api/admin/users/${userId}`, { role });
            ui.showToast('Role updated successfully', 'success');
        } catch (error) {
            ui.showToast('Error updating role: ' + error.message, 'error');
            this.load();
        }
    },
    
    viewDetails(userId) {
        const user = this.users.find(u => u.id === userId);
        if(!user) return;
        
        ui.showToast(`User: ${user.email} | Role: ${user.role} | Tier: ${user.subscription_tier}`, 'info');
    },
    
    async disable(userId) {
        if(!confirm('Disable this user? They will lose access to the platform.')) return;
        
        try {
            await api.delete(`/api/admin/users/${userId}`);
            ui.showToast('User disabled', 'success');
            this.load();
        } catch (error) {
            ui.showToast('Error disabling user: ' + error.message, 'error');
        }
    },
    
    search() {
        const term = document.getElementById('user-search')?.value.toLowerCase();
        if(!term) {
            this.render();
            return;
        }
        
        const filtered = this.users.filter(u => 
            u.email.toLowerCase().includes(term) ||
            (u.full_name && u.full_name.toLowerCase().includes(term))
        );
        
        const tbody = document.getElementById('admin-users-tbody');
        if(filtered.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">No matching users</td></tr>';
            return;
        }
        
        tbody.innerHTML = filtered.map(user => `
            <tr>
                <td>
                    <div class="user-cell">
                        <div class="user-cell-avatar">${(user.full_name || user.email).charAt(0).toUpperCase()}</div>
                        <div class="user-cell-info">
                            <div class="user-cell-name">${user.full_name || 'N/A'}</div>
                        </div>
                    </div>
                </td>
                <td>${user.email}</td>
                <td>${user.role}</td>
                <td><span class="badge badge-${user.subscription_tier === 'vip' ? 'premium' : 'secondary'}">${user.subscription_tier.toUpperCase()}</span></td>
                <td><span class="status-badge status-${user.subscription_status === 'active' ? 'active' : 'inactive'}">${user.subscription_status}</span></td>
                <td>${ui.formatDate(user.created_at)}</td>
                <td>
                    <button class="btn btn-sm" onclick="adminUsers.viewDetails(${user.id})"><i class="fas fa-eye"></i></button>
                    <button class="btn btn-sm btn-danger" onclick="adminUsers.disable(${user.id})"><i class="fas fa-ban"></i></button>
                </td>
            </tr>
        `).join('');
    }
};
