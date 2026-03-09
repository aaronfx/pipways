// In AdminPage.js, replace the bindForms method:

bindForms() {
    // SAFETY CHECK: Ensure element exists
    if (!this.element) {
        console.warn('AdminPage element not ready');
        return;
    }

    // Blog form
    const blogForm = this.element.querySelector('#blog-form');
    if (blogForm) {
        blogForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = {
                title: this.element.querySelector('#blog-title')?.value,
                content: this.element.querySelector('#blog-content')?.value,
                excerpt: this.element.querySelector('#blog-excerpt')?.value,
                category: this.element.querySelector('#blog-category')?.value,
                status: this.element.querySelector('#blog-status')?.value,
                is_premium: this.element.querySelector('#blog-premium')?.checked || false
            };
            
            try {
                await api.createPost(formData);
                alert('Blog post created!');
                this.loadData();
            } catch (err) {
                alert('Failed to create post: ' + err.message);
            }
        });
    }

    // Course form
    const courseForm = this.element.querySelector('#course-form');
    if (courseForm) {
        courseForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = {
                title: this.element.querySelector('#course-title')?.value,
                description: this.element.querySelector('#course-description')?.value,
                level: this.element.querySelector('#course-level')?.value,
                duration_hours: parseInt(this.element.querySelector('#course-duration')?.value || 0),
                is_premium: this.element.querySelector('#course-premium')?.checked || false
            };
            
            try {
                await api.createCourse(formData);
                alert('Course created!');
                this.loadData();
            } catch (err) {
                alert('Failed to create course: ' + err.message);
            }
        });
    }

    // Webinar form
    const webinarForm = this.element.querySelector('#webinar-form');
    if (webinarForm) {
        webinarForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = {
                title: this.element.querySelector('#webinar-title')?.value,
                description: this.element.querySelector('#webinar-description')?.value,
                scheduled_at: this.element.querySelector('#webinar-date')?.value,
                duration_minutes: parseInt(this.element.querySelector('#webinar-duration')?.value || 60),
                max_participants: parseInt(this.element.querySelector('#webinar-max')?.value || 100),
                is_premium: this.element.querySelector('#webinar-premium')?.checked || false
            };
            
            try {
                await api.createWebinar(formData);
                alert('Webinar created!');
                this.loadData();
            } catch (err) {
                alert('Failed to create webinar: ' + err.message);
            }
        });
    }
}
