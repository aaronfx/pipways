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

    /**
     * renderPostCTAs — injected below every blog post.
     * Drives conversions from reader → platform user.
     * Uses only existing platform features.
     */
    renderPostCTAs(container, category) {
        const isAuth = !!localStorage.getItem('pipways_token');
        category = (category || '').toLowerCase();

        // Pick the most relevant CTA tool based on post category
        let primaryCTA;
        if (category.includes('risk') || category.includes('position')) {
            primaryCTA = {
                emoji: '💰',
                title: 'Try Our Free Risk Calculator',
                desc:  'Calculate the exact lot size for your next trade in seconds.',
                btn:   'Open Risk Calculator',
                action: isAuth ? "dashboard.navigate('risk')" : "window.location.href='/'",
            };
        } else if (category.includes('chart') || category.includes('analysis') || category.includes('pattern')) {
            primaryCTA = {
                emoji: '📊',
                title: 'Analyse Your Chart with AI',
                desc:  'Upload a screenshot — get instant pattern recognition and trade ideas.',
                btn:   'Try Chart Analysis',
                action: isAuth ? "dashboard.navigate('analysis')" : "window.location.href='/'",
            };
        } else {
            primaryCTA = {
                emoji: '📚',
                title: 'Learn This in the Academy',
                desc:  'Structured lessons, quizzes and certificates. Completely free.',
                btn:   'Open Trading Academy',
                action: "window.location.href='/academy.html'",
            };
        }

        // Email capture for non-logged-in readers
        const emailBlock = !isAuth ? `
        <div style="margin-top:16px;display:flex;gap:8px;flex-wrap:wrap;">
            <input type="email" id="blog-cta-email" placeholder="Your email address"
                style="flex:1;min-width:200px;padding:10px 14px;border-radius:6px;
                       border:1px solid #d1d5db;font-size:.875rem;outline:none;">
            <button onclick="BlogEnhanced._captureFromBlog()"
                style="padding:10px 18px;background:#3b82f6;color:white;border:none;
                       border-radius:6px;font-weight:600;font-size:.875rem;cursor:pointer;
                       white-space:nowrap;">
                Get Free Access →
            </button>
        </div>
        <p style="margin:6px 0 0;font-size:.75rem;color:#9ca3af;">
            Join 5,000+ Nigerian traders. No spam, unsubscribe anytime.
        </p>` : '';

        container.insertAdjacentHTML('beforeend', `
        <div style="margin-top:3rem;display:grid;grid-template-columns:1fr 1fr;gap:1rem;
                    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">

            <!-- Primary CTA -->
            <div style="background:linear-gradient(135deg,#667eea,#764ba2);border-radius:12px;
                        padding:24px;color:white;grid-column:${!isAuth ? '1' : '1/3'};">
                <div style="font-size:1.75rem;margin-bottom:8px;">${primaryCTA.emoji}</div>
                <h4 style="margin:0 0 6px;font-size:1rem;font-weight:700;">${primaryCTA.title}</h4>
                <p style="margin:0 0 14px;font-size:.875rem;opacity:.9;">${primaryCTA.desc}</p>
                <button onclick="${primaryCTA.action}"
                    style="background:white;color:#7c3aed;border:none;padding:10px 20px;
                           border-radius:6px;font-weight:700;font-size:.875rem;cursor:pointer;">
                    ${primaryCTA.btn} →
                </button>
            </div>

            <!-- Email CTA (non-auth only) -->
            ${!isAuth ? `
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:24px;">
                <div style="font-size:1.75rem;margin-bottom:8px;">🚀</div>
                <h4 style="margin:0 0 6px;font-size:1rem;font-weight:700;color:#111827;">
                    Get Free Platform Access
                </h4>
                <p style="margin:0;font-size:.875rem;color:#6b7280;">
                    Academy, Risk Calculator, AI Mentor — all free.
                </p>
                ${emailBlock}
            </div>` : `
            <!-- Academy nudge for logged-in users -->
            <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:24px;"
                 onclick="window.location.href='/academy.html'" style="cursor:pointer;">
                <div style="font-size:1.75rem;margin-bottom:8px;">📚</div>
                <h4 style="margin:0 0 6px;font-size:1rem;font-weight:700;color:#111827;">
                    Continue Learning
                </h4>
                <p style="margin:0 0 14px;font-size:.875rem;color:#6b7280;">
                    Pick up where you left off in the Trading Academy.
                </p>
                <span style="font-size:.875rem;color:#16a34a;font-weight:600;">Open Academy →</span>
            </div>`}
        </div>`);
    },

    async _captureFromBlog() {
        const input = document.getElementById('blog-cta-email');
        const email = input?.value.trim();
        if (!email) return;
        try {
            await fetch('/email/capture', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, source: 'blog' }),
            });
            if (input) input.closest('div').innerHTML =
                '<p style="color:#16a34a;font-weight:600;margin:8px 0 0;">✅ Check your email!</p>';
        } catch (_) {
            if (input) input.placeholder = 'Something went wrong — try again';
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
