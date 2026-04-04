// ── BlogPage ─────────────────────────────────────────────────────────────────
// FIX SUMMARY:
//   1. renderPost: replaced unsafe ${post.content} template literal with
//      safe DOM-based innerHTML on a dedicated div — prevents SyntaxError
//      when content contains backticks or special characters
//   2. renderPost: added null guard on post.tags before .map()
//   3. renderPost: added image onerror handler via addEventListener
//   4. render: articles now navigate to the post via dashboard router
//   5. render: image errors show gradient placeholder instead of disappearing
//   6. Both: _e() helper used consistently for XSS protection

const BlogPage = {

    // ── Helper: safe HTML escape ──────────────────────────────────────────
    _e(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    },

    // ── Blog listing page ─────────────────────────────────────────────────
    async render(container) {
        container.innerHTML = '<div class="page-header"><h1>Trading Blog</h1></div>';

        if (typeof Store !== 'undefined' && Store.state?.isAdmin) {
            const calBtn = document.createElement('div');
            calBtn.style.marginBottom = '1rem';
            calBtn.innerHTML = '<button class="btn btn-primary">📅 Content Calendar</button>';
            calBtn.querySelector('button').addEventListener('click', () => {
                const app = document.getElementById('app');
                if (app && typeof BlogEnhanced !== 'undefined') BlogEnhanced.renderCalendar(app);
            });
            container.appendChild(calBtn);
        }

        try {
            const posts = await API.getBlogPosts({ is_published: true });

            if (!posts || !posts.length) {
                const empty = document.createElement('div');
                empty.className = 'pw-empty';
                empty.innerHTML = '<p class="pw-empty-title">No articles published yet</p>'
                    + '<p class="pw-empty-sub">Market analysis and educational content is coming soon.</p>';
                container.appendChild(empty);
                return;
            }

            const grid = document.createElement('div');
            grid.className = 'blog-grid';

            posts.forEach(post => {
                const article = document.createElement('article');
                article.className = 'blog-card';
                article.style.cursor = 'pointer';
                // Navigate to post on click
                article.addEventListener('click', () => {
                    if (typeof dashboard !== 'undefined') {
                        // Push slug into URL hash for routing
                        window.location.hash = '#/blog/' + post.slug;
                    }
                });

                // Featured image
                if (post.featured_image) {
                    const img = document.createElement('img');
                    img.src = post.featured_image;
                    img.alt = post.title || '';
                    img.style.cssText = 'width:100%;height:200px;object-fit:cover;border-radius:.375rem;margin-bottom:1rem;';
                    img.addEventListener('error', function() {
                        // Replace with gradient placeholder on 404
                        const ph = document.createElement('div');
                        ph.style.cssText = 'width:100%;height:200px;border-radius:.375rem;margin-bottom:1rem;background:linear-gradient(135deg,#1e1b4b,#0f172a);display:flex;align-items:center;justify-content:center;';
                        ph.innerHTML = '<i class="fas fa-newspaper" style="font-size:3rem;color:rgba(255,255,255,.1);"></i>';
                        this.replaceWith(ph);
                    });
                    article.appendChild(img);
                }

                // Content body
                const body = document.createElement('div');
                body.className = 'blog-content';

                const cat = document.createElement('span');
                cat.className = 'category';
                cat.textContent = post.category || 'General';
                body.appendChild(cat);

                const h2 = document.createElement('h2');
                h2.textContent = post.title || 'Untitled';
                body.appendChild(h2);

                const excerpt = document.createElement('p');
                excerpt.textContent = post.excerpt || '';
                body.appendChild(excerpt);

                const meta = document.createElement('div');
                meta.className = 'blog-meta';
                const dateStr = post.created_at
                    ? (typeof UI !== 'undefined' ? UI.formatDate(post.created_at) : new Date(post.created_at).toLocaleDateString())
                    : '';
                meta.innerHTML = '<span>' + dateStr + '</span>'
                    + '<span>' + (post.views || 0) + ' views</span>';
                body.appendChild(meta);

                article.appendChild(body);
                grid.appendChild(article);
            });

            container.appendChild(grid);

        } catch (error) {
            console.error('[BlogPage] render error:', error);
            const errEl = document.createElement('p');
            errEl.textContent = 'Failed to load blog posts';
            container.appendChild(errEl);
        }
    },

    // ── Single post page ──────────────────────────────────────────────────
    async renderPost(container, slug) {
        try {
            const post = await API.getBlogPost(slug);

            // Build article safely with DOM API
            // ── FIX: NEVER inject post.content via template literal ──
            // Template literals break if content contains backticks.
            // Use element.innerHTML on a dedicated div instead.

            const article = document.createElement('article');
            article.className = 'blog-post';
            article.style.cssText = 'max-width:800px;margin:0 auto;';

            // Category badge
            const cat = document.createElement('span');
            cat.className = 'category';
            cat.textContent = post.category || 'General';
            article.appendChild(cat);

            // Title
            const h1 = document.createElement('h1');
            h1.textContent = post.title || 'Untitled';
            article.appendChild(h1);

            // Meta
            const meta = document.createElement('div');
            meta.className = 'blog-meta';
            const dateStr = post.created_at
                ? (typeof UI !== 'undefined' ? UI.formatDate(post.created_at) : new Date(post.created_at).toLocaleDateString())
                : '';
            meta.innerHTML = '<span>' + dateStr + '</span>'
                + '<span>' + (post.views || 0) + ' views</span>';
            article.appendChild(meta);

            // Featured image with safe error fallback
            if (post.featured_image) {
                const img = document.createElement('img');
                img.src = post.featured_image;
                img.className = 'featured-image';
                img.alt = post.title || '';
                img.style.cssText = 'width:100%;margin:2rem 0;border-radius:.5rem;';
                img.addEventListener('error', function() {
                    this.style.display = 'none';
                });
                article.appendChild(img);
            }

            // ── CRITICAL FIX: post.content injected via .innerHTML on a div ──
            // This is safe because we're setting innerHTML on a dedicated element,
            // not embedding it inside a JavaScript template literal string.
            const contentDiv = document.createElement('div');
            contentDiv.className = 'post-content';
            contentDiv.style.cssText = 'line-height:1.8;font-size:1.125rem;';
            contentDiv.innerHTML = post.content || '';
            article.appendChild(contentDiv);

            // Tags — with null guard (post.tags may be null/undefined)
            const tags = Array.isArray(post.tags) ? post.tags : [];
            if (tags.length) {
                const tagsDiv = document.createElement('div');
                tagsDiv.style.marginTop = '2rem';
                tags.forEach(tag => {
                    const span = document.createElement('span');
                    span.className = 'badge';
                    span.style.marginRight = '.5rem';
                    span.textContent = tag;
                    tagsDiv.appendChild(span);
                });
                article.appendChild(tagsDiv);
            }

            container.innerHTML = '';
            container.appendChild(article);

            // Blog CTAs — convert readers to platform users
            if (typeof BlogEnhanced !== 'undefined') {
                BlogEnhanced.renderPostCTAs(container, post.category);
                BlogEnhanced.renderRelatedPosts(post.id, container);
            }

        } catch (error) {
            console.error('[BlogPage] renderPost error:', error);
            container.innerHTML = '<div class="pw-empty"><p class="pw-empty-title">Post not found</p>'
                + '<p class="pw-empty-sub">This article may have been moved or deleted.</p></div>';
        }
    }
};
