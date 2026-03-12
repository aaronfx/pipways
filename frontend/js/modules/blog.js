const BlogPage = {
    async render(container) {
        container.innerHTML = '<div class="page-header"><h1>Trading Blog</h1></div>';

        if (Store.state.isAdmin) {
            container.innerHTML += `
                <div style="margin-bottom: 1rem;">
                    <button onclick="BlogEnhanced.renderCalendar(document.getElementById('app'))" class="btn btn-primary">
                        📅 Content Calendar
                    </button>
                </div>
            `;
        }

        try {
            const posts = await API.getBlogPosts({ is_published: true });

            let html = '<div class="blog-grid">';
            posts.forEach(post => {
                html += `
                    <article class="blog-card">
                        ${post.featured_image ? `<img src="${post.featured_image}" alt="" style="width: 100%; height: 200px; object-fit: cover; border-radius: 0.375rem; margin-bottom: 1rem;">` : ''}
                        <div class="blog-content">
                            <span class="category">${post.category}</span>
                            <h2><a href="#/blog/${post.slug}">${UI.escapeHtml(post.title)}</a></h2>
                            <p>${UI.escapeHtml(post.excerpt)}</p>
                            <div class="blog-meta">
                                <span>${UI.formatDate(post.created_at)}</span>
                                <span>${post.views} views</span>
                            </div>
                        </div>
                    </article>
                `;
            });
            html += '</div>';
            container.innerHTML += html;
        } catch (error) {
            container.innerHTML += '<p>Failed to load blog posts</p>';
        }
    },

    async renderPost(container, slug) {
        try {
            const post = await API.getBlogPost(slug);
            container.innerHTML = `
                <article class="blog-post" style="max-width: 800px; margin: 0 auto;">
                    <span class="category">${post.category}</span>
                    <h1>${UI.escapeHtml(post.title)}</h1>
                    <div class="blog-meta">
                        <span>${UI.formatDate(post.created_at)}</span>
                        <span>${post.views} views</span>
                    </div>
                    ${post.featured_image ? `<img src="${post.featured_image}" class="featured-image" style="width: 100%; margin: 2rem 0;">` : ''}
                    <div class="post-content" style="line-height: 1.8; font-size: 1.125rem;">
                        ${post.content}
                    </div>
                    <div class="tags" style="margin-top: 2rem;">
                        ${post.tags.map(tag => `<span class="badge" style="margin-right: 0.5rem;">${tag}</span>`).join('')}
                    </div>
                </article>
            `;

            // Show content upgrade if available
            // BlogEnhanced.renderContentUpgrade(upgrade); // Would need upgrade data

            // Show related posts
            BlogEnhanced.renderRelatedPosts(post.id, container);

        } catch (error) {
            container.innerHTML = '<p>Post not found</p>';
        }
    }
};