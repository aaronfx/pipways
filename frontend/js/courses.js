/**
 * Courses Module
 * Handles course display and enrollment
 */

const courses = {
    async loadCourses() {
        const container = document.getElementById('courses-grid');
        const searchTerm = document.getElementById('course-search')?.value || '';
        const level = document.getElementById('course-level')?.value || '';
        
        if (!container) return;

        try {
            let url = '/api/courses';  // FIXED: Added /api prefix
            const params = [];
            if (searchTerm) params.push(`search=${encodeURIComponent(searchTerm)}`);
            if (level) params.push(`level=${level}`);
            if (params.length > 0) url += '?' + params.join('&');

            const data = await api.get(url);
            
            if (!data || data.length === 0) {
                container.innerHTML = '<div class="content-card"><p style="text-align: center; color: var(--text-secondary);">No courses found</p></div>';
                return;
            }

            container.innerHTML = data.map(course => this.renderCourseCard(course)).join('');
            
        } catch (error) {
            container.innerHTML = `<div class="content-card"><p style="text-align: center; color: var(--danger);">Error: ${error.message}</p></div>`;
        }
    },

    renderCourseCard(course) {
        const isPremium = course.is_premium ? '<span class="badge badge-premium">Premium</span>' : '';
        const levelBadge = course.level ? `<span class="badge badge-info">${course.level}</span>` : '';
        const thumbnail = course.thumbnail ? `<img src="${course.thumbnail}" style="width: 100%; height: 180px; object-fit: cover; border-radius: 0.375rem; margin-bottom: 1rem;">` : '';

        return `
            <div class="content-card course-card" style="cursor: pointer;" onclick="courses.loadCourseDetail(${course.id})">
                ${thumbnail}
                <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
                    ${levelBadge}
                    ${isPremium}
                </div>
                <h3>${course.title}</h3>
                <p style="color: var(--text-secondary); font-size: 0.9rem;">${course.description?.substring(0, 100) || ''}...</p>
                ${course.duration_hours ? `<small style="color: var(--text-secondary);">Duration: ${course.duration_hours} hours</small>` : ''}
            </div>
        `;
    },

    async loadCourseDetail(courseId) {
        const container = document.getElementById('course-detail-content');
        const titleEl = document.getElementById('course-detail-title');
        const levelEl = document.getElementById('course-detail-level');
        
        if (!container) return;

        try {
            const course = await api.get(`/api/courses/${courseId}`);  // FIXED: Added /api prefix
            
            titleEl.textContent = course.title;
            levelEl.textContent = course.level || 'All Levels';
            
            container.innerHTML = `
                <div class="card" style="max-width: 900px; margin: 0 auto;">
                    ${course.thumbnail ? `<img src="${course.thumbnail}" style="width: 100%; max-height: 300px; object-fit: cover; border-radius: 0.5rem; margin-bottom: 1rem;">` : ''}
                    <p>${course.content || course.description}</p>
                    
                    <h3 style="margin-top: 2rem; margin-bottom: 1rem;">Course Modules</h3>
                    ${course.modules && course.modules.length > 0 ? `
                        <div class="modules-list">
                            ${course.modules.map((m, i) => `
                                <div class="card" style="margin-bottom: 0.5rem;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <div>
                                            <strong>Module ${i + 1}: ${m.title}</strong>
                                            ${m.is_premium ? ' <span class="badge badge-premium">VIP</span>' : ''}
                                        </div>
                                        ${m.video_url ? '<button class="btn btn-sm">Watch</button>' : ''}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : '<p>No modules available yet.</p>'}
                </div>
            `;
            
            app.showSection('course-detail');
            
        } catch (error) {
            ui.showToast('Error loading course: ' + error.message, 'error');
        }
    }
};
