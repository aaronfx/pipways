/**
 * Admin Dashboard Module
 * Handles content management, user management, and settings
 */

const admin = {
    currentTab: 'content',

    async loadStats() {
        try {
            const stats = await api.get('/api/admin/dashboard/stats');
            
            document.getElementById('stat-total-users').textContent = stats.total_users || 0;
            document.getElementById('stat-active-signals').textContent = stats.active_signals || 0;
            document.getElementById('stat-premium-users').textContent = stats.vip_users || 0;
            document.getElementById('stat-blog-posts').textContent = stats.published_posts || 0;
            
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    },

    showTab(tabName, btnElement) {
        // Hide all panels
        document.querySelectorAll('.admin-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        
        // Show target panel
        document.getElementById(`panel-${tabName}`).classList.add('active');
        
        // Update tab buttons
        document.querySelectorAll('.admin-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        btnElement.classList.add('active');
        
        this.currentTab = tabName;

        // Load tab-specific data
        switch(tabName) {
            case 'content':
                this.loadBlogPosts();
                break;
            case 'users':
                this.loadUsers();
                break;
            case 'courses':
                this.loadAdminCourses();
                break;
            case 'webinars':
                this.loadAdminWebinars();
                break;
            case 'signals':
                this.loadAdminSignals();
                break;
            case 'settings':
                this.loadSettings();
                break;
        }
    },

    // Blog Management
    async loadBlogPosts() {
        const tbody = document.getElementById('blog-table-body');
        if (!tbody) return;

        try {
            const posts = await api.get('/blog?limit=50');
            
            tbody.innerHTML = posts.map(post => `
                <tr>
                    <td>${post.title}</td>
                    <td><span class="badge badge-${post.status === 'published' ? 'success' : 'secondary'}">${post.status}</span></td>
                    <td>${post.category || '-'}</td>
                    <td>${ui.formatDate(post.created_at)}</td>
                    <td>
                        <button class="btn btn-sm" onclick="admin.editBlogPost(${post.id})">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="admin.deleteBlogPost(${post.id})">Delete</button>
                    </td>
                </tr>
            `).join('');
            
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--danger);">Error: ${error.message}</td></tr>`;
        }
    },

    openBlogModal() {
        document.getElementById('blog-form').reset();
        document.getElementById('blog-post-id').value = '';
        document.getElementById('blog-modal-title').textContent = 'Create Blog Post';
        ui.openModal('blog-modal');
    },

    async editBlogPost(id) {
        try {
            const post = await api.get(`/blog/${id}`);
            
            document.getElementById('blog-post-id').value = post.id;
            document.getElementById('blog-title').value = post.title;
            document.getElementById('blog-content').value = post.content;
            document.getElementById('blog-category-select').value = post.category || 'Trading';
            document.getElementById('blog-status').value = post.status || 'draft';
            document.getElementById('blog-image').value = post.featured_image || '';
            document.getElementById('blog-is-premium').checked = post.is_premium || false;
            
            document.getElementById('blog-modal-title').textContent = 'Edit Blog Post';
            ui.openModal('blog-modal');
            
        } catch (error) {
            ui.showToast('Error loading post: ' + error.message, 'error');
        }
    },

    async submitBlogPost() {
        const id = document.getElementById('blog-post-id').value;
        const data = {
            title: document.getElementById('blog-title').value,
            content: document.getElementById('blog-content').value,
            category: document.getElementById('blog-category-select').value,
            status: document.getElementById('blog-status').value,
            featured_image: document.getElementById('blog-image').value,
            is_premium: document.getElementById('blog-is-premium').checked
        };

        try {
            if (id) {
                await api.put(`/blog/${id}`, data);
            } else {
                await api.post('/blog', data);
            }
            
            ui.closeModal('blog-modal');
            ui.showToast('Blog post saved successfully', 'success');
            this.loadBlogPosts();
            
        } catch (error) {
            ui.showToast('Error saving post: ' + error.message, 'error');
        }
    },

    async deleteBlogPost(id) {
        if (!confirm('Are you sure you want to delete this post?')) return;
        
        try {
            await api.delete(`/blog/${id}`);
            ui.showToast('Post deleted', 'success');
            this.loadBlogPosts();
        } catch (error) {
            ui.showToast('Error: ' + error.message, 'error');
        }
    },

    // User Management
    async loadUsers() {
        const tbody = document.getElementById('users-table-body');
        if (!tbody) return;

        try {
            const users = await api.get('/api/admin/users?limit=50');
            
            tbody.innerHTML = users.map(user => `
                <tr>
                    <td>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div class="user-avatar" style="width: 32px; height: 32px; font-size: 14px;">${(user.full_name || user.email).charAt(0).toUpperCase()}</div>
                            <div>
                                <div>${user.full_name || 'N/A'}</div>
                                <small style="color: var(--text-secondary);">${user.email}</small>
                            </div>
                        </div>
                    </td>
                    <td>
                        <select onchange="admin.updateUserRole(${user.id}, this.value)" class="form-select" style="width: auto;">
                            <option value="user" ${user.role === 'user' ? 'selected' : ''}>User</option>
                            <option value="moderator" ${user.role === 'moderator' ? 'selected' : ''}>Moderator</option>
                            <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>Admin</option>
                        </select>
                    </td>
                    <td>
                        <select onchange="admin.updateUserTier(${user.id}, this.value)" class="form-select" style="width: auto;">
                            <option value="free" ${user.subscription_tier === 'free' ? 'selected' : ''}>Free</option>
                            <option value="vip" ${user.subscription_tier === 'vip' ? 'selected' : ''}>VIP</option>
                        </select>
                    </td>
                    <td>${ui.formatDate(user.created_at)}</td>
                    <td>
                        <button class="btn btn-sm btn-danger" onclick="admin.deleteUser(${user.id})">Delete</button>
                    </td>
                </tr>
            `).join('');
            
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--danger);">Error: ${error.message}</td></tr>`;
        }
    },

    async updateUserRole(userId, role) {
        try {
            await api.put(`/api/admin/users/${userId}`, { role });
            ui.showToast('User role updated', 'success');
        } catch (error) {
            ui.showToast('Error: ' + error.message, 'error');
        }
    },

    async updateUserTier(userId, tier) {
        try {
            await api.put(`/api/admin/users/${userId}`, { subscription_tier: tier });
            ui.showToast('User tier updated', 'success');
        } catch (error) {
            ui.showToast('Error: ' + error.message, 'error');
        }
    },

    async deleteUser(userId) {
        if (!confirm('Delete this user? This cannot be undone.')) return;
        
        try {
            await api.delete(`/api/admin/users/${userId}`);
            ui.showToast('User deleted', 'success');
            this.loadUsers();
        } catch (error) {
            ui.showToast('Error: ' + error.message, 'error');
        }
    },

    // Course Management
    async loadAdminCourses() {
        const container = document.getElementById('admin-courses-list');
        if (!container) return;

        try {
            const courses = await api.get('/courses');
            
            container.innerHTML = courses.map(course => `
                <div class="card" style="margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4>${course.title} ${course.is_premium ? '<span class="badge badge-premium">Premium</span>' : ''}</h4>
                        <p style="color: var(--text-secondary); font-size: 0.9rem;">${course.level || 'All Levels'} • ${course.modules?.length || 0} modules</p>
                    </div>
                    <div style="display: flex; gap: 0.5rem;">
                        <button class="btn btn-sm" onclick="admin.editCourse(${course.id})">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="admin.deleteCourse(${course.id})">Delete</button>
                    </div>
                </div>
            `).join('');
            
        } catch (error) {
            container.innerHTML = `<p style="color: var(--danger);">Error: ${error.message}</p>`;
        }
    },

    openCourseModal() {
        document.getElementById('course-form').reset();
        document.getElementById('course-id').value = '';
        document.getElementById('course-modal-title').textContent = 'Create Course';
        ui.openModal('course-modal');
    },

    async editCourse(id) {
        try {
            const course = await api.get(`/courses/${id}`);
            
            document.getElementById('course-id').value = course.id;
            document.getElementById('course-title').value = course.title;
            document.getElementById('course-description').value = course.description;
            document.getElementById('course-content').value = course.content || '';
            document.getElementById('course-level-select').value = course.level || 'beginner';
            document.getElementById('course-duration').value = course.duration_hours || '';
            document.getElementById('course-thumbnail').value = course.thumbnail || '';
            document.getElementById('course-is-premium').checked = course.is_premium || false;
            
            document.getElementById('course-modal-title').textContent = 'Edit Course';
            ui.openModal('course-modal');
            
        } catch (error) {
            ui.showToast('Error loading course: ' + error.message, 'error');
        }
    },

    async submitCourse() {
        const id = document.getElementById('course-id').value;
        const data = {
            title: document.getElementById('course-title').value,
            description: document.getElementById('course-description').value,
            content: document.getElementById('course-content').value,
            level: document.getElementById('course-level-select').value,
            duration_hours: parseFloat(document.getElementById('course-duration').value) || null,
            thumbnail: document.getElementById('course-thumbnail').value,
            is_premium: document.getElementById('course-is-premium').checked
        };

        try {
            if (id) {
                await api.put(`/courses/${id}`, data);
            } else {
                await api.post('/courses', data);
            }
            
            ui.closeModal('course-modal');
            ui.showToast('Course saved successfully', 'success');
            this.loadAdminCourses();
            
        } catch (error) {
            ui.showToast('Error: ' + error.message, 'error');
        }
    },

    async deleteCourse(id) {
        if (!confirm('Delete this course and all its modules?')) return;
        
        try {
            await api.delete(`/courses/${id}`);
            ui.showToast('Course deleted', 'success');
            this.loadAdminCourses();
        } catch (error) {
            ui.showToast('Error: ' + error.message, 'error');
        }
    },

    // Webinar Management
    async loadAdminWebinars() {
        const container = document.getElementById('admin-webinars-list');
        if (!container) return;

        try {
            const webinars = await api.get('/webinars');
            
            container.innerHTML = webinars.map(w => `
                <div class="card" style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <h4>${w.title} ${w.is_premium ? '<span class="badge badge-premium">VIP</span>' : ''}</h4>
                            <p style="color: var(--text-secondary);">${ui.formatDate(w.scheduled_at)} • ${w.duration_minutes} mins</p>
                        </div>
                        <div style="display: flex; gap: 0.5rem;">
                            <button class="btn btn-sm" onclick="admin.editWebinar(${w.id})">Edit</button>
                            <button class="btn btn-sm btn-danger" onclick="admin.deleteWebinar(${w.id})">Delete</button>
                        </div>
                    </div>
                </div>
            `).join('');
            
        } catch (error) {
            container.innerHTML = `<p style="color: var(--danger);">Error: ${error.message}</p>`;
        }
    },

    openWebinarModal() {
        document.getElementById('webinar-form').reset();
        document.getElementById('webinar-id').value = '';
        document.getElementById('webinar-modal-title').textContent = 'Create Webinar';
        ui.openModal('webinar-modal');
    },

    async editWebinar(id) {
        try {
            const webinars = await api.get('/webinars');
            const webinar = webinars.find(w => w.id === id);
            if (!webinar) throw new Error('Webinar not found');

            document.getElementById('webinar-id').value = webinar.id;
            document.getElementById('webinar-title').value = webinar.title;
            document.getElementById('webinar-description').value = webinar.description;
            document.getElementById('webinar-scheduled').value = new Date(webinar.scheduled_at).toISOString().slice(0, 16);
            document.getElementById('webinar-duration').value = webinar.duration_minutes;
            document.getElementById('webinar-link').value = webinar.meeting_link || '';
            document.getElementById('webinar-max').value = webinar.max_participants || 100;
            document.getElementById('webinar-reminder').value = webinar.reminder_message || '';
            document.getElementById('webinar-is-premium').checked = webinar.is_premium || false;
            
            document.getElementById('webinar-modal-title').textContent = 'Edit Webinar';
            ui.openModal('webinar-modal');
            
        } catch (error) {
            ui.showToast('Error: ' + error.message, 'error');
        }
    },

    async submitWebinar() {
        const id = document.getElementById('webinar-id').value;
        const data = {
            title: document.getElementById('webinar-title').value,
            description: document.getElementById('webinar-description').value,
            scheduled_at: new Date(document.getElementById('webinar-scheduled').value).toISOString(),
            duration_minutes: parseInt(document.getElementById('webinar-duration').value),
            meeting_link: document.getElementById('webinar-link').value,
            max_participants: parseInt(document.getElementById('webinar-max').value) || 100,
            reminder_message: document.getElementById('webinar-reminder').value,
            is_premium: document.getElementById('webinar-is-premium').checked
        };

        try {
            if (id) {
                await api.put(`/webinars/${id}`, data);
            } else {
                await api.post('/webinars', data);
            }
            
            ui.closeModal('webinar-modal');
            ui.showToast('Webinar saved', 'success');
            this.loadAdminWebinars();
            
        } catch (error) {
            ui.showToast('Error: ' + error.message, 'error');
        }
    },

    async deleteWebinar(id) {
        if (!confirm('Delete this webinar?')) return;
        
        try {
            await api.delete(`/webinars/${id}`);
            ui.showToast('Webinar deleted', 'success');
            this.loadAdminWebinars();
        } catch (error) {
            ui.showToast('Error: ' + error.message, 'error');
        }
    },

    // Signal Management
    async loadAdminSignals() {
        const tbody = document.getElementById('admin-signals-table-body');
        if (!tbody) return;

        try {
            const signals = await api.get('/api/admin/signals');
            
            tbody.innerHTML = signals.map(s => `
                <tr>
                    <td><strong>${s.pair}</strong></td>
                    <td><span class="badge badge-${s.direction === 'buy' ? 'success' : 'danger'}">${s.direction}</span></td>
                    <td>${ui.formatPrice(s.entry_price)}</td>
                    <td>${s.status}</td>
                    <td>${s.result || '-'}</td>
                    <td>
                        <button class="btn btn-sm" onclick="admin.editSignal(${s.id})">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="admin.deleteSignal(${s.id})">Delete</button>
                    </td>
                </tr>
            `).join('');
            
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--danger);">Error: ${error.message}</td></tr>`;
        }
    },

    openSignalModal() {
        document.getElementById('signal-form').reset();
        document.getElementById('signal-id').value = '';
        document.getElementById('signal-modal-title').textContent = 'Create Signal';
        ui.openModal('signal-modal');
    },

    async editSignal(id) {
        try {
            const signals = await api.get('/api/admin/signals');
            const signal = signals.find(s => s.id === id);
            
            document.getElementById('signal-id').value = signal.id;
            document.getElementById('signal-pair').value = signal.pair;
            document.getElementById('signal-direction').value = signal.direction;
            document.getElementById('signal-entry').value = signal.entry_price;
            document.getElementById('signal-sl').value = signal.stop_loss || '';
            document.getElementById('signal-tp1').value = signal.tp1 || '';
            document.getElementById('signal-tp2').value = signal.tp2 || '';
            document.getElementById('signal-analysis').value = signal.analysis || '';
            document.getElementById('signal-is-premium').checked = signal.is_premium || false;
            
            document.getElementById('signal-modal-title').textContent = 'Edit Signal';
            ui.openModal('signal-modal');
            
        } catch (error) {
            ui.showToast('Error: ' + error.message, 'error');
        }
    },

    async submitSignal() {
        const id = document.getElementById('signal-id').value;
        const data = {
            pair: document.getElementById('signal-pair').value,
            direction: document.getElementById('signal-direction').value,
            entry_price: parseFloat(document.getElementById('signal-entry').value),
            stop_loss: parseFloat(document.getElementById('signal-sl').value) || null,
            tp1: parseFloat(document.getElementById('signal-tp1').value) || null,
            tp2: parseFloat(document.getElementById('signal-tp2').value) || null,
            analysis: document.getElementById('signal-analysis').value,
            is_premium: document.getElementById('signal-is-premium').checked
        };

        try {
            if (id) {
                await api.put(`/api/admin/signals/${id}`, data);
            } else {
                await api.post('/api/admin/signals', data);
            }
            
            ui.closeModal('signal-modal');
            ui.showToast('Signal saved', 'success');
            this.loadAdminSignals();
            
        } catch (error) {
            ui.showToast('Error: ' + error.message, 'error');
        }
    },

    async deleteSignal(id) {
        if (!confirm('Delete this signal?')) return;
        
        try {
            await api.delete(`/api/admin/signals/${id}`);
            ui.showToast('Signal deleted', 'success');
            this.loadAdminSignals();
        } catch (error) {
            ui.showToast('Error: ' + error.message, 'error');
        }
    },

    // Settings
    async loadSettings() {
        try {
            const settings = await api.get('/api/admin/settings');
            
            document.getElementById('setting-site-name').value = settings.site_name || '';
            document.getElementById('setting-contact-email').value = settings.contact_email || '';
            document.getElementById('setting-telegram-free').value = settings.telegram_free_link || '';
            document.getElementById('setting-telegram-vip').value = settings.telegram_vip_link || '';
            document.getElementById('setting-vip-price').value = settings.vip_price || '';
            document.getElementById('setting-vip-currency').value = settings.vip_price_currency || 'USD';
            
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    },

    async updateSettings(e) {
        e.preventDefault();
        
        const data = {
            site_name: document.getElementById('setting-site-name').value,
            contact_email: document.getElementById('setting-contact-email').value,
            telegram_free_link: document.getElementById('setting-telegram-free').value,
            telegram_vip_link: document.getElementById('setting-telegram-vip').value,
            vip_price: parseFloat(document.getElementById('setting-vip-price').value) || null,
            vip_price_currency: document.getElementById('setting-vip-currency').value
        };

        try {
            await api.put('/api/admin/settings', data);
            ui.showToast('Settings saved', 'success');
        } catch (error) {
            ui.showToast('Error: ' + error.message, 'error');
        }
    },

    // Media Upload
    async handleMediaUpload(input) {
        const files = input.files;
        if (!files.length) return;

        ui.showLoading('Uploading...');

        try {
            const formData = new FormData();
            for (let file of files) {
                formData.append('files', file);
            }

            const response = await api.upload('/api/admin/media/upload', formData);
            ui.showToast('Upload successful', 'success');
            
            // Display uploaded files
            const container = document.getElementById('media-list');
            container.innerHTML = (response.urls || []).map(url => `
                <div style="display: inline-block; margin: 5px; position: relative;">
                    <img src="${url}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px;">
                    <button onclick="navigator.clipboard.writeText('${url}'); ui.showToast('URL copied')" class="btn btn-sm" style="position: absolute; bottom: 5px; right: 5px; padding: 2px 6px;">
                        <i class="fas fa-copy"></i>
                    </button>
                </div>
            `).join('');
            
        } catch (error) {
            ui.showToast('Upload failed: ' + error.message, 'error');
        } finally {
            ui.hideLoading();
        }
    },

    openQuizModal() {
        ui.openModal('quiz-modal');
    },

    async submitQuiz() {
        // Implementation depends on your quiz schema
        ui.showToast('Quiz creation - implement based on your backend schema', 'info');
        ui.closeModal('quiz-modal');
    }
};
