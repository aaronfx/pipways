const DashboardPage = {
    async render(container) {
        container.innerHTML = `
            <div class="page-header">
                <h1>My Dashboard</h1>
            </div>
            <div class="dashboard-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem;">
                <div class="dashboard-card" style="background: white; padding: 1.5rem; border-radius: 0.5rem;">
                    <h3>Active Signals</h3>
                    <p class="stat" style="font-size: 2rem; font-weight: 700; color: #3b82f6;">${Store.state.signals.filter(s => s.status === 'ACTIVE').length}</p>
                </div>
                <div class="dashboard-card" style="background: white; padding: 1.5rem; border-radius: 0.5rem;">
                    <h3>Course Progress</h3>
                    <p class="stat" style="font-size: 2rem; font-weight: 700; color: #3b82f6;">0%</p>
                    <button onclick="Router.go('#/courses')" class="btn btn-secondary" style="margin-top: 0.5rem;">Continue Learning</button>
                </div>
                <div class="dashboard-card" style="background: white; padding: 1.5rem; border-radius: 0.5rem;">
                    <h3>Risk Calculator</h3>
                    <p style="margin-bottom: 1rem;">Calculate optimal position sizes</p>
                    <button onclick="Router.go('#/risk-calculator')" class="btn btn-primary">Open Calculator</button>
                </div>
            </div>

            <div class="quick-actions" style="margin-top: 2rem; background: white; padding: 1.5rem; border-radius: 0.5rem;">
                <h3>Quick Actions</h3>
                <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                    <button onclick="Router.go('#/signals')" class="btn btn-secondary">View Signals</button>
                    <button onclick="Router.go('#/blog')" class="btn btn-secondary">Read Blog</button>
                    <button onclick="Router.go('#/webinars')" class="btn btn-secondary">Join Webinars</button>
                </div>
            </div>
        `;
    }
};