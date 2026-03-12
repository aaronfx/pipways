/**
 * Admin Blog CMS Module
 */

const adminBlog = {
    posts: [],
    editingId: null,
    
    async load() {
        const tbody = document.getElementById('admin-blog-tbody');
        if(!tbody) return;
        
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Loading posts...</td></tr>';
        
        try {
            const response = await api.get('/api/admin/blog');
            this.posts = response.posts || [];
            this.render();
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error: ${error.message}</td></tr>`;
        }
    },
    
    render() {
        const tbody = document.getElementById('admin-blog-tbody');
        const categoryFilter = document.getElementById('blog-category-filter')?.value;
        const statusFilter = document.getElementById('blog-status-filter')?.value;
        
        let filtered = this.posts;
        if(categoryFilter) {
            filtered = filtered.filter(p => p.category === categoryFilter);
        }
        if(statusFilter) {
            filtered = filtered.filter(p => p.status === statusFilter);
        }
        
        if(filtered.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No posts found</td></tr>';
            return;
        }
        
        tbody.innerHTML = filtered.map(post => `
            <tr>
                <td>
                    <div style="display: flex; align-items: center; gap: 12px;">
                        ${post.featured_image ? `<img src="${post.featured_image}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px;">` : '<div style="width: 40px; height: 40px; background: var(--bg-hover); border-radius: 4px; display: flex; align-items: center; justify-content: center;"><i class="fas fa-image" style="color: var(--text-secondary);"></i></div>'}
                        <div>
                            <div style="font-weight: 600;">${post.title}</div>
                            <small style="color: var(--text-secondary);">${post.excerpt || post.content?.substring(0, 50)}...</small>
                        </div>
                    </div>
                </td>
                <td><span class="badge badge-info">${post.category || 'General'}</span></td>
                <td>
                    <span class="badge badge-${post.status === 'published' ? 'success' : 'secondary'}">
                        ${post.status}
                    </span>
                </td>
                <td>${post.author_id || 'Admin'}</td>
                <td>${ui.formatDate(post.created_at)}</td>
                <td>
                    <div style="display: flex; gap: 8px;">
                        <button class="btn btn-sm" onclick="adminBlog.edit(${post.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="adminBlog.delete(${post.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    },
    
    openModal() {
        this.editingId = null;
        document.getElementById('blog-form').reset();
        document.getElementById('blog-modal-title').textContent = 'Create Blog Post';
        document.getElementById('blog-post-id').value = '';
        ui.openModal('blog-modal');
    },
    
    async edit(id) {
        const post = this.posts.find(p => p.id === id);
        if(!post) return;
        
        this.editingId = id;
        document.getElementById('blog-modal-title').textContent = 'Edit Blog Post';
        document.getElementById('blog-post-id').value = post.id;
        document.getElementById('blog-title').value = post.title;
        document.getElementById('blog-category').value = post.category || 'Trading';
        document.getElementById('blog-status').value = post.status || 'draft';
        document.getElementById('blog-image').value = post.featured_image || '';
        document.getElementById('blog-content').value = post.content || '';
        document.getElementById('blog-premium').checked = post.is_premium || false;
        
        ui.openModal('blog-modal');
    },
    
    async save() {
        const data = {
            title: document.getElementById('blog-title').value,
            content: document.getElementById('blog-content').value,
            excerpt: document.getElementById('blog-content').value.substring(0, 150) + '...',
            category: document.getElementById('blog-category').value,
            featured_image: document.getElementById('blog-image').value,
            status: document.getElementById('blog-status').value,
            is_premium: document.getElementById('blog-premium').checked
        };
        
        try {
            ui.showLoading('Saving post...');
            
            if(this.editingId) {
                await api.put(`/api/blog/${this.editingId}`, data);
                ui.showToast('Post updated successfully', 'success');
            } else {
                await api.post('/api/blog', data);
                ui.showToast('Post published successfully', 'success');
            }
            
            ui.closeModal('blog-modal');
            this.load();
            
        } catch (error) {
            ui.showToast('Error saving post: ' + error.message, 'error');
        } finally {
            ui.hideLoading();
        }
    },
    
    async delete(id) {
        if(!confirm('Delete this blog post?')) return;
        
        try {
            await api.delete(`/api/blog/${id}`);
            ui.showToast('Post deleted', 'success');
            this.load();
        } catch (error) {
            ui.showToast('Error deleting post: ' + error.message, 'error');
        }
    },
    
    search() {
        const term = document.getElementById('blog-search')?.value.toLowerCase();
        if(!term) {
            this.render();
            return;
        }
        
        const filtered = this.posts.filter(p => 
            p.title.toLowerCase().includes(term) ||
            (p.content && p.content.toLowerCase().includes(term))
        );
        
        const tbody = document.getElementById('admin-blog-tbody');
        if(filtered.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No matching posts</td></tr>';
            return;
        }
        
        tbody.innerHTML = filtered.map(post => `
            <tr>
                <td>
                    <div style="display: flex; align-items: center; gap: 12px;">
                        ${post.featured_image ? `<img src="${post.featured_image}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px;">` : '<div style="width: 40px; height: 40px; background: var(--bg-hover); border-radius: 4px;"></div>'}
                        <div>
                            <div style="font-weight: 600;">${post.title}</div>
                            <small style="color: var(--text-secondary);">${post.excerpt || post.content?.substring(0, 50)}...</small>
                        </div>
                    </div>
                </td>
                <td><span class="badge badge-info">${post.category || 'General'}</span></td>
                <td><span class="badge badge-${post.status === 'published' ? 'success' : 'secondary'}">${post.status}</span></td>
                <td>${post.author_id || 'Admin'}</td>
                <td>${ui.formatDate(post.created_at)}</td>
                <td>
                    <button class="btn btn-sm" onclick="adminBlog.edit(${post.id})"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-sm btn-danger" onclick="adminBlog.delete(${post.id})"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('');
    }
};
