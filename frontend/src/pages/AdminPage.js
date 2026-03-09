import { Component } from '../components/Component.js';
import { Sidebar } from '../components/Sidebar.js';
import { api } from '../api/client.js';
import { showLoading } from '../utils/helpers.js';

export class AdminPage extends Component {
    constructor() {
        super();
        this.currentTab = 'dashboard';
    }

    async render() {
        const container = document.createElement('div');
        container.className = 'main-app';
        
        const sidebar = new Sidebar();
        container.appendChild(sidebar.render());
        
        const main = document.createElement('main');
        main.className = 'main-content';
        main.innerHTML = `
            <div class="page-header">
                <h2><i class="fas fa-cog" style="color: var(--primary);"></i> Admin Dashboard</h2>
                <p>Manage users, content, and signals</p>
            </div>
            
            <div class="admin-tabs">
                <button class="tab-btn ${this.currentTab === 'dashboard' ? 'active' : ''}" data-tab="dashboard">Dashboard</button>
                <button class="tab-btn ${this.currentTab === 'users' ? 'active' : ''}" data-tab="users">Users</button>
                <button class="tab-btn ${this.currentTab === 'blog' ? 'active' : ''}" data-tab="blog">Blog</button>
                <button class="tab-btn ${this.currentTab === 'courses' ? 'active' : ''}" data-tab="courses">Courses</button>
                <button class="tab-btn ${this.currentTab === 'webinars' ? 'active' : ''}" data-tab="webinars">Webinars</button>
                <button class="tab-btn ${this.currentTab === 'signals' ? 'active' : ''}" data-tab="signals">Signals</button>
            </div>
            
            <div id="admin-content" class="admin-content">
                <p>Loading...</p>
            </div>
        `;
        
        container.appendChild(main);
        this.element = container;
        
        // Load data after element is set
        setTimeout(() => this.loadData(), 0);
        
        return container;
    }

    bindEvents() {
        if (!this.element) return;
        
        // Tab switching
        const tabButtons = this.element.querySelectorAll('.tab-btn');
        tabButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.currentTab = e.target.dataset.tab;
                this.updateContent(this.currentTab);
                // Update active class
                tabButtons.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });
        
        this.bindForms();
    }

    async loadData() {
        if (!this.element) return;
        
        try {
            showLoading(true, 'Loading admin data...');
            const stats = await api.getStats();
            this.stats = stats;
            this.updateContent(this.currentTab);
        } catch (error) {
            console.error('Failed to load admin data:', error);
            if (this.element) {
                const content = this.element.querySelector('#admin-content');
                if (content) {
                    content.innerHTML = '<p class="text-danger">Failed to load data. Please refresh.</p>';
                }
            }
        } finally {
            showLoading(false);
        }
    }

    updateContent(tab) {
        const contentArea = this.element?.querySelector('#admin-content');
        if (!contentArea) return;
        
        switch(tab) {
            case 'dashboard':
                contentArea.innerHTML = this.renderDashboard();
                break;
            case 'users':
                contentArea.innerHTML = this.renderUsers();
                this.loadUsers();
                break;
            case 'blog':
                contentArea.innerHTML = this.renderBlogForm();
                this.bindForms();
                break;
            case 'courses':
                contentArea.innerHTML = this.renderCourseForm();
                this.bindForms();
                break;
            case 'webinars':
                contentArea.innerHTML = this.renderWebinarForm();
                this.bindForms();
                break;
            case 'signals':
                contentArea.innerHTML = this.renderSignalForm();
                this.bindForms();
                break;
            default:
                contentArea.innerHTML = '<p>Select a tab</p>';
        }
    }

    renderDashboard() {
        if (!this.stats) return '<p>Loading stats...</p>';
        
        return `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">${this.stats.total_users || 0}</div>
                    <div class="stat-label">Total Users</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${this.stats.premium_users || 0}</div>
                    <div class="stat-label">Premium Users</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${this.stats.active_signals || 0}</div>
                    <div class="stat-label">Active Signals</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${this.stats.content_stats?.blog_posts || 0}</div>
                    <div class="stat-label">Blog Posts</div>
                </div>
            </div>
        `;
    }

    renderUsers() {
        return `
            <div class="data-table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Email</th>
                            <th>Name</th>
                            <th>Role</th>
                            <th>Tier</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="users-table-body">
                        <tr><td colspan="5">Loading users...</td></tr>
                    </tbody>
                </table>
            </div>
        `;
    }

    async loadUsers() {
        const tbody = this.element?.querySelector('#users-table-body');
        if (!tbody) return;
        
        try {
            const data = await api.getUsers(1);
            if (data?.users?.length > 0) {
                tbody.innerHTML = data.users.map(user => `
                    <tr>
                        <td>${user.email}</td>
                        <td>${user.full_name || '-'}</td>
                        <td>${user.role}</td>
                        <td><span class="badge badge-${user.subscription_tier === 'premium' ? 'premium' : 'secondary'}">${user.subscription_tier}</span></td>
                        <td>
                            <button class="btn btn-sm btn-danger delete-user" data-id="${user.id}">Delete</button>
                        </td>
                    </tr>
                `).join('');
                
                // Bind delete buttons
                tbody.querySelectorAll('.delete-user').forEach(btn => {
                    btn.addEventListener('click', async (e) => {
                        const userId = e.target.dataset.id;
                        if (confirm('Delete this user?')) {
                            try {
                                await api.deleteUser(userId);
                                this.loadUsers();
                            } catch (err) {
                                alert('Failed to delete user');
                            }
                        }
                    });
                });
            } else {
                tbody.innerHTML = '<tr><td colspan="5">No users found</td></tr>';
            }
        } catch (error) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-danger">Failed to load users</td></tr>';
        }
    }

    renderBlogForm() {
        return `
            <div class="form-container card">
                <h3>Create Blog Post</h3>
                <form id="blog-form">
                    <div class="form-group">
                        <label class="form-label">Title</label>
                        <input type="text" id="blog-title" class="form-input" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Content</label>
                        <textarea id="blog-content" class="form-input" rows="6" required></textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Excerpt</label>
                        <input type="text" id="blog-excerpt" class="form-input">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Category</label>
                        <select id="blog-category" class="form-input">
                            <option value="analysis">Analysis</option>
                            <option value="education">Education</option>
                            <option value="news">News</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">
                            <input type="checkbox" id="blog-premium"> Premium Only
                        </label>
                    </div>
                    <button type="submit" class="btn btn-primary">Create Post</button>
                </form>
            </div>
        `;
    }

    renderCourseForm() {
        return `
            <div class="form-container card">
                <h3>Create Course</h3>
                <form id="course-form">
                    <div class="form-group">
                        <label class="form-label">Title</label>
                        <input type="text" id="course-title" class="form-input" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Description</label>
                        <textarea id="course-description" class="form-input" rows="4" required></textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Level</label>
                        <select id="course-level" class="form-input">
                            <option value="beginner">Beginner</option>
                            <option value="intermediate">Intermediate</option>
                            <option value="advanced">Advanced</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Duration (hours)</label>
                        <input type="number" id="course-duration" class="form-input" value="1">
                    </div>
                    <div class="form-group">
                        <label class="form-label">
                            <input type="checkbox" id="course-premium"> Premium Only
                        </label>
                    </div>
                    <button type="submit" class="btn btn-primary">Create Course</button>
                </form>
            </div>
        `;
    }

    renderWebinarForm() {
        return `
            <div class="form-container card">
                <h3>Create Webinar</h3>
                <form id="webinar-form">
                    <div class="form-group">
                        <label class="form-label">Title</label>
                        <input type="text" id="webinar-title" class="form-input" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Description</label>
                        <textarea id="webinar-description" class="form-input" rows="4"></textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Date & Time</label>
                        <input type="datetime-local" id="webinar-date" class="form-input" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Duration (minutes)</label>
                        <input type="number" id="webinar-duration" class="form-input" value="60">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Max Participants</label>
                        <input type="number" id="webinar-max" class="form-input" value="100">
                    </div>
                    <div class="form-group">
                        <label class="form-label">
                            <input type="checkbox" id="webinar-premium"> Premium Only
                        </label>
                    </div>
                    <button type="submit" class="btn btn-primary">Create Webinar</button>
                </form>
            </div>
        `;
    }

    renderSignalForm() {
        return `
            <div class="form-container card">
                <h3>Create Trading Signal</h3>
                <form id="signal-form">
                    <div class="form-group">
                        <label class="form-label">Currency Pair</label>
                        <input type="text" id="signal-pair" class="form-input" placeholder="EURUSD" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Direction</label>
                        <select id="signal-direction" class="form-input">
                            <option value="buy">Buy</option>
                            <option value="sell">Sell</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Entry Price</label>
                        <input type="number" id="signal-entry" class="form-input" step="0.00001" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Stop Loss</label>
                        <input type="number" id="signal-sl" class="form-input" step="0.00001" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Take Profit</label>
                        <input type="number" id="signal-tp" class="form-input" step="0.00001" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Analysis</label>
                        <textarea id="signal-analysis" class="form-input" rows="3"></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">Create Signal</button>
                </form>
            </div>
        `;
    }

    bindForms() {
        if (!this.element) return;

        // Blog form
        const blogForm = this.element.querySelector('#blog-form');
        if (blogForm) {
            blogForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const titleInput = this.element.querySelector('#blog-title');
                const contentInput = this.element.querySelector('#blog-content');
                const excerptInput = this.element.querySelector('#blog-excerpt');
                const categoryInput = this.element.querySelector('#blog-category');
                const premiumInput = this.element.querySelector('#blog-premium');
                
                if (!titleInput || !contentInput) return;
                
                const formData = {
                    title: titleInput.value,
                    content: contentInput.value,
                    excerpt: excerptInput?.value || '',
                    category: categoryInput?.value || 'analysis',
                    status: 'published',
                    is_premium: premiumInput?.checked || false
                };
                
                try {
                    await api.createPost(formData);
                    alert('Blog post created!');
                    titleInput.value = '';
                    contentInput.value = '';
                    excerptInput && (excerptInput.value = '');
                } catch (err) {
                    alert('Failed to create post: ' + err.message);
                }
            });
        }

        // Course form
        const courseForm = this.element.querySelector('#course-form');
        if (courseForm) {
            courseForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const titleInput = this.element.querySelector('#course-title');
                const descInput = this.element.querySelector('#course-description');
                const levelInput = this.element.querySelector('#course-level');
                const durationInput = this.element.querySelector('#course-duration');
                const premiumInput = this.element.querySelector('#course-premium');
                
                if (!titleInput || !descInput) return;
                
                const formData = {
                    title: titleInput.value,
                    description: descInput.value,
                    content: descInput.value,
                    level: levelInput?.value || 'beginner',
                    duration_hours: parseInt(durationInput?.value || 1),
                    is_premium: premiumInput?.checked || false
                };
                
                try {
                    await api.createCourse(formData);
                    alert('Course created!');
                    courseForm.reset();
                } catch (err) {
                    alert('Failed to create course: ' + err.message);
                }
            });
        }

        // Webinar form
        const webinarForm = this.element.querySelector('#webinar-form');
        if (webinarForm) {
            webinarForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const titleInput = this.element.querySelector('#webinar-title');
                const descInput = this.element.querySelector('#webinar-description');
                const dateInput = this.element.querySelector('#webinar-date');
                const durationInput = this.element.querySelector('#webinar-duration');
                const maxInput = this.element.querySelector('#webinar-max');
                const premiumInput = this.element.querySelector('#webinar-premium');
                
                if (!titleInput || !dateInput) return;
                
                const formData = {
                    title: titleInput.value,
                    description: descInput?.value || '',
                    scheduled_at: dateInput.value,
                    duration_minutes: parseInt(durationInput?.value || 60),
                    max_participants: parseInt(maxInput?.value || 100),
                    is_premium: premiumInput?.checked || false
                };
                
                try {
                    await api.createWebinar(formData);
                    alert('Webinar created!');
                    webinarForm.reset();
                } catch (err) {
                    alert('Failed to create webinar: ' + err.message);
                }
            });
        }

        // Signal form
        const signalForm = this.element.querySelector('#signal-form');
        if (signalForm) {
            signalForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const pairInput = this.element.querySelector('#signal-pair');
                const directionInput = this.element.querySelector('#signal-direction');
                const entryInput = this.element.querySelector('#signal-entry');
                const slInput = this.element.querySelector('#signal-sl');
                const tpInput = this.element.querySelector('#signal-tp');
                const analysisInput = this.element.querySelector('#signal-analysis');
                
                if (!pairInput || !entryInput) return;
                
                const formData = {
                    pair: pairInput.value,
                    direction: directionInput?.value || 'buy',
                    entry_price: parseFloat(entryInput.value),
                    stop_loss: parseFloat(slInput?.value || 0),
                    take_profit: parseFloat(tpInput?.value || 0),
                    analysis: analysisInput?.value || '',
                    is_premium: false
                };
                
                try {
                    await api.createSignal(formData);
                    alert('Signal created!');
                    signalForm.reset();
                } catch (err) {
                    alert('Failed to create signal: ' + err.message);
                }
            });
        }
    }
}
