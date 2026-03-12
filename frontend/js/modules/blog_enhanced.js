const BlogEnhanced = {
    async renderSEOAdmin(postId) {
        if (!Store.state.isAdmin) return;

        try {
            const response = await fetch(`${API.baseURL}/blog/${postId}/auto-seo`, {
                method: 'POST',
                headers: API.defaultHeaders
            });

            if (response.ok) {
                UI.showToast('SEO metadata auto-generated', 'success');
            }
        } catch (e) {
            console.error('SEO generation failed');
        }
    },

    renderContentUpgrade(upgrade) {
        return `
            <div class="content-upgrade-box" data-upgrade-id="${upgrade.id}">
                <div class="upgrade-icon">${this.getUpgradeIcon(upgrade.upgrade_type)}</div>
                <h4>${upgrade.title}</h4>
                <p>Free ${upgrade.upgrade_type} to accompany this article</p>
                ${upgrade.require_email ? `
                <form onsubmit="BlogEnhanced.captureEmail(event, ${upgrade.id})">
                    <input type="email" placeholder="Enter your email" required>
                    <button type="submit" class="btn btn-primary">
                        Download Free ${upgrade.upgrade_type.toUpperCase()}
                    </button>
                </form>
                ` : `
                <a href="${upgrade.file_url}" download class="btn btn-primary">
                    Download Now
                </a>
                `}
                <small class="privacy-note">Join 5,000+ traders. Unsubscribe anytime.</small>
            </div>
        `;
    },

    getUpgradeIcon(type) {
        const icons = {
            'checklist': '✅',
            'cheatsheet': '📋',
            'template': '📄',
            'calculator': '🧮',
            'video': '🎥'
        };
        return icons[type] || '🎁';
    },

    async captureEmail(e, upgradeId) {
        e.preventDefault();
        const email = e.target.querySelector('input[type="email"]').value;

        try {
            const result = await API.captureEmail({
                email: email,
                upgrade_id: upgradeId
            });

            window.open(result.download_url, '_blank');
            UI.showToast('Download started! Check your email.', 'success');
        } catch (error) {
            UI.showToast(error.message, 'error');
        }
    },

    async renderRelatedPosts(postId, container) {
        try {
            const related = await API.request(`/blog/${postId}/related?limit=3`);

            if (related.length === 0) return;

            container.insertAdjacentHTML('beforeend', `
                <div class="related-posts" style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #e5e7eb;">
                    <h3>Continue Your Trading Education</h3>
                    <div class="related-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin-top: 1rem;">
                        ${related.map(post => `
                            <a href="#/blog/${post.slug}" class="related-card" style="background: white; padding: 1rem; border-radius: 0.375rem; text-decoration: none; color: inherit;">
                                <span class="category" style="font-size: 0.75rem; color: #3b82f6;">${post.category}</span>
                                <h4 style="margin-top: 0.5rem;">${post.title}</h4>
                            </a>
                        `).join('')}
                    </div>
                </div>
            `);
        } catch (e) {
            console.error('Failed to load related posts');
        }
    },

    async renderCalendar(container) {
        if (!Store.state.isAdmin) {
            container.innerHTML = '<p>Admin access required</p>';
            return;
        }

        try {
            const items = await API.request('/blog/calendar');

            container.innerHTML = `
                <div class="calendar-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
                    <h2>Content Calendar</h2>
                    <button onclick="BlogEnhanced.showAddCalendarItem()" class="btn btn-primary">
                        + Schedule Post
                    </button>
                </div>
                <div class="calendar-grid">
                    ${items.map(item => this.renderCalendarItem(item)).join('')}
                </div>
            `;
        } catch (e) {
            container.innerHTML = '<p>Failed to load calendar</p>';
        }
    },

    renderCalendarItem(item) {
        const statusColors = {
            'planned': 'gray',
            'writing': 'blue',
            'review': 'orange',
            'scheduled': 'purple',
            'published': 'green'
        };

        return `
            <div class="calendar-item status-${statusColors[item.status]}">
                <div class="calendar-date">${new Date(item.planned_publish_date).toLocaleDateString()}</div>
                <h4>${item.planned_title}</h4>
                <div class="calendar-meta">
                    <span class="badge">${item.category}</span>
                    <span>Target: ${item.target_keyword}</span>
                    <span>Assigned: ${item.username}</span>
                </div>
            </div>
        `;
    }
};