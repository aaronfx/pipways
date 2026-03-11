/**
 * Admin Dashboard Module
 */
const admin = {
    async loadDashboard(container) {
        if (!auth.requireAdmin()) {
            container.innerHTML = '<div class="error">Admin access required</div>';
            return;
        }

        container.innerHTML = '<div class="loading">Loading dashboard...</div>';

        try {
            const stats = await api.get('/api/admin/dashboard/stats');
            const users = await api.get('/api/admin/users?limit=5');

            const html = `
                <div class="page-header">
                    <h1>Admin Dashboard</h1>
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                    <div class="card" style="text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold; color: var(--primary);">${stats.total_users || 0}</div>
                        <div>Total Users</div>
                    </div>
                    <div class="card" style="text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold; color: var(--success);">${stats.new_users_30d || 0}</div>
                        <div>New (30d)</div>
                    </div>
                    <div class="card" style="text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold; color: var(--warning);">${stats.vip_users || 0}</div>
                        <div>VIP Users</div>
                    </div>
                    <div class="card" style="text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold; color: var(--info);">${stats.published_posts || 0}</div>
                        <div>Blog Posts</div>
                    </div>
                </div>

                <div class="grid">
                    <div class="card">
                        <div class="card-header">
                            <h3>Recent Users</h3>
                            <a href="#" onclick="admin.loadUsers(); return false;">View All</a>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Email</th>
                                    <th>Role</th>
                                    <th>Tier</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${users.map(u => `
                                    <tr>
                                        <td>${u.full_name || 'N/A'}</td>
                                        <td>${u.email}</td>
                                        <td><span class="badge badge-${u.role === 'admin' ? 'danger' : 'info'}">${u.role}</span></td>
                                        <td><span class="badge badge-${u.subscription_tier === 'vip' ? 'premium' : 'secondary'}">${u.subscription_tier}</span></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h3>Quick Actions</h3>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                            <button onclick="admin.loadAdminSignals()">Manage Signals</button>
                            <button onclick="window.location='/blog'">Manage Blog</button>
                            <button onclick="window.location='/courses'">Manage Courses</button>
                            <button onclick="window.location='/webinars'">Manage Webinars</button>
                        </div>
                    </div>
                </div>
            `;

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="error">Failed to load dashboard: ${error.message}</div>`;
        }
    },

    async loadUsers() {
        const container = document.getElementById('main-content');
        container.innerHTML = '<div class="loading">Loading users...</div>';

        try {
            const users = await api.get('/api/admin/users?limit=50');

            const html = `
                <div class="page-header">
                    <h1>User Management</h1>
                    <button onclick="admin.loadDashboard(document.getElementById('main-content'))">Back to Dashboard</button>
                </div>
                <div class="card">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Role</th>
                                <th>Tier</th>
                                <th>Joined</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${users.map(u => `
                                <tr>
                                    <td>${u.id}</td>
                                    <td>${u.full_name || 'N/A'}</td>
                                    <td>${u.email}</td>
                                    <td>
                                        <select onchange="admin.updateUser(${u.id}, 'role', this.value)">
                                            <option value="user" ${u.role === 'user' ? 'selected' : ''}>User</option>
                                            <option value="moderator" ${u.role === 'moderator' ? 'selected' : ''}>Moderator</option>
                                            <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>Admin</option>
                                        </select>
                                    </td>
                                    <td>
                                        <select onchange="admin.updateUser(${u.id}, 'subscription_tier', this.value)">
                                            <option value="free" ${u.subscription_tier === 'free' ? 'selected' : ''}>Free</option>
                                            <option value="vip" ${u.subscription_tier === 'vip' ? 'selected' : ''}>VIP</option>
                                        </select>
                                    </td>
                                    <td>${ui.formatDate(u.created_at)}</td>
                                    <td>
                                        <button class="secondary" onclick="admin.deleteUser(${u.id})">Delete</button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="error">Failed to load users: ${error.message}</div>`;
        }
    },

    async loadAdminSignals() {
        const container = document.getElementById('main-content');
        container.innerHTML = '<div class="loading">Loading signals...</div>';

        try {
            const signals = await api.get('/api/admin/signals?limit=100');

            const html = `
                <div class="page-header">
                    <h1>Signal Management</h1>
                    <button onclick="admin.showCreateSignalModal()">Create Signal</button>
                    <button onclick="admin.loadDashboard(document.getElementById('main-content'))">Back</button>
                </div>
                <div class="card">
                    <table>
                        <thead>
                            <tr>
                                <th>Pair</th>
                                <th>Direction</th>
                                <th>Entry</th>
                                <th>Status</th>
                                <th>Result</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${signals.map(s => `
                                <tr>
                                    <td><strong>${s.pair}</strong></td>
                                    <td><span class="badge badge-${s.direction === 'buy' ? 'success' : 'danger'}">${s.direction}</span></td>
                                    <td>${s.entry_price}</td>
                                    <td>${s.status}</td>
                                    <td>${s.result || 'Pending'}</td>
                                    <td>
                                        <button onclick="admin.editSignal(${s.id})">Edit</button>
                                        <button class="secondary" onclick="admin.deleteSignal(${s.id})">Delete</button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="error">Failed to load signals: ${error.message}</div>`;
        }
    },

    showCreateSignalModal() {
        // Implementation placeholder - would open modal with form
        ui.showToast('Signal creation modal would open here');
    },

    async editSignal(signalId) {
        ui.showToast('Edit signal form for ID: ' + signalId);
    },

    async deleteSignal(signalId) {
        if (!confirm('Delete this signal?')) return;
        try {
            await api.delete(`/api/admin/signals/${signalId}`);
            ui.showToast('Signal deleted', 'success');
            this.loadAdminSignals();
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    },

    async updateUser(userId, field, value) {
        try {
            await api.put(`/api/admin/users/${userId}`, { [field]: value });
            ui.showToast('User updated', 'success');
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    },

    async deleteUser(userId) {
        if (!confirm('Delete this user?')) return;
        try {
            await api.delete(`/api/admin/users/${userId}`);
            ui.showToast('User deleted', 'success');
            this.loadUsers();
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    }
};
