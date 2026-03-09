
import { Component } from '../components/Component.js';
import { Sidebar } from '../components/Sidebar.js';
import { StatsCard } from '../components/StatsCard.js';
import { DataTable } from '../components/DataTable.js';
import { api } from '../api/client.js';
import { store } from '../state.js';
import { showLoading } from '../utils/helpers.js';

export class AdminPage extends Component {
    constructor() {
        super();
        this.currentTab = 'dashboard';
        this.stats = null;
        this.users = [];
        this.posts = [];
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
                <h2><i class="fas fa-cog" style="color: var(--warning);"></i> Admin Dashboard</h2>
            </div>

            <div class="admin-tabs">
                <button class="tab-btn ${this.currentTab === 'dashboard' ? 'active' : ''}" data-tab="dashboard">
                    <i class="fas fa-chart-bar"></i> Overview
                </button>
                <button class="tab-btn ${this.currentTab === 'users' ? 'active' : ''}" data-tab="users">
                    <i class="fas fa-users"></i> Users
                </button>
                <button class="tab-btn ${this.currentTab === 'blog' ? 'active' : ''}" data-tab="blog">
                    <i class="fas fa-newspaper"></i> Blog
                </button>
                <button class="tab-btn ${this.currentTab === 'courses' ? 'active' : ''}" data-tab="courses">
                    <i class="fas fa-graduation-cap"></i> Courses
                </button>
                <button class="tab-btn ${this.currentTab === 'webinars' ? 'active' : ''}" data-tab="webinars">
                    <i class="fas fa-video"></i> Webinars
                </button>
            </div>

            <div id="admin-content" class="admin-content">
                ${this.renderContent()}
            </div>
        `;

        container.appendChild(main);

        // Load data after rendering
        setTimeout(() => this.loadData(), 0);

        return container;
    }

    renderContent() {
        switch(this.currentTab) {
            case 'dashboard':
                return this.renderDashboard();
            case 'users':
                return this.renderUsers();
            case 'blog':
                return this.renderBlog();
            case 'courses':
                return this.renderCourses();
            case 'webinars':
                return this.renderWebinars();
            default:
                return this.renderDashboard();
        }
    }

    renderDashboard() {
        if (!this.stats) {
            return '<div class="loading">Loading stats...</div>';
        }

        return `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon" style="background: rgba(99,102,241,0.2); color: #6366f1;">
                        <i class="fas fa-users"></i>
                    </div>
                    <div class="stat-content">
                        <h3>${this.stats.total_users || 0}</h3>
                        <p>Total Users</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon" style="background: rgba(245,158,11,0.2); color: #f59e0b;">
                        <i class="fas fa-crown"></i>
                    </div>
                    <div class="stat-content">
                        <h3>${this.stats.premium_users || 0}</h3>
                        <p>Premium Users</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon" style="background: rgba(16,185,129,0.2); color: #10b981;">
                        <i class="fas fa-satellite-dish"></i>
                    </div>
                    <div class="stat-content">
                        <h3>${this.stats.active_signals || 0}</h3>
                        <p>Active Signals</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon" style="background: rgba(236,72,153,0.2); color: #ec4899;">
                        <i class="fas fa-newspaper"></i>
                    </div>
                    <div class="stat-content">
                        <h3>${this.stats.content_stats?.blog_posts || 0}</h3>
                        <p>Blog Posts</p>
                    </div>
                </div>
            </div>
        `;
    }

    renderUsers() {
        if (this.users.length === 0) {
            return '<div class="loading">Loading users...</div>';
        }

        return `
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>User</th>
                            <th>Role</th>
                            <th>Status</th>
                            <th>Joined</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.users.map(user => `
                            <tr>
                                <td>
                                    <div class="user-cell">
                                        <div class="avatar">${(user.full_name || user.email).charAt(0).toUpperCase()}</div>
                                        <div>
                                            <div class="font-medium">${user.full_name || 'No Name'}</div>
                                            <div class="text-sm text-secondary">${user.email}</div>
                                        </div>
                                    </div>
                                </td>
                                <td><span class="badge badge-${user.role === 'admin' ? 'warning' : 'secondary'}">${user.role}</span></td>
                                <td><span class="badge badge-${user.subscription_tier !== 'free' ? 'premium' : 'secondary'}">${user.subscription_tier}</span></td>
                                <td>${new Date(user.created_at).toLocaleDateString()}</td>
                                <td>
                                    <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    renderBlog() {
        return `
            <div class="admin-section">
                <div class="section-header">
                    <h3>Create Blog Post</h3>
                </div>
                <form id="blog-form" class="admin-form">
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Title *</label>
                            <input type="text" name="title" class="form-input" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Category</label>
                            <select name="category" class="form-input">
                                <option value="trading">Trading</option>
                                <option value="analysis">Analysis</option>
                                <option value="education">Education</option>
                                <option value="news">News</option>
                            </select>
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Excerpt</label>
                        <input type="text" name="excerpt" class="form-input" placeholder="Brief description...">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Content *</label>
                        <textarea name="content" class="form-input" rows="10" required placeholder="Write your content here..."></textarea>
                    </div>

                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Meta Title (SEO)</label>
                            <input type="text" name="meta_title" class="form-input">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Meta Description (SEO)</label>
                            <input type="text" name="meta_description" class="form-input">
                        </div>
                    </div>

                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Tags (comma separated)</label>
                            <input type="text" name="tags" class="form-input" placeholder="forex, trading, gold">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Featured Image URL</label>
                            <input type="url" name="featured_image" class="form-input" placeholder="https://...">
                        </div>
                    </div>

                    <div class="form-row">
                        <label class="checkbox-label">
                            <input type="checkbox" name="is_premium"> Premium Content
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" name="status" value="published" checked> Publish Immediately
                        </label>
                    </div>

                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-plus"></i> Create Post
                    </button>
                </form>
            </div>
        `;
    }

    renderCourses() {
        return `
            <div class="admin-section">
                <h3>Create Course</h3>
                <form id="course-form" class="admin-form">
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Title *</label>
                            <input type="text" name="title" class="form-input" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Level</label>
                            <select name="level" class="form-input">
                                <option value="beginner">Beginner</option>
                                <option value="intermediate">Intermediate</option>
                                <option value="advanced">Advanced</option>
                            </select>
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Description *</label>
                        <textarea name="description" class="form-input" rows="3" required></textarea>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Content (Markdown supported)</label>
                        <textarea name="content" class="form-input" rows="6" placeholder="Full course content..."></textarea>
                    </div>

                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Duration (hours)</label>
                            <input type="number" name="duration_hours" class="form-input" step="0.5" placeholder="2.5">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Thumbnail URL</label>
                            <input type="url" name="thumbnail" class="form-input" placeholder="https://...">
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Modules (JSON format)</label>
                        <textarea name="modules" class="form-input" rows="3" placeholder='[{"title": "Intro", "content": "..."}]'></textarea>
                    </div>

                    <label class="checkbox-label">
                        <input type="checkbox" name="is_premium"> Premium Course
                    </label>

                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-plus"></i> Create Course
                    </button>
                </form>
            </div>
        `;
    }

    renderWebinars() {
        return `
            <div class="admin-section">
                <h3>Create Webinar</h3>
                <form id="webinar-form" class="admin-form">
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Title *</label>
                            <input type="text" name="title" class="form-input" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Scheduled Date/Time *</label>
                            <input type="datetime-local" name="scheduled_at" class="form-input" required>
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Description *</label>
                        <textarea name="description" class="form-input" rows="3" required></textarea>
                    </div>

                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Duration (minutes)</label>
                            <input type="number" name="duration_minutes" class="form-input" value="60" min="15">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Max Participants</label>
                            <input type="number" name="max_participants" class="form-input" value="100" min="1">
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Meeting Link (Zoom/Google Meet)</label>
                        <input type="url" name="meeting_link" class="form-input" placeholder="https://zoom.us/j/...">
                    </div>

                    <label class="checkbox-label">
                        <input type="checkbox" name="is_premium"> Premium Webinar
                    </label>

                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-video"></i> Create Webinar
                    </button>
                </form>
            </div>
        `;
    }

    async loadData() {
        if (this.currentTab === 'dashboard' && !this.stats) {
            showLoading(true, 'Loading stats...');
            try {
                this.stats = await api.getStats();
                this.updateContent();
            } catch (e) {
                console.error(e);
            } finally {
                showLoading(false);
            }
        } else if (this.currentTab === 'users' && this.users.length === 0) {
            showLoading(true, 'Loading users...');
            try {
                const data = await api.getUsers(1);
                this.users = data.users || [];
                this.updateContent();
            } catch (e) {
                console.error(e);
            } finally {
                showLoading(false);
            }
        }
    }

    updateContent() {
        const content = document.getElementById('admin-content');
        if (content) {
            content.innerHTML = this.renderContent();
            this.bindForms();
        }
    }

    bindEvents() {
        // Tab switching
        this.element.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.currentTab = e.currentTarget.dataset.tab;
                this.updateContent();
                this.loadData();

                // Update active tab UI
                this.element.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');
            });
        });

        this.bindForms();
    }

    bindForms() {
        // Blog form
        const blogForm = this.element.querySelector('#blog-form');
        if (blogForm) {
            blogForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(blogForm);
                const data = {
                    title: formData.get('title'),
                    content: formData.get('content'),
                    excerpt: formData.get('excerpt'),
                    category: formData.get('category'),
                    status: formData.has('status') ? 'published' : 'draft',
                    meta_title: formData.get('meta_title'),
                    meta_description: formData.get('meta_description'),
                    tags: formData.get('tags') ? formData.get('tags').split(',').map(t => t.trim()) : [],
                    featured_image: formData.get('featured_image'),
                    is_premium: formData.has('is_premium')
                };

                try {
                    showLoading(true, 'Creating post...');
                    await api.createPost(data);
                    api.showToast('Blog post created!', 'success');
                    blogForm.reset();
                } catch (error) {
                    console.error(error);
                } finally {
                    showLoading(false);
                }
            });
        }

        // Course form
        const courseForm = this.element.querySelector('#course-form');
        if (courseForm) {
            courseForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(courseForm);
                const data = {
                    title: formData.get('title'),
                    description: formData.get('description'),
                    content: formData.get('content'),
                    level: formData.get('level'),
                    duration_hours: parseFloat(formData.get('duration_hours')) || null,
                    thumbnail: formData.get('thumbnail'),
                    is_premium: formData.has('is_premium'),
                    modules: formData.get('modules') ? JSON.parse(formData.get('modules')) : []
                };

                try {
                    showLoading(true, 'Creating course...');
                    await api.createCourse(data);
                    api.showToast('Course created!', 'success');
                    courseForm.reset();
                } catch (error) {
                    console.error(error);
                } finally {
                    showLoading(false);
                }
            });
        }

        // Webinar form
        const webinarForm = this.element.querySelector('#webinar-form');
        if (webinarForm) {
            webinarForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(webinarForm);
                const data = {
                    title: formData.get('title'),
                    description: formData.get('description'),
                    scheduled_at: formData.get('scheduled_at'),
                    duration_minutes: parseInt(formData.get('duration_minutes')) || 60,
                    max_participants: parseInt(formData.get('max_participants')) || 100,
                    meeting_link: formData.get('meeting_link'),
                    is_premium: formData.has('is_premium')
                };

                try {
                    showLoading(true, 'Creating webinar...');
                    await api.createWebinar(data);
                    api.showToast('Webinar created!', 'success');
                    webinarForm.reset();
                } catch (error) {
                    console.error(error);
                } finally {
                    showLoading(false);
                }
            });
        }
    }
}

window.deleteUser = async (id) => {
    if (confirm('Are you sure you want to delete this user?')) {
        try {
            await api.deleteUser(id);
            api.showToast('User deleted', 'success');
            // Reload page to refresh list
            window.location.reload();
        } catch (e) {
            console.error(e);
        }
    }
};
