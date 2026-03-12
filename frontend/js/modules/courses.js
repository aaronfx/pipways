const CoursesPage = {
    async render(container) {
        container.innerHTML = `
            <div class="page-header">
                <h1>Trading Courses</h1>
                <div class="filters">
                    <select id="levelFilter" onchange="CoursesPage.filter()">
                        <option value="">All Levels</option>
                        <option value="BEGINNER">Beginner</option>
                        <option value="INTERMEDIATE">Intermediate</option>
                        <option value="ADVANCED">Advanced</option>
                    </select>
                </div>
            </div>
        `;

        try {
            const courses = await API.getCourses({ is_published: true });
            Store.setState('courses', courses);
            this.renderGrid(courses);
        } catch (error) {
            container.innerHTML += '<p class="error">Failed to load courses</p>';
        }
    },

    renderGrid(courses) {
        const container = document.getElementById('app');
        if (courses.length === 0) {
            container.innerHTML += '<p>No courses available.</p>';
            return;
        }

        let html = '<div class="courses-grid">';
        courses.forEach(course => {
            html += `
                <div class="course-card">
                    <div class="course-level ${course.level.toLowerCase()}">${course.level}</div>
                    <h3>${UI.escapeHtml(course.title)}</h3>
                    <p>${UI.escapeHtml(course.description)}</p>
                    <div class="course-footer">
                        <span class="category">${course.category}</span>
                        <span class="price">${course.price > 0 ? '$' + course.price : 'Free'}</span>
                    </div>
                    <button class="btn btn-secondary btn-block" onclick="CoursesPage.viewCourse(${course.id})">
                        View Course
                    </button>
                </div>
            `;
        });
        html += '</div>';
        container.innerHTML += html;
    },

    filter() {
        const level = document.getElementById('levelFilter').value;
        const filtered = level 
            ? Store.state.courses.filter(c => c.level === level)
            : Store.state.courses;
        const grid = document.querySelector('.courses-grid');
        if (grid) grid.remove();
        this.renderGrid(filtered);
    },

    viewCourse(id) {
        UI.showToast('Course detail view - implement with quiz module', 'info');
    }
};