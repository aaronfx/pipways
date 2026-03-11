/**
 * Courses Module
 */
const courses = {
    async loadCourses(container) {
        container.innerHTML = '<div class="loading">Loading courses...</div>';

        try {
            const data = await api.get('/courses');

            let html = `
                <div class="page-header">
                    <h1>Trading Courses</h1>
                    ${auth.requireAdmin() ? '<button class="primary" onclick="courses.showCreateModal()">New Course</button>' : ''}
                </div>
                <div class="courses-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem;">
                    ${data.length === 0 ? '<p>No courses available.</p>' : 
                      data.map(c => this.renderCourseCard(c)).join('')}
                </div>
            `;

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="error">Failed to load courses: ${error.message}</div>`;
        }
    },

    renderCourseCard(course) {
        const isPremium = course.is_premium ? '<span class="badge badge-premium">Premium</span>' : '';
        const levelBadge = course.level ? `<span class="badge badge-info">${course.level}</span>` : '';

        return `
            <div class="card course-card" onclick="courses.loadCourseDetail(${course.id})" style="cursor: pointer;">
                ${course.thumbnail ? `<img src="${course.thumbnail}" style="width: 100%; height: 180px; object-fit: cover; border-radius: 0.375rem; margin-bottom: 1rem;">` : ''}
                <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
                    ${levelBadge}
                    ${isPremium}
                </div>
                <h3>${course.title}</h3>
                <p style="color: var(--text-light); font-size: 0.9rem;">${course.description || ''}</p>
                ${course.duration_hours ? `<small>Duration: ${course.duration_hours} hours</small>` : ''}
            </div>
        `;
    },

    async loadCourseDetail(courseId) {
        const container = document.getElementById('main-content');
        container.innerHTML = '<div class="loading">Loading course...</div>';

        try {
            const course = await api.get(`/courses/${courseId}`);

            const html = `
                <div class="card" style="max-width: 900px; margin: 0 auto;">
                    <button onclick="window.history.back()" style="margin-bottom: 1rem;">← Back</button>
                    ${course.thumbnail ? `<img src="${course.thumbnail}" style="width: 100%; max-height: 300px; object-fit: cover; border-radius: 0.5rem; margin-bottom: 1rem;">` : ''}
                    <h1>${course.title}</h1>
                    <div style="display: flex; gap: 0.5rem; margin: 1rem 0;">
                        <span class="badge badge-info">${course.level || 'All Levels'}</span>
                        ${course.is_premium ? '<span class="badge badge-premium">Premium</span>' : ''}
                    </div>
                    <p>${course.description}</p>

                    <h2 style="margin-top: 2rem; margin-bottom: 1rem;">Course Modules</h2>
                    ${course.modules && course.modules.length > 0 ? `
                        <div class="modules-list">
                            ${course.modules.map((m, i) => `
                                <div class="card" style="margin-bottom: 0.5rem;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <div>
                                            <strong>Module ${i + 1}: ${m.title}</strong>
                                            ${m.is_premium ? ' <span class="badge badge-premium">VIP</span>' : ''}
                                        </div>
                                        ${m.video_url ? '<button>Watch</button>' : ''}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : '<p>No modules available.</p>'}
                </div>
            `;

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="error">Failed to load course: ${error.message}</div>`;
        }
    },

    showCreateModal() {
        ui.showToast('Create course form would appear here');
    }
};
