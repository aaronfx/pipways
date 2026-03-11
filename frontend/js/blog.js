/**
 * Blog Module
 * Handles blog post display and reading
 */

const blog = {
    async loadBlogPosts() {
        const container = document.getElementById('blog-grid');
        const searchTerm = document.getElementById('blog-search')?.value || '';
        const category = document.getElementById('blog-category')?.value || '';
        
        if (!container) return;

        try {
            let url = '/api/blog?status=published';
            if (searchTerm) url += `&search=${encodeURIComponent(searchTerm)}`;
            if (category) url += `&category=${category}`;

            const data = await api.get(url);
            
            if (!data || data.length === 0) {
                container.innerHTML = '<div class="content-card"><p style="text-align: center; color: var(--text-secondary);">No articles found</p></div>';
                return;
            }

            container.innerHTML = data.map(post => this.renderPostCard(post)).join('');
            
        } catch (error) {
            container.innerHTML = `<div class="content-card"><p style="text-align: center; color: var(--danger);">Error: ${error.message}</p></div>`;
        }
    },

    renderPostCard(post) {
        const isPremium = post.is_premium ? '<span class="badge badge-premium">Premium</span>' : '';
        const image = post.featured_image ? `<img src="${post.featured_image}" style="width: 100%; height: 200px; object-fit: cover; border-radius: 0.5rem; margin-bottom: 1rem;">` : '';

        return `
            <article class="content-card blog-card" style="cursor: pointer;" onclick="blog.loadPostDetail(${post.id})">
                ${image}
                <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
                    ${isPremium}
                    ${post.category ? `<span class="badge badge-info">${post.category}</span>` : ''}
                </div>
                <h2 style="margin-bottom: 0.5rem; font-size: 1.25rem;">${post.title}</h2>
                <p style="color: var(--text-secondary); font-size: 0.9rem;">${post.excerpt || post.content?.substring(0, 150) || ''}...</p>
                <small style="color: var(--text-light);">${ui.formatDate(post.created_at)}</small>
            </article>
        `;
    },

    async loadPostDetail(postId) {
        const container = document.getElementById('blog-reader-content');
        
        try {
            const post = await api.get(`/api/blog/${postId}`);
            
            container.innerHTML = `
                <button class="btn btn-sm btn-secondary" onclick="app.showSection('blog', document.querySelectorAll('.nav-link')[8])" style="margin-bottom: 2rem;">
                    <i class="fas fa-arrow-left"></i> Back to Blog
                </button>
                ${post.featured_image ? `<img src="${post.featured_image}" style="width: 100%; max-height: 400px; object-fit: cover; border-radius: 0.5rem; margin-bottom: 2rem;">` : ''}
                <h1 style="margin-bottom: 1rem;">${post.title}</h1>
                <div style="display: flex; gap: 1rem; margin-bottom: 2rem; color: var(--text-secondary);">
                    <span>${ui.formatDate(post.created_at)}</span>
                    ${post.category ? `<span class="badge badge-info">${post.category}</span>` : ''}
                    ${post.is_premium ? '<span class="badge badge-premium">Premium</span>' : ''}
                </div>
                <div class="post-content" style="line-height: 1.8; font-size: 1.1rem;">
                    ${post.content}
                </div>
            `;
            
            app.showSection('blog-reader');
            
        } catch (error) {
            ui.showToast('Error loading article: ' + error.message, 'error');
        }
    }
};
