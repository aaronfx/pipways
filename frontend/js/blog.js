/**
 * Blog Module
 */
const blog = {
    async loadPosts(container, page = 1) {
        container.innerHTML = '<div class="loading">Loading articles...</div>';

        try {
            const posts = await api.get(`/blog?status=published&limit=10&offset=${(page-1)*10}`);

            let html = `
                <div class="page-header">
                    <h1>Trading Blog</h1>
                    ${auth.currentUser && (auth.currentUser.role === 'admin' || auth.currentUser.role === 'moderator') ? 
                        '<button class="primary" onclick="blog.showCreateModal()">New Post</button>' : ''}
                </div>
                <div class="blog-grid" style="display: grid; gap: 1.5rem; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));">
                    ${posts.length === 0 ? '<p>No articles yet.</p>' : 
                      posts.map(p => this.renderPostCard(p)).join('')}
                </div>
            `;

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="error">Failed to load blog: ${error.message}</div>`;
        }
    },

    renderPostCard(post) {
        const isPremium = post.is_premium ? '<span class="badge badge-premium">Premium</span>' : '';
        const image = post.featured_image ? `<img src="${post.featured_image}" style="width: 100%; height: 200px; object-fit: cover; border-radius: 0.5rem; margin-bottom: 1rem;">` : '';

        return `
            <article class="card blog-card" style="cursor: pointer; display: flex; flex-direction: column;">
                <div onclick="window.location='/blog/${post.id}'">
                    ${image}
                    <div class="blog-meta" style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
                        ${isPremium}
                        ${post.category ? `<span class="badge badge-info">${post.category}</span>` : ''}
                    </div>
                    <h2 style="margin-bottom: 0.5rem;">${post.title}</h2>
                    <p style="color: var(--text-light); flex: 1;">${post.excerpt || ''}</p>
                    <small style="color: var(--text-light);">${ui.formatDate(post.created_at)}</small>
                </div>
                ${auth.currentUser && (auth.currentUser.role === 'admin' || auth.currentUser.role === 'moderator') ? `
                    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border); display: flex; gap: 0.5rem;">
                        <button onclick="event.stopPropagation(); blog.editPost(${post.id})">Edit</button>
                        <button class="secondary" onclick="event.stopPropagation(); blog.deletePost(${post.id})">Delete</button>
                    </div>
                ` : ''}
            </article>
        `;
    },

    async loadPostDetail(container, postId) {
        container.innerHTML = '<div class="loading">Loading article...</div>';

        try {
            const post = await api.get(`/blog/${postId}`);

            const html = `
                <article class="card" style="max-width: 800px; margin: 0 auto;">
                    <button onclick="window.history.back()" style="margin-bottom: 1rem;">← Back</button>
                    ${post.featured_image ? `<img src="${post.featured_image}" style="width: 100%; max-height: 400px; object-fit: cover; border-radius: 0.5rem; margin-bottom: 1rem;">` : ''}
                    <h1>${post.title}</h1>
                    <div style="display: flex; gap: 1rem; margin: 1rem 0; color: var(--text-light);">
                        <span>${ui.formatDate(post.created_at)}</span>
                        ${post.category ? `<span class="badge badge-info">${post.category}</span>` : ''}
                        ${post.is_premium ? '<span class="badge badge-premium">Premium</span>' : ''}
                    </div>
                    <div class="post-content" style="line-height: 1.8; margin-top: 2rem;">
                        ${post.content}
                    </div>
                    ${auth.currentUser && (auth.currentUser.role === 'admin' || auth.currentUser.role === 'moderator') ? `
                        <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border); display: flex; gap: 0.5rem;">
                            <button onclick="blog.editPost(${post.id})">Edit</button>
                            <button class="secondary" onclick="blog.deletePost(${post.id})">Delete</button>
                        </div>
                    ` : ''}
                </article>
            `;

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="error">Failed to load article: ${error.message}</div>`;
        }
    },

    showCreateModal() {
        const container = document.getElementById('main-content');
        container.innerHTML = `
            <div class="card" style="max-width: 800px; margin: 0 auto;">
                <h2>Create New Blog Post</h2>
                <form onsubmit="blog.handleCreate(event)">
                    <div class="form-group">
                        <label>Title</label>
                        <input type="text" name="title" required>
                    </div>
                    <div class="form-group">
                        <label>Content</label>
                        <textarea name="content" rows="10" required></textarea>
                    </div>
                    <div class="form-group">
                        <label>Excerpt</label>
                        <textarea name="excerpt" rows="2"></textarea>
                    </div>
                    <div class="form-group">
                        <label>Category</label>
                        <input type="text" name="category">
                    </div>
                    <div class="form-group">
                        <label>Featured Image URL</label>
                        <input type="text" name="featured_image">
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" name="is_premium"> Premium Content
                        </label>
                    </div>
                    <div style="display: flex; gap: 1rem;">
                        <button type="submit" class="primary">Publish</button>
                        <button type="button" onclick="window.location='/blog'">Cancel</button>
                    </div>
                </form>
            </div>
        `;
    },

    async handleCreate(e) {
        e.preventDefault();
        const form = e.target;
        const data = {
            title: form.title.value,
            content: form.content.value,
            excerpt: form.excerpt.value,
            category: form.category.value,
            featured_image: form.featured_image.value,
            is_premium: form.is_premium.checked,
            status: 'published'
        };

        try {
            await api.post('/blog', data);
            ui.showToast('Blog post created successfully', 'success');
            window.location.href = '/blog';
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    },

    async editPost(postId) {
        try {
            const post = await api.get(`/blog/${postId}`);
            const container = document.getElementById('main-content');
            
            container.innerHTML = `
                <div class="card" style="max-width: 800px; margin: 0 auto;">
                    <h2>Edit Blog Post</h2>
                    <form onsubmit="blog.handleUpdate(event, ${postId})">
                        <div class="form-group">
                            <label>Title</label>
                            <input type="text" name="title" value="${post.title}" required>
                        </div>
                        <div class="form-group">
                            <label>Content</label>
                            <textarea name="content" rows="10" required>${post.content}</textarea>
                        </div>
                        <div class="form-group">
                            <label>Excerpt</label>
                            <textarea name="excerpt" rows="2">${post.excerpt || ''}</textarea>
                        </div>
                        <div class="form-group">
                            <label>Category</label>
                            <input type="text" name="category" value="${post.category || ''}">
                        </div>
                        <div class="form-group">
                            <label>Featured Image URL</label>
                            <input type="text" name="featured_image" value="${post.featured_image || ''}">
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" name="is_premium" ${post.is_premium ? 'checked' : ''}> Premium Content
                            </label>
                        </div>
                        <div style="display: flex; gap: 1rem;">
                            <button type="submit" class="primary">Update</button>
                            <button type="button" onclick="window.location='/blog'">Cancel</button>
                        </div>
                    </form>
                </div>
            `;
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    },

    async handleUpdate(e, postId) {
        e.preventDefault();
        const form = e.target;
        const data = {
            title: form.title.value,
            content: form.content.value,
            excerpt: form.excerpt.value,
            category: form.category.value,
            featured_image: form.featured_image.value,
            is_premium: form.is_premium.checked
        };

        try {
            await api.put(`/blog/${postId}`, data);
            ui.showToast('Blog post updated successfully', 'success');
            window.location.href = '/blog';
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    },

    async deletePost(postId) {
        if (!confirm('Are you sure you want to delete this blog post? This action cannot be undone.')) return;
        
        try {
            await api.delete(`/blog/${postId}`);
            ui.showToast('Blog post deleted successfully', 'success');
            
            // If on detail page, go back to list
            if (window.location.pathname.includes('/blog/')) {
                window.location.href = '/blog';
            } else {
                // Refresh current view
                this.loadPosts(document.getElementById('main-content'));
            }
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    }
};
