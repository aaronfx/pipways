/**
 * Admin LMS (Learning Management System) Module
 */

const adminLMS = {
    courses: [],
    editingId: null,
    
    async load() {
        const container = document.getElementById('admin-courses-grid');
        if(!container) return;
        
        container.innerHTML = '<div class="text-center" style="grid-column: 1/-1; padding: 40px;">Loading courses...</div>';
        
        try {
            const response = await api.get('/api/admin/courses');
            this.courses = response.courses || [];
            this.render();
        } catch (error) {
            container.innerHTML = `<div class="text-center text-danger" style="grid-column: 1/-1;">Error: ${error.message}</div>`;
        }
    },
    
    render() {
        const container = document.getElementById('admin-courses-grid');
        
        if(this.courses.length === 0) {
            container.innerHTML = '<div class="text-center" style="grid-column: 1/-1; padding: 40px;">No courses found</div>';
            return;
        }
        
        container.innerHTML = this.courses.map(course => `
            <div class="course-admin-card">
                <div class="course-admin-header">
                    <h4>${course.title}</h4>
                    <p style="color: var(--text-secondary); font-size: 14px; margin-top: 4px;">${course.description?.substring(0, 60)}...</p>
                    <div class="course-admin-meta">
                        <span><i class="fas fa-layer-group"></i> ${course.level}</span>
                        <span><i class="fas fa-clock"></i> ${course.duration_hours || 0}h</span>
                        <span><i class="fas fa-book"></i> ${course.modules?.length || 0} modules</span>
                        ${course.is_premium ? '<span class="badge badge-premium">VIP</span>' : ''}
                    </div>
                </div>
                <div class="course-admin-actions">
                    <button class="btn btn-sm" onclick="adminLMS.editCourse(${course.id})">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="adminLMS.manageModules(${course.id})">
                        <i class="fas fa-list"></i> Modules
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="adminLMS.deleteCourse(${course.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    },
    
    openCourseModal() {
        this.editingId = null;
        document.getElementById('course-form').reset();
        document.getElementById('course-modal-title').textContent = 'Create Course';
        document.getElementById('course-id').value = '';
        ui.openModal('course-modal');
    },
    
    async editCourse(id) {
        const course = this.courses.find(c => c.id === id);
        if(!course) return;
        
        this.editingId = id;
        document.getElementById('course-modal-title').textContent = 'Edit Course';
        document.getElementById('course-id').value = course.id;
        document.getElementById('course-title').value = course.title;
        document.getElementById('course-description').value = course.description || '';
        document.getElementById('course-level').value = course.level || 'beginner';
        document.getElementById('course-duration').value = course.duration_hours || '';
        document.getElementById('course-thumbnail').value = course.thumbnail || '';
        document.getElementById('course-premium').checked = course.is_premium || false;
        
        ui.openModal('course-modal');
    },
    
    async saveCourse() {
        const data = {
            title: document.getElementById('course-title').value,
            description: document.getElementById('course-description').value,
            content: document.getElementById('course-description').value,
            level: document.getElementById('course-level').value,
            duration_hours: parseFloat(document.getElementById('course-duration').value) || null,
            thumbnail: document.getElementById('course-thumbnail').value,
            is_premium: document.getElementById('course-premium').checked
        };
        
        try {
            ui.showLoading('Saving course...');
            
            if(this.editingId) {
                await api.put(`/api/courses/${this.editingId}`, data);
                ui.showToast('Course updated successfully', 'success');
            } else {
                await api.post('/api/courses', data);
                ui.showToast('Course created successfully', 'success');
            }
            
            ui.closeModal('course-modal');
            this.load();
            
        } catch (error) {
            ui.showToast('Error saving course: ' + error.message, 'error');
        } finally {
            ui.hideLoading();
        }
    },
    
    async deleteCourse(id) {
        if(!confirm('Delete this course and all its modules?')) return;
        
        try {
            await api.delete(`/api/courses/${id}`);
            ui.showToast('Course deleted', 'success');
            this.load();
        } catch (error) {
            ui.showToast('Error deleting course: ' + error.message, 'error');
        }
    },
    
    manageModules(courseId) {
        const course = this.courses.find(c => c.id === courseId);
        if(!course) return;
        
        ui.showToast(`Managing modules for: ${course.title}`, 'info');
    },
    
    search() {
        const term = document.getElementById('course-search')?.value.toLowerCase();
        if(!term) {
            this.render();
            return;
        }
        
        const filtered = this.courses.filter(c => 
            c.title.toLowerCase().includes(term) ||
            (c.description && c.description.toLowerCase().includes(term))
        );
        
        const container = document.getElementById('admin-courses-grid');
        if(filtered.length === 0) {
            container.innerHTML = '<div class="text-center" style="grid-column: 1/-1;">No matching courses</div>';
            return;
        }
        
        container.innerHTML = filtered.map(course => `
            <div class="course-admin-card">
                <div class="course-admin-header">
                    <h4>${course.title}</h4>
                    <p style="color: var(--text-secondary); font-size: 14px;">${course.description?.substring(0, 60)}...</p>
                    <div class="course-admin-meta">
                        <span><i class="fas fa-layer-group"></i> ${course.level}</span>
                        <span><i class="fas fa-clock"></i> ${course.duration_hours || 0}h</span>
                        <span><i class="fas fa-book"></i> ${course.modules?.length || 0} modules</span>
                        ${course.is_premium ? '<span class="badge badge-premium">VIP</span>' : ''}
                    </div>
                </div>
                <div class="course-admin-actions">
                    <button class="btn btn-sm" onclick="adminLMS.editCourse(${course.id})"><i class="fas fa-edit"></i> Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="adminLMS.deleteCourse(${course.id})"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        `).join('');
    }
};
