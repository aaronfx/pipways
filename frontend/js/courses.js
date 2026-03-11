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
                    ${auth.currentUser && (auth.currentUser.role === 'admin' || auth.currentUser.role === 'moderator') ? 
                        '<button class="primary" onclick="courses.showCreateModal()">New Course</button>' : ''}
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
            <div class="card course-card" style="cursor: pointer; display: flex; flex-direction: column;">
                <div onclick="courses.loadCourseDetail(${course.id})">
                    ${course.thumbnail ? `<img src="${course.thumbnail}" style="width: 100%; height: 180px; object-fit: cover; border-radius: 0.375rem; margin-bottom: 1rem;">` : ''}
                    <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
                        ${levelBadge}
                        ${isPremium}
                    </div>
                    <h3>${course.title}</h3>
                    <p style="color: var(--text-light); font-size: 0.9rem; flex: 1;">${course.description || ''}</p>
                    ${course.duration_hours ? `<small style="color: var(--text-light);">Duration: ${course.duration_hours} hours</small>` : ''}
                </div>
                ${auth.currentUser && (auth.currentUser.role === 'admin' || auth.currentUser.role === 'moderator') ? `
                    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border); display: flex; gap: 0.5rem;">
                        <button onclick="event.stopPropagation(); courses.editCourse(${course.id})">Edit</button>
                        <button class="secondary" onclick="event.stopPropagation(); courses.deleteCourse(${course.id})">Delete</button>
                    </div>
                ` : ''}
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
                    
                    ${auth.currentUser && (auth.currentUser.role === 'admin' || auth.currentUser.role === 'moderator') ? `
                        <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border);">
                            <button onclick="courses.editCourse(${course.id})">Edit Course</button>
                            <button class="secondary" onclick="courses.deleteCourse(${course.id})">Delete Course</button>
                        </div>
                    ` : ''}
                </div>
            `;

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="error">Failed to load course: ${error.message}</div>`;
        }
    },

    showCreateModal() {
        const container = document.getElementById('main-content');
        container.innerHTML = `
            <div class="card" style="max-width: 800px; margin: 0 auto;">
                <h2>Create New Course</h2>
                <form onsubmit="courses.handleCreate(event)">
                    <div class="form-group">
                        <label>Title</label>
                        <input type="text" name="title" required>
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <textarea name="description" rows="4" required></textarea>
                    </div>
                    <div class="form-group">
                        <label>Content</label>
                        <textarea name="content" rows="6" required></textarea>
                    </div>
                    <div class="form-group">
                        <label>Level</label>
                        <select name="level">
                            <option value="beginner">Beginner</option>
                            <option value="intermediate">Intermediate</option>
                            <option value="advanced">Advanced</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Duration (hours)</label>
                        <input type="number" name="duration_hours" step="0.5">
                    </div>
                    <div class="form-group">
                        <label>Thumbnail URL</label>
                        <input type="text" name="thumbnail">
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" name="is_premium"> Premium Course
                        </label>
                    </div>
                    <div style="display: flex; gap: 1rem;">
                        <button type="submit" class="primary">Create</button>
                        <button type="button" onclick="window.location='/courses'">Cancel</button>
                    </div>
                </form>
            </div>
        `;
    },

    async handleCreate(e) {
        e.preventDefault();
        const form = e.target;
        const data = {
            title: form.title.value,
            description: form.description.value,
            content: form.content.value,
            level: form.level.value,
            duration_hours: parseFloat(form.duration_hours.value) || null,
            thumbnail: form.thumbnail.value,
            is_premium: form.is_premium.checked
        };

        try {
            await api.post('/courses', data);
            ui.showToast('Course created successfully', 'success');
            window.location.href = '/courses';
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    },

    async editCourse(courseId) {
        try {
            const course = await api.get(`/courses/${courseId}`);
            const container = document.getElementById('main-content');
            
            container.innerHTML = `
                <div class="card" style="max-width: 800px; margin: 0 auto;">
                    <h2>Edit Course</h2>
                    <form onsubmit="courses.handleUpdate(event, ${courseId})">
                        <div class="form-group">
                            <label>Title</label>
                            <input type="text" name="title" value="${course.title}" required>
                        </div>
                        <div class="form-group">
                            <label>Description</label>
                            <textarea name="description" rows="4" required>${course.description}</textarea>
                        </div>
                        <div class="form-group">
                            <label>Content</label>
                            <textarea name="content" rows="6" required>${course.content}</textarea>
                        </div>
                        <div class="form-group">
                            <label>Level</label>
                            <select name="level">
                                <option value="beginner" ${course.level === 'beginner' ? 'selected' : ''}>Beginner</option>
                                <option value="intermediate" ${course.level === 'intermediate' ? 'selected' : ''}>Intermediate</option>
                                <option value="advanced" ${course.level === 'advanced' ? 'selected' : ''}>Advanced</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Duration (hours)</label>
                            <input type="number" name="duration_hours" step="0.5" value="${course.duration_hours || ''}">
                        </div>
                        <div class="form-group">
                            <label>Thumbnail URL</label>
                            <input type="text" name="thumbnail" value="${course.thumbnail || ''}">
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" name="is_premium" ${course.is_premium ? 'checked' : ''}> Premium Course
                            </label>
                        </div>
                        <div style="display: flex; gap: 1rem;">
                            <button type="submit" class="primary">Update</button>
                            <button type="button" onclick="window.location='/courses'">Cancel</button>
                        </div>
                    </form>
                </div>
            `;
        } catch (error) {
            ui.showToast(error.message, 'error');
