const AdminPage = {
    async render(container) {
        container.innerHTML = '<div class="page-header"><h1>Admin Panel</h1></div>';

        try {
            const stats = await API.getAdminStats();

            container.innerHTML += `
                <div class="stats-grid">
                    <div class="stat-card">
                        <h4>Total Users</h4>
                        <p class="stat-number">${stats.total_users}</p>
                    </div>
                    <div class="stat-card">
                        <h4>Active Signals</h4>
                        <p class="stat-number">${stats.active_signals}</p>
                    </div>
                    <div class="stat-card">
                        <h4>Courses</h4>
                        <p class="stat-number">${stats.total_courses}</p>
                    </div>
                    <div class="stat-card">
                        <h4>Upcoming Webinars</h4>
                        <p class="stat-number">${stats.upcoming_webinars}</p>
                    </div>
                </div>

                <div class="admin-section" style="margin-top: 2rem; background: white; padding: 1.5rem; border-radius: 0.5rem;">
                    <h3>Recent Users</h3>
                    <div class="table-responsive">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Username</th>
                                    <th>Email</th>
                                    <th>Joined</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${stats.recent_users.map(u => `
                                    <tr>
                                        <td>${UI.escapeHtml(u.username)}</td>
                                        <td>${UI.escapeHtml(u.email)}</td>
                                        <td>${UI.formatDate(u.created_at)}</td>
                                        <td>
                                            <span class="badge ${u.is_active ? 'badge-success' : 'badge-danger'}">
                                                ${u.is_active ? 'Active' : 'Inactive'}
                                            </span>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } catch (error) {
            container.innerHTML += '<p>Failed to load admin data</p>';
        }
    }
};