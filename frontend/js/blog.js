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
                    ${auth.requireAdmin() ? '<button class="primary" onclick="blog.showCreateModal()">New Post</button>' : ''}
                </div>
                <div class="blog-grid" style="display: grid; gap: 1.5rem;">
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
            <article class="card blog-card" onclick="window.location='/blog/${post.id}'" style="cursor: pointer;">
                ${image}
                <div class="blog-meta" style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
                    ${isPremium}
                    ${post.category ? `<span class="badge badge-info">${post.category}</span>` : ''}
                </div>
                <h2 style="margin-bottom: 0.5rem;">${post.title}</h2>
                <p style="color: var(--text-light);">${post.excerpt || ''}</p>
                <small style="color: var(--text-light);">${ui.formatDate(post.created_at)}</small>
            </article>
        `;
    },

    async loadPostDetail(container, postId) {
        container.innerHTML = '<div class="loading">Loading article...</div>';

        try {
            const post = await api.get(`/blog/${postId}`);

            const html = `
                <article class="card" style="max-width: 800px; margin: 0 auto;">
                    ${post.featured_image ? `<img src="${post.featured_image}" style="width: 100%; max-height: 400px; object-fit: cover; border-radius: 0.5rem; margin-bottom: 1rem;">` : ''}
                    <h1>${post.title}</h1>
                    <div style="display: flex; gap: 1rem; margin: 1rem 0; color: var(--text-light);">
                        <span>${ui.formatDate(post.created_at)}</span>
                        ${post.category ? `<span>${post.category}</span>` : ''}
                    </div>
                    <div class="post-content" style="line-height: 1.8; margin-top: 2rem;">
                        ${post.content}
                    </div>
                    ${auth.requireAdmin() ? `
                        <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border);">
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
        ui.showToast('Create post form would appear here');
    },

    editPost(postId) {
        ui.showToast('Edit form would appear here');
    },

    async deletePost(postId) {
        if (!confirm('Delete this post?')) return;
        try {
            await api.delete(`/blog/${postId}`);
            ui.showToast('Post deleted', 'success');
            window.location.href = '/blog';
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    }
};
