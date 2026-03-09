
import { Component } from '../components/Component.js';
import { Sidebar } from '../components/Sidebar.js';
import { api } from '../api/client.js';

export class BlogPage extends Component {
    constructor() {
        super();
        this.posts = [];
    }

    async render() {
        const container = document.createElement('div');
        container.className = 'main-app';

        const sidebar = new Sidebar();
        container.appendChild(sidebar.render());

        const main = document.createElement('main');
        main.className = 'main-content';
        main.innerHTML = `
            <div class="page-header">
                <h2><i class="fas fa-newspaper" style="color: var(--primary);"></i> Trading Blog</h2>
                <p>Latest insights, analysis, and education</p>
            </div>

            <div id="blog-grid" class="blog-grid">
                ${this.renderPosts()}
            </div>
        `;

        container.appendChild(main);

        // Load posts
        setTimeout(() => this.loadPosts(), 0);

        return container;
    }

    renderPosts() {
        if (this.posts.length === 0) {
            return '<div class="loading">Loading posts...</div>';
        }

        return this.posts.map(post => `
            <article class="blog-card card">
                ${post.featured_image ? `
                    <div class="blog-image">
                        <img src="${post.featured_image}" alt="${post.title}" loading="lazy">
                    </div>
                ` : ''}
                <div class="blog-content">
                    <div class="blog-meta">
                        <span class="blog-category">${post.category}</span>
                        ${post.is_premium ? '<span class="badge badge-premium">Premium</span>' : ''}
                    </div>
                    <h3 class="blog-title">
                        <a href="/blog/${post.slug}" data-link>${post.title}</a>
                    </h3>
                    <p class="blog-excerpt">${post.excerpt || post.content.substring(0, 150)}...</p>
                    <div class="blog-footer">
                        <span class="blog-date">${new Date(post.created_at).toLocaleDateString()}</span>
                        <span class="blog-views"><i class="fas fa-eye"></i> ${post.views || 0}</span>
                    </div>
                </div>
            </article>
        `).join('');
    }

    async loadPosts() {
        try {
            const data = await api.getPosts();
            this.posts = data.posts || [];

            const grid = this.element.querySelector('#blog-grid');
            if (grid) {
                grid.innerHTML = this.renderPosts();
            }
        } catch (e) {
            console.error('Failed to load posts', e);
        }
    }
}
