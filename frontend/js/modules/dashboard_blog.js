// Dashboard Module: Blog
// Extracted from dashboard.js for maintainability

DashboardController.prototype.loadBlog = async function() {
    if (typeof PublicPages !== 'undefined') {
        await PublicPages.blog('blog-container', this);
        return;
    }
    const container = document.getElementById('blog-container');
    if (!container) return;
    container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500"><i class="fas fa-spinner fa-spin mr-2"></i>Loading articles…</div>';
    try {
        const data = await this.apiRequest('/blog/posts');
        const posts = Array.isArray(data) ? data : (data.posts || []);
        if (!posts.length) {
            container.innerHTML = `<div class="col-span-full pw-empty">
                <div class="pw-empty-icon"><i class="fas fa-newspaper text-xl" style="color:#6b7280;"></i></div>
                <p class="pw-empty-title">No articles published yet</p>
                <p class="pw-empty-sub">Market analysis and educational content is coming soon.</p>
            </div>`;
            return;
        }
        // ── FIX: build blog cards via DOM to avoid onerror string injection issues ──
        const placeholder_html = '<div class="h-48 bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center"><i class="fas fa-newspaper text-5xl text-white/20"></i></div>';

        const fragment = document.createDocumentFragment();
        posts.forEach(p => {
            const article = document.createElement('article');
            article.className = 'bg-gray-800 rounded-xl overflow-hidden border border-gray-700 hover:border-blue-600/40 transition-colors cursor-pointer group';

            // Thumb — image with proper fallback to placeholder
            if (p.featured_image) {
                const img = document.createElement('img');
                img.src = p.featured_image;
                img.className = 'w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300';
                img.alt = '';
                img.addEventListener('error', function() {
                    // Replace broken image with the gradient placeholder
                    const ph = document.createElement('div');
                    ph.className = 'h-48 bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center';
                    ph.innerHTML = '<i class="fas fa-newspaper text-5xl text-white/20"></i>';
                    this.replaceWith(ph);
                });
                article.appendChild(img);
            } else {
                const ph = document.createElement('div');
                ph.className = 'h-48 bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center';
                ph.innerHTML = '<i class="fas fa-newspaper text-5xl text-white/20"></i>';
                article.appendChild(ph);
            }

            // Body
            const body = document.createElement('div');
            body.className = 'p-4';
            const date = p.created_at ? new Date(p.created_at).toLocaleDateString() : '';
            body.innerHTML = '<div class="text-xs text-purple-400 font-semibold uppercase tracking-wide mb-1">' + _e(p.category || 'General') + '</div>'
                + '<h4 class="font-bold text-white mb-2 group-hover:text-purple-300 transition-colors">' + _e(p.title) + '</h4>'
                + '<p class="text-sm text-gray-400 line-clamp-3 mb-3">' + _e(p.excerpt || '') + '</p>'
                + '<div class="flex justify-between items-center text-xs text-gray-500">'
                + '<span>' + date + '</span>'
                + '<span class="text-purple-400">Read more →</span>'
                + '</div>';

            article.appendChild(body);
            fragment.appendChild(article);
        });

        container.innerHTML = '';
        container.appendChild(fragment);
    } catch (error) {
        container.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">Failed to load articles.</div>';
    }
};

